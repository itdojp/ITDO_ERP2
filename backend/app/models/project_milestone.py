"""ProjectMilestone model implementation."""

from datetime import date
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, ForeignKey, Date, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import SoftDeletableModel

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.project_phase import ProjectPhase


class ProjectMilestone(SoftDeletableModel):
    """Project milestone model representing key checkpoints in a project."""
    
    __tablename__ = "project_milestones"
    __table_args__ = (
        Index('ix_project_milestones_due_date', 'due_date'),
        Index('ix_project_milestones_status', 'status'),
        Index('ix_project_milestones_critical', 'is_critical'),
    )
    
    # Foreign keys
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
        comment="Project ID"
    )
    phase_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("project_phases.id"),
        nullable=True,
        index=True,
        comment="Associated phase ID (optional)"
    )
    
    # Milestone details
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Milestone name"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Milestone description"
    )
    
    # Dates
    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Milestone due date"
    )
    completed_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Actual completion date"
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        comment="Milestone status (pending, completed, missed)"
    )
    
    # Critical path
    is_critical: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether this milestone is on the critical path"
    )
    
    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="milestones",
        lazy="joined"
    )
    phase: Mapped[Optional["ProjectPhase"]] = relationship(
        "ProjectPhase",
        back_populates="milestones",
        lazy="joined"
    )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<ProjectMilestone(id={self.id}, name='{self.name}', due_date={self.due_date}, status='{self.status}')>"
    
    @property
    def is_completed(self) -> bool:
        """Check if milestone is completed."""
        return self.status == "completed"
    
    @property
    def is_missed(self) -> bool:
        """Check if milestone is missed."""
        return self.status == "missed"
    
    @property
    def is_pending(self) -> bool:
        """Check if milestone is pending."""
        return self.status == "pending"
    
    @property
    def is_overdue(self) -> bool:
        """Check if milestone is overdue."""
        if self.status != "pending":
            return False
        
        from datetime import date as dt
        return dt.today() > self.due_date
    
    @property
    def days_until_due(self) -> int:
        """Get days until due date (negative if overdue)."""
        from datetime import date as dt
        delta = self.due_date - dt.today()
        return delta.days
    
    @property
    def completion_delay_days(self) -> Optional[int]:
        """Get completion delay in days (positive means late)."""
        if self.completed_date:
            delta = self.completed_date - self.due_date
            return delta.days
        return None
    
    @property
    def is_upcoming(self, days: int = 7) -> bool:
        """Check if milestone is upcoming within specified days."""
        if self.status != "pending":
            return False
        
        days_until = self.days_until_due
        return 0 <= days_until <= days
    
    def complete(self, completion_date: Optional[date] = None) -> None:
        """Mark milestone as completed."""
        if self.status != "pending":
            raise ValueError("Only pending milestones can be completed")
        
        from datetime import date as dt
        self.status = "completed"
        self.completed_date = completion_date or dt.today()
    
    def miss(self) -> None:
        """Mark milestone as missed."""
        if self.status != "pending":
            raise ValueError("Only pending milestones can be missed")
        
        if not self.is_overdue:
            raise ValueError("Milestone is not overdue yet")
        
        self.status = "missed"
    
    def update_status(self) -> None:
        """Update milestone status based on current date."""
        if self.status == "pending" and self.is_overdue:
            self.miss()
    
    def validate_dates(self) -> None:
        """Validate milestone dates."""
        # Validate against project dates
        if hasattr(self, 'project') and self.project:
            if self.project.planned_start_date and self.due_date < self.project.planned_start_date:
                raise ValueError("Milestone due date cannot be before project start date")
            
            if self.project.planned_end_date and self.due_date > self.project.planned_end_date:
                raise ValueError("Milestone due date cannot be after project end date")
        
        # Validate against phase dates if associated
        if hasattr(self, 'phase') and self.phase:
            if self.phase.planned_start_date and self.due_date < self.phase.planned_start_date:
                raise ValueError("Milestone due date cannot be before phase start date")
            
            if self.phase.planned_end_date and self.due_date > self.phase.planned_end_date:
                raise ValueError("Milestone due date cannot be after phase end date")
    
    def can_be_critical(self) -> bool:
        """Check if milestone can be marked as critical."""
        # A milestone is critical if delay would impact project end date
        if not hasattr(self, 'project') or not self.project:
            return True
        
        # If it's the last milestone before project end, it's critical
        later_milestones = self.project.milestones.filter(
            ProjectMilestone.due_date > self.due_date,
            ProjectMilestone.is_deleted == False
        ).count()
        
        return later_milestones == 0