"""Dashboard service implementation with business logic."""

from typing import List, Optional, Dict, Any, Tuple
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, select

from app.models.user import User
from app.models.organization import Organization
from app.models.role import UserRole
from app.schemas.dashboard import (
    OrganizationStats,
    PersonalStats,
    ProjectProgressSummary,
    TaskSummary,
    MilestoneSummary,
    RecentActivity,
    BudgetStatus,
    TimelineStatus,
    ProjectDashboardStats,
    TrendData,
    TrendDataPoint,
    MainDashboardData,
    PersonalDashboardData,
    DashboardFilters
)
from app.types import OrganizationId, UserId
from app.core.exceptions import NotFound, PermissionDenied


class DashboardService:
    """Service for dashboard data aggregation and business logic."""
    
    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
    
    def get_main_dashboard(
        self,
        user_id: UserId,
        filters: DashboardFilters
    ) -> MainDashboardData:
        """Get main dashboard data for organization overview."""
        # Check permissions
        if not self._can_view_organization_dashboard(user_id, filters.organization_id):
            raise PermissionDenied("You don't have permission to view this organization's dashboard")
        
        # Get organization stats
        org_stats = self._get_organization_stats(user_id, filters.organization_id)
        
        # Get recent projects
        recent_projects = self._get_recent_projects(user_id, filters)
        
        # Get overdue items summary
        overdue_items = self._get_overdue_summary(user_id, filters.organization_id)
        
        # Get recent activities
        recent_activities = self._get_recent_activities(user_id, filters, limit=10)
        
        # Get budget overview
        budget_overview = self._get_budget_overview(user_id, filters.organization_id)
        
        # Get performance trends
        performance_trends = self._get_performance_trends(user_id, filters)
        
        return MainDashboardData(
            organization_stats=org_stats,
            recent_projects=recent_projects,
            overdue_items=overdue_items,
            recent_activities=recent_activities,
            budget_overview=budget_overview,
            performance_trends=performance_trends
        )
    
    def get_personal_dashboard(
        self,
        user_id: UserId,
        filters: DashboardFilters
    ) -> PersonalDashboardData:
        """Get personal dashboard data for user."""
        # Get personal stats
        personal_stats = self._get_personal_stats(user_id, filters.date_range)
        
        # Get user's projects
        my_projects = self._get_user_projects(user_id, limit=10)
        
        # Get user's tasks
        my_tasks = self._get_user_tasks(user_id, filters.date_range, limit=20)
        
        # Get upcoming milestones
        upcoming_milestones = self._get_upcoming_milestones(user_id, days=7)
        
        # Get today's schedule
        today_schedule = self._get_today_tasks(user_id)
        
        # Get recent activities
        recent_activities = self._get_user_activities(user_id, limit=5)
        
        return PersonalDashboardData(
            personal_stats=personal_stats,
            my_projects=my_projects,
            my_tasks=my_tasks,
            upcoming_milestones=upcoming_milestones,
            today_schedule=today_schedule,
            recent_activities=recent_activities
        )
    
    def get_project_dashboard(
        self,
        project_id: int,
        user_id: UserId
    ) -> ProjectDashboardStats:
        """Get project-specific dashboard data."""
        # Import here to avoid circular imports
        from app.models.project import Project
        from app.services.project import ProjectService
        
        project_service = ProjectService(self.db)
        
        # Check if user can view this project
        project = project_service.get_project(project_id, user_id)
        if not project:
            raise NotFound("Project not found")
        
        # Get project statistics
        stats = project_service.get_project_statistics(project_id, user_id)
        
        # Get budget status
        budget_status = self._calculate_project_budget_status(project)
        
        # Get timeline status
        timeline_status = self._calculate_project_timeline_status(project)
        
        return ProjectDashboardStats(
            project_id=project.id,
            project_name=project.name,
            project_code=project.code,
            project_status=project.status,
            total_tasks=stats.task_count,
            completed_tasks=stats.completed_task_count,
            in_progress_tasks=stats.task_count - stats.completed_task_count,
            overdue_tasks=0,  # This would need task model implementation
            total_phases=stats.phase_count,
            completed_phases=stats.completed_phase_count,
            total_milestones=stats.milestone_count,
            completed_milestones=stats.completed_milestone_count,
            overdue_milestones=stats.overdue_milestone_count,
            team_members=stats.active_member_count,
            budget_status=budget_status,
            timeline_status=timeline_status
        )
    
    # Private helper methods
    
    def _get_organization_stats(
        self,
        user_id: UserId,
        organization_id: Optional[OrganizationId]
    ) -> OrganizationStats:
        """Get organization-wide statistics."""
        from app.models.project import Project
        
        # Build base query for projects
        project_query = select(Project).where(Project.is_deleted == False)
        
        if organization_id:
            project_query = project_query.where(Project.organization_id == organization_id)
        else:
            # Get user's organizations
            user_orgs = self._get_user_organizations(user_id)
            if user_orgs:
                project_query = project_query.where(Project.organization_id.in_(user_orgs))
        
        # Get project counts
        total_projects = self.db.scalar(select(func.count()).select_from(project_query.subquery())) or 0
        
        active_projects = self.db.scalar(
            select(func.count()).select_from(
                project_query.where(Project.status.in_(['planning', 'in_progress'])).subquery()
            )
        ) or 0
        
        completed_projects = self.db.scalar(
            select(func.count()).select_from(
                project_query.where(Project.status == 'completed').subquery()
            )
        ) or 0
        
        # Get overdue projects
        overdue_projects = self.db.scalar(
            select(func.count()).select_from(
                project_query.where(
                    and_(
                        Project.planned_end_date < date.today(),
                        Project.status.in_(['planning', 'in_progress'])
                    )
                ).subquery()
            )
        ) or 0
        
        # Get user counts
        user_query = select(User).where(User.is_active == True)
        if organization_id:
            user_query = user_query.join(UserRole).where(UserRole.organization_id == organization_id)
        
        total_users = self.db.scalar(select(func.count()).select_from(user_query.subquery())) or 0
        active_users = total_users  # For now, same as total
        
        # Get budget information
        budget_query = project_query.where(Project.budget.isnot(None))
        total_budget = self.db.scalar(select(func.sum(Project.budget)).select_from(budget_query.subquery()))
        total_spent = self.db.scalar(select(func.sum(Project.actual_cost)).select_from(budget_query.subquery()))
        
        budget_utilization = None
        if total_budget and total_budget > 0 and total_spent:
            budget_utilization = float((total_spent / total_budget) * 100)
        
        return OrganizationStats(
            total_projects=total_projects,
            active_projects=active_projects,
            completed_projects=completed_projects,
            overdue_projects=overdue_projects,
            total_tasks=0,  # Would need task model
            pending_tasks=0,
            overdue_tasks=0,
            total_users=total_users,
            active_users=active_users,
            total_budget=total_budget,
            total_spent=total_spent,
            budget_utilization=budget_utilization
        )
    
    def _get_personal_stats(self, user_id: UserId, date_range: str) -> PersonalStats:
        """Get personal statistics for user."""
        from app.models.project import Project
        from app.models.project_member import ProjectMember
        
        # Get user's projects
        my_projects_count = self.db.scalar(
            select(func.count(Project.id)).select_from(
                select(Project)
                .join(ProjectMember)
                .where(
                    and_(
                        ProjectMember.user_id == user_id,
                        ProjectMember.is_active == True,
                        Project.is_deleted == False
                    )
                ).subquery()
            )
        ) or 0
        
        my_active_projects = self.db.scalar(
            select(func.count(Project.id)).select_from(
                select(Project)
                .join(ProjectMember)
                .where(
                    and_(
                        ProjectMember.user_id == user_id,
                        ProjectMember.is_active == True,
                        Project.is_deleted == False,
                        Project.status.in_(['planning', 'in_progress'])
                    )
                ).subquery()
            )
        ) or 0
        
        # Task statistics would go here when task model is implemented
        my_tasks = 0
        my_pending_tasks = 0
        my_overdue_tasks = 0
        tasks_due_today = 0
        tasks_due_this_week = 0
        completion_rate = 0.0
        
        return PersonalStats(
            my_projects=my_projects_count,
            my_active_projects=my_active_projects,
            my_tasks=my_tasks,
            my_pending_tasks=my_pending_tasks,
            my_overdue_tasks=my_overdue_tasks,
            tasks_due_today=tasks_due_today,
            tasks_due_this_week=tasks_due_this_week,
            completion_rate=completion_rate
        )
    
    def _get_recent_projects(
        self,
        user_id: UserId,
        filters: DashboardFilters,
        limit: int = 10
    ) -> List[ProjectProgressSummary]:
        """Get recently updated projects."""
        from app.models.project import Project
        from app.services.project import ProjectService
        
        project_service = ProjectService(self.db)
        
        # Get projects with permissions
        projects, _ = project_service.list_projects(
            user_id=user_id,
            organization_id=filters.organization_id,
            department_id=filters.department_id,
            status=filters.status_filter,
            skip=0,
            limit=limit
        )
        
        # Convert to summary format
        summaries = []
        for project in projects:
            member_count = project_service.repository.get_member_count(project.id)
            
            summaries.append(ProjectProgressSummary(
                id=project.id,
                code=project.code,
                name=project.name,
                status=project.status,
                progress_percentage=project.progress_percentage,
                planned_end_date=project.planned_end_date,
                is_overdue=project.is_overdue,
                days_remaining=project.days_remaining,
                member_count=member_count,
                budget_usage_percentage=project.budget_usage_percentage
            ))
        
        return summaries
    
    def _get_overdue_summary(
        self,
        user_id: UserId,
        organization_id: Optional[OrganizationId]
    ) -> Dict[str, int]:
        """Get summary of overdue items."""
        from app.models.project import Project
        from app.models.project_milestone import ProjectMilestone
        
        # Get user's organizations for filtering
        user_orgs = self._get_user_organizations(user_id)
        
        # Base query filter
        org_filter = []
        if organization_id:
            org_filter.append(Project.organization_id == organization_id)
        elif user_orgs:
            org_filter.append(Project.organization_id.in_(user_orgs))
        
        # Overdue projects
        overdue_projects = 0
        if org_filter:
            overdue_projects = self.db.scalar(
                select(func.count(Project.id)).where(
                    and_(
                        Project.is_deleted == False,
                        Project.planned_end_date < date.today(),
                        Project.status.in_(['planning', 'in_progress']),
                        or_(*org_filter)
                    )
                )
            ) or 0
        
        # Overdue milestones
        overdue_milestones = 0
        if org_filter:
            overdue_milestones = self.db.scalar(
                select(func.count(ProjectMilestone.id))
                .select_from(
                    select(ProjectMilestone)
                    .join(Project)
                    .where(
                        and_(
                            ProjectMilestone.is_deleted == False,
                            ProjectMilestone.due_date < date.today(),
                            ProjectMilestone.status == 'pending',
                            or_(*org_filter)
                        )
                    ).subquery()
                )
            ) or 0
        
        return {
            "projects": overdue_projects,
            "milestones": overdue_milestones,
            "tasks": 0  # Would need task model
        }
    
    def _get_recent_activities(
        self,
        user_id: UserId,
        filters: DashboardFilters,
        limit: int = 10
    ) -> List[RecentActivity]:
        """Get recent activities (placeholder - would need audit log implementation)."""
        # This would typically query an audit log table
        # For now, return empty list
        return []
    
    def _get_budget_overview(
        self,
        user_id: UserId,
        organization_id: Optional[OrganizationId]
    ) -> BudgetStatus:
        """Get budget overview for organization."""
        from app.models.project import Project
        
        # Get user's organizations
        user_orgs = self._get_user_organizations(user_id)
        
        # Build query
        query = select(Project).where(
            and_(
                Project.is_deleted == False,
                Project.budget.isnot(None)
            )
        )
        
        if organization_id:
            query = query.where(Project.organization_id == organization_id)
        elif user_orgs:
            query = query.where(Project.organization_id.in_(user_orgs))
        
        # Get totals
        total_budget = self.db.scalar(
            select(func.sum(Project.budget)).select_from(query.subquery())
        )
        spent_amount = self.db.scalar(
            select(func.sum(Project.actual_cost)).select_from(query.subquery())
        )
        
        # Calculate derived values
        remaining_amount = None
        utilization_percentage = None
        is_over_budget = False
        
        if total_budget:
            remaining_amount = total_budget - (spent_amount or Decimal('0'))
            if spent_amount:
                utilization_percentage = float((spent_amount / total_budget) * 100)
                is_over_budget = spent_amount > total_budget
        
        return BudgetStatus(
            total_budget=total_budget,
            spent_amount=spent_amount,
            remaining_amount=remaining_amount,
            utilization_percentage=utilization_percentage,
            is_over_budget=is_over_budget
        )
    
    def _get_performance_trends(
        self,
        user_id: UserId,
        filters: DashboardFilters
    ) -> List[TrendData]:
        """Get performance trends (placeholder)."""
        # This would typically analyze historical data
        # For now, return empty list
        return []
    
    def _get_user_projects(
        self,
        user_id: UserId,
        limit: int = 10
    ) -> List[ProjectProgressSummary]:
        """Get projects for user."""
        from app.services.project import ProjectService
        
        project_service = ProjectService(self.db)
        projects = project_service.get_user_projects(user_id)[:limit]
        
        summaries = []
        for project in projects:
            member_count = project_service.repository.get_member_count(project.id)
            
            summaries.append(ProjectProgressSummary(
                id=project.id,
                code=project.code,
                name=project.name,
                status=project.status,
                progress_percentage=project.progress_percentage,
                planned_end_date=project.planned_end_date,
                is_overdue=project.is_overdue,
                days_remaining=project.days_remaining,
                member_count=member_count,
                budget_usage_percentage=project.budget_usage_percentage
            ))
        
        return summaries
    
    def _get_user_tasks(
        self,
        user_id: UserId,
        date_range: str,
        limit: int = 20
    ) -> List[TaskSummary]:
        """Get tasks for user (placeholder)."""
        # Would need task model implementation
        return []
    
    def _get_upcoming_milestones(
        self,
        user_id: UserId,
        days: int = 7
    ) -> List[MilestoneSummary]:
        """Get upcoming milestones for user."""
        from app.models.project_milestone import ProjectMilestone
        from app.models.project import Project
        from app.models.project_member import ProjectMember
        
        end_date = date.today() + timedelta(days=days)
        
        milestones = self.db.scalars(
            select(ProjectMilestone)
            .join(Project)
            .join(ProjectMember)
            .where(
                and_(
                    ProjectMilestone.is_deleted == False,
                    ProjectMilestone.status == 'pending',
                    ProjectMilestone.due_date.between(date.today(), end_date),
                    ProjectMember.user_id == user_id,
                    ProjectMember.is_active == True,
                    Project.is_deleted == False
                )
            )
            .order_by(ProjectMilestone.due_date)
            .limit(10)
        ).all()
        
        summaries = []
        for milestone in milestones:
            summaries.append(MilestoneSummary(
                id=milestone.id,
                name=milestone.name,
                due_date=milestone.due_date,
                status=milestone.status,
                is_critical=milestone.is_critical,
                project_id=milestone.project_id,
                project_name=milestone.project.name,
                days_until_due=milestone.days_until_due
            ))
        
        return summaries
    
    def _get_today_tasks(self, user_id: UserId) -> List[TaskSummary]:
        """Get tasks due today (placeholder)."""
        # Would need task model implementation
        return []
    
    def _get_user_activities(
        self,
        user_id: UserId,
        limit: int = 5
    ) -> List[RecentActivity]:
        """Get user's recent activities (placeholder)."""
        # Would need audit log implementation
        return []
    
    def _calculate_project_budget_status(self, project) -> BudgetStatus:
        """Calculate budget status for a project."""
        total_budget = project.budget
        spent_amount = project.actual_cost
        
        remaining_amount = None
        utilization_percentage = None
        is_over_budget = False
        
        if total_budget:
            remaining_amount = total_budget - (spent_amount or Decimal('0'))
            if spent_amount:
                utilization_percentage = float((spent_amount / total_budget) * 100)
                is_over_budget = spent_amount > total_budget
        
        return BudgetStatus(
            total_budget=total_budget,
            spent_amount=spent_amount,
            remaining_amount=remaining_amount,
            utilization_percentage=utilization_percentage,
            is_over_budget=is_over_budget
        )
    
    def _calculate_project_timeline_status(self, project) -> TimelineStatus:
        """Calculate timeline status for a project."""
        return TimelineStatus(
            planned_start=project.planned_start_date,
            planned_end=project.planned_end_date,
            actual_start=project.actual_start_date,
            actual_end=project.actual_end_date,
            days_remaining=project.days_remaining,
            is_on_schedule=not project.is_overdue,
            is_overdue=project.is_overdue
        )
    
    # Permission helper methods
    
    def _can_view_organization_dashboard(
        self,
        user_id: UserId,
        organization_id: Optional[OrganizationId]
    ) -> bool:
        """Check if user can view organization dashboard."""
        user = self.db.get(User, user_id)
        if not user:
            return False
        
        # Admin can view all
        if user.is_superuser:
            return True
        
        # If no specific organization, user can view their own organizations
        if not organization_id:
            return True
        
        # Check if user is member of the organization
        return self.db.scalar(
            select(func.count(UserRole.id)).where(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.organization_id == organization_id,
                    UserRole.is_active == True
                )
            )
        ) > 0
    
    def _get_user_organizations(self, user_id: UserId) -> List[OrganizationId]:
        """Get user's organizations."""
        user_roles = self.db.scalars(
            select(UserRole).where(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.is_active == True
                )
            )
        ).all()
        
        return list(set(ur.organization_id for ur in user_roles))