"""Project repository implementation (stub for type checking)."""

from sqlalchemy.orm import Session


class ProjectRepository:
    """Project repository stub."""

    def __init__(self, db: Session):
        self.db = db

    def get_member_count(self, project_id: int) -> int:
        """Get number of project members."""
        return 0
