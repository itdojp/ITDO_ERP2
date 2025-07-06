"""Project schemas."""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class ProjectBase(BaseModel):
    """Project base schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field("planning", regex="^(planning|in_progress|completed|cancelled|on_hold)$")
    start_date: date
    end_date: Optional[date] = None

    @validator("end_date")
    def validate_end_date(cls, v, values):
        if v and "start_date" in values and v < values["start_date"]:
            raise ValueError("終了日は開始日以降である必要があります")
        return v


class ProjectCreateRequest(ProjectBase):
    """Project creation request schema."""
    organization_id: int = Field(..., gt=0)


class ProjectUpdateRequest(BaseModel):
    """Project update request schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field(None, regex="^(planning|in_progress|completed|cancelled|on_hold)$")
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @validator("end_date")
    def validate_end_date(cls, v, values):
        if v and "start_date" in values and values["start_date"] and v < values["start_date"]:
            raise ValueError("終了日は開始日以降である必要があります")
        return v


class ProjectResponse(ProjectBase):
    """Project response schema."""
    id: int
    actual_end_date: Optional[date] = None
    organization_id: int
    created_at: datetime
    updated_at: datetime
    created_by: int
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True


class ProjectSearchParams(BaseModel):
    """Project search parameters."""
    search: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, regex="^(planning|in_progress|completed|cancelled|on_hold)$")
    organization_id: Optional[int] = Field(None, gt=0)
    start_date_from: Optional[date] = None
    start_date_to: Optional[date] = None
    page: Optional[int] = Field(1, ge=1)
    limit: Optional[int] = Field(20, ge=1, le=100)


class ProjectListResponse(BaseModel):
    """Project list response schema."""
    items: List[ProjectResponse]
    total: int
    page: int
    limit: int