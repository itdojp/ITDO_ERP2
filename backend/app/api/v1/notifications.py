"""Notification API endpoints for multi-channel notification system."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.notification import (
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
)
from app.models.user import User
from app.services.notification_service import (
    NotificationService,
    NotificationTemplateService,
    NotificationPreferenceService,
    NotificationQueueService,
    check_notification_health,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


# Pydantic schemas
class NotificationTemplateCreate(BaseModel):
    name: str = Field(..., max_length=100)
    template_key: str = Field(..., max_length=100)
    description: Optional[str] = None
    category: str = Field(..., max_length=50)
    channel: NotificationChannel
    subject_template: Optional[str] = None
    content_template: str
    html_template: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    default_priority: NotificationPriority = NotificationPriority.MEDIUM
    is_active: bool = True


class NotificationTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    subject_template: Optional[str] = None
    content_template: Optional[str] = None
    html_template: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    default_priority: Optional[NotificationPriority] = None
    is_active: Optional[bool] = None


class NotificationTemplateResponse(BaseModel):
    id: int
    name: str
    template_key: str
    description: Optional[str]
    category: str
    channel: NotificationChannel
    subject_template: Optional[str]
    content_template: str
    html_template: Optional[str]
    variables: Optional[Dict[str, Any]]
    validation_rules: Optional[Dict[str, Any]]
    default_priority: NotificationPriority
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class NotificationSend(BaseModel):
    template_key: str
    recipient_user_id: Optional[int] = None
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    priority: NotificationPriority = NotificationPriority.MEDIUM
    scheduled_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class NotificationBatchSend(BaseModel):
    template_key: str
    recipients: List[Dict[str, Any]]
    variables: Optional[Dict[str, Any]] = None
    priority: NotificationPriority = NotificationPriority.MEDIUM
    scheduled_at: Optional[datetime] = None


class NotificationResponse(BaseModel):
    id: int
    external_id: Optional[str]
    batch_id: Optional[str]
    channel: NotificationChannel
    priority: NotificationPriority
    subject: Optional[str]
    content: str
    html_content: Optional[str]
    status: NotificationStatus
    recipient_user_id: Optional[int]
    recipient_email: Optional[str]
    recipient_phone: Optional[str]
    provider: Optional[str]
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    opened_at: Optional[datetime]
    clicked_at: Optional[datetime]
    retry_count: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class NotificationPreferenceUpdate(BaseModel):
    category: str
    channel: NotificationChannel
    enabled: bool
    frequency: str = "immediate"
    contact_info: Optional[Dict[str, str]] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    timezone: str = "UTC"


class NotificationPreferenceResponse(BaseModel):
    id: int
    category: str
    channel: NotificationChannel
    enabled: bool
    frequency: str
    contact_info: Optional[Dict[str, str]]
    quiet_hours_start: Optional[str]
    quiet_hours_end: Optional[str]
    timezone: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Template endpoints
@router.post("/templates", response_model=NotificationTemplateResponse)
async def create_template(
    template_data: NotificationTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new notification template."""
    service = NotificationTemplateService(db)
    
    template = await service.create_template(
        name=template_data.name,
        template_key=template_data.template_key,
        channel=template_data.channel,
        content_template=template_data.content_template,
        category=template_data.category,
        description=template_data.description,
        subject_template=template_data.subject_template,
        html_template=template_data.html_template,
        variables=template_data.variables,
        validation_rules=template_data.validation_rules,
        default_priority=template_data.default_priority,
        is_active=template_data.is_active,
        organization_id=current_user.organization_id,
        created_by=current_user.id
    )
    
    return template


