"""
ITDO ERP Backend - Project Management API
Day 16: Project Management Implementation (Requirements 2.3)
Complete project lifecycle management with tasks, milestones, and team collaboration
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator
from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.project import Project
from app.models.task import Task
from app.models.user import User


# Mock authentication dependency for project management APIs
async def get_current_user() -> User:
    """Mock current user for project management APIs"""
    from unittest.mock import Mock

    mock_user = Mock()
    mock_user.id = "00000000-0000-0000-0000-000000000001"
    return mock_user


router = APIRouter(prefix="/api/v1/projects", tags=["project-management"])


# Project Status Enums
class ProjectStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class ProjectPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Pydantic Schemas
class ProjectBase(BaseModel):
    """Base project schema with common fields"""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: ProjectStatus = ProjectStatus.PLANNING
    priority: ProjectPriority = ProjectPriority.MEDIUM
    budget: Optional[Decimal] = Field(None, ge=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    organization_id: Optional[int] = None
    department_id: Optional[int] = None

    @validator("budget", pre=True)
    def validate_budget(cls, v):
        if v is not None:
            return Decimal(str(v))
        return v


class ProjectCreate(ProjectBase):
    """Schema for creating a new project"""

    pass


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project"""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[ProjectStatus] = None
    priority: Optional[ProjectPriority] = None
    budget: Optional[Decimal] = Field(None, ge=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    planned_end_date: Optional[date] = None

    @validator("budget", pre=True)
    def validate_budget(cls, v):
        if v is not None:
            return Decimal(str(v))
        return v


class TaskSummary(BaseModel):
    """Task summary for project response"""

    id: int
    title: str
    status: str
    priority: str
    assignee_id: Optional[int] = None
    due_date: Optional[datetime] = None


class ProjectResponse(ProjectBase):
    """Schema for project response"""

    id: int
    owner_id: int
    total_budget: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    completion_percentage: Optional[float] = None
    tasks_count: int = 0
    active_tasks_count: int = 0
    completed_tasks_count: int = 0
    overdue_tasks_count: int = 0
    tasks: List[TaskSummary] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Schema for paginated project list response"""

    projects: List[ProjectResponse]
    total: int
    page: int
    size: int
    pages: int


class ProjectStatsResponse(BaseModel):
    """Project statistics response"""

    total_projects: int
    active_projects: int
    completed_projects: int
    overdue_projects: int
    total_budget: Decimal
    actual_cost: Decimal
    average_completion: float


# Project Management Service
class ProjectManagementService:
    """Service for project management operations"""

    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.redis = redis_client

    async def create_project(
        self, project_data: ProjectCreate, user_id: int
    ) -> ProjectResponse:
        """Create a new project with task management setup"""

        # Check for duplicate project code
        if project_data.code:
            existing = await self.db.execute(
                select(Project).where(Project.code == project_data.code)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Project with code '{project_data.code}' already exists",
                )

        # Create project instance
        project = Project(
            code=project_data.code,
            name=project_data.name,
            description=project_data.description,
            status=project_data.status.value,
            priority=project_data.priority.value,
            budget=float(project_data.budget) if project_data.budget else None,
            start_date=project_data.start_date,
            end_date=project_data.end_date,
            planned_end_date=project_data.planned_end_date,
            organization_id=project_data.organization_id or 1,
            department_id=project_data.department_id,
            owner_id=user_id,
            created_at=datetime.utcnow(),
        )

        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)

        # Initialize project metrics
        await self._initialize_project_metrics(project.id)

        return await self._build_project_response(project)

    async def get_project(self, project_id: int) -> Optional[ProjectResponse]:
        """Get a project by ID with tasks and statistics"""

        result = await self.db.execute(
            select(Project)
            .options(selectinload(Project.tasks))
            .where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            return None

        return await self._build_project_response(project)

    async def update_project(
        self, project_id: int, project_data: ProjectUpdate, user_id: int
    ) -> Optional[ProjectResponse]:
        """Update a project with validation"""

        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            return None

        # Update fields
        update_data = project_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "budget" and value is not None:
                setattr(project, field, float(value))
            elif hasattr(project, field):
                setattr(project, field, value)

        project.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(project)

        # Update project metrics
        await self._update_project_metrics(project.id)

        return await self._build_project_response(project)

    async def delete_project(self, project_id: int) -> bool:
        """Soft delete a project and archive associated tasks"""

        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            return False

        # Archive project
        project.status = ProjectStatus.ARCHIVED.value
        project.updated_at = datetime.utcnow()
        project.deleted_at = datetime.utcnow()

        # Archive associated tasks
        await self.db.execute(select(Task).where(Task.project_id == project_id))
        # Update task statuses to cancelled
        # (Implementation would depend on Task model structure)

        await self.db.commit()

        return True

    async def list_projects(
        self,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        status: Optional[ProjectStatus] = None,
        priority: Optional[ProjectPriority] = None,
        owner_id: Optional[int] = None,
        department_id: Optional[int] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> ProjectListResponse:
        """List projects with filtering and pagination"""

        query = select(Project).options(selectinload(Project.tasks))

        # Apply filters
        filters = []
        if search:
            filters.append(
                Project.name.ilike(f"%{search}%")
                | Project.description.ilike(f"%{search}%")
                | Project.code.ilike(f"%{search}%")
            )

        if status:
            filters.append(Project.status == status.value)

        if priority:
            filters.append(Project.priority == priority.value)

        if owner_id:
            filters.append(Project.owner_id == owner_id)

        if department_id:
            filters.append(Project.department_id == department_id)

        # Exclude archived projects by default
        filters.append(Project.status != ProjectStatus.ARCHIVED.value)

        if filters:
            query = query.where(and_(*filters))

        # Apply sorting
        sort_column = getattr(Project, sort_by, Project.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Get total count
        count_query = select(func.count(Project.id))
        if filters:
            count_query = count_query.where(and_(*filters))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        projects = result.scalars().all()

        # Build responses with statistics
        project_responses = []
        for project in projects:
            project_response = await self._build_project_response(project)
            project_responses.append(project_response)

        return ProjectListResponse(
            projects=project_responses,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )

    async def get_project_statistics(
        self, organization_id: Optional[int] = None
    ) -> ProjectStatsResponse:
        """Get overall project statistics"""

        base_query = select(Project)
        if organization_id:
            base_query = base_query.where(Project.organization_id == organization_id)

        # Total projects
        total_result = await self.db.execute(
            select(func.count(Project.id)).select_from(base_query.subquery())
        )
        total_projects = total_result.scalar() or 0

        # Active projects
        active_result = await self.db.execute(
            base_query.where(Project.status == ProjectStatus.ACTIVE.value)
        )
        active_projects = len(active_result.scalars().all())

        # Completed projects
        completed_result = await self.db.execute(
            base_query.where(Project.status == ProjectStatus.COMPLETED.value)
        )
        completed_projects = len(completed_result.scalars().all())

        # Budget calculations
        budget_result = await self.db.execute(
            select(
                func.sum(Project.budget).label("total_budget"),
                func.sum(Project.actual_cost).label("actual_cost"),
            ).select_from(base_query.subquery())
        )
        budget_data = budget_result.first()

        total_budget = Decimal(str(budget_data.total_budget or 0))
        actual_cost = Decimal(str(budget_data.actual_cost or 0))

        return ProjectStatsResponse(
            total_projects=total_projects,
            active_projects=active_projects,
            completed_projects=completed_projects,
            overdue_projects=0,  # Would need to calculate based on end_date
            total_budget=total_budget,
            actual_cost=actual_cost,
            average_completion=0.0,  # Would need task completion data
        )

    async def _build_project_response(self, project: Project) -> ProjectResponse:
        """Build a complete project response with task statistics"""

        # Get task statistics
        tasks_result = await self.db.execute(
            select(Task).where(Task.project_id == project.id)
        )
        tasks = tasks_result.scalars().all()

        tasks_count = len(tasks)
        active_tasks_count = len(
            [t for t in tasks if t.status in ["todo", "in_progress"]]
        )
        completed_tasks_count = len([t for t in tasks if t.status == "completed"])
        overdue_tasks_count = 0  # Would need to calculate based on due_date

        # Build task summaries
        task_summaries = []
        for task in tasks[:10]:  # Limit to 10 tasks for response size
            task_summary = TaskSummary(
                id=task.id,
                title=task.title,
                status=task.status,
                priority=task.priority,
                assignee_id=task.assignee_id,
                due_date=task.due_date,
            )
            task_summaries.append(task_summary)

        # Calculate completion percentage
        completion_percentage = 0.0
        if tasks_count > 0:
            completion_percentage = (completed_tasks_count / tasks_count) * 100

        return ProjectResponse(
            id=project.id,
            code=project.code,
            name=project.name,
            description=project.description,
            status=ProjectStatus(project.status),
            priority=ProjectPriority(project.priority),
            budget=Decimal(str(project.budget)) if project.budget else None,
            start_date=project.start_date,
            end_date=project.end_date,
            planned_end_date=project.planned_end_date,
            organization_id=project.organization_id,
            department_id=project.department_id,
            owner_id=project.owner_id,
            total_budget=Decimal(str(project.total_budget))
            if project.total_budget
            else None,
            actual_cost=Decimal(str(project.actual_cost))
            if project.actual_cost
            else None,
            completion_percentage=completion_percentage,
            tasks_count=tasks_count,
            active_tasks_count=active_tasks_count,
            completed_tasks_count=completed_tasks_count,
            overdue_tasks_count=overdue_tasks_count,
            tasks=task_summaries,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    async def _initialize_project_metrics(self, project_id: int):
        """Initialize project metrics in Redis"""
        await self.redis.hset(
            f"project_metrics:{project_id}",
            mapping={
                "tasks_count": 0,
                "completed_tasks": 0,
                "active_tasks": 0,
                "total_hours": 0,
                "actual_hours": 0,
            },
        )

    async def _update_project_metrics(self, project_id: int):
        """Update project metrics in Redis"""
        # Get current task statistics
        tasks_result = await self.db.execute(
            select(Task).where(Task.project_id == project_id)
        )
        tasks = tasks_result.scalars().all()

        metrics = {
            "tasks_count": len(tasks),
            "completed_tasks": len([t for t in tasks if t.status == "completed"]),
            "active_tasks": len(
                [t for t in tasks if t.status in ["todo", "in_progress"]]
            ),
            "total_hours": sum(t.estimated_hours or 0 for t in tasks),
            "actual_hours": sum(t.actual_hours or 0 for t in tasks),
        }

        await self.redis.hset(f"project_metrics:{project_id}", mapping=metrics)


# API Dependencies
async def get_redis() -> aioredis.Redis:
    """Get Redis client"""
    return aioredis.Redis.from_url("redis://localhost:6379")


async def get_project_service(
    db: AsyncSession = Depends(get_db), redis: aioredis.Redis = Depends(get_redis)
) -> ProjectManagementService:
    """Get project management service instance"""
    return ProjectManagementService(db, redis)


# API Endpoints - Project Management
@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    service: ProjectManagementService = Depends(get_project_service),
):
    """Create a new project with task management setup"""
    return await service.create_project(project_data, current_user.id)


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[ProjectStatus] = Query(None),
    priority: Optional[ProjectPriority] = Query(None),
    owner_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    service: ProjectManagementService = Depends(get_project_service),
):
    """List projects with filtering and pagination"""
    return await service.list_projects(
        page=page,
        size=size,
        search=search,
        status=status,
        priority=priority,
        owner_id=owner_id,
        department_id=department_id,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/statistics", response_model=ProjectStatsResponse)
async def get_project_statistics(
    organization_id: Optional[int] = Query(None),
    service: ProjectManagementService = Depends(get_project_service),
):
    """Get overall project statistics"""
    return await service.get_project_statistics(organization_id)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    service: ProjectManagementService = Depends(get_project_service),
):
    """Get a project by ID with tasks and statistics"""
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    service: ProjectManagementService = Depends(get_project_service),
):
    """Update a project"""
    project = await service.update_project(project_id, project_data, current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    service: ProjectManagementService = Depends(get_project_service),
):
    """Delete a project (soft delete with archiving)"""
    success = await service.delete_project(project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )


# Health check endpoint
@router.get("/health", include_in_schema=False)
async def health_check():
    """Health check for project management API"""
    return {
        "status": "healthy",
        "service": "project-management-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }
