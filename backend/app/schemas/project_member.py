"""Project member schemas for API validation and serialization."""

from datetime import date
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.types import UserId


class ProjectMemberBase(BaseModel):
    """Base project member schema."""
    role: str = Field(..., description="Member role in project")
    allocation_percentage: int = Field(
        default=100, 
        ge=0, 
        le=100, 
        description="Time allocation percentage"
    )
    start_date: date = Field(..., description="Member start date")
    end_date: Optional[date] = Field(None, description="Member end date")
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate member role."""
        valid_roles = ['owner', 'manager', 'member', 'viewer']
        if v not in valid_roles:
            raise ValueError(f'Role must be one of: {", ".join(valid_roles)}')
        return v
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        str_strip_whitespace=True
    )


class ProjectMemberCreate(ProjectMemberBase):
    """Project member creation schema."""
    user_id: UserId = Field(..., description="User ID to add as member")


class ProjectMemberUpdate(BaseModel):
    """Project member update schema."""
    role: Optional[str] = None
    allocation_percentage: Optional[int] = Field(None, ge=0, le=100)
    end_date: Optional[date] = None
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        """Validate member role."""
        if v is not None:
            valid_roles = ['owner', 'manager', 'member', 'viewer']
            if v not in valid_roles:
                raise ValueError(f'Role must be one of: {", ".join(valid_roles)}')
        return v
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        str_strip_whitespace=True
    )


class ProjectMemberSummary(BaseModel):
    """Project member summary for lists."""
    id: int
    user_id: UserId
    project_id: int
    role: str
    allocation_percentage: int
    start_date: date
    end_date: Optional[date]
    is_active: bool
    user: Dict[str, Any]
    days_allocated: int
    is_current: bool
    
    model_config = ConfigDict(from_attributes=True)


class ProjectMemberResponse(ProjectMemberBase):
    """Full project member response."""
    id: int
    user_id: UserId
    project_id: int
    is_active: bool
    created_at: date
    updated_at: date
    created_by: Optional[UserId]
    updated_by: Optional[UserId]
    user: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)