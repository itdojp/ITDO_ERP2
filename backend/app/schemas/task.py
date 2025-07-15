"""Task schemas for API request/response validation."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task status enumeration."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"


class TaskPriority(str, Enum):
    """Task priority enumeration."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskBase(BaseModel):
    """Base task schema."""

    title: str = Field(..., max_length=200, description="Task title")
    description: str | None = Field(
        None, max_length=5000, description="Task description"
    )
    project_id: int = Field(..., description="Project ID")
    parent_task_id: int | None = Field(None, description="Parent task ID")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Task priority")
    due_date: datetime | None = Field(None, description="Due date")
    estimated_hours: float | None = Field(None, ge=0, description="Estimated hours")


class TaskCreate(TaskBase):
    """Schema for creating a task."""

    assignee_ids: list[int] | None = Field(None, description="List of assignee IDs")
    tags: list[str] | None = Field(None, description="Task tags")
    # CRITICAL: Department integration fields for Phase 3
    department_id: int | None = Field(
        None, description="Department ID for task assignment"
    )
    department_visibility: str = Field(
        default="department_hierarchy", description="Visibility scope"
    )


class TaskUpdate(BaseModel):
    """Schema for updating a task."""

    title: str | None = Field(None, max_length=200)
    description: str | None = Field(None, max_length=5000)
    priority: TaskPriority | None = None
    due_date: datetime | None = None
    estimated_hours: float | None = Field(None, ge=0)
    actual_hours: float | None = Field(None, ge=0)


class TaskStatusUpdate(BaseModel):
    """Schema for updating task status."""

    status: TaskStatus
    comment: str | None = Field(None, max_length=1000)


class TaskAssignment(BaseModel):
    """Schema for task assignment."""

    user_id: int
    role: str | None = Field(None, max_length=50)


class TaskDependency(BaseModel):
    """Schema for task dependency."""

    depends_on_task_id: int
    dependency_type: str = Field("blocking", description="Dependency type")


class UserInfo(BaseModel):
    """User information for responses."""

    id: int
    name: str
    email: str


class ProjectInfo(BaseModel):
    """Project information for responses."""

    id: int
    name: str


class DepartmentBasic(BaseModel):
    """Department basic information for task responses."""

    id: int
    name: str
    code: str

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    """Task response schema."""

    id: int
    title: str
    description: str | None
    project: ProjectInfo
    parent_task_id: int | None
    status: TaskStatus
    priority: TaskPriority
    due_date: datetime | None
    estimated_hours: float | None
    actual_hours: float | None
    assignees: list[UserInfo]
    tags: list[str]
    created_at: datetime
    updated_at: datetime
    created_by: UserInfo
    # CRITICAL: Department integration fields for Phase 3
    department_id: int | None = None
    department_visibility: str = "department_hierarchy"
    department: DepartmentBasic | None = None

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Response for task list with pagination."""

    items: list[TaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TaskHistoryItem(BaseModel):
    """Task history item schema."""

    id: int
<<<<<<< HEAD
    field_name: str
    old_value: str | None
    new_value: str | None
    changed_by: UserInfo
    changed_at: datetime
=======
    action: str
    user_name: str
    timestamp: datetime
    changes: dict[str, Any]
>>>>>>> main


class TaskHistoryResponse(BaseModel):
    """Response for task history."""

    items: list[TaskHistoryItem]
    total: int


class BulkStatusUpdate(BaseModel):
    """Schema for bulk status update."""

    task_ids: list[int] = Field(..., min_length=1)
    status: TaskStatus


class BulkUpdateResponse(BaseModel):
    """Response for bulk update operations."""

    updated_count: int
    failed_count: int
    errors: list[dict[str, Any]] | None = None
