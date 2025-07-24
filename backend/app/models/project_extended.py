"""
Project Management Models - CC02 v31.0 Phase 2

Comprehensive project management system with:
- Project Planning & Management
- Task Management & Dependencies
- Resource Management
- Time Tracking & Reporting
- Project Collaboration
- Risk Management
- Quality Assurance
- Project Templates
- Portfolio Management
- Project Analytics
"""

import uuid
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class ProjectStatus(str, Enum):
    """Project status enumeration."""

    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class TaskStatus(str, Enum):
    """Task status enumeration."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class ResourceRole(str, Enum):
    """Resource role enumeration."""

    PROJECT_MANAGER = "project_manager"
    TEAM_LEAD = "team_lead"
    DEVELOPER = "developer"
    DESIGNER = "designer"
    TESTER = "tester"
    ANALYST = "analyst"
    ARCHITECT = "architect"
    CONSULTANT = "consultant"


class RiskLevel(str, Enum):
    """Risk level enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskStatus(str, Enum):
    """Risk status enumeration."""

    IDENTIFIED = "identified"
    ASSESSED = "assessed"
    MITIGATED = "mitigated"
    MONITORED = "monitored"
    CLOSED = "closed"


class TimeEntryType(str, Enum):
    """Time entry type enumeration."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    DESIGN = "design"
    MEETING = "meeting"
    DOCUMENTATION = "documentation"
    RESEARCH = "research"
    BUG_FIXING = "bug_fixing"
    REVIEW = "review"


class ProjectExtended(Base):
    """Extended Project Management - Enhanced project tracking and management."""

    __tablename__ = "projects_extended"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Project identification
    project_code = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    project_type = Column(String(50))  # internal, client, maintenance, research

    # Project management
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.PLANNING)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)
    project_manager_id = Column(String, ForeignKey("users.id"))
    sponsor_id = Column(String, ForeignKey("users.id"))

    # Timeline
    planned_start_date = Column(Date)
    planned_end_date = Column(Date)
    actual_start_date = Column(Date)
    actual_end_date = Column(Date)

    # Budget and costs
    total_budget = Column(Numeric(15, 2))
    actual_cost = Column(Numeric(15, 2), default=0)
    currency = Column(String(3), default="JPY")

    # Progress tracking
    progress_percentage = Column(Numeric(5, 2), default=0)
    completion_percentage = Column(Numeric(5, 2), default=0)

    # Resource allocation
    estimated_hours = Column(Numeric(10, 2))
    actual_hours = Column(Numeric(10, 2), default=0)
    team_size = Column(Integer, default=1)

    # Quality metrics
    quality_score = Column(Numeric(4, 2))  # 0.00 to 5.00
    customer_satisfaction = Column(Numeric(4, 2))  # 0.00 to 5.00

    # Risk assessment
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.LOW)
    risk_score = Column(Numeric(5, 2), default=0)

    # Methodology and process
    methodology = Column(String(50))  # agile, waterfall, hybrid
    sprint_duration = Column(Integer)  # days
    current_sprint = Column(Integer)
    total_sprints = Column(Integer)

    # Client information
    client_id = Column(String, ForeignKey("customers.id"))
    client_contact_id = Column(String)

    # Documentation
    project_charter = Column(Text)
    requirements_document = Column(Text)
    project_plan = Column(Text)

    # System fields
    is_active = Column(Boolean, default=True)
    is_billable = Column(Boolean, default=False)
    is_confidential = Column(Boolean, default=False)

    # Metadata
    tags = Column(JSON, default=[])
    custom_fields = Column(JSON, default={})
    attachments = Column(JSON, default=[])

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))
    updated_by = Column(String, ForeignKey("users.id"))

    # Relationships
    organization = relationship("Organization")
    project_manager = relationship("User", foreign_keys=[project_manager_id])
    sponsor = relationship("User", foreign_keys=[sponsor_id])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    # Project-related relationships
    tasks = relationship("TaskExtended", back_populates="project")
    resources = relationship("ProjectResource", back_populates="project")
    time_entries = relationship("TimeEntry", back_populates="project")
    risks = relationship("ProjectRisk", back_populates="project")
    milestones = relationship("ProjectMilestoneExtended", back_populates="project")
    deliverables = relationship("ProjectDeliverable", back_populates="project")
    issues = relationship("ProjectIssue", back_populates="project")


class TaskExtended(Base):
    """Extended Task Management - Enhanced task tracking and dependencies."""

    __tablename__ = "tasks_extended"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects_extended.id"), nullable=False)
    parent_task_id = Column(String, ForeignKey("tasks_extended.id"))

    # Task identification
    task_number = Column(String(50), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)

    # Task management
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.NOT_STARTED)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)
    task_type = Column(String(50))  # feature, bug, task, epic, story

    # Assignment
    assigned_to_id = Column(String, ForeignKey("users.id"))
    assigned_by_id = Column(String, ForeignKey("users.id"))

    # Timeline
    due_date = Column(Date)
    start_date = Column(Date)
    completion_date = Column(Date)

    # Effort estimation
    estimated_hours = Column(Numeric(8, 2))
    actual_hours = Column(Numeric(8, 2), default=0)
    remaining_hours = Column(Numeric(8, 2))

    # Progress
    progress_percentage = Column(Numeric(5, 2), default=0)

    # Story points (for agile)
    story_points = Column(Integer)
    epic_id = Column(String)
    sprint_id = Column(String)

    # Acceptance criteria
    acceptance_criteria = Column(JSON, default=[])
    definition_of_done = Column(Text)

    # Quality
    review_required = Column(Boolean, default=False)
    testing_required = Column(Boolean, default=False)
    reviewed_by_id = Column(String, ForeignKey("users.id"))
    reviewed_at = Column(DateTime)

    # System fields
    is_milestone = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    blocking_reason = Column(String(500))

    # Metadata
    tags = Column(JSON, default=[])
    custom_fields = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))

    # Relationships
    project = relationship("ProjectExtended", back_populates="tasks")
    parent_task = relationship("TaskExtended", remote_side=[id])
    subtasks = relationship("TaskExtended", back_populates="parent_task")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by_id])
    creator = relationship("User", foreign_keys=[created_by])

    # Task-related relationships
    dependencies = relationship(
        "TaskDependencyExtended",
        foreign_keys="[TaskDependencyExtended.task_id]",
        back_populates="task",
    )
    dependents = relationship(
        "TaskDependencyExtended",
        foreign_keys="[TaskDependencyExtended.dependent_task_id]",
        back_populates="dependent_task",
    )
    time_entries = relationship("TimeEntry", back_populates="task")
    comments = relationship("TaskComment", back_populates="task")


class TaskDependencyExtended(Base):
    """Enhanced Task Dependencies - Complex task relationship management."""

    __tablename__ = "task_dependencies_extended"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks_extended.id"), nullable=False)
    dependent_task_id = Column(String, ForeignKey("tasks_extended.id"), nullable=False)

    # Dependency type
    dependency_type = Column(
        String(50), default="finish_to_start"
    )  # finish_to_start, start_to_start, finish_to_finish, start_to_finish
    lag_days = Column(Integer, default=0)  # Lag time in days

    # Metadata
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String, ForeignKey("users.id"))

    # Relationships
    task = relationship(
        "TaskExtended", foreign_keys=[task_id], back_populates="dependencies"
    )
    dependent_task = relationship(
        "TaskExtended", foreign_keys=[dependent_task_id], back_populates="dependents"
    )
    creator = relationship("User", foreign_keys=[created_by])


class ProjectResource(Base):
    """Project Resource Management - Team member allocation and roles."""

    __tablename__ = "project_resources"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects_extended.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Role and assignment
    role = Column(SQLEnum(ResourceRole), nullable=False)
    allocation_percentage = Column(Numeric(5, 2), default=100)  # 0-100%
    hourly_rate = Column(Numeric(10, 2))

    # Timeline
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)

    # Capacity
    planned_hours = Column(Numeric(8, 2))
    actual_hours = Column(Numeric(8, 2), default=0)

    # System fields
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)

    # Metadata
    notes = Column(Text)
    skills = Column(JSON, default=[])

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))

    # Relationships
    project = relationship("ProjectExtended", back_populates="resources")
    user = relationship("User")
    creator = relationship("User", foreign_keys=[created_by])


class TimeEntry(Base):
    """Time Tracking - Detailed work time logging."""

    __tablename__ = "time_entries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects_extended.id"), nullable=False)
    task_id = Column(String, ForeignKey("tasks_extended.id"))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Time details
    date = Column(Date, nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    hours = Column(Numeric(6, 2), nullable=False)

    # Work classification
    entry_type = Column(SQLEnum(TimeEntryType), default=TimeEntryType.DEVELOPMENT)
    description = Column(Text)

    # Billing
    is_billable = Column(Boolean, default=True)
    billing_rate = Column(Numeric(10, 2))
    billing_amount = Column(Numeric(12, 2))

    # Approval
    is_approved = Column(Boolean, default=False)
    approved_by_id = Column(String, ForeignKey("users.id"))
    approved_at = Column(DateTime)

    # System fields
    invoice_id = Column(String)  # Link to invoice if billed

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("ProjectExtended", back_populates="time_entries")
    task = relationship("TaskExtended", back_populates="time_entries")
    user = relationship("User")
    approver = relationship("User", foreign_keys=[approved_by_id])


class ProjectRisk(Base):
    """Risk Management - Project risk identification and mitigation."""

    __tablename__ = "project_risks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects_extended.id"), nullable=False)

    # Risk identification
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))  # technical, schedule, budget, resource, external

    # Risk assessment
    probability = Column(Numeric(3, 2))  # 0.00 to 1.00
    impact = Column(Numeric(3, 2))  # 0.00 to 1.00
    risk_score = Column(Numeric(5, 2))  # probability * impact * 100
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.LOW)

    # Risk management
    status = Column(SQLEnum(RiskStatus), default=RiskStatus.IDENTIFIED)
    owner_id = Column(String, ForeignKey("users.id"))

    # Mitigation
    mitigation_strategy = Column(Text)
    contingency_plan = Column(Text)
    mitigation_cost = Column(Numeric(12, 2))

    # Timeline
    identified_date = Column(Date, nullable=False)
    target_closure_date = Column(Date)
    actual_closure_date = Column(Date)

    # Monitoring
    last_reviewed_date = Column(Date)
    next_review_date = Column(Date)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))

    # Relationships
    project = relationship("ProjectExtended", back_populates="risks")
    owner = relationship("User", foreign_keys=[owner_id])
    creator = relationship("User", foreign_keys=[created_by])


class ProjectMilestoneExtended(Base):
    """Enhanced Project Milestones - Key project checkpoints."""

    __tablename__ = "project_milestones_extended"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects_extended.id"), nullable=False)

    # Milestone details
    name = Column(String(200), nullable=False)
    description = Column(Text)
    milestone_type = Column(String(50))  # phase_gate, deliverable, review, approval

    # Timeline
    planned_date = Column(Date, nullable=False)
    actual_date = Column(Date)

    # Status
    is_completed = Column(Boolean, default=False)
    completion_percentage = Column(Numeric(5, 2), default=0)

    # Dependencies
    dependent_tasks = Column(JSON, default=[])  # Task IDs that must complete

    # Approval
    requires_approval = Column(Boolean, default=False)
    approved_by_id = Column(String, ForeignKey("users.id"))
    approval_date = Column(Date)

    # Deliverables
    deliverables = Column(JSON, default=[])
    success_criteria = Column(JSON, default=[])

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))

    # Relationships
    project = relationship("ProjectExtended", back_populates="milestones")
    approver = relationship("User", foreign_keys=[approved_by_id])
    creator = relationship("User", foreign_keys=[created_by])


class ProjectDeliverable(Base):
    """Project Deliverables - Tangible project outputs."""

    __tablename__ = "project_deliverables"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects_extended.id"), nullable=False)
    milestone_id = Column(String, ForeignKey("project_milestones_extended.id"))

    # Deliverable details
    name = Column(String(200), nullable=False)
    description = Column(Text)
    deliverable_type = Column(String(50))  # document, software, report, presentation

    # Status
    status = Column(
        String(50), default="planned"
    )  # planned, in_progress, completed, delivered
    completion_percentage = Column(Numeric(5, 2), default=0)

    # Timeline
    due_date = Column(Date)
    completion_date = Column(Date)
    delivery_date = Column(Date)

    # Quality
    quality_requirements = Column(JSON, default=[])
    acceptance_criteria = Column(JSON, default=[])
    quality_score = Column(Numeric(4, 2))

    # Assignment
    responsible_user_id = Column(String, ForeignKey("users.id"))
    reviewer_id = Column(String, ForeignKey("users.id"))

    # Files and attachments
    file_attachments = Column(JSON, default=[])
    version = Column(String(20), default="1.0")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))

    # Relationships
    project = relationship("ProjectExtended", back_populates="deliverables")
    milestone = relationship("ProjectMilestoneExtended")
    responsible_user = relationship("User", foreign_keys=[responsible_user_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    creator = relationship("User", foreign_keys=[created_by])


class ProjectIssue(Base):
    """Project Issues - Problem tracking and resolution."""

    __tablename__ = "project_issues"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects_extended.id"), nullable=False)
    task_id = Column(String, ForeignKey("tasks_extended.id"))

    # Issue identification
    issue_number = Column(String(50), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)

    # Classification
    issue_type = Column(String(50))  # bug, blocker, enhancement, question
    severity = Column(String(50))  # low, medium, high, critical
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)

    # Status
    status = Column(String(50), default="open")  # open, in_progress, resolved, closed
    resolution = Column(String(50))  # fixed, duplicate, invalid, wontfix

    # Assignment
    reporter_id = Column(String, ForeignKey("users.id"), nullable=False)
    assigned_to_id = Column(String, ForeignKey("users.id"))

    # Timeline
    reported_date = Column(Date, nullable=False)
    due_date = Column(Date)
    resolved_date = Column(Date)
    closed_date = Column(Date)

    # Resolution details
    resolution_description = Column(Text)
    workaround = Column(Text)

    # Impact
    affects_milestone = Column(Boolean, default=False)
    affects_deliverable = Column(Boolean, default=False)
    business_impact = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("ProjectExtended", back_populates="issues")
    task = relationship("TaskExtended")
    reporter = relationship("User", foreign_keys=[reporter_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])


class TaskComment(Base):
    """Task Comments - Collaboration and communication."""

    __tablename__ = "task_comments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks_extended.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Comment details
    comment = Column(Text, nullable=False)
    comment_type = Column(
        String(50), default="general"
    )  # general, status_update, question, review

    # Mentions and notifications
    mentions = Column(JSON, default=[])  # User IDs mentioned

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    task = relationship("TaskExtended", back_populates="comments")
    user = relationship("User")


class ProjectTemplate(Base):
    """Project Templates - Reusable project structures."""

    __tablename__ = "project_templates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Template details
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))

    # Template structure
    template_data = Column(JSON, nullable=False)  # Contains project structure
    default_duration_days = Column(Integer)
    default_team_size = Column(Integer)

    # Usage
    usage_count = Column(Integer, default=0)
    is_public = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Metadata
    tags = Column(JSON, default=[])

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))

    # Relationships
    organization = relationship("Organization")
    creator = relationship("User", foreign_keys=[created_by])


class ProjectPortfolio(Base):
    """Project Portfolio - High-level project grouping and management."""

    __tablename__ = "project_portfolios"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Portfolio details
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Management
    portfolio_manager_id = Column(String, ForeignKey("users.id"))

    # Budget
    total_budget = Column(Numeric(18, 2))
    allocated_budget = Column(Numeric(18, 2), default=0)
    currency = Column(String(3), default="JPY")

    # Strategic alignment
    strategic_objectives = Column(JSON, default=[])
    success_metrics = Column(JSON, default=[])

    # Portfolio projects (many-to-many through project_portfolio_projects table)

    # System fields
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))

    # Relationships
    organization = relationship("Organization")
    portfolio_manager = relationship("User", foreign_keys=[portfolio_manager_id])
    creator = relationship("User", foreign_keys=[created_by])
