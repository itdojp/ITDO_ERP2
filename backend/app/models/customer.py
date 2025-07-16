"""Customer relationship management models for Phase 5 CRM."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
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
    """Customer model for CRM functionality with Japanese business support."""

    __tablename__ = "customers"

    # Basic identification fields
    customer_code: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="Customer code"
    )
    company_name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Company name"
    )
    name_kana: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="Company name in katakana"
    )
    short_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Short name/abbreviation"
    )

    # Customer classification
    customer_type: Mapped[CustomerType] = mapped_column(
        String(50), nullable=False, comment="Customer type"
    )
    status: Mapped[CustomerStatus] = mapped_column(
        String(50), default=CustomerStatus.PROSPECT, comment="Customer status"
    )
    industry: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Industry"
    )
    scale: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Company scale: large/medium/small"
    )

    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        comment="Organization ID",
    )
    assigned_to: Mapped[Optional[UserId]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, comment="Assigned sales rep"
    )

    # Contact information
    email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Primary email"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Primary phone"
    )
    fax: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="FAX number"
    )
    website: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Company website"
    )

    # Address information (Japanese format)
    postal_code: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Postal code"
    )
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
        String(100), nullable=True, comment="State/Prefecture"
    )
    country: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Country"
    )

    # Business information
    annual_revenue: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True, comment="Annual revenue"
    )
    employee_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Number of employees"
    )
    credit_limit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True, comment="Credit limit"
    )
    payment_terms: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Payment terms"
    )

    # Priority and preferences
    priority: Mapped[str] = mapped_column(
        String(50), default="normal", comment="Priority: high/normal/low"
    )

    # Notes and descriptions
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Customer notes"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="General description"
    )
    internal_memo: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Internal memo (not visible to customer)"
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
    first_transaction_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="First transaction date"
    )
    last_transaction_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Last transaction date"
    )

    # Sales summary
    total_sales: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), comment="Total sales amount"
    )
    total_transactions: Mapped[int] = mapped_column(
        Integer, default=0, comment="Total number of transactions"
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

    def update_sales_summary(self) -> None:
        """Update sales summary from transaction data."""
        # This would be implemented when transaction models are available
        pass

    def get_latest_activity(self) -> Optional["CustomerActivity"]:
        """Get the most recent activity."""
        if self.activities:
            return max(self.activities, key=lambda x: x.activity_date)
        return None

    def __str__(self) -> str:
        return f"{self.customer_code} - {self.company_name}"

    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, code='{self.customer_code}', name='{self.company_name}', status='{self.status}')>"


class CustomerContact(SoftDeletableModel):
    """Customer contact model for individual contacts within a customer."""

    __tablename__ = "customer_contacts"

    # Foreign keys
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=False, comment="Customer ID"
    )

    # Contact details (supporting both Western and Japanese naming)
    first_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="First name"
    )
    last_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Last name"
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Full name (primary field)"
    )
    name_kana: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Name in katakana"
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
    decision_maker: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Alternative decision maker flag"
    )

    # Additional information
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Contact notes"
    )

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="contacts")

    @property
    def full_name(self) -> str:
        """Get full name (with fallback logic)."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.name

    def __str__(self) -> str:
        return f"{self.full_name} ({self.customer.company_name})"

    def __repr__(self) -> str:
        return f"<CustomerContact(id={self.id}, name='{self.name}', customer_id={self.customer_id})>"


class Opportunity(SoftDeletableModel):
    """Opportunity model for sales opportunities."""

    __tablename__ = "opportunities"

    # Basic fields
    opportunity_code: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True, comment="Opportunity code"
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Opportunity name"
    )
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Opportunity title (Japanese naming)"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Opportunity description"
    )

    # Foreign keys
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=False, comment="Customer ID"
    )
    assigned_to: Mapped[Optional[UserId]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, comment="Assigned sales rep"
    )
    owner_id: Mapped[UserId] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="Opportunity owner"
    )

    # Opportunity details
    stage: Mapped[OpportunityStage] = mapped_column(
        String(50), default=OpportunityStage.LEAD, comment="Opportunity stage"
    )
    status: Mapped[str] = mapped_column(
        String(50), default="open", comment="Status: open/won/lost/canceled"
    )
    value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True, comment="Opportunity value"
    )
    estimated_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True, comment="Estimated value"
    )
    probability: Mapped[int] = mapped_column(
        Integer, default=0, comment="Win probability (0-100)"
    )

    # Important dates
    expected_close_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Expected close date"
    )
    actual_close_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Actual close date"
    )

    # Additional information
    source: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Lead source"
    )
    competitor: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="Main competitor"
    )
    competitors: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="All competitors"
    )
    loss_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Loss reason"
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Opportunity notes"
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(
        "Customer", back_populates="opportunities"
    )
    assigned_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[assigned_to], lazy="select"
    )
    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_id], lazy="select")
    activities: Mapped[List["CustomerActivity"]] = relationship(
        "CustomerActivity", back_populates="opportunity", cascade="all, delete-orphan"
    )

    @property
    def is_open(self) -> bool:
        """Check if opportunity is still open."""
        return self.stage not in [
            OpportunityStage.CLOSED_WON,
            OpportunityStage.CLOSED_LOST,
        ]

    @property
    def is_won(self) -> bool:
        """Check if opportunity is won."""
        return self.stage == OpportunityStage.CLOSED_WON

    @property
    def weighted_value(self) -> Optional[Decimal]:
        """Calculate weighted value based on probability."""
        value = self.value or self.estimated_value
        if value is None:
            return None
        return value * (Decimal(self.probability) / Decimal("100.00"))

    def update_probability_by_stage(self) -> None:
        """Update probability based on stage."""
        stage_probability = {
            "lead": 10,
            "qualified": 25,
            "proposal": 40,
            "negotiation": 60,
            "closed_won": 100,
            "closed_lost": 0,
        }
        if self.stage.value in stage_probability:
            self.probability = stage_probability[self.stage.value]

    def __str__(self) -> str:
        if self.opportunity_code:
            return f"{self.opportunity_code} - {self.name}"
        return f"{self.title}"

    def __repr__(self) -> str:
        return f"<Opportunity(id={self.id}, title='{self.title}', status='{self.status}', probability={self.probability})>"


class CustomerActivity(SoftDeletableModel):
    """Customer activity model for tracking interactions."""

    __tablename__ = "customer_activities"

    # Foreign keys
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=False, comment="Customer ID"
    )
    opportunity_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("opportunities.id"),
        nullable=True,
        comment="Related opportunity",
    )
    user_id: Mapped[UserId] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="User who performed activity",
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
        Integer, nullable=True, comment="Duration in minutes"
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50), default="completed", comment="Status: planned/completed/canceled"
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Completion status"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Completion timestamp"
    )

    # Follow-up
    outcome: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Activity outcome"
    )
    next_action: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Next action to take"
    )
    next_action_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Next action date"
    )

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="activities")
    opportunity: Mapped[Optional["Opportunity"]] = relationship(
        "Opportunity", back_populates="activities"
    )
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="select")

    def __str__(self) -> str:
        return f"{self.activity_type.value}: {self.subject}"

    def __repr__(self) -> str:
        return f"<CustomerActivity(id={self.id}, type='{self.activity_type}', subject='{self.subject}', date={self.activity_date})>"
