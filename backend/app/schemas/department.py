"""Department schemas."""

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import AuditInfo, SoftDeleteInfo
from app.schemas.organization import OrganizationBasic
from app.schemas.user import UserBasic


class UserSummary(BaseModel):
    """Summary information about a user."""

    id: int
    email: str
    full_name: str
    phone: str | None = None
    is_active: bool
    department_id: int | None = None
    department_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DepartmentBase(BaseModel):
    """Base schema for department."""

    code: str = Field(..., min_length=1, max_length=50, description="Department code")
    name: str = Field(..., min_length=1, max_length=200, description="Department name")
    name_kana: str | None = Field(
        None, max_length=200, description="Department name in Katakana"
    )
    name_en: str | None = Field(
        None, max_length=200, description="Department name in English"
    )
    short_name: str | None = Field(
        None, max_length=50, description="Short name or abbreviation"
    )
    is_active: bool = Field(True, description="Whether the department is active")


class DepartmentContactInfo(BaseModel):
    """Department contact information."""

    phone: str | None = Field(None, max_length=20, pattern=r"^[\d\-\+\(\)]+$")
    fax: str | None = Field(None, max_length=20, pattern=r"^[\d\-\+\(\)]+$")
    email: str | None = Field(
        None, max_length=255, pattern=r"^[\w\.\-]+@[\w\.\-]+\.\w+$"
    )
    location: str | None = Field(None, max_length=255, description="Physical location")


class DepartmentOperationalInfo(BaseModel):
    """Department operational information."""

    department_type: str | None = Field(
        None, max_length=50, description="Type of department"
    )
    budget: int | None = Field(None, ge=0, description="Annual budget in JPY")
    headcount_limit: int | None = Field(
        None, ge=0, description="Maximum allowed headcount"
    )
    cost_center_code: str | None = Field(
        None, max_length=50, description="Cost center code"
    )
    display_order: int = Field(0, ge=0, description="Display order")


class DepartmentCreate(
    DepartmentBase, DepartmentContactInfo, DepartmentOperationalInfo
):
    """Schema for creating a department."""

    organization_id: int = Field(..., description="Organization ID")
    parent_id: int | None = Field(None, description="Parent department ID")
    manager_id: int | None = Field(None, description="Department manager user ID")
    description: str | None = Field(None, max_length=1000)


class DepartmentUpdate(BaseModel):
    """Schema for updating a department."""

    code: str | None = Field(None, min_length=1, max_length=50)
    name: str | None = Field(None, min_length=1, max_length=200)
    name_kana: str | None = Field(None, max_length=200)
    name_en: str | None = Field(None, max_length=200)
    short_name: str | None = Field(None, max_length=50)
    is_active: bool | None = None

    # Contact info
    phone: str | None = Field(None, max_length=20, pattern=r"^[\d\-\+\(\)]+$")
    fax: str | None = Field(None, max_length=20, pattern=r"^[\d\-\+\(\)]+$")
    email: str | None = Field(
        None, max_length=255, pattern=r"^[\w\.\-]+@[\w\.\-]+\.\w+$"
    )
    location: str | None = Field(None, max_length=255)

    # Operational info
    department_type: str | None = Field(None, max_length=50)
    budget: int | None = Field(None, ge=0)
    headcount_limit: int | None = Field(None, ge=0)
    cost_center_code: str | None = Field(None, max_length=50)
    display_order: int | None = Field(None, ge=0)

    # Other fields
    parent_id: int | None = None
    manager_id: int | None = None
    description: str | None = Field(None, max_length=1000)


class DepartmentBasic(BaseModel):
    """Basic department information."""

    id: int
    code: str
    name: str
    name_en: str | None = None
    short_name: str | None = None
    organization_id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class DepartmentSummary(DepartmentBasic):
    """Department summary with additional info."""

    name_en: str | None = None
    organization_id: int
    organization_name: str | None = None
    parent_id: int | None = None
    parent_name: str | None = None
    manager_id: int | None = None
    manager_name: str | None = None
    department_type: str | None = None
    current_headcount: int = 0
    headcount_limit: int | None = None
    is_over_headcount: bool = False
    sub_department_count: int = 0
    user_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class DepartmentResponse(
    DepartmentBase,
    DepartmentContactInfo,
    DepartmentOperationalInfo,
    AuditInfo,
    SoftDeleteInfo,
):
    """Full department response schema."""

    id: int
    organization_id: int
    organization: OrganizationBasic
    parent_id: int | None = None
    parent: DepartmentBasic | None = None
    manager_id: int | None = None
    manager: UserBasic | None = None
    description: str | None = None
    full_code: str
    is_sub_department: bool = False
    is_parent_department: bool = False
    current_headcount: int = 0
    is_over_headcount: bool = False
    path: str | None = None
    depth: int = 0

    model_config = ConfigDict(from_attributes=True)


class DepartmentTree(BaseModel):
    """Department tree structure."""

    id: int
    code: str
    name: str
    name_en: str | None = None
    short_name: str | None = None
    is_active: bool
    level: int = 0
    parent_id: int | None = None
    manager_id: int | None = None
    manager_name: str | None = None
    current_headcount: int = 0
    headcount_limit: int | None = None
    user_count: int = 0
<<<<<<< HEAD
=======
    path: str | None = None
    depth: int = 0
    display_order: int = 0
>>>>>>> main
    children: list["DepartmentTree"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DepartmentWithUsers(DepartmentResponse):
    """Department with user list."""

    users: list[UserBasic] = Field(default_factory=list)
    total_users: int = 0

    model_config = ConfigDict(from_attributes=True)


# Update forward references
DepartmentTree.model_rebuild()
