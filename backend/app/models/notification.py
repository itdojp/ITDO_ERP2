"""Notification system models for multi-channel notifications."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"


class NotificationStatus(str, Enum):
    """Notification delivery status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    CLICKED = "clicked"
    OPENED = "opened"
    UNSUBSCRIBED = "unsubscribed"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class NotificationTemplate(Base):
    """Notification templates for different channels and purposes."""
    
    __tablename__ = "notification_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Template identification
    template_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Channel and content
    channel: Mapped[NotificationChannel] = mapped_column(String(20), nullable=False, index=True)
    subject_template: Mapped[Optional[str]] = mapped_column(Text)  # For email/SMS
    content_template: Mapped[str] = mapped_column(Text, nullable=False)
    html_template: Mapped[Optional[str]] = mapped_column(Text)  # For email
    
    # Template variables and validation
    variables: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Expected variables
    validation_rules: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Configuration
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # System templates cannot be deleted
    default_priority: Mapped[NotificationPriority] = mapped_column(String(20), default=NotificationPriority.MEDIUM)
    
    # Audit fields
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organizations.id"), index=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="notification_templates")
    creator = relationship("User", foreign_keys=[created_by])
    notifications = relationship("Notification", back_populates="template")

    def __repr__(self) -> str:
        return f"<NotificationTemplate(key='{self.template_key}', channel='{self.channel}')>"


class NotificationPreference(Base):
    """User notification preferences and subscription settings."""
    
    __tablename__ = "notification_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # User identification
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organizations.id"), index=True)
    
    # Preference settings
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # e.g., "security", "updates", "marketing"
    channel: Mapped[NotificationChannel] = mapped_column(String(20), nullable=False, index=True)
    
    # Subscription settings
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    frequency: Mapped[str] = mapped_column(String(20), default="immediate")  # immediate, daily, weekly, monthly
    quiet_hours_start: Mapped[Optional[str]] = mapped_column(String(5))  # "22:00"
    quiet_hours_end: Mapped[Optional[str]] = mapped_column(String(5))    # "08:00"
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    
    # Contact information per channel
    contact_info: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON)  # {"email": "user@example.com", "phone": "+1234567890"}
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="notification_preferences")
    organization = relationship("Organization")

    def __repr__(self) -> str:
        return f"<NotificationPreference(user_id={self.user_id}, category='{self.category}', channel='{self.channel}')>"


class Notification(Base):
    """Individual notification instances with delivery tracking."""
    
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Notification identification
    external_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)  # Provider-specific ID
    batch_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)  # For bulk notifications
    
    # Recipient information
    recipient_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    recipient_email: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    recipient_phone: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    recipient_device_token: Mapped[Optional[str]] = mapped_column(String(255))  # For push notifications
    
    # Content and delivery
    template_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("notification_templates.id"), index=True)
    channel: Mapped[NotificationChannel] = mapped_column(String(20), nullable=False, index=True)
    priority: Mapped[NotificationPriority] = mapped_column(String(20), default=NotificationPriority.MEDIUM, index=True)
    
    # Message content
    subject: Mapped[Optional[str]] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    html_content: Mapped[Optional[str]] = mapped_column(Text)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Additional data, tracking pixels, etc.
    
    # Delivery tracking
    status: Mapped[NotificationStatus] = mapped_column(String(20), default=NotificationStatus.PENDING, index=True)
    provider: Mapped[Optional[str]] = mapped_column(String(50))  # SendGrid, Twilio, Firebase, etc.
    provider_response: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Timing
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    clicked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Error handling
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Audit fields
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organizations.id"), index=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    recipient_user = relationship("User", foreign_keys=[recipient_user_id], back_populates="received_notifications")
    template = relationship("NotificationTemplate", back_populates="notifications")
    organization = relationship("Organization")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, channel='{self.channel}', status='{self.status}')>"


class NotificationEvent(Base):
    """Notification event tracking for analytics and debugging."""
    
    __tablename__ = "notification_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Event identification
    notification_id: Mapped[int] = mapped_column(Integer, ForeignKey("notifications.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # sent, delivered, opened, clicked, bounced, etc.
    
    # Event data
    event_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    
    # Provider information
    provider: Mapped[Optional[str]] = mapped_column(String(50))
    provider_event_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Timing
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    notification = relationship("Notification")

    def __repr__(self) -> str:
        return f"<NotificationEvent(notification_id={self.notification_id}, type='{self.event_type}')>"


class NotificationQueue(Base):
    """Queue for batch processing and scheduled notifications."""
    
    __tablename__ = "notification_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Queue identification
    batch_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    queue_name: Mapped[str] = mapped_column(String(50), default="default", index=True)
    
    # Processing settings
    priority: Mapped[NotificationPriority] = mapped_column(String(20), default=NotificationPriority.MEDIUM, index=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    
    # Queue data
    notification_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    template_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    recipients: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False)
    
    # Processing status
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # pending, processing, completed, failed
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Statistics
    total_recipients: Mapped[int] = mapped_column(Integer, default=0)
    successful_sends: Mapped[int] = mapped_column(Integer, default=0)
    failed_sends: Mapped[int] = mapped_column(Integer, default=0)
    
    # Audit fields
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organizations.id"), index=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")
    creator = relationship("User")

    def __repr__(self) -> str:
        return f"<NotificationQueue(batch_id='{self.batch_id}', status='{self.status}')>"