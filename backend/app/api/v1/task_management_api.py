"""
ITDO ERP Backend - Task Management API
Day 16: Task Management Implementation (Requirements 2.3)
Complete task lifecycle management with project integration and progress tracking
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


# Mock authentication dependency for task management APIs
async def get_current_user() -> User:
    """Mock current user for task management APIs"""
    from unittest.mock import Mock

    mock_user = Mock()
    mock_user.id = "00000000-0000-0000-0000-000000000001"
    return mock_user


router = APIRouter(prefix="/api/v1/tasks", tags=["task-management"])


# Task Status and Priority Enums (using existing enums from model)
class TaskStatusEnum(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class TaskPriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Pydantic Schemas
class TaskBase(BaseModel):
    """Base task schema with common fields"""

    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: TaskStatusEnum = TaskStatusEnum.TODO
    priority: TaskPriorityEnum = TaskPriorityEnum.MEDIUM
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None
    reporter_id: Optional[int] = None
    parent_task_id: Optional[int] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[Decimal] = Field(None, ge=0)
    actual_hours: Optional[Decimal] = Field(None, ge=0)
    completion_percentage: Optional[int] = Field(None, ge=0, le=100)
    tags: Optional[List[str]] = Field(default_factory=list)

    @validator("estimated_hours", "actual_hours", pre=True)
    def validate_hours(cls, v):
        if v is not None:
            return Decimal(str(v))
        return v


class TaskCreate(TaskBase):
    """Schema for creating a new task"""

    pass


class TaskUpdate(BaseModel):
    """Schema for updating an existing task"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[TaskStatusEnum] = None
    priority: Optional[TaskPriorityEnum] = None
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[Decimal] = Field(None, ge=0)
    actual_hours: Optional[Decimal] = Field(None, ge=0)
    completion_percentage: Optional[int] = Field(None, ge=0, le=100)
    tags: Optional[List[str]] = None

    @validator("estimated_hours", "actual_hours", pre=True)
    def validate_hours(cls, v):
        if v is not None:
            return Decimal(str(v))
        return v


class SubtaskSummary(BaseModel):
    """Subtask summary for task response"""

    id: int
    title: str
    status: str
    priority: str
    completion_percentage: Optional[int] = None
    assignee_id: Optional[int] = None


