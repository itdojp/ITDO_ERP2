"""Integration tests for user preferences API."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from tests.conftest import create_auth_headers


class TestUserPreferencesAPI:
    """Test cases for user preferences API endpoints."""

    def test_get_preferences_success(
        self, client: TestClient, db_session: Session, user_token: str, test_user: User
    ) -> None:
        """Test getting user preferences successfully."""
        response = client.get(
            "/api/v1/users/preferences/me",
            headers=create_auth_headers(user_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert "language" in data
        assert "timezone" in data
        assert "theme" in data
        assert "notifications_email" in data
        assert "notifications_push" in data

    def test_update_preferences_success(
        self, client: TestClient, db_session: Session, user_token: str, test_user: User
    ) -> None:
        """Test updating user preferences successfully."""
        # First create preferences
        create_data = {
            "language": "en",
            "timezone": "UTC",
            "theme": "light",
            "notifications_email": True,
            "notifications_push": True,
        }
        client.post(
            "/api/v1/users/preferences/me",
            json=create_data,
            headers=create_auth_headers(user_token),
        )

        # Then update them
        update_data = {
            "language": "ja",
            "timezone": "Asia/Tokyo",
            "theme": "dark",
            "notifications_email": False,
        }

        response = client.put(
            "/api/v1/users/preferences/me",
            json=update_data,
            headers=create_auth_headers(user_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "ja"
        assert data["timezone"] == "Asia/Tokyo"
        assert data["theme"] == "dark"
        assert data["notifications_email"] is False

    def test_update_preferences_invalid_language(
        self, client: TestClient, db_session: Session, user_token: str, test_user: User
    ) -> None:
        """Test updating preferences with invalid language."""
        update_data = {"language": "invalid_lang"}

        response = client.put(
            "/api/v1/users/preferences/me",
            json=update_data,
            headers=create_auth_headers(user_token),
        )

        assert response.status_code == 422

    def test_get_preferences_unauthorized(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test getting preferences without authentication."""
        response = client.get("/api/v1/users/preferences/me")

        assert response.status_code == 403

    def test_update_preferences_unauthorized(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test updating preferences without authentication."""
        update_data = {"language": "ja"}

        response = client.put(
            "/api/v1/users/preferences/me", 
            json=update_data
        )

        assert response.status_code == 403

    def test_get_locale_info_success(
        self, client: TestClient, db_session: Session, user_token: str, test_user: User
    ) -> None:
        """Test getting user locale information."""
        response = client.get(
            "/api/v1/users/preferences/me/locale",
            headers=create_auth_headers(user_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert "language" in data
        assert "timezone" in data
        assert "locale_string" in data
        assert "currency" in data