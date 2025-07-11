"""Role and UserRole models implementation."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

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
    name_en: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="Role name in English"
    )

    # Role details
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Role description"
    )
    role_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="custom",
        comment="Type of role (system, organization, custom)",
    )

    # Organization scope
    organization_id: Mapped[Optional[OrganizationId]] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=True,
        index=True,
        comment="Organization ID if role is organization-specific",
    )

    # Hierarchy
    parent_id: Mapped[Optional[RoleId]] = mapped_column(
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
    permissions: Mapped[Dict[str, Any]] = mapped_column(
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
    icon: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Icon name or class for UI"
    )
    color: Mapped[Optional[str]] = mapped_column(
        String(7), nullable=True, comment="Color code for UI (hex format)"
    )

    # Relationships
    parent: Mapped[Optional["Role"]] = relationship(
        "Role", remote_side="Role.id", back_populates="child_roles", lazy="joined"
    )
    child_roles: Mapped[List["Role"]] = relationship(
        "Role", back_populates="parent", lazy="select"
    )
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole", back_populates="role", cascade="all, delete-orphan", lazy="dynamic"
    )
    role_permissions: Mapped[List["RolePermission"]] = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Role(id={self.id}, code='{self.code}', name='{self.name}')>"

    @property
    def is_inherited(self) -> bool:
        """Check if this role inherits from another role."""
        return self.parent_id is not None

    def get_all_permissions(self) -> Dict[str, Any]:
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

        # Handle nested permissions (e.g., "users.create")
        parts = permission.split(".")
        current = all_permissions

        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]

        return bool(current)

    def get_users_count(self) -> int:
        """Get count of users with this role."""
        return len([ur for ur in self.user_roles if ur.is_active])


class UserRole(AuditableModel):
    """Association between users and roles with organizational context."""

    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "role_id",
            "organization_id",
            "department_id",
            name="uq_user_role_org_dept",
        ),
        # Note: expires_at and is_active already have index=True in column definitions
    )

    # Foreign keys
    user_id: Mapped[UserId] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="User ID"
    )
    role_id: Mapped[RoleId] = mapped_column(
        Integer, ForeignKey("roles.id"), nullable=False, index=True, comment="Role ID"
    )
    organization_id: Mapped[OrganizationId] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
        comment="Organization context for the role",
    )
    department_id: Mapped[Optional[DepartmentId]] = mapped_column(
        Integer,
        ForeignKey("departments.id"),
        nullable=True,
        index=True,
        comment="Department context (optional)",
    )

    # Assignment details
    assigned_by: Mapped[Optional[UserId]] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="User who assigned this role",
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When the role was assigned",
    )

    # Validity period
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When the role becomes valid",
    )
    valid_to: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the role validity ends (deprecated, use expires_at)",
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="When the role expires (null = never)",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether the role assignment is active",
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this is the user's primary role",
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Notes about this role assignment"
    )

    # Approval workflow
    approval_status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Approval status (pending, approved, rejected)",
    )
    approved_by: Mapped[Optional[UserId]] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="User who approved this role assignment",
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="When the role was approved"
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="user_roles"
    )
    role: Mapped["Role"] = relationship(
        "Role", back_populates="user_roles", lazy="joined"
    )
    organization: Mapped["Organization"] = relationship("Organization", lazy="joined")
    department: Mapped[Optional["Department"]] = relationship(
        "Department", lazy="joined"
    )
    assigned_by_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[assigned_by], lazy="joined"
    )
    approved_by_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[approved_by], lazy="joined"
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<UserRole(user_id={self.user_id}, role_id={self.role_id}, "
            f"org_id={self.organization_id}, dept_id={self.department_id})>"
        )

    @property
    def is_expired(self) -> bool:
        """Check if role assignment is expired."""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if role assignment is currently valid."""
        now = datetime.now(timezone.utc)

        # Check if active
        if not self.is_active:
            return False

        # Check validity period
        if now < self.valid_from:
            return False

        # Check expiration
        if self.expires_at and now > self.expires_at:
            return False

        # Check approval if required
        if self.approval_status == "pending":
            return False

        return True

    @property
    def days_until_expiry(self) -> Optional[int]:
        """Get days until expiry (None if no expiry date)."""
        if not self.expires_at:
            return None

        delta = self.expires_at - datetime.now(timezone.utc)
        return delta.days

    def get_effective_permissions(self) -> Dict[str, Any]:
        """Get effective permissions for this role assignment."""
        if not self.is_valid:
            return {}

        return self.role.get_all_permissions()


class RolePermission(BaseModel):
    """Association table between roles and permissions."""

    __tablename__ = "role_permissions"

    role_id: Mapped[RoleId] = mapped_column(
        Integer, ForeignKey("roles.id"), primary_key=True, comment="Role ID"
    )
    permission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("permissions.id"), primary_key=True, comment="Permission ID"
    )

    # Additional metadata
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When permission was granted",
    )
    granted_by: Mapped[Optional[UserId]] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="User who granted the permission",
    )

    # Relationships
    role: Mapped["Role"] = relationship(
        "Role", back_populates="role_permissions", lazy="joined"
    )
    permission: Mapped["Permission"] = relationship(
        "Permission", back_populates="role_permissions", lazy="joined"
    )

    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions"),
        Index("ix_role_permissions_role_id", "role_id"),
        Index("ix_role_permissions_permission_id", "permission_id"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<RolePermission(role_id={self.role_id}, "
            f"permission_id={self.permission_id})>"
        )
