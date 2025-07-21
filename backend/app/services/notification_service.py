"""Comprehensive notification service with multi-channel support."""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.base_service import BaseService
from app.core.cache import cache_manager, ModelCache
from app.core.monitoring import monitor_performance
from app.models.notification import (
    Notification,
    NotificationChannel,
    NotificationEvent,
    NotificationPreference,
    NotificationPriority,
    NotificationQueue,
    NotificationStatus,
    NotificationTemplate,
)
from app.models.user import User
from app.models.organization import Organization


class NotificationTemplateService(BaseService[NotificationTemplate]):
    """Service for managing notification templates."""

    def __init__(self, db: AsyncSession):
        super().__init__(NotificationTemplate, db)

    @monitor_performance("notification.template.create")
    async def create_template(
        self,
        name: str,
        template_key: str,
        channel: NotificationChannel,
        content_template: str,
        category: str,
        subject_template: Optional[str] = None,
        html_template: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        validation_rules: Optional[Dict[str, Any]] = None,
        organization_id: Optional[int] = None,
        created_by: Optional[int] = None,
        **kwargs
    ) -> NotificationTemplate:
        """Create a new notification template."""
        template_data = {
            "name": name,
            "template_key": template_key,
            "channel": channel,
            "content_template": content_template,
            "category": category,
            "subject_template": subject_template,
            "html_template": html_template,
            "variables": variables or {},
            "validation_rules": validation_rules or {},
            "organization_id": organization_id,
            "created_by": created_by,
            **kwargs
        }
        
        template = await self.create(template_data)
        
        # Cache the template
        await cache_manager.set(
            f"template:{template_key}",
            template.__dict__,
            ttl=3600,
            namespace="notification_templates"
        )
        
        return template

    @monitor_performance("notification.template.get_by_key")
    async def get_by_key(
        self,
        template_key: str,
        organization_id: Optional[int] = None
    ) -> Optional[NotificationTemplate]:
        """Get template by key with caching."""
        # Try cache first
        cached = await cache_manager.get(
            f"template:{template_key}",
            namespace="notification_templates"
        )
        if cached:
            return NotificationTemplate(**cached)

        # Build query
        query = await self.get_query()
        query = query.filter(NotificationTemplate.template_key == template_key)
        query = query.filter(NotificationTemplate.is_active == True)
        
        if organization_id:
            query = query.filter(
                or_(
                    NotificationTemplate.organization_id == organization_id,
                    NotificationTemplate.organization_id.is_(None)  # System templates
                )
            )
        
        result = await self.db.execute(query)
        template = result.scalar_one_or_none()
        
        if template:
            # Cache the result
            await cache_manager.set(
                f"template:{template_key}",
                template.__dict__,
                ttl=3600,
                namespace="notification_templates"
            )
        
        return template

    @monitor_performance("notification.template.render")
    async def render_template(
        self,
        template: NotificationTemplate,
        variables: Dict[str, Any]
    ) -> Dict[str, str]:
        """Render template with variables."""
        try:
            from jinja2 import Template, Environment, BaseLoader
            
            env = Environment(loader=BaseLoader())
            
            # Render content
            content_tmpl = env.from_string(template.content_template)
            rendered_content = content_tmpl.render(**variables)
            
            result = {"content": rendered_content}
            
            # Render subject if available
            if template.subject_template:
                subject_tmpl = env.from_string(template.subject_template)
                result["subject"] = subject_tmpl.render(**variables)
            
            # Render HTML if available
            if template.html_template:
                html_tmpl = env.from_string(template.html_template)
                result["html_content"] = html_tmpl.render(**variables)
            
            return result
        
        except Exception as e:
            raise ValueError(f"Template rendering failed: {str(e)}")

    async def list_by_category(
        self,
        category: str,
        organization_id: Optional[int] = None,
        channel: Optional[NotificationChannel] = None
    ) -> List[NotificationTemplate]:
        """List templates by category."""
        query = await self.get_query()
        query = query.filter(NotificationTemplate.category == category)
        query = query.filter(NotificationTemplate.is_active == True)
        
        if organization_id:
            query = query.filter(
                or_(
                    NotificationTemplate.organization_id == organization_id,
                    NotificationTemplate.organization_id.is_(None)
                )
            )
        
        if channel:
            query = query.filter(NotificationTemplate.channel == channel)
        
        query = query.order_by(NotificationTemplate.name)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())


