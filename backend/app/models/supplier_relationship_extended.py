from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer, Decimal, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class SupplierRelationship(Base):
    __tablename__ = "supplier_relationships"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_id = Column(String, ForeignKey('suppliers.id'), nullable=False)
    relationship_manager_id = Column(String, ForeignKey('users.id'), nullable=False)
    
    # 関係基本情報
    relationship_type = Column(String(50), default="vendor")  # vendor, partner, strategic, preferred
    partnership_level = Column(String(50), default="standard")  # strategic, preferred, standard, conditional
    contract_type = Column(String(50))  # master_agreement, project_based, spot_buy, framework
    
    # 契約情報
    contract_start_date = Column(Date)
    contract_end_date = Column(Date)
    auto_renewal = Column(Boolean, default=False)
    renewal_notice_days = Column(Integer, default=30)
    
    # パフォーマンス評価
    overall_score = Column(Decimal(3, 2), default=0)  # 0-5.0
    quality_score = Column(Decimal(3, 2), default=0)  # 0-5.0
    delivery_score = Column(Decimal(3, 2), default=0)  # 0-5.0
    service_score = Column(Decimal(3, 2), default=0)  # 0-5.0
    cost_competitiveness = Column(Decimal(3, 2), default=0)  # 0-5.0
    innovation_score = Column(Decimal(3, 2), default=0)  # 0-5.0
    
    # ビジネス指標
    annual_spend = Column(Decimal(15, 2), default=0)
    spend_percentage = Column(Decimal(5, 2), default=0)  # percentage of total procurement
    cost_savings_achieved = Column(Decimal(12, 2), default=0)
    
    # リスク評価
    risk_level = Column(String(20), default="low")  # critical, high, medium, low
    business_continuity_risk = Column(String(20), default="low")
    financial_risk = Column(String(20), default="low")
    compliance_risk = Column(String(20), default="low")
    geographic_risk = Column(String(20), default="low")
    
    # 戦略的重要度
    strategic_importance = Column(String(20), default="medium")  # critical, high, medium, low
    business_impact = Column(String(20), default="medium")  # critical, high, medium, low
    substitutability = Column(String(20), default="high")  # high, medium, low
    
    # ステータス・承認
    status = Column(String(50), default="active")  # active, under_review, suspended, terminated
    approval_status = Column(String(50), default="approved")  # approved, pending, rejected
    approved_by = Column(String, ForeignKey('users.id'))
    approved_at = Column(DateTime)
    
    # 次回レビュー
    next_review_date = Column(Date)
    review_frequency_months = Column(Integer, default=12)
    
    # メタデータ
    notes = Column(Text)
    strengths = Column(JSON, default=[])
    weaknesses = Column(JSON, default=[])
    improvement_areas = Column(JSON, default=[])
    action_items = Column(JSON, default=[])
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_reviewed_at = Column(DateTime)
    
    # リレーション
    supplier = relationship("Supplier")
    relationship_manager = relationship("User", foreign_keys=[relationship_manager_id])
    approver = relationship("User", foreign_keys=[approved_by])
    performance_reviews = relationship("SupplierPerformanceReview", back_populates="supplier_relationship", cascade="all, delete-orphan")
    negotiations = relationship("SupplierNegotiation", back_populates="supplier_relationship", cascade="all, delete-orphan")

