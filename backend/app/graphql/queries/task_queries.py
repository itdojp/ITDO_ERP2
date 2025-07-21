"""Task GraphQL query resolvers."""

from typing import List, Optional

import strawberry
from strawberry import Info
from sqlalchemy import select

from app.graphql.context import GraphQLContext
from app.graphql.types.task import Task, TaskFilters
from app.graphql.types.common import PaginationInput
from app.models.task import Task as TaskModel
from app.core.monitoring import monitor_performance


@strawberry.type
class TaskQueries:
    """Task-related GraphQL queries."""

    @strawberry.field
    @monitor_performance("graphql.task.get_task")
    async def task(
        self, 
        info: Info[GraphQLContext, None], 
        id: strawberry.ID
    ) -> Optional[Task]:
        """Get a single task by ID."""
        context = info.context
        context.require_authentication()
        
        task_id = int(id)
        
        # Use DataLoader for efficient loading
        task_model = await context.task_loader.load(task_id)
        
        if not task_model:
            return None
        
        # Check permissions - users can view tasks in their organization
        if (not context.current_user.is_superuser and 
            task_model.organization_id != context.organization_id):
            raise PermissionError("Insufficient permissions to view task")
        
        return Task.from_model(task_model)

    @strawberry.field
    @monitor_performance("graphql.task.get_tasks")
    async def tasks(
        self,
        info: Info[GraphQLContext, None],
        filters: Optional[TaskFilters] = None,
        pagination: Optional[PaginationInput] = None
    ) -> List[Task]:
        """Get multiple tasks with filtering and pagination."""
        context = info.context
        context.require_authentication()
        
        # Build query
        query = select(TaskModel)
        
        # Apply organization filter for non-superusers
        if not context.current_user.is_superuser and context.organization_id:
            query = query.where(TaskModel.organization_id == context.organization_id)
        
        # Apply filters
        if filters:
            if filters.status:
                query = query.where(TaskModel.status == filters.status.value)
            if filters.priority:
                query = query.where(TaskModel.priority == filters.priority.value)
            if filters.assignee_id:
                query = query.where(TaskModel.assignee_id == filters.assignee_id)
            if filters.project_id:
                query = query.where(TaskModel.project_id == filters.project_id)
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.where(
                    TaskModel.title.ilike(search_term) |
                    TaskModel.description.ilike(search_term)
                )
        
        # Apply pagination
        if pagination:
            if pagination.first:
                query = query.limit(pagination.first)
        
        # Default ordering
        query = query.order_by(TaskModel.created_at.desc())
        
        # Execute query
        if hasattr(context.db, 'execute'):  # AsyncSession
            result = await context.db.execute(query)
            task_models = result.scalars().all()
        else:  # Session
            result = context.db.execute(query)
            task_models = result.scalars().all()
        
        return [Task.from_model(task_model) for task_model in task_models]

    @strawberry.field
    @monitor_performance("graphql.task.get_my_tasks")
    async def my_tasks(
        self,
        info: Info[GraphQLContext, None],
        filters: Optional[TaskFilters] = None
    ) -> List[Task]:
        """Get tasks assigned to current user."""
        context = info.context
        user = context.require_authentication()
        
        # Build query for user's assigned tasks
        query = select(TaskModel).where(TaskModel.assignee_id == user.id)
        
        # Apply filters
        if filters:
            if filters.status:
                query = query.where(TaskModel.status == filters.status.value)
            if filters.priority:
                query = query.where(TaskModel.priority == filters.priority.value)
            if filters.project_id:
                query = query.where(TaskModel.project_id == filters.project_id)
        
        # Order by priority and due date
        query = query.order_by(
            TaskModel.priority.desc(),
            TaskModel.due_date.asc().nullslast(),
            TaskModel.created_at.desc()
        )
        
        # Execute query
        if hasattr(context.db, 'execute'):  # AsyncSession
            result = await context.db.execute(query)
            task_models = result.scalars().all()
        else:  # Session
            result = context.db.execute(query)
            task_models = result.scalars().all()
        
        return [Task.from_model(task_model) for task_model in task_models]

    @strawberry.field
    @monitor_performance("graphql.task.get_project_tasks")
    async def project_tasks(
        self,
        info: Info[GraphQLContext, None],
        project_id: int,
        filters: Optional[TaskFilters] = None
    ) -> List[Task]:
        """Get tasks for a specific project."""
        context = info.context
        context.require_authentication()
        
        # Build query for project tasks
        query = select(TaskModel).where(TaskModel.project_id == project_id)
        
        # Apply organization filter for non-superusers
        if not context.current_user.is_superuser and context.organization_id:
            query = query.where(TaskModel.organization_id == context.organization_id)
        
        # Apply additional filters
        if filters:
            if filters.status:
                query = query.where(TaskModel.status == filters.status.value)
            if filters.priority:
                query = query.where(TaskModel.priority == filters.priority.value)
            if filters.assignee_id:
                query = query.where(TaskModel.assignee_id == filters.assignee_id)
        
        # Order by priority
        query = query.order_by(TaskModel.priority.desc(), TaskModel.created_at.desc())
        
        # Execute query
        if hasattr(context.db, 'execute'):  # AsyncSession
            result = await context.db.execute(query)
            task_models = result.scalars().all()
        else:  # Session
            result = context.db.execute(query)
            task_models = result.scalars().all()
        
        return [Task.from_model(task_model) for task_model in task_models]