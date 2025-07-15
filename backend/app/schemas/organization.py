"""Organization schemas."""

<<<<<<< HEAD
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator
=======
import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import AuditInfo, SoftDeleteInfo
>>>>>>> origin/main


class OrganizationBase(BaseModel):
    """Base organization schema."""

<<<<<<< HEAD
    code: str = Field(..., min_length=1, max_length=50, description="組織コード")
    name: str = Field(..., min_length=1, max_length=255, description="組織名")
    name_kana: Optional[str] = Field(None, max_length=255, description="組織名（カナ）")
    postal_code: Optional[str] = Field(None, max_length=10, description="郵便番号")
    address: Optional[str] = Field(None, description="住所")
    phone: Optional[str] = Field(None, max_length=20, description="電話番号")
    email: Optional[str] = Field(None, max_length=255, description="メールアドレス")
    website: Optional[str] = Field(None, max_length=255, description="ウェブサイト")
    fiscal_year_start: int = Field(4, ge=1, le=12, description="会計年度開始月")

    @validator("email")
    def validate_email(cls, v):
        if v and "@" not in v:
            raise ValueError("有効なメールアドレスを入力してください")
        return v

    @validator("fiscal_year_start")
    def validate_fiscal_year_start(cls, v):
        if v < 1 or v > 12:
            raise ValueError("会計年度開始月は1-12の範囲で入力してください")
        return v
=======
    code: str = Field(
        ..., min_length=1, max_length=50, description="Unique organization code"
    )
    name: str = Field(
        ..., min_length=1, max_length=200, description="Organization name"
    )
    name_kana: str | None = Field(
        None, max_length=200, description="Organization name in Katakana"
    )
    name_en: str | None = Field(
        None, max_length=200, description="Organization name in English"
    )
    is_active: bool = Field(True, description="Whether the organization is active")
>>>>>>> origin/main


class OrganizationCreate(OrganizationBase):
    """Organization creation schema."""

<<<<<<< HEAD
    pass
=======
    phone: str | None = Field(None, max_length=20, pattern=r"^[\d\-\+\(\)]+$")
    fax: str | None = Field(None, max_length=20, pattern=r"^[\d\-\+\(\)]+$")
    email: str | None = Field(
        None, max_length=255, pattern=r"^[\w\.\-]+@[\w\.\-]+\.\w+$"
    )
    website: str | None = Field(None, max_length=255)


class OrganizationAddressInfo(BaseModel):
    """Address information schema."""

    postal_code: str | None = Field(None, max_length=10, pattern=r"^\d{3}-?\d{4}$")
    prefecture: str | None = Field(None, max_length=50)
    city: str | None = Field(None, max_length=100)
    address_line1: str | None = Field(None, max_length=255)
    address_line2: str | None = Field(None, max_length=255)


class OrganizationBusinessInfo(BaseModel):
    """Business information schema."""

    business_type: str | None = Field(None, max_length=100)
    industry: str | None = Field(None, max_length=100)
    capital: int | None = Field(None, ge=0, description="Capital amount in JPY")
    employee_count: int | None = Field(None, ge=0)
    fiscal_year_end: str | None = Field(
        None, pattern=r"^\d{2}-\d{2}$", description="MM-DD format"
    )


class OrganizationCreate(
    OrganizationBase,
    OrganizationContactInfo,
    OrganizationAddressInfo,
    OrganizationBusinessInfo,
):
    """Schema for creating an organization."""

    parent_id: int | None = Field(None, description="Parent organization ID")
    description: str | None = Field(None, max_length=1000)
    logo_url: str | None = Field(None, max_length=255)
    settings: dict[str, Any] | None = Field(default_factory=dict)
>>>>>>> origin/main


class OrganizationUpdate(BaseModel):
    """Organization update schema."""

<<<<<<< HEAD
    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="組織名"
    )
    name_kana: Optional[str] = Field(None, max_length=255, description="組織名（カナ）")
    postal_code: Optional[str] = Field(None, max_length=10, description="郵便番号")
    address: Optional[str] = Field(None, description="住所")
    phone: Optional[str] = Field(None, max_length=20, description="電話番号")
    email: Optional[str] = Field(None, max_length=255, description="メールアドレス")
    website: Optional[str] = Field(None, max_length=255, description="ウェブサイト")
    fiscal_year_start: Optional[int] = Field(
        None, ge=1, le=12, description="会計年度開始月"
    )

    @validator("email")
    def validate_email(cls, v):
        if v and "@" not in v:
            raise ValueError("有効なメールアドレスを入力してください")
        return v
=======
    code: str | None = Field(None, min_length=1, max_length=50)
    name: str | None = Field(None, min_length=1, max_length=200)
    name_kana: str | None = Field(None, max_length=200)
    name_en: str | None = Field(None, max_length=200)
    is_active: bool | None = None

    # Contact info
    phone: str | None = Field(None, max_length=20, pattern=r"^[\d\-\+\(\)]+$")
    fax: str | None = Field(None, max_length=20, pattern=r"^[\d\-\+\(\)]+$")
    email: str | None = Field(
        None, max_length=255, pattern=r"^[\w\.\-]+@[\w\.\-]+\.\w+$"
    )
    website: str | None = Field(None, max_length=255)

    # Address info
    postal_code: str | None = Field(None, max_length=10, pattern=r"^\d{3}-?\d{4}$")
    prefecture: str | None = Field(None, max_length=50)
    city: str | None = Field(None, max_length=100)
    address_line1: str | None = Field(None, max_length=255)
    address_line2: str | None = Field(None, max_length=255)

    # Business info
    business_type: str | None = Field(None, max_length=100)
    industry: str | None = Field(None, max_length=100)
    capital: int | None = Field(None, ge=0)
    employee_count: int | None = Field(None, ge=0)
    fiscal_year_end: str | None = Field(None, pattern=r"^\d{2}-\d{2}$")

    # Other fields
    parent_id: int | None = None
    description: str | None = Field(None, max_length=1000)
    logo_url: str | None = Field(None, max_length=255)
    settings: dict[str, Any] | None = None
>>>>>>> origin/main


class OrganizationResponse(OrganizationBase):
    """Organization response schema."""

    id: int
<<<<<<< HEAD
=======
    code: str
    name: str
    name_en: str | None = None
>>>>>>> origin/main
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True


class OrganizationList(BaseModel):
    """Organization list response schema."""

<<<<<<< HEAD
    items: list[OrganizationResponse]
    total: int
    page: int = 1
    limit: int = 10

    class Config:
        from_attributes = True
=======
    parent_id: int | None = None
    parent_name: str | None = None
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
    parent_id: int | None = None
    parent: OrganizationBasic | None = None
    description: str | None = None
    logo_url: str | None = None
    settings: dict[str, Any] = Field(default_factory=dict)
    full_address: str | None = None
    is_subsidiary: bool = False
    is_parent: bool = False
    subsidiary_count: int = 0

    model_config = ConfigDict(from_attributes=True)

    @field_validator("settings", mode="before")
    @classmethod
    def parse_settings_json(cls, v: Any) -> dict[str, Any]:
        """Parse settings JSON string to dict."""
        if isinstance(v, str):
            try:
                result = json.loads(v)
                if isinstance(result, dict):
                    return result
                return {}
            except (json.JSONDecodeError, TypeError):
                return {}
        return v or {}


class OrganizationTree(BaseModel):
    """Organization tree structure."""

    id: int
    code: str
    name: str
    is_active: bool
    level: int = 0
    parent_id: int | None = None
    children: list["OrganizationTree"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# Update forward references
OrganizationTree.model_rebuild()
>>>>>>> origin/main
