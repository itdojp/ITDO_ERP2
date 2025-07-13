"""User preferences schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


class UserPreferencesBase(BaseModel):
    """Base user preferences schema."""

    language: str = Field(default="en", description="User interface language")
    timezone: str = Field(default="UTC", description="User timezone")
    theme: str = Field(default="light", description="UI theme preference")
    notifications_email: bool = Field(
        default=True, description="Email notifications enabled"
    )
    notifications_push: bool = Field(
        default=True, description="Push notifications enabled"
    )
    date_format: str = Field(default="YYYY-MM-DD", description="Date display format")
    time_format: str = Field(default="24h", description="Time display format")

    @validator("language")
    def validate_language(cls, v):
        """Validate language code."""
        supported_languages = ["en", "ja", "es", "fr", "de", "zh", "ko"]
        if v not in supported_languages:
            raise ValueError("サポートされていない言語です")
        return v

    @validator("timezone")
    def validate_timezone(cls, v):
        """Validate timezone."""
        import pytz

        try:
            pytz.timezone(v)
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError("無効なタイムゾーンです")
        return v

    @validator("theme")
    def validate_theme(cls, v):
        """Validate theme."""
        supported_themes = ["light", "dark", "auto"]
        if v not in supported_themes:
            raise ValueError("サポートされていないテーマです")
        return v

    @validator("date_format")
    def validate_date_format(cls, v):
        """Validate date format."""
        supported_formats = [
            "YYYY-MM-DD",
            "DD/MM/YYYY",
            "MM/DD/YYYY",
            "YYYY年MM月DD日",
            "DD.MM.YYYY",
        ]
        if v not in supported_formats:
            raise ValueError("サポートされていない日付フォーマットです")
        return v

    @validator("time_format")
    def validate_time_format(cls, v):
        """Validate time format."""
        supported_formats = ["12h", "24h"]
        if v not in supported_formats:
            raise ValueError("サポートされていない時刻フォーマットです")
        return v


class UserPreferencesCreate(UserPreferencesBase):
    """Schema for creating user preferences."""

    pass


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences."""

    language: Optional[str] = None
    timezone: Optional[str] = None
    theme: Optional[str] = None
    notifications_email: Optional[bool] = None
    notifications_push: Optional[bool] = None
    date_format: Optional[str] = None
    time_format: Optional[str] = None

    @validator("language")
    def validate_language(cls, v):
        """Validate language code."""
        if v is not None:
            supported_languages = ["en", "ja", "es", "fr", "de", "zh", "ko"]
            if v not in supported_languages:
                raise ValueError("サポートされていない言語です")
        return v

    @validator("timezone")
    def validate_timezone(cls, v):
        """Validate timezone."""
        if v is not None:
            import pytz

            try:
                pytz.timezone(v)
            except pytz.exceptions.UnknownTimeZoneError:
                raise ValueError("無効なタイムゾーンです")
        return v

    @validator("theme")
    def validate_theme(cls, v):
        """Validate theme."""
        if v is not None:
            supported_themes = ["light", "dark", "auto"]
            if v not in supported_themes:
                raise ValueError("サポートされていないテーマです")
        return v

    @validator("date_format")
    def validate_date_format(cls, v):
        """Validate date format."""
        if v is not None:
            supported_formats = [
                "YYYY-MM-DD",
                "DD/MM/YYYY",
                "MM/DD/YYYY",
                "YYYY年MM月DD日",
                "DD.MM.YYYY",
            ]
            if v not in supported_formats:
                raise ValueError("サポートされていない日付フォーマットです")
        return v

    @validator("time_format")
    def validate_time_format(cls, v):
        """Validate time format."""
        if v is not None:
            supported_formats = ["12h", "24h"]
            if v not in supported_formats:
                raise ValueError("サポートされていない時刻フォーマットです")
        return v


class UserPreferencesResponse(UserPreferencesBase):
    """Schema for user preferences response."""

    id: int = Field(description="Preferences ID")
    user_id: int = Field(description="User ID")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    class Config:
        from_attributes = True


class UserLocaleInfo(BaseModel):
    """Schema for user locale information."""

    language: str = Field(description="Language code")
    timezone: str = Field(description="Timezone")
    date_format: str = Field(description="Date format")
    time_format: str = Field(description="Time format")
    locale_string: str = Field(description="Full locale string (e.g., ja_JP)")
    currency: str = Field(default="USD", description="Currency code")
    number_format: str = Field(default="1,234.56", description="Number format example")
