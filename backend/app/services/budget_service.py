"""
Budget Service for financial management.
予算管理サービス（財務管理機能）
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.budget import Budget, BudgetItem
from app.schemas.budget import (
    BudgetAnalyticsResponse,
    BudgetApprovalRequest,
    BudgetCreate,
    BudgetDetailResponse,
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
    ) -> Optional[BudgetDetailResponse]:
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
            .options(selectinload(Budget.items))
        )

        result = await self.db.execute(query)
        budget = result.scalar_one_or_none()

        if budget:
            return BudgetDetailResponse.model_validate(budget)
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
                f"Budget code '{budget_data.code}' already exists for fiscal year {budget_data.fiscal_year}"
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

        if budget.status != "pending":
            raise ValueError("Only pending budgets can be approved")

        budget.status = "approved" if approval_data.approved else "rejected"
        budget.approved_by_id = approved_by_id
        budget.approved_at = datetime.utcnow()
        budget.approval_comment = approval_data.comment
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
        report_data = {
            "budget": budget,
            "actual_amount": 0.0,  # 実績額（実装時に計算）
            "variance": 0.0,  # 差異額
            "utilization_rate": 0.0,  # 利用率
            "items_report": [],  # 項目別レポート
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
        total_budgets = len(budgets)
        total_amount = sum(budget.total_amount for budget in budgets)
        status_summary = {}

        for budget in budgets:
            status_summary[budget.status] = status_summary.get(budget.status, 0) + 1

        return BudgetAnalyticsResponse(
            total_budgets=total_budgets,
            total_amount=total_amount,
            status_summary=status_summary,
            average_amount=total_amount / total_budgets if total_budgets > 0 else 0,
            department_summary={},  # 部門別サマリー（実装時に計算）
            trend_data={},  # トレンドデータ（実装時に計算）
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
        total_query = select(func.sum(BudgetItem.budget_amount)).where(
            and_(BudgetItem.budget_id == budget_id, BudgetItem.deleted_at.is_(None))
        )
        total_result = await self.db.execute(total_query)
        total_amount = total_result.scalar() or 0.0

        budget_query = select(Budget).where(Budget.id == budget_id)
        budget_result = await self.db.execute(budget_query)
        budget = budget_result.scalar_one_or_none()

        if budget:
            budget.total_amount = total_amount
            budget.updated_at = datetime.utcnow()
            await self.db.commit()
