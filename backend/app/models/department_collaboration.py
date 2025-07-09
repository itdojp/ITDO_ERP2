"""Department collaboration agreement model."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel
from app.types import DepartmentId, UserId

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.user import User


class DepartmentCollaboration(SoftDeletableModel):
    """Department collaboration agreement model."""

    __tablename__ = "department_collaborations"

    # Department A (initiator)
    department_a_id: Mapped[DepartmentId] = mapped_column(
        Integer,
        ForeignKey("departments.id"),
        nullable=False,
        index=True,
        comment="First department in collaboration",
    )

    # Department B (partner)
    department_b_id: Mapped[DepartmentId] = mapped_column(
        Integer,
        ForeignKey("departments.id"),
        nullable=False,
        index=True,
        comment="Second department in collaboration",
    )

    # Type of collaboration
    collaboration_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of collaboration (project_sharing, resource_sharing, etc.)",
    )

    # Description
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Description of the collaboration agreement",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether collaboration is currently active",
    )

    # Approval status
    approval_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        comment="Approval status: pending, approved, rejected",
    )

    # Dates
    effective_from: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="When collaboration becomes effective",
    )

    effective_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="When collaboration expires",
    )

    # Approvers
    approved_by_a: Mapped[Optional[UserId]] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="User who approved from department A",
    )

    approved_by_b: Mapped[Optional[UserId]] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="User who approved from department B",
    )

    # Relationships
    department_a: Mapped["Department"] = relationship(
        "Department",
        foreign_keys=[department_a_id],
        back_populates="collaborations_initiated",
        lazy="joined",
    )

    department_b: Mapped["Department"] = relationship(
        "Department",
        foreign_keys=[department_b_id],
        back_populates="collaborations_received",
        lazy="joined",
    )

    approved_by_a_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[approved_by_a],
        lazy="joined",
    )

    approved_by_b_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[approved_by_b],
        lazy="joined",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<DepartmentCollaboration(id={self.id}, "
            f"dept_a={self.department_a_id}, dept_b={self.department_b_id}, "
            f"type='{self.collaboration_type}', active={self.is_active})>"
        )

    @property
    def is_fully_approved(self) -> bool:
        """Check if collaboration is fully approved by both departments."""
        return (
            self.approval_status == "approved"
            and self.approved_by_a is not None
            and self.approved_by_b is not None
        )

    @property
    def is_pending_approval(self) -> bool:
        """Check if collaboration is pending approval."""
        return self.approval_status == "pending"

    @property
    def is_effective(self) -> bool:
        """Check if collaboration is currently effective."""
        now = datetime.utcnow()
        
        # Must be active and approved
        if not self.is_active or not self.is_fully_approved:
            return False
        
        # Check effective dates
        if self.effective_from and now < self.effective_from:
            return False
        
        if self.effective_until and now > self.effective_until:
            return False
        
        return True

    def get_other_department_id(self, department_id: DepartmentId) -> Optional[DepartmentId]:
        """Get the other department ID in the collaboration."""
        if self.department_a_id == department_id:
            return self.department_b_id
        elif self.department_b_id == department_id:
            return self.department_a_id
        return None

    def involves_department(self, department_id: DepartmentId) -> bool:
        """Check if this collaboration involves the given department."""
        return department_id in [self.department_a_id, self.department_b_id]


# Predefined collaboration types
COLLABORATION_TYPES = [
    "project_sharing",      # Share projects between departments
    "resource_sharing",     # Share resources (people, equipment)
    "data_sharing",         # Share data and information
    "reporting",           # Joint reporting and analytics
    "system_integration",  # Technical system integration
    "full_access",         # Full collaboration access
    "temporary_project",   # Temporary project-based collaboration
    "budget_sharing",      # Share budget and financial resources
]