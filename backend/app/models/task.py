"""Task model for project task management."""

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class TaskStatus(str, Enum):
    """Task status enumeration."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class TaskPriority(str, Enum):
    """Task priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class DependencyType(str, Enum):
    """Task dependency type enumeration."""

    BLOCKS = "blocks"  # This task blocks the dependent task
    DEPENDS_ON = "depends_on"  # This task depends on another task
    RELATES_TO = "relates_to"  # Loose relationship


class Task(SoftDeletableModel):
    """Task model for project task management."""

    __tablename__ = "tasks"

    # Basic task information
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status and priority
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus), nullable=False, default=TaskStatus.TODO, index=True
    )
    priority: Mapped[TaskPriority] = mapped_column(
        SQLEnum(TaskPriority), nullable=False, default=TaskPriority.MEDIUM, index=True
    )

    # Relationships - Foreign Keys
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=False, index=True
    )
    assigned_to: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    # Time tracking
    estimated_hours: Mapped[Optional[float]] = mapped_column(nullable=True)
    actual_hours: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Dates
    start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Progress tracking
    progress_percentage: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # Tags for categorization
    tags: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    assignee: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[assigned_to], back_populates="assigned_tasks"
    )
    creator: Mapped["User"] = relationship(
        "User", foreign_keys=[created_by], back_populates="created_tasks"
    )
    
    # Task dependencies (self-referential many-to-many)
    dependencies: Mapped[List["TaskDependency"]] = relationship(
        "TaskDependency", 
        foreign_keys="TaskDependency.task_id",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    dependent_tasks: Mapped[List["TaskDependency"]] = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.depends_on_task_id", 
        back_populates="depends_on_task"
    )

    # Task history/audit
    task_history: Mapped[List["TaskHistory"]] = relationship(
        "TaskHistory", back_populates="task", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if not self.due_date or self.status == TaskStatus.COMPLETED:
            return False
        return datetime.now(timezone.utc) > self.due_date

    @property
    def is_blocked(self) -> bool:
        """Check if task is blocked by dependencies."""
        return self.status == TaskStatus.BLOCKED or any(
            dep.depends_on_task.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]
            for dep in self.dependencies
            if dep.dependency_type == DependencyType.DEPENDS_ON
        )

    @property
    def blocking_tasks(self) -> List["Task"]:
        """Get tasks that this task blocks."""
        return [
            dep.task for dep in self.dependent_tasks
            if dep.dependency_type == DependencyType.BLOCKS
        ]

    @property
    def dependent_on_tasks(self) -> List["Task"]:
        """Get tasks that this task depends on."""
        return [
            dep.depends_on_task for dep in self.dependencies
            if dep.dependency_type == DependencyType.DEPENDS_ON
        ]

    def can_start(self) -> bool:
        """Check if task can be started (no blocking dependencies)."""
        if self.status != TaskStatus.TODO:
            return False
        
        blocking_deps = [
            dep for dep in self.dependencies
            if dep.dependency_type == DependencyType.DEPENDS_ON
        ]
        
        return all(
            dep.depends_on_task.status == TaskStatus.COMPLETED
            for dep in blocking_deps
        )

    def complete_task(self, completed_by: int) -> None:
        """Mark task as completed."""
        if self.status == TaskStatus.COMPLETED:
            return
            
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.progress_percentage = 100
        
        # Record in history
        self._add_history_entry(
            "task_completed",
            {"completed_by": completed_by},
            completed_by
        )

    def assign_task(self, assignee_id: int, assigned_by: int) -> None:
        """Assign task to a user."""
        old_assignee = self.assigned_to
        self.assigned_to = assignee_id
        
        # Record in history
        self._add_history_entry(
            "task_assigned",
            {
                "old_assignee": old_assignee,
                "new_assignee": assignee_id,
                "assigned_by": assigned_by
            },
            assigned_by
        )

    def update_status(self, new_status: TaskStatus, updated_by: int) -> None:
        """Update task status with validation."""
        if not self._validate_status_transition(self.status, new_status):
            raise ValueError(f"Invalid status transition from {self.status} to {new_status}")
        
        old_status = self.status
        self.status = new_status
        
        # Auto-update completion time
        if new_status == TaskStatus.COMPLETED:
            self.completed_at = datetime.now(timezone.utc)
            self.progress_percentage = 100
        elif old_status == TaskStatus.COMPLETED:
            self.completed_at = None
        
        # Record in history
        self._add_history_entry(
            "status_changed",
            {
                "old_status": old_status.value,
                "new_status": new_status.value
            },
            updated_by
        )

    def update_progress(self, percentage: int, updated_by: int) -> None:
        """Update task progress percentage."""
        if not 0 <= percentage <= 100:
            raise ValueError("Progress percentage must be between 0 and 100")
        
        old_progress = self.progress_percentage
        self.progress_percentage = percentage
        
        # Auto-update status based on progress
        if percentage == 100 and self.status != TaskStatus.COMPLETED:
            self.status = TaskStatus.COMPLETED
            self.completed_at = datetime.now(timezone.utc)
        elif percentage > 0 and self.status == TaskStatus.TODO:
            self.status = TaskStatus.IN_PROGRESS
        
        # Record in history
        self._add_history_entry(
            "progress_updated",
            {
                "old_progress": old_progress,
                "new_progress": percentage
            },
            updated_by
        )

    def add_dependency(
        self, 
        depends_on_task_id: int, 
        dependency_type: DependencyType,
        created_by: int
    ) -> "TaskDependency":
        """Add a dependency to another task."""
        # Prevent self-dependency
        if depends_on_task_id == self.id:
            raise ValueError("Task cannot depend on itself")
        
        # Check for circular dependencies (simplified check)
        if self._would_create_circular_dependency(depends_on_task_id):
            raise ValueError("Circular dependency detected")
        
        # Create dependency
        dependency = TaskDependency(
            task_id=self.id,
            depends_on_task_id=depends_on_task_id,
            dependency_type=dependency_type,
            created_by=created_by
        )
        
        self.dependencies.append(dependency)
        
        # Record in history
        self._add_history_entry(
            "dependency_added",
            {
                "depends_on_task_id": depends_on_task_id,
                "dependency_type": dependency_type.value
            },
            created_by
        )
        
        return dependency

    def get_tags_list(self) -> List[str]:
        """Get tags as a list."""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]

    def set_tags(self, tags: List[str]) -> None:
        """Set tags from a list."""
        self.tags = ", ".join(tags) if tags else None

    def _validate_status_transition(
        self, 
        from_status: TaskStatus, 
        to_status: TaskStatus
    ) -> bool:
        """Validate if status transition is allowed."""
        # Define allowed transitions
        allowed_transitions = {
            TaskStatus.TODO: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
            TaskStatus.IN_PROGRESS: [
                TaskStatus.TODO, TaskStatus.IN_REVIEW, 
                TaskStatus.COMPLETED, TaskStatus.BLOCKED, TaskStatus.CANCELLED
            ],
            TaskStatus.IN_REVIEW: [
                TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED, TaskStatus.CANCELLED
            ],
            TaskStatus.COMPLETED: [TaskStatus.IN_PROGRESS],  # Reopen
            TaskStatus.CANCELLED: [TaskStatus.TODO, TaskStatus.IN_PROGRESS],
            TaskStatus.BLOCKED: [
                TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED
            ],
        }
        
        return to_status in allowed_transitions.get(from_status, [])

    def _would_create_circular_dependency(self, depends_on_task_id: int) -> bool:
        """Check if adding dependency would create circular dependency."""
        # Simple implementation - could be enhanced with graph traversal
        # For now, just check direct circular dependency
        existing_deps = [dep.depends_on_task_id for dep in self.dependencies]
        
        # If the task we want to depend on already depends on this task
        return self.id in existing_deps or depends_on_task_id in existing_deps

    def _add_history_entry(
        self, 
        action: str, 
        details: Dict[str, Any], 
        user_id: int
    ) -> None:
        """Add entry to task history."""
        history_entry = TaskHistory(
            task_id=self.id,
            action=action,
            details=details,
            changed_by=user_id,
            changed_at=datetime.now(timezone.utc)
        )
        self.task_history.append(history_entry)


