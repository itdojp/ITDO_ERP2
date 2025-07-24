"""
Budget Service for financial management.
予算管理サービス（財務管理機能）
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.budget import Budget, BudgetItem, BudgetStatus
from app.schemas.budget import (
    BudgetAnalyticsResponse,
    BudgetApprovalRequest,
    BudgetCreate,
    BudgetItemCreate,
    BudgetItemResponse,
    BudgetItemUpdate,
    BudgetReportResponse,
    BudgetResponse,
    BudgetUpdate,
)


class BudgetService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_budgets(
        self,
        organization_id: int,
        fiscal_year: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[BudgetResponse]:
        """予算一覧取得"""
        query = select(Budget).where(
            and_(Budget.organization_id == organization_id, Budget.deleted_at.is_(None))
        )

        if fiscal_year:
            query = query.where(Budget.fiscal_year == fiscal_year)

        if status:
            query = query.where(Budget.status == status)

        query = query.order_by(desc(Budget.fiscal_year), Budget.code)
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        budgets = result.scalars().all()

        return [BudgetResponse.model_validate(budget) for budget in budgets]

    async def get_budget_by_id(
        self, budget_id: int, organization_id: int
    ) -> Optional[BudgetResponse]:
        """予算詳細取得"""
        query = (
            select(Budget)
            .where(
                and_(
                    Budget.id == budget_id,
                    Budget.organization_id == organization_id,
                    Budget.deleted_at.is_(None),
                )
            )
            .options(selectinload(Budget.budget_items))
        )

        result = await self.db.execute(query)
        budget = result.scalar_one_or_none()

        if budget:
            return BudgetResponse.model_validate(budget)
        return None

    async def create_budget(
        self, budget_data: BudgetCreate, organization_id: int, created_by_id: int
    ) -> BudgetResponse:
        """予算新規作成"""
        # 重複チェック
        existing = await self._check_duplicate_code(
            budget_data.code, organization_id, budget_data.fiscal_year
        )
        if existing:
            raise ValueError(
                f"Budget code '{budget_data.code}' already exists for "
                f"fiscal year {budget_data.fiscal_year}"
            )

        budget = Budget(
            organization_id=organization_id,
            created_by_id=created_by_id,
            **budget_data.model_dump(),
        )

        self.db.add(budget)
        await self.db.commit()
        await self.db.refresh(budget)

        return BudgetResponse.model_validate(budget)

    async def update_budget(
        self, budget_id: int, budget_data: BudgetUpdate, organization_id: int
    ) -> Optional[BudgetResponse]:
        """予算更新"""
        query = select(Budget).where(
            and_(
                Budget.id == budget_id,
                Budget.organization_id == organization_id,
                Budget.deleted_at.is_(None),
            )
        )

        result = await self.db.execute(query)
        budget = result.scalar_one_or_none()

        if not budget:
            return None

        # 承認済み予算は更新制限
        if budget.status == "approved" and budget_data.total_amount:
            raise ValueError("Cannot modify total amount of approved budget")

        # コード重複チェック（自分以外）
        if budget_data.code and budget_data.code != budget.code:
            existing = await self._check_duplicate_code(
                budget_data.code,
                organization_id,
                budget.fiscal_year,
                exclude_id=budget_id,
            )
            if existing:
                raise ValueError(f"Budget code '{budget_data.code}' already exists")

        # 更新
        for field, value in budget_data.model_dump(exclude_unset=True).items():
            setattr(budget, field, value)

        budget.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(budget)

        return BudgetResponse.model_validate(budget)

    async def delete_budget(self, budget_id: int, organization_id: int) -> bool:
        """予算削除（論理削除）"""
        query = select(Budget).where(
            and_(
                Budget.id == budget_id,
                Budget.organization_id == organization_id,
                Budget.deleted_at.is_(None),
            )
        )

        result = await self.db.execute(query)
        budget = result.scalar_one_or_none()

        if not budget:
            return False

        # 承認済み予算は削除不可
        if budget.status == "approved":
            raise ValueError("Cannot delete approved budget")

        # 論理削除
        budget.deleted_at = datetime.utcnow()
        await self.db.commit()

        return True

    async def approve_budget(
        self,
        budget_id: int,
        approval_data: BudgetApprovalRequest,
        organization_id: int,
        approved_by_id: int,
    ) -> Optional[BudgetResponse]:
        """予算承認"""
        query = select(Budget).where(
            and_(
                Budget.id == budget_id,
                Budget.organization_id == organization_id,
                Budget.deleted_at.is_(None),
            )
        )

        result = await self.db.execute(query)
        budget = result.scalar_one_or_none()

        if not budget:
            return None

        if budget.status != BudgetStatus.SUBMITTED:
            raise ValueError("Only submitted budgets can be approved")

        # Map action to status
        if approval_data.action == "approve":
            budget.status = BudgetStatus.APPROVED
        elif approval_data.action == "reject":
            budget.status = BudgetStatus.REJECTED
        else:
            budget.status = BudgetStatus.SUBMITTED  # request_changes keeps it submitted

        budget.approved_by = approved_by_id
        budget.approved_at = datetime.utcnow()
        if hasattr(budget, "approval_comment"):  # Check if field exists
            budget.approval_comment = approval_data.comments
        budget.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(budget)

        return BudgetResponse.model_validate(budget)

    async def create_budget_item(
        self, budget_id: int, item_data: BudgetItemCreate, organization_id: int
    ) -> BudgetItemResponse:
        """予算項目新規作成"""
        # 予算存在確認
        budget_query = select(Budget).where(
            and_(
                Budget.id == budget_id,
                Budget.organization_id == organization_id,
                Budget.deleted_at.is_(None),
            )
        )
        budget_result = await self.db.execute(budget_query)
        budget = budget_result.scalar_one_or_none()

        if not budget:
            raise ValueError("Budget not found")

        if budget.status == "approved":
            raise ValueError("Cannot modify approved budget")

        item = BudgetItem(budget_id=budget_id, **item_data.model_dump())

        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)

        # 予算合計額更新
        await self._update_budget_total(budget_id)

        return BudgetItemResponse.model_validate(item)

    async def update_budget_item(
        self,
        budget_id: int,
        item_id: int,
        item_data: BudgetItemUpdate,
        organization_id: int,
    ) -> Optional[BudgetItemResponse]:
        """予算項目更新"""
        # 予算確認
        budget_query = select(Budget).where(
            and_(
                Budget.id == budget_id,
                Budget.organization_id == organization_id,
                Budget.deleted_at.is_(None),
            )
        )
        budget_result = await self.db.execute(budget_query)
        budget = budget_result.scalar_one_or_none()

        if not budget or budget.status == "approved":
            return None

        # 項目確認
        item_query = select(BudgetItem).where(
            and_(
                BudgetItem.id == item_id,
                BudgetItem.budget_id == budget_id,
                BudgetItem.deleted_at.is_(None),
            )
        )
        item_result = await self.db.execute(item_query)
        item = item_result.scalar_one_or_none()

        if not item:
            return None

        # 更新
        for field, value in item_data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)

        item.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(item)

        # 予算合計額更新
        await self._update_budget_total(budget_id)

        return BudgetItemResponse.model_validate(item)

    async def delete_budget_item(
        self, budget_id: int, item_id: int, organization_id: int
    ) -> bool:
        """予算項目削除"""
        # 予算確認
        budget_query = select(Budget).where(
            and_(
                Budget.id == budget_id,
                Budget.organization_id == organization_id,
                Budget.deleted_at.is_(None),
            )
        )
        budget_result = await self.db.execute(budget_query)
        budget = budget_result.scalar_one_or_none()

        if not budget or budget.status == "approved":
            return False

        # 項目確認
        item_query = select(BudgetItem).where(
            and_(
                BudgetItem.id == item_id,
                BudgetItem.budget_id == budget_id,
                BudgetItem.deleted_at.is_(None),
            )
        )
        item_result = await self.db.execute(item_query)
        item = item_result.scalar_one_or_none()

        if not item:
            return False

        # 論理削除
        item.deleted_at = datetime.utcnow()
        await self.db.commit()

        # 予算合計額更新
        await self._update_budget_total(budget_id)

        return True

    async def get_budget_report(
        self,
        budget_id: int,
        organization_id: int,
        include_variance: bool = True,
        include_utilization: bool = True,
    ) -> Optional[BudgetReportResponse]:
        """予算実績レポート"""
        budget = await self.get_budget_by_id(budget_id, organization_id)
        if not budget:
            return None

        # 実績データは別途実装
        report_data: dict[str, Any] = {
            "report_id": f"BR-{budget.id}-{datetime.utcnow().strftime('%Y%m%d')}",
            "budget_period": f"{budget.start_date} - {budget.end_date}",
            "generated_at": datetime.utcnow(),
            "summary": {
                "total_budget": float(budget.total_amount),
                "actual_amount": 0.0,  # 実績額（実装時に計算）
                "variance": 0.0,  # 差異額
                "utilization_rate": 0.0,  # 利用率
            },
            "department_details": [],  # 部門別詳細（実装時に計算）
            "category_details": [],  # カテゴリ別詳細（実装時に計算）
            "variance_analysis": {
                "positive_variance": 0.0,
                "negative_variance": 0.0,
                "significant_variances": [],
            },
            "recommendations": [],  # 推奨事項（実装時に生成）
        }

        return BudgetReportResponse(**report_data)

    async def get_budget_analytics(
        self,
        organization_id: int,
        fiscal_year: Optional[int] = None,
        department_id: Optional[int] = None,
    ) -> BudgetAnalyticsResponse:
        """予算分析サマリー"""
        query = select(Budget).where(
            and_(Budget.organization_id == organization_id, Budget.deleted_at.is_(None))
        )

        if fiscal_year:
            query = query.where(Budget.fiscal_year == fiscal_year)

        if department_id:
            query = query.where(Budget.department_id == department_id)

        result = await self.db.execute(query)
        budgets = result.scalars().all()

        # 集計計算
        total_amount = sum(budget.total_amount for budget in budgets)
        status_summary: dict[str, int] = {}

        for budget in budgets:
            status_summary[budget.status] = status_summary.get(budget.status, 0) + 1

        return BudgetAnalyticsResponse(
            total_budget_amount=float(total_amount),
            total_utilized_amount=0.0,  # 実装時に計算
            utilization_percentage=0.0,  # 実装時に計算
            variance_amount=0.0,  # 実装時に計算
            variance_percentage=0.0,  # 実装時に計算
            department_breakdown={},  # 部門別サマリー（実装時に計算）
            category_breakdown={},  # カテゴリ別サマリー（実装時に計算）
            monthly_trends=[],  # トレンドデータ（実装時に計算）
        )

    async def _check_duplicate_code(
        self,
        code: str,
        organization_id: int,
        fiscal_year: int,
        exclude_id: Optional[int] = None,
    ) -> bool:
        """コード重複チェック"""
        query = select(Budget).where(
            and_(
                Budget.code == code,
                Budget.organization_id == organization_id,
                Budget.fiscal_year == fiscal_year,
                Budget.deleted_at.is_(None),
            )
        )

        if exclude_id:
            query = query.where(Budget.id != exclude_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def _update_budget_total(self, budget_id: int) -> None:
        """予算合計額更新"""
        total_query = select(func.sum(BudgetItem.budgeted_amount)).where(
            and_(BudgetItem.budget_id == budget_id, BudgetItem.deleted_at.is_(None))
        )
        total_result = await self.db.execute(total_query)
        total_amount = total_result.scalar() or Decimal("0.00")

        budget_query = select(Budget).where(Budget.id == budget_id)
        budget_result = await self.db.execute(budget_query)
        budget = budget_result.scalar_one_or_none()

        if budget:
            budget.total_amount = total_amount
            budget.updated_at = datetime.utcnow()
            await self.db.commit()

    async def get_budget_vs_actual_analysis(
        self, organization_id: int, fiscal_year: int
    ) -> dict[str, Any]:
        """Budget vs Actual comparison analysis for Phase 4."""
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

        total_budgeted = 0.0
        total_actual = 0.0
        variance_analysis = []

        for budget in budgets:
            # Calculate actual spending (simulated for demo)
            # In real implementation, this would query expense/transaction tables
            budgeted_amount = float(budget.total_amount or 0)
            actual_amount = budgeted_amount * 0.85  # Simulated 85% utilization

            variance = budgeted_amount - actual_amount
            variance_percentage = (
                (variance / budgeted_amount * 100) if budgeted_amount > 0 else 0
            )

            variance_analysis.append(
                {
                    "budget_code": budget.code,
                    "budget_name": budget.name,
                    "budgeted_amount": budgeted_amount,
                    "actual_amount": actual_amount,
                    "variance": variance,
                    "variance_percentage": variance_percentage,
                    "status": "under_budget" if variance > 0 else "over_budget",
                }
            )

            total_budgeted += budgeted_amount
            total_actual += actual_amount

        overall_variance = total_budgeted - total_actual
        overall_variance_percentage = (
            (overall_variance / total_budgeted * 100) if total_budgeted > 0 else 0
        )

        return {
            "fiscal_year": fiscal_year,
            "organization_id": organization_id,
            "summary": {
                "total_budgeted": total_budgeted,
                "total_actual": total_actual,
                "overall_variance": overall_variance,
                "overall_variance_percentage": overall_variance_percentage,
                "utilization_rate": (total_actual / total_budgeted * 100)
                if total_budgeted > 0
                else 0,
            },
            "budget_details": variance_analysis,
            "analysis_date": datetime.utcnow().isoformat(),
        }