class NotificationPreferenceService(BaseService[NotificationPreference]):
    """Service for managing user notification preferences."""

    def __init__(self, db: AsyncSession):
        super().__init__(NotificationPreference, db)

    @monitor_performance("notification.preference.get_user_preferences")
    async def get_user_preferences(
        self,
        user_id: int,
        organization_id: Optional[int] = None
    ) -> List[NotificationPreference]:
        """Get all preferences for a user."""
        # Try cache first
        cache_key = f"user_preferences:{user_id}"
        if organization_id:
            cache_key += f":{organization_id}"
        
        cached = await cache_manager.get(cache_key, namespace="preferences")
        if cached:
            return [NotificationPreference(**pref) for pref in cached]

        query = await self.get_query()
        query = query.filter(NotificationPreference.user_id == user_id)
        
        if organization_id:
            query = query.filter(
                or_(
                    NotificationPreference.organization_id == organization_id,
                    NotificationPreference.organization_id.is_(None)
                )
            )
        
        result = await self.db.execute(query)
        preferences = list(result.scalars().all())
        
        # Cache the result
        await cache_manager.set(
            cache_key,
            [pref.__dict__ for pref in preferences],
            ttl=1800,
            namespace="preferences"
        )
        
        return preferences

    @monitor_performance("notification.preference.check_permission")
    async def check_permission(
        self,
        user_id: int,
        category: str,
        channel: NotificationChannel,
        organization_id: Optional[int] = None
    ) -> bool:
        """Check if user allows notifications for category/channel."""
        preferences = await self.get_user_preferences(user_id, organization_id)
        
        # Find specific preference
        for pref in preferences:
            if pref.category == category and pref.channel == channel:
                return pref.enabled
        
        # Default to enabled if no specific preference found
        return True

    async def update_preference(
        self,
        user_id: int,
        category: str,
        channel: NotificationChannel,
        enabled: bool,
        frequency: str = "immediate",
        contact_info: Optional[Dict[str, str]] = None,
        organization_id: Optional[int] = None
    ) -> NotificationPreference:
        """Update or create notification preference."""
        # Check if preference exists
        existing = await self.get_by_filters({
            "user_id": user_id,
            "category": category,
            "channel": channel,
            "organization_id": organization_id
        })
        
        if existing:
            # Update existing
            preference = await self.update(existing.id, {
                "enabled": enabled,
                "frequency": frequency,
                "contact_info": contact_info or existing.contact_info
            })
        else:
            # Create new
            preference = await self.create({
                "user_id": user_id,
                "category": category,
                "channel": channel,
                "enabled": enabled,
                "frequency": frequency,
                "contact_info": contact_info,
                "organization_id": organization_id
            })
        
        # Invalidate cache
        cache_key = f"user_preferences:{user_id}"
        if organization_id:
            cache_key += f":{organization_id}"
        await cache_manager.delete(cache_key, namespace="preferences")
        
        return preference


