"""
Workflow System Models - CC02 v31.0 Phase 2

Comprehensive workflow system with:
- Business Process Automation & Orchestration
- Approval Workflows & State Management
- Dynamic Workflow Configuration
- Parallel & Sequential Processing
- Conditional Logic & Decision Trees
- Role-Based Task Assignment
- Workflow Analytics & Performance Tracking
- Template-Based Workflow Creation
- Integration Hooks & External Triggers
- Compliance & Audit Trail
"""

import uuid
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class WorkflowType(str, Enum):
    """Workflow type enumeration."""
    
    APPROVAL = "approval"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    SUB_WORKFLOW = "sub_workflow"
    ESCALATION = "escalation"
    NOTIFICATION = "notification"
    INTEGRATION = "integration"
    CUSTOM = "custom"


class WorkflowStatus(str, Enum):
    """Workflow status enumeration."""
    
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class WorkflowInstanceStatus(str, Enum):
    """Workflow instance status enumeration."""
    
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    ESCALATED = "escalated"


class TaskStatus(str, Enum):
    """Task status enumeration."""
    
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"


class TaskPriority(str, Enum):
    """Task priority enumeration."""
    
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class ActionType(str, Enum):
    """Action type enumeration."""
    
    APPROVE = "approve"
    REJECT = "reject"
    DELEGATE = "delegate"
    ESCALATE = "escalate"
    COMMENT = "comment"
    ATTACH = "attach"
    MODIFY = "modify"
    COMPLETE = "complete"
    CANCEL = "cancel"
    SUSPEND = "suspend"
    RESUME = "resume"


class TriggerType(str, Enum):
    """Trigger type enumeration."""
    
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    SCHEDULED = "scheduled"
    EVENT = "event"
    WEBHOOK = "webhook"
    EMAIL = "email"
    API = "api"
    FILE_UPLOAD = "file_upload"


class WorkflowDefinition(Base):
    """Workflow Definition - Template for workflow processes."""

    __tablename__ = "workflow_definitions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    
    # Definition identification
    name = Column(String(200), nullable=False)
    code = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    workflow_type = Column(SQLEnum(WorkflowType), nullable=False)
    category = Column(String(100))
    
    # Configuration
    definition_schema = Column(JSON, nullable=False)  # JSON workflow definition
    steps_config = Column(JSON, default=[])
    decision_rules = Column(JSON, default={})
    approval_matrix = Column(JSON, default={})
    
    # Execution settings
    auto_start = Column(Boolean, default=False)
    parallel_execution = Column(Boolean, default=False)
    max_parallel_tasks = Column(Integer, default=5)
    timeout_minutes = Column(Integer)
    retry_attempts = Column(Integer, default=0)
    
    # Triggers
    trigger_types = Column(JSON, default=[])
    trigger_conditions = Column(JSON, default={})
    trigger_schedule = Column(String(100))  # cron expression
    
    # Assignment rules
    default_assignee_type = Column(String(50), default="user")  # user, role, group, auto
    default_assignee_id = Column(String)
    assignment_rules = Column(JSON, default={})
    escalation_rules = Column(JSON, default=[])
    
    # Notifications
    notification_settings = Column(JSON, default={})
    email_templates = Column(JSON, default={})
    reminder_settings = Column(JSON, default={})
    
    # SLA and performance
    sla_minutes = Column(Integer)
    warning_threshold_percent = Column(Numeric(5, 2), default=Decimal("80.0"))
    escalation_threshold_percent = Column(Numeric(5, 2), default=Decimal("100.0"))
    
    # Versioning
    version = Column(String(50), default="1.0")
    previous_version_id = Column(String, ForeignKey("workflow_definitions.id"))
    change_log = Column(JSON, default=[])
    
    # Status and metrics
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.DRAFT)
    is_template = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    success_rate = Column(Numeric(5, 2))
    average_completion_time = Column(Numeric(10, 2))
    
    # Access control
    is_public = Column(Boolean, default=False)
    allowed_roles = Column(JSON, default=[])
    allowed_users = Column(JSON, default=[])
    allowed_departments = Column(JSON, default=[])
    
    # Metadata
    tags = Column(JSON, default=[])
    custom_fields = Column(JSON, default={})
    workflow_metadata = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    updated_by = Column(String, ForeignKey("users.id"))

    # Relationships
    organization = relationship("Organization")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    previous_version = relationship("WorkflowDefinition", remote_side=[id])
    instances = relationship("WorkflowInstance", back_populates="definition")
    steps = relationship("WorkflowStep", back_populates="definition")


