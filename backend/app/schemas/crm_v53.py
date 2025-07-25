"""
CC02 v53.0 CRM Schemas - Issue #568
10-Day ERP Business API Implementation Sprint - Day 7-8
Customer Relationship Management API Schemas
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class LeadSource(str, Enum):
    """Lead source enumeration"""
    WEBSITE = "website"
    REFERRAL = "referral"
    ADVERTISEMENT = "advertisement"
    SOCIAL_MEDIA = "social_media"
    EMAIL_CAMPAIGN = "email_campaign"
    TRADE_SHOW = "trade_show"
    COLD_CALL = "cold_call"
    PARTNER = "partner"
    OTHER = "other"


class LeadStatus(str, Enum):
    """Lead status enumeration"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CONVERTED = "converted"
    LOST = "lost"
    UNQUALIFIED = "unqualified"


class OpportunityStage(str, Enum):
    """Opportunity stage enumeration"""
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    NEEDS_ANALYSIS = "needs_analysis"
    VALUE_PROPOSITION = "value_proposition"
    DECISION_MAKERS = "decision_makers"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class ActivityType(str, Enum):
    """Activity type enumeration"""
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    TASK = "task"
    NOTE = "note"
    DEMO = "demo"
    PROPOSAL = "proposal"
    FOLLOW_UP = "follow_up"
    REMINDER = "reminder"


class ActivityStatus(str, Enum):
    """Activity status enumeration"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class ContactType(str, Enum):
    """Contact type enumeration"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    BILLING = "billing"
    TECHNICAL = "technical"
    DECISION_MAKER = "decision_maker"
    INFLUENCER = "influencer"


class CampaignType(str, Enum):
    """Campaign type enumeration"""
    EMAIL = "email"
    SOCIAL_MEDIA = "social_media"
    WEBINAR = "webinar"
    TRADE_SHOW = "trade_show"
    CONTENT = "content"
    ADVERTISING = "advertising"
    DIRECT_MAIL = "direct_mail"
    TELEMARKETING = "telemarketing"


class CampaignStatus(str, Enum):
    """Campaign status enumeration"""
    PLANNED = "planned"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# Lead Management Schemas

class LeadCreate(BaseModel):
    """Schema for creating lead"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    company: Optional[str] = Field(None, max_length=200)
    job_title: Optional[str] = Field(None, max_length=100)
    lead_source: LeadSource = Field(default=LeadSource.OTHER)
    status: LeadStatus = Field(default=LeadStatus.NEW)
    estimated_value: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    probability: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=1)
    expected_close_date: Optional[date] = None
    address: Optional[str] = Field(None, max_length=500)
    website: Optional[str] = Field(None, max_length=200)
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[int] = Field(None, ge=1)
    annual_revenue: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    assigned_to: Optional[str] = None
    campaign_id: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=2000)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class LeadUpdate(BaseModel):
    """Schema for updating lead"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    company: Optional[str] = Field(None, max_length=200)
    job_title: Optional[str] = Field(None, max_length=100)
    lead_source: Optional[LeadSource] = None
    status: Optional[LeadStatus] = None
    estimated_value: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    probability: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=1)
    expected_close_date: Optional[date] = None
    address: Optional[str] = Field(None, max_length=500)
    website: Optional[str] = Field(None, max_length=200)
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[int] = Field(None, ge=1)
    annual_revenue: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    assigned_to: Optional[str] = None
    campaign_id: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=2000)
    custom_fields: Optional[Dict[str, Any]] = None


