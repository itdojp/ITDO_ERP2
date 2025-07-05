"""
Keycloak test utilities and mock helpers.
"""

from contextlib import contextmanager
from typing import Dict, Any, List, Generator
from unittest.mock import patch, Mock
import jwt
import time
from datetime import datetime, timedelta

from app.core.config import get_settings


def create_keycloak_token_with_roles(
    roles: List[str],
    user_id: str = "test-user-123",
    email: str = "test@example.com",
) -> str:
    """Create a mock Keycloak JWT token with specified roles."""
    settings = get_settings()
    
    payload = {
        "sub": user_id,
        "email": email,
        "name": "Test User",
        "realm_access": {"roles": roles},
        "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "iss": f"{settings.KEYCLOAK_SERVER_URL}/auth/realms/{settings.KEYCLOAK_REALM}",
        "aud": settings.KEYCLOAK_CLIENT_ID,
        "typ": "Bearer",
    }
    
    # In tests, we use a known secret for predictable tokens
    return jwt.encode(payload, "test-secret-key", algorithm="HS256")


def create_expired_keycloak_token() -> str:
    """Create an expired Keycloak token for testing."""
    settings = get_settings()
    
    payload = {
        "sub": "test-user-123",
        "email": "test@example.com",
        "exp": int((datetime.utcnow() - timedelta(hours=1)).timestamp()),
        "iat": int((datetime.utcnow() - timedelta(hours=2)).timestamp()),
    }
    
    return jwt.encode(payload, "test-secret-key", algorithm="HS256")


@contextmanager
def mock_keycloak_token_exchange() -> Generator[Mock, None, None]:
    """Mock Keycloak token exchange response."""
    with patch("app.core.keycloak.KeycloakClient.exchange_code") as mock:
        mock.return_value = {
            "access_token": "mock-keycloak-access-token",
            "refresh_token": "mock-keycloak-refresh-token",
            "expires_in": 300,
            "token_type": "Bearer",
            "id_token": "mock-id-token",
        }
        yield mock


@contextmanager
def mock_keycloak_token_refresh() -> Generator[Mock, None, None]:
    """Mock Keycloak token refresh response."""
    with patch("app.core.keycloak.KeycloakClient.refresh_token") as mock:
        mock.return_value = {
            "access_token": "new-mock-access-token",
            "refresh_token": "new-mock-refresh-token",
            "expires_in": 300,
            "token_type": "Bearer",
        }
        yield mock


@contextmanager
def mock_keycloak_userinfo() -> Generator[Mock, None, None]:
    """Mock Keycloak userinfo response."""
    with patch("app.core.keycloak.KeycloakClient.get_userinfo") as mock:
        mock.return_value = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "name": "Test User",
            "preferred_username": "testuser",
            "given_name": "Test",
            "family_name": "User",
            "realm_access": {"roles": ["user", "admin"]},
            "groups": ["management", "sales"],
            "email_verified": True,
        }
        yield mock


@contextmanager
def mock_keycloak_introspect(active: bool = True) -> Generator[Mock, None, None]:
    """Mock Keycloak token introspection response."""
    with patch("app.core.keycloak.KeycloakClient.introspect") as mock:
        mock.return_value = {
            "active": active,
            "sub": "test-user-123",
            "email": "test@example.com",
            "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.utcnow().timestamp()),
        }
        yield mock


@contextmanager
def mock_keycloak_down() -> Generator[None, None, None]:
    """Mock Keycloak service being unavailable."""
    with patch("app.core.keycloak.KeycloakClient") as mock_class:
        mock_class.side_effect = Exception("Connection refused")
        yield


def create_mock_state_token() -> str:
    """Create a mock state token for CSRF protection."""
    import secrets
    return secrets.token_urlsafe(32)


def create_mock_pkce_verifier() -> str:
    """Create a mock PKCE verifier."""
    import secrets
    import string
    
    # PKCE verifier should be 43-128 characters from allowed set
    allowed_chars = string.ascii_letters + string.digits + "-._~"
    length = 64  # Middle of the allowed range
    return "".join(secrets.choice(allowed_chars) for _ in range(length))


def create_mock_auth_code() -> str:
    """Create a mock authorization code."""
    import secrets
    return secrets.token_urlsafe(32)


class MockKeycloakClient:
    """Mock Keycloak client for testing."""
    
    def __init__(self, settings: Any) -> None:
        """Initialize mock client."""
        self.settings = settings
        self.realm_name = settings.KEYCLOAK_REALM
        self.client_id = settings.KEYCLOAK_CLIENT_ID
        self.server_url = settings.KEYCLOAK_SERVER_URL
    
    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        """Generate mock auth URL."""
        base_url = f"{self.server_url}/auth/realms/{self.realm_name}/protocol/openid-connect/auth"
        return f"{base_url}?client_id={self.client_id}&response_type=code&redirect_uri={redirect_uri}&state={state}"
    
    def get_auth_url_with_pkce(
        self, redirect_uri: str, state: str
    ) -> tuple[str, str]:
        """Generate mock auth URL with PKCE."""
        verifier = create_mock_pkce_verifier()
        # In real implementation, challenge would be SHA256(verifier)
        challenge = "mock-challenge"
        
        base_url = self.get_auth_url(redirect_uri, state)
        url = f"{base_url}&code_challenge={challenge}&code_challenge_method=S256"
        return url, verifier
    
    def exchange_code(
        self, code: str, redirect_uri: str, code_verifier: str = None
    ) -> Dict[str, Any]:
        """Mock code exchange."""
        return {
            "access_token": "mock-access-token",
            "refresh_token": "mock-refresh-token",
            "expires_in": 300,
            "token_type": "Bearer",
        }
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Mock token verification."""
        if token == "invalid-token":
            raise Exception("Token is not active")
        
        return {
            "sub": "test-user-123",
            "email": "test@example.com",
            "realm_access": {"roles": ["user"]},
        }
    
    def get_userinfo(self, token: str) -> Dict[str, Any]:
        """Mock userinfo retrieval."""
        return {
            "sub": "test-user-123",
            "email": "test@example.com",
            "name": "Test User",
            "realm_access": {"roles": ["user", "admin"]},
            "groups": ["management"],
        }
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Mock token refresh."""
        return {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "expires_in": 300,
            "token_type": "Bearer",
        }
    
    def logout(self, refresh_token: str) -> None:
        """Mock logout."""
        pass


@contextmanager
def use_mock_keycloak_client() -> Generator[None, None, None]:
    """Replace real Keycloak client with mock for testing."""
    with patch("app.core.keycloak.KeycloakClient", MockKeycloakClient):
        yield