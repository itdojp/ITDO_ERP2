"""Role and UserRole models implementation."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditableModel, BaseModel, SoftDeletableModel
from app.types import DepartmentId, OrganizationId, RoleId, UserId

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.organization import Organization
    from app.models.permission import Permission
    from app.models.user import User


class Role(SoftDeletableModel):
    """Role model representing a set of permissions."""

    __tablename__ = "roles"

    # Basic fields
    code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="Unique role code"
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Role display name"
    )
    name_en: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="Role name in English"
    )

    # Role details
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Role description"
    )
    role_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="custom",
        comment="Type of role (system, organization, custom)",
    )

    # Organization scope
    organization_id: Mapped[OrganizationId | None] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=True,
        index=True,
        comment="Organization ID if role is organization-specific",
    )

    # Hierarchy
    parent_id: Mapped[RoleId | None] = mapped_column(
        Integer,
        ForeignKey("roles.id"),
        nullable=True,
        comment="Parent role ID for role inheritance",
    )

    # Hierarchy metadata
    full_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="/",
        comment="Full path in hierarchy (e.g., /1/2/3)",
    )
    depth: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Depth in hierarchy (0 for root)"
    )

    # Permissions (JSON array)
    permissions: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict, comment="Role permissions in JSON format"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether the role is active",
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this is a system role (cannot be modified)",
    )

    # Display
    display_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Display order for UI"
    )
    icon: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Icon name or class for UI"
    )
    color: Mapped[str | None] = mapped_column(
        String(7), nullable=True, comment="Color code for UI (hex format)"
    )

    # Relationships
    parent: Mapped[Optional["Role"]] = relationship(
        "Role", remote_side="Role.id", back_populates="child_roles", lazy="joined"
    )
    child_roles: Mapped[list["Role"]] = relationship(
        "Role", back_populates="parent", lazy="select"
    )
    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole", back_populates="role", cascade="all, delete-orphan", lazy="dynamic"
    )
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization", back_populates="roles", lazy="joined"
    )
    users: Mapped[list["User"]] = relationship(
        "User", 
        secondary="user_roles",
        primaryjoin="Role.id == UserRole.role_id",
        secondaryjoin="UserRole.user_id == User.id",
        back_populates="roles", 
        lazy="select",
        overlaps="user_roles"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Role(id={self.id}, code='{self.code}', name='{self.name}')>"

    @property
    def is_inherited(self) -> bool:
        """Check if this role inherits from another role."""
        return self.parent_id is not None

    def get_all_permissions(self) -> dict[str, Any]:
        """Get all permissions including inherited ones."""
        all_permissions = {}

        # Get inherited permissions recursively
        if self.parent:
            all_permissions.update(self.parent.get_all_permissions())

        # Override with own permissions
        all_permissions.update(self.permissions)

        return all_permissions

    def has_permission(self, permission: str) -> bool:
        """Check if role has a specific permission."""
        all_permissions = self.get_all_permissions()
        return permission in all_permissions and all_permissions[permission] is True

    def add_permission(self, permission: str) -> None:
        """Add a permission to the role."""
        if not self.permissions:
            self.permissions = {}
        self.permissions[permission] = True

    def remove_permission(self, permission: str) -> None:
        """Remove a permission from the role."""
        if self.permissions and permission in self.permissions:
            del self.permissions[permission]

    def get_permission_list(self) -> list[str]:
        """Get list of permissions as strings."""
        all_permissions = self.get_all_permissions()
        return [perm for perm, granted in all_permissions.items() if granted]


class UserRole(AuditableModel):
    """Association table for user-role relationships."""

    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "role_id",
            "organization_id",
            name="uq_user_role_org",
        ),
        Index("idx_user_roles_user_id", "user_id"),
        Index("idx_user_roles_role_id", "role_id"),
        Index("idx_user_roles_org_id", "organization_id"),
    )

    # Foreign keys
    user_id: Mapped[UserId] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="User ID"
    )
    role_id: Mapped[RoleId] = mapped_column(
        Integer, ForeignKey("roles.id"), nullable=False, comment="Role ID"
    )
    organization_id: Mapped[OrganizationId] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        comment="Organization context",
    )

    # Department context (optional)
    department_id: Mapped[DepartmentId | None] = mapped_column(
        Integer,
        ForeignKey("departments.id"),
        nullable=True,
        comment="Department context (optional)",
    )

    # Assignment metadata
    assigned_by: Mapped[UserId | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="User who assigned the role",
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When the role was assigned",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the role assignment expires",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the role assignment is active",
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this is the primary role for the user",
    )

    # Additional metadata
    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Additional notes about the assignment"
    )

    # Approval workflow
    approval_status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Approval status (pending, approved, rejected)",
    )
    approved_by: Mapped[UserId | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="User who approved the assignment",
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the assignment was approved",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="user_roles", lazy="joined"
    )
    role: Mapped["Role"] = relationship(
        "Role", foreign_keys=[role_id], back_populates="user_roles", lazy="joined"
    )
    organization: Mapped["Organization"] = relationship(
        "Organization", foreign_keys=[organization_id], lazy="joined"
    )
    department: Mapped["Department"] = relationship(
        "Department", foreign_keys=[department_id], lazy="joined"
    )

    # User references
    assigned_by_user: Mapped["User"] = relationship(
        "User", foreign_keys=[assigned_by], lazy="joined"
    )
    approved_by_user: Mapped["User"] = relationship(
        "User", foreign_keys=[approved_by], lazy="joined"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id}, org_id={self.organization_id})>"

    @property
    def is_expired(self) -> bool:
        """Check if the role assignment has expired."""
        if self.expires_at is None:
            return False
        return self.expires_at < datetime.now(UTC)

    @property
    def is_valid(self) -> bool:
        """Check if the role assignment is currently valid."""
        return self.is_active and not self.is_expired

    def get_effective_permissions(self) -> dict[str, Any]:
        """Get effective permissions for this role assignment."""
        if not self.is_valid:
            return {}
        
        return self.role.get_all_permissions()
