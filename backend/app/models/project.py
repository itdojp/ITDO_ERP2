"""Project model."""

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, func, or_
from sqlalchemy.orm import Session, relationship

from app.core.database import Base
from app.core.exceptions import BusinessLogicError, NotFound


class Project(Base):
    """Project model."""
    
    __tablename__ = "projects"
    
    # Basic fields
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    status = Column(String(20), nullable=False, default="planning")
    
    # Date fields
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    actual_end_date = Column(Date)
    
    # Foreign keys
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    organization = relationship("Organization", back_populates="projects")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    deleter = relationship("User", foreign_keys=[deleted_by])
    tasks = relationship("Task", back_populates="project")
    
    # Valid status values
    VALID_STATUSES = ["planning", "in_progress", "completed", "cancelled", "on_hold"]
    
    @classmethod
    def create(
        cls,
        db: Session,
        *,
        name: str,
        start_date: date,
        organization_id: int,
        created_by: int,
        description: Optional[str] = None,
        end_date: Optional[date] = None,
        status: str = "planning",
        **kwargs
    ) -> "Project":
        """Create a new project."""
        # Validation
        cls._validate_project_data(name, status, start_date, end_date)
        cls._validate_organization_exists(db, organization_id)
        
        # Create project instance
        project = cls(
            name=name,
            description=description,
            status=status,
            start_date=start_date,
            end_date=end_date,
            organization_id=organization_id,
            created_by=created_by,
            **kwargs
        )
        
        # Add to database
        db.add(project)
        db.flush()
        
        return project
    
    def update(
        self,
        db: Session,
        updated_by: int,
        **kwargs
    ) -> None:
        """Update project attributes."""
        # Extract and validate data
        name = kwargs.get("name", self.name)
        status = kwargs.get("status", self.status)
        start_date = kwargs.get("start_date", self.start_date)
        end_date = kwargs.get("end_date", self.end_date)
        
        self._validate_project_data(name, status, start_date, end_date)
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(self, key) and key not in ["id", "created_at", "created_by"]:
                setattr(self, key, value)
        
        self.updated_by = updated_by
        db.add(self)
        db.flush()
    
    def update_status(self, status: str, updated_by: int) -> None:
        """Update project status."""
        if status not in self.VALID_STATUSES:
            raise BusinessLogicError("不正なステータスです")
        
        self.status = status
        self.updated_by = updated_by
    
    def complete(self, updated_by: int) -> None:
        """Complete the project."""
        self.status = "completed"
        self.actual_end_date = date.today()
        self.updated_by = updated_by
    
    def soft_delete(self, db: Session, deleted_by: int) -> None:
        """Soft delete the project."""
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by
        db.add(self)
        db.flush()
    
    @classmethod
    def get_active_projects(cls, db: Session, organization_id: int) -> List["Project"]:
        """Get active projects for an organization."""
        return db.query(cls).filter(
            cls.organization_id == organization_id,
            cls.deleted_at.is_(None)
        ).order_by(cls.created_at.desc()).all()
    
    @staticmethod
    def _validate_project_data(
        name: str,
        status: str,
        start_date: date,
        end_date: Optional[date]
    ) -> None:
        """Validate project data."""
        # Name validation
        if not name or not name.strip():
            raise BusinessLogicError("プロジェクト名は必須です")
        
        if len(name) > 100:
            raise BusinessLogicError("プロジェクト名は100文字以内で入力してください")
        
        # Status validation
        if status not in Project.VALID_STATUSES:
            raise BusinessLogicError("不正なステータスです")
        
        # Date validation
        if end_date and end_date < start_date:
            raise BusinessLogicError("終了日は開始日以降である必要があります")
    
    @staticmethod
    def _validate_organization_exists(db: Session, organization_id: int) -> None:
        """Validate organization exists."""
        from app.models.organization import Organization
        
        organization = db.query(Organization).filter(
            Organization.id == organization_id
        ).first()
        
        if not organization:
            raise BusinessLogicError("指定された組織が見つかりません")