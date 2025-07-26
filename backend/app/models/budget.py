"""Budget model implementation for financial management."""

from datetime import date, datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel
from app.types import DepartmentId, OrganizationId, UserId

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.expense_category import ExpenseCategory
    from app.models.organization import Organization
    from app.models.project import Project
    from app.models.user import User


class Budget(SoftDeletableModel):
    """予算モデル - Budget model for financial planning and control."""

    __tablename__ = "budgets"

    # Basic fields
    code: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="Budget code"
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Budget name"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Budget description"
    )

    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        comment="Organization ID for multi-tenant support",
    )
    project_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("projects.id"),
        nullable=True,
        comment="Project ID for project-specific budgets",
    )
    department_id: Mapped[DepartmentId | None] = mapped_column(
        Integer,
        ForeignKey("departments.id"),
        nullable=True,
        comment="Department ID for department-specific budgets",
    )

    # Budget details
    budget_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Budget type: project/department/annual/quarterly/monthly",
    )
    fiscal_year: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Fiscal year"
    )
    budget_period: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="annual",
        comment="Budget period: annual/quarterly/monthly",
    )
    start_date: Mapped[date] = mapped_column(
        Date, nullable=False, comment="Budget start date"
    )
    end_date: Mapped[date] = mapped_column(
        Date, nullable=False, comment="Budget end date"
    )

    # Financial amounts (in organization's base currency)
    total_amount: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Total budget amount"
    )
    approved_amount: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Approved budget amount"
    )
    actual_amount: Mapped[float] = mapped_column(
        Float, default=0.0, comment="Actual spent amount"
    )
    committed_amount: Mapped[float] = mapped_column(
        Float, default=0.0, comment="Committed amount (pending expenses)"
    )
    remaining_amount: Mapped[float] = mapped_column(
        Float, default=0.0, comment="Remaining budget amount"
    )

    # Currency
    currency: Mapped[str] = mapped_column(
        String(3), default="JPY", comment="Currency code"
    )

    # Status and approval
    status: Mapped[str] = mapped_column(
        String(50),
        default="draft",
        comment="Budget status: draft/submitted/approved/rejected/active/closed",
    )
    approval_level: Mapped[int] = mapped_column(
        Integer, default=0, comment="Current approval level"
    )
    approved_by: Mapped[UserId | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="User who approved the budget",
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Budget approval timestamp"
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Budget submission timestamp"
    )

    # Variance tracking
    variance_amount: Mapped[float] = mapped_column(
        Float, default=0.0, comment="Variance amount (actual - budget)"
    )
    variance_percentage: Mapped[float] = mapped_column(
        Float, default=0.0, comment="Variance percentage"
    )

    # Alert settings
    alert_threshold: Mapped[float] = mapped_column(
        Float, default=80.0, comment="Alert threshold percentage (0-100)"
    )
    is_alert_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Whether budget alerts are enabled"
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", lazy="select")
    project: Mapped["Project | None"] = relationship("Project", lazy="select")
    department: Mapped["Department | None"] = relationship("Department", lazy="select")
    approved_by_user: Mapped["User | None"] = relationship(
        "User", foreign_keys=[approved_by], lazy="select"
    )
    budget_items: Mapped[List["BudgetItem"]] = relationship(
        "BudgetItem", back_populates="budget", cascade="all, delete-orphan"
    )
    # TODO: Add relationship to expense allocations when expense model is implemented

    # Computed properties
    @property
    def utilization_percentage(self) -> float:
        """Calculate budget utilization percentage."""
        if self.total_amount == 0:
            return 0.0
        return (self.actual_amount / self.total_amount) * 100

    @property
    def available_amount(self) -> float:
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
        return self.status == "active"

    @property
    def is_editable(self) -> bool:
        """Check if budget can be edited."""
        return self.status in ["draft", "submitted"]

    @property
    def days_remaining(self) -> int:
        """Calculate days remaining in budget period."""
        today = date.today()
        if today > self.end_date:
            return 0
        return (self.end_date - today).days

    @property
    def progress_percentage(self) -> float:
        """Calculate time progress percentage."""
        today = date.today()
        total_days = (self.end_date - self.start_date).days
        if total_days <= 0:
            return 100.0

        elapsed_days = (today - self.start_date).days
        if elapsed_days < 0:
            return 0.0
        elif elapsed_days > total_days:
            return 100.0
        else:
            return (elapsed_days / total_days) * 100

    def calculate_totals(self) -> None:
        """Calculate total amounts from budget items."""
        if not self.budget_items:
            return

        self.total_amount = sum(item.budgeted_amount for item in self.budget_items)
        self.actual_amount = sum(item.actual_amount for item in self.budget_items)
        self.variance_amount = self.actual_amount - self.total_amount

        if self.total_amount > 0:
            self.variance_percentage = (self.variance_amount / self.total_amount) * 100
        else:
            self.variance_percentage = 0.0

        self.remaining_amount = (
            self.total_amount - self.actual_amount - self.committed_amount
        )

    def submit_for_approval(self, submitted_by: UserId) -> None:
        """Submit budget for approval."""
        if self.status != "draft":
            raise ValueError("Only draft budgets can be submitted for approval")

        self.status = "submitted"
        self.submitted_at = datetime.now()
        self.updated_by = submitted_by

    def approve(self, approved_by: UserId) -> None:
        """Approve budget."""
        if self.status != "submitted":
            raise ValueError("Only submitted budgets can be approved")

        self.status = "approved"
        self.approved_by = approved_by
        self.approved_at = datetime.now()
        self.approved_amount = self.total_amount

    def reject(self, rejected_by: UserId) -> None:
        """Reject budget."""
        if self.status != "submitted":
            raise ValueError("Only submitted budgets can be rejected")

        self.status = "rejected"
        self.updated_by = rejected_by

    def activate(self) -> None:
        """Activate approved budget."""
        if self.status != "approved":
            raise ValueError("Only approved budgets can be activated")

        self.status = "active"

    def close(self, closed_by: UserId) -> None:
        """Close budget."""
        if self.status != "active":
            raise ValueError("Only active budgets can be closed")

        self.status = "closed"
        self.updated_by = closed_by

    def __str__(self) -> str:
        """String representation."""
        return f"{self.code} - {self.name} ({self.fiscal_year})"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"<Budget(id={self.id}, code='{self.code}', name='{self.name}', status='{self.status}')>"


