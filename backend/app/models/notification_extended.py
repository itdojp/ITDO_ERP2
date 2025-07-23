"""
Notification System Models - CC02 v31.0 Phase 2

Comprehensive notification system with:
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

import uuid
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class NotificationType(str, Enum):
    """Notification type enumeration."""

    SYSTEM = "system"
    ALERT = "alert"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"
    ERROR = "error"
    REMINDER = "reminder"
    TASK = "task"
    MESSAGE = "message"
    ANNOUNCEMENT = "announcement"


class NotificationChannel(str, Enum):
    """Notification channel enumeration."""

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"
    DISCORD = "discord"


class NotificationStatus(str, Enum):
    """Notification status enumeration."""

    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationPriority(str, Enum):
    """Notification priority enumeration."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class SubscriptionStatus(str, Enum):
    """Subscription status enumeration."""

    ACTIVE = "active"
    PAUSED = "paused"
    INACTIVE = "inactive"
    BLOCKED = "blocked"


class DeliveryStatus(str, Enum):
    """Delivery status enumeration."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    BOUNCED = "bounced"
    FAILED = "failed"
    OPENED = "opened"
    CLICKED = "clicked"


class NotificationExtended(Base):
    """Extended Notification Management - Comprehensive notification handling."""

    __tablename__ = "notifications_extended"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Notification identification
    notification_number = Column(String(50), nullable=False, unique=True, index=True)
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    summary = Column(String(500))

    # Notification classification
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    category = Column(String(100))
    subcategory = Column(String(100))
    priority = Column(
        SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL
    )

    # Recipients
    recipient_user_id = Column(String, ForeignKey("users.id"))
    recipient_email = Column(String(200))
    recipient_phone = Column(String(50))
    recipient_groups = Column(JSON, default=[])
    recipient_roles = Column(JSON, default=[])

    # Targeting and filtering
    target_audience = Column(JSON, default={})
    audience_filter = Column(JSON, default={})
    geographic_targeting = Column(JSON, default=[])
    demographic_targeting = Column(JSON, default={})

    # Content and formatting
    content_html = Column(Text)
    content_plain = Column(Text)
    content_markdown = Column(Text)
    rich_content = Column(JSON, default={})
    attachments = Column(JSON, default=[])

    # Delivery channels
    channels = Column(JSON, default=["in_app"])
    primary_channel = Column(
        SQLEnum(NotificationChannel), default=NotificationChannel.IN_APP
    )
    fallback_channels = Column(JSON, default=[])

    # Scheduling and timing
    send_at = Column(DateTime)
    scheduled_at = Column(DateTime)
    expires_at = Column(DateTime)
    timezone = Column(String(50))

    # Status and tracking
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    is_archived = Column(Boolean, default=False)
    archived_at = Column(DateTime)

    # Template and personalization
    template_id = Column(String, ForeignKey("notification_templates.id"))
    template_variables = Column(JSON, default={})
    personalization_data = Column(JSON, default={})

    # Source and context
    source_system = Column(String(100))
    source_event = Column(String(200))
    source_entity_type = Column(String(100))
    source_entity_id = Column(String(200))
    context_data = Column(JSON, default={})

    # Interaction and engagement
    action_buttons = Column(JSON, default=[])
    deep_link_url = Column(String(1000))
    tracking_params = Column(JSON, default={})

    # Delivery tracking
    delivery_attempts = Column(Integer, default=0)
    max_delivery_attempts = Column(Integer, default=3)
    last_delivery_attempt = Column(DateTime)
    delivery_errors = Column(JSON, default=[])

    # Analytics and metrics
    view_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)
    action_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)

    # A/B testing
    ab_test_group = Column(String(50))
    ab_test_variant = Column(String(50))

    # Metadata
    tags = Column(JSON, default=[])
    notif_metadata = Column(JSON, default={})
    custom_fields = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    created_by = Column(String, ForeignKey("users.id"))

    # Relationships
    organization = relationship("Organization")
    recipient_user = relationship("User", foreign_keys=[recipient_user_id])
    template = relationship("NotificationTemplate")
    creator = relationship("User", foreign_keys=[created_by])

    # Notification-related relationships
    deliveries = relationship("NotificationDelivery", back_populates="notification")
    interactions = relationship(
        "NotificationInteraction", back_populates="notification"
    )


class NotificationTemplate(Base):
    """Notification Template Management - Template-based notification creation."""

    __tablename__ = "notification_templates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Template identification
    name = Column(String(200), nullable=False)
    code = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    category = Column(String(100))

    # Template content
    subject_template = Column(String(500))
    title_template = Column(String(500))
    message_template = Column(Text, nullable=False)
    html_template = Column(Text)
    plain_template = Column(Text)

    # Template configuration
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    default_priority = Column(
        SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL
    )
    default_channels = Column(JSON, default=["in_app"])

    # Variables and placeholders
    variables = Column(JSON, default=[])
    required_variables = Column(JSON, default=[])
    default_values = Column(JSON, default={})
    validation_rules = Column(JSON, default={})

    # Formatting and styling
    styling = Column(JSON, default={})
    layout = Column(String(100))
    theme = Column(String(100))

    # Localization
    language = Column(String(10), default="en")
    localized_versions = Column(JSON, default={})

    # Usage and analytics
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime)
    success_rate = Column(Numeric(5, 2))

    # Access control
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Metadata
    tags = Column(JSON, default=[])
    notif_metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization")
    owner = relationship("User", foreign_keys=[owner_id])
    creator = relationship("User", foreign_keys=[created_by])

    # Template-related relationships
    notifications = relationship("NotificationExtended", back_populates="template")


class NotificationDelivery(Base):
    """Notification Delivery Tracking - Multi-channel delivery management."""

    __tablename__ = "notification_deliveries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    notification_id = Column(
        String, ForeignKey("notifications_extended.id"), nullable=False
    )
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Delivery channel
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    provider = Column(String(100))  # AWS SES, Twilio, Firebase, etc.
    provider_message_id = Column(String(200))

    # Recipient information
    recipient_address = Column(
        String(500), nullable=False
    )  # email, phone, device token
    recipient_name = Column(String(200))
    recipient_type = Column(String(50))  # user, group, role, external

    # Delivery status
    status = Column(SQLEnum(DeliveryStatus), default=DeliveryStatus.PENDING)
    attempt_number = Column(Integer, default=1)

    # Timing
    scheduled_at = Column(DateTime)
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    failed_at = Column(DateTime)

    # Content delivered
    subject = Column(String(500))
    content = Column(Text)
    formatted_content = Column(Text)

    # Delivery details
    delivery_response = Column(JSON)
    error_code = Column(String(100))
    error_message = Column(String(1000))
    retry_count = Column(Integer, default=0)

    # Tracking and analytics
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    bounced_at = Column(DateTime)
    unsubscribed_at = Column(DateTime)

    # Provider-specific data
    provider_data = Column(JSON, default={})
    tracking_id = Column(String(200))

    # Cost and billing
    delivery_cost = Column(Numeric(10, 4))
    cost_currency = Column(String(3), default="USD")

    # Metadata
    notif_metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    notification = relationship("NotificationExtended", back_populates="deliveries")
    organization = relationship("Organization")


class NotificationPreference(Base):
    """Notification Preferences - User-specific notification settings."""

    __tablename__ = "notification_preferences"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # General preferences
    is_enabled = Column(Boolean, default=True)
    global_opt_out = Column(Boolean, default=False)

    # Channel preferences
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)

    # Type-specific preferences
    system_notifications = Column(Boolean, default=True)
    alert_notifications = Column(Boolean, default=True)
    warning_notifications = Column(Boolean, default=True)
    info_notifications = Column(Boolean, default=True)
    reminder_notifications = Column(Boolean, default=True)
    task_notifications = Column(Boolean, default=True)
    message_notifications = Column(Boolean, default=True)
    announcement_notifications = Column(Boolean, default=True)

    # Timing preferences
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String(5))  # HH:MM format
    quiet_hours_end = Column(String(5))  # HH:MM format
    timezone = Column(String(50))

    # Frequency preferences
    max_emails_per_day = Column(Integer, default=50)
    max_sms_per_day = Column(Integer, default=10)
    digest_frequency = Column(
        String(20), default="daily"
    )  # instant, hourly, daily, weekly

    # Channel-specific settings
    email_address = Column(String(200))
    phone_number = Column(String(50))
    push_tokens = Column(JSON, default=[])

    # Subscription management
    subscriptions = Column(JSON, default=[])
    unsubscribed_categories = Column(JSON, default=[])
    blocked_senders = Column(JSON, default=[])

    # Advanced settings
    language_preference = Column(String(10), default="en")
    content_format = Column(String(20), default="html")  # html, plain, markdown
    grouping_enabled = Column(Boolean, default=True)

    # Metadata
    custom_settings = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")
    organization = relationship("Organization")


class NotificationSubscription(Base):
    """Notification Subscription Management - Topic and event subscriptions."""

    __tablename__ = "notification_subscriptions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Subscription details
    topic = Column(String(200), nullable=False)
    event_type = Column(String(200))
    entity_type = Column(String(100))
    entity_id = Column(String(200))

    # Subscription configuration
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    channels = Column(JSON, default=["in_app"])
    priority = Column(
        SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL
    )

    # Filters and conditions
    filters = Column(JSON, default={})
    conditions = Column(JSON, default={})
    keywords = Column(JSON, default=[])

    # Frequency and timing
    frequency = Column(String(20), default="instant")  # instant, daily, weekly, monthly
    delivery_time = Column(String(5))  # HH:MM for scheduled delivery
    timezone = Column(String(50))

    # Subscription metadata
    name = Column(String(200))
    description = Column(Text)
    auto_created = Column(Boolean, default=False)

    # Analytics
    notification_count = Column(Integer, default=0)
    last_notification_at = Column(DateTime)

    # Expiration
    expires_at = Column(DateTime)

    # Metadata
    notif_metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")
    organization = relationship("Organization")


class NotificationInteraction(Base):
    """Notification Interaction Tracking - User engagement analytics."""

    __tablename__ = "notification_interactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    notification_id = Column(
        String, ForeignKey("notifications_extended.id"), nullable=False
    )
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Interaction details
    user_id = Column(String, ForeignKey("users.id"))
    session_id = Column(String(100))
    interaction_type = Column(
        String(50), nullable=False
    )  # view, click, action, share, dismiss
    action_id = Column(String(100))  # For action buttons

    # Context information
    channel = Column(SQLEnum(NotificationChannel))
    device_type = Column(String(50))
    platform = Column(String(50))
    browser = Column(String(100))

    # Location and timing
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    referrer = Column(String(1000))

    # Interaction data
    interaction_data = Column(JSON, default={})
    duration_seconds = Column(Integer)

    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    notification = relationship("NotificationExtended", back_populates="interactions")
    organization = relationship("Organization")
    user = relationship("User")


class NotificationEvent(Base):
    """Notification Event Management - Event-driven notification triggers."""

    __tablename__ = "notification_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Event identification
    event_name = Column(String(200), nullable=False)
    event_type = Column(String(100), nullable=False)
    source_system = Column(String(100))

    # Event data
    event_data = Column(JSON, default={})
    entity_type = Column(String(100))
    entity_id = Column(String(200))

    # Event processing
    is_processed = Column(Boolean, default=False)
    processed_at = Column(DateTime)
    processing_errors = Column(JSON, default=[])

    # Event metadata
    priority = Column(
        SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL
    )
    batch_id = Column(String(100))
    correlation_id = Column(String(100))

    # Timestamps
    event_timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization")


class NotificationRule(Base):
    """Notification Rule Engine - Automated notification generation rules."""

    __tablename__ = "notification_rules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Rule identification
    name = Column(String(200), nullable=False)
    description = Column(Text)
    rule_type = Column(String(100), nullable=False)

    # Rule configuration
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=100)

    # Triggers and conditions
    trigger_events = Column(JSON, default=[])
    conditions = Column(JSON, default={})
    filters = Column(JSON, default={})

    # Action configuration
    template_id = Column(String, ForeignKey("notification_templates.id"))
    notification_type = Column(SQLEnum(NotificationType))
    channels = Column(JSON, default=["in_app"])
    priority_override = Column(SQLEnum(NotificationPriority))

    # Recipients
    recipient_rules = Column(JSON, default={})
    target_users = Column(JSON, default=[])
    target_groups = Column(JSON, default=[])
    target_roles = Column(JSON, default=[])

    # Timing and scheduling
    delay_seconds = Column(Integer, default=0)
    max_frequency = Column(String(50))  # Per user frequency limit
    quiet_hours_respect = Column(Boolean, default=True)

    # Content customization
    content_rules = Column(JSON, default={})
    variable_mappings = Column(JSON, default={})

    # Analytics
    execution_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    last_executed_at = Column(DateTime)

    # Metadata
    tags = Column(JSON, default=[])
    notif_metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization")
    template = relationship("NotificationTemplate")
    creator = relationship("User")


class NotificationQueue(Base):
    """Notification Queue Management - Queued notification processing."""

    __tablename__ = "notification_queue"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Queue item details
    notification_id = Column(String, ForeignKey("notifications_extended.id"))
    queue_name = Column(String(100), default="default")
    priority = Column(Integer, default=100)

    # Processing status
    status = Column(String(50), default="pending")
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)

    # Scheduling
    scheduled_at = Column(DateTime)
    process_after = Column(DateTime)

    # Processing details
    processed_at = Column(DateTime)
    processing_time_ms = Column(Integer)
    error_message = Column(Text)

    # Batch processing
    batch_id = Column(String(100))
    batch_size = Column(Integer)

    # Metadata
    notif_metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization")
    notification = relationship("NotificationExtended")


class NotificationAnalytics(Base):
    """Notification Analytics - Comprehensive notification performance analytics."""

    __tablename__ = "notification_analytics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Reporting period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    period_type = Column(String(20), default="daily")

    # Notification metrics
    total_notifications = Column(Integer, default=0)
    notifications_sent = Column(Integer, default=0)
    notifications_delivered = Column(Integer, default=0)
    notifications_failed = Column(Integer, default=0)
    notifications_read = Column(Integer, default=0)

    # Channel metrics
    email_sent = Column(Integer, default=0)
    email_delivered = Column(Integer, default=0)
    email_opened = Column(Integer, default=0)
    email_clicked = Column(Integer, default=0)
    email_bounced = Column(Integer, default=0)

    sms_sent = Column(Integer, default=0)
    sms_delivered = Column(Integer, default=0)
    sms_failed = Column(Integer, default=0)

    push_sent = Column(Integer, default=0)
    push_delivered = Column(Integer, default=0)
    push_opened = Column(Integer, default=0)

    in_app_created = Column(Integer, default=0)
    in_app_viewed = Column(Integer, default=0)
    in_app_clicked = Column(Integer, default=0)

    # Engagement metrics
    total_views = Column(Integer, default=0)
    total_clicks = Column(Integer, default=0)
    total_actions = Column(Integer, default=0)
    unique_viewers = Column(Integer, default=0)

    # Performance metrics
    average_delivery_time_seconds = Column(Numeric(8, 2))
    delivery_success_rate = Column(Numeric(5, 2))
    open_rate = Column(Numeric(5, 2))
    click_rate = Column(Numeric(5, 2))
    conversion_rate = Column(Numeric(5, 2))

    # Cost metrics
    total_cost = Column(Numeric(10, 2))
    cost_per_notification = Column(Numeric(6, 4))
    cost_per_delivery = Column(Numeric(6, 4))

    # Template performance
    top_templates = Column(JSON, default=[])
    template_performance = Column(JSON, default={})

    # User engagement
    active_users = Column(Integer, default=0)
    engaged_users = Column(Integer, default=0)
    opted_out_users = Column(Integer, default=0)

    # Error analysis
    error_types = Column(JSON, default={})
    failure_reasons = Column(JSON, default={})

    # Trends and comparisons
    growth_rate = Column(Numeric(5, 2))
    period_comparison = Column(JSON, default={})

    # Calculation metadata
    calculated_date = Column(DateTime)
    calculated_by = Column(String, ForeignKey("users.id"))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization")
    calculator = relationship("User")
