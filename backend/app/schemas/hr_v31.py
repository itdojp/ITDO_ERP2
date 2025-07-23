"""
HR API Schemas - CC02 v31.0 Phase 2

Pydantic schemas for human resources management API including:
- Employee Management
- Position/Job Management
- Payroll Processing
- Performance Management
- Leave Management
- Training & Development
- Benefits Administration
- Recruitment Management
- Employee Onboarding
- HR Analytics
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.models.hr_extended import (
    EmployeeStatus,
    EmploymentType,
    LeaveStatus,
    LeaveType,
    PayFrequency,
    PerformanceRating,
    RecruitmentStatus,
    TrainingStatus,
)

# =============================================================================
# Employee Schemas
# =============================================================================


class EmployeeBase(BaseModel):
    """Base schema for Employee."""

    organization_id: str
    user_id: str
    employee_number: Optional[str] = None
    badge_number: Optional[str] = None
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    preferred_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    nationality: Optional[str] = None
    personal_email: Optional[str] = None
    phone_personal: Optional[str] = None
    phone_mobile: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "JP"
    employment_type: EmploymentType
    hire_date: date
    probation_end_date: Optional[date] = None
    job_title: str
    department_id: Optional[str] = None
    manager_id: Optional[str] = None
    work_location: Optional[str] = None
    base_salary: Optional[Decimal] = None
    hourly_rate: Optional[Decimal] = None
    pay_frequency: Optional[PayFrequency] = None
    currency: str = "JPY"
    standard_hours_per_week: Decimal = Field(default=40, ge=0, le=168)
    work_schedule_id: Optional[str] = None
    time_zone: str = "Asia/Tokyo"
    tax_id: Optional[str] = None
    pension_number: Optional[str] = None
    health_insurance_number: Optional[str] = None
    employment_insurance_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_routing_number: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}


class EmployeeCreate(EmployeeBase):
    """Schema for creating Employee."""

    pass


class EmployeeUpdate(BaseModel):
    """Schema for updating Employee."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    preferred_name: Optional[str] = None
    personal_email: Optional[str] = None
    phone_personal: Optional[str] = None
    phone_mobile: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    job_title: Optional[str] = None
    department_id: Optional[str] = None
    manager_id: Optional[str] = None
    work_location: Optional[str] = None
    base_salary: Optional[Decimal] = None
    hourly_rate: Optional[Decimal] = None
    standard_hours_per_week: Optional[Decimal] = Field(None, ge=0, le=168)
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class EmployeeResponse(EmployeeBase):
    """Schema for Employee response."""

    id: str
    employee_status: EmployeeStatus
    termination_date: Optional[date] = None
    termination_reason: Optional[str] = None
    is_active: bool
    last_performance_review_date: Optional[date] = None
    next_performance_review_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True


# =============================================================================
# Position Schemas
# =============================================================================


class PositionBase(BaseModel):
    """Base schema for Position."""

    organization_id: str
    position_code: str
    position_title: str
    position_level: Optional[str] = None
    position_grade: Optional[str] = None
    department_id: Optional[str] = None
    reports_to_position_id: Optional[str] = None
    job_summary: Optional[str] = None
    key_responsibilities: List[str] = []
    required_qualifications: List[str] = []
    preferred_qualifications: List[str] = []
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    employment_type: Optional[EmploymentType] = None
    is_exempt: bool = False
    travel_percentage: int = Field(default=0, ge=0, le=100)
    physical_requirements: List[str] = []
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    salary_currency: str = "JPY"
    effective_date: date
    end_date: Optional[date] = None
    approved_headcount: int = Field(default=1, ge=0)


class PositionCreate(PositionBase):
    """Schema for creating Position."""

    pass


class PositionUpdate(BaseModel):
    """Schema for updating Position."""

    position_title: Optional[str] = None
    position_level: Optional[str] = None
    job_summary: Optional[str] = None
    key_responsibilities: Optional[List[str]] = None
    required_qualifications: Optional[List[str]] = None
    preferred_qualifications: Optional[List[str]] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    travel_percentage: Optional[int] = Field(None, ge=0, le=100)
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    end_date: Optional[date] = None
    approved_headcount: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class PositionResponse(PositionBase):
    """Schema for Position response."""

    id: str
    current_headcount: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str

    class Config:
        from_attributes = True


