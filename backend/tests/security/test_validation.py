"""Security tests for input validation."""

import pytest
from fastapi.testclient import TestClient


class TestInputValidation:
    """Test input validation and security."""

    @pytest.mark.parametrize("email,password", [
        ("test@example.com' OR '1'='1", "' OR '1'='1"),  # SQL injection
        ("test@example.com'; DROP TABLE users;--", "password"),  # SQL injection
        ("test@example.com", "' OR 1=1--"),  # SQL injection in password
    ])
    def test_sql_injection_prevention(self, client: TestClient, email: str, password: str) -> None:
        """Test that SQL injection attempts are prevented."""
        # When: Attempting SQL injection
        response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password}
        )
        
        # Then: Should handle as normal authentication failure
        assert response.status_code in [401, 422]  # Either auth failure or validation error
        # Should not expose database errors
        if response.status_code == 401:
            assert "syntax" not in response.text.lower()
            assert "sql" not in response.text.lower()

    @pytest.mark.parametrize("password", [
        "short",              # Too short
        "alllowercase123",    # No uppercase
        "ALLUPPERCASE123",    # No lowercase
        "NoNumbers!",         # No numbers
        "NoSpecialChar123",   # No special characters
        "12345678",          # Only numbers
        "!@#$%^&*",          # Only special chars
    ])
    def test_weak_password_rejection(self, client: TestClient, admin_token: str, password: str) -> None:
        """Test that weak passwords are rejected."""
        # When: Creating user with weak password
        response = client.post(
            "/api/v1/users",
            json={
                "email": "weakpass@example.com",
                "password": password,
                "full_name": "Weak Password User"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Then: Should return validation error
        assert response.status_code == 422

    def test_xss_prevention_in_user_data(self, client: TestClient, admin_token: str) -> None:
        """Test that XSS attempts in user data are handled safely."""
        # When: Creating user with XSS attempt in name
        response = client.post(
            "/api/v1/users",
            json={
                "email": "xss@example.com",
                "password": "SecurePass123!",
                "full_name": "<script>alert('XSS')</script>"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Then: Should accept but data should be stored safely
        assert response.status_code == 201
        data = response.json()
        # The data should be stored as-is (escaped when rendered)
        assert data["full_name"] == "<script>alert('XSS')</script>"

    @pytest.mark.parametrize("token", [
        "Bearer",                    # Missing token
        "InvalidBearer token123",    # Invalid format
        "Bearer ",                   # Empty token
        "",                         # Empty header
        "Basic dGVzdDp0ZXN0",       # Wrong auth type
    ])
    def test_invalid_authorization_header(self, client: TestClient, token: str) -> None:
        """Test various invalid authorization headers."""
        # When: Using invalid authorization header
        headers = {"Authorization": token} if token else {}
        response = client.get("/api/v1/users/me", headers=headers)
        
        # Then: Should return 401
        assert response.status_code == 401

    def test_rate_limiting_simulation(self, client: TestClient) -> None:
        """Test behavior under rapid requests (rate limiting simulation)."""
        # When: Making many rapid requests
        responses = []
        for _ in range(20):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "ratelimit@example.com",
                    "password": "WrongPassword123!"
                }
            )
            responses.append(response.status_code)
        
        # Then: All should be handled (actual rate limiting would be implemented later)
        assert all(status == 401 for status in responses)

    def test_long_input_handling(self, client: TestClient, admin_token: str) -> None:
        """Test handling of excessively long inputs."""
        # When: Sending very long inputs
        response = client.post(
            "/api/v1/users",
            json={
                "email": "a" * 100 + "@example.com",  # Very long email
                "password": "SecurePass123!",
                "full_name": "A" * 1000  # Very long name
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Then: Should return validation error
        assert response.status_code == 422