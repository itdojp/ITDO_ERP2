"""Task schemas for API operations."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, validator

from app.models.task import TaskPriority, TaskStatus, TaskType


class TaskBase(BaseModel):
    """Base schema for Task."""

    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status: str = Field(TaskStatus.TODO.value, description="Task status")
    priority: str = Field(TaskPriority.MEDIUM.value, description="Task priority")
    task_type: str = Field(TaskType.FEATURE.value, description="Task type")
    due_date: Optional[date] = Field(None, description="Due date")
    estimated_hours: Optional[float] = Field(None, ge=0, description="Estimated hours")
    labels: Optional[List[str]] = Field(None, description="Task labels")
    tags: Optional[List[str]] = Field(None, description="Task tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator("status")
    def validate_status(cls, v):
        """Validate task status."""
        valid_statuses = [status.value for status in TaskStatus]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        return v

    @validator("priority")
    def validate_priority(cls, v):
        """Validate task priority."""
        valid_priorities = [priority.value for priority in TaskPriority]
        if v not in valid_priorities:
            raise ValueError(f"Invalid priority. Must be one of: {valid_priorities}")
        return v

    @validator("task_type")
    def validate_task_type(cls, v):
        """Validate task type."""
        valid_types = [task_type.value for task_type in TaskType]
        if v not in valid_types:
            raise ValueError(f"Invalid task type. Must be one of: {valid_types}")
        return v


class TaskCreate(TaskBase):
    """Schema for creating a Task."""

    project_id: int = Field(..., description="Project ID")
    assignee_id: Optional[int] = Field(None, description="Assignee user ID")
    reporter_id: Optional[int] = Field(None, description="Reporter user ID")
    epic_id: Optional[int] = Field(None, description="Epic task ID")
    parent_task_id: Optional[int] = Field(None, description="Parent task ID")
    dependencies: Optional[List[int]] = Field(None, description="Dependent task IDs")


class TaskUpdate(BaseModel):
    """Schema for updating a Task."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None)
    status: Optional[str] = Field(None)
    priority: Optional[str] = Field(None)
    task_type: Optional[str] = Field(None)
    due_date: Optional[date] = Field(None)
    start_date: Optional[date] = Field(None)
    completed_date: Optional[date] = Field(None)
    estimated_hours: Optional[float] = Field(None, ge=0)
    actual_hours: Optional[float] = Field(None, ge=0)
    assignee_id: Optional[int] = Field(None)
    reporter_id: Optional[int] = Field(None)
    epic_id: Optional[int] = Field(None)
    parent_task_id: Optional[int] = Field(None)
    dependencies: Optional[List[int]] = Field(None)
    labels: Optional[List[str]] = Field(None)
    tags: Optional[List[str]] = Field(None)
    metadata: Optional[Dict[str, Any]] = Field(None)
    is_active: Optional[bool] = Field(None)

    @validator("status")
    def validate_status(cls, v):
        """Validate task status."""
        if v is not None:
            valid_statuses = [status.value for status in TaskStatus]
            if v not in valid_statuses:
                raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        return v

    @validator("priority")
    def validate_priority(cls, v):
        """Validate task priority."""
        if v is not None:
            valid_priorities = [priority.value for priority in TaskPriority]
            if v not in valid_priorities:
                raise ValueError(f"Invalid priority. Must be one of: {valid_priorities}")
        return v

    @validator("task_type")
    def validate_task_type(cls, v):
        """Validate task type."""
        if v is not None:
            valid_types = [task_type.value for task_type in TaskType]
            if v not in valid_types:
                raise ValueError(f"Invalid task type. Must be one of: {valid_types}")
        return v

    model_config = ConfigDict(extra="forbid")


class TaskResponse(TaskBase):
    """Schema for Task response."""

    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    
    # Extended fields
    assignee_id: Optional[int]
    reporter_id: Optional[int]
    epic_id: Optional[int]
    parent_task_id: Optional[int]
    start_date: Optional[date]
    completed_date: Optional[date]
    actual_hours: Optional[float]
    story_points: Optional[int]
    is_active: bool
    
    # Computed properties
    is_overdue: bool
    days_remaining: Optional[int]
    completion_rate: Optional[float]
    time_spent_percentage: Optional[float]
    
    # Relationships
    assignee_name: Optional[str] = Field(None, description="Assignee name")
    reporter_name: Optional[str] = Field(None, description="Reporter name")
    project_name: Optional[str] = Field(None, description="Project name")
    epic_title: Optional[str] = Field(None, description="Epic title")
    parent_task_title: Optional[str] = Field(None, description="Parent task title")
    
    # Counts
    subtask_count: int = Field(0, description="Number of subtasks")
    dependency_count: int = Field(0, description="Number of dependencies")

    model_config = ConfigDict(from_attributes=True)