# =============================================================================
# Payroll Schemas
# =============================================================================


class PayrollRecordBase(BaseModel):
    """Base schema for Payroll Record."""

    employee_id: str
    organization_id: str
    pay_period_start: date
    pay_period_end: date
    pay_date: date
    regular_hours: Decimal = Field(default=0, ge=0)
    regular_rate: Optional[Decimal] = None
    regular_pay: Decimal = Field(default=0, ge=0)
    overtime_hours: Decimal = Field(default=0, ge=0)
    overtime_rate: Optional[Decimal] = None
    overtime_pay: Decimal = Field(default=0, ge=0)
    bonus: Decimal = Field(default=0, ge=0)
    commission: Decimal = Field(default=0, ge=0)
    allowances: Decimal = Field(default=0, ge=0)
    reimbursements: Decimal = Field(default=0, ge=0)
    gross_pay: Decimal = Field(ge=0)
    health_insurance_employee: Decimal = Field(default=0, ge=0)
    dental_insurance_employee: Decimal = Field(default=0, ge=0)
    retirement_contribution_employee: Decimal = Field(default=0, ge=0)
    other_pretax_deductions: Decimal = Field(default=0, ge=0)
    taxable_income: Optional[Decimal] = None
    federal_income_tax: Decimal = Field(default=0, ge=0)
    state_income_tax: Decimal = Field(default=0, ge=0)
    local_income_tax: Decimal = Field(default=0, ge=0)
    social_security_tax: Decimal = Field(default=0, ge=0)
    medicare_tax: Decimal = Field(default=0, ge=0)
    unemployment_tax: Decimal = Field(default=0, ge=0)
    post_tax_deductions: Decimal = Field(default=0, ge=0)
    net_pay: Decimal = Field(ge=0)
    health_insurance_employer: Decimal = Field(default=0, ge=0)
    retirement_contribution_employer: Decimal = Field(default=0, ge=0)
    payroll_tax_employer: Decimal = Field(default=0, ge=0)
    workers_comp: Decimal = Field(default=0, ge=0)
    payment_method: str = "direct_deposit"
    check_number: Optional[str] = None
    adjustments: List[Dict[str, Any]] = []
    notes: Optional[str] = None


class PayrollRecordCreate(PayrollRecordBase):
    """Schema for creating Payroll Record."""

    pass


class PayrollRecordUpdate(BaseModel):
    """Schema for updating Payroll Record."""

    bonus: Optional[Decimal] = Field(None, ge=0)
    commission: Optional[Decimal] = Field(None, ge=0)
    allowances: Optional[Decimal] = Field(None, ge=0)
    reimbursements: Optional[Decimal] = Field(None, ge=0)
    other_pretax_deductions: Optional[Decimal] = Field(None, ge=0)
    post_tax_deductions: Optional[Decimal] = Field(None, ge=0)
    payment_method: Optional[str] = None
    check_number: Optional[str] = None
    adjustments: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = None


class PayrollRecordResponse(PayrollRecordBase):
    """Schema for Payroll Record response."""

    id: str
    ytd_gross_pay: Optional[Decimal] = None
    ytd_tax_withheld: Optional[Decimal] = None
    ytd_net_pay: Optional[Decimal] = None
    is_processed: bool
    processed_date: Optional[datetime] = None
    processed_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str

    class Config:
        from_attributes = True


# =============================================================================
# Leave Request Schemas
# =============================================================================


class LeaveRequestBase(BaseModel):
    """Base schema for Leave Request."""

    employee_id: str
    organization_id: str
    leave_type: LeaveType
    start_date: date
    end_date: date
    return_date: Optional[date] = None
    reason: Optional[str] = None
    emergency_contact: Optional[str] = None
    work_coverage_plan: Optional[str] = None
    is_medical_leave: bool = False
    doctor_certificate_required: bool = False
    is_paid: bool = True
    attachments: List[Dict[str, str]] = []
    notes: Optional[str] = None

    @validator("end_date")
    def validate_end_date(cls, v, values):
        if "start_date" in values and v < values["start_date"]:
            raise ValueError("End date must be after start date")
        return v


