"""Basic organization schemas for ERP v17.0 user management."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class OrganizationBasic(BaseModel):
    """Basic organization info for nested responses."""

    id: int
    code: str
    name: str

    class Config:
        from_attributes = True


class OrganizationCreate(BaseModel):
    """Organization creation schema for ERP v17.0."""

    code: str = Field(..., min_length=1, max_length=50, description="Organization code")
    name: str = Field(
        ..., min_length=1, max_length=200, description="Organization name"
    )
    name_en: Optional[str] = Field(None, max_length=200, description="Name in English")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    website: Optional[str] = Field(None, max_length=255, description="Website URL")
    business_type: Optional[str] = Field(
        None, max_length=100, description="Business type"
    )
    industry: Optional[str] = Field(None, max_length=100, description="Industry")
    parent_id: Optional[int] = Field(None, description="Parent organization ID")
    is_active: bool = Field(True, description="Active status")
    description: Optional[str] = Field(None, description="Description")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v) -> dict:
        if v and "@" not in v:
            raise ValueError("Invalid email format")
        return v

    @field_validator("code")
    @classmethod
    def validate_code(cls, v) -> dict:
        if not v or not v.strip():
            raise ValueError("Organization code cannot be empty")
        return v.strip().upper()


class OrganizationUpdate(BaseModel):
    """Organization update schema for ERP v17.0."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    name_en: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)
    business_type: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v) -> dict:
        if v and "@" not in v:
            raise ValueError("Invalid email format")
        return v


class OrganizationResponse(BaseModel):
    """Organization response schema for ERP v17.0."""

    id: int = Field(..., description="Organization ID")
    code: str = Field(..., description="Organization code")
    name: str = Field(..., description="Organization name")
    name_en: Optional[str] = Field(None, description="Name in English")
    display_name: str = Field(..., description="Display name")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    website: Optional[str] = Field(None, description="Website URL")
    full_address: Optional[str] = Field(None, description="Full formatted address")
    business_type: Optional[str] = Field(None, description="Business type")
    industry: Optional[str] = Field(None, description="Industry")
    employee_count: Optional[int] = Field(None, description="Employee count")
    parent_id: Optional[int] = Field(None, description="Parent organization ID")
    is_active: bool = Field(..., description="Active status")
    is_subsidiary: bool = Field(..., description="Is subsidiary organization")
    is_parent: bool = Field(..., description="Has subsidiary organizations")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True
