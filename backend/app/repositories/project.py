"""Project repository with type-safe CRUD operations."""

from typing import Optional, List, Dict, Any, Tuple
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import select, and_, or_, func, case
from sqlalchemy.orm import Session, selectinload, joinedload

from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.project_phase import ProjectPhase
from app.models.project_milestone import ProjectMilestone
from app.repositories.base import BaseRepository
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.types import OrganizationId, DepartmentId, UserId


class ProjectRepository(BaseRepository[Project, ProjectCreate, ProjectUpdate]):
    """Repository for Project model with specialized queries."""
    
    def __init__(self, db: Session):
        """Initialize repository with Project model."""
        super().__init__(Project, db)
    
    def get_by_code(self, organization_id: OrganizationId, code: str) -> Optional[Project]:
        """Get project by code within an organization."""
        return self.db.scalar(
            select(Project).where(
                and_(
                    Project.organization_id == organization_id,
                    Project.code == code,
                    Project.is_deleted == False
                )
            )
        )
    
    def get_with_relationships(self, project_id: int) -> Optional[Project]:
        """Get project with all relationships loaded."""
        return self.db.scalar(
            select(Project)
            .options(
                joinedload(Project.organization),
                joinedload(Project.department),
                joinedload(Project.project_manager),
                joinedload(Project.parent),
                selectinload(Project.members).joinedload(ProjectMember.user),
                selectinload(Project.phases),
                selectinload(Project.milestones)
            )
            .where(
                and_(
                    Project.id == project_id,
                    Project.is_deleted == False
                )
            )
        )
    
    def search_projects(
        self,
        organization_id: Optional[OrganizationId] = None,
        department_id: Optional[DepartmentId] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        project_type: Optional[str] = None,
        parent_id: Optional[int] = None,
        manager_id: Optional[UserId] = None,
        query: Optional[str] = None,
        start_date_from: Optional[date] = None,
        start_date_to: Optional[date] = None,
        end_date_from: Optional[date] = None,
        end_date_to: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Project], int]:
        """Search projects with multiple filters."""
        stmt = select(Project).where(Project.is_deleted == False)
        
        # Apply filters
        if organization_id is not None:
            stmt = stmt.where(Project.organization_id == organization_id)
        
        if department_id is not None:
            stmt = stmt.where(Project.department_id == department_id)
        
        if status is not None:
            stmt = stmt.where(Project.status == status)
        
        if priority is not None:
            stmt = stmt.where(Project.priority == priority)
        
        if project_type is not None:
            stmt = stmt.where(Project.project_type == project_type)
        
        if parent_id is not None:
            stmt = stmt.where(Project.parent_id == parent_id)
        
        if manager_id is not None:
            stmt = stmt.where(Project.project_manager_id == manager_id)
        
        # Text search
        if query:
            search_term = f"%{query}%"
            stmt = stmt.where(
                or_(
                    Project.code.ilike(search_term),
                    Project.name.ilike(search_term),
                    Project.name_en.ilike(search_term),
                    Project.description.ilike(search_term)
                )
            )
        
        # Date range filters
        if start_date_from:
            stmt = stmt.where(Project.planned_start_date >= start_date_from)
        
        if start_date_to:
            stmt = stmt.where(Project.planned_start_date <= start_date_to)
        
        if end_date_from:
            stmt = stmt.where(Project.planned_end_date >= end_date_from)
        
        if end_date_to:
            stmt = stmt.where(Project.planned_end_date <= end_date_to)
        
        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = self.db.scalar(count_stmt) or 0
        
        # Apply pagination and ordering
        stmt = stmt.order_by(Project.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)
        
        # Load relationships
        stmt = stmt.options(
            joinedload(Project.organization),
            joinedload(Project.department),
            joinedload(Project.project_manager)
        )
        
        results = list(self.db.scalars(stmt))
        return results, total_count
    
    def get_root_projects(self, organization_id: Optional[OrganizationId] = None) -> List[Project]:
        """Get root projects (no parent)."""
        stmt = select(Project).where(
            and_(
                Project.parent_id == None,
                Project.is_deleted == False
            )
        )
        
        if organization_id:
            stmt = stmt.where(Project.organization_id == organization_id)
        
        stmt = stmt.order_by(Project.name)
        return list(self.db.scalars(stmt))
    
    def get_sub_projects(self, parent_id: int) -> List[Project]:
        """Get direct sub-projects of a parent project."""
        stmt = select(Project).where(
            and_(
                Project.parent_id == parent_id,
                Project.is_deleted == False
            )
        ).order_by(Project.name)
        
        return list(self.db.scalars(stmt))
    
    def get_all_sub_projects(self, parent_id: int) -> List[Project]:
        """Get all sub-projects recursively."""
        # Using recursive CTE for hierarchical query
        parent = self.get(parent_id)
        if not parent:
            return []
        
        # For now, use Python recursion (can be optimized with CTE)
        result = []
        sub_projects = self.get_sub_projects(parent_id)
        for sub in sub_projects:
            result.append(sub)
            result.extend(self.get_all_sub_projects(sub.id))
        
        return result
    
    def get_overdue_projects(self, organization_id: Optional[OrganizationId] = None) -> List[Project]:
        """Get overdue projects."""
        stmt = select(Project).where(
            and_(
                Project.status.in_(['planning', 'in_progress']),
                Project.planned_end_date < date.today(),
                Project.is_deleted == False
            )
        )
        
        if organization_id:
            stmt = stmt.where(Project.organization_id == organization_id)
        
        stmt = stmt.order_by(Project.planned_end_date)
        return list(self.db.scalars(stmt))
    
    def get_project_statistics(self, project_id: int) -> Dict[str, Any]:
        """Get comprehensive project statistics."""
        project = self.get_with_relationships(project_id)
        if not project:
            return {}
        
        # Member statistics
        member_count = project.members.count()
        active_member_count = project.members.filter_by(is_active=True).count()
        
        # Phase statistics
        phase_count = project.phases.filter_by(is_deleted=False).count()
        completed_phase_count = project.phases.filter_by(
            is_deleted=False,
            status='completed'
        ).count()
        
        # Milestone statistics
        milestone_count = project.milestones.filter_by(is_deleted=False).count()
        completed_milestone_count = project.milestones.filter_by(
            is_deleted=False,
            status='completed'
        ).count()
        upcoming_milestone_count = project.milestones.filter(
            and_(
                ProjectMilestone.is_deleted == False,
                ProjectMilestone.status == 'pending',
                ProjectMilestone.due_date >= date.today(),
                ProjectMilestone.due_date <= date.today() + timedelta(days=7)
            )
        ).count()
        overdue_milestone_count = project.milestones.filter(
            and_(
                ProjectMilestone.is_deleted == False,
                ProjectMilestone.status == 'pending',
                ProjectMilestone.due_date < date.today()
            )
        ).count()
        
        # Budget calculation
        total_budget = project.budget or Decimal('0')
        total_actual_cost = project.actual_cost or Decimal('0')
        
        # Include sub-project budgets
        for sub in project.sub_projects:
            if sub.budget:
                total_budget += sub.budget
            if sub.actual_cost:
                total_actual_cost += sub.actual_cost
        
        budget_usage_percentage = None
        if total_budget > 0:
            budget_usage_percentage = float((total_actual_cost / total_budget) * 100)
        
        return {
            'id': project.id,
            'total_budget': total_budget,
            'total_actual_cost': total_actual_cost,
            'budget_usage_percentage': budget_usage_percentage,
            'overall_progress': project.progress_percentage,
            'member_count': member_count,
            'active_member_count': active_member_count,
            'phase_count': phase_count,
            'completed_phase_count': completed_phase_count,
            'milestone_count': milestone_count,
            'completed_milestone_count': completed_milestone_count,
            'upcoming_milestone_count': upcoming_milestone_count,
            'overdue_milestone_count': overdue_milestone_count,
            'task_count': 0,  # Placeholder for future task integration
            'completed_task_count': 0
        }
    
    def validate_unique_code(self, organization_id: OrganizationId, code: str, exclude_id: Optional[int] = None) -> bool:
        """Validate if project code is unique within organization."""
        stmt = select(func.count(Project.id)).where(
            and_(
                Project.organization_id == organization_id,
                Project.code == code,
                Project.is_deleted == False
            )
        )
        
        if exclude_id:
            stmt = stmt.where(Project.id != exclude_id)
        
        count = self.db.scalar(stmt) or 0
        return count == 0
    
    def get_member_count(self, project_id: int) -> int:
        """Get active member count for a project."""
        return self.db.scalar(
            select(func.count(ProjectMember.id))
            .where(
                and_(
                    ProjectMember.project_id == project_id,
                    ProjectMember.is_active == True
                )
            )
        ) or 0
    
    def get_projects_by_member(self, user_id: UserId, is_active: bool = True) -> List[Project]:
        """Get projects where user is a member."""
        stmt = select(Project).join(ProjectMember).where(
            and_(
                ProjectMember.user_id == user_id,
                ProjectMember.is_active == is_active,
                Project.is_deleted == False
            )
        ).order_by(Project.name)
        
        return list(self.db.scalars(stmt))
    
    def update_progress(self, project_id: int) -> Optional[Project]:
        """Update project progress based on phases or sub-projects."""
        project = self.get(project_id)
        if not project:
            return None
        
        project.update_progress()
        self.db.commit()
        self.db.refresh(project)
        
        return project