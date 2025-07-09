"""Project milestone model implementation (stub for type checking)."""

from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.project import Project
from app.models.base import SoftDeletableModel


class MilestoneStatus(Enum):
    """Project milestone status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class ProjectMilestone(SoftDeletableModel):
    """Project milestone model (stub implementation)."""

    __tablename__ = "project_milestones"

    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=MilestoneStatus.PENDING.value)
    completion_percentage: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    planned_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_overdue: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Additional fields for completeness
    deliverables: Mapped[Optional[List[str]]] = mapped_column(
        JSON, nullable=True, default=list, comment="List of deliverables"
    )
    dependencies: Mapped[Optional[List[int]]] = mapped_column(
        JSON, nullable=True, default=list, comment="List of dependent milestone IDs"
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    assigned_to: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project", back_populates="milestones", lazy="select"
    )

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
    def is_completed(self) -> bool:
        """Check if milestone is completed."""
        return self.status == MilestoneStatus.COMPLETED.value
