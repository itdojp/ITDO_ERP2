"""Customer relationship management models for Phase 5 CRM."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date, DateTime, Numeric, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel
from app.types import OrganizationId, UserId

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class CustomerType(str, Enum):
    """Customer type enumeration."""
    INDIVIDUAL = "individual"
    CORPORATE = "corporate"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"


class CustomerStatus(str, Enum):
    """Customer status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROSPECT = "prospect"
    FORMER = "former"


class OpportunityStage(str, Enum):
    """Opportunity stage enumeration."""
    LEAD = "lead"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class ActivityType(str, Enum):
    """Activity type enumeration."""
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    TASK = "task"
    NOTE = "note"
    PROPOSAL = "proposal"


class Customer(SoftDeletableModel):
    """Customer model for CRM functionality."""

    __tablename__ = "customers"

    # Basic fields
    customer_code: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="Customer code"
    )
    company_name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Company name"
    )
    customer_type: Mapped[CustomerType] = mapped_column(
        String(50), nullable=False, comment="Customer type"
    )
    status: Mapped[CustomerStatus] = mapped_column(
        String(50), default=CustomerStatus.PROSPECT, comment="Customer status"
    )

    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, comment="Organization ID"
    )
    assigned_to: Mapped[Optional[UserId]] = mapped_column(
        ForeignKey("users.id"), nullable=True, comment="Assigned sales rep"
    )

    # Contact information
    email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Primary email"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Primary phone"
    )
    website: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Company website"
    )

    # Address information
    address_line1: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Address line 1"
    )
    address_line2: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Address line 2"
    )
    city: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="City"
    )
    state: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="State/Province"
    )
    postal_code: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Postal code"
    )
    country: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Country"
    )

    # Business information
    industry: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Industry"
    )
    annual_revenue: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True, comment="Annual revenue"
    )
    employee_count: Mapped[Optional[int]] = mapped_column(
        nullable=True, comment="Number of employees"
    )
    
    # Additional fields
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Customer notes"
    )
    tags: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Customer tags (comma-separated)"
    )

    # Important dates
    first_contact_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="First contact date"
    )
    last_contact_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Last contact date"
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", lazy="select")
    assigned_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[assigned_to], lazy="select"
    )
    contacts: Mapped[List["CustomerContact"]] = relationship(
        "CustomerContact", back_populates="customer", cascade="all, delete-orphan"
    )
    opportunities: Mapped[List["Opportunity"]] = relationship(
        "Opportunity", back_populates="customer", cascade="all, delete-orphan"
    )
    activities: Mapped[List["CustomerActivity"]] = relationship(
        "CustomerActivity", back_populates="customer", cascade="all, delete-orphan"
    )

    def __str__(self) -> str:
        return f"{self.customer_code} - {self.company_name}"


class CustomerContact(SoftDeletableModel):
    """Customer contact model for individual contacts within a customer."""

    __tablename__ = "customer_contacts"

    # Foreign keys
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"), nullable=False, comment="Customer ID"
    )

    # Contact details
    first_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="First name"
    )
    last_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Last name"
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Job title"
    )
    department: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Department"
    )

    # Contact information
    email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Email address"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Phone number"
    )
    mobile: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Mobile number"
    )

    # Flags
    is_primary: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Primary contact flag"
    )
    is_decision_maker: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Decision maker flag"
    )

    # Additional information
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Contact notes"
    )

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="contacts")

    @property
    def full_name(self) -> str:
        """Get full name."""
        return f"{self.first_name} {self.last_name}"

    def __str__(self) -> str:
        return f"{self.full_name} ({self.customer.company_name})"


class Opportunity(SoftDeletableModel):
    """Opportunity model for sales opportunities."""

    __tablename__ = "opportunities"

    # Basic fields
    opportunity_code: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="Opportunity code"
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Opportunity name"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Opportunity description"
    )

    # Foreign keys
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"), nullable=False, comment="Customer ID"
    )
    assigned_to: Mapped[Optional[UserId]] = mapped_column(
        ForeignKey("users.id"), nullable=True, comment="Assigned sales rep"
    )

    # Opportunity details
    stage: Mapped[OpportunityStage] = mapped_column(
        String(50), default=OpportunityStage.LEAD, comment="Opportunity stage"
    )
    value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True, comment="Opportunity value"
    )
    probability: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True, comment="Win probability (0-100)"
    )
    
    # Important dates
    expected_close_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Expected close date"
    )
    actual_close_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Actual close date"
    )

    # Additional information
    source: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Lead source"
    )
    competitor: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="Main competitor"
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Opportunity notes"
    )

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="opportunities")
    assigned_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[assigned_to], lazy="select"
    )

    @property
    def is_open(self) -> bool:
        """Check if opportunity is still open."""
        return self.stage not in [OpportunityStage.CLOSED_WON, OpportunityStage.CLOSED_LOST]

    @property
    def is_won(self) -> bool:
        """Check if opportunity is won."""
        return self.stage == OpportunityStage.CLOSED_WON

    @property
    def weighted_value(self) -> Optional[Decimal]:
        """Calculate weighted value based on probability."""
        if self.value is None or self.probability is None:
            return None
        return self.value * (self.probability / Decimal("100.00"))

    def __str__(self) -> str:
        return f"{self.opportunity_code} - {self.name}"


class CustomerActivity(SoftDeletableModel):
    """Customer activity model for tracking interactions."""

    __tablename__ = "customer_activities"

    # Foreign keys
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"), nullable=False, comment="Customer ID"
    )
    opportunity_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("opportunities.id"), nullable=True, comment="Related opportunity"
    )
    user_id: Mapped[UserId] = mapped_column(
        ForeignKey("users.id"), nullable=False, comment="User who performed activity"
    )

    # Activity details
    activity_type: Mapped[ActivityType] = mapped_column(
        String(50), nullable=False, comment="Activity type"
    )
    subject: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Activity subject"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Activity description"
    )

    # Scheduling
    activity_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="Activity date"
    )
    duration_minutes: Mapped[Optional[int]] = mapped_column(
        nullable=True, comment="Duration in minutes"
    )

    # Status
    is_completed: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Completion status"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Completion timestamp"
    )

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="activities")
    opportunity: Mapped[Optional["Opportunity"]] = relationship("Opportunity", lazy="select")
    user: Mapped["User"] = relationship("User", lazy="select")

    def __str__(self) -> str:
        return f"{self.activity_type}: {self.subject}"