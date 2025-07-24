"""
CRM API Schemas - CC02 v31.0 Phase 2

Pydantic schemas for CRM (Customer Relationship Management) API including:
- Customer Management & Lifecycle
- Contact Management & Relationship Tracking
- Lead Management & Nurturing
- Opportunity Management & Sales Pipeline
- Activity Tracking & Communication History
- Campaign Management & ROI Tracking
- Customer Service & Support
- CRM Analytics & Reporting
- Customer Health & Satisfaction Monitoring
- Sales Process Automation
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.models.crm_extended import (
    ActivityType,
    CampaignStatus,
    CampaignType,
    ContactType,
    LeadSource,
    LeadStatus,
    OpportunityStage,
    SupportTicketPriority,
    SupportTicketStatus,
)

# =============================================================================
# Customer Schemas
# =============================================================================


class CustomerBase(BaseModel):
    """Base schema for Customer."""

    organization_id: str
    customer_code: Optional[str] = None
    company_name: str
    legal_name: Optional[str] = None
    doing_business_as: Optional[str] = None
    industry: Optional[str] = None
    sub_industry: Optional[str] = None
    company_size: Optional[str] = None
    annual_revenue: Optional[Decimal] = Field(None, ge=0)
    employee_count: Optional[int] = Field(None, ge=1)
    website: Optional[str] = None
    main_phone: Optional[str] = None
    main_email: Optional[str] = None
    main_address_line1: Optional[str] = None
    main_address_line2: Optional[str] = None
    main_city: Optional[str] = None
    main_state_province: Optional[str] = None
    main_postal_code: Optional[str] = None
    main_country: str = "JP"
    tax_id: Optional[str] = None
    registration_number: Optional[str] = None
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    payment_terms: Optional[str] = None
    preferred_currency: str = "JPY"
    account_manager_id: Optional[str] = None
    customer_success_manager_id: Optional[str] = None
    sales_rep_id: Optional[str] = None
    customer_tier: Optional[str] = None
    customer_segment: Optional[str] = None
    preferred_contact_method: Optional[str] = None
    communication_frequency: Optional[str] = None
    opt_out_marketing: bool = False
    opt_out_surveys: bool = False
    is_prospect: bool = False
    is_partner: bool = False
    notes: Optional[str] = None
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}


class CustomerCreate(CustomerBase):
    """Schema for creating Customer."""

    pass


class CustomerUpdate(BaseModel):
    """Schema for updating Customer."""

    company_name: Optional[str] = None
    legal_name: Optional[str] = None
    doing_business_as: Optional[str] = None
    industry: Optional[str] = None
    sub_industry: Optional[str] = None
    company_size: Optional[str] = None
    annual_revenue: Optional[Decimal] = Field(None, ge=0)
    employee_count: Optional[int] = Field(None, ge=1)
    website: Optional[str] = None
    main_phone: Optional[str] = None
    main_email: Optional[str] = None
    main_address_line1: Optional[str] = None
    main_address_line2: Optional[str] = None
    main_city: Optional[str] = None
    main_state_province: Optional[str] = None
    main_postal_code: Optional[str] = None
    main_country: Optional[str] = None
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    payment_terms: Optional[str] = None
    account_manager_id: Optional[str] = None
    customer_success_manager_id: Optional[str] = None
    sales_rep_id: Optional[str] = None
    customer_tier: Optional[str] = None
    customer_segment: Optional[str] = None
    risk_category: Optional[str] = None
    preferred_contact_method: Optional[str] = None
    communication_frequency: Optional[str] = None
    opt_out_marketing: Optional[bool] = None
    opt_out_surveys: Optional[bool] = None
    is_active: Optional[bool] = None
    is_prospect: Optional[bool] = None
    is_partner: Optional[bool] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class CustomerResponse(CustomerBase):
    """Schema for Customer response."""

    id: str
    acquisition_date: Optional[date] = None
    first_purchase_date: Optional[date] = None
    last_purchase_date: Optional[date] = None
    churn_date: Optional[date] = None
    churn_reason: Optional[str] = None
    lifetime_value: Optional[Decimal] = None
    average_order_value: Optional[Decimal] = None
    total_orders: int
    total_revenue: Decimal
    health_score: Optional[Decimal] = None
    satisfaction_score: Optional[Decimal] = None
    nps_score: Optional[int] = None
    risk_category: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True


# =============================================================================
# Contact Schemas
# =============================================================================


class ContactBase(BaseModel):
    """Base schema for Contact."""

    customer_id: str
    organization_id: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    preferred_name: Optional[str] = None
    salutation: Optional[str] = None
    suffix: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    seniority_level: Optional[str] = None
    work_email: Optional[str] = None
    personal_email: Optional[str] = None
    work_phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    home_phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_handle: Optional[str] = None
    other_social_profiles: Dict[str, str] = {}
    preferred_contact_method: Optional[str] = None
    best_time_to_contact: Optional[str] = None
    time_zone: Optional[str] = None
    language_preference: str = "en"
    contact_type: ContactType = ContactType.PRIMARY
    decision_making_authority: Optional[str] = None
    influence_level: Optional[int] = Field(None, ge=1, le=10)
    relationship_strength: Optional[int] = Field(None, ge=1, le=10)
    birthday: Optional[date] = None
    anniversary: Optional[date] = None
    spouse_name: Optional[str] = None
    children_count: Optional[int] = Field(None, ge=0)
    hobbies: List[str] = []
    interests: List[str] = []
    is_primary: bool = False
    is_decision_maker: bool = False
    notes: Optional[str] = None
    tags: List[str] = []


class ContactCreate(ContactBase):
    """Schema for creating Contact."""

    pass


class ContactUpdate(BaseModel):
    """Schema for updating Contact."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    preferred_name: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    seniority_level: Optional[str] = None
    work_email: Optional[str] = None
    personal_email: Optional[str] = None
    work_phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    preferred_contact_method: Optional[str] = None
    best_time_to_contact: Optional[str] = None
    contact_type: Optional[ContactType] = None
    decision_making_authority: Optional[str] = None
    influence_level: Optional[int] = Field(None, ge=1, le=10)
    relationship_strength: Optional[int] = Field(None, ge=1, le=10)
    last_contact_date: Optional[date] = None
    next_contact_date: Optional[date] = None
    birthday: Optional[date] = None
    spouse_name: Optional[str] = None
    children_count: Optional[int] = Field(None, ge=0)
    hobbies: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_primary: Optional[bool] = None
    is_decision_maker: Optional[bool] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class ContactResponse(ContactBase):
    """Schema for Contact response."""

    id: str
    last_contact_date: Optional[date] = None
    last_contact_method: Optional[str] = None
    last_meeting_date: Optional[date] = None
    next_contact_date: Optional[date] = None
    is_active: bool
    email_bounced: bool
    opted_out: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str

    class Config:
        from_attributes = True


