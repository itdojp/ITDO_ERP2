"""Customer relationship management schemas for Phase 5 CRM API."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, validator

from app.schemas.base import BaseResponse


class CustomerContactBase(BaseModel):
    """Base schema for customer contacts."""

    # Support both naming conventions
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    name: str = Field(..., max_length=100, description="Full name (primary field)")
    name_kana: Optional[str] = Field(
        None, max_length=100, description="Name in katakana"
    )
    title: Optional[str] = Field(None, max_length=100, description="Job title")
    department: Optional[str] = Field(None, max_length=100, description="Department")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    mobile: Optional[str] = Field(None, max_length=50, description="Mobile number")
    is_primary: bool = Field(False, description="Primary contact flag")
    is_decision_maker: bool = Field(False, description="Decision maker flag")
    decision_maker: bool = Field(False, description="Alternative decision maker flag")
    notes: Optional[str] = Field(None, description="Contact notes")


class CustomerContactCreate(CustomerContactBase):
    """Schema for creating customer contacts."""

    customer_id: int = Field(..., description="Customer ID")


class CustomerContactUpdate(BaseModel):
    """Schema for updating customer contacts."""

    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    name: Optional[str] = Field(None, max_length=100)
    name_kana: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None)
    phone: Optional[str] = Field(None, max_length=50)
    mobile: Optional[str] = Field(None, max_length=50)
    is_primary: Optional[bool] = Field(None)
    is_decision_maker: Optional[bool] = Field(None)
    decision_maker: Optional[bool] = Field(None)
    notes: Optional[str] = Field(None)


class CustomerContactResponse(CustomerContactBase, BaseResponse):
    """Schema for customer contact responses."""

    id: int
    customer_id: int
    full_name: str

    model_config = ConfigDict(from_attributes=True)


class CustomerBase(BaseModel):
    """Base schema for customers."""

    customer_code: str = Field(..., max_length=50, description="Customer code")
    company_name: str = Field(..., max_length=200, description="Company name")
    name_kana: Optional[str] = Field(
        None, max_length=200, description="Company name in katakana"
    )
    short_name: Optional[str] = Field(
        None, max_length=100, description="Short name/abbreviation"
    )
    customer_type: str = Field(..., description="Customer type")
    status: str = Field("prospect", description="Customer status")
    industry: Optional[str] = Field(None, max_length=100, description="Industry")
    scale: Optional[str] = Field(
        None, max_length=50, description="Company scale: large/medium/small"
    )
    assigned_to: Optional[int] = Field(None, description="Assigned sales rep ID")
    email: Optional[str] = Field(None, description="Primary email")
    phone: Optional[str] = Field(None, max_length=50, description="Primary phone")
    fax: Optional[str] = Field(None, max_length=20, description="FAX number")
    website: Optional[str] = Field(None, description="Company website")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal code")
    address_line1: Optional[str] = Field(
        None, max_length=255, description="Address line 1"
    )
    address_line2: Optional[str] = Field(
        None, max_length=255, description="Address line 2"
    )
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State/Prefecture")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    annual_revenue: Optional[Decimal] = Field(None, description="Annual revenue")
    employee_count: Optional[int] = Field(None, description="Number of employees")
    credit_limit: Optional[Decimal] = Field(None, description="Credit limit")
    payment_terms: Optional[str] = Field(
        None, max_length=100, description="Payment terms"
    )
    priority: str = Field("normal", description="Priority: high/normal/low")
    notes: Optional[str] = Field(None, description="Customer notes")
    description: Optional[str] = Field(None, description="General description")
    internal_memo: Optional[str] = Field(None, description="Internal memo")
    tags: Optional[str] = Field(None, max_length=500, description="Customer tags")
    first_contact_date: Optional[date] = Field(None, description="First contact date")
    last_contact_date: Optional[date] = Field(None, description="Last contact date")

    @field_validator("customer_type")
    def validate_customer_type(cls, v) -> dict:
        allowed_types = ["individual", "corporate", "government", "non_profit"]
        if v not in allowed_types:
            raise ValueError(
                f"Customer type must be one of: {', '.join(allowed_types)}"
            )
        return v

    @field_validator("status")
    def validate_status(cls, v) -> dict:
        allowed_statuses = ["active", "inactive", "prospect", "former"]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v

    @field_validator("scale")
    def validate_scale(cls, v) -> dict:
        if v is not None:
            allowed_scales = ["large", "medium", "small"]
            if v not in allowed_scales:
                raise ValueError(f"Scale must be one of: {', '.join(allowed_scales)}")
        return v

    @field_validator("priority")
    def validate_priority(cls, v) -> dict:
        allowed_priorities = ["high", "normal", "low"]
        if v not in allowed_priorities:
            raise ValueError(
                f"Priority must be one of: {', '.join(allowed_priorities)}"
            )
        return v


class CustomerCreate(CustomerBase):
    """Schema for creating customers."""

    contacts: List[CustomerContactCreate] = Field(
        default_factory=list, description="Customer contacts"
    )


class CustomerUpdate(BaseModel):
    """Schema for updating customers."""

    customer_code: Optional[str] = Field(None, max_length=50)
    company_name: Optional[str] = Field(None, max_length=200)
    name_kana: Optional[str] = Field(None, max_length=200)
    short_name: Optional[str] = Field(None, max_length=100)
    customer_type: Optional[str] = Field(None)
    status: Optional[str] = Field(None)
    industry: Optional[str] = Field(None, max_length=100)
    scale: Optional[str] = Field(None, max_length=50)
    assigned_to: Optional[int] = Field(None)
    email: Optional[str] = Field(None)
    phone: Optional[str] = Field(None, max_length=50)
    fax: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None)
    postal_code: Optional[str] = Field(None, max_length=20)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    annual_revenue: Optional[Decimal] = Field(None)
    employee_count: Optional[int] = Field(None)
    credit_limit: Optional[Decimal] = Field(None)
    payment_terms: Optional[str] = Field(None, max_length=100)
    priority: Optional[str] = Field(None)
    notes: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    internal_memo: Optional[str] = Field(None)
    tags: Optional[str] = Field(None, max_length=500)
    first_contact_date: Optional[date] = Field(None)
    last_contact_date: Optional[date] = Field(None)


class CustomerResponse(CustomerBase, BaseResponse):
    """Schema for customer responses."""

    id: int
    organization_id: int
    first_transaction_date: Optional[datetime]
    last_transaction_date: Optional[datetime]
    total_sales: Decimal
    total_transactions: int

    # Relationships
    contacts: List[CustomerContactResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class OpportunityBase(BaseModel):
    """Base schema for opportunities."""

    opportunity_code: Optional[str] = Field(
        None, max_length=50, description="Opportunity code"
    )
    name: str = Field(..., max_length=200, description="Opportunity name")
    title: str = Field(..., max_length=200, description="Opportunity title")
    description: Optional[str] = Field(None, description="Opportunity description")
    stage: str = Field("lead", description="Opportunity stage")
    status: str = Field("open", description="Status: open/won/lost/canceled")
    value: Optional[Decimal] = Field(None, description="Opportunity value")
    estimated_value: Optional[Decimal] = Field(None, description="Estimated value")
    probability: int = Field(0, ge=0, le=100, description="Win probability (0-100)")
    expected_close_date: Optional[datetime] = Field(
        None, description="Expected close date"
    )
    actual_close_date: Optional[datetime] = Field(None, description="Actual close date")
    source: Optional[str] = Field(None, max_length=100, description="Lead source")
    competitor: Optional[str] = Field(
        None, max_length=200, description="Main competitor"
    )
    competitors: Optional[str] = Field(None, description="All competitors")
    loss_reason: Optional[str] = Field(None, description="Loss reason")
    notes: Optional[str] = Field(None, description="Opportunity notes")
    assigned_to: Optional[int] = Field(None, description="Assigned sales rep ID")
    owner_id: int = Field(..., description="Opportunity owner ID")

    @field_validator("stage")
    def validate_stage(cls, v) -> dict:
        allowed_stages = [
            "lead",
            "qualified",
            "proposal",
            "negotiation",
            "closed_won",
            "closed_lost",
        ]
        if v not in allowed_stages:
            raise ValueError(f"Stage must be one of: {', '.join(allowed_stages)}")
        return v

    @field_validator("status")
    def validate_status(cls, v) -> dict:
        allowed_statuses = ["open", "won", "lost", "canceled"]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v


class OpportunityCreate(OpportunityBase):
    """Schema for creating opportunities."""

    customer_id: int = Field(..., description="Customer ID")


class OpportunityUpdate(BaseModel):
    """Schema for updating opportunities."""

    opportunity_code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=200)
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None)
    stage: Optional[str] = Field(None)
    status: Optional[str] = Field(None)
    value: Optional[Decimal] = Field(None)
    estimated_value: Optional[Decimal] = Field(None)
    probability: Optional[int] = Field(None, ge=0, le=100)
    expected_close_date: Optional[datetime] = Field(None)
    actual_close_date: Optional[datetime] = Field(None)
    source: Optional[str] = Field(None, max_length=100)
    competitor: Optional[str] = Field(None, max_length=200)
    competitors: Optional[str] = Field(None)
    loss_reason: Optional[str] = Field(None)
    notes: Optional[str] = Field(None)
    assigned_to: Optional[int] = Field(None)
    owner_id: Optional[int] = Field(None)


class OpportunityResponse(OpportunityBase, BaseResponse):
    """Schema for opportunity responses."""

    id: int
    customer_id: int

    # Computed properties
    is_open: bool
    is_won: bool
    weighted_value: Optional[Decimal]

    model_config = ConfigDict(from_attributes=True)


class CustomerActivityBase(BaseModel):
    """Base schema for customer activities."""

    activity_type: str = Field(..., description="Activity type")
    subject: str = Field(..., max_length=200, description="Activity subject")
    description: Optional[str] = Field(None, description="Activity description")
    activity_date: datetime = Field(..., description="Activity date")
    duration_minutes: Optional[int] = Field(None, description="Duration in minutes")
    status: str = Field("completed", description="Status: planned/completed/canceled")
    is_completed: bool = Field(True, description="Completion status")
    outcome: Optional[str] = Field(None, description="Activity outcome")
    next_action: Optional[str] = Field(None, description="Next action")
    next_action_date: Optional[datetime] = Field(None, description="Next action date")
    opportunity_id: Optional[int] = Field(None, description="Related opportunity ID")

    @field_validator("activity_type")
    def validate_activity_type(cls, v) -> dict:
        allowed_types = [
            "call",
            "email",
            "meeting",
            "task",
            "note",
            "proposal",
            "other",
        ]
        if v not in allowed_types:
            raise ValueError(
                f"Activity type must be one of: {', '.join(allowed_types)}"
            )
        return v

    @field_validator("status")
    def validate_status(cls, v) -> dict:
        allowed_statuses = ["planned", "completed", "canceled"]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
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
    status: Optional[str] = Field(None)
    is_completed: Optional[bool] = Field(None)
    outcome: Optional[str] = Field(None)
    next_action: Optional[str] = Field(None)
    next_action_date: Optional[datetime] = Field(None)
    opportunity_id: Optional[int] = Field(None)


class CustomerActivityResponse(CustomerActivityBase, BaseResponse):
    """Schema for customer activity responses."""

    id: int
    customer_id: int
    user_id: int
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# Complex response schemas with relationships
class CustomerDetailResponse(CustomerResponse):
    """Schema for detailed customer responses with relationships."""

    contacts: List[CustomerContactResponse] = Field(default_factory=list)
    opportunities: List[OpportunityResponse] = Field(default_factory=list)
    recent_activities: List[CustomerActivityResponse] = Field(default_factory=list)


class OpportunityDetailResponse(OpportunityResponse):
    """Schema for detailed opportunity responses with relationships."""

    activities: List[CustomerActivityResponse] = Field(default_factory=list)


class CustomerListResponse(BaseModel):
    """Schema for customer list responses."""

    items: List[CustomerResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool

    model_config = ConfigDict(from_attributes=True)


class OpportunityListResponse(BaseModel):
    """Schema for opportunity list responses."""

    items: List[OpportunityResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool

    model_config = ConfigDict(from_attributes=True)


class CustomerSearch(BaseModel):
    """Schema for customer search filters."""

    customer_type: Optional[str] = Field(None, description="Customer type filter")
    status: Optional[str] = Field(None, description="Status filter")
    assigned_to: Optional[int] = Field(None, description="Assigned sales rep filter")
    industry: Optional[str] = Field(None, description="Industry filter")
    scale: Optional[str] = Field(None, description="Scale filter")
    priority: Optional[str] = Field(None, description="Priority filter")
    city: Optional[str] = Field(None, description="City filter")
    country: Optional[str] = Field(None, description="Country filter")
    search_text: Optional[str] = Field(None, description="Text search in name/notes")
    tags: Optional[str] = Field(None, description="Tag filter")


class OpportunitySearch(BaseModel):
    """Schema for opportunity search filters."""

    stage: Optional[str] = Field(None, description="Stage filter")
    status: Optional[str] = Field(None, description="Status filter")
    assigned_to: Optional[int] = Field(None, description="Assigned user filter")
    owner_id: Optional[int] = Field(None, description="Owner filter")
    customer_id: Optional[int] = Field(None, description="Customer filter")
    min_value: Optional[Decimal] = Field(None, description="Minimum value")
    max_value: Optional[Decimal] = Field(None, description="Maximum value")
    expected_close_from: Optional[date] = Field(
        None, description="Expected close date from"
    )
    expected_close_to: Optional[date] = Field(
        None, description="Expected close date to"
    )


# Analytics schemas
class CustomerAnalytics(BaseModel):
    """Schema for customer analytics."""

    total_customers: int
    active_customers: int
    prospects: int
    inactive_customers: int
    customers_by_industry: dict = Field(default_factory=dict)
    customers_by_scale: dict = Field(default_factory=dict)
    customers_by_type: dict = Field(default_factory=dict)
    top_customers_by_sales: List[dict] = Field(default_factory=list)
    recent_acquisitions: int
    average_customer_value: Decimal

    model_config = ConfigDict(from_attributes=True)


class OpportunityAnalytics(BaseModel):
    """Schema for opportunity analytics."""

    total_opportunities: int
    open_opportunities: int
    won_opportunities: int
    lost_opportunities: int
    total_pipeline_value: Decimal
    weighted_pipeline_value: Decimal
    average_deal_size: Decimal
    win_rate: Decimal
    opportunities_by_stage: dict = Field(default_factory=dict)
    opportunities_by_source: dict = Field(default_factory=dict)
    monthly_closed_deals: dict = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class CRMAnalytics(BaseModel):
    """Schema for comprehensive CRM analytics."""

    customer_analytics: CustomerAnalytics
    opportunity_analytics: OpportunityAnalytics

    # Combined metrics
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
    by_stage: List[dict] = Field(
        default_factory=list, description="Opportunities by stage"
    )
    by_source: List[dict] = Field(
        default_factory=list, description="Opportunities by source"
    )
    by_assigned_user: List[dict] = Field(
        default_factory=list, description="Opportunities by user"
    )
    monthly_trends: List[dict] = Field(
        default_factory=list, description="Monthly trends"
    )

    model_config = ConfigDict(from_attributes=True)


# Bulk operations
class CustomerBulkCreate(BaseModel):
    """Schema for bulk customer creation."""

    customers: List[CustomerCreate]


class CustomerBulkUpdate(BaseModel):
    """Schema for bulk customer updates."""

    updates: List[dict] = Field(..., description="List of update operations")


class CustomerImport(BaseModel):
    """Schema for customer import operations."""

    file_format: str = Field(..., description="File format: csv/xlsx")
    mapping: dict = Field(..., description="Field mapping configuration")
    validation_rules: dict = Field(default_factory=dict, description="Validation rules")
    import_mode: str = Field("create", description="Import mode: create/update/upsert")


class CustomerExport(BaseModel):
    """Schema for customer export operations."""

    format: str = Field("csv", description="Export format: csv/xlsx/pdf")
    fields: List[str] = Field(default_factory=list, description="Fields to export")
    filters: Optional[CustomerSearch] = Field(None, description="Export filters")
    include_contacts: bool = Field(False, description="Include contact information")
    include_opportunities: bool = Field(False, description="Include opportunities")
    include_activities: bool = Field(False, description="Include activities")
