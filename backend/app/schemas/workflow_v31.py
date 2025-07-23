"""
Workflow System Schemas - CC02 v31.0 Phase 2

Comprehensive Pydantic schemas for workflow system including:
- Business Process Automation & Orchestration
- Approval Workflows & State Management
- Dynamic Workflow Configuration
- Parallel & Sequential Processing
- Conditional Logic & Decision Trees
- Role-Based Task Assignment
- Workflow Analytics & Performance Tracking
- Template-Based Workflow Creation
- Integration Hooks & External Triggers
- Compliance & Audit Trail
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.models.workflow_extended import (
    ActionType,
    TaskPriority,
    TaskStatus,
    WorkflowInstanceStatus,
    WorkflowStatus,
    WorkflowType,
)

# =============================================================================
# Base Schemas
# =============================================================================


class BaseWorkflowSchema(BaseModel):
    """Base schema for workflow-related models."""

    class Config:
        orm_mode = True
        use_enum_values = True


# =============================================================================
# Workflow Definition Schemas
# =============================================================================


class WorkflowDefinitionCreateRequest(BaseWorkflowSchema):
    """Schema for creating a new workflow definition."""

    organization_id: str = Field(..., description="Organization ID")
    name: str = Field(..., min_length=1, max_length=200, description="Workflow name")
    code: str = Field(..., min_length=1, max_length=100, description="Workflow code")
    description: Optional[str] = Field(None, description="Workflow description")
    workflow_type: WorkflowType = Field(..., description="Workflow type")
    category: Optional[str] = Field(
        None, max_length=100, description="Workflow category"
    )

    # Configuration
    definition_schema: Dict[str, Any] = Field(
        ..., description="JSON workflow definition"
    )
    steps_config: List[Dict[str, Any]] = Field(
        default_factory=list, description="Steps configuration"
    )
    decision_rules: Dict[str, Any] = Field(
        default_factory=dict, description="Decision rules"
    )
    approval_matrix: Dict[str, Any] = Field(
        default_factory=dict, description="Approval matrix"
    )

    # Execution settings
    auto_start: bool = Field(False, description="Auto-start workflow")
    parallel_execution: bool = Field(False, description="Allow parallel execution")
    max_parallel_tasks: int = Field(5, ge=1, le=50, description="Max parallel tasks")
    timeout_minutes: Optional[int] = Field(None, ge=1, description="Workflow timeout")
    retry_attempts: int = Field(0, ge=0, le=10, description="Retry attempts")

    # Triggers
    trigger_types: List[str] = Field(default_factory=list, description="Trigger types")
    trigger_conditions: Dict[str, Any] = Field(
        default_factory=dict, description="Trigger conditions"
    )
    trigger_schedule: Optional[str] = Field(
        None, max_length=100, description="Cron schedule"
    )

    # Assignment rules
    default_assignee_type: str = Field("user", description="Default assignee type")
    default_assignee_id: Optional[str] = Field(None, description="Default assignee ID")
    assignment_rules: Dict[str, Any] = Field(
        default_factory=dict, description="Assignment rules"
    )
    escalation_rules: List[Dict[str, Any]] = Field(
        default_factory=list, description="Escalation rules"
    )

    # Notifications
    notification_settings: Dict[str, Any] = Field(
        default_factory=dict, description="Notification settings"
    )
    email_templates: Dict[str, Any] = Field(
        default_factory=dict, description="Email templates"
    )
    reminder_settings: Dict[str, Any] = Field(
        default_factory=dict, description="Reminder settings"
    )

    # SLA and performance
    sla_minutes: Optional[int] = Field(None, ge=1, description="SLA in minutes")
    warning_threshold_percent: Decimal = Field(
        Decimal("80.0"), ge=0, le=100, description="Warning threshold %"
    )
    escalation_threshold_percent: Decimal = Field(
        Decimal("100.0"), ge=0, le=200, description="Escalation threshold %"
    )

    # Access control
    is_public: bool = Field(False, description="Public workflow")
    allowed_roles: List[str] = Field(default_factory=list, description="Allowed roles")
    allowed_users: List[str] = Field(default_factory=list, description="Allowed users")
    allowed_departments: List[str] = Field(
        default_factory=list, description="Allowed departments"
    )

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags")
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict, description="Custom fields"
    )
    workflow_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    created_by: str = Field(..., description="Creator user ID")

    @validator("definition_schema")
    def validate_definition_schema(cls, v):
        """Validate workflow definition schema."""
        if not isinstance(v, dict):
            raise ValueError("Definition schema must be a dictionary")
        if "steps" not in v or not isinstance(v["steps"], list):
            raise ValueError("Definition schema must contain steps array")
        if len(v["steps"]) == 0:
            raise ValueError("Definition schema must contain at least one step")
        return v


class WorkflowDefinitionUpdateRequest(BaseWorkflowSchema):
    """Schema for updating a workflow definition."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=200, description="Workflow name"
    )
    description: Optional[str] = Field(None, description="Workflow description")
    definition_schema: Optional[Dict[str, Any]] = Field(
        None, description="JSON workflow definition"
    )
    status: Optional[WorkflowStatus] = Field(None, description="Workflow status")
    sla_minutes: Optional[int] = Field(None, ge=1, description="SLA in minutes")
    auto_start: Optional[bool] = Field(None, description="Auto-start workflow")
    is_public: Optional[bool] = Field(None, description="Public workflow")
    tags: Optional[List[str]] = Field(None, description="Tags")
    workflow_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata"
    )


