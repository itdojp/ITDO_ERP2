"""Base class for SQLAlchemy models."""
from app.core.database import Base

# Re-export Base for backward compatibility
__all__ = ["Base"]