class WorkflowStep(Base):
    """Workflow Step - Individual steps within a workflow definition."""

    __tablename__ = "workflow_steps"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    definition_id = Column(String, ForeignKey("workflow_definitions.id"), nullable=False)
    
    # Step identification
    name = Column(String(200), nullable=False)
    code = Column(String(100), nullable=False)
    description = Column(Text)
    step_type = Column(String(100), nullable=False)  # task, approval, decision, parallel, loop, end
    
    # Position and flow
    step_order = Column(Integer, nullable=False)
    parent_step_id = Column(String, ForeignKey("workflow_steps.id"))
    next_step_ids = Column(JSON, default=[])
    previous_step_ids = Column(JSON, default=[])
    
    # Configuration
    step_config = Column(JSON, default={})
    form_schema = Column(JSON, default={})
    validation_rules = Column(JSON, default={})
    business_rules = Column(JSON, default={})
    
    # Assignment
    assignee_type = Column(String(50))  # user, role, group, auto, previous_assignee
    assignee_id = Column(String)
    assignee_rules = Column(JSON, default={})
    auto_assign_logic = Column(Text)
    
    # Execution
    is_required = Column(Boolean, default=True)
    allow_skip = Column(Boolean, default=False)
    allow_delegate = Column(Boolean, default=True)
    allow_reassign = Column(Boolean, default=True)
    
    # Timing
    estimated_duration_minutes = Column(Integer)
    max_duration_minutes = Column(Integer)
    due_date_calculation = Column(String(200))
    
    # Conditions
    start_conditions = Column(JSON, default={})
    completion_conditions = Column(JSON, default={})
    escalation_conditions = Column(JSON, default={})
    
    # Actions
    on_start_actions = Column(JSON, default=[])
    on_complete_actions = Column(JSON, default=[])
    on_error_actions = Column(JSON, default=[])
    
    # Notifications
    notification_events = Column(JSON, default=[])
    notification_recipients = Column(JSON, default=[])
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    tags = Column(JSON, default=[])
    step_metadata = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization")
    definition = relationship("WorkflowDefinition", back_populates="steps")
    parent_step = relationship("WorkflowStep", remote_side=[id])
    tasks = relationship("WorkflowTask", back_populates="step")


class WorkflowInstance(Base):
    """Workflow Instance - Active execution of a workflow definition."""

    __tablename__ = "workflow_instances_extended"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    definition_id = Column(String, ForeignKey("workflow_definitions.id"), nullable=False)
    
    # Instance identification
    instance_number = Column(String(100), nullable=False, index=True)
    title = Column(String(300))
    description = Column(Text)
    
    # Context
    entity_type = Column(String(100))  # The type of entity this workflow is processing
    entity_id = Column(String(200))    # The ID of the entity being processed
    context_data = Column(JSON, default={})
    form_data = Column(JSON, default={})
    
    # Execution
    status = Column(SQLEnum(WorkflowInstanceStatus), default=WorkflowInstanceStatus.PENDING)
    current_step_id = Column(String, ForeignKey("workflow_steps.id"))
    current_assignee_id = Column(String, ForeignKey("users.id"))
    
    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    due_date = Column(DateTime)
    sla_deadline = Column(DateTime)
    duration_minutes = Column(Integer)
    
    # Priority and urgency
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.NORMAL)
    urgency_level = Column(Integer, default=3)  # 1-5 scale
    business_impact = Column(String(100))
    
    # Progress tracking
    total_steps = Column(Integer, default=0)
    completed_steps = Column(Integer, default=0)
    progress_percentage = Column(Numeric(5, 2), default=Decimal("0.00"))
    
    # Performance metrics
    sla_breach = Column(Boolean, default=False)
    escalation_count = Column(Integer, default=0)
    reassignment_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    
    # Results
    final_status = Column(String(50))
    final_result = Column(JSON)
    completion_notes = Column(Text)
    
    # Error handling
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # User interaction
    initiated_by = Column(String, ForeignKey("users.id"))
    completed_by = Column(String, ForeignKey("users.id"))
    cancelled_by = Column(String, ForeignKey("users.id"))
    cancellation_reason = Column(String(500))
    
    # Notifications
    notification_settings = Column(JSON, default={})
    last_notification_sent = Column(DateTime)
    
    # Metadata
    tags = Column(JSON, default=[])
    custom_fields = Column(JSON, default={})
    instance_metadata = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization")
    definition = relationship("WorkflowDefinition", back_populates="instances")
    current_step = relationship("WorkflowStep")
    current_assignee = relationship("User", foreign_keys=[current_assignee_id])
    initiator = relationship("User", foreign_keys=[initiated_by])
    completer = relationship("User", foreign_keys=[completed_by])
    canceller = relationship("User", foreign_keys=[cancelled_by])
    tasks = relationship("WorkflowTask", back_populates="instance")
    activities = relationship("WorkflowActivity", back_populates="instance")


