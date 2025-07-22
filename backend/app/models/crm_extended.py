from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer, Decimal, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class CRMCustomer(Base):
    __tablename__ = "crm_customers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_code = Column(String(50), unique=True, nullable=False)
    
    # 基本情報
    first_name = Column(String(100))
    last_name = Column(String(100))
    full_name = Column(String(200), nullable=False)
    company_name = Column(String(200))
    job_title = Column(String(100))
    department = Column(String(100))
    
    # 連絡先情報
    primary_email = Column(String(200), nullable=False, index=True)
    secondary_email = Column(String(200))
    primary_phone = Column(String(50))
    secondary_phone = Column(String(50))
    mobile_phone = Column(String(50))
    fax = Column(String(50))
    website = Column(String(200))
    linkedin_profile = Column(String(300))
    
    # 住所情報
    billing_address_line1 = Column(String(200))
    billing_address_line2 = Column(String(200))
    billing_city = Column(String(100))
    billing_state = Column(String(100))
    billing_postal_code = Column(String(20))
    billing_country = Column(String(100), default="Japan")
    
    mailing_address_line1 = Column(String(200))
    mailing_address_line2 = Column(String(200))
    mailing_city = Column(String(100))
    mailing_state = Column(String(100))
    mailing_postal_code = Column(String(20))
    mailing_country = Column(String(100), default="Japan")
    
    # 顧客分類・セグメント
    customer_type = Column(String(50), default="individual")  # individual, business, partner
    customer_segment = Column(String(50))  # enterprise, smb, startup
    industry = Column(String(100))
    company_size = Column(String(50))  # startup, small, medium, large, enterprise
    annual_revenue = Column(Decimal(15, 2))
    
    # CRM固有情報
    lead_source = Column(String(100))  # website, referral, campaign, trade_show
    lead_status = Column(String(50), default="new")  # new, contacted, qualified, opportunity, customer, lost
    customer_stage = Column(String(50), default="prospect")  # prospect, lead, opportunity, customer, advocate
    lifecycle_stage = Column(String(50), default="subscriber")  # subscriber, lead, mql, sql, opportunity, customer, evangelist
    
    # 営業・マーケティング
    assigned_sales_rep = Column(String, ForeignKey('users.id'))
    assigned_account_manager = Column(String, ForeignKey('users.id'))
    lead_score = Column(Integer, default=0)  # 0-100
    engagement_score = Column(Integer, default=0)  # 0-100
    
    # 購買・財務情報
    total_contract_value = Column(Decimal(15, 2), default=0)
    lifetime_value = Column(Decimal(15, 2), default=0)
    average_deal_size = Column(Decimal(12, 2), default=0)
    last_purchase_date = Column(Date)
    first_purchase_date = Column(Date)
    purchase_frequency = Column(String(50))  # weekly, monthly, quarterly, yearly
    
    # コミュニケーション設定
    email_opt_in = Column(Boolean, default=True)
    sms_opt_in = Column(Boolean, default=False)
    phone_opt_in = Column(Boolean, default=True)
    marketing_opt_in = Column(Boolean, default=True)
    preferred_contact_method = Column(String(50), default="email")  # email, phone, sms, none
    preferred_contact_time = Column(String(50))  # morning, afternoon, evening
    time_zone = Column(String(50), default="Asia/Tokyo")
    
    # ステータス・フラグ
    is_active = Column(Boolean, default=True)
    is_qualified = Column(Boolean, default=False)
    is_vip = Column(Boolean, default=False)
    is_decision_maker = Column(Boolean, default=False)
    do_not_contact = Column(Boolean, default=False)
    
    # 追加属性
    tags = Column(JSON, default=[])  # custom tags
    custom_fields = Column(JSON, default={})
    social_profiles = Column(JSON, default={})  # twitter, facebook, etc
    
    # メタデータ
    notes = Column(Text)
    description = Column(Text)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_contacted_at = Column(DateTime(timezone=True))
    last_activity_at = Column(DateTime(timezone=True))
    
    # リレーション
    sales_rep = relationship("User", foreign_keys=[assigned_sales_rep])
    account_manager = relationship("User", foreign_keys=[assigned_account_manager])
    interactions = relationship("CustomerInteraction", back_populates="customer", cascade="all, delete-orphan")
    opportunities = relationship("SalesOpportunity", back_populates="customer", cascade="all, delete-orphan")
    activities = relationship("CustomerActivity", back_populates="customer", cascade="all, delete-orphan")
    segments = relationship("CustomerSegment", secondary="customer_segment_members", back_populates="customers")

