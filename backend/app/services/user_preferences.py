"""User preferences management service."""

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import NotFound
from app.models.user_preferences import UserPreferences
from app.schemas.user_preferences import (
    UserLocaleInfo,
    UserPreferencesCreate,
    UserPreferencesResponse,
    UserPreferencesUpdate,
)


class UserPreferencesService:
    """User preferences management service."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db

    def create_preferences(
        self, user_id: int, data: UserPreferencesCreate
    ) -> UserPreferencesResponse:
        """Create user preferences."""
        # Check if preferences already exist
        existing = (
            self.db.query(UserPreferences)
            .filter(UserPreferences.user_id == user_id)
            .first()
        )
        if existing:
            # Update existing preferences instead
            return self.update_preferences(
                user_id, UserPreferencesUpdate(**data.dict())
            )

        # Create new preferences
        preferences = UserPreferences.create(
            self.db,
            user_id=user_id,
            language=data.language,
            timezone=data.timezone,
            theme=data.theme,
            notifications_email=data.notifications_email,
            notifications_push=data.notifications_push,
            date_format=data.date_format,
            time_format=data.time_format,
        )

        self.db.commit()

        return UserPreferencesResponse.from_orm(preferences)

    def get_preferences(self, user_id: int) -> UserPreferencesResponse:
        """Get user preferences."""
        preferences = (
            self.db.query(UserPreferences)
            .filter(UserPreferences.user_id == user_id)
            .first()
        )

        if not preferences:
            raise NotFound("ユーザー設定が見つかりません")

        return UserPreferencesResponse.from_orm(preferences)

    def get_preferences_or_default(self, user_id: int) -> UserPreferencesResponse:
        """Get user preferences or return defaults if none exist."""
        try:
            return self.get_preferences(user_id)
        except NotFound:
            # Return default preferences
            default_data = UserPreferencesCreate()
            return UserPreferencesResponse(
                id=0,  # Temporary ID for default
                user_id=user_id,
                language=default_data.language,
                timezone=default_data.timezone,
                theme=default_data.theme,
                notifications_email=default_data.notifications_email,
                notifications_push=default_data.notifications_push,
                date_format=default_data.date_format,
                time_format=default_data.time_format,
                created_at=None,
                updated_at=None,
            )

    def update_preferences(
        self, user_id: int, data: UserPreferencesUpdate
    ) -> UserPreferencesResponse:
        """Update user preferences."""
        preferences = (
            self.db.query(UserPreferences)
            .filter(UserPreferences.user_id == user_id)
            .first()
        )

        if not preferences:
            raise NotFound("ユーザー設定が見つかりません")

        # Update only provided fields
        update_data = data.dict(exclude_unset=True)
        preferences.update(self.db, **update_data)

        self.db.commit()

        return UserPreferencesResponse.from_orm(preferences)

    def delete_preferences(self, user_id: int) -> None:
        """Delete user preferences."""
        preferences = (
            self.db.query(UserPreferences)
            .filter(UserPreferences.user_id == user_id)
            .first()
        )

        if not preferences:
            raise NotFound("ユーザー設定が見つかりません")

        self.db.delete(preferences)
        self.db.commit()

    def get_user_locale_info(self, user_id: int) -> Dict[str, Any]:
        """Get user locale information for internationalization."""
        try:
            preferences = self.get_preferences(user_id)
        except NotFound:
            preferences = self.get_preferences_or_default(user_id)

        # Create UserPreferences object to use helper methods
        temp_prefs = UserPreferences(
            user_id=user_id,
            language=preferences.language,
            timezone=preferences.timezone,
            theme=preferences.theme,
            notifications_email=preferences.notifications_email,
            notifications_push=preferences.notifications_push,
            date_format=preferences.date_format,
            time_format=preferences.time_format,
        )

        return {
            "language": preferences.language,
            "timezone": preferences.timezone,
            "date_format": preferences.date_format,
            "time_format": preferences.time_format,
            "locale_string": temp_prefs.get_locale_string(),
            "currency": temp_prefs.get_currency_for_locale(),
            "number_format": temp_prefs.get_number_format_example(),
        }

    def set_language(self, user_id: int, language: str) -> UserPreferencesResponse:
        """Set user language preference."""
        update_data = UserPreferencesUpdate(language=language)
        return self.update_preferences(user_id, update_data)

    def set_timezone(self, user_id: int, timezone: str) -> UserPreferencesResponse:
        """Set user timezone preference."""
        update_data = UserPreferencesUpdate(timezone=timezone)
        return self.update_preferences(user_id, update_data)

    def set_theme(self, user_id: int, theme: str) -> UserPreferencesResponse:
        """Set user theme preference."""
        update_data = UserPreferencesUpdate(theme=theme)
        return self.update_preferences(user_id, update_data)

    def toggle_email_notifications(self, user_id: int) -> UserPreferencesResponse:
        """Toggle email notifications on/off."""
        try:
            current_prefs = self.get_preferences(user_id)
            new_value = not current_prefs.notifications_email
        except NotFound:
            new_value = False  # Default to off if no preferences exist

        update_data = UserPreferencesUpdate(notifications_email=new_value)
        return self.update_preferences(user_id, update_data)

    def toggle_push_notifications(self, user_id: int) -> UserPreferencesResponse:
        """Toggle push notifications on/off."""
        try:
            current_prefs = self.get_preferences(user_id)
            new_value = not current_prefs.notifications_push
        except NotFound:
            new_value = False  # Default to off if no preferences exist

        update_data = UserPreferencesUpdate(notifications_push=new_value)
        return self.update_preferences(user_id, update_data)
