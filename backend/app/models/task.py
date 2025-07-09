"""Task model implementation with project integration."""

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    select,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel
from app.types import UserId

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class TaskStatus(str, Enum):
    """Task status enumeration."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class TaskPriority(str, Enum):
    """Task priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskType(str, Enum):
    """Task type enumeration."""

    FEATURE = "feature"
    BUG = "bug"
    ENHANCEMENT = "enhancement"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    MAINTENANCE = "maintenance"
    EPIC = "epic"


class Task(SoftDeletableModel):
    """Task model with comprehensive project integration."""

    __tablename__ = "tasks"

    # Basic fields
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Task title"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Task description"
    )
    code: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True, comment="Task code/identifier"
    )

    # Project relationship
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=False, index=True,
        comment="Project ID"
    )

    # User assignments
    assignee_id: Mapped[Optional[UserId]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True,
        comment="Assigned user ID"
    )
    reporter_id: Mapped[UserId] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True,
        comment="Reporter user ID"
    )

    # Task details
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=TaskStatus.TODO.value,
        index=True, comment="Task status"
    )
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default=TaskPriority.MEDIUM.value,
        index=True, comment="Task priority"
    )
    task_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=TaskType.FEATURE.value,
        comment="Task type"
    )

    # Timeline fields
    start_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Task start date"
    )
    due_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, index=True, comment="Task due date"
    )
    completed_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Task completion date"
    )

    # Effort tracking
    estimated_hours: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Estimated hours to complete"
    )
    actual_hours: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=0.0, comment="Actual hours worked"
    )
    remaining_hours: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Remaining hours to complete"
    )

    # Progress tracking
    progress_percentage: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Progress percentage (0-100)"
    )

    # Dependencies
    depends_on: Mapped[Optional[List[int]]] = mapped_column(
        JSON, nullable=True, default=list,
        comment="List of task IDs this task depends on"
    )
    blocks: Mapped[Optional[List[int]]] = mapped_column(
        JSON, nullable=True, default=list,
        comment="List of task IDs this task blocks"
    )

    # Additional fields
    story_points: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Story points for estimation"
    )
    epic_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("tasks.id"), nullable=True, index=True,
        comment="Parent epic task ID"
    )
    sprint_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True, comment="Sprint ID"
    )

    # Metadata
    tags: Mapped[Optional[List[str]]] = mapped_column(
        JSON, nullable=True, default=list, comment="Task tags"
    )
    labels: Mapped[Optional[Dict[str, str]]] = mapped_column(
        JSON, nullable=True, default=dict, comment="Task labels"
    )
    custom_fields: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default=dict, comment="Custom fields"
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project", lazy="select"
    )
    assignee: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[assignee_id], lazy="joined"
    )
    reporter: Mapped["User"] = relationship(
        "User", foreign_keys=[reporter_id], lazy="joined"
    )

    # Self-referential relationship for epics
    epic: Mapped[Optional["Task"]] = relationship(
        "Task", remote_side="Task.id", back_populates="subtasks"
    )
    subtasks: Mapped[List["Task"]] = relationship(
        "Task", back_populates="epic", cascade="all, delete-orphan"
    )

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("project_id", "code", name="uq_task_code_project"),
        Index("idx_task_status_priority", "status", "priority"),
        Index("idx_task_assignee_status", "assignee_id", "status"),
        Index("idx_task_project_status", "project_id", "status"),
        Index("idx_task_due_date_status", "due_date", "status"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if self.due_date and self.status not in [TaskStatus.DONE.value, TaskStatus.CANCELLED.value]:
            return self.due_date < date.today()
        return False

    @property
    def days_remaining(self) -> Optional[int]:
        """Get days remaining until due date."""
        if self.due_date and self.status not in [TaskStatus.DONE.value, TaskStatus.CANCELLED.value]:
            today = date.today()
            delta = self.due_date - today
            return delta.days
        return None

    @property
    def hours_usage_percentage(self) -> Optional[float]:
        """Get hours usage percentage."""
        if self.estimated_hours and self.actual_hours:
            return (self.actual_hours / self.estimated_hours) * 100
        return None

    @property
    def completion_rate(self) -> Optional[float]:
        """Get completion rate based on progress percentage."""
        return float(self.progress_percentage) if self.progress_percentage is not None else None

    @property
    def time_spent_percentage(self) -> Optional[float]:
        """Get time spent percentage."""
        if self.estimated_hours and self.actual_hours:
            return (self.actual_hours / self.estimated_hours) * 100
        return None

    @property
    def is_epic(self) -> bool:
        """Check if task is an epic (has subtasks)."""
        return bool(self.subtasks)

    @property
    def is_subtask(self) -> bool:
        """Check if task is a subtask (has parent epic)."""
        return self.epic_id is not None

    @property
    def status_color(self) -> str:
        """Get status color for UI."""
        status_colors = {
            TaskStatus.TODO.value: "gray",
            TaskStatus.IN_PROGRESS.value: "blue",
            TaskStatus.IN_REVIEW.value: "yellow",
            TaskStatus.DONE.value: "green",
            TaskStatus.CANCELLED.value: "red",
            TaskStatus.BLOCKED.value: "orange",
        }
        return status_colors.get(self.status, "gray")

    @property
    def priority_level(self) -> int:
        """Get priority as numeric level."""
        priority_levels = {
            TaskPriority.LOW.value: 1,
            TaskPriority.MEDIUM.value: 2,
            TaskPriority.HIGH.value: 3,
            TaskPriority.URGENT.value: 4,
        }
        return priority_levels.get(self.priority, 2)

    def get_dependency_tasks(self) -> List["Task"]:
        """Get tasks this task depends on."""
        if not self.depends_on:
            return []

        from sqlalchemy.orm import Session
        
        session = Session.object_session(self)
        if not session:
            return []
            
        stmt = select(Task).where(
            Task.id.in_(self.depends_on),
            Task.project_id == self.project_id,
            Task.deleted_at.is_(None)
        )
        return list(session.execute(stmt).scalars().all())

    def get_blocked_tasks(self) -> List["Task"]:
        """Get tasks blocked by this task."""
        if not self.blocks:
            return []

        from sqlalchemy.orm import Session
        
        session = Session.object_session(self)
        if not session:
            return []
            
        stmt = select(Task).where(
            Task.id.in_(self.blocks),
            Task.project_id == self.project_id,
            Task.deleted_at.is_(None)
        )
        return list(session.execute(stmt).scalars().all())

    def can_start(self) -> bool:
        """Check if task can be started (all dependencies completed)."""
        if not self.depends_on:
            return True

        dependencies = self.get_dependency_tasks()
        return all(dep.status == TaskStatus.DONE.value for dep in dependencies)

    def get_blocked_by_tasks(self) -> List["Task"]:
        """Get tasks that are blocking this task."""
        if not self.depends_on:
            return []

        dependencies = self.get_dependency_tasks()
        return [dep for dep in dependencies if dep.status != TaskStatus.DONE.value]

    def add_dependency(self, task_id: int) -> None:
        """Add a dependency to this task."""
        if not self.depends_on:
            self.depends_on = []
        if task_id not in self.depends_on:
            self.depends_on.append(task_id)

    def remove_dependency(self, task_id: int) -> None:
        """Remove a dependency from this task."""
        if self.depends_on and task_id in self.depends_on:
            self.depends_on.remove(task_id)

    def add_blocked_task(self, task_id: int) -> None:
        """Add a task that this task blocks."""
        if not self.blocks:
            self.blocks = []
        if task_id not in self.blocks:
            self.blocks.append(task_id)

    def remove_blocked_task(self, task_id: int) -> None:
        """Remove a task that this task blocks."""
        if self.blocks and task_id in self.blocks:
            self.blocks.remove(task_id)

    def add_tag(self, tag: str) -> None:
        """Add a tag to this task."""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from this task."""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)

    def set_label(self, key: str, value: str) -> None:
        """Set a label on this task."""
        if self.labels is None:
            self.labels = {}
        self.labels[key] = value

    def remove_label(self, key: str) -> None:
        """Remove a label from this task."""
        if self.labels is not None and key in self.labels:
            del self.labels[key]

    def update_progress(self, percentage: int) -> None:
        """Update task progress percentage."""
        if 0 <= percentage <= 100:
            self.progress_percentage = percentage
            if percentage == 100 and self.status != TaskStatus.DONE.value:
                self.status = TaskStatus.DONE.value
                self.completed_date = datetime.utcnow()

    def start_task(self) -> None:
        """Start the task."""
        if self.can_start():
            self.status = TaskStatus.IN_PROGRESS.value
            if not self.start_date:
                self.start_date = date.today()
        else:
            raise ValueError("Task cannot be started due to incomplete dependencies")

    def complete_task(self) -> None:
        """Complete the task."""
        self.status = TaskStatus.DONE.value
        self.progress_percentage = 100
        self.completed_date = datetime.utcnow()

    def cancel_task(self) -> None:
        """Cancel the task."""
        self.status = TaskStatus.CANCELLED.value
        self.completed_date = datetime.utcnow()

    def block_task(self) -> None:
        """Block the task."""
        self.status = TaskStatus.BLOCKED.value

    def unblock_task(self) -> None:
        """Unblock the task."""
        if self.status == TaskStatus.BLOCKED.value:
            self.status = TaskStatus.TODO.value

    def get_summary(self) -> Dict[str, Any]:
        """Get task summary for dashboard."""
        return {
            "id": self.id,
            "title": self.title,
            "code": self.code,
            "status": self.status,
            "priority": self.priority,
            "task_type": self.task_type,
            "progress_percentage": self.progress_percentage,
            "is_overdue": self.is_overdue,
            "days_remaining": self.days_remaining,
            "hours_usage_percentage": self.hours_usage_percentage,
            "assignee_name": self.assignee.full_name if self.assignee else None,
            "reporter_name": self.reporter.full_name if self.reporter else None,
            "project_name": self.project.name if self.project else None,
            "status_color": self.status_color,
            "priority_level": self.priority_level,
            "is_epic": self.is_epic,
            "is_subtask": self.is_subtask,
            "can_start": self.can_start(),
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "due_date": self.due_date,
            "tags": self.tags,
            "labels": self.labels,
        }
