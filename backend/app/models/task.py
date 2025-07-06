"""Task model."""

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import Session, relationship

from app.core.database import Base
from app.core.exceptions import BusinessLogicError


class Task(Base):
    """Task model."""
    
    __tablename__ = "tasks"
    
    # Basic fields
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(20), nullable=False, default="not_started")
    priority = Column(String(20), nullable=False, default="medium")
    
    # Date fields
    estimated_start_date = Column(Date)
    estimated_end_date = Column(Date)
    actual_start_date = Column(Date)
    actual_end_date = Column(Date)
    
    # Foreign keys
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assigned_to])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    deleter = relationship("User", foreign_keys=[deleted_by])
    
    # Valid values
    VALID_STATUSES = ["not_started", "in_progress", "completed", "on_hold"]
    VALID_PRIORITIES = ["low", "medium", "high", "urgent"]
    
    @classmethod
    def create(
        cls,
        db: Session,
        *,
        title: str,
        project_id: int,
        created_by: int,
        description: Optional[str] = None,
        status: str = "not_started",
        priority: str = "medium",
        assigned_to: Optional[int] = None,
        estimated_start_date: Optional[date] = None,
        estimated_end_date: Optional[date] = None,
        **kwargs
    ) -> "Task":
        """Create a new task."""
        # Validation
        cls._validate_task_data(title, status, priority, estimated_start_date, estimated_end_date)
        cls._validate_project_exists(db, project_id)
        
        # Create task instance
        task = cls(
            title=title,
            description=description,
            status=status,
            priority=priority,
            project_id=project_id,
            assigned_to=assigned_to,
            estimated_start_date=estimated_start_date,
            estimated_end_date=estimated_end_date,
            created_by=created_by,
            **kwargs
        )
        
        # Add to database
        db.add(task)
        db.flush()
        
        return task
    
    def update(
        self,
        db: Session,
        updated_by: int,
        **kwargs
    ) -> None:
        """Update task attributes."""
        # Extract and validate data
        title = kwargs.get("title", self.title)
        status = kwargs.get("status", self.status)
        priority = kwargs.get("priority", self.priority)
        estimated_start_date = kwargs.get("estimated_start_date", self.estimated_start_date)
        estimated_end_date = kwargs.get("estimated_end_date", self.estimated_end_date)
        
        self._validate_task_data(title, status, priority, estimated_start_date, estimated_end_date)
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(self, key) and key not in ["id", "created_at", "created_by"]:
                setattr(self, key, value)
        
        self.updated_by = updated_by
        db.add(self)
        db.flush()
    
    def start_task(self, updated_by: int) -> None:
        """Start the task."""
        self.status = "in_progress"
        self.actual_start_date = date.today()
        self.updated_by = updated_by
    
    def complete_task(self, updated_by: int) -> None:
        """Complete the task."""
        self.status = "completed"
        self.actual_end_date = date.today()
        self.updated_by = updated_by
    
    def soft_delete(self, db: Session, deleted_by: int) -> None:
        """Soft delete the task."""
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by
        db.add(self)
        db.flush()
    
    @classmethod
    def get_by_project(cls, db: Session, project_id: int) -> List["Task"]:
        """Get tasks for a project."""
        return db.query(cls).filter(
            cls.project_id == project_id,
            cls.deleted_at.is_(None)
        ).order_by(cls.created_at.desc()).all()
    
    @staticmethod
    def _validate_task_data(
        title: str,
        status: str,
        priority: str,
        estimated_start_date: Optional[date],
        estimated_end_date: Optional[date]
    ) -> None:
        """Validate task data."""
        # Title validation
        if not title or not title.strip():
            raise BusinessLogicError("タスクタイトルは必須です")
        
        if len(title) > 200:
            raise BusinessLogicError("タスクタイトルは200文字以内で入力してください")
        
        # Status validation
        if status not in Task.VALID_STATUSES:
            raise BusinessLogicError("不正なステータスです")
        
        # Priority validation
        if priority not in Task.VALID_PRIORITIES:
            raise BusinessLogicError("不正な優先度です")
        
        # Date validation
        if (estimated_start_date and estimated_end_date and 
            estimated_end_date < estimated_start_date):
            raise BusinessLogicError("終了予定日は開始予定日以降である必要があります")
    
    @staticmethod
    def _validate_project_exists(db: Session, project_id: int) -> None:
        """Validate project exists."""
        from app.models.project import Project
        
        project = db.query(Project).filter(
            Project.id == project_id
        ).first()
        
        if not project:
            raise BusinessLogicError("指定されたプロジェクトが見つかりません")