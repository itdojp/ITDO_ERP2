"""ProjectMember model implementation."""

from datetime import date
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, ForeignKey, Date, Boolean, UniqueConstraint, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import AuditableModel
from app.types import UserId

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class ProjectMember(AuditableModel):
    """Project member model representing user assignments to projects."""
    
    __tablename__ = "project_members"
    __table_args__ = (
        UniqueConstraint('project_id', 'user_id', 'start_date', name='uq_project_member'),
        Index('ix_project_members_active', 'is_active'),
        Index('ix_project_members_dates', 'start_date', 'end_date'),
        CheckConstraint('allocation_percentage >= 0 AND allocation_percentage <= 100', 
                       name='ck_allocation_percentage'),
    )
    
    # Foreign keys
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
        comment="Project ID"
    )
    user_id: Mapped[UserId] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="User ID"
    )
    
    # Member details
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Role in the project (developer, designer, analyst, etc.)"
    )
    allocation_percentage: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        comment="Allocation percentage (0-100)"
    )
    
    # Period
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Assignment start date"
    )
    end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Assignment end date"
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether the assignment is active"
    )
    
    # Additional information
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Notes about the assignment"
    )
    
    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="members",
        lazy="joined"
    )
    user: Mapped["User"] = relationship(
        "User",
        lazy="joined"
    )
    
    def __repr__(self) -> str:
        """String representation."""
        return (f"<ProjectMember(project_id={self.project_id}, user_id={self.user_id}, "
                f"role='{self.role}', allocation={self.allocation_percentage}%)>")
    
    @property
    def is_current(self) -> bool:
        """Check if assignment is currently active."""
        if not self.is_active:
            return False
        
        from datetime import date as dt
        today = dt.today()
        
        if self.start_date > today:
            return False
        
        if self.end_date and self.end_date < today:
            return False
        
        return True
    
    @property
    def days_remaining(self) -> Optional[int]:
        """Get days remaining in assignment."""
        if not self.end_date or not self.is_current:
            return None
        
        from datetime import date as dt
        delta = self.end_date - dt.today()
        return max(0, delta.days)
    
    @property
    def assignment_duration(self) -> Optional[int]:
        """Get total assignment duration in days."""
        if self.end_date:
            delta = self.end_date - self.start_date
            return delta.days
        return None
    
    def validate_dates(self) -> None:
        """Validate assignment dates."""
        if self.end_date and self.start_date > self.end_date:
            raise ValueError("End date must be after start date")
        
        # Validate against project dates
        if hasattr(self, 'project') and self.project:
            if self.project.planned_start_date and self.start_date < self.project.planned_start_date:
                raise ValueError("Assignment cannot start before project start date")
            
            if self.project.planned_end_date and self.end_date and self.end_date > self.project.planned_end_date:
                raise ValueError("Assignment cannot end after project end date")
    
    def validate_allocation(self) -> None:
        """Validate allocation percentage."""
        if self.allocation_percentage < 0 or self.allocation_percentage > 100:
            raise ValueError("Allocation percentage must be between 0 and 100")
    
    def can_overlap_with(self, other: "ProjectMember") -> bool:
        """Check if this assignment can overlap with another."""
        # Same user on different projects
        if self.user_id != other.user_id:
            return True
        
        # Same project
        if self.project_id == other.project_id:
            return False
        
        # Check date overlap
        if self.end_date and other.start_date > self.end_date:
            return True
        
        if other.end_date and self.start_date > other.end_date:
            return True
        
        # Check if total allocation exceeds 100%
        return (self.allocation_percentage + other.allocation_percentage) <= 100