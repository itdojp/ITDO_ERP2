"""User session model."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User  # type: ignore


class UserSession(Base):
    """User session model for tracking active sessions."""

    __tablename__ = "user_sessions"

    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token: str = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token: Optional[str] = Column(String(255), unique=True)
    ip_address: Optional[str] = Column(String(45))  # IPv6 support
    user_agent: Optional[str] = Column(Text)
    is_active: bool = Column(Boolean, default=True)
    expires_at: datetime = Column(DateTime(timezone=True), nullable=False)
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    last_activity: datetime = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Security flags
    requires_verification: bool = Column(Boolean, default=False)
    security_alert: Optional[str] = Column(String(50))

    # Relationships
    user = relationship("User", back_populates="sessions")

    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at

    def is_valid(self) -> bool:
        """Check if session is valid."""
        return self.is_active and not self.is_expired()

    def invalidate(self) -> None:
        """Invalidate the session."""
        self.is_active = False

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"