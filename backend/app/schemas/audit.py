"""Audit log schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class AuditLogBase(BaseModel):
    """Base audit log schema."""

    user_id: int = Field(description="User who performed the action")
    action: str = Field(description="Action performed")
    resource_type: str = Field(description="Type of resource affected")
    resource_id: Optional[int] = Field(
        default=None, description="ID of affected resource"
    )
    organization_id: int = Field(description="Organization context")
    changes: Optional[Dict[str, Any]] = Field(default=None, description="Changes made")
    ip_address: Optional[str] = Field(default=None, description="IP address")
    user_agent: Optional[str] = Field(default=None, description="User agent string")


class AuditLogCreate(AuditLogBase):
    """Schema for creating audit logs."""



class AuditLogResponse(AuditLogBase):
    """Schema for audit log responses."""

    id: int = Field(description="Audit log ID")
    created_at: datetime = Field(description="When the log was created")
    checksum: str = Field(description="Integrity checksum")
    user_email: Optional[str] = Field(default=None, description="User email")
    user_full_name: Optional[str] = Field(default=None, description="User full name")

    class Config:
        from_attributes = True


class AuditLogFilter(BaseModel):
    """Schema for filtering audit logs."""

    user_id: Optional[int] = Field(default=None, description="Filter by user ID")
    action: Optional[str] = Field(default=None, description="Filter by action")
    resource_type: Optional[str] = Field(
        default=None, description="Filter by resource type"
    )
    resource_id: Optional[int] = Field(
        default=None, description="Filter by resource ID"
    )
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")
    limit: int = Field(default=50, ge=1, le=1000, description="Number of results")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


class AuditLogSearch(BaseModel):
    """Advanced search schema for audit logs."""

    organization_id: int = Field(description="Organization ID")
    user_ids: Optional[List[int]] = Field(
        default=None, description="Filter by user IDs"
    )
    actions: Optional[List[str]] = Field(default=None, description="Filter by actions")
    resource_types: Optional[List[str]] = Field(
        default=None, description="Filter by resource types"
    )
    resource_ids: Optional[List[int]] = Field(
        default=None, description="Filter by resource IDs"
    )
    date_from: Optional[datetime] = Field(default=None, description="Start date range")
    date_to: Optional[datetime] = Field(default=None, description="End date range")
    changes_contain: Optional[str] = Field(
        default=None, description="Search in changes JSON"
    )
    ip_address: Optional[str] = Field(default=None, description="Filter by IP address")
    limit: int = Field(default=50, ge=1, le=1000, description="Number of results")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")

    @validator("sort_order")
    def validate_sort_order(cls, v: str) -> str:
        if v not in ["asc", "desc"]:
            raise ValueError('sort_order must be "asc" or "desc"')
        return v

    @validator("sort_by")
    def validate_sort_by(cls, v: str) -> str:
        allowed_fields = ["created_at", "action", "resource_type", "user_id"]
        if v not in allowed_fields:
            raise ValueError(f"sort_by must be one of: {', '.join(allowed_fields)}")
        return v


class AuditLogListResponse(BaseModel):
    """Paginated audit log list response."""

    items: List[AuditLogResponse] = Field(description="Audit log items")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")


class AuditLogStats(BaseModel):
    """Audit log statistics schema."""

    total_logs: int = Field(description="Total number of audit logs")
    unique_users: int = Field(description="Number of unique users")
    unique_actions: int = Field(description="Number of unique actions")
    unique_resource_types: int = Field(description="Number of unique resource types")
    action_counts: Dict[str, int] = Field(description="Count by action type")
    resource_type_counts: Dict[str, int] = Field(description="Count by resource type")
    daily_counts: Dict[str, int] = Field(description="Daily activity counts")
    date_from: datetime = Field(description="Statistics start date")
    date_to: datetime = Field(description="Statistics end date")


class AuditLogIntegrityResult(BaseModel):
    """Audit log integrity check result."""

    log_id: int = Field(description="Audit log ID")
    is_valid: bool = Field(description="Whether the log is valid")
    expected_checksum: str = Field(description="Expected checksum")
    actual_checksum: str = Field(description="Actual checksum")
    error_message: Optional[str] = Field(default=None, description="Error details")


class AuditLogBulkIntegrityResult(BaseModel):
    """Bulk audit log integrity check result."""

    total_checked: int = Field(description="Total logs checked")
    valid_count: int = Field(description="Number of valid logs")
    corrupted_count: int = Field(description="Number of corrupted logs")
    integrity_percentage: float = Field(description="Integrity percentage")
    corrupted_log_ids: List[int] = Field(description="IDs of corrupted logs")
    check_duration_seconds: float = Field(description="Time taken for check")


class AuditLogExportRequest(BaseModel):
    """Audit log export request schema."""

    organization_id: int = Field(description="Organization ID")
    format: str = Field(default="csv", description="Export format")
    date_from: Optional[datetime] = Field(default=None, description="Start date")
    date_to: Optional[datetime] = Field(default=None, description="End date")
    actions: Optional[List[str]] = Field(default=None, description="Filter by actions")
    resource_types: Optional[List[str]] = Field(
        default=None, description="Filter by resource types"
    )
    include_sensitive: bool = Field(default=False, description="Include sensitive data")

    @validator("format")
    def validate_format(cls, v: str) -> str:
        if v not in ["csv", "json", "xlsx"]:
            raise ValueError('format must be "csv", "json", or "xlsx"')
        return v


class AuditLogRetentionRequest(BaseModel):
    """Audit log retention policy request."""

    organization_id: int = Field(description="Organization ID")
    retention_days: int = Field(ge=30, le=3650, description="Retention period in days")
    dry_run: bool = Field(default=True, description="Whether to perform dry run")
    archive_before_delete: bool = Field(
        default=True, description="Archive before deletion"
    )


class AuditLogRetentionResult(BaseModel):
    """Audit log retention policy result."""

    affected_logs: int = Field(description="Number of affected logs")
    archived_logs: int = Field(description="Number of archived logs")
    deleted_logs: int = Field(description="Number of deleted logs")
    oldest_remaining_date: Optional[datetime] = Field(
        default=None, description="Oldest remaining log date"
    )
    execution_time_seconds: float = Field(description="Execution time")


class AuditLogAlert(BaseModel):
    """Audit log alert schema."""

    id: int = Field(description="Alert ID")
    organization_id: int = Field(description="Organization ID")
    alert_type: str = Field(description="Type of alert")
    severity: str = Field(description="Alert severity")
    title: str = Field(description="Alert title")
    description: str = Field(description="Alert description")
    triggered_by_log_id: int = Field(description="Log that triggered the alert")
    is_acknowledged: bool = Field(
        default=False, description="Whether alert is acknowledged"
    )
    created_at: datetime = Field(description="When alert was created")
    acknowledged_at: Optional[datetime] = Field(
        default=None, description="When acknowledged"
    )
    acknowledged_by: Optional[int] = Field(default=None, description="Who acknowledged")

    class Config:
        from_attributes = True
