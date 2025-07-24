from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.sql import func

from app.core.database_simple import Base


class Organization(Base):  # type: ignore[valid-type,misc]
    """Simple organization model - v19.0 practical approach"""

    __tablename__ = "organizations_simple"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)  # type: ignore[arg-type]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> dict:  # type: ignore[no-untyped-def]
        return f"<Organization(id={self.id}, code={self.code}, name={self.name})>"
