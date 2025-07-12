"""Role and UserRole schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import AuditInfo, SoftDeleteInfo
from app.schemas.department import DepartmentBasic
from app.schemas.organization import OrganizationBasic
from app.schemas.user import UserBasic


class PermissionBasic(BaseModel):
    """Basic permission information."""

    id: int
    code: str
    name: str
    category: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RoleBase(BaseModel):
    """Base schema for role."""

    code: str = Field(..., min_length=1, max_length=50, description="Unique role code")
    name: str = Field(
        ..., min_length=1, max_length=200, description="Role display name"
    )
    name_en: str | None = Field(
        None, max_length=200, description="Role name in English"
    )
    description: str | None = Field(None, max_length=1000)
    is_active: bool = Field(True, description="Whether the role is active")


class RolePermissions(BaseModel):
    """Role permissions schema."""

    permissions: dict[str, Any] = Field(
        default_factory=dict, description="Role permissions"
    )


class RoleDisplay(BaseModel):
    """Role display settings."""

    display_order: int = Field(0, ge=0, description="Display order")
    icon: str | None = Field(None, max_length=50, description="Icon name or class")
    color: str | None = Field(
        None, pattern=r"^#[0-9A-Fa-f]{6}$", description="Hex color code"
    )


class RoleCreate(RoleBase, RolePermissions, RoleDisplay):
    """Schema for creating a role."""

    organization_id: int = Field(..., description="Organization ID")
    role_type: str = Field("custom", max_length=50, description="Type of role")
    parent_id: int | None = Field(None, description="Parent role ID for inheritance")
    is_system: bool = Field(False, description="Whether this is a system role")


class RoleUpdate(BaseModel):
    """Schema for updating a role."""

    code: str | None = Field(None, min_length=1, max_length=50)
    name: str | None = Field(None, min_length=1, max_length=200)
    name_en: str | None = Field(None, max_length=200)
    description: str | None = Field(None, max_length=1000)
    is_active: bool | None = None
    permissions: dict[str, Any] | None = None
    parent_id: int | None = None
    display_order: int | None = Field(None, ge=0)
    icon: str | None = Field(None, max_length=50)
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class RoleBasic(BaseModel):
    """Basic role information."""

    id: int
    code: str
    name: str
    name_en: str | None = None
    role_type: str
    is_active: bool
    is_system: bool

    model_config = ConfigDict(from_attributes=True)


class RoleResponse(RoleBase, RolePermissions, RoleDisplay, AuditInfo, SoftDeleteInfo):
    """Full role response schema."""

    id: int
    role_type: str
    parent_id: int | None = None
    parent: RoleBasic | None = None
    is_system: bool
    is_inherited: bool = False
    users_count: int = 0
    all_permissions: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class RoleTree(BaseModel):
    """Role hierarchy tree."""

    id: int
    code: str
    name: str
    description: str | None = None
    role_type: str
    is_active: bool
    level: int = 0
    parent_id: int | None = None
    user_count: int = 0
    permission_count: int = 0
    children: list["RoleTree"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# UserRole schemas
class UserRoleBase(BaseModel):
    """Base schema for user role assignment."""

    user_id: int = Field(..., description="User ID")
    role_id: int = Field(..., description="Role ID")
    organization_id: int = Field(..., description="Organization ID")
    department_id: int | None = Field(None, description="Department ID")


class UserRoleCreate(UserRoleBase):
    """Schema for creating a user role assignment."""

    valid_from: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    is_primary: bool = Field(False, description="Whether this is the primary role")
    notes: str | None = Field(None, max_length=1000)
    approval_status: str | None = Field(None, max_length=50)


class UserRoleUpdate(BaseModel):
    """Schema for updating a user role assignment."""

    expires_at: datetime | None = None
    is_active: bool | None = None
    is_primary: bool | None = None
    notes: str | None = Field(None, max_length=1000)
    approval_status: str | None = Field(None, max_length=50)
    approved_by: int | None = None
    approved_at: datetime | None = None


class UserRoleInfo(BaseModel):
    """User role information with details."""

    id: int
    user_id: int
    role: RoleBasic
    organization: OrganizationBasic
    department: DepartmentBasic | None = None
    assigned_by: UserBasic | None = None
    assigned_at: datetime
    valid_from: datetime
    expires_at: datetime | None = None
    is_active: bool
    is_primary: bool
    is_expired: bool
    is_valid: bool
    days_until_expiry: int | None = None
    notes: str | None = None
    approval_status: str | None = None
    approved_by: UserBasic | None = None
    approved_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserRoleResponse(UserRoleInfo, AuditInfo):
    """Full user role response schema."""

    effective_permissions: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class BulkRoleAssignment(BaseModel):
    """Schema for bulk role assignment."""

    user_ids: list[int] = Field(..., min_length=1, description="List of user IDs")
    role_id: int = Field(..., description="Role ID to assign")
    organization_id: int = Field(..., description="Organization ID")
    department_id: int | None = Field(None, description="Department ID")
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    notes: str | None = Field(None, max_length=1000)


# Additional schemas for API compatibility
class RoleSummary(RoleBasic):
    """Role summary with additional info."""

    description: str | None = None
    user_count: int = 0
    permission_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class RoleWithPermissions(RoleResponse):
    """Role with permissions information."""

    permission_list: list[PermissionBasic] = Field(
        default_factory=list, description="List of permissions"
    )

    model_config = ConfigDict(from_attributes=True)


class UserRoleAssignment(BaseModel):
    """Schema for user role assignment."""

    user_id: int = Field(..., description="User ID")
    role_id: int = Field(..., description="Role ID")
    organization_id: int = Field(..., description="Organization ID")
    department_id: int | None = Field(None, description="Department ID")
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None


# Update forward references
RoleTree.model_rebuild()