class WorkflowTask(Base):
    """Workflow Task - Individual tasks within a workflow instance."""

    __tablename__ = "workflow_tasks_extended"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    instance_id = Column(String, ForeignKey("workflow_instances_extended.id"), nullable=False)
    step_id = Column(String, ForeignKey("workflow_steps.id"), nullable=False)
    
    # Task identification
    task_number = Column(String(100), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Assignment
    assignee_id = Column(String, ForeignKey("users.id"))
    assignee_type = Column(String(50))  # user, role, group
    assigned_by = Column(String, ForeignKey("users.id"))
    assigned_at = Column(DateTime)
    
    # Status and progress
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    progress_percentage = Column(Numeric(5, 2), default=Decimal("0.00"))
    
    # Timing
    due_date = Column(DateTime)
    estimated_duration_minutes = Column(Integer)
    actual_duration_minutes = Column(Integer)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Priority and urgency
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.NORMAL)
    urgency_score = Column(Integer, default=3)
    
    # Task data
    form_data = Column(JSON, default={})
    context_data = Column(JSON, default={})
    validation_errors = Column(JSON, default=[])
    
    # Results
    completion_result = Column(String(100))  # approved, rejected, completed, etc.
    result_data = Column(JSON)
    completion_notes = Column(Text)
    
    # Delegation and escalation
    original_assignee_id = Column(String, ForeignKey("users.id"))
    delegated_from = Column(String, ForeignKey("users.id"))
    delegated_to = Column(String, ForeignKey("users.id"))
    escalated_from = Column(String, ForeignKey("users.id"))
    escalated_to = Column(String, ForeignKey("users.id"))
    escalation_reason = Column(String(500))
    
    # Performance tracking
    sla_breach = Column(Boolean, default=False)
    overdue_hours = Column(Numeric(8, 2))
    reminder_count = Column(Integer, default=0)
    last_reminder_sent = Column(DateTime)
    
    # Attachments and comments
    attachment_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    
    # Error handling
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    
    # Metadata
    tags = Column(JSON, default=[])
    custom_fields = Column(JSON, default={})
    task_metadata = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization")
    instance = relationship("WorkflowInstance", back_populates="tasks")
    step = relationship("WorkflowStep", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assignee_id])
    assigner = relationship("User", foreign_keys=[assigned_by])
    original_assignee = relationship("User", foreign_keys=[original_assignee_id])
    activities = relationship("WorkflowActivity", back_populates="task")
    comments = relationship("WorkflowComment", back_populates="task")
    attachments = relationship("WorkflowAttachment", back_populates="task")


