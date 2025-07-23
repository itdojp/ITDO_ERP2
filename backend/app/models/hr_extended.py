"""
HR Management Models - CC02 v31.0 Phase 2

Comprehensive human resources management system with:
- Employee Management
- Position/Job Management
- Payroll Management
- Performance Management
- Leave Management
- Training & Development
- Benefits Management
- Recruitment Management
- Employee Onboarding
- HR Analytics
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
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class EmployeeStatus(str, Enum):
    """Employee status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"
    PROBATION = "probation"
    SUSPENDED = "suspended"


class EmploymentType(str, Enum):
    """Employment type enumeration."""

    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    TEMPORARY = "temporary"
    INTERN = "intern"
    CONSULTANT = "consultant"


class PayFrequency(str, Enum):
    """Pay frequency enumeration."""

    WEEKLY = "weekly"
    BI_WEEKLY = "bi_weekly"
    SEMI_MONTHLY = "semi_monthly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class LeaveType(str, Enum):
    """Leave type enumeration."""

    ANNUAL = "annual"
    SICK = "sick"
    MATERNITY = "maternity"
    PATERNITY = "paternity"
    EMERGENCY = "emergency"
    BEREAVEMENT = "bereavement"
    STUDY = "study"
    UNPAID = "unpaid"


class LeaveStatus(str, Enum):
    """Leave request status enumeration."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class PerformanceRating(str, Enum):
    """Performance rating enumeration."""

    OUTSTANDING = "outstanding"
    EXCEEDS_EXPECTATIONS = "exceeds_expectations"
    MEETS_EXPECTATIONS = "meets_expectations"
    NEEDS_IMPROVEMENT = "needs_improvement"
    UNSATISFACTORY = "unsatisfactory"


class TrainingStatus(str, Enum):
    """Training status enumeration."""

    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class RecruitmentStatus(str, Enum):
    """Recruitment status enumeration."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    FILLED = "filled"
    CANCELLED = "cancelled"


class Employee(Base):
    """Employee Master Data - Core employee information."""

    __tablename__ = "hr_employees"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Employee identification
    employee_number = Column(String(50), nullable=False, unique=True, index=True)
    badge_number = Column(String(50))

    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    preferred_name = Column(String(100))
    date_of_birth = Column(Date)
    gender = Column(String(20))
    marital_status = Column(String(20))
    nationality = Column(String(50))

    # Contact information
    personal_email = Column(String(200))
    phone_personal = Column(String(50))
    phone_mobile = Column(String(50))
    emergency_contact_name = Column(String(200))
    emergency_contact_phone = Column(String(50))
    emergency_contact_relationship = Column(String(100))

    # Address information
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100))
    state_province = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(2), default="JP")

    # Employment information
    employment_type = Column(SQLEnum(EmploymentType), nullable=False)
    employee_status = Column(SQLEnum(EmployeeStatus), default=EmployeeStatus.ACTIVE)
    hire_date = Column(Date, nullable=False)
    probation_end_date = Column(Date)
    termination_date = Column(Date)
    termination_reason = Column(String(500))

    # Job information
    job_title = Column(String(200), nullable=False)
    department_id = Column(String, ForeignKey("departments.id"))
    manager_id = Column(String, ForeignKey("hr_employees.id"))
    work_location = Column(String(200))

    # Compensation
    base_salary = Column(Numeric(12, 2))
    hourly_rate = Column(Numeric(8, 2))
    pay_frequency = Column(SQLEnum(PayFrequency))
    currency = Column(String(3), default="JPY")

    # Work schedule
    standard_hours_per_week = Column(Numeric(5, 2), default=40)
    work_schedule_id = Column(String)
    time_zone = Column(String(50), default="Asia/Tokyo")

    # Government/Legal information
    tax_id = Column(String(50))  # Social Security Number, SIN, etc.
    pension_number = Column(String(50))
    health_insurance_number = Column(String(50))
    employment_insurance_number = Column(String(50))

    # Banking information (encrypted)
    bank_name = Column(String(200))
    bank_account_number = Column(String(50))
    bank_routing_number = Column(String(20))

    # System fields
    is_active = Column(Boolean, default=True)
    last_performance_review_date = Column(Date)
    next_performance_review_date = Column(Date)

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
    user = relationship("User", foreign_keys=[user_id])
    department = relationship("Department")
    manager = relationship("Employee", remote_side=[id])
    direct_reports = relationship("Employee", back_populates="manager")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    # HR-related relationships
    payroll_records = relationship("PayrollRecord", back_populates="employee")
    leave_requests = relationship("LeaveRequest", back_populates="employee")
    performance_reviews = relationship("PerformanceReview", back_populates="employee")
    training_records = relationship("TrainingRecord", back_populates="employee")
    benefits = relationship("EmployeeBenefit", back_populates="employee")
    onboarding_records = relationship("OnboardingRecord", back_populates="employee")