class LeaveRequestCreate(LeaveRequestBase):
    """Schema for creating Leave Request."""

    pass


class LeaveRequestUpdate(BaseModel):
    """Schema for updating Leave Request."""

    return_date: Optional[date] = None
    reason: Optional[str] = None
    emergency_contact: Optional[str] = None
    work_coverage_plan: Optional[str] = None
    doctor_certificate_received: Optional[bool] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    actual_return_date: Optional[date] = None
    notes: Optional[str] = None


class LeaveRequestResponse(LeaveRequestBase):
    """Schema for Leave Request response."""

    id: str
    total_days: Decimal
    status: LeaveStatus
    requested_date: datetime
    approved_by: Optional[str] = None
    approved_date: Optional[datetime] = None
    approval_notes: Optional[str] = None
    doctor_certificate_received: bool
    fitness_for_duty_required: bool
    balance_before: Optional[Decimal] = None
    balance_after: Optional[Decimal] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    actual_return_date: Optional[date] = None
    actual_days_taken: Optional[Decimal] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# Performance Review Schemas
# =============================================================================


class PerformanceReviewBase(BaseModel):
    """Base schema for Performance Review."""

    employee_id: str
    organization_id: str
    review_period_start: date
    review_period_end: date
    review_type: str = "annual"
    reviewer_id: str
    second_reviewer_id: Optional[str] = None
    overall_rating: Optional[PerformanceRating] = None
    job_knowledge_rating: Optional[PerformanceRating] = None
    job_knowledge_comments: Optional[str] = None
    quality_of_work_rating: Optional[PerformanceRating] = None
    quality_of_work_comments: Optional[str] = None
    productivity_rating: Optional[PerformanceRating] = None
    productivity_comments: Optional[str] = None
    communication_rating: Optional[PerformanceRating] = None
    communication_comments: Optional[str] = None
    teamwork_rating: Optional[PerformanceRating] = None
    teamwork_comments: Optional[str] = None
    leadership_rating: Optional[PerformanceRating] = None
    leadership_comments: Optional[str] = None
    goals_achieved: List[str] = []
    goals_missed: List[str] = []
    development_areas: List[str] = []
    development_plan: Optional[str] = None
    next_review_goals: List[str] = []
    promotion_readiness: Optional[str] = None
    career_interests: List[str] = []
    suggested_next_roles: List[str] = []
    salary_increase_recommended: bool = False
    salary_increase_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    bonus_recommended: Optional[Decimal] = Field(None, ge=0)
    employee_comments: Optional[str] = None
    attachments: List[Dict[str, str]] = []
    custom_fields: Dict[str, Any] = {}


class PerformanceReviewCreate(PerformanceReviewBase):
    """Schema for creating Performance Review."""

    pass


class PerformanceReviewUpdate(BaseModel):
    """Schema for updating Performance Review."""

    overall_rating: Optional[PerformanceRating] = None
    job_knowledge_rating: Optional[PerformanceRating] = None
    job_knowledge_comments: Optional[str] = None
    quality_of_work_rating: Optional[PerformanceRating] = None
    quality_of_work_comments: Optional[str] = None
    productivity_rating: Optional[PerformanceRating] = None
    productivity_comments: Optional[str] = None
    communication_rating: Optional[PerformanceRating] = None
    communication_comments: Optional[str] = None
    teamwork_rating: Optional[PerformanceRating] = None
    teamwork_comments: Optional[str] = None
    leadership_rating: Optional[PerformanceRating] = None
    leadership_comments: Optional[str] = None
    goals_achieved: Optional[List[str]] = None
    goals_missed: Optional[List[str]] = None
    development_areas: Optional[List[str]] = None
    development_plan: Optional[str] = None
    next_review_goals: Optional[List[str]] = None
    promotion_readiness: Optional[str] = None
    salary_increase_recommended: Optional[bool] = None
    salary_increase_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    bonus_recommended: Optional[Decimal] = Field(None, ge=0)
    employee_comments: Optional[str] = None
    status: Optional[str] = None
    employee_acknowledged: Optional[bool] = None


