"""Workflow management models for Phase 6 advanced workflow functionality."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel
from app.types import OrganizationId, UserId

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.organization import Organization
    from app.models.user import User


class WorkflowStatus(str, Enum):
    """Workflow status enumeration."""

    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class WorkflowInstanceStatus(str, Enum):
    """Workflow instance status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TaskStatus(str, Enum):
    """Workflow task status enumeration."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


class ApplicationStatus(str, Enum):
    """Application status enumeration."""

    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    PENDING_CLARIFICATION = "pending_clarification"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ApplicationType(str, Enum):
    """Application type enumeration."""

    LEAVE_REQUEST = "leave_request"
    EXPENSE_REPORT = "expense_report"
    PURCHASE_REQUEST = "purchase_request"
    TRAVEL_REQUEST = "travel_request"
    OVERTIME_REQUEST = "overtime_request"
    TRAINING_REQUEST = "training_request"
    OTHER = "other"


class ApprovalStatus(str, Enum):
    """Approval status enumeration."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DELEGATED = "delegated"


class NodeType(str, Enum):
    """Workflow node type enumeration."""

    START = "start"
    END = "end"
    TASK = "task"
    APPROVAL = "approval"
    CONDITION = "condition"
    PARALLEL = "parallel"
    MERGE = "merge"
    TIMER = "timer"


class Workflow(SoftDeletableModel):
    """Workflow definition model."""

    __tablename__ = "workflows"

    # Basic fields
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Workflow name"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Workflow description"
    )
    version: Mapped[str] = mapped_column(
        String(20), default="1.0", comment="Workflow version"
    )

    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, comment="Organization ID"
    )
    created_by: Mapped[UserId] = mapped_column(
        ForeignKey("users.id"), nullable=False, comment="Creator user ID"
    )

    # Workflow configuration
    status: Mapped[WorkflowStatus] = mapped_column(
        String(50), default=WorkflowStatus.DRAFT, comment="Workflow status"
    )
    is_template: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Template flag"
    )
    trigger_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Trigger type (manual, automatic, scheduled)",
    )
    trigger_conditions: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Trigger conditions (JSON)"
    )

    # Workflow definition (visual editor data)
    workflow_definition: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, comment="Workflow definition (nodes, connections)"
    )

    # Settings
    allow_parallel_instances: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Allow multiple instances"
    )
    timeout_hours: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Workflow timeout in hours"
    )

    # Metadata
    tags: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Workflow tags (comma-separated)"
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Workflow category"
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", lazy="select")
    created_by_user: Mapped["User"] = relationship(
        "User", foreign_keys=[created_by], lazy="select"
    )
    nodes: Mapped[List["WorkflowNode"]] = relationship(
        "WorkflowNode", back_populates="workflow", cascade="all, delete-orphan"
    )
    instances: Mapped[List["WorkflowInstance"]] = relationship(
        "WorkflowInstance", back_populates="workflow", cascade="all, delete-orphan"
    )

    def __str__(self) -> str:
        return f"{self.name} v{self.version}"


class WorkflowNode(SoftDeletableModel):
    """Workflow node model for individual workflow steps."""

    __tablename__ = "workflow_nodes"

    # Foreign keys
    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id"), nullable=False, comment="Workflow ID"
    )

    # Node identification
    node_id: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Unique node ID within workflow"
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="Node name")
    node_type: Mapped[NodeType] = mapped_column(
        String(50), nullable=False, comment="Node type"
    )

    # Node configuration
    configuration: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, comment="Node configuration (JSON)"
    )
    position_x: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="X position in visual editor"
    )
    position_y: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Y position in visual editor"
    )

    # Assignment settings
    assign_to_role: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Role-based assignment"
    )
    assign_to_user: Mapped[Optional[UserId]] = mapped_column(
        ForeignKey("users.id"), nullable=True, comment="User-based assignment"
    )
    auto_assign_rules: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Auto-assignment rules (JSON)"
    )

    # Conditions and rules
    entry_conditions: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Entry conditions (JSON)"
    )
    exit_conditions: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Exit conditions (JSON)"
    )

    # Timing
    estimated_duration_hours: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Estimated duration in hours"
    )
    timeout_hours: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Node timeout in hours"
    )

    # Relationships
    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="nodes")
    assigned_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[assign_to_user], lazy="select"
    )
    connections_from: Mapped[List["WorkflowConnection"]] = relationship(
        "WorkflowConnection",
        foreign_keys="WorkflowConnection.from_node_id",
        back_populates="from_node",
        cascade="all, delete-orphan",
    )
    connections_to: Mapped[List["WorkflowConnection"]] = relationship(
        "WorkflowConnection",
        foreign_keys="WorkflowConnection.to_node_id",
        back_populates="to_node",
        cascade="all, delete-orphan",
    )

    def __str__(self) -> str:
        return f"{self.name} ({self.node_type})"


