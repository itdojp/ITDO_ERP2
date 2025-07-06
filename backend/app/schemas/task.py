"""Task schemas."""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class TaskBase(BaseModel):
    """Task base schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = Field("not_started", regex="^(not_started|in_progress|completed|on_hold)$")
    priority: Optional[str] = Field("medium", regex="^(low|medium|high|urgent)$")
    estimated_start_date: Optional[date] = None
    estimated_end_date: Optional[date] = None

    @validator("estimated_end_date")
    def validate_estimated_end_date(cls, v, values):
        if (v and "estimated_start_date" in values and 
            values["estimated_start_date"] and v < values["estimated_start_date"]):
            raise ValueError("終了予定日は開始予定日以降である必要があります")
        return v


class TaskCreateRequest(TaskBase):
    """Task creation request schema."""
    project_id: int = Field(..., gt=0)
    assigned_to: Optional[int] = Field(None, gt=0)


class TaskUpdateRequest(BaseModel):
    """Task update request schema."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = Field(None, regex="^(not_started|in_progress|completed|on_hold)$")
    priority: Optional[str] = Field(None, regex="^(low|medium|high|urgent)$")
    assigned_to: Optional[int] = Field(None, gt=0)
    estimated_start_date: Optional[date] = None
    estimated_end_date: Optional[date] = None

    @validator("estimated_end_date")
    def validate_estimated_end_date(cls, v, values):
        if (v and "estimated_start_date" in values and 
            values["estimated_start_date"] and v < values["estimated_start_date"]):
            raise ValueError("終了予定日は開始予定日以降である必要があります")
        return v


class TaskResponse(TaskBase):
    """Task response schema."""
    id: int
    project_id: int
    assigned_to: Optional[int] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    created_by: int
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True


class TaskSearchParams(BaseModel):
    """Task search parameters."""
    search: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, regex="^(not_started|in_progress|completed|on_hold)$")
    priority: Optional[str] = Field(None, regex="^(low|medium|high|urgent)$")
    assigned_to: Optional[int] = Field(None, gt=0)
    page: Optional[int] = Field(1, ge=1)
    limit: Optional[int] = Field(20, ge=1, le=100)


class TaskListResponse(BaseModel):
    """Task list response schema."""
    items: List[TaskResponse]
    total: int
    page: int
    limit: int