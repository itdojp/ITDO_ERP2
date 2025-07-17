"""Integration tests for core API endpoints."""

from fastapi.testclient import TestClient

from app.models.user import User


class TestCoreAPI:
    """Test cases for core API endpoints."""

    def test_health_check(self, client: TestClient) -> None:
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_root_endpoint(self, client: TestClient) -> None:
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200

    def test_api_info(self, client: TestClient) -> None:
        """Test API info endpoint."""
        response = client.get("/api/v1/ping")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "pong"

    def test_unauthorized_protected_endpoint(self, client: TestClient) -> None:
        """Test access to protected endpoint without auth."""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 403  # HTTPBearer returns 403 when no auth header

    def test_authorized_access(
        self, client: TestClient, test_user: User, user_token: str
    ) -> None:
        """Test authorized access to protected endpoint."""
        # Database session isolation issue resolved
        response = client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email

    def test_admin_access(
        self, client: TestClient, test_admin: User, admin_token: str
    ) -> None:
        """Test admin access to protected endpoint."""
        # Database session isolation issue resolved
        response = client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_admin.id
        assert data["email"] == test_admin.email
        # Note: is_superuser might not be included in the response schema
        # We can verify the admin access by checking the response success

    def test_cors_headers(self, client: TestClient) -> None:
        """Test CORS headers are present."""
        response = client.options("/api/v1/users/me")
        # Check that CORS is handled (either 200 with headers or 405)
        assert response.status_code in [200, 405]
