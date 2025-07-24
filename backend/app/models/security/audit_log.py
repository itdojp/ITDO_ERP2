"""Security audit log model."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base_class import Base


class SecurityAuditLog(Base):
    """Security audit log for tracking all security-related events."""

    __tablename__ = "security_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type = Column(String(100), nullable=False, index=True)
    severity = Column(
        String(20), nullable=False, index=True
    )  # INFO, WARNING, ERROR, CRITICAL
    user_id = Column(UUID(as_uuid=True), index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    resource_type = Column(String(100))
    resource_id = Column(String(255))
    action = Column(String(100), nullable=False)
    result = Column(String(20), nullable=False)  # SUCCESS, FAILURE, BLOCKED
    details = Column(JSON)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Composite indexes for common queries
    __table_args__ = (
        Index("idx_security_audit_user_time", "user_id", "created_at"),
        Index("idx_security_audit_type_time", "event_type", "created_at"),
        Index("idx_security_audit_severity_time", "severity", "created_at"),
    )
