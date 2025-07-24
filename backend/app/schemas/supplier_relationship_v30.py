from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SupplierRelationshipBase(BaseModel):
    supplier_id: str
    relationship_type: str = Field(
        default="vendor", regex="^(vendor|partner|strategic|preferred)$"
    )
    partnership_level: str = Field(
        default="standard", regex="^(strategic|preferred|standard|conditional)$"
    )


class SupplierRelationshipCreate(SupplierRelationshipBase):
    contract_type: Optional[str] = Field(
        None, regex="^(master_agreement|project_based|spot_buy|framework)$"
    )
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    auto_renewal: bool = False
    renewal_notice_days: int = Field(default=30, ge=1)

    # パフォーマンス評価
    overall_score: Decimal = Field(default=0, ge=0, le=5)
    quality_score: Decimal = Field(default=0, ge=0, le=5)
    delivery_score: Decimal = Field(default=0, ge=0, le=5)
    service_score: Decimal = Field(default=0, ge=0, le=5)
    cost_competitiveness: Decimal = Field(default=0, ge=0, le=5)
    innovation_score: Decimal = Field(default=0, ge=0, le=5)

    # ビジネス指標
    annual_spend: Decimal = Field(default=0, ge=0)
    spend_percentage: Decimal = Field(default=0, ge=0, le=100)
    cost_savings_achieved: Decimal = Field(default=0, ge=0)

    # リスク評価
    risk_level: str = Field(default="low", regex="^(critical|high|medium|low)$")
    business_continuity_risk: str = Field(
        default="low", regex="^(critical|high|medium|low)$"
    )
    financial_risk: str = Field(default="low", regex="^(critical|high|medium|low)$")
    compliance_risk: str = Field(default="low", regex="^(critical|high|medium|low)$")
    geographic_risk: str = Field(default="low", regex="^(critical|high|medium|low)$")

    # 戦略的重要度
    strategic_importance: str = Field(
        default="medium", regex="^(critical|high|medium|low)$"
    )
    business_impact: str = Field(default="medium", regex="^(critical|high|medium|low)$")
    substitutability: str = Field(default="high", regex="^(high|medium|low)$")

    # 次回レビュー
    next_review_date: Optional[date] = None
    review_frequency_months: int = Field(default=12, ge=1, le=60)

    # メタデータ
    notes: Optional[str] = None
    strengths: List[str] = []
    weaknesses: List[str] = []
    improvement_areas: List[str] = []
    action_items: List[str] = []


class SupplierRelationshipUpdate(BaseModel):
    relationship_type: Optional[str] = Field(
        None, regex="^(vendor|partner|strategic|preferred)$"
    )
    partnership_level: Optional[str] = Field(
        None, regex="^(strategic|preferred|standard|conditional)$"
    )
    contract_type: Optional[str] = Field(
        None, regex="^(master_agreement|project_based|spot_buy|framework)$"
    )
    contract_end_date: Optional[date] = None
    auto_renewal: Optional[bool] = None
    overall_score: Optional[Decimal] = Field(None, ge=0, le=5)
    quality_score: Optional[Decimal] = Field(None, ge=0, le=5)
    delivery_score: Optional[Decimal] = Field(None, ge=0, le=5)
    service_score: Optional[Decimal] = Field(None, ge=0, le=5)
    annual_spend: Optional[Decimal] = Field(None, ge=0)
    risk_level: Optional[str] = Field(None, regex="^(critical|high|medium|low)$")
    strategic_importance: Optional[str] = Field(
        None, regex="^(critical|high|medium|low)$"
    )
    status: Optional[str] = Field(
        None, regex="^(active|under_review|suspended|terminated)$"
    )
    next_review_date: Optional[date] = None
    notes: Optional[str] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    improvement_areas: Optional[List[str]] = None
    action_items: Optional[List[str]] = None


class SupplierRelationshipResponse(SupplierRelationshipBase):
    id: str
    relationship_manager_id: str
    contract_type: Optional[str]
    contract_start_date: Optional[date]
    contract_end_date: Optional[date]
    auto_renewal: bool
    renewal_notice_days: int
    overall_score: Decimal
    quality_score: Decimal
    delivery_score: Decimal
    service_score: Decimal
    cost_competitiveness: Decimal
    innovation_score: Decimal
    annual_spend: Decimal
    spend_percentage: Decimal
    cost_savings_achieved: Decimal
    risk_level: str
    business_continuity_risk: str
    financial_risk: str
    compliance_risk: str
    geographic_risk: str
    strategic_importance: str
    business_impact: str
    substitutability: str
    status: str
    approval_status: str
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    next_review_date: Optional[date]
    review_frequency_months: int
    notes: Optional[str]
    strengths: List[str]
    weaknesses: List[str]
    improvement_areas: List[str]
    action_items: List[str]
    created_at: datetime
    updated_at: Optional[datetime]
    last_reviewed_at: Optional[datetime]

    class Config:
        orm_mode = True


