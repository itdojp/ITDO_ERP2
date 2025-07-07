"""Project member model implementation (stub for type checking)."""
from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditableModel
from app.types import UserId


class ProjectMember(AuditableModel):
    """Project member model (stub implementation)."""

    __tablename__ = "project_members"

    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=False
    )
    user_id: Mapped[UserId] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="member")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
