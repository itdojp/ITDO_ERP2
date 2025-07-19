"""Notification model implementation.

This module provides notification models for in-app notifications,
email notifications, and notification preferences.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.types import UserId

if TYPE_CHECKING:
    from app.models.user import User


class NotificationType(str, Enum):
    """Notification type enumeration."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class NotificationChannel(str, Enum):
    """Notification delivery channel enumeration."""

    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"
    WEBHOOK = "webhook"


class NotificationPriority(str, Enum):
    """Notification priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(BaseModel):
    """In-app notification model."""

    __tablename__ = "notifications"

    # Recipient information
    user_id: Mapped[UserId] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Notification content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[NotificationType] = mapped_column(
        SQLEnum(NotificationType), default=NotificationType.INFO, nullable=False
    )
    priority: Mapped[NotificationPriority] = mapped_column(
        SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL, nullable=False
    )

    # Status tracking
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Metadata
    action_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    extra_data: Mapped[Dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Organization context
    organization_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Expiration
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")

    def mark_as_read(self) -> None:
        """Mark notification as read."""
        self.is_read = True
        self.read_at = datetime.utcnow()

    def is_expired(self) -> bool:
        """Check if notification is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


class NotificationPreference(BaseModel):
    """User notification preferences model."""

    __tablename__ = "notification_preferences"

    # User reference
    user_id: Mapped[UserId] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    # Channel preferences
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Category preferences (JSON object for flexibility)
    category_preferences: Mapped[Dict[str, Dict[str, bool]] | None] = mapped_column(
        JSON, nullable=True,
        comment="Category-specific channel preferences"
    )

    # Timing preferences
    email_digest_frequency: Mapped[str] = mapped_column(
        String(20), default="daily", nullable=False
    )  # immediate, hourly, daily, weekly, never
    quiet_hours_start: Mapped[str | None] = mapped_column(String(5), nullable=True)  # HH:MM
    quiet_hours_end: Mapped[str | None] = mapped_column(String(5), nullable=True)    # HH:MM
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notification_preferences")


class NotificationQueue(BaseModel):
    """Notification queue for background processing."""

    __tablename__ = "notification_queue"

    # Message details
    user_id: Mapped[UserId] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        SQLEnum(NotificationChannel), nullable=False, index=True
    )

    # Content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    template_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    template_data: Mapped[Dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Delivery configuration
    recipient_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    priority: Mapped[NotificationPriority] = mapped_column(
        SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL, nullable=False
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )  # pending, processing, sent, failed, cancelled
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Result tracking
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Organization context
    organization_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User")


class WebhookEndpoint(BaseModel):
    """Webhook endpoint configuration for external notifications."""

    __tablename__ = "webhook_endpoints"

    # Organization context
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Endpoint configuration
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Filtering
    event_types: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Status tracking
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Created by
    created_by: Mapped[UserId] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


# Export all notification models
__all__ = [
    "Notification",
    "NotificationPreference",
    "NotificationQueue",
    "WebhookEndpoint",
    "NotificationType",
    "NotificationChannel",
    "NotificationPriority",
]
