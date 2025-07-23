"""
Finance API Schemas - CC02 v31.0 Phase 2

Pydantic schemas for financial management API including:
- Chart of Accounts
- Journal Entries
- Budget Management
- Cost Centers
- Financial Reports
- Tax Configuration
- Audit Logging
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.models.finance_extended import (
    AccountType,
    BudgetStatus,
    FinancialPeriodStatus,
    TransactionType,
)

# =============================================================================
# Account Schemas
# =============================================================================


class AccountBase(BaseModel):
    """Base schema for Account."""

    organization_id: str
    account_code: Optional[str] = None
    account_name: str
    account_type: AccountType
    parent_account_id: Optional[str] = None
    is_active: bool = True
    is_system_account: bool = False
    allow_transactions: bool = True
    require_department: bool = False
    require_project: bool = False
    normal_balance: TransactionType
    tax_category_id: Optional[str] = None
    is_tax_account: bool = False
    bank_account_number: Optional[str] = None
    bank_routing_number: Optional[str] = None
    bank_name: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}


class AccountCreate(AccountBase):
    """Schema for creating Account."""

    pass


class AccountUpdate(BaseModel):
    """Schema for updating Account."""

    account_name: Optional[str] = None
    is_active: Optional[bool] = None
    allow_transactions: Optional[bool] = None
    require_department: Optional[bool] = None
    require_project: Optional[bool] = None
    tax_category_id: Optional[str] = None
    is_tax_account: Optional[bool] = None
    bank_account_number: Optional[str] = None
    bank_routing_number: Optional[str] = None
    bank_name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class AccountResponse(AccountBase):
    """Schema for Account response."""

    id: str
    account_level: int
    account_path: str
    current_balance: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True


# =============================================================================
# Journal Entry Schemas
# =============================================================================


class JournalEntryLineBase(BaseModel):
    """Base schema for Journal Entry Line."""

    account_id: str
    description: Optional[str] = None
    debit_amount: Decimal = Field(default=0, ge=0)
    credit_amount: Decimal = Field(default=0, ge=0)
    department_id: Optional[str] = None
    cost_center_id: Optional[str] = None
    project_id: Optional[str] = None
    reference_document: Optional[str] = None
    reference_line: Optional[int] = None
    tax_amount: Decimal = Field(default=0, ge=0)
    tax_code: Optional[str] = None
    custom_fields: Dict[str, Any] = {}

    @validator("debit_amount", "credit_amount")
    def validate_amounts(cls, v, values):
        """Validate that either debit or credit is specified, not both."""
        if "debit_amount" in values:
            debit = values["debit_amount"]
            if v > 0 and debit > 0:
                raise ValueError("Cannot have both debit and credit amounts")
        return v


class JournalEntryLineCreate(JournalEntryLineBase):
    """Schema for creating Journal Entry Line."""

    pass


class JournalEntryLineResponse(JournalEntryLineBase):
    """Schema for Journal Entry Line response."""

    id: str
    journal_entry_id: str
    line_number: int
    created_at: datetime

    class Config:
        from_attributes = True


class JournalEntryBase(BaseModel):
    """Base schema for Journal Entry."""

    organization_id: str
    reference_number: Optional[str] = None
    source_document: Optional[str] = None
    transaction_date: datetime
    period_id: Optional[str] = None
    description: str
    memo: Optional[str] = None
    currency_code: str = "JPY"
    exchange_rate: Decimal = Field(default=1.0, gt=0)
    source_module: Optional[str] = None
    source_transaction_id: Optional[str] = None
    requires_approval: bool = False
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}


class JournalEntryCreate(JournalEntryBase):
    """Schema for creating Journal Entry."""

    lines: List[JournalEntryLineCreate] = Field(min_items=2)

    @validator("lines")
    def validate_balanced_entry(cls, v):
        """Validate that debits equal credits."""
        total_debits = sum(line.debit_amount for line in v)
        total_credits = sum(line.credit_amount for line in v)

        if abs(total_debits - total_credits) > 0.01:
            raise ValueError("Debits must equal credits")

        return v


class JournalEntryUpdate(BaseModel):
    """Schema for updating Journal Entry."""

    reference_number: Optional[str] = None
    source_document: Optional[str] = None
    description: Optional[str] = None
    memo: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class JournalEntryResponse(JournalEntryBase):
    """Schema for Journal Entry response."""

    id: str
    entry_number: str
    total_debit: Decimal
    total_credit: Decimal
    is_posted: bool
    is_reversed: bool
    reversal_entry_id: Optional[str] = None
    posting_date: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str
    updated_by: Optional[str] = None
    lines: List[JournalEntryLineResponse] = []

    class Config:
        from_attributes = True


# =============================================================================
# Budget Schemas
# =============================================================================


class BudgetLineBase(BaseModel):
    """Base schema for Budget Line."""

    account_id: str
    line_description: Optional[str] = None
    annual_budget: Decimal = Field(default=0)
    q1_budget: Decimal = Field(default=0)
    q2_budget: Decimal = Field(default=0)
    q3_budget: Decimal = Field(default=0)
    q4_budget: Decimal = Field(default=0)
    jan_budget: Decimal = Field(default=0)
    feb_budget: Decimal = Field(default=0)
    mar_budget: Decimal = Field(default=0)
    apr_budget: Decimal = Field(default=0)
    may_budget: Decimal = Field(default=0)
    jun_budget: Decimal = Field(default=0)
    jul_budget: Decimal = Field(default=0)
    aug_budget: Decimal = Field(default=0)
    sep_budget: Decimal = Field(default=0)
    oct_budget: Decimal = Field(default=0)
    nov_budget: Decimal = Field(default=0)
    dec_budget: Decimal = Field(default=0)
    department_id: Optional[str] = None
    cost_center_id: Optional[str] = None
    project_id: Optional[str] = None
    notes: Optional[str] = None
    custom_fields: Dict[str, Any] = {}


class BudgetLineCreate(BudgetLineBase):
    """Schema for creating Budget Line."""

    pass


class BudgetLineResponse(BudgetLineBase):
    """Schema for Budget Line response."""

    id: str
    budget_id: str
    line_number: int
    actual_amount: Decimal
    variance_amount: Decimal
    variance_percentage: Decimal
    is_committed: bool
    committed_amount: Decimal
    available_amount: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BudgetBase(BaseModel):
    """Base schema for Budget."""

    organization_id: str
    period_id: str
    budget_name: str
    budget_code: str
    budget_type: str = "operational"
    budget_start_date: datetime
    budget_end_date: datetime
    allow_overspend: bool = False
    warning_threshold: Decimal = Field(default=90, ge=0, le=100)
    description: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}


class BudgetCreate(BudgetBase):
    """Schema for creating Budget."""

    pass


class BudgetUpdate(BaseModel):
    """Schema for updating Budget."""

    budget_name: Optional[str] = None
    allow_overspend: Optional[bool] = None
    warning_threshold: Optional[Decimal] = Field(None, ge=0, le=100)
    description: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class BudgetResponse(BudgetBase):
    """Schema for Budget response."""

    id: str
    status: BudgetStatus
    version: int
    total_revenue_budget: Decimal
    total_expense_budget: Decimal
    net_budget: Decimal
    total_revenue_actual: Decimal
    total_expense_actual: Decimal
    net_actual: Decimal
    revenue_variance: Decimal
    expense_variance: Decimal
    net_variance: Decimal
    submitted_date: Optional[datetime] = None
    submitted_by: Optional[str] = None
    approved_date: Optional[datetime] = None
    approved_by: Optional[str] = None
    approval_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str
    updated_by: Optional[str] = None
    budget_lines: List[BudgetLineResponse] = []

    class Config:
        from_attributes = True


# =============================================================================
# Cost Center Schemas
# =============================================================================


class CostCenterBase(BaseModel):
    """Base schema for Cost Center."""

    organization_id: str
    cost_center_code: Optional[str] = None
    cost_center_name: str
    cost_center_type: str = "operational"
    parent_cost_center_id: Optional[str] = None
    manager_id: Optional[str] = None
    department_id: Optional[str] = None
    budget_amount: Decimal = Field(default=0, ge=0)
    is_active: bool = True
    is_profit_center: bool = False
    allow_direct_charges: bool = True
    allocation_method: Optional[str] = None
    allocation_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    allocation_driver: Optional[str] = None
    effective_date: datetime
    expiration_date: Optional[datetime] = None
    description: Optional[str] = None
    purpose: Optional[str] = None
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}


class CostCenterCreate(CostCenterBase):
    """Schema for creating Cost Center."""

    pass


class CostCenterUpdate(BaseModel):
    """Schema for updating Cost Center."""

    cost_center_name: Optional[str] = None
    cost_center_type: Optional[str] = None
    manager_id: Optional[str] = None
    budget_amount: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None
    is_profit_center: Optional[bool] = None
    allow_direct_charges: Optional[bool] = None
    allocation_method: Optional[str] = None
    allocation_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    allocation_driver: Optional[str] = None
    expiration_date: Optional[datetime] = None
    description: Optional[str] = None
    purpose: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class CostCenterResponse(CostCenterBase):
    """Schema for Cost Center response."""

    id: str
    cost_center_level: int
    actual_amount: Decimal
    committed_amount: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True


# =============================================================================
# Financial Period Schemas
# =============================================================================


class FinancialPeriodBase(BaseModel):
    """Base schema for Financial Period."""

    organization_id: str
    period_name: str
    period_code: str
    fiscal_year: int = Field(ge=1900, le=2100)
    period_number: int = Field(ge=1, le=12)
    start_date: datetime
    end_date: datetime
    is_adjustment_period: bool = False


class FinancialPeriodCreate(FinancialPeriodBase):
    """Schema for creating Financial Period."""

    pass


class FinancialPeriodUpdate(BaseModel):
    """Schema for updating Financial Period."""

    period_name: Optional[str] = None
    allow_transactions: Optional[bool] = None


class FinancialPeriodResponse(FinancialPeriodBase):
    """Schema for Financial Period response."""

    id: str
    status: FinancialPeriodStatus
    allow_transactions: bool
    opening_balance_posted: bool
    closing_balance_calculated: bool
    closed_date: Optional[datetime] = None
    closed_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str

    class Config:
        from_attributes = True


# =============================================================================
# Financial Report Schemas
# =============================================================================


class FinancialReportBase(BaseModel):
    """Base schema for Financial Report."""

    organization_id: str
    report_name: str
    report_code: str
    report_type: str = Field(regex="^(balance_sheet|income_statement|cash_flow)$")
    template_data: Optional[Dict[str, Any]] = None
    format_options: Dict[str, Any] = {}
    is_public: bool = False
    authorized_users: List[str] = []
    authorized_roles: List[str] = []
    auto_generate: bool = False
    schedule_frequency: Optional[str] = None
    output_formats: List[str] = ["pdf", "excel"]
    email_recipients: List[str] = []
    description: Optional[str] = None
    parameters: Dict[str, Any] = {}
    tags: List[str] = []


class FinancialReportCreate(FinancialReportBase):
    """Schema for creating Financial Report."""

    pass


class FinancialReportUpdate(BaseModel):
    """Schema for updating Financial Report."""

    report_name: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    format_options: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
    authorized_users: Optional[List[str]] = None
    authorized_roles: Optional[List[str]] = None
    auto_generate: Optional[bool] = None
    schedule_frequency: Optional[str] = None
    output_formats: Optional[List[str]] = None
    email_recipients: Optional[List[str]] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class FinancialReportResponse(FinancialReportBase):
    """Schema for Financial Report response."""

    id: str
    is_active: bool
    next_generation_date: Optional[datetime] = None
    last_generated_at: Optional[datetime] = None
    last_generated_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True


# =============================================================================
# Tax Configuration Schemas
# =============================================================================


class TaxConfigurationBase(BaseModel):
    """Base schema for Tax Configuration."""

    organization_id: str
    tax_name: str
    tax_code: str
    tax_type: str = Field(regex="^(sales_tax|vat|income_tax|withholding)$")
    tax_rate: Decimal = Field(ge=0, le=100)
    minimum_amount: Decimal = Field(default=0, ge=0)
    maximum_amount: Optional[Decimal] = Field(None, gt=0)
    applies_to_sales: bool = True
    applies_to_purchases: bool = True
    tax_payable_account_id: Optional[str] = None
    tax_receivable_account_id: Optional[str] = None
    tax_expense_account_id: Optional[str] = None
    effective_date: datetime
    expiration_date: Optional[datetime] = None
    is_compound: bool = False
    calculation_method: str = "percentage"
    tax_authority: Optional[str] = None
    reporting_code: Optional[str] = None
    description: Optional[str] = None
    jurisdiction: Optional[str] = None


class TaxConfigurationCreate(TaxConfigurationBase):
    """Schema for creating Tax Configuration."""

    pass


class TaxConfigurationUpdate(BaseModel):
    """Schema for updating Tax Configuration."""

    tax_name: Optional[str] = None
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    minimum_amount: Optional[Decimal] = Field(None, ge=0)
    maximum_amount: Optional[Decimal] = Field(None, gt=0)
    applies_to_sales: Optional[bool] = None
    applies_to_purchases: Optional[bool] = None
    tax_payable_account_id: Optional[str] = None
    tax_receivable_account_id: Optional[str] = None
    tax_expense_account_id: Optional[str] = None
    expiration_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    is_compound: Optional[bool] = None
    calculation_method: Optional[str] = None
    tax_authority: Optional[str] = None
    reporting_code: Optional[str] = None
    description: Optional[str] = None
    jurisdiction: Optional[str] = None


class TaxConfigurationResponse(TaxConfigurationBase):
    """Schema for Tax Configuration response."""

    id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str

    class Config:
        from_attributes = True


# =============================================================================
# Financial Analysis Schemas
# =============================================================================


class TrialBalanceLine(BaseModel):
    """Schema for trial balance line item."""

    account_id: str
    account_code: str
    account_name: str
    account_type: str
    debit_balance: Decimal
    credit_balance: Decimal
    total_debits: Decimal
    total_credits: Decimal


class TrialBalanceResponse(BaseModel):
    """Schema for trial balance report."""

    organization_id: str
    as_of_date: datetime
    accounts: List[TrialBalanceLine]
    total_debits: Decimal
    total_credits: Decimal
    is_balanced: bool


class BudgetVarianceAnalysisLine(BaseModel):
    """Schema for budget variance analysis line."""

    account_id: str
    account_code: str
    account_name: str
    budget_amount: Decimal
    actual_amount: Decimal
    variance_amount: Decimal
    variance_percentage: Decimal
    status: str  # on_track, watch, concern, critical


class BudgetVarianceAnalysisResponse(BaseModel):
    """Schema for budget variance analysis."""

    budget_id: str
    budget_name: str
    analysis_date: datetime
    total_budget: Decimal
    total_actual: Decimal
    total_variance: Decimal
    line_variances: List[BudgetVarianceAnalysisLine]


class CostCenterPerformanceResponse(BaseModel):
    """Schema for cost center performance metrics."""

    cost_center_id: str
    cost_center_code: str
    cost_center_name: str
    period_start: datetime
    period_end: datetime
    budget_amount: Decimal
    actual_amount: Decimal
    committed_amount: Decimal
    available_amount: Decimal
    budget_variance: Decimal
    budget_variance_percentage: Decimal
    utilization_percentage: Decimal


class BalanceSheetAccount(BaseModel):
    """Schema for balance sheet account line."""

    account_id: str
    account_code: str
    account_name: str
    balance: Decimal
    debit_total: Decimal
    credit_total: Decimal


class BalanceSheetSection(BaseModel):
    """Schema for balance sheet section."""

    accounts: List[BalanceSheetAccount]
    total: Decimal


class BalanceSheetResponse(BaseModel):
    """Schema for balance sheet report."""

    report_type: str = "balance_sheet"
    organization_id: str
    as_of_date: datetime
    assets: BalanceSheetSection
    liabilities: BalanceSheetSection
    equity: BalanceSheetSection
    total_liabilities_equity: Decimal
    balanced: bool


class IncomeStatementResponse(BaseModel):
    """Schema for income statement report."""

    report_type: str = "income_statement"
    organization_id: str
    start_date: datetime
    end_date: datetime
    revenue: BalanceSheetSection  # Reuse for consistency
    expenses: BalanceSheetSection
    net_income: Decimal
    gross_margin: Decimal
    margin_percentage: Decimal


class TaxCalculationResponse(BaseModel):
    """Schema for tax calculation result."""

    tax_code: str
    tax_name: str
    tax_rate: Decimal
    base_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    tax_type: str


# =============================================================================
# Request Schemas for Actions
# =============================================================================


class PostJournalEntryRequest(BaseModel):
    """Schema for posting journal entry."""

    journal_entry_id: str


class ReverseJournalEntryRequest(BaseModel):
    """Schema for reversing journal entry."""

    journal_entry_id: str
    reason: str


class ApproveBudgetRequest(BaseModel):
    """Schema for approving budget."""

    budget_id: str
    approval_notes: Optional[str] = None


class ClosePeriodRequest(BaseModel):
    """Schema for closing financial period."""

    period_id: str


class TaxCalculationRequest(BaseModel):
    """Schema for tax calculation."""

    tax_code: str
    base_amount: Decimal
    effective_date: Optional[datetime] = None
