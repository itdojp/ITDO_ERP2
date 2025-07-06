"""Project phase schemas for API validation and serialization."""

from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.types import UserId


class ProjectPhaseBase(BaseModel):
    """Base project phase schema."""
    phase_number: int = Field(..., ge=1, description="Phase sequence number")
    name: str = Field(..., min_length=1, max_length=200, description="Phase name")
    description: Optional[str] = Field(None, description="Phase description")
    planned_start_date: date = Field(..., description="Planned start date")
    planned_end_date: date = Field(..., description="Planned end date")
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        str_strip_whitespace=True
    )


class ProjectPhaseCreate(ProjectPhaseBase):
    """Project phase creation schema."""
    status: str = Field(default="pending", description="Initial phase status")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status value."""
        valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v


class ProjectPhaseUpdate(BaseModel):
    """Project phase update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    status: Optional[str] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status value."""
        if v is not None:
            valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
            if v not in valid_statuses:
                raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        str_strip_whitespace=True
    )


class ProjectPhaseSummary(BaseModel):
    """Project phase summary for lists."""
    id: int
    project_id: int
    phase_number: int
    name: str
    status: str
    progress_percentage: int
    planned_start_date: date
    planned_end_date: date
    actual_start_date: Optional[date]
    actual_end_date: Optional[date]
    duration_days: Optional[int]
    is_active: bool
    is_completed: bool
    is_overdue: bool
    milestone_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class ProjectPhaseResponse(ProjectPhaseBase):
    """Full project phase response."""
    id: int
    project_id: int
    status: str
    progress_percentage: int
    actual_start_date: Optional[date]
    actual_end_date: Optional[date]
    created_at: date
    updated_at: date
    created_by: Optional[UserId]
    updated_by: Optional[UserId]
    
    # Computed fields
    duration_days: Optional[int]
    is_active: bool
    is_completed: bool
    is_overdue: bool
    
    model_config = ConfigDict(from_attributes=True)