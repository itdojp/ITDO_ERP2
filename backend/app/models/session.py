"""Session management models."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from app.models.base import Base


class UserSession(Base):
    """User session model for tracking active sessions."""

    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    session_token: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    refresh_token: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    
    # Session metadata
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)  # IPv6 max length
    user_agent: Mapped[str] = mapped_column(String(500), nullable=False)
    device_id: Mapped[str | None] = mapped_column(String(100))
    device_name: Mapped[str | None] = mapped_column(String(100))
    
    # Session timing
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    refresh_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Session state
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    revoke_reason: Mapped[str | None] = mapped_column(String(255))
    
    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="sessions")
    revoked_by_user: Mapped["User | None"] = relationship("User", foreign_keys=[revoked_by])
    
    def update_activity(self, db: Session) -> None:
        """Update last activity timestamp."""
        self.last_activity_at = datetime.now(UTC)
        db.commit()
    
    def revoke(self, db: Session, revoked_by: int | None = None, reason: str | None = None) -> None:
        """Revoke this session."""
        self.is_active = False
        self.revoked_at = datetime.now(UTC)
        self.revoked_by = revoked_by
        self.revoke_reason = reason
        db.commit()
    
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.now(UTC) > self.expires_at
    
    def is_refresh_expired(self) -> bool:
        """Check if refresh token is expired."""
        return datetime.now(UTC) > self.refresh_expires_at
    
    def extend_session(self, db: Session, hours: int = 8) -> None:
        """Extend session expiry."""
        self.expires_at = datetime.now(UTC) + timedelta(hours=hours)
        self.last_activity_at = datetime.now(UTC)
        db.commit()


class SessionActivity(Base):
    """Track significant session activities."""

    __tablename__ = "session_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_sessions.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Activity details
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # login, logout, refresh, extend
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[str] = mapped_column(String(500), nullable=False)
    details: Mapped[str | None] = mapped_column(Text)  # JSON additional details
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    
    # Relationships
    session: Mapped[UserSession] = relationship("UserSession", backref="activities")
    user: Mapped["User"] = relationship("User")


class SessionConfiguration(Base):
    """User-specific session configuration."""

    __tablename__ = "session_configurations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Session duration settings
    session_timeout_hours: Mapped[int] = mapped_column(Integer, default=8)
    max_session_timeout_hours: Mapped[int] = mapped_column(Integer, default=24)
    refresh_token_days: Mapped[int] = mapped_column(Integer, default=30)
    
    # Security settings
    allow_multiple_sessions: Mapped[bool] = mapped_column(Boolean, default=True)
    max_concurrent_sessions: Mapped[int] = mapped_column(Integer, default=3)
    require_mfa_for_new_device: Mapped[bool] = mapped_column(Boolean, default=True)
    trusted_devices: Mapped[str | None] = mapped_column(Text)  # JSON array of device IDs
    
    # Notification settings
    notify_new_device_login: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_suspicious_activity: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="session_config")


# Import User type for relationships
from app.models.user import User