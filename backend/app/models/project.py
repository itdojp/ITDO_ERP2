"""Project model implementation (stub for type checking)."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel
from app.types import DepartmentId, OrganizationId, UserId

if TYPE_CHECKING:
    from app.models.department import Department  # noqa: F401
    from app.models.organization import Organization  # noqa: F401
    from app.models.task import Task
    from app.models.user import User


class Project(SoftDeletableModel):
    """Project model (stub implementation)."""

    __tablename__ = "projects"

    # Basic fields
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    department_id: Mapped[DepartmentId | None] = mapped_column(
        Integer, ForeignKey("departments.id"), nullable=True
    )
    owner_id: Mapped[UserId] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )

    # Project details
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="planning")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    budget: Mapped[float | None] = mapped_column(Float, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    planned_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_budget: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_cost: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    organization = relationship("Organization", lazy="select")
    department = relationship("Department", lazy="select")
    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_id], lazy="joined")

    # Task relationship
    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="project", cascade="all, delete-orphan"
    )

    # Computed properties for dashboard
    @property
    def progress_percentage(self) -> int:
        """Get project progress percentage."""
        return 0  # Stub

    @property
    def is_overdue(self) -> bool:
        """Check if project is overdue."""
        if self.planned_end_date:
            today = date.today()
            return self.planned_end_date < today and self.status in [
                "planning",
                "in_progress",
            ]
        return False

    @property
    def days_remaining(self) -> int | None:
        """Get days remaining until planned end date."""
        if self.planned_end_date:
            today = date.today()
            delta = self.planned_end_date - today
            return delta.days
        return None

    @property
    def budget_usage_percentage(self) -> float | None:
        """Get budget usage percentage."""
        if self.total_budget and self.actual_cost:
            return float((self.actual_cost / self.total_budget) * 100)
        return None

    @property
    def planned_start_date(self) -> date | None:
        """Get planned start date."""
        return self.start_date

    @property
    def actual_start_date(self) -> date | None:
        """Get actual start date."""
        return self.start_date  # Stub

    @property
    def actual_end_date(self) -> date | None:
        """Get actual end date."""
        return None  # Stub
