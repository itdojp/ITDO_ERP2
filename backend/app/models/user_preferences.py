"""User preferences model."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class UserPreferences(BaseModel):
    """User preferences model for storing individual user settings."""

    __tablename__ = "user_preferences"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign key to user
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True
    )

    # Locale and language preferences
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)

    # UI preferences
    theme: Mapped[str] = mapped_column(String(20), default="light", nullable=False)

    # Notification preferences
    notifications_email: Mapped[bool] = mapped_column(Boolean, default=True)
    notifications_push: Mapped[bool] = mapped_column(Boolean, default=True)

    # Format preferences
    date_format: Mapped[str] = mapped_column(
        String(20), default="YYYY-MM-DD", nullable=False
    )
    time_format: Mapped[str] = mapped_column(String(10), default="24h", nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="preferences")

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        user_id: int,
        language: str = "en",
        timezone: str = "UTC",
        theme: str = "light",
        notifications_email: bool = True,
        notifications_push: bool = True,
        date_format: str = "YYYY-MM-DD",
        time_format: str = "24h",
    ) -> "UserPreferences":
        """Create user preferences."""
        preferences = cls(
            user_id=user_id,
            language=language,
            timezone=timezone,
            theme=theme,
            notifications_email=notifications_email,
            notifications_push=notifications_push,
            date_format=date_format,
            time_format=time_format,
        )
        db.add(preferences)
        db.flush()
        return preferences

    def update(self, db: Session, **kwargs: Any) -> "UserPreferences":
        """Update user preferences."""
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)

        db.add(self)
        db.flush()
        return self

    def get_locale_string(self) -> str:
        """Get locale string in format language_COUNTRY."""
        locale_map = {
            "en": "en_US",
            "ja": "ja_JP",
            "es": "es_ES",
            "fr": "fr_FR",
            "de": "de_DE",
            "zh": "zh_CN",
            "ko": "ko_KR",
        }
        return locale_map.get(self.language, "en_US")

    def get_currency_for_locale(self) -> str:
        """Get default currency for user's locale."""
        currency_map = {
            "en": "USD",
            "ja": "JPY",
            "es": "EUR",
            "fr": "EUR",
            "de": "EUR",
            "zh": "CNY",
            "ko": "KRW",
        }
        return currency_map.get(self.language, "USD")

    def get_number_format_example(self) -> str:
        """Get number format example for user's locale."""
        format_map = {
            "en": "1,234.56",
            "ja": "1,234.56",
            "es": "1.234,56",
            "fr": "1 234,56",
            "de": "1.234,56",
            "zh": "1,234.56",
            "ko": "1,234.56",
        }
        return format_map.get(self.language, "1,234.56")

    def __repr__(self) -> str:
        return (
            f"<UserPreferences(id={self.id}, user_id={self.user_id}, "
            f"language={self.language}, theme={self.theme})>"
        )
