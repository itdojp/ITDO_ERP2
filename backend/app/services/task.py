"""Task management service."""

from typing import List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import BusinessLogicError, NotFound, PermissionDenied
from app.models.task import Task
from app.models.project import Project
from app.models.user import User
from app.schemas.task import (
    TaskCreateRequest,
    TaskUpdateRequest,
    TaskResponse,
    TaskListResponse,
    TaskSearchParams,
)
from app.services.audit import AuditLogger


class TaskService:
    """Task management service class."""

    def create_task(
        self, data: TaskCreateRequest, creator: User, db: Session
    ) -> Task:
        """Create a new task with permission checks."""
        # Validate project exists and check permissions
        project = db.query(Project).filter(
            Project.id == data.project_id,
            Project.deleted_at.is_(None)
        ).first()
        
        if not project:
            raise NotFound("指定されたプロジェクトが見つかりません")

        # Check permissions
        if not self._can_access_project(creator, project):
            raise PermissionDenied("このプロジェクトへのアクセス権限がありません")

        # Create task
        task = Task.create(
            db,
            title=data.title,
            description=data.description,
            status=data.status or "not_started",
            priority=data.priority or "medium",
            project_id=data.project_id,
            assigned_to=data.assigned_to,
            estimated_start_date=data.estimated_start_date,
            estimated_end_date=data.estimated_end_date,
            created_by=creator.id,
        )

        db.flush()

        # Log audit
        self._log_audit(
            "create",
            "task",
            task.id,
            creator,
            {
                "title": task.title,
                "project_id": data.project_id,
                "assigned_to": data.assigned_to,
            },
            db,
        )

        return task

    def get_task(
        self, task_id: int, viewer: User, db: Session
    ) -> TaskResponse:
        """Get task details with permission check."""
        task = db.query(Task).options(
            joinedload(Task.project),
            joinedload(Task.assignee),
        ).filter(
            Task.id == task_id,
            Task.deleted_at.is_(None)
        ).first()
        
        if not task:
            raise NotFound("タスクが見つかりません")

        # Permission check
        if not self._can_access_project(viewer, task.project):
            raise PermissionDenied("このタスクへのアクセス権限がありません")

        return self._task_to_response(task)

    def search_tasks_by_project(
        self, project_id: int, params: TaskSearchParams, searcher: User, db: Session
    ) -> TaskListResponse:
        """Search tasks by project with filters."""
        # Validate project exists and check permissions
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.deleted_at.is_(None)
        ).first()
        
        if not project:
            raise NotFound("指定されたプロジェクトが見つかりません")

        if not self._can_access_project(searcher, project):
            raise PermissionDenied("このプロジェクトへのアクセス権限がありません")

        query = db.query(Task).options(
            joinedload(Task.assignee),
        ).filter(
            Task.project_id == project_id,
            Task.deleted_at.is_(None)
        )

        # Apply filters
        if params.search:
            search_term = f"%{params.search}%"
            query = query.filter(
                or_(
                    Task.title.ilike(search_term),
                    Task.description.ilike(search_term),
                )
            )

        if params.status:
            query = query.filter(Task.status == params.status)

        if params.priority:
            query = query.filter(Task.priority == params.priority)

        if params.assigned_to:
            query = query.filter(Task.assigned_to == params.assigned_to)

        # Count total
        total = query.count()

        # Default pagination
        page = params.page or 1
        limit = params.limit or 20
        offset = (page - 1) * limit

        # Execute query
        tasks = query.offset(offset).limit(limit).all()

        return TaskListResponse(
            items=[self._task_to_response(t) for t in tasks],
            total=total,
            page=page,
            limit=limit,
        )

    def update_task(
        self, task_id: int, data: TaskUpdateRequest, updater: User, db: Session
    ) -> Task:
        """Update task information."""
        task = db.query(Task).options(
            joinedload(Task.project),
        ).filter(
            Task.id == task_id,
            Task.deleted_at.is_(None)
        ).first()
        
        if not task:
            raise NotFound("タスクが見つかりません")

        # Permission check
        if not self._can_edit_task(updater, task):
            raise PermissionDenied("このタスクを更新する権限がありません")

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        task.update(db, updated_by=updater.id, **update_data)

        # Log audit
        self._log_audit("update", "task", task.id, updater, update_data, db)

        return task

    def assign_task(
        self, task_id: int, assignee_id: int, assigner: User, db: Session
    ) -> Task:
        """Assign task to user."""
        task = db.query(Task).options(
            joinedload(Task.project),
        ).filter(
            Task.id == task_id,
            Task.deleted_at.is_(None)
        ).first()
        
        if not task:
            raise NotFound("タスクが見つかりません")

        # Permission check
        if not self._can_edit_task(assigner, task):
            raise PermissionDenied("このタスクを割り当てる権限がありません")

        # Validate assignee exists and has access to project
        assignee = db.query(User).filter(User.id == assignee_id).first()
        if not assignee:
            raise NotFound("指定されたユーザーが見つかりません")

        if not self._can_access_project(assignee, task.project):
            raise PermissionDenied("担当者はこのプロジェクトにアクセスできません")

        # Update assignment
        task.assigned_to = assignee_id
        task.updated_by = assigner.id
        db.add(task)

        # Log audit
        self._log_audit(
            "assign",
            "task",
            task.id,
            assigner,
            {"assigned_to": assignee_id},
            db,
        )

        return task

    def delete_task(
        self, task_id: int, deleter: User, db: Session
    ) -> None:
        """Delete task (soft delete)."""
        task = db.query(Task).options(
            joinedload(Task.project),
        ).filter(
            Task.id == task_id,
            Task.deleted_at.is_(None)
        ).first()
        
        if not task:
            raise NotFound("タスクが見つかりません")

        # Permission check
        if not self._can_edit_task(deleter, task):
            raise PermissionDenied("このタスクを削除する権限がありません")

        # Soft delete
        task.soft_delete(db, deleter.id)

        # Log audit
        self._log_audit("delete", "task", task.id, deleter, {}, db)

    def _can_access_project(self, user: User, project: Project) -> bool:
        """Check if user can access project."""
        if user.is_superuser:
            return True

        # User must be in the same organization
        user_org_ids = [o.id for o in user.get_organizations()]
        return project.organization_id in user_org_ids

    def _can_edit_task(self, user: User, task: Task) -> bool:
        """Check if user can edit task."""
        if user.is_superuser:
            return True

        # Task creator can edit
        if task.created_by == user.id:
            return True

        # Task assignee can edit
        if task.assigned_to == user.id:
            return True

        # Project admin can edit
        return any(
            r.code in ["PROJECT_ADMIN", "ORG_ADMIN"]
            for r in user.get_roles_in_organization(task.project.organization_id)
        )

    def _task_to_response(self, task: Task) -> TaskResponse:
        """Convert task to response schema."""
        return TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            project_id=task.project_id,
            assigned_to=task.assigned_to,
            estimated_start_date=task.estimated_start_date,
            estimated_end_date=task.estimated_end_date,
            actual_start_date=task.actual_start_date,
            actual_end_date=task.actual_end_date,
            created_at=task.created_at,
            updated_at=task.updated_at,
            created_by=task.created_by,
            updated_by=task.updated_by,
        )

    def _log_audit(
        self,
        action: str,
        resource_type: str,
        resource_id: int,
        user: User,
        changes: dict,
        db: Session,
    ) -> None:
        """Log audit trail."""
        AuditLogger.log(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user=user,
            changes=changes,
            db=db,
        )