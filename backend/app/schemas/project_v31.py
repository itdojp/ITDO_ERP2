"""
Project Management API Schemas - CC02 v31.0 Phase 2

Pydantic schemas for project management API including:
- Project Planning & Management
- Task Management & Dependencies
- Resource Management & Allocation
- Time Tracking & Reporting
- Risk Management
- Portfolio Management
- Quality Assurance
- Collaboration Tools
- Project Analytics
- Template Management
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.models.project_extended import (
    ProjectStatus,
    TaskStatus,
    TaskPriority,
    ResourceRole,
    RiskLevel,
    RiskStatus,
    TimeEntryType,
)


# =============================================================================
# Project Schemas
# =============================================================================

class ProjectBase(BaseModel):
    """Base schema for Project."""
    
    organization_id: str
    project_code: Optional[str] = None
    name: str
    description: Optional[str] = None
    project_type: Optional[str] = None
    priority: Optional[TaskPriority] = TaskPriority.MEDIUM
    project_manager_id: Optional[str] = None
    sponsor_id: Optional[str] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    total_budget: Optional[Decimal] = Field(None, ge=0)
    currency: str = "JPY"
    estimated_hours: Optional[Decimal] = Field(None, ge=0)
    team_size: int = Field(default=1, ge=1)
    methodology: Optional[str] = None
    sprint_duration: Optional[int] = Field(None, ge=1, le=30)
    client_id: Optional[str] = None
    is_billable: bool = False
    is_confidential: bool = False
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}


class ProjectCreate(ProjectBase):
    """Schema for creating Project."""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating Project."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[str] = None
    priority: Optional[TaskPriority] = None
    project_manager_id: Optional[str] = None
    sponsor_id: Optional[str] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    total_budget: Optional[Decimal] = Field(None, ge=0)
    estimated_hours: Optional[Decimal] = Field(None, ge=0)
    team_size: Optional[int] = Field(None, ge=1)
    methodology: Optional[str] = None
    sprint_duration: Optional[int] = Field(None, ge=1, le=30)
    current_sprint: Optional[int] = Field(None, ge=1)
    total_sprints: Optional[int] = Field(None, ge=1)
    status: Optional[ProjectStatus] = None
    progress_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    quality_score: Optional[Decimal] = Field(None, ge=0, le=5)
    customer_satisfaction: Optional[Decimal] = Field(None, ge=0, le=5)
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class ProjectResponse(ProjectBase):
    """Schema for Project response."""
    
    id: str
    status: ProjectStatus
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    actual_cost: Decimal
    progress_percentage: Decimal
    completion_percentage: Decimal
    actual_hours: Decimal
    quality_score: Optional[Decimal] = None
    customer_satisfaction: Optional[Decimal] = None
    risk_level: RiskLevel
    risk_score: Decimal
    current_sprint: Optional[int] = None
    total_sprints: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True


# =============================================================================
# Task Schemas
# =============================================================================

class TaskBase(BaseModel):
    """Base schema for Task."""
    
    project_id: str
    parent_task_id: Optional[str] = None
    task_number: Optional[str] = None
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    task_type: Optional[str] = None
    assigned_to_id: Optional[str] = None
    due_date: Optional[date] = None
    start_date: Optional[date] = None
    estimated_hours: Optional[Decimal] = Field(None, ge=0)
    story_points: Optional[int] = Field(None, ge=1)
    epic_id: Optional[str] = None
    sprint_id: Optional[str] = None
    acceptance_criteria: List[str] = []
    definition_of_done: Optional[str] = None
    review_required: bool = False
    testing_required: bool = False
    is_milestone: bool = False
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}


class TaskCreate(TaskBase):
    """Schema for creating Task."""
    pass


class TaskUpdate(BaseModel):
    """Schema for updating Task."""
    
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    task_type: Optional[str] = None
    assigned_to_id: Optional[str] = None
    due_date: Optional[date] = None
    start_date: Optional[date] = None
    completion_date: Optional[date] = None
    estimated_hours: Optional[Decimal] = Field(None, ge=0)
    actual_hours: Optional[Decimal] = Field(None, ge=0)
    remaining_hours: Optional[Decimal] = Field(None, ge=0)
    progress_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    story_points: Optional[int] = Field(None, ge=1)
    status: Optional[TaskStatus] = None
    acceptance_criteria: Optional[List[str]] = None
    definition_of_done: Optional[str] = None
    is_blocked: Optional[bool] = None
    blocking_reason: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class TaskResponse(TaskBase):
    """Schema for Task response."""
    
    id: str
    status: TaskStatus
    completion_date: Optional[date] = None
    actual_hours: Decimal
    remaining_hours: Optional[Decimal] = None
    progress_percentage: Decimal
    assigned_by_id: Optional[str] = None
    reviewed_by_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    is_blocked: bool
    blocking_reason: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str

    class Config:
        from_attributes = True


# =============================================================================
# Task Dependency Schemas
# =============================================================================

class TaskDependencyBase(BaseModel):
    """Base schema for Task Dependency."""
    
    task_id: str
    dependent_task_id: str
    dependency_type: str = "finish_to_start"
    lag_days: int = Field(default=0, ge=0)
    notes: Optional[str] = None


class TaskDependencyCreate(TaskDependencyBase):
    """Schema for creating Task Dependency."""
    pass


class TaskDependencyResponse(TaskDependencyBase):
    """Schema for Task Dependency response."""
    
    id: str
    created_at: datetime
    created_by: str

    class Config:
        from_attributes = True


# =============================================================================
# Resource Management Schemas
# =============================================================================

class ProjectResourceBase(BaseModel):
    """Base schema for Project Resource."""
    
    project_id: str
    user_id: str
    role: ResourceRole
    allocation_percentage: Decimal = Field(default=100, ge=0, le=100)
    hourly_rate: Optional[Decimal] = Field(None, ge=0)
    start_date: date
    end_date: Optional[date] = None
    planned_hours: Optional[Decimal] = Field(None, ge=0)
    is_primary: bool = False
    notes: Optional[str] = None
    skills: List[str] = []


class ProjectResourceCreate(ProjectResourceBase):
    """Schema for creating Project Resource."""
    pass


class ProjectResourceUpdate(BaseModel):
    """Schema for updating Project Resource."""
    
    role: Optional[ResourceRole] = None
    allocation_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    hourly_rate: Optional[Decimal] = Field(None, ge=0)
    end_date: Optional[date] = None
    planned_hours: Optional[Decimal] = Field(None, ge=0)
    actual_hours: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None
    is_primary: Optional[bool] = None
    notes: Optional[str] = None
    skills: Optional[List[str]] = None


class ProjectResourceResponse(ProjectResourceBase):
    """Schema for Project Resource response."""
    
    id: str
    actual_hours: Decimal
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str

    class Config:
        from_attributes = True


# =============================================================================
# Time Tracking Schemas
# =============================================================================

class TimeEntryBase(BaseModel):
    """Base schema for Time Entry."""
    
    project_id: str
    task_id: Optional[str] = None
    user_id: str
    date: date
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    hours: Decimal = Field(ge=0, le=24)
    entry_type: TimeEntryType = TimeEntryType.DEVELOPMENT
    description: Optional[str] = None
    is_billable: bool = True
    billing_rate: Optional[Decimal] = Field(None, ge=0)

    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and values['start_time'] and v:
            if v <= values['start_time']:
                raise ValueError('End time must be after start time')
        return v


class TimeEntryCreate(TimeEntryBase):
    """Schema for creating Time Entry."""
    pass


class TimeEntryUpdate(BaseModel):
    """Schema for updating Time Entry."""
    
    date: Optional[date] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    hours: Optional[Decimal] = Field(None, ge=0, le=24)
    entry_type: Optional[TimeEntryType] = None
    description: Optional[str] = None
    is_billable: Optional[bool] = None
    billing_rate: Optional[Decimal] = Field(None, ge=0)


class TimeEntryResponse(TimeEntryBase):
    """Schema for Time Entry response."""
    
    id: str
    billing_amount: Optional[Decimal] = None
    is_approved: bool
    approved_by_id: Optional[str] = None
    approved_at: Optional[datetime] = None
    invoice_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# Risk Management Schemas
# =============================================================================

class ProjectRiskBase(BaseModel):
    """Base schema for Project Risk."""
    
    project_id: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    probability: Optional[Decimal] = Field(None, ge=0, le=1)
    impact: Optional[Decimal] = Field(None, ge=0, le=1)
    owner_id: Optional[str] = None
    mitigation_strategy: Optional[str] = None
    contingency_plan: Optional[str] = None
    mitigation_cost: Optional[Decimal] = Field(None, ge=0)
    identified_date: date
    target_closure_date: Optional[date] = None


class ProjectRiskCreate(ProjectRiskBase):
    """Schema for creating Project Risk."""
    pass


class ProjectRiskUpdate(BaseModel):
    """Schema for updating Project Risk."""
    
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    probability: Optional[Decimal] = Field(None, ge=0, le=1)
    impact: Optional[Decimal] = Field(None, ge=0, le=1)
    status: Optional[RiskStatus] = None
    owner_id: Optional[str] = None
    mitigation_strategy: Optional[str] = None
    contingency_plan: Optional[str] = None
    mitigation_cost: Optional[Decimal] = Field(None, ge=0)
    target_closure_date: Optional[date] = None
    actual_closure_date: Optional[date] = None
    last_reviewed_date: Optional[date] = None
    next_review_date: Optional[date] = None


class ProjectRiskResponse(ProjectRiskBase):
    """Schema for Project Risk response."""
    
    id: str
    risk_score: Optional[Decimal] = None
    risk_level: RiskLevel
    status: RiskStatus
    actual_closure_date: Optional[date] = None
    last_reviewed_date: Optional[date] = None
    next_review_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str

    class Config:
        from_attributes = True


# =============================================================================
# Milestone Schemas
# =============================================================================

class ProjectMilestoneBase(BaseModel):
    """Base schema for Project Milestone."""
    
    project_id: str
    name: str
    description: Optional[str] = None
    milestone_type: Optional[str] = None
    planned_date: date
    dependent_tasks: List[str] = []
    requires_approval: bool = False
    deliverables: List[str] = []
    success_criteria: List[str] = []


class ProjectMilestoneCreate(ProjectMilestoneBase):
    """Schema for creating Project Milestone."""
    pass


class ProjectMilestoneUpdate(BaseModel):
    """Schema for updating Project Milestone."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    milestone_type: Optional[str] = None
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None
    is_completed: Optional[bool] = None
    completion_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    dependent_tasks: Optional[List[str]] = None
    deliverables: Optional[List[str]] = None
    success_criteria: Optional[List[str]] = None


