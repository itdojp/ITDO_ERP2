"""Budget management models for Phase 4 financial management."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel
from app.types import DepartmentId, OrganizationId, UserId

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.organization import Organization
    from app.models.project import Project
    from app.models.user import User
    from app.models.expense_category import ExpenseCategory


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
        Integer, ForeignKey("organizations.id"), nullable=False, comment="Organization ID for multi-tenant support"
    )
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=True, comment="Project ID for project-specific budgets"
    )
    department_id: Mapped[Optional[DepartmentId]] = mapped_column(
        Integer, ForeignKey("departments.id"), nullable=True, comment="Department ID for department-specific budgets"
    )

    # Budget details
    budget_type: Mapped[BudgetType] = mapped_column(
        String(50), nullable=False, comment="Budget type: project/department/annual/quarterly/monthly"
    )
    fiscal_year: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Fiscal year"
    )
    budget_period: Mapped[str] = mapped_column(
        String(20), nullable=False, default="annual", comment="Budget period: annual/quarterly/monthly"
    )
    start_date: Mapped[date] = mapped_column(
        Date, nullable=False, comment="Budget start date"
    )
    end_date: Mapped[date] = mapped_column(
        Date, nullable=False, comment="Budget end date"
    )

    # Financial amounts - Supporting both Decimal and Float for different use cases
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, comment="Total budget amount"
    )
    approved_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True, comment="Approved budget amount"
    )
    actual_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), comment="Actual spent amount"
    )
    committed_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), comment="Committed amount (pending expenses)"
    )
    remaining_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), comment="Remaining budget amount"
    )

    # Variance tracking
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), comment="Variance amount (actual - budget)"
    )
    variance_percentage: Mapped[Decimal] = mapped_column(
        Numeric(8, 4), default=Decimal("0.00"), comment="Variance percentage"
    )

    # Currency
    currency: Mapped[str] = mapped_column(
        String(3), default="JPY", comment="Currency code"
    )

    # Status and approval
    status: Mapped[BudgetStatus] = mapped_column(
        String(50), default=BudgetStatus.DRAFT, comment="Budget status: draft/submitted/approved/rejected/active/closed"
    )
    approval_level: Mapped[int] = mapped_column(
        Integer, default=0, comment="Current approval level"
    )
    approved_by: Mapped[Optional[UserId]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, comment="User who approved the budget"
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Budget approval timestamp"
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Budget submission timestamp"
    )

    # Alert settings
    alert_threshold: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("80.00"), comment="Alert threshold percentage (0-100)"
    )
    is_alert_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Whether budget alerts are enabled"
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

    # Computed properties
    @property
    def utilization_percentage(self) -> Decimal:
        """Calculate budget utilization percentage."""
        if self.total_amount == 0:
            return Decimal("0.00")
        return (self.actual_amount / self.total_amount) * Decimal("100.00")

    @property
    def available_amount(self) -> Decimal:
        """Calculate available budget amount."""
        return self.total_amount - self.actual_amount - self.committed_amount

    @property
    def is_over_budget(self) -> bool:
        """Check if budget is over allocated."""
        return self.actual_amount > self.total_amount

    @property
    def is_alert_threshold_exceeded(self) -> bool:
        """Check if alert threshold is exceeded."""
        return self.utilization_percentage >= self.alert_threshold

    @property
    def is_active(self) -> bool:
        """Check if budget is currently active."""
        return self.status == BudgetStatus.ACTIVE

    @property
    def is_editable(self) -> bool:
        """Check if budget can be edited."""
        return self.status in [BudgetStatus.DRAFT, BudgetStatus.SUBMITTED]

    @property
    def days_remaining(self) -> int:
        """Calculate days remaining in budget period."""
        today = date.today()
        if today > self.end_date:
            return 0
        return (self.end_date - today).days

    @property
    def progress_percentage(self) -> Decimal:
        """Calculate time progress percentage."""
        today = date.today()
        total_days = (self.end_date - self.start_date).days
        if total_days <= 0:
            return Decimal("100.00")

        elapsed_days = (today - self.start_date).days
        if elapsed_days < 0:
            return Decimal("0.00")
        elif elapsed_days > total_days:
            return Decimal("100.00")
        else:
            return (Decimal(elapsed_days) / Decimal(total_days)) * Decimal("100.00")

    def calculate_totals(self) -> None:
        """Calculate total amounts from budget items."""
        if not self.budget_items:
            return

        self.total_amount = sum(item.budgeted_amount for item in self.budget_items)
        self.actual_amount = sum(item.actual_amount for item in self.budget_items)
        self.committed_amount = sum(item.committed_amount for item in self.budget_items)
        self.variance_amount = self.actual_amount - self.total_amount

        if self.total_amount > 0:
            self.variance_percentage = (self.variance_amount / self.total_amount) * Decimal("100.00")
        else:
            self.variance_percentage = Decimal("0.00")

        self.remaining_amount = self.total_amount - self.actual_amount - self.committed_amount

    def submit_for_approval(self, submitted_by: UserId) -> None:
        """Submit budget for approval."""
        if self.status != BudgetStatus.DRAFT:
            raise ValueError("Only draft budgets can be submitted for approval")

        self.status = BudgetStatus.SUBMITTED
        self.submitted_at = datetime.now()
        self.updated_by = submitted_by

    def approve(self, approved_by: UserId) -> None:
        """Approve budget."""
        if self.status != BudgetStatus.SUBMITTED:
            raise ValueError("Only submitted budgets can be approved")

        self.status = BudgetStatus.APPROVED
        self.approved_by = approved_by
        self.approved_at = datetime.now()
        self.approved_amount = self.total_amount

    def reject(self, rejected_by: UserId) -> None:
        """Reject budget."""
        if self.status != BudgetStatus.SUBMITTED:
            raise ValueError("Only submitted budgets can be rejected")

        self.status = BudgetStatus.REJECTED
        self.updated_by = rejected_by

    def activate(self) -> None:
        """Activate approved budget."""
        if self.status != BudgetStatus.APPROVED:
            raise ValueError("Only approved budgets can be activated")

        self.status = BudgetStatus.ACTIVE

    def close(self, closed_by: UserId) -> None:
        """Close budget."""
        if self.status != BudgetStatus.ACTIVE:
            raise ValueError("Only active budgets can be closed")

        self.status = BudgetStatus.CLOSED
        self.updated_by = closed_by

    def __str__(self) -> str:
        """String representation."""
        return f"{self.code} - {self.name} ({self.fiscal_year})"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"<Budget(id={self.id}, code='{self.code}', name='{self.name}', status='{self.status}')>"



class BudgetItem(SoftDeletableModel):
    """Budget item model for detailed budget breakdown."""

    __tablename__ = "budget_items"

    # Foreign keys
    budget_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("budgets.id"), nullable=False, comment="Budget ID"
    )
    expense_category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("expense_categories.id"), nullable=False, comment="Expense category ID"
    )

    # Item details
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Budget item name"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Budget item description"
    )

    # Quantity and unit
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 3), default=Decimal("1.000"), comment="Quantity"
    )
    unit: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Unit of measurement"
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), comment="Unit price"
    )

    # Financial amounts
    budgeted_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, comment="Budgeted amount"
    )
    actual_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), comment="Actual spent amount"
    )
    committed_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), comment="Committed amount"
    )
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), comment="Variance amount"
    )
    variance_percentage: Mapped[Decimal] = mapped_column(
        Numeric(8, 4), default=Decimal("0.00"), comment="Variance percentage"
    )

    # Monthly breakdown (JSON)
    monthly_breakdown: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Monthly budget breakdown (JSON)"
    )

    # Sort order
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, comment="Sort order"
    )

    # Relationships
    budget: Mapped["Budget"] = relationship("Budget", back_populates="budget_items")
    expense_category: Mapped["ExpenseCategory"] = relationship("ExpenseCategory", lazy="select")

    # Computed properties
    @property
    def remaining_amount(self) -> Decimal:
        """Calculate remaining amount."""
        return self.budgeted_amount - self.actual_amount - self.committed_amount

    @property
    def utilization_percentage(self) -> Decimal:
        """Calculate utilization percentage."""
        if self.budgeted_amount == 0:
            return Decimal("0.00")
        return (self.actual_amount / self.budgeted_amount) * Decimal("100.00")

    @property
    def is_over_budget(self) -> bool:
        """Check if over budget."""
        return self.actual_amount > self.budgeted_amount

    def calculate_variance(self) -> None:
        """Calculate variance amounts."""
        self.variance_amount = self.actual_amount - self.budgeted_amount
        if self.budgeted_amount > 0:
            self.variance_percentage = (self.variance_amount / self.budgeted_amount) * Decimal("100.00")
        else:
            self.variance_percentage = Decimal("0.00")

    def __str__(self) -> str:
        """String representation."""
        return f"{self.name} - {self.budgeted_amount}"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"<BudgetItem(id={self.id}, name='{self.name}', amount={self.budgeted_amount})>"