class SupplierPerformanceReview(Base):
    __tablename__ = "supplier_performance_reviews"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_relationship_id = Column(String, ForeignKey('supplier_relationships.id'), nullable=False)
    reviewer_id = Column(String, ForeignKey('users.id'), nullable=False)
    
    # レビュー基本情報
    review_period_start = Column(Date, nullable=False)
    review_period_end = Column(Date, nullable=False)
    review_type = Column(String(50), default="quarterly")  # monthly, quarterly, semi_annual, annual
    review_status = Column(String(50), default="draft")  # draft, in_review, completed, approved
    
    # 定量評価 (1-5スケール)
    quality_rating = Column(Decimal(3, 2))
    delivery_rating = Column(Decimal(3, 2))
    service_rating = Column(Decimal(3, 2))
    cost_rating = Column(Decimal(3, 2))
    innovation_rating = Column(Decimal(3, 2))
    compliance_rating = Column(Decimal(3, 2))
    communication_rating = Column(Decimal(3, 2))
    responsiveness_rating = Column(Decimal(3, 2))
    
    # 総合評価
    overall_rating = Column(Decimal(3, 2))
    overall_grade = Column(String(2))  # A+, A, B+, B, C+, C, D, F
    
    # KPI指標
    on_time_delivery_rate = Column(Decimal(5, 2))  # percentage
    quality_defect_rate = Column(Decimal(5, 4))  # percentage
    cost_variance = Column(Decimal(8, 2))  # actual vs budget
    invoice_accuracy_rate = Column(Decimal(5, 2))  # percentage
    response_time_hours = Column(Decimal(6, 2))  # average response time
    
    # 定性評価
    strengths_identified = Column(JSON, default=[])
    weaknesses_identified = Column(JSON, default=[])
    improvement_recommendations = Column(JSON, default=[])
    action_items = Column(JSON, default=[])
    
    # コメント
    quality_comments = Column(Text)
    delivery_comments = Column(Text)
    service_comments = Column(Text)
    cost_comments = Column(Text)
    general_comments = Column(Text)
    
    # 次期目標
    next_period_goals = Column(JSON, default=[])
    improvement_plan = Column(Text)
    
    # 承認
    approved_by = Column(String, ForeignKey('users.id'))
    approved_at = Column(DateTime)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime)
    
    # リレーション
    supplier_relationship = relationship("SupplierRelationship", back_populates="performance_reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    approver = relationship("User", foreign_keys=[approved_by])

class SupplierNegotiation(Base):
    __tablename__ = "supplier_negotiations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_relationship_id = Column(String, ForeignKey('supplier_relationships.id'), nullable=False)
    lead_negotiator_id = Column(String, ForeignKey('users.id'), nullable=False)
    
    # 交渉基本情報
    negotiation_title = Column(String(300), nullable=False)
    negotiation_type = Column(String(50), default="contract_renewal")  # contract_renewal, price_adjustment, terms_revision, new_contract
    description = Column(Text)
    
    # ステータス・フェーズ
    status = Column(String(50), default="preparation")  # preparation, active, on_hold, completed, cancelled
    current_phase = Column(String(50), default="planning")  # planning, proposal, negotiation, agreement, finalization
    
    # 日程
    start_date = Column(Date)
    target_completion_date = Column(Date)
    actual_completion_date = Column(Date)
    next_meeting_date = Column(Date)
    
    # 交渉目標・結果
    primary_objectives = Column(JSON, default=[])
    secondary_objectives = Column(JSON, default=[])
    minimum_acceptable_terms = Column(JSON, default=[])
    achieved_outcomes = Column(JSON, default=[])
    
    # 財務影響
    current_annual_value = Column(Decimal(15, 2))
    target_annual_value = Column(Decimal(15, 2))
    achieved_annual_value = Column(Decimal(15, 2))
    estimated_savings = Column(Decimal(12, 2))
    actual_savings = Column(Decimal(12, 2))
    
    # 主要条件
    payment_terms = Column(String(100))
    delivery_terms = Column(String(100))
    quality_requirements = Column(Text)
    service_level_agreements = Column(JSON, default=[])
    penalty_clauses = Column(JSON, default=[])
    
    # リスク・課題
    identified_risks = Column(JSON, default=[])
    mitigation_strategies = Column(JSON, default=[])
    escalation_points = Column(JSON, default=[])
    
    # 交渉チーム
    negotiation_team = Column(JSON, default=[])  # list of user IDs
    supplier_representatives = Column(JSON, default=[])
    
    # 結果評価
    success_rating = Column(Decimal(3, 2))  # 1-5
    objectives_achieved_percentage = Column(Decimal(5, 2))  # 0-100%
    relationship_impact = Column(String(20))  # positive, neutral, negative
    
    # 文書・記録
    meeting_notes = Column(JSON, default=[])
    documents_exchanged = Column(JSON, default=[])
    final_agreement_document = Column(String(500))  # file path or URL
    
    # 承認
    requires_approval = Column(Boolean, default=True)
    approved_by = Column(String, ForeignKey('users.id'))
    approved_at = Column(DateTime)
    approval_notes = Column(Text)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    supplier_relationship = relationship("SupplierRelationship", back_populates="negotiations")
    lead_negotiator = relationship("User", foreign_keys=[lead_negotiator_id])
    approver = relationship("User", foreign_keys=[approved_by])
    meetings = relationship("NegotiationMeeting", back_populates="negotiation", cascade="all, delete-orphan")

class NegotiationMeeting(Base):
    __tablename__ = "negotiation_meetings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    negotiation_id = Column(String, ForeignKey('supplier_negotiations.id'), nullable=False)
    organizer_id = Column(String, ForeignKey('users.id'), nullable=False)
    
    # ミーティング基本情報
    meeting_title = Column(String(300), nullable=False)
    meeting_type = Column(String(50), default="negotiation")  # kickoff, negotiation, review, finalization
    meeting_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer)
    location = Column(String(200))
    meeting_format = Column(String(50), default="in_person")  # in_person, virtual, hybrid
    
    # 参加者
    internal_attendees = Column(JSON, default=[])  # list of user IDs
    supplier_attendees = Column(JSON, default=[])  # list of names/roles
    
    # 議題・内容
    agenda_items = Column(JSON, default=[])
    discussion_points = Column(JSON, default=[])
    decisions_made = Column(JSON, default=[])
    action_items = Column(JSON, default=[])
    
    # 進捗・成果
    objectives_addressed = Column(JSON, default=[])
    progress_made = Column(Text)
    challenges_encountered = Column(JSON, default=[])
    next_steps = Column(JSON, default=[])
    
    # 評価
    meeting_effectiveness = Column(Decimal(3, 2))  # 1-5
    supplier_engagement = Column(Decimal(3, 2))  # 1-5
    progress_rating = Column(Decimal(3, 2))  # 1-5
    
    # 文書
    meeting_notes = Column(Text)
    presentation_files = Column(JSON, default=[])
    shared_documents = Column(JSON, default=[])
    meeting_recording_url = Column(String(500))
    
    # フォローアップ
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(Date)
    follow_up_responsible = Column(String, ForeignKey('users.id'))
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    negotiation = relationship("SupplierNegotiation", back_populates="meetings")
    organizer = relationship("User", foreign_keys=[organizer_id])
    follow_up_owner = relationship("User", foreign_keys=[follow_up_required])

