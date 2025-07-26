"""
Resource Management Schemas
Day 21-22: Pydantic schemas for resource management APIs
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Base Resource Schemas
class ResourceBase(BaseModel):
    code: str = Field(..., description="Unique resource code")
    name: str = Field(..., description="Resource name")
    type: str = Field(
        ...,
        description="Resource type: human, equipment, software, facility, material, budget",
    )
    status: str = Field(
        ..., description="Resource status: available, allocated, maintenance, retired"
    )
    capacity: float = Field(
        ..., description="Resource capacity (hours per week for human resources)"
    )
    hourly_rate: Optional[Decimal] = Field(
        None, description="Hourly rate for cost calculations"
    )
    availability_start: Optional[date] = Field(
        None, description="Availability start date"
    )
    availability_end: Optional[date] = Field(None, description="Availability end date")
    skills: List[str] = Field(default=[], description="List of skills or capabilities")
    location: Optional[str] = Field(None, description="Resource location")
    department_id: Optional[int] = Field(None, description="Department ID")
    manager_id: Optional[int] = Field(None, description="Manager user ID")


class ResourceCreate(ResourceBase):
    pass


class ResourceUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    capacity: Optional[float] = None
    hourly_rate: Optional[Decimal] = None
    availability_start: Optional[date] = None
    availability_end: Optional[date] = None
    skills: Optional[List[str]] = None
    location: Optional[str] = None
    department_id: Optional[int] = None
    manager_id: Optional[int] = None


class ResourceResponse(ResourceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: int
    updated_by: Optional[int] = None
    is_deleted: bool = False

    class Config:
        from_attributes = True


# Resource Allocation Schemas
class ResourceAllocationBase(BaseModel):
    resource_id: int = Field(..., description="Resource ID")
    project_id: Optional[int] = Field(None, description="Project ID")
    task_id: Optional[int] = Field(None, description="Task ID")
    allocation_percentage: float = Field(
        ..., description="Allocation percentage (0-100)"
    )
    start_date: date = Field(..., description="Allocation start date")
    end_date: date = Field(..., description="Allocation end date")
    hourly_rate: Optional[Decimal] = Field(
        None, description="Allocation-specific hourly rate"
    )
    notes: Optional[str] = Field(None, description="Allocation notes")


class ResourceAllocationCreate(ResourceAllocationBase):
    pass


class ResourceAllocationUpdate(BaseModel):
    allocation_percentage: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    hourly_rate: Optional[Decimal] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class ResourceAllocationResponse(ResourceAllocationBase):
    id: int
    status: str = Field(default="active", description="Allocation status")
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: int

    class Config:
        from_attributes = True


# Resource Utilization Schemas
class ResourceUtilizationResponse(BaseModel):
    resource_id: int
    period_start: date
    period_end: date
    total_allocations: int
    average_utilization_percentage: float
    peak_utilization_percentage: float
    minimum_utilization_percentage: float
    total_allocated_hours: float
    actual_hours_worked: Optional[float] = None
    efficiency_score: float
    utilization_trend: str  # increasing, decreasing, stable
    overallocation_periods: int
    underutilization_periods: int


class ResourceStatisticsResponse(BaseModel):
    total_resources: int
    available_resources: int
    allocated_resources: int
    maintenance_resources: int
    average_utilization: float
    total_capacity_hours: float
    total_allocated_hours: float
    capacity_utilization_percentage: float
    top_utilized_resources: List[Dict[str, Any]]
    underutilized_resources: List[Dict[str, Any]]
    cost_summary: Dict[str, Decimal]
    generated_at: datetime


# Resource Optimization Schemas
class ResourceOptimizationRequest(BaseModel):
    resource_ids: List[int] = Field(..., description="Resources to optimize")
    project_ids: Optional[List[int]] = Field(None, description="Projects to consider")
    start_date: date = Field(..., description="Optimization start date")
    end_date: date = Field(..., description="Optimization end date")
    optimization_goal: str = Field(
        ..., description="Optimization goal: efficiency, cost, time, balance"
    )
    constraints: Dict[str, Any] = Field(
        default={}, description="Optimization constraints"
    )


class ResourceOptimizationResponse(BaseModel):
    optimization_goal: str
    optimized_allocations: List[Dict[str, Any]]
    efficiency_score: float
    cost_savings: float
    time_savings_days: int
    resource_utilization_improvement: float
    implementation_complexity: str
    recommendations: List[str]
    generated_at: datetime


# Resource Analytics Schemas
class ResourceAnalyticsResponse(BaseModel):
    period_start: date
    period_end: date
    total_resources: int
    average_utilization: float
    total_cost: Decimal
    efficiency_score: float
    overutilized_resources: int
    underutilized_resources: int
    top_performers: List[Dict[str, Any]]
    cost_breakdown: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    generated_at: datetime


class ResourceTrendAnalysisResponse(BaseModel):
    resource_ids: List[int]
    period_start: date
    period_end: date
    granularity: str
    utilization_trends: List[Dict[str, Any]]
    cost_trends: List[Dict[str, Any]]
    forecast: List[Dict[str, Any]]
    trend_summary: Dict[str, Any]
    generated_at: datetime


class ResourceKPIResponse(BaseModel):
    time_range: str
    period_start: date
    period_end: date
    current_kpis: Dict[str, float]
    previous_kpis: Optional[Dict[str, float]]
    kpi_changes: Dict[str, float]
    performance_indicators: List[Dict[str, Any]]
    generated_at: datetime


class ResourceForecastRequest(BaseModel):
    start_date: date
    end_date: date
    forecast_periods: int
    granularity: str = "monthly"
    departments: Optional[List[int]] = None
    resource_types: Optional[List[str]] = None
    growth_assumptions: Dict[str, float] = {}
    constraints: Dict[str, Any] = {}


class ResourceForecastResponse(BaseModel):
    forecast_start: date
    forecast_periods: int
    granularity: str
    demand_forecast: List[Dict[str, Any]]
    capacity_forecast: List[Dict[str, Any]]
    gaps_and_surpluses: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    confidence_level: float
    methodology: str
    generated_at: datetime


class ResourceBenchmarkResponse(BaseModel):
    benchmark_type: str
    resource_comparisons: List[Dict[str, Any]]
    benchmark_data: Dict[str, Any]
    overall_performance: Dict[str, Any]
    generated_at: datetime


class ResourceCapacityForecastResponse(BaseModel):
    forecast_period: Dict[str, date]
    current_capacity: Dict[str, Any]
    projected_capacity: List[Dict[str, Any]]
    capacity_recommendations: List[Dict[str, Any]]
    generated_at: datetime


class ResourceROIAnalysisResponse(BaseModel):
    resource_analyses: List[Dict[str, Any]]
    overall_roi: float
    top_performing_resources: List[Dict[str, Any]]
    underperforming_resources: List[Dict[str, Any]]
    optimization_opportunities: List[Dict[str, Any]]
    investment_recommendations: List[Dict[str, Any]]
    generated_at: datetime


class ResourceUtilizationTrendResponse(BaseModel):
    resource_id: int
    trend_data: List[Dict[str, Any]]
    trend_direction: str
    seasonal_patterns: List[Dict[str, Any]]
    forecast: List[Dict[str, Any]]
    generated_at: datetime


# Resource Planning Schemas
class ResourcePlanningRequest(BaseModel):
    plan_name: str
    planning_horizon: Dict[str, date]
    departments: List[int]
    project_requirements: List[Dict[str, Any]]
    required_skills: List[str]
    growth_targets: Dict[str, float]
    budget_constraints: Dict[str, Decimal]
    timeline_constraints: Dict[str, date]
    priority_projects: List[int]
    training_budget: Optional[Decimal] = None
    constraints: Dict[str, Any] = {}


class ResourcePlanningResponse(BaseModel):
    plan_id: int
    plan_name: str
    planning_horizon: Dict[str, date]
    current_state: Dict[str, Any]
    demand_analysis: Dict[str, Any]
    capacity_plan: Dict[str, Any]
    skill_gaps: List[Dict[str, Any]]
    hiring_plan: Dict[str, Any]
    training_plan: Dict[str, Any]
    implementation_roadmap: Dict[str, Any]
    cost_analysis: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    recommendations: List[str]
    created_at: datetime
    created_by: int


class CapacityPlanningRequest(BaseModel):
    planning_period: Dict[str, date]
    departments: List[int]
    resource_types: List[str]
    demand_drivers: List[Dict[str, Any]]
    growth_assumptions: Dict[str, float]
    service_level_targets: Dict[str, float]
    scaling_options: List[Dict[str, Any]]
    budget_constraints: Dict[str, Decimal]
    optimization_goals: List[str]
    implementation_timeline: Dict[str, date]


class CapacityPlanningResponse(BaseModel):
    planning_period: Dict[str, date]
    current_capacity: Dict[str, Any]
    demand_projection: Dict[str, Any]
    capacity_gaps: List[Dict[str, Any]]
    scaling_scenarios: List[Dict[str, Any]]
    optimal_allocation: Dict[str, Any]
    capacity_roadmap: Dict[str, Any]
    performance_metrics: Dict[str, float]
    recommendations: List[Dict[str, Any]]
    generated_at: datetime
    generated_by: int


class ResourceScenarioRequest(BaseModel):
    scenario_name: str
    baseline_demand: Dict[str, Any]
    baseline_constraints: Dict[str, Any]
    scenarios: List[Dict[str, Any]]
    planning_horizon: Dict[str, date]
    decision_criteria: List[str]
    cost_parameters: Dict[str, float]


class ResourceScenarioResponse(BaseModel):
    baseline_scenario: Dict[str, Any]
    analyzed_scenarios: List[Dict[str, Any]]
    scenario_comparison: Dict[str, Any]
    recommended_scenario: Dict[str, Any]
    sensitivity_analysis: Dict[str, Any]
    decision_support: Dict[str, Any]
    generated_at: datetime
    generated_by: int


class SkillGapAnalysisRequest(BaseModel):
    departments: List[int]
    resource_types: List[str]
    skill_categories: List[str]
    project_pipeline: List[Dict[str, Any]]
    technology_roadmap: Dict[str, Any]
    planning_horizon: Dict[str, date]
    proficiency_levels: Dict[str, int]
    business_priorities: List[str]
    urgency_factors: Dict[str, float]
    development_preferences: Dict[str, Any]
    learning_resources: List[Dict[str, Any]]
    budget_constraints: Dict[str, Decimal]
    timeline_constraints: Dict[str, date]


class SkillGapAnalysisResponse(BaseModel):
    analysis_period: Dict[str, date]
    current_skills: Dict[str, Any]
    future_requirements: Dict[str, Any]
    skill_gaps: List[Dict[str, Any]]
    development_strategies: List[Dict[str, Any]]
    learning_paths: List[Dict[str, Any]]
    investment_analysis: Dict[str, Any]
    development_risks: List[Dict[str, Any]]
    success_metrics: Dict[str, Any]
    implementation_timeline: Dict[str, Any]
    generated_at: datetime
    generated_by: int


class ResourceBudgetPlanRequest(BaseModel):
    planning_period: Dict[str, date]
    departments: List[int]
    total_budget: Decimal
    historical_periods: int
    cost_categories: List[str]
    growth_assumptions: Dict[str, float]
    inflation_rates: Dict[str, float]
    allocation_priorities: Dict[str, float]
    constraints: Dict[str, Any]
    cash_flow_constraints: Dict[str, Any]
    optimization_targets: Dict[str, float]
    risk_factors: List[Dict[str, Any]]
    contingency_percentage: float
    value_drivers: List[Dict[str, Any]]


class ResourceBudgetPlanResponse(BaseModel):
    planning_period: Dict[str, date]
    total_budget: Decimal
    historical_analysis: Dict[str, Any]
    cost_projections: Dict[str, Any]
    budget_allocation: Dict[str, Any]
    phased_plan: Dict[str, Any]
    optimization_opportunities: List[Dict[str, Any]]
    contingency_plans: List[Dict[str, Any]]
    roi_projections: Dict[str, Any]
    variance_analysis: Dict[str, Any]
    monitoring_framework: Dict[str, Any]
    generated_at: datetime
    generated_by: int


class ResourceDemandPredictionResponse(BaseModel):
    prediction_horizon: Dict[str, date]
    historical_data: Dict[str, Any]
    ml_predictions: Dict[str, Any]
    statistical_forecasts: Dict[str, Any]
    combined_predictions: Dict[str, Any]
    confidence_intervals: Dict[str, Any]
    demand_patterns: List[Dict[str, Any]]
    model_accuracy: Dict[str, float]
    key_drivers: List[Dict[str, Any]]
    generated_at: datetime


class ResourceSuccessionPlanRequest(BaseModel):
    departments: List[int]
    criticality_criteria: Dict[str, float]
    business_impact_factors: List[str]
    competency_requirements: Dict[str, Any]
    readiness_criteria: Dict[str, float]
    succession_pool_criteria: Dict[str, Any]
    development_timeline: Dict[str, date]


class ResourceSuccessionPlanResponse(BaseModel):
    planning_scope: List[int]
    critical_positions: List[Dict[str, Any]]
    succession_readiness: Dict[str, Any]
    potential_successors: List[Dict[str, Any]]
    development_plans: List[Dict[str, Any]]
    succession_risks: List[Dict[str, Any]]
    transition_plans: List[Dict[str, Any]]
    monitoring_framework: Dict[str, Any]
    success_metrics: Dict[str, Any]
    generated_at: datetime
    generated_by: int


# List and pagination schemas
class ResourceListResponse(BaseModel):
    items: List[ResourceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ResourceAllocationListResponse(BaseModel):
    items: List[ResourceAllocationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
