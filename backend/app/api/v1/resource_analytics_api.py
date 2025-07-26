"""
ITDO ERP Backend - Resource Analytics API
Day 22: Advanced analytics and reporting for resource management
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.resource import (
    ResourceAnalyticsResponse,
    ResourceBenchmarkResponse,
    ResourceForecastRequest,
    ResourceForecastResponse,
    ResourceKPIResponse,
    ResourceROIAnalysisResponse,
    ResourceTrendAnalysisResponse,
)

router = APIRouter()


class ResourceAnalyticsService:
    """Service for resource analytics and reporting"""

    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.redis = redis_client

    async def get_resource_analytics(
        self,
        start_date: date,
        end_date: date,
        resource_ids: Optional[List[int]] = None,
        department_ids: Optional[List[int]] = None,
        resource_types: Optional[List[str]] = None,
    ) -> ResourceAnalyticsResponse:
        """Get comprehensive resource analytics"""

        # Build filters
        filters = [
            # Assuming ResourceAllocation model exists
            text("start_date <= :end_date"),
            text("end_date >= :start_date"),
        ]

        if resource_ids:
            filters.append(text("resource_id = ANY(:resource_ids)"))
        if department_ids:
            filters.append(text("department_id = ANY(:department_ids)"))
        if resource_types:
            filters.append(text("resource_type = ANY(:resource_types)"))

        # Get utilization data
        utilization_query = text("""
            SELECT
                resource_id,
                AVG(allocation_percentage) as avg_utilization,
                MAX(allocation_percentage) as peak_utilization,
                MIN(allocation_percentage) as min_utilization,
                COUNT(*) as allocation_count,
                SUM(CASE WHEN allocation_percentage > 85 THEN 1 ELSE 0 END) as overutilized_periods,
                SUM(CASE WHEN allocation_percentage < 50 THEN 1 ELSE 0 END) as underutilized_periods
            FROM resource_allocations
            WHERE start_date <= :end_date AND end_date >= :start_date
            GROUP BY resource_id
        """)

        result = await self.db.execute(
            utilization_query,
            {
                "start_date": start_date,
                "end_date": end_date,
                "resource_ids": resource_ids,
                "department_ids": department_ids,
                "resource_types": resource_types,
            },
        )
        utilization_data = result.fetchall()

        # Get cost data
        cost_query = text("""
            SELECT
                resource_id,
                SUM(allocation_percentage * hourly_rate * capacity / 100 *
                    EXTRACT(DAYS FROM LEAST(end_date, :end_date) - GREATEST(start_date, :start_date)) * 8 / 7) as total_cost,
                AVG(hourly_rate) as avg_hourly_rate,
                COUNT(DISTINCT project_id) as projects_involved
            FROM resource_allocations ra
            JOIN resources r ON ra.resource_id = r.id
            WHERE start_date <= :end_date AND end_date >= :start_date
            GROUP BY resource_id
        """)

        cost_result = await self.db.execute(
            cost_query, {"start_date": start_date, "end_date": end_date}
        )
        cost_data = cost_result.fetchall()

        # Calculate analytics
        total_resources = len(utilization_data)
        avg_utilization = (
            sum(row.avg_utilization for row in utilization_data) / total_resources
            if total_resources > 0
            else 0
        )
        total_cost = sum(row.total_cost for row in cost_data)
        overutilized_resources = sum(
            1 for row in utilization_data if row.avg_utilization > 85
        )
        underutilized_resources = sum(
            1 for row in utilization_data if row.avg_utilization < 50
        )

        # Resource efficiency score
        efficiency_score = self._calculate_efficiency_score(utilization_data, cost_data)

        # Top performers
        top_performers = sorted(
            [
                {
                    "resource_id": row.resource_id,
                    "utilization": row.avg_utilization,
                    "efficiency_score": self._calculate_resource_efficiency(
                        row, cost_data
                    ),
                }
                for row in utilization_data
            ],
            key=lambda x: x["efficiency_score"],
            reverse=True,
        )[:10]

        # Recommendations
        recommendations = self._generate_resource_recommendations(
            utilization_data, cost_data, overutilized_resources, underutilized_resources
        )

        return ResourceAnalyticsResponse(
            period_start=start_date,
            period_end=end_date,
            total_resources=total_resources,
            average_utilization=avg_utilization,
            total_cost=Decimal(str(total_cost)),
            efficiency_score=efficiency_score,
            overutilized_resources=overutilized_resources,
            underutilized_resources=underutilized_resources,
            top_performers=top_performers,
            cost_breakdown=[
                {
                    "resource_id": row.resource_id,
                    "total_cost": Decimal(str(row.total_cost)),
                    "avg_hourly_rate": Decimal(str(row.avg_hourly_rate)),
                    "projects_count": row.projects_involved,
                }
                for row in cost_data
            ],
            recommendations=recommendations,
            generated_at=datetime.utcnow(),
        )

    async def get_resource_trends(
        self,
        resource_ids: List[int],
        start_date: date,
        end_date: date,
        granularity: str = "monthly",
    ) -> ResourceTrendAnalysisResponse:
        """Get resource utilization trends over time"""

        # Cache key
        cache_key = f"trends:{':'.join(map(str, resource_ids))}:{start_date}:{end_date}:{granularity}"
        cached_result = await self.redis.get(cache_key)

        if cached_result:
            return ResourceTrendAnalysisResponse.parse_raw(cached_result)

        # Generate time periods based on granularity
        time_periods = self._generate_time_periods(start_date, end_date, granularity)

        # Get trend data for each period
        trend_data = []
        for period_start, period_end in time_periods:
            period_query = text("""
                SELECT
                    resource_id,
                    AVG(allocation_percentage) as avg_utilization,
                    SUM(allocation_percentage * hourly_rate * capacity / 100 *
                        EXTRACT(DAYS FROM LEAST(end_date, :period_end) - GREATEST(start_date, :period_start)) * 8 / 7) as period_cost,
                    COUNT(DISTINCT project_id) as active_projects
                FROM resource_allocations ra
                JOIN resources r ON ra.resource_id = r.id
                WHERE resource_id = ANY(:resource_ids)
                  AND start_date <= :period_end
                  AND end_date >= :period_start
                GROUP BY resource_id
            """)

            result = await self.db.execute(
                period_query,
                {
                    "resource_ids": resource_ids,
                    "period_start": period_start,
                    "period_end": period_end,
                },
            )

            period_data = result.fetchall()
            trend_data.append(
                {
                    "period_start": period_start,
                    "period_end": period_end,
                    "resources": [
                        {
                            "resource_id": row.resource_id,
                            "utilization": row.avg_utilization,
                            "cost": Decimal(str(row.period_cost)),
                            "active_projects": row.active_projects,
                        }
                        for row in period_data
                    ],
                }
            )

        # Calculate trends
        utilization_trends = self._calculate_utilization_trends(trend_data)
        cost_trends = self._calculate_cost_trends(trend_data)
        forecast = self._generate_trend_forecast(trend_data, 3)  # 3 periods ahead

        response = ResourceTrendAnalysisResponse(
            resource_ids=resource_ids,
            period_start=start_date,
            period_end=end_date,
            granularity=granularity,
            utilization_trends=utilization_trends,
            cost_trends=cost_trends,
            forecast=forecast,
            trend_summary={
                "overall_direction": self._get_trend_direction(utilization_trends),
                "volatility": self._calculate_trend_volatility(utilization_trends),
                "seasonality_detected": self._detect_seasonality(utilization_trends),
            },
            generated_at=datetime.utcnow(),
        )

        # Cache result
        await self.redis.setex(cache_key, 1800, response.json())  # 30 minutes

        return response

    async def get_resource_kpis(
        self, time_range: str = "month", compare_previous: bool = True
    ) -> ResourceKPIResponse:
        """Get key performance indicators for resources"""

        end_date = date.today()

        if time_range == "week":
            start_date = end_date - timedelta(days=7)
            prev_start = start_date - timedelta(days=7)
        elif time_range == "month":
            start_date = end_date.replace(day=1)
            prev_start = (start_date - timedelta(days=1)).replace(day=1)
        elif time_range == "quarter":
            quarter_start_month = ((end_date.month - 1) // 3) * 3 + 1
            start_date = end_date.replace(month=quarter_start_month, day=1)
            prev_start = (start_date - timedelta(days=1)).replace(day=1)
            prev_start = prev_start.replace(month=((prev_start.month - 1) // 3) * 3 + 1)
        else:
            start_date = end_date.replace(month=1, day=1)
            prev_start = start_date.replace(year=start_date.year - 1)

        prev_end = start_date - timedelta(days=1)

        # Current period KPIs
        current_kpis = await self._calculate_period_kpis(start_date, end_date)

        # Previous period KPIs for comparison
        previous_kpis = None
        if compare_previous:
            previous_kpis = await self._calculate_period_kpis(prev_start, prev_end)

        # Calculate changes
        kpi_changes = {}
        if previous_kpis:
            for key in current_kpis:
                if key in previous_kpis and previous_kpis[key] != 0:
                    change = (
                        (current_kpis[key] - previous_kpis[key]) / previous_kpis[key]
                    ) * 100
                    kpi_changes[key] = change
                else:
                    kpi_changes[key] = 0

        return ResourceKPIResponse(
            time_range=time_range,
            period_start=start_date,
            period_end=end_date,
            current_kpis=current_kpis,
            previous_kpis=previous_kpis,
            kpi_changes=kpi_changes,
            performance_indicators=[
                {
                    "indicator": "Resource Utilization",
                    "value": current_kpis.get("avg_utilization", 0),
                    "target": 75.0,
                    "status": "good"
                    if current_kpis.get("avg_utilization", 0) >= 70
                    else "warning",
                },
                {
                    "indicator": "Cost Efficiency",
                    "value": current_kpis.get("cost_per_hour", 0),
                    "target": 100.0,
                    "status": "good"
                    if current_kpis.get("cost_per_hour", 0) <= 100
                    else "warning",
                },
                {
                    "indicator": "Resource Satisfaction",
                    "value": current_kpis.get("satisfaction_score", 0),
                    "target": 80.0,
                    "status": "good"
                    if current_kpis.get("satisfaction_score", 0) >= 80
                    else "warning",
                },
            ],
            generated_at=datetime.utcnow(),
        )

    async def generate_resource_forecast(
        self, forecast_request: ResourceForecastRequest
    ) -> ResourceForecastResponse:
        """Generate resource demand and availability forecast"""

        # Get historical data for forecasting
        historical_data = await self._get_historical_resource_data(
            forecast_request.start_date,
            forecast_request.forecast_periods,
            forecast_request.granularity,
        )

        # Apply forecasting algorithms
        demand_forecast = self._forecast_resource_demand(
            historical_data,
            forecast_request.forecast_periods,
            forecast_request.departments,
            forecast_request.resource_types,
        )

        capacity_forecast = self._forecast_resource_capacity(
            historical_data,
            forecast_request.forecast_periods,
            forecast_request.growth_assumptions,
        )

        # Identify gaps and surpluses
        gaps_and_surpluses = self._identify_capacity_gaps(
            demand_forecast, capacity_forecast
        )

        # Generate recommendations
        recommendations = self._generate_forecast_recommendations(
            gaps_and_surpluses, forecast_request.constraints
        )

        return ResourceForecastResponse(
            forecast_start=forecast_request.end_date,
            forecast_periods=forecast_request.forecast_periods,
            granularity=forecast_request.granularity,
            demand_forecast=demand_forecast,
            capacity_forecast=capacity_forecast,
            gaps_and_surpluses=gaps_and_surpluses,
            recommendations=recommendations,
            confidence_level=self._calculate_forecast_confidence(historical_data),
            methodology="Time series analysis with seasonal adjustments",
            generated_at=datetime.utcnow(),
        )

    async def get_resource_benchmarks(
        self, resource_ids: List[int], benchmark_type: str = "industry"
    ) -> ResourceBenchmarkResponse:
        """Get resource performance benchmarks"""

        # Get resource metrics
        resource_metrics = await self._get_resource_metrics(resource_ids)

        # Get benchmark data (would typically come from external source)
        benchmark_data = await self._get_benchmark_data(benchmark_type)

        # Calculate comparisons
        comparisons = []
        for resource in resource_metrics:
            comparison = {
                "resource_id": resource["resource_id"],
                "metrics": resource["metrics"],
                "benchmark_comparisons": self._compare_to_benchmarks(
                    resource["metrics"], benchmark_data
                ),
                "performance_score": self._calculate_performance_score(
                    resource["metrics"], benchmark_data
                ),
                "improvement_areas": self._identify_improvement_areas(
                    resource["metrics"], benchmark_data
                ),
            }
            comparisons.append(comparison)

        return ResourceBenchmarkResponse(
            benchmark_type=benchmark_type,
            resource_comparisons=comparisons,
            benchmark_data=benchmark_data,
            overall_performance={
                "average_score": sum(c["performance_score"] for c in comparisons)
                / len(comparisons),
                "top_performers": sorted(
                    comparisons, key=lambda x: x["performance_score"], reverse=True
                )[:5],
                "improvement_needed": [
                    c for c in comparisons if c["performance_score"] < 70
                ],
            },
            generated_at=datetime.utcnow(),
        )

    async def analyze_resource_roi(
        self, resource_ids: List[int], start_date: date, end_date: date
    ) -> ResourceROIAnalysisResponse:
        """Analyze return on investment for resources"""

        roi_analyses = []

        for resource_id in resource_ids:
            # Get resource costs
            cost_data = await self._get_resource_costs(
                resource_id, start_date, end_date
            )

            # Get resource value contribution
            value_data = await self._get_resource_value_contribution(
                resource_id, start_date, end_date
            )

            # Calculate ROI metrics
            total_cost = cost_data["total_cost"]
            total_value = value_data["total_value"]
            roi_percentage = (
                ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0
            )

            # Calculate productivity metrics
            productivity_metrics = self._calculate_productivity_metrics(
                cost_data, value_data
            )

            # Value drivers analysis
            value_drivers = self._analyze_value_drivers(value_data)

            roi_analysis = {
                "resource_id": resource_id,
                "period_start": start_date,
                "period_end": end_date,
                "cost_breakdown": cost_data,
                "value_contribution": value_data,
                "roi_percentage": roi_percentage,
                "productivity_metrics": productivity_metrics,
                "value_drivers": value_drivers,
                "performance_rating": self._rate_resource_performance(
                    roi_percentage, productivity_metrics
                ),
            }

            roi_analyses.append(roi_analysis)

        # Overall insights
        overall_roi = sum(
            analysis["roi_percentage"] for analysis in roi_analyses
        ) / len(roi_analyses)

        return ResourceROIAnalysisResponse(
            resource_analyses=roi_analyses,
            overall_roi=overall_roi,
            top_performing_resources=sorted(
                roi_analyses, key=lambda x: x["roi_percentage"], reverse=True
            )[:5],
            underperforming_resources=[
                a for a in roi_analyses if a["roi_percentage"] < 0
            ],
            optimization_opportunities=self._identify_roi_optimization_opportunities(
                roi_analyses
            ),
            investment_recommendations=self._generate_investment_recommendations(
                roi_analyses
            ),
            generated_at=datetime.utcnow(),
        )

    # Helper methods
    def _calculate_efficiency_score(self, utilization_data, cost_data) -> float:
        """Calculate overall resource efficiency score"""
        if not utilization_data or not cost_data:
            return 0.0

        # Combine utilization and cost efficiency
        avg_utilization = sum(row.avg_utilization for row in utilization_data) / len(
            utilization_data
        )
        avg_cost_per_hour = sum(row.avg_hourly_rate for row in cost_data) / len(
            cost_data
        )

        # Normalize and combine (utilization weight: 70%, cost efficiency weight: 30%)
        utilization_score = min(
            avg_utilization / 85 * 100, 100
        )  # 85% utilization = 100 score
        cost_score = max(
            100 - (avg_cost_per_hour - 100) / 2, 0
        )  # Lower cost = higher score

        return utilization_score * 0.7 + cost_score * 0.3

    def _calculate_resource_efficiency(self, utilization_row, cost_data) -> float:
        """Calculate individual resource efficiency"""
        utilization_score = min(utilization_row.avg_utilization / 85 * 100, 100)

        # Find cost data for this resource
        resource_cost = next(
            (
                row
                for row in cost_data
                if row.resource_id == utilization_row.resource_id
            ),
            None,
        )
        if resource_cost:
            cost_score = max(100 - (resource_cost.avg_hourly_rate - 100) / 2, 0)
        else:
            cost_score = 50  # Default if no cost data

        return utilization_score * 0.7 + cost_score * 0.3

    def _generate_resource_recommendations(
        self, utilization_data, cost_data, overutilized, underutilized
    ) -> List[Dict[str, Any]]:
        """Generate resource management recommendations"""
        recommendations = []

        if overutilized > 0:
            recommendations.append(
                {
                    "type": "overutilization",
                    "priority": "high",
                    "message": f"{overutilized} resources are overutilized (>85%). Consider workload redistribution.",
                    "action": "redistribute_workload",
                }
            )

        if underutilized > 0:
            recommendations.append(
                {
                    "type": "underutilization",
                    "priority": "medium",
                    "message": f"{underutilized} resources are underutilized (<50%). Consider additional assignments.",
                    "action": "increase_allocation",
                }
            )

        # High cost resources
        high_cost_resources = [row for row in cost_data if row.avg_hourly_rate > 150]
        if high_cost_resources:
            recommendations.append(
                {
                    "type": "cost_optimization",
                    "priority": "medium",
                    "message": f"{len(high_cost_resources)} resources have high hourly rates. Review cost-effectiveness.",
                    "action": "review_rates",
                }
            )

        return recommendations

    def _generate_time_periods(
        self, start_date: date, end_date: date, granularity: str
    ):
        """Generate time periods for trend analysis"""
        periods = []
        current = start_date

        while current < end_date:
            if granularity == "weekly":
                period_end = min(current + timedelta(days=6), end_date)
            elif granularity == "monthly":
                next_month = current.replace(day=28) + timedelta(days=4)
                period_end = min(
                    next_month.replace(day=1) - timedelta(days=1), end_date
                )
            elif granularity == "quarterly":
                quarter_month = ((current.month - 1) // 3 + 1) * 3
                period_end = min(
                    current.replace(month=quarter_month, day=1) + timedelta(days=90),
                    end_date,
                )
            else:  # daily
                period_end = min(current + timedelta(days=1), end_date)

            periods.append((current, period_end))
            current = period_end + timedelta(days=1)

        return periods

    def _calculate_utilization_trends(self, trend_data) -> List[Dict[str, Any]]:
        """Calculate utilization trends from time series data"""
        trends = []

        for i, period in enumerate(trend_data):
            if i == 0:
                continue

            prev_period = trend_data[i - 1]
            for resource in period["resources"]:
                prev_resource = next(
                    (
                        r
                        for r in prev_period["resources"]
                        if r["resource_id"] == resource["resource_id"]
                    ),
                    None,
                )

                if prev_resource:
                    change = resource["utilization"] - prev_resource["utilization"]
                    trends.append(
                        {
                            "resource_id": resource["resource_id"],
                            "period": period["period_start"],
                            "utilization": resource["utilization"],
                            "change": change,
                            "trend": "increasing"
                            if change > 2
                            else "decreasing"
                            if change < -2
                            else "stable",
                        }
                    )

        return trends

    def _calculate_cost_trends(self, trend_data) -> List[Dict[str, Any]]:
        """Calculate cost trends from time series data"""
        trends = []

        for i, period in enumerate(trend_data):
            if i == 0:
                continue

            prev_period = trend_data[i - 1]
            for resource in period["resources"]:
                prev_resource = next(
                    (
                        r
                        for r in prev_period["resources"]
                        if r["resource_id"] == resource["resource_id"]
                    ),
                    None,
                )

                if prev_resource and prev_resource["cost"] > 0:
                    change_pct = (
                        (resource["cost"] - prev_resource["cost"])
                        / prev_resource["cost"]
                    ) * 100
                    trends.append(
                        {
                            "resource_id": resource["resource_id"],
                            "period": period["period_start"],
                            "cost": resource["cost"],
                            "change_percentage": change_pct,
                            "trend": "increasing"
                            if change_pct > 5
                            else "decreasing"
                            if change_pct < -5
                            else "stable",
                        }
                    )

        return trends

    def _generate_trend_forecast(
        self, trend_data, periods_ahead: int
    ) -> List[Dict[str, Any]]:
        """Generate forecast based on historical trends"""
        if len(trend_data) < 3:
            return []

        # Simple linear forecast for demo
        forecasts = []
        last_period = trend_data[-1]

        for resource in last_period["resources"]:
            # Calculate average change over last 3 periods
            recent_data = [
                next(
                    (
                        r
                        for r in period["resources"]
                        if r["resource_id"] == resource["resource_id"]
                    ),
                    None,
                )
                for period in trend_data[-3:]
            ]
            recent_data = [r for r in recent_data if r is not None]

            if len(recent_data) >= 2:
                utilization_changes = [
                    recent_data[i]["utilization"] - recent_data[i - 1]["utilization"]
                    for i in range(1, len(recent_data))
                ]
                avg_change = sum(utilization_changes) / len(utilization_changes)

                for i in range(1, periods_ahead + 1):
                    forecasts.append(
                        {
                            "resource_id": resource["resource_id"],
                            "period_ahead": i,
                            "predicted_utilization": max(
                                0, min(100, resource["utilization"] + avg_change * i)
                            ),
                            "confidence": max(
                                0.3, 0.9 - i * 0.1
                            ),  # Decreasing confidence
                        }
                    )

        return forecasts

    def _get_trend_direction(self, trends) -> str:
        """Determine overall trend direction"""
        if not trends:
            return "stable"

        increasing = sum(1 for t in trends if t["trend"] == "increasing")
        decreasing = sum(1 for t in trends if t["trend"] == "decreasing")

        if increasing > decreasing * 1.2:
            return "increasing"
        elif decreasing > increasing * 1.2:
            return "decreasing"
        else:
            return "stable"

    def _calculate_trend_volatility(self, trends) -> float:
        """Calculate trend volatility"""
        if not trends:
            return 0.0

        changes = [abs(t["change"]) for t in trends]
        return sum(changes) / len(changes)

    def _detect_seasonality(self, trends) -> bool:
        """Detect seasonal patterns in trends"""
        # Simple seasonality detection - would need more sophisticated analysis in practice
        if len(trends) < 12:  # Need at least a year of data
            return False

        # Look for patterns that repeat every 3-4 periods
        return len(set(t["trend"] for t in trends)) > 1

    async def _calculate_period_kpis(
        self, start_date: date, end_date: date
    ) -> Dict[str, float]:
        """Calculate KPIs for a specific period"""

        # Mock KPI calculations - would use actual database queries
        kpis = {
            "total_resources": 150.0,
            "avg_utilization": 78.5,
            "total_cost": 2450000.0,
            "cost_per_hour": 95.50,
            "active_projects": 45.0,
            "completed_projects": 12.0,
            "satisfaction_score": 82.3,
            "efficiency_score": 85.7,
        }

        return kpis

    # Additional helper methods would be implemented here...
    async def _get_historical_resource_data(self, start_date, periods, granularity):
        """Get historical resource data for forecasting"""
        return {}  # Mock implementation

    def _forecast_resource_demand(
        self, historical_data, periods, departments, resource_types
    ):
        """Forecast resource demand"""
        return []  # Mock implementation

    def _forecast_resource_capacity(self, historical_data, periods, growth_assumptions):
        """Forecast resource capacity"""
        return []  # Mock implementation

    def _identify_capacity_gaps(self, demand_forecast, capacity_forecast):
        """Identify capacity gaps and surpluses"""
        return []  # Mock implementation

    def _generate_forecast_recommendations(self, gaps_and_surpluses, constraints):
        """Generate forecast-based recommendations"""
        return []  # Mock implementation

    def _calculate_forecast_confidence(self, historical_data):
        """Calculate forecast confidence level"""
        return 0.75  # Mock implementation

    async def _get_resource_metrics(self, resource_ids):
        """Get detailed resource metrics"""
        return []  # Mock implementation

    async def _get_benchmark_data(self, benchmark_type):
        """Get benchmark data"""
        return {}  # Mock implementation

    def _compare_to_benchmarks(self, metrics, benchmark_data):
        """Compare metrics to benchmarks"""
        return {}  # Mock implementation

    def _calculate_performance_score(self, metrics, benchmark_data):
        """Calculate performance score"""
        return 75.0  # Mock implementation

    def _identify_improvement_areas(self, metrics, benchmark_data):
        """Identify areas for improvement"""
        return []  # Mock implementation

    async def _get_resource_costs(self, resource_id, start_date, end_date):
        """Get resource costs"""
        return {"total_cost": 50000.0}  # Mock implementation

    async def _get_resource_value_contribution(self, resource_id, start_date, end_date):
        """Get resource value contribution"""
        return {"total_value": 75000.0}  # Mock implementation

    def _calculate_productivity_metrics(self, cost_data, value_data):
        """Calculate productivity metrics"""
        return {}  # Mock implementation

    def _analyze_value_drivers(self, value_data):
        """Analyze value drivers"""
        return []  # Mock implementation

    def _rate_resource_performance(self, roi_percentage, productivity_metrics):
        """Rate resource performance"""
        return "good"  # Mock implementation

    def _identify_roi_optimization_opportunities(self, roi_analyses):
        """Identify ROI optimization opportunities"""
        return []  # Mock implementation

    def _generate_investment_recommendations(self, roi_analyses):
        """Generate investment recommendations"""
        return []  # Mock implementation


# Mock authentication dependency
async def get_current_user():
    return {"id": 1, "username": "admin"}


@router.get("/analytics", response_model=ResourceAnalyticsResponse)
async def get_resource_analytics(
    start_date: date = Query(..., description="Analytics start date"),
    end_date: date = Query(..., description="Analytics end date"),
    resource_ids: Optional[str] = Query(
        None, description="Comma-separated resource IDs"
    ),
    department_ids: Optional[str] = Query(
        None, description="Comma-separated department IDs"
    ),
    resource_types: Optional[str] = Query(
        None, description="Comma-separated resource types"
    ),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get comprehensive resource analytics"""

    # Parse comma-separated values
    resource_id_list = (
        [int(x.strip()) for x in resource_ids.split(",")] if resource_ids else None
    )
    department_id_list = (
        [int(x.strip()) for x in department_ids.split(",")] if department_ids else None
    )
    resource_type_list = (
        [x.strip() for x in resource_types.split(",")] if resource_types else None
    )

    redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=False)
    service = ResourceAnalyticsService(db, redis_client)

    return await service.get_resource_analytics(
        start_date=start_date,
        end_date=end_date,
        resource_ids=resource_id_list,
        department_ids=department_id_list,
        resource_types=resource_type_list,
    )


