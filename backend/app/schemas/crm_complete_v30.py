import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, validator


class CRMCustomerBase(BaseModel):
    customer_code: str = Field(..., min_length=1, max_length=50)
    full_name: str = Field(..., min_length=1, max_length=200)
    primary_email: EmailStr
    customer_type: str = Field(
        default="individual", regex="^(individual|business|partner)$"
    )
    lead_status: str = Field(
        default="new", regex="^(new|contacted|qualified|opportunity|customer|lost)$"
    )

    @validator("customer_code")
    def code_valid(cls, v):
        if not re.match(r"^[A-Z0-9_-]+$", v):
            raise ValueError(
                "Customer code must contain only uppercase letters, numbers, hyphens and underscores"
            )
        return v


class CRMCustomerCreate(CRMCustomerBase):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None

    # 連絡先情報
    secondary_email: Optional[EmailStr] = None
    primary_phone: Optional[str] = None
    secondary_phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    website: Optional[str] = None
    linkedin_profile: Optional[str] = None

    # 住所情報
    billing_address_line1: Optional[str] = None
    billing_city: Optional[str] = None
    billing_postal_code: Optional[str] = None
    billing_country: str = "Japan"

    mailing_address_line1: Optional[str] = None
    mailing_city: Optional[str] = None
    mailing_postal_code: Optional[str] = None
    mailing_country: str = "Japan"

    # 顧客分類
    customer_segment: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = Field(
        None, regex="^(startup|small|medium|large|enterprise)$"
    )
    annual_revenue: Optional[Decimal] = Field(None, ge=0)

    # CRM情報
    lead_source: Optional[str] = None
    customer_stage: str = Field(
        default="prospect", regex="^(prospect|lead|opportunity|customer|advocate)$"
    )
    lifecycle_stage: str = Field(
        default="subscriber",
        regex="^(subscriber|lead|mql|sql|opportunity|customer|evangelist)$",
    )
    assigned_sales_rep: Optional[str] = None
    assigned_account_manager: Optional[str] = None

    # コミュニケーション設定
    email_opt_in: bool = True
    sms_opt_in: bool = False
    phone_opt_in: bool = True
    marketing_opt_in: bool = True
    preferred_contact_method: str = Field(
        default="email", regex="^(email|phone|sms|none)$"
    )
    preferred_contact_time: Optional[str] = None
    time_zone: str = "Asia/Tokyo"

    # 属性
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}
    social_profiles: Dict[str, str] = {}
    notes: Optional[str] = None
    description: Optional[str] = None


class CRMCustomerUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    primary_email: Optional[EmailStr] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    customer_type: Optional[str] = Field(None, regex="^(individual|business|partner)$")
    customer_segment: Optional[str] = None
    industry: Optional[str] = None
    lead_status: Optional[str] = Field(
        None, regex="^(new|contacted|qualified|opportunity|customer|lost)$"
    )
    customer_stage: Optional[str] = Field(
        None, regex="^(prospect|lead|opportunity|customer|advocate)$"
    )
    lifecycle_stage: Optional[str] = Field(
        None, regex="^(subscriber|lead|mql|sql|opportunity|customer|evangelist)$"
    )
    lead_score: Optional[int] = Field(None, ge=0, le=100)
    engagement_score: Optional[int] = Field(None, ge=0, le=100)
    assigned_sales_rep: Optional[str] = None
    assigned_account_manager: Optional[str] = None
    is_qualified: Optional[bool] = None
    is_vip: Optional[bool] = None
    is_decision_maker: Optional[bool] = None
    do_not_contact: Optional[bool] = None
    email_opt_in: Optional[bool] = None
    marketing_opt_in: Optional[bool] = None
    preferred_contact_method: Optional[str] = Field(
        None, regex="^(email|phone|sms|none)$"
    )
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class CRMCustomerResponse(CRMCustomerBase):
    id: str
    first_name: Optional[str]
    last_name: Optional[str]
    company_name: Optional[str]
    job_title: Optional[str]
    department: Optional[str]
    secondary_email: Optional[str]
    primary_phone: Optional[str]
    mobile_phone: Optional[str]
    website: Optional[str]
    billing_address_line1: Optional[str]
    billing_city: Optional[str]
    billing_country: str
    customer_segment: Optional[str]
    industry: Optional[str]
    company_size: Optional[str]
    annual_revenue: Optional[Decimal]
    lead_source: Optional[str]
    customer_stage: str
    lifecycle_stage: str
    assigned_sales_rep: Optional[str]
    assigned_account_manager: Optional[str]
    lead_score: int
    engagement_score: int
    total_contract_value: Decimal
    lifetime_value: Decimal
    average_deal_size: Decimal
    last_purchase_date: Optional[date]
    first_purchase_date: Optional[date]
    email_opt_in: bool
    marketing_opt_in: bool
    preferred_contact_method: str
    time_zone: str
    is_active: bool
    is_qualified: bool
    is_vip: bool
    is_decision_maker: bool
    do_not_contact: bool
    tags: List[str]
    custom_fields: Dict[str, Any]
    social_profiles: Dict[str, str]
    notes: Optional[str]
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    last_contacted_at: Optional[datetime]
    last_activity_at: Optional[datetime]

    class Config:
        orm_mode = True


