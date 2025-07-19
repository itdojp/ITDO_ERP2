"""Notification models for in-app and external notifications."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class NotificationType(str, Enum):
    """Notification type enumeration."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    SYSTEM = "system"
    USER = "user"


class NotificationChannel(str, Enum):
    """Notification delivery channel enumeration."""

    IN_APP = "in_app"
    EMAIL = "email"
    WEBHOOK = "webhook"
    SMS = "sms"
    PUSH = "push"


class NotificationStatus(str, Enum):
    """Notification delivery status enumeration."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


class Notification(Base):
    """Model for storing notifications."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Notification content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[NotificationType] = mapped_column(
        String(20), nullable=False
    )

    # Target and sender
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sender_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Delivery configuration
    channels: Mapped[list[NotificationChannel]] = mapped_column(JSON, nullable=False)
    priority: Mapped[int] = mapped_column(
        Integer, default=5, nullable=False
    )  # 1-10 scale

    # Status tracking
    status: Mapped[NotificationStatus] = mapped_column(
        String(20), default=NotificationStatus.PENDING, nullable=False
    )

    # Interaction tracking
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Delivery tracking
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Additional data
    action_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    action_text: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    extra_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, default={}
    )

    # Scheduling
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        """String representation of Notification."""
        return (
            f"<Notification(id={self.id}, title='{self.title}', "
            f"user_id={self.user_id})>"
        )

    @property
    def is_expired(self) -> bool:
        """Check if notification is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_scheduled(self) -> bool:
        """Check if notification is scheduled for future delivery."""
        if not self.scheduled_for:
            return False
        return datetime.utcnow() < self.scheduled_for

    def mark_as_read(self) -> None:
        """Mark notification as read."""
        self.is_read = True
        self.read_at = datetime.utcnow()

    def mark_as_sent(self) -> None:
        """Mark notification as sent."""
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.utcnow()

    def mark_as_delivered(self) -> None:
        """Mark notification as delivered."""
        self.status = NotificationStatus.DELIVERED
        self.delivered_at = datetime.utcnow()

    def mark_as_failed(self) -> None:
        """Mark notification as failed."""
        self.status = NotificationStatus.FAILED
        self.failed_at = datetime.utcnow()


class NotificationPreferences(Base):
    """Model for user notification preferences."""

    __tablename__ = "notification_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # User and organization
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True
    )
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Email preferences
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_digest: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_frequency: Mapped[str] = mapped_column(
        String(20), default="immediate", nullable=False
    )  # immediate, hourly, daily

    # In-app preferences
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    desktop_notifications: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    # Notification type preferences
    notification_types: Mapped[Dict[str, bool]] = mapped_column(
        JSON,
        nullable=False,
        default={
            "info": True,
            "warning": True,
            "error": True,
            "success": True,
            "system": True,
            "user": True,
        },
    )

    # Channel preferences by type
    channel_preferences: Mapped[Dict[str, list[str]]] = mapped_column(
        JSON,
        nullable=False,
        default={
            "info": ["in_app"],
            "warning": ["in_app", "email"],
            "error": ["in_app", "email"],
            "success": ["in_app"],
            "system": ["in_app", "email"],
            "user": ["in_app", "email"],
        },
    )

    # Quiet hours
    quiet_hours_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    quiet_hours_start: Mapped[Optional[str]] = mapped_column(
        String(5), nullable=True
    )  # HH:MM format
    quiet_hours_end: Mapped[Optional[str]] = mapped_column(
        String(5), nullable=True
    )  # HH:MM format

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="notification_preferences"
    )

    def __repr__(self) -> str:
        """String representation of NotificationPreferences."""
        return f"<NotificationPreferences(user_id={self.user_id})>"

    def is_notification_enabled(self, notification_type: NotificationType) -> bool:
        """Check if notification type is enabled for user."""
        return self.notification_types.get(notification_type.value, True)

    def get_preferred_channels(
        self, notification_type: NotificationType
    ) -> list[NotificationChannel]:
        """Get preferred delivery channels for notification type."""
        channels = self.channel_preferences.get(notification_type.value, ["in_app"])
        return [NotificationChannel(channel) for channel in channels]

    def is_quiet_time(self) -> bool:
        """Check if current time is within quiet hours."""
        if (
            not self.quiet_hours_enabled
            or not self.quiet_hours_start
            or not self.quiet_hours_end
        ):
            return False

        from datetime import time

        current_time = datetime.utcnow().time()
        start_time = time.fromisoformat(self.quiet_hours_start)
        end_time = time.fromisoformat(self.quiet_hours_end)

        # Handle overnight quiet hours (e.g., 22:00 to 06:00)
        if start_time > end_time:
            return current_time >= start_time or current_time <= end_time
        else:
            return start_time <= current_time <= end_time


class NotificationQueue(Base):
    """Model for notification queue/batch processing."""

    __tablename__ = "notification_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Queue identification
    batch_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )

    # Notification reference
    notification_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Delivery details
    channel: Mapped[NotificationChannel] = mapped_column(String(20), nullable=False)
    recipient: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # email, phone, webhook URL

    # Processing status
    status: Mapped[NotificationStatus] = mapped_column(
        String(20), default=NotificationStatus.PENDING, nullable=False
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    # Timing
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Results
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    delivery_response: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        """String representation of NotificationQueue."""
        return (
            f"<NotificationQueue(id={self.id}, notification_id={self.notification_id}, "
            f"channel={self.channel})>"
        )

    @property
    def can_retry(self) -> bool:
        """Check if notification can be retried."""
        return (
            self.attempts < self.max_attempts
            and self.status == NotificationStatus.FAILED
        )

    def increment_attempts(self) -> None:
        """Increment retry attempts."""
        self.attempts += 1

    def calculate_next_retry(self) -> datetime:
        """Calculate next retry time with exponential backoff."""
        from datetime import timedelta

        base_delay = 60  # 1 minute base delay
        delay_seconds = base_delay * (2 ** (self.attempts - 1))  # Exponential backoff
        delay_seconds = min(delay_seconds, 3600)  # Max 1 hour delay

        return datetime.utcnow() + timedelta(seconds=delay_seconds)


class WebhookEndpoint(Base):
    """Model for webhook notification endpoints."""

    __tablename__ = "webhook_endpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Endpoint details
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # For HMAC signing

    # Configuration
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by: Mapped[int] = mapped_column(Integer, nullable=False)

    # Filtering
    notification_types: Mapped[list[NotificationType]] = mapped_column(
        JSON, nullable=False, default=[]
    )
    event_filters: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, default={}
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Headers and auth
    headers: Mapped[Dict[str, str]] = mapped_column(JSON, nullable=False, default={})
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    # Statistics
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_success_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_failure_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    def __repr__(self) -> str:
        """String representation of WebhookEndpoint."""
        return f"<WebhookEndpoint(id={self.id}, name='{self.name}', url='{self.url}')>"

    @property
    def success_rate(self) -> float:
        """Calculate webhook success rate."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return (self.success_count / total) * 100

    def record_success(self) -> None:
        """Record successful webhook delivery."""
        self.success_count += 1
        self.last_success_at = datetime.utcnow()

    def record_failure(self) -> None:
        """Record failed webhook delivery."""
        self.failure_count += 1
        self.last_failure_at = datetime.utcnow()
