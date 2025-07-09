"""Permission schemas for API operations."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PermissionBase(BaseModel):
    """Base schema for Permission."""

    code: str = Field(..., description="Unique permission code")
    name: str = Field(..., description="Permission display name")
    category: str = Field(..., description="Permission category")
    description: Optional[str] = Field(None, description="Permission description")


class PermissionCreate(PermissionBase):
    """Schema for creating a Permission."""

    is_active: bool = Field(True, description="Whether permission is active")


class PermissionUpdate(BaseModel):
    """Schema for updating a Permission."""

    name: Optional[str] = Field(None, description="Permission display name")
    description: Optional[str] = Field(None, description="Permission description")
    is_active: Optional[bool] = Field(None, description="Whether permission is active")

    model_config = ConfigDict(extra="forbid")


class PermissionResponse(PermissionBase):
    """Schema for Permission response."""

    id: int
    is_active: bool
    is_system: bool

    model_config = ConfigDict(from_attributes=True)


class PermissionBasic(BaseModel):
    """Basic permission info for nested responses."""

    id: int
    code: str
    name: str
    category: str

    model_config = ConfigDict(from_attributes=True)


class PermissionWithEffect(PermissionBasic):
    """Permission with effect information."""

    effect: str = Field(..., description="Permission effect: allow or deny")
    organization_id: Optional[int] = Field(None, description="Organization scope")
    department_id: Optional[int] = Field(None, description="Department scope")
    granted_at: Optional[str] = Field(None, description="When permission was granted")
    expires_at: Optional[str] = Field(None, description="When permission expires")
    is_override: bool = Field(False, description="Whether this overrides inherited permissions")
    priority: int = Field(0, description="Priority for conflict resolution")

    model_config = ConfigDict(from_attributes=True)
