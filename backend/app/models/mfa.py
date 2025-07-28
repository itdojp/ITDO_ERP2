"""Multi-Factor Authentication models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class MFADevice(BaseModel):
    """MFA device model for tracking user's MFA devices."""

    __tablename__ = "mfa_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    device_name: Mapped[str] = mapped_column(String(100), nullable=False)
    device_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'totp', 'sms', 'email'
    secret: Mapped[str | None] = mapped_column(String(255))  # Encrypted
    phone_number: Mapped[str | None] = mapped_column(String(20))  # For SMS
    email: Mapped[str | None] = mapped_column(String(255))  # For email
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="mfa_devices")
    backup_codes: Mapped[list["MFABackupCode"]] = relationship(
        "MFABackupCode", back_populates="device", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MFADevice(id={self.id}, user_id={self.user_id}, type={self.device_type})>"


class MFABackupCode(BaseModel):
    """MFA backup codes for recovery."""

    __tablename__ = "mfa_backup_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mfa_devices.id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False)  # Hashed
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    device: Mapped["MFADevice"] = relationship("MFADevice", back_populates="backup_codes")

    def __repr__(self) -> str:
        return f"<MFABackupCode(id={self.id}, device_id={self.device_id}, used={self.is_used})>"


class MFAChallenge(BaseModel):
    """MFA challenge tracking for security."""

    __tablename__ = "mfa_challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    challenge_token: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    challenge_type: Mapped[str] = mapped_column(String(20), nullable=False)
    device_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("mfa_devices.id"))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    device: Mapped["MFADevice | None"] = relationship("MFADevice")

    def is_expired(self) -> bool:
        """Check if challenge is expired."""
        from datetime import timezone

        if self.expires_at.tzinfo is None:
            return datetime.now() > self.expires_at
        else:
            return datetime.now(timezone.utc) > self.expires_at

    def is_valid(self) -> bool:
        """Check if challenge is still valid."""
        return (
            not self.is_expired()
            and self.attempts < self.max_attempts
            and self.completed_at is None
        )

    def __repr__(self) -> str:
        return f"<MFAChallenge(id={self.id}, user_id={self.user_id}, type={self.challenge_type})>"