class WorkflowConnection(SoftDeletableModel):
    """Workflow connection model for node relationships."""

    __tablename__ = "workflow_connections"

    # Foreign keys
    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id"), nullable=False, comment="Workflow ID"
    )
    from_node_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_nodes.id"), nullable=False, comment="Source node ID"
    )
    to_node_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_nodes.id"), nullable=False, comment="Target node ID"
    )

    # Connection details
    name: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="Connection name"
    )
    condition: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Connection condition (JSON)"
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Default connection flag"
    )

    # Relationships
    workflow: Mapped["Workflow"] = relationship("Workflow", lazy="select")
    from_node: Mapped["WorkflowNode"] = relationship(
        "WorkflowNode", foreign_keys=[from_node_id], back_populates="connections_from"
    )
    to_node: Mapped["WorkflowNode"] = relationship(
        "WorkflowNode", foreign_keys=[to_node_id], back_populates="connections_to"
    )

    def __str__(self) -> str:
        return f"{self.from_node.name} -> {self.to_node.name}"


class WorkflowInstance(SoftDeletableModel):
    """Workflow instance model for workflow executions."""

    __tablename__ = "workflow_instances"

    # Foreign keys
    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id"), nullable=False, comment="Workflow ID"
    )
    started_by: Mapped[UserId] = mapped_column(
        ForeignKey("users.id"), nullable=False, comment="User who started instance"
    )

    # Instance details
    instance_name: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="Instance name"
    )
    status: Mapped[WorkflowInstanceStatus] = mapped_column(
        String(50), default=WorkflowInstanceStatus.PENDING, comment="Instance status"
    )

    # Context data
    context_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Instance context data (JSON)"
    )
    input_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Instance input data (JSON)"
    )
    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Instance output data (JSON)"
    )

    # Timing
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="Start timestamp"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Completion timestamp"
    )
    deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Instance deadline"
    )

    # Priority and metadata
    priority: Mapped[int] = mapped_column(
        Integer, default=5, comment="Instance priority (1-10)"
    )
    reference_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Reference object type"
    )
    reference_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Reference object ID"
    )

    # Relationships
    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="instances")
    started_by_user: Mapped["User"] = relationship(
        "User", foreign_keys=[started_by], lazy="select"
    )
    tasks: Mapped[List["WorkflowTask"]] = relationship(
        "WorkflowTask", back_populates="instance", cascade="all, delete-orphan"
    )

    @property
    def is_active(self) -> bool:
        """Check if instance is currently active."""
        return self.status in [
            WorkflowInstanceStatus.PENDING,
            WorkflowInstanceStatus.IN_PROGRESS,
        ]

    @property
    def is_completed(self) -> bool:
        """Check if instance is completed."""
        return self.status == WorkflowInstanceStatus.COMPLETED

    @property
    def duration_hours(self) -> Optional[float]:
        """Calculate instance duration in hours."""
        if self.completed_at is None:
            return None
        delta = self.completed_at - self.started_at
        return delta.total_seconds() / 3600

    def __str__(self) -> str:
        return f"{self.workflow.name} - {self.id}"


