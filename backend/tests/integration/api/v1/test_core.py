"""Core API integration tests - basic functionality only."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from tests.conftest import create_auth_headers


class TestCoreAPI:
    """Test core API functionality that should always work."""
    
    def test_health_check(self, client: TestClient) -> None:
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_root_endpoint(self, client: TestClient) -> None:
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_openapi_docs(self, client: TestClient) -> None:
        """Test OpenAPI documentation endpoint."""
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
    
    def test_docs_endpoint(self, client: TestClient) -> None:
        """Test Swagger UI docs endpoint."""
        response = client.get("/api/v1/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestAuthenticationAPI:
    """Test authentication flow."""
    
    def test_login_flow(
        self,
        client: TestClient,
        test_admin: User
    ) -> None:
        """Test basic login flow."""
        # Test login with valid credentials
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_admin.email,
                "password": "AdminPassword123!"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client: TestClient) -> None:
        """Test login with invalid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
    
    def test_me_endpoint(
        self,
        client: TestClient,
        test_admin: User,
        admin_token: str
    ) -> None:
        """Test current user endpoint."""
        response = client.get(
            "/api/v1/users/me",
            headers=create_auth_headers(admin_token)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_admin.email
        assert data["id"] == test_admin.id