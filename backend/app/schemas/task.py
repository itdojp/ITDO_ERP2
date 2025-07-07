"""Task management Pydantic schemas."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.task import TaskStatus, TaskPriority, DependencyType, AssignmentRole


# Base schemas
class TaskBase(BaseModel):
    """Base task schema with common fields."""
    title: str = Field(..., max_length=200, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    project_id: int = Field(..., gt=0, description="Project ID")
    parent_task_id: Optional[int] = Field(None, gt=0, description="Parent task ID")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Task priority")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    start_date: Optional[datetime] = Field(None, description="Task start date")
    estimated_hours: Optional[float] = Field(None, ge=0, description="Estimated hours")
    tags: Optional[List[str]] = Field(None, description="Task tags")


class TaskCreate(TaskBase):
    """Schema for creating a new task."""
    assignee_ids: Optional[List[int]] = Field(None, description="Initial assignee user IDs")
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None and len(v) > 10:
            raise ValueError('Maximum 10 tags allowed')
        return v


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    actual_hours: Optional[float] = Field(None, ge=0)
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    tags: Optional[List[str]] = None
    version: int = Field(..., description="Version for optimistic locking")
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None and len(v) > 10:
            raise ValueError('Maximum 10 tags allowed')
        return v


class TaskStatusUpdate(BaseModel):
    """Schema for updating task status."""
    status: TaskStatus = Field(..., description="New task status")
    comment: Optional[str] = Field(None, description="Status change comment")
    version: int = Field(..., description="Version for optimistic locking")


class TaskResponse(BaseModel):
    """Schema for task response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    description: Optional[str]
    project_id: int
    parent_task_id: Optional[int]
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[datetime]
    start_date: Optional[datetime]
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    progress_percentage: int
    tags: Optional[List[str]]
    version: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]
    updated_by: Optional[int]
    is_deleted: bool


class TaskListResponse(BaseModel):
    """Schema for task list response with pagination."""
    items: List[TaskResponse]
    total: int
    page: int = 1
    limit: int = 20
    has_next: bool = False
    has_prev: bool = False


class TaskSearchParams(BaseModel):
    """Schema for task search parameters."""
    search: Optional[str] = Field(None, description="Search in title and description")
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[int] = None
    project_id: Optional[int] = None
    due_date_from: Optional[datetime] = None
    due_date_to: Optional[datetime] = None
    tags: Optional[List[str]] = None
    is_overdue: Optional[bool] = None
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
    sort_by: Optional[str] = Field("created_at", description="Sort field")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$")


# Assignment schemas
class TaskAssignmentCreate(BaseModel):
    """Schema for creating a task assignment."""
    user_id: int = Field(..., gt=0)
    role: AssignmentRole = Field(AssignmentRole.ASSIGNEE)


class TaskAssignmentResponse(BaseModel):
    """Schema for task assignment response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    task_id: int
    user_id: int
    role: AssignmentRole
    assigned_at: datetime
    assigned_by: Optional[int]


class BulkAssignmentRequest(BaseModel):
    """Schema for bulk user assignment."""
    user_ids: List[int] = Field(..., min_length=1, max_length=50)
    role: AssignmentRole = Field(AssignmentRole.ASSIGNEE)


# Dependency schemas
class TaskDependencyCreate(BaseModel):
    """Schema for creating a task dependency."""
    predecessor_id: int = Field(..., gt=0)
    dependency_type: DependencyType = Field(DependencyType.FINISH_TO_START)
    lag_time: int = Field(0, description="Lag time in days")


class TaskDependencyResponse(BaseModel):
    """Schema for task dependency response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    predecessor_id: int
    successor_id: int
    dependency_type: DependencyType
    lag_time: int


# Comment schemas
class TaskCommentCreate(BaseModel):
    """Schema for creating a task comment."""
    content: str = Field(..., min_length=1, max_length=5000)
    parent_comment_id: Optional[int] = None
    mentioned_users: Optional[List[int]] = None


class TaskCommentResponse(BaseModel):
    """Schema for task comment response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    task_id: int
    content: str
    user_id: int
    parent_comment_id: Optional[int]
    mentioned_users: Optional[List[int]]
    created_at: datetime
    updated_at: datetime
    is_deleted: bool


# Attachment schemas
class TaskAttachmentResponse(BaseModel):
    """Schema for task attachment response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    task_id: int
    comment_id: Optional[int]
    file_name: str
    file_size: int
    mime_type: str
    uploaded_by: Optional[int]
    created_at: datetime


# Analytics schemas
class UserWorkloadResponse(BaseModel):
    """Schema for user workload analytics."""
    user_id: int
    assigned_tasks_count: int
    estimated_hours_total: float
    overdue_tasks_count: int
    completed_tasks_count: int
    in_progress_tasks_count: int


class TaskAnalyticsResponse(BaseModel):
    """Schema for task analytics response."""
    total_tasks: int
    by_status: Dict[TaskStatus, int]
    by_priority: Dict[TaskPriority, int]
    overdue_count: int
    completion_rate: float
    average_completion_time_days: Optional[float]


# WebSocket schemas
class TaskEventData(BaseModel):
    """Schema for WebSocket task events."""
    type: str = Field(..., description="Event type")
    task_id: int
    user_id: Optional[int] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


# Bulk operation schemas
class BulkTaskUpdate(BaseModel):
    """Schema for bulk task updates."""
    task_ids: List[int] = Field(..., min_length=1, max_length=100)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[int] = None
    due_date: Optional[datetime] = None


class BulkOperationResponse(BaseModel):
    """Schema for bulk operation response."""
    success_count: int
    error_count: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)