"""Notification service implementation.

This module provides comprehensive notification functionality including
in-app notifications, email notifications, push notifications, and webhook integrations.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, cast

import redis
from fastapi import BackgroundTasks
from fastapi_mail import ConnectionConfig
from pydantic import SecretStr
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFound
from app.models.notification import (
    Notification,
    NotificationChannel,
    NotificationPreferences,
    NotificationQueue,
)
from app.models.user import User
from app.schemas.notification import (
    BulkNotificationCreate,
    NotificationCreate,
    NotificationPreferencesUpdate,
    NotificationQueueCreate,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications."""

    def __init__(self, db: Session):
        """Initialize notification service."""
        self.db = db
        self.redis_client = self._get_redis_client()
        self.mail_config = self._get_mail_config()

    def _get_redis_client(self) -> Optional[redis.Redis]:
        """Get Redis client for queue management."""
        try:
            client = cast(
                redis.Redis,
                redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                )
            )
            # Test connection
            client.ping()
            return client
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            return None

    def _get_mail_config(self) -> Optional[ConnectionConfig]:
        """Get email configuration."""
        try:
            return ConnectionConfig(
                MAIL_USERNAME=settings.MAIL_USERNAME,
                MAIL_PASSWORD=SecretStr(settings.MAIL_PASSWORD),
                MAIL_FROM=settings.MAIL_FROM,
                MAIL_PORT=settings.MAIL_PORT,
                MAIL_SERVER=settings.MAIL_SERVER,
                MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
                MAIL_STARTTLS=settings.MAIL_STARTTLS,
                MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
                USE_CREDENTIALS=settings.MAIL_USE_CREDENTIALS,
            )
        except Exception as e:
            logger.warning(f"Mail configuration failed: {e}")
            return None

    # Notification CRUD Operations

    def create_notification(
        self, notification_data: NotificationCreate, created_by: Optional[int] = None
    ) -> Notification:
        """Create a new in-app notification."""

        # Validate user exists
        user = self.db.query(User).filter(User.id == notification_data.user_id).first()
        if not user:
            raise NotFound(f"User with ID {notification_data.user_id} not found")

        notification = Notification(
            user_id=notification_data.user_id,
            title=notification_data.title,
            message=notification_data.message,
            notification_type=notification_data.notification_type,
            priority=notification_data.priority,
            action_url=notification_data.action_url,
            extra_metadata=notification_data.extra_metadata,
            organization_id=notification_data.organization_id,
            expires_at=notification_data.expires_at,
        )

        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)

        # Add to Redis for real-time updates
        self._publish_notification_update(notification)

        logger.info(
            (
                f"Created notification {notification.id} "
                f"for user {notification_data.user_id}"
            )
        )
        return notification

    def get_user_notifications(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False,
        category: Optional[str] = None,
        organization_id: Optional[int] = None,
    ) -> tuple[List[Notification], int]:
        """Get notifications for a user with pagination."""

        query = self.db.query(Notification).filter(Notification.user_id == user_id)

        # Apply filters
        if unread_only:
            query = query.filter(~Notification.is_read)

        # Note: category field does not exist in Notification model
        # This filter is commented out until category field is added
        # if category:
        #     query = query.filter(Notification.category == category)

        if organization_id:
            query = query.filter(Notification.organization_id == organization_id)

        # Filter out expired notifications
        query = query.filter(
            or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > datetime.utcnow(),
            )
        )

        total = query.count()

        notifications = (
            query.order_by(desc(Notification.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

        return notifications, total

    def mark_notifications_as_read(
        self, user_id: int, notification_ids: List[int]
    ) -> int:
        """Mark multiple notifications as read."""

        updated_count = (
            self.db.query(Notification)
            .filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.id.in_(notification_ids),
                    ~Notification.is_read,
                )
            )
            .update(
                {
                    "is_read": True,
                    "read_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
                synchronize_session=False,
            )
        )

        self.db.commit()

        # Publish update for real-time notifications
        if updated_count > 0:
            self._publish_read_status_update(user_id, notification_ids)

        logger.info(f"Marked {updated_count} notifications as read for user {user_id}")
        return updated_count

    def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user."""

        updated_count = (
            self.db.query(Notification)
            .filter(and_(Notification.user_id == user_id, ~Notification.is_read))
            .update(
                {
                    "is_read": True,
                    "read_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
                synchronize_session=False,
            )
        )

        self.db.commit()

        if updated_count > 0:
            self._publish_read_status_update(user_id, [])

        logger.info(
            f"Marked all {updated_count} notifications as read for user {user_id}"
        )
        return updated_count

    def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications for a user."""

        return (
            self.db.query(Notification)
            .filter(
                and_(
                    Notification.user_id == user_id,
                    ~Notification.is_read,
                    or_(
                        Notification.expires_at.is_(None),
                        Notification.expires_at > datetime.utcnow(),
                    ),
                )
            )
            .count()
        )

    def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """Delete a notification (user can only delete their own notifications)."""

        notification = (
            self.db.query(Notification)
            .filter(
                and_(
                    Notification.id == notification_id, Notification.user_id == user_id
                )
            )
            .first()
        )

        if not notification:
            return False

        self.db.delete(notification)
        self.db.commit()

        logger.info(f"Deleted notification {notification_id} for user {user_id}")
        return True

    # Bulk Operations

    def create_bulk_notifications(
        self,
        bulk_data: BulkNotificationCreate,
        created_by: Optional[int] = None,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> Dict[str, Any]:
        """Create notifications for multiple users."""

        created_count = 0
        queued_count = 0
        failed_count = 0
        errors = []

        # Validate users exist
        valid_users = (
            self.db.query(User.id).filter(User.id.in_(bulk_data.user_ids)).all()
        )
        valid_user_ids = {user.id for user in valid_users}

        for user_id in bulk_data.user_ids:
            if user_id not in valid_user_ids:
                failed_count += 1
                errors.append(f"User {user_id} not found")
                continue

            try:
                # Create in-app notification if requested
                if NotificationChannel.IN_APP in bulk_data.channels:
                    notification_data = NotificationCreate(
                        user_id=user_id,
                        title=bulk_data.title,
                        message=bulk_data.message,
                        notification_type=bulk_data.notification_type,
                        priority=bulk_data.priority,
                        action_url=bulk_data.action_url,
                        extra_metadata=bulk_data.extra_metadata,
                        organization_id=bulk_data.organization_id,
                        expires_at=bulk_data.expires_at,
                    )
                    self.create_notification(notification_data, created_by)
                    created_count += 1

                # Queue other channels for background processing
                for channel in bulk_data.channels:
                    if channel != NotificationChannel.IN_APP:
                        queue_data = NotificationQueueCreate(
                            user_id=user_id,
                            channel=channel,
                            title=bulk_data.title,
                            message=bulk_data.message,
                            priority=bulk_data.priority,
                            organization_id=bulk_data.organization_id,
                        )

                        if background_tasks:
                            background_tasks.add_task(
                                self._queue_notification, queue_data
                            )
                        else:
                            self._queue_notification(queue_data)
                        queued_count += 1

            except Exception as e:
                failed_count += 1
                errors.append(
                    f"Failed to create notification for user {user_id}: {str(e)}"
                )
                logger.error(f"Bulk notification error for user {user_id}: {e}")

        return {
            "created_count": created_count,
            "queued_count": queued_count,
            "failed_count": failed_count,
            "errors": errors,
        }

    # Notification Preferences

    def get_user_preferences(self, user_id: int) -> Optional[NotificationPreferences]:
        """Get notification preferences for a user."""

        return (
            self.db.query(NotificationPreferences)
            .filter(NotificationPreferences.user_id == user_id)
            .first()
        )

    def create_or_update_preferences(
        self, user_id: int, preferences_data: NotificationPreferencesUpdate
    ) -> NotificationPreferences:
        """Create or update notification preferences for a user."""

        existing = self.get_user_preferences(user_id)

        if existing:
            # Update existing preferences
            for field, value in preferences_data.dict(exclude_unset=True).items():
                setattr(existing, field, value)
            existing.updated_at = datetime.utcnow()
            preferences = existing
        else:
            # Create new preferences
            preferences = NotificationPreferences(
                user_id=user_id, **preferences_data.dict()
            )
            self.db.add(preferences)

        self.db.commit()
        self.db.refresh(preferences)

        logger.info(f"Updated notification preferences for user {user_id}")
        return preferences

    # Queue Management

    def _queue_notification(
        self, queue_data: NotificationQueueCreate
    ) -> NotificationQueue:
        """Add notification to processing queue."""

        queue_item = NotificationQueue(
            user_id=queue_data.user_id,
            channel=queue_data.channel,
            title=queue_data.title,
            message=queue_data.message,
            template_name=queue_data.template_name,
            template_data=queue_data.template_data,
            recipient_email=queue_data.recipient_email,
            priority=queue_data.priority,
            organization_id=queue_data.organization_id,
            status="pending",
            next_attempt_at=datetime.utcnow(),
        )

        self.db.add(queue_item)
        self.db.commit()
        self.db.refresh(queue_item)

        # Add to Redis queue for background processing
        if self.redis_client:
            queue_name = f"notifications:{queue_data.channel.value}"
            self.redis_client.lpush(
                queue_name,
                json.dumps(
                    {
                        "id": queue_item.id,
                        "channel": queue_data.channel.value,
                        "priority": queue_data.priority,
                    }
                ),
            )

        return queue_item

    # Real-time Updates

    def _publish_notification_update(self, notification: Notification) -> None:
        """Publish notification update to Redis for real-time updates."""

        if not self.redis_client:
            return

        channel = f"user:{notification.user_id}:notifications"
        message = {
            "type": "new_notification",
            "notification_id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "priority": notification.priority,
            "created_at": notification.created_at.isoformat(),
        }

        self.redis_client.publish(channel, json.dumps(message))

    def _publish_read_status_update(
        self, user_id: int, notification_ids: List[int]
    ) -> None:
        """Publish read status update to Redis."""

        if not self.redis_client:
            return

        channel = f"user:{user_id}:notifications"
        message = {
            "type": "read_status_update",
            "notification_ids": notification_ids,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.redis_client.publish(channel, json.dumps(message))

    # Statistics and Analytics

    def get_notification_stats(self, user_id: int) -> Dict[str, Any]:
        """Get notification statistics for a user."""

        base_query = self.db.query(Notification).filter(Notification.user_id == user_id)

        total_notifications = base_query.count()
        unread_notifications = base_query.filter(~Notification.is_read).count()

        # Notifications by type
        type_stats = (
            base_query.with_entities(
                Notification.notification_type, func.count(Notification.id)
            )
            .group_by(Notification.notification_type)
            .all()
        )
        notifications_by_type = {
            type_val.value: count for type_val, count in type_stats
        }

        # Notifications by priority
        priority_stats = (
            base_query.with_entities(Notification.priority, func.count(Notification.id))
            .group_by(Notification.priority)
            .all()
        )
        notifications_by_priority = {
            priority.value: count for priority, count in priority_stats
        }

        # Notifications by category (disabled until category field is added)
        # category_stats = (
        #     base_query.filter(Notification.category.isnot(None))
        #     .with_entities(Notification.category, func.count(Notification.id))
        #     .group_by(Notification.category)
        #     .all()
        # )
        notifications_by_category: Dict[str, int] = {}

        # Recent activity (last 10 notifications)
        recent_notifications = (
            base_query.order_by(desc(Notification.created_at)).limit(10).all()
        )

        return {
            "total_notifications": total_notifications,
            "unread_notifications": unread_notifications,
            "notifications_by_type": notifications_by_type,
            "notifications_by_priority": notifications_by_priority,
            "notifications_by_category": notifications_by_category,
            "recent_activity": recent_notifications,
        }

    # Cleanup Operations

    def cleanup_expired_notifications(self) -> int:
        """Remove expired notifications."""

        deleted_count = (
            self.db.query(Notification)
            .filter(
                and_(
                    Notification.expires_at.isnot(None),
                    Notification.expires_at < datetime.utcnow(),
                )
            )
            .delete(synchronize_session=False)
        )

        self.db.commit()

        logger.info(f"Cleaned up {deleted_count} expired notifications")
        return deleted_count

    def cleanup_old_read_notifications(self, days_old: int = 30) -> int:
        """Remove old read notifications."""

        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        deleted_count = (
            self.db.query(Notification)
            .filter(and_(Notification.is_read, Notification.read_at < cutoff_date))
            .delete(synchronize_session=False)
        )

        self.db.commit()

        logger.info(f"Cleaned up {deleted_count} old read notifications")
        return deleted_count


# Export notification service
__all__ = ["NotificationService"]