class SupplierContract(Base):
    __tablename__ = "supplier_contracts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_id = Column(String, ForeignKey('suppliers.id'), nullable=False)
    contract_manager_id = Column(String, ForeignKey('users.id'), nullable=False)
    
    # 契約基本情報
    contract_number = Column(String(100), unique=True, nullable=False)
    contract_title = Column(String(300), nullable=False)
    contract_type = Column(String(50), default="purchase_agreement")  # purchase_agreement, service_agreement, nda, framework
    
    # 契約期間
    effective_date = Column(Date, nullable=False)
    expiration_date = Column(Date)
    contract_duration_months = Column(Integer)
    auto_renewal = Column(Boolean, default=False)
    renewal_notice_days = Column(Integer, default=30)
    
    # 契約価値
    contract_value = Column(Decimal(15, 2))
    currency = Column(String(3), default="JPY")
    pricing_model = Column(String(50))  # fixed, variable, cost_plus, market_based
    
    # 支払条件
    payment_terms = Column(String(100))
    payment_schedule = Column(JSON, default=[])
    early_payment_discount = Column(Decimal(5, 2))
    late_payment_penalty = Column(Decimal(5, 2))
    
    # 配送・履行条件
    delivery_terms = Column(String(100))  # FOB, CIF, DDP, etc.
    delivery_location = Column(String(200))
    lead_time_days = Column(Integer)
    minimum_order_quantity = Column(Decimal(10, 2))
    
    # 品質・コンプライアンス
    quality_standards = Column(JSON, default=[])
    compliance_requirements = Column(JSON, default=[])
    audit_rights = Column(Boolean, default=False)
    certifications_required = Column(JSON, default=[])
    
    # パフォーマンス指標
    service_level_agreements = Column(JSON, default=[])
    key_performance_indicators = Column(JSON, default=[])
    performance_bonuses = Column(JSON, default=[])
    performance_penalties = Column(JSON, default=[])
    
    # リスク・責任
    liability_cap = Column(Decimal(15, 2))
    insurance_requirements = Column(JSON, default=[])
    force_majeure_clauses = Column(JSON, default=[])
    termination_conditions = Column(JSON, default=[])
    
    # ステータス・承認
    status = Column(String(50), default="draft")  # draft, under_review, approved, active, expired, terminated
    approval_workflow = Column(JSON, default=[])
    signed_by_supplier = Column(Boolean, default=False)
    signed_by_company = Column(Boolean, default=False)
    company_signatory = Column(String, ForeignKey('users.id'))
    signing_date = Column(Date)
    
    # 文書管理
    contract_document_path = Column(String(500))
    amendment_documents = Column(JSON, default=[])
    related_documents = Column(JSON, default=[])
    
    # アラート・通知
    renewal_alert_sent = Column(Boolean, default=False)
    expiry_alert_sent = Column(Boolean, default=False)
    performance_alert_sent = Column(Boolean, default=False)
    
    # メタデータ
    confidentiality_level = Column(String(20), default="internal")  # public, internal, confidential, restricted
    tags = Column(JSON, default=[])
    notes = Column(Text)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    supplier = relationship("Supplier")
    contract_manager = relationship("User", foreign_keys=[contract_manager_id])
    company_signatory_user = relationship("User", foreign_keys=[company_signatory])
    amendments = relationship("ContractAmendment", back_populates="contract", cascade="all, delete-orphan")
    milestones = relationship("ContractMilestone", back_populates="contract", cascade="all, delete-orphan")

