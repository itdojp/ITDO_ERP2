"""Tests for user preferences management service."""

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import NotFound, PermissionDenied
from app.models.user import User
from app.schemas.user_preferences import (
    UserPreferencesCreate,
    UserPreferencesResponse,
    UserPreferencesUpdate,
)
from app.services.user_preferences import UserPreferencesService
from tests.factories import UserFactory


class TestUserPreferencesService:
    """Test user preferences service functionality."""

    @pytest.fixture
    def user_preferences_service(self, db_session: Session) -> UserPreferencesService:
        """Create user preferences service instance."""
        return UserPreferencesService(db_session)

    @pytest.fixture
    def user(self, db_session: Session) -> User:
        """Create test user."""
        return UserFactory.create_with_password(
            db_session, password="password123", email="prefs@example.com"
        )

    def test_create_user_preferences(
        self, user_preferences_service: UserPreferencesService, user: User
    ) -> None:
        """Test creating user preferences."""
        preferences_data = UserPreferencesCreate(
            language="ja",
            timezone="Asia/Tokyo",
            theme="dark",
            notifications_email=True,
            notifications_push=False,
            date_format="YYYY-MM-DD",
            time_format="24h",
        )

        preferences = user_preferences_service.create_preferences(
            user_id=user.id, data=preferences_data
        )

        assert preferences.user_id == user.id
        assert preferences.language == "ja"
        assert preferences.timezone == "Asia/Tokyo"
        assert preferences.theme == "dark"
        assert preferences.notifications_email is True
        assert preferences.notifications_push is False

    def test_get_user_preferences(
        self, user_preferences_service: UserPreferencesService, user: User
    ) -> None:
        """Test getting user preferences."""
        # Create preferences first
        preferences_data = UserPreferencesCreate(
            language="en", timezone="UTC", theme="light"
        )
        created_prefs = user_preferences_service.create_preferences(
            user_id=user.id, data=preferences_data
        )

        # Get preferences
        retrieved_prefs = user_preferences_service.get_preferences(user_id=user.id)

        assert retrieved_prefs.user_id == user.id
        assert retrieved_prefs.language == "en"
        assert retrieved_prefs.timezone == "UTC"
        assert retrieved_prefs.theme == "light"

    def test_get_nonexistent_user_preferences(
        self, user_preferences_service: UserPreferencesService
    ) -> None:
        """Test getting preferences for non-existent user."""
        with pytest.raises(NotFound, match="ユーザー設定が見つかりません"):
            user_preferences_service.get_preferences(user_id=99999)

    def test_update_user_preferences(
        self, user_preferences_service: UserPreferencesService, user: User
    ) -> None:
        """Test updating user preferences."""
        # Create initial preferences
        initial_data = UserPreferencesCreate(
            language="en", timezone="UTC", theme="light"
        )
        user_preferences_service.create_preferences(user_id=user.id, data=initial_data)

        # Update preferences
        update_data = UserPreferencesUpdate(
            language="ja", theme="dark", notifications_email=False
        )
        updated_prefs = user_preferences_service.update_preferences(
            user_id=user.id, data=update_data
        )

        assert updated_prefs.language == "ja"
        assert updated_prefs.theme == "dark"
        assert updated_prefs.timezone == "UTC"  # Should remain unchanged
        assert updated_prefs.notifications_email is False

    def test_delete_user_preferences(
        self, user_preferences_service: UserPreferencesService, user: User
    ) -> None:
        """Test deleting user preferences."""
        # Create preferences first
        preferences_data = UserPreferencesCreate(language="en", timezone="UTC")
        user_preferences_service.create_preferences(
            user_id=user.id, data=preferences_data
        )

        # Delete preferences
        user_preferences_service.delete_preferences(user_id=user.id)

        # Verify deletion
        with pytest.raises(NotFound):
            user_preferences_service.get_preferences(user_id=user.id)

    def test_get_default_preferences(
        self, user_preferences_service: UserPreferencesService, user: User
    ) -> None:
        """Test getting default preferences for user without custom settings."""
        # User has no preferences set, should return defaults
        default_prefs = user_preferences_service.get_preferences_or_default(
            user_id=user.id
        )

        assert default_prefs.language == "en"  # Default language
        assert default_prefs.timezone == "UTC"  # Default timezone
        assert default_prefs.theme == "light"  # Default theme
        assert default_prefs.notifications_email is True  # Default email notifications

    def test_bulk_update_preferences(
        self, user_preferences_service: UserPreferencesService, user: User
    ) -> None:
        """Test bulk updating multiple preference settings."""
        # Create initial preferences
        initial_data = UserPreferencesCreate(
            language="en",
            timezone="UTC",
            theme="light",
            notifications_email=True,
            notifications_push=True,
        )
        user_preferences_service.create_preferences(user_id=user.id, data=initial_data)

        # Bulk update
        bulk_update = UserPreferencesUpdate(
            language="ja",
            timezone="Asia/Tokyo",
            theme="dark",
            notifications_push=False,
            date_format="DD/MM/YYYY",
            time_format="12h",
        )

        updated_prefs = user_preferences_service.update_preferences(
            user_id=user.id, data=bulk_update
        )

        assert updated_prefs.language == "ja"
        assert updated_prefs.timezone == "Asia/Tokyo"
        assert updated_prefs.theme == "dark"
        assert updated_prefs.notifications_email is True  # Unchanged
        assert updated_prefs.notifications_push is False  # Updated
        assert updated_prefs.date_format == "DD/MM/YYYY"
        assert updated_prefs.time_format == "12h"

    def test_invalid_timezone_preference(
        self, user_preferences_service: UserPreferencesService, user: User
    ) -> None:
        """Test creating preferences with invalid timezone."""
        invalid_data = UserPreferencesCreate(
            language="en", timezone="Invalid/Timezone", theme="light"
        )

        with pytest.raises(ValueError, match="無効なタイムゾーンです"):
            user_preferences_service.create_preferences(
                user_id=user.id, data=invalid_data
            )

    def test_invalid_language_preference(
        self, user_preferences_service: UserPreferencesService, user: User
    ) -> None:
        """Test creating preferences with invalid language."""
        invalid_data = UserPreferencesCreate(
            language="invalid_lang", timezone="UTC", theme="light"
        )

        with pytest.raises(ValueError, match="サポートされていない言語です"):
            user_preferences_service.create_preferences(
                user_id=user.id, data=invalid_data
            )

    def test_get_user_locale_info(
        self, user_preferences_service: UserPreferencesService, user: User
    ) -> None:
        """Test getting user locale information."""
        # Create preferences with Japanese locale
        preferences_data = UserPreferencesCreate(
            language="ja",
            timezone="Asia/Tokyo",
            date_format="YYYY年MM月DD日",
            time_format="24h",
        )
        user_preferences_service.create_preferences(
            user_id=user.id, data=preferences_data
        )

        locale_info = user_preferences_service.get_user_locale_info(user_id=user.id)

        assert locale_info["language"] == "ja"
        assert locale_info["timezone"] == "Asia/Tokyo"
        assert locale_info["date_format"] == "YYYY年MM月DD日"
        assert locale_info["time_format"] == "24h"
        assert "locale_string" in locale_info  # e.g., "ja_JP"
