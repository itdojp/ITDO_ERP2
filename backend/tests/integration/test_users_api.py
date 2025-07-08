"""Integration tests for users API."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User


class TestUsersAPI:
    """Test users API endpoints."""

    def test_create_user_as_admin(
        self, client: TestClient, admin_token: str, db_session: Session
    ) -> None:
        """Test user creation by admin."""
        # When: Creating user as admin
        response = client.post(
            "/api/v1/users",
            json={
                "email": "newuser@example.com",
                "password": "NewUserPass123!",
                "full_name": "New User",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: User should be created
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "hashed_password" not in data  # Should not expose password

    def test_create_user_duplicate_email(
        self, client: TestClient, admin_token: str, test_user: User
    ) -> None:
        """Test creating user with duplicate email."""
        # When: Creating user with existing email
        response = client.post(
            "/api/v1/users",
            json={
                "email": test_user.email,
                "password": "Password123!",
                "full_name": "Duplicate User",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: Should return 409
        assert response.status_code == 409
        assert response.json()["code"] == "USER001"

    def test_create_user_as_regular_user(
        self, client: TestClient, user_token: str
    ) -> None:
        """Test that regular users cannot create users."""
        # When: Trying to create user as regular user
        response = client.post(
            "/api/v1/users",
            json={
                "email": "forbidden@example.com",
                "password": "Password123!",
                "full_name": "Forbidden User",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Then: Should return 403
        assert response.status_code == 403
        assert response.json()["code"] == "AUTH004"

    def test_create_user_no_auth(self, client: TestClient) -> None:
        """Test creating user without authentication."""
        # When: Creating user without auth
        response = client.post(
            "/api/v1/users",
            json={
                "email": "noauth@example.com",
                "password": "Password123!",
                "full_name": "No Auth User",
            },
        )

        # Then: Should return 401
        assert response.status_code == 401

    def test_create_user_weak_password(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Test creating user with weak password."""
        # When: Creating user with weak password
        response = client.post(
            "/api/v1/users",
            json={
                "email": "weakpass@example.com",
                "password": "weak",
                "full_name": "Weak Pass User",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: Should return 422
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any(error["loc"] == ["body", "password"] for error in errors)

    def test_get_current_user(
        self, client: TestClient, test_user, user_token: str
    ) -> None:
        """Test getting current user info."""
        # When: Getting current user
        response = client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {user_token}"}
        )

        # Then: Should return user info
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert data["is_active"] is True
        assert "hashed_password" not in data

    def test_get_current_user_no_auth(self, client: TestClient) -> None:
        """Test getting current user without auth."""
        # When: Getting current user without auth
        response = client.get("/api/v1/users/me")

        # Then: Should return 401
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client: TestClient) -> None:
        """Test getting current user with invalid token."""
        # When: Using invalid token
        response = client.get(
            "/api/v1/users/me", headers={"Authorization": "Bearer invalid.token.here"}
        )

        # Then: Should return 401
        assert response.status_code == 401

    def test_create_user_with_is_active_false(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Test creating inactive user."""
        # When: Creating inactive user
        response = client.post(
            "/api/v1/users",
            json={
                "email": "inactive_new@example.com",
                "password": "InactivePass123!",
                "full_name": "Inactive New User",
                "is_active": False,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: User should be created as inactive
        assert response.status_code == 201
        assert response.json()["is_active"] is False

    @pytest.mark.parametrize(
        "email",
        [
            "invalid-email",
            "@example.com",
            "user@",
            "user@.com",
            "",
        ],
    )
    def test_create_user_invalid_email(
        self, client: TestClient, admin_token: str, email: str
    ) -> None:
        """Test creating user with invalid email format."""
        # When: Creating user with invalid email
        response = client.post(
            "/api/v1/users",
            json={
                "email": email,
                "password": "Password123!",
                "full_name": "Invalid Email User",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: Should return 422
        assert response.status_code == 422