@router.get("/templates", response_model=List[NotificationTemplateResponse])
async def list_templates(
    category: Optional[str] = Query(None),
    channel: Optional[NotificationChannel] = Query(None),
    active_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List notification templates."""
    service = NotificationTemplateService(db)
    
    if category:
        templates = await service.list_by_category(
            category=category,
            organization_id=current_user.organization_id,
            channel=channel
        )
    else:
        filters = {}
        if active_only:
            filters["is_active"] = True
        if channel:
            filters["channel"] = channel
        
        templates = await service.get_multi(
            skip=skip,
            limit=limit,
            filters=filters,
            organization_id=current_user.organization_id
        )
    
    return templates


@router.get("/templates/{template_id}", response_model=NotificationTemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific notification template."""
    service = NotificationTemplateService(db)
    
    template = await service.get_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check access permissions
    if template.organization_id and template.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return template


@router.put("/templates/{template_id}", response_model=NotificationTemplateResponse)
async def update_template(
    template_id: int,
    template_data: NotificationTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a notification template."""
    service = NotificationTemplateService(db)
    
    template = await service.get_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check permissions
    if template.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if template.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify system templates"
        )
    
    # Update template
    update_data = template_data.dict(exclude_unset=True)
    updated_template = await service.update(template_id, update_data)
    
    return updated_template


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a notification template."""
    service = NotificationTemplateService(db)
    
    template = await service.get_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check permissions
    if template.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if template.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete system templates"
        )
    
    await service.delete(template_id)
    return {"message": "Template deleted successfully"}


# Notification sending endpoints
@router.post("/send", response_model=NotificationResponse)
async def send_notification(
    notification_data: NotificationSend,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a single notification."""
    service = NotificationService(db)
    
    try:
        notification = await service.send_notification(
            template_key=notification_data.template_key,
            recipient_user_id=notification_data.recipient_user_id,
            recipient_email=notification_data.recipient_email,
            recipient_phone=notification_data.recipient_phone,
            variables=notification_data.variables,
            priority=notification_data.priority,
            scheduled_at=notification_data.scheduled_at,
            organization_id=current_user.organization_id,
            created_by=current_user.id,
            metadata=notification_data.metadata
        )
        
        return notification
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/send-batch")
async def send_batch_notification(
    batch_data: NotificationBatchSend,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send batch notifications."""
    service = NotificationService(db)
    
    try:
        batch_id = await service.send_batch_notification(
            template_key=batch_data.template_key,
            recipients=batch_data.recipients,
            variables=batch_data.variables,
            priority=batch_data.priority,
            scheduled_at=batch_data.scheduled_at,
            organization_id=current_user.organization_id,
            created_by=current_user.id
        )
        
        return {"batch_id": batch_id, "message": f"Batch queued with {len(batch_data.recipients)} recipients"}
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# User notification endpoints
@router.get("/my-notifications", response_model=List[NotificationResponse])
async def get_my_notifications(
    unread_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's notifications."""
    service = NotificationService(db)
    
    notifications = await service.get_user_notifications(
        user_id=current_user.id,
        limit=limit,
        offset=skip,
        unread_only=unread_only,
        organization_id=current_user.organization_id
    )
    
    return notifications


@router.post("/my-notifications/{notification_id}/mark-opened")
async def mark_notification_opened(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark notification as opened."""
    service = NotificationService(db)
    
    success = await service.mark_as_opened(notification_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return {"message": "Notification marked as opened"}


# Preference endpoints
@router.get("/preferences", response_model=List[NotificationPreferenceResponse])
async def get_my_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's notification preferences."""
    service = NotificationPreferenceService(db)
    
    preferences = await service.get_user_preferences(
        user_id=current_user.id,
        organization_id=current_user.organization_id
    )
    
    return preferences


@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_preference(
    preference_data: NotificationPreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update notification preference."""
    service = NotificationPreferenceService(db)
    
    preference = await service.update_preference(
        user_id=current_user.id,
        category=preference_data.category,
        channel=preference_data.channel,
        enabled=preference_data.enabled,
        frequency=preference_data.frequency,
        contact_info=preference_data.contact_info,
        organization_id=current_user.organization_id
    )
    
    return preference


# Admin endpoints
@router.get("/admin/notifications", response_model=List[NotificationResponse])
async def list_all_notifications(
    status: Optional[NotificationStatus] = Query(None),
    channel: Optional[NotificationChannel] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all notifications (admin only)."""
    # Check admin permissions (would need to implement admin role check)
    service = NotificationService(db)
    
    filters = {}
    if status:
        filters["status"] = status
    if channel:
        filters["channel"] = channel
    
    notifications = await service.get_multi(
        skip=skip,
        limit=limit,
        filters=filters,
        organization_id=current_user.organization_id
    )
    
    return notifications


@router.get("/admin/queue")
async def get_notification_queue(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notification queue status (admin only)."""
    service = NotificationQueueService(db)
    
    pending_batches = await service.get_pending_batches(limit=limit)
    
    return {
        "pending_batches": len(pending_batches),
        "batches": [
            {
                "batch_id": batch.batch_id,
                "template_key": batch.template_key,
                "recipient_count": batch.total_recipients,
                "scheduled_at": batch.scheduled_at,
                "status": batch.status
            }
            for batch in pending_batches
        ]
    }


@router.post("/admin/queue/{batch_id}/process")
async def process_batch(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process a specific batch (admin only)."""
    service = NotificationQueueService(db)
    
    try:
        stats = await service.process_batch(batch_id)
        return {
            "batch_id": batch_id,
            "processed": True,
            "stats": stats
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/health")
async def notification_health():
    """Check notification system health."""
    health_info = await check_notification_health()
    
    if health_info["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_info
        )
    
    return health_info