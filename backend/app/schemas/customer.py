"""Customer relationship management schemas for Phase 5 CRM API."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from app.schemas.base import BaseResponse


class CustomerContactBase(BaseModel):
    """Base schema for customer contacts."""
    
    first_name: str = Field(..., max_length=100, description="First name")
    last_name: str = Field(..., max_length=100, description="Last name")
    title: Optional[str] = Field(None, max_length=100, description="Job title")
    department: Optional[str] = Field(None, max_length=100, description="Department")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    mobile: Optional[str] = Field(None, max_length=50, description="Mobile number")
    is_primary: bool = Field(False, description="Primary contact flag")
    is_decision_maker: bool = Field(False, description="Decision maker flag")
    notes: Optional[str] = Field(None, description="Contact notes")


class CustomerContactCreate(CustomerContactBase):
    """Schema for creating customer contacts."""
    pass


class CustomerContactUpdate(BaseModel):
    """Schema for updating customer contacts."""
    
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None)
    phone: Optional[str] = Field(None, max_length=50)
    mobile: Optional[str] = Field(None, max_length=50)
    is_primary: Optional[bool] = Field(None)
    is_decision_maker: Optional[bool] = Field(None)
    notes: Optional[str] = Field(None)


class CustomerContactResponse(CustomerContactBase, BaseResponse):
    """Schema for customer contact responses."""
    
    id: int
    customer_id: int
    full_name: str
    
    class Config:
        from_attributes = True


class CustomerBase(BaseModel):
    """Base schema for customers."""
    
    customer_code: str = Field(..., max_length=50, description="Customer code")
    company_name: str = Field(..., max_length=200, description="Company name")
    customer_type: str = Field(..., description="Customer type")
    status: str = Field("prospect", description="Customer status")
    assigned_to: Optional[int] = Field(None, description="Assigned sales rep ID")
    email: Optional[str] = Field(None, description="Primary email")
    phone: Optional[str] = Field(None, max_length=50, description="Primary phone")
    website: Optional[str] = Field(None, description="Company website")
    address_line1: Optional[str] = Field(None, max_length=255, description="Address line 1")
    address_line2: Optional[str] = Field(None, max_length=255, description="Address line 2")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State/Province")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal code")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    industry: Optional[str] = Field(None, max_length=100, description="Industry")
    annual_revenue: Optional[Decimal] = Field(None, description="Annual revenue")
    employee_count: Optional[int] = Field(None, description="Number of employees")
    notes: Optional[str] = Field(None, description="Customer notes")
    tags: Optional[str] = Field(None, max_length=500, description="Customer tags")
    first_contact_date: Optional[date] = Field(None, description="First contact date")
    last_contact_date: Optional[date] = Field(None, description="Last contact date")

    @validator('customer_type')
    def validate_customer_type(cls, v):
        allowed_types = ['individual', 'corporate', 'government', 'non_profit']
        if v not in allowed_types:
            raise ValueError(f'Customer type must be one of: {", ".join(allowed_types)}')
        return v

    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['active', 'inactive', 'prospect', 'former']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v


class CustomerCreate(CustomerBase):
    """Schema for creating customers."""
    
    contacts: List[CustomerContactCreate] = Field(default_factory=list, description="Customer contacts")


class CustomerUpdate(BaseModel):
    """Schema for updating customers."""
    
    company_name: Optional[str] = Field(None, max_length=200)
    customer_type: Optional[str] = Field(None)
    status: Optional[str] = Field(None)
    assigned_to: Optional[int] = Field(None)
    email: Optional[str] = Field(None)
    phone: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    annual_revenue: Optional[Decimal] = Field(None)
    employee_count: Optional[int] = Field(None)
    notes: Optional[str] = Field(None)
    tags: Optional[str] = Field(None, max_length=500)
    first_contact_date: Optional[date] = Field(None)
    last_contact_date: Optional[date] = Field(None)


class CustomerResponse(CustomerBase, BaseResponse):
    """Schema for customer responses."""
    
    id: int
    organization_id: int
    
    # Relationships
    contacts: List[CustomerContactResponse] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class OpportunityBase(BaseModel):
    """Base schema for opportunities."""
    
    opportunity_code: str = Field(..., max_length=50, description="Opportunity code")
    name: str = Field(..., max_length=200, description="Opportunity name")
    description: Optional[str] = Field(None, description="Opportunity description")
    stage: str = Field("lead", description="Opportunity stage")
    value: Optional[Decimal] = Field(None, description="Opportunity value")
    probability: Optional[Decimal] = Field(None, ge=0, le=100, description="Win probability")
    expected_close_date: Optional[date] = Field(None, description="Expected close date")
    actual_close_date: Optional[date] = Field(None, description="Actual close date")
    source: Optional[str] = Field(None, max_length=100, description="Lead source")
    competitor: Optional[str] = Field(None, max_length=200, description="Main competitor")
    notes: Optional[str] = Field(None, description="Opportunity notes")
    assigned_to: Optional[int] = Field(None, description="Assigned sales rep ID")

    @validator('stage')
    def validate_stage(cls, v):
        allowed_stages = ['lead', 'qualified', 'proposal', 'negotiation', 'closed_won', 'closed_lost']
        if v not in allowed_stages:
            raise ValueError(f'Stage must be one of: {", ".join(allowed_stages)}')
        return v


class OpportunityCreate(OpportunityBase):
    """Schema for creating opportunities."""
    
    customer_id: int = Field(..., description="Customer ID")


class OpportunityUpdate(BaseModel):
    """Schema for updating opportunities."""
    
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None)
    stage: Optional[str] = Field(None)
    value: Optional[Decimal] = Field(None)
    probability: Optional[Decimal] = Field(None, ge=0, le=100)
    expected_close_date: Optional[date] = Field(None)
    actual_close_date: Optional[date] = Field(None)
    source: Optional[str] = Field(None, max_length=100)
    competitor: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = Field(None)
    assigned_to: Optional[int] = Field(None)


class OpportunityResponse(OpportunityBase, BaseResponse):
    """Schema for opportunity responses."""
    
    id: int
    customer_id: int
    
    # Computed properties
    is_open: bool
    is_won: bool
    weighted_value: Optional[Decimal]
    
    class Config:
        from_attributes = True


class CustomerActivityBase(BaseModel):
    """Base schema for customer activities."""
    
    activity_type: str = Field(..., description="Activity type")
    subject: str = Field(..., max_length=200, description="Activity subject")
    description: Optional[str] = Field(None, description="Activity description")
    activity_date: datetime = Field(..., description="Activity date")
    duration_minutes: Optional[int] = Field(None, description="Duration in minutes")
    is_completed: bool = Field(True, description="Completion status")
    opportunity_id: Optional[int] = Field(None, description="Related opportunity ID")

    @validator('activity_type')
    def validate_activity_type(cls, v):
        allowed_types = ['call', 'email', 'meeting', 'task', 'note', 'proposal']
        if v not in allowed_types:
            raise ValueError(f'Activity type must be one of: {", ".join(allowed_types)}')
        return v


class CustomerActivityCreate(CustomerActivityBase):
    """Schema for creating customer activities."""
    
    customer_id: int = Field(..., description="Customer ID")


class CustomerActivityUpdate(BaseModel):
    """Schema for updating customer activities."""
    
    activity_type: Optional[str] = Field(None)
    subject: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None)
    activity_date: Optional[datetime] = Field(None)
    duration_minutes: Optional[int] = Field(None)
    is_completed: Optional[bool] = Field(None)
    opportunity_id: Optional[int] = Field(None)


class CustomerActivityResponse(CustomerActivityBase, BaseResponse):
    """Schema for customer activity responses."""
    
    id: int
    customer_id: int
    user_id: int
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class CustomerListResponse(BaseModel):
    """Schema for customer list responses."""
    
    items: List[CustomerResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


class OpportunityListResponse(BaseModel):
    """Schema for opportunity list responses."""
    
    items: List[OpportunityResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


class CustomerSearch(BaseModel):
    """Schema for customer search filters."""
    
    customer_type: Optional[str] = Field(None, description="Customer type filter")
    status: Optional[str] = Field(None, description="Status filter")
    assigned_to: Optional[int] = Field(None, description="Assigned sales rep filter")
    industry: Optional[str] = Field(None, description="Industry filter")
    city: Optional[str] = Field(None, description="City filter")
    country: Optional[str] = Field(None, description="Country filter")
    search_text: Optional[str] = Field(None, description="Text search in name/notes")
    tags: Optional[str] = Field(None, description="Tag filter")


class CRMAnalytics(BaseModel):
    """Schema for CRM analytics."""
    
    total_customers: int
    active_customers: int
    prospects: int
    total_opportunities: int
    open_opportunities: int
    total_opportunity_value: Decimal
    weighted_pipeline_value: Decimal
    won_opportunities: int
    won_opportunity_value: Decimal
    conversion_rate: Decimal
    
    # Pipeline analysis
    by_stage: List[dict] = Field(default_factory=list, description="Opportunities by stage")
    by_source: List[dict] = Field(default_factory=list, description="Opportunities by source")
    by_assigned_user: List[dict] = Field(default_factory=list, description="Opportunities by user")
    monthly_trends: List[dict] = Field(default_factory=list, description="Monthly trends")