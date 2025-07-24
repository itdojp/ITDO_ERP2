"""
CRM (Customer Relationship Management) Models - CC02 v31.0 Phase 2

Comprehensive CRM system with:
- Customer Management
- Contact Management
- Lead Management & Pipeline
- Opportunity Management
- Sales Process Management
- Account Management
- Campaign Management
- Customer Service & Support
- Sales Analytics
- Customer Communication History
"""

import uuid
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class LeadStatus(str, Enum):
    """Lead status enumeration."""

    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    CONVERTED = "converted"
    LOST = "lost"


class LeadSource(str, Enum):
    """Lead source enumeration."""

    WEBSITE = "website"
    REFERRAL = "referral"
    SOCIAL_MEDIA = "social_media"
    EMAIL_CAMPAIGN = "email_campaign"
    TRADE_SHOW = "trade_show"
    COLD_CALL = "cold_call"
    ADVERTISEMENT = "advertisement"
    PARTNER = "partner"
    OTHER = "other"


class OpportunityStage(str, Enum):
    """Opportunity stage enumeration."""

    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    NEEDS_ANALYSIS = "needs_analysis"
    VALUE_PROPOSITION = "value_proposition"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class ContactType(str, Enum):
    """Contact type enumeration."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    TECHNICAL = "technical"
    FINANCIAL = "financial"
    DECISION_MAKER = "decision_maker"
    INFLUENCER = "influencer"
    USER = "user"


class ActivityType(str, Enum):
    """Activity type enumeration."""

    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    TASK = "task"
    NOTE = "note"
    DEMO = "demo"
    PROPOSAL = "proposal"
    CONTRACT = "contract"
    FOLLOW_UP = "follow_up"


class CampaignType(str, Enum):
    """Campaign type enumeration."""

    EMAIL = "email"
    WEBINAR = "webinar"
    TRADE_SHOW = "trade_show"
    ADVERTISEMENT = "advertisement"
    DIRECT_MAIL = "direct_mail"
    SOCIAL_MEDIA = "social_media"
    CONFERENCE = "conference"
    CONTENT_MARKETING = "content_marketing"


class CampaignStatus(str, Enum):
    """Campaign status enumeration."""

    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SupportTicketStatus(str, Enum):
    """Support ticket status enumeration."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_CUSTOMER = "pending_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class SupportTicketPriority(str, Enum):
    """Support ticket priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class CustomerExtended(Base):
    """Extended Customer Management - Comprehensive customer data and relationship tracking."""

    __tablename__ = "customers_extended"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Customer identification
    customer_code = Column(String(50), nullable=False, unique=True, index=True)
    company_name = Column(String(200), nullable=False)
    legal_name = Column(String(200))
    doing_business_as = Column(String(200))

    # Industry and classification
    industry = Column(String(100))
    sub_industry = Column(String(100))
    company_size = Column(String(50))  # startup, small, medium, large, enterprise
    annual_revenue = Column(Numeric(15, 2))
    employee_count = Column(Integer)

    # Contact information
    website = Column(String(200))
    main_phone = Column(String(50))
    main_email = Column(String(200))
    main_address_line1 = Column(String(200))
    main_address_line2 = Column(String(200))
    main_city = Column(String(100))
    main_state_province = Column(String(100))
    main_postal_code = Column(String(20))
    main_country = Column(String(2), default="JP")

    # Business information
    tax_id = Column(String(50))
    registration_number = Column(String(50))
    credit_limit = Column(Numeric(15, 2))
    payment_terms = Column(String(50))
    preferred_currency = Column(String(3), default="JPY")

    # Relationship management
    account_manager_id = Column(String, ForeignKey("users.id"))
    customer_success_manager_id = Column(String, ForeignKey("users.id"))
    sales_rep_id = Column(String, ForeignKey("users.id"))

    # Customer lifecycle
    acquisition_date = Column(Date)
    first_purchase_date = Column(Date)
    last_purchase_date = Column(Date)
    churn_date = Column(Date)
    churn_reason = Column(String(500))

    # Customer value metrics
    lifetime_value = Column(Numeric(15, 2))
    average_order_value = Column(Numeric(12, 2))
    total_orders = Column(Integer, default=0)
    total_revenue = Column(Numeric(15, 2), default=0)

    # Customer health and satisfaction
    health_score = Column(Numeric(4, 2))  # 0.00 to 5.00
    satisfaction_score = Column(Numeric(4, 2))  # 0.00 to 5.00
    nps_score = Column(Integer)  # Net Promoter Score -100 to 100

    # Customer segmentation
    customer_tier = Column(String(20))  # bronze, silver, gold, platinum
    customer_segment = Column(String(50))
    risk_category = Column(String(20))  # low, medium, high

    # Preferences
    preferred_contact_method = Column(String(20))  # email, phone, sms, mail
    communication_frequency = Column(String(20))  # daily, weekly, monthly, quarterly
    opt_out_marketing = Column(Boolean, default=False)
    opt_out_surveys = Column(Boolean, default=False)

    # System fields
    is_active = Column(Boolean, default=True)
    is_prospect = Column(Boolean, default=False)
    is_partner = Column(Boolean, default=False)
    is_competitor = Column(Boolean, default=False)

    # Metadata
    notes = Column(Text)
    tags = Column(JSON, default=[])
    custom_fields = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))
    updated_by = Column(String, ForeignKey("users.id"))

    # Relationships
    organization = relationship("Organization")
    account_manager = relationship("User", foreign_keys=[account_manager_id])
    customer_success_manager = relationship(
        "User", foreign_keys=[customer_success_manager_id]
    )
    sales_rep = relationship("User", foreign_keys=[sales_rep_id])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    # CRM relationships
    contacts = relationship("ContactExtended", back_populates="customer")
    leads = relationship("LeadExtended", back_populates="customer")
    opportunities = relationship("OpportunityExtended", back_populates="customer")
    activities = relationship("CRMActivity", back_populates="customer")
    support_tickets = relationship("SupportTicket", back_populates="customer")


class ContactExtended(Base):
    """Extended Contact Management - Individual contact person management."""

    __tablename__ = "contacts_extended"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, ForeignKey("customers_extended.id"), nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    preferred_name = Column(String(100))
    salutation = Column(String(20))  # Mr., Ms., Dr., etc.
    suffix = Column(String(20))  # Jr., Sr., III, etc.

    # Professional information
    job_title = Column(String(200))
    department = Column(String(100))
    seniority_level = Column(String(50))  # junior, mid, senior, executive, c_level

    # Contact information
    work_email = Column(String(200))
    personal_email = Column(String(200))
    work_phone = Column(String(50))
    mobile_phone = Column(String(50))
    home_phone = Column(String(50))

    # Address (if different from company)
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100))
    state_province = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(2))

    # Social and professional networks
    linkedin_url = Column(String(300))
    twitter_handle = Column(String(100))
    other_social_profiles = Column(JSON, default={})

    # Contact preferences
    preferred_contact_method = Column(String(20))
    best_time_to_contact = Column(String(100))
    time_zone = Column(String(50))
    language_preference = Column(String(10), default="en")

    # Relationship details
    contact_type = Column(SQLEnum(ContactType), default=ContactType.PRIMARY)
    decision_making_authority = Column(String(100))
    influence_level = Column(Integer)  # 1-10 scale
    relationship_strength = Column(Integer)  # 1-10 scale

    # Engagement tracking
    last_contact_date = Column(Date)
    last_contact_method = Column(String(20))
    last_meeting_date = Column(Date)
    next_contact_date = Column(Date)

    # Personal details (for relationship building)
    birthday = Column(Date)
    anniversary = Column(Date)
    spouse_name = Column(String(200))
    children_count = Column(Integer)
    hobbies = Column(JSON, default=[])
    interests = Column(JSON, default=[])

    # System fields
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)
    is_decision_maker = Column(Boolean, default=False)
    email_bounced = Column(Boolean, default=False)
    opted_out = Column(Boolean, default=False)

    # Metadata
    notes = Column(Text)
    tags = Column(JSON, default=[])

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))

    # Relationships
    customer = relationship("CustomerExtended", back_populates="contacts")
    organization = relationship("Organization")
    creator = relationship("User", foreign_keys=[created_by])

    # Contact-related relationships
    activities = relationship("CRMActivity", back_populates="contact")


class LeadExtended(Base):
    """Extended Lead Management - Comprehensive lead tracking and nurturing."""

    __tablename__ = "leads_extended"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    customer_id = Column(String, ForeignKey("customers_extended.id"))  # If converted

    # Lead identification
    lead_number = Column(String(50), nullable=False, unique=True, index=True)

    # Personal/Company information
    first_name = Column(String(100))
    last_name = Column(String(100))
    company_name = Column(String(200))
    job_title = Column(String(200))

    # Contact information
    email = Column(String(200), nullable=False)
    phone = Column(String(50))
    mobile_phone = Column(String(50))
    website = Column(String(200))

    # Address
    address_line1 = Column(String(200))
    city = Column(String(100))
    state_province = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(2))

    # Lead qualification
    status = Column(SQLEnum(LeadStatus), default=LeadStatus.NEW)
    lead_source = Column(SQLEnum(LeadSource), nullable=False)
    source_details = Column(String(200))

    # Qualification criteria
    budget_range = Column(String(50))
    timeline = Column(String(50))
    decision_maker = Column(Boolean, default=False)
    need_identified = Column(Boolean, default=False)

    # Lead scoring
    lead_score = Column(Integer, default=0)
    demographic_score = Column(Integer, default=0)
    behavioral_score = Column(Integer, default=0)
    fit_score = Column(Integer, default=0)

    # Assignment and ownership
    assigned_to_id = Column(String, ForeignKey("users.id"))
    assigned_date = Column(DateTime)

    # Engagement tracking
    first_contact_date = Column(DateTime)
    last_contact_date = Column(DateTime)
    last_activity_date = Column(DateTime)
    next_follow_up_date = Column(DateTime)

    # Conversion tracking
    conversion_date = Column(DateTime)
    converted_opportunity_id = Column(String)
    conversion_value = Column(Numeric(12, 2))

    # Company information
    industry = Column(String(100))
    company_size = Column(String(50))
    annual_revenue = Column(Numeric(15, 2))
    employee_count = Column(Integer)

    # Interest and needs
    products_interested = Column(JSON, default=[])
    pain_points = Column(JSON, default=[])
    requirements = Column(Text)

    # Campaign tracking
    campaign_id = Column(String, ForeignKey("campaigns_extended.id"))
    utm_source = Column(String(100))
    utm_medium = Column(String(100))
    utm_campaign = Column(String(100))
    utm_content = Column(String(100))

    # System fields
    is_qualified = Column(Boolean, default=False)
    is_marketing_qualified = Column(Boolean, default=False)
    is_sales_qualified = Column(Boolean, default=False)

    # Metadata
    notes = Column(Text)
    tags = Column(JSON, default=[])
    custom_fields = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))

    # Relationships
    organization = relationship("Organization")
    customer = relationship("CustomerExtended", back_populates="leads")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    campaign = relationship("CampaignExtended")
    creator = relationship("User", foreign_keys=[created_by])

    # Lead-related relationships
    activities = relationship("CRMActivity", back_populates="lead")


class OpportunityExtended(Base):
    """Extended Opportunity Management - Sales opportunity tracking and pipeline management."""

    __tablename__ = "opportunities_extended"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, ForeignKey("customers_extended.id"), nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    lead_id = Column(
        String, ForeignKey("leads_extended.id")
    )  # Source lead if applicable

    # Opportunity identification
    opportunity_number = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Sales process
    stage = Column(SQLEnum(OpportunityStage), default=OpportunityStage.PROSPECTING)
    probability = Column(Numeric(5, 2), default=0)  # 0-100%

    # Financial details
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="JPY")
    cost = Column(Numeric(15, 2))  # Cost to deliver
    expected_margin = Column(Numeric(15, 2))
    discount_amount = Column(Numeric(15, 2), default=0)
    final_amount = Column(Numeric(15, 2))

    # Timeline
    expected_close_date = Column(Date, nullable=False)
    actual_close_date = Column(Date)

    # Sales team
    sales_rep_id = Column(String, ForeignKey("users.id"), nullable=False)
    sales_manager_id = Column(String, ForeignKey("users.id"))
    sales_engineer_id = Column(String, ForeignKey("users.id"))

    # Competition
    competitors = Column(JSON, default=[])
    competitive_position = Column(String(50))  # leading, competitive, behind
    key_differentiators = Column(JSON, default=[])

    # Products and services
    products = Column(JSON, default=[])
    services = Column(JSON, default=[])
    solution_type = Column(String(100))

    # Customer needs and pain points
    customer_needs = Column(JSON, default=[])
    pain_points = Column(JSON, default=[])
    success_criteria = Column(JSON, default=[])

    # Decision process
    decision_makers = Column(JSON, default=[])
    decision_criteria = Column(JSON, default=[])
    decision_process = Column(Text)
    budget_confirmed = Column(Boolean, default=False)
    authority_confirmed = Column(Boolean, default=False)
    need_confirmed = Column(Boolean, default=False)
    timeline_confirmed = Column(Boolean, default=False)

    # Proposal and contract
    proposal_sent_date = Column(Date)
    proposal_value = Column(Numeric(15, 2))
    contract_sent_date = Column(Date)
    contract_signed_date = Column(Date)

    # Loss analysis (if applicable)
    lost_reason = Column(String(200))
    lost_to_competitor = Column(String(200))
    lost_details = Column(Text)

    # Forecasting
    forecast_category = Column(String(20))  # commit, best_case, pipeline, omitted
    weighted_amount = Column(Numeric(15, 2))  # amount * probability

    # System fields
    is_active = Column(Boolean, default=True)
    requires_approval = Column(Boolean, default=False)
    approved_by_id = Column(String, ForeignKey("users.id"))
    approval_date = Column(DateTime)

    # Metadata
    notes = Column(Text)
    tags = Column(JSON, default=[])
    custom_fields = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))

    # Relationships
    customer = relationship("CustomerExtended", back_populates="opportunities")
    organization = relationship("Organization")
    lead = relationship("LeadExtended")
    sales_rep = relationship("User", foreign_keys=[sales_rep_id])
    sales_manager = relationship("User", foreign_keys=[sales_manager_id])
    sales_engineer = relationship("User", foreign_keys=[sales_engineer_id])
    approver = relationship("User", foreign_keys=[approved_by_id])
    creator = relationship("User", foreign_keys=[created_by])

    # Opportunity-related relationships
    activities = relationship("CRMActivity", back_populates="opportunity")


class CRMActivity(Base):
    """CRM Activity Tracking - All customer interactions and touchpoints."""

    __tablename__ = "crm_activities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Activity relationships
    customer_id = Column(String, ForeignKey("customers_extended.id"))
    contact_id = Column(String, ForeignKey("contacts_extended.id"))
    lead_id = Column(String, ForeignKey("leads_extended.id"))
    opportunity_id = Column(String, ForeignKey("opportunities_extended.id"))

    # Activity details
    activity_type = Column(SQLEnum(ActivityType), nullable=False)
    subject = Column(String(200), nullable=False)
    description = Column(Text)

    # Scheduling
    activity_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer)
    location = Column(String(200))
    is_all_day = Column(Boolean, default=False)

    # Ownership and assignment
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    assigned_to_id = Column(String, ForeignKey("users.id"))
    participants = Column(JSON, default=[])  # List of user IDs

    # Status and completion
    is_completed = Column(Boolean, default=False)
    completion_date = Column(DateTime)
    outcome = Column(String(500))

    # Follow-up
    requires_follow_up = Column(Boolean, default=False)
    follow_up_date = Column(DateTime)
    follow_up_task_id = Column(String)

    # Communication details
    direction = Column(String(20))  # inbound, outbound
    channel = Column(String(50))  # phone, email, in_person, video_call, etc.

    # Email specifics (if applicable)
    email_subject = Column(String(200))
    email_template_id = Column(String)
    email_sent_count = Column(Integer, default=0)
    email_opened = Column(Boolean, default=False)
    email_clicked = Column(Boolean, default=False)

    # Call specifics (if applicable)
    call_duration_seconds = Column(Integer)
    call_recording_url = Column(String(500))
    call_outcome = Column(String(100))  # answered, voicemail, busy, no_answer

    # Meeting specifics (if applicable)
    meeting_url = Column(String(500))
    meeting_attendees = Column(JSON, default=[])
    meeting_agenda = Column(Text)
    meeting_notes = Column(Text)

    # System fields
    is_logged_automatically = Column(Boolean, default=False)
    source_system = Column(String(50))
    external_id = Column(String(100))

    # Metadata
    attachments = Column(JSON, default=[])
    tags = Column(JSON, default=[])

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization")
    customer = relationship("CustomerExtended", back_populates="activities")
    contact = relationship("ContactExtended", back_populates="activities")
    lead = relationship("LeadExtended", back_populates="activities")
    opportunity = relationship("OpportunityExtended", back_populates="activities")
    owner = relationship("User", foreign_keys=[owner_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])


class CampaignExtended(Base):
    """Extended Campaign Management - Marketing campaign tracking and management."""

    __tablename__ = "campaigns_extended"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Campaign identification
    campaign_code = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Campaign details
    campaign_type = Column(SQLEnum(CampaignType), nullable=False)
    status = Column(SQLEnum(CampaignStatus), default=CampaignStatus.PLANNING)

    # Timeline
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    actual_start_date = Column(Date)
    actual_end_date = Column(Date)

    # Budget and costs
    budget = Column(Numeric(15, 2))
    actual_cost = Column(Numeric(15, 2), default=0)
    cost_per_lead = Column(Numeric(10, 2))
    cost_per_acquisition = Column(Numeric(10, 2))

    # Targeting
    target_audience = Column(JSON, default={})
    geographic_targeting = Column(JSON, default=[])
    demographic_targeting = Column(JSON, default={})

    # Campaign goals
    primary_goal = Column(String(100))  # lead_generation, brand_awareness, sales, etc.
    target_leads = Column(Integer)
    target_opportunities = Column(Integer)
    target_revenue = Column(Numeric(15, 2))

    # Content and messaging
    key_message = Column(Text)
    call_to_action = Column(String(200))
    landing_page_url = Column(String(500))

    # Channel details
    email_template_id = Column(String)
    social_media_accounts = Column(JSON, default=[])
    advertising_platforms = Column(JSON, default=[])

    # Results and metrics
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    click_through_rate = Column(Numeric(5, 4), default=0)  # Percentage as decimal
    leads_generated = Column(Integer, default=0)
    opportunities_created = Column(Integer, default=0)
    revenue_generated = Column(Numeric(15, 2), default=0)
    conversions = Column(Integer, default=0)
    conversion_rate = Column(Numeric(5, 4), default=0)

    # ROI calculation
    roi_percentage = Column(Numeric(8, 2))
    roas = Column(Numeric(8, 2))  # Return on ad spend

    # Campaign manager
    campaign_manager_id = Column(String, ForeignKey("users.id"))

    # System fields
    is_active = Column(Boolean, default=True)

    # Metadata
    notes = Column(Text)
    tags = Column(JSON, default=[])

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))

    # Relationships
    organization = relationship("Organization")
    campaign_manager = relationship("User", foreign_keys=[campaign_manager_id])
    creator = relationship("User", foreign_keys=[created_by])

    # Campaign-related relationships
    leads = relationship("LeadExtended", back_populates="campaign")


class SupportTicket(Base):
    """Customer Support Ticket Management - Customer service and support tracking."""

    __tablename__ = "support_tickets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, ForeignKey("customers_extended.id"), nullable=False)
    contact_id = Column(String, ForeignKey("contacts_extended.id"))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Ticket identification
    ticket_number = Column(String(50), nullable=False, unique=True, index=True)
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # Classification
    category = Column(String(100))  # technical, billing, general, feature_request
    subcategory = Column(String(100))
    product = Column(String(100))
    component = Column(String(100))

    # Priority and severity
    priority = Column(
        SQLEnum(SupportTicketPriority), default=SupportTicketPriority.MEDIUM
    )
    severity = Column(String(20))  # low, medium, high, critical

    # Status and assignment
    status = Column(SQLEnum(SupportTicketStatus), default=SupportTicketStatus.OPEN)
    assigned_to_id = Column(String, ForeignKey("users.id"))
    assigned_team = Column(String(100))

    # Reporter information
    reporter_name = Column(String(200))
    reporter_email = Column(String(200))
    reporter_phone = Column(String(50))

    # Timeline
    created_date = Column(DateTime, nullable=False)
    first_response_date = Column(DateTime)
    resolved_date = Column(DateTime)
    closed_date = Column(DateTime)

    # SLA tracking
    sla_due_date = Column(DateTime)
    sla_breached = Column(Boolean, default=False)
    response_time_minutes = Column(Integer)
    resolution_time_minutes = Column(Integer)

    # Resolution
    resolution = Column(Text)
    resolution_category = Column(String(100))
    workaround = Column(Text)

    # Customer satisfaction
    satisfaction_rating = Column(Integer)  # 1-5 scale
    satisfaction_feedback = Column(Text)

    # Escalation
    is_escalated = Column(Boolean, default=False)
    escalated_to_id = Column(String, ForeignKey("users.id"))
    escalation_reason = Column(String(500))
    escalation_date = Column(DateTime)

    # Related information
    related_tickets = Column(JSON, default=[])
    related_opportunities = Column(JSON, default=[])

    # System fields
    source = Column(String(50))  # email, phone, chat, web, api
    channel = Column(String(50))  # support_portal, direct_email, phone, chat

    # Metadata
    attachments = Column(JSON, default=[])
    tags = Column(JSON, default=[])

    # Timestamps
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("CustomerExtended", back_populates="support_tickets")
    contact = relationship("ContactExtended")
    organization = relationship("Organization")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    escalated_to = relationship("User", foreign_keys=[escalated_to_id])


class CRMAnalytics(Base):
    """CRM Analytics - Key performance indicators and metrics for CRM activities."""

    __tablename__ = "crm_analytics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Reporting period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    period_type = Column(
        String(20), default="monthly"
    )  # daily, weekly, monthly, quarterly, annual

    # Lead metrics
    leads_generated = Column(Integer, default=0)
    leads_converted = Column(Integer, default=0)
    lead_conversion_rate = Column(Numeric(5, 2), default=0)
    cost_per_lead = Column(Numeric(10, 2))

    # Opportunity metrics
    opportunities_created = Column(Integer, default=0)
    opportunities_won = Column(Integer, default=0)
    opportunities_lost = Column(Integer, default=0)
    win_rate = Column(Numeric(5, 2), default=0)
    average_deal_size = Column(Numeric(12, 2))

    # Sales metrics
    total_revenue = Column(Numeric(15, 2), default=0)
    recurring_revenue = Column(Numeric(15, 2), default=0)
    new_customer_revenue = Column(Numeric(15, 2), default=0)
    average_sales_cycle_days = Column(Numeric(8, 2))

    # Customer metrics
    new_customers = Column(Integer, default=0)
    active_customers = Column(Integer, default=0)
    churned_customers = Column(Integer, default=0)
    customer_churn_rate = Column(Numeric(5, 2), default=0)
    customer_retention_rate = Column(Numeric(5, 2), default=0)
    average_customer_lifetime_value = Column(Numeric(15, 2))

    # Activity metrics
    total_activities = Column(Integer, default=0)
    calls_made = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    meetings_held = Column(Integer, default=0)

    # Pipeline metrics
    pipeline_value = Column(Numeric(15, 2), default=0)
    weighted_pipeline_value = Column(Numeric(15, 2), default=0)
    pipeline_velocity = Column(Numeric(12, 2))

    # Support metrics
    tickets_created = Column(Integer, default=0)
    tickets_resolved = Column(Integer, default=0)
    average_resolution_time_hours = Column(Numeric(8, 2))
    customer_satisfaction_score = Column(Numeric(4, 2))

    # Campaign metrics
    campaign_roi = Column(Numeric(8, 2))
    marketing_qualified_leads = Column(Integer, default=0)
    sales_qualified_leads = Column(Integer, default=0)

    # Sales team metrics
    quota_attainment = Column(Numeric(5, 2), default=0)
    activities_per_rep = Column(Numeric(8, 2))

    # Calculation metadata
    calculated_date = Column(DateTime)
    calculated_by = Column(String, ForeignKey("users.id"))
    data_sources = Column(JSON, default=[])

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization")
    calculator = relationship("User", foreign_keys=[calculated_by])
