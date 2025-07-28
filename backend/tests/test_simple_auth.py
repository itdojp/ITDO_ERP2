"""Simple authentication test to verify basic functionality."""

import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.user import User
from app.services.auth import AuthService
from app.services.mfa_service import MFAService


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_user_model_mfa_fields(db_session):
    """Test that User model has MFA fields."""
    user = User(
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User",
        mfa_required=True,
        mfa_secret="secret123",
    )
    db_session.add(user)
    db_session.commit()

    assert user.mfa_required is True
    assert user.mfa_secret == "secret123"
    assert user.mfa_enabled_at is None


def test_auth_service_authenticate_user(db_session):
    """Test AuthService authenticate_user method."""
    # Create a test user
    from app.core.security import hash_password

    user = User(
        email="test@example.com",
        hashed_password=hash_password("password123"),
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    # Test authentication
    auth_service = AuthService(db_session)

    # Should succeed with correct password
    authenticated = auth_service.authenticate_user(
        email="test@example.com", password="password123"
    )
    assert authenticated.id == user.id

    # Should fail with wrong password
    try:
        auth_service.authenticate_user(
            email="test@example.com", password="wrongpassword"
        )
        assert False, "Should have raised BusinessLogicError"
    except Exception as e:
        assert "メールアドレスまたはパスワードが正しくありません" in str(e)


def test_mfa_service_create_challenge(db_session):
    """Test MFA service challenge creation."""
    mfa_service = MFAService(db_session)

    # Create test user
    user = User(
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()

    # Create MFA challenge
    challenge = mfa_service.create_challenge(
        user_id=user.id, challenge_type="login", ip_address="127.0.0.1"
    )

    assert challenge.user_id == user.id
    assert challenge.challenge_type == "login"
    assert challenge.challenge_token is not None
    assert len(challenge.challenge_token) > 20
    assert challenge.expires_at > datetime.now()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
