"""Extended user schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.user import UserBase, UserResponse


class UserCreateExtended(UserBase):
    """Extended user creation schema with organization/role assignment."""
    
    password: str = Field(..., min_length=8, description="User password")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    organization_id: int = Field(..., description="Organization ID")
    department_id: Optional[int] = Field(None, description="Department ID")
    role_ids: List[int] = Field(..., description="List of role IDs to assign")
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Check for at least 3 of: uppercase, lowercase, digit, special char
        import re
        checks = [
            bool(re.search(r"[A-Z]", v)),  # Has uppercase
            bool(re.search(r"[a-z]", v)),  # Has lowercase
            bool(re.search(r"\d", v)),     # Has digit
            bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", v))  # Has special char
        ]
        
        if sum(checks) < 3:
            raise ValueError(
                "Password must contain at least 3 of: uppercase letter, "
                "lowercase letter, digit, special character"
            )
        
        return v


class UserUpdate(BaseModel):
    """User update schema."""
    
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    profile_image_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class UserResponseExtended(UserResponse):
    """Extended user response with additional fields."""
    
    phone: Optional[str] = None
    profile_image_url: Optional[str] = None
    last_login_at: Optional[datetime] = None
    organizations: List["OrganizationBasic"] = []
    departments: List["DepartmentBasic"] = []
    roles: List["UserRoleInfo"] = []


class PasswordChange(BaseModel):
    """Password change request."""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        import re
        checks = [
            bool(re.search(r"[A-Z]", v)),
            bool(re.search(r"[a-z]", v)),
            bool(re.search(r"\d", v)),
            bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", v))
        ]
        
        if sum(checks) < 3:
            raise ValueError(
                "Password must contain at least 3 of: uppercase letter, "
                "lowercase letter, digit, special character"
            )
        
        return v


class UserSearchParams(BaseModel):
    """User search parameters."""
    
    search: Optional[str] = Field(None, description="Search term")
    organization_id: Optional[int] = Field(None, description="Filter by organization")
    department_id: Optional[int] = Field(None, description="Filter by department")
    role_id: Optional[int] = Field(None, description="Filter by role")
    is_active: Optional[bool] = Field(None, description="Filter by active status")


class UserListResponse(BaseModel):
    """Paginated user list response."""
    
    items: List[UserResponseExtended]
    total: int
    page: int
    limit: int


class RoleAssignment(BaseModel):
    """Role assignment request."""
    
    role_id: int = Field(..., description="Role ID")
    organization_id: int = Field(..., description="Organization ID")
    department_id: Optional[int] = Field(None, description="Department ID")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")


class UserRoleInfo(BaseModel):
    """User role information."""
    
    role: "RoleBasic"
    organization: "OrganizationBasic"
    department: Optional["DepartmentBasic"] = None
    assigned_at: datetime
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PermissionListResponse(BaseModel):
    """User permissions response."""
    
    permissions: List[str] = Field(..., description="List of permissions")
    organization_id: int = Field(..., description="Organization context")


class UserImport(BaseModel):
    """User import data."""
    
    email: EmailStr
    full_name: str
    phone: Optional[str] = None


class BulkImportRequest(BaseModel):
    """Bulk user import request."""
    
    organization_id: int
    role_id: int
    users: List[UserImport]


class BulkImportResponse(BaseModel):
    """Bulk import response."""
    
    success_count: int
    error_count: int
    created_users: List[UserResponseExtended]
    errors: List[dict] = []


class UserExportFormat(BaseModel):
    """User export format."""
    
    format: str = Field(..., pattern="^(csv|xlsx|json)$")
    organization_id: int
    include_inactive: bool = False


class UserActivity(BaseModel):
    """User activity log entry."""
    
    action: str
    details: dict
    ip_address: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserActivityListResponse(BaseModel):
    """User activity list response."""
    
    items: List[UserActivity]
    total: int


# Import these at the end to avoid circular imports
from app.schemas.organization_basic import OrganizationBasic
from app.schemas.department_basic import DepartmentBasic
from app.schemas.role_basic import RoleBasic

# Update forward refs
UserResponseExtended.model_rebuild()
UserRoleInfo.model_rebuild()