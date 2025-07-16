"""Budget management models for Phase 4 financial management."""

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
    from app.models.project import Project
    from app.models.department import Department
    from app.models.user import User


class BudgetStatus(str, Enum):
    """Budget status enumeration."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    CLOSED = "closed"


class BudgetType(str, Enum):
    """Budget type enumeration."""
    PROJECT = "project"
    DEPARTMENT = "department"
    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    MONTHLY = "monthly"


class Budget(SoftDeletableModel):
    """Budget model for financial planning and control."""

    __tablename__ = "budgets"

    # Basic fields
    code: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="Budget code"
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Budget name"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Budget description"
    )

    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, comment="Organization ID"
    )
    project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("projects.id"), nullable=True, comment="Project ID"
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id"), nullable=True, comment="Department ID"
    )

    # Budget details
    budget_type: Mapped[BudgetType] = mapped_column(
        String(50), nullable=False, comment="Budget type"
    )
    fiscal_year: Mapped[int] = mapped_column(
        nullable=False, comment="Fiscal year"
    )
    start_date: Mapped[date] = mapped_column(
        Date, nullable=False, comment="Budget start date"
    )
    end_date: Mapped[date] = mapped_column(
        Date, nullable=False, comment="Budget end date"
    )

    # Financial amounts
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, comment="Total budget amount"
    )
    approved_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True, comment="Approved amount"
    )
    actual_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), comment="Actual spent amount"
    )
    remaining_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), comment="Remaining amount"
    )

    # Status and approval
    status: Mapped[BudgetStatus] = mapped_column(
        String(50), default=BudgetStatus.DRAFT, comment="Budget status"
    )
    approved_by: Mapped[Optional[UserId]] = mapped_column(
        ForeignKey("users.id"), nullable=True, comment="Approver user ID"
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Approval timestamp"
    )

    # Alert settings
    alert_threshold: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("80.00"), comment="Alert threshold %"
    )
    is_alert_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Alert enabled flag"
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", lazy="select")
    project: Mapped[Optional["Project"]] = relationship("Project", lazy="select")
    department: Mapped[Optional["Department"]] = relationship("Department", lazy="select")
    approved_by_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[approved_by], lazy="select"
    )
    budget_items: Mapped[List["BudgetItem"]] = relationship(
        "BudgetItem", back_populates="budget", cascade="all, delete-orphan"
    )

    @property
    def utilization_percentage(self) -> Decimal:
        """Calculate budget utilization percentage."""
        if self.total_amount == 0:
            return Decimal("0.00")
        return (self.actual_amount / self.total_amount) * Decimal("100.00")

    @property
    def is_over_budget(self) -> bool:
        """Check if budget is over allocated."""
        return self.actual_amount > self.total_amount

    @property
    def is_alert_threshold_exceeded(self) -> bool:
        """Check if alert threshold is exceeded."""
        return self.utilization_percentage >= self.alert_threshold

    def __str__(self) -> str:
        return f"{self.code} - {self.name} ({self.fiscal_year})"


class ExpenseCategory(SoftDeletableModel):
    """Expense category model for financial management."""

    __tablename__ = "expense_categories"

    # Basic fields
    code: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="Category code"
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Category name"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Category description"
    )

    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, comment="Organization ID"
    )
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("expense_categories.id"), nullable=True, comment="Parent category"
    )

    # Category settings
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Active status"
    )
    requires_receipt: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Receipt required"
    )
    approval_required: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Approval required"
    )
    approval_limit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True, comment="Approval limit"
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", lazy="select")
    parent: Mapped[Optional["ExpenseCategory"]] = relationship(
        "ExpenseCategory", remote_side="ExpenseCategory.id", back_populates="children"
    )
    children: Mapped[List["ExpenseCategory"]] = relationship(
        "ExpenseCategory", back_populates="parent", cascade="all, delete-orphan"
    )

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class BudgetItem(SoftDeletableModel):
    """Budget item model for detailed budget breakdown."""

    __tablename__ = "budget_items"

    # Foreign keys
    budget_id: Mapped[int] = mapped_column(
        ForeignKey("budgets.id"), nullable=False, comment="Budget ID"
    )
    expense_category_id: Mapped[int] = mapped_column(
        ForeignKey("expense_categories.id"), nullable=False, comment="Category ID"
    )

    # Item details
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Item name"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Item description"
    )

    # Financial amounts
    budgeted_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, comment="Budgeted amount"
    )
    actual_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), comment="Actual amount"
    )
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), comment="Variance amount"
    )

    # Relationships
    budget: Mapped["Budget"] = relationship("Budget", back_populates="budget_items")
    expense_category: Mapped["ExpenseCategory"] = relationship(
        "ExpenseCategory", lazy="select"
    )

    @property
    def variance_percentage(self) -> Decimal:
        """Calculate variance percentage."""
        if self.budgeted_amount == 0:
            return Decimal("0.00")
        return (self.variance_amount / self.budgeted_amount) * Decimal("100.00")

    def __str__(self) -> str:
        return f"{self.name} - {self.budgeted_amount}"