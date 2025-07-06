"""Project milestone schemas for API validation and serialization."""

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.types import UserId


class ProjectMilestoneBase(BaseModel):
    """Base project milestone schema."""
    name: str = Field(..., min_length=1, max_length=200, description="Milestone name")
    description: Optional[str] = Field(None, description="Milestone description")
    due_date: date = Field(..., description="Milestone due date")
    is_critical: bool = Field(default=False, description="Whether milestone is critical")
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        str_strip_whitespace=True
    )


class ProjectMilestoneCreate(ProjectMilestoneBase):
    """Project milestone creation schema."""
    phase_id: Optional[int] = Field(None, description="Associated phase ID")


class ProjectMilestoneUpdate(BaseModel):
    """Project milestone update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[date] = None
    completed_date: Optional[date] = None
    status: Optional[str] = None
    is_critical: Optional[bool] = None
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status value."""
        if v is not None:
            valid_statuses = ['pending', 'completed', 'missed']
            if v not in valid_statuses:
                raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        str_strip_whitespace=True
    )


class ProjectMilestoneSummary(BaseModel):
    """Project milestone summary for lists."""
    id: int
    project_id: int
    phase_id: Optional[int]
    name: str
    due_date: date
    completed_date: Optional[date]
    status: str
    is_critical: bool
    is_completed: bool
    is_missed: bool
    is_pending: bool
    is_overdue: bool
    days_until_due: int
    is_upcoming: bool
    
    model_config = ConfigDict(from_attributes=True)


class ProjectMilestoneResponse(ProjectMilestoneBase):
    """Full project milestone response."""
    id: int
    project_id: int
    phase_id: Optional[int]
    completed_date: Optional[date]
    status: str
    created_at: date
    updated_at: date
    created_by: Optional[UserId]
    updated_by: Optional[UserId]
    
    # Computed fields
    is_completed: bool
    is_missed: bool
    is_pending: bool
    is_overdue: bool
    days_until_due: int
    completion_delay_days: Optional[int]
    is_upcoming: bool
    
    model_config = ConfigDict(from_attributes=True)