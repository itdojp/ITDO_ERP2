"""Project schemas for API operations."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, validator

from app.models.project import ProjectPriority, ProjectStatus, ProjectType


class ProjectBase(BaseModel):
    """Base schema for Project."""

    code: str = Field(..., min_length=2, max_length=50, description="Unique project code")
    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    department_id: Optional[int] = Field(None, description="Department ID")
    status: str = Field(ProjectStatus.PLANNING.value, description="Project status")
    priority: str = Field(ProjectPriority.MEDIUM.value, description="Project priority")
    project_type: str = Field(ProjectType.INTERNAL.value, description="Project type")
    start_date: Optional[date] = Field(None, description="Project start date")
    end_date: Optional[date] = Field(None, description="Planned end date")
    budget: Optional[Decimal] = Field(None, ge=0, description="Total budget")
    estimated_hours: Optional[float] = Field(None, ge=0, description="Estimated hours")
    is_public: bool = Field(False, description="Whether project is public")
    tags: Optional[List[str]] = Field(None, description="Project tags")
    settings: Optional[Dict[str, Any]] = Field(None, description="Project settings")

    @validator("status")
    def validate_status(cls, v: str) -> str:
        """Validate project status."""
        valid_statuses = [status.value for status in ProjectStatus]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        return v

    @validator("priority")
    def validate_priority(cls, v: str) -> str:
        """Validate project priority."""
        valid_priorities = [priority.value for priority in ProjectPriority]
        if v not in valid_priorities:
            raise ValueError(f"Invalid priority. Must be one of: {valid_priorities}")
        return v

    @validator("project_type")
    def validate_project_type(cls, v: str) -> str:
        """Validate project type."""
        valid_types = [ptype.value for ptype in ProjectType]
        if v not in valid_types:
            raise ValueError(f"Invalid project type. Must be one of: {valid_types}")
        return v

    @validator("end_date")
    def validate_end_date(cls, v: Optional[date], values: Dict[str, Any]) -> Optional[date]:
        """Validate end date is after start date."""
        if v and values.get("start_date") and v < values["start_date"]:
            raise ValueError("End date must be after start date")
        return v


class ProjectCreate(ProjectBase):
    """Schema for creating a Project."""

    organization_id: int = Field(..., description="Organization ID")
    department_id: Optional[int] = Field(None, description="Department ID")
    manager_id: Optional[int] = Field(None, description="Project manager ID")
    start_date: date = Field(..., description="Project start date")


class ProjectUpdate(BaseModel):
    """Schema for updating a Project."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None)
    status: Optional[str] = Field(None)
    priority: Optional[str] = Field(None)
    project_type: Optional[str] = Field(None)
    start_date: Optional[date] = Field(None)
    end_date: Optional[date] = Field(None)
    actual_start_date: Optional[date] = Field(None)
    actual_end_date: Optional[date] = Field(None)
    budget: Optional[float] = Field(None, ge=0)
    spent_budget: Optional[float] = Field(None, ge=0)
    estimated_hours: Optional[float] = Field(None, ge=0)
    actual_hours: Optional[float] = Field(None, ge=0)
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    manager_id: Optional[int] = Field(None)
    is_public: Optional[bool] = Field(None)
    is_active: Optional[bool] = Field(None)
    tags: Optional[List[str]] = Field(None)
    settings: Optional[Dict[str, Any]] = Field(None)
    project_metadata: Optional[Dict[str, Any]] = Field(None)

    @validator("status")
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate project status."""
        if v is not None:
            valid_statuses = [status.value for status in ProjectStatus]
            if v not in valid_statuses:
                raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        return v

    @validator("priority")
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        """Validate project priority."""
        if v is not None:
            valid_priorities = [priority.value for priority in ProjectPriority]
            if v not in valid_priorities:
                raise ValueError(f"Invalid priority. Must be one of: {valid_priorities}")
        return v

    @validator("project_type")
    def validate_project_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate project type."""
        if v is not None:
            valid_types = [ptype.value for ptype in ProjectType]
            if v not in valid_types:
                raise ValueError(f"Invalid project type. Must be one of: {valid_types}")
        return v

    model_config = ConfigDict(extra="forbid")


class ProjectMemberBase(BaseModel):
    """Base schema for Project Member."""

    user_id: int = Field(..., description="User ID")
    role: str = Field(..., description="Member role in project")
    permissions: Optional[List[str]] = Field(None, description="Member permissions")
    is_active: bool = Field(True, description="Whether member is active")


class ProjectMemberCreate(ProjectMemberBase):
    """Schema for creating a Project Member."""

    project_id: int = Field(..., description="Project ID")


class ProjectMemberUpdate(BaseModel):
    """Schema for updating a Project Member."""

    role: Optional[str] = Field(None)
    permissions: Optional[List[str]] = Field(None)
    is_active: Optional[bool] = Field(None)

    model_config = ConfigDict(extra="forbid")


