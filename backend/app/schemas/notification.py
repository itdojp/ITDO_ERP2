"""Notification schema definitions.

This module provides Pydantic schemas for notification-related API operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.models.notification import (
    NotificationChannel,
    NotificationPriority,
    NotificationType,
)


class NotificationBase(BaseModel):
    """Base notification schema."""

    title: str = Field(..., max_length=255, description="Notification title")
    message: str = Field(..., description="Notification message content")
    type: NotificationType = Field(default=NotificationType.INFO, description="Notification type")
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL, description="Notification priority")
    action_url: Optional[str] = Field(None, max_length=500, description="Optional action URL")
    icon: Optional[str] = Field(None, max_length=100, description="Icon identifier")
    category: Optional[str] = Field(None, max_length=50, description="Notification category")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")


class NotificationCreate(NotificationBase):
    """Schema for creating notifications."""

    user_id: int = Field(..., description="Target user ID")
    organization_id: Optional[int] = Field(None, description="Organization context")


class NotificationUpdate(BaseModel):
    """Schema for updating notifications."""

    is_read: Optional[bool] = Field(None, description="Read status")
    title: Optional[str] = Field(None, max_length=255, description="Notification title")
    message: Optional[str] = Field(None, description="Notification message")
    action_url: Optional[str] = Field(None, max_length=500, description="Action URL")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")


class NotificationResponse(NotificationBase):
    """Schema for notification responses."""

    id: int
    user_id: int
    organization_id: Optional[int]
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Schema for paginated notification lists."""

    items: List[NotificationResponse]
    total: int = Field(..., description="Total number of notifications")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    unread_count: int = Field(..., description="Number of unread notifications")


class NotificationMarkReadRequest(BaseModel):
    """Schema for marking notifications as read."""

    notification_ids: List[int] = Field(..., description="List of notification IDs to mark as read")


