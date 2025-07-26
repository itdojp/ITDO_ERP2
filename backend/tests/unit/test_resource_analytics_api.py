"""
ITDO ERP Backend - Resource Analytics API Unit Tests
Day 22: Comprehensive unit tests for resource analytics functionality
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.api.v1.resource_analytics_api import ResourceAnalyticsService
from app.schemas.resource import (
    ResourceAnalyticsResponse,
    ResourceBenchmarkResponse,
    ResourceForecastRequest,
    ResourceForecastResponse,
    ResourceKPIResponse,
    ResourceROIAnalysisResponse,
    ResourceTrendAnalysisResponse,
)


class TestResourceAnalyticsService:
    """Unit tests for ResourceAnalyticsService"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return AsyncMock()

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        return AsyncMock()

    @pytest.fixture
    def analytics_service(self, mock_db, mock_redis):
        """ResourceAnalyticsService instance with mocked dependencies"""
        return ResourceAnalyticsService(mock_db, mock_redis)

    @pytest.fixture
    def sample_utilization_data(self):
        """Sample utilization data for testing"""
        return [
            Mock(
                resource_id=1,
                avg_utilization=75.5,
                peak_utilization=95.0,
                min_utilization=45.0,
                allocation_count=3,
                overutilized_periods=1,
                underutilized_periods=0,
            ),
            Mock(
                resource_id=2,
                avg_utilization=85.2,
                peak_utilization=100.0,
                min_utilization=60.0,
                allocation_count=4,
                overutilized_periods=2,
                underutilized_periods=0,
            ),
            Mock(
                resource_id=3,
                avg_utilization=42.8,
                peak_utilization=75.0,
                min_utilization=20.0,
                allocation_count=2,
                overutilized_periods=0,
                underutilized_periods=1,
            ),
        ]

    @pytest.fixture
    def sample_cost_data(self):
        """Sample cost data for testing"""
        return [
            Mock(
                resource_id=1,
                total_cost=48000.0,
                avg_hourly_rate=150.0,
                projects_involved=2,
            ),
            Mock(
                resource_id=2,
                total_cost=38400.0,
                avg_hourly_rate=120.0,
                projects_involved=3,
            ),
            Mock(
                resource_id=3,
                total_cost=28800.0,
                avg_hourly_rate=90.0,
                projects_involved=1,
            ),
        ]

    @pytest.mark.asyncio
    async def test_get_resource_analytics_basic(
        self, analytics_service, sample_utilization_data, sample_cost_data
    ):
        """Test basic resource analytics retrieval"""

        # Mock database queries
        analytics_service.db.execute.side_effect = [
            Mock(fetchall=Mock(return_value=sample_utilization_data)),
            Mock(fetchall=Mock(return_value=sample_cost_data)),
        ]

        # Test parameters
        start_date = date(2025, 8, 1)
        end_date = date(2025, 8, 31)

        # Execute
        result = await analytics_service.get_resource_analytics(
            start_date=start_date, end_date=end_date
        )

        # Verify response structure
        assert isinstance(result, ResourceAnalyticsResponse)
        assert result.period_start == start_date
        assert result.period_end == end_date
        assert result.total_resources == 3
        assert result.average_utilization == pytest.approx(67.83, rel=1e-2)
        assert result.total_cost == Decimal("115200.0")
        assert result.overutilized_resources == 1
        assert result.underutilized_resources == 1
        assert len(result.top_performers) > 0
        assert len(result.cost_breakdown) == 3
        assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_get_resource_analytics_with_filters(
        self, analytics_service, sample_utilization_data, sample_cost_data
    ):
        """Test resource analytics with filters"""

        # Mock database queries
        analytics_service.db.execute.side_effect = [
            Mock(fetchall=Mock(return_value=sample_utilization_data[:2])),
            Mock(fetchall=Mock(return_value=sample_cost_data[:2])),
        ]

        # Test with filters
        result = await analytics_service.get_resource_analytics(
            start_date=date(2025, 8, 1),
            end_date=date(2025, 8, 31),
            resource_ids=[1, 2],
            department_ids=[1],
            resource_types=["human"],
        )

        # Verify filtered results
        assert result.total_resources == 2
        assert len(result.cost_breakdown) == 2

        # Verify database was called with filters
        assert analytics_service.db.execute.call_count == 2
        call_args = analytics_service.db.execute.call_args_list[0][0]
        assert "resource_ids" in call_args[1]
        assert "department_ids" in call_args[1]
        assert "resource_types" in call_args[1]

    @pytest.mark.asyncio
    async def test_get_resource_trends_with_caching(self, analytics_service):
        """Test resource trends with Redis caching"""

        # Mock cached data
        cached_response = ResourceTrendAnalysisResponse(
            resource_ids=[1, 2],
            period_start=date(2025, 7, 1),
            period_end=date(2025, 8, 31),
            granularity="monthly",
            utilization_trends=[],
            cost_trends=[],
            forecast=[],
            trend_summary={},
            generated_at=datetime.utcnow(),
        )

        analytics_service.redis.get.return_value = cached_response.json()

        # Execute
        result = await analytics_service.get_resource_trends(
            resource_ids=[1, 2],
            start_date=date(2025, 7, 1),
            end_date=date(2025, 8, 31),
            granularity="monthly",
        )

        # Verify cache hit
        assert isinstance(result, ResourceTrendAnalysisResponse)
        assert result.resource_ids == [1, 2]
        analytics_service.redis.get.assert_called_once()
        analytics_service.db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_resource_trends_cache_miss(self, analytics_service):
        """Test resource trends when cache miss occurs"""

        # Mock cache miss
        analytics_service.redis.get.return_value = None

        # Mock database responses for trend periods
        mock_period_data = [
            Mock(
                resource_id=1,
                avg_utilization=75.0,
                period_cost=12000.0,
                active_projects=2,
            ),
            Mock(
                resource_id=2,
                avg_utilization=80.0,
                period_cost=9600.0,
                active_projects=1,
            ),
        ]
        analytics_service.db.execute.return_value = Mock(
            fetchall=Mock(return_value=mock_period_data)
        )

        # Mock time period generation
        with patch.object(analytics_service, "_generate_time_periods") as mock_periods:
            mock_periods.return_value = [
                (date(2025, 8, 1), date(2025, 8, 31)),
                (date(2025, 9, 1), date(2025, 9, 30)),
            ]

            # Execute
            result = await analytics_service.get_resource_trends(
                resource_ids=[1, 2],
                start_date=date(2025, 8, 1),
                end_date=date(2025, 9, 30),
                granularity="monthly",
            )

        # Verify cache miss handling
        assert isinstance(result, ResourceTrendAnalysisResponse)
        assert result.resource_ids == [1, 2]
        assert result.granularity == "monthly"

        # Verify cache was set
        analytics_service.redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_resource_kpis_current_period(self, analytics_service):
        """Test KPI calculation for current period"""

        # Mock KPI calculation
        mock_kpis = {
            "total_resources": 25.0,
            "avg_utilization": 78.5,
            "total_cost": 245000.0,
            "cost_per_hour": 95.50,
            "active_projects": 12.0,
            "completed_projects": 5.0,
            "satisfaction_score": 82.3,
            "efficiency_score": 85.7,
        }

        with patch.object(analytics_service, "_calculate_period_kpis") as mock_calc:
            mock_calc.return_value = mock_kpis

            # Execute
            result = await analytics_service.get_resource_kpis(
                time_range="month", compare_previous=False
            )

        # Verify KPI response
        assert isinstance(result, ResourceKPIResponse)
        assert result.time_range == "month"
        assert result.current_kpis == mock_kpis
        assert result.previous_kpis is None
        assert len(result.performance_indicators) >= 3

    @pytest.mark.asyncio
    async def test_get_resource_kpis_with_comparison(self, analytics_service):
        """Test KPI calculation with previous period comparison"""

        current_kpis = {
            "avg_utilization": 78.5,
            "cost_per_hour": 95.50,
            "efficiency_score": 85.7,
        }

        previous_kpis = {
            "avg_utilization": 75.0,
            "cost_per_hour": 100.0,
            "efficiency_score": 82.0,
        }

        with patch.object(analytics_service, "_calculate_period_kpis") as mock_calc:
            mock_calc.side_effect = [current_kpis, previous_kpis]

            # Execute
            result = await analytics_service.get_resource_kpis(
                time_range="month", compare_previous=True
            )

        # Verify comparison calculations
        assert result.current_kpis == current_kpis
        assert result.previous_kpis == previous_kpis
        assert result.kpi_changes["avg_utilization"] == pytest.approx(
            4.67, rel=1e-2
        )  # (78.5-75)/75*100
        assert result.kpi_changes["cost_per_hour"] == pytest.approx(
            -4.5, rel=1e-2
        )  # (95.5-100)/100*100

    @pytest.mark.asyncio
    async def test_generate_resource_forecast(self, analytics_service):
        """Test resource demand and capacity forecasting"""

        forecast_request = ResourceForecastRequest(
            start_date=date(2025, 8, 1),
            end_date=date(2025, 10, 31),
            forecast_periods=3,
            granularity="monthly",
            departments=[1, 2],
            resource_types=["human"],
            growth_assumptions={"demand_growth": 0.05},
            constraints={"max_capacity": 1000},
        )

        # Mock forecast methods
        mock_historical = {"months": 12, "utilization_avg": 75.0}
        mock_demand = [{"period": 1, "demand": 800}]
        mock_capacity = [{"period": 1, "capacity": 900}]
        mock_gaps = [{"period": 1, "gap": -100, "type": "surplus"}]
        mock_recommendations = [{"action": "reduce_capacity", "impact": "medium"}]

        with (
            patch.object(
                analytics_service, "_get_historical_resource_data"
            ) as mock_hist,
            patch.object(
                analytics_service, "_forecast_resource_demand"
            ) as mock_demand_fc,
            patch.object(
                analytics_service, "_forecast_resource_capacity"
            ) as mock_capacity_fc,
            patch.object(analytics_service, "_identify_capacity_gaps") as mock_gaps_fc,
            patch.object(
                analytics_service, "_generate_forecast_recommendations"
            ) as mock_rec_fc,
            patch.object(
                analytics_service, "_calculate_forecast_confidence"
            ) as mock_conf,
        ):
            mock_hist.return_value = mock_historical
            mock_demand_fc.return_value = mock_demand
            mock_capacity_fc.return_value = mock_capacity
            mock_gaps_fc.return_value = mock_gaps
            mock_rec_fc.return_value = mock_recommendations
            mock_conf.return_value = 0.85

            # Execute
            result = await analytics_service.generate_resource_forecast(
                forecast_request
            )

        # Verify forecast response
        assert isinstance(result, ResourceForecastResponse)
        assert result.forecast_periods == 3
        assert result.granularity == "monthly"
        assert result.demand_forecast == mock_demand
        assert result.capacity_forecast == mock_capacity
        assert result.gaps_and_surpluses == mock_gaps
        assert result.recommendations == mock_recommendations
        assert result.confidence_level == 0.85
        assert result.methodology is not None

    @pytest.mark.asyncio
    async def test_get_resource_benchmarks(self, analytics_service):
        """Test resource performance benchmarking"""

        resource_ids = [1, 2, 3]
        benchmark_type = "industry"

        # Mock benchmark data
        mock_resource_metrics = [
            {"resource_id": 1, "metrics": {"utilization": 85.0, "productivity": 92.0}},
            {"resource_id": 2, "metrics": {"utilization": 78.0, "productivity": 88.0}},
            {"resource_id": 3, "metrics": {"utilization": 65.0, "productivity": 75.0}},
        ]

        mock_benchmark_data = {
            "industry_avg_utilization": 75.0,
            "industry_avg_productivity": 80.0,
            "percentiles": {"50th": 75.0, "75th": 85.0, "90th": 95.0},
        }

        with (
            patch.object(analytics_service, "_get_resource_metrics") as mock_metrics,
            patch.object(analytics_service, "_get_benchmark_data") as mock_bench,
            patch.object(analytics_service, "_compare_to_benchmarks") as mock_compare,
            patch.object(
                analytics_service, "_calculate_performance_score"
            ) as mock_score,
            patch.object(
                analytics_service, "_identify_improvement_areas"
            ) as mock_improve,
        ):
            mock_metrics.return_value = mock_resource_metrics
            mock_bench.return_value = mock_benchmark_data
            mock_compare.return_value = {"utilization_vs_avg": 10.0}
            mock_score.return_value = 88.5
            mock_improve.return_value = ["time_management"]

            # Execute
            result = await analytics_service.get_resource_benchmarks(
                resource_ids=resource_ids, benchmark_type=benchmark_type
            )

        # Verify benchmark response
        assert isinstance(result, ResourceBenchmarkResponse)
        assert result.benchmark_type == benchmark_type
        assert len(result.resource_comparisons) == 3
        assert result.benchmark_data == mock_benchmark_data
        assert "average_score" in result.overall_performance
        assert "top_performers" in result.overall_performance

    @pytest.mark.asyncio
    async def test_analyze_resource_roi(self, analytics_service):
        """Test ROI analysis for resources"""

        resource_ids = [1, 2]
        start_date = date(2025, 8, 1)
        end_date = date(2025, 8, 31)

        # Mock ROI data
        mock_cost_data = {"total_cost": 25000.0, "hourly_cost": 150.0}
        mock_value_data = {"total_value": 35000.0, "project_value": 30000.0}

        with (
            patch.object(analytics_service, "_get_resource_costs") as mock_costs,
            patch.object(
                analytics_service, "_get_resource_value_contribution"
            ) as mock_value,
            patch.object(
                analytics_service, "_calculate_productivity_metrics"
            ) as mock_prod,
            patch.object(analytics_service, "_analyze_value_drivers") as mock_drivers,
            patch.object(
                analytics_service, "_rate_resource_performance"
            ) as mock_rating,
            patch.object(
                analytics_service, "_identify_roi_optimization_opportunities"
            ) as mock_opt,
            patch.object(
                analytics_service, "_generate_investment_recommendations"
            ) as mock_invest,
        ):
            mock_costs.return_value = mock_cost_data
            mock_value.return_value = mock_value_data
            mock_prod.return_value = {"productivity_score": 92.0}
            mock_drivers.return_value = [
                {"driver": "project_completion", "impact": 0.7}
            ]
            mock_rating.return_value = "excellent"
            mock_opt.return_value = [
                {"opportunity": "increase_allocation", "potential": 0.15}
            ]
            mock_invest.return_value = [
                {"recommendation": "training_investment", "roi": 1.8}
            ]

            # Execute
            result = await analytics_service.analyze_resource_roi(
                resource_ids=resource_ids, start_date=start_date, end_date=end_date
            )

        # Verify ROI analysis
        assert isinstance(result, ResourceROIAnalysisResponse)
        assert len(result.resource_analyses) == 2

        # Check first resource analysis
        first_analysis = result.resource_analyses[0]
        assert first_analysis["resource_id"] == 1
        assert first_analysis["roi_percentage"] == 40.0  # (35000-25000)/25000*100
        assert first_analysis["performance_rating"] == "excellent"

        assert result.overall_roi > 0
        assert len(result.top_performing_resources) > 0
        assert len(result.optimization_opportunities) > 0
        assert len(result.investment_recommendations) > 0

    def test_calculate_efficiency_score(self, analytics_service):
        """Test efficiency score calculation"""

        utilization_data = [
            Mock(avg_utilization=75.0),
            Mock(avg_utilization=85.0),
            Mock(avg_utilization=65.0),
        ]

        cost_data = [
            Mock(avg_hourly_rate=120.0),
            Mock(avg_hourly_rate=100.0),
            Mock(avg_hourly_rate=90.0),
        ]

        # Execute
        score = analytics_service._calculate_efficiency_score(
            utilization_data, cost_data
        )

        # Verify calculation
        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert score > 0  # Should have positive efficiency

    def test_calculate_resource_efficiency(self, analytics_service):
        """Test individual resource efficiency calculation"""

        utilization_row = Mock(resource_id=1, avg_utilization=80.0)
        cost_data = [
            Mock(resource_id=1, avg_hourly_rate=150.0),
            Mock(resource_id=2, avg_hourly_rate=120.0),
        ]

        # Execute
        efficiency = analytics_service._calculate_resource_efficiency(
            utilization_row, cost_data
        )

        # Verify calculation
        assert isinstance(efficiency, float)
        assert 0 <= efficiency <= 100

    def test_generate_resource_recommendations(self, analytics_service):
        """Test resource management recommendations generation"""

        utilization_data = [Mock(avg_utilization=95.0), Mock(avg_utilization=45.0)]
        cost_data = [Mock(avg_hourly_rate=180.0), Mock(avg_hourly_rate=120.0)]
        overutilized = 1
        underutilized = 1

        # Execute
        recommendations = analytics_service._generate_resource_recommendations(
            utilization_data, cost_data, overutilized, underutilized
        )

        # Verify recommendations
        assert isinstance(recommendations, list)
        assert (
            len(recommendations) >= 2
        )  # Should have overutilization and underutilization recommendations

        # Check recommendation structure
        for rec in recommendations:
            assert "type" in rec
            assert "priority" in rec
            assert "message" in rec
            assert "action" in rec

    def test_generate_time_periods_monthly(self, analytics_service):
        """Test time period generation for monthly granularity"""

        start_date = date(2025, 8, 1)
        end_date = date(2025, 10, 31)
        granularity = "monthly"

        # Execute
        periods = analytics_service._generate_time_periods(
            start_date, end_date, granularity
        )

        # Verify periods
        assert isinstance(periods, list)
        assert len(periods) == 3  # August, September, October

        # Check period structure
        for start, end in periods:
            assert isinstance(start, date)
            assert isinstance(end, date)
            assert start <= end

    def test_generate_time_periods_weekly(self, analytics_service):
        """Test time period generation for weekly granularity"""

        start_date = date(2025, 8, 1)
        end_date = date(2025, 8, 21)  # 3 weeks
        granularity = "weekly"

        # Execute
        periods = analytics_service._generate_time_periods(
            start_date, end_date, granularity
        )

        # Verify periods
        assert isinstance(periods, list)
        assert len(periods) == 3

        # Check each period is approximately 7 days
        for start, end in periods:
            duration = (end - start).days
            assert 6 <= duration <= 7  # Account for partial weeks

    def test_calculate_utilization_trends(self, analytics_service):
        """Test utilization trend calculation"""

        trend_data = [
            {
                "period_start": date(2025, 8, 1),
                "resources": [
                    {"resource_id": 1, "utilization": 75.0},
                    {"resource_id": 2, "utilization": 80.0},
                ],
            },
            {
                "period_start": date(2025, 9, 1),
                "resources": [
                    {"resource_id": 1, "utilization": 80.0},
                    {"resource_id": 2, "utilization": 75.0},
                ],
            },
        ]

        # Execute
        trends = analytics_service._calculate_utilization_trends(trend_data)

        # Verify trends
        assert isinstance(trends, list)
        assert len(trends) == 2  # One trend per resource

        # Check trend structure
        for trend in trends:
            assert "resource_id" in trend
            assert "period" in trend
            assert "utilization" in trend
            assert "change" in trend
            assert "trend" in trend
            assert trend["trend"] in ["increasing", "decreasing", "stable"]

    def test_get_trend_direction(self, analytics_service):
        """Test overall trend direction calculation"""

        trends = [
            {"trend": "increasing"},
            {"trend": "increasing"},
            {"trend": "stable"},
            {"trend": "decreasing"},
        ]

        # Execute
        direction = analytics_service._get_trend_direction(trends)

        # Verify direction
        assert direction in ["increasing", "decreasing", "stable"]
        assert direction == "increasing"  # 2 increasing vs 1 decreasing

    def test_calculate_trend_volatility(self, analytics_service):
        """Test trend volatility calculation"""

        trends = [{"change": 5.0}, {"change": -3.0}, {"change": 8.0}, {"change": -2.0}]

        # Execute
        volatility = analytics_service._calculate_trend_volatility(trends)

        # Verify volatility
        assert isinstance(volatility, float)
        assert volatility >= 0
        assert volatility == 4.5  # (5+3+8+2)/4

    def test_detect_seasonality(self, analytics_service):
        """Test seasonality detection"""

        # Test with insufficient data
        short_trends = [{"trend": "increasing"}] * 5
        assert analytics_service._detect_seasonality(short_trends) is False

        # Test with sufficient varied data
        long_trends = [
            {"trend": "increasing"},
            {"trend": "decreasing"},
            {"trend": "stable"},
            {"trend": "increasing"},
        ] * 4  # 16 periods
        assert analytics_service._detect_seasonality(long_trends) is True

    @pytest.mark.asyncio
    async def test_calculate_period_kpis(self, analytics_service):
        """Test period KPI calculation"""

        start_date = date(2025, 8, 1)
        end_date = date(2025, 8, 31)

        # Execute
        kpis = await analytics_service._calculate_period_kpis(start_date, end_date)

        # Verify KPIs
        assert isinstance(kpis, dict)
        required_kpis = [
            "total_resources",
            "avg_utilization",
            "total_cost",
            "cost_per_hour",
            "active_projects",
            "completed_projects",
            "satisfaction_score",
            "efficiency_score",
        ]

        for kpi in required_kpis:
            assert kpi in kpis
            assert isinstance(kpis[kpi], (int, float))
            assert kpis[kpi] >= 0

    @pytest.mark.asyncio
    async def test_error_handling_database_failure(self, analytics_service):
        """Test error handling when database queries fail"""

        # Mock database failure
        analytics_service.db.execute.side_effect = Exception(
            "Database connection failed"
        )

        # Execute and expect exception
        with pytest.raises(Exception) as exc_info:
            await analytics_service.get_resource_analytics(
                start_date=date(2025, 8, 1), end_date=date(2025, 8, 31)
            )

        assert "Database connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_error_handling_empty_data(self, analytics_service):
        """Test handling of empty data sets"""

        # Mock empty data
        analytics_service.db.execute.side_effect = [
            Mock(fetchall=Mock(return_value=[])),
            Mock(fetchall=Mock(return_value=[])),
        ]

        # Execute
        result = await analytics_service.get_resource_analytics(
            start_date=date(2025, 8, 1), end_date=date(2025, 8, 31)
        )

        # Verify graceful handling
        assert result.total_resources == 0
        assert result.average_utilization == 0
        assert result.total_cost == Decimal("0")
        assert result.efficiency_score == 0.0
        assert len(result.top_performers) == 0
        assert len(result.cost_breakdown) == 0

    @pytest.mark.asyncio
    async def test_redis_connection_failure(self, analytics_service):
        """Test handling of Redis connection failures"""

        # Mock Redis failure for caching
        analytics_service.redis.get.side_effect = Exception("Redis connection failed")
        analytics_service.redis.setex.side_effect = Exception("Redis connection failed")

        # Mock database data
        mock_period_data = [
            Mock(
                resource_id=1,
                avg_utilization=75.0,
                period_cost=12000.0,
                active_projects=2,
            )
        ]
        analytics_service.db.execute.return_value = Mock(
            fetchall=Mock(return_value=mock_period_data)
        )

        with patch.object(analytics_service, "_generate_time_periods") as mock_periods:
            mock_periods.return_value = [(date(2025, 8, 1), date(2025, 8, 31))]

            # Should still work without caching
            result = await analytics_service.get_resource_trends(
                resource_ids=[1],
                start_date=date(2025, 8, 1),
                end_date=date(2025, 8, 31),
            )

        # Verify it still returns valid data
        assert isinstance(result, ResourceTrendAnalysisResponse)
        assert result.resource_ids == [1]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--asyncio-mode=auto"])