class SupplierPerformanceReviewBase(BaseModel):
    review_period_start: date
    review_period_end: date
    review_type: str = Field(
        default="quarterly", regex="^(monthly|quarterly|semi_annual|annual)$"
    )


class SupplierPerformanceReviewCreate(SupplierPerformanceReviewBase):
    supplier_relationship_id: str

    # 定量評価
    quality_rating: Optional[Decimal] = Field(None, ge=1, le=5)
    delivery_rating: Optional[Decimal] = Field(None, ge=1, le=5)
    service_rating: Optional[Decimal] = Field(None, ge=1, le=5)
    cost_rating: Optional[Decimal] = Field(None, ge=1, le=5)
    innovation_rating: Optional[Decimal] = Field(None, ge=1, le=5)
    compliance_rating: Optional[Decimal] = Field(None, ge=1, le=5)
    communication_rating: Optional[Decimal] = Field(None, ge=1, le=5)
    responsiveness_rating: Optional[Decimal] = Field(None, ge=1, le=5)

    # KPI指標
    on_time_delivery_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    quality_defect_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    cost_variance: Optional[Decimal] = None
    invoice_accuracy_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    response_time_hours: Optional[Decimal] = Field(None, ge=0)

    # 定性評価
    strengths_identified: List[str] = []
    weaknesses_identified: List[str] = []
    improvement_recommendations: List[str] = []
    action_items: List[str] = []

    # コメント
    quality_comments: Optional[str] = None
    delivery_comments: Optional[str] = None
    service_comments: Optional[str] = None
    cost_comments: Optional[str] = None
    general_comments: Optional[str] = None

    # 次期目標
    next_period_goals: List[str] = []
    improvement_plan: Optional[str] = None


class SupplierPerformanceReviewUpdate(BaseModel):
    review_status: Optional[str] = Field(
        None, regex="^(draft|in_review|completed|approved)$"
    )
    quality_rating: Optional[Decimal] = Field(None, ge=1, le=5)
    delivery_rating: Optional[Decimal] = Field(None, ge=1, le=5)
    service_rating: Optional[Decimal] = Field(None, ge=1, le=5)
    cost_rating: Optional[Decimal] = Field(None, ge=1, le=5)
    overall_rating: Optional[Decimal] = Field(None, ge=1, le=5)
    overall_grade: Optional[str] = Field(None, regex="^(A\\+|A|B\\+|B|C\\+|C|D|F)$")
    on_time_delivery_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    quality_defect_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    general_comments: Optional[str] = None
    improvement_plan: Optional[str] = None


class SupplierPerformanceReviewResponse(SupplierPerformanceReviewBase):
    id: str
    supplier_relationship_id: str
    reviewer_id: str
    review_status: str
    quality_rating: Optional[Decimal]
    delivery_rating: Optional[Decimal]
    service_rating: Optional[Decimal]
    cost_rating: Optional[Decimal]
    innovation_rating: Optional[Decimal]
    compliance_rating: Optional[Decimal]
    communication_rating: Optional[Decimal]
    responsiveness_rating: Optional[Decimal]
    overall_rating: Optional[Decimal]
    overall_grade: Optional[str]
    on_time_delivery_rate: Optional[Decimal]
    quality_defect_rate: Optional[Decimal]
    cost_variance: Optional[Decimal]
    invoice_accuracy_rate: Optional[Decimal]
    response_time_hours: Optional[Decimal]
    strengths_identified: List[str]
    weaknesses_identified: List[str]
    improvement_recommendations: List[str]
    action_items: List[str]
    quality_comments: Optional[str]
    delivery_comments: Optional[str]
    service_comments: Optional[str]
    cost_comments: Optional[str]
    general_comments: Optional[str]
    next_period_goals: List[str]
    improvement_plan: Optional[str]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        orm_mode = True


class SupplierNegotiationBase(BaseModel):
    negotiation_title: str = Field(..., min_length=1, max_length=300)
    negotiation_type: str = Field(
        default="contract_renewal",
        regex="^(contract_renewal|price_adjustment|terms_revision|new_contract)$",
    )
    description: Optional[str] = None


