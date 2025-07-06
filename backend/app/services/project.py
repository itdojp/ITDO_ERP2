"""Project management service."""

from typing import List, Optional
from datetime import date

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import BusinessLogicError, NotFound, PermissionDenied
from app.models.project import Project
from app.models.user import User
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
    ProjectListResponse,
    ProjectSearchParams,
)
from app.services.audit import AuditLogger


class ProjectService:
    """Project management service class."""

    def create_project(
        self, data: ProjectCreateRequest, creator: User, db: Session
    ) -> Project:
        """Create a new project with permission checks."""
        # Check permissions
        if not creator.is_superuser:
            # User must be a member of the organization
            user_org_ids = [o.id for o in creator.get_organizations()]
            if data.organization_id not in user_org_ids:
                raise PermissionDenied("組織へのアクセス権限がありません")

            # Check if creator has project creation role
            if not any(
                r.code in ["PROJECT_ADMIN", "MEMBER"]
                for r in creator.get_roles_in_organization(data.organization_id)
            ):
                raise PermissionDenied("プロジェクトを作成する権限がありません")

        # Create project
        project = Project.create(
            db,
            name=data.name,
            description=data.description,
            start_date=data.start_date,
            end_date=data.end_date,
            status=data.status or "planning",
            organization_id=data.organization_id,
            created_by=creator.id,
        )

        db.flush()

        # Log audit
        self._log_audit(
            "create",
            "project",
            project.id,
            creator,
            {
                "name": project.name,
                "organization_id": data.organization_id,
            },
            db,
        )

        return project

    def get_project(
        self, project_id: int, viewer: User, db: Session
    ) -> ProjectResponse:
        """Get project details with permission check."""
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.deleted_at.is_(None)
        ).first()
        
        if not project:
            raise NotFound("プロジェクトが見つかりません")

        # Permission check
        if not self._can_access_project(viewer, project):
            raise PermissionDenied("このプロジェクトへのアクセス権限がありません")

        return self._project_to_response(project)

    def search_projects(
        self, params: ProjectSearchParams, searcher: User, db: Session
    ) -> ProjectListResponse:
        """Search projects with filters and multi-tenant isolation."""
        query = db.query(Project).options(
            joinedload(Project.organization),
            joinedload(Project.creator),
        ).filter(Project.deleted_at.is_(None))

        # Multi-tenant isolation
        if not searcher.is_superuser:
            # Get searcher's organizations
            searcher_org_ids = [o.id for o in searcher.get_organizations()]
            query = query.filter(Project.organization_id.in_(searcher_org_ids))

        # Apply filters
        if params.search:
            search_term = f"%{params.search}%"
            query = query.filter(
                or_(
                    Project.name.ilike(search_term),
                    Project.description.ilike(search_term),
                )
            )

        if params.status:
            query = query.filter(Project.status == params.status)

        if params.organization_id is not None:
            query = query.filter(Project.organization_id == params.organization_id)

        if params.start_date_from:
            query = query.filter(Project.start_date >= params.start_date_from)

        if params.start_date_to:
            query = query.filter(Project.start_date <= params.start_date_to)

        # Count total
        total = query.count()

        # Default pagination
        page = params.page or 1
        limit = params.limit or 20
        offset = (page - 1) * limit

        # Execute query
        projects = query.offset(offset).limit(limit).all()

        return ProjectListResponse(
            items=[self._project_to_response(p) for p in projects],
            total=total,
            page=page,
            limit=limit,
        )

    def update_project(
        self, project_id: int, data: ProjectUpdateRequest, updater: User, db: Session
    ) -> Project:
        """Update project information."""
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.deleted_at.is_(None)
        ).first()
        
        if not project:
            raise NotFound("プロジェクトが見つかりません")

        # Permission check
        if not self._can_edit_project(updater, project):
            raise PermissionDenied("このプロジェクトを更新する権限がありません")

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        project.update(db, updated_by=updater.id, **update_data)

        # Log audit
        self._log_audit("update", "project", project.id, updater, update_data, db)

        return project

    def delete_project(
        self, project_id: int, deleter: User, db: Session
    ) -> None:
        """Delete project (soft delete)."""
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.deleted_at.is_(None)
        ).first()
        
        if not project:
            raise NotFound("プロジェクトが見つかりません")

        # Permission check
        if not deleter.is_superuser:
            # Only project admins or system admins can delete
            if not any(
                r.code == "PROJECT_ADMIN"
                for r in deleter.get_roles_in_organization(project.organization_id)
            ):
                raise PermissionDenied("プロジェクトを削除する権限がありません")

        # Soft delete
        project.soft_delete(db, deleter.id)

        # Log audit
        self._log_audit("delete", "project", project.id, deleter, {}, db)

    def _can_access_project(self, user: User, project: Project) -> bool:
        """Check if user can access project."""
        if user.is_superuser:
            return True

        # User must be in the same organization
        user_org_ids = [o.id for o in user.get_organizations()]
        return project.organization_id in user_org_ids

    def _can_edit_project(self, user: User, project: Project) -> bool:
        """Check if user can edit project."""
        if user.is_superuser:
            return True

        # User must be project admin or creator
        if project.created_by == user.id:
            return True

        # Check if user has admin role in organization
        return any(
            r.code in ["PROJECT_ADMIN", "ORG_ADMIN"]
            for r in user.get_roles_in_organization(project.organization_id)
        )

    def _project_to_response(self, project: Project) -> ProjectResponse:
        """Convert project to response schema."""
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            start_date=project.start_date,
            end_date=project.end_date,
            actual_end_date=project.actual_end_date,
            organization_id=project.organization_id,
            created_at=project.created_at,
            updated_at=project.updated_at,
            created_by=project.created_by,
            updated_by=project.updated_by,
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