class WorkflowActivity(Base):
    """Workflow Activity - Log of all actions performed on workflow instances."""

    __tablename__ = "workflow_activities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    instance_id = Column(String, ForeignKey("workflow_instances_extended.id"), nullable=False)
    task_id = Column(String, ForeignKey("workflow_tasks_extended.id"))
    
    # Activity details
    activity_type = Column(String(100), nullable=False)
    action_type = Column(SQLEnum(ActionType), nullable=False)
    description = Column(String(1000))
    
    # Actor
    performed_by = Column(String, ForeignKey("users.id"))
    performed_on_behalf_of = Column(String, ForeignKey("users.id"))
    actor_type = Column(String(50), default="user")  # user, system, integration
    
    # Context
    from_status = Column(String(50))
    to_status = Column(String(50))
    from_assignee = Column(String, ForeignKey("users.id"))
    to_assignee = Column(String, ForeignKey("users.id"))
    
    # Data changes
    field_changes = Column(JSON, default={})
    old_values = Column(JSON)
    new_values = Column(JSON)
    
    # Additional data
    activity_data = Column(JSON, default={})
    comments = Column(Text)
    attachments = Column(JSON, default=[])
    
    # System info
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    source_system = Column(String(100))
    
    # Timestamp
    performed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization")
    instance = relationship("WorkflowInstance", back_populates="activities")
    task = relationship("WorkflowTask", back_populates="activities")
    performer = relationship("User", foreign_keys=[performed_by])
    on_behalf_of = relationship("User", foreign_keys=[performed_on_behalf_of])
    from_assignee_user = relationship("User", foreign_keys=[from_assignee])
    to_assignee_user = relationship("User", foreign_keys=[to_assignee])


class WorkflowComment(Base):
    """Workflow Comment - Comments and discussions on workflow tasks."""

    __tablename__ = "workflow_comments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    task_id = Column(String, ForeignKey("workflow_tasks_extended.id"), nullable=False)
    
    # Comment details
    comment_text = Column(Text, nullable=False)
    comment_type = Column(String(50), default="general")  # general, approval, rejection, question, answer
    is_internal = Column(Boolean, default=False)
    is_system_generated = Column(Boolean, default=False)
    
    # Hierarchy
    parent_comment_id = Column(String, ForeignKey("workflow_comments.id"))
    thread_id = Column(String)
    
    # Author
    author_id = Column(String, ForeignKey("users.id"), nullable=False)
    author_role = Column(String(100))
    
    # Status
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(String, ForeignKey("users.id"))
    
    # Mentions and notifications
    mentioned_users = Column(JSON, default=[])
    notification_sent = Column(Boolean, default=False)
    
    # Metadata
    comment_metadata = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization")
    task = relationship("WorkflowTask", back_populates="comments")
    parent_comment = relationship("WorkflowComment", remote_side=[id])
    author = relationship("User", foreign_keys=[author_id])
    deleter = relationship("User", foreign_keys=[deleted_by])


class WorkflowAttachment(Base):
    """Workflow Attachment - Files and documents attached to workflow tasks."""

    __tablename__ = "workflow_attachments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    task_id = Column(String, ForeignKey("workflow_tasks_extended.id"), nullable=False)
    
    # File details
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500))
    file_path = Column(String(1000))
    file_size = Column(Integer)
    file_type = Column(String(100))
    mime_type = Column(String(200))
    
    # Classification
    attachment_type = Column(String(100), default="document")  # document, image, evidence, reference
    category = Column(String(100))
    
    # Storage
    storage_provider = Column(String(100), default="local")
    storage_path = Column(String(1000))
    storage_metadata = Column(JSON, default={})
    
    # Security
    access_level = Column(String(50), default="task_participants")
    encryption_status = Column(String(50))
    checksum = Column(String(100))
    
    # Versions
    version = Column(String(50), default="1.0")
    previous_version_id = Column(String, ForeignKey("workflow_attachments.id"))
    
    # Upload details
    uploaded_by = Column(String, ForeignKey("users.id"), nullable=False)
    upload_source = Column(String(100), default="web")
    
    # Status
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(String, ForeignKey("users.id"))
    
    # Metadata
    description = Column(Text)
    tags = Column(JSON, default=[])
    attachment_metadata = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization")
    task = relationship("WorkflowTask", back_populates="attachments")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    deleter = relationship("User", foreign_keys=[deleted_by])
    previous_version = relationship("WorkflowAttachment", remote_side=[id])