class NotificationService(BaseService[Notification]):
    """Main notification service for sending and tracking notifications."""

    def __init__(self, db: AsyncSession):
        super().__init__(Notification, db)
        self.template_service = NotificationTemplateService(db)
        self.preference_service = NotificationPreferenceService(db)

    @monitor_performance("notification.send")
    async def send_notification(
        self,
        template_key: str,
        recipient_user_id: Optional[int] = None,
        recipient_email: Optional[str] = None,
        recipient_phone: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        scheduled_at: Optional[datetime] = None,
        organization_id: Optional[int] = None,
        created_by: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """Send a single notification."""
        # Get template
        template = await self.template_service.get_by_key(template_key, organization_id)
        if not template:
            raise ValueError(f"Template not found: {template_key}")

        # Check user preferences if recipient_user_id provided
        if recipient_user_id:
            can_send = await self.preference_service.check_permission(
                recipient_user_id,
                template.category,
                template.channel,
                organization_id
            )
            if not can_send:
                raise ValueError("User has disabled this type of notification")

        # Render template
        rendered = await self.template_service.render_template(template, variables or {})

        # Determine recipient contact info
        contact_info = await self._get_recipient_info(
            template.channel,
            recipient_user_id,
            recipient_email,
            recipient_phone
        )

        # Create notification record
        notification_data = {
            "template_id": template.id,
            "channel": template.channel,
            "priority": priority,
            "subject": rendered.get("subject"),
            "content": rendered["content"],
            "html_content": rendered.get("html_content"),
            "recipient_user_id": recipient_user_id,
            "scheduled_at": scheduled_at,
            "organization_id": organization_id,
            "created_by": created_by,
            "metadata": metadata,
            **contact_info
        }

        notification = await self.create(notification_data)

        # Queue for immediate or scheduled delivery
        if scheduled_at and scheduled_at > datetime.utcnow():
            # Schedule for later
            await self._schedule_notification(notification)
        else:
            # Send immediately
            await self._deliver_notification(notification)

        return notification

    @monitor_performance("notification.send_batch")
    async def send_batch_notification(
        self,
        template_key: str,
        recipients: List[Dict[str, Any]],
        variables: Optional[Dict[str, Any]] = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        scheduled_at: Optional[datetime] = None,
        organization_id: Optional[int] = None,
        created_by: Optional[int] = None
    ) -> str:
        """Send batch notifications and return batch ID."""
        batch_id = str(uuid4())
        
        # Queue the batch for processing
        queue_service = NotificationQueueService(self.db)
        await queue_service.create({
            "batch_id": batch_id,
            "template_key": template_key,
            "notification_data": {
                "variables": variables or {},
                "priority": priority,
                "metadata": {"batch": True}
            },
            "recipients": recipients,
            "scheduled_at": scheduled_at or datetime.utcnow(),
            "total_recipients": len(recipients),
            "organization_id": organization_id,
            "created_by": created_by
        })
        
        return batch_id

    async def _get_recipient_info(
        self,
        channel: NotificationChannel,
        user_id: Optional[int],
        email: Optional[str],
        phone: Optional[str]
    ) -> Dict[str, Optional[str]]:
        """Get recipient contact information based on channel."""
        result = {
            "recipient_email": None,
            "recipient_phone": None,
            "recipient_device_token": None
        }

        if user_id:
            # Get user preferences to find contact info
            preferences = await self.preference_service.get_user_preferences(user_id)
            for pref in preferences:
                if pref.channel == channel and pref.contact_info:
                    if channel == NotificationChannel.EMAIL:
                        result["recipient_email"] = pref.contact_info.get("email")
                    elif channel == NotificationChannel.SMS:
                        result["recipient_phone"] = pref.contact_info.get("phone")
                    elif channel == NotificationChannel.PUSH:
                        result["recipient_device_token"] = pref.contact_info.get("device_token")
                    break

        # Override with provided values
        if email:
            result["recipient_email"] = email
        if phone:
            result["recipient_phone"] = phone

        return result

    async def _deliver_notification(self, notification: Notification) -> None:
        """Deliver notification through appropriate channel."""
        try:
            # Update status to sending
            await self.update(notification.id, {
                "status": NotificationStatus.SENT,
                "sent_at": datetime.utcnow()
            })

            # Here you would integrate with actual providers
            # For now, we'll simulate delivery
            if notification.channel == NotificationChannel.EMAIL:
                await self._send_email(notification)
            elif notification.channel == NotificationChannel.SMS:
                await self._send_sms(notification)
            elif notification.channel == NotificationChannel.PUSH:
                await self._send_push(notification)
            elif notification.channel == NotificationChannel.IN_APP:
                await self._send_in_app(notification)

            # Update status to delivered
            await self.update(notification.id, {
                "status": NotificationStatus.DELIVERED,
                "delivered_at": datetime.utcnow()
            })

        except Exception as e:
            # Handle delivery failure
            await self.update(notification.id, {
                "status": NotificationStatus.FAILED,
                "error_message": str(e),
                "retry_count": notification.retry_count + 1
            })

            # Schedule retry if within limits
            if notification.retry_count < notification.max_retries:
                await self._schedule_retry(notification)

    async def _send_email(self, notification: Notification) -> None:
        """Send email notification (placeholder for actual implementation)."""
        # Here you would integrate with email providers like SendGrid, AWS SES, etc.
        print(f"Sending email to {notification.recipient_email}: {notification.subject}")

    async def _send_sms(self, notification: Notification) -> None:
        """Send SMS notification (placeholder for actual implementation)."""
        # Here you would integrate with SMS providers like Twilio, AWS SNS, etc.
        print(f"Sending SMS to {notification.recipient_phone}: {notification.content}")

    async def _send_push(self, notification: Notification) -> None:
        """Send push notification (placeholder for actual implementation)."""
        # Here you would integrate with push providers like Firebase, Apple Push, etc.
        print(f"Sending push to {notification.recipient_device_token}: {notification.content}")

    async def _send_in_app(self, notification: Notification) -> None:
        """Send in-app notification (usually just marks as delivered)."""
        print(f"In-app notification created for user {notification.recipient_user_id}")

    async def _schedule_notification(self, notification: Notification) -> None:
        """Schedule notification for later delivery."""
        # This would typically use a task queue like Celery or RQ
        print(f"Scheduled notification {notification.id} for {notification.scheduled_at}")

    async def _schedule_retry(self, notification: Notification) -> None:
        """Schedule notification retry."""
        # Calculate retry delay (exponential backoff)
        delay_minutes = 2 ** notification.retry_count
        retry_at = datetime.utcnow() + timedelta(minutes=delay_minutes)
        
        await self.update(notification.id, {
            "scheduled_at": retry_at
        })

    @monitor_performance("notification.get_user_notifications")
    async def get_user_notifications(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
        organization_id: Optional[int] = None
    ) -> List[Notification]:
        """Get notifications for a user."""
        query = await self.get_query()
        query = query.filter(Notification.recipient_user_id == user_id)
        
        if organization_id:
            query = query.filter(Notification.organization_id == organization_id)
        
        if unread_only:
            query = query.filter(Notification.opened_at.is_(None))
        
        query = query.order_by(desc(Notification.created_at))
        query = query.offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def mark_as_opened(self, notification_id: int, user_id: int) -> bool:
        """Mark notification as opened."""
        notification = await self.get_by_id(notification_id)
        if not notification or notification.recipient_user_id != user_id:
            return False
        
        await self.update(notification_id, {
            "opened_at": datetime.utcnow()
        })
        
        # Create event record
        await self._create_event(notification_id, "opened")
        
        return True

    async def _create_event(
        self,
        notification_id: int,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create notification event record."""
        from app.models.notification import NotificationEvent
        
        event = NotificationEvent(
            notification_id=notification_id,
            event_type=event_type,
            event_data=event_data,
            occurred_at=datetime.utcnow()
        )
        
        self.db.add(event)
        await self.db.commit()


class NotificationQueueService(BaseService[NotificationQueue]):
    """Service for managing notification queue and batch processing."""

    def __init__(self, db: AsyncSession):
        super().__init__(NotificationQueue, db)

    @monitor_performance("notification.queue.process_batch")
    async def process_batch(self, batch_id: str) -> Dict[str, int]:
        """Process a batch of notifications."""
        queue_item = await self.get_by_filters({"batch_id": batch_id})
        if not queue_item:
            raise ValueError(f"Batch not found: {batch_id}")

        # Update status to processing
        await self.update(queue_item.id, {"status": "processing"})

        notification_service = NotificationService(self.db)
        stats = {"successful": 0, "failed": 0}

        try:
            for recipient in queue_item.recipients:
                try:
                    await notification_service.send_notification(
                        template_key=queue_item.template_key,
                        recipient_user_id=recipient.get("user_id"),
                        recipient_email=recipient.get("email"),
                        recipient_phone=recipient.get("phone"),
                        variables=queue_item.notification_data.get("variables", {}),
                        priority=queue_item.notification_data.get("priority", NotificationPriority.MEDIUM),
                        organization_id=queue_item.organization_id,
                        created_by=queue_item.created_by,
                        metadata={"batch_id": batch_id}
                    )
                    stats["successful"] += 1
                except Exception as e:
                    print(f"Failed to send notification to {recipient}: {e}")
                    stats["failed"] += 1

            # Update final status
            await self.update(queue_item.id, {
                "status": "completed",
                "processed_at": datetime.utcnow(),
                "successful_sends": stats["successful"],
                "failed_sends": stats["failed"]
            })

        except Exception as e:
            await self.update(queue_item.id, {
                "status": "failed",
                "processed_at": datetime.utcnow(),
                "error_message": str(e)
            })
            raise

        return stats

    async def get_pending_batches(self, limit: int = 10) -> List[NotificationQueue]:
        """Get pending batches for processing."""
        query = await self.get_query()
        query = query.filter(NotificationQueue.status == "pending")
        query = query.filter(NotificationQueue.scheduled_at <= datetime.utcnow())
        query = query.order_by(asc(NotificationQueue.priority), asc(NotificationQueue.scheduled_at))
        query = query.limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())


# Health check for notification system
async def check_notification_health() -> Dict[str, Any]:
    """Check notification system health."""
    health_info = {
        "status": "healthy",
        "template_count": 0,
        "pending_notifications": 0,
        "failed_notifications_24h": 0,
        "provider_status": {}
    }
    
    try:
        # This would check actual provider status in real implementation
        health_info["provider_status"] = {
            "email": "healthy",
            "sms": "healthy",
            "push": "healthy"
        }
        
    except Exception as e:
        health_info["status"] = "degraded"
        health_info["error"] = str(e)
    
    return health_info