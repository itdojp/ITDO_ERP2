"""
ITDO ERP Backend - Resource Analytics & Planning Integration Tests
Day 22: Integration tests for resource analytics and planning API interaction
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.api.v1.resource_analytics_api import ResourceAnalyticsService
from app.api.v1.resource_planning_api import ResourcePlanningService
from app.schemas.resource import (
    ResourceBudgetPlanRequest,
    ResourceBudgetPlanResponse,
    ResourceForecastRequest,
    ResourcePlanningRequest,
    ResourcePlanningResponse,
    SkillGapAnalysisRequest,
    SkillGapAnalysisResponse,
)


class TestResourceAnalyticsPlanningIntegration:
    """Integration tests for analytics and planning services working together"""

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
        """ResourceAnalyticsService instance"""
        return ResourceAnalyticsService(mock_db, mock_redis)

    @pytest.fixture
    def planning_service(self, mock_db, mock_redis):
        """ResourcePlanningService instance"""
        return ResourcePlanningService(mock_db, mock_redis)

    @pytest.fixture
    def sample_analytics_data(self):
        """Sample analytics data for integration testing"""
        return {
            "utilization_data": [
                Mock(
                    resource_id=1,
                    avg_utilization=85.0,
                    peak_utilization=95.0,
                    min_utilization=65.0,
                ),
                Mock(
                    resource_id=2,
                    avg_utilization=75.0,
                    peak_utilization=90.0,
                    min_utilization=55.0,
                ),
                Mock(
                    resource_id=3,
                    avg_utilization=45.0,
                    peak_utilization=70.0,
                    min_utilization=25.0,
                ),
            ],
            "cost_data": [
                Mock(
                    resource_id=1,
                    total_cost=48000.0,
                    avg_hourly_rate=150.0,
                    projects_involved=3,
                ),
                Mock(
                    resource_id=2,
                    total_cost=36000.0,
                    avg_hourly_rate=120.0,
                    projects_involved=2,
                ),
                Mock(
                    resource_id=3,
                    total_cost=21600.0,
                    avg_hourly_rate=90.0,
                    projects_involved=1,
                ),
            ],
        }

    @pytest.mark.asyncio
    async def test_analytics_driven_resource_planning(
        self, analytics_service, planning_service, sample_analytics_data
    ):
        """Test resource planning based on analytics insights"""

        # Step 1: Get current resource analytics
        analytics_service.db.execute.side_effect = [
            Mock(fetchall=Mock(return_value=sample_analytics_data["utilization_data"])),
            Mock(fetchall=Mock(return_value=sample_analytics_data["cost_data"])),
        ]

        analytics_result = await analytics_service.get_resource_analytics(
            start_date=date(2025, 7, 1), end_date=date(2025, 7, 31)
        )

        # Step 2: Use analytics data to inform planning
        planning_request = ResourcePlanningRequest(
            plan_name="Analytics-Driven Resource Plan",
            planning_horizon={
                "start_date": date(2025, 8, 1),
                "end_date": date(2025, 12, 31),
            },
            departments=[1, 2],
            project_requirements=[
                {
                    "project_id": 1,
                    "required_hours": 800,
                    "skills": ["Python", "FastAPI"],
                    "priority": "high",
                }
            ],
            required_skills=["Python", "FastAPI", "React"],
            growth_targets={"utilization_improvement": 0.1},  # Based on analytics
            budget_constraints={"total_budget": Decimal("200000.00")},
            timeline_constraints={},
            priority_projects=[1],
        )

        # Mock planning service methods with analytics-informed data
        planning_service.redis.incr.return_value = 456

        with patch.multiple(
            planning_service,
            _analyze_current_resource_state=AsyncMock(
                return_value={
                    "total_resources": 3,
                    "avg_utilization": analytics_result.average_utilization,
                    "underutilized_resources": analytics_result.underutilized_resources,
                    "efficiency_score": analytics_result.efficiency_score,
                }
            ),
            _analyze_demand_requirements=AsyncMock(
                return_value={"projected_demand": 800}
            ),
            _generate_capacity_plan=AsyncMock(
                return_value={
                    "recommendations": [
                        "Increase utilization of resource 3",
                        "Redistribute workload",
                    ]
                }
            ),
            _identify_skill_gaps=AsyncMock(
                return_value=[{"skill": "Python", "gap_size": 2, "priority": "high"}]
            ),
            _generate_hiring_plan=AsyncMock(return_value={"new_hires_needed": 2}),
            _generate_training_plan=AsyncMock(return_value={"training_programs": 1}),
            _create_implementation_roadmap=AsyncMock(
                return_value={"phases": ["Phase 1"]}
            ),
            _calculate_plan_costs=AsyncMock(return_value={"total_cost": 180000}),
            _assess_plan_risks=AsyncMock(return_value={"risk_level": "low"}),
            _generate_planning_recommendations=Mock(
                return_value=[
                    "Focus on underutilized resources",
                    "Implement skills training for Python",
                ]
            ),
        ):
            planning_result = await planning_service.create_resource_plan(
                planning_request=planning_request, user_id=1
            )

        # Verify integration between analytics and planning
        assert isinstance(planning_result, ResourcePlanningResponse)
        assert (
            planning_result.current_state["avg_utilization"]
            == analytics_result.average_utilization
        )
        assert (
            planning_result.current_state["underutilized_resources"]
            == analytics_result.underutilized_resources
        )

        # Verify planning recommendations are informed by analytics
        recommendations = planning_result.recommendations
        assert any("underutilized" in rec for rec in recommendations)
        assert any("Python" in rec for rec in recommendations)

    @pytest.mark.asyncio
    async def test_forecast_based_capacity_planning(
        self, analytics_service, planning_service
    ):
        """Test capacity planning based on demand forecasting"""

        # Step 1: Generate demand forecast using analytics
        forecast_request = ResourceForecastRequest(
            start_date=date(2025, 8, 1),
            end_date=date(2025, 10, 31),
            forecast_periods=3,
            granularity="monthly",
            departments=[1, 2],
            resource_types=["human"],
            growth_assumptions={"demand_growth": 0.15},
            constraints={"max_capacity": 2000},
        )

        # Mock forecast methods
        with patch.multiple(
            analytics_service,
            _get_historical_resource_data=AsyncMock(
                return_value={"utilization_trend": "increasing"}
            ),
            _forecast_resource_demand=Mock(
                return_value=[
                    {"period": 1, "demand": 180, "confidence": 0.85},
                    {"period": 2, "demand": 195, "confidence": 0.80},
                    {"period": 3, "demand": 210, "confidence": 0.75},
                ]
            ),
            _forecast_resource_capacity=Mock(
                return_value=[
                    {"period": 1, "capacity": 200},
                    {"period": 2, "capacity": 200},
                    {"period": 3, "capacity": 200},
                ]
            ),
            _identify_capacity_gaps=Mock(
                return_value=[{"period": 3, "gap": -10, "type": "shortage"}]
            ),
            _generate_forecast_recommendations=Mock(
                return_value=[
                    {"action": "hire_additional_resources", "timeline": "month_2"}
                ]
            ),
            _calculate_forecast_confidence=Mock(return_value=0.80),
        ):
            forecast_result = await analytics_service.generate_resource_forecast(
                forecast_request
            )

        # Step 2: Use forecast data for capacity planning
        capacity_request = {
            "planning_period": {
                "start_date": date(2025, 8, 1),
                "end_date": date(2025, 10, 31),
            },
            "departments": [1, 2],
            "resource_types": ["human"],
            "demand_drivers": [{"factor": "forecasted_demand", "impact": 1.2}],
            "growth_assumptions": {"demand_growth": 0.15},
            "service_level_targets": {"availability": 95.0},
            "scaling_options": [
                {"type": "hiring", "cost_per_unit": 120000.0, "lead_time_weeks": 6}
            ],
            "budget_constraints": {"max_budget": Decimal("500000.00")},
            "optimization_goals": ["meet_forecasted_demand"],
            "implementation_timeline": {
                "phase1_start": date(2025, 8, 1),
                "completion": date(2025, 10, 31),
            },
        }

        # Mock capacity planning with forecast-informed decisions
        with patch.multiple(
            planning_service,
            _analyze_current_capacity=AsyncMock(return_value={"current_capacity": 200}),
            _project_capacity_demand=AsyncMock(
                return_value={
                    "projected_demand": max(
                        item["demand"] for item in forecast_result.demand_forecast
                    ),
                    "peak_period": "month_3",
                }
            ),
            _calculate_capacity_gaps=AsyncMock(
                return_value=[
                    {
                        "gap_type": "forecasted_shortage",
                        "amount": 10,
                        "period": "month_3",
                    }
                ]
            ),
            _generate_scaling_scenarios=AsyncMock(
                return_value=[
                    {
                        "scenario": "hire_1_resource",
                        "cost": 120000,
                        "addresses_gap": True,
                    }
                ]
            ),
            _optimize_capacity_allocation=AsyncMock(
                return_value={"optimal_strategy": "early_hiring_to_avoid_bottleneck"}
            ),
            _create_capacity_roadmap=AsyncMock(
                return_value={
                    "milestones": ["hire_by_month_2", "training_complete_month_3"]
                }
            ),
            _calculate_capacity_utilization=Mock(return_value=95.0),
            _calculate_efficiency_score=Mock(return_value=88.0),
            _calculate_cost_effectiveness=Mock(return_value=82.0),
            _generate_capacity_recommendations=Mock(
                return_value=[
                    "Start hiring process immediately",
                    "Plan for 6-week onboarding timeline",
                ]
            ),
        ):
            from app.schemas.resource import CapacityPlanningRequest

            capacity_planning_request = CapacityPlanningRequest(**capacity_request)
            capacity_result = await planning_service.create_capacity_plan(
                capacity_request=capacity_planning_request, user_id=2
            )

        # Verify integration between forecast and capacity planning
        assert isinstance(capacity_result, CapacityPlanningResponse)
        assert capacity_result.demand_projection["peak_period"] == "month_3"
        assert any("shortage" in str(gap) for gap in capacity_result.capacity_gaps)
        assert any("hire" in rec for rec in capacity_result.recommendations)

    @pytest.mark.asyncio
    async def test_roi_analysis_budget_planning_integration(
        self, analytics_service, planning_service
    ):
        """Test budget planning informed by ROI analysis"""

        # Step 1: Analyze current resource ROI
        resource_ids = [1, 2, 3]

        # Mock ROI analysis
        with patch.multiple(
            analytics_service,
            _get_resource_costs=AsyncMock(
                side_effect=[
                    {"total_cost": 48000.0},
                    {"total_cost": 36000.0},
                    {"total_cost": 21600.0},
                ]
            ),
            _get_resource_value_contribution=AsyncMock(
                side_effect=[
                    {"total_value": 72000.0},
                    {"total_value": 43200.0},
                    {"total_value": 19440.0},
                ]
            ),
            _calculate_productivity_metrics=Mock(
                return_value={"productivity_score": 85.0}
            ),
            _analyze_value_drivers=Mock(
                return_value=[{"driver": "project_delivery", "impact": 0.7}]
            ),
            _rate_resource_performance=Mock(
                side_effect=["excellent", "good", "needs_improvement"]
            ),
            _identify_roi_optimization_opportunities=Mock(
                return_value=[
                    {
                        "resource_id": 3,
                        "opportunity": "training_investment",
                        "potential_roi": 1.8,
                    }
                ]
            ),
            _generate_investment_recommendations=Mock(
                return_value=[
                    {
                        "resource_id": 3,
                        "recommendation": "skills_upgrade",
                        "investment": 5000,
                        "expected_roi": 1.8,
                    }
                ]
            ),
        ):
            roi_result = await analytics_service.analyze_resource_roi(
                resource_ids=resource_ids,
                start_date=date(2025, 7, 1),
                end_date=date(2025, 7, 31),
            )

        # Step 2: Create budget plan based on ROI insights
        budget_request = ResourceBudgetPlanRequest(
            planning_period={
                "start_date": date(2025, 8, 1),
                "end_date": date(2025, 12, 31),
            },
            departments=[1, 2],
            total_budget=Decimal("600000.00"),
            historical_periods=3,
            cost_categories=["salaries", "training", "tools"],
            growth_assumptions={"salary_increase": 0.05},
            inflation_rates={"general": 0.03},
            allocation_priorities={
                "salaries": 0.75,
                "training": 0.20,  # Increased based on ROI analysis
                "tools": 0.05,
            },
            constraints={"training_focus_resource_3": True},  # Based on ROI findings
            cash_flow_constraints={},
            optimization_targets={"roi_improvement": 0.15},
            risk_factors=[],
            contingency_percentage=10.0,
            value_drivers=[
                {"driver": "training_investment", "value": 0.25}  # From ROI analysis
            ],
        )

        # Mock budget planning with ROI-informed decisions
        with patch.multiple(
            planning_service,
            _analyze_historical_spending=AsyncMock(
                return_value={
                    "training_underspend": 15000,  # Opportunity identified
                    "roi_correlation": {"training": 1.8, "tools": 1.2},
                }
            ),
            _project_future_costs=AsyncMock(
                return_value={
                    "training_investment_needed": 30000,  # For resource 3
                    "expected_roi_improvement": 0.18,
                }
            ),
            _allocate_budget_by_category=AsyncMock(
                return_value={
                    "salaries": 450000,
                    "training": 120000,  # Increased allocation
                    "tools": 30000,
                }
            ),
            _create_phased_budget_plan=AsyncMock(
                return_value={
                    "phase1": {"training_priority": "resource_3_skills_upgrade"}
                }
            ),
            _identify_cost_optimizations=AsyncMock(
                return_value=[
                    {"opportunity": "roi_based_training", "roi_improvement": 0.8}
                ]
            ),
            _create_budget_contingency_plans=AsyncMock(
                return_value=[
                    {"scenario": "accelerated_training", "budget_increase": 20000}
                ]
            ),
            _calculate_budget_roi_projections=AsyncMock(
                return_value={
                    "projected_roi": 2.1,  # Improved from current 1.85
                    "training_contribution": 0.35,
                }
            ),
            _create_variance_analysis_framework=AsyncMock(
                return_value={"roi_tracking": "monthly_resource_productivity"}
            ),
            _create_budget_monitoring_framework=AsyncMock(
                return_value={
                    "roi_kpis": ["resource_productivity", "training_effectiveness"]
                }
            ),
        ):
            budget_result = await planning_service.create_budget_plan(
                budget_request=budget_request, user_id=3
            )

        # Verify integration between ROI analysis and budget planning
        assert isinstance(budget_result, ResourceBudgetPlanResponse)
        assert (
            budget_result.budget_allocation["training"]
            > budget_result.budget_allocation["tools"]
        )
        assert budget_result.roi_projections["projected_roi"] > roi_result.overall_roi
        assert any(
            "training" in str(opp) for opp in budget_result.optimization_opportunities
        )

    @pytest.mark.asyncio
    async def test_skills_analytics_gap_analysis_integration(
        self, analytics_service, planning_service
    ):
        """Test skill gap analysis integrated with performance analytics"""

        # Step 1: Analyze current resource performance by skills
        # Mock skill-based performance analytics
        analytics_service.db.execute.side_effect = [
            Mock(
                fetchall=Mock(
                    return_value=[
                        Mock(
                            resource_id=1,
                            skill="Python",
                            performance_score=95.0,
                            utilization=85.0,
                        ),
                        Mock(
                            resource_id=2,
                            skill="Python",
                            performance_score=75.0,
                            utilization=70.0,
                        ),
                        Mock(
                            resource_id=1,
                            skill="React",
                            performance_score=80.0,
                            utilization=60.0,
                        ),
                        Mock(
                            resource_id=3,
                            skill="React",
                            performance_score=60.0,
                            utilization=45.0,
                        ),
                    ]
                )
            )
        ]

        # Simulate skills performance analysis
        skills_performance = {
            "Python": {
                "avg_performance": 85.0,
                "resource_count": 2,
                "top_performer": 1,
            },
            "React": {
                "avg_performance": 70.0,
                "resource_count": 2,
                "needs_improvement": [3],
            },
        }

        # Step 2: Use skills performance data for gap analysis
        skill_gap_request = SkillGapAnalysisRequest(
            departments=[1, 2],
            resource_types=["human"],
            skill_categories=["technical"],
            project_pipeline=[
                {
                    "project": "New Platform",
                    "skills": ["Python", "React"],
                    "required_performance": 85.0,
                }
            ],
            technology_roadmap={"python_advanced": 0.8, "react_modern": 0.9},
            planning_horizon={
                "start_date": date(2025, 8, 1),
                "end_date": date(2025, 12, 31),
            },
            proficiency_levels={"advanced": 85.0, "expert": 95.0},
            business_priorities=["performance_improvement"],
            urgency_factors={"react_skills": 0.8},  # Based on analytics
            development_preferences={"internal_training": 0.8},
            learning_resources=[],
            budget_constraints={"training_budget": Decimal("50000.00")},
            timeline_constraints={},
        )

        # Mock skill gap analysis with performance-informed decisions
        with patch.multiple(
            planning_service,
            _analyze_current_skills=AsyncMock(
                return_value={
                    "skill_performance": skills_performance,
                    "performance_gaps": {
                        "React": {"gap_size": 15.0, "affected_resources": [3]}
                    },
                }
            ),
            _analyze_future_skill_requirements=AsyncMock(
                return_value={
                    "performance_requirements": {"Python": 90.0, "React": 85.0},
                    "gap_projections": {"React": {"performance_gap": 15.0}},
                }
            ),
            _identify_detailed_skill_gaps=AsyncMock(
                return_value=[
                    {
                        "skill": "React",
                        "current_performance": 70.0,
                        "required_performance": 85.0,
                        "gap": 15.0,
                        "affected_resources": [3],
                    }
                ]
            ),
            _prioritize_skill_gaps=AsyncMock(
                return_value=[
                    {
                        "skill": "React",
                        "priority_score": 0.9,
                        "performance_impact": "high",
                        "business_critical": True,
                    }
                ]
            ),
            _generate_skill_development_strategies=AsyncMock(
                return_value=[
                    {
                        "strategy": "targeted_react_training",
                        "resources": [3],
                        "expected_improvement": 20.0,
                        "timeline": "3_months",
                    }
                ]
            ),
            _create_learning_paths=AsyncMock(
                return_value=[
                    {
                        "skill": "React",
                        "resource_id": 3,
                        "path": "intermediate_to_advanced",
                        "expected_performance_gain": 20.0,
                    }
                ]
            ),
            _calculate_skill_investment=AsyncMock(
                return_value={
                    "total_investment": 15000,
                    "expected_performance_roi": 2.5,
                }
            ),
            _assess_skill_development_risks=AsyncMock(
                return_value=[
                    {"risk": "performance_plateau", "mitigation": "advanced_mentoring"}
                ]
            ),
            _define_skill_success_metrics=AsyncMock(
                return_value={"performance_improvement": 0.8, "project_readiness": 0.9}
            ),
            _create_skill_implementation_timeline=AsyncMock(
                return_value={
                    "milestones": [
                        "performance_assessment",
                        "training_completion",
                        "project_application",
                    ]
                }
            ),
        ):
            skill_gap_result = await planning_service.analyze_skill_gaps(
                skill_gap_request=skill_gap_request, user_id=4
            )

        # Verify integration between skills analytics and gap analysis
        assert isinstance(skill_gap_result, SkillGapAnalysisResponse)
        assert "skill_performance" in skill_gap_result.current_skills
        assert len(skill_gap_result.skill_gaps) == 1
        assert skill_gap_result.skill_gaps[0]["skill"] == "React"
        assert skill_gap_result.skill_gaps[0]["performance_impact"] == "high"
        assert any(
            "performance" in str(strategy)
            for strategy in skill_gap_result.development_strategies
        )

    @pytest.mark.asyncio
    async def test_comprehensive_resource_optimization_workflow(
        self, analytics_service, planning_service, sample_analytics_data
    ):
        """Test comprehensive workflow combining all analytics and planning features"""

        # Step 1: Current state analysis
        analytics_service.db.execute.side_effect = [
            Mock(fetchall=Mock(return_value=sample_analytics_data["utilization_data"])),
            Mock(fetchall=Mock(return_value=sample_analytics_data["cost_data"])),
        ]

        current_analytics = await analytics_service.get_resource_analytics(
            start_date=date(2025, 7, 1), end_date=date(2025, 7, 31)
        )

        # Step 2: Demand forecasting
        with patch.multiple(
            analytics_service,
            _get_historical_resource_data=AsyncMock(return_value={"trend": "growth"}),
            _forecast_resource_demand=Mock(return_value=[{"period": 1, "demand": 220}]),
            _forecast_resource_capacity=Mock(
                return_value=[{"period": 1, "capacity": 200}]
            ),
            _identify_capacity_gaps=Mock(return_value=[{"period": 1, "gap": -20}]),
            _generate_forecast_recommendations=Mock(
                return_value=[{"action": "capacity_increase"}]
            ),
            _calculate_forecast_confidence=Mock(return_value=0.82),
        ):
            forecast_request = ResourceForecastRequest(
                start_date=date(2025, 8, 1),
                end_date=date(2025, 8, 31),
                forecast_periods=1,
                granularity="monthly",
                departments=[1, 2],
                resource_types=["human"],
            )
            demand_forecast = await analytics_service.generate_resource_forecast(
                forecast_request
            )

        # Step 3: ROI-based optimization
        with patch.multiple(
            analytics_service,
            _get_resource_costs=AsyncMock(return_value={"total_cost": 40000.0}),
            _get_resource_value_contribution=AsyncMock(
                return_value={"total_value": 60000.0}
            ),
            _calculate_productivity_metrics=Mock(return_value={"score": 80.0}),
            _analyze_value_drivers=Mock(return_value=[]),
            _rate_resource_performance=Mock(return_value="good"),
            _identify_roi_optimization_opportunities=Mock(
                return_value=[{"opportunity": "training", "roi": 1.5}]
            ),
            _generate_investment_recommendations=Mock(
                return_value=[{"investment": "skills_training", "expected_roi": 1.8}]
            ),
        ):
            roi_analysis = await analytics_service.analyze_resource_roi(
                resource_ids=[1, 2, 3],
                start_date=date(2025, 7, 1),
                end_date=date(2025, 7, 31),
            )

        # Step 4: Comprehensive resource planning
        planning_request = ResourcePlanningRequest(
            plan_name="Comprehensive Optimization Plan",
            planning_horizon={
                "start_date": date(2025, 8, 1),
                "end_date": date(2025, 12, 31),
            },
            departments=[1, 2],
            project_requirements=[
                {
                    "project_id": 1,
                    "required_hours": 880,  # From demand forecast
                    "priority": "high",
                }
            ],
            required_skills=["Python", "React"],
            growth_targets={
                "capacity_increase": 0.1,  # From gap analysis
                "roi_improvement": 0.2,  # From ROI analysis
            },
            budget_constraints={"total_budget": Decimal("300000.00")},
            timeline_constraints={},
            priority_projects=[1],
            training_budget=Decimal("40000.00"),  # From ROI recommendations
        )

        planning_service.redis.incr.return_value = 789

        with patch.multiple(
            planning_service,
            _analyze_current_resource_state=AsyncMock(
                return_value={
                    "utilization": current_analytics.average_utilization,
                    "efficiency": current_analytics.efficiency_score,
                    "underutilized": current_analytics.underutilized_resources,
                }
            ),
            _analyze_demand_requirements=AsyncMock(
                return_value={
                    "forecasted_demand": demand_forecast.demand_forecast[0]["demand"]
                }
            ),
            _generate_capacity_plan=AsyncMock(
                return_value={
                    "capacity_gap": demand_forecast.gaps_and_surpluses[0]["gap"]
                }
            ),
            _identify_skill_gaps=AsyncMock(
                return_value=[{"skill": "React", "gap_size": 2}]
            ),
            _generate_hiring_plan=AsyncMock(
                return_value={"new_hires": 1, "timeline": "2_months"}
            ),
            _generate_training_plan=AsyncMock(
                return_value={
                    "roi_focused_training": roi_analysis.investment_recommendations[0]
                }
            ),
            _create_implementation_roadmap=AsyncMock(
                return_value={"integrated_approach": "analytics_driven_optimization"}
            ),
            _calculate_plan_costs=AsyncMock(
                return_value={"total_cost": 280000, "expected_roi": 2.2}
            ),
            _assess_plan_risks=AsyncMock(
                return_value={"risk_level": "low", "data_driven_confidence": 0.85}
            ),
            _generate_planning_recommendations=Mock(
                return_value=[
                    "Implement analytics-driven resource allocation",
                    "Focus training investment on high-ROI opportunities",
                    "Address capacity gaps proactively based on forecast",
                ]
            ),
        ):
            comprehensive_plan = await planning_service.create_resource_plan(
                planning_request=planning_request, user_id=5
            )

        # Verify comprehensive integration
        assert isinstance(comprehensive_plan, ResourcePlanningResponse)

        # Verify analytics informed the current state
        assert (
            comprehensive_plan.current_state["utilization"]
            == current_analytics.average_utilization
        )
        assert (
            comprehensive_plan.current_state["efficiency"]
            == current_analytics.efficiency_score
        )

        # Verify forecast informed demand analysis
        assert (
            comprehensive_plan.demand_analysis["forecasted_demand"]
            == demand_forecast.demand_forecast[0]["demand"]
        )

        # Verify ROI analysis informed training plan
        training_plan = comprehensive_plan.training_plan
        assert "roi_focused_training" in training_plan

        # Verify integrated recommendations
        recommendations = comprehensive_plan.recommendations
        assert any("analytics-driven" in rec for rec in recommendations)
        assert any("ROI" in rec for rec in recommendations)
        assert any("forecast" in rec for rec in recommendations)

    @pytest.mark.asyncio
    async def test_analytics_planning_error_propagation(
        self, analytics_service, planning_service
    ):
        """Test error handling when analytics fails and impacts planning"""

        # Mock analytics failure
        analytics_service.db.execute.side_effect = Exception(
            "Analytics database failure"
        )

        # Attempt to get analytics for planning
        with pytest.raises(Exception) as exc_info:
            await analytics_service.get_resource_analytics(
                start_date=date(2025, 7, 1), end_date=date(2025, 7, 31)
            )

        assert "Analytics database failure" in str(exc_info.value)

        # Planning should handle missing analytics gracefully
        planning_request = ResourcePlanningRequest(
            plan_name="Fallback Plan",
            planning_horizon={
                "start_date": date(2025, 8, 1),
                "end_date": date(2025, 12, 31),
            },
            departments=[1],
            project_requirements=[],
            required_skills=[],
            growth_targets={},
            budget_constraints={},
            timeline_constraints={},
            priority_projects=[],
        )

        planning_service.redis.incr.return_value = 999

        # Mock planning with fallback values when analytics unavailable
        with patch.multiple(
            planning_service,
            _analyze_current_resource_state=AsyncMock(
                return_value={"fallback_mode": True, "estimated_resources": 10}
            ),
            _analyze_demand_requirements=AsyncMock(
                return_value={"fallback_demand": 100}
            ),
            _generate_capacity_plan=AsyncMock(return_value={"conservative_plan": True}),
            _identify_skill_gaps=AsyncMock(return_value=[]),
            _generate_hiring_plan=AsyncMock(return_value={"conservative_hiring": 0}),
            _generate_training_plan=AsyncMock(return_value={"basic_training": True}),
            _create_implementation_roadmap=AsyncMock(
                return_value={"fallback_roadmap": True}
            ),
            _calculate_plan_costs=AsyncMock(return_value={"estimated_cost": 50000}),
            _assess_plan_risks=AsyncMock(
                return_value={"risk_level": "high_uncertainty"}
            ),
            _generate_planning_recommendations=Mock(
                return_value=[
                    "Collect current analytics data before implementation",
                    "Use conservative estimates due to missing analytics",
                ]
            ),
        ):
            fallback_plan = await planning_service.create_resource_plan(
                planning_request=planning_request, user_id=6
            )

        # Verify fallback planning works without analytics
        assert isinstance(fallback_plan, ResourcePlanningResponse)
        assert fallback_plan.current_state["fallback_mode"] is True
        assert fallback_plan.risk_assessment["risk_level"] == "high_uncertainty"
        assert any("analytics" in rec for rec in fallback_plan.recommendations)

    @pytest.mark.asyncio
    async def test_performance_integration_large_dataset(
        self, analytics_service, planning_service
    ):
        """Test performance when integrating analytics and planning with large datasets"""

        # Simulate large dataset processing
        large_utilization_data = [
            Mock(resource_id=i, avg_utilization=75.0 + (i % 20), peak_utilization=95.0)
            for i in range(1, 101)  # 100 resources
        ]

        large_cost_data = [
            Mock(
                resource_id=i,
                total_cost=50000.0 + (i * 100),
                avg_hourly_rate=120.0 + (i % 30),
            )
            for i in range(1, 101)
        ]

        # Mock large dataset queries
        analytics_service.db.execute.side_effect = [
            Mock(fetchall=Mock(return_value=large_utilization_data)),
            Mock(fetchall=Mock(return_value=large_cost_data)),
        ]

        # Measure analytics processing time
        import time

        start_time = time.time()

        large_analytics = await analytics_service.get_resource_analytics(
            start_date=date(2025, 7, 1), end_date=date(2025, 7, 31)
        )

        analytics_time = time.time() - start_time

        # Verify analytics can handle large datasets
        assert large_analytics.total_resources == 100
        assert analytics_time < 2.0  # Should complete within 2 seconds

        # Use large analytics data for planning
        planning_request = ResourcePlanningRequest(
            plan_name="Large Scale Planning",
            planning_horizon={
                "start_date": date(2025, 8, 1),
                "end_date": date(2025, 12, 31),
            },
            departments=list(range(1, 11)),  # 10 departments
            project_requirements=[
                {
                    "project_id": i,
                    "required_hours": 1000,
                    "skills": ["Python"],
                    "priority": "medium",
                }
                for i in range(1, 21)
            ],  # 20 projects
            required_skills=["Python", "React", "FastAPI"],
            growth_targets={"team_size": 1.1},
            budget_constraints={"total_budget": Decimal("5000000.00")},
            timeline_constraints={},
            priority_projects=list(range(1, 6)),
        )

        planning_service.redis.incr.return_value = 1000

        with patch.multiple(
            planning_service,
            _analyze_current_resource_state=AsyncMock(
                return_value={
                    "large_scale": True,
                    "total_resources": large_analytics.total_resources,
                }
            ),
            _analyze_demand_requirements=AsyncMock(
                return_value={"total_demand": 20000}
            ),
            _generate_capacity_plan=AsyncMock(return_value={"scaling_required": True}),
            _identify_skill_gaps=AsyncMock(
                return_value=[{"skill": "Python", "gap_size": 20}]
            ),
            _generate_hiring_plan=AsyncMock(return_value={"new_hires_needed": 25}),
            _generate_training_plan=AsyncMock(return_value={"training_programs": 10}),
            _create_implementation_roadmap=AsyncMock(return_value={"phases": 4}),
            _calculate_plan_costs=AsyncMock(return_value={"total_cost": 4800000}),
            _assess_plan_risks=AsyncMock(return_value={"risk_level": "medium"}),
            _generate_planning_recommendations=Mock(
                return_value=[
                    "Phased implementation for large scale changes",
                    "Establish resource management centers of excellence",
                ]
            ),
        ):
            start_time = time.time()
            large_plan = await planning_service.create_resource_plan(
                planning_request=planning_request, user_id=7
            )
            planning_time = time.time() - start_time

        # Verify planning can handle large scale integration
        assert isinstance(large_plan, ResourcePlanningResponse)
        assert large_plan.current_state["total_resources"] == 100
        assert planning_time < 3.0  # Should complete within 3 seconds
        assert any("large scale" in rec for rec in large_plan.recommendations)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--asyncio-mode=auto"])
