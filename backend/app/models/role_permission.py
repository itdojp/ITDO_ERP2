"""RolePermission join table for RBAC system."""

from enum import Enum
from typing import TYPE_CHECKING, Optional, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.types import UserId

if TYPE_CHECKING:
    from app.models.permission import Permission
    from app.models.role import Role


class PermissionEffect(str, Enum):
    """Permission effect type."""

    ALLOW = "allow"
    DENY = "deny"


class RolePermission(BaseModel):
    """Join table for Role and Permission with additional metadata."""

    __tablename__ = "role_permissions"

    # Foreign keys
    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        comment="Role ID",
    )
    permission_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        comment="Permission ID",
    )

    # Permission effect (allow or deny)
    effect: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default=PermissionEffect.ALLOW.value,
        comment="Permission effect: allow or deny",
    )

    # Scope constraints (JSON field for flexibility)
    scope_constraints: Mapped[Optional[dict[str, Any]]] = mapped_column(
        String,  # Will be JSON in actual implementation
        nullable=True,
        comment="JSON constraints for permission scope",
    )

    # Organization scope limitation
    organization_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        comment="Organization scope for this permission",
    )

    # Department scope limitation
    department_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=True,
        comment="Department scope for this permission",
    )

    # Grant metadata
    granted_by: Mapped[Optional[UserId]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who granted this permission",
    )
    granted_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
        comment="When this permission was granted",
    )

    # Expiration
    expires_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this permission expires",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether this permission grant is active",
    )

    # Override flag for inherited permissions
    is_override: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether this overrides inherited permissions",
    )

    # Priority for conflict resolution (higher number = higher priority)
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Priority for conflict resolution",
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
            "role_id",
            "permission_id",
            "organization_id",
            "department_id",
            name="uq_role_permission_scope",
        ),
        Index("ix_role_permissions_role_active", "role_id", "is_active"),
        Index("ix_role_permissions_permission_active", "permission_id", "is_active"),
        Index("ix_role_permissions_org_dept", "organization_id", "department_id"),
        Index("ix_role_permissions_expires", "expires_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<RolePermission(role_id={self.role_id}, "
            f"permission_id={self.permission_id}, effect={self.effect})>"
        )

    @property
    def is_expired(self) -> bool:
        """Check if this permission grant has expired."""
        if self.expires_at is None:
            return False
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if this permission grant is valid."""
        return self.is_active and not self.is_expired

    @property
    def is_allow(self) -> bool:
        """Check if this is an ALLOW permission."""
        return self.effect == PermissionEffect.ALLOW.value

    @property
    def is_deny(self) -> bool:
        """Check if this is a DENY permission."""
        return self.effect == PermissionEffect.DENY.value

    def matches_scope(
        self, organization_id: Optional[int] = None, department_id: Optional[int] = None
    ) -> bool:
        """Check if this permission matches the given scope."""
        # Global permission (no scope constraints)
        if not self.organization_id and not self.department_id:
            return True

        # Organization-scoped permission
        if self.organization_id and not self.department_id:
            return self.organization_id == organization_id

        # Department-scoped permission
        if self.department_id:
            return (
                self.department_id == department_id
                and (not self.organization_id or self.organization_id == organization_id)
            )

        return False