class WorkflowDefinitionResponse(BaseWorkflowSchema):
    """Schema for workflow definition response."""

    id: str = Field(..., description="Definition ID")
    organization_id: str = Field(..., description="Organization ID")
    name: str = Field(..., description="Workflow name")
    code: str = Field(..., description="Workflow code")
    description: Optional[str] = Field(None, description="Workflow description")
    workflow_type: WorkflowType = Field(..., description="Workflow type")
    category: Optional[str] = Field(None, description="Workflow category")

    # Configuration
    definition_schema: Dict[str, Any] = Field(
        ..., description="JSON workflow definition"
    )
    auto_start: bool = Field(..., description="Auto-start workflow")
    parallel_execution: bool = Field(..., description="Allow parallel execution")
    max_parallel_tasks: int = Field(..., description="Max parallel tasks")

    # SLA and performance
    sla_minutes: Optional[int] = Field(None, description="SLA in minutes")
    warning_threshold_percent: Decimal = Field(..., description="Warning threshold %")

    # Status and metrics
    status: WorkflowStatus = Field(..., description="Workflow status")
    usage_count: int = Field(..., description="Usage count")
    success_rate: Optional[Decimal] = Field(None, description="Success rate %")
    average_completion_time: Optional[Decimal] = Field(
        None, description="Average completion time"
    )

    # Versioning
    version: str = Field(..., description="Version")
    previous_version_id: Optional[str] = Field(None, description="Previous version ID")

    # Access control
    is_public: bool = Field(..., description="Public workflow")
    allowed_roles: List[str] = Field(..., description="Allowed roles")

    # Metadata
    tags: List[str] = Field(..., description="Tags")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


class WorkflowDefinitionListResponse(BaseWorkflowSchema):
    """Schema for workflow definition list response."""

    definitions: List[WorkflowDefinitionResponse] = Field(
        ..., description="Workflow definitions"
    )
    total_count: int = Field(..., description="Total count")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Items per page")
    has_more: bool = Field(False, description="Has more items")


# =============================================================================
# Workflow Step Schemas
# =============================================================================


class WorkflowStepResponse(BaseWorkflowSchema):
    """Schema for workflow step response."""

    id: str = Field(..., description="Step ID")
    name: str = Field(..., description="Step name")
    code: str = Field(..., description="Step code")
    description: Optional[str] = Field(None, description="Step description")
    step_type: str = Field(..., description="Step type")
    step_order: int = Field(..., description="Step order")

    # Configuration
    step_config: Dict[str, Any] = Field(..., description="Step configuration")
    form_schema: Dict[str, Any] = Field(..., description="Form schema")

    # Assignment
    assignee_type: Optional[str] = Field(None, description="Assignee type")
    assignee_id: Optional[str] = Field(None, description="Assignee ID")

    # Execution
    is_required: bool = Field(..., description="Required step")
    allow_skip: bool = Field(..., description="Allow skip")
    allow_delegate: bool = Field(..., description="Allow delegation")

    # Timing
    estimated_duration_minutes: Optional[int] = Field(
        None, description="Estimated duration"
    )

    # Status
    is_active: bool = Field(..., description="Active status")


# =============================================================================
# Workflow Instance Schemas
# =============================================================================


class WorkflowInstanceStartRequest(BaseWorkflowSchema):
    """Schema for starting a workflow instance."""

    definition_id: str = Field(..., description="Workflow definition ID")
    title: Optional[str] = Field(None, max_length=300, description="Instance title")
    description: Optional[str] = Field(None, description="Instance description")

    # Context
    entity_type: Optional[str] = Field(None, max_length=100, description="Entity type")
    entity_id: Optional[str] = Field(None, max_length=200, description="Entity ID")
    context_data: Dict[str, Any] = Field(
        default_factory=dict, description="Context data"
    )
    form_data: Dict[str, Any] = Field(default_factory=dict, description="Form data")

    # Priority
    priority: TaskPriority = Field(TaskPriority.NORMAL, description="Priority level")
    urgency_level: int = Field(3, ge=1, le=5, description="Urgency level")
    business_impact: Optional[str] = Field(
        None, max_length=100, description="Business impact"
    )

    # Settings
    due_date: Optional[datetime] = Field(None, description="Due date")
    notification_settings: Dict[str, Any] = Field(
        default_factory=dict, description="Notification settings"
    )

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags")
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict, description="Custom fields"
    )
    initiated_by: str = Field(..., description="Initiator user ID")


class WorkflowInstanceResponse(BaseWorkflowSchema):
    """Schema for workflow instance response."""

    id: str = Field(..., description="Instance ID")
    organization_id: str = Field(..., description="Organization ID")
    definition_id: str = Field(..., description="Definition ID")
    instance_number: str = Field(..., description="Instance number")
    title: Optional[str] = Field(None, description="Instance title")
    description: Optional[str] = Field(None, description="Instance description")

    # Context
    entity_type: Optional[str] = Field(None, description="Entity type")
    entity_id: Optional[str] = Field(None, description="Entity ID")

    # Status
    status: WorkflowInstanceStatus = Field(..., description="Instance status")
    current_step_id: Optional[str] = Field(None, description="Current step ID")
    current_assignee_id: Optional[str] = Field(None, description="Current assignee ID")

    # Timing
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    due_date: Optional[datetime] = Field(None, description="Due date")
    sla_deadline: Optional[datetime] = Field(None, description="SLA deadline")
    duration_minutes: Optional[int] = Field(None, description="Duration in minutes")

    # Priority and urgency
    priority: TaskPriority = Field(..., description="Priority level")
    urgency_level: int = Field(..., description="Urgency level")
    business_impact: Optional[str] = Field(None, description="Business impact")

    # Progress
    total_steps: int = Field(..., description="Total steps")
    completed_steps: int = Field(..., description="Completed steps")
    progress_percentage: Decimal = Field(..., description="Progress percentage")

    # Performance metrics
    sla_breach: bool = Field(..., description="SLA breach status")
    escalation_count: int = Field(..., description="Escalation count")
    reassignment_count: int = Field(..., description="Reassignment count")
    comment_count: int = Field(..., description="Comment count")

    # Results
    final_status: Optional[str] = Field(None, description="Final status")
    completion_notes: Optional[str] = Field(None, description="Completion notes")

    # Error handling
    error_count: int = Field(..., description="Error count")
    last_error: Optional[str] = Field(None, description="Last error")

    # Metadata
    tags: List[str] = Field(..., description="Tags")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


