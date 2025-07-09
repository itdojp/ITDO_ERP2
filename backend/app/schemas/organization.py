"""Organization schemas."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import AuditInfo, SoftDeleteInfo


class OrganizationBase(BaseModel):
    """Base schema for organization."""

    code: str = Field(
        ..., min_length=1, max_length=50, description="Unique organization code"
    )
    name: str = Field(
        ..., min_length=1, max_length=200, description="Organization name"
    )
    name_kana: Optional[str] = Field(
        None, max_length=200, description="Organization name in Katakana"
    )
    name_en: Optional[str] = Field(
        None, max_length=200, description="Organization name in English"
    )
    is_active: bool = Field(True, description="Whether the organization is active")


class OrganizationContactInfo(BaseModel):
    """Contact information schema."""

    phone: Optional[str] = Field(None, max_length=20, pattern=r"^[\d\-\+\(\)]+$")
    fax: Optional[str] = Field(None, max_length=20, pattern=r"^[\d\-\+\(\)]+$")
    email: Optional[str] = Field(
        None, max_length=255, pattern=r"^[\w\.\-]+@[\w\.\-]+\.\w+$"
    )
    website: Optional[str] = Field(None, max_length=255)


class OrganizationAddressInfo(BaseModel):
    """Address information schema."""

    postal_code: Optional[str] = Field(None, max_length=10, pattern=r"^\d{3}-?\d{4}$")
    prefecture: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=100)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)


class OrganizationBusinessInfo(BaseModel):
    """Business information schema."""

    business_type: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    capital: Optional[int] = Field(None, ge=0, description="Capital amount in JPY")
    employee_count: Optional[int] = Field(None, ge=0)
    fiscal_year_end: Optional[str] = Field(
        None, pattern=r"^\d{2}-\d{2}$", description="MM-DD format"
    )


class OrganizationCreate(
    OrganizationBase,
    OrganizationContactInfo,
    OrganizationAddressInfo,
    OrganizationBusinessInfo,
):
    """Schema for creating an organization."""

    parent_id: Optional[int] = Field(None, description="Parent organization ID")
    description: Optional[str] = Field(None, max_length=1000)
    logo_url: Optional[str] = Field(None, max_length=255)
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""

    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    name_kana: Optional[str] = Field(None, max_length=200)
    name_en: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None

    # Contact info
    phone: Optional[str] = Field(None, max_length=20, pattern=r"^[\d\-\+\(\)]+$")
    fax: Optional[str] = Field(None, max_length=20, pattern=r"^[\d\-\+\(\)]+$")
    email: Optional[str] = Field(
        None, max_length=255, pattern=r"^[\w\.\-]+@[\w\.\-]+\.\w+$"
    )
    website: Optional[str] = Field(None, max_length=255)

    # Address info
    postal_code: Optional[str] = Field(None, max_length=10, pattern=r"^\d{3}-?\d{4}$")
    prefecture: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=100)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)

    # Business info
    business_type: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    capital: Optional[int] = Field(None, ge=0)
    employee_count: Optional[int] = Field(None, ge=0)
    fiscal_year_end: Optional[str] = Field(None, pattern=r"^\d{2}-\d{2}$")

    # Other fields
    parent_id: Optional[int] = None
    description: Optional[str] = Field(None, max_length=1000)
    logo_url: Optional[str] = Field(None, max_length=255)
    settings: Optional[Dict[str, Any]] = None


class OrganizationBasic(BaseModel):
    """Basic organization information."""

    id: int
    code: str
    name: str
    name_en: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class OrganizationSummary(OrganizationBasic):
    """Organization summary with additional info."""

    parent_id: Optional[int] = None
    parent_name: Optional[str] = None
    department_count: int = 0
    user_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class OrganizationResponse(
    OrganizationBase,
    OrganizationContactInfo,
    OrganizationAddressInfo,
    OrganizationBusinessInfo,
    AuditInfo,
    SoftDeleteInfo,
):
    """Full organization response schema."""

    id: int
    parent_id: Optional[int] = None
    parent: Optional[OrganizationBasic] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)
    full_address: Optional[str] = None
    is_subsidiary: bool = False
    is_parent: bool = False
    subsidiary_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class OrganizationTree(BaseModel):
    """Organization tree structure."""

    id: int
    code: str
    name: str
    is_active: bool
    level: int = 0
    parent_id: Optional[int] = None
    children: List["OrganizationTree"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# Update forward references
OrganizationTree.model_rebuild()


class OrganizationSettings(BaseModel):
    """Organization settings schema."""

    # 基本設定
    fiscal_year_start: str = Field(
        default="04-01",
        pattern="^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$",
        description="Fiscal year start date (MM-DD format)"
    )
    default_currency: str = Field(
        default="JPY",
        description="Default currency code"
    )
    timezone: str = Field(
        default="Asia/Tokyo",
        description="Default timezone"
    )
    date_format: str = Field(
        default="YYYY-MM-DD",
        description="Default date format"
    )

    # 部門設定
    max_department_depth: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum department hierarchy depth"
    )
    require_department_budget: bool = Field(
        default=True,
        description="Whether departments must have budget assigned"
    )
    max_department_budget: Optional[float] = Field(
        default=None,
        description="Maximum budget per department"
    )

    # プロジェクト設定
    default_project_duration_days: int = Field(
        default=90,
        ge=1,
        description="Default project duration in days"
    )
    require_project_approval: bool = Field(
        default=True,
        description="Whether new projects require approval"
    )
    auto_archive_completed_projects: bool = Field(
        default=False,
        description="Auto-archive completed projects after specified days"
    )
    archive_after_days: int = Field(
        default=365,
        ge=30,
        description="Days after completion to auto-archive"
    )

    # 権限設定
    allow_cross_department_projects: bool = Field(
        default=True,
        description="Allow projects across departments"
    )
    inherit_parent_permissions: bool = Field(
        default=True,
        description="Inherit permissions from parent organization"
    )
    default_user_role: str = Field(
        default="member",
        description="Default role for new users"
    )

    # 通知設定
    enable_email_notifications: bool = Field(
        default=True,
        description="Enable email notifications"
    )
    notification_digest_frequency: str = Field(
        default="daily",
        pattern="^(instant|daily|weekly|monthly)$",
        description="Notification digest frequency"
    )

    # セキュリティ設定
    password_min_length: int = Field(
        default=8,
        ge=6,
        le=32,
        description="Minimum password length"
    )
    require_mfa: bool = Field(
        default=False,
        description="Require multi-factor authentication"
    )
    session_timeout_minutes: int = Field(
        default=480,
        ge=5,
        le=1440,
        description="Session timeout in minutes"
    )

    # カスタムフィールド
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom organization-specific fields"
    )


class OrganizationSettingsUpdate(BaseModel):
    """Organization settings update schema."""

    fiscal_year_start: Optional[str] = Field(
        None,
        pattern="^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$"
    )
    default_currency: Optional[str] = None
    timezone: Optional[str] = None
    date_format: Optional[str] = None

    max_department_depth: Optional[int] = Field(None, ge=1, le=10)
    require_department_budget: Optional[bool] = None
    max_department_budget: Optional[float] = None

    default_project_duration_days: Optional[int] = Field(None, ge=1)
    require_project_approval: Optional[bool] = None
    auto_archive_completed_projects: Optional[bool] = None
    archive_after_days: Optional[int] = Field(None, ge=30)

    allow_cross_department_projects: Optional[bool] = None
    inherit_parent_permissions: Optional[bool] = None
    default_user_role: Optional[str] = None

    enable_email_notifications: Optional[bool] = None
    notification_digest_frequency: Optional[str] = Field(
        None,
        pattern="^(instant|daily|weekly|monthly)$"
    )

    password_min_length: Optional[int] = Field(None, ge=6, le=32)
    require_mfa: Optional[bool] = None
    session_timeout_minutes: Optional[int] = Field(None, ge=5, le=1440)

    custom_fields: Optional[Dict[str, Any]] = None


class PermissionTemplate(BaseModel):
    """Permission template for organization roles."""

    id: Optional[int] = None
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    role_type: str = Field(..., description="Role type (admin, manager, member, viewer)")
    permissions: List[str] = Field(
        default_factory=list,
        description="List of permission codes"
    )
    is_default: bool = Field(
        default=False,
        description="Whether this is the default template for the role type"
    )
    is_active: bool = Field(default=True, description="Whether template is active")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class OrganizationPolicy(BaseModel):
    """Organization policy schema."""

    id: Optional[int] = None
    policy_type: str = Field(
        ...,
        description="Policy type (security, compliance, operational)"
    )
    name: str = Field(..., description="Policy name")
    description: Optional[str] = Field(None, description="Policy description")
    rules: Dict[str, Any] = Field(
        default_factory=dict,
        description="Policy rules and constraints"
    )
    enforcement_level: str = Field(
        default="strict",
        pattern="^(strict|moderate|lenient)$",
        description="Policy enforcement level"
    )
    effective_from: Optional[date] = Field(
        None,
        description="Date when policy becomes effective"
    )
    expires_at: Optional[date] = Field(
        None,
        description="Policy expiration date"
    )
    is_active: bool = Field(default=True, description="Whether policy is active")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class OrganizationSettingsResponse(BaseModel):
    """Response schema for organization settings."""

    organization_id: int
    settings: OrganizationSettings
    permission_templates: List[PermissionTemplate] = Field(
        default_factory=list,
        description="Available permission templates"
    )
    policies: List[OrganizationPolicy] = Field(
        default_factory=list,
        description="Active organization policies"
    )
    inherited_settings: Optional[Dict[str, Any]] = Field(
        None,
        description="Settings inherited from parent organization"
    )
    effective_settings: Dict[str, Any] = Field(
        ...,
        description="Effective settings after inheritance"
    )