# =============================================================================
# Lead Schemas
# =============================================================================


class LeadBase(BaseModel):
    """Base schema for Lead."""

    organization_id: str
    lead_number: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    email: str
    phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    lead_source: LeadSource
    source_details: Optional[str] = None
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    decision_maker: bool = False
    need_identified: bool = False
    assigned_to_id: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    annual_revenue: Optional[Decimal] = Field(None, ge=0)
    employee_count: Optional[int] = Field(None, ge=1)
    products_interested: List[str] = []
    pain_points: List[str] = []
    requirements: Optional[str] = None
    campaign_id: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}


class LeadCreate(LeadBase):
    """Schema for creating Lead."""

    pass


class LeadUpdate(BaseModel):
    """Schema for updating Lead."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    website: Optional[str] = None
    status: Optional[LeadStatus] = None
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    decision_maker: Optional[bool] = None
    need_identified: Optional[bool] = None
    assigned_to_id: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    annual_revenue: Optional[Decimal] = Field(None, ge=0)
    employee_count: Optional[int] = Field(None, ge=1)
    products_interested: Optional[List[str]] = None
    pain_points: Optional[List[str]] = None
    requirements: Optional[str] = None
    next_follow_up_date: Optional[datetime] = None
    is_qualified: Optional[bool] = None
    is_marketing_qualified: Optional[bool] = None
    is_sales_qualified: Optional[bool] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class LeadResponse(LeadBase):
    """Schema for Lead response."""

    id: str
    status: LeadStatus
    lead_score: int
    demographic_score: int
    behavioral_score: int
    fit_score: int
    assigned_date: Optional[datetime] = None
    first_contact_date: Optional[datetime] = None
    last_contact_date: Optional[datetime] = None
    last_activity_date: Optional[datetime] = None
    next_follow_up_date: Optional[datetime] = None
    conversion_date: Optional[datetime] = None
    converted_opportunity_id: Optional[str] = None
    conversion_value: Optional[Decimal] = None
    is_qualified: bool
    is_marketing_qualified: bool
    is_sales_qualified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str

    class Config:
        from_attributes = True


# =============================================================================
# Opportunity Schemas
# =============================================================================


class OpportunityBase(BaseModel):
    """Base schema for Opportunity."""

    customer_id: str
    organization_id: str
    lead_id: Optional[str] = None
    opportunity_number: Optional[str] = None
    name: str
    description: Optional[str] = None
    amount: Decimal = Field(ge=0)
    currency: str = "JPY"
    expected_close_date: date
    sales_rep_id: str
    sales_manager_id: Optional[str] = None
    sales_engineer_id: Optional[str] = None
    stage: OpportunityStage = OpportunityStage.PROSPECTING
    probability: Decimal = Field(default=0, ge=0, le=100)
    cost: Optional[Decimal] = Field(None, ge=0)
    discount_amount: Decimal = Field(default=0, ge=0)
    competitors: List[str] = []
    competitive_position: Optional[str] = None
    key_differentiators: List[str] = []
    products: List[str] = []
    services: List[str] = []
    solution_type: Optional[str] = None
    customer_needs: List[str] = []
    pain_points: List[str] = []
    success_criteria: List[str] = []
    decision_makers: List[str] = []
    decision_criteria: List[str] = []
    decision_process: Optional[str] = None
    budget_confirmed: bool = False
    authority_confirmed: bool = False
    need_confirmed: bool = False
    timeline_confirmed: bool = False
    forecast_category: Optional[str] = None
    requires_approval: bool = False
    notes: Optional[str] = None
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}

    @validator("expected_close_date")
    def validate_close_date(cls, v) -> dict:
        if v < date.today():
            raise ValueError("Expected close date cannot be in the past")
        return v


class OpportunityCreate(OpportunityBase):
    """Schema for creating Opportunity."""

    pass


class OpportunityUpdate(BaseModel):
    """Schema for updating Opportunity."""

    name: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = Field(None, ge=0)
    expected_close_date: Optional[date] = None
    actual_close_date: Optional[date] = None
    stage: Optional[OpportunityStage] = None
    probability: Optional[Decimal] = Field(None, ge=0, le=100)
    cost: Optional[Decimal] = Field(None, ge=0)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    sales_manager_id: Optional[str] = None
    sales_engineer_id: Optional[str] = None
    competitors: Optional[List[str]] = None
    competitive_position: Optional[str] = None
    key_differentiators: Optional[List[str]] = None
    products: Optional[List[str]] = None
    services: Optional[List[str]] = None
    solution_type: Optional[str] = None
    customer_needs: Optional[List[str]] = None
    pain_points: Optional[List[str]] = None
    success_criteria: Optional[List[str]] = None
    decision_makers: Optional[List[str]] = None
    decision_criteria: Optional[List[str]] = None
    budget_confirmed: Optional[bool] = None
    authority_confirmed: Optional[bool] = None
    need_confirmed: Optional[bool] = None
    timeline_confirmed: Optional[bool] = None
    proposal_sent_date: Optional[date] = None
    proposal_value: Optional[Decimal] = Field(None, ge=0)
    contract_sent_date: Optional[date] = None
    contract_signed_date: Optional[date] = None
    lost_reason: Optional[str] = None
    lost_to_competitor: Optional[str] = None
    lost_details: Optional[str] = None
    forecast_category: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class OpportunityResponse(OpportunityBase):
    """Schema for Opportunity response."""

    id: str
    actual_close_date: Optional[date] = None
    expected_margin: Optional[Decimal] = None
    final_amount: Optional[Decimal] = None
    weighted_amount: Optional[Decimal] = None
    proposal_sent_date: Optional[date] = None
    proposal_value: Optional[Decimal] = None
    contract_sent_date: Optional[date] = None
    contract_signed_date: Optional[date] = None
    lost_reason: Optional[str] = None
    lost_to_competitor: Optional[str] = None
    lost_details: Optional[str] = None
    is_active: bool
    approved_by_id: Optional[str] = None
    approval_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str

    class Config:
        from_attributes = True


# =============================================================================
# Activity Schemas
# =============================================================================


class ActivityBase(BaseModel):
    """Base schema for CRM Activity."""

    organization_id: str
    customer_id: Optional[str] = None
    contact_id: Optional[str] = None
    lead_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    activity_type: ActivityType
    subject: str
    description: Optional[str] = None
    activity_date: datetime
    duration_minutes: Optional[int] = Field(None, ge=1)
    location: Optional[str] = None
    is_all_day: bool = False
    owner_id: str
    assigned_to_id: Optional[str] = None
    participants: List[str] = []
    outcome: Optional[str] = None
    requires_follow_up: bool = False
    follow_up_date: Optional[datetime] = None
    direction: Optional[str] = None
    channel: Optional[str] = None
    email_subject: Optional[str] = None
    call_duration_seconds: Optional[int] = Field(None, ge=1)
    call_outcome: Optional[str] = None
    meeting_url: Optional[str] = None
    meeting_attendees: List[str] = []
    meeting_agenda: Optional[str] = None
    meeting_notes: Optional[str] = None
    attachments: List[Dict[str, str]] = []
    tags: List[str] = []


class ActivityCreate(ActivityBase):
    """Schema for creating Activity."""

    pass


class ActivityUpdate(BaseModel):
    """Schema for updating Activity."""

    subject: Optional[str] = None
    description: Optional[str] = None
    activity_date: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=1)
    location: Optional[str] = None
    assigned_to_id: Optional[str] = None
    participants: Optional[List[str]] = None
    is_completed: Optional[bool] = None
    completion_date: Optional[datetime] = None
    outcome: Optional[str] = None
    requires_follow_up: Optional[bool] = None
    follow_up_date: Optional[datetime] = None
    call_duration_seconds: Optional[int] = Field(None, ge=1)
    call_outcome: Optional[str] = None
    meeting_notes: Optional[str] = None
    attachments: Optional[List[Dict[str, str]]] = None
    tags: Optional[List[str]] = None


class ActivityResponse(ActivityBase):
    """Schema for Activity response."""

    id: str
    is_completed: bool
    completion_date: Optional[datetime] = None
    follow_up_task_id: Optional[str] = None
    email_template_id: Optional[str] = None
    email_sent_count: int
    email_opened: bool
    email_clicked: bool
    call_recording_url: Optional[str] = None
    is_logged_automatically: bool
    source_system: Optional[str] = None
    external_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# Campaign Schemas
# =============================================================================


class CampaignBase(BaseModel):
    """Base schema for Campaign."""

    organization_id: str
    campaign_code: Optional[str] = None
    name: str
    description: Optional[str] = None
    campaign_type: CampaignType
    start_date: date
    end_date: Optional[date] = None
    budget: Optional[Decimal] = Field(None, ge=0)
    target_audience: Dict[str, Any] = {}
    geographic_targeting: List[str] = []
    demographic_targeting: Dict[str, Any] = {}
    primary_goal: Optional[str] = None
    target_leads: Optional[int] = Field(None, ge=1)
    target_opportunities: Optional[int] = Field(None, ge=1)
    target_revenue: Optional[Decimal] = Field(None, ge=0)
    key_message: Optional[str] = None
    call_to_action: Optional[str] = None
    landing_page_url: Optional[str] = None
    email_template_id: Optional[str] = None
    social_media_accounts: List[str] = []
    advertising_platforms: List[str] = []
    campaign_manager_id: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = []

    @validator("end_date")
    def validate_end_date(cls, v, values) -> dict:
        if "start_date" in values and v and v < values["start_date"]:
            raise ValueError("End date must be after start date")
        return v


class CampaignCreate(CampaignBase):
    """Schema for creating Campaign."""

    pass


class CampaignUpdate(BaseModel):
    """Schema for updating Campaign."""

    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CampaignStatus] = None
    end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    budget: Optional[Decimal] = Field(None, ge=0)
    actual_cost: Optional[Decimal] = Field(None, ge=0)
    target_leads: Optional[int] = Field(None, ge=1)
    target_opportunities: Optional[int] = Field(None, ge=1)
    target_revenue: Optional[Decimal] = Field(None, ge=0)
    key_message: Optional[str] = None
    call_to_action: Optional[str] = None
    landing_page_url: Optional[str] = None
    impressions: Optional[int] = Field(None, ge=0)
    clicks: Optional[int] = Field(None, ge=0)
    leads_generated: Optional[int] = Field(None, ge=0)
    opportunities_created: Optional[int] = Field(None, ge=0)
    revenue_generated: Optional[Decimal] = Field(None, ge=0)
    conversions: Optional[int] = Field(None, ge=0)
    campaign_manager_id: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class CampaignResponse(CampaignBase):
    """Schema for Campaign response."""

    id: str
    status: CampaignStatus
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    actual_cost: Decimal
    cost_per_lead: Optional[Decimal] = None
    cost_per_acquisition: Optional[Decimal] = None
    impressions: int
    clicks: int
    click_through_rate: Decimal
    leads_generated: int
    opportunities_created: int
    revenue_generated: Decimal
    conversions: int
    conversion_rate: Decimal
    roi_percentage: Optional[Decimal] = None
    roas: Optional[Decimal] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str

    class Config:
        from_attributes = True


# =============================================================================
# Support Ticket Schemas
# =============================================================================


class SupportTicketBase(BaseModel):
    """Base schema for Support Ticket."""

    customer_id: str
    contact_id: Optional[str] = None
    organization_id: str
    ticket_number: Optional[str] = None
    subject: str
    description: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    product: Optional[str] = None
    component: Optional[str] = None
    priority: SupportTicketPriority = SupportTicketPriority.MEDIUM
    severity: Optional[str] = None
    assigned_to_id: Optional[str] = None
    assigned_team: Optional[str] = None
    reporter_name: Optional[str] = None
    reporter_email: Optional[str] = None
    reporter_phone: Optional[str] = None
    related_tickets: List[str] = []
    related_opportunities: List[str] = []
    source: Optional[str] = None
    channel: Optional[str] = None
    attachments: List[Dict[str, str]] = []
    tags: List[str] = []


class SupportTicketCreate(SupportTicketBase):
    """Schema for creating Support Ticket."""

    pass


class SupportTicketUpdate(BaseModel):
    """Schema for updating Support Ticket."""

    subject: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    priority: Optional[SupportTicketPriority] = None
    severity: Optional[str] = None
    status: Optional[SupportTicketStatus] = None
    assigned_to_id: Optional[str] = None
    assigned_team: Optional[str] = None
    resolution: Optional[str] = None
    resolution_category: Optional[str] = None
    workaround: Optional[str] = None
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)
    satisfaction_feedback: Optional[str] = None
    is_escalated: Optional[bool] = None
    escalated_to_id: Optional[str] = None
    escalation_reason: Optional[str] = None
    related_tickets: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, str]]] = None
    tags: Optional[List[str]] = None


class SupportTicketResponse(SupportTicketBase):
    """Schema for Support Ticket response."""

    id: str
    status: SupportTicketStatus
    created_date: datetime
    first_response_date: Optional[datetime] = None
    resolved_date: Optional[datetime] = None
    closed_date: Optional[datetime] = None
    sla_due_date: Optional[datetime] = None
    sla_breached: bool
    response_time_minutes: Optional[int] = None
    resolution_time_minutes: Optional[int] = None
    resolution: Optional[str] = None
    resolution_category: Optional[str] = None
    workaround: Optional[str] = None
    satisfaction_rating: Optional[int] = None
    satisfaction_feedback: Optional[str] = None
    is_escalated: bool
    escalated_to_id: Optional[str] = None
    escalation_reason: Optional[str] = None
    escalation_date: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# Analytics and Reporting Schemas
# =============================================================================


class CRMDashboardMetrics(BaseModel):
    """Schema for CRM dashboard metrics."""

    organization_id: str
    period_start: date
    period_end: date
    leads_created: int
    leads_converted: int
    lead_conversion_rate: float
    opportunities_created: int
    opportunities_won: int
    win_rate: float
    total_revenue: float
    pipeline_value: float
    new_customers: int
    total_activities: int
    metrics_date: datetime


class CustomerHealthScore(BaseModel):
    """Schema for customer health score."""

    customer_id: str
    overall_health_score: float
    health_status: str
    health_factors: Dict[str, Dict[str, float]]
    recommendations: List[str]


class LeadConversionAnalysis(BaseModel):
    """Schema for lead conversion analysis."""

    lead_id: str
    customer_id: str
    contact_id: str
    conversion_date: datetime


class SalesForecast(BaseModel):
    """Schema for sales forecast data."""

    organization_id: str
    forecast_period: str
    total_pipeline_value: float
    weighted_pipeline_value: float
    committed_forecast: float
    best_case_forecast: float
    opportunities_by_stage: Dict[str, int]
    forecast_accuracy: Optional[float] = None


# =============================================================================
# Action Request Schemas
# =============================================================================


class ConvertLeadRequest(BaseModel):
    """Schema for converting lead to customer."""

    lead_id: str
    customer_data: Optional[Dict[str, Any]] = None


class AssignLeadRequest(BaseModel):
    """Schema for assigning lead to sales rep."""

    lead_id: str
    assigned_to_id: str
    notes: Optional[str] = None


class EscalateTicketRequest(BaseModel):
    """Schema for escalating support ticket."""

    ticket_id: str
    escalated_to_id: str
    escalation_reason: str


class UpdateOpportunityStageRequest(BaseModel):
    """Schema for updating opportunity stage."""

    opportunity_id: str
    stage: OpportunityStage
    probability: Optional[Decimal] = Field(None, ge=0, le=100)
    notes: Optional[str] = None


class BulkEmailCampaignRequest(BaseModel):
    """Schema for bulk email campaign."""

    campaign_id: str
    recipient_list: List[str]
    email_template_id: str
    send_date: Optional[datetime] = None


# =============================================================================
# Filter and Search Schemas
# =============================================================================


class CustomerFilterRequest(BaseModel):
    """Schema for customer filtering."""

    organization_id: Optional[str] = None
    account_manager_id: Optional[str] = None
    customer_tier: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    is_active: Optional[bool] = None
    is_prospect: Optional[bool] = None
    search_text: Optional[str] = None


class LeadFilterRequest(BaseModel):
    """Schema for lead filtering."""

    organization_id: Optional[str] = None
    status: Optional[LeadStatus] = None
    lead_source: Optional[LeadSource] = None
    assigned_to_id: Optional[str] = None
    is_qualified: Optional[bool] = None
    min_lead_score: Optional[int] = Field(None, ge=0, le=100)
    campaign_id: Optional[str] = None
    search_text: Optional[str] = None


class OpportunityFilterRequest(BaseModel):
    """Schema for opportunity filtering."""

    organization_id: Optional[str] = None
    customer_id: Optional[str] = None
    stage: Optional[OpportunityStage] = None
    sales_rep_id: Optional[str] = None
    is_active: Optional[bool] = None
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_amount: Optional[Decimal] = Field(None, ge=0)
    expected_close_date_from: Optional[date] = None
    expected_close_date_to: Optional[date] = None


class ActivityFilterRequest(BaseModel):
    """Schema for activity filtering."""

    customer_id: Optional[str] = None
    contact_id: Optional[str] = None
    lead_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    owner_id: Optional[str] = None
    activity_type: Optional[ActivityType] = None
    is_completed: Optional[bool] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
