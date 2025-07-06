"""Dashboard schemas for API validation and serialization."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.types import OrganizationId, DepartmentId, UserId


class OrganizationStats(BaseModel):
    """Organization-wide statistics."""
    total_projects: int = Field(..., description="Total number of projects")
    active_projects: int = Field(..., description="Number of active projects")
    completed_projects: int = Field(..., description="Number of completed projects")
    overdue_projects: int = Field(..., description="Number of overdue projects")
    total_tasks: int = Field(..., description="Total number of tasks")
    pending_tasks: int = Field(..., description="Number of pending tasks")
    overdue_tasks: int = Field(..., description="Number of overdue tasks")
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    total_budget: Optional[Decimal] = Field(None, description="Total budget across all projects")
    total_spent: Optional[Decimal] = Field(None, description="Total amount spent")
    budget_utilization: Optional[float] = Field(None, description="Budget utilization percentage")
    
    model_config = ConfigDict(from_attributes=True)


class PersonalStats(BaseModel):
    """Personal user statistics."""
    my_projects: int = Field(..., description="Number of projects user is involved in")
    my_active_projects: int = Field(..., description="Number of active projects")
    my_tasks: int = Field(..., description="Total number of user's tasks")
    my_pending_tasks: int = Field(..., description="Number of pending tasks")
    my_overdue_tasks: int = Field(..., description="Number of overdue tasks")
    tasks_due_today: int = Field(..., description="Number of tasks due today")
    tasks_due_this_week: int = Field(..., description="Number of tasks due this week")
    completion_rate: float = Field(..., description="Task completion rate percentage")
    
    model_config = ConfigDict(from_attributes=True)


class ProjectProgressSummary(BaseModel):
    """Project progress summary for dashboard."""
    id: int
    code: str
    name: str
    status: str
    progress_percentage: int
    planned_end_date: Optional[date]
    is_overdue: bool
    days_remaining: Optional[int]
    member_count: int
    budget_usage_percentage: Optional[float]
    
    model_config = ConfigDict(from_attributes=True)


class TaskSummary(BaseModel):
    """Task summary for dashboard."""
    id: int
    title: str
    status: str
    priority: str
    due_date: Optional[date]
    is_overdue: bool
    project_id: int
    project_name: str
    assigned_to: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


class MilestoneSummary(BaseModel):
    """Milestone summary for dashboard."""
    id: int
    name: str
    due_date: date
    status: str
    is_critical: bool
    project_id: int
    project_name: str
    days_until_due: int
    
    model_config = ConfigDict(from_attributes=True)


class RecentActivity(BaseModel):
    """Recent activity item."""
    id: int
    activity_type: str = Field(..., description="Type of activity")
    description: str = Field(..., description="Activity description")
    entity_type: str = Field(..., description="Type of entity")
    entity_id: int = Field(..., description="Entity ID")
    entity_name: str = Field(..., description="Entity name")
    user_id: UserId = Field(..., description="User who performed the activity")
    user_name: str = Field(..., description="User name")
    timestamp: datetime = Field(..., description="When the activity occurred")
    
    model_config = ConfigDict(from_attributes=True)


class BudgetStatus(BaseModel):
    """Budget status information."""
    total_budget: Optional[Decimal]
    spent_amount: Optional[Decimal]
    remaining_amount: Optional[Decimal]
    utilization_percentage: Optional[float]
    is_over_budget: bool
    
    model_config = ConfigDict(from_attributes=True)


class TimelineStatus(BaseModel):
    """Timeline status information."""
    planned_start: Optional[date]
    planned_end: Optional[date]
    actual_start: Optional[date]
    actual_end: Optional[date]
    days_remaining: Optional[int]
    is_on_schedule: bool
    is_overdue: bool
    
    model_config = ConfigDict(from_attributes=True)


class ProjectDashboardStats(BaseModel):
    """Project-specific dashboard statistics."""
    project_id: int
    project_name: str
    project_code: str
    project_status: str
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    overdue_tasks: int
    total_phases: int
    completed_phases: int
    total_milestones: int
    completed_milestones: int
    overdue_milestones: int
    team_members: int
    budget_status: BudgetStatus
    timeline_status: TimelineStatus
    
    model_config = ConfigDict(from_attributes=True)


class TrendDataPoint(BaseModel):
    """Single data point for trends."""
    date: date
    value: float
    label: str
    
    model_config = ConfigDict(from_attributes=True)


class TrendData(BaseModel):
    """Trend data for charts."""
    metric_name: str
    period: str
    data_points: List[TrendDataPoint]
    total_change: float
    percentage_change: float
    
    model_config = ConfigDict(from_attributes=True)


class MainDashboardData(BaseModel):
    """Main dashboard data."""
    organization_stats: OrganizationStats
    recent_projects: List[ProjectProgressSummary]
    overdue_items: Dict[str, int]
    recent_activities: List[RecentActivity]
    budget_overview: BudgetStatus
    performance_trends: List[TrendData]
    
    model_config = ConfigDict(from_attributes=True)


class PersonalDashboardData(BaseModel):
    """Personal dashboard data."""
    personal_stats: PersonalStats
    my_projects: List[ProjectProgressSummary]
    my_tasks: List[TaskSummary]
    upcoming_milestones: List[MilestoneSummary]
    today_schedule: List[TaskSummary]
    recent_activities: List[RecentActivity]
    
    model_config = ConfigDict(from_attributes=True)


class DashboardConfigUpdate(BaseModel):
    """Dashboard configuration update."""
    layout: Optional[Dict[str, Any]] = Field(None, description="Dashboard layout settings")
    widgets: Optional[List[Dict[str, Any]]] = Field(None, description="Widget configurations")
    default_filters: Optional[Dict[str, Any]] = Field(None, description="Default filter settings")
    display_preferences: Optional[Dict[str, Any]] = Field(None, description="Display preferences")
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True
    )


class DashboardConfig(BaseModel):
    """Dashboard configuration."""
    user_id: UserId
    layout: Dict[str, Any] = Field(default_factory=dict, description="Dashboard layout settings")
    widgets: List[Dict[str, Any]] = Field(default_factory=list, description="Widget configurations")
    default_filters: Dict[str, Any] = Field(default_factory=dict, description="Default filter settings")
    display_preferences: Dict[str, Any] = Field(default_factory=dict, description="Display preferences")
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DashboardFilters(BaseModel):
    """Dashboard filter parameters."""
    organization_id: Optional[OrganizationId] = None
    department_id: Optional[DepartmentId] = None
    project_id: Optional[int] = None
    date_range: str = Field(default="month", description="Date range: today, week, month, quarter")
    status_filter: Optional[str] = None
    priority_filter: Optional[str] = None
    refresh: bool = Field(default=False, description="Force refresh cache")
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True
    )