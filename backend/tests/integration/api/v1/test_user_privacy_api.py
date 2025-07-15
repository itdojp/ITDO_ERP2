"""Integration tests for user privacy API."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from tests.conftest import create_auth_headers


class TestUserPrivacyAPI:
    """Test cases for user privacy API endpoints."""

    def test_get_privacy_settings_success(
        self, client: TestClient, db_session: Session, user_token: str, test_user: User
    ) -> None:
        """Test getting user privacy settings successfully."""
        response = client.get(
            "/api/v1/users/privacy/me",
            headers=create_auth_headers(user_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert "profile_visibility" in data
        assert "email_visibility" in data
        assert "phone_visibility" in data
        assert "show_online_status" in data
        assert "allow_direct_messages" in data

    def test_update_privacy_settings_success(
        self, client: TestClient, db_session: Session, user_token: str, test_user: User
    ) -> None:
        """Test updating user privacy settings successfully."""
        # First create privacy settings
        create_data = {
            "profile_visibility": "public",
            "email_visibility": "public",
            "phone_visibility": "public",
            "show_online_status": True,
            "allow_direct_messages": True,
        }
        client.post(
            "/api/v1/users/privacy/me",
            json=create_data,
            headers=create_auth_headers(user_token),
        )

        # Then update them
        update_data = {
            "profile_visibility": "private",
            "email_visibility": "department",
            "phone_visibility": "private",
            "show_online_status": False,
            "allow_direct_messages": False,
        }

        response = client.put(
            "/api/v1/users/privacy/me",
            json=update_data,
            headers=create_auth_headers(user_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["profile_visibility"] == "private"
        assert data["email_visibility"] == "department"
        assert data["phone_visibility"] == "private"
        assert data["show_online_status"] is False
        assert data["allow_direct_messages"] is False

    def test_set_all_private_success(
        self, client: TestClient, db_session: Session, user_token: str, test_user: User
    ) -> None:
        """Test setting all privacy settings to private."""
        response = client.post(
            "/api/v1/users/privacy/me/set-all-private",
            headers=create_auth_headers(user_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["profile_visibility"] == "private"
        assert data["email_visibility"] == "private"
        assert data["phone_visibility"] == "private"
        assert data["show_online_status"] is False
        assert data["allow_direct_messages"] is False

    def test_check_profile_visibility_success(
        self, client: TestClient, db_session: Session, user_token: str, test_user: User
    ) -> None:
        """Test checking if profile is visible."""
        # Create another user to test visibility
        from tests.factories import UserFactory

        other_user = UserFactory.create_with_password(
            db_session, email="other@test.com", password="password123"
        )

        response = client.get(
            f"/api/v1/users/privacy/check/profile/{other_user.id}",
            headers=create_auth_headers(user_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert "allowed" in data
        assert isinstance(data["allowed"], bool)

    def test_get_privacy_settings_unauthorized(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test getting privacy settings without authentication."""
        response = client.get("/api/v1/users/privacy/me")

        assert response.status_code == 403

    def test_update_privacy_settings_unauthorized(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test updating privacy settings without authentication."""
        update_data = {"profile_visibility": "private"}

        response = client.put("/api/v1/users/privacy/me", json=update_data)

        assert response.status_code == 403

    def test_invalid_visibility_level(
        self, client: TestClient, db_session: Session, user_token: str, test_user: User
    ) -> None:
        """Test updating privacy settings with invalid visibility level."""
        update_data = {"profile_visibility": "invalid_level"}

        response = client.put(
            "/api/v1/users/privacy/me",
            json=update_data,
            headers=create_auth_headers(user_token),
        )

        assert response.status_code == 422
