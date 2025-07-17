"""
Security Monitoring Schemas for Issue #46.
セキュリティ監視スキーマ（Issue #46）
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ThreatDetectionRequest(BaseModel):
    """Request schema for threat detection."""
    
    time_window_hours: int = Field(24, ge=1, le=168, description="Time window in hours")
    max_failed_logins: int = Field(5, ge=1, le=50, description="Max failed login threshold")
    max_privilege_escalations: int = Field(3, ge=1, le=20, description="Max privilege escalation threshold")


class SuspiciousActivity(BaseModel):
    """Schema for suspicious activity item."""
    
    user_id: int
    username: str
    risk_level: str = Field(..., description="Risk level: low, medium, high, critical")
    recommended_action: str
    last_occurrence: str = Field(..., description="ISO format datetime")


class FailedLoginActivity(SuspiciousActivity):
    """Schema for failed login suspicious activity."""
    
    failed_count: int
    ip_addresses: List[str] = Field(default_factory=list)


class PrivilegeEscalationActivity(SuspiciousActivity):
    """Schema for privilege escalation suspicious activity."""
    
    escalation_count: int
    resources_modified: List[str] = Field(default_factory=list)


class BulkDataAccessActivity(SuspiciousActivity):
    """Schema for bulk data access suspicious activity."""
    
    access_count: int
    resource_types: int
    last_access: str


class AfterHoursAccessActivity(SuspiciousActivity):
    """Schema for after-hours access suspicious activity."""
    
    after_hours_count: int
    ip_addresses: List[str] = Field(default_factory=list)


class SuspiciousIPActivity(SuspiciousActivity):
    """Schema for suspicious IP pattern activity."""
    
    unique_ips: int
    ip_addresses: List[str] = Field(default_factory=list)


class ThreatSummary(BaseModel):
    """Schema for threat detection summary."""
    
    total_threats: int
    high_risk_users: List[int] = Field(default_factory=list)
    threat_score: int = Field(..., ge=0, le=100)
    risk_level: str = Field(..., description="Overall risk level: low, medium, high, critical")


class ThreatDetectionResponse(BaseModel):
    """Schema for threat detection response."""
    
    detection_time: str = Field(..., description="ISO format datetime")
    time_window_hours: int
    failed_logins: List[FailedLoginActivity] = Field(default_factory=list)
    privilege_escalations: List[PrivilegeEscalationActivity] = Field(default_factory=list)
    bulk_data_access: List[BulkDataAccessActivity] = Field(default_factory=list)
    after_hours_access: List[AfterHoursAccessActivity] = Field(default_factory=list)
    suspicious_ip_patterns: List[SuspiciousIPActivity] = Field(default_factory=list)
    summary: ThreatSummary


class SecurityAlert(BaseModel):
    """Schema for security alert."""
    
    alert_id: str
    alert_type: str
    severity: str = Field(..., description="Alert severity: low, medium, high, critical")
    generated_at: str = Field(..., description="ISO format datetime")
    threat_score: int = Field(..., ge=0, le=100)
    affected_users: int
    total_incidents: int
    recommended_actions: List[str] = Field(default_factory=list)
    details: Dict = Field(default_factory=dict)


class SecurityMetricsPeriod(BaseModel):
    """Schema for security metrics time period."""
    
    start_date: str = Field(..., description="ISO format datetime")
    end_date: str = Field(..., description="ISO format datetime")
    days: int


class SecurityMetricsData(BaseModel):
    """Schema for security metrics data."""
    
    total_audit_logs: int
    failed_logins: int
    successful_logins: int
    active_users: int
    permission_changes: int
    login_failure_rate: float = Field(..., ge=0, le=100)


class SecurityHealth(BaseModel):
    """Schema for security health status."""
    
    status: str = Field(..., description="Health status: good, warning, critical")
    recommendations: List[str] = Field(default_factory=list)


class SecurityMetricsResponse(BaseModel):
    """Schema for security metrics response."""
    
    period: SecurityMetricsPeriod
    metrics: SecurityMetricsData
    security_health: SecurityHealth


class UserRiskAssessment(BaseModel):
    """Schema for user risk assessment."""
    
    user_id: int
    risk_level: str = Field(..., description="Risk level: low, medium, high")
    risk_score: int = Field(..., ge=0, le=100)
    risk_factors: List[str] = Field(default_factory=list)
    recent_activity: Dict = Field(default_factory=dict)
    assessment_date: str = Field(..., description="ISO format datetime")


class SecurityEventLog(BaseModel):
    """Schema for security event logging."""
    
    event_type: str
    details: Dict
    target_user_id: Optional[int] = None


class SecurityEventResponse(BaseModel):
    """Schema for security event log response."""
    
    status: str
    message: str
    event_type: str
    logged_by: int
    target_user: Optional[int] = None


class SecurityDashboard(BaseModel):
    """Schema for security monitoring dashboard."""
    
    dashboard_type: str = Field(default="security_monitoring")
    generated_at: str = Field(..., description="ISO format datetime")
    threat_summary: ThreatSummary
    recent_threats: Dict = Field(default_factory=dict)
    security_metrics: SecurityMetricsData
    security_health: SecurityHealth
    high_risk_users: List[int] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


# Export schemas for API response models
class AlertGenerationRequest(BaseModel):
    """Schema for alert generation request."""
    
    threat_data: Dict
    alert_type: str = Field(default="security_incident")


class MetricsRequest(BaseModel):
    """Schema for metrics request."""
    
    days_back: int = Field(30, ge=1, le=365, description="Days to look back")


# Audit Log Enhancement Schemas
class AuditLogFilter(BaseModel):
    """Schema for audit log filtering."""
    
    user_id: Optional[int] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    organization_id: Optional[int] = None


class AuditLogExport(BaseModel):
    """Schema for audit log export configuration."""
    
    format: str = Field("csv", description="Export format: csv, xlsx, json")
    filters: Optional[AuditLogFilter] = None
    include_user_details: bool = Field(True, description="Include user information")
    include_changes: bool = Field(True, description="Include change details")


class AuditLogResponse(BaseModel):
    """Schema for audit log response."""
    
    id: int
    user_id: int
    username: str
    action: str
    resource_type: str
    resource_id: int
    organization_id: Optional[int] = None
    changes: Dict = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: str = Field(..., description="ISO format datetime")
    integrity_verified: bool = Field(default=True)


class AuditLogListResponse(BaseModel):
    """Schema for audit log list response."""
    
    items: List[AuditLogResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool