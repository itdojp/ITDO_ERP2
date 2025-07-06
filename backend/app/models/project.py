"""Project model implementation with type safety."""

from datetime import date
from decimal import Decimal
from typing import Optional, TYPE_CHECKING, List, Dict, Any
from sqlalchemy import String, Text, Integer, ForeignKey, Date, Numeric, JSON, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import SoftDeletableModel
from app.types import OrganizationId, DepartmentId, UserId

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.department import Department
    from app.models.user import User
    from app.models.project_member import ProjectMember
    from app.models.project_phase import ProjectPhase
    from app.models.project_milestone import ProjectMilestone


class Project(SoftDeletableModel):
    """Project model representing a project within an organization."""
    
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint('organization_id', 'code', name='uq_project_org_code'),
        Index('ix_projects_status', 'status'),
        Index('ix_projects_priority', 'priority'),
        Index('ix_projects_planned_dates', 'planned_start_date', 'planned_end_date'),
    )
    
    # Basic fields
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Project code (unique within organization)"
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Project name"
    )
    name_en: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Project name in English"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Project description"
    )
    
    # Organization and department
    organization_id: Mapped[OrganizationId] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
        comment="Organization this project belongs to"
    )
    department_id: Mapped[Optional[DepartmentId]] = mapped_column(
        Integer,
        ForeignKey("departments.id"),
        nullable=True,
        index=True,
        comment="Primary department responsible for the project"
    )
    
    # Project details
    project_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="general",
        comment="Type of project (general, development, research, etc.)"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="planning",
        comment="Project status (planning, in_progress, completed, cancelled, on_hold)"
    )
    priority: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="medium",
        comment="Project priority (low, medium, high, urgent)"
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
    
    # Budget and cost
    budget: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="Project budget"
    )
    actual_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="Actual cost incurred"
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="JPY",
        comment="Currency code (ISO 4217)"
    )
    
    # Progress
    progress_percentage: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Progress percentage (0-100)"
    )
    
    # Hierarchy
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("projects.id"),
        nullable=True,
        index=True,
        comment="Parent project ID for sub-projects"
    )
    
    # Responsibility
    project_manager_id: Mapped[Optional[UserId]] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="Project manager user ID"
    )
    
    # Metadata
    tags: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="Project tags"
    )
    custom_fields: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="Custom fields for flexibility"
    )
    
    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="joined"
    )
    department: Mapped[Optional["Department"]] = relationship(
        "Department",
        lazy="joined"
    )
    project_manager: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[project_manager_id],
        lazy="joined"
    )
    parent: Mapped[Optional["Project"]] = relationship(
        "Project",
        remote_side=[id],
        backref="sub_projects",
        lazy="joined"
    )
    members: Mapped[List["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    phases: Mapped[List["ProjectPhase"]] = relationship(
        "ProjectPhase",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="ProjectPhase.phase_order"
    )
    milestones: Mapped[List["ProjectMilestone"]] = relationship(
        "ProjectMilestone",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="ProjectMilestone.due_date"
    )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<Project(id={self.id}, code='{self.code}', name='{self.name}', status='{self.status}')>"
    
    @property
    def full_code(self) -> str:
        """Get full project code including organization code."""
        return f"{self.organization.code}-{self.code}"
    
    @property
    def is_sub_project(self) -> bool:
        """Check if this is a sub-project."""
        return self.parent_id is not None
    
    @property
    def is_parent_project(self) -> bool:
        """Check if this project has sub-projects."""
        return len(self.sub_projects) > 0
    
    @property
    def is_overdue(self) -> bool:
        """Check if project is overdue."""
        if self.status in ["completed", "cancelled"]:
            return False
        if self.planned_end_date:
            from datetime import date as dt
            return dt.today() > self.planned_end_date
        return False
    
    @property
    def is_over_budget(self) -> bool:
        """Check if project is over budget."""
        if self.budget and self.actual_cost:
            return self.actual_cost > self.budget
        return False
    
    @property
    def budget_usage_percentage(self) -> Optional[float]:
        """Get budget usage percentage."""
        if self.budget and self.budget > 0:
            if self.actual_cost:
                return float((self.actual_cost / self.budget) * 100)
            return 0.0
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
    def duration_days(self) -> Optional[int]:
        """Get project duration in days."""
        if self.planned_start_date and self.planned_end_date:
            delta = self.planned_end_date - self.planned_start_date
            return delta.days
        return None
    
    def get_all_sub_projects(self) -> List["Project"]:
        """Get all sub-projects recursively."""
        result = []
        for sub_project in self.sub_projects:
            result.append(sub_project)
            result.extend(sub_project.get_all_sub_projects())
        return result
    
    def get_hierarchy_path(self) -> List["Project"]:
        """Get the full hierarchy path from root to this project."""
        path = [self]
        current = self
        while current.parent:
            path.insert(0, current.parent)
            current = current.parent
        return path
    
    def calculate_progress_from_phases(self) -> int:
        """Calculate progress based on phase completion."""
        if not self.phases.count():
            return self.progress_percentage
        
        total_weight = 0
        weighted_progress = 0
        
        for phase in self.phases.filter_by(is_deleted=False).all():
            # Assume equal weight for simplicity
            weight = 100 / self.phases.count()
            total_weight += weight
            
            if phase.status == "completed":
                weighted_progress += weight
            elif phase.status == "in_progress":
                # Assume 50% completion for in-progress phases
                weighted_progress += weight * 0.5
        
        return int(weighted_progress)
    
    def update_progress(self) -> None:
        """Update project progress based on phases or sub-projects."""
        if self.phases.count() > 0:
            self.progress_percentage = self.calculate_progress_from_phases()
        elif self.sub_projects:
            # Calculate from sub-projects
            total_progress = sum(sp.progress_percentage for sp in self.sub_projects)
            self.progress_percentage = int(total_progress / len(self.sub_projects))
    
    def can_be_deleted(self) -> bool:
        """Check if project can be deleted."""
        # Cannot delete if has active sub-projects
        if any(sp.status != "cancelled" for sp in self.sub_projects):
            return False
        # Cannot delete if in progress
        if self.status == "in_progress":
            return False
        return True
    
    def validate_dates(self) -> None:
        """Validate project dates."""
        if self.planned_start_date and self.planned_end_date:
            if self.planned_start_date > self.planned_end_date:
                raise ValueError("Planned end date must be after planned start date")
        
        if self.actual_start_date and self.actual_end_date:
            if self.actual_start_date > self.actual_end_date:
                raise ValueError("Actual end date must be after actual start date")
        
        # Validate against parent project dates
        if self.parent:
            if self.planned_start_date and self.parent.planned_start_date:
                if self.planned_start_date < self.parent.planned_start_date:
                    raise ValueError("Sub-project cannot start before parent project")
            
            if self.planned_end_date and self.parent.planned_end_date:
                if self.planned_end_date > self.parent.planned_end_date:
                    raise ValueError("Sub-project cannot end after parent project")
    
    def validate_budget(self) -> None:
        """Validate project budget."""
        if self.budget is not None and self.budget < 0:
            raise ValueError("Budget cannot be negative")
        
        if self.actual_cost is not None and self.actual_cost < 0:
            raise ValueError("Actual cost cannot be negative")
    
    def validate_progress(self) -> None:
        """Validate progress percentage."""
        if self.progress_percentage < 0 or self.progress_percentage > 100:
            raise ValueError("Progress percentage must be between 0 and 100")