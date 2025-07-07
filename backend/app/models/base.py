"""Base model implementation for ITDO ERP System.

This module provides base model classes with common functionality for all database models.
"""
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, TypeVar

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.types import UserId

if TYPE_CHECKING:
    pass

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

    # Relationships to user (commented out to avoid circular imports and typing issues)
    # These can be added manually in specific models if needed


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

    # Relationship to deleter user (commented out to avoid circular imports and typing issues)
    # This can be added manually in specific models if needed

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
        return query.filter(not cls.is_deleted)


# Export all base classes
__all__ = [
    'Base',
    'BaseModel',
    'AuditableModel',
    'SoftDeletableModel',
]
