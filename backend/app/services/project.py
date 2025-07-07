"""Project service implementation (stub for type checking)."""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.project import Project
from app.types import UserId


class ProjectService:
    """Service for managing projects (stub implementation)."""
    
    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
    
    def get_project(self, project_id: int, user_id: UserId) -> Optional[Project]:
        """Get a project by ID if user has access."""
        # Stub implementation
        return self.db.get(Project, project_id)
    
    def get_project_statistics(self, project_id: int, user_id: UserId) -> Dict[str, Any]:
        """Get project statistics."""
        # Stub implementation
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
            "is_overdue": False
        }