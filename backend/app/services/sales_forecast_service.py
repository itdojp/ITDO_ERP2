"""
Sales Forecast Service for Phase 5 CRM - Advanced Sales Analytics.
営業予測分析サービス（CRM機能Phase 5）
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import (
    Customer,
    CustomerStatus,
    Opportunity,
    OpportunityStage,
)


class SalesForecastService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_sales_forecast(
        self,
        organization_id: int,
        forecast_months: int = 12,
        include_pipeline: bool = True,
        include_trends: bool = True,
    ) -> Dict:
        """Generate comprehensive sales forecast analysis."""
        # Get all opportunities for the organization
        opportunities_query = (
            select(Opportunity)
            .join(Customer)
            .where(
                and_(
                    Customer.organization_id == organization_id,
                    Opportunity.deleted_at.is_(None),
                    Customer.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(Opportunity.customer),
                selectinload(Opportunity.owner),
                selectinload(Opportunity.assigned_user),
            )
        )

        opportunities_result = await self.db.execute(opportunities_query)
        opportunities = opportunities_result.scalars().all()

        # Calculate current period metrics
        current_period_metrics = await self._calculate_current_period_metrics(
            opportunities
        )

        # Generate forecast by month
        monthly_forecast = await self._generate_monthly_forecast(
            opportunities, forecast_months
        )

        # Calculate win probability analysis
        probability_analysis = await self._calculate_win_probability_analysis(
            opportunities
        )

        # Generate pipeline analysis
        pipeline_analysis = None
        if include_pipeline:
            pipeline_analysis = await self._generate_pipeline_analysis(opportunities)

        # Generate trend analysis
        trend_analysis = None
        if include_trends:
            trend_analysis = await self._generate_trend_analysis(
                organization_id, opportunities
            )

        return {
            "forecast_type": "sales_forecast",
            "organization_id": organization_id,
            "forecast_months": forecast_months,
            "generation_date": datetime.utcnow().isoformat(),
            "current_period": current_period_metrics,
            "monthly_forecast": monthly_forecast,
            "probability_analysis": probability_analysis,
            "pipeline_analysis": pipeline_analysis,
            "trend_analysis": trend_analysis,
            "summary": {
                "total_pipeline_value": sum(
                    float(opp.value or 0) for opp in opportunities if opp.is_open
                ),
                "weighted_pipeline_value": sum(
                    float(opp.weighted_value or 0)
                    for opp in opportunities if opp.is_open
                ),
                "total_opportunities": len(opportunities),
                "open_opportunities": len(
                    [opp for opp in opportunities if opp.is_open]
                ),
                "won_opportunities": len([opp for opp in opportunities if opp.is_won]),
            },
        }

    async def calculate_win_probability(
        self, organization_id: int, opportunity_id: Optional[int] = None
    ) -> Dict:
        """Calculate win probability using historical data and ML-like analysis."""
        # Base query for opportunities
        query = (
            select(Opportunity)
            .join(Customer)
            .where(
                and_(
                    Customer.organization_id == organization_id,
                    Opportunity.deleted_at.is_(None),
                    Customer.deleted_at.is_(None),
                )
            )
        )

        if opportunity_id:
            query = query.where(Opportunity.id == opportunity_id)

        opportunities_result = await self.db.execute(query)
        opportunities = opportunities_result.scalars().all()

        # Calculate historical win rates by various factors
        historical_analysis = await self._calculate_historical_win_rates(opportunities)

        # For specific opportunity, calculate enhanced probability
        if opportunity_id and opportunities:
            opportunity = opportunities[0]
            enhanced_probability = await self._calculate_enhanced_probability(
                opportunity, historical_analysis
            )
            return {
                "opportunity_id": opportunity_id,
                "current_probability": opportunity.probability,
                "enhanced_probability": enhanced_probability,
                "historical_analysis": historical_analysis,
                "recommendations": await self._generate_probability_recommendations(
                    opportunity, enhanced_probability
                ),
            }

        return {
            "organization_analysis": historical_analysis,
            "total_opportunities_analyzed": len(opportunities),
        }

    async def analyze_customer_sales_potential(
        self, organization_id: int, customer_id: Optional[int] = None
    ) -> Dict:
        """Analyze sales potential for customers."""
        # Get customers with their opportunities and activities
        customers_query = (
            select(Customer)
            .where(
                and_(
                    Customer.organization_id == organization_id,
                    Customer.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(Customer.opportunities),
                selectinload(Customer.activities),
                selectinload(Customer.assigned_user),
            )
        )

        if customer_id:
            customers_query = customers_query.where(Customer.id == customer_id)

        customers_result = await self.db.execute(customers_query)
        customers = customers_result.scalars().all()

        customer_analyses = []
        for customer in customers:
            analysis = await self._analyze_single_customer_potential(customer)
            customer_analyses.append(analysis)

        # Sort by potential score
        customer_analyses.sort(key=lambda x: x["potential_score"], reverse=True)

        return {
            "analysis_type": "customer_sales_potential",
            "organization_id": organization_id,
            "customer_id": customer_id,
            "analysis_date": datetime.utcnow().isoformat(),
            "customer_analyses": customer_analyses,
            "summary": {
                "total_customers_analyzed": len(customer_analyses),
                "high_potential_customers": len(
                    [c for c in customer_analyses if c["potential_score"] >= 80]
                ),
                "medium_potential_customers": len(
                    [
                        c
                        for c in customer_analyses
                        if 50 <= c["potential_score"] < 80
                    ]
                ),
                "low_potential_customers": len(
                    [c for c in customer_analyses if c["potential_score"] < 50]
                ),
            },
        }

    async def generate_sales_performance_analysis(
        self,
        organization_id: int,
        user_id: Optional[int] = None,
        period_months: int = 6
    ) -> Dict:
        """Generate sales performance analysis for sales reps."""
        # Get opportunities with user assignments
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_months * 30)

        opportunities_query = (
            select(Opportunity)
            .join(Customer)
            .where(
                and_(
                    Customer.organization_id == organization_id,
                    Opportunity.deleted_at.is_(None),
                    Customer.deleted_at.is_(None),
                    Opportunity.created_at >= start_date,
                )
            )
            .options(
                selectinload(Opportunity.customer),
                selectinload(Opportunity.owner),
                selectinload(Opportunity.assigned_user),
            )
        )

        if user_id:
            opportunities_query = opportunities_query.where(
                Opportunity.assigned_to == user_id
            )

        opportunities_result = await self.db.execute(opportunities_query)
        opportunities = opportunities_result.scalars().all()

        # Group by sales rep
        sales_rep_performance = {}
        for opportunity in opportunities:
            rep_id = opportunity.assigned_to or opportunity.owner_id
            rep_name = (
                opportunity.assigned_user.full_name
                if opportunity.assigned_user
                else opportunity.owner.full_name
            )

            if rep_id not in sales_rep_performance:
                sales_rep_performance[rep_id] = {
                    "user_id": rep_id,
                    "user_name": rep_name,
                    "total_opportunities": 0,
                    "won_opportunities": 0,
                    "lost_opportunities": 0,
                    "total_value": 0.0,
                    "won_value": 0.0,
                    "pipeline_value": 0.0,
                    "win_rate": 0.0,
                    "average_deal_size": 0.0,
                    "conversion_rate": 0.0,
                }

            perf = sales_rep_performance[rep_id]
            perf["total_opportunities"] += 1
            perf["total_value"] += float(opportunity.value or 0)

            if opportunity.stage == OpportunityStage.CLOSED_WON:
                perf["won_opportunities"] += 1
                perf["won_value"] += float(opportunity.value or 0)
            elif opportunity.stage == OpportunityStage.CLOSED_LOST:
                perf["lost_opportunities"] += 1
            else:
                perf["pipeline_value"] += float(opportunity.value or 0)

        # Calculate derived metrics
        for rep_id, perf in sales_rep_performance.items():
            closed_opportunities = (
                perf["won_opportunities"] + perf["lost_opportunities"]
            )
            if closed_opportunities > 0:
                perf["win_rate"] = (
                    perf["won_opportunities"] / closed_opportunities * 100
                )

            if perf["won_opportunities"] > 0:
                perf["average_deal_size"] = (
                    perf["won_value"] / perf["won_opportunities"]
                )

            if perf["total_opportunities"] > 0:
                perf["conversion_rate"] = (
                    perf["won_opportunities"] / perf["total_opportunities"] * 100
                )

        return {
            "analysis_type": "sales_performance",
            "organization_id": organization_id,
            "user_id": user_id,
            "period_months": period_months,
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "sales_rep_performance": list(sales_rep_performance.values()),
            "team_summary": await self._calculate_team_summary(
                list(sales_rep_performance.values())
            ),
        }

    async def _calculate_current_period_metrics(
        self, opportunities: List[Opportunity]
    ) -> Dict:
        """Calculate current period sales metrics."""
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year

        current_month_opps = [
            opp
            for opp in opportunities
            if (
                opp.created_at.month == current_month
                and opp.created_at.year == current_year
            )
        ]

        won_this_month = [
            opp for opp in current_month_opps
            if opp.stage == OpportunityStage.CLOSED_WON
        ]

        return {
            "current_month": current_month,
            "current_year": current_year,
            "new_opportunities": len(current_month_opps),
            "won_opportunities": len(won_this_month),
            "won_value": sum(float(opp.value or 0) for opp in won_this_month),
            "pipeline_value": sum(
                float(opp.value or 0) for opp in current_month_opps if opp.is_open
            ),
            "average_deal_size": (
                sum(float(opp.value or 0) for opp in won_this_month)
                / len(won_this_month)
                if won_this_month
                else 0
            ),
        }

    async def _generate_monthly_forecast(
        self, opportunities: List[Opportunity], forecast_months: int
    ) -> List[Dict]:
        """Generate monthly sales forecast."""
        monthly_forecast = []
        current_date = datetime.utcnow()

        for month_offset in range(forecast_months):
            target_date = current_date + timedelta(days=month_offset * 30)
            target_month = target_date.month
            target_year = target_date.year

            # Opportunities expected to close in this month
            month_opportunities = [
                opp
                for opp in opportunities
                if opp.expected_close_date
                and opp.expected_close_date.month == target_month
                and opp.expected_close_date.year == target_year
                and opp.is_open
            ]

            # Calculate forecast based on probability
            forecasted_value = sum(
                float(opp.weighted_value or 0) for opp in month_opportunities
            )

            # Conservative and optimistic scenarios
            conservative_value = forecasted_value * 0.7  # 70% of weighted
            optimistic_value = sum(
                float(opp.value or 0) for opp in month_opportunities
            )  # 100% of pipeline

            monthly_forecast.append(
                {
                    "month": target_month,
                    "year": target_year,
                    "date": target_date.isoformat(),
                    "forecasted_value": forecasted_value,
                    "conservative_value": conservative_value,
                    "optimistic_value": optimistic_value,
                    "opportunity_count": len(month_opportunities),
                    "opportunities": [
                        {
                            "id": opp.id,
                            "name": opp.name,
                            "customer": opp.customer.company_name,
                            "value": float(opp.value or 0),
                            "probability": opp.probability,
                            "weighted_value": float(opp.weighted_value or 0),
                        }
                        for opp in month_opportunities
                    ],
                }
            )

        return monthly_forecast

    async def _calculate_win_probability_analysis(
        self, opportunities: List[Opportunity]
    ) -> Dict:
        """Calculate win probability analysis across different dimensions."""
        # Group by stage
        stage_analysis = {}
        for opp in opportunities:
            stage = opp.stage.value
            if stage not in stage_analysis:
                stage_analysis[stage] = {
                    "count": 0,
                    "total_value": 0.0,
                    "won_count": 0,
                    "won_value": 0.0,
                    "win_rate": 0.0,
                }

            stage_analysis[stage]["count"] += 1
            stage_analysis[stage]["total_value"] += float(opp.value or 0)

            if opp.stage == OpportunityStage.CLOSED_WON:
                stage_analysis[stage]["won_count"] += 1
                stage_analysis[stage]["won_value"] += float(opp.value or 0)

        # Calculate win rates
        for stage, data in stage_analysis.items():
            if data["count"] > 0:
                data["win_rate"] = data["won_count"] / data["count"] * 100

        # Value range analysis
        value_ranges = [
            {"min": 0, "max": 100000, "label": "Small (<¥100K)"},
            {"min": 100000, "max": 500000, "label": "Medium (¥100K-¥500K)"},
            {"min": 500000, "max": 1000000, "label": "Large (¥500K-¥1M)"},
            {"min": 1000000, "max": float("inf"), "label": "Enterprise (>¥1M)"},
        ]

        value_analysis = {}
        for range_def in value_ranges:
            range_opps = [
                opp
                for opp in opportunities
                if range_def["min"] <= float(opp.value or 0) < range_def["max"]
            ]
            won_opps = [opp for opp in range_opps if opp.is_won]

            value_analysis[range_def["label"]] = {
                "count": len(range_opps),
                "won_count": len(won_opps),
                "win_rate": len(won_opps) / len(range_opps) * 100 if range_opps else 0,
                "total_value": sum(float(opp.value or 0) for opp in range_opps),
                "won_value": sum(float(opp.value or 0) for opp in won_opps),
            }

        return {
            "stage_analysis": stage_analysis,
            "value_analysis": value_analysis,
            "overall_win_rate": (
                len([opp for opp in opportunities if opp.is_won])
                / len([opp for opp in opportunities if not opp.is_open])
                * 100
                if [opp for opp in opportunities if not opp.is_open]
                else 0
            ),
        }

    async def _generate_pipeline_analysis(
        self, opportunities: List[Opportunity]
    ) -> Dict:
        """Generate detailed pipeline analysis."""
        open_opportunities = [opp for opp in opportunities if opp.is_open]

        # Group by stage
        pipeline_by_stage = {}
        for opp in open_opportunities:
            stage = opp.stage.value
            if stage not in pipeline_by_stage:
                pipeline_by_stage[stage] = {
                    "count": 0,
                    "total_value": 0.0,
                    "weighted_value": 0.0,
                    "opportunities": [],
                }

            pipeline_by_stage[stage]["count"] += 1
            pipeline_by_stage[stage]["total_value"] += float(opp.value or 0)
            pipeline_by_stage[stage]["weighted_value"] += float(opp.weighted_value or 0)
            pipeline_by_stage[stage]["opportunities"].append(
                {
                    "id": opp.id,
                    "name": opp.name,
                    "customer": opp.customer.company_name,
                    "value": float(opp.value or 0),
                    "probability": opp.probability,
                    "expected_close_date": (
                        opp.expected_close_date.isoformat()
                        if opp.expected_close_date
                        else None
                    ),
                }
            )

        # Age analysis
        age_analysis = {}
        for opp in open_opportunities:
            age_days = (datetime.utcnow() - opp.created_at).days
            age_bucket = (
                "0-30 days"
                if age_days <= 30
                else "31-60 days"
                if age_days <= 60
                else "61-90 days"
                if age_days <= 90
                else "90+ days"
            )

            if age_bucket not in age_analysis:
                age_analysis[age_bucket] = {"count": 0, "total_value": 0.0}

            age_analysis[age_bucket]["count"] += 1
            age_analysis[age_bucket]["total_value"] += float(opp.value or 0)

        return {
            "pipeline_by_stage": pipeline_by_stage,
            "age_analysis": age_analysis,
            "total_pipeline": {
                "count": len(open_opportunities),
                "total_value": sum(float(opp.value or 0) for opp in open_opportunities),
                "weighted_value": sum(
                    float(opp.weighted_value or 0) for opp in open_opportunities
                ),
            },
        }

    async def _generate_trend_analysis(
        self, organization_id: int, opportunities: List[Opportunity]
    ) -> Dict:
        """Generate trend analysis for sales forecast."""
        # Calculate monthly trends for the past 12 months
        monthly_trends = []
        current_date = datetime.utcnow()

        for month_offset in range(12):
            target_date = current_date - timedelta(days=month_offset * 30)
            target_month = target_date.month
            target_year = target_date.year

            month_opportunities = [
                opp
                for opp in opportunities
                if opp.created_at.month == target_month
                and opp.created_at.year == target_year
            ]

            won_opportunities = [
                opp for opp in month_opportunities if opp.is_won
            ]

            monthly_trends.append(
                {
                    "month": target_month,
                    "year": target_year,
                    "date": target_date.replace(day=1).isoformat(),
                    "new_opportunities": len(month_opportunities),
                    "won_opportunities": len(won_opportunities),
                    "won_value": sum(
                        float(opp.value or 0) for opp in won_opportunities
                    ),
                    "pipeline_value": sum(
                        float(opp.value or 0)
                        for opp in month_opportunities
                        if opp.is_open
                    ),
                }
            )

        # Reverse to have chronological order
        monthly_trends.reverse()

        # Calculate growth trends
        if len(monthly_trends) >= 2:
            recent_3_months = monthly_trends[-3:]
            previous_3_months = (
                monthly_trends[-6:-3] if len(monthly_trends) >= 6 else []
            )

            recent_avg = (
                sum(month["won_value"] for month in recent_3_months)
                / len(recent_3_months)
                if recent_3_months
                else 0
            )
            previous_avg = (
                sum(month["won_value"] for month in previous_3_months)
                / len(previous_3_months)
                if previous_3_months
                else 0
            )

            growth_rate = (
                ((recent_avg - previous_avg) / previous_avg * 100)
                if previous_avg > 0
                else 0
            )
        else:
            growth_rate = 0

        return {
            "monthly_trends": monthly_trends,
            "growth_analysis": {
                "recent_3_month_average": recent_avg if len(monthly_trends) >= 2 else 0,
                "previous_3_month_average": (
                    previous_avg if len(monthly_trends) >= 2 else 0
                ),
                "growth_rate_percentage": growth_rate,
                "trend_direction": (
                    "increasing" if growth_rate > 5
                    else "decreasing" if growth_rate < -5
                    else "stable"
                ),
            },
        }

    async def _calculate_historical_win_rates(
        self, opportunities: List[Opportunity]
    ) -> Dict:
        """Calculate historical win rates for probability enhancement."""
        closed_opportunities = [opp for opp in opportunities if not opp.is_open]
        won_opportunities = [opp for opp in opportunities if opp.is_won]

        overall_win_rate = (
            len(won_opportunities) / len(closed_opportunities) * 100
            if closed_opportunities
            else 0
        )

        # Win rate by customer type
        customer_type_rates = {}
        # Win rate by opportunity value range
        value_range_rates = {}
        # Win rate by sales rep
        sales_rep_rates = {}

        # This would be enhanced with more sophisticated analysis
        return {
            "overall_win_rate": overall_win_rate,
            "customer_type_rates": customer_type_rates,
            "value_range_rates": value_range_rates,
            "sales_rep_rates": sales_rep_rates,
            "total_opportunities_analyzed": len(closed_opportunities),
        }

    async def _calculate_enhanced_probability(
        self, opportunity: Opportunity, historical_analysis: Dict
    ) -> int:
        """Calculate enhanced probability using historical data."""
        # Start with current probability
        enhanced_prob = opportunity.probability

        # Adjust based on historical win rates
        overall_rate = historical_analysis["overall_win_rate"]
        if overall_rate > 0:
            # Simple adjustment based on historical performance
            adjustment_factor = overall_rate / 50  # Normalize around 50%
            enhanced_prob = min(100, max(0, int(enhanced_prob * adjustment_factor)))

        return enhanced_prob

    async def _generate_probability_recommendations(
        self, opportunity: Opportunity, enhanced_probability: int
    ) -> List[str]:
        """Generate recommendations for improving win probability."""
        recommendations = []

        if enhanced_probability < 30:
            recommendations.extend([
                "Focus on qualifying the opportunity better",
                "Identify key decision makers",
                "Understand budget and timeline constraints",
            ])
        elif enhanced_probability < 60:
            recommendations.extend([
                "Develop a compelling value proposition",
                "Address potential objections proactively",
                "Build relationships with stakeholders",
            ])
        else:
            recommendations.extend([
                "Focus on closing activities",
                "Prepare final proposal",
                "Schedule decision meeting",
            ])

        return recommendations

    async def _analyze_single_customer_potential(self, customer: Customer) -> Dict:
        """Analyze sales potential for a single customer."""
        # Calculate potential score based on various factors
        potential_score = 50  # Base score

        # Adjust based on customer status
        if customer.status == CustomerStatus.ACTIVE:
            potential_score += 20
        elif customer.status == CustomerStatus.PROSPECT:
            potential_score += 10

        # Adjust based on annual revenue
        if customer.annual_revenue:
            if customer.annual_revenue > 1000000:
                potential_score += 15
            elif customer.annual_revenue > 500000:
                potential_score += 10

        # Adjust based on opportunity history
        open_opportunities = [opp for opp in customer.opportunities if opp.is_open]
        won_opportunities = [opp for opp in customer.opportunities if opp.is_won]

        potential_score += min(len(open_opportunities) * 5, 20)
        potential_score += min(len(won_opportunities) * 3, 15)

        # Cap at 100
        potential_score = min(100, potential_score)

        return {
            "customer_id": customer.id,
            "customer_code": customer.customer_code,
            "company_name": customer.company_name,
            "potential_score": potential_score,
            "status": customer.status.value,
            "annual_revenue": float(customer.annual_revenue or 0),
            "total_sales": float(customer.total_sales),
            "open_opportunities": len(open_opportunities),
            "won_opportunities": len(won_opportunities),
            "last_contact_date": (
                customer.last_contact_date.isoformat()
                if customer.last_contact_date
                else None
            ),
            "assigned_to": (
                customer.assigned_user.full_name if customer.assigned_user else None
            ),
        }

    async def _calculate_team_summary(self, sales_rep_performance: List[Dict]) -> Dict:
        """Calculate team summary metrics."""
        if not sales_rep_performance:
            return {}

        total_opportunities = sum(
            rep["total_opportunities"] for rep in sales_rep_performance
        )
        total_won = sum(rep["won_opportunities"] for rep in sales_rep_performance)
        total_value = sum(rep["won_value"] for rep in sales_rep_performance)

        return {
            "team_size": len(sales_rep_performance),
            "total_opportunities": total_opportunities,
            "total_won_opportunities": total_won,
            "total_won_value": total_value,
            "team_win_rate": (
                total_won / total_opportunities * 100
                if total_opportunities > 0 else 0
            ),
            "average_deal_size": total_value / total_won if total_won > 0 else 0,
            "top_performer": max(
                sales_rep_performance, key=lambda x: x["won_value"], default={}
            ),
            "most_active": max(
                sales_rep_performance,
                key=lambda x: x["total_opportunities"],
                default={}
            ),
        }