class PerformanceReviewResponse(PerformanceReviewBase):
    """Schema for Performance Review response."""

    id: str
    overall_score: Optional[Decimal] = None
    job_knowledge_score: Optional[Decimal] = None
    quality_of_work_score: Optional[Decimal] = None
    productivity_score: Optional[Decimal] = None
    communication_score: Optional[Decimal] = None
    teamwork_score: Optional[Decimal] = None
    leadership_score: Optional[Decimal] = None
    status: str
    employee_acknowledged: bool
    employee_acknowledgment_date: Optional[datetime] = None
    review_completed_date: Optional[datetime] = None
    hr_approved_date: Optional[datetime] = None
    hr_approved_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# Training Record Schemas
# =============================================================================


class TrainingRecordBase(BaseModel):
    """Base schema for Training Record."""

    employee_id: str
    organization_id: str
    training_title: str
    training_type: Optional[str] = None
    training_category: Optional[str] = None
    training_provider: Optional[str] = None
    training_method: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    duration_hours: Optional[Decimal] = Field(None, ge=0)
    location: Optional[str] = None
    instructor: Optional[str] = None
    assessment_required: bool = False
    passing_score: Optional[Decimal] = Field(None, ge=0, le=100)
    training_cost: Optional[Decimal] = Field(None, ge=0)
    travel_cost: Optional[Decimal] = Field(None, ge=0)
    material_cost: Optional[Decimal] = Field(None, ge=0)
    follow_up_required: bool = False
    follow_up_date: Optional[date] = None
    learning_objectives: List[str] = []
    materials_provided: List[str] = []
    prerequisites: List[str] = []
    notes: Optional[str] = None


class TrainingRecordCreate(TrainingRecordBase):
    """Schema for creating Training Record."""

    pass


class TrainingRecordUpdate(BaseModel):
    """Schema for updating Training Record."""

    scheduled_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location: Optional[str] = None
    instructor: Optional[str] = None
    training_cost: Optional[Decimal] = Field(None, ge=0)
    travel_cost: Optional[Decimal] = Field(None, ge=0)
    material_cost: Optional[Decimal] = Field(None, ge=0)
    status: Optional[TrainingStatus] = None
    completion_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    assessment_score: Optional[Decimal] = Field(None, ge=0, le=100)
    certification_earned: Optional[bool] = None
    certificate_number: Optional[str] = None
    certification_expiry_date: Optional[date] = None
    employee_satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)
    knowledge_gained_rating: Optional[int] = Field(None, ge=1, le=5)
    applicability_rating: Optional[int] = Field(None, ge=1, le=5)
    employee_feedback: Optional[str] = None
    follow_up_completed: Optional[bool] = None
    notes: Optional[str] = None


class TrainingRecordResponse(TrainingRecordBase):
    """Schema for Training Record response."""

    id: str
    status: TrainingStatus
    completion_date: Optional[datetime] = None
    completion_percentage: Decimal
    assessment_score: Optional[Decimal] = None
    certification_earned: bool
    certificate_number: Optional[str] = None
    certification_expiry_date: Optional[date] = None
    total_cost: Optional[Decimal] = None
    employee_satisfaction_rating: Optional[int] = None
    knowledge_gained_rating: Optional[int] = None
    applicability_rating: Optional[int] = None
    employee_feedback: Optional[str] = None
    follow_up_completed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# Employee Benefit Schemas
# =============================================================================


