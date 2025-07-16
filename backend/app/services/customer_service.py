"""
Customer Service for CRM functionality.
顧客管理サービス（CRM機能）
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.schemas.customer import (
    CustomerAnalytics,
    CustomerBulkCreate,
    CustomerCreate,
    CustomerDetailResponse,
    CustomerResponse,
    CustomerUpdate,
)


class CustomerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_customers(
        self,
        organization_id: int,
        status: Optional[str] = None,
        customer_type: Optional[str] = None,
        industry: Optional[str] = None,
        sales_rep_id: Optional[int] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CustomerResponse]:
        """顧客一覧取得"""
        query = select(Customer).where(
            and_(
                Customer.organization_id == organization_id,
                Customer.deleted_at.is_(None),
            )
        )

        if status:
            query = query.where(Customer.status == status)

        if customer_type:
            query = query.where(Customer.customer_type == customer_type)

        if industry:
            query = query.where(Customer.industry == industry)

        if sales_rep_id:
            query = query.where(Customer.sales_rep_id == sales_rep_id)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                Customer.name.ilike(search_term)
                | Customer.code.ilike(search_term)
                | Customer.email.ilike(search_term)
            )

        query = query.order_by(desc(Customer.updated_at))
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        customers = result.scalars().all()

        return [CustomerResponse.model_validate(customer) for customer in customers]

    async def get_customer_by_id(
        self, customer_id: int, organization_id: int
    ) -> Optional[CustomerDetailResponse]:
        """顧客詳細取得"""
        query = (
            select(Customer)
            .where(
                and_(
                    Customer.id == customer_id,
                    Customer.organization_id == organization_id,
                    Customer.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(Customer.contacts),
                selectinload(Customer.opportunities),
                selectinload(Customer.activities).selectinload(
                    "CustomerActivity.user"
                ),
            )
        )

        result = await self.db.execute(query)
        customer = result.scalar_one_or_none()

        if customer:
            # 最新活動のみ取得（最大10件）
            recent_activities = sorted(
                customer.activities, key=lambda x: x.activity_date, reverse=True
            )[:10]

            return CustomerDetailResponse(
                **customer.__dict__,
                contacts=[
                    contact for contact in customer.contacts if not contact.deleted_at
                ],
                opportunities=[
                    opp for opp in customer.opportunities if not opp.deleted_at
                ],
                recent_activities=recent_activities,
            )
        return None

    async def create_customer(
        self, customer_data: CustomerCreate, organization_id: int
    ) -> CustomerResponse:
        """顧客新規作成"""
        # 重複チェック
        existing = await self._check_duplicate_code(customer_data.code, organization_id)
        if existing:
            raise ValueError(f"Customer code '{customer_data.code}' already exists")

        customer = Customer(
            organization_id=organization_id, **customer_data.model_dump()
        )

        self.db.add(customer)
        await self.db.commit()
        await self.db.refresh(customer)

        return CustomerResponse.model_validate(customer)

    async def create_customers_bulk(
        self, customers_data: CustomerBulkCreate, organization_id: int
    ) -> List[CustomerResponse]:
        """顧客一括作成"""
        customers = []

        for customer_data in customers_data.customers:
            # 重複チェック
            existing = await self._check_duplicate_code(
                customer_data.code, organization_id
            )
            if existing:
                continue  # スキップ

            customer = Customer(
                organization_id=organization_id, **customer_data.model_dump()
            )
            customers.append(customer)

        if customers:
            self.db.add_all(customers)
            await self.db.commit()

            for customer in customers:
                await self.db.refresh(customer)

        return [CustomerResponse.model_validate(customer) for customer in customers]

    async def update_customer(
        self, customer_id: int, customer_data: CustomerUpdate, organization_id: int
    ) -> Optional[CustomerResponse]:
        """顧客更新"""
        query = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.organization_id == organization_id,
                Customer.deleted_at.is_(None),
            )
        )

        result = await self.db.execute(query)
        customer = result.scalar_one_or_none()

        if not customer:
            return None

        # コード重複チェック（自分以外）
        if customer_data.code and customer_data.code != customer.code:
            existing = await self._check_duplicate_code(
                customer_data.code, organization_id, exclude_id=customer_id
            )
            if existing:
                raise ValueError(
                    f"Customer code '{customer_data.code}' already exists"
                )

        # 更新
        for field, value in customer_data.model_dump(exclude_unset=True).items():
            setattr(customer, field, value)

        customer.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(customer)

        return CustomerResponse.model_validate(customer)

    async def delete_customer(self, customer_id: int, organization_id: int) -> bool:
        """顧客削除（論理削除）"""
        query = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.organization_id == organization_id,
                Customer.deleted_at.is_(None),
            )
        )

        result = await self.db.execute(query)
        customer = result.scalar_one_or_none()

        if not customer:
            return False

        # 論理削除
        customer.deleted_at = datetime.utcnow()
        await self.db.commit()

        return True

    async def assign_sales_rep(
        self, customer_id: int, sales_rep_id: int, organization_id: int
    ) -> bool:
        """営業担当者アサイン"""
        query = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.organization_id == organization_id,
                Customer.deleted_at.is_(None),
            )
        )

        result = await self.db.execute(query)
        customer = result.scalar_one_or_none()

        if not customer:
            return False

        customer.sales_rep_id = sales_rep_id
        customer.updated_at = datetime.utcnow()

        await self.db.commit()
        return True

    async def get_sales_summary(
        self,
        customer_id: int,
        organization_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Optional[dict]:
        """顧客売上サマリー"""
        query = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.organization_id == organization_id,
                Customer.deleted_at.is_(None),
            )
        )

        result = await self.db.execute(query)
        customer = result.scalar_one_or_none()

        if not customer:
            return None

        # 実際の売上データは別テーブルから取得（実装時）
        return {
            "customer_id": customer_id,
            "total_sales": customer.total_sales,
            "total_transactions": customer.total_transactions,
            "first_transaction_date": customer.first_transaction_date,
            "last_transaction_date": customer.last_transaction_date,
            "period_sales": 0.0,  # 期間売上（実装時）
            "period_transactions": 0,  # 期間取引数（実装時）
        }

    async def get_customer_analytics(
        self,
        organization_id: int,
        industry: Optional[str] = None,
        sales_rep_id: Optional[int] = None,
    ) -> CustomerAnalytics:
        """顧客分析サマリー"""
        base_query = select(Customer).where(
            and_(
                Customer.organization_id == organization_id,
                Customer.deleted_at.is_(None),
            )
        )

        if industry:
            base_query = base_query.where(Customer.industry == industry)

        if sales_rep_id:
            base_query = base_query.where(Customer.sales_rep_id == sales_rep_id)

        # 基本統計
        total_query = select(func.count(Customer.id)).where(
            and_(
                Customer.organization_id == organization_id,
                Customer.deleted_at.is_(None),
            )
        )
        total_result = await self.db.execute(total_query)
        total_customers = total_result.scalar()

        # ステータス別統計
        status_stats = {}
        for status in ["active", "inactive", "prospect"]:
            status_query = select(func.count(Customer.id)).where(
                and_(
                    Customer.organization_id == organization_id,
                    Customer.deleted_at.is_(None),
                    Customer.status == status,
                )
            )
            status_result = await self.db.execute(status_query)
            status_stats[status] = status_result.scalar()

        # 業界別統計
        industry_stats_query = (
            select(Customer.industry, func.count(Customer.id).label("count"))
            .where(
                and_(
                    Customer.organization_id == organization_id,
                    Customer.deleted_at.is_(None),
                    Customer.industry.is_not(None),
                )
            )
            .group_by(Customer.industry)
        )

        industry_stats_result = await self.db.execute(industry_stats_query)
        industry_stats = {
            row.industry: row.count for row in industry_stats_result
        }

        # 規模別統計
        scale_stats_query = (
            select(Customer.scale, func.count(Customer.id).label("count"))
            .where(
                and_(
                    Customer.organization_id == organization_id,
                    Customer.deleted_at.is_(None),
                    Customer.scale.is_not(None),
                )
            )
            .group_by(Customer.scale)
        )

        scale_stats_result = await self.db.execute(scale_stats_query)
        scale_stats = {row.scale: row.count for row in scale_stats_result}

        # トップ顧客（売上順）
        top_customers_query = (
            select(Customer)
            .where(
                and_(
                    Customer.organization_id == organization_id,
                    Customer.deleted_at.is_(None),
                )
            )
            .order_by(desc(Customer.total_sales))
            .limit(10)
        )

        top_customers_result = await self.db.execute(top_customers_query)
        top_customers = top_customers_result.scalars().all()

        top_customers_data = [
            {
                "id": customer.id,
                "name": customer.name,
                "total_sales": customer.total_sales,
                "total_transactions": customer.total_transactions,
            }
            for customer in top_customers
        ]

        return CustomerAnalytics(
            total_customers=total_customers,
            active_customers=status_stats.get("active", 0),
            prospects=status_stats.get("prospect", 0),
            inactive_customers=status_stats.get("inactive", 0),
            customers_by_industry=industry_stats,
            customers_by_scale=scale_stats,
            top_customers_by_sales=top_customers_data,
            recent_acquisitions=0,  # 新規獲得数（実装時）
        )

    async def _check_duplicate_code(
        self, code: str, organization_id: int, exclude_id: Optional[int] = None
    ) -> bool:
        """コード重複チェック"""
        query = select(Customer).where(
            and_(
                Customer.code == code,
                Customer.organization_id == organization_id,
                Customer.deleted_at.is_(None),
            )
        )

        if exclude_id:
            query = query.where(Customer.id != exclude_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
