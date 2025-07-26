"""
ITDO ERP Backend - Resource Management Integration API
Day 23: Unified resource management system integration
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.resource_analytics_api import ResourceAnalyticsService
from app.api.v1.resource_management_api import ResourceManagementService
from app.api.v1.resource_planning_api import ResourcePlanningService
from app.core.database import get_db

router = APIRouter()


class ResourceIntegrationService:
    """Unified service for complete resource management integration"""

    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.redis = redis_client

        # Initialize component services
        self.resource_service = ResourceManagementService(db, redis_client)
        self.analytics_service = ResourceAnalyticsService(db, redis_client)
        self.planning_service = ResourcePlanningService(db, redis_client)

    async def get_unified_resource_dashboard(
        self,
        user_id: int,
        time_period: str = "month",
        departments: Optional[List[int]] = None,
        include_forecasts: bool = True,
        include_optimization: bool = True,
    ) -> Dict[str, Any]:
        """Get comprehensive resource management dashboard"""

        # Calculate date ranges
        end_date = date.today()
        if time_period == "week":
            start_date = end_date - timedelta(days=7)
        elif time_period == "quarter":
            quarter_start_month = ((end_date.month - 1) // 3) * 3 + 1
            start_date = end_date.replace(month=quarter_start_month, day=1)
        elif time_period == "year":
            start_date = end_date.replace(month=1, day=1)
        else:  # month
            start_date = end_date.replace(day=1)

        # Get current resource data
        resources = await self.resource_service.get_resources(
            skip=0, limit=100, departments=departments
        )

        # Get analytics
        analytics = await self.analytics_service.get_resource_analytics(
            start_date=start_date, end_date=end_date, department_ids=departments
        )

        # Get KPIs
        kpis = await self.analytics_service.get_resource_kpis(
            time_range=time_period, compare_previous=True
        )

        # Get resource trends
        resource_ids = [r.id for r in resources.items] if resources.items else []
        trends = None
        if resource_ids:
            trends = await self.analytics_service.get_resource_trends(
                resource_ids=resource_ids[:10],  # Limit for performance
                start_date=start_date,
                end_date=end_date,
                granularity="weekly" if time_period == "month" else "monthly",
            )

        dashboard = {
            "period": {
                "start_date": start_date,
                "end_date": end_date,
                "time_range": time_period,
            },
            "summary": {
                "total_resources": analytics.total_resources,
                "average_utilization": analytics.average_utilization,
                "total_cost": analytics.total_cost,
                "efficiency_score": analytics.efficiency_score,
                "overutilized_resources": analytics.overutilized_resources,
                "underutilized_resources": analytics.underutilized_resources,
            },
            "kpis": {
                "current": kpis.current_kpis,
                "changes": kpis.kpi_changes if hasattr(kpis, "kpi_changes") else {},
                "indicators": kpis.performance_indicators,
            },
            "top_performers": analytics.top_performers,
            "cost_breakdown": analytics.cost_breakdown,
            "recommendations": analytics.recommendations,
            "trends": trends.utilization_trends if trends else [],
            "generated_at": datetime.utcnow(),
        }

        # Add forecasts if requested
        if include_forecasts and resource_ids:
            try:
                from app.schemas.resource import ResourceForecastRequest

                forecast_request = ResourceForecastRequest(
                    start_date=end_date + timedelta(days=1),
                    end_date=end_date + timedelta(days=90),
                    forecast_periods=3,
                    granularity="monthly",
                    departments=departments or [],
                    resource_types=["human"],
                    growth_assumptions={"demand_growth": 0.1},
                )
                forecast = await self.analytics_service.generate_resource_forecast(
                    forecast_request
                )
                dashboard["forecast"] = {
                    "demand_forecast": forecast.demand_forecast,
                    "capacity_forecast": forecast.capacity_forecast,
                    "gaps_and_surpluses": forecast.gaps_and_surpluses,
                    "confidence_level": forecast.confidence_level,
                }
            except Exception as e:
                dashboard["forecast"] = {
                    "error": f"Forecast generation failed: {str(e)}"
                }

        # Add optimization suggestions if requested
        if include_optimization and resource_ids:
            try:
                optimization = await self.resource_service.optimize_resources(
                    resource_ids=resource_ids[:20],  # Limit for performance
                    start_date=start_date,
                    end_date=end_date,
                    optimization_goal="efficiency",
                )
                dashboard["optimization"] = {
                    "efficiency_score": optimization.efficiency_score,
                    "cost_savings": optimization.cost_savings,
                    "recommendations": optimization.recommendations[:5],  # Top 5
                }
            except Exception as e:
                dashboard["optimization"] = {"error": f"Optimization failed: {str(e)}"}

        # Cache dashboard for 15 minutes
        cache_key = f"dashboard:{user_id}:{time_period}:{hash(str(departments))}"
        await self.redis.setex(cache_key, 900, str(dashboard))

        return dashboard

    async def create_comprehensive_resource_plan(
        self,
        planning_request: Dict[str, Any],
        user_id: int,
        include_analytics: bool = True,
    ) -> Dict[str, Any]:
        """Create comprehensive resource plan with analytics integration"""

        plan_id = str(uuid.uuid4())

        # Step 1: Analyze current state using analytics
        current_analytics = None
        if include_analytics:
            try:
                current_analytics = await self.analytics_service.get_resource_analytics(
                    start_date=date.today() - timedelta(days=30),
                    end_date=date.today(),
                    department_ids=planning_request.get("departments", []),
                )
            except Exception as e:
                current_analytics = {"error": f"Analytics failed: {str(e)}"}

        # Step 2: Create resource plan
        from app.schemas.resource import ResourcePlanningRequest

        planning_req = ResourcePlanningRequest(**planning_request)
        resource_plan = await self.planning_service.create_resource_plan(
            planning_request=planning_req, user_id=user_id
        )

        # Step 3: Generate capacity analysis
        capacity_analysis = None
        if planning_request.get("include_capacity_analysis", True):
            try:
                from app.schemas.resource import CapacityPlanningRequest

                capacity_req_data = {
                    "planning_period": planning_request["planning_horizon"],
                    "departments": planning_request["departments"],
                    "resource_types": ["human"],
                    "demand_drivers": [{"factor": "projected_growth", "impact": 1.2}],
                    "growth_assumptions": planning_request.get("growth_targets", {}),
                    "service_level_targets": {"availability": 95.0},
                    "scaling_options": [
                        {
                            "type": "hiring",
                            "cost_per_unit": 150000.0,
                            "lead_time_weeks": 8,
                        }
                    ],
                    "budget_constraints": planning_request.get(
                        "budget_constraints", {}
                    ),
                    "optimization_goals": ["minimize_cost", "maximize_utilization"],
                }
                capacity_req = CapacityPlanningRequest(**capacity_req_data)
                capacity_analysis = await self.planning_service.create_capacity_plan(
                    capacity_request=capacity_req, user_id=user_id
                )
            except Exception as e:
                capacity_analysis = {"error": f"Capacity analysis failed: {str(e)}"}

        # Step 4: Perform skill gap analysis
        skill_analysis = None
        if planning_request.get("include_skill_analysis", True):
            try:
                from app.schemas.resource import SkillGapAnalysisRequest

                skill_req_data = {
                    "departments": planning_request["departments"],
                    "resource_types": ["human"],
                    "skill_categories": ["technical", "leadership"],
                    "project_pipeline": planning_request.get(
                        "project_requirements", []
                    ),
                    "planning_horizon": planning_request["planning_horizon"],
                    "proficiency_levels": {"advanced": 3, "expert": 4},
                    "business_priorities": ["skill_development"],
                    "budget_constraints": {
                        "training_budget": planning_request.get(
                            "training_budget", 50000.0
                        )
                    },
                }
                skill_req = SkillGapAnalysisRequest(**skill_req_data)
                skill_analysis = await self.planning_service.analyze_skill_gaps(
                    skill_gap_request=skill_req, user_id=user_id
                )
            except Exception as e:
                skill_analysis = {"error": f"Skill analysis failed: {str(e)}"}

        # Step 5: Create integrated response
        comprehensive_plan = {
            "plan_id": plan_id,
            "created_at": datetime.utcnow(),
            "created_by": user_id,
            "planning_request": planning_request,
            "current_analytics": current_analytics,
            "resource_plan": {
                "plan_id": resource_plan.plan_id,
                "plan_name": resource_plan.plan_name,
                "current_state": resource_plan.current_state,
                "demand_analysis": resource_plan.demand_analysis,
                "capacity_plan": resource_plan.capacity_plan,
                "skill_gaps": resource_plan.skill_gaps,
                "hiring_plan": resource_plan.hiring_plan,
                "training_plan": resource_plan.training_plan,
                "cost_analysis": resource_plan.cost_analysis,
                "recommendations": resource_plan.recommendations,
            },
            "capacity_analysis": capacity_analysis,
            "skill_analysis": skill_analysis,
            "integration_insights": self._generate_integration_insights(
                current_analytics, resource_plan, capacity_analysis, skill_analysis
            ),
            "implementation_roadmap": self._create_implementation_roadmap(
                resource_plan, capacity_analysis, skill_analysis
            ),
            "success_metrics": self._define_success_metrics(resource_plan),
            "risk_assessment": self._assess_integrated_risks(
                resource_plan, capacity_analysis, skill_analysis
            ),
        }

        # Store comprehensive plan
        await self.redis.hset(
            f"comprehensive_plan:{plan_id}",
            mapping={"data": str(comprehensive_plan), "user_id": user_id},
        )
        await self.redis.expire(f"comprehensive_plan:{plan_id}", 86400 * 7)  # 7 days

        return comprehensive_plan

    async def execute_resource_optimization(
        self,
        optimization_request: Dict[str, Any],
        user_id: int,
        background_tasks: BackgroundTasks,
    ) -> Dict[str, Any]:
        """Execute comprehensive resource optimization workflow"""

        optimization_id = str(uuid.uuid4())

        # Step 1: Analyze current resource state
        current_state = await self.analytics_service.get_resource_analytics(
            start_date=optimization_request.get(
                "start_date", date.today() - timedelta(days=30)
            ),
            end_date=optimization_request.get("end_date", date.today()),
            resource_ids=optimization_request.get("resource_ids"),
            department_ids=optimization_request.get("department_ids"),
        )

        # Step 2: Get ROI analysis
        roi_analysis = await self.analytics_service.analyze_resource_roi(
            resource_ids=optimization_request["resource_ids"],
            start_date=optimization_request.get(
                "start_date", date.today() - timedelta(days=30)
            ),
            end_date=optimization_request.get("end_date", date.today()),
        )

        # Step 3: Optimize resource allocation
        optimization_result = await self.resource_service.optimize_resources(
            resource_ids=optimization_request["resource_ids"],
            project_ids=optimization_request.get("project_ids"),
            start_date=optimization_request.get("start_date", date.today()),
            end_date=optimization_request.get(
                "end_date", date.today() + timedelta(days=90)
            ),
            optimization_goal=optimization_request.get(
                "optimization_goal", "efficiency"
            ),
            constraints=optimization_request.get("constraints", {}),
        )

        # Step 4: Create implementation plan
        implementation_plan = {
            "optimization_id": optimization_id,
            "phases": [
                {
                    "phase": 1,
                    "name": "Immediate Optimizations",
                    "duration_days": 7,
                    "actions": [
                        action
                        for action in optimization_result.recommendations
                        if "immediate" in action or "urgent" in action
                    ],
                },
                {
                    "phase": 2,
                    "name": "Medium-term Adjustments",
                    "duration_days": 30,
                    "actions": [
                        action
                        for action in optimization_result.recommendations
                        if "training" in action or "reallocation" in action
                    ],
                },
                {
                    "phase": 3,
                    "name": "Strategic Changes",
                    "duration_days": 90,
                    "actions": [
                        action
                        for action in optimization_result.recommendations
                        if "hiring" in action or "restructure" in action
                    ],
                },
            ],
            "expected_benefits": {
                "cost_savings": optimization_result.cost_savings,
                "efficiency_improvement": optimization_result.efficiency_score
                - current_state.efficiency_score,
                "utilization_improvement": self._calculate_utilization_improvement(
                    current_state, optimization_result
                ),
            },
            "implementation_complexity": optimization_result.implementation_complexity,
            "timeline_estimate": "90 days",
            "success_criteria": [
                f"Achieve {optimization_result.efficiency_score}% efficiency score",
                f"Reduce costs by ${optimization_result.cost_savings}",
                "Improve resource utilization by 10%",
            ],
        }

        # Step 5: Create monitoring framework
        monitoring_framework = {
            "kpis": [
                {"name": "Resource Utilization", "target": 85.0, "frequency": "weekly"},
                {"name": "Cost per Hour", "target": 100.0, "frequency": "monthly"},
                {
                    "name": "Efficiency Score",
                    "target": optimization_result.efficiency_score,
                    "frequency": "monthly",
                },
            ],
            "checkpoints": [
                {
                    "milestone": "Phase 1 Complete",
                    "target_date": date.today() + timedelta(days=7),
                },
                {
                    "milestone": "Phase 2 Complete",
                    "target_date": date.today() + timedelta(days=37),
                },
                {
                    "milestone": "Optimization Complete",
                    "target_date": date.today() + timedelta(days=90),
                },
            ],
            "alerts": [
                {"condition": "utilization < 70%", "action": "rebalance_workload"},
                {"condition": "cost_variance > 15%", "action": "review_allocations"},
            ],
        }

        optimization_execution = {
            "optimization_id": optimization_id,
            "created_at": datetime.utcnow(),
            "created_by": user_id,
            "status": "planned",
            "current_state": current_state,
            "roi_analysis": roi_analysis,
            "optimization_result": optimization_result,
            "implementation_plan": implementation_plan,
            "monitoring_framework": monitoring_framework,
            "progress": {
                "phase": 0,
                "completion_percentage": 0.0,
                "completed_actions": [],
                "pending_actions": sum(
                    len(phase["actions"]) for phase in implementation_plan["phases"]
                ),
            },
        }

        # Store optimization execution plan
        await self.redis.hset(
            f"optimization_execution:{optimization_id}",
            mapping={"data": str(optimization_execution), "user_id": user_id},
        )
        await self.redis.expire(
            f"optimization_execution:{optimization_id}", 86400 * 30
        )  # 30 days

        # Schedule background monitoring
        background_tasks.add_task(
            self._start_optimization_monitoring, optimization_id, monitoring_framework
        )

        return optimization_execution

    async def get_resource_health_status(
        self, departments: Optional[List[int]] = None, include_predictions: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive resource management system health status"""

        # Get current date range
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        # Check resource management service health
        try:
            resource_stats = await self.resource_service.get_resource_statistics()
            resource_health = "healthy"
        except Exception:
            resource_stats = None
            resource_health = "critical"

        # Check analytics service health
        try:
            analytics_kpis = await self.analytics_service.get_resource_kpis(
                "month", False
            )
            analytics_health = "healthy"
        except Exception:
            analytics_kpis = None
            analytics_health = "critical"

        # Check planning service health
        try:
            # Test planning service with minimal request
            await self.planning_service.predict_resource_demand(
                departments=departments or [1],
                planning_horizon={"start_date": start_date, "end_date": end_date},
                demand_drivers=[],
            )
            planning_health = "healthy"
        except Exception:
            planning_health = "critical"

        # Check Redis health
        try:
            await self.redis.ping()
            redis_health = "healthy"
        except Exception:
            redis_health = "critical"

        # Check database health
        try:
            await self.db.execute(text("SELECT 1"))
            db_health = "healthy"
        except Exception:
            db_health = "critical"

        # Determine overall health
        component_healths = [
            resource_health,
            analytics_health,
            planning_health,
            redis_health,
            db_health,
        ]
        if "critical" in component_healths:
            overall_health = "critical"
        elif resource_health == "degraded" or analytics_health == "degraded":
            overall_health = "degraded"
        else:
            overall_health = "healthy"

        health_status = {
            "overall_status": overall_health,
            "timestamp": datetime.utcnow(),
            "components": {
                "resource_management": resource_health,
                "analytics": analytics_health,
                "planning": planning_health,
                "redis": redis_health,
                "database": db_health,
            },
            "metrics": {
                "total_resources": resource_stats.total_resources
                if resource_stats
                else 0,
                "average_utilization": resource_stats.average_utilization
                if resource_stats
                else 0,
                "system_efficiency": analytics_kpis.current_kpis.get(
                    "efficiency_score", 0
                )
                if analytics_kpis
                else 0,
            },
            "issues": [],
            "recommendations": [],
        }

        # Add issues and recommendations based on health
        if overall_health == "critical":
            health_status["issues"].append(
                {
                    "severity": "high",
                    "component": "system",
                    "message": "Critical system components are failing",
                    "impact": "Resource management operations may be unavailable",
                }
            )
            health_status["recommendations"].append(
                "Immediate system maintenance required"
            )

        if resource_stats and resource_stats.average_utilization < 60:
            health_status["issues"].append(
                {
                    "severity": "medium",
                    "component": "utilization",
                    "message": f"Low resource utilization: {resource_stats.average_utilization}%",
                    "impact": "Potential resource waste",
                }
            )
            health_status["recommendations"].append(
                "Review resource allocation and consider optimization"
            )

        # Add predictions if requested
        if include_predictions and overall_health != "critical":
            try:
                # Predict system load for next 30 days
                predictions = {
                    "resource_demand_trend": "increasing",
                    "expected_utilization": 82.5,
                    "capacity_warnings": [],
                    "optimization_opportunities": 3,
                }
                health_status["predictions"] = predictions
            except Exception:
                health_status["predictions"] = {"error": "Prediction generation failed"}

        return health_status

    # Helper methods
    def _generate_integration_insights(
        self,
        analytics: Any,
        resource_plan: Any,
        capacity_analysis: Any,
        skill_analysis: Any,
    ) -> List[Dict[str, Any]]:
        """Generate insights from integrated analysis"""

        insights = []

        # Analytics-based insights
        if analytics and not isinstance(analytics, dict):
            if analytics.underutilized_resources > 0:
                insights.append(
                    {
                        "type": "utilization",
                        "severity": "medium",
                        "message": f"{analytics.underutilized_resources} resources are underutilized",
                        "recommendation": "Consider workload redistribution or capacity reduction",
                        "impact": "cost_optimization",
                    }
                )

        # Planning-based insights
        if resource_plan and hasattr(resource_plan, "skill_gaps"):
            critical_gaps = [
                gap
                for gap in resource_plan.skill_gaps
                if gap.get("priority", "") == "high"
            ]
            if critical_gaps:
                insights.append(
                    {
                        "type": "skills",
                        "severity": "high",
                        "message": f"{len(critical_gaps)} critical skill gaps identified",
                        "recommendation": "Prioritize training or hiring for critical skills",
                        "impact": "project_delivery",
                    }
                )

        # Capacity-based insights
        if capacity_analysis and not isinstance(capacity_analysis, dict):
            if (
                hasattr(capacity_analysis, "capacity_gaps")
                and capacity_analysis.capacity_gaps
            ):
                insights.append(
                    {
                        "type": "capacity",
                        "severity": "high",
                        "message": "Capacity shortfalls identified in planning period",
                        "recommendation": "Begin scaling preparations early",
                        "impact": "service_delivery",
                    }
                )

        return insights

    def _create_implementation_roadmap(
        self, resource_plan: Any, capacity_analysis: Any, skill_analysis: Any
    ) -> Dict[str, Any]:
        """Create implementation roadmap for integrated plan"""

        roadmap_phases = []

        # Phase 1: Immediate actions (0-30 days)
        phase1_actions = []
        if resource_plan and hasattr(resource_plan, "recommendations"):
            urgent_actions = [
                rec
                for rec in resource_plan.recommendations
                if "immediate" in rec.lower()
            ]
            phase1_actions.extend(urgent_actions)

        roadmap_phases.append(
            {
                "phase": 1,
                "name": "Immediate Implementation",
                "duration": "0-30 days",
                "actions": phase1_actions
                or ["Begin resource assessment", "Identify quick wins"],
                "success_criteria": [
                    "Quick wins implemented",
                    "Baseline metrics established",
                ],
            }
        )

        # Phase 2: Medium-term actions (1-3 months)
        phase2_actions = []
        if skill_analysis and not isinstance(skill_analysis, dict):
            if hasattr(skill_analysis, "development_strategies"):
                phase2_actions.extend(
                    [
                        f"Implement {strategy.get('strategy', '')}"
                        for strategy in skill_analysis.development_strategies[:3]
                    ]
                )

        roadmap_phases.append(
            {
                "phase": 2,
                "name": "Skill Development & Training",
                "duration": "1-3 months",
                "actions": phase2_actions
                or ["Launch training programs", "Begin hiring process"],
                "success_criteria": [
                    "Training programs active",
                    "Hiring pipeline established",
                ],
            }
        )

        # Phase 3: Long-term actions (3-6 months)
        roadmap_phases.append(
            {
                "phase": 3,
                "name": "Strategic Optimization",
                "duration": "3-6 months",
                "actions": [
                    "Complete capacity scaling",
                    "Achieve target utilization",
                    "Optimize resource allocation",
                ],
                "success_criteria": [
                    "All skill gaps addressed",
                    "Target efficiency achieved",
                    "Full plan implementation",
                ],
            }
        )

        return {
            "total_duration": "6 months",
            "phases": roadmap_phases,
            "critical_path": [
                "Resource assessment",
                "Skill development",
                "Capacity optimization",
            ],
            "milestones": [
                {"name": "Phase 1 Complete", "target": "30 days"},
                {"name": "Phase 2 Complete", "target": "90 days"},
                {"name": "Full Implementation", "target": "180 days"},
            ],
        }

    def _define_success_metrics(self, resource_plan: Any) -> Dict[str, Any]:
        """Define success metrics for integrated plan"""

        return {
            "quantitative_metrics": [
                {"name": "Resource Utilization", "target": 85.0, "unit": "percentage"},
                {"name": "Cost Efficiency", "target": 95.0, "unit": "score"},
                {"name": "Skill Gap Closure", "target": 90.0, "unit": "percentage"},
                {"name": "Project Delivery", "target": 100.0, "unit": "percentage"},
            ],
            "qualitative_metrics": [
                {"name": "Resource Satisfaction", "target": "4.0/5.0"},
                {"name": "System Adoption", "target": "High"},
                {"name": "Process Efficiency", "target": "Improved"},
            ],
            "business_outcomes": [
                {"name": "Cost Reduction", "target": "10-15%"},
                {"name": "Productivity Increase", "target": "20%"},
                {"name": "Time to Market", "target": "Reduced by 25%"},
            ],
        }

    def _assess_integrated_risks(
        self, resource_plan: Any, capacity_analysis: Any, skill_analysis: Any
    ) -> Dict[str, Any]:
        """Assess risks for integrated plan"""

        risks = [
            {
                "risk": "Talent Acquisition Delays",
                "probability": "medium",
                "impact": "high",
                "mitigation": "Multiple recruitment channels, contractor backup",
                "owner": "HR Department",
            },
            {
                "risk": "Training Program Effectiveness",
                "probability": "low",
                "impact": "medium",
                "mitigation": "Proven training providers, progress monitoring",
                "owner": "Learning & Development",
            },
            {
                "risk": "Budget Overruns",
                "probability": "medium",
                "impact": "high",
                "mitigation": "Regular budget reviews, contingency planning",
                "owner": "Finance Team",
            },
            {
                "risk": "Technology Integration Issues",
                "probability": "low",
                "impact": "medium",
                "mitigation": "Phased rollout, extensive testing",
                "owner": "IT Department",
            },
        ]

        return {
            "overall_risk_level": "medium",
            "identified_risks": risks,
            "risk_mitigation_plan": {
                "monitoring_frequency": "weekly",
                "escalation_criteria": [
                    "high impact risks materialize",
                    "multiple medium risks occur",
                ],
                "contingency_budget": "15% of total budget",
            },
        }

    def _calculate_utilization_improvement(
        self, current_state: Any, optimization_result: Any
    ) -> float:
        """Calculate expected utilization improvement"""

        if not current_state or not optimization_result:
            return 0.0

        current_utilization = getattr(current_state, "average_utilization", 75.0)
        target_efficiency = getattr(optimization_result, "efficiency_score", 85.0)

        # Estimate utilization improvement based on efficiency gain
        return min(
            target_efficiency - current_utilization, 15.0
        )  # Cap at 15% improvement

    async def _start_optimization_monitoring(
        self, optimization_id: str, monitoring_framework: Dict[str, Any]
    ):
        """Start background monitoring for optimization execution"""

        # This would typically integrate with a job scheduler
        # For now, we'll just store the monitoring configuration
        await self.redis.hset(
            f"monitoring:{optimization_id}",
            mapping={
                "framework": str(monitoring_framework),
                "status": "active",
                "started_at": datetime.utcnow().isoformat(),
            },
        )
        await self.redis.expire(f"monitoring:{optimization_id}", 86400 * 90)  # 90 days


