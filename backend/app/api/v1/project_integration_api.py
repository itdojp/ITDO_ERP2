"""
ITDO ERP Backend - Project Management Integration API
Day 18: Project Management Integration (Requirements 2.3)
Complete integration of all project management components with unified workflows
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.gantt_scheduling_api import GanttSchedulingService
from app.api.v1.project_dashboard_api import ProjectDashboardService

# Import service dependencies
from app.api.v1.project_management_api import ProjectManagementService
from app.api.v1.task_management_api import TaskManagementService
from app.api.v1.team_management_api import TeamManagementService
from app.core.database import get_db
from app.models.user import User


# Mock authentication dependency
async def get_current_user() -> User:
    """Mock current user for integration APIs"""
    from unittest.mock import Mock

    mock_user = Mock()
    mock_user.id = "00000000-0000-0000-0000-000000000001"
    return mock_user


router = APIRouter(prefix="/api/v1/project-integration", tags=["project-integration"])


# Integration Workflow Models
class WorkflowStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IntegrationEvent(str, Enum):
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_DELETED = "project_deleted"
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    TEAM_MEMBER_ADDED = "team_member_added"
    TEAM_MEMBER_REMOVED = "team_member_removed"
    MILESTONE_REACHED = "milestone_reached"
    BUDGET_EXCEEDED = "budget_exceeded"
    DEADLINE_APPROACHING = "deadline_approaching"


class ProjectCreationRequest(BaseModel):
    """Complete project creation with team setup"""

    # Project details
    project_data: Dict[str, Any]

    # Initial team setup
    team_members: List[Dict[str, Any]] = Field(default_factory=list)

    # Initial tasks
    initial_tasks: List[Dict[str, Any]] = Field(default_factory=list)

    # Milestones
    milestones: List[Dict[str, Any]] = Field(default_factory=list)

    # Integration options
    auto_create_gantt: bool = True
    auto_setup_dashboard: bool = True
    notify_team: bool = True


class ProjectCreationResponse(BaseModel):
    """Complete project creation response"""

    project: Dict[str, Any]
    team_setup_result: Dict[str, Any]
    tasks_created: List[Dict[str, Any]]
    milestones_created: List[Dict[str, Any]]
    gantt_chart: Optional[Dict[str, Any]] = None
    dashboard_setup: Dict[str, Any]
    workflow_id: str
    created_at: datetime


class WorkflowExecution(BaseModel):
    """Workflow execution tracking"""

    id: str
    name: str
    status: WorkflowStatus
    steps: List[Dict[str, Any]]
    current_step: int
    total_steps: int
    progress_percentage: float
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectSyncRequest(BaseModel):
    """Project synchronization request"""

    project_id: int
    sync_tasks: bool = True
    sync_team: bool = True
    sync_gantt: bool = True
    sync_dashboard: bool = True
    force_update: bool = False


class ProjectSyncResponse(BaseModel):
    """Project synchronization response"""

    project_id: int
    sync_results: Dict[str, Any]
    updated_components: List[str]
    sync_time: datetime
    next_sync_time: Optional[datetime] = None


class IntegrationHealth(BaseModel):
    """Integration system health status"""

    overall_status: str  # healthy, degraded, critical
    component_status: Dict[str, str]
    performance_metrics: Dict[str, float]
    active_workflows: int
    failed_workflows: int
    last_health_check: datetime
    issues: List[Dict[str, Any]] = Field(default_factory=list)


# Project Integration Service
class ProjectIntegrationService:
    """Service for project management integration"""

    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.redis = redis_client

        # Initialize component services
        self.project_service = ProjectManagementService(db, redis_client)
        self.task_service = TaskManagementService(db, redis_client)
        self.gantt_service = GanttSchedulingService(db, redis_client)
        self.team_service = TeamManagementService(db, redis_client)
        self.dashboard_service = ProjectDashboardService(db, redis_client)

    async def create_complete_project(
        self, request: ProjectCreationRequest, user_id: int
    ) -> ProjectCreationResponse:
        """Create complete project with all components"""

        workflow_id = f"project_creation_{uuid.uuid4().hex[:12]}"

        # Initialize workflow tracking
        workflow = WorkflowExecution(
            id=workflow_id,
            name="Complete Project Creation",
            status=WorkflowStatus.IN_PROGRESS,
            steps=[
                {"name": "Create Project", "status": "pending"},
                {"name": "Setup Team", "status": "pending"},
                {"name": "Create Initial Tasks", "status": "pending"},
                {"name": "Create Milestones", "status": "pending"},
                {"name": "Generate Gantt Chart", "status": "pending"},
                {"name": "Setup Dashboard", "status": "pending"},
                {"name": "Send Notifications", "status": "pending"},
            ],
            current_step=0,
            total_steps=7,
            progress_percentage=0.0,
            started_at=datetime.utcnow(),
        )

        await self._save_workflow(workflow)

        try:
            results = {}

            # Step 1: Create Project
            workflow.current_step = 1
            workflow.steps[0]["status"] = "in_progress"
            await self._update_workflow(workflow)

            project = await self.project_service.create_project(
                request.project_data, user_id
            )
            results["project"] = project

            workflow.steps[0]["status"] = "completed"
            workflow.progress_percentage = 14.3
            await self._update_workflow(workflow)

            # Step 2: Setup Team
            if request.team_members:
                workflow.current_step = 2
                workflow.steps[1]["status"] = "in_progress"
                await self._update_workflow(workflow)

                team_results = []
                for member_data in request.team_members:
                    member_data["project_id"] = project.id
                    member = await self.team_service.add_team_member(
                        member_data, user_id
                    )
                    team_results.append(member)

                results["team_setup_result"] = {
                    "members_added": len(team_results),
                    "members": team_results,
                }

                workflow.steps[1]["status"] = "completed"
                workflow.progress_percentage = 28.6
                await self._update_workflow(workflow)

            # Step 3: Create Initial Tasks
            if request.initial_tasks:
                workflow.current_step = 3
                workflow.steps[2]["status"] = "in_progress"
                await self._update_workflow(workflow)

                tasks_created = []
                for task_data in request.initial_tasks:
                    task_data["project_id"] = project.id
                    task = await self.task_service.create_task(task_data, user_id)
                    tasks_created.append(task)

                results["tasks_created"] = tasks_created

                workflow.steps[2]["status"] = "completed"
                workflow.progress_percentage = 42.9
                await self._update_workflow(workflow)

            # Step 4: Create Milestones
            if request.milestones:
                workflow.current_step = 4
                workflow.steps[3]["status"] = "in_progress"
                await self._update_workflow(workflow)

                milestones_created = []
                for milestone_data in request.milestones:
                    milestone_data["project_id"] = project.id
                    milestone = await self.gantt_service.create_milestone(
                        milestone_data, user_id
                    )
                    milestones_created.append(milestone)

                results["milestones_created"] = milestones_created

                workflow.steps[3]["status"] = "completed"
                workflow.progress_percentage = 57.2
                await self._update_workflow(workflow)

            # Step 5: Generate Gantt Chart
            if request.auto_create_gantt:
                workflow.current_step = 5
                workflow.steps[4]["status"] = "in_progress"
                await self._update_workflow(workflow)

                gantt_chart = await self.gantt_service.get_gantt_chart(
                    project_id=project.id
                )
                results["gantt_chart"] = gantt_chart

                workflow.steps[4]["status"] = "completed"
                workflow.progress_percentage = 71.5
                await self._update_workflow(workflow)

            # Step 6: Setup Dashboard
            if request.auto_setup_dashboard:
                workflow.current_step = 6
                workflow.steps[5]["status"] = "in_progress"
                await self._update_workflow(workflow)

                dashboard_setup = await self._initialize_project_dashboard(
                    project.id, user_id
                )
                results["dashboard_setup"] = dashboard_setup

                workflow.steps[5]["status"] = "completed"
                workflow.progress_percentage = 85.8
                await self._update_workflow(workflow)

            # Step 7: Send Notifications
            if request.notify_team:
                workflow.current_step = 7
                workflow.steps[6]["status"] = "in_progress"
                await self._update_workflow(workflow)

                await self._send_project_notifications(
                    project.id, user_id, IntegrationEvent.PROJECT_CREATED
                )

                workflow.steps[6]["status"] = "completed"
                workflow.progress_percentage = 100.0
                await self._update_workflow(workflow)

            # Complete workflow
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.utcnow()
            await self._update_workflow(workflow)

            return ProjectCreationResponse(
                project=results.get("project"),
                team_setup_result=results.get("team_setup_result", {}),
                tasks_created=results.get("tasks_created", []),
                milestones_created=results.get("milestones_created", []),
                gantt_chart=results.get("gantt_chart"),
                dashboard_setup=results.get("dashboard_setup", {}),
                workflow_id=workflow_id,
                created_at=datetime.utcnow(),
            )

        except Exception as e:
            # Handle workflow failure
            workflow.status = WorkflowStatus.FAILED
            workflow.error_message = str(e)
            workflow.completed_at = datetime.utcnow()
            await self._update_workflow(workflow)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Project creation workflow failed: {str(e)}",
            )

    async def sync_project_components(
        self, request: ProjectSyncRequest
    ) -> ProjectSyncResponse:
        """Synchronize all project components"""

        sync_results = {}
        updated_components = []

        # Sync tasks
        if request.sync_tasks:
            task_sync = await self._sync_project_tasks(
                request.project_id, request.force_update
            )
            sync_results["tasks"] = task_sync
            if task_sync.get("updated", False):
                updated_components.append("tasks")

        # Sync team
        if request.sync_team:
            team_sync = await self._sync_project_team(
                request.project_id, request.force_update
            )
            sync_results["team"] = team_sync
            if team_sync.get("updated", False):
                updated_components.append("team")

        # Sync Gantt chart
        if request.sync_gantt:
            gantt_sync = await self._sync_project_gantt(
                request.project_id, request.force_update
            )
            sync_results["gantt"] = gantt_sync
            if gantt_sync.get("updated", False):
                updated_components.append("gantt")

        # Sync dashboard
        if request.sync_dashboard:
            dashboard_sync = await self._sync_project_dashboard(
                request.project_id, request.force_update
            )
            sync_results["dashboard"] = dashboard_sync
            if dashboard_sync.get("updated", False):
                updated_components.append("dashboard")

        # Schedule next sync
        next_sync_time = datetime.utcnow() + timedelta(hours=6)  # 6-hour sync interval

        return ProjectSyncResponse(
            project_id=request.project_id,
            sync_results=sync_results,
            updated_components=updated_components,
            sync_time=datetime.utcnow(),
            next_sync_time=next_sync_time,
        )

    async def get_integration_health(self) -> IntegrationHealth:
        """Get integration system health status"""

        # Check component health
        component_status = {}

        try:
            # Test project service
            await self.project_service.get_project_statistics()
            component_status["project_management"] = "healthy"
        except Exception:
            component_status["project_management"] = "degraded"

        try:
            # Test task service
            await self.task_service.get_task_statistics()
            component_status["task_management"] = "healthy"
        except Exception:
            component_status["task_management"] = "degraded"

        try:
            # Test team service
            await self.team_service.get_team_statistics()
            component_status["team_management"] = "healthy"
        except Exception:
            component_status["team_management"] = "degraded"

        # Test Redis connectivity
        try:
            await self.redis.ping()
            component_status["redis"] = "healthy"
        except Exception:
            component_status["redis"] = "critical"

        # Test database connectivity
        try:
            await self.db.execute(select(1))
            component_status["database"] = "healthy"
        except Exception:
            component_status["database"] = "critical"

        # Calculate overall status
        critical_count = sum(
            1 for status in component_status.values() if status == "critical"
        )
        degraded_count = sum(
            1 for status in component_status.values() if status == "degraded"
        )

        if critical_count > 0:
            overall_status = "critical"
        elif degraded_count > 1:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        # Get performance metrics
        performance_metrics = await self._get_performance_metrics()

        # Get workflow statistics
        active_workflows = await self._count_workflows(WorkflowStatus.IN_PROGRESS)
        failed_workflows = await self._count_workflows(WorkflowStatus.FAILED)

        # Identify issues
        issues = []
        for component, status in component_status.items():
            if status != "healthy":
                issues.append(
                    {
                        "component": component,
                        "status": status,
                        "description": f"{component} is {status}",
                        "severity": "high" if status == "critical" else "medium",
                    }
                )

        return IntegrationHealth(
            overall_status=overall_status,
            component_status=component_status,
            performance_metrics=performance_metrics,
            active_workflows=active_workflows,
            failed_workflows=failed_workflows,
            last_health_check=datetime.utcnow(),
            issues=issues,
        )

    async def get_workflow_status(
        self, workflow_id: str
    ) -> Optional[WorkflowExecution]:
        """Get workflow execution status"""

        workflow_data = await self.redis.hgetall(f"workflow:{workflow_id}")
        if not workflow_data:
            return None

        # Deserialize workflow data
        workflow_dict = {k.decode(): v.decode() for k, v in workflow_data.items()}

        return WorkflowExecution(
            id=workflow_dict["id"],
            name=workflow_dict["name"],
            status=WorkflowStatus(workflow_dict["status"]),
            steps=eval(
                workflow_dict["steps"]
            ),  # In production, use proper JSON serialization
            current_step=int(workflow_dict["current_step"]),
            total_steps=int(workflow_dict["total_steps"]),
            progress_percentage=float(workflow_dict["progress_percentage"]),
            started_at=datetime.fromisoformat(workflow_dict["started_at"]),
            completed_at=datetime.fromisoformat(workflow_dict["completed_at"])
            if workflow_dict.get("completed_at")
            else None,
            error_message=workflow_dict.get("error_message"),
            metadata=eval(workflow_dict.get("metadata", "{}")),
        )

    async def _save_workflow(self, workflow: WorkflowExecution):
        """Save workflow to Redis"""

        workflow_data = {
            "id": workflow.id,
            "name": workflow.name,
            "status": workflow.status.value,
            "steps": str(workflow.steps),
            "current_step": workflow.current_step,
            "total_steps": workflow.total_steps,
            "progress_percentage": workflow.progress_percentage,
            "started_at": workflow.started_at.isoformat(),
            "completed_at": workflow.completed_at.isoformat()
            if workflow.completed_at
            else "",
            "error_message": workflow.error_message or "",
            "metadata": str(workflow.metadata),
        }

        await self.redis.hset(f"workflow:{workflow.id}", mapping=workflow_data)
        await self.redis.expire(f"workflow:{workflow.id}", 86400)  # 24 hour expiry

    async def _update_workflow(self, workflow: WorkflowExecution):
        """Update workflow status"""
        await self._save_workflow(workflow)

    async def _initialize_project_dashboard(
        self, project_id: int, user_id: int
    ) -> Dict[str, Any]:
        """Initialize project dashboard"""

        # Create initial dashboard configuration
        dashboard_config = {
            "project_id": project_id,
            "kpi_widgets": ["progress", "budget", "team", "tasks"],
            "chart_types": ["gantt", "burndown", "team_workload"],
            "alert_settings": {
                "budget_threshold": 90,
                "deadline_warning_days": 7,
                "overdue_task_alerts": True,
            },
            "refresh_interval": 300,  # 5 minutes
            "created_at": datetime.utcnow().isoformat(),
            "created_by": user_id,
        }

        # Save dashboard configuration
        await self.redis.hset(
            f"dashboard_config:{project_id}",
            mapping={k: str(v) for k, v in dashboard_config.items()},
        )

        return {
            "status": "initialized",
            "widgets_created": len(dashboard_config["kpi_widgets"]),
            "charts_configured": len(dashboard_config["chart_types"]),
            "configuration": dashboard_config,
        }

    async def _send_project_notifications(
        self, project_id: int, user_id: int, event: IntegrationEvent
    ):
        """Send project notifications"""

        # Mock notification system
        notification_data = {
            "event": event.value,
            "project_id": project_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Project event: {event.value}",
        }

        # Store notification for retrieval
        notification_id = await self.redis.incr("notification_counter")
        await self.redis.hset(
            f"notification:{notification_id}", mapping=notification_data
        )

        # Add to user's notification queue
        await self.redis.lpush(f"user_notifications:{user_id}", notification_id)

    async def _sync_project_tasks(
        self, project_id: int, force_update: bool = False
    ) -> Dict[str, Any]:
        """Sync project tasks"""

        # Get current task statistics
        stats = await self.task_service.get_task_statistics(project_id=project_id)

        # Update project metrics based on task data
        await self.project_service._update_project_task_metrics(project_id)

        return {
            "updated": True,
            "task_count": stats.total_tasks,
            "completed_tasks": stats.completed_tasks,
            "sync_time": datetime.utcnow().isoformat(),
        }

    async def _sync_project_team(
        self, project_id: int, force_update: bool = False
    ) -> Dict[str, Any]:
        """Sync project team"""

        # Get current team information
        team = await self.team_service.get_project_team(project_id)

        return {
            "updated": True,
            "team_size": team.team_size,
            "active_members": team.active_members,
            "sync_time": datetime.utcnow().isoformat(),
        }

    async def _sync_project_gantt(
        self, project_id: int, force_update: bool = False
    ) -> Dict[str, Any]:
        """Sync project Gantt chart"""

        # Regenerate Gantt chart
        gantt = await self.gantt_service.get_gantt_chart(project_id=project_id)

        return {
            "updated": True,
            "task_count": len(gantt.tasks),
            "critical_path_tasks": len(gantt.critical_path),
            "sync_time": datetime.utcnow().isoformat(),
        }

    async def _sync_project_dashboard(
        self, project_id: int, force_update: bool = False
    ) -> Dict[str, Any]:
        """Sync project dashboard"""

        # Update dashboard metrics
        await self.dashboard_service.get_project_details_dashboard(project_id)

        return {
            "updated": True,
            "kpi_count": 5,  # Mock KPI count
            "chart_count": 4,  # Mock chart count
            "sync_time": datetime.utcnow().isoformat(),
        }

    async def _get_performance_metrics(self) -> Dict[str, float]:
        """Get system performance metrics"""

        # Mock performance metrics
        return {
            "avg_response_time_ms": 125.5,
            "requests_per_second": 45.2,
            "cpu_usage_percent": 23.8,
            "memory_usage_percent": 67.4,
            "redis_hit_rate": 94.2,
            "database_connection_pool_usage": 12.5,
        }

    async def _count_workflows(self, status: WorkflowStatus) -> int:
        """Count workflows by status"""

        # Mock workflow counting
        workflow_counts = {
            WorkflowStatus.IN_PROGRESS: 3,
            WorkflowStatus.FAILED: 1,
            WorkflowStatus.COMPLETED: 45,
            WorkflowStatus.PENDING: 0,
            WorkflowStatus.CANCELLED: 2,
        }

        return workflow_counts.get(status, 0)


# API Dependencies
async def get_redis() -> aioredis.Redis:
    """Get Redis client"""
    return aioredis.Redis.from_url("redis://localhost:6379")


async def get_integration_service(
    db: AsyncSession = Depends(get_db), redis: aioredis.Redis = Depends(get_redis)
) -> ProjectIntegrationService:
    """Get integration service instance"""
    return ProjectIntegrationService(db, redis)


# API Endpoints - Project Integration
@router.post("/projects/create-complete", response_model=ProjectCreationResponse)
async def create_complete_project(
    request: ProjectCreationRequest,
    current_user: User = Depends(get_current_user),
    service: ProjectIntegrationService = Depends(get_integration_service),
):
    """Create complete project with all components"""
    return await service.create_complete_project(request, current_user.id)


@router.post("/projects/sync", response_model=ProjectSyncResponse)
async def sync_project_components(
    request: ProjectSyncRequest,
    service: ProjectIntegrationService = Depends(get_integration_service),
):
    """Synchronize all project components"""
    return await service.sync_project_components(request)


@router.get("/health", response_model=IntegrationHealth)
async def get_integration_health(
    service: ProjectIntegrationService = Depends(get_integration_service),
):
    """Get integration system health status"""
    return await service.get_integration_health()


@router.get("/workflows/{workflow_id}", response_model=WorkflowExecution)
async def get_workflow_status(
    workflow_id: str,
    service: ProjectIntegrationService = Depends(get_integration_service),
):
    """Get workflow execution status"""
    workflow = await service.get_workflow_status(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found"
        )
    return workflow


# Health check endpoint
@router.get("/healthcheck", include_in_schema=False)
async def health_check():
    """Health check for integration API"""
    return {
        "status": "healthy",
        "service": "project-integration-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }
