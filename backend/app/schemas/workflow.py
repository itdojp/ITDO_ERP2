"""Workflow schemas for API request/response validation."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse


class WorkflowStatus(str, Enum):
    """Workflow status enumeration."""

    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class WorkflowInstanceStatus(str, Enum):
    """Workflow instance status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TaskStatus(str, Enum):
    """Workflow task status enumeration."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


class NodeType(str, Enum):
    """Workflow node type enumeration."""

    START = "start"
    END = "end"
    TASK = "task"
    APPROVAL = "approval"
    CONDITION = "condition"
    PARALLEL = "parallel"
    MERGE = "merge"
    TIMER = "timer"


class TriggerType(str, Enum):
    """Workflow trigger type enumeration."""

    MANUAL = "manual"
    AUTOMATIC = "automatic"
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"


# Base schemas
class WorkflowNodeBase(BaseModel):
    """Base workflow node schema."""

    node_id: str = Field(
        ..., max_length=100, description="Unique node ID within workflow"
    )
    name: str = Field(..., max_length=200, description="Node name")
    node_type: NodeType = Field(..., description="Node type")
    configuration: Dict[str, Any] = Field(
        default_factory=dict, description="Node configuration"
    )
    position_x: Optional[int] = Field(None, description="X position in visual editor")
    position_y: Optional[int] = Field(None, description="Y position in visual editor")
    assign_to_role: Optional[str] = Field(
        None, max_length=100, description="Role-based assignment"
    )
    assign_to_user: Optional[int] = Field(None, description="User-based assignment")
    auto_assign_rules: Optional[Dict[str, Any]] = Field(
        None, description="Auto-assignment rules"
    )
    entry_conditions: Optional[Dict[str, Any]] = Field(
        None, description="Entry conditions"
    )
    exit_conditions: Optional[Dict[str, Any]] = Field(
        None, description="Exit conditions"
    )
    estimated_duration_hours: Optional[int] = Field(
        None, ge=0, description="Estimated duration in hours"
    )
    timeout_hours: Optional[int] = Field(
        None, ge=0, description="Node timeout in hours"
    )


class WorkflowConnectionBase(BaseModel):
    """Base workflow connection schema."""

    from_node_id: int = Field(..., description="Source node ID")
    to_node_id: int = Field(..., description="Target node ID")
    name: Optional[str] = Field(None, max_length=200, description="Connection name")
    condition: Optional[Dict[str, Any]] = Field(
        None, description="Connection condition"
    )
    is_default: bool = Field(False, description="Default connection flag")


class WorkflowBase(BaseModel):
    """Base workflow schema."""

    name: str = Field(..., max_length=200, description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    version: str = Field("1.0", max_length=20, description="Workflow version")
    organization_id: int = Field(..., description="Organization ID")
    status: WorkflowStatus = Field(WorkflowStatus.DRAFT, description="Workflow status")
    is_template: bool = Field(False, description="Template flag")
    trigger_type: TriggerType = Field(..., description="Trigger type")
    trigger_conditions: Optional[Dict[str, Any]] = Field(
        None, description="Trigger conditions"
    )
    workflow_definition: Dict[str, Any] = Field(
        ..., description="Workflow definition (nodes, connections)"
    )
    allow_parallel_instances: bool = Field(True, description="Allow multiple instances")
    timeout_hours: Optional[int] = Field(
        None, ge=0, description="Workflow timeout in hours"
    )
    tags: Optional[str] = Field(
        None, max_length=500, description="Workflow tags (comma-separated)"
    )
    category: Optional[str] = Field(
        None, max_length=100, description="Workflow category"
    )


class WorkflowInstanceBase(BaseModel):
    """Base workflow instance schema."""

    workflow_id: int = Field(..., description="Workflow ID")
    instance_name: Optional[str] = Field(
        None, max_length=200, description="Instance name"
    )
    status: WorkflowInstanceStatus = Field(
        WorkflowInstanceStatus.PENDING, description="Instance status"
    )
    context_data: Optional[Dict[str, Any]] = Field(
        None, description="Instance context data"
    )
    input_data: Optional[Dict[str, Any]] = Field(
        None, description="Instance input data"
    )
    output_data: Optional[Dict[str, Any]] = Field(
        None, description="Instance output data"
    )
    priority: int = Field(5, ge=1, le=10, description="Instance priority (1-10)")
    reference_type: Optional[str] = Field(
        None, max_length=100, description="Reference object type"
    )
    reference_id: Optional[str] = Field(
        None, max_length=100, description="Reference object ID"
    )
    deadline: Optional[datetime] = Field(None, description="Instance deadline")


class WorkflowTaskBase(BaseModel):
    """Base workflow task schema."""

    instance_id: int = Field(..., description="Instance ID")
    node_id: int = Field(..., description="Node ID")
    task_name: str = Field(..., max_length=200, description="Task name")
    status: TaskStatus = Field(TaskStatus.PENDING, description="Task status")
    assigned_to: Optional[int] = Field(None, description="Assigned user ID")
    input_data: Optional[Dict[str, Any]] = Field(None, description="Task input data")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Task output data")
    form_data: Optional[Dict[str, Any]] = Field(
        None, description="Form submission data"
    )
    due_date: Optional[datetime] = Field(None, description="Task due date")
    comments: Optional[str] = Field(None, description="Task comments")
    completion_notes: Optional[str] = Field(None, description="Completion notes")


# Create schemas
class WorkflowCreate(WorkflowBase):
    """Schema for creating a workflow."""

    nodes: List[WorkflowNodeBase] = Field(
        default_factory=list, description="Workflow nodes"
    )
    connections: List[WorkflowConnectionBase] = Field(
        default_factory=list, description="Workflow connections"
    )


class WorkflowNodeCreate(WorkflowNodeBase):
    """Schema for creating a workflow node."""

    workflow_id: int = Field(..., description="Workflow ID")


class WorkflowConnectionCreate(WorkflowConnectionBase):
    """Schema for creating a workflow connection."""

    workflow_id: int = Field(..., description="Workflow ID")


class WorkflowInstanceCreate(WorkflowInstanceBase):
    """Schema for creating a workflow instance."""

    pass


class WorkflowTaskCreate(WorkflowTaskBase):
    """Schema for creating a workflow task."""

    pass


# Update schemas
class WorkflowUpdate(BaseModel):
    """Schema for updating a workflow."""

    name: Optional[str] = Field(None, max_length=200, description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    status: Optional[WorkflowStatus] = Field(None, description="Workflow status")
    trigger_conditions: Optional[Dict[str, Any]] = Field(
        None, description="Trigger conditions"
    )
    workflow_definition: Optional[Dict[str, Any]] = Field(
        None, description="Workflow definition"
    )
    timeout_hours: Optional[int] = Field(
        None, ge=0, description="Workflow timeout in hours"
    )
    tags: Optional[str] = Field(None, max_length=500, description="Workflow tags")
    category: Optional[str] = Field(
        None, max_length=100, description="Workflow category"
    )


class WorkflowInstanceUpdate(BaseModel):
    """Schema for updating a workflow instance."""

    instance_name: Optional[str] = Field(
        None, max_length=200, description="Instance name"
    )
    status: Optional[WorkflowInstanceStatus] = Field(
        None, description="Instance status"
    )
    context_data: Optional[Dict[str, Any]] = Field(
        None, description="Instance context data"
    )
    output_data: Optional[Dict[str, Any]] = Field(
        None, description="Instance output data"
    )
    priority: Optional[int] = Field(None, ge=1, le=10, description="Instance priority")
    deadline: Optional[datetime] = Field(None, description="Instance deadline")


class WorkflowTaskUpdate(BaseModel):
    """Schema for updating a workflow task."""

    status: Optional[TaskStatus] = Field(None, description="Task status")
    assigned_to: Optional[int] = Field(None, description="Assigned user ID")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Task output data")
    form_data: Optional[Dict[str, Any]] = Field(
        None, description="Form submission data"
    )
    due_date: Optional[datetime] = Field(None, description="Task due date")
    comments: Optional[str] = Field(None, description="Task comments")
    completion_notes: Optional[str] = Field(None, description="Completion notes")


# Response schemas
class WorkflowNodeResponse(WorkflowNodeBase, BaseResponse):
    """Workflow node response schema."""

    workflow_id: int = Field(..., description="Workflow ID")
    assigned_user_name: Optional[str] = Field(None, description="Assigned user name")


class WorkflowConnectionResponse(WorkflowConnectionBase, BaseResponse):
    """Workflow connection response schema."""

    workflow_id: int = Field(..., description="Workflow ID")
    from_node_name: Optional[str] = Field(None, description="Source node name")
    to_node_name: Optional[str] = Field(None, description="Target node name")


class WorkflowResponse(WorkflowBase, BaseResponse):
    """Workflow response schema."""

    created_by_name: Optional[str] = Field(None, description="Creator user name")
    organization_name: Optional[str] = Field(None, description="Organization name")
    nodes_count: int = Field(0, description="Number of nodes")
    active_instances_count: int = Field(0, description="Number of active instances")


class WorkflowInstanceResponse(WorkflowInstanceBase, BaseResponse):
    """Workflow instance response schema."""

    workflow_name: str = Field(..., description="Workflow name")
    started_by_name: str = Field(..., description="User who started instance")
    started_at: datetime = Field(..., description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    duration_hours: Optional[float] = Field(None, description="Duration in hours")
    tasks_count: int = Field(0, description="Number of tasks")
    completed_tasks_count: int = Field(0, description="Number of completed tasks")


class WorkflowTaskResponse(WorkflowTaskBase, BaseResponse):
    """Workflow task response schema."""

    workflow_name: str = Field(..., description="Workflow name")
    instance_name: Optional[str] = Field(None, description="Instance name")
    node_name: str = Field(..., description="Node name")
    assigned_user_name: Optional[str] = Field(None, description="Assigned user name")
    created_at: datetime = Field(..., description="Task creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Task start timestamp")
    completed_at: Optional[datetime] = Field(
        None, description="Task completion timestamp"
    )
    duration_hours: Optional[float] = Field(None, description="Duration in hours")
    is_overdue: bool = Field(False, description="Is task overdue")


# Specialized schemas for workflow operations
class WorkflowStartRequest(BaseModel):
    """Schema for starting a workflow instance."""

    workflow_id: int = Field(..., description="Workflow ID")
    instance_name: Optional[str] = Field(
        None, max_length=200, description="Instance name"
    )
    input_data: Optional[Dict[str, Any]] = Field(
        None, description="Instance input data"
    )
    context_data: Optional[Dict[str, Any]] = Field(
        None, description="Instance context data"
    )
    priority: int = Field(5, ge=1, le=10, description="Instance priority")
    deadline: Optional[datetime] = Field(None, description="Instance deadline")
    reference_type: Optional[str] = Field(
        None, max_length=100, description="Reference object type"
    )
    reference_id: Optional[str] = Field(
        None, max_length=100, description="Reference object ID"
    )


class WorkflowCompleteTaskRequest(BaseModel):
    """Schema for completing a workflow task."""

    task_id: int = Field(..., description="Task ID")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Task output data")
    form_data: Optional[Dict[str, Any]] = Field(
        None, description="Form submission data"
    )
    completion_notes: Optional[str] = Field(None, description="Completion notes")


class WorkflowAssignTaskRequest(BaseModel):
    """Schema for assigning a workflow task."""

    task_id: int = Field(..., description="Task ID")
    assigned_to: int = Field(..., description="User ID to assign task to")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    comments: Optional[str] = Field(None, description="Assignment comments")


# List and pagination schemas
class WorkflowListResponse(BaseModel):
    """Workflow list response schema."""

    items: List[WorkflowResponse] = Field(..., description="List of workflows")
    total: int = Field(..., description="Total number of workflows")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")


class WorkflowInstanceListResponse(BaseModel):
    """Workflow instance list response schema."""

    items: List[WorkflowInstanceResponse] = Field(
        ..., description="List of workflow instances"
    )
    total: int = Field(..., description="Total number of instances")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")


class WorkflowTaskListResponse(BaseModel):
    """Workflow task list response schema."""

    items: List[WorkflowTaskResponse] = Field(..., description="List of workflow tasks")
    total: int = Field(..., description="Total number of tasks")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")


# Analytics and monitoring schemas
class WorkflowAnalyticsResponse(BaseModel):
    """Workflow analytics response schema."""

    workflow_id: int = Field(..., description="Workflow ID")
    workflow_name: str = Field(..., description="Workflow name")
    total_instances: int = Field(..., description="Total instances created")
    completed_instances: int = Field(..., description="Completed instances")
    failed_instances: int = Field(..., description="Failed instances")
    avg_completion_time_hours: Optional[float] = Field(
        None, description="Average completion time in hours"
    )
    completion_rate: float = Field(..., description="Completion rate (0-1)")
    current_active_instances: int = Field(..., description="Currently active instances")
    bottleneck_nodes: List[str] = Field(
        default_factory=list, description="Nodes with longest processing times"
    )


class WorkflowPerformanceMetrics(BaseModel):
    """Workflow performance metrics schema."""

    period_start: datetime = Field(..., description="Metrics period start")
    period_end: datetime = Field(..., description="Metrics period end")
    total_workflows: int = Field(..., description="Total active workflows")
    total_instances: int = Field(..., description="Total instances processed")
    avg_processing_time_hours: Optional[float] = Field(
        None, description="Average processing time"
    )
    throughput_per_day: float = Field(..., description="Average instances per day")
    success_rate: float = Field(..., description="Success rate (0-1)")
    most_used_workflows: List[Dict[str, Any]] = Field(
        default_factory=list, description="Most frequently used workflows"
    )
