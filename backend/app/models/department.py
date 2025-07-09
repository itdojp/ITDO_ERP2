"""Department model implementation."""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel
from app.types import DepartmentId, OrganizationId, UserId

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class Department(SoftDeletableModel):
    """Department model representing a division within an organization."""

    __tablename__ = "departments"

    # Basic fields
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Department code (unique within organization)",
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Department name"
    )
    name_kana: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="Department name in Katakana"
    )
    name_en: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="Department name in English"
    )
    short_name: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Short name or abbreviation"
    )

    # Organization relationship
    organization_id: Mapped[OrganizationId] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
        comment="Organization this department belongs to",
    )

    # Hierarchy
    parent_id: Mapped[Optional[DepartmentId]] = mapped_column(
        Integer,
        ForeignKey("departments.id"),
        nullable=True,
        index=True,
        comment="Parent department ID for sub-departments",
    )

    # Department head
    manager_id: Mapped[Optional[UserId]] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="Department manager/head user ID",
    )

    # Contact information
    phone: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Department phone number"
    )
    fax: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Department fax number"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Department email address"
    )

    # Location
    location: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Physical location (building, floor, etc.)"
    )

    # Budget and headcount
    budget: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Annual budget in JPY"
    )
    headcount_limit: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Maximum allowed headcount"
    )

    # Status and type
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether the department is active",
    )
    department_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Type of department (e.g., sales, engineering, admin)",
    )

    # Cost center
    cost_center_code: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Cost center code for accounting"
    )

    # Display order
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Display order within the same level",
    )

    # Hierarchy management fields
    path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        index=True,
        comment="Materialized path for efficient hierarchy queries (e.g., '1.2.3')",
    )
    depth: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        index=True,
        comment="Depth level in hierarchy (0 for root departments)",
    )

    # Additional fields
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Department description or mission"
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="departments", lazy="joined"
    )
    parent: Mapped[Optional["Department"]] = relationship(
        "Department",
        remote_side="Department.id",
        back_populates="sub_departments",
        lazy="joined",
    )
    sub_departments: Mapped[List["Department"]] = relationship(
        "Department", back_populates="parent", lazy="select"
    )
    manager: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[manager_id], lazy="joined"
    )
    users = relationship(
        "User",
        secondary="user_roles",
        primaryjoin="Department.id == UserRole.department_id",
        secondaryjoin="UserRole.user_id == User.id",
        viewonly=True,
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Department(id={self.id}, code='{self.code}', "
            f"name='{self.name}', org_id={self.organization_id})>"
        )

    @property
    def full_code(self) -> str:
        """Get full department code including organization code."""
        return f"{self.organization.code}-{self.code}"

    @property
    def is_sub_department(self) -> bool:
        """Check if this is a sub-department."""
        return self.parent_id is not None

    @property
    def is_parent_department(self) -> bool:
        """Check if this department has sub-departments."""
        return len(self.sub_departments) > 0

    @property
    def current_headcount(self) -> int:
        """Get current number of users in the department."""
        return self.users.filter_by(is_active=True).count()  # type: ignore[no-any-return]

    @property
    def is_over_headcount(self) -> bool:
        """Check if department is over headcount limit."""
        if self.headcount_limit is None:
            return False
        return self.current_headcount > self.headcount_limit

    def get_all_sub_departments(self) -> List["Department"]:
        """Get all sub-departments recursively."""
        result = []
        for sub_dept in self.sub_departments:
            result.append(sub_dept)
            result.extend(sub_dept.get_all_sub_departments())
        return result

    def get_hierarchy_path(self) -> List["Department"]:
        """Get the full hierarchy path from root to this department."""
        path = [self]
        current = self
        while current.parent:
            path.insert(0, current.parent)
            current = current.parent
        return path

    def get_all_users(self, include_sub_departments: bool = False) -> List["User"]:
        """Get all users in this department and optionally in sub-departments."""
        users = list(self.users.filter_by(is_active=True).all())

        if include_sub_departments:
            for sub_dept in self.get_all_sub_departments():
                users.extend(sub_dept.users.filter_by(is_active=True).all())

        # Remove duplicates while preserving order
        seen = set()
        unique_users = []
        for user in users:
            if user.id not in seen:
                seen.add(user.id)
                unique_users.append(user)

        return unique_users

    def update_path(self) -> None:
        """Update the materialized path for this department."""
        if self.parent_id is None:
            self.path = str(self.id)
            self.depth = 0
        else:
            parent_path = self.parent.path or str(self.parent_id)
            self.path = f"{parent_path}.{self.id}"
            self.depth = (self.parent.depth or 0) + 1

    def update_subtree_paths(self) -> None:
        """Update paths for all sub-departments recursively."""
        for sub_dept in self.sub_departments:
            sub_dept.update_path()
            sub_dept.update_subtree_paths()
