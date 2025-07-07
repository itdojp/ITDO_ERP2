"""Task schemas for API request/response validation."""

from datetime import datetime
from typing import Optional, List, Any
from enum import Enum
from pydantic import BaseModel, Field, validator


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
    description: Optional[str] = Field(None, max_length=5000, description="Task description")
    project_id: int = Field(..., description="Project ID")
    parent_task_id: Optional[int] = Field(None, description="Parent task ID")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Task priority")
    due_date: Optional[datetime] = Field(None, description="Due date")
    estimated_hours: Optional[float] = Field(None, ge=0, description="Estimated hours")


class TaskCreate(TaskBase):
    """Schema for creating a task."""
    assignee_ids: Optional[List[int]] = Field(None, description="List of assignee IDs")
    tags: Optional[List[str]] = Field(None, description="Task tags")


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    actual_hours: Optional[float] = Field(None, ge=0)


class TaskStatusUpdate(BaseModel):
    """Schema for updating task status."""
    status: TaskStatus
    comment: Optional[str] = Field(None, max_length=1000)


class TaskAssignment(BaseModel):
    """Schema for task assignment."""
    user_id: int
    role: Optional[str] = Field(None, max_length=50)


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


class TaskResponse(BaseModel):
    """Task response schema."""
    id: int
    title: str
    description: Optional[str]
    project: ProjectInfo
    parent_task_id: Optional[int]
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[datetime]
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    assignees: List[UserInfo]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    created_by: UserInfo

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Response for task list with pagination."""
    items: List[TaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TaskHistoryItem(BaseModel):
    """Task history item schema."""
    id: int
    field_name: str
    old_value: Optional[str]
    new_value: Optional[str]
    changed_by: UserInfo
    changed_at: datetime


class TaskHistoryResponse(BaseModel):
    """Response for task history."""
    items: List[TaskHistoryItem]
    total: int


class BulkStatusUpdate(BaseModel):
    """Schema for bulk status update."""
    task_ids: List[int] = Field(..., min_length=1)
    status: TaskStatus


class BulkUpdateResponse(BaseModel):
    """Response for bulk update operations."""
    updated_count: int
    failed_count: int
    errors: Optional[List[dict[str, Any]]] = None