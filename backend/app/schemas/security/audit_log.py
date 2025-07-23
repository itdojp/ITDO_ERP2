"""Security audit log schemas."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SecurityEventType(str, Enum):
    """Types of security events."""
    LOGIN_ATTEMPT = "login_attempt"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PERMISSION_DENIED = "permission_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    API_RATE_LIMIT = "api_rate_limit"
    INVALID_TOKEN = "invalid_token"


class SecuritySeverity(str, Enum):
    """Security event severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SecurityAuditLogBase(BaseModel):
    """Base schema for security audit log."""

    event_type: SecurityEventType
    severity: SecuritySeverity
    user_id: Optional[UUID] = None
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = None
    resource_type: Optional[str] = Field(None, max_length=100)
    resource_id: Optional[str] = Field(None, max_length=255)
    action: str = Field(..., max_length=100)
    result: str = Field(..., pattern="^(SUCCESS|FAILURE|BLOCKED)$")
    details: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class SecurityAuditLogCreate(SecurityAuditLogBase):
    """Schema for creating security audit log."""
    pass


class SecurityAuditLogResponse(SecurityAuditLogBase):
    """Schema for security audit log response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


class SecurityAuditLogFilter(BaseModel):
    """Schema for filtering security audit logs."""

    event_type: Optional[SecurityEventType] = None
    severity: Optional[SecuritySeverity] = None
    user_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    result: Optional[str] = None


class SecurityMetrics(BaseModel):
    """Security metrics summary."""

    total_events: int
    events_by_type: Dict[str, int]
    events_by_severity: Dict[str, int]
    failed_login_attempts: int
    suspicious_activities: int
    blocked_requests: int
    unique_users_affected: int
    time_range: Dict[str, datetime]