class WorkflowInstanceListResponse(BaseWorkflowSchema):
    """Schema for workflow instance list response."""

    instances: List[WorkflowInstanceResponse] = Field(
        ..., description="Workflow instances"
    )
    total_count: int = Field(..., description="Total count")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Items per page")
    has_more: bool = Field(False, description="Has more items")


# =============================================================================
# Workflow Task Schemas
# =============================================================================


class WorkflowTaskResponse(BaseWorkflowSchema):
    """Schema for workflow task response."""

    id: str = Field(..., description="Task ID")
    organization_id: str = Field(..., description="Organization ID")
    instance_id: str = Field(..., description="Instance ID")
    step_id: str = Field(..., description="Step ID")
    task_number: str = Field(..., description="Task number")
    name: str = Field(..., description="Task name")
    description: Optional[str] = Field(None, description="Task description")

    # Assignment
    assignee_id: Optional[str] = Field(None, description="Assignee ID")
    assignee_type: Optional[str] = Field(None, description="Assignee type")
    assigned_by: Optional[str] = Field(None, description="Assigned by user ID")
    assigned_at: Optional[datetime] = Field(None, description="Assignment timestamp")

    # Status and progress
    status: TaskStatus = Field(..., description="Task status")
    progress_percentage: Decimal = Field(..., description="Progress percentage")

    # Timing
    due_date: Optional[datetime] = Field(None, description="Due date")
    estimated_duration_minutes: Optional[int] = Field(
        None, description="Estimated duration"
    )
    actual_duration_minutes: Optional[int] = Field(None, description="Actual duration")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")

    # Priority
    priority: TaskPriority = Field(..., description="Priority level")
    urgency_score: int = Field(..., description="Urgency score")

    # Results
    completion_result: Optional[str] = Field(None, description="Completion result")
    completion_notes: Optional[str] = Field(None, description="Completion notes")

    # Delegation and escalation
    original_assignee_id: Optional[str] = Field(
        None, description="Original assignee ID"
    )
    delegated_from: Optional[str] = Field(None, description="Delegated from user ID")
    delegated_to: Optional[str] = Field(None, description="Delegated to user ID")
    escalated_to: Optional[str] = Field(None, description="Escalated to user ID")
    escalation_reason: Optional[str] = Field(None, description="Escalation reason")

    # Performance
    sla_breach: bool = Field(..., description="SLA breach status")
    overdue_hours: Optional[Decimal] = Field(None, description="Overdue hours")
    reminder_count: int = Field(..., description="Reminder count")

    # Attachments and comments
    attachment_count: int = Field(..., description="Attachment count")
    comment_count: int = Field(..., description="Comment count")

    # Metadata
    tags: List[str] = Field(..., description="Tags")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


class TaskActionRequest(BaseWorkflowSchema):
    """Schema for task action requests."""

    action_type: ActionType = Field(..., description="Action type")
    result: Optional[str] = Field(None, description="Action result")
    result_data: Optional[Dict[str, Any]] = Field(None, description="Result data")
    notes: Optional[str] = Field(None, description="Action notes")
    form_data: Optional[Dict[str, Any]] = Field(None, description="Form data")
    performed_by: str = Field(..., description="User performing action")


class TaskAssignmentRequest(BaseWorkflowSchema):
    """Schema for task assignment requests."""

    assignee_id: str = Field(..., description="New assignee user ID")
    assigned_by: str = Field(..., description="User making assignment")
    assignment_reason: Optional[str] = Field(
        None, max_length=500, description="Assignment reason"
    )
    notify_assignee: bool = Field(True, description="Send notification to assignee")


class TaskDelegationRequest(BaseWorkflowSchema):
    """Schema for task delegation requests."""

    delegate_to: str = Field(..., description="User to delegate to")
    delegated_by: str = Field(..., description="User delegating task")
    delegation_reason: Optional[str] = Field(
        None, max_length=500, description="Delegation reason"
    )
    temporary: bool = Field(False, description="Temporary delegation")
    return_date: Optional[datetime] = Field(
        None, description="Return date for temporary delegation"
    )