class CustomerInteractionBase(BaseModel):
    interaction_type: str = Field(..., regex="^(call|email|meeting|demo|webinar|chat)$")
    subject: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = None


class CustomerInteractionCreate(CustomerInteractionBase):
    customer_id: str
    interaction_direction: str = Field(default="outbound", regex="^(inbound|outbound)$")
    outcome: Optional[str] = None
    next_steps: Optional[str] = None
    interaction_date: datetime = Field(default_factory=datetime.utcnow)
    duration_minutes: Optional[int] = Field(None, ge=0)
    scheduled_follow_up: Optional[datetime] = None
    status: str = Field(
        default="completed", regex="^(scheduled|completed|cancelled|no_show)$"
    )
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)
    lead_quality_score: Optional[int] = Field(None, ge=1, le=10)
    channel: Optional[str] = None
    campaign_id: Optional[str] = None
    custom_fields: Dict[str, Any] = {}


class CustomerInteractionUpdate(BaseModel):
    subject: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = None
    outcome: Optional[str] = None
    next_steps: Optional[str] = None
    scheduled_follow_up: Optional[datetime] = None
    status: Optional[str] = Field(
        None, regex="^(scheduled|completed|cancelled|no_show)$"
    )
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)
    lead_quality_score: Optional[int] = Field(None, ge=1, le=10)


class CustomerInteractionResponse(CustomerInteractionBase):
    id: str
    customer_id: str
    user_id: str
    interaction_direction: str
    outcome: Optional[str]
    next_steps: Optional[str]
    interaction_date: datetime
    duration_minutes: Optional[int]
    scheduled_follow_up: Optional[datetime]
    status: str
    satisfaction_rating: Optional[int]
    lead_quality_score: Optional[int]
    channel: Optional[str]
    campaign_id: Optional[str]
    custom_fields: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class SalesOpportunityBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    amount: Optional[Decimal] = Field(None, ge=0)
    probability: int = Field(default=0, ge=0, le=100)


class SalesOpportunityCreate(SalesOpportunityBase):
    customer_id: str
    description: Optional[str] = None
    currency: str = "JPY"
    stage: str = Field(
        default="prospecting",
        regex="^(prospecting|qualification|proposal|negotiation|closed_won|closed_lost)$",
    )
    expected_close_date: Optional[date] = None
    product_category: Optional[str] = None
    solution_type: Optional[str] = None
    competitors: List[str] = []
    decision_criteria: Optional[str] = None
    decision_makers: List[str] = []
    budget_confirmed: bool = False
    timeline_confirmed: bool = False
    authority_confirmed: bool = False
    need_confirmed: bool = False
    source: Optional[str] = None
    campaign_id: Optional[str] = None
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}


class SalesOpportunityUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = None
    amount: Optional[Decimal] = Field(None, ge=0)
    probability: Optional[int] = Field(None, ge=0, le=100)
    stage: Optional[str] = Field(
        None,
        regex="^(prospecting|qualification|proposal|negotiation|closed_won|closed_lost)$",
    )
    status: Optional[str] = Field(None, regex="^(open|won|lost|on_hold)$")
    expected_close_date: Optional[date] = None
    actual_close_date: Optional[date] = None
    product_category: Optional[str] = None
    solution_type: Optional[str] = None
    competitors: Optional[List[str]] = None
    decision_criteria: Optional[str] = None
    decision_makers: Optional[List[str]] = None
    budget_confirmed: Optional[bool] = None
    timeline_confirmed: Optional[bool] = None
    authority_confirmed: Optional[bool] = None
    need_confirmed: Optional[bool] = None
    loss_reason: Optional[str] = None
    loss_reason_detail: Optional[str] = None
    next_action: Optional[str] = None
    next_action_date: Optional[date] = None


class SalesOpportunityResponse(SalesOpportunityBase):
    id: str
    opportunity_number: str
    customer_id: str
    owner_id: str
    description: Optional[str]
    currency: str
    weighted_amount: Optional[Decimal]
    stage: str
    stage_updated_at: Optional[datetime]
    status: str
    created_date: date
    expected_close_date: Optional[date]
    actual_close_date: Optional[date]
    last_stage_change_date: Optional[date]
    product_category: Optional[str]
    solution_type: Optional[str]
    competitors: List[str]
    decision_criteria: Optional[str]
    decision_makers: List[str]
    budget_confirmed: bool
    timeline_confirmed: bool
    authority_confirmed: bool
    need_confirmed: bool
    loss_reason: Optional[str]
    loss_reason_detail: Optional[str]
    next_action: Optional[str]
    next_action_date: Optional[date]
    last_activity_date: Optional[date]
    source: Optional[str]
    campaign_id: Optional[str]
    tags: List[str]
    custom_fields: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class OpportunityActivityBase(BaseModel):
    activity_type: str = Field(..., regex="^(call|email|meeting|proposal_sent|demo)$")
    subject: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = None


class OpportunityActivityCreate(OpportunityActivityBase):
    opportunity_id: str
    activity_date: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None
    status: str = Field(
        default="completed", regex="^(planned|in_progress|completed|cancelled)$"
    )
    priority: str = Field(default="normal", regex="^(low|normal|high|urgent)$")
    outcome: Optional[str] = None
    outcome_notes: Optional[str] = None


class OpportunityActivityResponse(OpportunityActivityBase):
    id: str
    opportunity_id: str
    user_id: str
    activity_date: datetime
    due_date: Optional[datetime]
    status: str
    priority: str
    outcome: Optional[str]
    outcome_notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class CustomerActivityBase(BaseModel):
    activity_type: str = Field(
        ..., regex="^(task|note|call|email|meeting|webpage_visit|form_submit)$"
    )
    subject: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = None


class CustomerActivityCreate(CustomerActivityBase):
    customer_id: str
    activity_category: Optional[str] = Field(
        None, regex="^(sales|marketing|support|system)$"
    )
    activity_date: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None
    status: str = Field(
        default="completed", regex="^(planned|in_progress|completed|cancelled|overdue)$"
    )
    priority: str = Field(default="normal", regex="^(low|normal|high|urgent)$")
    page_url: Optional[str] = None
    referrer_url: Optional[str] = None
    source: Optional[str] = None
    campaign_id: Optional[str] = None
    custom_fields: Dict[str, Any] = {}