class ContractAmendment(Base):
    __tablename__ = "contract_amendments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String, ForeignKey('supplier_contracts.id'), nullable=False)
    amendment_number = Column(String(50), nullable=False)
    
    # 修正内容
    amendment_type = Column(String(50), default="terms_change")  # terms_change, price_adjustment, scope_change, extension
    description = Column(Text, nullable=False)
    reason = Column(Text)
    
    # 変更詳細
    changes_summary = Column(JSON, default=[])
    previous_values = Column(JSON, default=[])
    new_values = Column(JSON, default=[])
    financial_impact = Column(Decimal(12, 2))
    
    # 日程
    amendment_date = Column(Date, default=func.current_date())
    effective_date = Column(Date)
    
    # 承認
    status = Column(String(50), default="draft")  # draft, pending, approved, rejected, active
    requested_by = Column(String, ForeignKey('users.id'), nullable=False)
    approved_by = Column(String, ForeignKey('users.id'))
    approved_at = Column(DateTime)
    
    # 文書
    amendment_document_path = Column(String(500))
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    contract = relationship("SupplierContract", back_populates="amendments")
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])

class ContractMilestone(Base):
    __tablename__ = "contract_milestones"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String, ForeignKey('supplier_contracts.id'), nullable=False)
    
    # マイルストーン基本情報
    milestone_name = Column(String(200), nullable=False)
    milestone_type = Column(String(50), default="deliverable")  # deliverable, payment, review, renewal, expiry
    description = Column(Text)
    
    # 日程
    planned_date = Column(Date, nullable=False)
    actual_date = Column(Date)
    reminder_days_before = Column(Integer, default=30)
    
    # ステータス・完了
    status = Column(String(50), default="upcoming")  # upcoming, due, completed, overdue, cancelled
    completion_percentage = Column(Integer, default=0)  # 0-100
    
    # 責任者・通知
    responsible_user_id = Column(String, ForeignKey('users.id'))
    notification_sent = Column(Boolean, default=False)
    escalation_sent = Column(Boolean, default=False)
    
    # 成果物・結果
    deliverables = Column(JSON, default=[])
    completion_notes = Column(Text)
    
    # 財務影響
    financial_value = Column(Decimal(12, 2))
    payment_due = Column(Boolean, default=False)
    invoice_required = Column(Boolean, default=False)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime)
    
    # リレーション
    contract = relationship("SupplierContract", back_populates="milestones")
    responsible_user = relationship("User")