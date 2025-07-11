"""User session model."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

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
    refresh_token: Mapped[str | None] = mapped_column(String(255), unique=True)
    ip_address: Mapped[str | None] = mapped_column(String(45))  # IPv6 support
    user_agent: Mapped[str | None] = mapped_column(Text)
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
    security_alert: Mapped[str | None] = mapped_column(String(50))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    def is_expired(self) -> bool:
        """Check if session is expired."""
        # Handle both timezone-aware and naive datetimes
        if self.expires_at.tzinfo is None:
            # If expires_at is naive, compare with naive datetime
            return datetime.now() > self.expires_at
        else:
            # If expires_at is timezone-aware, compare with timezone-aware datetime
            return datetime.now(UTC) > self.expires_at

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
