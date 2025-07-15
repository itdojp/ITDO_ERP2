"""Role model implementation for RBAC (Role-Based Access Control).

This module defines the Role, UserRole, and RolePermission models
for managing roles and permissions in the ITDO ERP System.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
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
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditableModel, Base, SoftDeletableModel
from app.types import DepartmentId, OrganizationId, RoleId, UserId

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.organization import Organization
    from app.models.permission import Permission
    from app.models.permission_inheritance import RoleInheritanceRule
    from app.models.user import User


class Role(SoftDeletableModel):
    """Role model for RBAC."""

    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "code", name="uq_role_org_code"
        ),  # Unique code per org
    )

    # Basic fields
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Unique role code within organization",
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Role display name"
    )
    name_en: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="Role name in English"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Role description"
    )

    # Type and hierarchy
    role_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="custom",
        comment="Role type (system, organization, custom)",
    )
    parent_id: Mapped[RoleId | None] = mapped_column(
        Integer,
        ForeignKey("roles.id"),
        nullable=True,
        index=True,
        comment="Parent role for inheritance",
    )
    level: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Role hierarchy level"
    )
    full_path: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Full hierarchical path"
    )
    depth: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Hierarchy depth"
    )

    # Organization scope
    organization_id: Mapped[OrganizationId | None] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=True,
        index=True,
        comment="Organization this role belongs to",
    )

    # Department scope (optional)
    department_id: Mapped[DepartmentId | None] = mapped_column(
        Integer,
        ForeignKey("departments.id"),
        nullable=True,
        index=True,
        comment="Department scope for this role",
    )

    # Scope and permissions
    scope: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="organization",
        comment="Role scope (system, organization, department)",
    )
    max_users: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Maximum users for this role"
    )
    priority: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Role priority for conflicts"
    )

    # Status flags
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Whether role is active"
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether this is a system role",
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether this is a default role for new users",
    )

    # Metadata
    permissions_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Cached count of permissions"
    )
    users_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Cached count of users"
    )
    
    # UI Display fields
    icon: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Icon name or class for UI"
    )
    color: Mapped[str | None] = mapped_column(
        String(7), nullable=True, comment="Color code for UI (hex format)"
    )

    # Relationships
    organization: Mapped["Organization | None"] = relationship(
        "Organization", back_populates="roles"
    )
    department: Mapped["Department | None"] = relationship("Department")
    parent: Mapped["Role | None"] = relationship(
        "Role", remote_side="Role.id", back_populates="children"
    )
    children: Mapped[list["Role"]] = relationship(
        "Role", back_populates="parent", cascade="all, delete-orphan"
    )

    # Many-to-many relationships
    users: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_roles",
        primaryjoin="Role.id == UserRole.role_id",
        secondaryjoin="UserRole.user_id == User.id",
        back_populates="roles",
    )
    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole", back_populates="role", cascade="all, delete-orphan", lazy="dynamic"
    )
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission", secondary="role_permissions", back_populates="roles"
    )
    role_permissions: Mapped[list["RolePermission"]] = relationship(
        "RolePermission", back_populates="role", cascade="all, delete-orphan"
    )

    # Inheritance relationships
    parent_inheritance_rules: Mapped[list["RoleInheritanceRule"]] = relationship(
        "RoleInheritanceRule",
        foreign_keys="RoleInheritanceRule.child_role_id",
        back_populates="child_role",
        cascade="all, delete-orphan",
    )
    child_inheritance_rules: Mapped[list["RoleInheritanceRule"]] = relationship(
        "RoleInheritanceRule",
        foreign_keys="RoleInheritanceRule.parent_role_id",
        back_populates="parent_role",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Role({self.code}, org={self.organization_id})>"

    def has_permission(self, permission_code: str) -> bool:
        """Check if role has a specific permission.

        Args:
            permission_code: Permission code to check

        Returns:
            True if role has the permission
        """
        # Check direct permissions
        for rp in self.role_permissions:
            if rp.permission.code == permission_code and rp.is_granted:
                return True

        # Check inherited permissions from parent
        if self.parent:
            return self.parent.has_permission(permission_code)

        return False

    def get_all_permissions(self) -> dict[str, Any]:
        """Get all permissions including inherited ones.

        Returns:
            Dictionary of permission codes to permission details
        """
        permissions = {}

        # Get inherited permissions first (can be overridden)
        if self.parent:
            permissions.update(self.parent.get_all_permissions())

        # Add/override with direct permissions
        for rp in self.role_permissions:
            if rp.is_granted:
                permissions[rp.permission.code] = {
                    "id": rp.permission.id,
                    "code": rp.permission.code,
                    "name": rp.permission.name,
                    "category": rp.permission.category,
                    "inherited": False,
                }

        return permissions

    def add_permission(
        self, permission: "Permission", granted_by: UserId | None = None
    ) -> None:
        """Add a permission to this role.

        Args:
            permission: Permission to add
            granted_by: User who granted the permission
        """
        # Check if already exists
        for rp in self.role_permissions:
            if rp.permission_id == permission.id:
                rp.is_granted = True
                rp.granted_at = datetime.now(UTC)
                rp.granted_by = granted_by
                return

        # Create new role-permission association
        from app.models.role import RolePermission

        role_perm = RolePermission(
            role_id=self.id,
            permission_id=permission.id,
            is_granted=True,
            granted_at=datetime.now(UTC),
            granted_by=granted_by,
        )
        self.role_permissions.append(role_perm)
        self.permissions_count = len(
            [rp for rp in self.role_permissions if rp.is_granted]
        )

    def remove_permission(self, permission: "Permission") -> None:
        """Remove a permission from this role.

        Args:
            permission: Permission to remove
        """
        for rp in self.role_permissions:
            if rp.permission_id == permission.id:
                rp.is_granted = False
                break

        self.permissions_count = len(
            [rp for rp in self.role_permissions if rp.is_granted]
        )

    def assign_to_user(
        self,
        user: "User",
        assigned_by: UserId | None = None,
        expires_at: datetime | None = None,
    ) -> "UserRole":
        """Assign this role to a user.

        Args:
            user: User to assign role to
            assigned_by: User who assigned the role
            expires_at: Optional expiration datetime

        Returns:
            UserRole association object
        """
        from app.models.role import UserRole

        # Check if already assigned
        for ur in self.user_roles:
            if ur.user_id == user.id:
                ur.is_active = True
                ur.assigned_at = datetime.now(UTC)
                ur.assigned_by = assigned_by
                ur.expires_at = expires_at
                return ur

        # Create new assignment
        user_role = UserRole(
            user_id=user.id,
            role_id=self.id,
            organization_id=self.organization_id,
            assigned_at=datetime.now(UTC),
            assigned_by=assigned_by,
            expires_at=expires_at,
            is_active=True,
        )
        self.user_roles.append(user_role)
        self.users_count = len([ur for ur in self.user_roles if ur.is_active])
        return user_role

    def validate_scope(self, user: "User") -> bool:
        """Validate if user is in the correct scope for this role.

        Args:
            user: User to validate

        Returns:
            True if user is in correct scope
        """
        if self.scope == "system":
            return True

        if self.scope == "organization":
            # Check if user has any role in this organization
            return any(
                ur.organization_id == self.organization_id
                for ur in user.user_roles
                if not ur.is_expired
            )

        if self.scope == "department":
            # Check if user has any role in this organization and department
            return any(
                ur.organization_id == self.organization_id
                and ur.department_id == self.department_id
                for ur in user.user_roles
                if not ur.is_expired
            )

        return False


class UserRole(AuditableModel):
    """Association table between users and roles with additional metadata."""

    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "role_id", "organization_id", name="uq_user_role_org"
        ),
    )

    # Primary keys
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
    department_id: Mapped[DepartmentId | None] = mapped_column(
        Integer,
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        comment="Department context (optional)",
    )

    # Assignment details
    assigned_by: Mapped[UserId | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="User who assigned the role",
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
    valid_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the role validity ends (deprecated, use expires_at)",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="When the role expires (null = never)",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Whether assignment is active"
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this is the user's primary role",
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Notes about this role assignment"
    )

    # Approval workflow
    approval_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Approval status (pending, approved, rejected)",
    )
    approved_by: Mapped[UserId | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="User who approved this role assignment",
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="When the role was approved"
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="user_roles", foreign_keys=[user_id]
    )
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")
    organization: Mapped["Organization"] = relationship(
        "Organization", foreign_keys=[organization_id]
    )
    department: Mapped["Department | None"] = relationship(
        "Department", foreign_keys=[department_id]
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
        now = datetime.now(UTC)
        expires_at = (
            self.expires_at
            if self.expires_at.tzinfo
            else self.expires_at.replace(tzinfo=UTC)
        )
        return now > expires_at

    @property
    def is_valid(self) -> bool:
        """Check if role assignment is currently valid."""
        now = datetime.now(UTC)

        # Check if active
        if not self.is_active:
            return False

        # Ensure timezone-aware datetime comparison
        valid_from = (
            self.valid_from
            if self.valid_from.tzinfo
            else self.valid_from.replace(tzinfo=UTC)
        )

        # Check validity period
        if now < valid_from:
            return False

        # Check expiration
        if self.expires_at:
            expires_at = (
                self.expires_at
                if self.expires_at.tzinfo
                else self.expires_at.replace(tzinfo=UTC)
            )
            if now > expires_at:
                return False

        # Check approval if required
        if self.approval_status == "pending":
            return False

        return True

    @property
    def days_until_expiry(self) -> int | None:
        """Get days until expiry (None if no expiry date)."""
        if not self.expires_at:
            return None

        now = datetime.now(UTC)
        expires_at = (
            self.expires_at
            if self.expires_at.tzinfo
            else self.expires_at.replace(tzinfo=UTC)
        )
        delta = expires_at - now
        return delta.days

    
    def get_effective_permissions(self) -> dict[str, Any]:
        """Get effective permissions for this role assignment."""
        if not self.is_valid:
            return {}

        return self.role.get_all_permissions()


class RolePermission(Base):
    """Association table between roles and permissions."""

    __tablename__ = "role_permissions"

    role_id: Mapped[RoleId] = mapped_column(
        Integer, ForeignKey("roles.id"), nullable=False, comment="Role ID"
    )
    permission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("permissions.id"), nullable=False, comment="Permission ID"
    )

    # Grant details
    is_granted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Whether permission is granted"
    )
    granted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
        comment="When permission was granted",
    )
    granted_by: Mapped[UserId | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="User who granted the permission",
    )

    # Add timestamps for compatibility
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
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
        UniqueConstraint(
            "role_id", "permission_id", name="ix_role_permissions_role_perm"
        ),
        Index("ix_role_permissions_role_id", "role_id"),
        Index("ix_role_permissions_permission_id", "permission_id"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<RolePermission(role_id={self.role_id}, "
            f"permission_id={self.permission_id})>"
        )
