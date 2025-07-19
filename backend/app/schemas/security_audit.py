"""Security audit schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.security_audit import RiskLevel, SecurityEventType


class SecurityAuditLogBase(BaseModel):
    """Base schema for security audit log."""

    event_type: SecurityEventType
    risk_level: RiskLevel = RiskLevel.LOW
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    description: str = Field(..., description="Description of the security event")
    details: Dict[str, Any] = Field(default_factory=dict)
    detection_method: Optional[str] = None
    is_automated_detection: bool = False
    requires_attention: bool = False


class SecurityAuditLogCreate(SecurityAuditLogBase):
    """Schema for creating security audit log."""

    user_id: Optional[int] = None
    organization_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None


class SecurityAuditLogUpdate(BaseModel):
    """Schema for updating security audit log."""

    is_resolved: Optional[bool] = None
    resolved_by: Optional[int] = None
    resolution_notes: Optional[str] = None


class SecurityAuditLogResponse(SecurityAuditLogBase):
    """Schema for security audit log responses."""

    id: int
    user_id: Optional[int]
    organization_id: Optional[int]
    ip_address: Optional[str]
    user_agent: Optional[str]
    session_id: Optional[str]
    is_resolved: bool
    resolved_by: Optional[int]
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class SecurityAlertBase(BaseModel):
    """Base schema for security alert."""

    alert_type: str
    severity: RiskLevel
    title: str = Field(..., max_length=255)
    message: str
    recipients: List[str] = Field(default_factory=list)


class SecurityAlertCreate(SecurityAlertBase):
    """Schema for creating security alert."""

    security_audit_log_id: int


class SecurityAlertResponse(SecurityAlertBase):
    """Schema for security alert responses."""

    id: int
    security_audit_log_id: int
    is_sent: bool
    sent_at: Optional[datetime]
    is_acknowledged: bool
    acknowledged_by: Optional[int]
    acknowledged_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class SecurityEventFilter(BaseModel):
    """Filter for security events."""

    event_types: Optional[List[SecurityEventType]] = None
    risk_levels: Optional[List[RiskLevel]] = None
    user_id: Optional[int] = None
    organization_id: Optional[int] = None
    ip_address: Optional[str] = None
    requires_attention: Optional[bool] = None
    is_resolved: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SecurityAnalytics(BaseModel):
    """Security analytics response."""

    total_events: int
    events_by_type: Dict[str, int]
    events_by_risk_level: Dict[str, int]
    unresolved_high_risk_count: int
    top_users_by_activity: List[Dict[str, Any]]
    top_ip_addresses: List[Dict[str, Any]]
    failed_login_attempts: int
    suspicious_activities: int
    recent_privilege_escalations: List[SecurityAuditLogResponse]
    security_trend: Dict[str, Any]  # Daily/weekly trends


class SecurityReport(BaseModel):
    """Comprehensive security report."""

    period: str
    start_date: datetime
    end_date: datetime
    summary: SecurityAnalytics
    critical_events: List[SecurityAuditLogResponse]
    recommendations: List[str]
    compliance_status: Dict[str, Any]