class ProjectMemberResponse(ProjectMemberBase):
    """Schema for Project Member response."""

    id: int
    project_id: int
    user_email: str
    user_name: str
    joined_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(ProjectBase):
    """Schema for Project response."""

    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    member_count: int
    task_count: int
    progress_percentage: float
    
    # Extended fields
    department_id: Optional[int]
    owner_id: int
    manager_id: Optional[int]
    actual_start_date: Optional[date]
    actual_end_date: Optional[date]
    spent_budget: Optional[Decimal]
    actual_hours: Optional[float]
    completion_date: Optional[datetime]
    is_active: bool
    is_archived: bool
    metadata: Optional[Dict[str, Any]]

    # Computed properties
    is_overdue: bool
    days_remaining: Optional[int]
    budget_usage_percentage: Optional[float]
    hours_usage_percentage: Optional[float]
    is_on_schedule: bool
    status_color: str
    priority_level: int
    health_status: str

    # Relationships
    owner_email: Optional[str] = Field(None, description="Owner email")
    manager_email: Optional[str] = Field(None, description="Manager email")
    organization_name: Optional[str] = Field(None, description="Organization name")
    department_name: Optional[str] = Field(None, description="Department name")

    model_config = ConfigDict(from_attributes=True)


class ProjectSummary(BaseModel):
    """Schema for Project summary."""

    id: int
    code: str
    name: str
    status: str
    priority: str
    progress_percentage: int
    is_overdue: bool
    days_remaining: Optional[int]
    budget_usage_percentage: Optional[float]
    member_count: int
    milestone_count: int
    health_status: str
    is_on_schedule: bool
    status_color: str
    organization_name: str
    department_name: Optional[str]
    owner_name: str

    model_config = ConfigDict(from_attributes=True)


class ProjectAnalytics(BaseModel):
    """Schema for Project analytics."""

    project_id: int
    total_tasks: int
    completed_tasks: int
    active_tasks: int
    overdue_tasks: int
    total_milestones: int
    completed_milestones: int
    team_size: int
    budget_utilization: Optional[float]
    hours_utilization: Optional[float]
    completion_rate: float
    average_task_completion_time: Optional[float]
    performance_metrics: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class ProjectFilter(BaseModel):
    """Schema for Project filtering."""

    organization_id: Optional[int] = Field(None, description="Filter by organization")
    department_id: Optional[int] = Field(None, description="Filter by department")
    owner_id: Optional[int] = Field(None, description="Filter by owner")
    manager_id: Optional[int] = Field(None, description="Filter by manager")
    status: Optional[str] = Field(None, description="Filter by status")
    priority: Optional[str] = Field(None, description="Filter by priority")
    project_type: Optional[str] = Field(None, description="Filter by project type")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_public: Optional[bool] = Field(None, description="Filter by public status")
    is_overdue: Optional[bool] = Field(None, description="Filter by overdue status")
    start_date_from: Optional[date] = Field(None, description="Filter by start date from")
    start_date_to: Optional[date] = Field(None, description="Filter by start date to")
    end_date_from: Optional[date] = Field(None, description="Filter by end date from")
    end_date_to: Optional[date] = Field(None, description="Filter by end date to")
    budget_min: Optional[float] = Field(None, ge=0, description="Minimum budget")
    budget_max: Optional[float] = Field(None, ge=0, description="Maximum budget")
    search: Optional[str] = Field(None, description="Search in name and description")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")

    model_config = ConfigDict(extra="forbid")


class ProjectBulkOperation(BaseModel):
    """Schema for bulk project operations."""

    project_ids: List[int] = Field(..., min_length=1, description="List of project IDs")
    operation: str = Field(..., description="Operation to perform")
    data: Optional[Dict[str, Any]] = Field(None, description="Operation data")

    @validator("operation")
    def validate_operation(cls, v: str) -> str:
        """Validate bulk operation."""
        valid_operations = [
            "archive",
            "unarchive",
            "activate",
            "deactivate",
            "update_status",
            "update_priority",
            "assign_manager",
            "add_tags",
            "remove_tags",
        ]
        if v not in valid_operations:
            raise ValueError(f"Invalid operation. Must be one of: {valid_operations}")
        return v

    model_config = ConfigDict(extra="forbid")


class ProjectStatusTransition(BaseModel):
    """Schema for project status transitions."""

    from_status: str = Field(..., description="Current status")
    to_status: str = Field(..., description="Target status")
    reason: Optional[str] = Field(None, description="Reason for transition")
    notes: Optional[str] = Field(None, description="Additional notes")

    @validator("from_status", "to_status")
    def validate_status(cls, v: str) -> str:
        """Validate status values."""
        valid_statuses = [status.value for status in ProjectStatus]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        return v

    model_config = ConfigDict(extra="forbid")


class ProjectStatistics(BaseModel):
    """Schema for project statistics response."""

    project_id: int
    member_count: int
    task_count: int
    completed_tasks: int
    active_tasks: int
    overdue_tasks: int
    progress_percentage: float
    budget_utilization: Optional[float] = None
    hours_utilization: Optional[float] = None
    health_status: str
    is_on_schedule: bool
    days_remaining: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class DeleteResponse(BaseModel):
    """Schema for delete operation response."""

    success: bool
    message: str
    deleted_id: Optional[int] = None


class PaginatedResponse(BaseModel):
    """Generic paginated response schema."""

    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int

    model_config = ConfigDict(from_attributes=True)
