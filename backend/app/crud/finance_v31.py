"""
Finance CRUD Operations - CC02 v31.0 Phase 2

Comprehensive CRUD operations for financial management including:
- Chart of Accounts management
- Journal Entry processing
- Budget management and control
- Cost Center operations
- Financial reporting
- Tax configuration
- Audit logging
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.finance_extended import (
    Account,
    AccountType,
    Budget,
    BudgetLine,
    BudgetStatus,
    CostCenter,
    FinanceAuditLog,
    FinancialPeriod,
    FinancialPeriodStatus,
    FinancialReport,
    JournalEntry,
    JournalEntryLine,
    TaxConfiguration,
    TransactionType,
)
from app.schemas.finance_v31 import (
    AccountCreate,
    AccountUpdate,
    BudgetCreate,
    BudgetLineCreate,
    BudgetUpdate,
    CostCenterCreate,
    CostCenterUpdate,
    FinancialPeriodCreate,
    FinancialPeriodUpdate,
    FinancialReportCreate,
    FinancialReportUpdate,
    JournalEntryCreate,
    JournalEntryUpdate,
    TaxConfigurationCreate,
    TaxConfigurationUpdate,
)


class AccountCRUD(CRUDBase[Account, AccountCreate, AccountUpdate]):
    """CRUD operations for Chart of Accounts."""

    def __init__(self, db: Session):
        super().__init__(Account)
        self.db = db

    def create_account(self, obj_in: AccountCreate, created_by: str) -> Account:
        """Create a new account with validation."""
        # Generate account code if not provided
        if not obj_in.account_code:
            obj_in.account_code = self._generate_account_code(
                obj_in.account_type, obj_in.organization_id
            )

        # Set account level and path for hierarchy
        account_level = 0
        account_path = obj_in.account_code

        if obj_in.parent_account_id:
            parent = self.get(obj_in.parent_account_id)
            if parent:
                account_level = parent.account_level + 1
                account_path = f"{parent.account_path}/{obj_in.account_code}"

        db_obj = Account(
            **obj_in.dict(),
            account_level=account_level,
            account_path=account_path,
            created_by=created_by,
        )

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)

        # Log audit trail
        self._log_audit_event(
            "create", "finance_accounts", db_obj.id, None, db_obj, created_by
        )

        return db_obj

    def get_by_code(self, account_code: str, organization_id: str) -> Optional[Account]:
        """Get account by code within organization."""
        return (
            self.db.query(Account)
            .filter(
                and_(
                    Account.account_code == account_code,
                    Account.organization_id == organization_id,
                )
            )
            .first()
        )

    def get_by_type(
        self, account_type: AccountType, organization_id: str, active_only: bool = True
    ) -> List[Account]:
        """Get accounts by type."""
        query = self.db.query(Account).filter(
            and_(
                Account.account_type == account_type,
                Account.organization_id == organization_id,
            )
        )

        if active_only:
            query = query.filter(Account.is_active)

        return query.order_by(Account.account_code).all()

    def get_account_hierarchy(self, organization_id: str) -> List[Account]:
        """Get complete account hierarchy."""
        return (
            self.db.query(Account)
            .filter(Account.organization_id == organization_id)
            .order_by(Account.account_path)
            .all()
        )

    def update_balance(
        self, account_id: str, amount: Decimal, transaction_type: TransactionType
    ):
        """Update account balance based on transaction."""
        account = self.get(account_id)
        if not account:
            return None

        # Apply balance based on normal balance and transaction type
        if account.normal_balance == TransactionType.DEBIT:
            if transaction_type == TransactionType.DEBIT:
                account.current_balance += amount
            else:
                account.current_balance -= amount
        else:  # Credit normal balance
            if transaction_type == TransactionType.CREDIT:
                account.current_balance += amount
            else:
                account.current_balance -= amount

        self.db.commit()
        return account

    def _generate_account_code(
        self, account_type: AccountType, organization_id: str
    ) -> str:
        """Generate next account code for account type."""
        prefixes = {
            AccountType.ASSET: "1",
            AccountType.LIABILITY: "2",
            AccountType.EQUITY: "3",
            AccountType.REVENUE: "4",
            AccountType.EXPENSE: "5",
        }

        prefix = prefixes[account_type]

        # Get highest existing code for this type
        highest = (
            self.db.query(Account.account_code)
            .filter(
                and_(
                    Account.organization_id == organization_id,
                    Account.account_code.like(f"{prefix}%"),
                )
            )
            .order_by(desc(Account.account_code))
            .first()
        )

        if highest:
            try:
                next_num = int(highest[0][1:]) + 1
                return f"{prefix}{next_num:04d}"
            except ValueError:
                pass

        return f"{prefix}0001"

    def _log_audit_event(
        self,
        event_type: str,
        table_name: str,
        record_id: str,
        old_values: Any,
        new_values: Any,
        user_id: str,
    ):
        """Log audit event for compliance."""
        audit_log = FinanceAuditLog(
            event_type=event_type,
            table_name=table_name,
            record_id=record_id,
            old_values=old_values.__dict__ if old_values else None,
            new_values=new_values.__dict__
            if hasattr(new_values, "__dict__")
            else new_values,
            user_id=user_id,
            organization_id=new_values.organization_id
            if hasattr(new_values, "organization_id")
            else None,
        )
        self.db.add(audit_log)


class JournalEntryCRUD(CRUDBase[JournalEntry, JournalEntryCreate, JournalEntryUpdate]):
    """CRUD operations for Journal Entries."""

    def __init__(self, db: Session):
        super().__init__(JournalEntry)
        self.db = db

    def create_journal_entry(
        self, obj_in: JournalEntryCreate, created_by: str
    ) -> JournalEntry:
        """Create journal entry with lines and validation."""
        # Generate entry number
        entry_number = self._generate_entry_number(obj_in.organization_id)

        # Validate debits equal credits
        total_debits = sum(line.debit_amount or 0 for line in obj_in.lines)
        total_credits = sum(line.credit_amount or 0 for line in obj_in.lines)

        if total_debits != total_credits:
            raise ValueError("Debits must equal credits")

        # Create journal entry header
        journal_data = obj_in.dict(exclude={"lines"})
        journal_data["entry_number"] = entry_number
        journal_data["total_debit"] = total_debits
        journal_data["total_credit"] = total_credits
        journal_data["created_by"] = created_by

        db_obj = JournalEntry(**journal_data)
        self.db.add(db_obj)
        self.db.flush()  # Get ID for lines

        # Create journal entry lines
        for i, line_data in enumerate(obj_in.lines, 1):
            line = JournalEntryLine(
                journal_entry_id=db_obj.id, line_number=i, **line_data.dict()
            )
            self.db.add(line)

        self.db.commit()
        self.db.refresh(db_obj)

        return db_obj

    def post_journal_entry(self, journal_entry_id: str, posted_by: str) -> JournalEntry:
        """Post journal entry and update account balances."""
        entry = self.get(journal_entry_id)
        if not entry or entry.is_posted:
            raise ValueError("Entry not found or already posted")

        # Update account balances
        account_crud = AccountCRUD(self.db)
        for line in entry.lines:
            if line.debit_amount > 0:
                account_crud.update_balance(
                    line.account_id, line.debit_amount, TransactionType.DEBIT
                )
            if line.credit_amount > 0:
                account_crud.update_balance(
                    line.account_id, line.credit_amount, TransactionType.CREDIT
                )

        # Mark as posted
        entry.is_posted = True
        entry.posting_date = datetime.utcnow()
        entry.updated_by = posted_by

        self.db.commit()
        return entry

    def reverse_journal_entry(
        self, journal_entry_id: str, reason: str, reversed_by: str
    ) -> JournalEntry:
        """Create reversing journal entry."""
        original_entry = self.get(journal_entry_id)
        if not original_entry or not original_entry.is_posted:
            raise ValueError("Original entry not found or not posted")

        # Create reversing entry
        reversal_data = {
            "organization_id": original_entry.organization_id,
            "transaction_date": datetime.utcnow(),
            "period_id": original_entry.period_id,
            "description": f"REVERSAL: {original_entry.description}",
            "memo": f"Reversal of entry {original_entry.entry_number}. Reason: {reason}",
            "total_debit": original_entry.total_debit,
            "total_credit": original_entry.total_credit,
            "currency_code": original_entry.currency_code,
            "exchange_rate": original_entry.exchange_rate,
            "source_module": "finance_reversal",
            "created_by": reversed_by,
        }

        reversal_entry = JournalEntry(**reversal_data)
        reversal_entry.entry_number = self._generate_entry_number(
            original_entry.organization_id
        )

        self.db.add(reversal_entry)
        self.db.flush()

        # Create reversing lines (swap debit/credit)
        for line in original_entry.lines:
            reversal_line = JournalEntryLine(
                journal_entry_id=reversal_entry.id,
                account_id=line.account_id,
                line_number=line.line_number,
                description=f"REVERSAL: {line.description}",
                debit_amount=line.credit_amount,  # Swap
                credit_amount=line.debit_amount,  # Swap
                department_id=line.department_id,
                cost_center_id=line.cost_center_id,
                project_id=line.project_id,
            )
            self.db.add(reversal_line)

        # Link entries and mark original as reversed
        original_entry.is_reversed = True
        original_entry.reversal_entry_id = reversal_entry.id

        self.db.commit()
        self.db.refresh(reversal_entry)

        # Auto-post the reversal
        self.post_journal_entry(reversal_entry.id, reversed_by)

        return reversal_entry

    def get_entries_by_account(
        self,
        account_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[JournalEntryLine]:
        """Get journal entry lines for specific account."""
        query = (
            self.db.query(JournalEntryLine)
            .join(JournalEntry)
            .filter(JournalEntryLine.account_id == account_id)
        )

        if start_date:
            query = query.filter(JournalEntry.transaction_date >= start_date)
        if end_date:
            query = query.filter(JournalEntry.transaction_date <= end_date)

        return query.order_by(JournalEntry.transaction_date).all()

    def get_trial_balance(
        self, organization_id: str, as_of_date: datetime
    ) -> List[Dict[str, Any]]:
        """Generate trial balance report."""
        # Get all accounts with balances
        query = (
            self.db.query(
                Account.id,
                Account.account_code,
                Account.account_name,
                Account.account_type,
                Account.current_balance,
                func.sum(JournalEntryLine.debit_amount).label("total_debits"),
                func.sum(JournalEntryLine.credit_amount).label("total_credits"),
            )
            .outerjoin(JournalEntryLine)
            .outerjoin(JournalEntry)
            .filter(Account.organization_id == organization_id)
            .filter(Account.is_active)
            .filter(
                or_(
                    JournalEntry.transaction_date.is_(None),
                    JournalEntry.transaction_date <= as_of_date,
                )
            )
            .filter(
                or_(
                    JournalEntry.is_posted.is_(None),
                    JournalEntry.is_posted,
                )
            )
            .group_by(Account.id)
            .order_by(Account.account_code)
        )

        results = []
        for row in query.all():
            # Calculate ending balance
            debits = row.total_debits or 0
            credits = row.total_credits or 0

            # Determine balance based on account normal balance
            if row.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
                balance = debits - credits
            else:
                balance = credits - debits

            results.append(
                {
                    "account_id": row.id,
                    "account_code": row.account_code,
                    "account_name": row.account_name,
                    "account_type": row.account_type.value,
                    "debit_balance": balance
                    if balance > 0
                    and row.account_type in [AccountType.ASSET, AccountType.EXPENSE]
                    else 0,
                    "credit_balance": balance
                    if balance > 0
                    and row.account_type not in [AccountType.ASSET, AccountType.EXPENSE]
                    else 0,
                    "total_debits": float(debits),
                    "total_credits": float(credits),
                }
            )

        return results

    def _generate_entry_number(self, organization_id: str) -> str:
        """Generate next journal entry number."""
        # Get current year and month
        now = datetime.utcnow()
        prefix = f"JE{now.year:04d}{now.month:02d}"

        # Get highest entry number for this period
        highest = (
            self.db.query(JournalEntry.entry_number)
            .filter(
                and_(
                    JournalEntry.organization_id == organization_id,
                    JournalEntry.entry_number.like(f"{prefix}%"),
                )
            )
            .order_by(desc(JournalEntry.entry_number))
            .first()
        )

        if highest:
            try:
                next_num = int(highest[0][-4:]) + 1
                return f"{prefix}{next_num:04d}"
            except ValueError:
                pass

        return f"{prefix}0001"


class BudgetCRUD(CRUDBase[Budget, BudgetCreate, BudgetUpdate]):
    """CRUD operations for Budget management."""

    def __init__(self, db: Session):
        super().__init__(Budget)
        self.db = db

    def create_budget_with_lines(
        self,
        obj_in: BudgetCreate,
        budget_lines: List[BudgetLineCreate],
        created_by: str,
    ) -> Budget:
        """Create budget with budget lines."""
        # Calculate totals from lines
        total_revenue = sum(
            line.annual_budget
            for line in budget_lines
            if self._is_revenue_account(line.account_id)
        )
        total_expense = sum(
            line.annual_budget
            for line in budget_lines
            if not self._is_revenue_account(line.account_id)
        )

        # Create budget header
        budget_data = obj_in.dict(exclude={"budget_lines"})
        budget_data.update(
            {
                "total_revenue_budget": total_revenue,
                "total_expense_budget": total_expense,
                "net_budget": total_revenue - total_expense,
                "created_by": created_by,
            }
        )

        db_obj = Budget(**budget_data)
        self.db.add(db_obj)
        self.db.flush()

        # Create budget lines
        for i, line_data in enumerate(budget_lines, 1):
            budget_line = BudgetLine(
                budget_id=db_obj.id, line_number=i, **line_data.dict()
            )
            self.db.add(budget_line)

        self.db.commit()
        self.db.refresh(db_obj)

        return db_obj

    def approve_budget(
        self, budget_id: str, approved_by: str, notes: str = ""
    ) -> Budget:
        """Approve budget and activate it."""
        budget = self.get(budget_id)
        if not budget or budget.status != BudgetStatus.DRAFT:
            raise ValueError("Budget not found or not in draft status")

        budget.status = BudgetStatus.ACTIVE
        budget.approved_date = datetime.utcnow()
        budget.approved_by = approved_by
        budget.approval_notes = notes

        self.db.commit()
        return budget

    def get_budget_variance_analysis(
        self, budget_id: str, as_of_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate budget vs actual variance analysis."""
        budget = self.get(budget_id)
        if not budget:
            raise ValueError("Budget not found")

        # Calculate actuals by account
        end_date = as_of_date or datetime.utcnow()

        actuals_query = (
            self.db.query(
                JournalEntryLine.account_id,
                func.sum(
                    JournalEntryLine.debit_amount - JournalEntryLine.credit_amount
                ).label("actual_amount"),
            )
            .join(JournalEntry)
            .filter(
                and_(
                    JournalEntry.organization_id == budget.organization_id,
                    JournalEntry.transaction_date >= budget.budget_start_date,
                    JournalEntry.transaction_date <= end_date,
                    JournalEntry.is_posted,
                )
            )
            .group_by(JournalEntryLine.account_id)
        )

        actuals = {row.account_id: row.actual_amount for row in actuals_query.all()}

        # Calculate variances for each budget line
        variances = []
        for line in budget.budget_lines:
            actual_amount = actuals.get(line.account_id, 0)
            variance_amount = actual_amount - line.annual_budget
            variance_percentage = (
                (variance_amount / line.annual_budget * 100)
                if line.annual_budget
                else 0
            )

            variances.append(
                {
                    "account_id": line.account_id,
                    "account_code": line.account.account_code if line.account else "",
                    "account_name": line.account.account_name if line.account else "",
                    "budget_amount": float(line.annual_budget),
                    "actual_amount": float(actual_amount),
                    "variance_amount": float(variance_amount),
                    "variance_percentage": float(variance_percentage),
                    "status": self._get_variance_status(variance_percentage),
                }
            )

        return {
            "budget_id": budget_id,
            "budget_name": budget.budget_name,
            "analysis_date": end_date,
            "total_budget": float(budget.net_budget),
            "total_actual": float(sum(actuals.values())),
            "total_variance": float(sum(actuals.values()) - budget.net_budget),
            "line_variances": variances,
        }

    def _is_revenue_account(self, account_id: str) -> bool:
        """Check if account is revenue account."""
        account = self.db.query(Account).filter(Account.id == account_id).first()
        return account and account.account_type == AccountType.REVENUE

    def _get_variance_status(self, variance_percentage: float) -> str:
        """Determine variance status based on percentage."""
        abs_variance = abs(variance_percentage)
        if abs_variance <= 5:
            return "on_track"
        elif abs_variance <= 10:
            return "watch"
        elif abs_variance <= 20:
            return "concern"
        else:
            return "critical"


class CostCenterCRUD(CRUDBase[CostCenter, CostCenterCreate, CostCenterUpdate]):
    """CRUD operations for Cost Center management."""

    def __init__(self, db: Session):
        super().__init__(CostCenter)
        self.db = db

    def create_cost_center(
        self, obj_in: CostCenterCreate, created_by: str
    ) -> CostCenter:
        """Create cost center with hierarchy management."""
        # Generate code if not provided
        if not obj_in.cost_center_code:
            obj_in.cost_center_code = self._generate_cost_center_code(
                obj_in.organization_id
            )

        # Set level based on parent
        cost_center_level = 0
        if obj_in.parent_cost_center_id:
            parent = self.get(obj_in.parent_cost_center_id)
            if parent:
                cost_center_level = parent.cost_center_level + 1

        db_obj = CostCenter(
            **obj_in.dict(),
            cost_center_level=cost_center_level,
            created_by=created_by,
        )

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)

        return db_obj

    def get_cost_center_performance(
        self, cost_center_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get cost center performance metrics."""
        cost_center = self.get(cost_center_id)
        if not cost_center:
            raise ValueError("Cost center not found")

        # Get actual costs for the period
        actual_costs = (
            self.db.query(
                func.sum(JournalEntryLine.debit_amount - JournalEntryLine.credit_amount)
            )
            .join(JournalEntry)
            .filter(
                and_(
                    JournalEntryLine.cost_center_id == cost_center_id,
                    JournalEntry.transaction_date >= start_date,
                    JournalEntry.transaction_date <= end_date,
                    JournalEntry.is_posted,
                )
            )
            .scalar()
            or 0
        )

        # Calculate variance
        budget_variance = actual_costs - cost_center.budget_amount
        budget_variance_pct = (
            (budget_variance / cost_center.budget_amount * 100)
            if cost_center.budget_amount
            else 0
        )

        return {
            "cost_center_id": cost_center_id,
            "cost_center_code": cost_center.cost_center_code,
            "cost_center_name": cost_center.cost_center_name,
            "period_start": start_date,
            "period_end": end_date,
            "budget_amount": float(cost_center.budget_amount),
            "actual_amount": float(actual_costs),
            "committed_amount": float(cost_center.committed_amount),
            "available_amount": float(
                cost_center.budget_amount - actual_costs - cost_center.committed_amount
            ),
            "budget_variance": float(budget_variance),
            "budget_variance_percentage": float(budget_variance_pct),
            "utilization_percentage": float(
                (actual_costs / cost_center.budget_amount * 100)
                if cost_center.budget_amount
                else 0
            ),
        }

    def _generate_cost_center_code(self, organization_id: str) -> str:
        """Generate next cost center code."""
        highest = (
            self.db.query(CostCenter.cost_center_code)
            .filter(CostCenter.organization_id == organization_id)
            .order_by(desc(CostCenter.cost_center_code))
            .first()
        )

        if highest and highest[0].startswith("CC"):
            try:
                next_num = int(highest[0][2:]) + 1
                return f"CC{next_num:04d}"
            except ValueError:
                pass

        return "CC0001"


class FinancialPeriodCRUD(
    CRUDBase[FinancialPeriod, FinancialPeriodCreate, FinancialPeriodUpdate]
):
    """CRUD operations for Financial Period management."""

    def __init__(self, db: Session):
        super().__init__(FinancialPeriod)
        self.db = db

    def close_period(self, period_id: str, closed_by: str) -> FinancialPeriod:
        """Close financial period and prevent further transactions."""
        period = self.get(period_id)
        if not period or period.status == FinancialPeriodStatus.CLOSED:
            raise ValueError("Period not found or already closed")

        # Verify all journal entries are posted
        unposted_entries = (
            self.db.query(JournalEntry)
            .filter(
                and_(
                    JournalEntry.period_id == period_id,
                    not JournalEntry.is_posted,
                )
            )
            .count()
        )

        if unposted_entries > 0:
            raise ValueError(
                f"Cannot close period with {unposted_entries} unposted entries"
            )

        period.status = FinancialPeriodStatus.CLOSED
        period.closed_date = datetime.utcnow()
        period.closed_by = closed_by
        period.allow_transactions = False

        self.db.commit()
        return period


class FinancialReportCRUD(
    CRUDBase[FinancialReport, FinancialReportCreate, FinancialReportUpdate]
):
    """CRUD operations for Financial Report management."""

    def __init__(self, db: Session):
        super().__init__(FinancialReport)
        self.db = db

    def generate_balance_sheet(
        self, organization_id: str, as_of_date: datetime
    ) -> Dict[str, Any]:
        """Generate balance sheet report."""
        # Get assets
        assets = self._get_account_balances(
            organization_id, AccountType.ASSET, as_of_date
        )

        # Get liabilities
        liabilities = self._get_account_balances(
            organization_id, AccountType.LIABILITY, as_of_date
        )

        # Get equity
        equity = self._get_account_balances(
            organization_id, AccountType.EQUITY, as_of_date
        )

        total_assets = sum(account["balance"] for account in assets)
        total_liabilities = sum(account["balance"] for account in liabilities)
        total_equity = sum(account["balance"] for account in equity)

        return {
            "report_type": "balance_sheet",
            "organization_id": organization_id,
            "as_of_date": as_of_date,
            "assets": {
                "accounts": assets,
                "total": total_assets,
            },
            "liabilities": {
                "accounts": liabilities,
                "total": total_liabilities,
            },
            "equity": {
                "accounts": equity,
                "total": total_equity,
            },
            "total_liabilities_equity": total_liabilities + total_equity,
            "balanced": abs(total_assets - (total_liabilities + total_equity)) < 0.01,
        }

    def generate_income_statement(
        self, organization_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Generate income statement report."""
        # Get revenue
        revenue = self._get_account_balances(
            organization_id, AccountType.REVENUE, end_date, start_date
        )

        # Get expenses
        expenses = self._get_account_balances(
            organization_id, AccountType.EXPENSE, end_date, start_date
        )

        total_revenue = sum(account["balance"] for account in revenue)
        total_expenses = sum(account["balance"] for account in expenses)
        net_income = total_revenue - total_expenses

        return {
            "report_type": "income_statement",
            "organization_id": organization_id,
            "start_date": start_date,
            "end_date": end_date,
            "revenue": {
                "accounts": revenue,
                "total": total_revenue,
            },
            "expenses": {
                "accounts": expenses,
                "total": total_expenses,
            },
            "net_income": net_income,
            "gross_margin": total_revenue - total_expenses if total_revenue > 0 else 0,
            "margin_percentage": ((net_income / total_revenue) * 100)
            if total_revenue > 0
            else 0,
        }

    def _get_account_balances(
        self,
        organization_id: str,
        account_type: AccountType,
        as_of_date: datetime,
        from_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get account balances for specific account type."""
        query = (
            self.db.query(
                Account.id,
                Account.account_code,
                Account.account_name,
                func.sum(JournalEntryLine.debit_amount).label("total_debits"),
                func.sum(JournalEntryLine.credit_amount).label("total_credits"),
            )
            .outerjoin(JournalEntryLine)
            .outerjoin(JournalEntry)
            .filter(
                and_(
                    Account.organization_id == organization_id,
                    Account.account_type == account_type,
                    Account.is_active,
                )
            )
            .filter(
                or_(
                    JournalEntry.transaction_date.is_(None),
                    JournalEntry.transaction_date <= as_of_date,
                )
            )
        )

        if from_date:
            query = query.filter(
                or_(
                    JournalEntry.transaction_date.is_(None),
                    JournalEntry.transaction_date >= from_date,
                )
            )

        query = (
            query.filter(
                or_(
                    JournalEntry.is_posted.is_(None),
                    JournalEntry.is_posted,
                )
            )
            .group_by(Account.id)
            .order_by(Account.account_code)
        )

        results = []
        for row in query.all():
            debits = row.total_debits or 0
            credits = row.total_credits or 0

            # Calculate balance based on account type
            if account_type in [AccountType.ASSET, AccountType.EXPENSE]:
                balance = debits - credits
            else:
                balance = credits - debits

            results.append(
                {
                    "account_id": row.id,
                    "account_code": row.account_code,
                    "account_name": row.account_name,
                    "balance": float(balance),
                    "debit_total": float(debits),
                    "credit_total": float(credits),
                }
            )

        return results


class TaxConfigurationCRUD(
    CRUDBase[TaxConfiguration, TaxConfigurationCreate, TaxConfigurationUpdate]
):
    """CRUD operations for Tax Configuration."""

    def __init__(self, db: Session):
        super().__init__(TaxConfiguration)
        self.db = db

    def get_active_tax_rates(
        self, organization_id: str, effective_date: Optional[datetime] = None
    ) -> List[TaxConfiguration]:
        """Get active tax rates for given date."""
        query_date = effective_date or datetime.utcnow()

        return (
            self.db.query(TaxConfiguration)
            .filter(
                and_(
                    TaxConfiguration.organization_id == organization_id,
                    TaxConfiguration.is_active,
                    TaxConfiguration.effective_date <= query_date,
                    or_(
                        TaxConfiguration.expiration_date.is_(None),
                        TaxConfiguration.expiration_date > query_date,
                    ),
                )
            )
            .order_by(TaxConfiguration.tax_code)
            .all()
        )

    def calculate_tax(
        self,
        organization_id: str,
        tax_code: str,
        base_amount: Decimal,
        effective_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Calculate tax amount based on configuration."""
        tax_config = (
            self.db.query(TaxConfiguration)
            .filter(
                and_(
                    TaxConfiguration.organization_id == organization_id,
                    TaxConfiguration.tax_code == tax_code,
                    TaxConfiguration.is_active,
                )
            )
            .first()
        )

        if not tax_config:
            raise ValueError(f"Tax configuration not found for code: {tax_code}")

        # Calculate tax amount
        tax_amount = base_amount * (tax_config.tax_rate / 100)

        # Apply minimum/maximum limits
        if tax_config.minimum_amount and tax_amount < tax_config.minimum_amount:
            tax_amount = tax_config.minimum_amount

        if tax_config.maximum_amount and tax_amount > tax_config.maximum_amount:
            tax_amount = tax_config.maximum_amount

        return {
            "tax_code": tax_code,
            "tax_name": tax_config.tax_name,
            "tax_rate": float(tax_config.tax_rate),
            "base_amount": float(base_amount),
            "tax_amount": float(tax_amount),
            "total_amount": float(base_amount + tax_amount),
            "tax_type": tax_config.tax_type,
        }