class Position(Base):
    """Position/Job Definition - Job roles and requirements."""

    __tablename__ = "hr_positions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Position identification
    position_code = Column(String(50), nullable=False, unique=True)
    position_title = Column(String(200), nullable=False)
    position_level = Column(String(50))  # junior, senior, manager, director
    position_grade = Column(String(20))

    # Organizational structure
    department_id = Column(String, ForeignKey("departments.id"))
    reports_to_position_id = Column(String, ForeignKey("hr_positions.id"))

    # Job description
    job_summary = Column(Text)
    key_responsibilities = Column(JSON, default=[])
    required_qualifications = Column(JSON, default=[])
    preferred_qualifications = Column(JSON, default=[])
    required_skills = Column(JSON, default=[])
    preferred_skills = Column(JSON, default=[])

    # Employment details
    employment_type = Column(SQLEnum(EmploymentType))
    is_exempt = Column(Boolean, default=False)  # Exempt from overtime
    travel_percentage = Column(Integer, default=0)
    physical_requirements = Column(JSON, default=[])

    # Compensation range
    salary_min = Column(Numeric(12, 2))
    salary_max = Column(Numeric(12, 2))
    salary_currency = Column(String(3), default="JPY")

    # Status and dates
    is_active = Column(Boolean, default=True)
    effective_date = Column(Date, nullable=False)
    end_date = Column(Date)

    # Headcount management
    approved_headcount = Column(Integer, default=1)
    current_headcount = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))

    # Relationships
    organization = relationship("Organization")
    department = relationship("Department")
    reports_to = relationship("Position", remote_side=[id])
    subordinate_positions = relationship("Position", back_populates="reports_to")
    creator = relationship("User", foreign_keys=[created_by])


class PayrollRecord(Base):
    """Payroll Processing - Employee compensation records."""

    __tablename__ = "hr_payroll_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = Column(String, ForeignKey("hr_employees.id"), nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Pay period
    pay_period_start = Column(Date, nullable=False)
    pay_period_end = Column(Date, nullable=False)
    pay_date = Column(Date, nullable=False)

    # Regular compensation
    regular_hours = Column(Numeric(8, 2), default=0)
    regular_rate = Column(Numeric(10, 4))
    regular_pay = Column(Numeric(12, 2), default=0)

    # Overtime
    overtime_hours = Column(Numeric(8, 2), default=0)
    overtime_rate = Column(Numeric(10, 4))
    overtime_pay = Column(Numeric(12, 2), default=0)

    # Additional compensation
    bonus = Column(Numeric(12, 2), default=0)
    commission = Column(Numeric(12, 2), default=0)
    allowances = Column(Numeric(12, 2), default=0)
    reimbursements = Column(Numeric(12, 2), default=0)

    # Gross pay
    gross_pay = Column(Numeric(12, 2), nullable=False)

    # Pre-tax deductions
    health_insurance_employee = Column(Numeric(10, 2), default=0)
    dental_insurance_employee = Column(Numeric(10, 2), default=0)
    retirement_contribution_employee = Column(Numeric(10, 2), default=0)
    other_pretax_deductions = Column(Numeric(10, 2), default=0)

    # Taxable income
    taxable_income = Column(Numeric(12, 2))

    # Tax withholdings
    federal_income_tax = Column(Numeric(10, 2), default=0)
    state_income_tax = Column(Numeric(10, 2), default=0)
    local_income_tax = Column(Numeric(10, 2), default=0)
    social_security_tax = Column(Numeric(10, 2), default=0)
    medicare_tax = Column(Numeric(10, 2), default=0)
    unemployment_tax = Column(Numeric(10, 2), default=0)

    # Post-tax deductions
    post_tax_deductions = Column(Numeric(10, 2), default=0)

    # Net pay
    net_pay = Column(Numeric(12, 2), nullable=False)

    # Employer costs
    health_insurance_employer = Column(Numeric(10, 2), default=0)
    retirement_contribution_employer = Column(Numeric(10, 2), default=0)
    payroll_tax_employer = Column(Numeric(10, 2), default=0)
    workers_comp = Column(Numeric(10, 2), default=0)

    # Year-to-date totals
    ytd_gross_pay = Column(Numeric(12, 2))
    ytd_tax_withheld = Column(Numeric(12, 2))
    ytd_net_pay = Column(Numeric(12, 2))

    # Processing status
    is_processed = Column(Boolean, default=False)
    processed_date = Column(DateTime)
    processed_by = Column(String, ForeignKey("users.id"))

    # Payment information
    payment_method = Column(String(50), default="direct_deposit")
    check_number = Column(String(20))

    # Metadata
    adjustments = Column(JSON, default=[])
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))

    # Relationships
    employee = relationship("Employee", back_populates="payroll_records")
    organization = relationship("Organization")
    processor = relationship("User", foreign_keys=[processed_by])
    creator = relationship("User", foreign_keys=[created_by])


