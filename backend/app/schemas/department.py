"""Department schemas."""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.schemas.common import AuditInfo, SoftDeleteInfo
from app.schemas.organization import OrganizationBasic
from app.schemas.user import UserBasic


class UserSummary(BaseModel):
    """Summary information about a user."""
    id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    is_active: bool
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class DepartmentBase(BaseModel):
    """Base schema for department."""
    code: str = Field(..., min_length=1, max_length=50, description="Department code")
    name: str = Field(..., min_length=1, max_length=200, description="Department name")
    name_kana: Optional[str] = Field(None, max_length=200, description="Department name in Katakana")
    name_en: Optional[str] = Field(None, max_length=200, description="Department name in English")
    short_name: Optional[str] = Field(None, max_length=50, description="Short name or abbreviation")
    is_active: bool = Field(True, description="Whether the department is active")


class DepartmentContactInfo(BaseModel):
    """Department contact information."""
    phone: Optional[str] = Field(None, max_length=20, pattern=r'^[\d\-\+\(\)]+$')
    fax: Optional[str] = Field(None, max_length=20, pattern=r'^[\d\-\+\(\)]+$')
    email: Optional[str] = Field(None, max_length=255, pattern=r'^[\w\.\-]+@[\w\.\-]+\.\w+$')
    location: Optional[str] = Field(None, max_length=255, description="Physical location")


class DepartmentOperationalInfo(BaseModel):
    """Department operational information."""
    department_type: Optional[str] = Field(None, max_length=50, description="Type of department")
    budget: Optional[int] = Field(None, ge=0, description="Annual budget in JPY")
    headcount_limit: Optional[int] = Field(None, ge=0, description="Maximum allowed headcount")
    cost_center_code: Optional[str] = Field(None, max_length=50, description="Cost center code")
    display_order: int = Field(0, ge=0, description="Display order")


class DepartmentCreate(
    DepartmentBase,
    DepartmentContactInfo,
    DepartmentOperationalInfo
):
    """Schema for creating a department."""
    organization_id: int = Field(..., description="Organization ID")
    parent_id: Optional[int] = Field(None, description="Parent department ID")
    manager_id: Optional[int] = Field(None, description="Department manager user ID")
    description: Optional[str] = Field(None, max_length=1000)


class DepartmentUpdate(BaseModel):
    """Schema for updating a department."""
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    name_kana: Optional[str] = Field(None, max_length=200)
    name_en: Optional[str] = Field(None, max_length=200)
    short_name: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    
    # Contact info
    phone: Optional[str] = Field(None, max_length=20, pattern=r'^[\d\-\+\(\)]+$')
    fax: Optional[str] = Field(None, max_length=20, pattern=r'^[\d\-\+\(\)]+$')
    email: Optional[str] = Field(None, max_length=255, pattern=r'^[\w\.\-]+@[\w\.\-]+\.\w+$')
    location: Optional[str] = Field(None, max_length=255)
    
    # Operational info
    department_type: Optional[str] = Field(None, max_length=50)
    budget: Optional[int] = Field(None, ge=0)
    headcount_limit: Optional[int] = Field(None, ge=0)
    cost_center_code: Optional[str] = Field(None, max_length=50)
    display_order: Optional[int] = Field(None, ge=0)
    
    # Other fields
    parent_id: Optional[int] = None
    manager_id: Optional[int] = None
    description: Optional[str] = Field(None, max_length=1000)


class DepartmentBasic(BaseModel):
    """Basic department information."""
    id: int
    code: str
    name: str
    name_en: Optional[str] = None
    short_name: Optional[str] = None
    organization_id: int
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class DepartmentSummary(DepartmentBasic):
    """Department summary with additional info."""
    name_en: Optional[str] = None
    organization_id: int
    organization_name: Optional[str] = None
    parent_id: Optional[int] = None
    parent_name: Optional[str] = None
    manager_id: Optional[int] = None
    manager_name: Optional[str] = None
    current_headcount: int = 0
    headcount_limit: Optional[int] = None
    is_over_headcount: bool = False
    sub_department_count: int = 0
    user_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class DepartmentResponse(
    DepartmentBase,
    DepartmentContactInfo,
    DepartmentOperationalInfo,
    AuditInfo,
    SoftDeleteInfo
):
    """Full department response schema."""
    id: int
    organization_id: int
    organization: OrganizationBasic
    parent_id: Optional[int] = None
    parent: Optional[DepartmentBasic] = None
    manager_id: Optional[int] = None
    manager: Optional[UserBasic] = None
    description: Optional[str] = None
    full_code: str
    is_sub_department: bool = False
    is_parent_department: bool = False
    current_headcount: int = 0
    is_over_headcount: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class DepartmentTree(BaseModel):
    """Department tree structure."""
    id: int
    code: str
    name: str
    name_en: Optional[str] = None
    short_name: Optional[str] = None
    is_active: bool
    level: int = 0
    parent_id: Optional[int] = None
    manager_id: Optional[int] = None
    manager_name: Optional[str] = None
    current_headcount: int = 0
    headcount_limit: Optional[int] = None
    user_count: int = 0
    children: List["DepartmentTree"] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class DepartmentWithUsers(DepartmentResponse):
    """Department with user list."""
    users: List[UserBasic] = Field(default_factory=list)
    total_users: int = 0
    
    model_config = ConfigDict(from_attributes=True)


# Update forward references
DepartmentTree.model_rebuild()