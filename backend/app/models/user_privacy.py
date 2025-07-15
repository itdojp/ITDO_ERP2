"""User privacy settings model."""

from datetime import datetime
<<<<<<< HEAD
from typing import TYPE_CHECKING
=======
from typing import TYPE_CHECKING, Any
>>>>>>> main

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from app.models.base import BaseModel
from app.schemas.user_privacy import VisibilityLevel

if TYPE_CHECKING:
    from app.models.user import User


class UserPrivacySettings(BaseModel):
    """User privacy settings model."""

    __tablename__ = "user_privacy_settings"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign key to user
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True
    )

    # Profile visibility settings
    profile_visibility: Mapped[VisibilityLevel] = mapped_column(
        Enum(VisibilityLevel), default=VisibilityLevel.ORGANIZATION, nullable=False
    )
    email_visibility: Mapped[VisibilityLevel] = mapped_column(
        Enum(VisibilityLevel), default=VisibilityLevel.ORGANIZATION, nullable=False
    )
    phone_visibility: Mapped[VisibilityLevel] = mapped_column(
        Enum(VisibilityLevel), default=VisibilityLevel.DEPARTMENT, nullable=False
    )
    activity_visibility: Mapped[VisibilityLevel] = mapped_column(
        Enum(VisibilityLevel), default=VisibilityLevel.ORGANIZATION, nullable=False
    )

    # Online status and messaging
    show_online_status: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_direct_messages: Mapped[bool] = mapped_column(Boolean, default=True)

    # Search settings
    searchable_by_email: Mapped[bool] = mapped_column(Boolean, default=True)
    searchable_by_name: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="privacy_settings")

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        user_id: int,
        profile_visibility: VisibilityLevel = VisibilityLevel.ORGANIZATION,
        email_visibility: VisibilityLevel = VisibilityLevel.ORGANIZATION,
        phone_visibility: VisibilityLevel = VisibilityLevel.DEPARTMENT,
        activity_visibility: VisibilityLevel = VisibilityLevel.ORGANIZATION,
        show_online_status: bool = True,
        allow_direct_messages: bool = True,
        searchable_by_email: bool = True,
        searchable_by_name: bool = True,
    ) -> "UserPrivacySettings":
        """Create privacy settings."""
        settings = cls(
            user_id=user_id,
            profile_visibility=profile_visibility,
            email_visibility=email_visibility,
            phone_visibility=phone_visibility,
            activity_visibility=activity_visibility,
            show_online_status=show_online_status,
            allow_direct_messages=allow_direct_messages,
            searchable_by_email=searchable_by_email,
            searchable_by_name=searchable_by_name,
        )
        db.add(settings)
        db.flush()
        return settings

<<<<<<< HEAD
    def update(self, db: Session, **kwargs) -> "UserPrivacySettings":
=======
    def update(self, db: Session, **kwargs: Any) -> "UserPrivacySettings":
>>>>>>> main
        """Update privacy settings."""
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)

        db.add(self)
        db.flush()
        return self

    def set_all_private(self, db: Session) -> "UserPrivacySettings":
        """Set all visibility to most restrictive."""
        self.profile_visibility = VisibilityLevel.PRIVATE
        self.email_visibility = VisibilityLevel.PRIVATE
        self.phone_visibility = VisibilityLevel.PRIVATE
        self.activity_visibility = VisibilityLevel.PRIVATE
        self.show_online_status = False
        self.allow_direct_messages = False
        self.searchable_by_email = False
        self.searchable_by_name = False

        db.add(self)
        db.flush()
        return self

    def set_all_public(self, db: Session) -> "UserPrivacySettings":
        """Set all visibility to least restrictive."""
        self.profile_visibility = VisibilityLevel.PUBLIC
        self.email_visibility = VisibilityLevel.PUBLIC
        self.phone_visibility = VisibilityLevel.PUBLIC
        self.activity_visibility = VisibilityLevel.PUBLIC
        self.show_online_status = True
        self.allow_direct_messages = True
        self.searchable_by_email = True
        self.searchable_by_name = True

        db.add(self)
        db.flush()
        return self

    def __repr__(self) -> str:
        return (
            f"<UserPrivacySettings(id={self.id}, user_id={self.user_id}, "
            f"profile={self.profile_visibility.value})>"
        )
