"""Project milestone model implementation (stub for type checking)."""
from typing import Optional
from sqlalchemy import Integer, ForeignKey, String, Date, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import SoftDeletableModel


class ProjectMilestone(SoftDeletableModel):
    """Project milestone model (stub implementation)."""
    
    __tablename__ = "project_milestones"
    
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    due_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    completion_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)