class TaskDependency(SoftDeletableModel):
    """Task dependency relationship model."""

    __tablename__ = "task_dependencies"

    # The task that has the dependency
    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tasks.id"), nullable=False, index=True
    )
    
    # The task that this task depends on
    depends_on_task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tasks.id"), nullable=False, index=True
    )
    
    # Type of dependency
    dependency_type: Mapped[DependencyType] = mapped_column(
        SQLEnum(DependencyType), nullable=False, default=DependencyType.DEPENDS_ON
    )
    
    # Who created this dependency
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )

    # Relationships
    task: Mapped["Task"] = relationship(
        "Task", foreign_keys=[task_id], back_populates="dependencies"
    )
    depends_on_task: Mapped["Task"] = relationship(
        "Task", foreign_keys=[depends_on_task_id], back_populates="dependent_tasks"
    )
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        """String representation."""
        return f"<TaskDependency(task_id={self.task_id}, depends_on={self.depends_on_task_id}, type={self.dependency_type})>"


class TaskHistory(SoftDeletableModel):
    """Task history/audit log model."""

    __tablename__ = "task_history"

    # The task this history entry belongs to
    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tasks.id"), nullable=False, index=True
    )
    
    # Action performed
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Detailed information about the change (JSON)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Who made the change
    changed_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    
    # When the change was made
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), index=True
    )

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="task_history")
    user: Mapped["User"] = relationship("User", foreign_keys=[changed_by])

    def __repr__(self) -> str:
        """String representation."""
        return f"<TaskHistory(task_id={self.task_id}, action='{self.action}', changed_by={self.changed_by})>"