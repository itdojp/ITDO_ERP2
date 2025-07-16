"""Tests for user privacy settings service."""

import pytest
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user_privacy import (
    PrivacySettingsCreate,
    PrivacySettingsUpdate,
    VisibilityLevel,
)
from app.services.user_privacy import UserPrivacyService
from tests.factories import UserFactory


class TestUserPrivacyService:
    """Test user privacy settings service functionality."""

    @pytest.fixture
    def privacy_service(self, db_session: Session) -> UserPrivacyService:
        """Create user privacy service instance."""
        return UserPrivacyService(db_session)

    @pytest.fixture
    def user(self, db_session: Session) -> User:
        """Create test user."""
        return UserFactory.create_with_password(
            db_session, password="password123", email="privacy@example.com"
        )

    @pytest.fixture
    def other_user(self, db_session: Session) -> User:
        """Create another test user."""
        return UserFactory.create_with_password(
            db_session, password="password123", email="other@example.com"
        )

    def test_create_privacy_settings(
        self, privacy_service: UserPrivacyService, user: User
    ) -> None:
        """Test creating privacy settings."""
        settings_data = PrivacySettingsCreate(
            profile_visibility=VisibilityLevel.PRIVATE,
            email_visibility=VisibilityLevel.ORGANIZATION,
            phone_visibility=VisibilityLevel.DEPARTMENT,
            activity_visibility=VisibilityLevel.PUBLIC,
            show_online_status=False,
            allow_direct_messages=True,
            searchable_by_email=False,
            searchable_by_name=True,
        )

        settings = privacy_service.create_settings(user_id=user.id, data=settings_data)

        assert settings.user_id == user.id
        assert settings.profile_visibility == VisibilityLevel.PRIVATE
        assert settings.email_visibility == VisibilityLevel.ORGANIZATION
        assert settings.show_online_status is False
        assert settings.searchable_by_email is False

    def test_get_privacy_settings(
        self, privacy_service: UserPrivacyService, user: User
    ) -> None:
        """Test getting privacy settings."""
        # Create settings first
        settings_data = PrivacySettingsCreate(
            profile_visibility=VisibilityLevel.PUBLIC,
            email_visibility=VisibilityLevel.PRIVATE,
        )
        privacy_service.create_settings(user_id=user.id, data=settings_data)

        # Get settings
        retrieved = privacy_service.get_settings(user_id=user.id)

        assert retrieved.user_id == user.id
        assert retrieved.profile_visibility == VisibilityLevel.PUBLIC
        assert retrieved.email_visibility == VisibilityLevel.PRIVATE

    def test_get_default_privacy_settings(
        self, privacy_service: UserPrivacyService, user: User
    ) -> None:
        """Test getting default privacy settings when none exist."""
        # No settings created, should return defaults
        defaults = privacy_service.get_settings_or_default(user_id=user.id)

        assert defaults.profile_visibility == VisibilityLevel.ORGANIZATION
        assert defaults.email_visibility == VisibilityLevel.ORGANIZATION
        assert defaults.phone_visibility == VisibilityLevel.DEPARTMENT
        assert defaults.show_online_status is True
        assert defaults.allow_direct_messages is True

    def test_update_privacy_settings(
        self, privacy_service: UserPrivacyService, user: User
    ) -> None:
        """Test updating privacy settings."""
        # Create initial settings
        initial_data = PrivacySettingsCreate(
            profile_visibility=VisibilityLevel.PUBLIC,
            show_online_status=True,
        )
        privacy_service.create_settings(user_id=user.id, data=initial_data)

        # Update settings
        update_data = PrivacySettingsUpdate(
            profile_visibility=VisibilityLevel.PRIVATE,
            show_online_status=False,
            searchable_by_email=False,
        )
        updated = privacy_service.update_settings(user_id=user.id, data=update_data)

        assert updated.profile_visibility == VisibilityLevel.PRIVATE
        assert updated.show_online_status is False
        assert updated.searchable_by_email is False

    def test_check_profile_visibility(
        self, privacy_service: UserPrivacyService, user: User, other_user: User
    ) -> None:
        """Test checking if profile is visible to another user."""
        # Set user's profile to private
        settings_data = PrivacySettingsCreate(
            profile_visibility=VisibilityLevel.PRIVATE
        )
        privacy_service.create_settings(user_id=user.id, data=settings_data)

        # Other user should not see private profile
        can_view = privacy_service.can_view_profile(
            viewer_id=other_user.id, target_user_id=user.id
        )
        assert can_view is False

        # User can view their own profile
        can_view_own = privacy_service.can_view_profile(
            viewer_id=user.id, target_user_id=user.id
        )
        assert can_view_own is True

    def test_check_email_visibility_organization(
        self, privacy_service: UserPrivacyService, user: User, other_user: User
    ) -> None:
        """Test email visibility within organization."""
        # Set email visibility to organization only
        settings_data = PrivacySettingsCreate(
            email_visibility=VisibilityLevel.ORGANIZATION
        )
        privacy_service.create_settings(user_id=user.id, data=settings_data)

        # Mock same organization membership
        from unittest import mock

        with mock.patch(
            "app.services.user_privacy.UserPrivacyService._users_in_same_organization",
            return_value=True,
        ):
            can_view = privacy_service.can_view_email(
                viewer_id=other_user.id, target_user_id=user.id
            )
            assert can_view is True

        # Mock different organization
        with mock.patch(
            "app.services.user_privacy.UserPrivacyService._users_in_same_organization",
            return_value=False,
        ):
            can_view = privacy_service.can_view_email(
                viewer_id=other_user.id, target_user_id=user.id
            )
            assert can_view is False

    def test_check_phone_visibility_department(
        self, privacy_service: UserPrivacyService, user: User, other_user: User
    ) -> None:
        """Test phone visibility within department."""
        # Set phone visibility to department only
        settings_data = PrivacySettingsCreate(
            phone_visibility=VisibilityLevel.DEPARTMENT
        )
        privacy_service.create_settings(user_id=user.id, data=settings_data)

        # Mock same department membership
        with mock.patch(
            "app.services.user_privacy.UserPrivacyService._users_in_same_department",
            return_value=True,
        ):
            can_view = privacy_service.can_view_phone(
                viewer_id=other_user.id, target_user_id=user.id
            )
            assert can_view is True

        # Mock different department
        with mock.patch(
            "app.services.user_privacy.UserPrivacyService._users_in_same_department",
            return_value=False,
        ):
            can_view = privacy_service.can_view_phone(
                viewer_id=other_user.id, target_user_id=user.id
            )
            assert can_view is False

    def test_check_activity_visibility(
        self, privacy_service: UserPrivacyService, user: User, other_user: User
    ) -> None:
        """Test activity visibility settings."""
        # Set activity to public
        settings_data = PrivacySettingsCreate(
            activity_visibility=VisibilityLevel.PUBLIC
        )
        privacy_service.create_settings(user_id=user.id, data=settings_data)

        can_view = privacy_service.can_view_activity(
            viewer_id=other_user.id, target_user_id=user.id
        )
        assert can_view is True

    def test_check_online_status_visibility(
        self, privacy_service: UserPrivacyService, user: User, other_user: User
    ) -> None:
        """Test online status visibility."""
        # Hide online status
        settings_data = PrivacySettingsCreate(show_online_status=False)
        privacy_service.create_settings(user_id=user.id, data=settings_data)

        can_view = privacy_service.can_view_online_status(
            viewer_id=other_user.id, target_user_id=user.id
        )
        assert can_view is False

    def test_check_direct_message_permission(
        self, privacy_service: UserPrivacyService, user: User, other_user: User
    ) -> None:
        """Test direct message permission."""
        # Disable direct messages
        settings_data = PrivacySettingsCreate(allow_direct_messages=False)
        privacy_service.create_settings(user_id=user.id, data=settings_data)

        can_message = privacy_service.can_send_direct_message(
            sender_id=other_user.id, recipient_id=user.id
        )
        assert can_message is False

    def test_search_by_email_permission(
        self, privacy_service: UserPrivacyService, user: User
    ) -> None:
        """Test search by email permission."""
        # Disable email search
        settings_data = PrivacySettingsCreate(searchable_by_email=False)
        privacy_service.create_settings(user_id=user.id, data=settings_data)

        searchable = privacy_service.is_searchable_by_email(user_id=user.id)
        assert searchable is False

    def test_search_by_name_permission(
        self, privacy_service: UserPrivacyService, user: User
    ) -> None:
        """Test search by name permission."""
        # Enable name search
        settings_data = PrivacySettingsCreate(searchable_by_name=True)
        privacy_service.create_settings(user_id=user.id, data=settings_data)

        searchable = privacy_service.is_searchable_by_name(user_id=user.id)
        assert searchable is True

    def test_apply_privacy_filter_to_user_data(
        self, privacy_service: UserPrivacyService, user: User, other_user: User
    ) -> None:
        """Test applying privacy filters to user data."""
        # Set restrictive privacy
        settings_data = PrivacySettingsCreate(
            profile_visibility=VisibilityLevel.PRIVATE,
            email_visibility=VisibilityLevel.PRIVATE,
            phone_visibility=VisibilityLevel.PRIVATE,
        )
        privacy_service.create_settings(user_id=user.id, data=settings_data)

        # Get filtered user data
        user_data = {
            "id": user.id,
            "full_name": "Test User",
            "email": "privacy@example.com",
            "phone": "123-456-7890",
            "profile_image_url": "https://example.com/image.jpg",
        }

        filtered = privacy_service.apply_privacy_filter(
            user_data=user_data, viewer_id=other_user.id, target_user_id=user.id
        )

        # Private fields should be hidden
        assert filtered["email"] == "***"
        assert filtered["phone"] == "***"
        assert "profile_image_url" not in filtered

    def test_bulk_privacy_update(
        self, privacy_service: UserPrivacyService, user: User
    ) -> None:
        """Test bulk updating privacy settings."""
        # Create initial settings
        initial_data = PrivacySettingsCreate()
        privacy_service.create_settings(user_id=user.id, data=initial_data)

        # Bulk update to most restrictive
        privacy_service.set_all_private(user_id=user.id)

        settings = privacy_service.get_settings(user_id=user.id)
        assert settings.profile_visibility == VisibilityLevel.PRIVATE
        assert settings.email_visibility == VisibilityLevel.PRIVATE
        assert settings.phone_visibility == VisibilityLevel.PRIVATE
        assert settings.activity_visibility == VisibilityLevel.PRIVATE
        assert settings.show_online_status is False
        assert settings.allow_direct_messages is False
        assert settings.searchable_by_email is False
        assert settings.searchable_by_name is False

    def test_admin_override_privacy(
        self, privacy_service: UserPrivacyService, user: User, other_user: User
    ) -> None:
        """Test admin can override privacy settings."""
        # Set everything to private
        settings_data = PrivacySettingsCreate(
            profile_visibility=VisibilityLevel.PRIVATE,
            email_visibility=VisibilityLevel.PRIVATE,
        )
        privacy_service.create_settings(user_id=user.id, data=settings_data)

        # Make other_user an admin
        other_user.is_superuser = True

        # Admin should bypass privacy
        can_view_profile = privacy_service.can_view_profile(
            viewer_id=other_user.id, target_user_id=user.id
        )
        assert can_view_profile is True

        can_view_email = privacy_service.can_view_email(
            viewer_id=other_user.id, target_user_id=user.id
        )
        assert can_view_email is True
