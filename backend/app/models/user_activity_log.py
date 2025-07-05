"""User activity log model."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User  # type: ignore


class UserActivityLog(Base):
    """User activity log for tracking user actions."""

    __tablename__ = "user_activity_logs"

    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action: str = Column(String(100), nullable=False, index=True)
    details: Dict[str, Any] = Column(JSON, default=dict)
    ip_address: Optional[str] = Column(String(45))
    user_agent: Optional[str] = Column(Text)
    created_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    user = relationship("User", back_populates="activity_logs")

    def __repr__(self) -> str:
        return f"<UserActivityLog(id={self.id}, user={self.user_id}, action={self.action})>"