class CustomerInteraction(Base):
    __tablename__ = "customer_interactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, ForeignKey('crm_customers.id'), nullable=False)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)  # who initiated the interaction
    
    # インタラクション基本情報
    interaction_type = Column(String(50), nullable=False)  # call, email, meeting, demo, webinar, chat
    interaction_direction = Column(String(20), default="outbound")  # inbound, outbound
    subject = Column(String(300))
    
    # 詳細情報
    description = Column(Text)
    outcome = Column(String(100))  # interested, not_interested, follow_up, meeting_scheduled
    next_steps = Column(Text)
    
    # 日時・期間
    interaction_date = Column(DateTime(timezone=True), default=func.now())
    duration_minutes = Column(Integer)  # for calls, meetings
    scheduled_follow_up = Column(DateTime(timezone=True))
    
    # ステータス・評価
    status = Column(String(50), default="completed")  # scheduled, completed, cancelled, no_show
    satisfaction_rating = Column(Integer)  # 1-5
    lead_quality_score = Column(Integer)  # 1-10
    
    # メタデータ
    channel = Column(String(50))  # phone, zoom, teams, in_person, email
    campaign_id = Column(String)  # if part of a campaign
    attachments = Column(JSON, default=[])
    custom_fields = Column(JSON, default={})
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    customer = relationship("CRMCustomer", back_populates="interactions")
    user = relationship("User")

class SalesOpportunity(Base):
    __tablename__ = "sales_opportunities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_number = Column(String(100), unique=True, nullable=False)
    customer_id = Column(String, ForeignKey('crm_customers.id'), nullable=False)
    owner_id = Column(String, ForeignKey('users.id'), nullable=False)
    
    # 案件基本情報
    name = Column(String(300), nullable=False)
    description = Column(Text)
    
    # 金額・価値
    amount = Column(Decimal(15, 2))
    currency = Column(String(3), default="JPY")
    probability = Column(Integer, default=0)  # 0-100%
    weighted_amount = Column(Decimal(15, 2))  # amount * probability / 100
    
    # ステージ・ステータス
    stage = Column(String(50), default="prospecting")  # prospecting, qualification, proposal, negotiation, closed_won, closed_lost
    stage_updated_at = Column(DateTime(timezone=True))
    status = Column(String(50), default="open")  # open, won, lost, on_hold
    
    # 日程
    created_date = Column(Date, default=func.current_date())
    expected_close_date = Column(Date)
    actual_close_date = Column(Date)
    last_stage_change_date = Column(Date)
    
    # 商品・サービス
    product_category = Column(String(100))
    solution_type = Column(String(100))
    
    # 競合・意思決定
    competitors = Column(JSON, default=[])  # list of competitor names
    decision_criteria = Column(Text)
    decision_makers = Column(JSON, default=[])  # list of people involved
    budget_confirmed = Column(Boolean, default=False)
    timeline_confirmed = Column(Boolean, default=False)
    authority_confirmed = Column(Boolean, default=False)
    need_confirmed = Column(Boolean, default=False)
    
    # 失注理由（closed_lostの場合）
    loss_reason = Column(String(100))  # price, competitor, no_budget, timing, feature_gap
    loss_reason_detail = Column(Text)
    
    # 営業活動
    next_action = Column(String(300))
    next_action_date = Column(Date)
    last_activity_date = Column(Date)
    
    # メタデータ
    source = Column(String(100))  # inbound, outbound, referral, marketing
    campaign_id = Column(String)
    tags = Column(JSON, default=[])
    custom_fields = Column(JSON, default={})
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    customer = relationship("CRMCustomer", back_populates="opportunities")
    owner = relationship("User")
    activities = relationship("OpportunityActivity", back_populates="opportunity", cascade="all, delete-orphan")

class OpportunityActivity(Base):
    __tablename__ = "opportunity_activities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id = Column(String, ForeignKey('sales_opportunities.id'), nullable=False)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    
    # 活動情報
    activity_type = Column(String(50), nullable=False)  # call, email, meeting, proposal_sent, demo
    subject = Column(String(300))
    description = Column(Text)
    
    # 日時
    activity_date = Column(DateTime(timezone=True), default=func.now())
    due_date = Column(DateTime(timezone=True))
    
    # ステータス
    status = Column(String(50), default="completed")  # planned, in_progress, completed, cancelled
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    
    # 成果・結果
    outcome = Column(String(100))
    outcome_notes = Column(Text)
    
    # メタデータ
    attachments = Column(JSON, default=[])
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    opportunity = relationship("SalesOpportunity", back_populates="activities")
    user = relationship("User")

