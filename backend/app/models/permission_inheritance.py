"""Permission inheritance models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.permission import Permission
    from app.models.role import Role
    from app.models.user import User


class PermissionDependency(BaseModel):
    """Permission dependency model for defining permission prerequisites."""

    __tablename__ = "permission_dependencies"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Dependencies
    permission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("permissions.id"), nullable=False, index=True
    )
    requires_permission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("permissions.id"), nullable=False, index=True
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )

    # Relationships
    permission: Mapped["Permission"] = relationship(
        "Permission", foreign_keys=[permission_id], back_populates="dependencies"
    )
    requires_permission: Mapped["Permission"] = relationship(
        "Permission", foreign_keys=[requires_permission_id]
    )
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return (
            f"<PermissionDependency(id={self.id}, "
            f"permission_id={self.permission_id}, "
            f"requires_permission_id={self.requires_permission_id})>"
        )


class RoleInheritanceRule(BaseModel):
    """Role inheritance rule model for defining permission inheritance."""

    __tablename__ = "role_inheritance_rules"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Role hierarchy
    parent_role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.id"), nullable=False, index=True
    )
    child_role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.id"), nullable=False, index=True
    )

    # Inheritance configuration
    inherit_all: Mapped[bool] = mapped_column(Boolean, default=True)
    selected_permissions: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=50)  # 0-100 priority
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )
    updated_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )

    # Relationships
    parent_role: Mapped["Role"] = relationship(
        "Role", foreign_keys=[parent_role_id], back_populates="child_inheritance_rules"
    )
    child_role: Mapped["Role"] = relationship(
        "Role", foreign_keys=[child_role_id], back_populates="parent_inheritance_rules"
    )
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    updater: Mapped["User | None"] = relationship("User", foreign_keys=[updated_by])

    def __repr__(self) -> str:
        return (
            f"<RoleInheritanceRule(id={self.id}, "
            f"parent_role_id={self.parent_role_id}, "
            f"child_role_id={self.child_role_id})>"
        )


class InheritanceConflictResolution(BaseModel):
    """Model for storing inheritance conflict resolutions."""

    __tablename__ = "inheritance_conflict_resolutions"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Conflict details
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.id"), nullable=False, index=True
    )
    permission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("permissions.id"), nullable=False, index=True
    )

    # Resolution details
    strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    manual_decision: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Audit fields
    resolved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    resolved_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )

    # Relationships
    role: Mapped["Role"] = relationship("Role")
    permission: Mapped["Permission"] = relationship("Permission")
    resolver: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return (
            f"<InheritanceConflictResolution(id={self.id}, "
            f"role_id={self.role_id}, "
            f"permission_id={self.permission_id}, "
            f"strategy={self.strategy})>"
        )


class InheritanceAuditLog(BaseModel):
    """Audit log for inheritance changes."""

    __tablename__ = "inheritance_audit_logs"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Audit details
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.id"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Audit metadata
    performed_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    role: Mapped["Role"] = relationship("Role")
    performer: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return (
            f"<InheritanceAuditLog(id={self.id}, "
            f"role_id={self.role_id}, "
            f"action={self.action})>"
        )