class LeaveRequest(Base):
    """Leave Management - Employee leave requests and balances."""

    __tablename__ = "hr_leave_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = Column(String, ForeignKey("hr_employees.id"), nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Leave details
    leave_type = Column(SQLEnum(LeaveType), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    return_date = Column(Date)
    total_days = Column(Numeric(5, 2), nullable=False)

    # Request information
    reason = Column(Text)
    emergency_contact = Column(String(200))
    work_coverage_plan = Column(Text)

    # Approval workflow
    status = Column(SQLEnum(LeaveStatus), default=LeaveStatus.PENDING)
    requested_date = Column(DateTime, nullable=False)
    approved_by = Column(String, ForeignKey("hr_employees.id"))
    approved_date = Column(DateTime)
    approval_notes = Column(Text)

    # Medical leave specifics (if applicable)
    is_medical_leave = Column(Boolean, default=False)
    doctor_certificate_required = Column(Boolean, default=False)
    doctor_certificate_received = Column(Boolean, default=False)
    fitness_for_duty_required = Column(Boolean, default=False)

    # Balance impact
    balance_before = Column(Numeric(8, 2))
    balance_after = Column(Numeric(8, 2))
    is_paid = Column(Boolean, default=True)

    # Actual dates (may differ from requested)
    actual_start_date = Column(Date)
    actual_end_date = Column(Date)
    actual_return_date = Column(Date)
    actual_days_taken = Column(Numeric(5, 2))

    # Metadata
    attachments = Column(JSON, default=[])
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="leave_requests")
    organization = relationship("Organization")
    approver = relationship("Employee", foreign_keys=[approved_by])


class PerformanceReview(Base):
    """Performance Management - Employee performance evaluations."""

    __tablename__ = "hr_performance_reviews"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = Column(String, ForeignKey("hr_employees.id"), nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Review period
    review_period_start = Column(Date, nullable=False)
    review_period_end = Column(Date, nullable=False)
    review_type = Column(String(50), default="annual")  # annual, mid_year, probation, project

    # Review participants
    reviewer_id = Column(String, ForeignKey("hr_employees.id"), nullable=False)
    second_reviewer_id = Column(String, ForeignKey("hr_employees.id"))

    # Overall rating
    overall_rating = Column(SQLEnum(PerformanceRating))
    overall_score = Column(Numeric(4, 2))  # 0.00 to 5.00

    # Performance areas
    job_knowledge_rating = Column(SQLEnum(PerformanceRating))
    job_knowledge_score = Column(Numeric(4, 2))
    job_knowledge_comments = Column(Text)

    quality_of_work_rating = Column(SQLEnum(PerformanceRating))
    quality_of_work_score = Column(Numeric(4, 2))
    quality_of_work_comments = Column(Text)

    productivity_rating = Column(SQLEnum(PerformanceRating))
    productivity_score = Column(Numeric(4, 2))
    productivity_comments = Column(Text)

    communication_rating = Column(SQLEnum(PerformanceRating))
    communication_score = Column(Numeric(4, 2))
    communication_comments = Column(Text)

    teamwork_rating = Column(SQLEnum(PerformanceRating))
    teamwork_score = Column(Numeric(4, 2))
    teamwork_comments = Column(Text)

    leadership_rating = Column(SQLEnum(PerformanceRating))
    leadership_score = Column(Numeric(4, 2))
    leadership_comments = Column(Text)

    # Goals and development
    goals_achieved = Column(JSON, default=[])
    goals_missed = Column(JSON, default=[])
    development_areas = Column(JSON, default=[])
    development_plan = Column(Text)
    next_review_goals = Column(JSON, default=[])

    # Career development
    promotion_readiness = Column(String(50))  # ready, needs_development, not_ready
    career_interests = Column(JSON, default=[])
    suggested_next_roles = Column(JSON, default=[])

    # Compensation recommendations
    salary_increase_recommended = Column(Boolean, default=False)
    salary_increase_percentage = Column(Numeric(5, 2))
    bonus_recommended = Column(Numeric(10, 2))

    # Review status
    status = Column(String(50), default="draft")  # draft, completed, approved
    employee_acknowledged = Column(Boolean, default=False)
    employee_acknowledgment_date = Column(DateTime)
    employee_comments = Column(Text)

    # Completion dates
    review_completed_date = Column(DateTime)
    hr_approved_date = Column(DateTime)
    hr_approved_by = Column(String, ForeignKey("users.id"))

    # Metadata
    attachments = Column(JSON, default=[])
    custom_fields = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="performance_reviews")
    organization = relationship("Organization")
    reviewer = relationship("Employee", foreign_keys=[reviewer_id])
    second_reviewer = relationship("Employee", foreign_keys=[second_reviewer_id])
    hr_approver = relationship("User", foreign_keys=[hr_approved_by])


