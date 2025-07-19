"""Security audit models for enhanced monitoring."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.organization import Organization  # noqa: F401
    from app.models.user import User  # noqa: F401


class SecurityEventType(str, Enum):
    """Security event types for monitoring."""

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    ROLE_ASSIGNMENT = "role_assignment"
    ROLE_REMOVAL = "role_removal"
    DATA_ACCESS = "data_access"
    DATA_EXPORT = "data_export"
    SENSITIVE_DATA_ACCESS = "sensitive_data_access"
    MULTIPLE_LOGIN_ATTEMPTS = "multiple_login_attempts"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    UNAUTHORIZED_ACCESS_ATTEMPT = "unauthorized_access_attempt"


class RiskLevel(str, Enum):
    """Risk levels for security events."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityAuditLog(BaseModel):
    """Enhanced security audit log for monitoring security events."""

    __tablename__ = "security_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    event_type: Mapped[SecurityEventType] = mapped_column(
        String(50), nullable=False, index=True
    )
    risk_level: Mapped[RiskLevel] = mapped_column(
        String(20), nullable=False, index=True, default=RiskLevel.LOW
    )
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    resource_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    organization_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("organizations.id"), index=True
    )

    # Security context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), index=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    session_id: Mapped[Optional[str]] = mapped_column(String(128), index=True)

    # Event details
    description: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Detection and response
    detection_method: Mapped[Optional[str]] = mapped_column(String(100))
    is_automated_detection: Mapped[bool] = mapped_column(default=False)
    requires_attention: Mapped[bool] = mapped_column(default=False, index=True)
    is_resolved: Mapped[bool] = mapped_column(default=False, index=True)
    resolved_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[user_id], lazy="select"
    )
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization", foreign_keys=[organization_id], lazy="select"
    )
    resolver: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[resolved_by], lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<SecurityAuditLog(id={self.id}, event_type={self.event_type}, "
            f"risk_level={self.risk_level}, user_id={self.user_id})>"
        )


class SecurityAlert(BaseModel):
    """Security alerts for real-time notifications."""

    __tablename__ = "security_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    security_audit_log_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("security_audit_logs.id"), nullable=False
    )
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[RiskLevel] = mapped_column(
        String(20), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Notification
    is_sent: Mapped[bool] = mapped_column(default=False, index=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    recipients: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Response
    is_acknowledged: Mapped[bool] = mapped_column(default=False, index=True)
    acknowledged_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    security_audit_log: Mapped[SecurityAuditLog] = relationship(
        "SecurityAuditLog", lazy="joined"
    )
    acknowledger: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[acknowledged_by], lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<SecurityAlert(id={self.id}, alert_type={self.alert_type}, "
            f"severity={self.severity}, is_sent={self.is_sent})>"
        )