class TaskEscalationRequest(BaseWorkflowSchema):
    """Schema for task escalation requests."""

    escalate_to: str = Field(..., description="User to escalate to")
    escalation_reason: str = Field(
        ..., min_length=1, max_length=500, description="Escalation reason"
    )
    escalation_type: str = Field("manual", description="Escalation type")
    priority_increase: bool = Field(True, description="Increase task priority")


# =============================================================================
# Comments and Attachments Schemas
# =============================================================================


class WorkflowCommentCreateRequest(BaseWorkflowSchema):
    """Schema for creating workflow comments."""

    organization_id: str = Field(..., description="Organization ID")
    comment_text: str = Field(..., min_length=1, description="Comment text")
    comment_type: str = Field("general", description="Comment type")
    is_internal: bool = Field(False, description="Internal comment")
    parent_comment_id: Optional[str] = Field(None, description="Parent comment ID")
    mentioned_users: List[str] = Field(
        default_factory=list, description="Mentioned users"
    )
    author_id: str = Field(..., description="Author user ID")


class WorkflowCommentResponse(BaseWorkflowSchema):
    """Schema for workflow comment response."""

    id: str = Field(..., description="Comment ID")
    task_id: str = Field(..., description="Task ID")
    comment_text: str = Field(..., description="Comment text")
    comment_type: str = Field(..., description="Comment type")
    is_internal: bool = Field(..., description="Internal comment")
    is_system_generated: bool = Field(..., description="System generated")

    # Hierarchy
    parent_comment_id: Optional[str] = Field(None, description="Parent comment ID")
    thread_id: Optional[str] = Field(None, description="Thread ID")

    # Author
    author_id: str = Field(..., description="Author user ID")
    author_role: Optional[str] = Field(None, description="Author role")

    # Status
    is_edited: bool = Field(..., description="Edited status")
    is_deleted: bool = Field(..., description="Deleted status")

    # Mentions
    mentioned_users: List[str] = Field(..., description="Mentioned users")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


class WorkflowAttachmentCreateRequest(BaseWorkflowSchema):
    """Schema for creating workflow attachments."""

    organization_id: str = Field(..., description="Organization ID")
    filename: str = Field(..., min_length=1, max_length=500, description="Filename")
    original_filename: Optional[str] = Field(
        None, max_length=500, description="Original filename"
    )
    file_path: str = Field(..., max_length=1000, description="File path")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    file_type: Optional[str] = Field(None, max_length=100, description="File type")
    mime_type: Optional[str] = Field(None, max_length=200, description="MIME type")

    # Classification
    attachment_type: str = Field("document", description="Attachment type")
    category: Optional[str] = Field(None, max_length=100, description="Category")

    # Storage
    storage_provider: str = Field("local", description="Storage provider")
    storage_path: Optional[str] = Field(
        None, max_length=1000, description="Storage path"
    )

    # Security
    access_level: str = Field("task_participants", description="Access level")

    # Metadata
    description: Optional[str] = Field(None, description="Description")
    tags: List[str] = Field(default_factory=list, description="Tags")
    uploaded_by: str = Field(..., description="Uploader user ID")