class WorkflowTemplate(Base):
    """Workflow Template - Predefined workflow templates for common processes."""

    __tablename__ = "workflow_templates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    
    # Template identification
    name = Column(String(200), nullable=False)
    code = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    category = Column(String(100))
    industry = Column(String(100))
    
    # Template definition
    template_schema = Column(JSON, nullable=False)
    default_config = Column(JSON, default={})
    customization_options = Column(JSON, default={})
    
    # Usage and popularity
    usage_count = Column(Integer, default=0)
    rating_average = Column(Numeric(3, 2))
    rating_count = Column(Integer, default=0)
    
    # Access and sharing
    is_public = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    allowed_organizations = Column(JSON, default=[])
    
    # Metadata
    tags = Column(JSON, default=[])
    template_metadata = Column(JSON, default={})
    
    # Versioning
    version = Column(String(50), default="1.0")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization")
    creator = relationship("User")


class WorkflowAnalytics(Base):
    """Workflow Analytics - Performance metrics and analytics for workflow processes."""

    __tablename__ = "workflow_analytics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    
    # Analytics period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    period_type = Column(String(50), nullable=False)  # daily, weekly, monthly, quarterly, yearly
    
    # Scope
    definition_id = Column(String, ForeignKey("workflow_definitions.id"))
    department = Column(String(100))
    workflow_type = Column(String(100))
    
    # Instance metrics
    total_instances = Column(Integer, default=0)
    completed_instances = Column(Integer, default=0)
    failed_instances = Column(Integer, default=0)
    cancelled_instances = Column(Integer, default=0)
    active_instances = Column(Integer, default=0)
    
    # Performance metrics
    average_completion_time_hours = Column(Numeric(10, 2))
    median_completion_time_hours = Column(Numeric(10, 2))
    min_completion_time_hours = Column(Numeric(10, 2))
    max_completion_time_hours = Column(Numeric(10, 2))
    
    # SLA metrics
    sla_compliance_rate = Column(Numeric(5, 2))
    sla_breaches = Column(Integer, default=0)
    average_sla_deviation_hours = Column(Numeric(10, 2))
    
    # Task metrics
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    overdue_tasks = Column(Integer, default=0)
    escalated_tasks = Column(Integer, default=0)
    reassigned_tasks = Column(Integer, default=0)
    
    # User productivity
    most_productive_user_id = Column(String, ForeignKey("users.id"))
    average_tasks_per_user = Column(Numeric(8, 2))
    user_utilization_rate = Column(Numeric(5, 2))
    
    # Bottlenecks and issues
    bottleneck_steps = Column(JSON, default=[])
    common_failure_points = Column(JSON, default=[])
    error_frequency = Column(JSON, default={})
    
    # Quality metrics
    approval_rate = Column(Numeric(5, 2))
    rejection_rate = Column(Numeric(5, 2))
    rework_rate = Column(Numeric(5, 2))
    
    # Cost metrics
    total_processing_cost = Column(Numeric(15, 2))
    cost_per_instance = Column(Numeric(15, 2))
    labor_cost = Column(Numeric(15, 2))
    
    # Trends
    volume_trend = Column(String(50))  # increasing, decreasing, stable
    performance_trend = Column(String(50))
    quality_trend = Column(String(50))
    
    # Calculated at
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization")
    definition = relationship("WorkflowDefinition")
    most_productive_user = relationship("User")


class WorkflowAuditLog(Base):
    """Workflow Audit Log - Comprehensive audit trail for workflow operations."""

    __tablename__ = "workflow_audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    
    # Action details
    action_type = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String, nullable=False)
    
    # User and session
    user_id = Column(String, ForeignKey("users.id"))
    session_id = Column(String(200))
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Changes
    old_values = Column(JSON)
    new_values = Column(JSON)
    changes_summary = Column(String(1000))
    
    # Context
    workflow_context = Column(JSON, default={})
    related_entities = Column(JSON, default=[])
    business_context = Column(String(500))
    
    # Impact assessment
    impact_level = Column(String(50))  # low, medium, high, critical
    affected_users = Column(JSON, default=[])
    compliance_relevance = Column(String(100))
    
    # Performance
    execution_time_ms = Column(Integer)
    resource_usage = Column(JSON, default={})
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization")
    user = relationship("User")