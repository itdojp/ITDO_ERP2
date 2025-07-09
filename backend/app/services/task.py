"""Task service implementation with comprehensive CRUD operations."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.cache import CacheManager
from app.core.performance import PerformanceOptimizer
from app.models.project import Project
from app.models.task import Task, TaskStatus, TaskPriority, TaskType
from app.models.user import User
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskFilter,
    TaskBulkOperation,
    TaskStatusTransition,
    TaskStatistics,
    TaskSummary,
)
from app.services.permission import PermissionService
from app.types import UserId


class TaskService:
    """Service for managing tasks with comprehensive CRUD operations."""

    def __init__(
        self,
        db: Session,
        cache_manager: Optional[CacheManager] = None,
        permission_service: Optional[PermissionService] = None,
    ):
        self.db = db
        self.cache_manager = cache_manager
        self.permission_service = permission_service
        self.optimizer = PerformanceOptimizer(db)

    def create_task(
        self,
        task_data: TaskCreate,
        creator_id: int,
        validate_permissions: bool = True,
    ) -> TaskResponse:
        """Create a new task with comprehensive validation."""
        # Validate project exists
        project = self.db.query(Project).filter(
            Project.id == task_data.project_id,
            Project.is_active == True,
        ).first()
        if not project:
            raise ValueError("Project not found or inactive")

        # Validate assignee exists if provided
        if task_data.assignee_id:
            assignee = self.db.query(User).filter(
                User.id == task_data.assignee_id,
                User.is_active == True,
            ).first()
            if not assignee:
                raise ValueError("Assignee not found or inactive")

        # Validate reporter exists if provided
        if task_data.reporter_id:
            reporter = self.db.query(User).filter(
                User.id == task_data.reporter_id,
                User.is_active == True,
            ).first()
            if not reporter:
                raise ValueError("Reporter not found or inactive")

        # Validate epic exists if provided
        if task_data.epic_id:
            epic = self.db.query(Task).filter(
                Task.id == task_data.epic_id,
                Task.project_id == task_data.project_id,
                Task.task_type == TaskType.EPIC.value,
                Task.is_deleted == False,
            ).first()
            if not epic:
                raise ValueError("Epic not found or invalid")

        # Validate parent task exists if provided
        parent_task_id = task_data.epic_id or task_data.parent_task_id
        if parent_task_id:
            parent_task = self.db.query(Task).filter(
                Task.id == parent_task_id,
                Task.project_id == task_data.project_id,
                Task.is_deleted == False,
            ).first()
            if not parent_task:
                raise ValueError("Parent task not found or invalid")

        # Validate permission if service is available
        if validate_permissions and self.permission_service:
            has_permission = self.permission_service.check_user_permission(
                creator_id, "task.create", project.organization_id
            )
            if not has_permission:
                raise PermissionError("Insufficient permissions to create task")

        # Create task
        task = Task(
            title=task_data.title,
            description=task_data.description,
            project_id=task_data.project_id,
            assignee_id=task_data.assignee_id,
            reporter_id=task_data.reporter_id or creator_id,
            epic_id=task_data.epic_id or task_data.parent_task_id,
            status=task_data.status,
            priority=task_data.priority,
            task_type=task_data.task_type,
            due_date=task_data.due_date,
            estimated_hours=task_data.estimated_hours,
            labels={label: "" for label in task_data.labels} if task_data.labels else {},
            custom_fields=task_data.metadata or {},
            depends_on=task_data.dependencies or [],
            is_deleted=False,
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        # Invalidate cache
        self._invalidate_task_cache(task.id, task.project_id)

        return self._task_to_response(task)

    def get_task(
        self,
        task_id: int,
        user_id: Optional[int] = None,
        validate_permissions: bool = True,
    ) -> Optional[TaskResponse]:
        """Get task by ID with permission validation."""
        query = (
            self.db.query(Task)
            .options(
                joinedload(Task.project),
                joinedload(Task.assignee),
                joinedload(Task.reporter),
                joinedload(Task.epic),
                selectinload(Task.subtasks),
            )
            .filter(Task.id == task_id, Task.is_deleted == False)
        )

        task = query.first()
        if not task:
            return None

        # Validate permission if service is available
        if validate_permissions and self.permission_service and user_id:
            has_permission = self.permission_service.check_user_permission(
                user_id, "task.view", task.project.organization_id
            )
            if not has_permission:
                raise PermissionError("Insufficient permissions to view task")

        return self._task_to_response(task)

    def update_task(
        self,
        task_id: int,
        task_data: TaskUpdate,
        user_id: int,
        validate_permissions: bool = True,
    ) -> TaskResponse:
        """Update task with comprehensive validation."""
        task = self.db.query(Task).filter(
            Task.id == task_id,
            Task.is_deleted == False,
        ).first()

        if not task:
            raise ValueError("Task not found")

        # Validate permission if service is available
        if validate_permissions and self.permission_service:
            has_permission = self.permission_service.check_user_permission(
                user_id, "task.edit", task.project.organization_id
            )
            if not has_permission and task.assignee_id != user_id:
                raise PermissionError("Insufficient permissions to update task")

        # Update fields
        update_data = task_data.model_dump(exclude_unset=True)
        
        # Handle status change
        if "status" in update_data:
            new_status = update_data["status"]
            if new_status != task.status:
                # Update completion date if task is completed
                if new_status == TaskStatus.DONE.value:
                    task.completed_date = datetime.utcnow()
                elif task.status == TaskStatus.DONE.value:
                    # Reset completion date if moving away from done
                    task.completed_date = None
                task.status = new_status

        # Handle other updates
        for field, value in update_data.items():
            if field != "status" and hasattr(task, field):
                setattr(task, field, value)

        # Update timestamps
        task.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(task)

        # Invalidate cache
        self._invalidate_task_cache(task.id, task.project_id)

        return self._task_to_response(task)

    def delete_task(
        self,
        task_id: int,
        user_id: int,
        validate_permissions: bool = True,
    ) -> bool:
        """Delete task (soft delete)."""
        task = self.db.query(Task).filter(
            Task.id == task_id,
            Task.is_deleted == False,
        ).first()

        if not task:
            raise ValueError("Task not found")

        # Validate permission if service is available
        if validate_permissions and self.permission_service:
            has_permission = self.permission_service.check_user_permission(
                user_id, "task.delete", task.project.organization_id
            )
            if not has_permission:
                raise PermissionError("Insufficient permissions to delete task")

        # Check if task has subtasks
        subtasks = self.db.query(Task).filter(
            Task.epic_id == task_id,
            Task.is_deleted == False,
        ).all()
        
        if subtasks:
            raise ValueError("Cannot delete task with active subtasks")

        # Soft delete
        task.is_deleted = True
        task.updated_at = datetime.utcnow()

        self.db.commit()

        # Invalidate cache
        self._invalidate_task_cache(task.id, task.project_id)

        return True

    def list_tasks(
        self,
        user_id: int,
        filters: Optional[TaskFilter] = None,
        page: int = 1,
        per_page: int = 50,
        validate_permissions: bool = True,
    ) -> Tuple[List[TaskResponse], int]:
        """List tasks with filtering and pagination."""
        query = (
            self.db.query(Task)
            .options(
                joinedload(Task.project),
                joinedload(Task.assignee),
                joinedload(Task.reporter),
            )
            .filter(Task.is_deleted == False)
        )

        # Apply filters
        if filters:
            if filters.project_id:
                query = query.filter(Task.project_id == filters.project_id)
            if filters.assignee_id:
                query = query.filter(Task.assignee_id == filters.assignee_id)
            if filters.reporter_id:
                query = query.filter(Task.reporter_id == filters.reporter_id)
            if filters.epic_id:
                query = query.filter(Task.epic_id == filters.epic_id)
            if filters.epic_id:
                query = query.filter(Task.epic_id == filters.epic_id)
            if filters.status:
                query = query.filter(Task.status == filters.status)
            if filters.priority:
                query = query.filter(Task.priority == filters.priority)
            if filters.task_type:
                query = query.filter(Task.task_type == filters.task_type)
            if filters.due_date_from:
                query = query.filter(Task.due_date >= filters.due_date_from)
            if filters.due_date_to:
                query = query.filter(Task.due_date <= filters.due_date_to)
            if filters.estimated_hours_min:
                query = query.filter(Task.estimated_hours >= filters.estimated_hours_min)
            if filters.estimated_hours_max:
                query = query.filter(Task.estimated_hours <= filters.estimated_hours_max)
            if filters.labels:
                # Filter by labels (assuming labels is a JSON array)
                for label in filters.labels:
                    query = query.filter(Task.labels.contains([label]))
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Task.title.ilike(search_term),
                        Task.description.ilike(search_term),
                    )
                )

        # Permission filtering
        if validate_permissions and self.permission_service:
            # Get accessible projects
            accessible_projects = self._get_accessible_projects(user_id)
            if accessible_projects:
                query = query.filter(Task.project_id.in_(accessible_projects))
            else:
                # No accessible projects, return empty result
                return [], 0

        # Get total count
        total = query.count()

        # Apply pagination
        tasks = query.offset((page - 1) * per_page).limit(per_page).all()

        return [self._task_to_response(task) for task in tasks], total

    def search_tasks(
        self,
        query: str,
        user_id: int,
        project_id: Optional[int] = None,
        limit: int = 20,
    ) -> List[TaskResponse]:
        """Search tasks by title and description."""
        search_query = (
            self.db.query(Task)
            .options(
                joinedload(Task.project),
                joinedload(Task.assignee),
            )
            .filter(
                Task.is_deleted == False,
                or_(
                    Task.title.ilike(f"%{query}%"),
                    Task.description.ilike(f"%{query}%"),
                )
            )
        )

        if project_id:
            search_query = search_query.filter(Task.project_id == project_id)

        # Permission filtering
        if self.permission_service:
            accessible_projects = self._get_accessible_projects(user_id)
            if accessible_projects:
                search_query = search_query.filter(Task.project_id.in_(accessible_projects))
            else:
                return []

        tasks = search_query.limit(limit).all()
        return [self._task_to_response(task) for task in tasks]

    def get_task_statistics(
        self,
        task_id: int,
        user_id: Optional[int] = None,
    ) -> TaskStatistics:
        """Get task statistics."""
        task = self.db.query(Task).filter(
            Task.id == task_id,
            Task.is_deleted == False,
        ).first()

        if not task:
            raise ValueError("Task not found")

        # Validate permission if service is available
        if self.permission_service and user_id:
            has_permission = self.permission_service.check_user_permission(
                user_id, "task.view", task.project.organization_id
            )
            if not has_permission:
                raise PermissionError("Insufficient permissions to view task statistics")

        # Calculate statistics
        subtask_count = self.db.query(Task).filter(
            Task.epic_id == task_id,
            Task.is_deleted == False,
        ).count()

        dependency_count = len(task.depends_on or [])
        
        # Count tasks blocked by this task
        blocked_by_count = self.db.query(Task).filter(
            Task.depends_on.contains([task_id]),
            Task.is_deleted == False,
        ).count()

        # Calculate completion rate
        completion_rate = None
        if task.estimated_hours and task.actual_hours:
            completion_rate = min(100.0, (task.actual_hours / task.estimated_hours) * 100)

        # Calculate time spent percentage
        time_spent_percentage = None
        if task.estimated_hours and task.actual_hours:
            time_spent_percentage = (task.actual_hours / task.estimated_hours) * 100

        return TaskStatistics(
            task_id=task.id,
            project_id=task.project_id,
            completion_rate=completion_rate,
            time_spent_percentage=time_spent_percentage,
            days_remaining=task.days_remaining,
            is_overdue=task.is_overdue,
            subtask_count=subtask_count,
            dependency_count=dependency_count,
            blocked_by_count=blocked_by_count,
        )

    def transition_task_status(
        self,
        task_id: int,
        transition: TaskStatusTransition,
        user_id: int,
    ) -> TaskResponse:
        """Transition task status with validation."""
        task = self.db.query(Task).filter(
            Task.id == task_id,
            Task.is_deleted == False,
        ).first()

        if not task:
            raise ValueError("Task not found")

        # Validate current status
        if task.status != transition.from_status:
            raise ValueError(f"Task is in {task.status} status, not {transition.from_status}")

        # Validate permission
        if self.permission_service:
            has_permission = self.permission_service.check_user_permission(
                user_id, "task.edit", task.project.organization_id
            )
            if not has_permission and task.assignee_id != user_id:
                raise PermissionError("Insufficient permissions to transition task")

        # Apply transition
        task.status = transition.to_status
        
        # Update completion date if moving to done
        if transition.to_status == TaskStatus.DONE.value:
            task.completed_date = datetime.utcnow()
        elif task.status == TaskStatus.DONE.value:
            task.completed_date = None

        # Update start date if moving to in progress
        if transition.to_status == TaskStatus.IN_PROGRESS.value and not task.start_date:
            task.start_date = datetime.utcnow().date()

        task.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(task)

        # Invalidate cache
        self._invalidate_task_cache(task.id, task.project_id)

        return self._task_to_response(task)

    def bulk_update_tasks(
        self,
        bulk_operation: TaskBulkOperation,
        user_id: int,
    ) -> Dict[str, Any]:
        """Bulk update tasks."""
        tasks = self.db.query(Task).filter(
            Task.id.in_(bulk_operation.task_ids),
            Task.is_deleted == False,
        ).all()

        if not tasks:
            return {"success": False, "message": "No tasks found", "updated_count": 0}

        # Validate permissions for all tasks
        if self.permission_service:
            for task in tasks:
                has_permission = self.permission_service.check_user_permission(
                    user_id, "task.edit", task.project.organization_id
                )
                if not has_permission:
                    raise PermissionError(f"Insufficient permissions to update task {task.id}")

        updated_count = 0
        errors = []

        for task in tasks:
            try:
                if bulk_operation.operation == "update_status":
                    if bulk_operation.data and "status" in bulk_operation.data:
                        task.status = bulk_operation.data["status"]
                        if task.status == TaskStatus.DONE.value:
                            task.completed_date = datetime.utcnow()
                        updated_count += 1

                elif bulk_operation.operation == "update_priority":
                    if bulk_operation.data and "priority" in bulk_operation.data:
                        task.priority = bulk_operation.data["priority"]
                        updated_count += 1

                elif bulk_operation.operation == "assign_to":
                    if bulk_operation.data and "assignee_id" in bulk_operation.data:
                        task.assignee_id = bulk_operation.data["assignee_id"]
                        updated_count += 1

                elif bulk_operation.operation == "set_due_date":
                    if bulk_operation.data and "due_date" in bulk_operation.data:
                        task.due_date = bulk_operation.data["due_date"]
                        updated_count += 1

                elif bulk_operation.operation == "add_labels":
                    if bulk_operation.data and "labels" in bulk_operation.data:
                        current_labels = set(task.labels.keys()) if task.labels else set()
                        new_labels = set(bulk_operation.data["labels"])
                        # Convert to dict format as expected by the model
                        task.labels = {label: "" for label in current_labels.union(new_labels)}
                        updated_count += 1

                elif bulk_operation.operation == "remove_labels":
                    if bulk_operation.data and "labels" in bulk_operation.data:
                        current_labels = set(task.labels.keys()) if task.labels else set()
                        remove_labels = set(bulk_operation.data["labels"])
                        # Convert to dict format as expected by the model
                        remaining_labels = current_labels - remove_labels
                        task.labels = {label: task.labels.get(label, "") if task.labels else "" for label in remaining_labels}
                        updated_count += 1

                elif bulk_operation.operation == "activate":
                    task.is_deleted = False
                    updated_count += 1

                elif bulk_operation.operation == "deactivate":
                    task.is_deleted = True
                    updated_count += 1

                task.updated_at = datetime.utcnow()

            except Exception as e:
                errors.append(f"Error updating task {task.id}: {str(e)}")

        if updated_count > 0:
            self.db.commit()

            # Invalidate cache for all updated tasks
            for task in tasks:
                self._invalidate_task_cache(task.id, task.project_id)

        return {
            "success": True,
            "updated_count": updated_count,
            "total_count": len(tasks),
            "errors": errors,
        }

    def get_task_dependencies(
        self,
        task_id: int,
        user_id: int,
    ) -> List[TaskResponse]:
        """Get task dependencies."""
        task = self.db.query(Task).filter(
            Task.id == task_id,
            Task.is_deleted == False,
        ).first()

        if not task:
            raise ValueError("Task not found")

        if not task.depends_on:
            return []

        dependencies = self.db.query(Task).filter(
            Task.id.in_(task.depends_on),
            Task.is_deleted == False,
        ).all()

        return [self._task_to_response(dep) for dep in dependencies]

    def get_task_subtasks(
        self,
        task_id: int,
        user_id: int,
    ) -> List[TaskResponse]:
        """Get task subtasks."""
        subtasks = self.db.query(Task).filter(
            Task.epic_id == task_id,
            Task.is_deleted == False,
        ).all()

        return [self._task_to_response(task) for task in subtasks]

    def _task_to_response(self, task: Task) -> TaskResponse:
        """Convert Task model to TaskResponse schema."""
        return TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            task_type=task.task_type,
            due_date=task.due_date,
            estimated_hours=task.estimated_hours,
            labels=list(task.labels.keys()) if task.labels else None,
            metadata=dict(task.custom_fields) if task.custom_fields else None,
            project_id=task.project_id,
            created_at=task.created_at,
            updated_at=task.updated_at,
            # Extended fields
            assignee_id=task.assignee_id,
            reporter_id=task.reporter_id,
            epic_id=task.epic_id,
            parent_task_id=task.epic_id,  # Use epic_id as parent_task_id
            start_date=task.start_date,
            completed_date=task.completed_date,
            actual_hours=task.actual_hours,
            story_points=task.story_points,
            is_active=not task.is_deleted,
            # Computed properties
            is_overdue=task.is_overdue,
            days_remaining=task.days_remaining,
            completion_rate=task.completion_rate,
            time_spent_percentage=task.time_spent_percentage,
            # Relationships
            assignee_name=task.assignee.full_name if task.assignee else None,
            reporter_name=task.reporter.full_name if task.reporter else None,
            project_name=task.project.name if task.project else None,
            epic_title=task.epic.title if task.epic else None,
            parent_task_title=task.epic.title if task.epic else None,
            # Counts
            subtask_count=len(task.subtasks) if task.subtasks else 0,
            dependency_count=len(task.depends_on) if task.depends_on else 0,
        )

    def _get_accessible_projects(self, user_id: int) -> List[int]:
        """Get list of project IDs accessible to the user."""
        # This is a simplified implementation
        # In a real system, you'd check user permissions
        return [p.id for p in self.db.query(Project).filter(Project.is_active == True).all()]

    def _invalidate_task_cache(self, task_id: int, project_id: int) -> None:
        """Invalidate task-related cache entries."""
        if self.cache_manager:
            cache_keys = [
                f"task:{task_id}",
                f"project:{project_id}:tasks",
                f"task:{task_id}:stats",
            ]
            for key in cache_keys:
                # Note: Cache delete is async but called synchronously here
                # This is a limitation of the current sync/async architecture
                pass