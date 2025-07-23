"""
Notification System Schemas - CC02 v31.0 Phase 2

Comprehensive Pydantic schemas for notification system including:
- Multi-Channel Notifications (Email, SMS, Push, In-App)
- Real-Time Notifications & WebSocket Support
- Template-Based Messaging
- Notification Preferences & Settings
- Delivery Tracking & Analytics
- Subscription Management
- Event-Driven Notifications
- Notification History & Audit
- Rich Content & Attachments
- Integration & Webhook Support
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from app.models.notification_extended import (
    NotificationType,
    NotificationChannel,
    NotificationStatus,
    NotificationPriority,
    SubscriptionStatus,
    DeliveryStatus,
)


# =============================================================================
# Base Schemas
# =============================================================================

class BaseNotificationSchema(BaseModel):
    """Base schema for notification-related models."""
    
    class Config:
        orm_mode = True
        use_enum_values = True


# =============================================================================
# Notification Schemas
# =============================================================================

class NotificationCreateRequest(BaseNotificationSchema):
    """Schema for creating a new notification."""
    
    organization_id: str = Field(..., description="Organization ID")
    title: str = Field(..., min_length=1, max_length=500, description="Notification title")
    message: str = Field(..., min_length=1, description="Notification message")
    summary: Optional[str] = Field(None, max_length=500, description="Brief summary")
    
    # Classification
    notification_type: NotificationType = Field(..., description="Type of notification")
    category: Optional[str] = Field(None, max_length=100, description="Category")
    subcategory: Optional[str] = Field(None, max_length=100, description="Subcategory")
    priority: NotificationPriority = Field(NotificationPriority.NORMAL, description="Priority level")
    
    # Recipients
    recipient_user_id: Optional[str] = Field(None, description="Target user ID")
    recipient_email: Optional[str] = Field(None, max_length=200, description="Recipient email")
    recipient_phone: Optional[str] = Field(None, max_length=50, description="Recipient phone")
    recipient_groups: List[str] = Field(default_factory=list, description="Target groups")
    recipient_roles: List[str] = Field(default_factory=list, description="Target roles")
    
    # Targeting
    target_audience: Dict[str, Any] = Field(default_factory=dict, description="Audience targeting")
    audience_filter: Dict[str, Any] = Field(default_factory=dict, description="Audience filters")
    geographic_targeting: List[str] = Field(default_factory=list, description="Geographic targets")
    demographic_targeting: Dict[str, Any] = Field(default_factory=dict, description="Demographic targeting")
    
    # Content
    content_html: Optional[str] = Field(None, description="HTML content")
    content_plain: Optional[str] = Field(None, description="Plain text content")
    content_markdown: Optional[str] = Field(None, description="Markdown content")
    rich_content: Dict[str, Any] = Field(default_factory=dict, description="Rich content data")
    attachments: List[Dict[str, Any]] = Field(default_factory=list, description="Attachments")
    
    # Delivery
    channels: List[str] = Field(default_factory=lambda: ["in_app"], description="Delivery channels")
    primary_channel: NotificationChannel = Field(NotificationChannel.IN_APP, description="Primary channel")
    fallback_channels: List[str] = Field(default_factory=list, description="Fallback channels")
    
    # Scheduling
    send_at: Optional[datetime] = Field(None, description="Scheduled send time")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled for processing")
    expires_at: Optional[datetime] = Field(None, description="Expiration time")
    timezone: Optional[str] = Field(None, max_length=50, description="Timezone")
    
    # Template
    template_id: Optional[str] = Field(None, description="Template ID")
    template_variables: Dict[str, Any] = Field(default_factory=dict, description="Template variables")
    personalization_data: Dict[str, Any] = Field(default_factory=dict, description="Personalization data")
    
    # Source
    source_system: Optional[str] = Field(None, max_length=100, description="Source system")
    source_event: Optional[str] = Field(None, max_length=200, description="Source event")
    source_entity_type: Optional[str] = Field(None, max_length=100, description="Source entity type")
    source_entity_id: Optional[str] = Field(None, max_length=200, description="Source entity ID")
    context_data: Dict[str, Any] = Field(default_factory=dict, description="Context data")
    
    # Interaction
    action_buttons: List[Dict[str, Any]] = Field(default_factory=list, description="Action buttons")
    deep_link_url: Optional[str] = Field(None, max_length=1000, description="Deep link URL")
    tracking_params: Dict[str, Any] = Field(default_factory=dict, description="Tracking parameters")
    
    # A/B Testing
    ab_test_group: Optional[str] = Field(None, max_length=50, description="A/B test group")
    ab_test_variant: Optional[str] = Field(None, max_length=50, description="A/B test variant")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom fields")
    created_by: Optional[str] = Field(None, description="Creator user ID")

    @validator('channels')
    def validate_channels(cls, v):
        """Validate channels list."""
        if not v:
            return ["in_app"]
        valid_channels = [channel.value for channel in NotificationChannel]
        for channel in v:
            if channel not in valid_channels:
                raise ValueError(f"Invalid channel: {channel}")
        return v


class NotificationUpdateRequest(BaseNotificationSchema):
    """Schema for updating a notification."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="Notification title")
    message: Optional[str] = Field(None, min_length=1, description="Notification message")
    summary: Optional[str] = Field(None, max_length=500, description="Brief summary")
    category: Optional[str] = Field(None, max_length=100, description="Category")
    subcategory: Optional[str] = Field(None, max_length=100, description="Subcategory")
    priority: Optional[NotificationPriority] = Field(None, description="Priority level")
    content_html: Optional[str] = Field(None, description="HTML content")
    content_plain: Optional[str] = Field(None, description="Plain text content")
    rich_content: Optional[Dict[str, Any]] = Field(None, description="Rich content data")
    tags: Optional[List[str]] = Field(None, description="Tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class NotificationResponse(BaseNotificationSchema):
    """Schema for notification response."""
    
    id: str = Field(..., description="Notification ID")
    organization_id: str = Field(..., description="Organization ID")
    notification_number: str = Field(..., description="Notification number")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    summary: Optional[str] = Field(None, description="Brief summary")
    
    # Classification
    notification_type: NotificationType = Field(..., description="Type of notification")
    category: Optional[str] = Field(None, description="Category")
    subcategory: Optional[str] = Field(None, description="Subcategory")
    priority: NotificationPriority = Field(..., description="Priority level")
    
    # Recipients
    recipient_user_id: Optional[str] = Field(None, description="Target user ID")
    recipient_email: Optional[str] = Field(None, description="Recipient email")
    recipient_phone: Optional[str] = Field(None, description="Recipient phone")
    
    # Status
    status: NotificationStatus = Field(..., description="Notification status")
    is_read: bool = Field(..., description="Read status")
    read_at: Optional[datetime] = Field(None, description="Read timestamp")
    is_archived: bool = Field(..., description="Archive status")
    archived_at: Optional[datetime] = Field(None, description="Archive timestamp")
    
    # Delivery
    channels: List[str] = Field(..., description="Delivery channels")
    primary_channel: NotificationChannel = Field(..., description="Primary channel")
    delivery_attempts: int = Field(..., description="Delivery attempts")
    
    # Analytics
    view_count: int = Field(..., description="View count")
    click_count: int = Field(..., description="Click count")
    action_count: int = Field(..., description="Action count")
    
    # Timing
    send_at: Optional[datetime] = Field(None, description="Scheduled send time")
    sent_at: Optional[datetime] = Field(None, description="Sent timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


class NotificationListResponse(BaseNotificationSchema):
    """Schema for notification list response."""
    
    notifications: List[NotificationResponse] = Field(..., description="Notifications")
    total_count: int = Field(..., description="Total count")
    unread_count: int = Field(0, description="Unread count")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Items per page")
    has_more: bool = Field(False, description="Has more items")


# =============================================================================
# Template Schemas
# =============================================================================

class NotificationTemplateCreateRequest(BaseNotificationSchema):
    """Schema for creating a notification template."""
    
    organization_id: str = Field(..., description="Organization ID")
    name: str = Field(..., min_length=1, max_length=200, description="Template name")
    code: str = Field(..., min_length=1, max_length=100, description="Template code")
    description: Optional[str] = Field(None, description="Template description")
    category: Optional[str] = Field(None, max_length=100, description="Template category")
    
    # Content templates
    subject_template: Optional[str] = Field(None, max_length=500, description="Subject template")
    title_template: Optional[str] = Field(None, max_length=500, description="Title template")
    message_template: str = Field(..., description="Message template")
    html_template: Optional[str] = Field(None, description="HTML template")
    plain_template: Optional[str] = Field(None, description="Plain text template")
    
    # Configuration
    notification_type: NotificationType = Field(..., description="Default notification type")
    default_priority: NotificationPriority = Field(NotificationPriority.NORMAL, description="Default priority")
    default_channels: List[str] = Field(default_factory=lambda: ["in_app"], description="Default channels")
    
    # Variables
    variables: List[str] = Field(default_factory=list, description="Available variables")
    required_variables: List[str] = Field(default_factory=list, description="Required variables")
    default_values: Dict[str, Any] = Field(default_factory=dict, description="Default values")
    validation_rules: Dict[str, Any] = Field(default_factory=dict, description="Validation rules")
    
    # Styling
    styling: Dict[str, Any] = Field(default_factory=dict, description="Styling configuration")
    layout: Optional[str] = Field(None, max_length=100, description="Layout")
    theme: Optional[str] = Field(None, max_length=100, description="Theme")
    
    # Localization
    language: str = Field("en", max_length=10, description="Primary language")
    localized_versions: Dict[str, Any] = Field(default_factory=dict, description="Localized versions")
    
    # Access
    owner_id: str = Field(..., description="Owner user ID")
    is_public: bool = Field(False, description="Public template")
    tags: List[str] = Field(default_factory=list, description="Tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_by: str = Field(..., description="Creator user ID")


class NotificationTemplateResponse(BaseNotificationSchema):
    """Schema for notification template response."""
    
    id: str = Field(..., description="Template ID")
    organization_id: str = Field(..., description="Organization ID")
    name: str = Field(..., description="Template name")
    code: str = Field(..., description="Template code")
    description: Optional[str] = Field(None, description="Template description")
    category: Optional[str] = Field(None, description="Template category")
    
    # Template content
    subject_template: Optional[str] = Field(None, description="Subject template")
    title_template: Optional[str] = Field(None, description="Title template")
    message_template: str = Field(..., description="Message template")
    
    # Configuration
    notification_type: NotificationType = Field(..., description="Default notification type")
    default_priority: NotificationPriority = Field(..., description="Default priority")
    default_channels: List[str] = Field(..., description="Default channels")
    
    # Variables
    variables: List[str] = Field(..., description="Available variables")
    required_variables: List[str] = Field(..., description="Required variables")
    
    # Usage
    usage_count: int = Field(..., description="Usage count")
    last_used_at: Optional[datetime] = Field(None, description="Last used timestamp")
    
    # Status
    is_active: bool = Field(..., description="Active status")
    is_public: bool = Field(..., description="Public template")
    
    # Metadata
    tags: List[str] = Field(..., description="Tags")
    language: str = Field(..., description="Primary language")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


class TemplateGenerationRequest(BaseNotificationSchema):
    """Schema for generating notification from template."""
    
    template_id: str = Field(..., description="Template ID")
    field_values: Dict[str, Any] = Field(..., description="Field values for template")
    
    # Override template defaults
    title: Optional[str] = Field(None, description="Override title")
    priority: Optional[NotificationPriority] = Field(None, description="Override priority")
    channels: Optional[List[str]] = Field(None, description="Override channels")
    
    # Recipients
    recipient_user_id: Optional[str] = Field(None, description="Target user ID")
    recipient_email: Optional[str] = Field(None, description="Recipient email")
    recipient_groups: List[str] = Field(default_factory=list, description="Target groups")
    
    # Scheduling
    send_at: Optional[datetime] = Field(None, description="Scheduled send time")
    
    # Context
    context_data: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


# =============================================================================
# Delivery Schemas
# =============================================================================

class NotificationDeliveryResponse(BaseNotificationSchema):
    """Schema for notification delivery response."""
    
    id: str = Field(..., description="Delivery ID")
    notification_id: str = Field(..., description="Notification ID")
    channel: NotificationChannel = Field(..., description="Delivery channel")
    recipient_address: str = Field(..., description="Recipient address")
    status: DeliveryStatus = Field(..., description="Delivery status")
    
    # Timing
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled time")
    sent_at: Optional[datetime] = Field(None, description="Sent time")
    delivered_at: Optional[datetime] = Field(None, description="Delivered time")
    
    # Provider info
    provider: Optional[str] = Field(None, description="Provider name")
    provider_message_id: Optional[str] = Field(None, description="Provider message ID")
    
    # Error info
    error_code: Optional[str] = Field(None, description="Error code")
    error_message: Optional[str] = Field(None, description="Error message")
    retry_count: int = Field(0, description="Retry count")
    
    # Analytics
    opened_at: Optional[datetime] = Field(None, description="Opened time")
    clicked_at: Optional[datetime] = Field(None, description="Clicked time")
    
    # Cost
    delivery_cost: Optional[Decimal] = Field(None, description="Delivery cost")
    cost_currency: str = Field("USD", description="Cost currency")


# =============================================================================
# Preference Schemas
# =============================================================================

class NotificationPreferenceUpdateRequest(BaseNotificationSchema):
    """Schema for updating notification preferences."""
    
    # General preferences
    is_enabled: Optional[bool] = Field(None, description="Global notification enabled")
    global_opt_out: Optional[bool] = Field(None, description="Global opt-out")
    
    # Channel preferences
    email_enabled: Optional[bool] = Field(None, description="Email notifications enabled")
    sms_enabled: Optional[bool] = Field(None, description="SMS notifications enabled")
    push_enabled: Optional[bool] = Field(None, description="Push notifications enabled")
    in_app_enabled: Optional[bool] = Field(None, description="In-app notifications enabled")
    
    # Type-specific preferences
    system_notifications: Optional[bool] = Field(None, description="System notifications")
    alert_notifications: Optional[bool] = Field(None, description="Alert notifications")
    warning_notifications: Optional[bool] = Field(None, description="Warning notifications")
    info_notifications: Optional[bool] = Field(None, description="Info notifications")
    reminder_notifications: Optional[bool] = Field(None, description="Reminder notifications")
    task_notifications: Optional[bool] = Field(None, description="Task notifications")
    message_notifications: Optional[bool] = Field(None, description="Message notifications")
    announcement_notifications: Optional[bool] = Field(None, description="Announcement notifications")
    
    # Timing preferences
    quiet_hours_enabled: Optional[bool] = Field(None, description="Quiet hours enabled")
    quiet_hours_start: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", description="Quiet hours start (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", description="Quiet hours end (HH:MM)")
    timezone: Optional[str] = Field(None, max_length=50, description="User timezone")
    
    # Frequency preferences
    max_emails_per_day: Optional[int] = Field(None, ge=0, le=1000, description="Max emails per day")
    max_sms_per_day: Optional[int] = Field(None, ge=0, le=100, description="Max SMS per day")
    digest_frequency: Optional[str] = Field(None, pattern=r"^(instant|hourly|daily|weekly)$", description="Digest frequency")
    
    # Contact info
    email_address: Optional[str] = Field(None, max_length=200, description="Email address")
    phone_number: Optional[str] = Field(None, max_length=50, description="Phone number")
    
    # Advanced settings
    language_preference: Optional[str] = Field(None, max_length=10, description="Language preference")
    content_format: Optional[str] = Field(None, pattern=r"^(html|plain|markdown)$", description="Content format")
    grouping_enabled: Optional[bool] = Field(None, description="Grouping enabled")


class NotificationPreferenceResponse(BaseNotificationSchema):
    """Schema for notification preference response."""
    
    id: str = Field(..., description="Preference ID")
    user_id: str = Field(..., description="User ID")
    organization_id: str = Field(..., description="Organization ID")
    
    # General preferences
    is_enabled: bool = Field(..., description="Global notification enabled")
    global_opt_out: bool = Field(..., description="Global opt-out")
    
    # Channel preferences
    email_enabled: bool = Field(..., description="Email notifications enabled")
    sms_enabled: bool = Field(..., description="SMS notifications enabled")
    push_enabled: bool = Field(..., description="Push notifications enabled")
    in_app_enabled: bool = Field(..., description="In-app notifications enabled")
    
    # Type-specific preferences
    system_notifications: bool = Field(..., description="System notifications")
    alert_notifications: bool = Field(..., description="Alert notifications")
    warning_notifications: bool = Field(..., description="Warning notifications")
    info_notifications: bool = Field(..., description="Info notifications")
    reminder_notifications: bool = Field(..., description="Reminder notifications")
    task_notifications: bool = Field(..., description="Task notifications")
    message_notifications: bool = Field(..., description="Message notifications")
    announcement_notifications: bool = Field(..., description="Announcement notifications")
    
    # Timing preferences
    quiet_hours_enabled: bool = Field(..., description="Quiet hours enabled")
    quiet_hours_start: Optional[str] = Field(None, description="Quiet hours start")
    quiet_hours_end: Optional[str] = Field(None, description="Quiet hours end")
    timezone: Optional[str] = Field(None, description="User timezone")
    
    # Frequency preferences
    max_emails_per_day: int = Field(..., description="Max emails per day")
    max_sms_per_day: int = Field(..., description="Max SMS per day")
    digest_frequency: str = Field(..., description="Digest frequency")
    
    # Advanced settings
    language_preference: str = Field(..., description="Language preference")
    content_format: str = Field(..., description="Content format")
    grouping_enabled: bool = Field(..., description="Grouping enabled")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


# =============================================================================
# Subscription Schemas
# =============================================================================

class NotificationSubscriptionCreateRequest(BaseNotificationSchema):
    """Schema for creating a notification subscription."""
    
    organization_id: str = Field(..., description="Organization ID")
    topic: str = Field(..., min_length=1, max_length=200, description="Subscription topic")
    event_type: Optional[str] = Field(None, max_length=200, description="Event type")
    entity_type: Optional[str] = Field(None, max_length=100, description="Entity type")
    entity_id: Optional[str] = Field(None, max_length=200, description="Entity ID")
    
    # Configuration
    channels: List[str] = Field(default_factory=lambda: ["in_app"], description="Notification channels")
    priority: NotificationPriority = Field(NotificationPriority.NORMAL, description="Priority level")
    
    # Filters
    filters: Dict[str, Any] = Field(default_factory=dict, description="Subscription filters")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Subscription conditions")
    keywords: List[str] = Field(default_factory=list, description="Keywords")
    
    # Frequency
    frequency: str = Field("instant", pattern=r"^(instant|daily|weekly|monthly)$", description="Notification frequency")
    delivery_time: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", description="Delivery time (HH:MM)")
    timezone: Optional[str] = Field(None, max_length=50, description="Timezone")
    
    # Metadata
    name: Optional[str] = Field(None, max_length=200, description="Subscription name")
    description: Optional[str] = Field(None, description="Description")
    expires_at: Optional[datetime] = Field(None, description="Expiration time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class NotificationSubscriptionResponse(BaseNotificationSchema):
    """Schema for notification subscription response."""
    
    id: str = Field(..., description="Subscription ID")
    user_id: str = Field(..., description="User ID")
    organization_id: str = Field(..., description="Organization ID")
    topic: str = Field(..., description="Subscription topic")
    event_type: Optional[str] = Field(None, description="Event type")
    entity_type: Optional[str] = Field(None, description="Entity type")
    entity_id: Optional[str] = Field(None, description="Entity ID")
    
    # Status
    status: SubscriptionStatus = Field(..., description="Subscription status")
    
    # Configuration
    channels: List[str] = Field(..., description="Notification channels")
    priority: NotificationPriority = Field(..., description="Priority level")
    frequency: str = Field(..., description="Notification frequency")
    
    # Analytics
    notification_count: int = Field(..., description="Notification count")
    last_notification_at: Optional[datetime] = Field(None, description="Last notification time")
    
    # Metadata
    name: Optional[str] = Field(None, description="Subscription name")
    description: Optional[str] = Field(None, description="Description")
    auto_created: bool = Field(..., description="Auto-created subscription")
    expires_at: Optional[datetime] = Field(None, description="Expiration time")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


# =============================================================================
# Event Schemas
# =============================================================================

class NotificationEventCreateRequest(BaseNotificationSchema):
    """Schema for creating a notification event."""
    
    organization_id: str = Field(..., description="Organization ID")
    event_name: str = Field(..., min_length=1, max_length=200, description="Event name")
    event_type: str = Field(..., min_length=1, max_length=100, description="Event type")
    source_system: Optional[str] = Field(None, max_length=100, description="Source system")
    
    # Event data
    event_data: Dict[str, Any] = Field(default_factory=dict, description="Event data")
    entity_type: Optional[str] = Field(None, max_length=100, description="Entity type")
    entity_id: Optional[str] = Field(None, max_length=200, description="Entity ID")
    
    # Event metadata
    priority: NotificationPriority = Field(NotificationPriority.NORMAL, description="Event priority")
    batch_id: Optional[str] = Field(None, max_length=100, description="Batch ID")
    correlation_id: Optional[str] = Field(None, max_length=100, description="Correlation ID")
    event_timestamp: datetime = Field(..., description="Event timestamp")


class NotificationEventResponse(BaseNotificationSchema):
    """Schema for notification event response."""
    
    id: str = Field(..., description="Event ID")
    organization_id: str = Field(..., description="Organization ID")
    event_name: str = Field(..., description="Event name")
    event_type: str = Field(..., description="Event type")
    source_system: Optional[str] = Field(None, description="Source system")
    
    # Event data
    event_data: Dict[str, Any] = Field(..., description="Event data")
    entity_type: Optional[str] = Field(None, description="Entity type")
    entity_id: Optional[str] = Field(None, description="Entity ID")
    
    # Processing status
    is_processed: bool = Field(..., description="Processing status")
    processed_at: Optional[datetime] = Field(None, description="Processed timestamp")
    processing_errors: List[Dict[str, Any]] = Field(..., description="Processing errors")
    
    # Event metadata
    priority: NotificationPriority = Field(..., description="Event priority")
    batch_id: Optional[str] = Field(None, description="Batch ID")
    correlation_id: Optional[str] = Field(None, description="Correlation ID")
    
    # Timestamps
    event_timestamp: datetime = Field(..., description="Event timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")


# =============================================================================
# Analytics Schemas
# =============================================================================

class NotificationAnalyticsRequest(BaseNotificationSchema):
    """Schema for notification analytics request."""
    
    organization_id: str = Field(..., description="Organization ID")
    period_start: date = Field(..., description="Period start date")
    period_end: date = Field(..., description="Period end date")
    period_type: str = Field("daily", pattern=r"^(daily|weekly|monthly|yearly)$", description="Period type")
    
    # Filters
    notification_type: Optional[NotificationType] = Field(None, description="Filter by notification type")
    channel: Optional[NotificationChannel] = Field(None, description="Filter by channel")
    user_id: Optional[str] = Field(None, description="Filter by user")


class NotificationAnalyticsResponse(BaseNotificationSchema):
    """Schema for notification analytics response."""
    
    id: str = Field(..., description="Analytics ID")
    organization_id: str = Field(..., description="Organization ID")
    period_start: date = Field(..., description="Period start date")
    period_end: date = Field(..., description="Period end date")
    period_type: str = Field(..., description="Period type")
    
    # Notification metrics
    total_notifications: int = Field(..., description="Total notifications")
    notifications_sent: int = Field(..., description="Notifications sent")
    notifications_delivered: int = Field(..., description="Notifications delivered")
    notifications_failed: int = Field(..., description="Notifications failed")
    notifications_read: int = Field(..., description="Notifications read")
    
    # Channel metrics
    email_sent: int = Field(..., description="Emails sent")
    email_delivered: int = Field(..., description="Emails delivered")
    email_opened: int = Field(..., description="Emails opened")
    email_clicked: int = Field(..., description="Emails clicked")
    
    sms_sent: int = Field(..., description="SMS sent")
    sms_delivered: int = Field(..., description="SMS delivered")
    sms_failed: int = Field(..., description="SMS failed")
    
    push_sent: int = Field(..., description="Push notifications sent")
    push_delivered: int = Field(..., description="Push notifications delivered")
    push_opened: int = Field(..., description="Push notifications opened")
    
    in_app_created: int = Field(..., description="In-app notifications created")
    in_app_viewed: int = Field(..., description="In-app notifications viewed")
    in_app_clicked: int = Field(..., description="In-app notifications clicked")
    
    # Engagement metrics
    total_views: int = Field(..., description="Total views")
    total_clicks: int = Field(..., description="Total clicks")
    unique_viewers: int = Field(..., description="Unique viewers")
    
    # Performance metrics
    average_delivery_time_seconds: Optional[Decimal] = Field(None, description="Average delivery time")
    delivery_success_rate: Optional[Decimal] = Field(None, description="Delivery success rate")
    open_rate: Optional[Decimal] = Field(None, description="Open rate")
    click_rate: Optional[Decimal] = Field(None, description="Click rate")
    
    # Cost metrics
    total_cost: Optional[Decimal] = Field(None, description="Total cost")
    cost_per_notification: Optional[Decimal] = Field(None, description="Cost per notification")
    
    # Calculated
    calculated_date: datetime = Field(..., description="Calculation timestamp")


# =============================================================================
# Interaction Schemas
# =============================================================================

class NotificationInteractionRequest(BaseNotificationSchema):
    """Schema for logging notification interaction."""
    
    notification_id: str = Field(..., description="Notification ID")
    interaction_type: str = Field(..., min_length=1, max_length=50, description="Interaction type")
    action_id: Optional[str] = Field(None, max_length=100, description="Action button ID")
    
    # Context
    channel: Optional[NotificationChannel] = Field(None, description="Interaction channel")
    device_type: Optional[str] = Field(None, max_length=50, description="Device type")
    platform: Optional[str] = Field(None, max_length=50, description="Platform")
    browser: Optional[str] = Field(None, max_length=100, description="Browser")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP address")
    user_agent: Optional[str] = Field(None, max_length=500, description="User agent")
    
    # Additional data
    interaction_data: Dict[str, Any] = Field(default_factory=dict, description="Interaction data")
    duration_seconds: Optional[int] = Field(None, ge=0, description="Duration in seconds")


# =============================================================================
# Health and Status Schemas
# =============================================================================

class NotificationSystemHealthResponse(BaseNotificationSchema):
    """Schema for notification system health response."""
    
    status: str = Field(..., description="System status")
    database_connection: str = Field(..., description="Database connection status")
    services_available: bool = Field(..., description="Services availability")
    
    statistics: Dict[str, Any] = Field(..., description="System statistics")
    version: str = Field(..., description="System version")
    timestamp: str = Field(..., description="Health check timestamp")
    
    # Optional error info
    error: Optional[str] = Field(None, description="Error message if unhealthy")


# =============================================================================
# Bulk Operation Schemas
# =============================================================================

class BulkNotificationRequest(BaseNotificationSchema):
    """Schema for bulk notification operations."""
    
    notifications: List[NotificationCreateRequest] = Field(..., min_items=1, max_items=1000, description="Notifications to create")
    batch_id: Optional[str] = Field(None, description="Batch ID")
    priority: NotificationPriority = Field(NotificationPriority.NORMAL, description="Batch priority")


class BulkNotificationResponse(BaseNotificationSchema):
    """Schema for bulk notification response."""
    
    batch_id: str = Field(..., description="Batch ID")
    total_requested: int = Field(..., description="Total requested")
    successful: int = Field(..., description="Successful operations")
    failed: int = Field(..., description="Failed operations")
    
    # Results
    created_notifications: List[str] = Field(..., description="Created notification IDs")
    errors: List[Dict[str, Any]] = Field(..., description="Error details")
    
    # Processing info
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    success_rate: float = Field(..., description="Success rate percentage")


# =============================================================================
# WebSocket Schemas
# =============================================================================

class WebSocketNotificationMessage(BaseNotificationSchema):
    """Schema for WebSocket notification messages."""
    
    type: str = Field(..., description="Message type")
    notification: NotificationResponse = Field(..., description="Notification data")
    timestamp: datetime = Field(..., description="Message timestamp")
    channel: str = Field(..., description="WebSocket channel")


class WebSocketSubscriptionRequest(BaseNotificationSchema):
    """Schema for WebSocket subscription request."""
    
    user_id: str = Field(..., description="User ID")
    organization_id: str = Field(..., description="Organization ID")
    channels: List[str] = Field(default_factory=list, description="Channels to subscribe")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Subscription filters")