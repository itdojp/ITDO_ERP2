"""Organization model implementation."""

from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from app.models.base import SoftDeletableModel
from app.types import OrganizationId

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.role import Role
    from app.models.user import User


class Organization(SoftDeletableModel):
    """Organization model for multi-tenant support."""

    __tablename__ = "organizations"

    id: Mapped[OrganizationId] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    parent_id: Mapped[Optional[OrganizationId]] = mapped_column(
        ForeignKey("organizations.id"), nullable=True
    )

    # Relationships
    parent: Mapped[Optional["Organization"]] = relationship(
        "Organization", remote_side=[id], back_populates="children"
    )
    children: Mapped[list["Organization"]] = relationship(
        "Organization", back_populates="parent"
    )
    departments: Mapped[list["Department"]] = relationship(
        "Department",
        back_populates="organization",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    users: Mapped[list["User"]] = relationship("User", back_populates="organization")
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        back_populates="organization",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    # Multi-tenant user relationships - extended functionality from HEAD
    user_memberships: Mapped[list["UserOrganization"]] = relationship(
        "UserOrganization",
        foreign_keys="UserOrganization.organization_id",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    invitations: Mapped[list["OrganizationInvitation"]] = relationship(
        "OrganizationInvitation",
        foreign_keys="OrganizationInvitation.organization_id",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    # Creator relationship for auditing
    creator: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys="Organization.created_by", lazy="joined"
    )
    updater: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys="Organization.updated_by", lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name='{self.name}', code='{self.code}')>"

    @property
    def full_path(self) -> str:
        """Get the full hierarchical path of the organization."""
        path = [self.name]
        current = self
        while current.parent:
            path.insert(0, current.parent.name)
            current = current.parent
        return " > ".join(path)

    def get_ancestors(self) -> list["Organization"]:
        """Get all ancestor organizations."""
        ancestors = []
        current = self
        while current.parent:
            ancestors.append(current.parent)
            current = current.parent
        return ancestors

    def get_descendants(self) -> list["Organization"]:
        """Get all descendant organizations."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def get_path_to_root(self) -> list["Organization"]:
        """Get path from this organization to root."""
        path = []
        current = self
        while current.parent:
            path.insert(0, current.parent)
            current = current.parent
        return path

    def update(self, db: Session, updated_by: int, **kwargs: Any) -> None:
        """Update organization attributes."""
        from datetime import datetime, timezone

        for key, value in kwargs.items():
            if hasattr(self, key) and key not in ["id", "created_at", "created_by"]:
                setattr(self, key, value)

        self.updated_by = updated_by
        self.updated_at = datetime.now(timezone.utc)
        db.add(self)
        db.flush()

    def validate(self) -> None:
        """Validate organization data."""
        if not self.code or len(self.code.strip()) == 0:
            raise ValueError("組織コードは必須です")

        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("組織名は必須です")

    def __str__(self) -> str:
        """String representation for display."""
        return f"{self.code} - {self.name}"

    def get_erp_context(self) -> dict:
        """Get ERP-specific organization context."""
        return {
            "organization_id": self.id,
            "code": self.code,
            "name": self.name,
            "parent_id": self.parent_id,
            "is_active": self.is_active,
            "hierarchy_level": len(self.get_path_to_root()),
            "full_path": self.full_path,
        }