@router.get("/trends", response_model=ResourceTrendAnalysisResponse)
async def get_resource_trends(
    resource_ids: str = Query(..., description="Comma-separated resource IDs"),
    start_date: date = Query(..., description="Trend analysis start date"),
    end_date: date = Query(..., description="Trend analysis end date"),
    granularity: str = Query(
        "monthly", description="Granularity: daily, weekly, monthly, quarterly"
    ),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get resource utilization trends"""

    resource_id_list = [int(x.strip()) for x in resource_ids.split(",")]

    redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=False)
    service = ResourceAnalyticsService(db, redis_client)

    return await service.get_resource_trends(
        resource_ids=resource_id_list,
        start_date=start_date,
        end_date=end_date,
        granularity=granularity,
    )


@router.get("/kpis", response_model=ResourceKPIResponse)
async def get_resource_kpis(
    time_range: str = Query(
        "month", description="Time range: week, month, quarter, year"
    ),
    compare_previous: bool = Query(True, description="Compare with previous period"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get resource key performance indicators"""

    redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=False)
    service = ResourceAnalyticsService(db, redis_client)

    return await service.get_resource_kpis(
        time_range=time_range, compare_previous=compare_previous
    )


@router.post("/forecast", response_model=ResourceForecastResponse)
async def generate_resource_forecast(
    forecast_request: ResourceForecastRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate resource demand and capacity forecast"""

    redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=False)
    service = ResourceAnalyticsService(db, redis_client)

    return await service.generate_resource_forecast(forecast_request)


@router.get("/benchmarks", response_model=ResourceBenchmarkResponse)
async def get_resource_benchmarks(
    resource_ids: str = Query(..., description="Comma-separated resource IDs"),
    benchmark_type: str = Query(
        "industry", description="Benchmark type: industry, company, team"
    ),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get resource performance benchmarks"""

    resource_id_list = [int(x.strip()) for x in resource_ids.split(",")]

    redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=False)
    service = ResourceAnalyticsService(db, redis_client)

    return await service.get_resource_benchmarks(
        resource_ids=resource_id_list, benchmark_type=benchmark_type
    )


@router.get("/roi-analysis", response_model=ResourceROIAnalysisResponse)
async def analyze_resource_roi(
    resource_ids: str = Query(..., description="Comma-separated resource IDs"),
    start_date: date = Query(..., description="Analysis start date"),
    end_date: date = Query(..., description="Analysis end date"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Analyze return on investment for resources"""

    resource_id_list = [int(x.strip()) for x in resource_ids.split(",")]

    redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=False)
    service = ResourceAnalyticsService(db, redis_client)

    return await service.analyze_resource_roi(
        resource_ids=resource_id_list, start_date=start_date, end_date=end_date
    )


@router.get("/health")
async def health_check():
    """Health check for resource analytics API"""
    return {
        "status": "healthy",
        "service": "resource_analytics",
        "timestamp": datetime.utcnow(),
    }
