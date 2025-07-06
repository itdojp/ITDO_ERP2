"""ProjectPhase model implementation."""

from datetime import date
from typing import Optional, TYPE_CHECKING, List, Dict, Any
from sqlalchemy import String, Text, Integer, ForeignKey, Date, JSON, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import SoftDeletableModel

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.project_milestone import ProjectMilestone


class ProjectPhase(SoftDeletableModel):
    """Project phase model representing distinct phases within a project."""
    
    __tablename__ = "project_phases"
    __table_args__ = (
        UniqueConstraint('project_id', 'phase_order', name='uq_project_phase_order'),
        Index('ix_project_phases_status', 'status'),
        Index('ix_project_phases_dates', 'planned_start_date', 'planned_end_date'),
    )
    
    # Foreign key
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
        comment="Project ID"
    )
    
    # Phase details
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Phase name"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Phase description"
    )
    phase_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Phase order within the project"
    )
    
    # Schedule
    planned_start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Planned start date"
    )
    planned_end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Planned end date"
    )
    actual_start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Actual start date"
    )
    actual_end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Actual end date"
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="not_started",
        comment="Phase status (not_started, in_progress, completed, cancelled)"
    )
    
    # Deliverables
    deliverables: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="List of deliverables for this phase"
    )
    
    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="phases",
        lazy="joined"
    )
    milestones: Mapped[List["ProjectMilestone"]] = relationship(
        "ProjectMilestone",
        back_populates="phase",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="ProjectMilestone.due_date"
    )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<ProjectPhase(id={self.id}, name='{self.name}', order={self.phase_order}, status='{self.status}')>"
    
    @property
    def is_completed(self) -> bool:
        """Check if phase is completed."""
        return self.status == "completed"
    
    @property
    def is_in_progress(self) -> bool:
        """Check if phase is in progress."""
        return self.status == "in_progress"
    
    @property
    def is_overdue(self) -> bool:
        """Check if phase is overdue."""
        if self.status in ["completed", "cancelled"]:
            return False
        if self.planned_end_date:
            from datetime import date as dt
            return dt.today() > self.planned_end_date
        return False
    
    @property
    def progress_percentage(self) -> int:
        """Get phase progress percentage based on status."""
        status_progress = {
            "not_started": 0,
            "in_progress": 50,
            "completed": 100,
            "cancelled": 0
        }
        return status_progress.get(self.status, 0)
    
    @property
    def duration_days(self) -> Optional[int]:
        """Get phase duration in days."""
        if self.planned_start_date and self.planned_end_date:
            delta = self.planned_end_date - self.planned_start_date
            return delta.days
        return None
    
    @property
    def actual_duration_days(self) -> Optional[int]:
        """Get actual phase duration in days."""
        if self.actual_start_date and self.actual_end_date:
            delta = self.actual_end_date - self.actual_start_date
            return delta.days
        return None
    
    @property
    def days_remaining(self) -> Optional[int]:
        """Get days remaining until planned end date."""
        if self.planned_end_date and self.status not in ["completed", "cancelled"]:
            from datetime import date as dt
            delta = self.planned_end_date - dt.today()
            return delta.days
        return None
    
    @property
    def deliverable_count(self) -> int:
        """Get number of deliverables."""
        return len(self.deliverables)
    
    @property
    def completed_deliverable_count(self) -> int:
        """Get number of completed deliverables."""
        return sum(1 for d in self.deliverables if isinstance(d, dict) and d.get('completed', False))
    
    @property
    def deliverable_completion_percentage(self) -> float:
        """Get deliverable completion percentage."""
        if not self.deliverables:
            return 0.0
        return (self.completed_deliverable_count / self.deliverable_count) * 100
    
    def validate_dates(self) -> None:
        """Validate phase dates."""
        if self.planned_start_date and self.planned_end_date:
            if self.planned_start_date > self.planned_end_date:
                raise ValueError("Planned end date must be after planned start date")
        
        if self.actual_start_date and self.actual_end_date:
            if self.actual_start_date > self.actual_end_date:
                raise ValueError("Actual end date must be after actual start date")
        
        # Validate against project dates
        if hasattr(self, 'project') and self.project:
            if self.project.planned_start_date and self.planned_start_date:
                if self.planned_start_date < self.project.planned_start_date:
                    raise ValueError("Phase cannot start before project start date")
            
            if self.project.planned_end_date and self.planned_end_date:
                if self.planned_end_date > self.project.planned_end_date:
                    raise ValueError("Phase cannot end after project end date")
    
    def can_start(self) -> bool:
        """Check if phase can be started."""
        if self.status != "not_started":
            return False
        
        # Check if previous phases are completed
        if hasattr(self, 'project') and self.project:
            previous_phases = self.project.phases.filter(
                ProjectPhase.phase_order < self.phase_order,
                ProjectPhase.is_deleted == False
            ).all()
            
            for phase in previous_phases:
                if phase.status not in ["completed", "cancelled"]:
                    return False
        
        return True
    
    def start(self) -> None:
        """Start the phase."""
        if not self.can_start():
            raise ValueError("Phase cannot be started")
        
        from datetime import date as dt
        self.status = "in_progress"
        if not self.actual_start_date:
            self.actual_start_date = dt.today()
    
    def complete(self) -> None:
        """Complete the phase."""
        if self.status != "in_progress":
            raise ValueError("Only in-progress phases can be completed")
        
        from datetime import date as dt
        self.status = "completed"
        if not self.actual_end_date:
            self.actual_end_date = dt.today()
    
    def cancel(self) -> None:
        """Cancel the phase."""
        if self.status == "completed":
            raise ValueError("Completed phases cannot be cancelled")
        
        self.status = "cancelled"