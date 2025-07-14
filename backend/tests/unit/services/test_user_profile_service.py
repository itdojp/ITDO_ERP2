"""Tests for user profile service methods."""

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import NotFound, PermissionDenied
from app.services.user import UserService
from tests.factories import create_test_user


class TestUserProfileService:
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
