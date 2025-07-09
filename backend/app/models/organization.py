"""Organization model implementation."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel
from app.types import OrganizationId

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.user import User


class Organization(SoftDeletableModel):
    """Organization model representing a company or business entity."""

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
    name_kana: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="Organization name in Katakana"
    )
    name_en: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="Organization name in English"
    )

    # Contact information
    phone: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Main phone number"
    )
    fax: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Fax number"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Main email address"
    )
    website: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Website URL"
    )

    # Address information
    postal_code: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, comment="Postal/Zip code"
    )
    prefecture: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Prefecture/State"
    )
    city: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="City"
    )
    address_line1: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Address line 1"
    )
    address_line2: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Address line 2"
    )

    # Business information
    business_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Type of business"
    )
    industry: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Industry category"
    )
    capital: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Capital amount in JPY"
    )
    employee_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Number of employees"
    )
    fiscal_year_end: Mapped[Optional[str]] = mapped_column(
        String(5), nullable=True, comment="Fiscal year end (MM-DD)"
    )

    # Hierarchy
    parent_id: Mapped[Optional[OrganizationId]] = mapped_column(
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
    settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default=dict, comment="Organization-specific settings"
    )

    # Additional information
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Organization description"
    )
    logo_url: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="URL to organization logo"
    )

    # Relationships
    parent: Mapped[Optional["Organization"]] = relationship(
        "Organization", remote_side="Organization.id", lazy="joined"
    )
    subsidiaries: Mapped[List["Organization"]] = relationship(
        "Organization", back_populates="parent", lazy="select"
    )
    departments: Mapped[List["Department"]] = relationship(
        "Department",
        back_populates="organization",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary="user_roles",
        primaryjoin="Organization.id == UserRole.organization_id",
        secondaryjoin="UserRole.user_id == User.id",
        viewonly=True,
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Organization(id={self.id}, code='{self.code}', name='{self.name}')>"

    @property
    def full_address(self) -> Optional[str]:
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

        return " ".join(parts) if parts else None

    @property
    def is_subsidiary(self) -> bool:
        """Check if this is a subsidiary organization."""
        return self.parent_id is not None

    @property
    def is_parent(self) -> bool:
        """Check if this organization has subsidiaries."""
        return len(self.subsidiaries) > 0

    def get_all_subsidiaries(self) -> List["Organization"]:
        """Get all subsidiaries recursively."""
        result = []
        for subsidiary in self.subsidiaries:
            result.append(subsidiary)
            result.extend(subsidiary.get_all_subsidiaries())
        return result

    def get_hierarchy_path(self) -> List["Organization"]:
        """Get the full hierarchy path from root to this organization."""
        path = [self]
        current = self
        while current.parent:
            path.insert(0, current.parent)
            current = current.parent
        return path

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary, ensuring JSON fields are properly handled."""
        data = super().to_dict()
        # Ensure settings is not None
        if data.get("settings") is None:
            data["settings"] = {}
        # Handle case where it's still a string (SQLite or PostgreSQL text representation)
        elif isinstance(data.get("settings"), str):
            import json
            try:
                data["settings"] = json.loads(data["settings"])
            except (json.JSONDecodeError, TypeError):
                data["settings"] = {}
        return data

    # Table configuration
    __table_args__ = (
        Index("idx_organization_code", "code"),
        Index("idx_organization_name", "name"),
        Index("idx_organization_parent", "parent_id"),
        Index("idx_organization_active", "is_active"),
        {"comment": "Organizations (companies/business entities)"},
    )