class ProjectMilestoneResponse(ProjectMilestoneBase):
    """Schema for Project Milestone response."""
    
    id: str
    actual_date: Optional[date] = None
    is_completed: bool
    completion_percentage: Decimal
    approved_by_id: Optional[str] = None
    approval_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str

    class Config:
        from_attributes = True


# =============================================================================
# Deliverable Schemas
# =============================================================================

class ProjectDeliverableBase(BaseModel):
    """Base schema for Project Deliverable."""
    
    project_id: str
    milestone_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    deliverable_type: Optional[str] = None
    due_date: Optional[date] = None
    quality_requirements: List[str] = []
    acceptance_criteria: List[str] = []
    responsible_user_id: Optional[str] = None
    reviewer_id: Optional[str] = None
    file_attachments: List[Dict[str, str]] = []
    version: str = "1.0"


class ProjectDeliverableCreate(ProjectDeliverableBase):
    """Schema for creating Project Deliverable."""
    pass


class ProjectDeliverableUpdate(BaseModel):
    """Schema for updating Project Deliverable."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    deliverable_type: Optional[str] = None
    status: Optional[str] = None
    completion_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    due_date: Optional[date] = None
    completion_date: Optional[date] = None
    delivery_date: Optional[date] = None
    quality_score: Optional[Decimal] = Field(None, ge=0, le=5)
    responsible_user_id: Optional[str] = None
    reviewer_id: Optional[str] = None
    file_attachments: Optional[List[Dict[str, str]]] = None
    version: Optional[str] = None


class ProjectDeliverableResponse(ProjectDeliverableBase):
    """Schema for Project Deliverable response."""
    
    id: str
    status: str
    completion_percentage: Decimal
    completion_date: Optional[date] = None
    delivery_date: Optional[date] = None
    quality_score: Optional[Decimal] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str

    class Config:
        from_attributes = True


# =============================================================================
# Issue Schemas
# =============================================================================

class ProjectIssueBase(BaseModel):
    """Base schema for Project Issue."""
    
    project_id: str
    task_id: Optional[str] = None
    issue_number: Optional[str] = None
    title: str
    description: Optional[str] = None
    issue_type: Optional[str] = None
    severity: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    reporter_id: str
    assigned_to_id: Optional[str] = None
    reported_date: date
    due_date: Optional[date] = None
    affects_milestone: bool = False
    affects_deliverable: bool = False
    business_impact: Optional[str] = None


class ProjectIssueCreate(ProjectIssueBase):
    """Schema for creating Project Issue."""
    pass


class ProjectIssueUpdate(BaseModel):
    """Schema for updating Project Issue."""
    
    title: Optional[str] = None
    description: Optional[str] = None
    issue_type: Optional[str] = None
    severity: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[str] = None
    resolution: Optional[str] = None
    assigned_to_id: Optional[str] = None
    due_date: Optional[date] = None
    resolved_date: Optional[date] = None
    closed_date: Optional[date] = None
    resolution_description: Optional[str] = None
    workaround: Optional[str] = None


class ProjectIssueResponse(ProjectIssueBase):
    """Schema for Project Issue response."""
    
    id: str
    status: str
    resolution: Optional[str] = None
    resolved_date: Optional[date] = None
    closed_date: Optional[date] = None
    resolution_description: Optional[str] = None
    workaround: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# Portfolio Schemas
# =============================================================================

class ProjectPortfolioBase(BaseModel):
    """Base schema for Project Portfolio."""
    
    organization_id: str
    name: str
    description: Optional[str] = None
    portfolio_manager_id: Optional[str] = None
    total_budget: Optional[Decimal] = Field(None, ge=0)
    currency: str = "JPY"
    strategic_objectives: List[str] = []
    success_metrics: List[str] = []


class ProjectPortfolioCreate(ProjectPortfolioBase):
    """Schema for creating Project Portfolio."""
    pass


class ProjectPortfolioUpdate(BaseModel):
    """Schema for updating Project Portfolio."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    portfolio_manager_id: Optional[str] = None
    total_budget: Optional[Decimal] = Field(None, ge=0)
    allocated_budget: Optional[Decimal] = Field(None, ge=0)
    strategic_objectives: Optional[List[str]] = None
    success_metrics: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ProjectPortfolioResponse(ProjectPortfolioBase):
    """Schema for Project Portfolio response."""
    
    id: str
    allocated_budget: Decimal
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str

    class Config:
        from_attributes = True


