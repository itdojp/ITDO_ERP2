"""
ITDO ERP Backend - Financial Management Schemas
Day 24: Pydantic schemas for financial management APIs
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.types import AccountId, DepartmentId, OrganizationId, UserId


# Account Schemas
class AccountBase(BaseModel):
    """Base schema for account"""

    account_code: str = Field(..., min_length=1, max_length=20)
    account_name: str = Field(..., min_length=1, max_length=255)
    account_type: str = Field(..., regex="^(asset|liability|equity|revenue|expense)$")
    parent_account_id: Optional[AccountId] = None
    is_active: bool = True
    description: Optional[str] = None


class AccountCreate(AccountBase):
    """Schema for creating accounts"""

    organization_id: OrganizationId


class AccountUpdate(BaseModel):
    """Schema for updating accounts"""

    account_name: Optional[str] = Field(None, min_length=1, max_length=255)
    account_type: Optional[str] = Field(
        None, regex="^(asset|liability|equity|revenue|expense)$"
    )
    parent_account_id: Optional[AccountId] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class AccountResponse(AccountBase):
    """Schema for account responses"""

    id: AccountId
    organization_id: OrganizationId
    balance: Decimal
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class AccountBalanceResponse(BaseModel):
    """Schema for account balance information"""

    account_id: AccountId
    account_code: str
    account_name: str
    account_type: str
    balance: Decimal
    child_accounts: List["AccountBalanceResponse"] = []

    class Config:
        from_attributes = True


# Journal Entry Schemas
class JournalEntryBase(BaseModel):
    """Base schema for journal entries"""

    account_id: AccountId
    transaction_id: str = Field(..., min_length=1, max_length=50)
    entry_date: date
    debit_amount: Optional[Decimal] = Field(None, ge=0)
    credit_amount: Optional[Decimal] = Field(None, ge=0)
    description: str = Field(..., min_length=1)
    reference_number: Optional[str] = Field(None, max_length=100)

    @validator("debit_amount", "credit_amount")
    def validate_amounts(cls, v, values):
        """Ensure either debit or credit is specified, but not both"""
        debit = values.get("debit_amount")
        credit = values.get("credit_amount")

        if v is not None:
            if v == 0:
                raise ValueError("Amount cannot be zero")

        # Check after all fields are validated
        if "debit_amount" in values and "credit_amount" in values:
            if debit is not None and credit is not None:
                raise ValueError("Cannot specify both debit and credit amounts")
            if debit is None and credit is None:
                raise ValueError("Must specify either debit or credit amount")

        return v


class JournalEntryCreate(JournalEntryBase):
    """Schema for creating journal entries"""

    organization_id: OrganizationId


class JournalEntryUpdate(BaseModel):
    """Schema for updating journal entries"""

    debit_amount: Optional[Decimal] = Field(None, ge=0)
    credit_amount: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = Field(None, min_length=1)
    reference_number: Optional[str] = Field(None, max_length=100)


class JournalEntryResponse(JournalEntryBase):
    """Schema for journal entry responses"""

    id: int
    organization_id: OrganizationId
    is_posted: bool
    posted_by: Optional[UserId]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Budget Schemas
class BudgetBase(BaseModel):
    """Base schema for budgets"""

    budget_name: str = Field(..., min_length=1, max_length=255)
    fiscal_year: int = Field(..., ge=1900, le=2100)
    budget_period: str = Field(..., regex="^(monthly|quarterly|semi-annual|annual)$")
    start_date: date
    end_date: date
    total_budget: Decimal = Field(..., ge=0)
    department_id: Optional[DepartmentId] = None

    @validator("end_date")
    def validate_date_range(cls, v, values):
        """Ensure end date is after start date"""
        start_date = values.get("start_date")
        if start_date and v <= start_date:
            raise ValueError("End date must be after start date")
        return v


class BudgetCreate(BudgetBase):
    """Schema for creating budgets"""

    organization_id: OrganizationId


class BudgetUpdate(BaseModel):
    """Schema for updating budgets"""

    budget_name: Optional[str] = Field(None, min_length=1, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_budget: Optional[Decimal] = Field(None, ge=0)
    status: Optional[str] = Field(
        None, regex="^(draft|submitted|approved|rejected|active|closed)$"
    )


class BudgetResponse(BudgetBase):
    """Schema for budget responses"""

    id: int
    organization_id: OrganizationId
    total_actual: Decimal
    variance: Decimal
    variance_percentage: Decimal
    status: str
    approved_by: Optional[UserId]
    approved_at: Optional[datetime]
    created_by: Optional[UserId]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Budget Item Schemas
class BudgetItemBase(BaseModel):
    """Base schema for budget items"""

    account_id: AccountId
    item_name: str = Field(..., min_length=1, max_length=255)
    budgeted_amount: Decimal = Field(..., ge=0)
    notes: Optional[str] = None


class BudgetItemCreate(BudgetItemBase):
    """Schema for creating budget items"""

    budget_id: int


class BudgetItemUpdate(BaseModel):
    """Schema for updating budget items"""

    item_name: Optional[str] = Field(None, min_length=1, max_length=255)
    budgeted_amount: Optional[Decimal] = Field(None, ge=0)
    actual_amount: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class BudgetItemResponse(BudgetItemBase):
    """Schema for budget item responses"""

    id: int
    budget_id: int
    actual_amount: Decimal
    variance: Decimal
    variance_percentage: Decimal
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Financial Report Schemas
class FinancialReportBase(BaseModel):
    """Base schema for financial reports"""

    report_type: str = Field(
        ...,
        regex="^(balance_sheet|income_statement|cash_flow|budget_variance|trial_balance)$",
    )
    report_name: str = Field(..., min_length=1, max_length=255)
    period_start: date
    period_end: date

    @validator("period_end")
    def validate_period(cls, v, values):
        """Ensure period end is after period start"""
        period_start = values.get("period_start")
        if period_start and v < period_start:
            raise ValueError("Period end must be after period start")
        return v


class FinancialReportCreate(FinancialReportBase):
    """Schema for creating financial reports"""

    organization_id: OrganizationId


class FinancialReportResponse(FinancialReportBase):
    """Schema for financial report responses"""

    id: int
    organization_id: OrganizationId
    report_data: Dict[str, Any]
    generated_by: Optional[UserId]
    generated_at: datetime

    class Config:
        from_attributes = True


# Cost Center Schemas
class CostCenterBase(BaseModel):
    """Base schema for cost centers"""

    center_code: str = Field(..., min_length=1, max_length=20)
    center_name: str = Field(..., min_length=1, max_length=255)
    manager_id: Optional[UserId] = None
    budget_limit: Optional[Decimal] = Field(None, ge=0)
    department_id: Optional[DepartmentId] = None
    is_active: bool = True
    description: Optional[str] = None


class CostCenterCreate(CostCenterBase):
    """Schema for creating cost centers"""

    organization_id: OrganizationId


class CostCenterUpdate(BaseModel):
    """Schema for updating cost centers"""

    center_name: Optional[str] = Field(None, min_length=1, max_length=255)
    manager_id: Optional[UserId] = None
    budget_limit: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None
    description: Optional[str] = None


class CostCenterResponse(CostCenterBase):
    """Schema for cost center responses"""

    id: int
    organization_id: OrganizationId
    current_spend: Decimal
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Financial Analytics Schemas
class FinancialKPIResponse(BaseModel):
    """Schema for financial KPI responses"""

    revenue_growth: Decimal
    profit_margin: Decimal
    budget_variance: Decimal
    cost_center_performance: Dict[str, Decimal]
    account_balances: Dict[str, Decimal]
    generated_at: datetime


class FinancialSummaryResponse(BaseModel):
    """Schema for financial summary responses"""

    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal
    total_revenue: Decimal
    total_expenses: Decimal
    net_income: Decimal
    budget_utilization: Decimal
    cost_center_count: int
    active_accounts: int
    period_start: date
    period_end: date


class FinancialAnalyticsRequest(BaseModel):
    """Schema for financial analytics requests"""

    start_date: date
    end_date: date
    account_types: Optional[List[str]] = None
    department_ids: Optional[List[DepartmentId]] = None
    cost_center_ids: Optional[List[int]] = None
    include_budget_variance: bool = True
    include_kpis: bool = True

    @validator("end_date")
    def validate_date_range(cls, v, values):
        """Ensure end date is after start date"""
        start_date = values.get("start_date")
        if start_date and v <= start_date:
            raise ValueError("End date must be after start date")
        return v


# Transaction Schemas for Bulk Operations
class BulkJournalEntryRequest(BaseModel):
    """Schema for bulk journal entry operations"""

    entries: List[JournalEntryCreate] = Field(..., min_items=1, max_items=1000)
    auto_balance: bool = False  # Automatically create balancing entries
    transaction_description: Optional[str] = None


class BulkJournalEntryResponse(BaseModel):
    """Schema for bulk journal entry responses"""

    created_entries: List[JournalEntryResponse]
    failed_entries: List[Dict[str, Any]]
    total_created: int
    total_failed: int
    transaction_ids: List[str]