class SupplierNegotiationCreate(SupplierNegotiationBase):
    supplier_relationship_id: str
    start_date: Optional[date] = None
    target_completion_date: Optional[date] = None

    # 交渉目標
    primary_objectives: List[str] = []
    secondary_objectives: List[str] = []
    minimum_acceptable_terms: List[str] = []

    # 財務影響
    current_annual_value: Optional[Decimal] = Field(None, ge=0)
    target_annual_value: Optional[Decimal] = Field(None, ge=0)
    estimated_savings: Optional[Decimal] = Field(None, ge=0)

    # 主要条件
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    quality_requirements: Optional[str] = None
    service_level_agreements: List[Dict[str, Any]] = []
    penalty_clauses: List[Dict[str, Any]] = []

    # リスク・課題
    identified_risks: List[str] = []
    mitigation_strategies: List[str] = []
    escalation_points: List[str] = []

    # 交渉チーム
    negotiation_team: List[str] = []  # user IDs
    supplier_representatives: List[str] = []


class SupplierNegotiationUpdate(BaseModel):
    status: Optional[str] = Field(
        None, regex="^(preparation|active|on_hold|completed|cancelled)$"
    )
    current_phase: Optional[str] = Field(
        None, regex="^(planning|proposal|negotiation|agreement|finalization)$"
    )
    target_completion_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    next_meeting_date: Optional[date] = None
    achieved_outcomes: Optional[List[str]] = None
    achieved_annual_value: Optional[Decimal] = Field(None, ge=0)
    actual_savings: Optional[Decimal] = Field(None, ge=0)
    success_rating: Optional[Decimal] = Field(None, ge=1, le=5)
    objectives_achieved_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    relationship_impact: Optional[str] = Field(
        None, regex="^(positive|neutral|negative)$"
    )
    final_agreement_document: Optional[str] = None


class SupplierNegotiationResponse(SupplierNegotiationBase):
    id: str
    supplier_relationship_id: str
    lead_negotiator_id: str
    status: str
    current_phase: str
    start_date: Optional[date]
    target_completion_date: Optional[date]
    actual_completion_date: Optional[date]
    next_meeting_date: Optional[date]
    primary_objectives: List[str]
    secondary_objectives: List[str]
    minimum_acceptable_terms: List[str]
    achieved_outcomes: List[str]
    current_annual_value: Optional[Decimal]
    target_annual_value: Optional[Decimal]
    achieved_annual_value: Optional[Decimal]
    estimated_savings: Optional[Decimal]
    actual_savings: Optional[Decimal]
    payment_terms: Optional[str]
    delivery_terms: Optional[str]
    quality_requirements: Optional[str]
    service_level_agreements: List[Dict[str, Any]]
    penalty_clauses: List[Dict[str, Any]]
    identified_risks: List[str]
    mitigation_strategies: List[str]
    escalation_points: List[str]
    negotiation_team: List[str]
    supplier_representatives: List[str]
    success_rating: Optional[Decimal]
    objectives_achieved_percentage: Optional[Decimal]
    relationship_impact: Optional[str]
    meeting_notes: List[Dict[str, Any]]
    documents_exchanged: List[str]
    final_agreement_document: Optional[str]
    requires_approval: bool
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    approval_notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class SupplierContractBase(BaseModel):
    contract_title: str = Field(..., min_length=1, max_length=300)
    contract_type: str = Field(
        default="purchase_agreement",
        regex="^(purchase_agreement|service_agreement|nda|framework)$",
    )
    effective_date: date


