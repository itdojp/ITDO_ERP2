"""Department model implementation."""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel
from app.types import DepartmentId, OrganizationId, UserId

if TYPE_CHECKING:
    from app.models.department_collaboration import DepartmentCollaboration
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
    
    # Hierarchical structure fields
    path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="",
        index=True,
        comment="Materialized path for hierarchical queries",
    )
    depth: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        index=True,
        comment="Depth in hierarchy (0 for root)",
    )

    # Permission inheritance
    inherit_permissions: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether to inherit permissions from parent departments",
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
    
    # Collaboration relationships
    collaborations_initiated: Mapped[List["DepartmentCollaboration"]] = relationship(
        "DepartmentCollaboration",
        foreign_keys="DepartmentCollaboration.department_a_id",
        back_populates="department_a",
        lazy="select",
    )
    
    collaborations_received: Mapped[List["DepartmentCollaboration"]] = relationship(
        "DepartmentCollaboration",
        foreign_keys="DepartmentCollaboration.department_b_id",
        back_populates="department_b",
        lazy="select",
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
        """Update the materialized path based on parent."""
        if self.parent_id is None:
            self.path = str(self.id)
            self.depth = 0
        else:
            if self.parent:
                self.path = f"{self.parent.path}.{self.id}"
                self.depth = self.parent.depth + 1
            else:
                # Fallback if parent not loaded
                from sqlalchemy import select
                from sqlalchemy.orm import object_session
                
                session = object_session(self)
                if session:
                    parent = session.scalar(
                        select(Department).where(Department.id == self.parent_id)
                    )
                    if parent:
                        self.path = f"{parent.path}.{self.id}"
                        self.depth = parent.depth + 1
    
    def update_subtree_paths(self) -> None:
        """Update paths for all descendants after a move."""
        from sqlalchemy import select, text
        from sqlalchemy.orm import object_session
        
        session = object_session(self)
        if not session:
            return
        
        # First, get the old path before we updated it
        # We need to find all descendants based on the old path pattern
        # Since we already updated self.path, we need to reconstruct the old path
        
        # Get all departments that have this department in their path
        # This query finds all descendants
        descendants = session.scalars(
            select(Department)
            .where(Department.path.contains(str(self.id)))
            .where(Department.id != self.id)
            .order_by(Department.depth, Department.id)
        ).all()
        
        # Update each descendant's path and depth
        for desc in descendants:
            # Check if this department is actually in the descendant's path
            path_parts = desc.path.split(".")
            if str(self.id) in path_parts:
                # Find the position of self.id in the path
                self_index = path_parts.index(str(self.id))
                
                # Rebuild the path with the new prefix
                # Get the parts after self.id in the descendant's path
                parts_after_self = path_parts[self_index + 1:]
                
                # The new path is self's new path + the parts after self
                if parts_after_self:
                    desc.path = f"{self.path}.{'.'.join(parts_after_self)}"
                else:
                    # This descendant is a direct child of self
                    desc.path = self.path
                
                desc.depth = desc.path.count(".")
    
    def get_ancestors_ids(self) -> List[int]:
        """Get list of ancestor IDs from the path."""
        if not self.path:
            return []
        
        path_parts = self.path.split(".")
        # Exclude self (last element)
        return [int(id_str) for id_str in path_parts[:-1]]
    
    def is_ancestor_of(self, department_id: int) -> bool:
        """Check if this department is an ancestor of the given department."""
        from sqlalchemy import select
        from sqlalchemy.orm import object_session
        
        session = object_session(self)
        if not session:
            return False
        
        other = session.scalar(
            select(Department).where(Department.id == department_id)
        )
        if not other:
            return False
        
        return other.path.startswith(f"{self.path}.")
    
    def is_descendant_of(self, department_id: int) -> bool:
        """Check if this department is a descendant of the given department."""
        from sqlalchemy import select
        from sqlalchemy.orm import object_session
        
        session = object_session(self)
        if not session:
            return False
        
        other = session.scalar(
            select(Department).where(Department.id == department_id)
        )
        if not other:
            return False
        
        return self.path.startswith(f"{other.path}.")
