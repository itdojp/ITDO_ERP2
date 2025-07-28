"""Base schemas for the ITDO ERP System."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base response schema with common fields."""

    id: int = Field(..., description="Resource ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: Optional[int] = Field(
        None, description="User who created this resource"
    )
    updated_by: Optional[int] = Field(
        None, description="User who last updated this resource"
    )
    is_deleted: bool = Field(False, description="Soft delete flag")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")
    deleted_by: Optional[int] = Field(
        None, description="User who deleted this resource"
    )

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Simple message response schema."""

    message: str = Field(..., description="Response message")
