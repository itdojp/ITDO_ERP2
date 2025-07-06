"""Dashboard schema definitions."""

from typing import List, Dict, Any, Optional
from datetime import datetime, date
from pydantic import BaseModel


class ProjectStats(BaseModel):
    """Project statistics schema."""
    total: int
    planning: int
    in_progress: int
    completed: int
    overdue: int


class TaskStats(BaseModel):
    """Task statistics schema."""
    total: int
    not_started: int
    in_progress: int
    completed: int
    on_hold: int
    overdue: int


class RecentActivity(BaseModel):
    """Recent activity schema."""
    type: str
    project_name: Optional[str] = None
    task_title: Optional[str] = None
    timestamp: datetime


class DashboardStatsResponse(BaseModel):
    """Dashboard statistics response schema."""
    project_stats: ProjectStats
    task_stats: TaskStats
    recent_activity: List[RecentActivity]


class ProgressDataPoint(BaseModel):
    """Progress data point schema."""
    date: date
    completed_projects: int
    completed_tasks: int
    total_progress: float


class ProjectProgress(BaseModel):
    """Project progress schema."""
    project_id: int
    project_name: str
    completion_percentage: float
    total_tasks: int
    completed_tasks: int
    is_overdue: bool


class ProgressDataResponse(BaseModel):
    """Progress data response schema."""
    period: str
    progress_data: List[ProgressDataPoint]
    project_progress: List[ProjectProgress]


class OverdueProject(BaseModel):
    """Overdue project schema."""
    project_id: int
    project_name: str
    end_date: date
    days_overdue: int


class OverdueTask(BaseModel):
    """Overdue task schema."""
    task_id: int
    task_title: str
    project_name: str
    end_date: date
    days_overdue: int


class UpcomingDeadline(BaseModel):
    """Upcoming deadline schema."""
    type: str  # "project" or "task"
    id: int
    name: str
    end_date: date
    days_remaining: int


class AlertsResponse(BaseModel):
    """Alerts response schema."""
    overdue_projects: List[OverdueProject]
    overdue_tasks: List[OverdueTask]
    upcoming_deadlines: List[UpcomingDeadline]