class CustomerActivityResponse(CustomerActivityBase):
    id: str
    customer_id: str
    user_id: Optional[str]
    activity_category: Optional[str]
    activity_date: datetime
    due_date: Optional[datetime]
    status: str
    priority: str
    page_url: Optional[str]
    referrer_url: Optional[str]
    source: Optional[str]
    campaign_id: Optional[str]
    custom_fields: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class CustomerSegmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class CustomerSegmentCreate(CustomerSegmentBase):
    segment_type: str = Field(default="static", regex="^(static|dynamic)$")
    criteria: Dict[str, Any] = {}
    color: str = Field(default="#007bff", regex="^#[0-9A-Fa-f]{6}$")
    is_active: bool = True


class CustomerSegmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    criteria: Optional[Dict[str, Any]] = None
    color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")
    is_active: Optional[bool] = None


class CustomerSegmentResponse(CustomerSegmentBase):
    id: str
    segment_type: str
    criteria: Dict[str, Any]
    customer_count: int
    total_value: Decimal
    avg_customer_value: Decimal
    color: str
    is_active: bool
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime]
    last_calculated_at: Optional[datetime]

    class Config:
        orm_mode = True


class MarketingCampaignBase(BaseModel):
    campaign_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class MarketingCampaignCreate(MarketingCampaignBase):
    campaign_type: Optional[str] = Field(
        None, regex="^(email|social_media|ppc|content|event|webinar)$"
    )
    channel: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[Decimal] = Field(None, ge=0)
    target_audience: Optional[str] = None
    target_segment_ids: List[str] = []
    owned_by: Optional[str] = None
    tags: List[str] = []


class MarketingCampaignUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = Field(
        None, regex="^(draft|active|paused|completed|cancelled)$"
    )
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[Decimal] = Field(None, ge=0)
    actual_cost: Optional[Decimal] = Field(None, ge=0)
    target_audience: Optional[str] = None
    target_segment_ids: Optional[List[str]] = None
    impressions: Optional[int] = Field(None, ge=0)
    clicks: Optional[int] = Field(None, ge=0)
    leads_generated: Optional[int] = Field(None, ge=0)
    opportunities_created: Optional[int] = Field(None, ge=0)
    customers_acquired: Optional[int] = Field(None, ge=0)
    revenue_generated: Optional[Decimal] = Field(None, ge=0)


class MarketingCampaignResponse(MarketingCampaignBase):
    id: str
    campaign_type: Optional[str]
    channel: Optional[str]
    status: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    budget: Optional[Decimal]
    actual_cost: Decimal
    cost_per_lead: Optional[Decimal]
    cost_per_acquisition: Optional[Decimal]
    target_audience: Optional[str]
    target_segment_ids: List[str]
    impressions: int
    clicks: int
    leads_generated: int
    opportunities_created: int
    customers_acquired: int
    revenue_generated: Decimal
    click_through_rate: Decimal
    conversion_rate: Decimal
    return_on_investment: Decimal
    created_by: str
    owned_by: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class CRMStatsResponse(BaseModel):
    total_customers: int
    active_customers: int
    qualified_leads: int
    total_opportunities: int
    open_opportunities: int
    total_pipeline_value: Decimal
    weighted_pipeline_value: Decimal
    avg_deal_size: Decimal
    win_rate: Decimal
    avg_sales_cycle: int
    by_stage: Dict[str, int]
    by_source: Dict[str, int]
    by_segment: Dict[str, Decimal]
    top_performers: List[Dict[str, Any]]


class CRMAnalyticsResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    new_customers: int
    qualified_leads: int
    opportunities_created: int
    deals_won: int
    deals_lost: int
    revenue_generated: Decimal
    pipeline_velocity: Decimal
    lead_conversion_rate: Decimal
    opportunity_win_rate: Decimal
    avg_deal_size: Decimal
    customer_acquisition_cost: Decimal
    lifetime_value: Decimal
    daily_breakdown: List[Dict[str, Any]]
    performance_by_rep: List[Dict[str, Any]]


class CRMCustomerListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[CRMCustomerResponse]


class SalesOpportunityListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[SalesOpportunityResponse]


class CustomerInteractionListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[CustomerInteractionResponse]
