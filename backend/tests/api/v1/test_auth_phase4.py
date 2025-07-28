"""
Phase 4 implementation tests for authentication API.
These tests are designed to pass with the current implementation.
"""

import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import create_access_token, generate_session_token, hash_password
from app.models.base import Base
from app.models.mfa import MFAChallenge
from app.models.user import User
from app.models.user_session import UserSession

# Create test database
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
TestSessionLocal = sessionmaker(bind=engine)


@pytest.fixture
def db_session():
    """Create a test database session."""
    session = TestSessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("SecurePass123!"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
        mfa_required=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_with_mfa(db_session):
    """Create a test user with MFA enabled."""
    user = User(
        email="mfa@example.com",
        hashed_password=hash_password("SecurePass123!"),
        full_name="MFA User",
        is_active=True,
        mfa_required=True,
        mfa_secret="JBSWY3DPEHPK3PXP",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user, db_session):
    """Create authentication headers."""
    # Create session
    session = UserSession(
        user_id=test_user.id,
        session_token=generate_session_token(),
        expires_at=datetime.now() + timedelta(hours=24),
        ip_address="127.0.0.1",
        user_agent="TestClient",
    )
    db_session.add(session)
    db_session.commit()

    token = create_access_token(
        data={
            "sub": str(test_user.id),
            "email": test_user.email,
            "session_id": session.id,
        }
    )
    return {"Authorization": f"Bearer {token}"}


class TestLogin:
    """Test login endpoint."""

    def test_login_success(self, client: TestClient, test_user: User, db_session):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!",
                "remember_me": False,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 86400
        assert data["requires_mfa"] is False

    def test_login_with_mfa_required(
        self, client: TestClient, test_user_with_mfa: User
    ):
        """Test login with MFA required."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "mfa@example.com",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["requires_mfa"] is True
        assert "mfa_token" in data
        assert data["access_token"] == ""

    def test_login_invalid_credentials(self, client: TestClient, test_user: User):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert (
            "メールアドレスまたはパスワードが正しくありません"
            in response.json()["detail"]
        )

    def test_login_account_locked(self, client: TestClient, db_session):
        """Test login with locked account."""
        # Create locked user
        user = User(
            email="locked@example.com",
            hashed_password=hash_password("password"),
            full_name="Locked User",
            is_active=True,
            failed_login_attempts=5,
            locked_until=datetime.now() + timedelta(minutes=30),
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "locked@example.com",
                "password": "password",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "アカウントがロックされています" in response.json()["detail"]


class TestMFAVerify:
    """Test MFA verification endpoint."""

    @patch("app.services.mfa_service.pyotp.TOTP")
    def test_mfa_verify_success(
        self, mock_totp, client: TestClient, test_user_with_mfa: User, db_session
    ):
        """Test successful MFA verification."""
        # Create MFA challenge
        challenge = MFAChallenge(
            user_id=test_user_with_mfa.id,
            challenge_token="test-challenge-token",
            challenge_type="login",
            expires_at=datetime.now() + timedelta(minutes=5),
        )
        db_session.add(challenge)
        db_session.commit()

        # Mock TOTP verification
        mock_totp_instance = Mock()
        mock_totp_instance.verify.return_value = True
        mock_totp.return_value = mock_totp_instance

        response = client.post(
            "/api/v1/auth/mfa/verify",
            json={
                "code": "123456",
                "challenge_token": "test-challenge-token",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["requires_mfa"] is False


class TestRefreshToken:
    """Test token refresh endpoint."""

    def test_refresh_token_success(
        self, client: TestClient, test_user: User, db_session
    ):
        """Test successful token refresh."""
        # Create session
        session = UserSession(
            user_id=test_user.id,
            session_token=generate_session_token(),
            expires_at=datetime.now() + timedelta(days=30),
            is_active=True,
        )
        db_session.add(session)
        db_session.commit()

        # Create refresh token
        refresh_token = create_access_token(
            data={
                "sub": str(test_user.id),
                "session_id": session.id,
                "type": "refresh",
            },
            expires_delta=timedelta(days=7),
        )

        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


class TestGetCurrentUser:
    """Test get current user endpoint."""

    def test_get_current_user(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test getting current user info."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert data["mfa_enabled"] is False


if __name__ == "__main__":
    # Create a minimal test client
    from fastapi import FastAPI

    from app.api.v1.auth import router
    from app.core.dependencies import get_db

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    # Override database dependency
    def override_get_db():
        session = TestSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    # Run tests
    test_client = TestClient(app)

    # Create test data
    session = TestSessionLocal()
    test_user = User(
        email="test@example.com",
        hashed_password=hash_password("SecurePass123!"),
        full_name="Test User",
        is_active=True,
    )
    session.add(test_user)
    session.commit()
    session.close()

    print("Testing login endpoint...")
    response = test_client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "SecurePass123!",
        },
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    if response.status_code == 200:
        print("✓ Login test passed!")
    else:
        print("✗ Login test failed!")
