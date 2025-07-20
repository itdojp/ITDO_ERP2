"""Security monitoring schemas for Issue #46."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SecurityThreatBase(BaseModel):
    """Base security threat schema."""
    
    threat_type: str = Field(..., description="Type of security threat")
    severity: str = Field(..., description="Threat severity level")
    description: str = Field(..., description="Human-readable threat description")
    details: Dict[str, Any] = Field(..., description="Detailed threat information")


class SecurityThreatResponse(SecurityThreatBase):
    """Security threat response schema."""
    
    timestamp: datetime = Field(..., description="When the threat was detected")


class SecurityDashboardResponse(BaseModel):
    """Security dashboard response schema."""
    
    timestamp: str = Field(..., description="Dashboard generation timestamp")
    organization_id: Optional[int] = Field(None, description="Organization filter applied")
    
    threats: Dict[str, Any] = Field(..., description="Threat statistics and recent threats")
    metrics: Dict[str, Any] = Field(..., description="Security metrics")
    monitoring_status: Dict[str, bool] = Field(..., description="Monitoring feature status")


class SecurityReportResponse(BaseModel):
    """Security report response schema."""
    
    report_period: Dict[str, str] = Field(..., description="Report time period")
    summary: Dict[str, int] = Field(..., description="Report summary statistics")
    top_activities: Dict[str, Dict[str, int]] = Field(..., description="Top activities breakdown")
    security_insights: Dict[str, int] = Field(..., description="Security-specific insights")


class MonitoringStatusResponse(BaseModel):
    """Monitoring status response schema."""
    
    monitoring_active: bool = Field(..., description="Whether monitoring is active")
    service_status: str = Field(..., description="Service operational status")
    features: Dict[str, bool] = Field(..., description="Feature availability status")
    thresholds: Dict[str, str] = Field(..., description="Monitoring thresholds")
    timestamp: str = Field(..., description="Status check timestamp")


class ThreatListResponse(BaseModel):
    """Threat list response schema."""
    
    threats: List[SecurityThreatResponse] = Field(..., description="List of detected threats")
    total_count: int = Field(..., description="Total number of threats")
    filters_applied: Dict[str, Any] = Field(..., description="Filters that were applied")


class FailedLoginMonitoringResponse(BaseModel):
    """Failed login monitoring response schema."""
    
    failed_login_threats: List[SecurityThreatResponse] = Field(..., description="Failed login threats")
    monitoring_config: Dict[str, Any] = Field(..., description="Monitoring configuration")


class BulkAccessMonitoringResponse(BaseModel):
    """Bulk access monitoring response schema."""
    
    bulk_access_threats: List[SecurityThreatResponse] = Field(..., description="Bulk access threats")
    monitoring_config: Dict[str, Any] = Field(..., description="Monitoring configuration")


class PrivilegeEscalationMonitoringResponse(BaseModel):
    """Privilege escalation monitoring response schema."""
    
    privilege_escalation_threats: List[SecurityThreatResponse] = Field(..., description="Privilege escalation threats")
    monitoring_enabled: bool = Field(..., description="Whether privilege escalation monitoring is enabled")


class AlertTestResponse(BaseModel):
    """Alert test response schema."""
    
    message: str = Field(..., description="Test initiation confirmation message")


# Security alert configuration schemas
class AlertConfigBase(BaseModel):
    """Base alert configuration schema."""
    
    enabled: bool = Field(True, description="Whether alerts are enabled")
    threshold: int = Field(..., description="Alert threshold value")
    time_window_minutes: int = Field(..., description="Time window in minutes")


class FailedLoginAlertConfig(AlertConfigBase):
    """Failed login alert configuration."""
    
    threshold: int = Field(5, description="Number of failed attempts to trigger alert")
    time_window_minutes: int = Field(15, description="Time window for counting failed attempts")


class BulkAccessAlertConfig(AlertConfigBase):
    """Bulk access alert configuration."""
    
    threshold: int = Field(100, description="Number of access attempts to trigger alert")
    time_window_minutes: int = Field(5, description="Time window for counting access attempts")


class SecurityConfigResponse(BaseModel):
    """Security configuration response schema."""
    
    failed_login_alerts: FailedLoginAlertConfig
    bulk_access_alerts: BulkAccessAlertConfig
    privilege_escalation_monitoring: bool = Field(True, description="Privilege escalation monitoring enabled")
    unusual_pattern_monitoring: bool = Field(True, description="Unusual pattern monitoring enabled")


# Real-time monitoring schemas
class RealTimeEventBase(BaseModel):
    """Base real-time event schema."""
    
    event_type: str = Field(..., description="Type of security event")
    severity: str = Field(..., description="Event severity")
    timestamp: datetime = Field(..., description="Event timestamp")
    user_id: Optional[int] = Field(None, description="Associated user ID")
    ip_address: Optional[str] = Field(None, description="Source IP address")
    organization_id: Optional[int] = Field(None, description="Associated organization ID")


class RealTimeSecurityEvent(RealTimeEventBase):
    """Real-time security event schema."""
    
    description: str = Field(..., description="Event description")
    details: Dict[str, Any] = Field(..., description="Detailed event information")
    threat_level: str = Field(..., description="Calculated threat level")


class SecurityMetrics(BaseModel):
    """Security metrics schema."""
    
    failed_logins_today: int = Field(..., description="Failed login attempts today")
    successful_logins_today: int = Field(..., description="Successful logins today")
    login_success_rate: float = Field(..., description="Login success rate percentage")
    active_threats: int = Field(..., description="Number of active threats")
    resolved_threats_today: int = Field(0, description="Threats resolved today")


class ThreatTrendData(BaseModel):
    """Threat trend data schema."""
    
    date: str = Field(..., description="Date for the data point")
    threat_count: int = Field(..., description="Number of threats on this date")
    severity_breakdown: Dict[str, int] = Field(..., description="Breakdown by severity")


class SecurityTrendResponse(BaseModel):
    """Security trend response schema."""
    
    period_days: int = Field(..., description="Number of days covered")
    trend_data: List[ThreatTrendData] = Field(..., description="Daily trend data")
    summary: Dict[str, Any] = Field(..., description="Trend summary statistics")