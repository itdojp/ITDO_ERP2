"""Integration tests for authentication API."""

import pytest
from fastapi.testclient import TestClient
from datetime import timedelta
import time

from app.core.security import create_access_token, create_refresh_token
from app.models.user import User


class TestAuthAPI:
    """Test authentication API endpoints."""

    def test_login_success(self, client: TestClient, db_session, test_user) -> None:
        """Test successful login."""
        # When: Logging in with correct credentials
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPassword123!"
            }
        )
        
        # Then: Should return tokens
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 86400  # 24 hours

    def test_login_invalid_password(self, client: TestClient, test_user) -> None:
        """Test login with invalid password."""
        # When: Logging in with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "WrongPassword123!"
            }
        )
        
        # Then: Should return 401
        assert response.status_code == 401
        assert response.json()["code"] == "AUTH001"

    def test_login_nonexistent_user(self, client: TestClient) -> None:
        """Test login with non-existent user."""
        # When: Logging in with non-existent email
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "Password123!"
            }
        )
        
        # Then: Should return 401
        assert response.status_code == 401
        assert response.json()["code"] == "AUTH001"

    def test_login_inactive_user(self, client: TestClient, db_session) -> None:
        """Test login with inactive user."""
        # Given: Inactive user
        user = User.create(
            db_session,
            email="inactive@example.com",
            password="InactivePass123!",
            full_name="Inactive User",
            is_active=False
        )
        db_session.commit()
        
        # When: Trying to login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "inactive@example.com",
                "password": "InactivePass123!"
            }
        )
        
        # Then: Should return 401
        assert response.status_code == 401
        assert response.json()["code"] == "AUTH001"

    def test_refresh_token_success(self, client: TestClient, test_user) -> None:
        """Test successful token refresh."""
        # Given: Valid refresh token
        refresh_token = create_refresh_token({"sub": str(test_user.id)})
        
        # When: Refreshing token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        # Then: Should return new tokens
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_invalid(self, client: TestClient) -> None:
        """Test refresh with invalid token."""
        # When: Using invalid refresh token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )
        
        # Then: Should return 401
        assert response.status_code == 401
        assert response.json()["code"] == "AUTH003"

    def test_refresh_token_expired(self, client: TestClient, test_user) -> None:
        """Test refresh with expired token."""
        # Given: Expired refresh token
        expired_token = create_refresh_token(
            {"sub": str(test_user.id)},
            expires_delta=timedelta(seconds=-1)
        )
        
        # When: Using expired token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": expired_token}
        )
        
        # Then: Should return 401
        assert response.status_code == 401
        assert response.json()["code"] == "AUTH002"

    def test_login_invalid_email_format(self, client: TestClient) -> None:
        """Test login with invalid email format."""
        # When: Using invalid email format
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "invalid-email",
                "password": "Password123!"
            }
        )
        
        # Then: Should return 422
        assert response.status_code == 422

    def test_login_missing_fields(self, client: TestClient) -> None:
        """Test login with missing fields."""
        # When: Missing password
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com"}
        )
        
        # Then: Should return 422
        assert response.status_code == 422

    def test_login_response_time(self, client: TestClient, test_user) -> None:
        """Test login API response time."""
        # When: Measuring login response time
        start_time = time.time()
        
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPassword123!"
            }
        )
        
        response_time = (time.time() - start_time) * 1000
        
        # Then: Should respond within 200ms
        assert response.status_code == 200
        assert response_time < 200