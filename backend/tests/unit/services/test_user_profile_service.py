<<<<<<< HEAD
"""Tests for user profile service methods."""

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import NotFound, PermissionDenied
from app.services.user import UserService
=======
"""
User profile service tests.

Tests for user profile management functionality including image upload,
personal settings, and privacy settings.
Following TDD approach - Red phase: Writing tests before implementation.
"""

import io
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError, PermissionDenied
from app.schemas.user_profile import (
    ProfileImageUploadResponse,
    UserPrivacySettings,
    UserPrivacySettingsUpdate,
    UserProfileSettings,
    UserProfileSettingsUpdate,
    UserProfileUpdate,
)
from app.services.user_profile import UserProfileService
>>>>>>> origin/main
from tests.factories import create_test_user


class TestUserProfileService:
<<<<<<< HEAD
    """Test user profile service methods."""

    @pytest.fixture
    def service(self, db_session: Session) -> UserService:
        """Create UserService instance."""
        return UserService(db_session)

    def test_update_profile_image_self(
        self, service: UserService, db_session: Session
    ) -> None:
        """TEST-PROFILE-001: ユーザーが自分のプロファイル画像を更新."""
        # Given: ユーザー
        user = create_test_user(db_session)
        db_session.commit()

        # When: プロファイル画像更新
        new_image_url = "/static/profile_images/user_123.jpg"
        updated_user = service.update_profile_image(
            user.id, new_image_url, user, db_session
        )

        # Then:
        assert updated_user.profile_image_url == new_image_url
        assert updated_user.id == user.id

    def test_update_profile_image_permission_denied(
        self, service: UserService, db_session: Session
    ) -> None:
        """TEST-PROFILE-002: 他のユーザーのプロファイル画像更新が拒否."""
        # Given: 2人のユーザー
        user1 = create_test_user(db_session)
        user2 = create_test_user(db_session)
        db_session.commit()

        # When & Then: 他のユーザーの画像更新を試行
        with pytest.raises(PermissionDenied):
            service.update_profile_image(
                user1.id, "/static/profile_images/user_123.jpg", user2, db_session
            )

    def test_update_profile_image_admin_can_update(
        self, service: UserService, db_session: Session
    ) -> None:
        """TEST-PROFILE-003: システム管理者が他のユーザーの画像を更新."""
        # Given: 一般ユーザーとシステム管理者
        user = create_test_user(db_session)
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # When: 管理者がユーザーの画像更新
        new_image_url = "/static/profile_images/admin_updated.jpg"
        updated_user = service.update_profile_image(
            user.id, new_image_url, admin, db_session
        )

        # Then:
        assert updated_user.profile_image_url == new_image_url

    def test_get_user_settings_self(
        self, service: UserService, db_session: Session
    ) -> None:
        """TEST-PROFILE-004: ユーザーが自分の設定を取得できることをテスト."""
        # Given: ユーザー
        user = create_test_user(db_session)
        db_session.commit()

        # When: 設定取得
        settings = service.get_user_settings(user.id, user, db_session)

        # Then:
        assert isinstance(settings, dict)
        assert "language" in settings
        assert "timezone" in settings
        assert "theme" in settings
        assert settings["language"] == "ja"

    def test_get_user_settings_permission_denied(
        self, service: UserService, db_session: Session
    ) -> None:
        """TEST-PROFILE-005: 他のユーザーの設定取得が拒否されることをテスト."""
        # Given: 2人のユーザー
        user1 = create_test_user(db_session)
        user2 = create_test_user(db_session)
        db_session.commit()

        # When & Then: 他のユーザーの設定取得を試行
        with pytest.raises(PermissionDenied):
            service.get_user_settings(user1.id, user2, db_session)

    def test_update_user_settings_self(
        self, service: UserService, db_session: Session
    ) -> None:
        """TEST-PROFILE-006: ユーザーが自分の設定を更新できることをテスト."""
        # Given: ユーザー
        user = create_test_user(db_session)
        db_session.commit()

        # When: 設定更新
        new_settings = {
            "language": "en",
            "timezone": "UTC",
            "theme": "dark",
            "notifications_email": False,
        }
        updated_settings = service.update_user_settings(
            user.id, new_settings, user, db_session
        )

        # Then:
        assert updated_settings["language"] == "en"
        assert updated_settings["timezone"] == "UTC"
        assert updated_settings["theme"] == "dark"
        assert updated_settings["notifications_email"] is False

    def test_get_privacy_settings_self(
        self, service: UserService, db_session: Session
    ) -> None:
        """TEST-PROFILE-007: ユーザーが自分のプライバシー設定を取得."""
        # Given: ユーザー
        user = create_test_user(db_session)
        db_session.commit()

        # When: プライバシー設定取得
        privacy_settings = service.get_privacy_settings(user.id, user, db_session)

        # Then:
        assert isinstance(privacy_settings, dict)
        assert "profile_visibility" in privacy_settings
        assert "contact_visibility" in privacy_settings
        assert "activity_visibility" in privacy_settings
        assert "search_visibility" in privacy_settings

    def test_update_privacy_settings_self(
        self, service: UserService, db_session: Session
    ) -> None:
        """TEST-PROFILE-008: ユーザーが自分のプライバシー設定を更新."""
        # Given: ユーザー
        user = create_test_user(db_session)
        db_session.commit()

        # When: プライバシー設定更新
        new_privacy = {
            "profile_visibility": "private",
            "contact_visibility": "private",
            "activity_visibility": "organization",
            "search_visibility": False,
        }
        updated_privacy = service.update_privacy_settings(
            user.id, new_privacy, user, db_session
        )

        # Then:
        assert updated_privacy["profile_visibility"] == "private"
        assert updated_privacy["contact_visibility"] == "private"
        assert updated_privacy["search_visibility"] is False

    def test_update_profile_image_user_not_found(
        self, service: UserService, db_session: Session
    ) -> None:
        """TEST-PROFILE-009: 存在しないユーザーの画像更新時にエラー."""
        # Given: システム管理者
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # When & Then: 存在しないユーザーの画像更新を試行
        with pytest.raises(NotFound):
            service.update_profile_image(
                999, "/static/profile_images/nonexistent.jpg", admin, db_session
            )
