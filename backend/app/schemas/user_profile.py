"""User profile related schemas."""

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
        return v


class ProfileImageUploadResponse(BaseModel):
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
            raise ValueError(f"言語は {', '.join(allowed_languages)} のいずれかを選択してください")
        return v
    
    @field_validator("theme")
    @classmethod
    def validate_theme(cls, v: str) -> str:
        """Validate theme."""
        allowed_themes = ["light", "dark", "auto"]
        if v not in allowed_themes:
            raise ValueError(f"テーマは {', '.join(allowed_themes)} のいずれかを選択してください")
        return v


class UserPrivacySettings(BaseModel):
    """Schema for user privacy settings."""
    
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
            raise ValueError(f"表示設定は {', '.join(allowed_values)} のいずれかを選択してください")
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