class EmployeeBenefitBase(BaseModel):
    """Base schema for Employee Benefit."""

    employee_id: str
    organization_id: str
    benefit_type: str
    benefit_plan_name: str
    benefit_provider: Optional[str] = None
    coverage_level: Optional[str] = None
    dependents_covered: List[Dict[str, str]] = []
    enrollment_date: date
    effective_date: date
    termination_date: Optional[date] = None
    employee_contribution: Decimal = Field(default=0, ge=0)
    employer_contribution: Decimal = Field(default=0, ge=0)
    total_premium: Optional[Decimal] = Field(None, ge=0)
    pay_frequency: Optional[PayFrequency] = None
    deductible: Optional[Decimal] = Field(None, ge=0)
    out_of_pocket_max: Optional[Decimal] = Field(None, ge=0)
    coverage_amount: Optional[Decimal] = Field(None, ge=0)
    primary_beneficiary: Optional[str] = None
    primary_beneficiary_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    contingent_beneficiary: Optional[str] = None
    contingent_beneficiary_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    enrollment_method: Optional[str] = None
    enrollment_reason: Optional[str] = None
    plan_details: Dict[str, Any] = {}
    election_details: Dict[str, Any] = {}
    notes: Optional[str] = None


class EmployeeBenefitCreate(EmployeeBenefitBase):
    """Schema for creating Employee Benefit."""

    pass


class EmployeeBenefitUpdate(BaseModel):
    """Schema for updating Employee Benefit."""

    coverage_level: Optional[str] = None
    dependents_covered: Optional[List[Dict[str, str]]] = None
    termination_date: Optional[date] = None
    employee_contribution: Optional[Decimal] = Field(None, ge=0)
    employer_contribution: Optional[Decimal] = Field(None, ge=0)
    total_premium: Optional[Decimal] = Field(None, ge=0)
    primary_beneficiary: Optional[str] = None
    primary_beneficiary_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    contingent_beneficiary: Optional[str] = None
    contingent_beneficiary_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    plan_details: Optional[Dict[str, Any]] = None
    election_details: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class EmployeeBenefitResponse(EmployeeBenefitBase):
    """Schema for Employee Benefit response."""

    id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# Job Posting Schemas
# =============================================================================


class JobPostingBase(BaseModel):
    """Base schema for Job Posting."""

    organization_id: str
    position_id: str
    posting_title: str
    posting_description: Optional[str] = None
    internal_only: bool = False
    posted_date: Optional[date] = None
    closing_date: Optional[date] = None
    application_instructions: Optional[str] = None
    required_documents: List[str] = []
    application_deadline: Optional[date] = None
    hiring_manager_id: Optional[str] = None
    recruiter_id: Optional[str] = None
    target_fill_date: Optional[date] = None
    internal_posting: bool = True
    external_posting: bool = False
    posting_channels: List[str] = []
    salary_range_min: Optional[Decimal] = Field(None, ge=0)
    salary_range_max: Optional[Decimal] = Field(None, ge=0)
    salary_currency: str = "JPY"
    show_salary_range: bool = False
    tags: List[str] = []
    notes: Optional[str] = None


class JobPostingCreate(JobPostingBase):
    """Schema for creating Job Posting."""

    pass


class JobPostingUpdate(BaseModel):
    """Schema for updating Job Posting."""

    posting_title: Optional[str] = None
    posting_description: Optional[str] = None
    closing_date: Optional[date] = None
    application_instructions: Optional[str] = None
    required_documents: Optional[List[str]] = None
    application_deadline: Optional[date] = None
    hiring_manager_id: Optional[str] = None
    recruiter_id: Optional[str] = None
    target_fill_date: Optional[date] = None
    posting_channels: Optional[List[str]] = None
    salary_range_min: Optional[Decimal] = Field(None, ge=0)
    salary_range_max: Optional[Decimal] = Field(None, ge=0)
    show_salary_range: Optional[bool] = None
    status: Optional[RecruitmentStatus] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class JobPostingResponse(JobPostingBase):
    """Schema for Job Posting response."""

    id: str
    status: RecruitmentStatus
    filled_date: Optional[date] = None
    applications_received: int
    candidates_interviewed: int
    candidates_rejected: int
    offers_extended: int
    offers_accepted: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str

    class Config:
        from_attributes = True


# =============================================================================
# Onboarding Record Schemas
# =============================================================================


