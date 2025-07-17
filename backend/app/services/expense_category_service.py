"""
Expense Category Service for financial management.
費目管理サービス（財務管理機能）
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.expense_category import ExpenseCategory
from app.schemas.expense_category import (
    ExpenseCategoryAnalytics,
    ExpenseCategoryCreate,
    ExpenseCategoryResponse,
    ExpenseCategoryUpdate,
)


class ExpenseCategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_categories(
        self,
        organization_id: int,
        parent_id: Optional[int] = None,
        category_type: Optional[str] = None,
        include_children: bool = False,
    ) -> List[ExpenseCategoryResponse]:
        """費目一覧取得"""
        query = select(ExpenseCategory).where(
            and_(
                ExpenseCategory.organization_id == organization_id,
                ExpenseCategory.deleted_at.is_(None),
            )
        )

        if parent_id is not None:
            query = query.where(ExpenseCategory.parent_id == parent_id)

        if category_type:
            query = query.where(ExpenseCategory.category_type == category_type)

        if include_children:
            query = query.options(selectinload(ExpenseCategory.children))

        query = query.order_by(ExpenseCategory.sort_order, ExpenseCategory.code)

        result = await self.db.execute(query)
        categories = result.scalars().all()

        return [ExpenseCategoryResponse.model_validate(cat) for cat in categories]

    async def get_category_tree(
        self, organization_id: int, category_type: Optional[str] = None
    ) -> List[ExpenseCategoryResponse]:
        """費目ツリー構造取得"""
        query = select(ExpenseCategory).where(
            and_(
                ExpenseCategory.organization_id == organization_id,
                ExpenseCategory.deleted_at.is_(None),
                ExpenseCategory.parent_id.is_(None),
            )
        )

        if category_type:
            query = query.where(ExpenseCategory.category_type == category_type)

        query = query.options(selectinload(ExpenseCategory.children))
        query = query.order_by(ExpenseCategory.sort_order, ExpenseCategory.code)

        result = await self.db.execute(query)
        root_categories = result.scalars().all()

        return [self._build_tree_node(cat) for cat in root_categories]

    def _build_tree_node(
        self, category: ExpenseCategory
    ) -> ExpenseCategoryResponse:
        """ツリーノード構築"""
        children = []
        if category.children:
            children = [
                self._build_tree_node(child)
                for child in sorted(
                    category.children, key=lambda x: (x.sort_order, x.code)
                )
            ]

        return ExpenseCategoryResponse(
            id=category.id,
            code=category.code,
            name=category.name,
            category_type=category.category_type,
            parent_id=category.parent_id,
            sort_order=category.sort_order,
            is_active=category.is_active,
            description=category.description,
            children=children,
        )

    async def get_category_by_id(
        self, category_id: int, organization_id: int
    ) -> Optional[ExpenseCategoryResponse]:
        """費目詳細取得"""
        query = select(ExpenseCategory).where(
            and_(
                ExpenseCategory.id == category_id,
                ExpenseCategory.organization_id == organization_id,
                ExpenseCategory.deleted_at.is_(None),
            )
        )

        result = await self.db.execute(query)
        category = result.scalar_one_or_none()

        if category:
            return ExpenseCategoryResponse.model_validate(category)
        return None

    async def create_category(
        self, category_data: ExpenseCategoryCreate, organization_id: int
    ) -> ExpenseCategoryResponse:
        """費目新規作成"""
        # 重複チェック
        existing = await self._check_duplicate_code(category_data.code, organization_id)
        if existing:
            raise ValueError(
                f"Expense category code '{category_data.code}' already exists"
            )

        # ソート順自動設定
        if category_data.sort_order is None:
            category_data.sort_order = await self._get_next_sort_order(
                organization_id, category_data.parent_id
            )

        category = ExpenseCategory(
            organization_id=organization_id, **category_data.model_dump()
        )

        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)

        return ExpenseCategoryResponse.model_validate(category)

    async def create_categories_bulk(
        self, categories_data: dict, organization_id: int
    ) -> List[ExpenseCategoryResponse]:
        """費目一括作成"""
        categories = []

        for category_data in categories_data.categories:
            # 重複チェック
            existing = await self._check_duplicate_code(
                category_data.code, organization_id
            )
            if existing:
                continue  # スキップ

            # ソート順自動設定
            if category_data.sort_order is None:
                category_data.sort_order = await self._get_next_sort_order(
                    organization_id, category_data.parent_id
                )

            category = ExpenseCategory(
                organization_id=organization_id, **category_data.model_dump()
            )
            categories.append(category)

        if categories:
            self.db.add_all(categories)
            await self.db.commit()

            for category in categories:
                await self.db.refresh(category)

        return [ExpenseCategoryResponse.model_validate(cat) for cat in categories]

    async def update_category(
        self,
        category_id: int,
        category_data: ExpenseCategoryUpdate,
        organization_id: int,
    ) -> Optional[ExpenseCategoryResponse]:
        """費目更新"""
        query = select(ExpenseCategory).where(
            and_(
                ExpenseCategory.id == category_id,
                ExpenseCategory.organization_id == organization_id,
                ExpenseCategory.deleted_at.is_(None),
            )
        )

        result = await self.db.execute(query)
        category = result.scalar_one_or_none()

        if not category:
            return None

        # コード重複チェック（自分以外）
        if category_data.code and category_data.code != category.code:
            existing = await self._check_duplicate_code(
                category_data.code, organization_id, exclude_id=category_id
            )
            if existing:
                raise ValueError(
                    f"Expense category code '{category_data.code}' already exists"
                )

        # 更新
        for field, value in category_data.model_dump(exclude_unset=True).items():
            setattr(category, field, value)

        category.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(category)

        return ExpenseCategoryResponse.model_validate(category)

    async def delete_category(self, category_id: int, organization_id: int) -> bool:
        """費目削除（論理削除）"""
        query = select(ExpenseCategory).where(
            and_(
                ExpenseCategory.id == category_id,
                ExpenseCategory.organization_id == organization_id,
                ExpenseCategory.deleted_at.is_(None),
            )
        )

        result = await self.db.execute(query)
        category = result.scalar_one_or_none()

        if not category:
            return False

        # 子カテゴリがある場合は削除不可
        children_query = select(func.count(ExpenseCategory.id)).where(
            and_(
                ExpenseCategory.parent_id == category_id,
                ExpenseCategory.deleted_at.is_(None),
            )
        )
        children_result = await self.db.execute(children_query)
        children_count = children_result.scalar()

        if children_count > 0:
            raise ValueError("Cannot delete category with child categories")

        # 論理削除
        category.deleted_at = datetime.utcnow()
        await self.db.commit()

        return True

    async def get_category_analytics(
        self,
        organization_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> ExpenseCategoryAnalytics:
        """費目使用状況分析"""
        # 基本統計
        total_query = select(func.count(ExpenseCategory.id)).where(
            and_(
                ExpenseCategory.organization_id == organization_id,
                ExpenseCategory.deleted_at.is_(None),
            )
        )
        total_result = await self.db.execute(total_query)
        total_categories = total_result.scalar()

        active_query = select(func.count(ExpenseCategory.id)).where(
            and_(
                ExpenseCategory.organization_id == organization_id,
                ExpenseCategory.deleted_at.is_(None),
                ExpenseCategory.is_active,
            )
        )
        active_result = await self.db.execute(active_query)
        active_categories = active_result.scalar()

        # カテゴリ別統計
        category_stats_query = (
            select(
                ExpenseCategory.category_type,
                func.count(ExpenseCategory.id).label("count"),
            )
            .where(
                and_(
                    ExpenseCategory.organization_id == organization_id,
                    ExpenseCategory.deleted_at.is_(None),
                )
            )
            .group_by(ExpenseCategory.category_type)
        )

        category_stats_result = await self.db.execute(category_stats_query)
        category_stats = {row.category_type: row.count for row in category_stats_result}

        return ExpenseCategoryAnalytics(
            total_categories=total_categories,
            active_categories=active_categories,
            inactive_categories=total_categories - active_categories,
            category_type_stats=category_stats,
            usage_stats={},  # 実際の使用状況は別途実装
        )

    async def _check_duplicate_code(
        self, code: str, organization_id: int, exclude_id: Optional[int] = None
    ) -> bool:
        """コード重複チェック"""
        query = select(ExpenseCategory).where(
            and_(
                ExpenseCategory.code == code,
                ExpenseCategory.organization_id == organization_id,
                ExpenseCategory.deleted_at.is_(None),
            )
        )

        if exclude_id:
            query = query.where(ExpenseCategory.id != exclude_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def _get_next_sort_order(
        self, organization_id: int, parent_id: Optional[int] = None
    ) -> int:
        """次のソート順取得"""
        query = select(func.max(ExpenseCategory.sort_order)).where(
            and_(
                ExpenseCategory.organization_id == organization_id,
                ExpenseCategory.parent_id == parent_id,
                ExpenseCategory.deleted_at.is_(None),
            )
        )

        result = await self.db.execute(query)
        max_sort_order = result.scalar()

        return (max_sort_order or 0) + 10