class SupplierContractCreate(SupplierContractBase):
    supplier_id: str
    expiration_date: Optional[date] = None
    contract_duration_months: Optional[int] = Field(None, ge=1)
    auto_renewal: bool = False
    renewal_notice_days: int = Field(default=30, ge=1)

    # 契約価値
    contract_value: Optional[Decimal] = Field(None, ge=0)
    currency: str = "JPY"
    pricing_model: Optional[str] = Field(
        None, regex="^(fixed|variable|cost_plus|market_based)$"
    )

    # 支払条件
    payment_terms: Optional[str] = None
    payment_schedule: List[Dict[str, Any]] = []
    early_payment_discount: Decimal = Field(default=0, ge=0, le=100)
    late_payment_penalty: Decimal = Field(default=0, ge=0, le=100)

    # 配送・履行条件
    delivery_terms: Optional[str] = None
    delivery_location: Optional[str] = None
    lead_time_days: Optional[int] = Field(None, ge=0)
    minimum_order_quantity: Optional[Decimal] = Field(None, ge=0)

    # 品質・コンプライアンス
    quality_standards: List[str] = []
    compliance_requirements: List[str] = []
    audit_rights: bool = False
    certifications_required: List[str] = []

    # パフォーマンス指標
    service_level_agreements: List[Dict[str, Any]] = []
    key_performance_indicators: List[Dict[str, Any]] = []
    performance_bonuses: List[Dict[str, Any]] = []
    performance_penalties: List[Dict[str, Any]] = []

    # リスク・責任
    liability_cap: Optional[Decimal] = Field(None, ge=0)
    insurance_requirements: List[str] = []
    force_majeure_clauses: List[str] = []
    termination_conditions: List[str] = []

    # 文書管理
    contract_document_path: Optional[str] = None
    related_documents: List[str] = []

    # メタデータ
    confidentiality_level: str = Field(
        default="internal", regex="^(public|internal|confidential|restricted)$"
    )
    tags: List[str] = []
    notes: Optional[str] = None


class SupplierContractUpdate(BaseModel):
    contract_title: Optional[str] = Field(None, min_length=1, max_length=300)
    expiration_date: Optional[date] = None
    auto_renewal: Optional[bool] = None
    contract_value: Optional[Decimal] = Field(None, ge=0)
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    lead_time_days: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(
        None, regex="^(draft|under_review|approved|active|expired|terminated)$"
    )
    signed_by_supplier: Optional[bool] = None
    signed_by_company: Optional[bool] = None
    signing_date: Optional[date] = None
    contract_document_path: Optional[str] = None
    notes: Optional[str] = None


class SupplierContractResponse(SupplierContractBase):
    id: str
    contract_number: str
    supplier_id: str
    contract_manager_id: str
    expiration_date: Optional[date]
    contract_duration_months: Optional[int]
    auto_renewal: bool
    renewal_notice_days: int
    contract_value: Optional[Decimal]
    currency: str
    pricing_model: Optional[str]
    payment_terms: Optional[str]
    payment_schedule: List[Dict[str, Any]]
    early_payment_discount: Decimal
    late_payment_penalty: Decimal
    delivery_terms: Optional[str]
    delivery_location: Optional[str]
    lead_time_days: Optional[int]
    minimum_order_quantity: Optional[Decimal]
    quality_standards: List[str]
    compliance_requirements: List[str]
    audit_rights: bool
    certifications_required: List[str]
    service_level_agreements: List[Dict[str, Any]]
    key_performance_indicators: List[Dict[str, Any]]
    performance_bonuses: List[Dict[str, Any]]
    performance_penalties: List[Dict[str, Any]]
    liability_cap: Optional[Decimal]
    insurance_requirements: List[str]
    force_majeure_clauses: List[str]
    termination_conditions: List[str]
    status: str
    approval_workflow: List[Dict[str, Any]]
    signed_by_supplier: bool
    signed_by_company: bool
    company_signatory: Optional[str]
    signing_date: Optional[date]
    contract_document_path: Optional[str]
    amendment_documents: List[str]
    related_documents: List[str]
    renewal_alert_sent: bool
    expiry_alert_sent: bool
    performance_alert_sent: bool
    confidentiality_level: str
    tags: List[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class SupplierRelationshipStatsResponse(BaseModel):
    total_relationships: int
    active_relationships: int
    strategic_partnerships: int
    avg_relationship_score: Decimal
    total_annual_spend: Decimal
    cost_savings_achieved: Decimal
    contracts_expiring_soon: int
    reviews_overdue: int
    by_partnership_level: Dict[str, int]
    by_risk_level: Dict[str, int]
    top_suppliers_by_spend: List[Dict[str, Any]]
    relationship_distribution: Dict[str, int]


class SupplierPerformanceAnalyticsResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    total_suppliers_reviewed: int
    avg_overall_rating: Decimal
    avg_quality_rating: Decimal
    avg_delivery_rating: Decimal
    avg_service_rating: Decimal
    top_performing_suppliers: List[Dict[str, Any]]
    improvement_needed_suppliers: List[Dict[str, Any]]
    performance_trends: List[Dict[str, Any]]
    category_performance: Dict[str, Decimal]


class SupplierRelationshipListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[SupplierRelationshipResponse]


class SupplierPerformanceReviewListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[SupplierPerformanceReviewResponse]


class SupplierNegotiationListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[SupplierNegotiationResponse]


class SupplierContractListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[SupplierContractResponse]