class TrainingRecord(Base):
    """Training & Development - Employee training and certification tracking."""

    __tablename__ = "hr_training_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = Column(String, ForeignKey("hr_employees.id"), nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Training information
    training_title = Column(String(200), nullable=False)
    training_type = Column(String(50))  # mandatory, optional, certification, skill_development
    training_category = Column(String(100))  # safety, technical, leadership, compliance
    training_provider = Column(String(200))
    training_method = Column(String(50))  # classroom, online, on_the_job, conference

    # Scheduling
    scheduled_date = Column(DateTime)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    duration_hours = Column(Numeric(6, 2))
    location = Column(String(200))
    instructor = Column(String(200))

    # Status and completion
    status = Column(SQLEnum(TrainingStatus), default=TrainingStatus.SCHEDULED)
    completion_date = Column(DateTime)
    completion_percentage = Column(Numeric(5, 2), default=0)

    # Assessment and certification
    assessment_required = Column(Boolean, default=False)
    assessment_score = Column(Numeric(5, 2))
    passing_score = Column(Numeric(5, 2))
    certification_earned = Column(Boolean, default=False)
    certificate_number = Column(String(100))
    certification_expiry_date = Column(Date)

    # Costs
    training_cost = Column(Numeric(10, 2))
    travel_cost = Column(Numeric(10, 2))
    material_cost = Column(Numeric(10, 2))
    total_cost = Column(Numeric(10, 2))

    # Effectiveness
    employee_satisfaction_rating = Column(Integer)  # 1-5 scale
    knowledge_gained_rating = Column(Integer)  # 1-5 scale
    applicability_rating = Column(Integer)  # 1-5 scale
    employee_feedback = Column(Text)

    # Follow-up
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(Date)
    follow_up_completed = Column(Boolean, default=False)

    # Metadata
    learning_objectives = Column(JSON, default=[])
    materials_provided = Column(JSON, default=[])
    prerequisites = Column(JSON, default=[])
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="training_records")
    organization = relationship("Organization")


