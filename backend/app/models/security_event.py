"""Security event models for comprehensive monitoring."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.organization import Organization  # noqa: F401
    from app.models.user import User  # noqa: F401


class ThreatLevel(str, Enum):
    """Threat level enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEventType(str, Enum):
    """Security event type enumeration."""

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGIN_MULTIPLE_FAILURES = "login_multiple_failures"
    LOGOUT = "logout"
    SESSION_TIMEOUT = "session_timeout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    PASSWORD_BREACH = "password_breach"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    DATA_EXPORT = "data_export"
    BULK_DATA_ACCESS = "bulk_data_access"
    SUSPICIOUS_IP = "suspicious_ip"
    AFTER_HOURS_ACCESS = "after_hours_access"
    ADMIN_ACTION = "admin_action"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_SETTING_CHANGE = "security_setting_change"
    API_ABUSE = "api_abuse"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    MALWARE_DETECTED = "malware_detected"
    VULNERABILITY_DETECTED = "vulnerability_detected"
    ANOMALY_DETECTED = "anomaly_detected"
    COMPLIANCE_VIOLATION = "compliance_violation"


class SecurityIncidentStatus(str, Enum):
    """Security incident status enumeration."""

    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    ESCALATED = "escalated"


class SecurityEvent(BaseModel):
    """Security event model for tracking security-related activities."""

    __tablename__ = "security_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    event_type: Mapped[SecurityEventType] = mapped_column(String(50), nullable=False, index=True)
    threat_level: Mapped[ThreatLevel] = mapped_column(String(20), nullable=False, index=True)
    
    # User and organization context
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), index=True
    )
    organization_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("organizations.id"), index=True
    )
    
    # Event details
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Context information
    source_ip: Mapped[str | None] = mapped_column(String(45), index=True)
    user_agent: Mapped[str | None] = mapped_column(Text)
    session_id: Mapped[str | None] = mapped_column(String(64), index=True)
    api_endpoint: Mapped[str | None] = mapped_column(String(255))
    http_method: Mapped[str | None] = mapped_column(String(10))
    
    # Risk assessment
    risk_score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    confidence: Mapped[float] = mapped_column(default=1.0)
    
    # Evidence and response
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    recommended_actions: Mapped[list[str]] = mapped_column(JSON, default=list)
    auto_response_taken: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Tracking
    resolved: Mapped[bool] = mapped_column(default=False, index=True)
    resolved_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    
    # Integrity and audit
    checksum: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id], lazy="joined")
    organization = relationship("Organization", foreign_keys=[organization_id], lazy="select")
    resolver = relationship("User", foreign_keys=[resolved_by], lazy="select")

    def calculate_checksum(self) -> str:
        """Calculate checksum for event integrity."""
        data = {
            "event_id": self.event_id,
            "event_type": self.event_type.value if self.event_type else None,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "title": self.title,
            "description": self.description,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify event has not been tampered with."""
        if not self.checksum:
            return False
        calculated = self.calculate_checksum()
        return calculated == self.checksum

    def __repr__(self) -> str:
        return (
            f"<SecurityEvent(id={self.id}, type={self.event_type}, "
            f"threat_level={self.threat_level}, user={self.user_id})>"
        )


class SecurityIncident(BaseModel):
    """Security incident model for tracking ongoing security issues."""

    __tablename__ = "security_incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    incident_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Classification
    severity: Mapped[ThreatLevel] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[SecurityIncidentStatus] = mapped_column(String(20), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Context
    organization_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("organizations.id"), index=True
    )
    affected_users: Mapped[list[int]] = mapped_column(JSON, default=list)
    affected_resources: Mapped[list[str]] = mapped_column(JSON, default=list)
    
    # Investigation
    assigned_to: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    investigation_notes: Mapped[str | None] = mapped_column(Text)
    timeline: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    
    # Related events
    related_events: Mapped[list[int]] = mapped_column(JSON, default=list)
    
    # Resolution
    resolution: Mapped[str | None] = mapped_column(Text)
    lessons_learned: Mapped[str | None] = mapped_column(Text)
    
    # Tracking
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    organization = relationship("Organization", foreign_keys=[organization_id], lazy="select")
    assignee = relationship("User", foreign_keys=[assigned_to], lazy="select")

    def __repr__(self) -> str:
        return (
            f"<SecurityIncident(id={self.id}, severity={self.severity}, "
            f"status={self.status}, title={self.title[:50]})>"
        )


class SecurityAlert(BaseModel):
    """Security alert model for real-time notifications."""

    __tablename__ = "security_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    alert_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[ThreatLevel] = mapped_column(String(20), nullable=False, index=True)
    
    # Content
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Context
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    organization_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("organizations.id"), index=True
    )
    
    # Related data
    related_event_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("security_events.id")
    )
    related_incident_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("security_incidents.id")
    )
    
    # Delivery
    recipients: Mapped[list[int]] = mapped_column(JSON, default=list)
    delivery_methods: Mapped[list[str]] = mapped_column(JSON, default=list)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    # Status
    acknowledged: Mapped[bool] = mapped_column(default=False, index=True)
    acknowledged_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    # Tracking
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id], lazy="select")
    organization = relationship("Organization", foreign_keys=[organization_id], lazy="select")
    acknowledger = relationship("User", foreign_keys=[acknowledged_by], lazy="select")
    related_event = relationship("SecurityEvent", foreign_keys=[related_event_id], lazy="select")
    related_incident = relationship("SecurityIncident", foreign_keys=[related_incident_id], lazy="select")

    def __repr__(self) -> str:
        return (
            f"<SecurityAlert(id={self.id}, type={self.alert_type}, "
            f"severity={self.severity}, acknowledged={self.acknowledged})>"
        )