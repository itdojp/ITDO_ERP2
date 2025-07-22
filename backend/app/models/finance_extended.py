"""
Finance Management Models - CC02 v31.0 Phase 2

Comprehensive financial management system with:
- Chart of Accounts
- Journal Entries
- Financial Transactions
- Budget Management
- Cost Centers
- Financial Reports
- Tax Management
- Audit Trails
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class AccountType(str, Enum):
    """Account types for chart of accounts."""

    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class TransactionType(str, Enum):
    """Transaction types for journal entries."""

    CREDIT = "credit"
    DEBIT = "debit"


class BudgetStatus(str, Enum):
    """Budget status enumeration."""

    DRAFT = "draft"
    ACTIVE = "active"
    LOCKED = "locked"
    ARCHIVED = "archived"


class FinancialPeriodStatus(str, Enum):
    """Financial period status."""

    OPEN = "open"
    CLOSED = "closed"
    LOCKED = "locked"


class Account(Base):
    """Chart of Accounts - Account management."""

    __tablename__ = "finance_accounts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Account identification
    account_code = Column(String(50), nullable=False, index=True)
    account_name = Column(String(200), nullable=False)
    account_type = Column(SQLEnum(AccountType), nullable=False)
    
    # Hierarchy
    parent_account_id = Column(String, ForeignKey("finance_accounts.id"))
    account_level = Column(Integer, default=0)
    account_path = Column(String(500))  # Hierarchical path
    
    # Configuration
    is_active = Column(Boolean, default=True)
    is_system_account = Column(Boolean, default=False)
    allow_transactions = Column(Boolean, default=True)
    require_department = Column(Boolean, default=False)
    require_project = Column(Boolean, default=False)
    
    # Financial properties
    normal_balance = Column(SQLEnum(TransactionType), nullable=False)
    current_balance = Column(Numeric(15, 2), default=0)
    
    # Tax configuration
    tax_category_id = Column(String)
    is_tax_account = Column(Boolean, default=False)
    
    # Banking
    bank_account_number = Column(String(50))
    bank_routing_number = Column(String(20))
    bank_name = Column(String(200))
    
    # Metadata
    description = Column(Text)
    tags = Column(JSON, default=[])
    custom_fields = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))
    updated_by = Column(String, ForeignKey("users.id"))

    # Relationships
    organization = relationship("Organization")
    parent_account = relationship("Account", remote_side=[id])
    child_accounts = relationship("Account")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    journal_entries = relationship("JournalEntryLine", back_populates="account")


class JournalEntry(Base):
    """Journal Entry Header - Financial transaction recording."""

    __tablename__ = "finance_journal_entries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Entry identification
    entry_number = Column(String(50), nullable=False, unique=True, index=True)
    reference_number = Column(String(100))
    source_document = Column(String(100))
    
    # Transaction details
    transaction_date = Column(DateTime, nullable=False)
    posting_date = Column(DateTime)
    period_id = Column(String, ForeignKey("finance_periods.id"))
    
    # Description and memo
    description = Column(Text, nullable=False)
    memo = Column(Text)
    
    # Financial details
    total_debit = Column(Numeric(15, 2), default=0)
    total_credit = Column(Numeric(15, 2), default=0)
    currency_code = Column(String(3), default="JPY")
    exchange_rate = Column(Numeric(10, 6), default=1.0)
    
    # Status and control
    is_posted = Column(Boolean, default=False)
    is_reversed = Column(Boolean, default=False)
    reversal_entry_id = Column(String, ForeignKey("finance_journal_entries.id"))
    
    # Source tracking
    source_module = Column(String(50))  # sales, purchase, inventory, etc.
    source_transaction_id = Column(String)
    
    # Approval workflow
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(String, ForeignKey("users.id"))
    approved_at = Column(DateTime)
    approval_notes = Column(Text)
    
    # Metadata
    tags = Column(JSON, default=[])
    custom_fields = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))
    updated_by = Column(String, ForeignKey("users.id"))

    # Relationships
    organization = relationship("Organization")
    period = relationship("FinancialPeriod")
    reversal_entry = relationship("JournalEntry", remote_side=[id])
    approver = relationship("User", foreign_keys=[approved_by])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    lines = relationship("JournalEntryLine", back_populates="journal_entry", cascade="all, delete-orphan")


class JournalEntryLine(Base):
    """Journal Entry Line - Individual account transactions."""

    __tablename__ = "finance_journal_entry_lines"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    journal_entry_id = Column(String, ForeignKey("finance_journal_entries.id"), nullable=False)
    account_id = Column(String, ForeignKey("finance_accounts.id"), nullable=False)

    # Line details
    line_number = Column(Integer, nullable=False)
    description = Column(Text)
    
    # Financial amounts
    debit_amount = Column(Numeric(15, 2), default=0)
    credit_amount = Column(Numeric(15, 2), default=0)
    
    # Dimensions for analysis
    department_id = Column(String, ForeignKey("departments.id"))
    cost_center_id = Column(String, ForeignKey("finance_cost_centers.id"))
    project_id = Column(String)
    
    # Reference information
    reference_document = Column(String(100))
    reference_line = Column(Integer)
    
    # Tax information
    tax_amount = Column(Numeric(10, 2), default=0)
    tax_code = Column(String(20))
    
    # Metadata
    custom_fields = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    journal_entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account", back_populates="journal_entries")
    cost_center = relationship("CostCenter")


class FinancialPeriod(Base):
    """Financial Period Management - Fiscal periods and accounting cycles."""

    __tablename__ = "finance_periods"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Period identification
    period_name = Column(String(100), nullable=False)
    period_code = Column(String(20), nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    period_number = Column(Integer, nullable=False)
    
    # Date ranges
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Status
    status = Column(SQLEnum(FinancialPeriodStatus), default=FinancialPeriodStatus.OPEN)
    closed_date = Column(DateTime)
    closed_by = Column(String, ForeignKey("users.id"))
    
    # Configuration
    is_adjustment_period = Column(Boolean, default=False)
    allow_transactions = Column(Boolean, default=True)
    
    # Balances
    opening_balance_posted = Column(Boolean, default=False)
    closing_balance_calculated = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))

    # Relationships
    organization = relationship("Organization")
    closer = relationship("User", foreign_keys=[closed_by])
    creator = relationship("User", foreign_keys=[created_by])
    journal_entries = relationship("JournalEntry", back_populates="period")
    budgets = relationship("Budget", back_populates="period")


class Budget(Base):
    """Budget Management - Financial planning and control."""

    __tablename__ = "finance_budgets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    period_id = Column(String, ForeignKey("finance_periods.id"), nullable=False)

    # Budget identification
    budget_name = Column(String(200), nullable=False)
    budget_code = Column(String(50), nullable=False)
    budget_type = Column(String(50), default="operational")  # operational, capital, cash_flow
    
    # Status and approval
    status = Column(SQLEnum(BudgetStatus), default=BudgetStatus.DRAFT)
    version = Column(Integer, default=1)
    
    # Date ranges
    budget_start_date = Column(DateTime, nullable=False)
    budget_end_date = Column(DateTime, nullable=False)
    
    # Approval workflow
    submitted_date = Column(DateTime)
    submitted_by = Column(String, ForeignKey("users.id"))
    approved_date = Column(DateTime)
    approved_by = Column(String, ForeignKey("users.id"))
    approval_notes = Column(Text)
    
    # Budget totals
    total_revenue_budget = Column(Numeric(15, 2), default=0)
    total_expense_budget = Column(Numeric(15, 2), default=0)
    net_budget = Column(Numeric(15, 2), default=0)
    
    # Actuals tracking
    total_revenue_actual = Column(Numeric(15, 2), default=0)
    total_expense_actual = Column(Numeric(15, 2), default=0)
    net_actual = Column(Numeric(15, 2), default=0)
    
    # Variance analysis
    revenue_variance = Column(Numeric(15, 2), default=0)
    expense_variance = Column(Numeric(15, 2), default=0)
    net_variance = Column(Numeric(15, 2), default=0)
    
    # Configuration
    allow_overspend = Column(Boolean, default=False)
    warning_threshold = Column(Numeric(5, 2), default=90)  # Percentage
    
    # Metadata
    description = Column(Text)
    notes = Column(Text)
    tags = Column(JSON, default=[])
    custom_fields = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))
    updated_by = Column(String, ForeignKey("users.id"))

    # Relationships
    organization = relationship("Organization")
    period = relationship("FinancialPeriod", back_populates="budgets")
    submitter = relationship("User", foreign_keys=[submitted_by])
    approver = relationship("User", foreign_keys=[approved_by])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    budget_lines = relationship("BudgetLine", back_populates="budget", cascade="all, delete-orphan")


class BudgetLine(Base):
    """Budget Line Items - Detailed budget allocations."""

    __tablename__ = "finance_budget_lines"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    budget_id = Column(String, ForeignKey("finance_budgets.id"), nullable=False)
    account_id = Column(String, ForeignKey("finance_accounts.id"), nullable=False)

    # Line identification
    line_number = Column(Integer, nullable=False)
    line_description = Column(Text)
    
    # Budget amounts by period
    annual_budget = Column(Numeric(15, 2), default=0)
    q1_budget = Column(Numeric(15, 2), default=0)
    q2_budget = Column(Numeric(15, 2), default=0)
    q3_budget = Column(Numeric(15, 2), default=0)
    q4_budget = Column(Numeric(15, 2), default=0)
    
    # Monthly breakdown
    jan_budget = Column(Numeric(12, 2), default=0)
    feb_budget = Column(Numeric(12, 2), default=0)
    mar_budget = Column(Numeric(12, 2), default=0)
    apr_budget = Column(Numeric(12, 2), default=0)
    may_budget = Column(Numeric(12, 2), default=0)
    jun_budget = Column(Numeric(12, 2), default=0)
    jul_budget = Column(Numeric(12, 2), default=0)
    aug_budget = Column(Numeric(12, 2), default=0)
    sep_budget = Column(Numeric(12, 2), default=0)
    oct_budget = Column(Numeric(12, 2), default=0)
    nov_budget = Column(Numeric(12, 2), default=0)
    dec_budget = Column(Numeric(12, 2), default=0)
    
    # Actual amounts for comparison
    actual_amount = Column(Numeric(15, 2), default=0)
    variance_amount = Column(Numeric(15, 2), default=0)
    variance_percentage = Column(Numeric(6, 2), default=0)
    
    # Dimensions
    department_id = Column(String, ForeignKey("departments.id"))
    cost_center_id = Column(String, ForeignKey("finance_cost_centers.id"))
    project_id = Column(String)
    
    # Control
    is_committed = Column(Boolean, default=False)
    committed_amount = Column(Numeric(15, 2), default=0)
    available_amount = Column(Numeric(15, 2), default=0)
    
    # Metadata
    notes = Column(Text)
    custom_fields = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    budget = relationship("Budget", back_populates="budget_lines")
    account = relationship("Account")
    cost_center = relationship("CostCenter")


class CostCenter(Base):
    """Cost Center Management - Cost allocation and analysis."""

    __tablename__ = "finance_cost_centers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Cost center identification
    cost_center_code = Column(String(50), nullable=False, unique=True)
    cost_center_name = Column(String(200), nullable=False)
    cost_center_type = Column(String(50), default="operational")  # operational, service, support
    
    # Hierarchy
    parent_cost_center_id = Column(String, ForeignKey("finance_cost_centers.id"))
    cost_center_level = Column(Integer, default=0)
    
    # Management
    manager_id = Column(String, ForeignKey("users.id"))
    department_id = Column(String, ForeignKey("departments.id"))
    
    # Financial tracking
    budget_amount = Column(Numeric(15, 2), default=0)
    actual_amount = Column(Numeric(15, 2), default=0)
    committed_amount = Column(Numeric(15, 2), default=0)
    
    # Configuration
    is_active = Column(Boolean, default=True)
    is_profit_center = Column(Boolean, default=False)
    allow_direct_charges = Column(Boolean, default=True)
    
    # Allocation rules
    allocation_method = Column(String(50))  # direct, percentage, activity_based
    allocation_percentage = Column(Numeric(5, 2))
    allocation_driver = Column(String(100))
    
    # Dates
    effective_date = Column(DateTime, nullable=False)
    expiration_date = Column(DateTime)
    
    # Metadata
    description = Column(Text)
    purpose = Column(Text)
    tags = Column(JSON, default=[])
    custom_fields = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))
    updated_by = Column(String, ForeignKey("users.id"))

    # Relationships
    organization = relationship("Organization")
    parent_cost_center = relationship("CostCenter", remote_side=[id])
    child_cost_centers = relationship("CostCenter")
    manager = relationship("User", foreign_keys=[manager_id])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    journal_entry_lines = relationship("JournalEntryLine", back_populates="cost_center")
    budget_lines = relationship("BudgetLine", back_populates="cost_center")


class FinancialReport(Base):
    """Financial Report Configuration - Report templates and generation."""

    __tablename__ = "finance_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Report identification
    report_name = Column(String(200), nullable=False)
    report_code = Column(String(50), nullable=False)
    report_type = Column(String(50), nullable=False)  # balance_sheet, income_statement, cash_flow
    
    # Template configuration
    template_data = Column(JSON)
    format_options = Column(JSON, default={})
    
    # Access control
    is_public = Column(Boolean, default=False)
    authorized_users = Column(JSON, default=[])
    authorized_roles = Column(JSON, default=[])
    
    # Scheduling
    auto_generate = Column(Boolean, default=False)
    schedule_frequency = Column(String(50))  # daily, weekly, monthly, quarterly
    next_generation_date = Column(DateTime)
    
    # Output options
    output_formats = Column(JSON, default=["pdf", "excel"])
    email_recipients = Column(JSON, default=[])
    
    # Status
    is_active = Column(Boolean, default=True)
    last_generated_at = Column(DateTime)
    last_generated_by = Column(String, ForeignKey("users.id"))
    
    # Metadata
    description = Column(Text)
    parameters = Column(JSON, default={})
    tags = Column(JSON, default=[])
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))
    updated_by = Column(String, ForeignKey("users.id"))

    # Relationships
    organization = relationship("Organization")
    last_generator = relationship("User", foreign_keys=[last_generated_by])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])


class TaxConfiguration(Base):
    """Tax Configuration - Tax rates and calculation rules."""

    __tablename__ = "finance_tax_configurations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Tax identification
    tax_name = Column(String(200), nullable=False)
    tax_code = Column(String(50), nullable=False)
    tax_type = Column(String(50), nullable=False)  # sales_tax, vat, income_tax, withholding
    
    # Tax rates
    tax_rate = Column(Numeric(6, 4), nullable=False)  # Percentage as decimal
    minimum_amount = Column(Numeric(12, 2), default=0)
    maximum_amount = Column(Numeric(12, 2))
    
    # Applicability
    applies_to_sales = Column(Boolean, default=True)
    applies_to_purchases = Column(Boolean, default=True)
    
    # Accounts
    tax_payable_account_id = Column(String, ForeignKey("finance_accounts.id"))
    tax_receivable_account_id = Column(String, ForeignKey("finance_accounts.id"))
    tax_expense_account_id = Column(String, ForeignKey("finance_accounts.id"))
    
    # Validity period
    effective_date = Column(DateTime, nullable=False)
    expiration_date = Column(DateTime)
    
    # Configuration
    is_active = Column(Boolean, default=True)
    is_compound = Column(Boolean, default=False)
    calculation_method = Column(String(50), default="percentage")
    
    # Reporting
    tax_authority = Column(String(200))
    reporting_code = Column(String(50))
    
    # Metadata
    description = Column(Text)
    jurisdiction = Column(String(200))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"))

    # Relationships
    organization = relationship("Organization")
    tax_payable_account = relationship("Account", foreign_keys=[tax_payable_account_id])
    tax_receivable_account = relationship("Account", foreign_keys=[tax_receivable_account_id])
    tax_expense_account = relationship("Account", foreign_keys=[tax_expense_account_id])
    creator = relationship("User", foreign_keys=[created_by])


class FinanceAuditLog(Base):
    """Finance Audit Log - Track all financial changes for compliance."""

    __tablename__ = "finance_audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Audit event details
    event_type = Column(String(50), nullable=False)  # create, update, delete, post, approve
    table_name = Column(String(100), nullable=False)
    record_id = Column(String, nullable=False)
    
    # Change tracking
    old_values = Column(JSON)
    new_values = Column(JSON)
    changed_fields = Column(JSON, default=[])
    
    # User and session
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Business context
    business_reason = Column(Text)
    reference_document = Column(String(100))
    
    # Risk assessment
    risk_level = Column(String(20), default="low")  # low, medium, high, critical
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(String, ForeignKey("users.id"))
    approved_at = Column(DateTime)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization")
    user = relationship("User", foreign_keys=[user_id])
    approver = relationship("User", foreign_keys=[approved_by])