"""Notification API endpoints."""

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.notification import (
    BulkNotificationCreate,
    NotificationCreate,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
    NotificationQueueCreate,
    NotificationResponse,
)
from app.services.notification import NotificationService

router = APIRouter()


@router.post("/", response_model=NotificationResponse)
def create_notification(
    notification_data: NotificationCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationResponse:
    """Create a new notification."""
    service = NotificationService(db)

    try:
        notification = service.create_notification(
            notification_data=notification_data,
            created_by=current_user.id,
        )
        # Convert to response model
        return NotificationResponse(
            id=notification.id,
            user_id=notification.user_id,
            title=notification.title,
            message=notification.message,
            notification_type=notification.notification_type,
            priority=notification.priority,
            is_read=notification.is_read,
            created_at=notification.created_at,
            read_at=notification.read_at,
            action_url=notification.action_url,
            extra_metadata=notification.extra_metadata,
            organization_id=notification.organization_id,
            expires_at=notification.expires_at,
            sender_id=notification.sender_id,
            channels=notification.channels,
            status=notification.status,
            sent_at=notification.sent_at,
            delivered_at=notification.delivered_at,
            failed_at=notification.failed_at,
            action_text=notification.action_text,
            scheduled_for=notification.scheduled_for,
            updated_at=notification.updated_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk", response_model=Dict[str, Any])
def create_bulk_notifications(
    bulk_data: BulkNotificationCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Create multiple notifications in bulk."""
    service = NotificationService(db)

    try:
        result = service.create_bulk_notifications(
            bulk_data=bulk_data,
            created_by=current_user.id,
            background_tasks=background_tasks,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[NotificationResponse])
def get_user_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[NotificationResponse]:
    """Get user's notifications with filtering."""
    service = NotificationService(db)

    try:
        notifications, total = service.get_user_notifications(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            unread_only=unread_only,
        )
        # Convert to response models
        return [
            NotificationResponse(
                id=notification.id,
                user_id=notification.user_id,
                title=notification.title,
                message=notification.message,
                notification_type=notification.notification_type,
                priority=notification.priority,
                is_read=notification.is_read,
                created_at=notification.created_at,
                read_at=notification.read_at,
                action_url=notification.action_url,
                extra_metadata=notification.extra_metadata,
                organization_id=notification.organization_id,
                expires_at=notification.expires_at,
                sender_id=notification.sender_id,
                channels=notification.channels,
                status=notification.status,
                sent_at=notification.sent_at,
                delivered_at=notification.delivered_at,
                failed_at=notification.failed_at,
                action_text=notification.action_text,
                scheduled_for=notification.scheduled_for,
                updated_at=notification.updated_at,
            )
            for notification in notifications
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Mark a notification as read."""
    service = NotificationService(db)

    try:
        count = service.mark_notifications_as_read(
            user_id=current_user.id,
            notification_ids=[notification_id],
        )
        if count == 0:
            raise HTTPException(
                status_code=404, detail="Notification not found or already read"
            )
        return {"message": "Notification marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/mark-all-read")
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Mark all user notifications as read."""
    service = NotificationService(db)

    try:
        count = service.mark_all_as_read(user_id=current_user.id)
        return {"message": f"Marked {count} notifications as read"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Delete a notification."""
    service = NotificationService(db)

    try:
        success = service.delete_notification(
            notification_id=notification_id,
            user_id=current_user.id,
        )
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        return {"message": "Notification deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preferences", response_model=NotificationPreferencesResponse)
def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationPreferencesResponse:
    """Get user's notification preferences."""
    service = NotificationService(db)

    try:
        preferences = service.get_user_preferences(user_id=current_user.id)
        if not preferences:
            # Return default preferences if none exist
            from app.schemas.notification import NotificationPreferencesResponse

            return NotificationPreferencesResponse(
                id=0,  # Default ID for non-persisted preferences
                user_id=current_user.id,
                organization_id=None,
                email_enabled=True,
                email_digest=False,
                email_frequency="immediate",
                in_app_enabled=True,
                desktop_notifications=True,
                notification_types={
                    "info": True,
                    "warning": True,
                    "error": True,
                    "success": True,
                    "system": True,
                    "user": True,
                },
                channel_preferences={
                    "info": ["in_app"],
                    "warning": ["in_app", "email"],
                    "error": ["in_app", "email"],
                    "success": ["in_app"],
                    "system": ["in_app", "email"],
                    "user": ["in_app", "email"],
                },
                quiet_hours_enabled=False,
                quiet_hours_start=None,
                quiet_hours_end=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        # Convert to response model if needed
        return NotificationPreferencesResponse(
            id=preferences.id,
            user_id=preferences.user_id,
            organization_id=preferences.organization_id,
            email_enabled=preferences.email_enabled,
            email_digest=preferences.email_digest,
            email_frequency=preferences.email_frequency,
            in_app_enabled=preferences.in_app_enabled,
            desktop_notifications=preferences.desktop_notifications,
            notification_types=preferences.notification_types,
            channel_preferences=preferences.channel_preferences,
            quiet_hours_enabled=preferences.quiet_hours_enabled,
            quiet_hours_start=preferences.quiet_hours_start,
            quiet_hours_end=preferences.quiet_hours_end,
            created_at=preferences.created_at,
            updated_at=preferences.updated_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/preferences", response_model=NotificationPreferencesResponse)
def update_notification_preferences(
    preferences_data: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationPreferencesResponse:
    """Update user's notification preferences."""
    service = NotificationService(db)

    try:
        preferences = service.create_or_update_preferences(
            user_id=current_user.id,
            preferences_data=preferences_data,
        )
        # Convert to response model
        return NotificationPreferencesResponse(
            id=preferences.id,
            user_id=preferences.user_id,
            organization_id=preferences.organization_id,
            email_enabled=preferences.email_enabled,
            email_digest=preferences.email_digest,
            email_frequency=preferences.email_frequency,
            in_app_enabled=preferences.in_app_enabled,
            desktop_notifications=preferences.desktop_notifications,
            notification_types=preferences.notification_types,
            channel_preferences=preferences.channel_preferences,
            quiet_hours_enabled=preferences.quiet_hours_enabled,
            quiet_hours_start=preferences.quiet_hours_start,
            quiet_hours_end=preferences.quiet_hours_end,
            created_at=preferences.created_at,
            updated_at=preferences.updated_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/queue", response_model=Dict[str, str])
def add_to_notification_queue(
    queue_data: NotificationQueueCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Add notification to processing queue."""
    service = NotificationService(db)

    try:
        service._queue_notification(queue_data)
        return {"message": "Notification added to queue successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=Dict[str, Any])
def get_notification_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get user's notification statistics."""
    service = NotificationService(db)

    try:
        stats = service.get_notification_stats(user_id=current_user.id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
