"""Base model implementation for ITDO ERP System.

This module provides base model classes with common functionality for all database models.
"""
from typing import Any, Dict, Optional, TypeVar, Generic, Type, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, declared_attr
from app.types import UserId, AuditableProtocol, SoftDeletableProtocol

if TYPE_CHECKING:
    from app.models.user import User

# Create base class for all models using SQLAlchemy 2.0 style
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    @classmethod
    def from_dict(cls: Type[ModelType], data: Dict[str, Any]) -> ModelType:
        """Create model instance from dictionary."""
        return cls(**data)
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update model instance from dictionary."""
        for key, value in data.items():
            if hasattr(self, key) and key != 'id':
                setattr(self, key, value)
    
    def __repr__(self) -> str:
        """String representation of model."""
        return f"<{self.__class__.__name__}(id={self.id})>"


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
    def creator(cls) -> Mapped[Optional["User"]]:
        return relationship(
            "User",
            foreign_keys="AuditableModel.created_by",
            lazy="joined",
            uselist=False
        )
    
    @declared_attr
    def updater(cls) -> Mapped[Optional["User"]]:
        return relationship(
            "User",
            foreign_keys="AuditableModel.updated_by",
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
    def deleter(cls) -> Mapped[Optional["User"]]:
        return relationship(
            "User",
            foreign_keys="SoftDeletableModel.deleted_by",
            lazy="joined",
            uselist=False
        )
    
    def soft_delete(self, deleted_by: Optional[UserId] = None) -> None:
        """Perform soft delete on the model."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by
    
    def restore(self) -> None:
        """Restore soft deleted model."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None


class TimestampModel(BaseModel):
    """Base model with only timestamp fields (no audit fields)."""
    
    __abstract__ = True
    
    # This class intentionally doesn't add new fields
    # It's used for models that need timestamps but not audit fields
    pass


# Type guards for protocol checking
def is_auditable(model: Any) -> bool:
    """Check if model implements AuditableProtocol."""
    return isinstance(model, AuditableModel)


def is_soft_deletable(model: Any) -> bool:
    """Check if model implements SoftDeletableProtocol."""
    return isinstance(model, SoftDeletableModel)


# Export all base models and utilities
__all__ = [
    'Base',
    'BaseModel',
    'AuditableModel',
    'SoftDeletableModel',
    'TimestampModel',
    'is_auditable',
    'is_soft_deletable',
]