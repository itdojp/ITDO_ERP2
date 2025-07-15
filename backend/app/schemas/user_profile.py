"""User profile related schemas."""

<<<<<<< HEAD
from typing import Optional

from pydantic import BaseModel, field_validator


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile."""

    full_name: Optional[str] = None
    phone: Optional[str] = None
    profile_image_url: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if v is None:
            return v
        # Basic phone validation - can be enhanced
        if len(v) > 20:
            raise ValueError("電話番号は20文字以内で入力してください")
=======
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile information."""

    full_name: str | None = Field(None, min_length=1, max_length=100)
    bio: str | None = Field(None, max_length=500)
    location: str | None = Field(None, max_length=100)
    website: HttpUrl | str | None = None

    @field_validator("website", mode="before")
    @classmethod
    def validate_website(cls, v: str | None) -> str | None:
        """Validate website URL."""
        if v and not v.startswith(("http://", "https://")):
            return f"https://{v}"
>>>>>>> origin/main
        return v


class ProfileImageUploadResponse(BaseModel):
<<<<<<< HEAD
    """Schema for profile image upload response."""

    image_url: str
    message: str = "プロファイル画像がアップロードされました"


class UserSettings(BaseModel):
    """Schema for user personal settings."""

    language: str = "ja"
    timezone: str = "Asia/Tokyo"
    theme: str = "light"
    notifications_email: bool = True
    notifications_browser: bool = True

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language code."""
        allowed_languages = ["ja", "en"]
        if v not in allowed_languages:
            raise ValueError(
                f"言語は {', '.join(allowed_languages)} のいずれかを選択してください"
            )
        return v

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, v: str) -> str:
        """Validate theme."""
        allowed_themes = ["light", "dark", "auto"]
        if v not in allowed_themes:
            raise ValueError(
                f"テーマは {', '.join(allowed_themes)} のいずれかを選択してください"
            )
        return v
=======
    """Response schema for profile image upload."""

    url: str
    size: int
    content_type: str
    uploaded_at: datetime


class UserProfileSettingsUpdate(BaseModel):
    """Schema for updating user profile settings."""

    language: str | None = Field(None, pattern="^[a-z]{2}$")
    timezone: str | None = None
    date_format: str | None = Field(
        None, pattern="^(YYYY-MM-DD|DD/MM/YYYY|MM/DD/YYYY)$"
    )
    time_format: Literal["12h", "24h"] | None = None
    notification_email: bool | None = None
    notification_push: bool | None = None


class UserProfileSettings(BaseModel):
    """Schema for user profile settings."""

    language: str = "en"
    timezone: str = "UTC"
    date_format: str = "YYYY-MM-DD"
    time_format: Literal["12h", "24h"] = "24h"
    notification_email: bool = True
    notification_push: bool = True
    updated_at: datetime


class UserPrivacySettingsUpdate(BaseModel):
    """Schema for updating user privacy settings."""

    profile_visibility: (
        Literal["public", "organization", "department", "private"] | None
    ) = None
    email_visibility: (
        Literal["public", "organization", "department", "private"] | None
    ) = None
    phone_visibility: (
        Literal["public", "organization", "department", "private"] | None
    ) = None
    allow_direct_messages: bool | None = None
    show_online_status: bool | None = None
>>>>>>> origin/main


class UserPrivacySettings(BaseModel):
    """Schema for user privacy settings."""

<<<<<<< HEAD
    profile_visibility: str = "organization"  # "public", "organization", "private"
    contact_visibility: str = "organization"
    activity_visibility: str = "organization"
    search_visibility: bool = True

    @field_validator("profile_visibility", "contact_visibility", "activity_visibility")
    @classmethod
    def validate_visibility(cls, v: str) -> str:
        """Validate visibility settings."""
        allowed_values = ["public", "organization", "private"]
        if v not in allowed_values:
            raise ValueError(
                f"表示設定は {', '.join(allowed_values)} のいずれかを選択してください"
            )
        return v


class UserProfileResponse(BaseModel):
    """Schema for user profile response."""

    id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    profile_image_url: Optional[str] = None
    settings: UserSettings
    privacy_settings: UserPrivacySettings

    class Config:
        """Pydantic config."""

        from_attributes = True
=======
    profile_visibility: Literal["public", "organization", "department", "private"] = (
        "organization"
    )
    email_visibility: Literal["public", "organization", "department", "private"] = (
        "organization"
    )
    phone_visibility: Literal["public", "organization", "department", "private"] = (
        "department"
    )
    allow_direct_messages: bool = True
    show_online_status: bool = True
    updated_at: datetime


class UserProfileResponse(BaseModel):
    """Response schema for user profile with privacy applied."""

    id: int
    full_name: str
    email: str | None  # May be hidden based on privacy settings
    phone: str | None  # May be hidden based on privacy settings
    profile_image_url: str | None
    bio: str | None
    location: str | None
    website: str | None
    is_online: bool | None  # May be hidden based on privacy settings
    last_seen_at: datetime | None  # May be hidden based on privacy settings
>>>>>>> origin/main
