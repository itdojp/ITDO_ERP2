from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.sql import func

from app.core.database_simple import Base


class User(Base):  # type: ignore[valid-type,misc]
    """Simple user model - v19.0 practical approach"""

    __tablename__ = "users_simple"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=True)  # type: ignore[arg-type]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> dict:  # type: ignore[no-untyped-def]
        return f"<User(id={self.id}, email={self.email})>"
