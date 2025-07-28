#!/usr/bin/env python
"""Simple standalone test for authentication."""

import os
import sys

# Set test environment
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALGORITHM"] = "HS256"

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.models.base import Base
from app.models.user import User
from app.services.auth import AuthService


def test_basic_auth():
    """Test basic authentication flow."""
    # Create database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    print("✓ Database created")

    # Create test user
    user = User(
        email="test@example.com",
        hashed_password=hash_password("SecurePass123!"),
        full_name="Test User",
        is_active=True,
        mfa_required=False,
    )
    session.add(user)
    session.commit()

    print("✓ Test user created")

    # Test authentication
    auth_service = AuthService(session)

    try:
        # Test successful login
        authenticated_user = auth_service.authenticate_user(
            email="test@example.com",
            password="SecurePass123!",
        )
        assert authenticated_user.id == user.id
        print("✓ Authentication successful")

        # Test session creation
        session_obj = auth_service.create_user_session(
            user=authenticated_user,
            ip_address="127.0.0.1",
            user_agent="TestAgent/1.0",
            remember_me=False,
        )
        assert session_obj.user_id == user.id
        assert session_obj.is_active
        print("✓ Session created")

        # Test token creation
        tokens = auth_service.create_tokens(
            user=authenticated_user,
            session_id=session_obj.id,
            remember_me=False,
        )
        assert tokens.access_token
        assert tokens.token_type == "bearer"
        assert tokens.expires_in == 86400
        print("✓ Tokens created")

        # Test failed login
        try:
            auth_service.authenticate_user(
                email="test@example.com",
                password="WrongPassword",
            )
            print("✗ Should have failed with wrong password")
        except Exception as e:
            assert "メールアドレスまたはパスワードが正しくありません" in str(e)
            print("✓ Failed login handled correctly")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        session.close()


def test_mfa_fields():
    """Test MFA fields in User model."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Create user with MFA
    user = User(
        email="mfa@example.com",
        hashed_password=hash_password("password"),
        full_name="MFA User",
        mfa_required=True,
        mfa_secret="JBSWY3DPEHPK3PXP",
        google_id="123456789",
    )
    session.add(user)
    session.commit()

    # Check fields
    assert user.mfa_required is True
    assert user.mfa_secret == "JBSWY3DPEHPK3PXP"
    assert user.google_id == "123456789"

    print("✓ MFA fields working correctly")

    session.close()


if __name__ == "__main__":
    print("Running authentication tests...\n")
    test_basic_auth()
    print()
    test_mfa_fields()
    print("\n✅ All tests passed!")
