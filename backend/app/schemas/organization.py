"""Organization schemas."""

import json
<<<<<<< HEAD
from typing import Any, Dict, List, Optional
=======
from typing import Any
>>>>>>> origin/main

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import AuditInfo, SoftDeleteInfo


class OrganizationBase(BaseModel):
    """Base schema for organization."""

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


class OrganizationContactInfo(BaseModel):
    """Contact information schema."""

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


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""

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


class OrganizationBasic(BaseModel):
    """Basic organization information."""

    id: int
    code: str
    name: str
    name_en: str | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class OrganizationSummary(OrganizationBasic):
    """Organization summary with additional info."""

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