# Mock authentication dependency
async def get_current_user():
    return {"id": 1, "username": "admin", "department_ids": [1, 2]}


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_unified_dashboard(
    time_period: str = Query(
        "month", description="Time period: week, month, quarter, year"
    ),
    departments: Optional[str] = Query(
        None, description="Comma-separated department IDs"
    ),
    include_forecasts: bool = Query(True, description="Include demand forecasts"),
    include_optimization: bool = Query(
        True, description="Include optimization suggestions"
    ),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get unified resource management dashboard"""

    department_list = None
    if departments:
        department_list = [int(x.strip()) for x in departments.split(",")]

    redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=False)
    service = ResourceIntegrationService(db, redis_client)

    return await service.get_unified_resource_dashboard(
        user_id=current_user["id"],
        time_period=time_period,
        departments=department_list,
        include_forecasts=include_forecasts,
        include_optimization=include_optimization,
    )


@router.post("/comprehensive-plan", response_model=Dict[str, Any])
async def create_comprehensive_plan(
    planning_request: Dict[str, Any],
    include_analytics: bool = Query(True, description="Include current analytics"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create comprehensive resource plan with full integration"""

    redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=False)
    service = ResourceIntegrationService(db, redis_client)

    return await service.create_comprehensive_resource_plan(
        planning_request=planning_request,
        user_id=current_user["id"],
        include_analytics=include_analytics,
    )


@router.post("/optimization-execution", response_model=Dict[str, Any])
async def execute_optimization(
    optimization_request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Execute comprehensive resource optimization workflow"""

    redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=False)
    service = ResourceIntegrationService(db, redis_client)

    return await service.execute_resource_optimization(
        optimization_request=optimization_request,
        user_id=current_user["id"],
        background_tasks=background_tasks,
    )


@router.get("/health", response_model=Dict[str, Any])
async def get_system_health(
    departments: Optional[str] = Query(
        None, description="Comma-separated department IDs"
    ),
    include_predictions: bool = Query(True, description="Include health predictions"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get comprehensive resource management system health status"""

    department_list = None
    if departments:
        department_list = [int(x.strip()) for x in departments.split(",")]

    redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=False)
    service = ResourceIntegrationService(db, redis_client)

    return await service.get_resource_health_status(
        departments=department_list, include_predictions=include_predictions
    )


@router.get("/health-check")
async def health_check():
    """Simple health check for resource integration API"""
    return {
        "status": "healthy",
        "service": "resource_integration",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
    }
