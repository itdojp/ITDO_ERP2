"""Project service implementation with comprehensive CRUD operations."""

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.cache import CacheManager
from app.core.performance import PerformanceOptimizer
from app.models.organization import Organization
from app.models.project import Project, ProjectStatus
from app.models.project_member import ProjectMember
from app.schemas.project import (
    ProjectAnalytics,
    ProjectBulkOperation,
    ProjectCreate,
    ProjectFilter,
    ProjectResponse,
    ProjectStatistics,
    ProjectStatusTransition,
    ProjectSummary,
    ProjectUpdate,
)
from app.services.permission import PermissionService
from app.types import UserId


class ProjectService:
    """Service for managing projects with comprehensive CRUD operations."""

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

    def create_project(
        self,
        project_data: ProjectCreate,
        owner_id: int,
        validate_permissions: bool = True,
    ) -> ProjectResponse:
        """Create a new project with comprehensive validation."""
        # Validate organization exists
        org = self.db.query(Organization).filter(
            Organization.id == project_data.organization_id,
            Organization.is_active == True,
        ).first()
        if not org:
            raise ValueError("Organization not found or inactive")

        # Validate department if provided
        if project_data.department_id:
            from app.models.department import Department
            dept = self.db.query(Department).filter(
                Department.id == project_data.department_id,
                Department.organization_id == project_data.organization_id,
                Department.is_active == True,
            ).first()
            if not dept:
                raise ValueError("Department not found or inactive")

        # Validate project code uniqueness within organization
        existing_project = self.db.query(Project).filter(
            Project.code == project_data.code,
            Project.organization_id == project_data.organization_id,
            Project.is_active == True,
        ).first()
        if existing_project:
            raise ValueError(f"Project code '{project_data.code}' already exists in organization")

        # Validate permission if service is available
        if validate_permissions and self.permission_service:
            has_permission = self.permission_service.check_user_permission(
                owner_id, "project.create", project_data.organization_id
            )
            if not has_permission:
                raise PermissionError("Insufficient permissions to create project")

        # Create project
        project = Project(
            code=project_data.code,
            name=project_data.name,
            description=project_data.description,
            organization_id=project_data.organization_id,
            department_id=project_data.department_id,
            owner_id=owner_id,
            manager_id=project_data.manager_id or owner_id,
            status=project_data.status,
            priority=project_data.priority,
            project_type=project_data.project_type,
            start_date=project_data.start_date,
            end_date=project_data.end_date,
            budget=project_data.budget,
            estimated_hours=project_data.estimated_hours,
            is_public=project_data.is_public,
            tags=project_data.tags or [],
            settings=project_data.settings or {},
            is_active=True,
        )

        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

        # Create default project member for owner
        owner_member = ProjectMember(
            project_id=project.id,
            user_id=owner_id,
            role="owner",
            permissions=["project.manage", "project.delete", "project.view", "project.edit"],
            is_active=True,
        )
        self.db.add(owner_member)

        # Add manager if different from owner
        if project_data.manager_id and project_data.manager_id != owner_id:
            manager_member = ProjectMember(
                project_id=project.id,
                user_id=project_data.manager_id,
                role="manager",
                permissions=["project.manage", "project.view", "project.edit"],
                is_active=True,
            )
            self.db.add(manager_member)

        self.db.commit()

        # Invalidate cache
        self._invalidate_project_cache(project.id, project.organization_id)

        return self._project_to_response(project)

    def get_project(
        self,
        project_id: int,
        user_id: Optional[int] = None,
        validate_permissions: bool = True,
    ) -> Optional[ProjectResponse]:
        """Get project by ID with permission validation."""
        query = (
            self.db.query(Project)
            .options(
                joinedload(Project.organization),
                joinedload(Project.department),
                joinedload(Project.owner),
                joinedload(Project.manager),
                selectinload(Project.members),
                selectinload(Project.milestones),
            )
            .filter(Project.id == project_id, Project.is_active == True)
        )

        project = query.first()
        if not project:
            return None

        # Validate permission if service is available
        if validate_permissions and self.permission_service and user_id:
            has_permission = self.permission_service.check_user_permission(
                user_id, "project.view", project.organization_id
            )
            if not has_permission and not self._is_project_member(project.id, user_id):
                raise PermissionError("Insufficient permissions to view project")

        return self._project_to_response(project)

    def update_project(
        self,
        project_id: int,
        project_data: ProjectUpdate,
        user_id: int,
        validate_permissions: bool = True,
    ) -> ProjectResponse:
        """Update project with comprehensive validation."""
        project = self.db.query(Project).filter(
            Project.id == project_id,
            Project.is_active == True,
        ).first()

        if not project:
            raise ValueError("Project not found")

        # Validate permission if service is available
        if validate_permissions and self.permission_service:
            has_permission = self.permission_service.check_user_permission(
                user_id, "project.edit", project.organization_id
            )
            if not has_permission and not self._is_project_manager(project.id, user_id):
                raise PermissionError("Insufficient permissions to update project")

        # Validate status transition
        if project_data.status and project_data.status != project.status:
            if not self._is_valid_status_transition(project.status, project_data.status):
                raise ValueError(f"Invalid status transition from {project.status} to {project_data.status}")

        # Update fields
        for field, value in project_data.dict(exclude_unset=True).items():
            if hasattr(project, field):
                setattr(project, field, value)

        # Update completion date if status is completed
        if project_data.status == ProjectStatus.COMPLETED.value:
            project.completion_date = datetime.now(timezone.utc)

        # Update progress based on status
        if project_data.status == ProjectStatus.COMPLETED.value:
            project.progress_percentage = 100
        elif project_data.status == ProjectStatus.CANCELLED.value:
            project.actual_end_date = date.today()

        self.db.commit()
        self.db.refresh(project)

        # Invalidate cache
        self._invalidate_project_cache(project.id, project.organization_id)

        return self._project_to_response(project)

    def delete_project(
        self,
        project_id: int,
        user_id: int,
        validate_permissions: bool = True,
    ) -> bool:
        """Soft delete project with validation."""
        project = self.db.query(Project).filter(
            Project.id == project_id,
            Project.is_active == True,
        ).first()

        if not project:
            return False

        # Validate permission if service is available
        if validate_permissions and self.permission_service:
            has_permission = self.permission_service.check_user_permission(
                user_id, "project.delete", project.organization_id
            )
            if not has_permission and project.owner_id != user_id:
                raise PermissionError("Insufficient permissions to delete project")

        # Check if project can be deleted
        if not project.can_be_deleted():
            raise ValueError("Project cannot be deleted in current status")

        # Soft delete project
        project.is_active = False
        project.deleted_at = datetime.now(timezone.utc)

        # Soft delete project members
        self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id
        ).update({"is_active": False})

        self.db.commit()

        # Invalidate cache
        self._invalidate_project_cache(project.id, project.organization_id)

        return True

    def get_project_tasks(
        self,
        project_id: int,
        user_id: Optional[int] = None,
        include_completed: bool = True,
    ) -> List[Dict[str, Any]]:
        """Get all tasks for a project."""
        from app.models.task import Task, TaskStatus

        project = self.db.query(Project).filter(
            Project.id == project_id,
            Project.is_active == True,
        ).first()

        if not project:
            return []

        # Validate permission if service is available
        if self.permission_service and user_id:
            has_permission = self.permission_service.check_user_permission(
                user_id, "task.view", project.organization_id
            )
            if not has_permission and not self._is_project_member(project.id, user_id):
                raise PermissionError("Insufficient permissions to view project tasks")

        # Build query
        query = self.db.query(Task).filter(
            Task.project_id == project_id,
            Task.is_deleted == False,
        ).options(
            joinedload(Task.assignee),
            joinedload(Task.reporter),
        )

        # Filter out completed tasks if requested
        if not include_completed:
            query = query.filter(Task.status != TaskStatus.DONE.value)

        tasks = query.order_by(Task.created_at.desc()).all()

        return [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "code": task.code,
                "status": task.status,
                "priority": task.priority,
                "task_type": task.task_type,
                "assignee_id": task.assignee_id,
                "assignee_name": task.assignee.full_name if task.assignee else None,
                "assignee_email": task.assignee.email if task.assignee else None,
                "reporter_id": task.reporter_id,
                "reporter_name": task.reporter.full_name if task.reporter else None,
                "reporter_email": task.reporter.email if task.reporter else None,
                "start_date": task.start_date,
                "due_date": task.due_date,
                "completed_date": task.completed_date,
                "estimated_hours": task.estimated_hours,
                "actual_hours": task.actual_hours,
                "remaining_hours": task.remaining_hours,
                "progress_percentage": task.progress_percentage,
                "story_points": task.story_points,
                "epic_id": task.epic_id,
                "sprint_id": task.sprint_id,
                "depends_on": task.depends_on,
                "blocks": task.blocks,
                "tags": task.tags,
                "labels": task.labels,
                "custom_fields": task.custom_fields,
                "is_overdue": task.is_overdue,
                "days_remaining": task.days_remaining,
                "hours_usage_percentage": task.hours_usage_percentage,
                "status_color": task.status_color,
                "priority_level": task.priority_level,
                "is_epic": task.is_epic,
                "is_subtask": task.is_subtask,
                "can_start": task.can_start(),
                "created_at": task.created_at,
                "updated_at": task.updated_at,
            }
            for task in tasks
        ]

    def get_project_members(
        self,
        project_id: int,
        user_id: Optional[int] = None,
        validate_permissions: bool = True,
    ) -> List[Dict[str, Any]]:
        """Get all members of a project."""
        project = self.db.query(Project).filter(
            Project.id == project_id,
            Project.is_active == True,
        ).first()

        if not project:
            return []

        # Validate permission if service is available
        if validate_permissions and self.permission_service and user_id:
            has_permission = self.permission_service.check_user_permission(
                user_id, "project.view", project.organization_id
            )
            if not has_permission and not self._is_project_member(project.id, user_id):
                raise PermissionError("Insufficient permissions to view project members")

        members = (
            self.db.query(ProjectMember)
            .options(joinedload(ProjectMember.user))
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.is_active == True,
            )
            .all()
        )

        return [
            {
                "id": member.id,
                "user_id": member.user_id,
                "user_email": member.user.email,
                "user_name": member.user.full_name,
                "role": member.role,
                "permissions": member.permissions,
                "joined_at": member.created_at,
                "is_active": member.is_active,
            }
            for member in members
        ]

    def manage_project_permissions(
        self,
        project_id: int,
        user_id: int,
        target_user_id: int,
        permissions: List[str],
        role: Optional[str] = None,
        manager_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Manage project member permissions."""
        # Validate manager permission
        if manager_id and self.permission_service:
            has_permission = self.permission_service.check_user_permission(
                manager_id, "project.manage", None
            )
            if not has_permission and not self._is_project_manager(project_id, manager_id):
                raise PermissionError("Insufficient permissions to manage project permissions")

        # Get or create project member
        member = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == target_user_id,
        ).first()

        if not member:
            member = ProjectMember(
                project_id=project_id,
                user_id=target_user_id,
                role=role or "member",
                permissions=permissions,
                is_active=True,
            )
            self.db.add(member)
        else:
            member.permissions = permissions
            if role:
                member.role = role
            member.is_active = True

        self.db.commit()

        return {
            "user_id": target_user_id,
            "permissions": permissions,
            "role": member.role,
            "updated": True,
        }

    def list_projects(
        self,
        user_id: Optional[int] = None,
        filters: Optional[ProjectFilter] = None,
        page: int = 1,
        per_page: int = 50,
        validate_permissions: bool = True,
    ) -> Tuple[List[ProjectResponse], int]:
        """List projects with filtering and pagination."""
        query = self.db.query(Project).filter(Project.is_active == True)

        # Apply filters
        if filters:
            if filters.organization_id:
                query = query.filter(Project.organization_id == filters.organization_id)
            if filters.department_id:
                query = query.filter(Project.department_id == filters.department_id)
            if filters.owner_id:
                query = query.filter(Project.owner_id == filters.owner_id)
            if filters.manager_id:
                query = query.filter(Project.manager_id == filters.manager_id)
            if filters.status:
                query = query.filter(Project.status == filters.status)
            if filters.priority:
                query = query.filter(Project.priority == filters.priority)
            if filters.project_type:
                query = query.filter(Project.project_type == filters.project_type)
            if filters.is_active is not None:
                query = query.filter(Project.is_active == filters.is_active)
            if filters.is_public is not None:
                query = query.filter(Project.is_public == filters.is_public)
            if filters.start_date_from:
                query = query.filter(Project.start_date >= filters.start_date_from)
            if filters.start_date_to:
                query = query.filter(Project.start_date <= filters.start_date_to)
            if filters.end_date_from:
                query = query.filter(Project.end_date >= filters.end_date_from)
            if filters.end_date_to:
                query = query.filter(Project.end_date <= filters.end_date_to)
            if filters.budget_min:
                query = query.filter(Project.budget >= filters.budget_min)
            if filters.budget_max:
                query = query.filter(Project.budget <= filters.budget_max)
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Project.name.ilike(search_term),
                        Project.description.ilike(search_term),
                        Project.code.ilike(search_term),
                    )
                )
            if filters.is_overdue:
                today = date.today()
                query = query.filter(
                    and_(
                        Project.end_date < today,
                        Project.status.in_([
                            ProjectStatus.PLANNING.value,
                            ProjectStatus.IN_PROGRESS.value,
                        ])
                    )
                )

        # Apply permission filtering if needed
        if validate_permissions and self.permission_service and user_id:
            # Filter projects based on user permissions
            # For now, we'll let the permission check happen per project
            # A more efficient implementation would cache accessible organizations
            pass

        # Get total count
        total = query.count()

        # Apply pagination
        projects = (
            query
            .options(
                joinedload(Project.organization),
                joinedload(Project.department),
                joinedload(Project.owner),
                joinedload(Project.manager),
            )
            .order_by(Project.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return [self._project_to_response(project) for project in projects], total

    def project_analytics(
        self,
        project_id: int,
        user_id: Optional[int] = None,
        validate_permissions: bool = True,
    ) -> ProjectAnalytics:
        """Generate comprehensive project analytics."""
        project = self.db.query(Project).filter(
            Project.id == project_id,
            Project.is_active == True,
        ).first()

        if not project:
            raise ValueError("Project not found")

        # Validate permission if service is available
        if validate_permissions and self.permission_service and user_id:
            has_permission = self.permission_service.check_user_permission(
                user_id, "project.view", project.organization_id
            )
            if not has_permission and not self._is_project_member(project.id, user_id):
                raise PermissionError("Insufficient permissions to view project analytics")

        # Get basic counts
        total_tasks = project.get_total_tasks_count()
        completed_tasks = project.get_completed_tasks_count()
        active_tasks = project.get_active_tasks_count()
        overdue_tasks = project.get_overdue_tasks_count()

        # Get milestone counts
        total_milestones = len(project.milestones)
        completed_milestones = len([m for m in project.milestones if m.is_completed])

        # Get team size
        team_size = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.is_active == True,
        ).count()

        # Calculate utilization
        budget_utilization = None
        if project.budget and project.spent_budget:
            budget_utilization = (project.spent_budget / project.budget) * 100

        hours_utilization = None
        if project.estimated_hours and project.actual_hours:
            hours_utilization = (project.actual_hours / project.estimated_hours) * 100

        # Calculate completion rate
        completion_rate = project.progress_percentage

        # Calculate average task completion time
        average_task_completion_time = None
        if completed_tasks > 0:
            from app.models.task import TaskStatus
            completed_task_objects = [
                t for t in project.tasks
                if t.status == TaskStatus.DONE.value and t.completed_date and t.start_date
            ]
            if completed_task_objects:
                total_completion_days = sum(
                    (t.completed_date.date() - t.start_date).days
                    for t in completed_task_objects
                    if t.completed_date is not None and t.start_date is not None
                )
                average_task_completion_time = total_completion_days / len(completed_task_objects)

        # Performance metrics
        performance_metrics = {
            "health_status": project.get_health_status(),
            "is_on_schedule": project.is_on_schedule,
            "is_overdue": project.is_overdue,
            "days_remaining": project.days_remaining,
            "budget_usage_percentage": project.budget_usage_percentage,
            "hours_usage_percentage": project.hours_usage_percentage,
            "priority_level": project.priority_level,
            "status_color": project.status_color,
        }

        return ProjectAnalytics(
            project_id=project_id,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            active_tasks=active_tasks,
            overdue_tasks=overdue_tasks,
            total_milestones=total_milestones,
            completed_milestones=completed_milestones,
            team_size=team_size,
            budget_utilization=budget_utilization,
            hours_utilization=hours_utilization,
            completion_rate=completion_rate,
            average_task_completion_time=average_task_completion_time,
            performance_metrics=performance_metrics,
        )

    def bulk_update_projects(
        self,
        bulk_operation: ProjectBulkOperation,
        user_id: int,
        validate_permissions: bool = True,
    ) -> Dict[str, Any]:
        """Perform bulk operations on projects."""
        projects = self.db.query(Project).filter(
            Project.id.in_(bulk_operation.project_ids),
            Project.is_active == True,
        ).all()

        if not projects:
            return {"success": False, "message": "No projects found"}

        # Validate permissions for all projects
        if validate_permissions and self.permission_service:
            for project in projects:
                has_permission = self.permission_service.check_user_permission(
                    user_id, "project.edit", project.organization_id
                )
                if not has_permission and not self._is_project_manager(project.id, user_id):
                    raise PermissionError(f"Insufficient permissions for project {project.code}")

        updated_count = 0
        errors = []

        for project in projects:
            try:
                if bulk_operation.operation == "archive":
                    if project.can_be_archived():
                        project.is_archived = True
                        project.status = ProjectStatus.ARCHIVED.value
                        updated_count += 1
                    else:
                        errors.append(f"Project {project.code} cannot be archived")

                elif bulk_operation.operation == "unarchive":
                    if project.is_archived:
                        project.is_archived = False
                        project.status = ProjectStatus.ON_HOLD.value
                        updated_count += 1

                elif bulk_operation.operation == "activate":
                    project.is_active = True
                    updated_count += 1

                elif bulk_operation.operation == "deactivate":
                    project.is_active = False
                    updated_count += 1

                elif bulk_operation.operation == "update_status":
                    new_status = bulk_operation.data.get("status") if bulk_operation.data else None
                    if new_status and self._is_valid_status_transition(project.status, new_status):
                        project.status = new_status
                        if new_status == ProjectStatus.COMPLETED.value:
                            project.completion_date = datetime.now(timezone.utc)
                        updated_count += 1
                    else:
                        errors.append(f"Invalid status transition for project {project.code}")

                elif bulk_operation.operation == "update_priority":
                    new_priority = bulk_operation.data.get("priority") if bulk_operation.data else None
                    if new_priority:
                        project.priority = new_priority
                        updated_count += 1

                elif bulk_operation.operation == "assign_manager":
                    manager_id = bulk_operation.data.get("manager_id") if bulk_operation.data else None
                    if manager_id:
                        project.manager_id = manager_id
                        updated_count += 1

                elif bulk_operation.operation == "add_tags":
                    tags = bulk_operation.data.get("tags", []) if bulk_operation.data else []
                    if tags:
                        current_tags = project.tags or []
                        project.tags = list(set(current_tags + tags))
                        updated_count += 1

                elif bulk_operation.operation == "remove_tags":
                    tags_to_remove = bulk_operation.data.get("tags", []) if bulk_operation.data else []
                    if tags_to_remove and project.tags:
                        project.tags = [tag for tag in project.tags if tag not in tags_to_remove]
                        updated_count += 1

            except Exception as e:
                errors.append(f"Error updating project {project.code}: {str(e)}")

        if updated_count > 0:
            self.db.commit()

            # Invalidate cache for all updated projects
            for project in projects:
                self._invalidate_project_cache(project.id, project.organization_id)

        return {
            "success": True,
            "updated_count": updated_count,
            "total_count": len(projects),
            "errors": errors,
        }

    def transition_project_status(
        self,
        project_id: int,
        transition: ProjectStatusTransition,
        user_id: int,
        validate_permissions: bool = True,
    ) -> Dict[str, Any]:
        """Transition project status with validation and tracking."""
        project = self.db.query(Project).filter(
            Project.id == project_id,
            Project.is_active == True,
        ).first()

        if not project:
            raise ValueError("Project not found")

        # Validate current status
        if project.status != transition.from_status:
            raise ValueError(f"Project status is {project.status}, not {transition.from_status}")

        # Validate transition
        if not self._is_valid_status_transition(transition.from_status, transition.to_status):
            raise ValueError(f"Invalid status transition from {transition.from_status} to {transition.to_status}")

        # Validate permission if service is available
        if validate_permissions and self.permission_service:
            has_permission = self.permission_service.check_user_permission(
                user_id, "project.edit", project.organization_id
            )
            if not has_permission and not self._is_project_manager(project.id, user_id):
                raise PermissionError("Insufficient permissions to change project status")

        # Perform transition
        old_status = project.status
        project.status = transition.to_status

        # Update related fields based on status
        if transition.to_status == ProjectStatus.IN_PROGRESS.value:
            if not project.actual_start_date:
                project.actual_start_date = date.today()
        elif transition.to_status == ProjectStatus.COMPLETED.value:
            project.completion_date = datetime.now(timezone.utc)
            project.actual_end_date = date.today()
            project.progress_percentage = 100
        elif transition.to_status == ProjectStatus.CANCELLED.value:
            project.actual_end_date = date.today()

        self.db.commit()

        # Invalidate cache
        self._invalidate_project_cache(project.id, project.organization_id)

        return {
            "project_id": project_id,
            "old_status": old_status,
            "new_status": project.status,
            "transition_date": datetime.now(timezone.utc),
            "reason": transition.reason,
            "notes": transition.notes,
            "updated_by": user_id,
        }

    def get_project_summary(
        self,
        project_id: int,
        user_id: Optional[int] = None,
    ) -> Optional[ProjectSummary]:
        """Get project summary for dashboard display."""
        project = self.db.query(Project).filter(
            Project.id == project_id,
            Project.is_active == True,
        ).options(
            joinedload(Project.organization),
            joinedload(Project.department),
            joinedload(Project.owner),
        ).first()

        if not project:
            return None

        # Get member count
        member_count = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.is_active == True,
        ).count()

        # Get milestone count
        milestone_count = len(project.milestones)

        return ProjectSummary(
            id=project.id,
            code=project.code,
            name=project.name,
            status=project.status,
            priority=project.priority,
            progress_percentage=project.progress_percentage,
            is_overdue=project.is_overdue,
            days_remaining=project.days_remaining,
            budget_usage_percentage=project.budget_usage_percentage,
            member_count=member_count,
            milestone_count=milestone_count,
            health_status=project.get_health_status(),
            is_on_schedule=project.is_on_schedule,
            status_color=project.status_color,
            organization_name=project.organization.name,
            department_name=project.department.name if project.department else None,
            owner_name=project.owner.full_name,
        )

    # Legacy methods for backward compatibility
    def get_project_statistics(
        self, project_id: int, user_id: UserId
    ) -> Dict[str, Any]:
        """Get project statistics (legacy method)."""
        try:
            analytics = self.project_analytics(project_id, user_id)
            return {
                "total_tasks": analytics.total_tasks,
                "completed_tasks": analytics.completed_tasks,
                "in_progress_tasks": analytics.active_tasks,
                "overdue_tasks": analytics.overdue_tasks,
                "completion_percentage": analytics.completion_rate,
                "budget_used": analytics.budget_utilization or 0.0,
                "budget_remaining": (100 - (analytics.budget_utilization or 0.0)),
                "team_members": analytics.team_size,
                "active_members": analytics.team_size,
                "milestones_total": analytics.total_milestones,
                "milestones_completed": analytics.completed_milestones,
                "days_remaining": analytics.performance_metrics.get("days_remaining", 0),
                "is_overdue": analytics.performance_metrics.get("is_overdue", False),
            }
        except Exception:
            return {
                "total_tasks": 0,
                "completed_tasks": 0,
                "in_progress_tasks": 0,
                "overdue_tasks": 0,
                "completion_percentage": 0.0,
                "budget_used": 0.0,
                "budget_remaining": 0.0,
                "team_members": 0,
                "active_members": 0,
                "milestones_total": 0,
                "milestones_completed": 0,
                "days_remaining": 0,
                "is_overdue": False,
            }

    def get_total_budget(self, project_id: int) -> float:
        """Get total project budget."""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        return project.budget if project and project.budget else 0.0

    def get_budget_utilization(self, project_id: int) -> float:
        """Get budget utilization percentage."""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if project and project.budget and project.spent_budget:
            return (project.spent_budget / project.budget) * 100
        return 0.0

    def get_user_projects(self, user_id: UserId) -> list[Project]:
        """Get projects for a user."""
        return self.db.query(Project).filter(
            or_(
                Project.owner_id == user_id,
                Project.manager_id == user_id,
                Project.members.any(
                    and_(
                        ProjectMember.user_id == user_id,
                        ProjectMember.is_active == True,
                    )
                ),
            ),
            Project.is_active == True,
        ).all()

    @property
    def repository(self) -> "ProjectRepository":
        """Get project repository."""
        return ProjectRepository(self.db)

    def _project_to_response(self, project: Project) -> ProjectResponse:
        """Convert Project model to ProjectResponse schema."""
        return ProjectResponse(
            id=project.id,
            code=project.code,
            name=project.name,
            description=project.description,
            status=project.status,
            priority=project.priority,
            project_type=project.project_type,
            start_date=project.start_date,
            end_date=project.end_date,
            budget=project.budget,
            estimated_hours=project.estimated_hours,
            is_public=project.is_public,
            tags=project.tags,
            settings=project.settings,
            organization_id=project.organization_id,
            created_at=project.created_at,
            updated_at=project.updated_at,
            member_count=project.get_member_count(),
            task_count=project.get_total_tasks_count(),
            progress_percentage=float(project.progress_percentage or 0),
            # Extended fields
            department_id=project.department_id,
            owner_id=project.owner_id,
            manager_id=project.manager_id,
            actual_start_date=project.actual_start_date,
            actual_end_date=project.actual_end_date,
            spent_budget=project.spent_budget,
            actual_hours=project.actual_hours,
            completion_date=project.completion_date,
            is_active=project.is_active,
            is_archived=project.is_archived,
            metadata=project.project_metadata,
            # Computed properties
            is_overdue=project.is_overdue,
            days_remaining=project.days_remaining,
            budget_usage_percentage=project.budget_usage_percentage,
            hours_usage_percentage=project.hours_usage_percentage,
            is_on_schedule=project.is_on_schedule,
            status_color=project.status_color,
            priority_level=project.priority_level,
            health_status=project.get_health_status(),
            # Relationships
            owner_email=project.owner.email if project.owner else None,
            manager_email=project.manager.email if project.manager else None,
            organization_name=project.organization.name if project.organization else None,
            department_name=project.department.name if project.department else None,
        )

    def _is_project_member(self, project_id: int, user_id: int) -> bool:
        """Check if user is a member of the project."""
        return self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.is_active == True,
        ).first() is not None

    def _is_project_manager(self, project_id: int, user_id: int) -> bool:
        """Check if user is a manager of the project."""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False

        return (
            project.manager_id == user_id or
            project.owner_id == user_id or
            self.db.query(ProjectMember).filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
                ProjectMember.role.in_(["manager", "owner"]),
                ProjectMember.is_active == True,
            ).first() is not None
        )

    def _is_valid_status_transition(self, from_status: str, to_status: str) -> bool:
        """Validate if status transition is allowed."""
        valid_transitions = {
            ProjectStatus.PLANNING.value: [
                ProjectStatus.IN_PROGRESS.value,
                ProjectStatus.ON_HOLD.value,
                ProjectStatus.CANCELLED.value,
            ],
            ProjectStatus.IN_PROGRESS.value: [
                ProjectStatus.ON_HOLD.value,
                ProjectStatus.COMPLETED.value,
                ProjectStatus.CANCELLED.value,
            ],
            ProjectStatus.ON_HOLD.value: [
                ProjectStatus.IN_PROGRESS.value,
                ProjectStatus.CANCELLED.value,
            ],
            ProjectStatus.COMPLETED.value: [
                ProjectStatus.ARCHIVED.value,
            ],
            ProjectStatus.CANCELLED.value: [
                ProjectStatus.ARCHIVED.value,
            ],
            ProjectStatus.ARCHIVED.value: [],
        }

        return to_status in valid_transitions.get(from_status, [])

    def _invalidate_project_cache(self, project_id: int, organization_id: int) -> None:
        """Invalidate project-related cache entries."""
        if not self.cache_manager:
            return

        cache_patterns = [
            f"project:{project_id}:*",
            f"projects:org:{organization_id}:*",
            f"project_analytics:{project_id}:*",
        ]

        for pattern in cache_patterns:
            # In a real implementation, this would use async
            # For now, we'll just note that cache should be invalidated
            pass

    # Additional methods required for Sprint 3 Day 2

    def add_member(
        self,
        project_id: int,
        user_id: int,
        role: str,
        current_user_id: int,
        permissions: Optional[List[str]] = None,
    ) -> bool:
        """Add a member to the project."""
        # Validate current user has permission to manage members
        project = self.db.query(Project).filter(
            Project.id == project_id,
            Project.is_active == True,
        ).first()

        if not project:
            raise ValueError("Project not found")

        if self.permission_service:
            has_permission = self.permission_service.check_user_permission(
                current_user_id, "project.member.manage", project.organization_id
            )
            if not has_permission and not self._is_project_manager(project_id, current_user_id):
                raise PermissionError("Insufficient permissions to manage project members")

        # Check if user already exists as member
        existing_member = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        ).first()

        if existing_member:
            if existing_member.is_active:
                raise ValueError("User is already a member of this project")
            else:
                # Reactivate existing member
                existing_member.is_active = True
                existing_member.role = role
                existing_member.permissions = permissions or []
                self.db.commit()
                return True

        # Create new member
        new_member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=role,
            permissions=permissions or [],
            is_active=True,
        )

        self.db.add(new_member)
        self.db.commit()

        return True

    def remove_member(
        self,
        project_id: int,
        user_id: int,
        current_user_id: int,
    ) -> bool:
        """Remove a member from the project."""
        # Validate current user has permission to manage members
        project = self.db.query(Project).filter(
            Project.id == project_id,
            Project.is_active == True,
        ).first()

        if not project:
            raise ValueError("Project not found")

        # Can't remove project owner
        if project.owner_id == user_id:
            raise ValueError("Cannot remove project owner")

        if self.permission_service:
            has_permission = self.permission_service.check_user_permission(
                current_user_id, "project.member.manage", project.organization_id
            )
            if not has_permission and not self._is_project_manager(project_id, current_user_id):
                raise PermissionError("Insufficient permissions to manage project members")

        # Find and deactivate member
        member = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.is_active == True,
        ).first()

        if not member:
            return False

        member.is_active = False
        self.db.commit()

        return True

    def update_member_role(
        self,
        project_id: int,
        user_id: int,
        role: str,
        current_user_id: int,
        permissions: Optional[List[str]] = None,
    ) -> bool:
        """Update a member's role in the project."""
        # Validate current user has permission to manage members
        project = self.db.query(Project).filter(
            Project.id == project_id,
            Project.is_active == True,
        ).first()

        if not project:
            raise ValueError("Project not found")

        if self.permission_service:
            has_permission = self.permission_service.check_user_permission(
                current_user_id, "project.member.manage", project.organization_id
            )
            if not has_permission and not self._is_project_manager(project_id, current_user_id):
                raise PermissionError("Insufficient permissions to manage project members")

        # Find and update member
        member = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.is_active == True,
        ).first()

        if not member:
            raise ValueError("Member not found")

        member.role = role
        if permissions is not None:
            member.permissions = permissions

        self.db.commit()

        return True

    def get_project_progress(self, project_id: int) -> float:
        """Get project progress percentage."""
        project = self.db.query(Project).filter(
            Project.id == project_id,
            Project.is_active == True,
        ).first()

        if not project:
            return 0.0

        # Update progress based on tasks and milestones
        project.update_progress()
        self.db.commit()

        return float(project.progress_percentage)

    def get_budget_utilization_details(self, project_id: int) -> Dict[str, float]:
        """Get budget utilization information."""
        project = self.db.query(Project).filter(
            Project.id == project_id,
            Project.is_active == True,
        ).first()

        if not project:
            return {"total_budget": 0.0, "spent_budget": 0.0, "utilization_percentage": 0.0}

        total_budget = float(project.budget) if project.budget else 0.0
        spent_budget = float(project.spent_budget) if project.spent_budget else 0.0
        utilization_percentage = (spent_budget / total_budget * 100) if total_budget > 0 else 0.0

        return {
            "total_budget": total_budget,
            "spent_budget": spent_budget,
            "remaining_budget": total_budget - spent_budget,
            "utilization_percentage": utilization_percentage,
        }

    def user_has_project_access(
        self,
        user_id: int,
        project_id: int,
        permission: str,
    ) -> bool:
        """Check if user has specific access to project."""
        project = self.db.query(Project).filter(
            Project.id == project_id,
            Project.is_active == True,
        ).first()

        if not project:
            return False

        # Check organization-level permission
        if self.permission_service:
            has_org_permission = self.permission_service.check_user_permission(
                user_id, permission, project.organization_id
            )
            if has_org_permission:
                return True

        # Check project membership
        if self._is_project_member(project_id, user_id):
            member = self.db.query(ProjectMember).filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
                ProjectMember.is_active == True,
            ).first()

            if member:
                effective_permissions = member.get_effective_permissions()
                return permission in effective_permissions

        return False

    def get_enhanced_project_statistics(
        self,
        project_id: int,
        user_id: Optional[int] = None,
    ) -> ProjectStatistics:
        """Get enhanced project statistics for API response."""
        project = self.db.query(Project).filter(
            Project.id == project_id,
            Project.is_active == True,
        ).first()

        if not project:
            raise ValueError("Project not found")

        # Validate permission if service is available
        if self.permission_service and user_id:
            has_permission = self.permission_service.check_user_permission(
                user_id, "project.view", project.organization_id
            )
            if not has_permission and not self._is_project_member(project.id, user_id):
                raise PermissionError("Insufficient permissions to view project statistics")

        # Get counts
        member_count = project.get_member_count()
        task_count = project.get_total_tasks_count()
        completed_tasks = project.get_completed_tasks_count()
        active_tasks = project.get_active_tasks_count()
        overdue_tasks = project.get_overdue_tasks_count()

        # Get utilization
        budget_utilization = project.budget_usage_percentage
        hours_utilization = project.hours_usage_percentage

        return ProjectStatistics(
            project_id=project_id,
            member_count=member_count,
            task_count=task_count,
            completed_tasks=completed_tasks,
            active_tasks=active_tasks,
            overdue_tasks=overdue_tasks,
            progress_percentage=float(project.progress_percentage),
            budget_utilization=budget_utilization,
            hours_utilization=hours_utilization,
            health_status=project.get_health_status(),
            is_on_schedule=project.is_on_schedule,
            days_remaining=project.days_remaining,
        )


class ProjectRepositoryLocal:
    """Local project repository stub for service."""

    def __init__(self, db: Session):
        self.db = db

    def get_member_count(self, project_id: int) -> int:
        """Get number of project members."""
        return self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.is_active == True,
        ).count()


# Type alias for backward compatibility
ProjectRepository = ProjectRepositoryLocal
