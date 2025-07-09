"""Department task assignment model."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel
from app.types import DepartmentId, TaskId, UserId

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.task import Task
    from app.models.user import User


class DepartmentTask(SoftDeletableModel):
    """Department task assignment model."""

    __tablename__ = "department_tasks"

    # Department and task relationship
    department_id: Mapped[DepartmentId] = mapped_column(
        Integer,
        ForeignKey("departments.id"),
        nullable=False,
        index=True,
        comment="Department assigned to task",
    )

    task_id: Mapped[TaskId] = mapped_column(
        Integer,
        ForeignKey("tasks.id"),
        nullable=False,
        index=True,
        comment="Task assigned to department",
    )

    # Assignment type
    assignment_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="department",
        comment="Type: department, inherited, shared, delegated",
    )

    # Visibility and access control
    visibility_scope: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="department",
        comment="Scope: private, department, organization, public",
    )

    # Delegation information
    delegated_from_department_id: Mapped[Optional[DepartmentId]] = mapped_column(
        Integer,
        ForeignKey("departments.id"),
        nullable=True,
        comment="Original department if this is a delegated task",
    )

    delegated_by: Mapped[Optional[UserId]] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="User who delegated the task",
    )

    # Status and dates
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether assignment is active",
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="When task was assigned to department",
    )

    # Notes and comments
    assignment_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Notes about the assignment",
    )

    # Relationships
    department: Mapped["Department"] = relationship(
        "Department",
        foreign_keys=[department_id],
        lazy="joined",
    )

    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="department_assignments",
        lazy="joined",
    )

    delegated_from_department: Mapped[Optional["Department"]] = relationship(
        "Department",
        foreign_keys=[delegated_from_department_id],
        lazy="joined",
    )

    delegated_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[delegated_by],
        lazy="joined",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<DepartmentTask(id={self.id}, "
            f"dept_id={self.department_id}, task_id={self.task_id}, "
            f"type='{self.assignment_type}', active={self.is_active})>"
        )

    @property
    def is_delegated(self) -> bool:
        """Check if this is a delegated task."""
        return self.assignment_type == "delegated" and self.delegated_from_department_id is not None

    @property
    def is_inherited(self) -> bool:
        """Check if this is an inherited task."""
        return self.assignment_type == "inherited"

    @property
    def is_shared(self) -> bool:
        """Check if this is a shared task."""
        return self.assignment_type == "shared"

    def get_assignment_source(self) -> Optional[str]:
        """Get the source of assignment."""
        if self.is_delegated:
            return f"Delegated from department {self.delegated_from_department_id}"
        elif self.is_inherited:
            return "Inherited from parent department"
        elif self.is_shared:
            return "Shared across departments"
        else:
            return "Direct department assignment"


# Predefined assignment types
ASSIGNMENT_TYPES = [
    "department",    # Direct department assignment
    "inherited",     # Inherited from parent department
    "shared",        # Shared between multiple departments
    "delegated",     # Delegated from another department
]

# Predefined visibility scopes
VISIBILITY_SCOPES = [
    "private",       # Only assigned department
    "department",    # Department and sub-departments
    "organization",  # Organization-wide
    "public",        # Public visibility
]