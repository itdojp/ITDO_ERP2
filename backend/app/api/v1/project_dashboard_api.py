"""
ITDO ERP Backend - Project Dashboard API
Day 17: Project Dashboard Implementation (Requirements 2.3)
Complete project overview, analytics, and KPI monitoring dashboard
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.project import Project
from app.models.task import Task
from app.models.user import User


# Mock authentication dependency
async def get_current_user() -> User:
    """Mock current user for dashboard APIs"""
    from unittest.mock import Mock

    mock_user = Mock()
    mock_user.id = "00000000-0000-0000-0000-000000000001"
    return mock_user


router = APIRouter(prefix="/api/v1/dashboard", tags=["project-dashboard"])


# Dashboard Data Models
class ProjectHealthStatus(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"


class TimeRange(str, Enum):
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class KPIMetric(BaseModel):
    """Key Performance Indicator metric"""

    name: str
    value: Union[int, float, Decimal]
    unit: str
    previous_value: Optional[Union[int, float, Decimal]] = None
    change_percentage: Optional[float] = None
    trend: str = "stable"  # up, down, stable
    target: Optional[Union[int, float, Decimal]] = None
    status: str = "normal"  # normal, warning, critical


class ProjectSummaryCard(BaseModel):
    """Project summary card for dashboard"""

    id: int
    name: str
    code: str
    status: str
    priority: str
    progress_percentage: float
    health_status: ProjectHealthStatus
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[Decimal] = None
    spent: Optional[Decimal] = None
    team_size: int
    active_tasks: int
    completed_tasks: int
    overdue_tasks: int
    risk_level: str = "low"  # low, medium, high
    last_activity: Optional[datetime] = None


class TaskDistribution(BaseModel):
    """Task distribution statistics"""

    todo: int
    in_progress: int
    review: int
    completed: int
    cancelled: int
    total: int


class ResourceUtilization(BaseModel):
    """Resource utilization statistics"""

    total_capacity: float
    allocated_hours: float
    utilized_hours: float
    utilization_percentage: float
    overtime_hours: float
    efficiency_score: float


class BudgetAnalysis(BaseModel):
    """Budget analysis data"""

    total_budget: Decimal
    allocated_budget: Decimal
    spent_amount: Decimal
    remaining_budget: Decimal
    burn_rate: Decimal
    projected_spend: Decimal
    budget_health: str  # healthy, warning, critical
    variance_percentage: float


class TeamPerformance(BaseModel):
    """Team performance metrics"""

    total_members: int
    active_members: int
    average_productivity: float
    collaboration_score: float
    satisfaction_score: float
    top_performers: List[Dict[str, Any]] = Field(default_factory=list)
    underperformers: List[Dict[str, Any]] = Field(default_factory=list)


class ProjectAlert(BaseModel):
    """Project alert/notification"""

    id: str
    type: str  # deadline, budget, quality, team
    severity: str  # info, warning, critical
    title: str
    message: str
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    created_at: datetime
    is_read: bool = False
    action_required: bool = False


class DashboardOverview(BaseModel):
    """Main dashboard overview response"""

    user_id: int
    organization_id: Optional[int] = None
    time_range: TimeRange
    generated_at: datetime

    # KPIs
    key_metrics: List[KPIMetric]

    # Project summaries
    total_projects: int
    active_projects: int
    projects_summary: List[ProjectSummaryCard]

    # Task analytics
    task_distribution: TaskDistribution

    # Resource analytics
    resource_utilization: ResourceUtilization

    # Budget analytics
    budget_analysis: BudgetAnalysis

    # Team analytics
    team_performance: TeamPerformance

    # Alerts and notifications
    alerts: List[ProjectAlert]

    # Charts data
    charts_data: Dict[str, Any] = Field(default_factory=dict)


class ProjectDetailsDashboard(BaseModel):
    """Detailed project dashboard"""

    project: ProjectSummaryCard
    timeline_data: Dict[str, Any]
    task_breakdown: Dict[str, int]
    team_workload: List[Dict[str, Any]]
    milestone_progress: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    recent_activities: List[Dict[str, Any]]
    performance_trends: Dict[str, List[float]]
    budget_breakdown: Dict[str, Decimal]


class DashboardFilters(BaseModel):
    """Dashboard filtering options"""

    time_range: TimeRange = TimeRange.MONTH
    project_ids: Optional[List[int]] = None
    status_filter: Optional[List[str]] = None
    priority_filter: Optional[List[str]] = None
    team_member_filter: Optional[List[int]] = None
    department_filter: Optional[List[int]] = None


# Project Dashboard Service
class ProjectDashboardService:
    """Service for project dashboard operations"""

    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.redis = redis_client

    async def get_dashboard_overview(
        self, user_id: int, filters: DashboardFilters = DashboardFilters()
    ) -> DashboardOverview:
        """Get complete dashboard overview"""

        # Get projects based on filters
        projects = await self._get_filtered_projects(filters)

        # Calculate KPIs
        key_metrics = await self._calculate_key_metrics(projects, filters.time_range)

        # Get project summaries
        projects_summary = []
        for project in projects[:10]:  # Limit to top 10 for performance
            project_card = await self._build_project_summary_card(project)
            projects_summary.append(project_card)

        # Calculate task distribution
        task_distribution = await self._calculate_task_distribution(projects)

        # Calculate resource utilization
        resource_utilization = await self._calculate_resource_utilization(projects)

        # Calculate budget analysis
        budget_analysis = await self._calculate_budget_analysis(projects)

        # Calculate team performance
        team_performance = await self._calculate_team_performance(projects)

        # Get alerts
        alerts = await self._get_project_alerts(user_id, projects)

        # Generate charts data
        charts_data = await self._generate_charts_data(projects, filters.time_range)

        return DashboardOverview(
            user_id=user_id,
            organization_id=1,  # Mock organization
            time_range=filters.time_range,
            generated_at=datetime.utcnow(),
            key_metrics=key_metrics,
            total_projects=len(projects),
            active_projects=len([p for p in projects if p.status == "active"]),
            projects_summary=projects_summary,
            task_distribution=task_distribution,
            resource_utilization=resource_utilization,
            budget_analysis=budget_analysis,
            team_performance=team_performance,
            alerts=alerts,
            charts_data=charts_data,
        )

    async def get_project_details_dashboard(
        self, project_id: int, time_range: TimeRange = TimeRange.MONTH
    ) -> ProjectDetailsDashboard:
        """Get detailed project dashboard"""

        # Get project
        project_result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )

        # Build project summary card
        project_card = await self._build_project_summary_card(project)

        # Get timeline data
        timeline_data = await self._get_project_timeline_data(project_id, time_range)

        # Get task breakdown
        task_breakdown = await self._get_project_task_breakdown(project_id)

        # Get team workload
        team_workload = await self._get_team_workload_data(project_id)

        # Get milestone progress
        milestone_progress = await self._get_milestone_progress(project_id)

        # Get risk assessment
        risk_assessment = await self._assess_project_risks(project)

        # Get recent activities
        recent_activities = await self._get_recent_project_activities(project_id)

        # Get performance trends
        performance_trends = await self._get_performance_trends(project_id, time_range)

        # Get budget breakdown
        budget_breakdown = await self._get_budget_breakdown(project_id)

        return ProjectDetailsDashboard(
            project=project_card,
            timeline_data=timeline_data,
            task_breakdown=task_breakdown,
            team_workload=team_workload,
            milestone_progress=milestone_progress,
            risk_assessment=risk_assessment,
            recent_activities=recent_activities,
            performance_trends=performance_trends,
            budget_breakdown=budget_breakdown,
        )

    async def _get_filtered_projects(self, filters: DashboardFilters) -> List[Project]:
        """Get projects based on filters"""

        query = select(Project).options(selectinload(Project.tasks))
        conditions = [Project.deleted_at.is_(None)]

        if filters.project_ids:
            conditions.append(Project.id.in_(filters.project_ids))

        if filters.status_filter:
            conditions.append(Project.status.in_(filters.status_filter))

        if filters.priority_filter:
            conditions.append(Project.priority.in_(filters.priority_filter))

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.db.execute(query)
        return result.scalars().all()

    async def _calculate_key_metrics(
        self, projects: List[Project], time_range: TimeRange
    ) -> List[KPIMetric]:
        """Calculate key performance indicators"""

        total_projects = len(projects)
        active_projects = len([p for p in projects if p.status == "active"])
        completed_projects = len([p for p in projects if p.status == "completed"])

        # Calculate completion rate
        completion_rate = (
            (completed_projects / total_projects * 100) if total_projects > 0 else 0
        )

        # Calculate average progress
        total_progress = sum(getattr(p, "progress_percentage", 0) for p in projects)
        avg_progress = total_progress / total_projects if total_projects > 0 else 0

        # Calculate budget utilization
        total_budget = sum(float(p.budget or 0) for p in projects)
        total_spent = sum(float(p.actual_cost or 0) for p in projects)
        budget_utilization = (
            (total_spent / total_budget * 100) if total_budget > 0 else 0
        )

        # Get task count
        total_tasks = sum(len(p.tasks) for p in projects)
        completed_tasks = sum(
            len([t for t in p.tasks if t.status == "completed"]) for p in projects
        )
        task_completion_rate = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )

        return [
            KPIMetric(
                name="Active Projects",
                value=active_projects,
                unit="projects",
                previous_value=active_projects - 2,  # Mock previous value
                change_percentage=5.2,
                trend="up",
                target=50,
                status="normal",
            ),
            KPIMetric(
                name="Completion Rate",
                value=round(completion_rate, 1),
                unit="%",
                previous_value=completion_rate - 3.5,
                change_percentage=8.1,
                trend="up",
                target=85.0,
                status="good" if completion_rate >= 80 else "warning",
            ),
            KPIMetric(
                name="Average Progress",
                value=round(avg_progress, 1),
                unit="%",
                previous_value=avg_progress - 2.1,
                change_percentage=3.2,
                trend="up",
                target=75.0,
                status="normal",
            ),
            KPIMetric(
                name="Budget Utilization",
                value=round(budget_utilization, 1),
                unit="%",
                previous_value=budget_utilization - 5.0,
                change_percentage=7.8,
                trend="up",
                target=90.0,
                status="warning" if budget_utilization > 95 else "normal",
            ),
            KPIMetric(
                name="Task Completion Rate",
                value=round(task_completion_rate, 1),
                unit="%",
                previous_value=task_completion_rate - 4.2,
                change_percentage=6.3,
                trend="up",
                target=80.0,
                status="good" if task_completion_rate >= 75 else "warning",
            ),
        ]

    async def _build_project_summary_card(self, project: Project) -> ProjectSummaryCard:
        """Build project summary card"""

        # Calculate progress percentage
        total_tasks = len(project.tasks)
        completed_tasks = len([t for t in project.tasks if t.status == "completed"])
        progress_percentage = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )

        # Determine health status
        health_status = ProjectHealthStatus.GOOD
        if progress_percentage < 25:
            health_status = ProjectHealthStatus.WARNING
        elif progress_percentage >= 75:
            health_status = ProjectHealthStatus.EXCELLENT

        # Count tasks by status
        active_tasks = len(
            [t for t in project.tasks if t.status in ["todo", "in_progress"]]
        )
        overdue_tasks = len(
            [
                t
                for t in project.tasks
                if t.due_date
                and t.due_date < datetime.utcnow()
                and t.status != "completed"
            ]
        )

        # Calculate team size (mock)
        team_size = 5  # Mock team size

        # Determine risk level
        risk_level = "low"
        if overdue_tasks > 3 or progress_percentage < 30:
            risk_level = "high"
        elif overdue_tasks > 1 or progress_percentage < 50:
            risk_level = "medium"

        return ProjectSummaryCard(
            id=project.id,
            name=project.name,
            code=project.code,
            status=project.status,
            priority=project.priority,
            progress_percentage=round(progress_percentage, 1),
            health_status=health_status,
            start_date=project.start_date,
            end_date=project.end_date,
            budget=Decimal(str(project.budget)) if project.budget else None,
            spent=Decimal(str(project.actual_cost)) if project.actual_cost else None,
            team_size=team_size,
            active_tasks=active_tasks,
            completed_tasks=completed_tasks,
            overdue_tasks=overdue_tasks,
            risk_level=risk_level,
            last_activity=datetime.utcnow()
            - timedelta(hours=2),  # Mock recent activity
        )

    async def _calculate_task_distribution(
        self, projects: List[Project]
    ) -> TaskDistribution:
        """Calculate task distribution across all projects"""

        all_tasks = []
        for project in projects:
            all_tasks.extend(project.tasks)

        todo = len([t for t in all_tasks if t.status == "todo"])
        in_progress = len([t for t in all_tasks if t.status == "in_progress"])
        review = len([t for t in all_tasks if t.status == "review"])
        completed = len([t for t in all_tasks if t.status == "completed"])
        cancelled = len([t for t in all_tasks if t.status == "cancelled"])

        return TaskDistribution(
            todo=todo,
            in_progress=in_progress,
            review=review,
            completed=completed,
            cancelled=cancelled,
            total=len(all_tasks),
        )

    async def _calculate_resource_utilization(
        self, projects: List[Project]
    ) -> ResourceUtilization:
        """Calculate resource utilization metrics"""

        # Mock calculations for resource utilization
        total_capacity = 2000.0  # Total available hours
        allocated_hours = 1650.0  # Hours allocated to projects
        utilized_hours = 1420.0  # Hours actually worked
        overtime_hours = 45.0  # Overtime hours

        utilization_percentage = (utilized_hours / total_capacity) * 100
        efficiency_score = (utilized_hours / allocated_hours) * 100

        return ResourceUtilization(
            total_capacity=total_capacity,
            allocated_hours=allocated_hours,
            utilized_hours=utilized_hours,
            utilization_percentage=round(utilization_percentage, 1),
            overtime_hours=overtime_hours,
            efficiency_score=round(efficiency_score, 1),
        )

    async def _calculate_budget_analysis(
        self, projects: List[Project]
    ) -> BudgetAnalysis:
        """Calculate budget analysis"""

        total_budget = sum(Decimal(str(p.budget or 0)) for p in projects)
        spent_amount = sum(Decimal(str(p.actual_cost or 0)) for p in projects)
        allocated_budget = total_budget * Decimal("0.85")  # 85% allocated
        remaining_budget = total_budget - spent_amount

        # Calculate burn rate (spending per week)
        burn_rate = spent_amount / Decimal("4")  # Mock: spent over 4 weeks

        # Project future spending
        weeks_remaining = 8  # Mock remaining weeks
        projected_spend = spent_amount + (burn_rate * weeks_remaining)

        # Determine budget health
        spend_percentage = (
            (spent_amount / total_budget) * 100 if total_budget > 0 else 0
        )
        if spend_percentage > 90:
            budget_health = "critical"
        elif spend_percentage > 75:
            budget_health = "warning"
        else:
            budget_health = "healthy"

        variance_percentage = (
            float((projected_spend - total_budget) / total_budget * 100)
            if total_budget > 0
            else 0
        )

        return BudgetAnalysis(
            total_budget=total_budget,
            allocated_budget=allocated_budget,
            spent_amount=spent_amount,
            remaining_budget=remaining_budget,
            burn_rate=burn_rate,
            projected_spend=projected_spend,
            budget_health=budget_health,
            variance_percentage=round(variance_percentage, 1),
        )

    async def _calculate_team_performance(
        self, projects: List[Project]
    ) -> TeamPerformance:
        """Calculate team performance metrics"""

        # Mock team performance calculations
        total_members = 25
        active_members = 22
        average_productivity = 82.5
        collaboration_score = 78.3
        satisfaction_score = 85.7

        top_performers = [
            {"id": 1, "name": "Alice Johnson", "score": 95.2, "projects": 3},
            {"id": 2, "name": "Bob Smith", "score": 91.8, "projects": 2},
            {"id": 3, "name": "Carol Davis", "score": 89.4, "projects": 4},
        ]

        underperformers = [
            {
                "id": 4,
                "name": "David Wilson",
                "score": 62.1,
                "projects": 1,
                "issues": ["missed deadlines"],
            }
        ]

        return TeamPerformance(
            total_members=total_members,
            active_members=active_members,
            average_productivity=average_productivity,
            collaboration_score=collaboration_score,
            satisfaction_score=satisfaction_score,
            top_performers=top_performers,
            underperformers=underperformers,
        )

    async def _get_project_alerts(
        self, user_id: int, projects: List[Project]
    ) -> List[ProjectAlert]:
        """Get project alerts and notifications"""

        alerts = []

        for project in projects:
            # Check for overdue tasks
            overdue_tasks = [
                t
                for t in project.tasks
                if t.due_date
                and t.due_date < datetime.utcnow()
                and t.status != "completed"
            ]

            if len(overdue_tasks) > 3:
                alerts.append(
                    ProjectAlert(
                        id=f"overdue_{project.id}",
                        type="deadline",
                        severity="critical",
                        title="Multiple Overdue Tasks",
                        message=f"Project '{project.name}' has {len(overdue_tasks)} overdue tasks",
                        project_id=project.id,
                        project_name=project.name,
                        created_at=datetime.utcnow(),
                        action_required=True,
                    )
                )

            # Check budget issues
            if project.budget and project.actual_cost:
                spend_percentage = (
                    float(project.actual_cost) / float(project.budget)
                ) * 100
                if spend_percentage > 90:
                    alerts.append(
                        ProjectAlert(
                            id=f"budget_{project.id}",
                            type="budget",
                            severity="warning",
                            title="Budget Alert",
                            message=f"Project '{project.name}' has used {spend_percentage:.1f}% of budget",
                            project_id=project.id,
                            project_name=project.name,
                            created_at=datetime.utcnow(),
                            action_required=True,
                        )
                    )

        return alerts[:10]  # Limit to 10 most important alerts

    async def _generate_charts_data(
        self, projects: List[Project], time_range: TimeRange
    ) -> Dict[str, Any]:
        """Generate data for dashboard charts"""

        # Project status distribution
        status_distribution = {}
        for project in projects:
            status = project.status
            status_distribution[status] = status_distribution.get(status, 0) + 1

        # Progress over time (mock data)
        progress_timeline = {
            "dates": ["2025-07-01", "2025-07-08", "2025-07-15", "2025-07-22"],
            "progress": [45.2, 52.8, 61.3, 68.7],
        }

        # Budget utilization chart
        budget_chart = {
            "categories": ["Allocated", "Spent", "Remaining"],
            "values": [850000, 675000, 175000],
        }

        # Team workload distribution
        workload_chart = {
            "members": ["Alice", "Bob", "Carol", "David", "Eve"],
            "hours": [42, 38, 45, 35, 40],
        }

        return {
            "status_distribution": status_distribution,
            "progress_timeline": progress_timeline,
            "budget_chart": budget_chart,
            "workload_chart": workload_chart,
        }

    async def _get_project_timeline_data(
        self, project_id: int, time_range: TimeRange
    ) -> Dict[str, Any]:
        """Get project timeline data for detailed dashboard"""

        # Mock timeline data
        return {
            "milestones": [
                {
                    "name": "Project Kickoff",
                    "date": "2025-08-01",
                    "status": "completed",
                },
                {
                    "name": "Phase 1 Complete",
                    "date": "2025-09-15",
                    "status": "in_progress",
                },
                {"name": "Beta Release", "date": "2025-11-01", "status": "planned"},
                {"name": "Final Delivery", "date": "2025-12-31", "status": "planned"},
            ],
            "critical_path": ["Task 1", "Task 3", "Task 5", "Task 8"],
            "dependencies": [
                {"from": "Task 1", "to": "Task 3"},
                {"from": "Task 3", "to": "Task 5"},
            ],
        }

    async def _get_project_task_breakdown(self, project_id: int) -> Dict[str, int]:
        """Get project task breakdown"""

        # Get project tasks
        tasks_result = await self.db.execute(
            select(Task).where(Task.project_id == project_id, Task.deleted_at.is_(None))
        )
        tasks = tasks_result.scalars().all()

        breakdown = {}
        for task in tasks:
            status = task.status
            breakdown[status] = breakdown.get(status, 0) + 1

        return breakdown

    async def _get_team_workload_data(self, project_id: int) -> List[Dict[str, Any]]:
        """Get team workload data for project"""

        # Mock team workload data
        return [
            {
                "member_id": 1,
                "name": "Alice",
                "allocated_hours": 40,
                "used_hours": 38,
                "efficiency": 95,
            },
            {
                "member_id": 2,
                "name": "Bob",
                "allocated_hours": 35,
                "used_hours": 32,
                "efficiency": 91,
            },
            {
                "member_id": 3,
                "name": "Carol",
                "allocated_hours": 45,
                "used_hours": 41,
                "efficiency": 89,
            },
        ]

    async def _get_milestone_progress(self, project_id: int) -> List[Dict[str, Any]]:
        """Get milestone progress for project"""

        # Mock milestone progress
        return [
            {
                "name": "Phase 1",
                "target_date": "2025-09-15",
                "progress": 75,
                "status": "on_track",
            },
            {
                "name": "Phase 2",
                "target_date": "2025-11-01",
                "progress": 25,
                "status": "at_risk",
            },
            {
                "name": "Final",
                "target_date": "2025-12-31",
                "progress": 0,
                "status": "planned",
            },
        ]

    async def _assess_project_risks(self, project: Project) -> Dict[str, Any]:
        """Assess project risks"""

        risks = []

        # Check schedule risk
        if project.end_date and project.end_date < date.today() + timedelta(days=30):
            risks.append(
                {
                    "type": "schedule",
                    "level": "high",
                    "description": "Project deadline approaching with incomplete tasks",
                }
            )

        # Check budget risk
        if project.budget and project.actual_cost:
            spend_percentage = (
                float(project.actual_cost) / float(project.budget)
            ) * 100
            if spend_percentage > 80:
                risks.append(
                    {
                        "type": "budget",
                        "level": "medium",
                        "description": f"Budget {spend_percentage:.1f}% utilized",
                    }
                )

        return {
            "overall_risk": "medium",
            "risk_factors": risks,
            "mitigation_strategies": [
                "Increase team size for critical tasks",
                "Reassess project scope and priorities",
                "Implement daily standup meetings",
            ],
        }

    async def _get_recent_project_activities(
        self, project_id: int
    ) -> List[Dict[str, Any]]:
        """Get recent project activities"""

        # Mock recent activities
        return [
            {
                "id": 1,
                "type": "task_completed",
                "description": "Task 'API Integration' completed by Alice",
                "timestamp": datetime.utcnow() - timedelta(hours=2),
                "user": "Alice Johnson",
            },
            {
                "id": 2,
                "type": "milestone_reached",
                "description": "Milestone 'Phase 1 Complete' reached",
                "timestamp": datetime.utcnow() - timedelta(hours=6),
                "user": "System",
            },
            {
                "id": 3,
                "type": "team_member_added",
                "description": "Bob Smith added to project team",
                "timestamp": datetime.utcnow() - timedelta(days=1),
                "user": "Project Manager",
            },
        ]

    async def _get_performance_trends(
        self, project_id: int, time_range: TimeRange
    ) -> Dict[str, List[float]]:
        """Get performance trends for project"""

        # Mock performance trends
        return {
            "velocity": [12, 15, 18, 16, 20, 17, 19],  # Story points per sprint
            "quality": [92, 89, 94, 91, 88, 93, 95],  # Quality score
            "team_satisfaction": [78, 82, 85, 79, 86, 88, 90],  # Team satisfaction
        }

    async def _get_budget_breakdown(self, project_id: int) -> Dict[str, Decimal]:
        """Get budget breakdown for project"""

        # Mock budget breakdown
        return {
            "development": Decimal("450000"),
            "testing": Decimal("120000"),
            "infrastructure": Decimal("80000"),
            "management": Decimal("100000"),
            "miscellaneous": Decimal("50000"),
        }


# API Dependencies
async def get_redis() -> aioredis.Redis:
    """Get Redis client"""
    return aioredis.Redis.from_url("redis://localhost:6379")


async def get_dashboard_service(
    db: AsyncSession = Depends(get_db), redis: aioredis.Redis = Depends(get_redis)
) -> ProjectDashboardService:
    """Get dashboard service instance"""
    return ProjectDashboardService(db, redis)


# API Endpoints - Project Dashboard
@router.get("/overview", response_model=DashboardOverview)
async def get_dashboard_overview(
    time_range: TimeRange = Query(TimeRange.MONTH),
    project_ids: Optional[str] = Query(None, description="Comma-separated project IDs"),
    status_filter: Optional[str] = Query(
        None, description="Comma-separated status values"
    ),
    priority_filter: Optional[str] = Query(
        None, description="Comma-separated priority values"
    ),
    current_user: User = Depends(get_current_user),
    service: ProjectDashboardService = Depends(get_dashboard_service),
):
    """Get complete dashboard overview"""

    filters = DashboardFilters(time_range=time_range)

    if project_ids:
        filters.project_ids = [int(x.strip()) for x in project_ids.split(",")]

    if status_filter:
        filters.status_filter = [x.strip() for x in status_filter.split(",")]

    if priority_filter:
        filters.priority_filter = [x.strip() for x in priority_filter.split(",")]

    return await service.get_dashboard_overview(current_user.id, filters)


@router.get("/projects/{project_id}/details", response_model=ProjectDetailsDashboard)
async def get_project_details_dashboard(
    project_id: int,
    time_range: TimeRange = Query(TimeRange.MONTH),
    service: ProjectDashboardService = Depends(get_dashboard_service),
):
    """Get detailed project dashboard"""
    return await service.get_project_details_dashboard(project_id, time_range)


@router.get("/kpis", response_model=List[KPIMetric])
async def get_kpi_metrics(
    time_range: TimeRange = Query(TimeRange.MONTH),
    service: ProjectDashboardService = Depends(get_dashboard_service),
):
    """Get KPI metrics only"""
    filters = DashboardFilters(time_range=time_range)
    projects = await service._get_filtered_projects(filters)
    return await service._calculate_key_metrics(projects, time_range)


@router.get("/alerts", response_model=List[ProjectAlert])
async def get_project_alerts(
    current_user: User = Depends(get_current_user),
    service: ProjectDashboardService = Depends(get_dashboard_service),
):
    """Get project alerts and notifications"""
    filters = DashboardFilters()
    projects = await service._get_filtered_projects(filters)
    return await service._get_project_alerts(current_user.id, projects)


# Health check endpoint
@router.get("/health", include_in_schema=False)
async def health_check():
    """Health check for dashboard API"""
    return {
        "status": "healthy",
        "service": "project-dashboard-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }
