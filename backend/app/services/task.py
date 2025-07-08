"""Task management service."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFound, PermissionDenied, BusinessLogicError
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.schemas.task import (
    BulkStatusUpdate,
    BulkUpdateResponse,
    TaskCreate,
    TaskHistoryResponse,
    TaskListResponse,
    TaskResponse,
    TaskStatusUpdate,
    TaskUpdate,
)


class TaskService:
    """Service for managing tasks."""

    def create_task(
        self, task_data: TaskCreate, user: User, db: Session
    ) -> TaskResponse:
        """Create a new task."""
        # Check if project exists and user has access
        project = db.query(Project).filter(Project.id == task_data.project_id).first()
        if not project:
            raise NotFound("Project not found")
        
        # TODO: Check project access permissions
        # For now, just check if user is active
        if not user.is_active:
            raise PermissionDenied("User is not active")
        
        # Create task
        task = Task(
            title=task_data.title,
            description=task_data.description,
            status="not_started",  # Default status
            priority=task_data.priority.value,
            project_id=task_data.project_id,
            assignee_id=task_data.assignee_ids[0] if task_data.assignee_ids else None,
            reporter_id=user.id,
            parent_task_id=task_data.parent_task_id,
            due_date=task_data.due_date,
            start_date=None,  # Not in TaskCreate schema
            estimated_hours=task_data.estimated_hours,
            created_by=user.id,
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        return self._task_to_response(task)

    def get_task(self, task_id: int, user: User, db: Session) -> TaskResponse:
        """Get task details."""
        task = db.query(Task).options(
            joinedload(Task.project),
            joinedload(Task.assignee),
            joinedload(Task.reporter),
        ).filter(Task.id == task_id).first()
        
        if not task:
            raise NotFound("Task not found")
        
        # TODO: Check task access permissions
        # For now, just check if user is active
        if not user.is_active:
            raise PermissionDenied("User is not active")
        
        return self._task_to_response(task)

    def update_task(
        self, task_id: int, update_data: TaskUpdate, user: User, db: Session
    ) -> TaskResponse:
        """Update task information."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFound("Task not found")
        
        # TODO: Check task update permissions
        # For now, just check if user is active
        if not user.is_active:
            raise PermissionDenied("User is not active")
        
        # Update fields
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(task, field, value)
        
        task.updated_by = user.id
        task.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(task)
        
        return self._task_to_response(task)

    def delete_task(self, task_id: int, user: User, db: Session) -> bool:
        """Delete a task."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFound("Task not found")
        
        # TODO: Check task delete permissions
        # For now, just check if user is active
        if not user.is_active:
            raise PermissionDenied("User is not active")
        
        # Soft delete
        task.deleted_at = datetime.utcnow()
        task.deleted_by = user.id
        task.is_active = False
        
        db.commit()
        return True

    def list_tasks(
        self,
        filters: Dict[str, Any],
        user: User,
        db: Session,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> TaskListResponse:
        """List tasks with filters and pagination."""
        query = db.query(Task).options(
            joinedload(Task.project),
            joinedload(Task.assignee),
            joinedload(Task.reporter),
        )
        
        # Apply filters
        if filters.get("project_id"):
            query = query.filter(Task.project_id == filters["project_id"])
        if filters.get("status"):
            query = query.filter(Task.status == filters["status"])
        if filters.get("priority"):
            query = query.filter(Task.priority == filters["priority"])
        if filters.get("assignee_id"):
            query = query.filter(Task.assignee_id == filters["assignee_id"])
        
        # Only show active tasks
        query = query.filter(Task.is_active == True)
        
        # Count total
        total = query.count()
        
        # Apply sorting
        if sort_by:
            sort_column = getattr(Task, sort_by, None)
            if sort_column:
                if sort_order == "desc":
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column)
        
        # Apply pagination
        offset = (page - 1) * page_size
        tasks = query.offset(offset).limit(page_size).all()
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return TaskListResponse(
            items=[self._task_to_response(task) for task in tasks],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def update_task_status(
        self, task_id: int, status_update: TaskStatusUpdate, user: User, db: Session
    ) -> TaskResponse:
        """Update task status."""
        raise NotImplementedError("Task status update not implemented")

    def get_task_history(
        self, task_id: int, user: User, db: Session
    ) -> TaskHistoryResponse:
        """Get task change history."""
        raise NotImplementedError("Task history not implemented")

    def assign_user(
        self, task_id: int, assignee_id: int, user: User, db: Session
    ) -> TaskResponse:
        """Assign a user to a task."""
        raise NotImplementedError("User assignment not implemented")

    def unassign_user(
        self, task_id: int, assignee_id: int, user: User, db: Session
    ) -> TaskResponse:
        """Remove a user from a task."""
        raise NotImplementedError("User unassignment not implemented")

    def bulk_assign_users(
        self, task_id: int, assignee_ids: List[int], user: User, db: Session
    ) -> TaskResponse:
        """Assign multiple users to a task."""
        raise NotImplementedError("Bulk user assignment not implemented")

    def set_due_date(
        self, task_id: int, due_date: datetime, user: User, db: Session
    ) -> TaskResponse:
        """Set task due date."""
        raise NotImplementedError("Due date setting not implemented")

    def get_overdue_tasks(
        self, project_id: int, user: User, db: Session
    ) -> TaskListResponse:
        """Get overdue tasks for a project."""
        raise NotImplementedError("Overdue task retrieval not implemented")

    def set_priority(
        self, task_id: int, priority: str, user: User, db: Session
    ) -> TaskResponse:
        """Set task priority."""
        raise NotImplementedError("Priority setting not implemented")

    def add_dependency(
        self, task_id: int, depends_on: int, user: User, db: Session
    ) -> Dict[str, Any]:
        """Add task dependency."""
        raise NotImplementedError("Dependency addition not implemented")

    def get_dependencies(self, task_id: int, user: User, db: Session) -> Dict[str, Any]:
        """Get task dependencies."""
        raise NotImplementedError("Dependency retrieval not implemented")

    def remove_dependency(
        self, task_id: int, depends_on: int, user: User, db: Session
    ) -> bool:
        """Remove task dependency."""
        raise NotImplementedError("Dependency removal not implemented")

    def bulk_update_status(
        self, bulk_data: BulkStatusUpdate, user: User, db: Session
    ) -> BulkUpdateResponse:
        """Update status for multiple tasks."""
        raise NotImplementedError("Bulk status update not implemented")

    def search_tasks(
        self, query: str, user: User, db: Session, page: int = 1, page_size: int = 20
    ) -> TaskListResponse:
        """Search tasks by keyword."""
        raise NotImplementedError("Task search not implemented")
    
    def _task_to_response(self, task: Task) -> TaskResponse:
        """Convert Task model to TaskResponse schema."""
        from app.schemas.task import ProjectInfo, UserInfo, TaskStatus, TaskPriority
        
        # Convert status string to enum
        status_map = {
            "not_started": TaskStatus.NOT_STARTED,
            "in_progress": TaskStatus.IN_PROGRESS,
            "completed": TaskStatus.COMPLETED,
            "on_hold": TaskStatus.ON_HOLD,
            "pending": TaskStatus.NOT_STARTED,  # Map pending to not_started
        }
        status = status_map.get(task.status, TaskStatus.NOT_STARTED)
        
        # Convert priority string to enum
        priority_map = {
            "high": TaskPriority.HIGH,
            "medium": TaskPriority.MEDIUM,
            "low": TaskPriority.LOW,
        }
        priority = priority_map.get(task.priority, TaskPriority.MEDIUM)
        
        # Build project info
        project_info = ProjectInfo(
            id=task.project.id if task.project else task.project_id,
            name=task.project.name if task.project else f"Project {task.project_id}"
        )
        
        # Build assignees list
        assignees = []
        if task.assignee:
            assignees.append(UserInfo(
                id=task.assignee.id,
                name=task.assignee.full_name,
                email=task.assignee.email,
            ))
        
        # Build created_by info
        created_by = UserInfo(
            id=task.reporter.id if task.reporter else task.reporter_id,
            name=task.reporter.full_name if task.reporter else "Unknown",
            email=task.reporter.email if task.reporter else "unknown@example.com",
        )
        
        return TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            project=project_info,
            parent_task_id=task.parent_task_id,
            status=status,
            priority=priority,
            due_date=task.due_date,
            estimated_hours=task.estimated_hours,
            actual_hours=task.actual_hours,
            assignees=assignees,
            tags=[],  # TODO: Implement tags
            created_at=task.created_at,
            updated_at=task.updated_at,
            created_by=created_by,
        )
