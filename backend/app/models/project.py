"""Project model implementation with enhanced features."""

from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel
from app.types import DepartmentId, OrganizationId, UserId

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.organization import Organization
    from app.models.project_member import ProjectMember
    from app.models.project_milestone import ProjectMilestone
    from app.models.task import Task
    from app.models.user import User


class ProjectStatus(str, Enum):
    """Project status enumeration."""

    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class ProjectPriority(str, Enum):
    """Project priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProjectType(str, Enum):
    """Project type enumeration."""

    INTERNAL = "internal"
    CLIENT = "client"
    RESEARCH = "research"
    MAINTENANCE = "maintenance"
    INNOVATION = "innovation"


class Project(SoftDeletableModel):
    """Enhanced Project model with comprehensive features."""

    __tablename__ = "projects"

    # Basic fields
    code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True,
        comment="Unique project code"
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Project name"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Project description"
    )

    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True,
        comment="Organization ID"
    )
    department_id: Mapped[Optional[DepartmentId]] = mapped_column(
        Integer, ForeignKey("departments.id"), nullable=True, index=True,
        comment="Department ID"
    )
    owner_id: Mapped[UserId] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True,
        comment="Project owner ID"
    )
    manager_id: Mapped[Optional[UserId]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True,
        comment="Project manager ID"
    )

    # Project details
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ProjectStatus.PLANNING.value,
        index=True, comment="Project status"
    )
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ProjectPriority.MEDIUM.value,
        index=True, comment="Project priority"
    )
    project_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ProjectType.INTERNAL.value,
        comment="Project type"
    )

    # Timeline fields
    start_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Planned start date"
    )
    end_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Planned end date"
    )
    actual_start_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Actual start date"
    )
    actual_end_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Actual end date"
    )

    # Budget fields
    budget: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Total budget"
    )
    spent_budget: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=0.0, comment="Budget spent"
    )
    estimated_hours: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Estimated hours"
    )
    actual_hours: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=0.0, comment="Actual hours worked"
    )

    # Progress tracking
    progress_percentage: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Progress percentage (0-100)"
    )
    completion_date: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Completion date"
    )

    # Status tracking
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True,
        comment="Whether project is active"
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="Whether project is visible to all organization members"
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True,
        comment="Whether project is archived"
    )

    # Metadata
    tags: Mapped[Optional[List[str]]] = mapped_column(
        JSON, nullable=True, default=list, comment="Project tags"
    )
    settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default=dict, comment="Project settings"
    )
    project_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default=dict, comment="Additional project metadata"
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", lazy="joined"
    )
    department: Mapped[Optional["Department"]] = relationship(
        "Department", lazy="joined"
    )
    owner: Mapped["User"] = relationship(
        "User", foreign_keys=[owner_id], lazy="joined"
    )
    manager: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[manager_id], lazy="select"
    )
    members: Mapped[List["ProjectMember"]] = relationship(
        "ProjectMember", back_populates="project", lazy="select",
        cascade="all, delete-orphan"
    )
    milestones: Mapped[List["ProjectMilestone"]] = relationship(
        "ProjectMilestone", back_populates="project", lazy="select",
        cascade="all, delete-orphan"
    )
    tasks: Mapped[List["Task"]] = relationship(
        "Task", back_populates="project", lazy="select",
        cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("code", "organization_id", name="uq_project_code_org"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Project(id={self.id}, code='{self.code}', name='{self.name}')>"

    @property
    def is_overdue(self) -> bool:
        """Check if project is overdue."""
        if self.end_date and self.status in [
            ProjectStatus.PLANNING.value,
            ProjectStatus.IN_PROGRESS.value,
        ]:
            today = date.today()
            return self.end_date < today
        return False

    @property
    def days_remaining(self) -> Optional[int]:
        """Get days remaining until planned end date."""
        if self.end_date and self.status not in [
            ProjectStatus.COMPLETED.value,
            ProjectStatus.CANCELLED.value,
        ]:
            today = date.today()
            delta = self.end_date - today
            return delta.days
        return None

    @property
    def budget_usage_percentage(self) -> Optional[float]:
        """Get budget usage percentage."""
        if self.budget and (self.spent_budget or 0) > 0:
            return float(((self.spent_budget or 0) / self.budget) * 100)
        return None

    @property
    def hours_usage_percentage(self) -> Optional[float]:
        """Get hours usage percentage."""
        if self.estimated_hours and (self.actual_hours or 0) > 0:
            return float(((self.actual_hours or 0) / self.estimated_hours) * 100)
        return None

    @property
    def is_on_schedule(self) -> bool:
        """Check if project is on schedule."""
        if not self.start_date or not self.end_date:
            return True

        today = date.today()
        if today < self.start_date:
            return True  # Not started yet

        if self.status == ProjectStatus.COMPLETED.value:
            return True  # Completed projects are considered on schedule

        # Calculate expected progress based on time elapsed
        total_days = (self.end_date - self.start_date).days
        if total_days <= 0:
            return True

        elapsed_days = (today - self.start_date).days
        expected_progress = min(100, (elapsed_days / total_days) * 100)

        # Allow 10% variance
        return (self.progress_percentage or 0) >= (expected_progress - 10)

    @property
    def status_color(self) -> str:
        """Get status color for UI."""
        status_colors = {
            ProjectStatus.PLANNING.value: "blue",
            ProjectStatus.IN_PROGRESS.value: "green",
            ProjectStatus.ON_HOLD.value: "yellow",
            ProjectStatus.COMPLETED.value: "green",
            ProjectStatus.CANCELLED.value: "red",
            ProjectStatus.ARCHIVED.value: "gray",
        }
        return status_colors.get(self.status, "gray")

    @property
    def priority_level(self) -> int:
        """Get priority as numeric level."""
        priority_levels = {
            ProjectPriority.LOW.value: 1,
            ProjectPriority.MEDIUM.value: 2,
            ProjectPriority.HIGH.value: 3,
            ProjectPriority.CRITICAL.value: 4,
        }
        return priority_levels.get(self.priority, 2)

    def get_member_count(self) -> int:
        """Get total number of project members."""
        return len([m for m in self.members if m.is_active])

    def get_active_tasks_count(self) -> int:
        """Get count of active tasks."""
        from app.models.task import TaskStatus
        return len([t for t in self.tasks if t.status in [
            TaskStatus.TODO.value,
            TaskStatus.IN_PROGRESS.value,
            TaskStatus.IN_REVIEW.value,
            TaskStatus.BLOCKED.value,
        ] and t.is_active])

    def get_completed_tasks_count(self) -> int:
        """Get count of completed tasks."""
        from app.models.task import TaskStatus
        return len([t for t in self.tasks if t.status == TaskStatus.DONE.value and t.is_active])

    def get_total_tasks_count(self) -> int:
        """Get count of total tasks."""
        return len([t for t in self.tasks if t.is_active])

    def get_overdue_tasks_count(self) -> int:
        """Get count of overdue tasks."""
        return len([t for t in self.tasks if t.is_overdue and t.is_active])

    def get_tasks_by_status(self, status: str) -> List["Task"]:
        """Get tasks by status."""
        return [t for t in self.tasks if t.status == status and t.is_active]

    def get_tasks_by_assignee(self, assignee_id: int) -> List["Task"]:
        """Get tasks by assignee."""
        return [t for t in self.tasks if t.assignee_id == assignee_id and t.is_active]

    def get_task_completion_rate(self) -> float:
        """Get task completion rate as percentage."""
        total_tasks = self.get_total_tasks_count()
        if total_tasks == 0:
            return 0.0
        completed_tasks = self.get_completed_tasks_count()
        return (completed_tasks / total_tasks) * 100

    def get_milestone_count(self) -> int:
        """Get total number of milestones."""
        return len(self.milestones)

    def get_completed_milestones_count(self) -> int:
        """Get count of completed milestones."""
        return len([m for m in self.milestones if m.is_completed])

    def update_progress(self) -> None:
        """Update project progress based on tasks and milestones."""
        total_tasks = self.get_total_tasks_count()
        completed_tasks = self.get_completed_tasks_count()

        if total_tasks > 0:
            task_progress = (completed_tasks / total_tasks) * 100

            # Weight tasks vs milestones (70% tasks, 30% milestones)
            total_milestones = self.get_milestone_count()
            if total_milestones > 0:
                completed_milestones = self.get_completed_milestones_count()
                milestone_progress = (completed_milestones / total_milestones) * 100
                self.progress_percentage = int((task_progress * 0.7) + (milestone_progress * 0.3))
            else:
                self.progress_percentage = int(task_progress)
        else:
            # If no tasks, base progress on milestones only
            total_milestones = self.get_milestone_count()
            if total_milestones > 0:
                completed_milestones = self.get_completed_milestones_count()
                self.progress_percentage = int((completed_milestones / total_milestones) * 100)
            else:
                self.progress_percentage = 0

        # Ensure progress doesn't exceed 100%
        self.progress_percentage = min(self.progress_percentage, 100)

    def can_be_deleted(self) -> bool:
        """Check if project can be deleted."""
        return self.status in [
            ProjectStatus.PLANNING.value,
            ProjectStatus.CANCELLED.value,
        ]

    def can_be_archived(self) -> bool:
        """Check if project can be archived."""
        return self.status in [
            ProjectStatus.COMPLETED.value,
            ProjectStatus.CANCELLED.value,
        ]

    def get_health_status(self) -> str:
        """Get project health status."""
        if self.status == ProjectStatus.COMPLETED.value:
            return "excellent"

        if self.status in [ProjectStatus.CANCELLED.value, ProjectStatus.ARCHIVED.value]:
            return "poor"

        if self.is_overdue:
            return "poor"

        if not self.is_on_schedule:
            return "fair"

        if self.budget_usage_percentage and self.budget_usage_percentage > 90:
            return "fair"

        return "good"

    def get_summary(self) -> Dict[str, Any]:
        """Get project summary for dashboard."""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "progress_percentage": self.progress_percentage,
            "is_overdue": self.is_overdue,
            "days_remaining": self.days_remaining,
            "budget_usage_percentage": self.budget_usage_percentage,
            "member_count": self.get_member_count(),
            "milestone_count": self.get_milestone_count(),
            "health_status": self.get_health_status(),
            "is_on_schedule": self.is_on_schedule,
            "status_color": self.status_color,
        }
