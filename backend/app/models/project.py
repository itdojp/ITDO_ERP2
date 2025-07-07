"""Project model implementation (stub for type checking)."""
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, ForeignKey, Float, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import SoftDeletableModel
from app.types import UserId, OrganizationId, DepartmentId

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.organization import Organization
    from app.models.department import Department


class Project(SoftDeletableModel):
    """Project model (stub implementation)."""
    
    __tablename__ = "projects"
    
    # Basic fields
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Foreign keys
    organization_id: Mapped[OrganizationId] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    department_id: Mapped[Optional[DepartmentId]] = mapped_column(
        Integer, ForeignKey("departments.id"), nullable=True
    )
    owner_id: Mapped[UserId] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    
    # Project details
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="planning")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    budget: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    start_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    planned_end_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    total_budget: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", lazy="joined")
    department: Mapped[Optional["Department"]] = relationship("Department", lazy="joined")
    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_id], lazy="joined")