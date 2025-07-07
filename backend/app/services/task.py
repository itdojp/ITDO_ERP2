"""Task management service with comprehensive business logic."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, select

from app.models.task import (
    Task, TaskAssignment, TaskDependency, TaskComment, TaskAttachment,
    TaskStatus, TaskPriority, DependencyType, AssignmentRole
)
from app.models.user import User
from app.models.organization import Project
from app.repositories.task import TaskRepository
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskResponse, TaskSearchParams, TaskListResponse,
    TaskAssignmentCreate, TaskDependencyCreate, TaskCommentCreate,
    BulkTaskUpdate, BulkOperationResponse, UserWorkloadResponse, TaskAnalyticsResponse
)
from app.core.exceptions import (
    NotFound, PermissionDenied, BusinessLogicError, CircularDependency,
    InvalidTransition, DependencyExists, OptimisticLockError
)


class TaskService:
    """Service class for task management with business logic."""
    
    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
        self.repository = TaskRepository(db)
    
    def create_task(self, task_data: TaskCreate, user: User) -> TaskResponse:
        """Create a new task with permission checks."""
        # Check project access
        project = self._check_project_access(task_data.project_id, user)
        
        # Validate parent task if specified
        if task_data.parent_task_id:
            parent_task = self.repository.get(task_data.parent_task_id)
            if not parent_task or parent_task.project_id != task_data.project_id:
                raise BusinessLogicError("Parent task must be in the same project")
        
        # Create task
        task_dict = task_data.model_dump(exclude={"assignee_ids"})
        task_dict.update({
            "organization_id": project.organization_id,
            "created_by": user.id,
            "updated_by": user.id
        })
        
        task = Task(**task_dict)
        self.db.add(task)
        self.db.flush()
        
        # Assign initial assignees
        if task_data.assignee_ids:
            for user_id in task_data.assignee_ids:
                self.assign_user(task.id, user_id, AssignmentRole.ASSIGNEE, user)
        
        self.db.commit()
        return self._task_to_response(task)
    
    def update_task(
        self,
        task_id: int,
        task_data: TaskUpdate,
        user: User
    ) -> TaskResponse:
        """Update task with optimistic locking."""
        task = self._get_task_with_permission_check(task_id, user)
        
        # Update with optimistic locking
        update_dict = task_data.model_dump(exclude_unset=True, exclude={"version"})
        update_dict["updated_by"] = user.id
        
        updated_task = self.repository.update_with_optimistic_lock(
            task_id, update_dict, task_data.version
        )
        
        if not updated_task:
            raise OptimisticLockError("Task was modified by another user")
        
        return self._task_to_response(updated_task)
    
    def update_task_status(
        self,
        task_id: int,
        new_status: TaskStatus,
        user: User,
        comment: Optional[str] = None,
        version: int = 1
    ) -> TaskResponse:
        """Update task status with validation."""
        task = self._get_task_with_permission_check(task_id, user)
        
        # Validate status transition
        if not task.can_transition_to(new_status):
            raise InvalidTransition(
                f"Cannot transition from {task.status} to {new_status}"
            )
        
        # Update status
        update_dict = {
            "status": new_status,
            "updated_by": user.id
        }
        
        # Auto-update progress
        if new_status == TaskStatus.COMPLETED:
            update_dict["progress_percentage"] = 100
        elif new_status == TaskStatus.NOT_STARTED:
            update_dict["progress_percentage"] = 0
        
        updated_task = self.repository.update_with_optimistic_lock(
            task_id, update_dict, version
        )
        
        # Add status change comment
        if comment:
            self.add_comment(task_id, TaskCommentCreate(content=comment), user)
        
        if updated_task:
            return self._task_to_response(updated_task)
        else:
            raise ValueError("Failed to update task status")
    
    def search_tasks(
        self,
        params: TaskSearchParams,
        user: User
    ) -> TaskListResponse:
        """Search tasks with user access control."""
        # Get user's organizations and accessible projects
        user_organizations = [org.id for org in user.get_organizations()]
        if not user_organizations:
            # Return empty result if user has no organizations
            return TaskListResponse(
                items=[], total=0, page=params.page, limit=params.limit,
                has_next=False, has_prev=False
            )
        
        # Use first organization for now (multi-org support can be added later)
        organization_id = user_organizations[0]
        accessible_projects = self._get_user_accessible_projects(user, organization_id)
        
        tasks, total = self.repository.search_tasks(
            params, organization_id, accessible_projects
        )
        
        return TaskListResponse(
            items=[self._task_to_response(task) for task in tasks],
            total=total,
            page=params.page,
            limit=params.limit,
            has_next=params.page * params.limit < total,
            has_prev=params.page > 1
        )
    
    def get_task(self, task_id: int, user: User) -> TaskResponse:
        """Get task by ID with permission check."""
        task = self._get_task_with_permission_check(task_id, user)
        return self._task_to_response(task)
    
    def delete_task(self, task_id: int, user: User) -> None:
        """Soft delete task after dependency checks."""
        task = self._get_task_with_permission_check(task_id, user)
        
        # Check for dependencies
        dependencies = self.db.scalars(
            select(TaskDependency).where(TaskDependency.predecessor_id == task_id)
        ).all()
        
        if dependencies:
            raise DependencyExists("Cannot delete task with existing dependencies")
        
        # Soft delete
        task.soft_delete(user.id)
        self.db.commit()
    
    def assign_user(
        self,
        task_id: int,
        user_id: int,
        role: AssignmentRole,
        assigner: User
    ) -> None:
        """Assign user to task."""
        task = self._get_task_with_permission_check(task_id, assigner)
        
        # Check if assignment already exists
        existing = self.db.scalar(
            select(TaskAssignment).where(
                and_(
                    TaskAssignment.task_id == task_id,
                    TaskAssignment.user_id == user_id,
                    TaskAssignment.role == role
                )
            )
        )
        
        if existing:
            raise BusinessLogicError("User already assigned to this task with this role")
        
        # Verify assignee exists and has project access
        assignee = self.db.get(User, user_id)
        if not assignee:
            raise NotFound("User not found")
        
        # Create assignment
        assignment = TaskAssignment(
            task_id=task_id,
            user_id=user_id,
            role=role,
            assigned_at=datetime.now(),
            assigned_by=assigner.id
        )
        self.db.add(assignment)
        self.db.commit()
        
        # TODO: Send notification to assigned user
    
    def remove_assignment(
        self,
        task_id: int,
        user_id: int,
        remover: User
    ) -> None:
        """Remove user assignment from task."""
        task = self._get_task_with_permission_check(task_id, remover)
        
        assignment = self.db.scalar(
            select(TaskAssignment).where(
                and_(
                    TaskAssignment.task_id == task_id,
                    TaskAssignment.user_id == user_id
                )
            )
        )
        
        if assignment:
            self.db.delete(assignment)
            self.db.commit()
    
    def add_dependency(
        self,
        task_id: int,
        dependency_data: TaskDependencyCreate,
        user: User
    ) -> None:
        """Add task dependency with circular dependency check."""
        task = self._get_task_with_permission_check(task_id, user)
        
        # Check for circular dependency
        if self.repository.detect_circular_dependency(
            dependency_data.predecessor_id, task_id
        ):
            raise CircularDependency("Adding this dependency would create a circular reference")
        
        # Verify predecessor exists and is in same project
        predecessor = self.repository.get(dependency_data.predecessor_id)
        if not predecessor:
            raise NotFound("Predecessor task not found")
        
        if predecessor.project_id != task.project_id:
            raise BusinessLogicError("Dependencies must be within the same project")
        
        # Create dependency
        dependency = TaskDependency(
            predecessor_id=dependency_data.predecessor_id,
            successor_id=task_id,
            dependency_type=dependency_data.dependency_type,
            lag_time=dependency_data.lag_time
        )
        self.db.add(dependency)
        self.db.commit()
    
    def remove_dependency(self, dependency_id: int, user: User) -> None:
        """Remove task dependency."""
        dependency = self.db.get(TaskDependency, dependency_id)
        if not dependency:
            raise NotFound("Dependency not found")
        
        # Check permission on successor task
        self._get_task_with_permission_check(dependency.successor_id, user)
        
        self.db.delete(dependency)
        self.db.commit()
    
    def add_comment(
        self,
        task_id: int,
        comment_data: TaskCommentCreate,
        user: User
    ) -> None:
        """Add comment to task."""
        task = self._get_task_with_permission_check(task_id, user)
        
        comment = TaskComment(
            task_id=task_id,
            content=comment_data.content,
            user_id=user.id,
            parent_comment_id=comment_data.parent_comment_id,
            mentioned_users=comment_data.mentioned_users,
            created_by=user.id
        )
        self.db.add(comment)
        self.db.commit()
        
        # TODO: Send notifications to mentioned users
    
    def get_user_workload(self, user_id: int, organization_id: int) -> UserWorkloadResponse:
        """Calculate user workload statistics."""
        user_tasks = self.repository.get_user_tasks(user_id, organization_id)
        
        assigned_count = len(user_tasks)
        estimated_hours = sum(task.estimated_hours or 0 for task in user_tasks)
        overdue_count = sum(1 for task in user_tasks if task.is_overdue())
        completed_count = sum(1 for task in user_tasks if task.status == TaskStatus.COMPLETED)
        in_progress_count = sum(1 for task in user_tasks if task.status == TaskStatus.IN_PROGRESS)
        
        return UserWorkloadResponse(
            user_id=user_id,
            assigned_tasks_count=assigned_count,
            estimated_hours_total=estimated_hours,
            overdue_tasks_count=overdue_count,
            completed_tasks_count=completed_count,
            in_progress_tasks_count=in_progress_count
        )
    
    def get_task_analytics(self, organization_id: int) -> TaskAnalyticsResponse:
        """Get task analytics for organization."""
        stats = self.repository.get_task_statistics(organization_id)
        
        return TaskAnalyticsResponse(
            total_tasks=stats["total_tasks"],
            by_status=stats["by_status"],
            by_priority=stats["by_priority"],
            overdue_count=stats["overdue_count"],
            completion_rate=stats["completion_rate"],
            average_completion_time_days=stats["average_completion_time_days"]
        )
    
    def calculate_critical_path(self, project_id: int, user: User) -> List[TaskResponse]:
        """Calculate critical path for project."""
        project = self._check_project_access(project_id, user)
        
        critical_tasks = self.repository.get_critical_path(project_id)
        return [self._task_to_response(task) for task in critical_tasks]
    
    def bulk_update_tasks(
        self,
        update_data: BulkTaskUpdate,
        user: User
    ) -> BulkOperationResponse:
        """Perform bulk updates on multiple tasks."""
        success_count = 0
        errors = []
        
        for task_id in update_data.task_ids:
            try:
                task = self._get_task_with_permission_check(task_id, user)
                
                update_dict: Dict[str, Any] = {}
                if update_data.status:
                    if task.can_transition_to(update_data.status):
                        update_dict["status"] = update_data.status
                    else:
                        errors.append({
                            "task_id": task_id,
                            "error": f"Invalid status transition from {task.status} to {update_data.status}"
                        })
                        continue
                
                if update_data.priority:
                    update_dict["priority"] = update_data.priority
                
                if update_data.due_date:
                    update_dict["due_date"] = update_data.due_date
                
                if update_data.assignee_id:
                    # Remove existing assignments and add new one
                    old_assignments = self.db.scalars(
                        select(TaskAssignment).where(TaskAssignment.task_id == task_id)
                    ).all()
                    for assignment in old_assignments:
                        self.db.delete(assignment)
                    
                    self.assign_user(task_id, update_data.assignee_id, AssignmentRole.ASSIGNEE, user)
                
                if update_dict:
                    update_dict["updated_by"] = user.id
                    self.repository.update_with_optimistic_lock(
                        task_id, update_dict, task.version
                    )
                
                success_count += 1
                
            except Exception as e:
                errors.append({
                    "task_id": task_id,
                    "error": str(e)
                })
        
        self.db.commit()
        
        return BulkOperationResponse(
            success_count=success_count,
            error_count=len(errors),
            errors=errors
        )
    
    def _get_task_with_permission_check(self, task_id: int, user: User) -> Task:
        """Get task and check user permissions."""
        task = self.repository.get(task_id)
        if not task:
            raise NotFound("Task not found")
        
        # Check organization access
        user_organizations = [org.id for org in user.get_organizations()]
        if task.organization_id not in user_organizations:
            raise PermissionDenied("Access denied to this task")
        
        # Check project access
        accessible_projects = self._get_user_accessible_projects(user, task.organization_id)
        if task.project_id not in accessible_projects:
            raise PermissionDenied("Access denied to this project")
        
        return task
    
    def _check_project_access(self, project_id: int, user: User) -> Project:
        """Check if user has access to project."""
        project = self.db.get(Project, project_id)
        if not project:
            raise NotFound("Project not found")
        
        user_organizations = [org.id for org in user.get_organizations()]
        if project.organization_id not in user_organizations:
            raise PermissionDenied("Access denied to this project")
        
        return project
    
    def _get_user_accessible_projects(self, user: User, organization_id: int) -> List[int]:
        """Get list of project IDs accessible to user."""
        # For now, return all projects in user's organization
        # TODO: Implement proper project-level access control
        projects = self.db.scalars(
            select(Project.id).where(Project.organization_id == organization_id)
        ).all()
        return list(projects)
    
    def _task_to_response(self, task: Task) -> TaskResponse:
        """Convert Task model to TaskResponse schema."""
        return TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            project_id=task.project_id,
            parent_task_id=task.parent_task_id,
            status=task.status,
            priority=task.priority,
            due_date=task.due_date,
            start_date=task.start_date,
            estimated_hours=task.estimated_hours,
            actual_hours=task.actual_hours,
            progress_percentage=task.progress_percentage,
            tags=task.tags,
            version=task.version,
            organization_id=task.organization_id,
            created_at=task.created_at,
            updated_at=task.updated_at,
            created_by=task.created_by,
            updated_by=task.updated_by,
            is_deleted=task.is_deleted
        )