"""Project schemas for API validation and serialization."""

from datetime import date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.types import OrganizationId, DepartmentId, UserId


class ProjectBase(BaseModel):
    """Base project schema."""
    code: str = Field(..., min_length=1, max_length=50, description="Project code")
    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    name_en: Optional[str] = Field(None, max_length=200, description="Project name in English")
    description: Optional[str] = Field(None, description="Project description")
    project_type: str = Field(default="general", max_length=50, description="Project type")
    priority: str = Field(default="medium", description="Project priority")
    planned_start_date: Optional[date] = Field(None, description="Planned start date")
    planned_end_date: Optional[date] = Field(None, description="Planned end date")
    budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="Project budget")
    currency: str = Field(default="JPY", min_length=3, max_length=3, description="Currency code")
    tags: List[str] = Field(default_factory=list, description="Project tags")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom fields")
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate project code."""
        # Remove spaces and convert to uppercase
        v = v.strip().upper()
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Code must contain only alphanumeric characters, hyphens, and underscores')
        return v
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Validate priority value."""
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        if v not in valid_priorities:
            raise ValueError(f'Priority must be one of: {", ".join(valid_priorities)}')
        return v
    
    @field_validator('project_type')
    @classmethod
    def validate_project_type(cls, v: str) -> str:
        """Validate project type."""
        valid_types = ['general', 'development', 'research', 'maintenance', 'implementation']
        if v not in valid_types:
            raise ValueError(f'Project type must be one of: {", ".join(valid_types)}')
        return v
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        str_strip_whitespace=True
    )


class ProjectCreate(ProjectBase):
    """Project creation schema."""
    organization_id: OrganizationId = Field(..., description="Organization ID")
    department_id: Optional[DepartmentId] = Field(None, description="Department ID")
    parent_id: Optional[int] = Field(None, description="Parent project ID")
    project_manager_id: Optional[UserId] = Field(None, description="Project manager ID")
    status: str = Field(default="planning", description="Initial project status")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status value."""
        valid_statuses = ['planning', 'in_progress', 'completed', 'cancelled', 'on_hold']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v


class ProjectUpdate(BaseModel):
    """Project update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    name_en: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    department_id: Optional[DepartmentId] = None
    project_type: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = None
    priority: Optional[str] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    actual_cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    project_manager_id: Optional[UserId] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status value."""
        if v is not None:
            valid_statuses = ['planning', 'in_progress', 'completed', 'cancelled', 'on_hold']
            if v not in valid_statuses:
                raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        """Validate priority value."""
        if v is not None:
            valid_priorities = ['low', 'medium', 'high', 'urgent']
            if v not in valid_priorities:
                raise ValueError(f'Priority must be one of: {", ".join(valid_priorities)}')
        return v
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        str_strip_whitespace=True
    )


class ProjectSummary(BaseModel):
    """Project summary for lists."""
    id: int
    code: str
    name: str
    name_en: Optional[str]
    organization_id: OrganizationId
    department_id: Optional[DepartmentId]
    project_type: str
    status: str
    priority: str
    progress_percentage: int
    planned_start_date: Optional[date]
    planned_end_date: Optional[date]
    is_overdue: bool
    is_active: bool
    member_count: Optional[int] = Field(None, description="Number of project members")
    
    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(ProjectBase):
    """Full project response."""
    id: int
    organization_id: OrganizationId
    department_id: Optional[DepartmentId]
    status: str
    progress_percentage: int
    actual_start_date: Optional[date]
    actual_end_date: Optional[date]
    actual_cost: Optional[Decimal]
    parent_id: Optional[int]
    project_manager_id: Optional[UserId]
    created_at: date
    updated_at: date
    created_by: Optional[UserId]
    updated_by: Optional[UserId]
    
    # Computed fields
    full_code: str
    is_sub_project: bool
    is_parent_project: bool
    is_overdue: bool
    is_over_budget: bool
    budget_usage_percentage: Optional[float]
    days_remaining: Optional[int]
    duration_days: Optional[int]
    
    # Relationships
    organization: Optional[Dict[str, Any]] = None
    department: Optional[Dict[str, Any]] = None
    project_manager: Optional[Dict[str, Any]] = None
    parent: Optional[Dict[str, Any]] = None
    sub_project_count: int = 0
    member_count: int = 0
    phase_count: int = 0
    milestone_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class ProjectTree(BaseModel):
    """Project hierarchy tree structure."""
    id: int
    code: str
    name: str
    status: str
    progress_percentage: int
    level: int
    parent_id: Optional[int]
    children: List["ProjectTree"] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class ProjectStatistics(BaseModel):
    """Project statistics."""
    id: int
    total_budget: Optional[Decimal]
    total_actual_cost: Optional[Decimal]
    budget_usage_percentage: Optional[float]
    overall_progress: int
    member_count: int
    active_member_count: int
    phase_count: int
    completed_phase_count: int
    milestone_count: int
    completed_milestone_count: int
    upcoming_milestone_count: int
    overdue_milestone_count: int
    task_count: int = 0  # For future integration
    completed_task_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


# Interface schemas for other modules
class ProjectInfo(BaseModel):
    """Basic project information for use in other modules."""
    id: int
    code: str
    name: str
    status: str
    
    model_config = ConfigDict(from_attributes=True)