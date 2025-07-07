"""Base model implementation for ITDO ERP System.

This module provides base model classes with common functionality for all database models.
"""
from typing import Any, Dict, List, Optional, TypeVar, Generic, Type, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Integer, DateTime, Boolean, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr, DeclarativeBase
from app.types import UserId, AuditableProtocol, SoftDeletableProtocol

if TYPE_CHECKING:
    from app.models.user import User

# Create base class for all models using SQLAlchemy 2.0 style
class Base(DeclarativeBase):
    """Base class for all models."""
    pass

# Type variable for model types
ModelType = TypeVar('ModelType', bound='BaseModel')

class BaseModel(Base):
    """Base model with common fields and functionality."""
    
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    def __repr__(self) -> str:
        """Default string representation."""
        return f"<{self.__class__.__name__}(id={self.id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    @classmethod
    def get_column_names(cls) -> List[str]:
        """Get list of column names."""
        return [c.name for c in cls.__table__.columns]


class AuditableModel(BaseModel):
    """Base model with audit fields."""
    
    __abstract__ = True
    
    created_by: Mapped[Optional[UserId]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    updated_by: Mapped[Optional[UserId]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships to user (will be defined in concrete models to avoid circular imports)
    @declared_attr
    def creator(cls) -> Any:
        """Relationship to creator user."""
        return relationship(
            "User",
            foreign_keys=f"{cls.__tablename__}.created_by",
            lazy="joined",
            uselist=False
        )
    
    @declared_attr
    def updater(cls) -> Any:
        """Relationship to updater user."""
        return relationship(
            "User",
            foreign_keys=f"{cls.__tablename__}.updated_by",
            lazy="joined",
            uselist=False
        )


class SoftDeletableModel(AuditableModel):
    """Base model with soft delete functionality."""
    
    __abstract__ = True
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    deleted_by: Mapped[Optional[UserId]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    
    @declared_attr
    def deleter(cls) -> Any:
        """Relationship to deleter user."""
        return relationship(
            "User",
            foreign_keys=f"{cls.__tablename__}.deleted_by",
            lazy="joined",
            uselist=False
        )
    
    def soft_delete(self, deleted_by: Optional[UserId] = None) -> None:
        """Perform soft delete on the model."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        if deleted_by:
            self.deleted_by = deleted_by
    
    def restore(self) -> None:
        """Restore soft deleted model."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
    
    @classmethod
    def apply_soft_delete_filter(cls, query: Any) -> Any:
        """Apply soft delete filter to query."""
        return query.filter(cls.is_deleted == False)


# Export all base classes
__all__ = [
    'Base',
    'BaseModel',
    'AuditableModel',
    'SoftDeletableModel',
]