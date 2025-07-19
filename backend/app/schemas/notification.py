"""Notification schemas for API requests and responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.models.notification import (
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)

# Request schemas


class NotificationCreate(BaseModel):
    """Schema for creating a new notification."""

    title: str = Field(
        ..., min_length=1, max_length=255, description="Notification title"
    )
    message: str = Field(..., min_length=1, description="Notification message content")
    notification_type: NotificationType = Field(..., description="Type of notification")

    user_id: int = Field(..., gt=0, description="Target user ID")
    organization_id: Optional[int] = Field(None, gt=0, description="Organization ID")
    sender_id: Optional[int] = Field(None, gt=0, description="Sender user ID")

    channels: List[NotificationChannel] = Field(
        default=[NotificationChannel.IN_APP],
        description="Delivery channels for the notification",
    )
    priority: int = Field(
        default=5, ge=1, le=10, description="Notification priority (1-10)"
    )

    action_url: Optional[str] = Field(
        None, max_length=500, description="Action URL for notification"
    )
    action_text: Optional[str] = Field(
        None, max_length=100, description="Action button text"
    )
    extra_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    scheduled_for: Optional[datetime] = Field(
        None, description="Schedule notification for future delivery"
    )
    expires_at: Optional[datetime] = Field(
        None, description="Notification expiration time"
    )

    @validator("channels")
    def validate_channels(
        cls, v: List[NotificationChannel]
    ) -> List[NotificationChannel]:
        """Validate channels list is not empty."""
        if not v:
            raise ValueError("At least one delivery channel must be specified")
        return v

    @validator("expires_at")
    def validate_expiration(
        cls, v: Optional[datetime], values: Dict[str, Any]
    ) -> Optional[datetime]:
        """Validate expiration is in the future."""
        if v and v <= datetime.utcnow():
            raise ValueError("Expiration time must be in the future")

        # Check that expiration is after scheduled time
        if v and values.get("scheduled_for") and v <= values["scheduled_for"]:
            raise ValueError("Expiration time must be after scheduled time")

        return v


class NotificationUpdate(BaseModel):
    """Schema for updating notification."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    message: Optional[str] = Field(None, min_length=1)
    notification_type: Optional[NotificationType] = None

    priority: Optional[int] = Field(None, ge=1, le=10)
    action_url: Optional[str] = Field(None, max_length=500)
    action_text: Optional[str] = Field(None, max_length=100)
    extra_metadata: Optional[Dict[str, Any]] = None

    scheduled_for: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class NotificationMarkRead(BaseModel):
    """Schema for marking notifications as read."""

    notification_ids: List[int] = Field(
        description="List of notification IDs to mark as read", min_length=1
    )


class NotificationPreferencesUpdate(BaseModel):
    """Schema for updating notification preferences."""

    email_enabled: Optional[bool] = None
    email_digest: Optional[bool] = None
    email_frequency: Optional[str] = Field(None, pattern="^(immediate|hourly|daily)$")

    in_app_enabled: Optional[bool] = None
    desktop_notifications: Optional[bool] = None

    notification_types: Optional[Dict[str, bool]] = None
    channel_preferences: Optional[Dict[str, List[str]]] = None

    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = Field(
        None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"
    )
    quiet_hours_end: Optional[str] = Field(
        None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"
    )


class WebhookEndpointCreate(BaseModel):
    """Schema for creating webhook endpoint."""

    name: str = Field(
        ..., min_length=1, max_length=100, description="Webhook endpoint name"
    )
    url: str = Field(..., min_length=1, max_length=500, description="Webhook URL")
    secret: Optional[str] = Field(
        None, max_length=255, description="Secret for HMAC signing"
    )

    organization_id: Optional[int] = Field(None, gt=0)

    notification_types: List[NotificationType] = Field(
        default_factory=list, description="Notification types to send to this webhook"
    )
    event_filters: Dict[str, Any] = Field(
        default_factory=dict, description="Event filtering rules"
    )

    headers: Dict[str, str] = Field(
        default_factory=dict, description="Additional HTTP headers"
    )
    timeout_seconds: int = Field(
        default=30, ge=5, le=300, description="Request timeout in seconds"
    )


class WebhookEndpointUpdate(BaseModel):
    """Schema for updating webhook endpoint."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    url: Optional[str] = Field(None, min_length=1, max_length=500)
    secret: Optional[str] = Field(None, max_length=255)

    notification_types: Optional[List[NotificationType]] = None
    event_filters: Optional[Dict[str, Any]] = None

    is_active: Optional[bool] = None
    headers: Optional[Dict[str, str]] = None
    timeout_seconds: Optional[int] = Field(None, ge=5, le=300)


class BulkNotificationCreate(BaseModel):
    """Schema for creating bulk notifications."""

    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    notification_type: NotificationType

    user_ids: List[int] = Field(..., min_items=1, description="List of target user IDs")
    organization_id: Optional[int] = Field(None, gt=0)

    channels: List[NotificationChannel] = Field(default=[NotificationChannel.IN_APP])
    priority: int = Field(default=5, ge=1, le=10)

    action_url: Optional[str] = Field(None, max_length=500)
    action_text: Optional[str] = Field(None, max_length=100)
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)

    scheduled_for: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class NotificationQueueCreate(BaseModel):
    """Schema for creating notification queue item."""

    user_id: int = Field(..., gt=0, description="Target user ID")
    channel: NotificationChannel = Field(..., description="Delivery channel")
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)

    template_name: Optional[str] = Field(None, max_length=100)
    template_data: Dict[str, Any] = Field(default_factory=dict)
    recipient_email: Optional[str] = Field(None, max_length=255)

    priority: int = Field(default=5, ge=1, le=10)
    organization_id: Optional[int] = Field(None, gt=0)


# Response schemas


class NotificationResponse(BaseModel):
    """Schema for notification response."""

    id: int
    title: str
    message: str
    notification_type: NotificationType

    user_id: int
    organization_id: Optional[int]
    sender_id: Optional[int]

    channels: List[NotificationChannel]
    priority: int
    status: NotificationStatus

    is_read: bool
    read_at: Optional[datetime]

    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    failed_at: Optional[datetime]

    action_url: Optional[str]
    action_text: Optional[str]
    extra_metadata: Dict[str, Any]

    scheduled_for: Optional[datetime]
    expires_at: Optional[datetime]

    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Schema for notification list response."""

    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    skip: int
    limit: int