class WorkflowAttachmentResponse(BaseWorkflowSchema):
    """Schema for workflow attachment response."""

    id: str = Field(..., description="Attachment ID")
    task_id: str = Field(..., description="Task ID")
    filename: str = Field(..., description="Filename")
    original_filename: Optional[str] = Field(None, description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    file_type: Optional[str] = Field(None, description="File type")
    mime_type: Optional[str] = Field(None, description="MIME type")

    # Classification
    attachment_type: str = Field(..., description="Attachment type")
    category: Optional[str] = Field(None, description="Category")

    # Versions
    version: str = Field(..., description="Version")

    # Upload details
    uploaded_by: str = Field(..., description="Uploader user ID")
    upload_source: str = Field(..., description="Upload source")

    # Status
    is_deleted: bool = Field(..., description="Deleted status")

    # Metadata
    description: Optional[str] = Field(None, description="Description")
    tags: List[str] = Field(..., description="Tags")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")


# =============================================================================
# Analytics Schemas
# =============================================================================


class WorkflowAnalyticsRequest(BaseWorkflowSchema):
    """Schema for workflow analytics request."""

    organization_id: str = Field(..., description="Organization ID")
    period_start: date = Field(..., description="Period start date")
    period_end: date = Field(..., description="Period end date")

    # Filters
    definition_id: Optional[str] = Field(None, description="Filter by definition ID")
    department: Optional[str] = Field(None, description="Filter by department")
    workflow_type: Optional[str] = Field(None, description="Filter by workflow type")

    # Options
    include_details: bool = Field(False, description="Include detailed metrics")
    group_by: List[str] = Field(default_factory=list, description="Group by fields")


class WorkflowAnalyticsResponse(BaseWorkflowSchema):
    """Schema for workflow analytics response."""

    organization_id: str = Field(..., description="Organization ID")
    period_start: date = Field(..., description="Period start date")
    period_end: date = Field(..., description="Period end date")
    period_type: str = Field(..., description="Period type")

    # Instance metrics
    total_instances: int = Field(..., description="Total instances")
    completed_instances: int = Field(..., description="Completed instances")
    failed_instances: int = Field(..., description="Failed instances")
    cancelled_instances: int = Field(..., description="Cancelled instances")
    active_instances: int = Field(..., description="Active instances")

    # Performance metrics
    average_completion_time_hours: Optional[Decimal] = Field(
        None, description="Average completion time"
    )
    median_completion_time_hours: Optional[Decimal] = Field(
        None, description="Median completion time"
    )
    min_completion_time_hours: Optional[Decimal] = Field(
        None, description="Minimum completion time"
    )
    max_completion_time_hours: Optional[Decimal] = Field(
        None, description="Maximum completion time"
    )

    # SLA metrics
    sla_compliance_rate: Optional[Decimal] = Field(
        None, description="SLA compliance rate %"
    )
    sla_breaches: int = Field(..., description="SLA breaches")
    average_sla_deviation_hours: Optional[Decimal] = Field(
        None, description="Average SLA deviation"
    )

    # Task metrics
    total_tasks: int = Field(..., description="Total tasks")
    completed_tasks: int = Field(..., description="Completed tasks")
    overdue_tasks: int = Field(..., description="Overdue tasks")
    escalated_tasks: int = Field(..., description="Escalated tasks")

    # Quality metrics
    approval_rate: Optional[Decimal] = Field(None, description="Approval rate %")
    rejection_rate: Optional[Decimal] = Field(None, description="Rejection rate %")
    rework_rate: Optional[Decimal] = Field(None, description="Rework rate %")

    # Bottlenecks
    bottleneck_steps: List[Dict[str, Any]] = Field(..., description="Bottleneck steps")
    common_failure_points: List[Dict[str, Any]] = Field(
        ..., description="Common failure points"
    )

    # Trends
    volume_trend: Optional[str] = Field(None, description="Volume trend")
    performance_trend: Optional[str] = Field(None, description="Performance trend")
    quality_trend: Optional[str] = Field(None, description="Quality trend")

    # Calculated timestamp
    calculated_at: datetime = Field(..., description="Calculation timestamp")


class WorkflowDashboardResponse(BaseWorkflowSchema):
    """Schema for workflow dashboard response."""

    active_instances: int = Field(..., description="Active instances")
    overdue_tasks: int = Field(..., description="Overdue tasks")
    completed_instances_period: int = Field(
        ..., description="Completed instances in period"
    )
    average_completion_time_hours: float = Field(
        ..., description="Average completion time"
    )

    top_bottlenecks: List[Dict[str, Any]] = Field(..., description="Top bottlenecks")

    period_start: str = Field(..., description="Period start")
    period_end: str = Field(..., description="Period end")


# =============================================================================
# Template Schemas
# =============================================================================


class WorkflowTemplateResponse(BaseWorkflowSchema):
    """Schema for workflow template response."""

    id: str = Field(..., description="Template ID")
    organization_id: str = Field(..., description="Organization ID")
    name: str = Field(..., description="Template name")
    code: str = Field(..., description="Template code")
    description: Optional[str] = Field(None, description="Template description")
    category: Optional[str] = Field(None, description="Template category")
    industry: Optional[str] = Field(None, description="Industry")

    # Template definition
    template_schema: Dict[str, Any] = Field(..., description="Template schema")
    default_config: Dict[str, Any] = Field(..., description="Default configuration")

    # Usage and popularity
    usage_count: int = Field(..., description="Usage count")
    rating_average: Optional[Decimal] = Field(None, description="Average rating")
    rating_count: int = Field(..., description="Rating count")

    # Access
    is_public: bool = Field(..., description="Public template")
    is_featured: bool = Field(..., description="Featured template")

    # Metadata
    tags: List[str] = Field(..., description="Tags")
    version: str = Field(..., description="Version")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


# =============================================================================
# Activity and Audit Schemas
# =============================================================================


class WorkflowActivityResponse(BaseWorkflowSchema):
    """Schema for workflow activity response."""

    id: str = Field(..., description="Activity ID")
    instance_id: str = Field(..., description="Instance ID")
    task_id: Optional[str] = Field(None, description="Task ID")
    activity_type: str = Field(..., description="Activity type")
    action_type: ActionType = Field(..., description="Action type")
    description: str = Field(..., description="Description")

    # Actor
    performed_by: Optional[str] = Field(None, description="Performed by user ID")
    actor_type: str = Field(..., description="Actor type")

    # Context
    from_status: Optional[str] = Field(None, description="From status")
    to_status: Optional[str] = Field(None, description="To status")
    from_assignee: Optional[str] = Field(None, description="From assignee")
    to_assignee: Optional[str] = Field(None, description="To assignee")

    # Data
    activity_data: Dict[str, Any] = Field(..., description="Activity data")
    comments: Optional[str] = Field(None, description="Comments")

    # Timestamp
    performed_at: datetime = Field(..., description="Performed timestamp")


# =============================================================================
# List Response Schemas
# =============================================================================


class WorkflowTaskListResponse(BaseWorkflowSchema):
    """Schema for workflow task list response."""

    tasks: List[WorkflowTaskResponse] = Field(..., description="Workflow tasks")
    total_count: int = Field(..., description="Total count")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Items per page")
    has_more: bool = Field(False, description="Has more items")


class WorkflowCommentListResponse(BaseWorkflowSchema):
    """Schema for workflow comment list response."""

    comments: List[WorkflowCommentResponse] = Field(
        ..., description="Workflow comments"
    )
    total_count: int = Field(..., description="Total count")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Items per page")
    has_more: bool = Field(False, description="Has more items")


class WorkflowAttachmentListResponse(BaseWorkflowSchema):
    """Schema for workflow attachment list response."""

    attachments: List[WorkflowAttachmentResponse] = Field(
        ..., description="Workflow attachments"
    )
    total_count: int = Field(..., description="Total count")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Items per page")
    has_more: bool = Field(False, description="Has more items")


class WorkflowActivityListResponse(BaseWorkflowSchema):
    """Schema for workflow activity list response."""

    activities: List[WorkflowActivityResponse] = Field(
        ..., description="Workflow activities"
    )
    total_count: int = Field(..., description="Total count")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Items per page")
    has_more: bool = Field(False, description="Has more items")


class WorkflowTemplateListResponse(BaseWorkflowSchema):
    """Schema for workflow template list response."""

    templates: List[WorkflowTemplateResponse] = Field(
        ..., description="Workflow templates"
    )
    total_count: int = Field(..., description="Total count")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Items per page")
    has_more: bool = Field(False, description="Has more items")
