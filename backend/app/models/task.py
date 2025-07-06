"""Task management models for ITDO ERP System v2."""

from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum
from sqlalchemy import String, Text, Integer, Float, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import ENUM as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel, BaseModel

if TYPE_CHECKING:
    from app.models.organization import Organization, Project
    from app.models.user import User


class TaskStatus(str, Enum):
    """Task status enumeration."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"


class TaskPriority(str, Enum):
    """Task priority enumeration."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class DependencyType(str, Enum):
    """Task dependency type enumeration."""
    FINISH_TO_START = "FS"  # Finish-to-Start
    START_TO_START = "SS"   # Start-to-Start
    FINISH_TO_FINISH = "FF" # Finish-to-Finish
    START_TO_FINISH = "SF"  # Start-to-Finish


class AssignmentRole(str, Enum):
    """Task assignment role enumeration."""
    ASSIGNEE = "ASSIGNEE"
    REVIEWER = "REVIEWER"
    OBSERVER = "OBSERVER"


class Task(SoftDeletableModel):
    """Task model with comprehensive task management features."""
    
    __tablename__ = "tasks"
    
    # Basic information
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    parent_task_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Status and priority
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus, name="task_status"),
        default=TaskStatus.NOT_STARTED,
        nullable=False,
        index=True
    )
    priority: Mapped[TaskPriority] = mapped_column(
        SQLEnum(TaskPriority, name="task_priority"),
        default=TaskPriority.MEDIUM,
        nullable=False,
        index=True
    )
    
    # Time management
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    estimated_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Progress management
    progress_percentage: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    
    # Optimistic locking
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Tags (JSON array)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Multi-tenant isolation
    organization_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="tasks",
        lazy="joined"
    )
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="joined"
    )
    parent_task: Mapped[Optional["Task"]] = relationship(
        "Task",
        remote_side="Task.id",
        back_populates="subtasks",
        lazy="joined"
    )
    subtasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="parent_task",
        lazy="select"
    )
    assignments: Mapped[List["TaskAssignment"]] = relationship(
        "TaskAssignment",
        back_populates="task",
        lazy="select",
        cascade="all, delete-orphan"
    )
    dependencies_as_successor: Mapped[List["TaskDependency"]] = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.successor_id",
        back_populates="successor",
        lazy="select",
        cascade="all, delete-orphan"
    )
    dependencies_as_predecessor: Mapped[List["TaskDependency"]] = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.predecessor_id",
        back_populates="predecessor",
        lazy="select",
        cascade="all, delete-orphan"
    )
    comments: Mapped[List["TaskComment"]] = relationship(
        "TaskComment",
        back_populates="task",
        lazy="select",
        cascade="all, delete-orphan"
    )
    attachments: Mapped[List["TaskAttachment"]] = relationship(
        "TaskAttachment",
        back_populates="task",
        lazy="select",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title='{self.title}', status={self.status})>"
    
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if not self.due_date:
            return False
        return datetime.now() > self.due_date and self.status != TaskStatus.COMPLETED
    
    def can_transition_to(self, new_status: TaskStatus) -> bool:
        """Check if status transition is valid."""
        valid_transitions = {
            TaskStatus.NOT_STARTED: [TaskStatus.IN_PROGRESS, TaskStatus.ON_HOLD],
            TaskStatus.IN_PROGRESS: [TaskStatus.IN_REVIEW, TaskStatus.ON_HOLD, TaskStatus.COMPLETED],
            TaskStatus.IN_REVIEW: [TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED, TaskStatus.ON_HOLD],
            TaskStatus.ON_HOLD: [TaskStatus.NOT_STARTED, TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW],
            TaskStatus.COMPLETED: []  # Cannot transition from completed
        }
        return new_status in valid_transitions.get(self.status, [])


class TaskAssignment(BaseModel):
    """Task assignment model for user-task relationships."""
    
    __tablename__ = "task_assignments"
    
    task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role: Mapped[AssignmentRole] = mapped_column(
        SQLEnum(AssignmentRole, name="assignment_role"),
        default=AssignmentRole.ASSIGNEE,
        nullable=False
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    assigned_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships
    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="assignments",
        lazy="joined"
    )
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="joined"
    )
    assigner: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assigned_by],
        lazy="joined"
    )
    
    def __repr__(self) -> str:
        return f"<TaskAssignment(task_id={self.task_id}, user_id={self.user_id}, role={self.role})>"


class TaskDependency(BaseModel):
    """Task dependency model for task relationships."""
    
    __tablename__ = "task_dependencies"
    
    predecessor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    successor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    dependency_type: Mapped[DependencyType] = mapped_column(
        SQLEnum(DependencyType, name="dependency_type"),
        default=DependencyType.FINISH_TO_START,
        nullable=False
    )
    lag_time: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Lag time in days"
    )
    
    # Relationships
    predecessor: Mapped["Task"] = relationship(
        "Task",
        foreign_keys=[predecessor_id],
        back_populates="dependencies_as_predecessor",
        lazy="joined"
    )
    successor: Mapped["Task"] = relationship(
        "Task",
        foreign_keys=[successor_id],
        back_populates="dependencies_as_successor",
        lazy="joined"
    )
    
    def __repr__(self) -> str:
        return f"<TaskDependency(predecessor={self.predecessor_id}, successor={self.successor_id}, type={self.dependency_type})>"


class TaskComment(SoftDeletableModel):
    """Task comment model for task discussions."""
    
    __tablename__ = "task_comments"
    
    task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    parent_comment_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("task_comments.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    mentioned_users: Mapped[Optional[List[int]]] = mapped_column(
        JSON,
        nullable=True,
        comment="List of mentioned user IDs"
    )
    
    # Relationships
    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="comments",
        lazy="joined"
    )
    user: Mapped["User"] = relationship(
        "User",
        lazy="joined"
    )
    parent_comment: Mapped[Optional["TaskComment"]] = relationship(
        "TaskComment",
        remote_side="TaskComment.id",
        back_populates="replies",
        lazy="joined"
    )
    replies: Mapped[List["TaskComment"]] = relationship(
        "TaskComment",
        back_populates="parent_comment",
        lazy="select"
    )
    attachments: Mapped[List["TaskAttachment"]] = relationship(
        "TaskAttachment",
        back_populates="comment",
        lazy="select"
    )
    
    def __repr__(self) -> str:
        return f"<TaskComment(id={self.id}, task_id={self.task_id}, user_id={self.user_id})>"


class TaskAttachment(SoftDeletableModel):
    """Task attachment model for file uploads."""
    
    __tablename__ = "task_attachments"
    
    task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    comment_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("task_comments.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    uploaded_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships
    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="attachments",
        lazy="joined"
    )
    comment: Mapped[Optional["TaskComment"]] = relationship(
        "TaskComment",
        back_populates="attachments",
        lazy="joined"
    )
    uploader: Mapped[Optional["User"]] = relationship(
        "User",
        lazy="joined"
    )
    
    def __repr__(self) -> str:
        return f"<TaskAttachment(id={self.id}, file_name='{self.file_name}', task_id={self.task_id})>"