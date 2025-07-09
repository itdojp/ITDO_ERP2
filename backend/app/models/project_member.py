"""Project member model implementation."""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditableModel
from app.types import UserId

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class ProjectMember(AuditableModel):
    """Project member model with role-based permissions."""

    __tablename__ = "project_members"

    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=False, index=True,
        comment="Project ID"
    )
    user_id: Mapped[UserId] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True,
        comment="User ID"
    )
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="member", index=True,
        comment="Member role in project"
    )
    permissions: Mapped[Optional[List[str]]] = mapped_column(
        JSON, nullable=True, default=list,
        comment="List of permissions granted to this member"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True,
        comment="Whether member is active"
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project", back_populates="members", lazy="select"
    )
    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], lazy="joined"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_member"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<ProjectMember(project_id={self.project_id}, user_id={self.user_id}, role='{self.role}')>"

    def has_permission(self, permission: str) -> bool:
        """Check if member has specific permission."""
        return bool(self.permissions and permission in self.permissions)

    def add_permission(self, permission: str) -> None:
        """Add permission to member."""
        if not self.permissions:
            self.permissions = []
        if permission not in self.permissions:
            self.permissions.append(permission)

    def remove_permission(self, permission: str) -> None:
        """Remove permission from member."""
        if self.permissions and permission in self.permissions:
            self.permissions.remove(permission)

    def get_role_permissions(self) -> List[str]:
        """Get default permissions for member role."""
        role_permissions = {
            "owner": [
                "project.manage",
                "project.delete",
                "project.view",
                "project.edit",
                "project.member.manage",
                "task.create",
                "task.edit",
                "task.delete",
                "task.view",
                "task.assign",
            ],
            "manager": [
                "project.manage",
                "project.view",
                "project.edit",
                "project.member.manage",
                "task.create",
                "task.edit",
                "task.delete",
                "task.view",
                "task.assign",
            ],
            "member": [
                "project.view",
                "task.view",
                "task.edit",
                "task.create",
            ],
            "viewer": [
                "project.view",
                "task.view",
            ],
        }
        return role_permissions.get(self.role, [])

    def get_effective_permissions(self) -> List[str]:
        """Get effective permissions (role + explicit permissions)."""
        role_perms = set(self.get_role_permissions())
        explicit_perms = set(self.permissions or [])
        return list(role_perms.union(explicit_perms))
