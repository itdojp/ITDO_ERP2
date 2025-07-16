"""Expense management models for Phase 4 financial management."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel
from app.types import OrganizationId, UserId

if TYPE_CHECKING:
    from app.models.budget import ExpenseCategory
    from app.models.organization import Organization
    from app.models.project import Project
    from app.models.user import User


class ExpenseStatus(str, Enum):
    """Expense status enumeration."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class PaymentMethod(str, Enum):
    """Payment method enumeration."""

    CASH = "cash"
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    OTHER = "other"


class Expense(SoftDeletableModel):
    """Expense model for expense management."""

    __tablename__ = "expenses"

    # Basic fields
    expense_number: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, comment="Expense number"
    )
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Expense title"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Expense description"
    )

    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, comment="Organization ID"
    )
    employee_id: Mapped[UserId] = mapped_column(
        ForeignKey("users.id"), nullable=False, comment="Employee ID"
    )
    project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("projects.id"), nullable=True, comment="Project ID"
    )
    expense_category_id: Mapped[int] = mapped_column(
        ForeignKey("expense_categories.id"), nullable=False, comment="Category ID"
    )

    # Expense details
    expense_date: Mapped[date] = mapped_column(
        Date, nullable=False, comment="Expense date"
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, comment="Expense amount"
    )
    currency: Mapped[str] = mapped_column(
        String(3), default="JPY", comment="Currency code"
    )
    payment_method: Mapped[PaymentMethod] = mapped_column(
        String(50), nullable=False, comment="Payment method"
    )

    # Receipt information
    receipt_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Receipt image URL"
    )
    receipt_number: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Receipt number"
    )
    vendor_name: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="Vendor name"
    )

    # Status and approval
    status: Mapped[ExpenseStatus] = mapped_column(
        String(50), default=ExpenseStatus.DRAFT, comment="Expense status"
    )
    approved_by: Mapped[Optional[UserId]] = mapped_column(
        ForeignKey("users.id"), nullable=True, comment="Approver user ID"
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Approval timestamp"
    )
    rejected_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Rejection reason"
    )

    # Payment information
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Payment timestamp"
    )
    paid_by: Mapped[Optional[UserId]] = mapped_column(
        ForeignKey("users.id"), nullable=True, comment="Payment processor ID"
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", lazy="select")
    employee: Mapped["User"] = relationship(
        "User", foreign_keys=[employee_id], lazy="select"
    )
    project: Mapped[Optional["Project"]] = relationship("Project", lazy="select")
    expense_category: Mapped["ExpenseCategory"] = relationship(
        "ExpenseCategory", lazy="select"
    )
    approved_by_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[approved_by], lazy="select"
    )
    paid_by_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[paid_by], lazy="select"
    )

    @property
    def is_pending_approval(self) -> bool:
        """Check if expense is pending approval."""
        return self.status == ExpenseStatus.SUBMITTED

    @property
    def is_approved(self) -> bool:
        """Check if expense is approved."""
        return self.status == ExpenseStatus.APPROVED

    @property
    def is_paid(self) -> bool:
        """Check if expense is paid."""
        return self.status == ExpenseStatus.PAID

    def __str__(self) -> str:
        return f"{self.expense_number} - {self.title}"


class ExpenseApprovalFlow(SoftDeletableModel):
    """Expense approval flow model."""

    __tablename__ = "expense_approval_flows"

    # Foreign keys
    expense_id: Mapped[int] = mapped_column(
        ForeignKey("expenses.id"), nullable=False, comment="Expense ID"
    )
    approver_id: Mapped[UserId] = mapped_column(
        ForeignKey("users.id"), nullable=False, comment="Approver ID"
    )

    # Flow details
    approval_level: Mapped[int] = mapped_column(
        nullable=False, comment="Approval level (1, 2, 3, ...)"
    )
    is_required: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Required approval"
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Approval timestamp"
    )
    comments: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Approval comments"
    )

    # Relationships
    expense: Mapped["Expense"] = relationship("Expense", lazy="select")
    approver: Mapped["User"] = relationship(
        "User", foreign_keys=[approver_id], lazy="select"
    )

    @property
    def is_approved(self) -> bool:
        """Check if this level is approved."""
        return self.approved_at is not None

    def __str__(self) -> str:
        return f"Level {self.approval_level} for {self.expense.expense_number}"