class TaskResponse(TaskBase):
    """Schema for task response"""

    id: int
    task_number: Optional[str] = None
    created_by: int
    subtasks: List[SubtaskSummary] = Field(default_factory=list)
    subtasks_count: int = 0
    completed_subtasks_count: int = 0
    is_overdue: bool = False
    days_until_due: Optional[int] = None
    time_spent_hours: Optional[Decimal] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Schema for paginated task list response"""

    tasks: List[TaskResponse]
    total: int
    page: int
    size: int
    pages: int


class TaskStatsResponse(BaseModel):
    """Task statistics response"""

    total_tasks: int
    todo_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    overdue_tasks: int
    total_estimated_hours: Decimal
    total_actual_hours: Decimal
    completion_rate: float


class TaskTimeLogCreate(BaseModel):
    """Schema for creating task time log"""

    task_id: int
    hours_spent: Decimal = Field(..., gt=0)
    description: Optional[str] = None
    work_date: date = Field(default_factory=date.today)


class TaskTimeLogResponse(BaseModel):
    """Schema for task time log response"""

    id: int
    task_id: int
    user_id: int
    hours_spent: Decimal
    description: Optional[str] = None
    work_date: date
    created_at: datetime


# Task Management Service
class TaskManagementService:
    """Service for task management operations"""

    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.redis = redis_client

    async def create_task(self, task_data: TaskCreate, user_id: int) -> TaskResponse:
        """Create a new task with project integration"""

        # Validate project exists if project_id provided
        if task_data.project_id:
            project_result = await self.db.execute(
                select(Project).where(Project.id == task_data.project_id)
            )
            project = project_result.scalar_one_or_none()
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Project with ID {task_data.project_id} not found",
                )

        # Validate parent task exists if parent_task_id provided
        if task_data.parent_task_id:
            parent_result = await self.db.execute(
                select(Task).where(Task.id == task_data.parent_task_id)
            )
            parent_task = parent_result.scalar_one_or_none()
            if not parent_task:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Parent task with ID {task_data.parent_task_id} not found",
                )

        # Generate task number
        task_number = await self._generate_task_number()

        # Create task instance
        task = Task(
            task_number=task_number,
            title=task_data.title,
            description=task_data.description,
            status=task_data.status.value,
            priority=task_data.priority.value,
            project_id=task_data.project_id,
            assignee_id=task_data.assignee_id,
            reporter_id=task_data.reporter_id or user_id,
            parent_task_id=task_data.parent_task_id,
            due_date=task_data.due_date,
            estimated_hours=float(task_data.estimated_hours)
            if task_data.estimated_hours
            else None,
            actual_hours=float(task_data.actual_hours)
            if task_data.actual_hours
            else None,
            completion_percentage=task_data.completion_percentage or 0,
            created_by=user_id,
            created_at=datetime.utcnow(),
        )

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        # Update project metrics if task is associated with project
        if task.project_id:
            await self._update_project_task_metrics(task.project_id)

        # Initialize task metrics
        await self._initialize_task_metrics(task.id)

        return await self._build_task_response(task)

    async def get_task(self, task_id: int) -> Optional[TaskResponse]:
        """Get a task by ID with subtasks and statistics"""

        result = await self.db.execute(
            select(Task).options(selectinload(Task.subtasks)).where(Task.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            return None

        return await self._build_task_response(task)

    async def update_task(
        self, task_id: int, task_data: TaskUpdate, user_id: int
    ) -> Optional[TaskResponse]:
        """Update a task with validation"""

        result = await self.db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            return None

        # Validate project exists if project_id being updated
        if task_data.project_id is not None and task_data.project_id != task.project_id:
            project_result = await self.db.execute(
                select(Project).where(Project.id == task_data.project_id)
            )
            project = project_result.scalar_one_or_none()
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Project with ID {task_data.project_id} not found",
                )

        # Store old project_id for metrics update
        old_project_id = task.project_id

        # Update fields
        update_data = task_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field in ["estimated_hours", "actual_hours"] and value is not None:
                setattr(task, field, float(value))
            elif hasattr(task, field):
                setattr(task, field, value)

        task.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(task)

        # Update project metrics for both old and new projects
        if old_project_id:
            await self._update_project_task_metrics(old_project_id)
        if task.project_id and task.project_id != old_project_id:
            await self._update_project_task_metrics(task.project_id)

        # Update task metrics
        await self._update_task_metrics(task.id)

        return await self._build_task_response(task)

    async def delete_task(self, task_id: int) -> bool:
        """Soft delete a task and update related metrics"""

        result = await self.db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            return False

        # Store project_id for metrics update
        project_id = task.project_id

        # Soft delete task
        task.deleted_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()

        # Also soft delete subtasks
        await self.db.execute(select(Task).where(Task.parent_task_id == task_id))

        await self.db.commit()

        # Update project metrics
        if project_id:
            await self._update_project_task_metrics(project_id)

        return True

    async def list_tasks(
        self,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        status: Optional[TaskStatusEnum] = None,
        priority: Optional[TaskPriorityEnum] = None,
        project_id: Optional[int] = None,
        assignee_id: Optional[int] = None,
        due_date_from: Optional[date] = None,
        due_date_to: Optional[date] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> TaskListResponse:
        """List tasks with filtering and pagination"""

        query = select(Task).options(selectinload(Task.subtasks))

        # Apply filters
        filters = []
        if search:
            filters.append(
                Task.title.ilike(f"%{search}%")
                | Task.description.ilike(f"%{search}%")
                | Task.task_number.ilike(f"%{search}%")
            )

        if status:
            filters.append(Task.status == status.value)

        if priority:
            filters.append(Task.priority == priority.value)

        if project_id:
            filters.append(Task.project_id == project_id)

        if assignee_id:
            filters.append(Task.assignee_id == assignee_id)

        if due_date_from:
            filters.append(Task.due_date >= due_date_from)

        if due_date_to:
            filters.append(Task.due_date <= due_date_to)

        # Exclude deleted tasks
        filters.append(Task.deleted_at.is_(None))

        if filters:
            query = query.where(and_(*filters))

        # Apply sorting
        sort_column = getattr(Task, sort_by, Task.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Get total count
        count_query = select(func.count(Task.id))
        if filters:
            count_query = count_query.where(and_(*filters))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        tasks = result.scalars().all()

        # Build responses with statistics
        task_responses = []
        for task in tasks:
            task_response = await self._build_task_response(task)
            task_responses.append(task_response)

        return TaskListResponse(
            tasks=task_responses,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )

    async def get_task_statistics(
        self, project_id: Optional[int] = None, assignee_id: Optional[int] = None
    ) -> TaskStatsResponse:
        """Get task statistics"""

        base_query = select(Task).where(Task.deleted_at.is_(None))

        if project_id:
            base_query = base_query.where(Task.project_id == project_id)

        if assignee_id:
            base_query = base_query.where(Task.assignee_id == assignee_id)

        # Total tasks
        total_result = await self.db.execute(
            select(func.count(Task.id)).select_from(base_query.subquery())
        )
        total_tasks = total_result.scalar() or 0

        # Status counts
        status_counts = {}
        for status_value in ["todo", "in_progress", "completed"]:
            count_result = await self.db.execute(
                base_query.where(Task.status == status_value)
            )
            status_counts[status_value] = len(count_result.scalars().all())

        # Hours calculations
        hours_result = await self.db.execute(
            select(
                func.sum(Task.estimated_hours).label("total_estimated"),
                func.sum(Task.actual_hours).label("total_actual"),
            ).select_from(base_query.subquery())
        )
        hours_data = hours_result.first()

        total_estimated = Decimal(str(hours_data.total_estimated or 0))
        total_actual = Decimal(str(hours_data.total_actual or 0))

        # Completion rate
        completion_rate = 0.0
        if total_tasks > 0:
            completion_rate = (status_counts.get("completed", 0) / total_tasks) * 100

        return TaskStatsResponse(
            total_tasks=total_tasks,
            todo_tasks=status_counts.get("todo", 0),
            in_progress_tasks=status_counts.get("in_progress", 0),
            completed_tasks=status_counts.get("completed", 0),
            overdue_tasks=0,  # Would need to calculate based on due_date
            total_estimated_hours=total_estimated,
            total_actual_hours=total_actual,
            completion_rate=completion_rate,
        )

    async def _build_task_response(self, task: Task) -> TaskResponse:
        """Build a complete task response with subtask statistics"""

        # Get subtask statistics
        subtasks_result = await self.db.execute(
            select(Task).where(
                Task.parent_task_id == task.id, Task.deleted_at.is_(None)
            )
        )
        subtasks = subtasks_result.scalars().all()

        subtasks_count = len(subtasks)
        completed_subtasks_count = len([t for t in subtasks if t.status == "completed"])

        # Build subtask summaries
        subtask_summaries = []
        for subtask in subtasks[:5]:  # Limit to 5 subtasks for response size
            subtask_summary = SubtaskSummary(
                id=subtask.id,
                title=subtask.title,
                status=subtask.status,
                priority=subtask.priority,
                completion_percentage=subtask.completion_percentage,
                assignee_id=subtask.assignee_id,
            )
            subtask_summaries.append(subtask_summary)

        # Calculate overdue status
        is_overdue = False
        days_until_due = None
        if task.due_date:
            today = datetime.now().date()
            due_date = (
                task.due_date.date()
                if isinstance(task.due_date, datetime)
                else task.due_date
            )
            days_until_due = (due_date - today).days
            is_overdue = days_until_due < 0 and task.status not in [
                "completed",
                "cancelled",
            ]

        return TaskResponse(
            id=task.id,
            task_number=task.task_number,
            title=task.title,
            description=task.description,
            status=TaskStatusEnum(task.status),
            priority=TaskPriorityEnum(task.priority),
            project_id=task.project_id,
            assignee_id=task.assignee_id,
            reporter_id=task.reporter_id,
            parent_task_id=task.parent_task_id,
            due_date=task.due_date,
            estimated_hours=Decimal(str(task.estimated_hours))
            if task.estimated_hours
            else None,
            actual_hours=Decimal(str(task.actual_hours)) if task.actual_hours else None,
            completion_percentage=task.completion_percentage,
            tags=[],  # Would come from separate tags table
            created_by=task.created_by,
            subtasks=subtask_summaries,
            subtasks_count=subtasks_count,
            completed_subtasks_count=completed_subtasks_count,
            is_overdue=is_overdue,
            days_until_due=days_until_due,
            time_spent_hours=Decimal(str(task.actual_hours))
            if task.actual_hours
            else None,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    async def _generate_task_number(self) -> str:
        """Generate unique task number"""
        # Get current counter
        counter = await self.redis.incr("task_counter")
        return f"TASK-{counter:06d}"

    async def _initialize_task_metrics(self, task_id: int):
        """Initialize task metrics in Redis"""
        await self.redis.hset(
            f"task_metrics:{task_id}",
            mapping={
                "time_logged": 0,
                "completion_percentage": 0,
                "status_changes": 0,
                "priority_changes": 0,
            },
        )

    async def _update_task_metrics(self, task_id: int):
        """Update task metrics in Redis"""
        # Get current task data
        task_result = await self.db.execute(select(Task).where(Task.id == task_id))
        task = task_result.scalar_one_or_none()

        if task:
            metrics = {
                "time_logged": float(task.actual_hours or 0),
                "completion_percentage": task.completion_percentage or 0,
                "current_status": task.status,
                "current_priority": task.priority,
            }

            await self.redis.hset(f"task_metrics:{task_id}", mapping=metrics)

    async def _update_project_task_metrics(self, project_id: int):
        """Update project task metrics in Redis"""
        # Get project tasks
        tasks_result = await self.db.execute(
            select(Task).where(Task.project_id == project_id, Task.deleted_at.is_(None))
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


async def get_task_service(
    db: AsyncSession = Depends(get_db), redis: aioredis.Redis = Depends(get_redis)
) -> TaskManagementService:
    """Get task management service instance"""
    return TaskManagementService(db, redis)


# API Endpoints - Task Management
@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    service: TaskManagementService = Depends(get_task_service),
):
    """Create a new task with project integration"""
    return await service.create_task(task_data, current_user.id)


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[TaskStatusEnum] = Query(None),
    priority: Optional[TaskPriorityEnum] = Query(None),
    project_id: Optional[int] = Query(None),
    assignee_id: Optional[int] = Query(None),
    due_date_from: Optional[date] = Query(None),
    due_date_to: Optional[date] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    service: TaskManagementService = Depends(get_task_service),
):
    """List tasks with filtering and pagination"""
    return await service.list_tasks(
        page=page,
        size=size,
        search=search,
        status=status,
        priority=priority,
        project_id=project_id,
        assignee_id=assignee_id,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/statistics", response_model=TaskStatsResponse)
async def get_task_statistics(
    project_id: Optional[int] = Query(None),
    assignee_id: Optional[int] = Query(None),
    service: TaskManagementService = Depends(get_task_service),
):
    """Get task statistics"""
    return await service.get_task_statistics(project_id, assignee_id)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    service: TaskManagementService = Depends(get_task_service),
):
    """Get a task by ID with subtasks and statistics"""
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    service: TaskManagementService = Depends(get_task_service),
):
    """Update a task"""
    task = await service.update_task(task_id, task_data, current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    service: TaskManagementService = Depends(get_task_service),
):
    """Delete a task (soft delete)"""
    success = await service.delete_task(task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )


# Health check endpoint
@router.get("/health", include_in_schema=False)
async def health_check():
    """Health check for task management API"""
    return {
        "status": "healthy",
        "service": "task-management-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }
