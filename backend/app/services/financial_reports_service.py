"""
Financial Reports Service for Phase 4 Financial Management.
財務レポート生成サービス（財務管理機能Phase 4）
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import and_, extract, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.budget import Budget
from app.models.expense import Expense, ExpenseStatus


class FinancialReportsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_budget_performance_report(
        self,
        organization_id: int,
        fiscal_year: int,
        include_variance_analysis: bool = True,
        include_trend_data: bool = True,
    ) -> Dict[str, Any]:
        """Generate comprehensive budget performance report."""
        # Get all budgets for the fiscal year
        budgets_query = select(Budget).where(
            and_(
                Budget.organization_id == organization_id,
                Budget.fiscal_year == fiscal_year,
                Budget.deleted_at.is_(None),
            )
        )
        budgets_result = await self.db.execute(budgets_query)
        budgets = budgets_result.scalars().all()

        # Get expense data for the fiscal year
        expenses_query = select(Expense).where(
            and_(
                Expense.organization_id == organization_id,
                extract("year", Expense.expense_date) == fiscal_year,
                Expense.status.in_([ExpenseStatus.APPROVED, ExpenseStatus.PAID]),
                Expense.deleted_at.is_(None),
            )
        )
        expenses_result = await self.db.execute(expenses_query)
        expenses = expenses_result.scalars().all()

        # Calculate budget performance metrics
        total_budget = sum(float(budget.total_amount or 0) for budget in budgets)
        total_actual = sum(float(expense.amount) for expense in expenses)
        overall_variance = total_budget - total_actual
        overall_variance_percentage = (
            (overall_variance / total_budget * 100) if total_budget > 0 else 0
        )
        utilization_rate = (
            (total_actual / total_budget * 100) if total_budget > 0 else 0
        )

        # Budget breakdown by category/department
        budget_breakdown = []
        for budget in budgets:
            budget_amount = float(budget.total_amount or 0)
            # Calculate actual expenses for this budget category
            actual_expenses = [
                exp
                for exp in expenses
                if hasattr(exp, "expense_category_id")
                and getattr(exp, "expense_category_id", None) == budget.id
            ]
            actual_amount = sum(float(exp.amount) for exp in actual_expenses)

            variance = budget_amount - actual_amount
            variance_percentage = (
                (variance / budget_amount * 100) if budget_amount > 0 else 0
            )

            budget_breakdown.append(
                {
                    "budget_code": budget.code,
                    "budget_name": budget.name,
                    "budget_amount": budget_amount,
                    "actual_amount": actual_amount,
                    "variance": variance,
                    "variance_percentage": variance_percentage,
                    "status": "under_budget" if variance > 0 else "over_budget",
                    "utilization_rate": (actual_amount / budget_amount * 100)
                    if budget_amount > 0
                    else 0,
                }
            )

        report = {
            "report_type": "budget_performance",
            "organization_id": organization_id,
            "fiscal_year": fiscal_year,
            "generation_date": datetime.utcnow().isoformat(),
            "summary": {
                "total_budget": total_budget,
                "total_actual": total_actual,
                "overall_variance": overall_variance,
                "overall_variance_percentage": overall_variance_percentage,
                "utilization_rate": utilization_rate,
                "budget_count": len(budgets),
                "expense_count": len(expenses),
            },
            "budget_breakdown": budget_breakdown,
        }

        if include_variance_analysis:
            report["variance_analysis"] = await self._generate_variance_analysis(
                list(budgets), list(expenses)
            )

        if include_trend_data:
            report["trend_data"] = await self._generate_budget_trend_data(
                organization_id, fiscal_year
            )

        return report

    async def generate_expense_summary_report(
        self,
        organization_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        include_employee_breakdown: bool = True,
        include_category_breakdown: bool = True,
    ) -> Dict[str, Any]:
        """Generate expense summary report."""
        # Build query for expenses
        query = (
            select(Expense)
            .where(
                and_(
                    Expense.organization_id == organization_id,
                    Expense.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(Expense.employee),
                selectinload(Expense.expense_category),
            )
        )

        if date_from:
            query = query.where(Expense.expense_date >= date_from)
        if date_to:
            query = query.where(Expense.expense_date <= date_to)

        result = await self.db.execute(query)
        expenses = result.scalars().all()

        # Calculate summary statistics
        total_expenses = len(expenses)
        total_amount = sum(float(expense.amount) for expense in expenses)

        # Status breakdown
        status_breakdown = {}
        for status in ExpenseStatus:
            status_expenses = [e for e in expenses if e.status == status]
            status_breakdown[status.value] = {
                "count": len(status_expenses),
                "amount": sum(float(e.amount) for e in status_expenses),
            }

        report = {
            "report_type": "expense_summary",
            "organization_id": organization_id,
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
            "generation_date": datetime.utcnow().isoformat(),
            "summary": {
                "total_expenses": total_expenses,
                "total_amount": total_amount,
                "average_amount": (
                    total_amount / total_expenses if total_expenses > 0 else 0
                ),
                "status_breakdown": status_breakdown,
            },
        }

        if include_employee_breakdown:
            report["employee_breakdown"] = await self._generate_employee_breakdown(
                list(expenses)
            )

        if include_category_breakdown:
            report["category_breakdown"] = await self._generate_category_breakdown(
                list(expenses)
            )

        return report

    async def generate_monthly_financial_report(
        self,
        organization_id: int,
        year: int,
        month: int,
    ) -> Dict[str, Any]:
        """Generate monthly financial report combining budgets and expenses."""
        # Get monthly budget data
        budgets_query = select(Budget).where(
            and_(
                Budget.organization_id == organization_id,
                Budget.fiscal_year == year,
                Budget.deleted_at.is_(None),
            )
        )
        budgets_result = await self.db.execute(budgets_query)
        budgets = budgets_result.scalars().all()

        # Get monthly expense data
        expenses_query = (
            select(Expense)
            .where(
                and_(
                    Expense.organization_id == organization_id,
                    extract("year", Expense.expense_date) == year,
                    extract("month", Expense.expense_date) == month,
                    Expense.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(Expense.employee),
                selectinload(Expense.expense_category),
            )
        )
        expenses_result = await self.db.execute(expenses_query)
        expenses = expenses_result.scalars().all()

        # Calculate monthly budget allocation (1/12 of annual budget)
        monthly_budget = sum(float(budget.total_amount or 0) for budget in budgets) / 12
        monthly_actual = sum(float(expense.amount) for expense in expenses)
        monthly_variance = monthly_budget - monthly_actual
        monthly_variance_percentage = (
            (monthly_variance / monthly_budget * 100) if monthly_budget > 0 else 0
        )

        # Expense trends (compare with previous months)
        previous_months_data = await self._get_previous_months_data(
            organization_id, year, month, 3
        )

        return {
            "report_type": "monthly_financial",
            "organization_id": organization_id,
            "year": year,
            "month": month,
            "generation_date": datetime.utcnow().isoformat(),
            "monthly_summary": {
                "monthly_budget": monthly_budget,
                "monthly_actual": monthly_actual,
                "monthly_variance": monthly_variance,
                "monthly_variance_percentage": monthly_variance_percentage,
                "expense_count": len(expenses),
                "average_expense": monthly_actual / len(expenses) if expenses else 0,
            },
            "expense_details": [
                {
                    "expense_id": expense.id,
                    "expense_number": expense.expense_number,
                    "employee_name": expense.employee.full_name,
                    "category": expense.expense_category.name
                    if expense.expense_category
                    else "Uncategorized",
                    "amount": float(expense.amount),
                    "date": expense.expense_date.isoformat(),
                    "status": expense.status.value,
                }
                for expense in expenses
            ],
            "trend_comparison": previous_months_data,
        }

    async def generate_yearly_financial_summary(
        self,
        organization_id: int,
        year: int,
    ) -> Dict[str, Any]:
        """Generate yearly financial summary report."""
        # Get yearly budget data
        budgets_query = select(Budget).where(
            and_(
                Budget.organization_id == organization_id,
                Budget.fiscal_year == year,
                Budget.deleted_at.is_(None),
            )
        )
        budgets_result = await self.db.execute(budgets_query)
        budgets = budgets_result.scalars().all()

        # Get yearly expense data
        expenses_query = select(Expense).where(
            and_(
                Expense.organization_id == organization_id,
                extract("year", Expense.expense_date) == year,
                Expense.deleted_at.is_(None),
            )
        )
        expenses_result = await self.db.execute(expenses_query)
        expenses = expenses_result.scalars().all()

        # Monthly breakdown
        monthly_data = []
        for month in range(1, 13):
            month_expenses = [e for e in expenses if e.expense_date.month == month]
            monthly_amount = sum(float(e.amount) for e in month_expenses)
            monthly_budget = sum(float(b.total_amount or 0) for b in budgets) / 12

            monthly_data.append(
                {
                    "month": month,
                    "budget": monthly_budget,
                    "actual": monthly_amount,
                    "variance": monthly_budget - monthly_amount,
                    "expense_count": len(month_expenses),
                }
            )

        total_budget = sum(float(budget.total_amount or 0) for budget in budgets)
        total_actual = sum(float(expense.amount) for expense in expenses)

        return {
            "report_type": "yearly_financial_summary",
            "organization_id": organization_id,
            "year": year,
            "generation_date": datetime.utcnow().isoformat(),
            "yearly_summary": {
                "total_budget": total_budget,
                "total_actual": total_actual,
                "overall_variance": total_budget - total_actual,
                "overall_variance_percentage": (
                    ((total_budget - total_actual) / total_budget * 100)
                    if total_budget > 0
                    else 0
                ),
                "total_expenses": len(expenses),
                "budget_count": len(budgets),
            },
            "monthly_breakdown": monthly_data,
            "top_expense_categories": await self._get_top_expense_categories(
                list(expenses), limit=10
            ),
            "expense_trends": await self._generate_yearly_expense_trends(
                organization_id, year
            ),
        }

    async def _generate_variance_analysis(
        self, budgets: List[Budget], expenses: List[Expense]
    ) -> Dict[str, Any]:
        """Generate detailed variance analysis."""
        variance_categories: Dict[str, List[Dict[str, Any]]] = {
            "significant_overruns": [],
            "significant_underruns": [],
            "on_track": [],
        }

        for budget in budgets:
            budget_amount = float(budget.total_amount or 0)
            # Calculate related expenses
            actual_amount = sum(
                float(exp.amount)
                for exp in expenses
                # Simplified: assume relationship exists
            )

            variance_percentage = (
                ((budget_amount - actual_amount) / budget_amount * 100)
                if budget_amount > 0
                else 0
            )

            budget_info = {
                "budget_code": budget.code,
                "budget_name": budget.name,
                "budget_amount": budget_amount,
                "actual_amount": actual_amount,
                "variance_percentage": variance_percentage,
            }

            if variance_percentage > 20:
                variance_categories["significant_underruns"].append(budget_info)
            elif variance_percentage < -20:
                variance_categories["significant_overruns"].append(budget_info)
            else:
                variance_categories["on_track"].append(budget_info)

        return variance_categories

    async def _generate_budget_trend_data(
        self, organization_id: int, fiscal_year: int
    ) -> Dict[str, Any]:
        """Generate budget trend data for the past 3 years."""
        trend_data = []

        for year in range(fiscal_year - 2, fiscal_year + 1):
            year_budgets_query = select(Budget).where(
                and_(
                    Budget.organization_id == organization_id,
                    Budget.fiscal_year == year,
                    Budget.deleted_at.is_(None),
                )
            )
            year_budgets_result = await self.db.execute(year_budgets_query)
            year_budgets = year_budgets_result.scalars().all()

            year_expenses_query = select(Expense).where(
                and_(
                    Expense.organization_id == organization_id,
                    extract("year", Expense.expense_date) == year,
                    Expense.deleted_at.is_(None),
                )
            )
            year_expenses_result = await self.db.execute(year_expenses_query)
            year_expenses = year_expenses_result.scalars().all()

            year_budget = sum(float(b.total_amount or 0) for b in year_budgets)
            year_actual = sum(float(e.amount) for e in year_expenses)

            trend_data.append(
                {
                    "year": year,
                    "budget": year_budget,
                    "actual": year_actual,
                    "variance": year_budget - year_actual,
                    "utilization_rate": (year_actual / year_budget * 100)
                    if year_budget > 0
                    else 0,
                }
            )

        return {"historical_trends": trend_data}

    async def _generate_employee_breakdown(self, expenses: List[Expense]) -> List[Dict[str, Any]]:
        """Generate employee expense breakdown."""
        employee_data: Dict[int, Dict[str, Any]] = {}

        for expense in expenses:
            employee_id = expense.employee_id
            if employee_id not in employee_data:
                employee_data[employee_id] = {
                    "employee_id": employee_id,
                    "employee_name": expense.employee.full_name,
                    "expense_count": 0,
                    "total_amount": 0.0,
                    "expenses": [],
                }

            employee_data[employee_id]["expense_count"] += 1
            employee_data[employee_id]["total_amount"] += float(expense.amount)
            employee_data[employee_id]["expenses"].append(
                {
                    "expense_id": expense.id,
                    "amount": float(expense.amount),
                    "date": expense.expense_date.isoformat(),
                    "status": expense.status.value,
                }
            )

        return list(employee_data.values())

    async def _generate_category_breakdown(self, expenses: List[Expense]) -> List[Dict[str, Any]]:
        """Generate expense category breakdown."""
        category_data: Dict[int, Dict[str, Any]] = {}

        for expense in expenses:
            category_id = expense.expense_category_id
            category_name = (
                expense.expense_category.name
                if expense.expense_category
                else "Uncategorized"
            )

            if category_id not in category_data:
                category_data[category_id] = {
                    "category_id": category_id,
                    "category_name": category_name,
                    "expense_count": 0,
                    "total_amount": 0.0,
                    "average_amount": 0.0,
                }

            category_data[category_id]["expense_count"] += 1
            category_data[category_id]["total_amount"] += float(expense.amount)

        # Calculate averages
        for category in category_data.values():
            if category["expense_count"] > 0:
                category["average_amount"] = (
                    category["total_amount"] / category["expense_count"]
                )

        return list(category_data.values())

    async def _get_previous_months_data(
        self, organization_id: int, year: int, month: int, months_back: int
    ) -> List[Dict[str, Any]]:
        """Get expense data for previous months for trend analysis."""
        previous_data = []

        for i in range(1, months_back + 1):
            target_month = month - i
            target_year = year

            if target_month <= 0:
                target_month += 12
                target_year -= 1

            month_expenses_query = select(Expense).where(
                and_(
                    Expense.organization_id == organization_id,
                    extract("year", Expense.expense_date) == target_year,
                    extract("month", Expense.expense_date) == target_month,
                    Expense.deleted_at.is_(None),
                )
            )

            month_expenses_result = await self.db.execute(month_expenses_query)
            month_expenses = month_expenses_result.scalars().all()

            month_total = sum(float(e.amount) for e in month_expenses)

            previous_data.append(
                {
                    "year": target_year,
                    "month": target_month,
                    "total_amount": month_total,
                    "expense_count": len(month_expenses),
                }
            )

        return previous_data

    async def _get_top_expense_categories(
        self, expenses: List[Expense], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top expense categories by amount."""
        category_totals: Dict[str, Dict[str, Any]] = {}

        for expense in expenses:
            category_name = (
                expense.expense_category.name
                if expense.expense_category
                else "Uncategorized"
            )

            if category_name not in category_totals:
                category_totals[category_name] = {
                    "category_name": category_name,
                    "total_amount": 0.0,
                    "expense_count": 0,
                }

            category_totals[category_name]["total_amount"] += float(expense.amount)
            category_totals[category_name]["expense_count"] += 1

        # Sort by total amount and return top categories
        sorted_categories = sorted(
            category_totals.values(),
            key=lambda x: float(x["total_amount"]),
            reverse=True,
        )

        return sorted_categories[:limit]

    async def _generate_yearly_expense_trends(
        self, organization_id: int, year: int
    ) -> Dict[str, Any]:
        """Generate yearly expense trends and projections."""
        # Get monthly expense data for the year
        monthly_trends = []

        for month in range(1, 13):
            month_expenses_query = select(Expense).where(
                and_(
                    Expense.organization_id == organization_id,
                    extract("year", Expense.expense_date) == year,
                    extract("month", Expense.expense_date) == month,
                    Expense.deleted_at.is_(None),
                )
            )

            month_expenses_result = await self.db.execute(month_expenses_query)
            month_expenses = month_expenses_result.scalars().all()

            month_total = sum(float(e.amount) for e in month_expenses)

            monthly_trends.append(
                {
                    "month": month,
                    "amount": month_total,
                    "expense_count": len(month_expenses),
                }
            )

        # Calculate trend indicators
        total_so_far = sum(month["amount"] for month in monthly_trends)
        months_with_data = len([m for m in monthly_trends if m["amount"] > 0])

        if months_with_data > 0:
            average_monthly = total_so_far / months_with_data
            projected_yearly = average_monthly * 12
        else:
            average_monthly = 0
            projected_yearly = 0

        return {
            "monthly_trends": monthly_trends,
            "trend_analysis": {
                "total_to_date": total_so_far,
                "average_monthly": average_monthly,
                "projected_yearly": projected_yearly,
                "months_with_data": months_with_data,
            },
        }