class BudgetItem(SoftDeletableModel):
    """予算明細モデル - Budget item model for detailed budget breakdown."""

    __tablename__ = "budget_items"

    # Foreign keys
    budget_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("budgets.id"), nullable=False, comment="Budget ID"
    )
    expense_category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("expense_categories.id"),
        nullable=False,
        comment="Expense category ID",
    )

    # Item details
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Budget item name"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Budget item description"
    )

    # Quantity and unit
    quantity: Mapped[float] = mapped_column(Float, default=1.0, comment="Quantity")
    unit: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Unit of measurement"
    )
    unit_price: Mapped[float] = mapped_column(Float, default=0.0, comment="Unit price")

    # Financial amounts
    budgeted_amount: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Budgeted amount"
    )
    actual_amount: Mapped[float] = mapped_column(
        Float, default=0.0, comment="Actual spent amount"
    )
    committed_amount: Mapped[float] = mapped_column(
        Float, default=0.0, comment="Committed amount"
    )
    variance_amount: Mapped[float] = mapped_column(
        Float, default=0.0, comment="Variance amount"
    )
    variance_percentage: Mapped[float] = mapped_column(
        Float, default=0.0, comment="Variance percentage"
    )

    # Monthly breakdown (JSON)
    monthly_breakdown: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Monthly budget breakdown (JSON)"
    )

    # Sort order
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="Sort order")

    # Relationships
    budget: Mapped["Budget"] = relationship("Budget", back_populates="budget_items")
    expense_category: Mapped["ExpenseCategory"] = relationship(
        "ExpenseCategory", lazy="select"
    )

    # Computed properties
    @property
    def remaining_amount(self) -> float:
        """Calculate remaining amount."""
        return self.budgeted_amount - self.actual_amount - self.committed_amount

    @property
    def utilization_percentage(self) -> float:
        """Calculate utilization percentage."""
        if self.budgeted_amount == 0:
            return 0.0
        return (self.actual_amount / self.budgeted_amount) * 100

    @property
    def is_over_budget(self) -> bool:
        """Check if over budget."""
        return self.actual_amount > self.budgeted_amount

    def calculate_variance(self) -> None:
        """Calculate variance amounts."""
        self.variance_amount = self.actual_amount - self.budgeted_amount
        if self.budgeted_amount > 0:
            self.variance_percentage = (
                self.variance_amount / self.budgeted_amount
            ) * 100
        else:
            self.variance_percentage = 0.0

    def __str__(self) -> str:
        """String representation."""
        return f"{self.name} - {self.budgeted_amount:,.0f}"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"<BudgetItem(id={self.id}, name='{self.name}', amount={self.budgeted_amount})>"
