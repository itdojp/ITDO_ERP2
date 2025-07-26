"""
ITDO ERP Backend - Resource Planning API Unit Tests
Day 22: Comprehensive unit tests for resource planning functionality
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.api.v1.resource_planning_api import ResourcePlanningService
from app.schemas.resource import (
    CapacityPlanningRequest,
    CapacityPlanningResponse,
    ResourceBudgetPlanRequest,
    ResourceBudgetPlanResponse,
    ResourceDemandPredictionResponse,
    ResourcePlanningRequest,
    ResourcePlanningResponse,
    ResourceScenarioRequest,
    ResourceScenarioResponse,
    ResourceSuccessionPlanRequest,
    ResourceSuccessionPlanResponse,
    SkillGapAnalysisRequest,
    SkillGapAnalysisResponse,
)


class TestResourcePlanningService:
    """Unit tests for ResourcePlanningService"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return AsyncMock()

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        return AsyncMock()

    @pytest.fixture
    def planning_service(self, mock_db, mock_redis):
        """ResourcePlanningService instance with mocked dependencies"""
        return ResourcePlanningService(mock_db, mock_redis)

    @pytest.fixture
    def sample_planning_request(self):
        """Sample resource planning request"""
        return ResourcePlanningRequest(
            plan_name="Q4 2025 Resource Plan",
            planning_horizon={
                "start_date": date(2025, 10, 1),
                "end_date": date(2025, 12, 31),
            },
            departments=[1, 2, 3],
            project_requirements=[
                {
                    "project_id": 1,
                    "required_hours": 800,
                    "skills": ["Python", "FastAPI"],
                    "priority": "high",
                },
                {
                    "project_id": 2,
                    "required_hours": 600,
                    "skills": ["React", "TypeScript"],
                    "priority": "medium",
                },
            ],
            required_skills=["Python", "React", "FastAPI", "TypeScript"],
            growth_targets={"team_size": 1.2, "productivity": 1.1},
            budget_constraints={
                "total_budget": Decimal("500000.00"),
                "hiring_budget": Decimal("200000.00"),
            },
            timeline_constraints={
                "hiring_deadline": date(2025, 11, 15),
                "training_completion": date(2025, 12, 1),
            },
            priority_projects=[1],
            training_budget=Decimal("50000.00"),
            constraints={"max_hiring": 5, "remote_work_allowed": True},
        )

    @pytest.fixture
    def sample_capacity_request(self):
        """Sample capacity planning request"""
        return CapacityPlanningRequest(
            planning_period={
                "start_date": date(2025, 10, 1),
                "end_date": date(2025, 12, 31),
            },
            departments=[1, 2],
            resource_types=["human", "equipment"],
            demand_drivers=[
                {"factor": "new_projects", "impact": 1.3},
                {"factor": "team_growth", "impact": 1.1},
            ],
            growth_assumptions={"demand_growth": 0.15, "efficiency_improvement": 0.05},
            service_level_targets={"availability": 95.0, "response_time": 24.0},
            scaling_options=[
                {"type": "hiring", "cost_per_unit": 150000.0, "lead_time_weeks": 8},
                {"type": "contractor", "cost_per_unit": 200.0, "lead_time_weeks": 2},
            ],
            budget_constraints={"max_budget": Decimal("600000.00")},
            optimization_goals=["minimize_cost", "maximize_utilization"],
            implementation_timeline={
                "phase1_start": date(2025, 10, 1),
                "phase2_start": date(2025, 11, 1),
                "completion": date(2025, 12, 31),
            },
        )

    @pytest.mark.asyncio
    async def test_create_resource_plan_complete(
        self, planning_service, sample_planning_request
    ):
        """Test complete resource plan creation"""

        # Mock Redis counter
        planning_service.redis.incr.return_value = 123

        # Mock all helper methods
        with patch.multiple(
            planning_service,
            _analyze_current_resource_state=AsyncMock(
                return_value={"total_resources": 25, "departments": [1, 2, 3]}
            ),
            _analyze_demand_requirements=AsyncMock(
                return_value={
                    "projected_demand": 1400,
                    "skills_needed": ["Python", "React"],
                }
            ),
            _generate_capacity_plan=AsyncMock(
                return_value={"capacity_increase_needed": 30, "timeline": "8 weeks"}
            ),
            _identify_skill_gaps=AsyncMock(
                return_value=[
                    {"skill": "Python", "gap_size": 3},
                    {"skill": "React", "gap_size": 2},
                ]
            ),
            _generate_hiring_plan=AsyncMock(
                return_value={
                    "new_hires_needed": 5,
                    "budget_required": 750000,
                    "timeline": "6 weeks",
                }
            ),
            _generate_training_plan=AsyncMock(
                return_value={
                    "training_programs": 3,
                    "budget_required": 45000,
                    "duration": "4 weeks",
                }
            ),
            _create_implementation_roadmap=AsyncMock(
                return_value={"phases": ["Phase 1", "Phase 2"], "duration": "12 weeks"}
            ),
            _calculate_plan_costs=AsyncMock(
                return_value={"total_cost": 795000, "roi_projection": 2.1}
            ),
            _assess_plan_risks=AsyncMock(
                return_value={"risk_level": "medium", "key_risks": ["talent_shortage"]}
            ),
            _generate_planning_recommendations=Mock(
                return_value=["Start hiring early", "Focus on Python skills"]
            ),
        ):
            # Execute
            result = await planning_service.create_resource_plan(
                planning_request=sample_planning_request, user_id=1
            )

        # Verify response structure
        assert isinstance(result, ResourcePlanningResponse)
        assert result.plan_id == 123
        assert result.plan_name == "Q4 2025 Resource Plan"
        assert result.planning_horizon == sample_planning_request.planning_horizon
        assert result.current_state["total_resources"] == 25
        assert result.demand_analysis["projected_demand"] == 1400
        assert result.capacity_plan["capacity_increase_needed"] == 30
        assert len(result.skill_gaps) == 2
        assert result.hiring_plan["new_hires_needed"] == 5
        assert result.training_plan["training_programs"] == 3
        assert result.cost_analysis["total_cost"] == 795000
        assert result.risk_assessment["risk_level"] == "medium"
        assert len(result.recommendations) == 2
        assert result.created_by == 1

        # Verify Redis operations
        planning_service.redis.incr.assert_called_once_with("resource_plan_counter")
        planning_service.redis.hset.assert_called_once()
        planning_service.redis.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_capacity_plan(
        self, planning_service, sample_capacity_request
    ):
        """Test capacity planning creation"""

        # Mock all helper methods
        with patch.multiple(
            planning_service,
            _analyze_current_capacity=AsyncMock(
                return_value={"total_capacity": 2000, "utilization": 75.0}
            ),
            _project_capacity_demand=AsyncMock(
                return_value={"projected_demand": 2600, "growth_rate": 0.3}
            ),
            _calculate_capacity_gaps=AsyncMock(
                return_value=[{"gap_type": "shortage", "amount": 600}]
            ),
            _generate_scaling_scenarios=AsyncMock(
                return_value=[{"scenario": "hire_3_people", "cost": 450000}]
            ),
            _optimize_capacity_allocation=AsyncMock(
                return_value={"optimal_allocation": "balanced"}
            ),
            _create_capacity_roadmap=AsyncMock(
                return_value={"roadmap": "3_phase_plan"}
            ),
            _calculate_capacity_utilization=Mock(return_value=82.5),
            _calculate_efficiency_score=Mock(return_value=88.0),
            _calculate_cost_effectiveness=Mock(return_value=75.5),
            _generate_capacity_recommendations=Mock(
                return_value=["Hire 3 senior developers", "Invest in automation"]
            ),
        ):
            # Execute
            result = await planning_service.create_capacity_plan(
                capacity_request=sample_capacity_request, user_id=2
            )

        # Verify response
        assert isinstance(result, CapacityPlanningResponse)
        assert result.planning_period == sample_capacity_request.planning_period
        assert result.current_capacity["total_capacity"] == 2000
        assert result.demand_projection["projected_demand"] == 2600
        assert len(result.capacity_gaps) == 1
        assert len(result.scaling_scenarios) == 1
        assert result.performance_metrics["capacity_utilization"] == 82.5
        assert result.performance_metrics["efficiency_score"] == 88.0
        assert result.performance_metrics["cost_effectiveness"] == 75.5
        assert len(result.recommendations) == 2
        assert result.generated_by == 2

    @pytest.mark.asyncio
    async def test_analyze_scenario_multiple_scenarios(self, planning_service):
        """Test scenario analysis with multiple what-if scenarios"""

        scenario_request = ResourceScenarioRequest(
            scenario_name="Resource Scaling Analysis",
            baseline_demand={"current_demand": 1000, "growth_rate": 0.1},
            baseline_constraints={"budget": 500000, "timeline": 6},
            scenarios=[
                {
                    "name": "Aggressive Growth",
                    "description": "Rapid team expansion",
                    "parameters": {"growth_rate": 0.3, "budget_increase": 0.5},
                },
                {
                    "name": "Conservative Growth",
                    "description": "Gradual team expansion",
                    "parameters": {"growth_rate": 0.15, "budget_increase": 0.2},
                },
            ],
            planning_horizon={
                "start_date": date(2025, 10, 1),
                "end_date": date(2025, 12, 31),
            },
            decision_criteria=["cost", "risk", "timeline"],
            cost_parameters={"hourly_rate": 120.0, "overhead": 0.3},
        )

        # Mock scenario analysis methods
        with patch.multiple(
            planning_service,
            _apply_scenario_to_demand=AsyncMock(
                side_effect=[
                    {"demand": 1300, "skills": ["Python", "React"]},
                    {"demand": 1150, "skills": ["Python", "React"]},
                ]
            ),
            _apply_scenario_to_constraints=AsyncMock(
                side_effect=[
                    {"budget": 750000, "timeline": 6},
                    {"budget": 600000, "timeline": 6},
                ]
            ),
            _calculate_scenario_requirements=AsyncMock(
                side_effect=[
                    {
                        "resources_needed": 8,
                        "skill_requirements": {"Python": 5, "React": 3},
                    },
                    {
                        "resources_needed": 5,
                        "skill_requirements": {"Python": 3, "React": 2},
                    },
                ]
            ),
            _calculate_scenario_costs=AsyncMock(
                side_effect=[
                    {"total_cost": 720000, "monthly_cost": 240000},
                    {"total_cost": 540000, "monthly_cost": 180000},
                ]
            ),
            _calculate_scenario_timeline=AsyncMock(
                side_effect=[
                    {"timeline_weeks": 8, "critical_path": ["hiring", "training"]},
                    {"timeline_weeks": 6, "critical_path": ["training"]},
                ]
            ),
            _assess_scenario_risks=AsyncMock(
                side_effect=[
                    {
                        "risk_score": 0.7,
                        "key_risks": ["talent_shortage", "budget_overrun"],
                    },
                    {"risk_score": 0.3, "key_risks": ["slower_delivery"]},
                ]
            ),
            _calculate_feasibility_score=Mock(side_effect=[75.0, 85.0]),
            _generate_scenario_recommendation=Mock(
                side_effect=[
                    "High-risk, high-reward option",
                    "Balanced approach with moderate risk",
                ]
            ),
            _compare_scenarios=AsyncMock(
                return_value={"comparison_matrix": "detailed_comparison"}
            ),
            _recommend_best_scenario=AsyncMock(
                return_value={"recommended": "Conservative Growth", "confidence": 0.8}
            ),
            _perform_sensitivity_analysis=AsyncMock(
                return_value={"sensitivity": "medium"}
            ),
            _identify_key_decision_factors=Mock(
                return_value=["budget_constraint", "timeline_pressure"]
            ),
            _identify_trade_offs=Mock(return_value=["cost_vs_speed", "risk_vs_reward"]),
            _identify_critical_assumptions=Mock(
                return_value=["market_demand", "talent_availability"]
            ),
        ):
            # Execute
            result = await planning_service.analyze_scenario(
                scenario_request=scenario_request, user_id=3
            )

        # Verify response
        assert isinstance(result, ResourceScenarioResponse)
        assert len(result.analyzed_scenarios) == 2

        # Check first scenario
        first_scenario = result.analyzed_scenarios[0]
        assert first_scenario["scenario_name"] == "Aggressive Growth"
        assert first_scenario["resource_requirements"]["resources_needed"] == 8
        assert first_scenario["cost_impact"]["total_cost"] == 720000
        assert first_scenario["feasibility_score"] == 75.0

        # Check second scenario
        second_scenario = result.analyzed_scenarios[1]
        assert second_scenario["scenario_name"] == "Conservative Growth"
        assert second_scenario["resource_requirements"]["resources_needed"] == 5
        assert second_scenario["feasibility_score"] == 85.0

        assert result.recommended_scenario["recommended"] == "Conservative Growth"
        assert "key_factors" in result.decision_support
        assert result.generated_by == 3

    @pytest.mark.asyncio
    async def test_analyze_skill_gaps_comprehensive(self, planning_service):
        """Test comprehensive skill gap analysis"""

        skill_gap_request = SkillGapAnalysisRequest(
            departments=[1, 2],
            resource_types=["human"],
            skill_categories=["technical", "leadership", "domain"],
            project_pipeline=[
                {
                    "project": "AI Platform",
                    "skills": ["Python", "ML", "AWS"],
                    "timeline": "Q4 2025",
                },
                {
                    "project": "Mobile App",
                    "skills": ["React Native", "TypeScript"],
                    "timeline": "Q1 2026",
                },
            ],
            technology_roadmap={"ai_adoption": 0.8, "cloud_migration": 1.0},
            planning_horizon={
                "start_date": date(2025, 10, 1),
                "end_date": date(2026, 3, 31),
            },
            proficiency_levels={
                "beginner": 1,
                "intermediate": 2,
                "advanced": 3,
                "expert": 4,
            },
            business_priorities=["digital_transformation", "ai_capabilities"],
            urgency_factors={"ai_skills": 0.9, "cloud_skills": 0.7},
            development_preferences={"internal_training": 0.7, "external_hiring": 0.3},
            learning_resources=[
                {"type": "online_course", "cost": 500, "duration_weeks": 8},
                {"type": "certification", "cost": 2000, "duration_weeks": 12},
            ],
            budget_constraints={"training_budget": Decimal("75000.00")},
            timeline_constraints={"urgent_skills_deadline": date(2025, 12, 31)},
        )

        # Mock skill gap analysis methods
        with patch.multiple(
            planning_service,
            _analyze_current_skills=AsyncMock(
                return_value={
                    "total_resources": 20,
                    "skill_inventory": {
                        "Python": 12,
                        "ML": 3,
                        "AWS": 8,
                        "React Native": 5,
                    },
                }
            ),
            _analyze_future_skill_requirements=AsyncMock(
                return_value={
                    "required_skills": {
                        "Python": 18,
                        "ML": 10,
                        "AWS": 15,
                        "React Native": 8,
                    },
                    "timeline_requirements": {
                        "urgent": ["ML", "AWS"],
                        "medium": ["React Native"],
                    },
                }
            ),
            _identify_detailed_skill_gaps=AsyncMock(
                return_value=[
                    {
                        "skill": "ML",
                        "current": 3,
                        "required": 10,
                        "gap": 7,
                        "priority": "high",
                    },
                    {
                        "skill": "AWS",
                        "current": 8,
                        "required": 15,
                        "gap": 7,
                        "priority": "high",
                    },
                    {
                        "skill": "React Native",
                        "current": 5,
                        "required": 8,
                        "gap": 3,
                        "priority": "medium",
                    },
                ]
            ),
            _prioritize_skill_gaps=AsyncMock(
                return_value=[
                    {
                        "skill": "ML",
                        "gap": 7,
                        "priority_score": 0.95,
                        "urgency": "critical",
                    },
                    {
                        "skill": "AWS",
                        "gap": 7,
                        "priority_score": 0.85,
                        "urgency": "high",
                    },
                ]
            ),
            _generate_skill_development_strategies=AsyncMock(
                return_value=[
                    {
                        "strategy": "hire_ml_experts",
                        "skill": "ML",
                        "approach": "external_hiring",
                    },
                    {
                        "strategy": "aws_certification_program",
                        "skill": "AWS",
                        "approach": "internal_training",
                    },
                ]
            ),
            _create_learning_paths=AsyncMock(
                return_value=[
                    {
                        "skill": "ML",
                        "path": "beginner_to_advanced",
                        "duration_weeks": 16,
                        "cost": 15000,
                    },
                    {
                        "skill": "AWS",
                        "path": "certification_track",
                        "duration_weeks": 12,
                        "cost": 8000,
                    },
                ]
            ),
            _calculate_skill_investment=AsyncMock(
                return_value={
                    "total_investment": 65000,
                    "roi_projection": 2.3,
                    "payback_months": 8,
                }
            ),
            _assess_skill_development_risks=AsyncMock(
                return_value=[
                    {
                        "risk": "talent_retention",
                        "impact": "high",
                        "mitigation": "retention_bonuses",
                    },
                    {
                        "risk": "training_quality",
                        "impact": "medium",
                        "mitigation": "certified_providers",
                    },
                ]
            ),
            _define_skill_success_metrics=AsyncMock(
                return_value={
                    "completion_rate": 0.9,
                    "proficiency_improvement": 0.8,
                    "project_readiness": 0.85,
                }
            ),
            _create_skill_implementation_timeline=AsyncMock(
                return_value={
                    "phase1": {"start": date(2025, 10, 1), "skills": ["ML"]},
                    "phase2": {"start": date(2025, 11, 15), "skills": ["AWS"]},
                }
            ),
        ):
            # Execute
            result = await planning_service.analyze_skill_gaps(
                skill_gap_request=skill_gap_request, user_id=4
            )

        # Verify response
        assert isinstance(result, SkillGapAnalysisResponse)
        assert result.current_skills["total_resources"] == 20
        assert len(result.skill_gaps) == 2  # Prioritized gaps
        assert result.skill_gaps[0]["skill"] == "ML"
        assert result.skill_gaps[0]["priority_score"] == 0.95
        assert len(result.development_strategies) == 2
        assert len(result.learning_paths) == 2
        assert result.investment_analysis["total_investment"] == 65000
        assert len(result.development_risks) == 2
        assert result.generated_by == 4

    @pytest.mark.asyncio
    async def test_create_budget_plan(self, planning_service):
        """Test resource budget plan creation"""

        budget_request = ResourceBudgetPlanRequest(
            planning_period={
                "start_date": date(2025, 10, 1),
                "end_date": date(2025, 12, 31),
            },
            departments=[1, 2],
            total_budget=Decimal("800000.00"),
            historical_periods=4,
            cost_categories=["salaries", "training", "tools", "infrastructure"],
            growth_assumptions={"salary_increase": 0.05, "team_growth": 0.1},
            inflation_rates={"general": 0.03, "technology": 0.08},
            allocation_priorities={
                "salaries": 0.7,
                "training": 0.15,
                "tools": 0.1,
                "infrastructure": 0.05,
            },
            constraints={"min_training_budget": 50000, "max_infrastructure": 100000},
            cash_flow_constraints={"monthly_limit": 300000, "q4_bonus_reserve": 150000},
            optimization_targets={"cost_efficiency": 0.9, "roi_improvement": 0.15},
            risk_factors=[
                {"factor": "market_volatility", "impact": 0.1},
                {"factor": "talent_competition", "impact": 0.15},
            ],
            contingency_percentage=10.0,
            value_drivers=[
                {"driver": "productivity_improvement", "value": 0.2},
                {"driver": "quality_enhancement", "value": 0.15},
            ],
        )

        # Mock budget planning methods
        with patch.multiple(
            planning_service,
            _analyze_historical_spending=AsyncMock(
                return_value={
                    "average_monthly": 200000,
                    "spending_trends": {"salaries": "increasing", "tools": "stable"},
                    "seasonal_patterns": {"q4_bonus": 150000},
                }
            ),
            _project_future_costs=AsyncMock(
                return_value={
                    "projected_total": 750000,
                    "category_projections": {"salaries": 525000, "training": 112500},
                }
            ),
            _allocate_budget_by_category=AsyncMock(
                return_value={
                    "salaries": 560000,
                    "training": 120000,
                    "tools": 80000,
                    "infrastructure": 40000,
                }
            ),
            _create_phased_budget_plan=AsyncMock(
                return_value={
                    "q4_2025": {"salaries": 280000, "training": 60000},
                    "monthly_breakdown": {"oct": 250000, "nov": 270000, "dec": 280000},
                }
            ),
            _identify_cost_optimizations=AsyncMock(
                return_value=[
                    {
                        "category": "tools",
                        "optimization": "consolidate_licenses",
                        "savings": 15000,
                    },
                    {
                        "category": "training",
                        "optimization": "bulk_discounts",
                        "savings": 8000,
                    },
                ]
            ),
            _create_budget_contingency_plans=AsyncMock(
                return_value=[
                    {
                        "scenario": "budget_cut_10",
                        "adjustments": {"training": -12000, "tools": -8000},
                    },
                    {"scenario": "emergency_hiring", "additional_budget": 100000},
                ]
            ),
            _calculate_budget_roi_projections=AsyncMock(
                return_value={
                    "projected_roi": 1.85,
                    "value_creation": {"productivity": 160000, "quality": 120000},
                }
            ),
            _create_variance_analysis_framework=AsyncMock(
                return_value={
                    "tracking_metrics": ["monthly_burn_rate", "category_variance"],
                    "alert_thresholds": {"variance": 0.1, "burn_rate": 1.2},
                }
            ),
            _create_budget_monitoring_framework=AsyncMock(
                return_value={
                    "reporting_frequency": "monthly",
                    "kpis": ["budget_utilization", "cost_per_hire"],
                }
            ),
        ):
            # Execute
            result = await planning_service.create_budget_plan(
                budget_request=budget_request, user_id=5
            )

        # Verify response
        assert isinstance(result, ResourceBudgetPlanResponse)
        assert result.total_budget == Decimal("800000.00")
        assert result.historical_analysis["average_monthly"] == 200000
        assert result.cost_projections["projected_total"] == 750000
        assert result.budget_allocation["salaries"] == 560000
        assert len(result.optimization_opportunities) == 2
        assert len(result.contingency_plans) == 2
        assert result.roi_projections["projected_roi"] == 1.85
        assert result.generated_by == 5

    @pytest.mark.asyncio
    async def test_predict_resource_demand(self, planning_service):
        """Test ML-based resource demand prediction"""

        departments = [1, 2, 3]
        planning_horizon = {
            "start_date": date(2025, 10, 1),
            "end_date": date(2025, 12, 31),
        }
        demand_drivers = [
            {"driver": "project_pipeline", "weight": 0.4, "trend": "increasing"},
            {"driver": "market_expansion", "weight": 0.3, "trend": "stable"},
            {"driver": "automation_impact", "weight": 0.3, "trend": "decreasing"},
        ]

        # Mock demand prediction methods
        with patch.multiple(
            planning_service,
            _gather_demand_history=AsyncMock(
                return_value={
                    "historical_periods": 12,
                    "demand_data": {
                        "monthly_avg": 150,
                        "seasonal_factors": {"q4": 1.2},
                    },
                    "correlation_factors": {"project_count": 0.8, "team_size": 0.6},
                }
            ),
            _apply_ml_demand_models=AsyncMock(
                return_value={
                    "linear_regression": {"prediction": 180, "confidence": 0.85},
                    "time_series": {"prediction": 175, "confidence": 0.78},
                    "ensemble": {"prediction": 178, "confidence": 0.82},
                }
            ),
            _apply_statistical_forecasting=AsyncMock(
                return_value={
                    "moving_average": {"prediction": 165, "trend": "increasing"},
                    "exponential_smoothing": {"prediction": 172, "seasonality": 0.15},
                }
            ),
            _combine_demand_predictions=AsyncMock(
                return_value={
                    "combined_prediction": 176,
                    "confidence_interval": {"lower": 160, "upper": 192},
                    "methodology": "weighted_ensemble",
                }
            ),
            _calculate_demand_confidence_intervals=AsyncMock(
                return_value={
                    "80_percent": {"lower": 165, "upper": 187},
                    "95_percent": {"lower": 155, "upper": 197},
                }
            ),
            _identify_demand_patterns=AsyncMock(
                return_value=[
                    {"pattern": "seasonal_q4_increase", "strength": 0.6},
                    {"pattern": "project_correlation", "strength": 0.8},
                ]
            ),
            _calculate_model_accuracy=AsyncMock(
                return_value={
                    "mape": 0.12,  # Mean Absolute Percentage Error
                    "rmse": 15.6,  # Root Mean Square Error
                    "r_squared": 0.78,
                }
            ),
            _identify_key_demand_drivers=AsyncMock(
                return_value=[
                    {
                        "driver": "project_pipeline",
                        "importance": 0.45,
                        "impact": "high",
                    },
                    {
                        "driver": "market_expansion",
                        "importance": 0.35,
                        "impact": "medium",
                    },
                ]
            ),
        ):
            # Execute
            result = await planning_service.predict_resource_demand(
                departments=departments,
                planning_horizon=planning_horizon,
                demand_drivers=demand_drivers,
            )

        # Verify response
        assert isinstance(result, ResourceDemandPredictionResponse)
        assert result.prediction_horizon == planning_horizon
        assert result.historical_data["historical_periods"] == 12
        assert result.ml_predictions["ensemble"]["prediction"] == 178
        assert result.statistical_forecasts["moving_average"]["prediction"] == 165
        assert result.combined_predictions["combined_prediction"] == 176
        assert len(result.demand_patterns) == 2
        assert result.model_accuracy["mape"] == 0.12
        assert len(result.key_drivers) == 2

    @pytest.mark.asyncio
    async def test_create_succession_plan(self, planning_service):
        """Test succession planning for critical resources"""

        succession_request = ResourceSuccessionPlanRequest(
            departments=[1, 2],
            criticality_criteria={
                "business_impact": 0.4,
                "knowledge_uniqueness": 0.3,
                "replacement_difficulty": 0.3,
            },
            business_impact_factors=[
                "revenue_impact",
                "operational_continuity",
                "team_dependencies",
            ],
            competency_requirements={
                "technical_skills": {"weight": 0.4, "threshold": 3.5},
                "leadership": {"weight": 0.3, "threshold": 3.0},
                "domain_knowledge": {"weight": 0.3, "threshold": 3.8},
            },
            readiness_criteria={
                "performance_rating": 4.0,
                "tenure_months": 18,
                "development_completion": 0.8,
            },
            succession_pool_criteria={
                "internal_candidates": 0.7,
                "external_candidates": 0.3,
                "min_pool_size": 2,
            },
            development_timeline={
                "assessment_phase": date(2025, 10, 15),
                "development_start": date(2025, 11, 1),
                "readiness_review": date(2026, 2, 1),
            },
        )

        # Mock succession planning methods
        with patch.multiple(
            planning_service,
            _identify_critical_positions=AsyncMock(
                return_value=[
                    {
                        "position_id": 1,
                        "title": "Lead Architect",
                        "criticality_score": 0.95,
                        "risk_factors": ["single_point_of_failure", "unique_knowledge"],
                    },
                    {
                        "position_id": 2,
                        "title": "Product Manager",
                        "criticality_score": 0.88,
                        "risk_factors": ["client_relationships", "domain_expertise"],
                    },
                ]
            ),
            _assess_succession_readiness=AsyncMock(
                return_value={
                    "overall_readiness": 0.65,
                    "position_readiness": {1: 0.4, 2: 0.8},
                    "gaps": ["technical_depth", "leadership_experience"],
                }
            ),
            _identify_potential_successors=AsyncMock(
                return_value=[
                    {
                        "candidate_id": 101,
                        "name": "Senior Developer A",
                        "readiness_score": 0.75,
                        "target_positions": [1],
                        "development_needs": ["architecture_design", "team_leadership"],
                    },
                    {
                        "candidate_id": 102,
                        "name": "Junior PM B",
                        "readiness_score": 0.85,
                        "target_positions": [2],
                        "development_needs": ["strategic_planning"],
                    },
                ]
            ),
            _create_successor_development_plans=AsyncMock(
                return_value=[
                    {
                        "candidate_id": 101,
                        "development_plan": {
                            "duration_months": 12,
                            "activities": [
                                "architecture_training",
                                "mentoring",
                                "project_leadership",
                            ],
                            "milestones": ["design_review_lead", "team_management"],
                        },
                    }
                ]
            ),
            _assess_succession_risks=AsyncMock(
                return_value=[
                    {
                        "risk": "candidate_retention",
                        "probability": 0.3,
                        "impact": "high",
                        "mitigation": "retention_incentives",
                    },
                    {
                        "risk": "development_timeline",
                        "probability": 0.4,
                        "impact": "medium",
                        "mitigation": "accelerated_training",
                    },
                ]
            ),
            _create_succession_transition_plans=AsyncMock(
                return_value=[
                    {
                        "position_id": 1,
                        "transition_plan": {
                            "knowledge_transfer": "6_weeks",
                            "gradual_handover": "3_months",
                            "support_period": "6_months",
                        },
                    }
                ]
            ),
            _create_succession_monitoring_framework=AsyncMock(
                return_value={
                    "review_frequency": "quarterly",
                    "progress_metrics": ["readiness_score", "competency_development"],
                    "escalation_triggers": ["readiness_decline", "candidate_departure"],
                }
            ),
            _define_succession_success_metrics=AsyncMock(
                return_value={
                    "succession_coverage": 0.9,
                    "development_completion_rate": 0.85,
                    "transition_success_rate": 0.95,
                }
            ),
        ):
            # Execute
            result = await planning_service.create_succession_plan(
                succession_request=succession_request, user_id=6
            )

        # Verify response
        assert isinstance(result, ResourceSuccessionPlanResponse)
        assert result.planning_scope == [1, 2]
        assert len(result.critical_positions) == 2
        assert result.critical_positions[0]["criticality_score"] == 0.95
        assert result.succession_readiness["overall_readiness"] == 0.65
        assert len(result.potential_successors) == 2
        assert result.potential_successors[0]["readiness_score"] == 0.75
        assert len(result.development_plans) == 1
        assert len(result.succession_risks) == 2
        assert len(result.transition_plans) == 1
        assert result.success_metrics["succession_coverage"] == 0.9
        assert result.generated_by == 6

    @pytest.mark.asyncio
    async def test_error_handling_redis_failure(
        self, planning_service, sample_planning_request
    ):
        """Test error handling when Redis operations fail"""

        # Mock Redis failure
        planning_service.redis.incr.side_effect = Exception("Redis connection failed")

        # Execute and expect exception
        with pytest.raises(Exception) as exc_info:
            await planning_service.create_resource_plan(
                planning_request=sample_planning_request, user_id=1
            )

        assert "Redis connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_helper_method_mocking(self, planning_service):
        """Test that helper methods are properly mocked"""

        # Test direct helper method calls
        result1 = await planning_service._analyze_current_resource_state([1, 2], {})
        assert result1 == {"total_resources": 150, "departments": [1, 2]}

        result2 = await planning_service._analyze_demand_requirements([], {})
        assert result2 == {
            "projected_demand": 200,
            "skills_needed": ["Python", "React"],
        }

        result3 = await planning_service._generate_capacity_plan({}, {}, {}, {})
        assert result3 == {"capacity_increase_needed": 50, "timeline": "6 months"}

    def test_recommendation_generation(self, planning_service):
        """Test planning recommendation generation"""

        capacity_plan = {"capacity_increase_needed": 30}
        skill_gaps = [{"skill": "Python", "gap_size": 5}]
        cost_analysis = {"total_cost": 500000, "roi_projection": 2.2}
        risk_assessment = {"risk_level": "medium"}

        # Execute
        recommendations = planning_service._generate_planning_recommendations(
            capacity_plan, skill_gaps, cost_analysis, risk_assessment
        )

        # Verify recommendations
        assert isinstance(recommendations, list)
        assert len(recommendations) == 2
        assert "Python" in recommendations[0]
        assert "hiring" in recommendations[1]

    def test_capacity_metrics_calculation(self, planning_service):
        """Test capacity metrics calculations"""

        # Test capacity utilization
        current_capacity = {"total_hours": 2000, "available_hours": 1700}
        demand_projection = {"required_hours": 1700}
        utilization = planning_service._calculate_capacity_utilization(
            current_capacity, demand_projection
        )
        assert utilization == 85.0

        # Test efficiency score
        optimal_allocation = {"efficiency_rating": 0.92}
        efficiency = planning_service._calculate_efficiency_score(optimal_allocation)
        assert efficiency == 92.0

        # Test cost effectiveness
        scaling_scenarios = [{"cost_benefit_ratio": 0.88}]
        cost_effectiveness = planning_service._calculate_cost_effectiveness(
            scaling_scenarios
        )
        assert cost_effectiveness == 88.0

    def test_capacity_recommendations(self, planning_service):
        """Test capacity planning recommendations"""

        capacity_gaps = [{"gap_type": "shortage", "amount": 500}]
        scaling_scenarios = [{"scenario": "hire_more", "impact": "high"}]
        optimal_allocation = {"recommendation": "balanced_approach"}

        # Execute
        recommendations = planning_service._generate_capacity_recommendations(
            capacity_gaps, scaling_scenarios, optimal_allocation
        )

        # Verify recommendations structure
        assert isinstance(recommendations, list)

    @pytest.mark.asyncio
    async def test_concurrent_planning_operations(self, planning_service):
        """Test concurrent planning operations"""

        import asyncio

        # Mock all required methods
        planning_service.redis.incr.return_value = 1
        with patch.multiple(
            planning_service,
            _analyze_current_resource_state=AsyncMock(return_value={}),
            _analyze_demand_requirements=AsyncMock(return_value={}),
            _generate_capacity_plan=AsyncMock(return_value={}),
            _identify_skill_gaps=AsyncMock(return_value=[]),
            _generate_hiring_plan=AsyncMock(return_value={}),
            _generate_training_plan=AsyncMock(return_value={}),
            _create_implementation_roadmap=AsyncMock(return_value={}),
            _calculate_plan_costs=AsyncMock(return_value={}),
            _assess_plan_risks=AsyncMock(return_value={}),
            _generate_planning_recommendations=Mock(return_value=[]),
        ):
            # Create multiple planning requests
            requests = []
            for i in range(3):
                request = ResourcePlanningRequest(
                    plan_name=f"Plan {i}",
                    planning_horizon={
                        "start_date": date(2025, 10, 1),
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
                requests.append(request)

            # Execute concurrently
            tasks = [
                planning_service.create_resource_plan(req, user_id=i + 1)
                for i, req in enumerate(requests)
            ]

            results = await asyncio.gather(*tasks)

            # Verify all completed successfully
            assert len(results) == 3
            for i, result in enumerate(results):
                assert isinstance(result, ResourcePlanningResponse)
                assert result.plan_name == f"Plan {i}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--asyncio-mode=auto"])
