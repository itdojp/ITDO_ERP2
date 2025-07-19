"""Notification API endpoints."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.notification import (
    BulkNotificationCreate,
    NotificationCreate,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
    NotificationQueueCreate,
    NotificationResponse,
    NotificationUpdateRequest,
)
from app.services.notification import NotificationService

router = APIRouter()


@router.post("/", response_model=NotificationResponse)
async def create_notification(
    notification_data: NotificationCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationResponse:
    """Create a new notification."""
    service = NotificationService(db)
    
    try:
        notification = await service.create_notification(
            notification_data=notification_data,
            created_by=current_user.id,
            background_tasks=background_tasks,
        )
        return notification
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk", response_model=Dict[str, Any])
async def create_bulk_notifications(
    bulk_data: BulkNotificationCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Create multiple notifications in bulk."""
    service = NotificationService(db)
    
    try:
        result = await service.create_bulk_notifications(
            bulk_data=bulk_data,
            created_by=current_user.id,
            background_tasks=background_tasks,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[NotificationResponse])
async def get_user_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    channel: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[NotificationResponse]:
    """Get user's notifications with filtering."""
    service = NotificationService(db)
    
    try:
        notifications = await service.get_user_notifications(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            unread_only=unread_only,
            channel=channel,
        )
        return notifications
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Mark a notification as read."""
    service = NotificationService(db)
    
    try:
        await service.mark_as_read(
            notification_id=notification_id,
            user_id=current_user.id,
        )
        return {"message": "Notification marked as read"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Mark all user notifications as read."""
    service = NotificationService(db)
    
    try:
        count = await service.mark_all_as_read(user_id=current_user.id)
        return {"message": f"Marked {count} notifications as read"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Delete a notification."""
    service = NotificationService(db)
    
    try:
        await service.delete_notification(
            notification_id=notification_id,
            user_id=current_user.id,
        )
        return {"message": "Notification deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationPreferencesResponse:
    """Get user's notification preferences."""
    service = NotificationService(db)
    
    try:
        preferences = await service.get_user_preferences(user_id=current_user.id)
        return preferences
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/preferences", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    preferences_data: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationPreferencesResponse:
    """Update user's notification preferences."""
    service = NotificationService(db)
    
    try:
        preferences = await service.update_user_preferences(
            user_id=current_user.id,
            preferences_data=preferences_data,
        )
        return preferences
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/queue", response_model=Dict[str, str])
async def add_to_notification_queue(
    queue_data: NotificationQueueCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Add notification to processing queue."""
    service = NotificationService(db)
    
    try:
        await service.add_to_queue(
            queue_data=queue_data,
            created_by=current_user.id,
        )
        return {"message": "Notification added to queue successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=Dict[str, Any])
async def get_notification_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get user's notification statistics."""
    service = NotificationService(db)
    
    try:
        stats = await service.get_notification_stats(user_id=current_user.id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))