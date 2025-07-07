"""Project milestone model implementation (stub for type checking)."""
from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

if TYPE_CHECKING:
    from app.models.project import Project
from app.models.base import SoftDeletableModel


class ProjectMilestone(SoftDeletableModel):
    """Project milestone model (stub implementation)."""

    __tablename__ = "project_milestones"

    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    completion_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    planned_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_overdue: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Computed properties for dashboard
    @property
    def days_until_due(self) -> int:
        """Get days until due date."""
        if self.due_date:
            today = date.today()
            delta = self.due_date - today
            return delta.days
        return 0

    @property
    def project(self) -> "Project":
        """Get related project (stub)."""
        # This would normally be a relationship
        from app.models.project import Project
        # For now, create a minimal project object
        project = Project()
        project.name = "Stub Project"
        return project
