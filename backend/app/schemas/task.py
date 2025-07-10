"""Task schemas for API serialization."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_core import ValidationInfo

from app.models.task import DependencyType, TaskPriority, TaskStatus


class TaskBase(BaseModel):
    """Base task schema."""

    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status: TaskStatus = Field(default=TaskStatus.TODO, description="Task status")
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM, description="Task priority"
    )
    estimated_hours: Optional[float] = Field(None, ge=0, description="Estimated hours")
    actual_hours: Optional[float] = Field(None, ge=0, description="Actual hours spent")
    start_date: Optional[datetime] = Field(None, description="Task start date")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    progress_percentage: int = Field(
        default=0, ge=0, le=100, description="Progress percentage"
    )
    tags: Optional[str] = Field(
        None, max_length=500, description="Comma-separated tags"
    )

    @field_validator("due_date", mode="before")
    @classmethod
    def validate_due_date(cls, v: Optional[datetime], info: ValidationInfo) -> Optional[datetime]:
        """Validate due date is not in the past."""
        if v and hasattr(info, "data"):
            start_date = info.data.get("start_date")
            if start_date and v < start_date:
                raise ValueError("Due date cannot be before start date")
        return v


class TaskCreate(TaskBase):
    """Schema for creating a task."""

    project_id: int = Field(..., description="Project ID this task belongs to")
    assigned_to: Optional[int] = Field(None, description="User ID of assignee")


class TaskUpdate(BaseModel):
    """Schema for updating a task."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[int] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    actual_hours: Optional[float] = Field(None, ge=0)
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    tags: Optional[str] = Field(None, max_length=500)


class TaskAssign(BaseModel):
    """Schema for assigning a task."""

    assigned_to: int = Field(..., description="User ID to assign task to")


class TaskStatusUpdate(BaseModel):
    """Schema for updating task status."""

    status: TaskStatus = Field(..., description="New task status")


class TaskProgressUpdate(BaseModel):
    """Schema for updating task progress."""

    progress_percentage: int = Field(
        ..., ge=0, le=100, description="Progress percentage"
    )


class UserBasic(BaseModel):
    """Basic user information for task responses."""

    id: int
    email: str
    full_name: str

    model_config = {"from_attributes": True}


class ProjectBasic(BaseModel):
    """Basic project information for task responses."""

    id: int
    name: str
    code: str

    model_config = {"from_attributes": True}


class TaskDependencyResponse(BaseModel):
    """Task dependency response schema."""

    id: int
    task_id: int
    depends_on_task_id: int
    dependency_type: DependencyType
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskHistoryResponse(BaseModel):
    """Task history response schema."""

    id: int
    action: str
    details: Optional[str]
    changed_by: int
    changed_at: datetime
    user: UserBasic

    model_config = {"from_attributes": True}


class TaskResponse(TaskBase):
    """Complete task response schema."""

    id: int
    project_id: int
    created_by: int
    assigned_to: Optional[int]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    # Computed properties
    is_overdue: bool
    is_blocked: bool

    # Related objects
    project: ProjectBasic
    creator: UserBasic
    assignee: Optional[UserBasic]

    # Dependencies (optional, for detailed view)
    dependencies: Optional[List[TaskDependencyResponse]] = None
    task_history: Optional[List[TaskHistoryResponse]] = None

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    """Response schema for task list with pagination."""

    items: List[TaskResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


class TaskDependencyCreate(BaseModel):
    """Schema for creating task dependency."""

    depends_on_task_id: int = Field(..., description="Task ID this task depends on")
    dependency_type: DependencyType = Field(
        default=DependencyType.DEPENDS_ON, description="Type of dependency"
    )


class TaskDependencyDelete(BaseModel):
    """Schema for deleting task dependency."""

    depends_on_task_id: int = Field(
        ..., description="Task ID to remove dependency from"
    )


class TaskSearchParams(BaseModel):
    """Parameters for searching tasks."""

    project_id: Optional[int] = None
    assigned_to: Optional[int] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    is_overdue: Optional[bool] = None
    tags: Optional[str] = None
    search: Optional[str] = Field(None, description="Search in title and description")
    start_date_from: Optional[datetime] = None
    start_date_to: Optional[datetime] = None
    due_date_from: Optional[datetime] = None
    due_date_to: Optional[datetime] = None
    created_by: Optional[int] = None

    # Pagination
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)

    # Sorting
    sort_by: str = Field(default="created_at", description="Field to sort by")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class TaskStatistics(BaseModel):
    """Task statistics response."""

    total_tasks: int
    todo_tasks: int
    in_progress_tasks: int
    in_review_tasks: int
    completed_tasks: int
    cancelled_tasks: int
    blocked_tasks: int
    overdue_tasks: int

    # Progress statistics
    avg_progress: float
    completion_rate: float

    # Time statistics
    avg_estimated_hours: Optional[float]
    avg_actual_hours: Optional[float]
    total_estimated_hours: Optional[float]
    total_actual_hours: Optional[float]


class TaskBulkAction(BaseModel):
    """Schema for bulk task actions."""

    task_ids: List[int] = Field(..., min_length=1, description="List of task IDs")
    action: str = Field(..., description="Action to perform")

    # Action-specific parameters
    status: Optional[TaskStatus] = None
    assigned_to: Optional[int] = None
    priority: Optional[TaskPriority] = None


class TaskBulkActionResponse(BaseModel):
    """Response for bulk task actions."""

    success_count: int
    error_count: int
    errors: List[dict]
    updated_tasks: List[TaskResponse]


class TaskTemplate(BaseModel):
    """Task template schema for creating multiple similar tasks."""

    name: str = Field(..., description="Template name")
    tasks: List[TaskCreate] = Field(..., description="List of tasks in template")


class TaskImportData(BaseModel):
    """Schema for importing tasks from external sources."""

    tasks: List[dict] = Field(..., description="List of task data to import")
    project_id: int = Field(..., description="Project to import tasks into")
    default_assignee: Optional[int] = None


class TaskExportParams(BaseModel):
    """Parameters for exporting tasks."""

    project_id: Optional[int] = None
    format: str = Field(default="csv", pattern="^(csv|xlsx|json)$")
    include_history: bool = Field(default=False)
    include_dependencies: bool = Field(default=False)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class BulkStatusUpdate(BaseModel):
    """Schema for bulk status updates."""

    task_ids: List[int] = Field(..., min_length=1, description="List of task IDs")
    status: TaskStatus = Field(..., description="New status for tasks")


class BulkUpdateResponse(BaseModel):
    """Response for bulk operations."""

    success_count: int
    error_count: int
    errors: List[str]