class OnboardingRecordBase(BaseModel):
    """Base schema for Onboarding Record."""

    employee_id: str
    organization_id: str
    onboarding_template_id: Optional[str] = None
    planned_start_date: date
    planned_completion_date: Optional[date] = None
    assigned_buddy_id: Optional[str] = None
    assigned_mentor_id: Optional[str] = None
    hr_coordinator_id: Optional[str] = None
    equipment_assigned: List[Dict[str, str]] = []
    system_access_granted: List[Dict[str, str]] = []
    badges_issued: List[Dict[str, str]] = []
    scheduled_trainings: List[Dict[str, Any]] = []
    custom_checklist_items: List[Dict[str, Any]] = []
    notes: Optional[str] = None


class OnboardingRecordCreate(OnboardingRecordBase):
    """Schema for creating Onboarding Record."""

    pass


class OnboardingRecordUpdate(BaseModel):
    """Schema for updating Onboarding Record."""

    actual_start_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    assigned_buddy_id: Optional[str] = None
    assigned_mentor_id: Optional[str] = None
    hr_coordinator_id: Optional[str] = None
    current_phase: Optional[str] = None
    documentation_completed: Optional[bool] = None
    it_setup_completed: Optional[bool] = None
    workspace_assigned: Optional[bool] = None
    benefits_enrollment_completed: Optional[bool] = None
    payroll_setup_completed: Optional[bool] = None
    security_training_completed: Optional[bool] = None
    role_specific_training_completed: Optional[bool] = None
    manager_meeting_completed: Optional[bool] = None
    team_introduction_completed: Optional[bool] = None
    equipment_assigned: Optional[List[Dict[str, str]]] = None
    system_access_granted: Optional[List[Dict[str, str]]] = None
    completed_trainings: Optional[List[Dict[str, Any]]] = None
    new_hire_satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)
    manager_feedback: Optional[str] = None
    hr_feedback: Optional[str] = None
    new_hire_feedback: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class OnboardingRecordResponse(OnboardingRecordBase):
    """Schema for Onboarding Record response."""

    id: str
    actual_start_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    overall_completion_percentage: Decimal
    current_phase: Optional[str] = None
    documentation_completed: bool
    it_setup_completed: bool
    workspace_assigned: bool
    benefits_enrollment_completed: bool
    payroll_setup_completed: bool
    security_training_completed: bool
    role_specific_training_completed: bool
    manager_meeting_completed: bool
    team_introduction_completed: bool
    completed_trainings: List[Dict[str, Any]]
    new_hire_satisfaction_rating: Optional[int] = None
    manager_feedback: Optional[str] = None
    hr_feedback: Optional[str] = None
    new_hire_feedback: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# HR Analytics Schemas
# =============================================================================


class HRAnalyticsResponse(BaseModel):
    """Schema for HR Analytics response."""

    id: str
    organization_id: str
    period_start: date
    period_end: date
    period_type: str
    total_employees: int
    active_employees: int
    full_time_employees: int
    part_time_employees: int
    contract_employees: int
    new_hires: int
    positions_filled: int
    open_positions: int
    time_to_fill_average: Optional[Decimal] = None
    cost_per_hire: Optional[Decimal] = None
    voluntary_terminations: int
    involuntary_terminations: int
    total_terminations: int
    turnover_rate: Decimal
    voluntary_turnover_rate: Decimal
    retention_rate: Decimal
    retention_rate_new_hire_90_day: Optional[Decimal] = None
    retention_rate_new_hire_1_year: Optional[Decimal] = None
    performance_review_completion_rate: Decimal
    average_performance_rating: Optional[Decimal] = None
    high_performers_percentage: Optional[Decimal] = None
    improvement_plans_active: int
    training_completion_rate: Decimal
    average_training_hours_per_employee: Optional[Decimal] = None
    training_cost_per_employee: Optional[Decimal] = None
    certification_completion_rate: Optional[Decimal] = None
    average_salary: Decimal
    median_salary: Optional[Decimal] = None
    payroll_cost_total: Decimal
    benefits_cost_total: Optional[Decimal] = None
    total_compensation_cost: Optional[Decimal] = None
    absenteeism_rate: Optional[Decimal] = None
    average_sick_days_per_employee: Optional[Decimal] = None
    leave_usage_rate: Optional[Decimal] = None
    overtime_hours_total: Optional[Decimal] = None
    diversity_metrics: Dict[str, Any]
    employee_satisfaction_score: Optional[Decimal] = None
    employee_engagement_score: Optional[Decimal] = None
    employee_net_promoter_score: Optional[Decimal] = None
    safety_incidents: int
    compliance_training_completion_rate: Optional[Decimal] = None
    policy_violations: int
    calculated_date: Optional[datetime] = None
    calculated_by: Optional[str] = None
    data_sources: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Analysis and Report Schemas
