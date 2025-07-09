"""Task model for project task management."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel

if TYPE_CHECKING:
    from app.models.department_task import DepartmentTask
    from app.models.project import Project
    from app.models.user import User


class Task(SoftDeletableModel):
    """Task model for project task management."""

    __tablename__ = "tasks"

    # Basic fields
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    priority: Mapped[str] = mapped_column(String(20), default="medium")

    # Related fields
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    parent_task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tasks.id"))

    # Date fields
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Additional fields
    estimated_hours: Mapped[Optional[float]] = mapped_column()
    actual_hours: Mapped[Optional[float]] = mapped_column()

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    assignee: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[assignee_id], back_populates="assigned_tasks"
    )
    reporter: Mapped["User"] = relationship(
        "User", foreign_keys=[reporter_id], back_populates="reported_tasks"
    )
    parent_task: Mapped[Optional["Task"]] = relationship(
        "Task", remote_side="Task.id", back_populates="subtasks"
    )
    subtasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="parent_task", cascade="all, delete-orphan"
    )
    department_assignments: Mapped[list["DepartmentTask"]] = relationship(
        "DepartmentTask", back_populates="task", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title={self.title}, status={self.status})>"