class EmployeeBenefit(Base):
    """Benefits Management - Employee benefits enrollment and administration."""

    __tablename__ = "hr_employee_benefits"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = Column(String, ForeignKey("hr_employees.id"), nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Benefit information
    benefit_type = Column(String(50), nullable=False)  # health, dental, vision, life, disability, retirement
    benefit_plan_name = Column(String(200), nullable=False)
    benefit_provider = Column(String(200))

    # Coverage details
    coverage_level = Column(String(50))  # employee, employee_spouse, family
    dependents_covered = Column(JSON, default=[])

    # Enrollment
    enrollment_date = Column(Date, nullable=False)
    effective_date = Column(Date, nullable=False)
    termination_date = Column(Date)
    is_active = Column(Boolean, default=True)

    # Costs
    employee_contribution = Column(Numeric(10, 2), default=0)
    employer_contribution = Column(Numeric(10, 2), default=0)
    total_premium = Column(Numeric(10, 2))
    pay_frequency = Column(SQLEnum(PayFrequency))

    # Plan details
    deductible = Column(Numeric(10, 2))
    out_of_pocket_max = Column(Numeric(10, 2))
    coverage_amount = Column(Numeric(12, 2))  # For life insurance, disability

    # Beneficiary information (for life insurance)
    primary_beneficiary = Column(String(200))
    primary_beneficiary_percentage = Column(Numeric(5, 2))
    contingent_beneficiary = Column(String(200))
    contingent_beneficiary_percentage = Column(Numeric(5, 2))

    # Enrollment source
    enrollment_method = Column(String(50))  # open_enrollment, new_hire, life_event
    enrollment_reason = Column(String(200))

    # Metadata
    plan_details = Column(JSON, default={})
    election_details = Column(JSON, default={})
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="benefits")
    organization = relationship("Organization")


class JobPosting(Base):
    """Recruitment Management - Job postings and candidate tracking."""

    __tablename__ = "hr_job_postings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    position_id = Column(String, ForeignKey("hr_positions.id"), nullable=False)

    # Posting information
    posting_title = Column(String(200), nullable=False)
    posting_description = Column(Text)
    internal_only = Column(Boolean, default=False)

    # Posting status
    status = Column(SQLEnum(RecruitmentStatus), default=RecruitmentStatus.OPEN)
    posted_date = Column(Date)
    closing_date = Column(Date)
    filled_date = Column(Date)

    # Application details
    application_instructions = Column(Text)
    required_documents = Column(JSON, default=[])
    application_deadline = Column(Date)

    # Hiring information
    hiring_manager_id = Column(String, ForeignKey("hr_employees.id"))
    recruiter_id = Column(String, ForeignKey("hr_employees.id"))
    target_fill_date = Column(Date)

    # Posting channels
    internal_posting = Column(Boolean, default=True)
    external_posting = Column(Boolean, default=False)
    posting_channels = Column(JSON, default=[])  # job boards, social media, etc.

    # Compensation (displayed range)
    salary_range_min = Column(Numeric(12, 2))
    salary_range_max = Column(Numeric(12, 2))
    salary_currency = Column(String(3), default="JPY")
    show_salary_range = Column(Boolean, default=False)

    # Application statistics
    applications_received = Column(Integer, default=0)
    candidates_interviewed = Column(Integer, default=0)
    candidates_rejected = Column(Integer, default=0)
    offers_extended = Column(Integer, default=0)
    offers_accepted = Column(Integer, default=0)

    # Metadata
    tags = Column(JSON, default=[])
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))

    # Relationships
    organization = relationship("Organization")
    position = relationship("Position")
    hiring_manager = relationship("Employee", foreign_keys=[hiring_manager_id])
    recruiter = relationship("Employee", foreign_keys=[recruiter_id])
    creator = relationship("User", foreign_keys=[created_by])


class OnboardingRecord(Base):
    """Employee Onboarding - New hire onboarding process tracking."""

    __tablename__ = "hr_onboarding_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = Column(String, ForeignKey("hr_employees.id"), nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Onboarding plan
    onboarding_template_id = Column(String)
    planned_start_date = Column(Date, nullable=False)
    actual_start_date = Column(Date)
    planned_completion_date = Column(Date)
    actual_completion_date = Column(Date)

    # Assignment details
    assigned_buddy_id = Column(String, ForeignKey("hr_employees.id"))
    assigned_mentor_id = Column(String, ForeignKey("hr_employees.id"))
    hr_coordinator_id = Column(String, ForeignKey("hr_employees.id"))

    # Progress tracking
    overall_completion_percentage = Column(Numeric(5, 2), default=0)
    current_phase = Column(String(100))

    # Checklist items
    documentation_completed = Column(Boolean, default=False)
    it_setup_completed = Column(Boolean, default=False)
    workspace_assigned = Column(Boolean, default=False)
    benefits_enrollment_completed = Column(Boolean, default=False)
    payroll_setup_completed = Column(Boolean, default=False)
    security_training_completed = Column(Boolean, default=False)
    role_specific_training_completed = Column(Boolean, default=False)
    manager_meeting_completed = Column(Boolean, default=False)
    team_introduction_completed = Column(Boolean, default=False)

    # Equipment and access
    equipment_assigned = Column(JSON, default=[])
    system_access_granted = Column(JSON, default=[])
    badges_issued = Column(JSON, default=[])

    # Training schedule
    scheduled_trainings = Column(JSON, default=[])
    completed_trainings = Column(JSON, default=[])

    # Feedback and assessment
    new_hire_satisfaction_rating = Column(Integer)  # 1-5 scale
    manager_feedback = Column(Text)
    hr_feedback = Column(Text)
    new_hire_feedback = Column(Text)

    # Status
    status = Column(String(50), default="in_progress")  # not_started, in_progress, completed, delayed

    # Metadata
    custom_checklist_items = Column(JSON, default=[])
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="onboarding_records")
    organization = relationship("Organization")
    buddy = relationship("Employee", foreign_keys=[assigned_buddy_id])
    mentor = relationship("Employee", foreign_keys=[assigned_mentor_id])
    hr_coordinator = relationship("Employee", foreign_keys=[hr_coordinator_id])