class TaskSummary(BaseModel):
    """Schema for Task summary."""

    id: int
    title: str
    status: str
    priority: str
    task_type: str
    due_date: Optional[date]
    is_overdue: bool
    days_remaining: Optional[int]
    assignee_name: Optional[str]
    project_name: str
    completion_rate: Optional[float]
    estimated_hours: Optional[float]
    actual_hours: Optional[float]

    model_config = ConfigDict(from_attributes=True)


class TaskFilter(BaseModel):
    """Schema for Task filtering."""

    project_id: Optional[int] = Field(None, description="Filter by project")
    assignee_id: Optional[int] = Field(None, description="Filter by assignee")
    reporter_id: Optional[int] = Field(None, description="Filter by reporter")
    epic_id: Optional[int] = Field(None, description="Filter by epic")
    parent_task_id: Optional[int] = Field(None, description="Filter by parent task")
    status: Optional[str] = Field(None, description="Filter by status")
    priority: Optional[str] = Field(None, description="Filter by priority")
    task_type: Optional[str] = Field(None, description="Filter by task type")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_overdue: Optional[bool] = Field(None, description="Filter by overdue status")
    due_date_from: Optional[date] = Field(None, description="Filter by due date from")
    due_date_to: Optional[date] = Field(None, description="Filter by due date to")
    estimated_hours_min: Optional[float] = Field(None, ge=0, description="Minimum estimated hours")
    estimated_hours_max: Optional[float] = Field(None, ge=0, description="Maximum estimated hours")
    labels: Optional[List[str]] = Field(None, description="Filter by labels")
    search: Optional[str] = Field(None, description="Search in title and description")

    model_config = ConfigDict(extra="forbid")


class TaskBulkOperation(BaseModel):
    """Schema for bulk task operations."""

    task_ids: List[int] = Field(..., min_length=1, description="List of task IDs")
    operation: str = Field(..., description="Operation to perform")
    data: Optional[Dict[str, Any]] = Field(None, description="Operation data")

    @validator("operation")
    def validate_operation(cls, v):
        """Validate bulk operation."""
        valid_operations = [
            "update_status",
            "update_priority",
            "assign_to",
            "move_to_project",
            "add_labels",
            "remove_labels",
            "set_due_date",
            "activate",
            "deactivate",
            "delete",
        ]
        if v not in valid_operations:
            raise ValueError(f"Invalid operation. Must be one of: {valid_operations}")
        return v

    model_config = ConfigDict(extra="forbid")


class TaskStatusTransition(BaseModel):
    """Schema for task status transitions."""

    from_status: str = Field(..., description="Current status")
    to_status: str = Field(..., description="Target status")
    reason: Optional[str] = Field(None, description="Reason for transition")
    notes: Optional[str] = Field(None, description="Additional notes")

    @validator("from_status", "to_status")
    def validate_status(cls, v):
        """Validate status values."""
        valid_statuses = [status.value for status in TaskStatus]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        return v

    model_config = ConfigDict(extra="forbid")


class TaskStatistics(BaseModel):
    """Schema for task statistics response."""
    
    task_id: int
    project_id: int
    completion_rate: Optional[float] = None
    time_spent_percentage: Optional[float] = None
    days_remaining: Optional[int] = None
    is_overdue: bool
    subtask_count: int
    dependency_count: int
    blocked_by_count: int
    
    model_config = ConfigDict(from_attributes=True)


class TaskTimeEntry(BaseModel):
    """Schema for task time entries."""

    task_id: int
    user_id: int
    hours_worked: float = Field(..., gt=0, description="Hours worked")
    work_date: date = Field(..., description="Date of work")
    description: Optional[str] = Field(None, description="Work description")
    billable: bool = Field(False, description="Whether time is billable")

    model_config = ConfigDict(extra="forbid")


class TaskComment(BaseModel):
    """Schema for task comments."""

    task_id: int
    user_id: int
    comment: str = Field(..., min_length=1, description="Comment text")
    is_internal: bool = Field(False, description="Whether comment is internal")

    model_config = ConfigDict(extra="forbid")


class TaskAssignment(BaseModel):
    """Schema for task assignment."""

    task_id: int
    assignee_id: int
    assigned_by: int
    notes: Optional[str] = Field(None, description="Assignment notes")

    model_config = ConfigDict(extra="forbid")


class DeleteResponse(BaseModel):
    """Schema for delete operation response."""
    
    success: bool
    message: str
    deleted_id: Optional[int] = None


class PaginatedTaskResponse(BaseModel):
    """Schema for paginated task responses."""
    
    items: List[TaskResponse]
    total: int
    page: int
    per_page: int
    pages: int
    
    model_config = ConfigDict(from_attributes=True)