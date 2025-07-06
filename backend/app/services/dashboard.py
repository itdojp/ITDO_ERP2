"""Dashboard service for statistics and analytics."""

from typing import Dict, Any, Optional, List
from datetime import datetime, date
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.exceptions import NotFound, PermissionDenied
from app.schemas.dashboard import (
    DashboardStatsResponse,
    ProgressDataResponse,
    AlertsResponse
)


class DashboardService:
    """Service for dashboard functionality."""

    def __init__(self):
        """Initialize dashboard service."""
        pass

    def get_dashboard_stats(
        self,
        user: User,
        db: Session,
        organization_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get dashboard statistics.
        
        Args:
            user: Current user
            db: Database session
            organization_id: Optional organization filter
            
        Returns:
            Dashboard statistics data
        """
        # Check permissions
        if organization_id and not user.is_superuser:
            # Regular users can only access their own organization data
            user_org_ids = self._get_user_organization_ids(user, db)
            if organization_id not in user_org_ids:
                raise PermissionDenied("組織へのアクセス権限がありません")
        
        # Get organization ID for filtering
        target_org_id = organization_id if organization_id else self._get_default_organization_id(user, db)
        
        # Calculate project statistics
        project_stats = self._calculate_project_stats(target_org_id, db)
        
        # Calculate task statistics
        task_stats = self._calculate_task_stats(target_org_id, db)
        
        # Get recent activity
        recent_activity = self._get_recent_activity(target_org_id, db)
        
        return {
            "project_stats": project_stats,
            "task_stats": task_stats,
            "recent_activity": recent_activity
        }

    def get_progress_data(
        self,
        user: User,
        db: Session,
        period: str = "month",
        organization_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get progress data.
        
        Args:
            user: Current user
            db: Database session
            period: Time period (week/month/quarter)
            organization_id: Optional organization filter
            
        Returns:
            Progress data
        """
        # Check permissions
        if organization_id and not user.is_superuser:
            user_org_ids = self._get_user_organization_ids(user, db)
            if organization_id not in user_org_ids:
                raise PermissionDenied("組織へのアクセス権限がありません")
        
        # Get organization ID for filtering
        target_org_id = organization_id if organization_id else self._get_default_organization_id(user, db)
        
        # Calculate progress data based on period
        progress_data = self._calculate_progress_data(target_org_id, period, db)
        
        # Get project progress details
        project_progress = self._get_project_progress_details(target_org_id, db)
        
        return {
            "period": period,
            "progress_data": progress_data,
            "project_progress": project_progress
        }

    def get_alerts(
        self,
        user: User,
        db: Session,
        organization_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get dashboard alerts.
        
        Args:
            user: Current user
            db: Database session
            organization_id: Optional organization filter
            
        Returns:
            Alert data
        """
        # Check permissions
        if organization_id and not user.is_superuser:
            user_org_ids = self._get_user_organization_ids(user, db)
            if organization_id not in user_org_ids:
                raise PermissionDenied("組織へのアクセス権限がありません")
        
        # Get organization ID for filtering
        target_org_id = organization_id if organization_id else self._get_default_organization_id(user, db)
        
        # Get overdue projects
        overdue_projects = self._get_overdue_projects(target_org_id, db)
        
        # Get overdue tasks
        overdue_tasks = self._get_overdue_tasks(target_org_id, db)
        
        # Get upcoming deadlines
        upcoming_deadlines = self._get_upcoming_deadlines(target_org_id, db)
        
        return {
            "overdue_projects": overdue_projects,
            "overdue_tasks": overdue_tasks,
            "upcoming_deadlines": upcoming_deadlines
        }

    def calculate_project_progress(
        self,
        project_id: int,
        db: Session
    ) -> float:
        """Calculate project progress percentage.
        
        Args:
            project_id: Project ID
            db: Database session
            
        Returns:
            Progress percentage (0.0 to 100.0)
        """
        # For now, return a mock progress calculation
        # In real implementation, this would query the database
        # and calculate based on completed tasks vs total tasks
        
        # Mock calculation - would be replaced with actual database queries
        total_tasks = 20  # Would come from database
        completed_tasks = 15  # Would come from database
        
        if total_tasks == 0:
            return 0.0
        
        progress = (completed_tasks / total_tasks) * 100.0
        return round(progress, 2)

    # Private helper methods
    
    def _get_user_organization_ids(self, user: User, db: Session) -> List[int]:
        """Get organization IDs that user has access to."""
        # Mock implementation - would query user's organizations
        return [1]  # User belongs to organization 1
    
    def _get_default_organization_id(self, user: User, db: Session) -> int:
        """Get user's default organization ID."""
        # Mock implementation - would get user's primary organization
        return 1
    
    def _calculate_project_stats(self, organization_id: int, db: Session) -> Dict[str, int]:
        """Calculate project statistics for organization."""
        # Mock implementation - would query projects table
        return {
            "total": 25,
            "planning": 5,
            "in_progress": 15,
            "completed": 5,
            "overdue": 3
        }
    
    def _calculate_task_stats(self, organization_id: int, db: Session) -> Dict[str, int]:
        """Calculate task statistics for organization."""
        # Mock implementation - would query tasks table
        return {
            "total": 150,
            "not_started": 30,
            "in_progress": 80,
            "completed": 35,
            "on_hold": 5,
            "overdue": 12
        }
    
    def _get_recent_activity(self, organization_id: int, db: Session) -> List[Dict[str, Any]]:
        """Get recent activity for organization."""
        # Mock implementation - would query activity log
        return []
    
    def _calculate_progress_data(self, organization_id: int, period: str, db: Session) -> List[Dict[str, Any]]:
        """Calculate progress data for period."""
        # Mock implementation - would calculate based on period
        return [
            {
                "date": "2025-07-01",
                "completed_projects": 2,
                "completed_tasks": 15,
                "total_progress": 65.5
            }
        ]
    
    def _get_project_progress_details(self, organization_id: int, db: Session) -> List[Dict[str, Any]]:
        """Get detailed project progress."""
        # Mock implementation - would query project progress
        return [
            {
                "project_id": 1,
                "project_name": "プロジェクトA",
                "completion_percentage": 75.0,
                "total_tasks": 20,
                "completed_tasks": 15,
                "is_overdue": False
            }
        ]
    
    def _get_overdue_projects(self, organization_id: int, db: Session) -> List[Dict[str, Any]]:
        """Get overdue projects."""
        # Mock implementation - would query overdue projects
        return [
            {
                "project_id": 5,
                "project_name": "遅延プロジェクト",
                "end_date": "2025-07-01",
                "days_overdue": 5
            }
        ]
    
    def _get_overdue_tasks(self, organization_id: int, db: Session) -> List[Dict[str, Any]]:
        """Get overdue tasks."""
        # Mock implementation - would query overdue tasks
        return []
    
    def _get_upcoming_deadlines(self, organization_id: int, db: Session) -> List[Dict[str, Any]]:
        """Get upcoming deadlines."""
        # Mock implementation - would query upcoming deadlines
        return []