class LeadResponse(BaseModel):
    """Schema for lead API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    first_name: str
    last_name: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    lead_source: LeadSource
    status: LeadStatus
    estimated_value: Optional[Decimal] = None
    probability: Optional[Decimal] = None
    expected_close_date: Optional[date] = None
    address: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[int] = None
    annual_revenue: Optional[Decimal] = None
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    campaign_id: Optional[str] = None
    campaign_name: Optional[str] = None
    is_converted: bool = False
    converted_customer_id: Optional[str] = None
    converted_opportunity_id: Optional[str] = None
    conversion_date: Optional[datetime] = None
    last_contacted: Optional[datetime] = None
    activities_count: int = 0
    notes: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


# Opportunity Management Schemas

class OpportunityCreate(BaseModel):
    """Schema for creating opportunity"""
    name: str = Field(..., min_length=1, max_length=200)
    customer_id: Optional[str] = None
    lead_id: Optional[str] = None
    stage: OpportunityStage = Field(default=OpportunityStage.PROSPECTING)
    amount: Decimal = Field(..., ge=0, decimal_places=2)
    probability: Decimal = Field(default=Decimal("50"), ge=0, le=100, decimal_places=1)
    expected_close_date: Optional[date] = None
    actual_close_date: Optional[date] = None
    lead_source: Optional[LeadSource] = None
    assigned_to: Optional[str] = None
    campaign_id: Optional[str] = None
    competitor: Optional[str] = Field(None, max_length=100)
    next_step: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    loss_reason: Optional[str] = Field(None, max_length=500)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class OpportunityUpdate(BaseModel):
    """Schema for updating opportunity"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    stage: Optional[OpportunityStage] = None
    amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    probability: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=1)
    expected_close_date: Optional[date] = None
    actual_close_date: Optional[date] = None
    lead_source: Optional[LeadSource] = None
    assigned_to: Optional[str] = None
    campaign_id: Optional[str] = None
    competitor: Optional[str] = Field(None, max_length=100)
    next_step: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    loss_reason: Optional[str] = Field(None, max_length=500)
    custom_fields: Optional[Dict[str, Any]] = None


class OpportunityResponse(BaseModel):
    """Schema for opportunity API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    lead_id: Optional[str] = None
    lead_name: Optional[str] = None
    stage: OpportunityStage
    amount: Decimal
    weighted_amount: Decimal
    probability: Decimal
    expected_close_date: Optional[date] = None
    actual_close_date: Optional[date] = None
    days_in_stage: int = 0
    age_days: int = 0
    lead_source: Optional[LeadSource] = None
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    campaign_id: Optional[str] = None
    campaign_name: Optional[str] = None
    competitor: Optional[str] = None
    next_step: Optional[str] = None
    description: Optional[str] = None
    loss_reason: Optional[str] = None
    is_won: bool = False
    is_lost: bool = False
    activities_count: int = 0
    last_activity_date: Optional[datetime] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


# Contact Management Schemas

class ContactCreate(BaseModel):
    """Schema for creating contact"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    mobile_phone: Optional[str] = Field(None, max_length=20)
    job_title: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    customer_id: Optional[str] = None
    contact_type: ContactType = Field(default=ContactType.PRIMARY)
    is_primary: bool = Field(default=False)
    is_decision_maker: bool = Field(default=False)
    address: Optional[str] = Field(None, max_length=500)
    linkedin_url: Optional[str] = Field(None, max_length=200)
    twitter_handle: Optional[str] = Field(None, max_length=50)
    preferred_contact_method: Optional[str] = Field(None, max_length=20)
    time_zone: Optional[str] = Field(None, max_length=50)
    birthday: Optional[date] = None
    assistant_name: Optional[str] = Field(None, max_length=100)
    assistant_phone: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field(None, max_length=2000)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class ContactResponse(BaseModel):
    """Schema for contact API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    first_name: str
    last_name: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    contact_type: ContactType
    is_primary: bool = False
    is_decision_maker: bool = False
    address: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_handle: Optional[str] = None
    preferred_contact_method: Optional[str] = None
    time_zone: Optional[str] = None
    birthday: Optional[date] = None
    assistant_name: Optional[str] = None
    assistant_phone: Optional[str] = None
    last_contacted: Optional[datetime] = None
    activities_count: int = 0
    opportunities_count: int = 0
    notes: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


# Activity Management Schemas

class ActivityCreate(BaseModel):
    """Schema for creating activity"""
    subject: str = Field(..., min_length=1, max_length=200)
    activity_type: ActivityType
    status: ActivityStatus = Field(default=ActivityStatus.SCHEDULED)
    priority: str = Field(default="medium", max_length=20)
    due_date: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=0, le=1440)  # Max 24 hours
    
    # Related entities
    customer_id: Optional[str] = None
    lead_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    contact_id: Optional[str] = None
    
    # Assignment
    assigned_to: Optional[str] = None
    created_by: Optional[str] = None
    
    # Details
    description: Optional[str] = Field(None, max_length=2000)
    location: Optional[str] = Field(None, max_length=200)
    outcome: Optional[str] = Field(None, max_length=1000)
    follow_up_required: bool = Field(default=False)
    follow_up_date: Optional[datetime] = None
    
    # Communication details
    call_result: Optional[str] = Field(None, max_length=100)
    email_subject: Optional[str] = Field(None, max_length=200)
    meeting_attendees: Optional[List[str]] = Field(default_factory=list)
    
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class ActivityUpdate(BaseModel):
    """Schema for updating activity"""
    subject: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[ActivityStatus] = None
    priority: Optional[str] = Field(None, max_length=20)
    due_date: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=0, le=1440)
    assigned_to: Optional[str] = None
    description: Optional[str] = Field(None, max_length=2000)
    location: Optional[str] = Field(None, max_length=200)
    outcome: Optional[str] = Field(None, max_length=1000)
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[datetime] = None
    call_result: Optional[str] = Field(None, max_length=100)
    email_subject: Optional[str] = Field(None, max_length=200)
    meeting_attendees: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class ActivityResponse(BaseModel):
    """Schema for activity API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    subject: str
    activity_type: ActivityType
    status: ActivityStatus
    priority: str = "medium"
    due_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    is_overdue: bool = False
    
    # Related entities
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    lead_id: Optional[str] = None
    lead_name: Optional[str] = None
    opportunity_id: Optional[str] = None
    opportunity_name: Optional[str] = None
    contact_id: Optional[str] = None
    contact_name: Optional[str] = None
    
    # Assignment
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    created_by: Optional[str] = None
    created_by_name: Optional[str] = None
    
    # Details
    description: Optional[str] = None
    location: Optional[str] = None
    outcome: Optional[str] = None
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None
    
    # Communication details
    call_result: Optional[str] = None
    email_subject: Optional[str] = None
    meeting_attendees: List[str] = Field(default_factory=list)
    
    # Completion details
    completed_date: Optional[datetime] = None
    completed_by: Optional[str] = None
    
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


