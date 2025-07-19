"""Task management service."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import BusinessLogicError, NotFound, PermissionDenied
from app.models.department import Department
from app.models.project import Project
from app.models.task import Task, TaskPriority, TaskStatus as ModelTaskStatus
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
from app.services.audit import AuditLogger
from app.services.permission import PermissionService, permission_service


class TaskService:
    """Service for managing tasks."""

    def __init__(self, permission_service: Optional[PermissionService] = None) -> None:
        """Initialize task service."""
        self.permission_service = permission_service

    def _log_task_change(
        self,
        action: str,
        task: Task,
        user: User,
        db: Session,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log task changes to audit log."""
        changes = {}

        if old_values and new_values:
            # Record specific field changes
            for field, new_value in new_values.items():
                old_value = old_values.get(field)
                if old_value != new_value:
                    changes[field] = {"old": old_value, "new": new_value}
        elif new_values:
            # For creation, record all values
            changes = {"created": new_values}
        elif old_values:
            # For deletion, record deleted values
            changes = {"deleted": old_values}

        AuditLogger.log(
            action=action,
            resource_type="task",
            resource_id=task.id,
            user=user,
            changes=changes,
            db=db,
            organization_id=getattr(user, "organization_id", None),
        )

    def create_task(
        self, task_data: TaskCreate, user: User, db: Session
    ) -> TaskResponse:
        """Create a new task."""
        # Check if project exists and user has access
        project = db.query(Project).filter(Project.id == task_data.project_id).first()
        if not project:
            raise NotFound("Project not found")

        # Check task creation permissions
        if self.permission_service:
            self.permission_service.require_permission(
                user, "task.create", organization_id=user.organization_id, db=db
            )

        # Check project access permissions
        if self.permission_service:
            self.permission_service.require_permission(
                user, "project.view", organization_id=user.organization_id, db=db
            )

        # Check if user has project access through roles
        user_org_ids = [org.id for org in user.get_organizations()]
        if project.organization_id not in user_org_ids:
            raise PermissionDenied("User does not have access to this project")

        # Create task
        task = Task(
            title=task_data.title,
            description=task_data.description,
            status="not_started",  # Default status
            priority=task_data.priority.value,
            project_id=task_data.project_id,
            assignee_id=task_data.assignee_ids[0] if task_data.assignee_ids else None,
            reporter_id=user.id,
            # parent_task_id=task_data.parent_task_id,  # TODO: Implement via TaskDependency
            due_date=task_data.due_date,
            start_date=None,  # Not in TaskCreate schema
            estimated_hours=task_data.estimated_hours,
            created_by=user.id,
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        # Log task creation
        self._log_task_change(
            action="create",
            task=task,
            user=user,
            db=db,
            new_values={
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
                "project_id": task.project_id,
                "assignee_id": task.assigned_to,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "estimated_hours": task.estimated_hours,
            },
        )

        return self._task_to_response(task)

    def get_task(self, task_id: int, user: User, db: Session) -> TaskResponse:
        """Get task details."""
        task = (
            db.query(Task)
            .options(
                joinedload(Task.project),
                joinedload(Task.assignee),
                joinedload(Task.creator),
            )
            .filter(Task.id == task_id)
            .first()
        )

        if not task:
            raise NotFound("Task not found")

        # Check task view permissions
        # User can view tasks they created or are assigned to (owner-based access)
        # or if they have general task.view permission
        has_general_permission = (
            self.permission_service and
            self.permission_service.has_permission(
                user, "task.view", organization_id=user.organization_id, db=db
            )
        )
        is_task_owner = task.created_by == user.id or task.assigned_to == user.id

        if not has_general_permission and not is_task_owner:
            raise PermissionDenied("No access to this task")

        # Check if user has access to the task's project
        user_org_ids = [org.id for org in user.get_organizations()]
        if task.project.organization_id not in user_org_ids:
            raise PermissionDenied("User does not have access to this task")

        return self._task_to_response(task)

    def update_task(
        self, task_id: int, update_data: TaskUpdate, user: User, db: Session
    ) -> TaskResponse:
        """Update task information."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFound("Task not found")

        # Check task update permissions
        # User can update tasks they created or are assigned to (owner-based access)
        # or if they have general task.edit permission
        has_general_permission = False
        if self.permission_service:
            has_general_permission = self.permission_service.has_permission(
                user, "task.edit", organization_id=user.organization_id, db=db
            )
        is_task_owner = task.created_by == user.id or task.assigned_to == user.id

        if not has_general_permission and not is_task_owner:
            raise PermissionDenied("No permission to update this task")

        # Capture old values for audit log
        old_values = {
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "assignee_id": task.assigned_to,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "estimated_hours": task.estimated_hours,
        }

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(task, field, value)

        task.updated_by = user.id
        task.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(task)

        # Capture new values for audit log
        new_values = {
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "assignee_id": task.assigned_to,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "estimated_hours": task.estimated_hours,
        }

        # Log task update
        self._log_task_change(
            action="update",
            task=task,
            user=user,
            db=db,
            old_values=old_values,
            new_values=new_values,
        )

        return self._task_to_response(task)

    def delete_task(self, task_id: int, user: User, db: Session) -> bool:
        """Delete a task."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFound("Task not found")

        # Check task delete permissions
        # Only users with task.delete permission or task creators can delete tasks
        has_delete_permission = False
        if self.permission_service:
            has_delete_permission = self.permission_service.has_permission(
                user, "task.delete", organization_id=user.organization_id, db=db
            )
        is_task_creator = task.created_by == user.id

        if not has_delete_permission and not is_task_creator:
            raise PermissionDenied("No permission to delete this task")

        # Capture task values before deletion for audit log
        old_values = {
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "project_id": task.project_id,
            "assignee_id": task.assigned_to,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "estimated_hours": task.estimated_hours,
        }

        # Check if user can delete this task
        # Users can delete tasks if they are:
        # 1. The task creator/reporter
        # 2. The task assignee
        # 3. Have 'task.delete' permission in the task's project organization
        can_delete = (
            task.created_by == user.id
            or task.assigned_to == user.id
            or user.is_superuser
        )

        # Check organization-level permissions if user is not directly involved
        if not can_delete and task.project and task.project.organization_id:
            can_delete = user.has_permission(
                "task.delete", task.project.organization_id
            )

        if not can_delete:
            raise PermissionDenied("Insufficient permissions to delete this task")

        # Soft delete
        task.deleted_at = datetime.utcnow()
        task.deleted_by = user.id
        task.is_deleted = True

        db.commit()

        # Log task deletion
        self._log_task_change(
            action="delete",
            task=task,
            user=user,
            db=db,
            old_values=old_values,
        )

        return True

    def list_tasks(
        self,
        filters: dict[str, Any],
        user: User,
        db: Session,
        page: int = 1,
        page_size: int = 20,
        sort_by: str | None = None,
        sort_order: str = "asc",
    ) -> TaskListResponse:
        """List tasks with filters and pagination."""
        query = db.query(Task).options(
            joinedload(Task.project),
            joinedload(Task.assignee),
            joinedload(Task.creator),
        )

        # Apply permission-based filtering
        # If user doesn't have general task.view permission, only show their own tasks
        has_general_permission = (
            self.permission_service and
            self.permission_service.has_permission(
                user, "task.view", organization_id=user.organization_id, db=db
            )
        )

        if not has_general_permission:
            # Filter to only tasks user created or is assigned to
            query = query.filter(
                (Task.created_by == user.id) | (Task.assigned_to == user.id)
            )

        # Apply filters
        if filters.get("project_id"):
            query = query.filter(Task.project_id == filters["project_id"])
        if filters.get("status"):
            query = query.filter(Task.status == filters["status"])
        if filters.get("priority"):
            query = query.filter(Task.priority == filters["priority"])
        if filters.get("assignee_id"):
            query = query.filter(Task.assigned_to == filters["assignee_id"])

        # Only show active tasks (not deleted)
        query = query.filter(Task.is_deleted.is_(False))

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
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFound("Task not found")

        # Check task update permissions
        # User can update status of tasks they created or are assigned to
        # (owner-based access)
        # or if they have general task.edit permission
        has_general_permission = False
        if self.permission_service:
            has_general_permission = self.permission_service.has_permission(
                user, "task.edit", organization_id=user.organization_id, db=db
            )
        is_task_owner = task.created_by == user.id or task.assigned_to == user.id

        if not has_general_permission and not is_task_owner:
            raise PermissionDenied("No permission to update this task status")

        # Capture old status for audit log
        old_status = task.status

        # Check if user can update this task
        # Users can update tasks if they are:
        # 1. The task creator/reporter
        # 2. The task assignee
        # 3. Have 'task.update' permission in the task's project organization
        can_update = (
            task.created_by == user.id
            or task.assigned_to == user.id
            or user.is_superuser
        )

        # Check organization-level permissions if user is not directly involved
        if not can_update and task.project and task.project.organization_id:
            can_update = user.has_permission(
                "task.update", task.project.organization_id
            )

        if not can_update:
            raise PermissionDenied("Insufficient permissions to update this task")

        # Update status
        task.status = ModelTaskStatus(status_update.status.value)
        if status_update.status.value == "completed":
            task.completed_at = datetime.utcnow()

        task.updated_by = user.id
        task.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(task)

        # Log status change
        self._log_task_change(
            action="update_status",
            task=task,
            user=user,
            db=db,
            old_values={"status": old_status},
            new_values={"status": status_update.status.value},
        )

        return self._task_to_response(task)

    def get_task_history(
        self, task_id: int, user: User, db: Session
    ) -> TaskHistoryResponse:
        """Get task change history."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFound("Task not found")

        # Check task view permissions
        # User can view history of tasks they created or are assigned to
        # (owner-based access)
        # or if they have general task.view permission
        has_general_permission = (
            self.permission_service and
            self.permission_service.has_permission(
                user, "task.view", organization_id=user.organization_id, db=db
            )
        )
        is_task_owner = task.created_by == user.id or task.assigned_to == user.id

        if not has_general_permission and not is_task_owner:
            raise PermissionDenied("No access to this task history")

        # Get audit logs for this task
        from app.models.audit import AuditLog

        audit_logs = (
            db.query(AuditLog)
            .filter(AuditLog.resource_type == "task", AuditLog.resource_id == task_id)
            .order_by(AuditLog.created_at.desc())
            .all()
        )

        # Convert audit logs to history items
        from app.schemas.task import TaskHistoryItem

        history_items = []
        for log in audit_logs:
            # Get user info for the log
            log_user = db.query(User).filter(User.id == log.user_id).first()
            user_name = log_user.full_name if log_user else "Unknown User"

            history_items.append(
                TaskHistoryItem(
                    id=log.id,
                    action=log.action,
                    user_name=user_name,
                    timestamp=log.created_at,
                    changes=log.changes or {},
                )
            )

        return TaskHistoryResponse(items=history_items, total=len(history_items))

    def assign_user(
        self, task_id: int, assignee_id: int, user: User, db: Session
    ) -> TaskResponse:
        """Assign a user to a task."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFound("Task not found")

        # Check if assignee exists
        from app.models.user import User as UserModel

        assignee = db.query(UserModel).filter(UserModel.id == assignee_id).first()
        if not assignee:
            raise NotFound("User not found")

        # Check assignment permissions
        # User can assign tasks they created or if they have task.edit permission
        has_general_permission = False
        if self.permission_service:
            has_general_permission = self.permission_service.has_permission(
                user, "task.edit", organization_id=user.organization_id, db=db
            )
        is_task_creator = task.created_by == user.id

        if not has_general_permission and not is_task_creator:
            raise PermissionDenied("No permission to assign this task")

        # Check if assignee is in the same organization
        if hasattr(assignee, "organization_id") and hasattr(user, "organization_id"):
            if assignee.organization_id != user.organization_id:
                raise PermissionDenied(
                    "Cannot assign task to user from different organization"
                )

        # Capture old assignee for audit log
        old_assignee_id = task.assigned_to

        # Check if user can assign this task
        # Users can assign tasks if they are:
        # 1. The task creator/reporter
        # 2. Have 'task.assign' permission in the task's project organization
        # 3. Are a project manager or have management role
        can_assign = task.created_by == user.id or user.is_superuser

        # Check organization-level permissions
        if not can_assign and task.project and task.project.organization_id:
            can_assign = user.has_permission(
                "task.assign", task.project.organization_id
            )

        if not can_assign:
            raise PermissionDenied("Insufficient permissions to assign this task")

        task.assigned_to = assignee_id
        task.updated_by = user.id
        task.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(task)

        # Log assignment change
        self._log_task_change(
            action="assign_user",
            task=task,
            user=user,
            db=db,
            old_values={"assignee_id": old_assignee_id},
            new_values={"assignee_id": assignee_id},
        )

        return self._task_to_response(task)

    def unassign_user(
        self, task_id: int, assignee_id: int, user: User, db: Session
    ) -> TaskResponse:
        """Remove a user from a task."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFound("Task not found")

        # Check unassignment permissions
        # User can unassign tasks they created or if they have task.edit permission
        has_general_permission = False
        if self.permission_service:
            has_general_permission = self.permission_service.has_permission(
                user, "task.edit", organization_id=user.organization_id, db=db
            )
        is_task_creator = task.created_by == user.id

        if not has_general_permission and not is_task_creator:
            raise PermissionDenied("No permission to unassign this task")

        # Check if user can unassign this task
        # Users can unassign tasks if they are:
        # 1. The task creator/reporter
        # 2. The currently assigned user (self-unassignment)
        # 3. Have 'task.assign' permission in the task's project organization
        can_unassign = (
            task.created_by == user.id
            or task.assigned_to == user.id
            or user.is_superuser
        )

        # Check organization-level permissions
        if not can_unassign and task.project and task.project.organization_id:
            can_unassign = user.has_permission(
                "task.assign", task.project.organization_id
            )

        if not can_unassign:
            raise PermissionDenied("Insufficient permissions to unassign this task")

        if task.assigned_to != assignee_id:
            raise BusinessLogicError("User is not assigned to this task")

        # Capture old assignee for audit log
        old_assignee_id = task.assigned_to

        task.assigned_to = None
        task.updated_by = user.id
        task.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(task)

        # Log unassignment change
        self._log_task_change(
            action="unassign_user",
            task=task,
            user=user,
            db=db,
            old_values={"assignee_id": old_assignee_id},
            new_values={"assignee_id": None},
        )

        return self._task_to_response(task)

    def bulk_assign_users(
        self, task_id: int, assignee_ids: list[int], user: User, db: Session
    ) -> TaskResponse:
        """Assign multiple users to a task."""
        # For now, assign the first user only (single assignee model)
        if not assignee_ids:
            raise BusinessLogicError("At least one assignee ID required")

        return self.assign_user(task_id, assignee_ids[0], user, db)

    def set_due_date(
        self, task_id: int, due_date: datetime, user: User, db: Session
    ) -> TaskResponse:
        """Set task due date."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFound("Task not found")

        # Check task update permissions
        # User can update due date of tasks they created or are assigned to
        # (owner-based access)
        # or if they have general task.edit permission
        has_general_permission = False
        if self.permission_service:
            has_general_permission = self.permission_service.has_permission(
                user, "task.edit", organization_id=user.organization_id, db=db
            )
        is_task_owner = task.created_by == user.id or task.assigned_to == user.id

        if not has_general_permission and not is_task_owner:
            raise PermissionDenied("No permission to update this task due date")

        # Check if user can update this task
        # Users can update tasks if they are:
        # 1. The task creator/reporter
        # 2. The task assignee
        # 3. Have 'task.update' permission in the task's project organization
        can_update = (
            task.created_by == user.id
            or task.assigned_to == user.id
            or user.is_superuser
        )

        # Check organization-level permissions if user is not directly involved
        if not can_update and task.project and task.project.organization_id:
            can_update = user.has_permission(
                "task.update", task.project.organization_id
            )

        if not can_update:
            raise PermissionDenied("Insufficient permissions to update this task")

        task.due_date = due_date
        task.updated_by = user.id
        task.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(task)

        return self._task_to_response(task)

    def get_overdue_tasks(
        self, project_id: int, user: User, db: Session
    ) -> TaskListResponse:
        """Get overdue tasks for a project."""
        if not user.is_active:
            raise PermissionDenied("User is not active")

        now = datetime.utcnow()
        overdue_tasks = (
            db.query(Task)
            .options(
                joinedload(Task.project),
                joinedload(Task.assignee),
                joinedload(Task.creator),
            )
            .filter(
                Task.project_id == project_id,
                Task.due_date < now,
                Task.status != "completed",
                Task.is_deleted.is_(False),
            )
            .all()
        )

        return TaskListResponse(
            items=[self._task_to_response(task) for task in overdue_tasks],
            total=len(overdue_tasks),
            page=1,
            page_size=len(overdue_tasks),
            total_pages=1,
        )

    def set_priority(
        self, task_id: int, priority: str, user: User, db: Session
    ) -> TaskResponse:
        """Set task priority."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFound("Task not found")

        # Validate priority
        valid_priorities = ["high", "medium", "low"]
        if priority not in valid_priorities:
            raise BusinessLogicError(
                f"Invalid priority. Must be one of: {valid_priorities}"
            )

        # Check task update permissions
        # User can update priority of tasks they created or are assigned to
        # (owner-based access)
        # or if they have general task.edit permission
        has_general_permission = False
        if self.permission_service:
            has_general_permission = self.permission_service.has_permission(
                user, "task.edit", organization_id=user.organization_id, db=db
            )
        is_task_owner = task.created_by == user.id or task.assigned_to == user.id

        if not has_general_permission and not is_task_owner:
            raise PermissionDenied("No permission to update this task priority")

        # Check if user can update this task
        # Users can update tasks if they are:
        # 1. The task creator/reporter
        # 2. The task assignee
        # 3. Have 'task.update' permission in the task's project organization
        can_update = (
            task.created_by == user.id
            or task.assigned_to == user.id
            or user.is_superuser
        )

        # Check organization-level permissions if user is not directly involved
        if not can_update and task.project and task.project.organization_id:
            can_update = user.has_permission(
                "task.update", task.project.organization_id
            )

        if not can_update:
            raise PermissionDenied("Insufficient permissions to update this task")

        task.priority = TaskPriority(priority)
        task.updated_by = user.id
        task.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(task)

        return self._task_to_response(task)

    def add_dependency(
        self, task_id: int, depends_on: int, user: User, db: Session
    ) -> dict[str, Any]:
        """Add task dependency."""
        # For now, use parent_task_id for simple hierarchy
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFound("Task not found")

        depends_task = db.query(Task).filter(Task.id == depends_on).first()
        if not depends_task:
            raise NotFound("Dependency task not found")

        if not user.is_active:
            raise PermissionDenied("User is not active")

        # Check for circular dependency
        if depends_on == task_id:
            raise BusinessLogicError("Task cannot depend on itself")

        # task.parent_task_id = depends_on  # TODO: Implement via TaskDependency model
        task.updated_by = user.id
        task.updated_at = datetime.utcnow()

        db.commit()

        return {"task_id": task_id, "depends_on": depends_on, "status": "added"}

    def get_dependencies(self, task_id: int, user: User, db: Session) -> dict[str, Any]:
        """Get task dependencies."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFound("Task not found")

        if not user.is_active:
            raise PermissionDenied("User is not active")

        dependencies: List[Dict[str, Any]] = []
        # TODO: Implement proper dependency retrieval via TaskDependency model
        # if task.parent_task_id:
        #     dependencies.append({"id": task.parent_task_id, "type": "blocks"})

        return {
            "task_id": task_id,
            "dependencies": dependencies,
            "count": len(dependencies),
        }

    def remove_dependency(
        self, task_id: int, depends_on: int, user: User, db: Session
    ) -> bool:
        """Remove task dependency."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFound("Task not found")

        if not user.is_active:
            raise PermissionDenied("User is not active")

        # TODO: Implement proper dependency removal via TaskDependency model
        # if task.parent_task_id != depends_on:
        #     raise BusinessLogicError("Dependency does not exist")
        
        # task.parent_task_id = None
        task.updated_by = user.id
        task.updated_at = datetime.utcnow()

        db.commit()

        return True

    def bulk_update_status(
        self, bulk_data: BulkStatusUpdate, user: User, db: Session
    ) -> BulkUpdateResponse:
        """Update status for multiple tasks."""
        if not user.is_active:
            raise PermissionDenied("User is not active")

        updated_count = 0
        failed_count = 0
        errors = []

        for task_id in bulk_data.task_ids:
            try:
                task = db.query(Task).filter(Task.id == task_id).first()
                if task:
                    task.status = ModelTaskStatus(bulk_data.status.value)
                    if bulk_data.status.value == "completed":
                        task.completed_at = datetime.utcnow()
                    task.updated_by = user.id
                    task.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    failed_count += 1
                    errors.append({"task_id": task_id, "error": "Task not found"})
            except Exception as e:
                failed_count += 1
                errors.append({"task_id": task_id, "error": str(e)})

        db.commit()

        return BulkUpdateResponse(
            updated_count=updated_count,
            failed_count=failed_count,
            errors=errors if errors else None,
        )

    def search_tasks(
        self, query: str, user: User, db: Session, page: int = 1, page_size: int = 20
    ) -> TaskListResponse:
        """Search tasks by keyword."""
        from sqlalchemy import or_

        # Check search permissions
        if not user.is_active:
            raise PermissionDenied("User is not active")

        # Users can search tasks in organizations they belong to
        user_org_ids = [org.id for org in user.get_organizations()]
        if not user_org_ids and not user.is_superuser:
            raise PermissionDenied(
                "User must belong to at least one organization to search tasks"
            )

        # Search in title and description
        search_filter = or_(
            Task.title.ilike(f"%{query}%"), Task.description.ilike(f"%{query}%")
        )

        query_obj = (
            db.query(Task)
            .options(
                joinedload(Task.project),
                joinedload(Task.assignee),
                joinedload(Task.creator),
            )
            .filter(search_filter, Task.is_deleted.is_(False))
        )

        # Count total
        total = query_obj.count()

        # Apply pagination
        offset = (page - 1) * page_size
        tasks = query_obj.offset(offset).limit(page_size).all()

        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return TaskListResponse(
            items=[self._task_to_response(task) for task in tasks],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def _task_to_response(self, task: Task) -> TaskResponse:
        """Convert Task model to TaskResponse schema."""
        from app.schemas.task import (
            DepartmentBasic,
            ProjectInfo,
            TaskPriority,
            TaskStatus,
            UserInfo,
        )

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
            name=task.project.name if task.project else f"Project {task.project_id}",
        )

        # Build assignees list
        assignees = []
        if task.assignee:
            assignees.append(
                UserInfo(
                    id=task.assignee.id,
                    name=task.assignee.full_name,
                    email=task.assignee.email,
                )
            )

        # Build created_by info
        created_by = UserInfo(
            id=task.creator.id if task.creator else task.created_by,
            name=task.creator.full_name if task.creator else "Unknown",
            email=task.creator.email if task.creator else "unknown@example.com",
        )

        # Build department info if available
        department_info = None
        if task.department:
            department_info = DepartmentBasic(
                id=task.department.id,
                name=task.department.name,
                code=task.department.code,
            )

        return TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            project=project_info,
            parent_task_id=None,  # TODO: Implement via TaskDependency model
            status=status,
            priority=priority,
            due_date=task.due_date,
            estimated_hours=task.estimated_hours,
            actual_hours=task.actual_hours,
            assignees=assignees,
            tags=getattr(task, "tags", []) or [],
            created_at=task.created_at,
            updated_at=task.updated_at,
            created_by=created_by,
            # CRITICAL: Department integration fields
            department_id=task.department_id,
            department_visibility=task.department_visibility or "department_hierarchy",
            department=department_info,
        )

    # CRITICAL: Department Integration Methods for Phase 3

    def create_department_task(
        self, task_data: TaskCreate, user: User, db: Session, department_id: int
    ) -> TaskResponse:
        """Create a new task assigned to a department."""
        # Check if department exists
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise NotFound("Department not found")

        # Check if project exists and user has access
        project = db.query(Project).filter(Project.id == task_data.project_id).first()
        if not project:
            raise NotFound("Project not found")

        # Basic permission check - can be enhanced with department-specific permissions
        if not user.is_active:
            raise PermissionDenied("User is not active")

        # Create task with department assignment
        task = Task(
            title=task_data.title,
            description=task_data.description,
            status="not_started",
            priority=task_data.priority.value,
            project_id=task_data.project_id,
            assignee_id=task_data.assignee_ids[0] if task_data.assignee_ids else None,
            reporter_id=user.id,
            # parent_task_id=task_data.parent_task_id,  # TODO: Implement via TaskDependency
            due_date=task_data.due_date,
            start_date=None,
            estimated_hours=task_data.estimated_hours,
            created_by=user.id,
            # CRITICAL: Department integration
            department_id=department_id,
            department_visibility="department_hierarchy",
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        return self._task_to_response(task)

    def get_department_tasks(
        self,
        department_id: int,
        user: User,
        db: Session,
        include_subdepartments: bool = True,
        status_filter: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> TaskListResponse:
        """Get tasks for a department with hierarchical support."""
        # Check if department exists
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise NotFound("Department not found")

        # Basic permission check
        if not user.is_active:
            raise PermissionDenied("User is not active")

        # Build query for department tasks
        query = db.query(Task).options(
            joinedload(Task.project),
            joinedload(Task.assignee),
            joinedload(Task.creator),
            joinedload(Task.department),
        )

        if include_subdepartments:
            # Get all subdepartments using materialized path
            subdept_query = db.query(Department).filter(
                Department.path.like(f"{department.path}%")
            )
            department_ids = [dept.id for dept in subdept_query.all()]
        else:
            department_ids = [department_id]

        # Filter by department IDs
        query = query.filter(Task.department_id.in_(department_ids))

        # Apply status filter if provided
        if status_filter:
            query = query.filter(Task.status == status_filter)

        # Only show active tasks
        query = query.filter(Task.is_deleted.is_(False))

        # Count total
        total = query.count()

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

    def assign_task_to_department(
        self, task_id: int, department_id: int, user: User, db: Session
    ) -> TaskResponse:
        """Assign an existing task to a department."""
        # Get task
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFound("Task not found")

        # Check if department exists
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise NotFound("Department not found")

        # Basic permission check
        if not user.is_active:
            raise PermissionDenied("User is not active")

        # Update task with department assignment
        task.department_id = department_id
        task.department_visibility = "department_hierarchy"
        task.updated_by = user.id
        task.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(task)

        return self._task_to_response(task)

    def get_tasks_by_visibility(
        self,
        user: User,
        db: Session,
        visibility_scope: str = "department_hierarchy",
        page: int = 1,
        page_size: int = 20,
    ) -> TaskListResponse:
        """Get tasks based on visibility scope and user's department context."""
        if not user.is_active:
            raise PermissionDenied("User is not active")

        query = db.query(Task).options(
            joinedload(Task.project),
            joinedload(Task.assignee),
            joinedload(Task.creator),
            joinedload(Task.department),
        )

        # Filter by visibility scope
        query = query.filter(Task.department_visibility == visibility_scope)

        # Only show active tasks
        query = query.filter(Task.is_deleted.is_(False))

        # Count total
        total = query.count()

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