class CustomerActivity(Base):
    __tablename__ = "customer_activities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, ForeignKey('crm_customers.id'), nullable=False)
    user_id = Column(String, ForeignKey('users.id'))  # nullable for system activities
    
    # 活動情報
    activity_type = Column(String(50), nullable=False)  # task, note, call, email, meeting, webpage_visit, form_submit
    activity_category = Column(String(50))  # sales, marketing, support, system
    subject = Column(String(300))
    description = Column(Text)
    
    # 日時・ステータス
    activity_date = Column(DateTime(timezone=True), default=func.now())
    due_date = Column(DateTime(timezone=True))
    status = Column(String(50), default="completed")  # planned, in_progress, completed, cancelled, overdue
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    
    # Webアクティビティ（マーケティング）
    page_url = Column(String(500))
    referrer_url = Column(String(500))
    user_agent = Column(String(500))
    ip_address = Column(String(45))
    session_duration = Column(Integer)  # seconds
    
    # メタデータ
    source = Column(String(100))  # manual, email_campaign, website, api, import
    campaign_id = Column(String)
    attachments = Column(JSON, default=[])
    custom_fields = Column(JSON, default={})
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    customer = relationship("CRMCustomer", back_populates="activities")
    user = relationship("User")

class CustomerSegment(Base):
    __tablename__ = "customer_segments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text)
    
    # セグメント条件
    segment_type = Column(String(50), default="static")  # static, dynamic
    criteria = Column(JSON, default={})  # for dynamic segments
    
    # 統計情報
    customer_count = Column(Integer, default=0)
    total_value = Column(Decimal(15, 2), default=0)
    avg_customer_value = Column(Decimal(12, 2), default=0)
    
    # メタデータ
    color = Column(String(7), default="#007bff")  # hex color code
    is_active = Column(Boolean, default=True)
    created_by = Column(String, ForeignKey('users.id'), nullable=False)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_calculated_at = Column(DateTime(timezone=True))
    
    # リレーション
    creator = relationship("User")
    customers = relationship("CRMCustomer", secondary="customer_segment_members", back_populates="segments")

# Association table for many-to-many relationship
from sqlalchemy import Table
customer_segment_members = Table(
    'customer_segment_members',
    Base.metadata,
    Column('customer_id', String, ForeignKey('crm_customers.id'), primary_key=True),
    Column('segment_id', String, ForeignKey('customer_segments.id'), primary_key=True),
    Column('added_at', DateTime(timezone=True), default=func.now()),
    Column('added_by', String, ForeignKey('users.id'))
)

class MarketingCampaign(Base):
    __tablename__ = "marketing_campaigns"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # キャンペーン基本情報
    campaign_type = Column(String(50))  # email, social_media, ppc, content, event, webinar
    channel = Column(String(50))  # email, facebook, google, linkedin, website
    status = Column(String(50), default="draft")  # draft, active, paused, completed, cancelled
    
    # 日程
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    
    # 予算・コスト
    budget = Column(Decimal(12, 2))
    actual_cost = Column(Decimal(12, 2), default=0)
    cost_per_lead = Column(Decimal(10, 2))
    cost_per_acquisition = Column(Decimal(10, 2))
    
    # ターゲット・セグメント
    target_audience = Column(Text)
    target_segment_ids = Column(JSON, default=[])  # list of segment IDs
    
    # 成果指標
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    leads_generated = Column(Integer, default=0)
    opportunities_created = Column(Integer, default=0)
    customers_acquired = Column(Integer, default=0)
    revenue_generated = Column(Decimal(15, 2), default=0)
    
    # 計算指標
    click_through_rate = Column(Decimal(5, 4), default=0)  # CTR
    conversion_rate = Column(Decimal(5, 4), default=0)
    return_on_investment = Column(Decimal(8, 2), default=0)  # ROI
    
    # メタデータ
    created_by = Column(String, ForeignKey('users.id'), nullable=False)
    owned_by = Column(String, ForeignKey('users.id'))
    tags = Column(JSON, default=[])
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    creator = relationship("User", foreign_keys=[created_by])
    owner = relationship("User", foreign_keys=[owned_by])