class HRAnalytics(Base):
    """HR Analytics - HR metrics and key performance indicators."""

    __tablename__ = "hr_analytics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Reporting period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    period_type = Column(String(20), default="monthly")  # weekly, monthly, quarterly, annual

    # Headcount metrics
    total_employees = Column(Integer, default=0)
    active_employees = Column(Integer, default=0)
    full_time_employees = Column(Integer, default=0)
    part_time_employees = Column(Integer, default=0)
    contract_employees = Column(Integer, default=0)

    # Hiring metrics
    new_hires = Column(Integer, default=0)
    positions_filled = Column(Integer, default=0)
    open_positions = Column(Integer, default=0)
    time_to_fill_average = Column(Numeric(8, 2))  # Days
    cost_per_hire = Column(Numeric(10, 2))

    # Turnover metrics
    voluntary_terminations = Column(Integer, default=0)
    involuntary_terminations = Column(Integer, default=0)
    total_terminations = Column(Integer, default=0)
    turnover_rate = Column(Numeric(5, 2))  # Percentage
    voluntary_turnover_rate = Column(Numeric(5, 2))

    # Retention metrics
    retention_rate = Column(Numeric(5, 2))
    retention_rate_new_hire_90_day = Column(Numeric(5, 2))
    retention_rate_new_hire_1_year = Column(Numeric(5, 2))

    # Performance metrics
    performance_review_completion_rate = Column(Numeric(5, 2))
    average_performance_rating = Column(Numeric(4, 2))
    high_performers_percentage = Column(Numeric(5, 2))
    improvement_plans_active = Column(Integer, default=0)

    # Training metrics
    training_completion_rate = Column(Numeric(5, 2))
    average_training_hours_per_employee = Column(Numeric(8, 2))
    training_cost_per_employee = Column(Numeric(10, 2))
    certification_completion_rate = Column(Numeric(5, 2))

    # Compensation metrics
    average_salary = Column(Numeric(12, 2))
    median_salary = Column(Numeric(12, 2))
    payroll_cost_total = Column(Numeric(15, 2))
    benefits_cost_total = Column(Numeric(15, 2))
    total_compensation_cost = Column(Numeric(15, 2))

    # Leave and attendance
    absenteeism_rate = Column(Numeric(5, 2))
    average_sick_days_per_employee = Column(Numeric(5, 2))
    leave_usage_rate = Column(Numeric(5, 2))
    overtime_hours_total = Column(Numeric(10, 2))

    # Diversity metrics
    diversity_metrics = Column(JSON, default={})  # Gender, age, ethnicity breakdowns

    # Employee satisfaction
    employee_satisfaction_score = Column(Numeric(4, 2))
    employee_engagement_score = Column(Numeric(4, 2))
    employee_net_promoter_score = Column(Numeric(4, 2))

    # Compliance metrics
    safety_incidents = Column(Integer, default=0)
    compliance_training_completion_rate = Column(Numeric(5, 2))
    policy_violations = Column(Integer, default=0)

    # Calculation metadata
    calculated_date = Column(DateTime)
    calculated_by = Column(String, ForeignKey("users.id"))
    data_sources = Column(JSON, default=[])

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization")
    calculator = relationship("User", foreign_keys=[calculated_by])