# =============================================================================


class EmployeeTenureAnalysis(BaseModel):
    """Schema for employee tenure analysis."""

    employee_id: str
    hire_date: date
    tenure_days: int
    tenure_months: float
    tenure_years: float
    service_milestones: List[str]
    is_probationary: bool
    probation_end_date: Optional[date] = None


class LeaveBalanceSummary(BaseModel):
    """Schema for leave balance summary."""

    employee_id: str
    as_of_date: date
    leave_balances: Dict[str, Dict[str, Any]]


class PerformanceTrends(BaseModel):
    """Schema for performance trends analysis."""

    employee_id: str
    trend_period_years: int
    total_reviews: int
    trend_direction: str  # improving, declining, stable
    average_score: float
    performance_history: List[Dict[str, Any]]


class TrainingHistory(BaseModel):
    """Schema for employee training history."""

    employee_id: str
    total_trainings: int
    completed_trainings: int
    total_training_hours: float
    active_certifications: int
    training_by_category: Dict[str, List[Dict[str, Any]]]
    certifications: Optional[List[Dict[str, Any]]] = None


class PayrollSummary(BaseModel):
    """Schema for payroll summary report."""

    organization_id: str
    period: str
    total_employees_paid: int
    total_payroll_records: int
    total_gross_pay: float
    total_net_pay: float
    total_taxes_withheld: float
    average_gross_pay: float
    average_net_pay: float


class OrgChartNode(BaseModel):
    """Schema for organizational chart node."""

    id: str
    name: str
    title: str
    manager_id: Optional[str] = None
    department_id: Optional[str] = None
    employee_number: str


class HRDashboardMetrics(BaseModel):
    """Schema for HR dashboard metrics."""

    organization_id: str
    as_of_date: date
    current_active_employees: int
    turnover_rate: float
    retention_rate: float
    new_hires_this_period: int
    performance_review_completion_rate: float
    training_completion_rate: float
    average_salary: float
    pending_leave_requests: int
    upcoming_performance_reviews: int
    last_analytics_update: Optional[datetime] = None


# =============================================================================
# Request Schemas for Actions
# =============================================================================


class TerminateEmployeeRequest(BaseModel):
    """Schema for employee termination."""

    employee_id: str
    termination_date: date
    termination_reason: str


class ApproveLeaveRequest(BaseModel):
    """Schema for approving leave request."""

    leave_request_id: str
    approval_notes: Optional[str] = None


class PayrollCalculationRequest(BaseModel):
    """Schema for payroll calculation."""

    employee_id: str
    pay_period_start: date
    pay_period_end: date
    regular_hours: Optional[Decimal] = None
    overtime_hours: Optional[Decimal] = None


class CompleteTrainingRequest(BaseModel):
    """Schema for completing training."""

    training_id: str
    assessment_score: Optional[Decimal] = None
    certificate_number: Optional[str] = None
    certification_expiry_date: Optional[date] = None
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)
    knowledge_rating: Optional[int] = Field(None, ge=1, le=5)
    applicability_rating: Optional[int] = Field(None, ge=1, le=5)
    employee_feedback: Optional[str] = None


class PerformanceReviewCycleRequest(BaseModel):
    """Schema for creating performance review cycle."""

    organization_id: str
    review_period_start: date
    review_period_end: date