class NotificationPreferencesResponse(BaseModel):
    """Schema for notification preferences response."""

    id: int
    user_id: int
    organization_id: Optional[int]

    email_enabled: bool
    email_digest: bool
    email_frequency: str

    in_app_enabled: bool
    desktop_notifications: bool

    notification_types: Dict[str, bool]
    channel_preferences: Dict[str, List[str]]

    quiet_hours_enabled: bool
    quiet_hours_start: Optional[str]
    quiet_hours_end: Optional[str]

    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class WebhookEndpointResponse(BaseModel):
    """Schema for webhook endpoint response."""

    id: int
    name: str
    url: str

    organization_id: Optional[int]
    created_by: int

    notification_types: List[NotificationType]
    event_filters: Dict[str, Any]

    is_active: bool
    headers: Dict[str, str]
    timeout_seconds: int

    success_count: int
    failure_count: int
    success_rate: float
    last_success_at: Optional[datetime]
    last_failure_at: Optional[datetime]

    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class NotificationStatisticsResponse(BaseModel):
    """Schema for notification statistics response."""

    total_notifications: int
    unread_count: int
    read_count: int

    notifications_by_type: Dict[str, int]
    notifications_by_channel: Dict[str, int]
    notifications_by_status: Dict[str, int]

    delivery_rate: float
    average_read_time: Optional[float]  # Minutes

    recent_activity: List[Dict[str, Any]]


class BulkNotificationResponse(BaseModel):
    """Schema for bulk notification creation response."""

    total_created: int
    notification_ids: List[int]
    failed_users: List[Dict[str, Any]]
    batch_id: Optional[str]


class NotificationQueueResponse(BaseModel):
    """Schema for notification queue status response."""

    id: int
    notification_id: int
    channel: NotificationChannel
    recipient: str

    status: NotificationStatus
    attempts: int
    max_attempts: int

    scheduled_for: Optional[datetime]
    next_retry_at: Optional[datetime]

    last_error: Optional[str]
    delivery_response: Optional[Dict[str, Any]]

    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


class NotificationTemplateResponse(BaseModel):
    """Schema for notification template response."""

    id: str
    name: str
    description: str

    template_type: NotificationType
    default_channels: List[NotificationChannel]

    title_template: str
    message_template: str

    required_variables: List[str]
    optional_variables: List[str]

    example_data: Dict[str, Any]


class NotificationHealthResponse(BaseModel):
    """Schema for notification service health response."""

    status: str
    service: str
    version: str

    queue_status: Dict[str, Any]
    delivery_stats: Dict[str, Any]
    error_rate: float

    features: List[str]
    integrations: Dict[str, bool]


# Utility schemas


class NotificationFilter(BaseModel):
    """Schema for filtering notifications."""

    notification_type: Optional[NotificationType] = None
    status: Optional[NotificationStatus] = None
    is_read: Optional[bool] = None
    channel: Optional[NotificationChannel] = None

    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

    priority_min: Optional[int] = Field(None, ge=1, le=10)
    priority_max: Optional[int] = Field(None, ge=1, le=10)

    sender_id: Optional[int] = None
    organization_id: Optional[int] = None


class NotificationSort(BaseModel):
    """Schema for sorting notifications."""

    sort_by: str = Field(
        default="created_at", regex="^(created_at|priority|status|notification_type)$"
    )
    sort_order: str = Field(default="desc", regex="^(asc|desc)$")


# Email-specific schemas


class EmailNotificationData(BaseModel):
    """Schema for email notification data."""

    to_email: str = Field(
        ..., regex=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    subject: str = Field(..., min_length=1, max_length=255)
    html_content: str = Field(..., min_length=1)
    text_content: Optional[str] = None

    from_email: Optional[str] = None
    from_name: Optional[str] = None

    reply_to: Optional[str] = None
    attachments: List[Dict[str, Any]] = Field(default_factory=list)

    template_id: Optional[str] = None
    template_data: Dict[str, Any] = Field(default_factory=dict)


class EmailDeliveryResponse(BaseModel):
    """Schema for email delivery response."""

    message_id: str
    status: str
    recipient: str

    sent_at: datetime
    delivered_at: Optional[datetime]

    delivery_status: Dict[str, Any]
    error_message: Optional[str]


# Webhook-specific schemas


class WebhookPayload(BaseModel):
    """Schema for webhook notification payload."""

    event_type: str
    event_id: str
    timestamp: datetime

    notification: NotificationResponse
    organization_id: Optional[int]

    additional_data: Dict[str, Any] = Field(default_factory=dict)


class WebhookDeliveryResponse(BaseModel):
    """Schema for webhook delivery response."""

    webhook_id: int
    notification_id: int

    status_code: int
    response_body: str
    response_headers: Dict[str, str]

    delivery_time_ms: int
    success: bool
    error_message: Optional[str]

    delivered_at: datetime
