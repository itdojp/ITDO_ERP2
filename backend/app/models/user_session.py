"""User session model."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class UserSession(BaseModel):
    """User session model for tracking active sessions."""

    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    session_token: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    refresh_token: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6 support
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Security flags
    requires_verification: Mapped[bool] = mapped_column(Boolean, default=False)
    security_alert: Mapped[Optional[str]] = mapped_column(String(50))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    def is_expired(self) -> bool:
        """Check if session is expired."""
        # Handle both timezone-aware and naive datetimes
        now = datetime.now(timezone.utc)
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return now > expires_at

    def is_valid(self) -> bool:
        """Check if session is valid."""
        return self.is_active and not self.is_expired()

    def invalidate(self) -> None:
        """Invalidate the session."""
        self.is_active = False

    def __repr__(self) -> str:
        return (
            f"<UserSession(id={self.id}, user_id={self.user_id}, "
            f"active={self.is_active})>"
        )
