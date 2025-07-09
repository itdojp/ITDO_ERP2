"""Role and UserRole models implementation."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditableModel, SoftDeletableModel
from app.types import DepartmentId, OrganizationId, RoleId, UserId

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.organization import Organization
    from app.models.role_permission import RolePermission
    from app.models.user import User


class RoleType(str, Enum):
    """Role type enumeration."""

    SYSTEM = "system"  # Built-in system roles
    ORGANIZATION = "organization"  # Organization-specific roles
    DEPARTMENT = "department"  # Department-specific roles
    PROJECT = "project"  # Project-specific roles
    CUSTOM = "custom"  # User-defined custom roles


class SystemRole(str, Enum):
    """System-defined role codes."""

    SUPER_ADMIN = "system.super_admin"
    ORG_ADMIN = "system.org_admin"
    DEPT_MANAGER = "system.dept_manager"
    PROJECT_MANAGER = "system.project_manager"
    USER = "system.user"
    VIEWER = "system.viewer"


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

    def get_effective_permissions(
        self, organization_id: Optional[int] = None, department_id: Optional[int] = None
    ) -> Set[str]:
        """Get effective permissions from RolePermission relationships."""
        permissions = set()

        # Get permissions from parent roles recursively
        if self.parent:
            permissions.update(
                self.parent.get_effective_permissions(organization_id, department_id)
            )

        # Process role permissions
        for rp in self.role_permissions:
            if not rp.is_valid:  # Skip inactive or expired permissions
                continue

            # Check scope matching
            if not rp.matches_scope(organization_id, department_id):
                continue

            # Handle permission effect
            if rp.permission and rp.permission.is_active:
                permission_code = rp.permission.code

                if rp.is_allow:
                    permissions.add(permission_code)
                    # Add wildcard permission if it's a category permission
                    if permission_code.endswith(".all"):
                        category = permission_code.split(".")[0]
                        permissions.add(f"{category}.*")
                elif rp.is_deny:
                    # Remove permission and any wildcards
                    permissions.discard(permission_code)
                    if "." in permission_code:
                        category = permission_code.split(".")[0]
                        permissions.discard(f"{category}.*")

        return permissions

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

    def has_effective_permission(
        self,
        permission_code: str,
        organization_id: Optional[int] = None,
        department_id: Optional[int] = None,
    ) -> bool:
        """Check if role has effective permission considering scope."""
        permissions = self.get_effective_permissions(organization_id, department_id)

        # Direct permission check
        if permission_code in permissions:
            return True

        # Wildcard permission check
        if "." in permission_code:
            category = permission_code.split(".")[0]
            if f"{category}.*" in permissions or f"{category}.all" in permissions:
                return True

        # Admin override
        if "admin.all" in permissions or "admin.*" in permissions:
            return True

        return False

    def get_users_count(self) -> int:
        """Get count of users with this role."""
        return len([ur for ur in self.user_roles if ur.is_active])

    def get_permission_priority(self) -> int:
        """Get permission priority based on role type and hierarchy."""
        # System roles have highest priority
        if self.is_system:
            return 1000

        # Priority based on role type
        type_priorities = {
            RoleType.ORGANIZATION.value: 500,
            RoleType.DEPARTMENT.value: 300,
            RoleType.PROJECT.value: 200,
            RoleType.CUSTOM.value: 100,
        }

        base_priority = type_priorities.get(self.role_type, 0)

        # Add depth to priority (deeper roles have lower priority)
        return base_priority - self.depth

    def can_inherit_from(self, parent_role: "Role") -> bool:
        """Check if this role can inherit from another role."""
        # Cannot inherit from self
        if self.id == parent_role.id:
            return False

        # System roles cannot inherit
        if self.is_system:
            return False

        # Check for circular inheritance
        current = parent_role
        while current:
            if current.id == self.id:
                return False
            current = current.parent

        # Check role type compatibility
        if self.role_type == RoleType.DEPARTMENT.value:
            # Department roles can only inherit from org or dept roles
            return parent_role.role_type in [
                RoleType.ORGANIZATION.value,
                RoleType.DEPARTMENT.value,
            ]

        return True

    @property
    def is_organization_admin(self) -> bool:
        """Check if this is an organization admin role."""
        return (
            self.code == SystemRole.ORG_ADMIN.value
            or self.role_type == RoleType.ORGANIZATION.value
            and "admin" in self.code.lower()
        )


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
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if role assignment is currently valid."""
        now = datetime.utcnow()

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

        delta = self.expires_at - datetime.utcnow()
        return delta.days

    def get_effective_permissions(self) -> Dict[str, Any]:
        """Get effective permissions for this role assignment."""
        if not self.is_valid:
            return {}

        return self.role.get_all_permissions()


