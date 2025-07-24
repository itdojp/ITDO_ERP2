"""Project service implementation (stub for type checking)."""

from typing import Any

from sqlalchemy.orm import Session

from app.models.project import Project
from app.types import UserId


class ProjectService:
    """Service for managing projects (stub implementation)."""

    def __init__(self, db: Session) -> dict:
        """Initialize service with database session."""
        self.db = db

    def get_project(self, project_id: int, user_id: UserId) -> Project | None:
        """Get a project by ID if user has access."""
        # Stub implementation
        return self.db.get(Project, project_id)

    def get_project_statistics(
        self, project_id: int, user_id: UserId
    ) -> dict[str, Any]:
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
            "is_overdue": False,
        }

    def get_total_budget(self, project_id: int) -> float:
        """Get total project budget."""
        return 0.0

    def get_budget_utilization(self, project_id: int) -> float:
        """Get budget utilization percentage."""
        return 0.0

    def list_projects(
        self,
        user_id: UserId,
        organization_id: int | None = None,
        department_id: int | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[Project], int]:
        """List projects with pagination."""
        # Stub implementation
        projects: list[Project] = []
        total = 0
        return projects, total

    def get_user_projects(self, user_id: UserId) -> list[Project]:
        """Get projects for a user."""
        # Stub implementation
        return []

    @property
    def repository(self) -> "ProjectRepository":
        """Get project repository."""
        # Return local repository instance
        return ProjectRepository(self.db)


class ProjectRepositoryLocal:
    """Local project repository stub for service."""

    def __init__(self, db: Session) -> dict:
        self.db = db

    def get_member_count(self, project_id: int) -> int:
        """Get number of project members."""
        return 0


# Type alias for backward compatibility
ProjectRepository = ProjectRepositoryLocal