class NotificationPreferenceBase(BaseModel):
    """Base notification preference schema."""

    email_enabled: bool = Field(default=True, description="Email notifications enabled")
    push_enabled: bool = Field(default=True, description="Push notifications enabled")
    in_app_enabled: bool = Field(default=True, description="In-app notifications enabled")
    category_preferences: Optional[Dict[str, Dict[str, bool]]] = Field(
        None, description="Category-specific channel preferences"
    )
    email_digest_frequency: str = Field(
        default="daily",
        description="Email digest frequency: immediate, hourly, daily, weekly, never"
    )
    quiet_hours_start: Optional[str] = Field(None, regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", description="Quiet hours start time (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", description="Quiet hours end time (HH:MM)")
    timezone: str = Field(default="UTC", max_length=50, description="User timezone")

    @validator("email_digest_frequency")
    def validate_digest_frequency(cls, v):
        allowed = ["immediate", "hourly", "daily", "weekly", "never"]
        if v not in allowed:
            raise ValueError(f"Invalid digest frequency. Must be one of: {allowed}")
        return v


class NotificationPreferenceCreate(NotificationPreferenceBase):
    """Schema for creating notification preferences."""
    pass


class NotificationPreferenceUpdate(BaseModel):
    """Schema for updating notification preferences."""

    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    category_preferences: Optional[Dict[str, Dict[str, bool]]] = None
    email_digest_frequency: Optional[str] = None
    quiet_hours_start: Optional[str] = Field(None, regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: Optional[str] = Field(None, regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    timezone: Optional[str] = None

    @validator("email_digest_frequency")
    def validate_digest_frequency(cls, v):
        if v is not None:
            allowed = ["immediate", "hourly", "daily", "weekly", "never"]
            if v not in allowed:
                raise ValueError(f"Invalid digest frequency. Must be one of: {allowed}")
        return v


class NotificationPreferenceResponse(NotificationPreferenceBase):
    """Schema for notification preference responses."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationQueueCreate(BaseModel):
    """Schema for adding notifications to queue."""

    user_id: int = Field(..., description="Target user ID")
    channel: NotificationChannel = Field(..., description="Delivery channel")
    title: str = Field(..., max_length=255, description="Notification title")
    message: str = Field(..., description="Notification message")
    template_name: Optional[str] = Field(None, max_length=100, description="Template name")
    template_data: Optional[Dict[str, Any]] = Field(None, description="Template data")
    recipient_email: Optional[str] = Field(None, max_length=255, description="Recipient email")
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL, description="Priority")
    organization_id: Optional[int] = Field(None, description="Organization context")


class NotificationQueueResponse(BaseModel):
    """Schema for notification queue responses."""

    id: int
    user_id: int
    channel: NotificationChannel
    title: str
    message: str
    template_name: Optional[str]
    recipient_email: Optional[str]
    priority: NotificationPriority
    status: str
    attempts: int
    max_attempts: int
    next_attempt_at: Optional[datetime]
    sent_at: Optional[datetime]
    error_message: Optional[str]
    organization_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebhookEndpointBase(BaseModel):
    """Base webhook endpoint schema."""

    name: str = Field(..., max_length=100, description="Endpoint name")
    url: str = Field(..., max_length=500, description="Webhook URL")
    secret: Optional[str] = Field(None, max_length=100, description="Webhook secret")
    event_types: Optional[List[str]] = Field(None, description="Subscribed event types")
    active: bool = Field(default=True, description="Whether endpoint is active")


class WebhookEndpointCreate(WebhookEndpointBase):
    """Schema for creating webhook endpoints."""

    organization_id: int = Field(..., description="Organization ID")


class WebhookEndpointUpdate(BaseModel):
    """Schema for updating webhook endpoints."""

    name: Optional[str] = Field(None, max_length=100)
    url: Optional[str] = Field(None, max_length=500)
    secret: Optional[str] = Field(None, max_length=100)
    event_types: Optional[List[str]] = None
    active: Optional[bool] = None


class WebhookEndpointResponse(WebhookEndpointBase):
    """Schema for webhook endpoint responses."""

    id: int
    organization_id: int
    last_success_at: Optional[datetime]
    last_failure_at: Optional[datetime]
    failure_count: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationStatsResponse(BaseModel):
    """Schema for notification statistics."""

    total_notifications: int = Field(..., description="Total notifications")
    unread_notifications: int = Field(..., description="Unread notifications")
    notifications_by_type: Dict[str, int] = Field(..., description="Notifications by type")
    notifications_by_priority: Dict[str, int] = Field(..., description="Notifications by priority")
    notifications_by_category: Dict[str, int] = Field(..., description="Notifications by category")
    recent_activity: List[NotificationResponse] = Field(..., description="Recent notifications")


class BulkNotificationCreate(BaseModel):
    """Schema for creating bulk notifications."""

    user_ids: List[int] = Field(..., description="Target user IDs")
    title: str = Field(..., max_length=255, description="Notification title")
    message: str = Field(..., description="Notification message")
    type: NotificationType = Field(default=NotificationType.INFO, description="Notification type")
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL, description="Priority")
    action_url: Optional[str] = Field(None, max_length=500, description="Action URL")
    icon: Optional[str] = Field(None, max_length=100, description="Icon")
    category: Optional[str] = Field(None, max_length=50, description="Category")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata")
    expires_at: Optional[datetime] = Field(None, description="Expiration")
    organization_id: Optional[int] = Field(None, description="Organization context")
    channels: List[NotificationChannel] = Field(default=[NotificationChannel.IN_APP], description="Delivery channels")


class BulkNotificationResponse(BaseModel):
    """Schema for bulk notification responses."""

    created_count: int = Field(..., description="Number of notifications created")
    queued_count: int = Field(..., description="Number of notifications queued")
    failed_count: int = Field(..., description="Number of failures")
    errors: List[str] = Field(default=[], description="Error messages")


# Export all notification schemas
__all__ = [
    "NotificationBase",
    "NotificationCreate",
    "NotificationUpdate",
    "NotificationResponse",
    "NotificationListResponse",
    "NotificationMarkReadRequest",
    "NotificationPreferenceBase",
    "NotificationPreferenceCreate",
    "NotificationPreferenceUpdate",
    "NotificationPreferenceResponse",
    "NotificationQueueCreate",
    "NotificationQueueResponse",
    "WebhookEndpointBase",
    "WebhookEndpointCreate",
    "WebhookEndpointUpdate",
    "WebhookEndpointResponse",
    "NotificationStatsResponse",
    "BulkNotificationCreate",
    "BulkNotificationResponse",
]