# =============================================================================
# Template Schemas
# =============================================================================

class ProjectTemplateBase(BaseModel):
    """Base schema for Project Template."""
    
    organization_id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    template_data: Dict[str, Any]
    default_duration_days: Optional[int] = Field(None, ge=1)
    default_team_size: Optional[int] = Field(None, ge=1)
    is_public: bool = False
    tags: List[str] = []


class ProjectTemplateCreate(ProjectTemplateBase):
    """Schema for creating Project Template."""
    pass


class ProjectTemplateUpdate(BaseModel):
    """Schema for updating Project Template."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    default_duration_days: Optional[int] = Field(None, ge=1)
    default_team_size: Optional[int] = Field(None, ge=1)
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None


class ProjectTemplateResponse(ProjectTemplateBase):
    """Schema for Project Template response."""
    
    id: str
    usage_count: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str

    class Config:
        from_attributes = True


# =============================================================================
# Analytics and Reporting Schemas
# =============================================================================

class ProjectDashboardMetrics(BaseModel):
    """Schema for project dashboard metrics."""
    
    project_id: str
    project_name: str
    status: str
    progress_percentage: float
    total_tasks: int
    completed_tasks: int
    task_completion_rate: float
    total_logged_hours: float
    billable_hours: float
    estimated_hours: float
    actual_hours: float
    budget_utilization: float
    high_priority_risks: int
    team_size: int
    days_remaining: Optional[int] = None
    is_on_schedule: bool
    quality_score: float


class OrganizationProjectSummary(BaseModel):
    """Schema for organization project summary."""
    
    organization_id: str
    total_active_projects: int
    project_status_distribution: Dict[str, int]
    total_resources_allocated: int
    total_budget: float
    total_actual_cost: float
    budget_utilization: float
    summary_date: datetime


class ProjectHealthScore(BaseModel):
    """Schema for project health score."""
    
    project_id: str
    overall_health_score: float
    health_status: str
    health_factors: Dict[str, Dict[str, float]]
    recommendations: List[str]


class TaskComment(BaseModel):
    """Schema for task comments."""
    
    task_id: str
    user_id: str
    comment: str
    comment_type: str = "general"
    mentions: List[str] = []


class TaskCommentResponse(TaskComment):
    """Schema for task comment response."""
    
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# Action Request Schemas
# =============================================================================

class ApproveTimeEntryRequest(BaseModel):
    """Schema for approving time entry."""
    
    entry_id: str
    approver_id: str


class UpdateRiskStatusRequest(BaseModel):
    """Schema for updating risk status."""
    
    risk_id: str
    status: RiskStatus
    notes: Optional[str] = None


class CreateProjectFromTemplateRequest(BaseModel):
    """Schema for creating project from template."""
    
    template_id: str
    project_name: str
    organization_id: str
    project_manager_id: Optional[str] = None
    planned_start_date: Optional[date] = None
    total_budget: Optional[Decimal] = Field(None, ge=0)


class BulkTaskUpdateRequest(BaseModel):
    """Schema for bulk task updates."""
    
    task_ids: List[str]
    updates: Dict[str, Any]


class ProjectCloneRequest(BaseModel):
    """Schema for cloning project."""
    
    source_project_id: str
    new_project_name: str
    include_tasks: bool = True
    include_resources: bool = False
    include_timeline: bool = False


# =============================================================================
# Filtering and Search Schemas
# =============================================================================

class ProjectFilterRequest(BaseModel):
    """Schema for project filtering."""
    
    organization_id: Optional[str] = None
    status: Optional[ProjectStatus] = None
    project_manager_id: Optional[str] = None
    priority: Optional[TaskPriority] = None
    project_type: Optional[str] = None
    start_date_from: Optional[date] = None
    end_date_to: Optional[date] = None
    is_active: Optional[bool] = None
    search_text: Optional[str] = None


class TaskFilterRequest(BaseModel):
    """Schema for task filtering."""
    
    project_id: Optional[str] = None
    assigned_to_id: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    task_type: Optional[str] = None
    is_blocked: Optional[bool] = None
    due_date_from: Optional[date] = None
    due_date_to: Optional[date] = None
    search_text: Optional[str] = None


class TimeEntryFilterRequest(BaseModel):
    """Schema for time entry filtering."""
    
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    task_id: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    is_billable: Optional[bool] = None
    is_approved: Optional[bool] = None
    entry_type: Optional[TimeEntryType] = None