=======
    """Test cases for UserProfileService."""

    @pytest.fixture
    def service(self, db_session: Session) -> UserProfileService:
        """Create service instance."""
        return UserProfileService(db_session)

    @pytest.fixture
    def test_image(self) -> io.BytesIO:
        """Create a test image file."""
        img = Image.new("RGB", (100, 100), color="red")
        img_io = io.BytesIO()
        img.save(img_io, "PNG")
        img_io.seek(0)
        return img_io

    def test_upload_profile_image_success(
        self, service: UserProfileService, db_session: Session, test_image: io.BytesIO
    ) -> None:
        """Test successful profile image upload."""
        # Given: User
        user = create_test_user(db_session)
        db_session.commit()

        # When: Uploading profile image
        result = service.upload_profile_image(
            user_id=user.id,
            file_data=test_image.read(),
            filename="profile.png",
            content_type="image/png",
            uploader=user,
            db=db_session,
        )

        # Then: Image should be uploaded
        assert isinstance(result, ProfileImageUploadResponse)
        assert result.url is not None
        assert result.url.startswith("/uploads/profile/")
        assert result.size > 0
        assert result.content_type == "image/png"

        # User's profile_image_url should be updated
        db_session.refresh(user)
        assert user.profile_image_url == result.url

    def test_upload_profile_image_invalid_format(
        self, service: UserProfileService, db_session: Session
    ) -> None:
        """Test profile image upload with invalid format."""
        # Given: User and invalid file
        user = create_test_user(db_session)
        db_session.commit()

        # When/Then: Uploading non-image file should fail
        with pytest.raises(BusinessLogicError, match="Invalid image format"):
            service.upload_profile_image(
                user_id=user.id,
                file_data=b"Not an image",
                filename="document.pdf",
                content_type="application/pdf",
                uploader=user,
                db=db_session,
            )

    def test_upload_profile_image_size_limit(
        self, service: UserProfileService, db_session: Session
    ) -> None:
        """Test profile image upload with size limit."""
        # Given: User and large image
        user = create_test_user(db_session)
        db_session.commit()

        # Create fake large image data (>5MB)
        large_data = b"x" * (6 * 1024 * 1024)  # 6MB of data

        # When/Then: Uploading large image should fail
        with pytest.raises(BusinessLogicError, match="Image size exceeds limit"):
            service.upload_profile_image(
                user_id=user.id,
                file_data=large_data,
                filename="large.png",
                content_type="image/png",
                uploader=user,
                db=db_session,
            )

    def test_upload_profile_image_permission_denied(
        self, service: UserProfileService, db_session: Session, test_image: io.BytesIO
    ) -> None:
        """Test profile image upload permission check."""
        # Given: Two different users
        user1 = create_test_user(db_session, email="user1@example.com")
        user2 = create_test_user(db_session, email="user2@example.com")
        db_session.commit()

        # When/Then: User2 trying to upload image for user1 should fail
        with pytest.raises(PermissionDenied):
            service.upload_profile_image(
                user_id=user1.id,
                file_data=test_image.read(),
                filename="profile.png",
                content_type="image/png",
                uploader=user2,
                db=db_session,
            )

    def test_delete_profile_image(
        self, service: UserProfileService, db_session: Session
    ) -> None:
        """Test profile image deletion."""
        # Given: User with profile image
        user = create_test_user(
            db_session, profile_image_url="/uploads/profile/test.png"
        )
        db_session.commit()

        # When: Deleting profile image
        service.delete_profile_image(
            user_id=user.id,
            deleter=user,
            db=db_session,
        )

        # Then: Profile image should be removed
        db_session.refresh(user)
        assert user.profile_image_url is None

    def test_update_profile_settings(
        self, service: UserProfileService, db_session: Session
    ) -> None:
        """Test updating user profile settings."""
        # Given: User
        user = create_test_user(db_session)
        db_session.commit()

        # When: Updating profile settings
        settings_update = UserProfileSettingsUpdate(
            language="ja",
            timezone="Asia/Tokyo",
            date_format="YYYY-MM-DD",
            time_format="24h",
            notification_email=True,
            notification_push=False,
        )

        result = service.update_profile_settings(
            user_id=user.id,
            settings=settings_update,
            updater=user,
            db=db_session,
        )

        # Then: Settings should be updated
        assert isinstance(result, UserProfileSettings)
        assert result.language == "ja"
        assert result.timezone == "Asia/Tokyo"
        assert result.date_format == "YYYY-MM-DD"
        assert result.time_format == "24h"
        assert result.notification_email is True
        assert result.notification_push is False

    def test_get_profile_settings(
        self, service: UserProfileService, db_session: Session
    ) -> None:
        """Test getting user profile settings."""
        # Given: User with settings
        user = create_test_user(db_session)
        db_session.commit()

        # When: Getting profile settings
        settings = service.get_profile_settings(
            user_id=user.id,
            viewer=user,
            db=db_session,
        )

        # Then: Should return settings with defaults
        assert isinstance(settings, UserProfileSettings)
        assert settings.language == "en"  # Default
        assert settings.timezone == "UTC"  # Default
        assert settings.notification_email is True  # Default

    def test_update_privacy_settings(
        self, service: UserProfileService, db_session: Session
    ) -> None:
        """Test updating user privacy settings."""
        # Given: User
        user = create_test_user(db_session)
        db_session.commit()

        # When: Updating privacy settings
        privacy_update = UserPrivacySettingsUpdate(
            profile_visibility="organization",  # Only visible to organization members
            email_visibility="private",  # Only visible to self
            phone_visibility="department",  # Only visible to department members
            allow_direct_messages=False,
            show_online_status=True,
        )

        result = service.update_privacy_settings(
            user_id=user.id,
            settings=privacy_update,
            updater=user,
            db=db_session,
        )

        # Then: Privacy settings should be updated
        assert isinstance(result, UserPrivacySettings)
        assert result.profile_visibility == "organization"
        assert result.email_visibility == "private"
        assert result.phone_visibility == "department"
        assert result.allow_direct_messages is False
        assert result.show_online_status is True

    def test_get_privacy_settings(
        self, service: UserProfileService, db_session: Session
    ) -> None:
        """Test getting user privacy settings."""
        # Given: User
        user = create_test_user(db_session)
        db_session.commit()

        # When: Getting privacy settings
        settings = service.get_privacy_settings(
            user_id=user.id,
            viewer=user,
            db=db_session,
        )

        # Then: Should return settings with defaults
        assert isinstance(settings, UserPrivacySettings)
        assert settings.profile_visibility == "organization"  # Default
        assert settings.email_visibility == "organization"  # Default
        assert settings.allow_direct_messages is True  # Default

    def test_visibility_rules_enforcement(
        self, service: UserProfileService, db_session: Session
    ) -> None:
        """Test that privacy visibility rules are enforced."""
        # Given: User with private email visibility
        # Organization created but not used in this test
        # org = create_test_organization(db_session)
        user1 = create_test_user(db_session, email="private@example.com")
        user2 = create_test_user(db_session, email="viewer@example.com")
        db_session.commit()

        # Set user1's email to private
        service.update_privacy_settings(
            user_id=user1.id,
            settings=UserPrivacySettingsUpdate(email_visibility="private"),
            updater=user1,
            db=db_session,
        )

        # When: User2 tries to view user1's profile
        profile = service.get_user_profile(
            user_id=user1.id,
            viewer=user2,
            db=db_session,
        )

        # Then: Email should be hidden
        assert profile.email is None  # Hidden due to privacy settings
        assert profile.full_name is not None  # Name is still visible

    def test_update_profile_basic_info(
        self, service: UserProfileService, db_session: Session
    ) -> None:
        """Test updating basic profile information."""
        # Given: User
        user = create_test_user(db_session, full_name="Old Name")
        db_session.commit()

        # When: Updating profile
        update_data = UserProfileUpdate(
            full_name="New Name",
            bio="Software Engineer with 10 years experience",
            location="Tokyo, Japan",
            website="https://example.com",
        )

        result = service.update_profile(
            user_id=user.id,
            data=update_data,
            updater=user,
            db=db_session,
        )

        # Then: Profile should be updated
        assert result.full_name == "New Name"
        assert result.bio == "Software Engineer with 10 years experience"
        assert result.location == "Tokyo, Japan"
        assert result.website == "https://example.com"

    def test_profile_image_processing(
        self, service: UserProfileService, db_session: Session
    ) -> None:
        """Test profile image processing (resize, optimize)."""
        # Given: User and large image
        user = create_test_user(db_session)
        db_session.commit()

        # Create a large image that needs processing
        large_img = Image.new("RGB", (2000, 2000), color="green")
        img_io = io.BytesIO()
        large_img.save(img_io, "PNG")
        img_io.seek(0)

        # When: Uploading image
        with patch.object(service, "_process_image") as mock_process:
            mock_process.return_value = (b"processed_image", 1024)

            result = service.upload_profile_image(
                user_id=user.id,
                file_data=img_io.read(),
                filename="large.png",
                content_type="image/png",
                uploader=user,
                db=db_session,
            )

            # Then: Image should be processed
            mock_process.assert_called_once()
            assert result.size == 1024  # Processed size

    def test_profile_settings_validation(
        self, service: UserProfileService, db_session: Session
    ) -> None:
        """Test profile settings validation."""
        # Given: User
        user = create_test_user(db_session)
        db_session.commit()

        # When/Then: Invalid language code should fail (Pydantic validation)
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="String should match pattern"):
            UserProfileSettingsUpdate(language="invalid")

        # When/Then: Language not in allowed list should fail
        with pytest.raises(BusinessLogicError, match="Invalid language code"):
            service.update_profile_settings(
                user_id=user.id,
                settings=UserProfileSettingsUpdate(
                    language="xx"
                ),  # Valid pattern but not in allowed list
                updater=user,
                db=db_session,
            )

        # When/Then: Invalid timezone should fail
        with pytest.raises(BusinessLogicError, match="Invalid timezone"):
            service.update_profile_settings(
                user_id=user.id,
                settings=UserProfileSettingsUpdate(timezone="Invalid/Timezone"),
                updater=user,
                db=db_session,
            )

    def test_admin_override_privacy_settings(
        self, service: UserProfileService, db_session: Session
    ) -> None:
        """Test that admins can override privacy settings."""
        # Given: Regular user with private profile and admin
        user = create_test_user(db_session, email="private@example.com")
        admin = create_test_user(
            db_session, email="admin@example.com", is_superuser=True
        )
        db_session.commit()

        # Set user's email to private
        service.update_privacy_settings(
            user_id=user.id,
            settings=UserPrivacySettingsUpdate(email_visibility="private"),
            updater=user,
            db=db_session,
        )

        # When: Admin views user's profile
        profile = service.get_user_profile(
            user_id=user.id,
            viewer=admin,
            db=db_session,
        )

        # Then: Admin can see private information
        assert profile.email == "private@example.com"  # Visible to admin

    @patch("app.services.user_profile.storage_client")
    def test_profile_image_storage_integration(
        self,
        mock_storage: MagicMock,
        service: UserProfileService,
        db_session: Session,
        test_image: io.BytesIO,
    ) -> None:
        """Test integration with storage service."""
        # Given: User and mock storage
        user = create_test_user(db_session)
        db_session.commit()

        mock_storage.upload.return_value = "/storage/profile/123.png"

        # When: Uploading image
        result = service.upload_profile_image(
            user_id=user.id,
            file_data=test_image.read(),
            filename="profile.png",
            content_type="image/png",
            uploader=user,
            db=db_session,
        )

        # Then: Storage service should be called
        mock_storage.upload.assert_called_once()
        assert result.url == "/storage/profile/123.png"
>>>>>>> origin/main
