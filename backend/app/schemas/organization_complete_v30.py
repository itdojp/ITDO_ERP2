from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import re

class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    organization_type: Optional[str] = Field(None, regex="^(corporation|division|department|team)$")
    industry: Optional[str] = None
    tax_id: Optional[str] = None
    registration_number: Optional[str] = None
    
    # 連絡先情報
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    website: Optional[str] = None
    
    # 住所情報
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "Japan"
    
    @validator('code')
    def code_valid(cls, v):
        if not re.match(r'^[A-Z0-9_-]+$', v):
            raise ValueError('Code must contain only uppercase letters, numbers, hyphens and underscores')
        return v

    @validator('phone', 'fax')
    def phone_valid(cls, v):
        if v and not re.match(r'^\+?[\d\s\-\(\)]+$', v):
            raise ValueError('Invalid phone number format')
        return v

    @validator('postal_code')
    def postal_code_valid(cls, v):
        if v and not re.match(r'^\d{3}-?\d{4}$', v):
            raise ValueError('Invalid Japanese postal code format')
        return v

class OrganizationCreate(OrganizationBase):
    parent_id: Optional[str] = None
    is_headquarters: bool = False
    annual_revenue: Optional[Decimal] = None
    employee_count: Optional[int] = None
    established_date: Optional[date] = None
    settings: Dict[str, Any] = {}

class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    organization_type: Optional[str] = Field(None, regex="^(corporation|division|department|team)$")
    industry: Optional[str] = None
    tax_id: Optional[str] = None
    registration_number: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    is_active: Optional[bool] = None
    annual_revenue: Optional[Decimal] = None
    employee_count: Optional[int] = None
    settings: Optional[Dict[str, Any]] = None

class OrganizationResponse(OrganizationBase):
    id: str
    parent_id: Optional[str]
    level: int
    path: Optional[str]
    is_active: bool
    is_headquarters: bool
    annual_revenue: Optional[Decimal]
    employee_count: Optional[int]
    established_date: Optional[date]
    created_at: datetime
    updated_at: Optional[datetime]
    children_count: int = 0
    departments_count: int = 0
    employees_count: int = 0

    class Config:
        orm_mode = True

class OrganizationListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[OrganizationResponse]

class OrganizationTreeNode(BaseModel):
    id: str
    name: str
    code: str
    level: int
    is_active: bool
    children: List['OrganizationTreeNode'] = []

class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    department_type: Optional[str] = Field(None, regex="^(operational|support|management)$")
    cost_center: Optional[str] = None
    budget: Optional[Decimal] = None
    location: Optional[str] = None

class DepartmentCreate(DepartmentBase):
    organization_id: str
    parent_department_id: Optional[str] = None
    manager_id: Optional[str] = None
    settings: Dict[str, Any] = {}

class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    department_type: Optional[str] = Field(None, regex="^(operational|support|management)$")
    cost_center: Optional[str] = None
    budget: Optional[Decimal] = None
    location: Optional[str] = None
    parent_department_id: Optional[str] = None
    manager_id: Optional[str] = None
    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None

class DepartmentResponse(DepartmentBase):
    id: str
    organization_id: str
    parent_department_id: Optional[str]
    manager_id: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    employees_count: int = 0
    child_departments_count: int = 0

    class Config:
        orm_mode = True

class AddressBase(BaseModel):
    address_type: str = Field(..., min_length=1, max_length=50)
    name: Optional[str] = None
    address_line1: str = Field(..., min_length=1, max_length=200)
    address_line2: Optional[str] = None
    city: str = Field(..., min_length=1, max_length=100)
    state: Optional[str] = None
    postal_code: str = Field(..., regex=r'^\d{3}-?\d{4}$')
    country: str = "Japan"
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[EmailStr] = None

class AddressCreate(AddressBase):
    organization_id: str
    is_primary: bool = False
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None

class AddressResponse(AddressBase):
    id: str
    organization_id: str
    is_primary: bool
    is_active: bool
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class ContactBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    title: Optional[str] = None
    department: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    contact_type: Optional[str] = Field(None, regex="^(primary|billing|technical|emergency)$")

class ContactCreate(ContactBase):
    organization_id: str
    is_primary: bool = False
    notes: Optional[str] = None

class ContactResponse(ContactBase):
    id: str
    organization_id: str
    is_primary: bool
    is_active: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class OrganizationStatsResponse(BaseModel):
    total_organizations: int
    active_organizations: int
    inactive_organizations: int
    headquarters_count: int
    by_type: Dict[str, int]
    by_industry: Dict[str, int]
    by_country: Dict[str, int]
    total_employees: int
    total_departments: int

class OrganizationHierarchyResponse(BaseModel):
    organization: OrganizationResponse
    departments: List[DepartmentResponse]
    children: List['OrganizationHierarchyResponse']

# Update forward references
OrganizationTreeNode.model_rebuild()
OrganizationHierarchyResponse.model_rebuild()