# Campaign Management Schemas

class CampaignCreate(BaseModel):
    """Schema for creating campaign"""
    name: str = Field(..., min_length=1, max_length=200)
    campaign_type: CampaignType
    status: CampaignStatus = Field(default=CampaignStatus.PLANNED)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    expected_revenue: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    target_audience: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    owner: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v, info):
        if v and 'start_date' in info.data and info.data['start_date']:
            start_date = info.data['start_date']
            if v < start_date:
                raise ValueError('end_date cannot be before start_date')
        return v


class CampaignResponse(BaseModel):
    """Schema for campaign API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    campaign_type: CampaignType
    status: CampaignStatus
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[Decimal] = None
    expected_revenue: Optional[Decimal] = None
    actual_cost: Decimal = Decimal("0")
    actual_revenue: Decimal = Decimal("0")
    roi: Optional[Decimal] = None
    
    # Metrics
    leads_generated: int = 0
    opportunities_created: int = 0
    deals_won: int = 0
    conversion_rate: Optional[Decimal] = None
    
    target_audience: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[str] = None
    owner_name: Optional[str] = None
    
    # Status tracking
    is_active: bool = False
    is_completed: bool = False
    days_remaining: Optional[int] = None
    
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


# CRM Analytics and Statistics Schemas

class CRMStatistics(BaseModel):
    """Comprehensive CRM statistics"""
    # Lead Statistics
    total_leads: int
    new_leads: int
    qualified_leads: int
    converted_leads: int
    lead_conversion_rate: Decimal
    
    # Opportunity Statistics  
    total_opportunities: int
    open_opportunities: int
    won_opportunities: int
    lost_opportunities: int
    opportunity_win_rate: Decimal
    average_deal_size: Decimal
    total_pipeline_value: Decimal
    weighted_pipeline_value: Decimal
    
    # Activity Statistics
    total_activities: int
    completed_activities: int
    overdue_activities: int
    activities_this_week: int
    activity_completion_rate: Decimal
    
    # Contact Statistics
    total_contacts: int
    decision_makers_count: int
    primary_contacts_count: int
    contacts_with_activities: int
    
    # Campaign Statistics
    active_campaigns: int
    total_campaigns: int
    campaign_roi: Decimal
    leads_from_campaigns: int
    
    # Performance Metrics
    sales_cycle_days: Optional[Decimal] = None
    activities_per_opportunity: Decimal
    follow_up_response_rate: Decimal
    
    # Time-based Analysis
    leads_by_source: Dict[str, int]
    opportunities_by_stage: Dict[str, int]
    activities_by_type: Dict[str, int]
    monthly_performance: Dict[str, Dict[str, Any]]
    
    # Team Performance
    top_performers: List[Dict[str, Any]]
    team_metrics: Dict[str, Any]
    
    last_updated: datetime
    calculation_time_ms: float


# List Response Schemas

class LeadListResponse(BaseModel):
    """Schema for paginated lead list responses"""
    items: List[LeadResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


class OpportunityListResponse(BaseModel):
    """Schema for paginated opportunity list responses"""
    items: List[OpportunityResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


class ContactListResponse(BaseModel):
    """Schema for paginated contact list responses"""
    items: List[ContactResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


class ActivityListResponse(BaseModel):
    """Schema for paginated activity list responses"""
    items: List[ActivityResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


class CampaignListResponse(BaseModel):
    """Schema for paginated campaign list responses"""
    items: List[CampaignResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


# Bulk Operations Schemas

class BulkLeadOperation(BaseModel):
    """Schema for bulk lead operations"""
    leads: List[LeadCreate]
    validate_only: bool = Field(default=False)
    stop_on_error: bool = Field(default=False)
    assign_to: Optional[str] = None
    default_campaign_id: Optional[str] = None


class BulkLeadResult(BaseModel):
    """Schema for bulk lead operation results"""
    created_count: int = 0
    updated_count: int = 0
    failed_count: int = 0
    created_items: List[LeadResponse] = Field(default_factory=list)
    updated_items: List[LeadResponse] = Field(default_factory=list)
    failed_items: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time_ms: Optional[float] = None


# Lead Conversion Schemas

class LeadConversionCreate(BaseModel):
    """Schema for lead conversion"""
    create_customer: bool = Field(default=True)
    create_opportunity: bool = Field(default=True)
    create_contact: bool = Field(default=True)
    
    # Customer details (if creating customer)
    customer_name: Optional[str] = None
    customer_type: str = Field(default="business")
    
    # Opportunity details (if creating opportunity)
    opportunity_name: Optional[str] = None
    opportunity_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    opportunity_stage: OpportunityStage = Field(default=OpportunityStage.QUALIFICATION)
    opportunity_close_date: Optional[date] = None
    
    # Additional notes
    conversion_notes: Optional[str] = Field(None, max_length=1000)


class LeadConversionResult(BaseModel):
    """Schema for lead conversion results"""
    lead_id: str
    customer_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    contact_id: Optional[str] = None
    conversion_date: datetime
    notes: Optional[str] = None


# Error Schemas

class CRMError(BaseModel):
    """CRM-specific error response"""
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# API Response Wrappers

class CRMAPIResponse(BaseModel):
    """CRM-specific API response"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Union[
        LeadResponse, 
        OpportunityResponse,
        ContactResponse,
        ActivityResponse,
        CampaignResponse,
        CRMStatistics,
        LeadListResponse,
        OpportunityListResponse,
        ContactListResponse,
        ActivityListResponse,
        CampaignListResponse,
        LeadConversionResult
    ]] = None
    errors: Optional[List[str]] = None
    meta: Optional[Dict[str, Any]] = None