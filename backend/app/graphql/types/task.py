"""Task GraphQL type definition."""

from typing import List, Optional

import strawberry
from strawberry import Info

from app.models.task import Task as TaskModel
from app.graphql.context import GraphQLContext


@strawberry.enum
class TaskStatus:
    """Task status enumeration."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@strawberry.enum
class TaskPriority:
    """Task priority enumeration."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@strawberry.type
class Task:
    """Task GraphQL type."""

    id: strawberry.ID
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    assignee_id: Optional[int]
    project_id: Optional[int]
    organization_id: Optional[int]
    due_date: Optional[str]
    created_at: str
    updated_at: Optional[str]

    @classmethod
    def from_model(cls, task_model: TaskModel) -> "Task":
        """Create GraphQL Task from SQLAlchemy Task model."""
        return cls(
            id=strawberry.ID(str(task_model.id)),
            title=task_model.title,
            description=task_model.description,
            status=TaskStatus(task_model.status),
            priority=TaskPriority(task_model.priority),
            assignee_id=task_model.assignee_id,
            project_id=task_model.project_id,
            organization_id=task_model.organization_id,
            due_date=task_model.due_date.isoformat() if task_model.due_date else None,
            created_at=task_model.created_at.isoformat() if task_model.created_at else "",
            updated_at=task_model.updated_at.isoformat() if task_model.updated_at else None,
        )

    @strawberry.field
    async def assignee(self, info: Info[GraphQLContext, None]) -> Optional["User"]:
        """Get task assignee using DataLoader."""
        if not self.assignee_id:
            return None
        
        user_model = await info.context.user_loader.load(self.assignee_id)
        if not user_model:
            return None
            
        from app.graphql.types.user import User
        return User.from_model(user_model)

    @strawberry.field
    async def project(self, info: Info[GraphQLContext, None]) -> Optional["Project"]:
        """Get task project."""
        # This would be implemented with proper DataLoader
        return None


@strawberry.input
class TaskCreateInput:
    """Input type for creating a task."""
    
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: Optional[int] = None
    project_id: Optional[int] = None
    due_date: Optional[str] = None


@strawberry.input
class TaskUpdateInput:
    """Input type for updating a task."""
    
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[int] = None
    project_id: Optional[int] = None
    due_date: Optional[str] = None


@strawberry.input
class TaskFilters:
    """Input type for filtering tasks."""
    
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[int] = None
    project_id: Optional[int] = None
    search: Optional[str] = None


@strawberry.type
class TaskPayload:
    """Payload type for task mutations."""
    
    task: Optional[Task]
    success: bool
    message: str