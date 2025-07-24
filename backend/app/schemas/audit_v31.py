"""
Audit Log System Schemas - CC02 v31.0 Phase 2

Comprehensive Pydantic schemas for audit log system including:
- System-wide Activity Tracking
- Compliance & Regulatory Auditing
- Security Event Monitoring
- Data Change Tracking
- User Action Logging
- Performance Monitoring
- Risk Assessment & Alerting
- Forensic Analysis Support
- Real-time Monitoring
- Automated Compliance Reporting

Provides complete audit trail validation for enterprise compliance and security
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.models.audit_extended import (
    AuditEventType,
    AuditSeverity,
    AuditStatus,
    ComplianceFramework,
)

# =============================================================================
# Base Schemas
# =============================================================================


class BaseAuditSchema(BaseModel):
    """Base schema for audit-related models."""

    class Config:
        orm_mode = True
        use_enum_values = True


# =============================================================================
# Audit Log Entry Schemas
# =============================================================================


class AuditLogEntryCreateRequest(BaseAuditSchema):
    """Schema for creating a new audit log entry."""

    organization_id: str = Field(..., description="Organization ID")
    event_type: AuditEventType = Field(..., description="Event type")
    event_category: str = Field(
        ..., min_length=1, max_length=100, description="Event category"
    )
    event_name: str = Field(..., min_length=1, max_length=200, description="Event name")
    event_description: Optional[str] = Field(None, description="Event description")

    # Actor information
    user_id: Optional[str] = Field(None, description="User ID")
    actor_type: str = Field("user", description="Actor type")
    actor_name: Optional[str] = Field(None, max_length=200, description="Actor name")
    impersonated_user_id: Optional[str] = Field(
        None, description="Impersonated user ID"
    )

    # Target/Resource information
    resource_type: Optional[str] = Field(
        None, max_length=100, description="Resource type"
    )
    resource_id: Optional[str] = Field(None, max_length=200, description="Resource ID")
    resource_name: Optional[str] = Field(
        None, max_length=500, description="Resource name"
    )

    # Event details
    action_performed: Optional[str] = Field(
        None, max_length=200, description="Action performed"
    )
    outcome: str = Field("success", description="Event outcome")
    severity: AuditSeverity = Field(AuditSeverity.LOW, description="Event severity")

    # Context data
    old_values: Optional[Dict[str, Any]] = Field(None, description="Old values")
    new_values: Optional[Dict[str, Any]] = Field(None, description="New values")
    change_details: Dict[str, Any] = Field(
        default_factory=dict, description="Change details"
    )
    event_data: Dict[str, Any] = Field(default_factory=dict, description="Event data")

    # Session and request information
    session_id: Optional[str] = Field(None, max_length=200, description="Session ID")
    request_id: Optional[str] = Field(None, max_length=200, description="Request ID")
    correlation_id: Optional[str] = Field(
        None, max_length=200, description="Correlation ID"
    )

    # Network information
    ip_address: Optional[str] = Field(None, max_length=45, description="IP address")
    user_agent: Optional[str] = Field(None, max_length=1000, description="User agent")
    source_system: Optional[str] = Field(
        None, max_length=100, description="Source system"
    )

    # Compliance and risk
    compliance_frameworks: List[str] = Field(
        default_factory=list, description="Compliance frameworks"
    )
    tags: List[str] = Field(default_factory=list, description="Tags")

    # Event timestamp
    event_timestamp: Optional[datetime] = Field(None, description="Event timestamp")

    @validator("outcome")
    def validate_outcome(cls, v) -> dict:
        """Validate outcome values."""
        valid_outcomes = ["success", "failure", "partial"]
        if v not in valid_outcomes:
            raise ValueError(f"Outcome must be one of: {valid_outcomes}")
        return v

    @validator("ip_address")
    def validate_ip_address(cls, v) -> dict:
        """Basic IP address validation."""
        if v and not (len(v.split(".")) == 4 or ":" in v):
            raise ValueError("Invalid IP address format")
        return v


class AuditLogEntryResponse(BaseAuditSchema):
    """Schema for audit log entry response."""

    id: str = Field(..., description="Entry ID")
    organization_id: str = Field(..., description="Organization ID")
    event_type: AuditEventType = Field(..., description="Event type")
    event_category: str = Field(..., description="Event category")
    event_name: str = Field(..., description="Event name")
    event_description: Optional[str] = Field(None, description="Event description")

    # Actor information
    user_id: Optional[str] = Field(None, description="User ID")
    actor_type: str = Field(..., description="Actor type")
    actor_name: Optional[str] = Field(None, description="Actor name")
    impersonated_user_id: Optional[str] = Field(
        None, description="Impersonated user ID"
    )

    # Target/Resource information
    resource_type: Optional[str] = Field(None, description="Resource type")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    resource_name: Optional[str] = Field(None, description="Resource name")

    # Event details
    action_performed: Optional[str] = Field(None, description="Action performed")
    outcome: str = Field(..., description="Event outcome")
    severity: AuditSeverity = Field(..., description="Event severity")

    # Context data
    old_values: Optional[Dict[str, Any]] = Field(None, description="Old values")
    new_values: Optional[Dict[str, Any]] = Field(None, description="New values")
    change_details: Dict[str, Any] = Field(..., description="Change details")
    event_data: Dict[str, Any] = Field(..., description="Event data")

    # Session and request information
    session_id: Optional[str] = Field(None, description="Session ID")
    request_id: Optional[str] = Field(None, description="Request ID")
    correlation_id: Optional[str] = Field(None, description="Correlation ID")

    # Network information
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    source_system: Optional[str] = Field(None, description="Source system")

    # Compliance and risk
    compliance_frameworks: List[str] = Field(..., description="Compliance frameworks")
    risk_score: int = Field(..., description="Risk score")
    tags: List[str] = Field(..., description="Tags")

    # Status and handling
    status: AuditStatus = Field(..., description="Entry status")
    acknowledged_by: Optional[str] = Field(None, description="Acknowledged by user ID")
    acknowledged_at: Optional[datetime] = Field(
        None, description="Acknowledgment timestamp"
    )
    resolution_notes: Optional[str] = Field(None, description="Resolution notes")

    # Timestamps
    event_timestamp: datetime = Field(..., description="Event timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")


class AuditLogSearchRequest(BaseAuditSchema):
    """Schema for audit log search request."""

    organization_id: str = Field(..., description="Organization ID")

    # Filter parameters
    event_type: Optional[AuditEventType] = Field(
        None, description="Filter by event type"
    )
    event_category: Optional[str] = Field(None, description="Filter by event category")
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    resource_type: Optional[str] = Field(None, description="Filter by resource type")
    resource_id: Optional[str] = Field(None, description="Filter by resource ID")
    severity: Optional[AuditSeverity] = Field(None, description="Filter by severity")
    outcome: Optional[str] = Field(None, description="Filter by outcome")
    ip_address: Optional[str] = Field(None, description="Filter by IP address")
    session_id: Optional[str] = Field(None, description="Filter by session ID")

    # Date range
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")

    # Risk score range
    min_risk_score: Optional[int] = Field(
        None, ge=0, le=100, description="Minimum risk score"
    )
    max_risk_score: Optional[int] = Field(
        None, ge=0, le=100, description="Maximum risk score"
    )

    # Compliance framework
    compliance_framework: Optional[str] = Field(
        None, description="Filter by compliance framework"
    )

    # Text search
    search_text: Optional[str] = Field(None, description="Text search in descriptions")

    # Sorting
    sort_by: str = Field("event_timestamp", description="Sort field")
    sort_order: str = Field("desc", description="Sort order")

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(50, ge=1, le=1000, description="Items per page")

    @validator("sort_order")
    def validate_sort_order(cls, v) -> dict:
        """Validate sort order."""
        if v not in ["asc", "desc"]:
            raise ValueError('Sort order must be "asc" or "desc"')
        return v


class AuditLogListResponse(BaseAuditSchema):
    """Schema for audit log list response."""

    entries: List[AuditLogEntryResponse] = Field(..., description="Audit log entries")
    total_count: int = Field(..., description="Total count")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Items per page")
    has_more: bool = Field(False, description="Has more items")


class AuditLogBulkCreateRequest(BaseAuditSchema):
    """Schema for bulk creating audit log entries."""

    entries: List[AuditLogEntryCreateRequest] = Field(
        ..., min_items=1, max_items=1000, description="List of audit entries to create"
    )


# =============================================================================
# Audit Rule Schemas
# =============================================================================


class AuditRuleCreateRequest(BaseAuditSchema):
    """Schema for creating audit rule."""

    organization_id: str = Field(..., description="Organization ID")
    name: str = Field(..., min_length=1, max_length=200, description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    rule_type: str = Field(..., description="Rule type")

    # Rule conditions
    conditions: Dict[str, Any] = Field(..., description="Rule conditions")
    event_filters: Dict[str, Any] = Field(
        default_factory=dict, description="Event filters"
    )
    threshold_config: Dict[str, Any] = Field(
        default_factory=dict, description="Threshold configuration"
    )

    # Actions
    actions: List[str] = Field(default_factory=list, description="Actions to take")
    alert_severity: AuditSeverity = Field(
        AuditSeverity.MEDIUM, description="Alert severity"
    )

    # Compliance mapping
    compliance_frameworks: List[str] = Field(
        default_factory=list, description="Compliance frameworks"
    )
    regulatory_requirements: List[str] = Field(
        default_factory=list, description="Regulatory requirements"
    )

    # Rule settings
    is_active: bool = Field(True, description="Rule active status")
    priority: int = Field(50, ge=1, le=100, description="Rule priority")
    evaluation_frequency: str = Field("real_time", description="Evaluation frequency")

    created_by: str = Field(..., description="Creator user ID")

    @validator("rule_type")
    def validate_rule_type(cls, v) -> dict:
        """Validate rule type."""
        valid_types = ["event_trigger", "threshold", "pattern", "anomaly"]
        if v not in valid_types:
            raise ValueError(f"Rule type must be one of: {valid_types}")
        return v

    @validator("evaluation_frequency")
    def validate_evaluation_frequency(cls, v) -> dict:
        """Validate evaluation frequency."""
        valid_frequencies = ["real_time", "hourly", "daily", "weekly"]
        if v not in valid_frequencies:
            raise ValueError(
                f"Evaluation frequency must be one of: {valid_frequencies}"
            )
        return v


class AuditRuleResponse(BaseAuditSchema):
    """Schema for audit rule response."""

    id: str = Field(..., description="Rule ID")
    organization_id: str = Field(..., description="Organization ID")
    name: str = Field(..., description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    rule_type: str = Field(..., description="Rule type")

    # Rule conditions
    conditions: Dict[str, Any] = Field(..., description="Rule conditions")
    event_filters: Dict[str, Any] = Field(..., description="Event filters")
    threshold_config: Dict[str, Any] = Field(..., description="Threshold configuration")

    # Actions
    actions: List[str] = Field(..., description="Actions to take")
    alert_severity: AuditSeverity = Field(..., description="Alert severity")

    # Compliance mapping
    compliance_frameworks: List[str] = Field(..., description="Compliance frameworks")
    regulatory_requirements: List[str] = Field(
        ..., description="Regulatory requirements"
    )

    # Rule settings
    is_active: bool = Field(..., description="Rule active status")
    priority: int = Field(..., description="Rule priority")
    evaluation_frequency: str = Field(..., description="Evaluation frequency")

    # Performance tracking
    trigger_count: int = Field(..., description="Trigger count")
    last_triggered: Optional[datetime] = Field(
        None, description="Last triggered timestamp"
    )
    false_positive_count: int = Field(..., description="False positive count")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")
    created_by: str = Field(..., description="Creator user ID")


class AuditRuleTestRequest(BaseAuditSchema):
    """Schema for testing audit rule."""

    test_data: Dict[str, Any] = Field(
        ..., description="Test data to evaluate rule against"
    )


class AuditRuleListResponse(BaseAuditSchema):
    """Schema for audit rule list response."""

    rules: List[AuditRuleResponse] = Field(..., description="Audit rules")
    total_count: int = Field(..., description="Total count")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Items per page")
    has_more: bool = Field(False, description="Has more items")


# =============================================================================
# Audit Alert Schemas
# =============================================================================


class AuditAlertCreateRequest(BaseAuditSchema):
    """Schema for creating audit alert."""

    organization_id: str = Field(..., description="Organization ID")
    rule_id: str = Field(..., description="Rule ID")
    alert_type: str = Field(..., description="Alert type")
    title: str = Field(..., min_length=1, max_length=300, description="Alert title")
    description: Optional[str] = Field(None, description="Alert description")
    severity: AuditSeverity = Field(..., description="Alert severity")

    # Triggering events
    triggering_event_ids: List[str] = Field(
        default_factory=list, description="Triggering event IDs"
    )
    event_count: int = Field(1, ge=1, description="Event count")

    # Alert details
    alert_data: Dict[str, Any] = Field(default_factory=dict, description="Alert data")
    risk_assessment: Dict[str, Any] = Field(
        default_factory=dict, description="Risk assessment"
    )
    recommended_actions: List[str] = Field(
        default_factory=list, description="Recommended actions"
    )

    # Assignment
    assigned_to: Optional[str] = Field(None, description="Assigned user ID")
    priority: int = Field(50, ge=1, le=100, description="Priority")


class AuditAlertResponse(BaseAuditSchema):
    """Schema for audit alert response."""

    id: str = Field(..., description="Alert ID")
    organization_id: str = Field(..., description="Organization ID")
    rule_id: str = Field(..., description="Rule ID")
    alert_type: str = Field(..., description="Alert type")
    title: str = Field(..., description="Alert title")
    description: Optional[str] = Field(None, description="Alert description")
    severity: AuditSeverity = Field(..., description="Alert severity")

    # Triggering events
    triggering_event_ids: List[str] = Field(..., description="Triggering event IDs")
    event_count: int = Field(..., description="Event count")

    # Alert details
    alert_data: Dict[str, Any] = Field(..., description="Alert data")
    risk_assessment: Dict[str, Any] = Field(..., description="Risk assessment")
    recommended_actions: List[str] = Field(..., description="Recommended actions")

    # Status tracking
    status: str = Field(..., description="Alert status")
    assigned_to: Optional[str] = Field(None, description="Assigned user ID")
    priority: int = Field(..., description="Priority")

    # Response tracking
    acknowledged_by: Optional[str] = Field(None, description="Acknowledged by user ID")
    acknowledged_at: Optional[datetime] = Field(
        None, description="Acknowledgment timestamp"
    )
    resolved_by: Optional[str] = Field(None, description="Resolved by user ID")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    resolution_notes: Optional[str] = Field(None, description="Resolution notes")

    # Escalation
    escalation_level: int = Field(..., description="Escalation level")
    escalated_to: List[str] = Field(..., description="Escalated to users")

    # Compliance
    compliance_impact: Optional[str] = Field(None, description="Compliance impact")
    regulatory_notification_required: bool = Field(
        ..., description="Regulatory notification required"
    )
    notification_sent: bool = Field(..., description="Notification sent")

    # Timestamps
    first_occurrence: datetime = Field(..., description="First occurrence timestamp")
    last_occurrence: datetime = Field(..., description="Last occurrence timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


class AlertResolutionRequest(BaseAuditSchema):
    """Schema for resolving alert."""

    resolved_by: str = Field(..., description="User ID resolving the alert")
    resolution_notes: str = Field(..., min_length=1, description="Resolution notes")


class AuditAlertListResponse(BaseAuditSchema):
    """Schema for audit alert list response."""

    alerts: List[AuditAlertResponse] = Field(..., description="Audit alerts")
    total_count: int = Field(..., description="Total count")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Items per page")
    has_more: bool = Field(False, description="Has more items")


# =============================================================================
# Audit Report Schemas
# =============================================================================


class AuditReportCreateRequest(BaseAuditSchema):
    """Schema for creating audit report."""

    organization_id: str = Field(..., description="Organization ID")
    report_name: str = Field(
        ..., min_length=1, max_length=300, description="Report name"
    )
    report_type: str = Field(..., description="Report type")
    description: Optional[str] = Field(None, description="Report description")

    # Report parameters
    period_start: date = Field(..., description="Period start date")
    period_end: date = Field(..., description="Period end date")
    report_filters: Dict[str, Any] = Field(
        default_factory=dict, description="Report filters"
    )
    report_config: Dict[str, Any] = Field(
        default_factory=dict, description="Report configuration"
    )

    # Compliance framework
    compliance_framework: Optional[ComplianceFramework] = Field(
        None, description="Compliance framework"
    )
    regulatory_requirements: List[str] = Field(
        default_factory=list, description="Regulatory requirements"
    )

    # File format
    file_format: str = Field("pdf", description="Output file format")

    # Distribution
    recipients: List[str] = Field(default_factory=list, description="Report recipients")

    # Generation details
    generated_by: str = Field(..., description="Generator user ID")

    @validator("report_type")
    def validate_report_type(cls, v) -> dict:
        """Validate report type."""
        valid_types = ["compliance", "security", "operational", "forensic", "custom"]
        if v not in valid_types:
            raise ValueError(f"Report type must be one of: {valid_types}")
        return v

    @validator("file_format")
    def validate_file_format(cls, v) -> dict:
        """Validate file format."""
        valid_formats = ["pdf", "xlsx", "csv", "json", "html"]
        if v not in valid_formats:
            raise ValueError(f"File format must be one of: {valid_formats}")
        return v

    @validator("period_end")
    def validate_period_end(cls, v, values) -> dict:
        """Validate period end is after period start."""
        if "period_start" in values and v <= values["period_start"]:
            raise ValueError("Period end must be after period start")
        return v


class AuditReportResponse(BaseAuditSchema):
    """Schema for audit report response."""

    id: str = Field(..., description="Report ID")
    organization_id: str = Field(..., description="Organization ID")
    report_name: str = Field(..., description="Report name")
    report_type: str = Field(..., description="Report type")
    description: Optional[str] = Field(None, description="Report description")

    # Report parameters
    period_start: date = Field(..., description="Period start date")
    period_end: date = Field(..., description="Period end date")
    report_filters: Dict[str, Any] = Field(..., description="Report filters")
    report_config: Dict[str, Any] = Field(..., description="Report configuration")

    # Compliance framework
    compliance_framework: Optional[ComplianceFramework] = Field(
        None, description="Compliance framework"
    )
    regulatory_requirements: List[str] = Field(
        ..., description="Regulatory requirements"
    )

    # Report content
    executive_summary: Optional[str] = Field(None, description="Executive summary")
    findings: List[Dict[str, Any]] = Field(..., description="Report findings")
    recommendations: List[Dict[str, Any]] = Field(..., description="Recommendations")
    metrics: Dict[str, Any] = Field(..., description="Report metrics")

    # Report data
    total_events: int = Field(..., description="Total events")
    critical_events: int = Field(..., description="Critical events")
    violations: int = Field(..., description="Violations")
    compliance_score: Optional[Decimal] = Field(None, description="Compliance score")

    # File information
    file_path: Optional[str] = Field(None, description="File path")
    file_format: str = Field(..., description="File format")
    file_size: Optional[int] = Field(None, description="File size")

    # Generation details
    generated_by: str = Field(..., description="Generator user ID")
    generation_status: str = Field(..., description="Generation status")
    generation_progress: int = Field(..., description="Generation progress %")
    generation_error: Optional[str] = Field(None, description="Generation error")

    # Distribution
    recipients: List[str] = Field(..., description="Recipients")
    distributed_at: Optional[datetime] = Field(
        None, description="Distribution timestamp"
    )
    distribution_status: Optional[str] = Field(None, description="Distribution status")

    # Retention
    retention_period_days: int = Field(..., description="Retention period in days")
    expires_at: Optional[date] = Field(None, description="Expiration date")
    is_archived: bool = Field(..., description="Archived status")

    # Timestamps
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")


class AuditReportListResponse(BaseAuditSchema):
    """Schema for audit report list response."""

    reports: List[AuditReportResponse] = Field(..., description="Audit reports")
    total_count: int = Field(..., description="Total count")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Items per page")
    has_more: bool = Field(False, description="Has more items")


# =============================================================================
# Session Schemas
# =============================================================================


class AuditSessionCreateRequest(BaseAuditSchema):
    """Schema for creating audit session."""

    organization_id: str = Field(..., description="Organization ID")
    user_id: str = Field(..., description="User ID")
    session_token: str = Field(..., description="Session token")
    session_type: str = Field("web", description="Session type")

    # Authentication details
    authentication_method: Optional[str] = Field(
        None, description="Authentication method"
    )
    mfa_verified: bool = Field(False, description="MFA verified")
    authentication_factors: List[str] = Field(
        default_factory=list, description="Authentication factors"
    )

    # Session details
    ip_address: Optional[str] = Field(None, max_length=45, description="IP address")
    user_agent: Optional[str] = Field(None, max_length=1000, description="User agent")
    device_fingerprint: Optional[str] = Field(
        None, max_length=500, description="Device fingerprint"
    )
    geolocation: Optional[Dict[str, Any]] = Field(None, description="Geolocation data")


class AuditSessionResponse(BaseAuditSchema):
    """Schema for audit session response."""

    id: str = Field(..., description="Session ID")
    organization_id: str = Field(..., description="Organization ID")
    user_id: str = Field(..., description="User ID")
    session_token: str = Field(..., description="Session token")
    session_type: str = Field(..., description="Session type")

    # Authentication details
    authentication_method: Optional[str] = Field(
        None, description="Authentication method"
    )
    mfa_verified: bool = Field(..., description="MFA verified")
    authentication_factors: List[str] = Field(..., description="Authentication factors")

    # Session details
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    device_fingerprint: Optional[str] = Field(None, description="Device fingerprint")
    geolocation: Optional[Dict[str, Any]] = Field(None, description="Geolocation data")

    # Session status
    is_active: bool = Field(..., description="Active status")
    last_activity: Optional[datetime] = Field(
        None, description="Last activity timestamp"
    )
    inactivity_duration: Optional[int] = Field(
        None, description="Inactivity duration in seconds"
    )

    # Security monitoring
    suspicious_activity_count: int = Field(..., description="Suspicious activity count")
    failed_action_count: int = Field(..., description="Failed action count")
    risk_score: int = Field(..., description="Risk score")

    # Session metrics
    actions_performed: int = Field(..., description="Actions performed")
    data_accessed: List[str] = Field(..., description="Data accessed")
    permissions_used: List[str] = Field(..., description="Permissions used")

    # Termination
    terminated_reason: Optional[str] = Field(None, description="Termination reason")
    terminated_by: Optional[str] = Field(None, description="Terminated by")

    # Timestamps
    started_at: datetime = Field(..., description="Start timestamp")
    ended_at: Optional[datetime] = Field(None, description="End timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")


# =============================================================================
# Compliance Schemas
# =============================================================================


class ComplianceAssessmentCreateRequest(BaseAuditSchema):
    """Schema for creating compliance assessment."""

    organization_id: str = Field(..., description="Organization ID")
    framework: ComplianceFramework = Field(..., description="Compliance framework")
    framework_version: Optional[str] = Field(
        None, max_length=50, description="Framework version"
    )
    requirement_id: str = Field(..., max_length=100, description="Requirement ID")
    requirement_name: str = Field(
        ..., min_length=1, max_length=300, description="Requirement name"
    )
    requirement_description: Optional[str] = Field(
        None, description="Requirement description"
    )

    # Assessment period
    assessment_period_start: date = Field(..., description="Assessment period start")
    assessment_period_end: date = Field(..., description="Assessment period end")

    # Compliance status
    compliance_status: str = Field(..., description="Compliance status")
    compliance_score: Optional[Decimal] = Field(
        None, ge=0, le=100, description="Compliance score"
    )
    risk_level: str = Field("medium", description="Risk level")

    # Evidence and documentation
    evidence_items: List[Dict[str, Any]] = Field(
        default_factory=list, description="Evidence items"
    )
    supporting_documents: List[str] = Field(
        default_factory=list, description="Supporting documents"
    )
    test_results: Dict[str, Any] = Field(
        default_factory=dict, description="Test results"
    )

    # Assessment details
    assessed_by: Optional[str] = Field(None, description="Assessed by user ID")
    assessment_method: str = Field("manual", description="Assessment method")
    assessment_notes: Optional[str] = Field(None, description="Assessment notes")

    @validator("compliance_status")
    def validate_compliance_status(cls, v) -> dict:
        """Validate compliance status."""
        valid_statuses = ["compliant", "non_compliant", "partial", "not_assessed"]
        if v not in valid_statuses:
            raise ValueError(f"Compliance status must be one of: {valid_statuses}")
        return v

    @validator("risk_level")
    def validate_risk_level(cls, v) -> dict:
        """Validate risk level."""
        valid_levels = ["low", "medium", "high", "critical"]
        if v not in valid_levels:
            raise ValueError(f"Risk level must be one of: {valid_levels}")
        return v

    @validator("assessment_method")
    def validate_assessment_method(cls, v) -> dict:
        """Validate assessment method."""
        valid_methods = ["automated", "manual", "hybrid"]
        if v not in valid_methods:
            raise ValueError(f"Assessment method must be one of: {valid_methods}")
        return v


class ComplianceAssessmentResponse(BaseAuditSchema):
    """Schema for compliance assessment response."""

    id: str = Field(..., description="Assessment ID")
    organization_id: str = Field(..., description="Organization ID")
    framework: ComplianceFramework = Field(..., description="Compliance framework")
    framework_version: Optional[str] = Field(None, description="Framework version")
    requirement_id: str = Field(..., description="Requirement ID")
    requirement_name: str = Field(..., description="Requirement name")
    requirement_description: Optional[str] = Field(
        None, description="Requirement description"
    )

    # Assessment period
    assessment_period_start: date = Field(..., description="Assessment period start")
    assessment_period_end: date = Field(..., description="Assessment period end")

    # Compliance status
    compliance_status: str = Field(..., description="Compliance status")
    compliance_score: Optional[Decimal] = Field(None, description="Compliance score")
    risk_level: str = Field(..., description="Risk level")

    # Evidence and documentation
    evidence_items: List[Dict[str, Any]] = Field(..., description="Evidence items")
    supporting_documents: List[str] = Field(..., description="Supporting documents")
    test_results: Dict[str, Any] = Field(..., description="Test results")

    # Findings
    findings: List[Dict[str, Any]] = Field(..., description="Assessment findings")
    gaps_identified: List[Dict[str, Any]] = Field(..., description="Gaps identified")
    remediation_actions: List[Dict[str, Any]] = Field(
        ..., description="Remediation actions"
    )

    # Assessment details
    assessed_by: Optional[str] = Field(None, description="Assessed by user ID")
    assessment_method: str = Field(..., description="Assessment method")
    assessment_notes: Optional[str] = Field(None, description="Assessment notes")

    # Remediation tracking
    remediation_plan: Optional[Dict[str, Any]] = Field(
        None, description="Remediation plan"
    )
    remediation_deadline: Optional[date] = Field(
        None, description="Remediation deadline"
    )
    remediation_status: Optional[str] = Field(None, description="Remediation status")
    remediation_owner: Optional[str] = Field(
        None, description="Remediation owner user ID"
    )

    # Review and approval
    reviewed_by: Optional[str] = Field(None, description="Reviewed by user ID")
    reviewed_at: Optional[datetime] = Field(None, description="Review timestamp")
    approved_by: Optional[str] = Field(None, description="Approved by user ID")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")

    # Next assessment
    next_assessment_due: Optional[date] = Field(
        None, description="Next assessment due date"
    )
    assessment_frequency: Optional[str] = Field(
        None, description="Assessment frequency"
    )

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


# =============================================================================
# Dashboard and Analytics Schemas
# =============================================================================


class ComplianceDashboardResponse(BaseAuditSchema):
    """Schema for compliance dashboard response."""

    overall_compliance_rate: float = Field(..., description="Overall compliance rate %")
    total_assessments: int = Field(..., description="Total assessments")
    compliant_assessments: int = Field(..., description="Compliant assessments")
    framework_statistics: Dict[str, Dict[str, Any]] = Field(
        ..., description="Framework statistics"
    )
    overdue_assessments: int = Field(..., description="Overdue assessments")
    last_updated: str = Field(..., description="Last updated timestamp")


class SecurityDashboardResponse(BaseAuditSchema):
    """Schema for security dashboard response."""

    security_events_week: int = Field(..., description="Security events this week")
    active_alerts: int = Field(..., description="Active alerts")
    high_risk_sessions: int = Field(..., description="High risk sessions")
    failed_logins_24h: int = Field(..., description="Failed logins in 24 hours")
    security_score: int = Field(..., description="Overall security score")
    last_updated: str = Field(..., description="Last updated timestamp")


class AuditMetricsResponse(BaseAuditSchema):
    """Schema for audit metrics response."""

    organization_id: str = Field(..., description="Organization ID")
    period_start: datetime = Field(..., description="Period start")
    period_end: datetime = Field(..., description="Period end")
    period_type: str = Field(..., description="Period type")

    # Event metrics
    total_events: int = Field(..., description="Total events")
    events_by_type: Dict[str, int] = Field(..., description="Events by type")
    events_by_severity: Dict[str, int] = Field(..., description="Events by severity")
    failed_events: int = Field(..., description="Failed events")

    # Alert metrics
    total_alerts: int = Field(..., description="Total alerts")
    alerts_by_severity: Dict[str, int] = Field(..., description="Alerts by severity")
    false_positive_rate: Optional[Decimal] = Field(
        None, description="False positive rate %"
    )
    average_resolution_time: Optional[Decimal] = Field(
        None, description="Average resolution time minutes"
    )

    # Performance metrics
    processing_latency_avg: Optional[Decimal] = Field(
        None, description="Average processing latency ms"
    )
    processing_latency_max: Optional[Decimal] = Field(
        None, description="Max processing latency ms"
    )
    throughput: Optional[int] = Field(None, description="Throughput events/second")
    error_rate: Optional[Decimal] = Field(None, description="Error rate %")

    # Storage metrics
    storage_used: Optional[Decimal] = Field(None, description="Storage used MB")
    storage_growth_rate: Optional[Decimal] = Field(
        None, description="Storage growth rate MB/day"
    )
    archived_records: int = Field(..., description="Archived records")
    deleted_records: int = Field(..., description="Deleted records")

    # User activity metrics
    active_users: int = Field(..., description="Active users")
    suspicious_activities: int = Field(..., description="Suspicious activities")
    policy_violations: int = Field(..., description="Policy violations")

    # Compliance metrics
    compliance_score: Optional[Decimal] = Field(None, description="Compliance score %")
    assessment_completion_rate: Optional[Decimal] = Field(
        None, description="Assessment completion rate %"
    )
    remediation_completion_rate: Optional[Decimal] = Field(
        None, description="Remediation completion rate %"
    )

    # System health
    system_uptime: Optional[Decimal] = Field(None, description="System uptime %")
    queue_backlog: int = Field(..., description="Queue backlog")
    resource_utilization: Dict[str, Any] = Field(
        ..., description="Resource utilization"
    )

    # Calculated timestamp
    calculated_at: datetime = Field(..., description="Calculation timestamp")


# =============================================================================
# Export and Import Schemas
# =============================================================================


class AuditExportRequest(BaseAuditSchema):
    """Schema for audit data export request."""

    organization_id: str = Field(..., description="Organization ID")
    export_type: str = Field(..., description="Export type")
    format: str = Field("csv", description="Export format")

    # Date range
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")

    # Filters
    filters: Dict[str, Any] = Field(default_factory=dict, description="Export filters")

    # Options
    include_sensitive_data: bool = Field(False, description="Include sensitive data")
    compression: bool = Field(True, description="Compress export")
    encryption: bool = Field(True, description="Encrypt export")

    @validator("export_type")
    def validate_export_type(cls, v) -> dict:
        """Validate export type."""
        valid_types = ["audit_logs", "alerts", "reports", "sessions", "compliance"]
        if v not in valid_types:
            raise ValueError(f"Export type must be one of: {valid_types}")
        return v

    @validator("format")
    def validate_format(cls, v) -> dict:
        """Validate export format."""
        valid_formats = ["csv", "json", "xlsx", "xml"]
        if v not in valid_formats:
            raise ValueError(f"Format must be one of: {valid_formats}")
        return v


class AuditExportResponse(BaseAuditSchema):
    """Schema for audit export response."""

    export_id: str = Field(..., description="Export ID")
    status: str = Field(..., description="Export status")
    file_path: Optional[str] = Field(None, description="Export file path")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    record_count: int = Field(..., description="Number of records exported")
    download_url: Optional[str] = Field(None, description="Download URL")
    expires_at: Optional[datetime] = Field(None, description="Download expiration")
    created_at: datetime = Field(..., description="Creation timestamp")


class RetentionPolicyExecutionResponse(BaseAuditSchema):
    """Schema for retention policy execution response."""

    success: bool = Field(..., description="Execution success")
    records_processed: int = Field(..., description="Records processed")
    records_archived: int = Field(..., description="Records archived")
    records_deleted: int = Field(..., description="Records deleted")
    error: Optional[str] = Field(None, description="Error message if failed")
