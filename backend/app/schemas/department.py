"""Department schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DepartmentBase(BaseModel):
    """Base department schema."""

    code: str = Field(..., min_length=1, max_length=50, description="部門コード")
    name: str = Field(..., min_length=1, max_length=255, description="部門名")
    name_kana: Optional[str] = Field(None, max_length=255, description="部門名（カナ）")
    description: Optional[str] = Field(None, description="説明")
    sort_order: int = Field(0, ge=0, description="並び順")


class DepartmentCreate(DepartmentBase):
    """Department creation schema."""

    organization_id: int = Field(..., description="組織ID")
    parent_id: Optional[int] = Field(None, description="親部門ID")


class DepartmentUpdate(BaseModel):
    """Department update schema."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="部門名"
    )
    name_kana: Optional[str] = Field(None, max_length=255, description="部門名（カナ）")
    description: Optional[str] = Field(None, description="説明")
    sort_order: Optional[int] = Field(None, ge=0, description="並び順")


class DepartmentResponse(DepartmentBase):
    """Department response schema."""

    id: int
    organization_id: int
    parent_id: Optional[int] = None
    level: int
    path: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True


class DepartmentList(BaseModel):
    """Department list response schema."""

    items: list[DepartmentResponse]
    total: int
    page: int = 1
    limit: int = 10

    class Config:
        from_attributes = True
