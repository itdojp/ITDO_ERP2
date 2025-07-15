"""Extended audit log schemas."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AuditLogLevel(str, Enum):
    """Audit log severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLogCategory(str, Enum):
    """Audit log categories."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SYSTEM_CONFIG = "system_config"
    USER_MANAGEMENT = "user_management"
    PERMISSION_CHANGE = "permission_change"
    SECURITY_EVENT = "security_event"


class AuditLogFilter(BaseModel):
    """Filter criteria for audit logs."""

    user_id: Optional[int] = Field(None, description="Filter by user ID")
    entity_type: Optional[str] = Field(None, description="Filter by entity type")
    entity_id: Optional[int] = Field(None, description="Filter by entity ID")
    action: Optional[str] = Field(None, description="Filter by action")
    category: Optional[AuditLogCategory] = Field(None, description="Filter by category")
    level: Optional[AuditLogLevel] = Field(None, description="Filter by level")
    date_from: Optional[datetime] = Field(None, description="Start date")
    date_to: Optional[datetime] = Field(None, description="End date")
    ip_address: Optional[str] = Field(None, description="Filter by IP address")
    success: Optional[bool] = Field(None, description="Filter by success status")


class AuditLogDetail(BaseModel):
    """Detailed audit log entry."""

    id: int
    user_id: Optional[int]
    user_email: Optional[str]
    user_name: Optional[str]
    action: str
    entity_type: str
    entity_id: Optional[int]
    entity_name: Optional[str]
    category: Optional[AuditLogCategory]
    level: AuditLogLevel = Field(default=AuditLogLevel.INFO)
    success: bool = Field(True, description="Whether the action was successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]
    session_id: Optional[str]
    changes: Optional[Dict[str, Any]]
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime


class AuditLogSummary(BaseModel):
    """Summary statistics for audit logs."""

    total_count: int
    date_range: Dict[str, datetime]
    by_category: Dict[str, int]
    by_level: Dict[str, int]
    by_action: Dict[str, int]
    by_entity_type: Dict[str, int]
    by_user: List[Dict[str, Any]]
    failed_attempts: int
    unique_users: int
    unique_ips: int


class AuditLogExport(BaseModel):
    """Audit log export request."""

    filter: AuditLogFilter
    format: str = Field("csv", description="Export format: csv, json, xlsx")
    include_fields: Optional[List[str]] = Field(None, description="Fields to include")
    exclude_fields: Optional[List[str]] = Field(None, description="Fields to exclude")
    timezone: str = Field("UTC", description="Timezone for date formatting")


class AuditLogRetentionPolicy(BaseModel):
    """Audit log retention policy."""

    id: int
    name: str
    description: Optional[str]
    category: Optional[AuditLogCategory]
    level: Optional[AuditLogLevel]
    retention_days: int = Field(..., gt=0, description="Days to retain logs")
    archive_enabled: bool = Field(
        False, description="Whether to archive before deletion"
    )
    archive_location: Optional[str]
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class AuditLogAlert(BaseModel):
    """Alert configuration for audit events."""

    id: int
    name: str
    description: Optional[str]
    category: Optional[AuditLogCategory]
    level: Optional[AuditLogLevel]
    action_pattern: Optional[str] = Field(None, description="Regex pattern for actions")
    threshold: Optional[int] = Field(
        None, description="Number of events to trigger alert"
    )
    time_window: Optional[int] = Field(None, description="Time window in minutes")
    alert_channels: List[str] = Field(
        ..., description="Alert channels: email, slack, webhook"
    )
    alert_recipients: List[str]
    is_active: bool = True
    last_triggered: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class AuditLogAlertCreate(BaseModel):
    """Create audit log alert request."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[AuditLogCategory]
    level: Optional[AuditLogLevel]
    action_pattern: Optional[str]
    threshold: Optional[int] = Field(None, gt=0)
    time_window: Optional[int] = Field(None, gt=0)
    alert_channels: List[str]
    alert_recipients: List[str]
    is_active: bool = True


class AuditTrailReport(BaseModel):
    """Comprehensive audit trail report."""

    report_id: str
    generated_at: datetime
    generated_by: int
    period_start: datetime
    period_end: datetime
    summary: AuditLogSummary
    high_risk_events: List[AuditLogDetail]
    failed_access_attempts: List[AuditLogDetail]
    permission_changes: List[AuditLogDetail]
    data_modifications: List[AuditLogDetail]
    anomalies: List[Dict[str, Any]]
    recommendations: List[str]
