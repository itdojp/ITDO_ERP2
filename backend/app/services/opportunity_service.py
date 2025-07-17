"""
Opportunity Service for CRM functionality.
商談管理サービス（CRM機能）
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Opportunity
from app.schemas.customer import (
    OpportunityAnalytics,
    OpportunityCreate,
    OpportunityDetailResponse,
    OpportunityResponse,
    OpportunityUpdate,
)


class OpportunityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_opportunities(
        self,
        organization_id: int,
        customer_id: Optional[int] = None,
        owner_id: Optional[int] = None,
        status: Optional[str] = None,
        stage: Optional[str] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[OpportunityResponse]:
        """商談一覧取得"""
        # Join with Customer to ensure organization_id filter
        query = (
            select(Opportunity)
            .join(Opportunity.customer)
            .where(
                and_(
                    Opportunity.customer.has(organization_id=organization_id),
                    Opportunity.deleted_at.is_(None),
                )
            )
        )

        if customer_id:
            query = query.where(Opportunity.customer_id == customer_id)

        if owner_id:
            query = query.where(Opportunity.owner_id == owner_id)

        if status:
            query = query.where(Opportunity.status == status)

        if stage:
            query = query.where(Opportunity.stage == stage)

        if min_value is not None:
            query = query.where(Opportunity.estimated_value >= min_value)

        if max_value is not None:
            query = query.where(Opportunity.estimated_value <= max_value)

        query = query.order_by(desc(Opportunity.updated_at))
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        opportunities = result.scalars().all()

        return [OpportunityResponse.model_validate(opp) for opp in opportunities]

    async def get_opportunity_by_id(
        self, opportunity_id: int, organization_id: int
    ) -> Optional[OpportunityDetailResponse]:
        """商談詳細取得"""
        query = (
            select(Opportunity)
            .where(
                and_(
                    Opportunity.id == opportunity_id,
                    Opportunity.deleted_at.is_(None),
                )
            )
            .join(Opportunity.customer)
            .where(Opportunity.customer.has(organization_id=organization_id))
            .options(selectinload(Opportunity.activities))
        )

        result = await self.db.execute(query)
        opportunity = result.scalar_one_or_none()

        if opportunity:
            return OpportunityDetailResponse(
                **opportunity.__dict__,
                activities=[
                    activity
                    for activity in opportunity.activities
                    if not activity.deleted_at
                ],
            )
        return None

    async def create_opportunity(
        self, opportunity_data: OpportunityCreate, organization_id: int
    ) -> OpportunityResponse:
        """商談新規作成"""
        # Customer existence and organization check
        from app.models.customer import Customer

        customer_query = select(Customer).where(
            and_(
                Customer.id == opportunity_data.customer_id,
                Customer.organization_id == organization_id,
                Customer.deleted_at.is_(None),
            )
        )
        customer_result = await self.db.execute(customer_query)
        customer = customer_result.scalar_one_or_none()

        if not customer:
            raise ValueError("Customer not found")

        opportunity = Opportunity(**opportunity_data.model_dump())

        # Auto-update probability based on stage
        opportunity.update_probability_by_stage()

        self.db.add(opportunity)
        await self.db.commit()
        await self.db.refresh(opportunity)

        return OpportunityResponse.model_validate(opportunity)

    async def update_opportunity(
        self,
        opportunity_id: int,
        opportunity_data: OpportunityUpdate,
        organization_id: int,
    ) -> Optional[OpportunityResponse]:
        """商談更新"""
        query = (
            select(Opportunity)
            .where(
                and_(
                    Opportunity.id == opportunity_id,
                    Opportunity.deleted_at.is_(None),
                )
            )
            .join(Opportunity.customer)
            .where(Opportunity.customer.has(organization_id=organization_id))
        )

        result = await self.db.execute(query)
        opportunity = result.scalar_one_or_none()

        if not opportunity:
            return None

        # 更新
        for field, value in opportunity_data.model_dump(exclude_unset=True).items():
            setattr(opportunity, field, value)

        # Auto-update probability if stage changed
        if opportunity_data.stage:
            opportunity.update_probability_by_stage()

        opportunity.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(opportunity)

        return OpportunityResponse.model_validate(opportunity)

    async def delete_opportunity(
        self, opportunity_id: int, organization_id: int
    ) -> bool:
        """商談削除（論理削除）"""
        query = (
            select(Opportunity)
            .where(
                and_(
                    Opportunity.id == opportunity_id,
                    Opportunity.deleted_at.is_(None),
                )
            )
            .join(Opportunity.customer)
            .where(Opportunity.customer.has(organization_id=organization_id))
        )

        result = await self.db.execute(query)
        opportunity = result.scalar_one_or_none()

        if not opportunity:
            return False

        # 論理削除
        opportunity.deleted_at = datetime.utcnow()
        await self.db.commit()

        return True

    async def update_stage(
        self, opportunity_id: int, stage: str, organization_id: int
    ) -> Optional[OpportunityResponse]:
        """商談ステージ更新"""
        query = (
            select(Opportunity)
            .where(
                and_(
                    Opportunity.id == opportunity_id,
                    Opportunity.deleted_at.is_(None),
                )
            )
            .join(Opportunity.customer)
            .where(Opportunity.customer.has(organization_id=organization_id))
        )

        result = await self.db.execute(query)
        opportunity = result.scalar_one_or_none()

        if not opportunity:
            return None

        opportunity.stage = stage
        opportunity.update_probability_by_stage()
        opportunity.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(opportunity)

        return OpportunityResponse.model_validate(opportunity)

    async def close_opportunity(
        self,
        opportunity_id: int,
        status: str,
        organization_id: int,
        reason: Optional[str] = None,
    ) -> Optional[OpportunityResponse]:
        """商談クローズ"""
        query = (
            select(Opportunity)
            .where(
                and_(
                    Opportunity.id == opportunity_id,
                    Opportunity.deleted_at.is_(None),
                )
            )
            .join(Opportunity.customer)
            .where(Opportunity.customer.has(organization_id=organization_id))
        )

        result = await self.db.execute(query)
        opportunity = result.scalar_one_or_none()

        if not opportunity:
            return None

        opportunity.status = status
        opportunity.actual_close_date = datetime.utcnow()

        if status == "won":
            opportunity.probability = 100
            opportunity.stage = "closed_won"
        elif status == "lost":
            opportunity.probability = 0
            opportunity.stage = "closed_lost"
            if reason:
                opportunity.loss_reason = reason

        opportunity.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(opportunity)

        return OpportunityResponse.model_validate(opportunity)

    async def get_opportunity_analytics(
        self,
        organization_id: int,
        owner_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> OpportunityAnalytics:
        """商談分析サマリー"""
        base_query = (
            select(Opportunity)
            .join(Opportunity.customer)
            .where(
                and_(
                    Opportunity.customer.has(organization_id=organization_id),
                    Opportunity.deleted_at.is_(None),
                )
            )
        )

        if owner_id:
            base_query = base_query.where(Opportunity.owner_id == owner_id)

        if customer_id:
            base_query = base_query.where(Opportunity.customer_id == customer_id)

        # 基本統計
        total_query = select(func.count(Opportunity.id)).select_from(
            base_query.subquery()
        )
        total_result = await self.db.execute(total_query)
        total_opportunities = total_result.scalar()

        # ステータス別統計
        status_stats = {}
        for status in ["open", "won", "lost", "canceled"]:
            status_query = base_query.where(Opportunity.status == status)
            status_count_query = select(func.count(Opportunity.id)).select_from(
                status_query.subquery()
            )
            status_result = await self.db.execute(status_count_query)
            status_stats[status] = status_result.scalar()

        # パイプライン価値
        pipeline_query = base_query.where(Opportunity.status == "open")
        pipeline_value_query = select(
            func.coalesce(func.sum(Opportunity.estimated_value), 0)
        ).select_from(pipeline_query.subquery())
        pipeline_result = await self.db.execute(pipeline_value_query)
        total_pipeline_value = float(pipeline_result.scalar())

        # 平均案件サイズ
        avg_deal_query = base_query.where(Opportunity.status == "won")
        avg_deal_size_query = select(
            func.coalesce(func.avg(Opportunity.estimated_value), 0)
        ).select_from(avg_deal_query.subquery())
        avg_result = await self.db.execute(avg_deal_size_query)
        average_deal_size = float(avg_result.scalar())

        # 成約率
        won_count = status_stats.get("won", 0)
        total_closed = won_count + status_stats.get("lost", 0)
        win_rate = (won_count / total_closed * 100) if total_closed > 0 else 0.0

        # ステージ別統計
        stage_stats_query = (
            base_query.where(Opportunity.status == "open")
            .group_by(Opportunity.stage)
            .with_only_columns(
                Opportunity.stage, func.count(Opportunity.id).label("count")
            )
        )
        stage_stats_result = await self.db.execute(stage_stats_query)
        stage_stats = {row.stage: row.count for row in stage_stats_result}

        return OpportunityAnalytics(
            total_opportunities=total_opportunities,
            open_opportunities=status_stats.get("open", 0),
            won_opportunities=won_count,
            lost_opportunities=status_stats.get("lost", 0),
            total_pipeline_value=total_pipeline_value,
            average_deal_size=average_deal_size,
            win_rate=win_rate,
            opportunities_by_stage=stage_stats,
            monthly_closed_deals={},  # 月次クローズ実績（実装時）
        )

    async def get_pipeline_forecast(
        self,
        organization_id: int,
        owner_id: Optional[int] = None,
        quarters: int = 4,
    ) -> dict:
        """パイプライン予測"""
        # 実装時：確度と金額に基づく予測計算
        return {
            "quarters": quarters,
            "forecast": [],  # 四半期別予測
            "weighted_pipeline": 0.0,  # 重み付きパイプライン
            "best_case": 0.0,  # ベストケース
            "worst_case": 0.0,  # ワーストケース
        }

    async def get_conversion_rate_report(
        self,
        organization_id: int,
        owner_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """成約率レポート"""
        # 実装時：ステージ間の成約率分析
        return {
            "overall_conversion_rate": 0.0,
            "stage_conversion_rates": {},
            "time_to_close_avg": 0,
            "conversion_trends": {},
        }