class WorkflowTask(SoftDeletableModel):
    """Workflow task model for individual task executions."""

    __tablename__ = "workflow_tasks"

    # Foreign keys
    instance_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_instances.id"), nullable=False, comment="Instance ID"
    )
    node_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_nodes.id"), nullable=False, comment="Node ID"
    )
    assigned_to: Mapped[Optional[UserId]] = mapped_column(
        ForeignKey("users.id"), nullable=True, comment="Assigned user ID"
    )

    # Task details
    task_name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Task name"
    )
    status: Mapped[TaskStatus] = mapped_column(
        String(50), default=TaskStatus.PENDING, comment="Task status"
    )

    # Task data
    input_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Task input data (JSON)"
    )
    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Task output data (JSON)"
    )
    form_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Form submission data (JSON)"
    )

    # Timing
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="Task creation timestamp"
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Task start timestamp"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Task completion timestamp"
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Task due date"
    )

    # Comments and notes
    comments: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Task comments"
    )
    completion_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Completion notes"
    )

    # Relationships
    instance: Mapped["WorkflowInstance"] = relationship(
        "WorkflowInstance", back_populates="tasks"
    )
    node: Mapped["WorkflowNode"] = relationship("WorkflowNode", lazy="select")
    assigned_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[assigned_to], lazy="select"
    )

    @property
    def is_pending(self) -> bool:
        """Check if task is pending."""
        return self.status == TaskStatus.PENDING

    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status == TaskStatus.COMPLETED

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if self.due_date is None or self.is_completed:
            return False
        return datetime.now() > self.due_date

    @property
    def duration_hours(self) -> Optional[float]:
        """Calculate task duration in hours."""
        if self.started_at is None or self.completed_at is None:
            return None
        delta = self.completed_at - self.started_at
        return delta.total_seconds() / 3600

    def __str__(self) -> str:
        return f"{self.task_name} - {self.status}"


class Application(SoftDeletableModel):
    """Application model for WF-002 application management functionality."""

    __tablename__ = "applications"

    # Basic fields
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Application title"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Application description"
    )
    application_type: Mapped[ApplicationType] = mapped_column(
        String(50), nullable=False, comment="Application type"
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        String(50), default=ApplicationStatus.DRAFT, comment="Application status"
    )

    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, comment="Organization ID"
    )
    created_by: Mapped[UserId] = mapped_column(
        ForeignKey("users.id"), nullable=False, comment="Creator user ID"
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id"), nullable=True, comment="Department ID"
    )

    # Application data
    form_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Application form data (JSON)"
    )
    priority: Mapped[str] = mapped_column(
        String(20), default="MEDIUM", comment="Application priority"
    )

    # Timing
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Submission timestamp"
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Approval timestamp"
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Cancellation timestamp"
    )

    # Additional metadata
    cancellation_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Cancellation reason"
    )
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="External reference number"
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", lazy="select")
    created_by_user: Mapped["User"] = relationship(
        "User", foreign_keys=[created_by], lazy="select"
    )
    department: Mapped[Optional["Department"]] = relationship(
        "Department", lazy="select"
    )
    approvals: Mapped[List["ApplicationApproval"]] = relationship(
        "ApplicationApproval",
        back_populates="application",
        cascade="all, delete-orphan",
    )

    @property
    def is_pending(self) -> bool:
        """Check if application is pending approval."""
        return self.status == ApplicationStatus.PENDING_APPROVAL

    @property
    def is_approved(self) -> bool:
        """Check if application is approved."""
        return self.status == ApplicationStatus.APPROVED

    @property
    def can_be_edited(self) -> bool:
        """Check if application can be edited."""
        return self.status == ApplicationStatus.DRAFT

    def __str__(self) -> str:
        return f"{self.title} ({self.application_type.value})"


class ApplicationApproval(SoftDeletableModel):
    """Application approval model for tracking approval decisions."""

    __tablename__ = "application_approvals"

    # Foreign keys
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id"), nullable=False, comment="Application ID"
    )
    approver_id: Mapped[UserId] = mapped_column(
        ForeignKey("users.id"), nullable=False, comment="Approver user ID"
    )

    # Approval details
    status: Mapped[ApprovalStatus] = mapped_column(
        String(50), default=ApprovalStatus.PENDING, comment="Approval status"
    )
    comments: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Approval comments"
    )

    # Timing
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Approval timestamp"
    )

    # Relationships
    application: Mapped["Application"] = relationship(
        "Application", back_populates="approvals"
    )
    approver: Mapped["User"] = relationship(
        "User", foreign_keys=[approver_id], lazy="select"
    )

    @property
    def is_pending(self) -> bool:
        """Check if approval is pending."""
        return self.status == ApprovalStatus.PENDING

    @property
    def is_approved(self) -> bool:
        """Check if approval is approved."""
        return self.status == ApprovalStatus.APPROVED

    def __str__(self) -> str:
        return f"Approval by {self.approver_id} - {self.status.value}"
