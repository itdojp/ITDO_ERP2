"""Organization schemas."""
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.schemas.common import AuditInfo, SoftDeleteInfo


class OrganizationBase(BaseModel):
    """Base schema for organization."""
    code: str = Field(..., min_length=1, max_length=50, description="Unique organization code")
    name: str = Field(..., min_length=1, max_length=200, description="Organization name")
    name_kana: Optional[str] = Field(None, max_length=200, description="Organization name in Katakana")
    name_en: Optional[str] = Field(None, max_length=200, description="Organization name in English")
    is_active: bool = Field(True, description="Whether the organization is active")


class OrganizationContactInfo(BaseModel):
    """Contact information schema."""
    phone: Optional[str] = Field(None, max_length=20, pattern=r'^[\d\-\+\(\)]+$')
    fax: Optional[str] = Field(None, max_length=20, pattern=r'^[\d\-\+\(\)]+$')
    email: Optional[str] = Field(None, max_length=255, pattern=r'^[\w\.\-]+@[\w\.\-]+\.\w+$')
    website: Optional[str] = Field(None, max_length=255)


class OrganizationAddressInfo(BaseModel):
    """Address information schema."""
    postal_code: Optional[str] = Field(None, max_length=10, pattern=r'^\d{3}-?\d{4}$')
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
    fiscal_year_end: Optional[str] = Field(None, pattern=r'^\d{2}-\d{2}$', description="MM-DD format")


class OrganizationCreate(
    OrganizationBase,
    OrganizationContactInfo,
    OrganizationAddressInfo,
    OrganizationBusinessInfo
):
    """Schema for creating an organization."""
    parent_id: Optional[int] = Field(None, description="Parent organization ID")
    description: Optional[str] = Field(None, max_length=1000)
    logo_url: Optional[str] = Field(None, max_length=255)
    settings: Optional[dict[str, Any]] = Field(default_factory=dict)


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    name_kana: Optional[str] = Field(None, max_length=200)
    name_en: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None
    
    # Contact info
    phone: Optional[str] = Field(None, max_length=20, pattern=r'^[\d\-\+\(\)]+$')
    fax: Optional[str] = Field(None, max_length=20, pattern=r'^[\d\-\+\(\)]+$')
    email: Optional[str] = Field(None, max_length=255, pattern=r'^[\w\.\-]+@[\w\.\-]+\.\w+$')
    website: Optional[str] = Field(None, max_length=255)
    
    # Address info
    postal_code: Optional[str] = Field(None, max_length=10, pattern=r'^\d{3}-?\d{4}$')
    prefecture: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=100)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    
    # Business info
    business_type: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    capital: Optional[int] = Field(None, ge=0)
    employee_count: Optional[int] = Field(None, ge=0)
    fiscal_year_end: Optional[str] = Field(None, pattern=r'^\d{2}-\d{2}$')
    
    # Other fields
    parent_id: Optional[int] = None
    description: Optional[str] = Field(None, max_length=1000)
    logo_url: Optional[str] = Field(None, max_length=255)
    settings: Optional[dict[str, Any]] = None


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
    SoftDeleteInfo
):
    """Full organization response schema."""
    id: int
    parent_id: Optional[int] = None
    parent: Optional[OrganizationBasic] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    settings: dict[str, Any] = Field(default_factory=dict)
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