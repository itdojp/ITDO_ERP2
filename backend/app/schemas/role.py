"""Role and UserRole schemas."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.schemas.common import AuditInfo, SoftDeleteInfo
from app.schemas.organization import OrganizationBasic
from app.schemas.department import DepartmentBasic
from app.schemas.user import UserBasic


class RoleBase(BaseModel):
    """Base schema for role."""
    code: str = Field(..., min_length=1, max_length=50, description="Unique role code")
    name: str = Field(..., min_length=1, max_length=200, description="Role display name")
    name_en: Optional[str] = Field(None, max_length=200, description="Role name in English")
    description: Optional[str] = Field(None, max_length=1000)
    is_active: bool = Field(True, description="Whether the role is active")


class RolePermissions(BaseModel):
    """Role permissions schema."""
    permissions: Dict[str, Any] = Field(default_factory=dict, description="Role permissions")
    
    @field_validator('permissions')
    @classmethod
    def validate_permissions(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate permissions structure."""
        # Add custom validation logic here
        return v


class RoleDisplay(BaseModel):
    """Role display settings."""
    display_order: int = Field(0, ge=0, description="Display order")
    icon: Optional[str] = Field(None, max_length=50, description="Icon name or class")
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description="Hex color code")


class RoleCreate(RoleBase, RolePermissions, RoleDisplay):
    """Schema for creating a role."""
    role_type: str = Field("custom", max_length=50, description="Type of role")
    parent_id: Optional[int] = Field(None, description="Parent role ID for inheritance")
    is_system: bool = Field(False, description="Whether this is a system role")


class RoleUpdate(BaseModel):
    """Schema for updating a role."""
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    name_en: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None
    permissions: Optional[Dict[str, Any]] = None
    parent_id: Optional[int] = None
    display_order: Optional[int] = Field(None, ge=0)
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')


class RoleBasic(BaseModel):
    """Basic role information."""
    id: int
    code: str
    name: str
    name_en: Optional[str] = None
    role_type: str
    is_active: bool
    is_system: bool
    
    model_config = ConfigDict(from_attributes=True)


class RoleResponse(
    RoleBase,
    RolePermissions,
    RoleDisplay,
    AuditInfo,
    SoftDeleteInfo
):
    """Full role response schema."""
    id: int
    role_type: str
    parent_id: Optional[int] = None
    parent: Optional[RoleBasic] = None
    is_system: bool
    is_inherited: bool = False
    users_count: int = 0
    all_permissions: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)


class RoleTree(BaseModel):
    """Role hierarchy tree."""
    id: int
    code: str
    name: str
    role_type: str
    is_active: bool
    level: int = 0
    parent_id: Optional[int] = None
    children: List["RoleTree"] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


# UserRole schemas
class UserRoleBase(BaseModel):
    """Base schema for user role assignment."""
    user_id: int = Field(..., description="User ID")
    role_id: int = Field(..., description="Role ID")
    organization_id: int = Field(..., description="Organization ID")
    department_id: Optional[int] = Field(None, description="Department ID")


class UserRoleCreate(UserRoleBase):
    """Schema for creating a user role assignment."""
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_primary: bool = Field(False, description="Whether this is the primary role")
    notes: Optional[str] = Field(None, max_length=1000)
    approval_status: Optional[str] = Field(None, max_length=50)


class UserRoleUpdate(BaseModel):
    """Schema for updating a user role assignment."""
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    is_primary: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=1000)
    approval_status: Optional[str] = Field(None, max_length=50)
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None


class UserRoleInfo(BaseModel):
    """User role information with details."""
    id: int
    user_id: int
    role: RoleBasic
    organization: OrganizationBasic
    department: Optional[DepartmentBasic] = None
    assigned_by: Optional[UserBasic] = None
    assigned_at: datetime
    valid_from: datetime
    expires_at: Optional[datetime] = None
    is_active: bool
    is_primary: bool
    is_expired: bool
    is_valid: bool
    days_until_expiry: Optional[int] = None
    notes: Optional[str] = None
    approval_status: Optional[str] = None
    approved_by: Optional[UserBasic] = None
    approved_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserRoleResponse(UserRoleInfo, AuditInfo):
    """Full user role response schema."""
    effective_permissions: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)


class BulkRoleAssignment(BaseModel):
    """Schema for bulk role assignment."""
    user_ids: List[int] = Field(..., min_length=1, description="List of user IDs")
    role_id: int = Field(..., description="Role ID to assign")
    organization_id: int = Field(..., description="Organization ID")
    department_id: Optional[int] = Field(None, description="Department ID")
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=1000)


# Update forward references
RoleTree.model_rebuild()