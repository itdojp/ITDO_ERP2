"""
ITDO ERP Backend - Financial Management Models
Day 24: Core financial management data models
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    DECIMAL,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.types import AccountId, DepartmentId, OrganizationId, UserId


class Account(Base):
    """Chart of accounts model for financial management"""

    __tablename__ = "accounts"

    id: Mapped[AccountId] = mapped_column(primary_key=True)
    organization_id: Mapped[OrganizationId] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    account_code: Mapped[str] = mapped_column(String(20), nullable=False)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)
    parent_account_id: Mapped[Optional[AccountId]] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    balance: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2), default=Decimal("0.00"), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    # organization: Mapped["Organization"] = relationship(back_populates="accounts")
    parent_account: Mapped[Optional["Account"]] = relationship(
        "Account", remote_side=[id], back_populates="child_accounts"
    )
    child_accounts: Mapped[List["Account"]] = relationship(
        "Account", back_populates="parent_account"
    )
    journal_entries: Mapped[List["JournalEntry"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    budget_items: Mapped[List["BudgetItem"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "account_type IN ('asset', 'liability', 'equity', 'revenue', 'expense')",
            name="ck_account_type",
        ),
        Index("ix_accounts_org_code", organization_id, account_code),
        Index("ix_accounts_type", account_type),
        Index("ix_accounts_parent", parent_account_id),
    )

    def __repr__(self) -> str:
        return f"<Account(id={self.id}, code={self.account_code}, name={self.account_name})>"


class JournalEntry(Base):
    """Journal entries for double-entry bookkeeping"""

    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[OrganizationId] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[AccountId] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    transaction_id: Mapped[str] = mapped_column(String(50), nullable=False)
    entry_date: Mapped[date] = mapped_column(nullable=False)
    debit_amount: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(15, 2), nullable=True
    )
    credit_amount: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(15, 2), nullable=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    posted_by: Mapped[UserId] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    is_posted: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    # organization: Mapped["Organization"] = relationship(back_populates="journal_entries")
    account: Mapped["Account"] = relationship(back_populates="journal_entries")
    # posted_by_user: Mapped[Optional["User"]] = relationship(
    #     foreign_keys=[posted_by], back_populates="posted_entries"
    # )

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "(debit_amount IS NOT NULL AND credit_amount IS NULL) OR "
            "(credit_amount IS NOT NULL AND debit_amount IS NULL)",
            name="ck_debit_or_credit",
        ),
        CheckConstraint("debit_amount >= 0", name="ck_debit_positive"),
        CheckConstraint("credit_amount >= 0", name="ck_credit_positive"),
        Index("ix_journal_org_date", organization_id, entry_date),
        Index("ix_journal_transaction", transaction_id),
        Index("ix_journal_account_date", account_id, entry_date),
    )

    def __repr__(self) -> str:
        amount = self.debit_amount or self.credit_amount
        return f"<JournalEntry(id={self.id}, account_id={self.account_id}, amount={amount})>"


class Budget(Base):
    """Annual/periodic budgets for financial planning"""

    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[OrganizationId] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    department_id: Mapped[Optional[DepartmentId]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    budget_name: Mapped[str] = mapped_column(String(255), nullable=False)
    fiscal_year: Mapped[int] = mapped_column(nullable=False)
    budget_period: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[date] = mapped_column(nullable=False)
    end_date: Mapped[date] = mapped_column(nullable=False)
    total_budget: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    total_actual: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2), default=Decimal("0.00"), nullable=False
    )
    variance: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2), default=Decimal("0.00"), nullable=False
    )
    variance_percentage: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 2), default=Decimal("0.00"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    approved_by: Mapped[Optional[UserId]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by: Mapped[UserId] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    # organization: Mapped["Organization"] = relationship(back_populates="budgets")
    # department: Mapped[Optional["Department"]] = relationship(
    #     back_populates="budgets"
    # )
    # approved_by_user: Mapped[Optional["User"]] = relationship(
    #     foreign_keys=[approved_by], back_populates="approved_budgets"
    # )
    # created_by_user: Mapped[Optional["User"]] = relationship(
    #     foreign_keys=[created_by], back_populates="created_budgets"
    # )
    budget_items: Mapped[List["BudgetItem"]] = relationship(
        back_populates="budget", cascade="all, delete-orphan"
    )

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "budget_period IN ('monthly', 'quarterly', 'semi-annual', 'annual')",
            name="ck_budget_period",
        ),
        CheckConstraint(
            "status IN ('draft', 'submitted', 'approved', 'rejected', 'active', 'closed')",
            name="ck_budget_status",
        ),
        CheckConstraint("start_date < end_date", name="ck_budget_date_range"),
        CheckConstraint("total_budget >= 0", name="ck_budget_positive"),
        Index("ix_budgets_org_year", organization_id, fiscal_year),
        Index("ix_budgets_department", department_id),
        Index("ix_budgets_period", start_date, end_date),
    )

    def __repr__(self) -> str:
        return f"<Budget(id={self.id}, name={self.budget_name}, fiscal_year={self.fiscal_year})>"


class BudgetItem(Base):
    """Individual line items within a budget"""

    __tablename__ = "budget_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    budget_id: Mapped[int] = mapped_column(
        ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[AccountId] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    budgeted_amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    actual_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2), default=Decimal("0.00"), nullable=False
    )
    variance: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2), default=Decimal("0.00"), nullable=False
    )
    variance_percentage: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 2), default=Decimal("0.00"), nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    budget: Mapped["Budget"] = relationship(back_populates="budget_items")
    account: Mapped["Account"] = relationship(back_populates="budget_items")

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("budgeted_amount >= 0", name="ck_budgeted_positive"),
        CheckConstraint("actual_amount >= 0", name="ck_actual_positive"),
        Index("ix_budget_items_budget", budget_id),
        Index("ix_budget_items_account", account_id),
    )

    def __repr__(self) -> str:
        return f"<BudgetItem(id={self.id}, name={self.item_name}, budgeted={self.budgeted_amount})>"


class FinancialReport(Base):
    """Generated financial reports storage"""

    __tablename__ = "financial_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[OrganizationId] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    report_name: Mapped[str] = mapped_column(String(255), nullable=False)
    period_start: Mapped[date] = mapped_column(nullable=False)
    period_end: Mapped[date] = mapped_column(nullable=False)
    report_data: Mapped[str] = mapped_column(Text, nullable=False)  # JSON data
    generated_by: Mapped[UserId] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    # organization: Mapped["Organization"] = relationship(
    #     back_populates="financial_reports"
    # )
    # generated_by_user: Mapped[Optional["User"]] = relationship(
    #     back_populates="generated_reports"
    # )

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "report_type IN ('balance_sheet', 'income_statement', 'cash_flow', 'budget_variance', 'trial_balance')",
            name="ck_report_type",
        ),
        CheckConstraint("period_start <= period_end", name="ck_report_period"),
        Index("ix_reports_org_type", organization_id, report_type),
        Index("ix_reports_period", period_start, period_end),
    )

    def __repr__(self) -> str:
        return f"<FinancialReport(id={self.id}, type={self.report_type}, period={self.period_start}-{self.period_end})>"


class CostCenter(Base):
    """Cost centers for expense allocation and tracking"""

    __tablename__ = "cost_centers"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[OrganizationId] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    department_id: Mapped[Optional[DepartmentId]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    center_code: Mapped[str] = mapped_column(String(20), nullable=False)
    center_name: Mapped[str] = mapped_column(String(255), nullable=False)
    manager_id: Mapped[Optional[UserId]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    budget_limit: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(15, 2), nullable=True
    )
    current_spend: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2), default=Decimal("0.00"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    # organization: Mapped["Organization"] = relationship(back_populates="cost_centers")
    # department: Mapped[Optional["Department"]] = relationship(
    #     back_populates="cost_centers"
    # )
    # manager: Mapped[Optional["User"]] = relationship(
    #     back_populates="managed_cost_centers"
    # )

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("budget_limit >= 0", name="ck_budget_limit_positive"),
        CheckConstraint("current_spend >= 0", name="ck_current_spend_positive"),
        Index("ix_cost_centers_org_code", organization_id, center_code),
        Index("ix_cost_centers_department", department_id),
        Index("ix_cost_centers_manager", manager_id),
    )

    def __repr__(self) -> str:
        return f"<CostCenter(id={self.id}, code={self.center_code}, name={self.center_name})>"
