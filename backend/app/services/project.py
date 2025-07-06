"""Project service implementation with business logic."""

from typing import List, Optional, Dict, Any, Tuple
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.project_phase import ProjectPhase
from app.models.project_milestone import ProjectMilestone
from app.models.user import User
from app.models.role import UserRole
from app.repositories.project import ProjectRepository
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectSummary,
    ProjectTree,
    ProjectStatistics
)
from app.types import OrganizationId, DepartmentId, UserId
from app.core.exceptions import NotFound, PermissionDenied, BusinessLogicError


class ProjectService:
    """Service for project business logic."""
    
    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
        self.repository = ProjectRepository(db)
    
    def get_project(self, project_id: int, user_id: UserId) -> Optional[Project]:
        """Get project by ID with permission check."""
        project = self.repository.get_with_relationships(project_id)
        if not project:
            return None
        
        # Check permissions
        if not self._can_view_project(user_id, project):
            raise PermissionDenied("You don't have permission to view this project")
        
        return project
    
    def list_projects(
        self,
        user_id: UserId,
        organization_id: Optional[OrganizationId] = None,
        department_id: Optional[DepartmentId] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        query: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Project], int]:
        """List projects with filters and permission check."""
        # Get user's organizations
        user_orgs = self._get_user_organizations(user_id)
        
        # Filter by user's organizations if not specified
        if organization_id:
            if organization_id not in user_orgs:
                raise PermissionDenied("You don't have access to this organization")
        else:
            # For listing, we don't filter by organization to allow cross-org view
            # but we'll filter results based on permissions
            pass
        
        # Search projects
        projects, total = self.repository.search_projects(
            organization_id=organization_id,
            department_id=department_id,
            status=status,
            priority=priority,
            query=query,
            skip=skip,
            limit=limit
        )
        
        # Filter by permissions
        filtered_projects = []
        for project in projects:
            if self._can_view_project(user_id, project):
                filtered_projects.append(project)
        
        return filtered_projects, len(filtered_projects)
    
    def create_project(
        self,
        project_data: ProjectCreate,
        user_id: UserId
    ) -> Project:
        """Create a new project."""
        # Check permissions
        if not self._can_create_project(user_id, project_data.organization_id):
            raise PermissionDenied("You don't have permission to create projects in this organization")
        
        # Validate unique code
        if not self.repository.validate_unique_code(project_data.organization_id, project_data.code):
            raise BusinessLogicError(f"Project code '{project_data.code}' already exists in this organization")
        
        # Validate parent project if specified
        if project_data.parent_id:
            parent = self.repository.get(project_data.parent_id)
            if not parent:
                raise NotFound("Parent project not found")
            if parent.organization_id != project_data.organization_id:
                raise BusinessLogicError("Parent project must be in the same organization")
        
        # Create project
        data = project_data.model_dump()
        data['created_by'] = user_id
        data['updated_by'] = user_id
        
        try:
            project = self.repository.create(ProjectCreate(**data))
            
            # Add creator as project member
            member_data = {
                'project_id': project.id,
                'user_id': user_id,
                'role': 'owner',
                'allocation_percentage': 100,
                'start_date': date.today(),
                'created_by': user_id,
                'updated_by': user_id
            }
            member = ProjectMember(**member_data)
            self.db.add(member)
            self.db.commit()
            
            return project
            
        except IntegrityError as e:
            self.db.rollback()
            raise BusinessLogicError(f"Failed to create project: {str(e)}")
    
    def update_project(
        self,
        project_id: int,
        project_data: ProjectUpdate,
        user_id: UserId
    ) -> Optional[Project]:
        """Update project details."""
        # Get project
        project = self.repository.get(project_id)
        if not project:
            return None
        
        # Check permissions
        if not self._can_update_project(user_id, project):
            raise PermissionDenied("You don't have permission to update this project")
        
        # Validate dates if being updated
        update_data = project_data.model_dump(exclude_unset=True)
        
        if 'planned_start_date' in update_data or 'planned_end_date' in update_data:
            start_date = update_data.get('planned_start_date', project.planned_start_date)
            end_date = update_data.get('planned_end_date', project.planned_end_date)
            
            if start_date and end_date and start_date > end_date:
                raise BusinessLogicError("End date must be after start date")
        
        # Validate progress
        if 'progress_percentage' in update_data:
            progress = update_data['progress_percentage']
            if progress < 0 or progress > 100:
                raise BusinessLogicError("Progress must be between 0 and 100")
        
        # Update project
        update_data['updated_by'] = user_id
        updated_project = self.repository.update(project_id, ProjectUpdate(**update_data))
        
        # Update status based on progress
        if updated_project and updated_project.progress_percentage == 100 and updated_project.status == 'in_progress':
            self.repository.update(project_id, ProjectUpdate(status='completed'))
        
        return updated_project
    
    def delete_project(self, project_id: int, user_id: UserId) -> bool:
        """Soft delete a project."""
        # Get project
        project = self.repository.get(project_id)
        if not project:
            return False
        
        # Check permissions
        if not self._can_delete_project(user_id, project):
            raise PermissionDenied("You don't have permission to delete this project")
        
        # Check if can be deleted
        if not project.can_be_deleted():
            raise BusinessLogicError("Project cannot be deleted due to active sub-projects or in-progress status")
        
        # Soft delete
        project.soft_delete(deleted_by=user_id)
        self.db.commit()
        
        return True
    
    def get_project_tree(
        self,
        user_id: UserId,
        organization_id: Optional[OrganizationId] = None,
        root_id: Optional[int] = None
    ) -> List[ProjectTree]:
        """Get project hierarchy tree."""
        # Get root projects
        if root_id:
            roots = [self.repository.get(root_id)]
            if not roots[0]:
                return []
        else:
            roots = self.repository.get_root_projects(organization_id)
        
        def build_tree(project: Project, level: int = 0) -> Optional[ProjectTree]:
            """Build tree recursively with permission check."""
            if not self._can_view_project(user_id, project):
                return None
            
            children = []
            for sub in self.repository.get_sub_projects(project.id):
                child = build_tree(sub, level + 1)
                if child:
                    children.append(child)
            
            return ProjectTree(
                id=project.id,
                code=project.code,
                name=project.name,
                status=project.status,
                progress_percentage=project.progress_percentage,
                level=level,
                parent_id=project.parent_id,
                children=children
            )
        
        trees = []
        for root in roots:
            tree = build_tree(root)
            if tree:
                trees.append(tree)
        
        return trees
    
    def get_project_statistics(self, project_id: int, user_id: UserId) -> ProjectStatistics:
        """Get project statistics."""
        # Get project
        project = self.get_project(project_id, user_id)
        if not project:
            raise NotFound("Project not found")
        
        # Get statistics
        stats = self.repository.get_project_statistics(project_id)
        return ProjectStatistics(**stats)
    
    def add_project_member(
        self,
        project_id: int,
        member_user_id: UserId,
        role: str,
        allocation_percentage: int,
        start_date: date,
        end_date: Optional[date],
        user_id: UserId
    ) -> ProjectMember:
        """Add a member to project."""
        # Get project
        project = self.repository.get(project_id)
        if not project:
            raise NotFound("Project not found")
        
        # Check permissions
        if not self._can_manage_members(user_id, project):
            raise PermissionDenied("You don't have permission to manage project members")
        
        # Validate member
        member_user = self.db.get(User, member_user_id)
        if not member_user:
            raise NotFound("User not found")
        
        # Check if already a member
        existing = self.db.query(ProjectMember).filter_by(
            project_id=project_id,
            user_id=member_user_id,
            is_active=True
        ).first()
        
        if existing:
            raise BusinessLogicError("User is already a project member")
        
        # Create member
        member = ProjectMember(
            project_id=project_id,
            user_id=member_user_id,
            role=role,
            allocation_percentage=allocation_percentage,
            start_date=start_date,
            end_date=end_date,
            created_by=user_id,
            updated_by=user_id
        )
        
        # Validate
        member.validate_dates()
        member.validate_allocation()
        
        self.db.add(member)
        self.db.commit()
        
        return member
    
    def update_project_progress(self, project_id: int, user_id: UserId) -> Optional[Project]:
        """Update project progress based on phases."""
        # Get project
        project = self.repository.get(project_id)
        if not project:
            return None
        
        # Check permissions
        if not self._can_update_project(user_id, project):
            raise PermissionDenied("You don't have permission to update this project")
        
        # Update progress
        return self.repository.update_progress(project_id)
    
    def get_overdue_projects(
        self,
        user_id: UserId,
        organization_id: Optional[OrganizationId] = None
    ) -> List[Project]:
        """Get overdue projects."""
        projects = self.repository.get_overdue_projects(organization_id)
        
        # Filter by permissions
        return [p for p in projects if self._can_view_project(user_id, p)]
    
    def get_user_projects(
        self,
        user_id: UserId,
        target_user_id: Optional[UserId] = None
    ) -> List[Project]:
        """Get projects where user is a member."""
        # Default to requesting user
        if not target_user_id:
            target_user_id = user_id
        
        # Check if can view other user's projects
        if target_user_id != user_id:
            # Check if has permission to view other users
            if not self._is_admin(user_id):
                raise PermissionDenied("You can only view your own projects")
        
        return self.repository.get_projects_by_member(target_user_id)
    
    # Permission helper methods
    
    def _can_view_project(self, user_id: UserId, project: Project) -> bool:
        """Check if user can view project."""
        # Admin can view all
        if self._is_admin(user_id):
            return True
        
        # Project member can view
        if self._is_project_member(user_id, project.id):
            return True
        
        # Organization member can view
        if self._is_organization_member(user_id, project.organization_id):
            return True
        
        return False
    
    def _can_create_project(self, user_id: UserId, organization_id: OrganizationId) -> bool:
        """Check if user can create projects in organization."""
        # Admin can create
        if self._is_admin(user_id):
            return True
        
        # Check organization permissions
        return self._has_organization_permission(user_id, organization_id, 'projects.create')
    
    def _can_update_project(self, user_id: UserId, project: Project) -> bool:
        """Check if user can update project."""
        # Admin can update
        if self._is_admin(user_id):
            return True
        
        # Project manager can update
        if project.project_manager_id == user_id:
            return True
        
        # Check project member role
        member = self.db.query(ProjectMember).filter_by(
            project_id=project.id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if member and member.role in ['owner', 'manager']:
            return True
        
        # Check organization permissions
        return self._has_organization_permission(user_id, project.organization_id, 'projects.update')
    
    def _can_delete_project(self, user_id: UserId, project: Project) -> bool:
        """Check if user can delete project."""
        # Admin can delete
        if self._is_admin(user_id):
            return True
        
        # Check organization permissions
        return self._has_organization_permission(user_id, project.organization_id, 'projects.delete')
    
    def _can_manage_members(self, user_id: UserId, project: Project) -> bool:
        """Check if user can manage project members."""
        # Admin can manage
        if self._is_admin(user_id):
            return True
        
        # Project manager can manage
        if project.project_manager_id == user_id:
            return True
        
        # Check project member role
        member = self.db.query(ProjectMember).filter_by(
            project_id=project.id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if member and member.role in ['owner', 'manager']:
            return True
        
        return False
    
    def _is_admin(self, user_id: UserId) -> bool:
        """Check if user is admin."""
        user = self.db.get(User, user_id)
        return user and user.is_superuser
    
    def _is_project_member(self, user_id: UserId, project_id: int) -> bool:
        """Check if user is project member."""
        return self.db.query(ProjectMember).filter_by(
            project_id=project_id,
            user_id=user_id,
            is_active=True
        ).first() is not None
    
    def _is_organization_member(self, user_id: UserId, organization_id: OrganizationId) -> bool:
        """Check if user is organization member."""
        return self.db.query(UserRole).filter_by(
            user_id=user_id,
            organization_id=organization_id,
            is_active=True
        ).first() is not None
    
    def _get_user_organizations(self, user_id: UserId) -> List[OrganizationId]:
        """Get user's organizations."""
        user_roles = self.db.query(UserRole).filter_by(
            user_id=user_id,
            is_active=True
        ).all()
        
        return list(set(ur.organization_id for ur in user_roles))
    
    def _has_organization_permission(
        self,
        user_id: UserId,
        organization_id: OrganizationId,
        permission: str
    ) -> bool:
        """Check if user has specific permission in organization."""
        user_roles = self.db.query(UserRole).filter_by(
            user_id=user_id,
            organization_id=organization_id,
            is_active=True
        ).all()
        
        for user_role in user_roles:
            if user_role.role and user_role.role.has_permission(permission):
                return True
        
        return False