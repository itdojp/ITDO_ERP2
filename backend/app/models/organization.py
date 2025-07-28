"""Organization model implementation."""

from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from app.models.base import SoftDeletableModel
from app.types import OrganizationId

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.project_management import Project
    from app.models.role import Role
    from app.models.user import User
    from app.models.user_organization import (
        OrganizationInvitation,
        UserOrganization,
    )


class Organization(SoftDeletableModel):
    """Organization model for multi-tenant support."""

    __tablename__ = "organizations"

    # Basic fields
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique organization code",
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Organization name"
    )
    name_kana: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="Organization name in Katakana"
    )
    name_en: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="Organization name in English"
    )

    # Contact information
    phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="Main phone number"
    )
    fax: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="Fax number"
    )
    email: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Main email address"
    )
    website: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Website URL"
    )

    # Address information
    postal_code: Mapped[str | None] = mapped_column(
        String(10), nullable=True, comment="Postal/Zip code"
    )
    prefecture: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Prefecture/State"
    )
    city: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="City")
    address_line1: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Address line 1"
    )
    address_line2: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Address line 2"
    )

    # Business information
    business_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Type of business"
    )
    industry: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Industry category"
    )
    capital: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Capital amount in JPY"
    )
    employee_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Number of employees"
    )
    fiscal_year_end: Mapped[str | None] = mapped_column(
        String(5), nullable=True, comment="Fiscal year end (MM-DD)"
    )

    # Hierarchy
    parent_id: Mapped[OrganizationId | None] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=True,
        comment="Parent organization ID for subsidiaries",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the organization is active",
    )

    # Settings (JSON)
    settings: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Organization-specific settings in JSON format"
    )

    # Additional information
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Organization description"
    )
    logo_url: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="URL to organization logo"
    )

    # Relationships
    parent: Mapped[Optional["Organization"]] = relationship(
        "Organization", remote_side=[id], back_populates="children"
    )
    subsidiaries: Mapped[list["Organization"]] = relationship(
        "Organization", back_populates="parent", lazy="select"
    )
    departments: Mapped[list["Department"]] = relationship(
        "Department",
        back_populates="organization",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        back_populates="organization",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    users: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_roles",
        primaryjoin="Organization.id == UserRole.organization_id",
        secondaryjoin="UserRole.user_id == User.id",
        viewonly=True,
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

    # Project management relationships
    projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="organization", cascade="all, delete-orphan"
    )

    # Multi-tenant user relationships
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

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name='{self.name}', code='{self.code}')>"

    @property
    def full_address(self) -> str | None:
        """Get full formatted address."""
        parts = []
        if self.postal_code:
            parts.append(f"〒{self.postal_code}")
        if self.prefecture:
            parts.append(self.prefecture)
        if self.city:
            parts.append(self.city)
        if self.address_line1:
            parts.append(self.address_line1)
        if self.address_line2:
            parts.append(self.address_line2)

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

    @property
    def is_parent(self) -> bool:
        """Check if this organization has subsidiaries."""
        return len(self.subsidiaries) > 0

    def get_all_subsidiaries(self) -> list["Organization"]:
        """Get all subsidiaries recursively."""
        result = []
        for subsidiary in self.subsidiaries:
            result.append(subsidiary)
            result.extend(subsidiary.get_all_subsidiaries())
        return result

    def get_hierarchy_path(self) -> list["Organization"]:
        """Get the full hierarchy path from root to this organization."""
        path = [self]
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
