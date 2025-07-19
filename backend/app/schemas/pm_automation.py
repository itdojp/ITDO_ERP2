"""PM Automation schema definitions."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProjectStructureRequest(BaseModel):
    """Request schema for project structure creation."""

    template_type: str = Field(
        ..., description="Template type (agile, waterfall, kanban)"
    )
    customizations: Optional[Dict[str, Any]] = Field(
        None, description="Custom template parameters"
    )


class ProjectStructureResponse(BaseModel):
    """Response schema for project structure creation."""

    template: str = Field(..., description="Template used")
    tasks_created: int = Field(..., description="Number of tasks created")
    tasks: List[Dict[str, Any]] = Field(..., description="Created tasks")
    milestones_created: int = Field(0, description="Number of milestones created")


class TaskAssignmentRequest(BaseModel):
    """Request schema for task assignment."""

    strategy: str = Field(..., description="Assignment strategy")
    filters: Optional[Dict[str, Any]] = Field(None, description="Task filters")
    dry_run: bool = Field(False, description="Dry run without actual assignment")


class TaskAssignmentResponse(BaseModel):
    """Response schema for task assignment."""

    status: str = Field(..., description="Assignment status")
    assigned_count: int = Field(..., description="Number of tasks assigned")
    total_tasks: int = Field(..., description="Total tasks processed")
    strategy: str = Field(..., description="Strategy used")
    assignments: List[Dict[str, Any]] = Field(..., description="Assignment details")


class ProgressReportRequest(BaseModel):
    """Request schema for progress report generation."""

    report_type: str = Field(..., description="Report type (daily, weekly, monthly)")
    include_trends: bool = Field(True, description="Include trend analysis")
    include_risks: bool = Field(True, description="Include risk analysis")
    include_recommendations: bool = Field(True, description="Include recommendations")


class ProjectStatistics(BaseModel):
    """Project statistics schema."""

    total_tasks: int = Field(..., description="Total number of tasks")
    completed_tasks: int = Field(..., description="Number of completed tasks")
    period_completed: int = Field(..., description="Tasks completed in period")
    overdue_tasks: int = Field(..., description="Number of overdue tasks")
    completion_rate: float = Field(..., description="Completion rate percentage")
    in_progress_tasks: int = Field(..., description="Tasks in progress")


class CompletionTrend(BaseModel):
    """Completion trend schema."""

    daily_completions: Dict[str, int] = Field(
        ..., description="Daily completion counts"
    )
    average_daily_completion: float = Field(..., description="Average daily completion")
    trend_direction: str = Field(..., description="Trend direction (up, down, stable)")


class ProjectRisk(BaseModel):
    """Project risk schema."""

    type: str = Field(..., description="Risk type")
    severity: str = Field(..., description="Risk severity (low, medium, high)")
    description: str = Field(..., description="Risk description")
    recommendation: str = Field(..., description="Mitigation recommendation")
    probability: Optional[float] = Field(None, description="Risk probability")


class ProjectRecommendation(BaseModel):
    """Project recommendation schema."""

    type: str = Field(..., description="Recommendation type")
    priority: str = Field(..., description="Priority level")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    impact: Optional[str] = Field(None, description="Expected impact")


class ProgressReportResponse(BaseModel):
    """Response schema for progress report."""

    project: Dict[str, Any] = Field(..., description="Project information")
    report_period: Dict[str, Any] = Field(..., description="Report period details")
    statistics: ProjectStatistics = Field(..., description="Project statistics")
    trends: CompletionTrend = Field(..., description="Completion trends")
    risks: List[ProjectRisk] = Field(..., description="Identified risks")
    recommendations: List[ProjectRecommendation] = Field(
        ..., description="Recommendations"
    )
    generated_at: datetime = Field(..., description="Report generation timestamp")
    generated_by: Optional[int] = Field(None, description="Report generator user ID")


class ScheduleOptimizationRequest(BaseModel):
    """Request schema for schedule optimization."""

    optimization_type: str = Field(..., description="Optimization type")
    constraints: Optional[Dict[str, Any]] = Field(
        None, description="Optimization constraints"
    )
    target_date: Optional[datetime] = Field(None, description="Target completion date")


class ScheduleOptimizationResponse(BaseModel):
    """Response schema for schedule optimization."""

    optimization_type: str = Field(..., description="Optimization type used")
    status: str = Field(..., description="Optimization status")
    recommendations: List[str] = Field(..., description="Optimization recommendations")
    time_saved: Optional[int] = Field(None, description="Estimated time saved in days")
    efficiency_gain: Optional[float] = Field(
        None, description="Efficiency gain percentage"
    )


class PredictiveAnalyticsRequest(BaseModel):
    """Request schema for predictive analytics."""

    prediction_type: str = Field(..., description="Prediction type")
    confidence_level: float = Field(0.8, description="Desired confidence level")
    historical_data_days: int = Field(30, description="Days of historical data to use")


class CompletionDatePrediction(BaseModel):
    """Completion date prediction schema."""

    predicted_completion: Optional[datetime] = Field(
        None, description="Predicted completion date"
    )
    confidence: str = Field(..., description="Confidence level")
    based_on: str = Field(..., description="Prediction basis")
    velocity_tasks_per_day: float = Field(..., description="Current velocity")
    factors_considered: List[str] = Field(
        default_factory=list, description="Factors considered"
    )


class BudgetForecast(BaseModel):
    """Budget forecast schema."""

    current_budget: float = Field(..., description="Current budget")
    predicted_usage: float = Field(..., description="Predicted budget usage")
    confidence: str = Field(..., description="Confidence level")
    based_on: str = Field(..., description="Forecast basis")
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors")


class RiskProbabilityPrediction(BaseModel):
    """Risk probability prediction schema."""

    risk_score: float = Field(..., description="Overall risk score")
    risk_level: str = Field(..., description="Risk level")
    confidence: str = Field(..., description="Confidence level")
    identified_risks: int = Field(..., description="Number of identified risks")
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors")


class PredictiveAnalyticsResponse(BaseModel):
    """Response schema for predictive analytics."""

    prediction_type: str = Field(..., description="Prediction type")
    completion_prediction: Optional[CompletionDatePrediction] = Field(
        None, description="Completion date prediction"
    )
    budget_forecast: Optional[BudgetForecast] = Field(
        None, description="Budget forecast"
    )
    risk_prediction: Optional[RiskProbabilityPrediction] = Field(
        None, description="Risk probability prediction"
    )
    generated_at: datetime = Field(..., description="Analysis generation timestamp")


class AutomationDashboardResponse(BaseModel):
    """Response schema for automation dashboard."""

    project_id: int = Field(..., description="Project ID")
    progress_report: ProgressReportResponse = Field(..., description="Progress report")
    completion_prediction: PredictiveAnalyticsResponse = Field(
        ..., description="Completion prediction"
    )
    risk_analysis: PredictiveAnalyticsResponse = Field(..., description="Risk analysis")
    last_updated: datetime = Field(..., description="Last update timestamp")
    automation_score: Optional[float] = Field(
        None, description="Automation effectiveness score"
    )


class ProjectTemplate(BaseModel):
    """Project template schema."""

    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    features: List[str] = Field(..., description="Template features")
    typical_duration: str = Field(..., description="Typical project duration")
    team_size: str = Field(..., description="Recommended team size")
    complexity: str = Field("medium", description="Template complexity level")


class AssignmentStrategy(BaseModel):
    """Assignment strategy schema."""

    name: str = Field(..., description="Strategy name")
    description: str = Field(..., description="Strategy description")
    best_for: str = Field(..., description="Best use case")
    considerations: List[str] = Field(..., description="Important considerations")
    effectiveness: str = Field("medium", description="Strategy effectiveness")


class TemplatesResponse(BaseModel):
    """Response schema for templates listing."""

    templates: Dict[str, ProjectTemplate] = Field(
        ..., description="Available templates"
    )
    total_templates: int = Field(..., description="Total number of templates")
    recommended_template: Optional[str] = Field(
        None, description="Recommended template"
    )


class StrategiesResponse(BaseModel):
    """Response schema for strategies listing."""

    strategies: Dict[str, AssignmentStrategy] = Field(
        ..., description="Available strategies"
    )
    total_strategies: int = Field(..., description="Total number of strategies")
    recommended_strategy: Optional[str] = Field(
        None, description="Recommended strategy"
    )


class AutomationMetrics(BaseModel):
    """Automation metrics schema."""

    tasks_automated: int = Field(..., description="Number of tasks automated")
    time_saved_hours: float = Field(..., description="Time saved in hours")
    efficiency_improvement: float = Field(
        ..., description="Efficiency improvement percentage"
    )
    error_reduction: float = Field(..., description="Error reduction percentage")
    user_satisfaction: Optional[float] = Field(
        None, description="User satisfaction score"
    )


class AutomationSummary(BaseModel):
    """Automation summary schema."""

    project_id: int = Field(..., description="Project ID")
    automation_enabled: bool = Field(..., description="Automation status")
    last_automation_run: Optional[datetime] = Field(
        None, description="Last automation run"
    )
    metrics: AutomationMetrics = Field(..., description="Automation metrics")
    active_automations: List[str] = Field(..., description="Active automation types")
    recommendations: List[str] = Field(..., description="Automation recommendations")


# Response wrapper schemas
class PMAutomationResponse(BaseModel):
    """Generic PM automation response wrapper."""

    success: bool = Field(..., description="Operation success status")
    data: Dict[str, Any] | List[Any] | str | int | float | bool | None = Field(
        ..., description="Response data"
    )
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Response timestamp"
    )
