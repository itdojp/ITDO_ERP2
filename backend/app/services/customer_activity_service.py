"""
Customer Activity Service for CRM functionality.
顧客活動履歴サービス（CRM機能）
"""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import CustomerActivity
from app.schemas.customer import (
    CustomerActivityCreate,
    CustomerActivityResponse,
    CustomerActivityUpdate,
)


class CustomerActivityService:
    def __init__(self, db: AsyncSession) -> dict:
        self.db = db

    async def get_activities(
        self,
        organization_id: int,
        customer_id: Optional[int] = None,
        opportunity_id: Optional[int] = None,
        activity_type: Optional[str] = None,
        user_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CustomerActivityResponse]:
        """顧客活動履歴一覧取得"""
        # Join with Customer to ensure organization_id filter
        query = (
            select(CustomerActivity)
            .join(CustomerActivity.customer)
            .where(
                and_(
                    CustomerActivity.customer.has(organization_id=organization_id),
                    CustomerActivity.deleted_at.is_(None),
                )
            )
        )

        if customer_id:
            query = query.where(CustomerActivity.customer_id == customer_id)

        if opportunity_id:
            query = query.where(CustomerActivity.opportunity_id == opportunity_id)

        if activity_type:
            query = query.where(CustomerActivity.activity_type == activity_type)

        if user_id:
            query = query.where(CustomerActivity.user_id == user_id)

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query = query.where(CustomerActivity.activity_date >= start_dt)

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            query = query.where(CustomerActivity.activity_date <= end_dt)

        query = query.order_by(desc(CustomerActivity.activity_date))
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        activities = result.scalars().all()

        return [
            CustomerActivityResponse.model_validate(activity) for activity in activities
        ]

    async def get_activity_by_id(
        self, activity_id: int, organization_id: int
    ) -> Optional[CustomerActivityResponse]:
        """顧客活動詳細取得"""
        query = (
            select(CustomerActivity)
            .where(
                and_(
                    CustomerActivity.id == activity_id,
                    CustomerActivity.deleted_at.is_(None),
                )
            )
            .join(CustomerActivity.customer)
            .where(CustomerActivity.customer.has(organization_id=organization_id))
        )

        result = await self.db.execute(query)
        activity = result.scalar_one_or_none()

        if activity:
            return CustomerActivityResponse.model_validate(activity)
        return None

    async def create_activity(
        self,
        activity_data: CustomerActivityCreate,
        organization_id: int,
        user_id: int,
    ) -> CustomerActivityResponse:
        """顧客活動新規作成"""
        # Customer existence and organization check
        from app.models.customer import Customer

        customer_query = select(Customer).where(
            and_(
                Customer.id == activity_data.customer_id,
                Customer.organization_id == organization_id,
                Customer.deleted_at.is_(None),
            )
        )
        customer_result = await self.db.execute(customer_query)
        customer = customer_result.scalar_one_or_none()

        if not customer:
            raise ValueError("Customer not found")

        # Opportunity check if specified
        if activity_data.opportunity_id:
            from app.models.customer import Opportunity

            opp_query = (
                select(Opportunity)
                .where(
                    and_(
                        Opportunity.id == activity_data.opportunity_id,
                        Opportunity.customer_id == activity_data.customer_id,
                        Opportunity.deleted_at.is_(None),
                    )
                )
                .join(Opportunity.customer)
                .where(Opportunity.customer.has(organization_id=organization_id))
            )
            opp_result = await self.db.execute(opp_query)
            opportunity = opp_result.scalar_one_or_none()

            if not opportunity:
                raise ValueError("Opportunity not found")

        activity = CustomerActivity(user_id=user_id, **activity_data.model_dump())

        self.db.add(activity)
        await self.db.commit()
        await self.db.refresh(activity)

        return CustomerActivityResponse.model_validate(activity)

    async def update_activity(
        self,
        activity_id: int,
        activity_data: CustomerActivityUpdate,
        organization_id: int,
    ) -> Optional[CustomerActivityResponse]:
        """顧客活動更新"""
        query = (
            select(CustomerActivity)
            .where(
                and_(
                    CustomerActivity.id == activity_id,
                    CustomerActivity.deleted_at.is_(None),
                )
            )
            .join(CustomerActivity.customer)
            .where(CustomerActivity.customer.has(organization_id=organization_id))
        )

        result = await self.db.execute(query)
        activity = result.scalar_one_or_none()

        if not activity:
            return None

        # 更新
        for field, value in activity_data.model_dump(exclude_unset=True).items():
            setattr(activity, field, value)

        activity.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(activity)

        return CustomerActivityResponse.model_validate(activity)

    async def delete_activity(self, activity_id: int, organization_id: int) -> bool:
        """顧客活動削除（論理削除）"""
        query = (
            select(CustomerActivity)
            .where(
                and_(
                    CustomerActivity.id == activity_id,
                    CustomerActivity.deleted_at.is_(None),
                )
            )
            .join(CustomerActivity.customer)
            .where(CustomerActivity.customer.has(organization_id=organization_id))
        )

        result = await self.db.execute(query)
        activity = result.scalar_one_or_none()

        if not activity:
            return False

        # 論理削除
        activity.deleted_at = datetime.utcnow()
        await self.db.commit()

        return True

    async def complete_activity(
        self,
        activity_id: int,
        organization_id: int,
        outcome: Optional[str] = None,
        next_action: Optional[str] = None,
        next_action_date: Optional[str] = None,
    ) -> Optional[CustomerActivityResponse]:
        """活動完了"""
        query = (
            select(CustomerActivity)
            .where(
                and_(
                    CustomerActivity.id == activity_id,
                    CustomerActivity.deleted_at.is_(None),
                )
            )
            .join(CustomerActivity.customer)
            .where(CustomerActivity.customer.has(organization_id=organization_id))
        )

        result = await self.db.execute(query)
        activity = result.scalar_one_or_none()

        if not activity:
            return None

        activity.status = "completed"
        if outcome:
            activity.outcome = outcome
        if next_action:
            activity.next_action = next_action
        if next_action_date:
            activity.next_action_date = datetime.fromisoformat(
                next_action_date.replace("Z", "+00:00")
            )

        activity.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(activity)

        return CustomerActivityResponse.model_validate(activity)

    async def get_activity_summary(
        self,
        organization_id: int,
        customer_id: Optional[int] = None,
        user_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """活動サマリーレポート"""
        base_query = (
            select(CustomerActivity)
            .join(CustomerActivity.customer)
            .where(
                and_(
                    CustomerActivity.customer.has(organization_id=organization_id),
                    CustomerActivity.deleted_at.is_(None),
                )
            )
        )

        if customer_id:
            base_query = base_query.where(CustomerActivity.customer_id == customer_id)

        if user_id:
            base_query = base_query.where(CustomerActivity.user_id == user_id)

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            base_query = base_query.where(CustomerActivity.activity_date >= start_dt)

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            base_query = base_query.where(CustomerActivity.activity_date <= end_dt)

        # 総活動数
        total_query = select(func.count(CustomerActivity.id)).select_from(
            base_query.subquery()
        )
        total_result = await self.db.execute(total_query)
        total_activities = total_result.scalar()

        # 活動種別統計
        type_stats_query = base_query.group_by(
            CustomerActivity.activity_type
        ).with_only_columns(
            CustomerActivity.activity_type,
            func.count(CustomerActivity.id).label("count"),
        )
        type_stats_result = await self.db.execute(type_stats_query)
        activity_type_stats = {
            row.activity_type: row.count for row in type_stats_result
        }

        # ステータス別統計
        status_stats_query = base_query.group_by(
            CustomerActivity.status
        ).with_only_columns(
            CustomerActivity.status, func.count(CustomerActivity.id).label("count")
        )
        status_stats_result = await self.db.execute(status_stats_query)
        status_stats = {row.status: row.count for row in status_stats_result}

        return {
            "total_activities": total_activities,
            "activity_type_breakdown": activity_type_stats,
            "status_breakdown": status_stats,
            "period_summary": {
                "start_date": start_date,
                "end_date": end_date,
            },
        }

    async def get_upcoming_actions(
        self,
        organization_id: int,
        user_id: int,
        days_ahead: int = 7,
    ) -> List[CustomerActivityResponse]:
        """今後のアクション予定"""
        end_date = datetime.utcnow() + timedelta(days=days_ahead)

        query = (
            select(CustomerActivity)
            .join(CustomerActivity.customer)
            .where(
                and_(
                    CustomerActivity.customer.has(organization_id=organization_id),
                    CustomerActivity.user_id == user_id,
                    CustomerActivity.next_action_date.is_not(None),
                    CustomerActivity.next_action_date <= end_date,
                    CustomerActivity.next_action_date >= datetime.utcnow(),
                    CustomerActivity.deleted_at.is_(None),
                )
            )
            .order_by(CustomerActivity.next_action_date)
        )

        result = await self.db.execute(query)
        activities = result.scalars().all()

        return [
            CustomerActivityResponse.model_validate(activity) for activity in activities
        ]
