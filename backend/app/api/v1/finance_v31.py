"""
Finance API Endpoints - CC02 v31.0 Phase 2

Comprehensive financial management API with 10 core endpoints:
1. Chart of Accounts Management
2. Journal Entry Processing
3. Budget Management
4. Cost Center Operations
5. Financial Period Management
6. Financial Reporting
7. Tax Configuration
8. Trial Balance
9. Budget Variance Analysis
10. Financial Analytics
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import BusinessRuleError, NotFoundError, ValidationError
from app.crud.finance_v31 import (
    AccountCRUD,
    BudgetCRUD,
    CostCenterCRUD,
    FinancialPeriodCRUD,
    FinancialReportCRUD,
    JournalEntryCRUD,
    TaxConfigurationCRUD,
)
from app.schemas.finance_v31 import (
    AccountCreate,
    AccountResponse,
    AccountUpdate,
    ApproveBudgetRequest,
    BalanceSheetResponse,
    BudgetCreate,
    BudgetResponse,
    BudgetVarianceAnalysisResponse,
    ClosePeriodRequest,
    CostCenterCreate,
    CostCenterPerformanceResponse,
    CostCenterResponse,
    FinancialPeriodCreate,
    FinancialPeriodResponse,
    FinancialReportCreate,
    FinancialReportResponse,
    IncomeStatementResponse,
    JournalEntryCreate,
    JournalEntryResponse,
    PostJournalEntryRequest,
    ReverseJournalEntryRequest,
    TaxCalculationRequest,
    TaxCalculationResponse,
    TaxConfigurationCreate,
    TaxConfigurationResponse,
    TrialBalanceResponse,
)

router = APIRouter()


# =============================================================================
# 1. Chart of Accounts Management
# =============================================================================

@router.post("/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> AccountResponse:
    """Create new account in chart of accounts."""
    try:
        account_crud = AccountCRUD(db)

        # Check for duplicate account code
        if account_data.account_code:
            existing = account_crud.get_by_code(account_data.account_code, account_data.organization_id)
            if existing:
                raise ValidationError(f"Account code {account_data.account_code} already exists")

        account = account_crud.create_account(account_data, current_user["sub"])
        return AccountResponse.from_orm(account)

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/accounts/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> AccountResponse:
    """Get account details by ID."""
    try:
        account_crud = AccountCRUD(db)
        account = account_crud.get(account_id)

        if not account:
            raise NotFoundError("Account not found")

        return AccountResponse.from_orm(account)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/accounts", response_model=List[AccountResponse])
def list_accounts(
    organization_id: str = Query(..., description="Organization ID"),
    account_type: Optional[str] = Query(None, description="Account type filter"),
    active_only: bool = Query(True, description="Show only active accounts"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> List[AccountResponse]:
    """List accounts with filtering options."""
    try:
        account_crud = AccountCRUD(db)

        if account_type:
            accounts = account_crud.get_by_type(account_type, organization_id, active_only)
        else:
            accounts = account_crud.get_account_hierarchy(organization_id)
            if active_only:
                accounts = [acc for acc in accounts if acc.is_active]

        # Apply pagination
        accounts = accounts[skip:skip + limit]

        return [AccountResponse.from_orm(account) for account in accounts]

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/accounts/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: str,
    account_data: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> AccountResponse:
    """Update account information."""
    try:
        account_crud = AccountCRUD(db)
        account = account_crud.update(account_id, account_data)

        if not account:
            raise NotFoundError("Account not found")

        account.updated_by = current_user["sub"]
        db.commit()

        return AccountResponse.from_orm(account)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# =============================================================================
# 2. Journal Entry Processing
# =============================================================================

@router.post("/journal-entries", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED)
def create_journal_entry(
    entry_data: JournalEntryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> JournalEntryResponse:
    """Create new journal entry with validation."""
    try:
        journal_crud = JournalEntryCRUD(db)
        entry = journal_crud.create_journal_entry(entry_data, current_user["sub"])

        return JournalEntryResponse.from_orm(entry)

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/journal-entries/{entry_id}", response_model=JournalEntryResponse)
def get_journal_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> JournalEntryResponse:
    """Get journal entry details."""
    try:
        journal_crud = JournalEntryCRUD(db)
        entry = journal_crud.get(entry_id)

        if not entry:
            raise NotFoundError("Journal entry not found")

        return JournalEntryResponse.from_orm(entry)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/journal-entries/post", response_model=JournalEntryResponse)
def post_journal_entry(
    post_request: PostJournalEntryRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> JournalEntryResponse:
    """Post journal entry and update account balances."""
    try:
        journal_crud = JournalEntryCRUD(db)
        entry = journal_crud.post_journal_entry(post_request.journal_entry_id, current_user["sub"])

        return JournalEntryResponse.from_orm(entry)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/journal-entries/reverse", response_model=JournalEntryResponse)
def reverse_journal_entry(
    reverse_request: ReverseJournalEntryRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> JournalEntryResponse:
    """Create reversing journal entry."""
    try:
        journal_crud = JournalEntryCRUD(db)
        reversal_entry = journal_crud.reverse_journal_entry(
            reverse_request.journal_entry_id,
            reverse_request.reason,
            current_user["sub"]
        )

        return JournalEntryResponse.from_orm(reversal_entry)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# =============================================================================
# 3. Budget Management
# =============================================================================

@router.post("/budgets", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget_data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> BudgetResponse:
    """Create new budget with budget lines."""
    try:
        budget_crud = BudgetCRUD(db)

        # For this example, we'll create a budget without lines initially
        # In production, you might want to accept budget lines in the request
        budget = budget_crud.create(budget_data)
        budget.created_by = current_user["sub"]
        db.commit()
        db.refresh(budget)

        return BudgetResponse.from_orm(budget)

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/budgets/{budget_id}", response_model=BudgetResponse)
def get_budget(
    budget_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> BudgetResponse:
    """Get budget details with budget lines."""
    try:
        budget_crud = BudgetCRUD(db)
        budget = budget_crud.get(budget_id)

        if not budget:
            raise NotFoundError("Budget not found")

        return BudgetResponse.from_orm(budget)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/budgets/approve", response_model=BudgetResponse)
def approve_budget(
    approve_request: ApproveBudgetRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> BudgetResponse:
    """Approve and activate budget."""
    try:
        budget_crud = BudgetCRUD(db)
        budget = budget_crud.approve_budget(
            approve_request.budget_id,
            current_user["sub"],
            approve_request.approval_notes or ""
        )

        return BudgetResponse.from_orm(budget)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# =============================================================================
# 4. Cost Center Operations
# =============================================================================

@router.post("/cost-centers", response_model=CostCenterResponse, status_code=status.HTTP_201_CREATED)
def create_cost_center(
    cost_center_data: CostCenterCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> CostCenterResponse:
    """Create new cost center."""
    try:
        cost_center_crud = CostCenterCRUD(db)
        cost_center = cost_center_crud.create_cost_center(cost_center_data, current_user["sub"])

        return CostCenterResponse.from_orm(cost_center)

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/cost-centers/{cost_center_id}/performance", response_model=CostCenterPerformanceResponse)
def get_cost_center_performance(
    cost_center_id: str,
    start_date: datetime = Query(..., description="Performance analysis start date"),
    end_date: datetime = Query(..., description="Performance analysis end date"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> CostCenterPerformanceResponse:
    """Get cost center performance metrics."""
    try:
        cost_center_crud = CostCenterCRUD(db)
        performance = cost_center_crud.get_cost_center_performance(
            cost_center_id, start_date, end_date
        )

        return CostCenterPerformanceResponse(**performance)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# =============================================================================
# 5. Financial Period Management
# =============================================================================

@router.post("/periods", response_model=FinancialPeriodResponse, status_code=status.HTTP_201_CREATED)
def create_financial_period(
    period_data: FinancialPeriodCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> FinancialPeriodResponse:
    """Create new financial period."""
    try:
        period_crud = FinancialPeriodCRUD(db)
        period = period_crud.create(period_data)
        period.created_by = current_user["sub"]
        db.commit()
        db.refresh(period)

        return FinancialPeriodResponse.from_orm(period)

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/periods/close", response_model=FinancialPeriodResponse)
def close_financial_period(
    close_request: ClosePeriodRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> FinancialPeriodResponse:
    """Close financial period and prevent further transactions."""
    try:
        period_crud = FinancialPeriodCRUD(db)
        period = period_crud.close_period(close_request.period_id, current_user["sub"])

        return FinancialPeriodResponse.from_orm(period)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# =============================================================================
# 6. Financial Reporting
# =============================================================================

@router.post("/reports", response_model=FinancialReportResponse, status_code=status.HTTP_201_CREATED)
def create_financial_report(
    report_data: FinancialReportCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> FinancialReportResponse:
    """Create new financial report template."""
    try:
        report_crud = FinancialReportCRUD(db)
        report = report_crud.create(report_data)
        report.created_by = current_user["sub"]
        db.commit()
        db.refresh(report)

        return FinancialReportResponse.from_orm(report)

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/reports/balance-sheet", response_model=BalanceSheetResponse)
def generate_balance_sheet(
    organization_id: str = Query(..., description="Organization ID"),
    as_of_date: datetime = Query(..., description="Balance sheet as of date"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> BalanceSheetResponse:
    """Generate balance sheet report."""
    try:
        report_crud = FinancialReportCRUD(db)
        balance_sheet = report_crud.generate_balance_sheet(organization_id, as_of_date)

        return BalanceSheetResponse(**balance_sheet)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/reports/income-statement", response_model=IncomeStatementResponse)
def generate_income_statement(
    organization_id: str = Query(..., description="Organization ID"),
    start_date: datetime = Query(..., description="Income statement start date"),
    end_date: datetime = Query(..., description="Income statement end date"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> IncomeStatementResponse:
    """Generate income statement report."""
    try:
        report_crud = FinancialReportCRUD(db)
        income_statement = report_crud.generate_income_statement(organization_id, start_date, end_date)

        return IncomeStatementResponse(**income_statement)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# =============================================================================
# 7. Tax Configuration
# =============================================================================

@router.post("/tax-configurations", response_model=TaxConfigurationResponse, status_code=status.HTTP_201_CREATED)
def create_tax_configuration(
    tax_data: TaxConfigurationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> TaxConfigurationResponse:
    """Create new tax configuration."""
    try:
        tax_crud = TaxConfigurationCRUD(db)
        tax_config = tax_crud.create(tax_data)
        tax_config.created_by = current_user["sub"]
        db.commit()
        db.refresh(tax_config)

        return TaxConfigurationResponse.from_orm(tax_config)

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/tax-configurations/calculate", response_model=TaxCalculationResponse)
def calculate_tax(
    calculation_request: TaxCalculationRequest,
    organization_id: str = Query(..., description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> TaxCalculationResponse:
    """Calculate tax amount based on configuration."""
    try:
        tax_crud = TaxConfigurationCRUD(db)
        calculation = tax_crud.calculate_tax(
            organization_id,
            calculation_request.tax_code,
            calculation_request.base_amount,
            calculation_request.effective_date
        )

        return TaxCalculationResponse(**calculation)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# =============================================================================
# 8. Trial Balance
# =============================================================================

@router.get("/trial-balance", response_model=TrialBalanceResponse)
def get_trial_balance(
    organization_id: str = Query(..., description="Organization ID"),
    as_of_date: datetime = Query(..., description="Trial balance as of date"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> TrialBalanceResponse:
    """Generate trial balance report."""
    try:
        journal_crud = JournalEntryCRUD(db)
        trial_balance_data = journal_crud.get_trial_balance(organization_id, as_of_date)

        total_debits = sum(line["debit_balance"] for line in trial_balance_data)
        total_credits = sum(line["credit_balance"] for line in trial_balance_data)

        return TrialBalanceResponse(
            organization_id=organization_id,
            as_of_date=as_of_date,
            accounts=trial_balance_data,
            total_debits=total_debits,
            total_credits=total_credits,
            is_balanced=abs(total_debits - total_credits) < 0.01
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# =============================================================================
# 9. Budget Variance Analysis
# =============================================================================

@router.get("/budgets/{budget_id}/variance-analysis", response_model=BudgetVarianceAnalysisResponse)
def get_budget_variance_analysis(
    budget_id: str,
    as_of_date: Optional[datetime] = Query(None, description="Analysis as of date"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> BudgetVarianceAnalysisResponse:
    """Generate budget variance analysis report."""
    try:
        budget_crud = BudgetCRUD(db)
        analysis = budget_crud.get_budget_variance_analysis(budget_id, as_of_date)

        return BudgetVarianceAnalysisResponse(**analysis)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# =============================================================================
# 10. Financial Analytics Dashboard
# =============================================================================

@router.get("/analytics/dashboard")
def get_financial_dashboard(
    organization_id: str = Query(..., description="Organization ID"),
    period_start: datetime = Query(..., description="Analysis period start"),
    period_end: datetime = Query(..., description="Analysis period end"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comprehensive financial analytics dashboard."""
    try:
        # Initialize CRUD objects
        journal_crud = JournalEntryCRUD(db)
        report_crud = FinancialReportCRUD(db)
        BudgetCRUD(db)

        # Generate key financial metrics
        dashboard_data = {
            "organization_id": organization_id,
            "period_start": period_start,
            "period_end": period_end,
            "generated_at": datetime.utcnow(),
        }

        # Balance sheet as of period end
        try:
            balance_sheet = report_crud.generate_balance_sheet(organization_id, period_end)
            dashboard_data["balance_sheet_summary"] = {
                "total_assets": balance_sheet["assets"]["total"],
                "total_liabilities": balance_sheet["liabilities"]["total"],
                "total_equity": balance_sheet["equity"]["total"],
                "is_balanced": balance_sheet["balanced"],
            }
        except Exception:
            dashboard_data["balance_sheet_summary"] = None

        # Income statement for period
        try:
            income_statement = report_crud.generate_income_statement(
                organization_id, period_start, period_end
            )
            dashboard_data["income_statement_summary"] = {
                "total_revenue": income_statement["revenue"]["total"],
                "total_expenses": income_statement["expenses"]["total"],
                "net_income": income_statement["net_income"],
                "margin_percentage": income_statement["margin_percentage"],
            }
        except Exception:
            dashboard_data["income_statement_summary"] = None

        # Trial balance as of period end
        try:
            trial_balance = journal_crud.get_trial_balance(organization_id, period_end)
            dashboard_data["trial_balance_summary"] = {
                "total_accounts": len(trial_balance),
                "total_debits": sum(line["debit_balance"] for line in trial_balance),
                "total_credits": sum(line["credit_balance"] for line in trial_balance),
                "is_balanced": abs(
                    sum(line["debit_balance"] for line in trial_balance) -
                    sum(line["credit_balance"] for line in trial_balance)
                ) < 0.01,
            }
        except Exception:
            dashboard_data["trial_balance_summary"] = None

        # Key performance indicators
        dashboard_data["key_metrics"] = {
            "current_ratio": None,  # Would calculate from balance sheet
            "debt_to_equity": None,  # Would calculate from balance sheet
            "gross_margin": None,  # Would calculate from income statement
            "operating_margin": None,  # Would calculate from income statement
            "return_on_assets": None,  # Would calculate from both statements
            "return_on_equity": None,  # Would calculate from both statements
        }

        # Recent activity summary
        dashboard_data["recent_activity"] = {
            "journal_entries_count": None,  # Would query recent entries
            "pending_entries_count": None,  # Would query unposted entries
            "budget_alerts_count": None,  # Would query budget variances
            "period_status": None,  # Would check current period status
        }

        return dashboard_data

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
