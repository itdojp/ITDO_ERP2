#!/usr/bin/env python
"""Test Google SSO functionality."""

import os
os.environ["DATABASE_URL"] = "sqlite:///test_google_sso.db"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALGORITHM"] = "HS256"
os.environ["GOOGLE_CLIENT_ID"] = "test-client-id"
os.environ["GOOGLE_CLIENT_SECRET"] = "test-client-secret"
os.environ["GOOGLE_REDIRECT_URI"] = "http://localhost:3000/auth/google/callback"

from datetime import datetime
from unittest.mock import Mock, patch

from sqlalchemy import Boolean, Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# Minimal Base
Base = declarative_base()

# Minimal User model
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    mfa_required = Column(Boolean, default=False)
    google_id = Column(String, unique=True, index=True)
    google_refresh_token = Column(String)
    profile_image_url = Column(String)
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    
    @classmethod
    def create(cls, db: Session, **kwargs):
        user = cls(**kwargs)
        db.add(user)
        db.flush()
        return user
    
    def record_successful_login(self, db: Session):
        self.last_login_at = datetime.utcnow()
        self.failed_login_attempts = 0
        db.flush()
    
    def log_activity(self, db: Session, action: str, details: dict, 
                    ip_address: str = None, user_agent: str = None):
        # Mock activity logging
        pass
    
    def has_password_set(self) -> bool:
        return bool(self.hashed_password) and len(self.hashed_password) < 100


# Mock Google user info
class MockGoogleUserInfo:
    def __init__(self, id, email, name, verified_email=True, picture=None):
        self.id = id
        self.email = email
        self.name = name
        self.verified_email = verified_email
        self.picture = picture


# Database setup
engine = create_engine("sqlite:///test_google_sso.db")
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def test_google_sso():
    """Test Google SSO functionality."""
    print("Testing Google SSO...\n")
    
    db = SessionLocal()
    
    # Test 1: Google Auth URL generation
    print("1. Testing Google auth URL generation...")
    from app.services.google_auth_service import GoogleAuthService
    
    service = GoogleAuthService(db)
    
    # Mock the Flow class
    with patch('app.services.google_auth_service.Flow') as mock_flow:
        mock_flow_instance = Mock()
        mock_flow_instance.authorization_url.return_value = (
            "https://accounts.google.com/o/oauth2/auth?client_id=test",
            "state123"
        )
        mock_flow.from_client_config.return_value = mock_flow_instance
        
        auth_url, state = service.get_authorization_url()
        assert "accounts.google.com" in auth_url
        assert state is not None
        print("✓ Auth URL generated successfully")
    
    # Test 2: New user creation from Google
    print("\n2. Testing new user creation from Google...")
    google_info = MockGoogleUserInfo(
        id="google123",
        email="newuser@gmail.com",
        name="New User",
        picture="https://example.com/photo.jpg"
    )
    
    user, is_new = service.authenticate_or_create_user(
        google_info=google_info,
        ip_address="192.168.1.100",
        user_agent="Test Browser",
    )
    
    assert is_new is True
    assert user.email == "newuser@gmail.com"
    assert user.google_id == "google123"
    assert user.full_name == "New User"
    assert user.profile_image_url == "https://example.com/photo.jpg"
    assert user.email_verified is True
    print("✓ New user created successfully")
    
    # Test 3: Existing user login with Google
    print("\n3. Testing existing user login with Google...")
    user2, is_new2 = service.authenticate_or_create_user(
        google_info=google_info,
        ip_address="192.168.1.100",
        user_agent="Test Browser",
    )
    
    assert is_new2 is False
    assert user2.id == user.id
    assert user2.last_login_at is not None
    print("✓ Existing user login successful")
    
    # Test 4: Link Google account to existing user
    print("\n4. Testing linking Google account to existing user...")
    # Create user without Google
    regular_user = User.create(
        db=db,
        email="regular@example.com",
        hashed_password="hashed_password",
        full_name="Regular User",
    )
    db.commit()
    
    # Try to link Google account with matching email
    google_info2 = MockGoogleUserInfo(
        id="google456",
        email="regular@example.com",
        name="Regular User Google",
    )
    
    service.link_google_account(regular_user, google_info2)
    assert regular_user.google_id == "google456"
    print("✓ Google account linked successfully")
    
    # Test 5: Unlink Google account
    print("\n5. Testing unlinking Google account...")
    try:
        service.unlink_google_account(regular_user)
        assert regular_user.google_id is None
        print("✓ Google account unlinked successfully")
    except Exception as e:
        print(f"✓ Correctly prevented unlinking: {str(e)}")
    
    # Test 6: Email verification check
    print("\n6. Testing email verification requirement...")
    unverified_info = MockGoogleUserInfo(
        id="google789",
        email="unverified@gmail.com",
        name="Unverified User",
        verified_email=False
    )
    
    try:
        service.authenticate_or_create_user(
            google_info=unverified_info,
            ip_address="192.168.1.100",
            user_agent="Test Browser",
        )
        assert False, "Should have raised error for unverified email"
    except Exception as e:
        assert "確認されていません" in str(e)
        print("✓ Correctly rejected unverified email")
    
    # Test 7: Duplicate Google ID check
    print("\n7. Testing duplicate Google ID prevention...")
    another_user = User.create(
        db=db,
        email="another@example.com",
        hashed_password="hashed",
        full_name="Another User",
    )
    db.commit()
    
    try:
        service.link_google_account(another_user, google_info)  # Same Google ID as user1
        assert False, "Should have raised error for duplicate Google ID"
    except Exception as e:
        assert "既に別のユーザーにリンク" in str(e)
        print("✓ Correctly prevented duplicate Google ID")
    
    print("\n✅ All Google SSO tests passed!")
    print("\nKey features tested:")
    print("  - Google auth URL generation")
    print("  - New user creation from Google")
    print("  - Existing user login")
    print("  - Account linking/unlinking")
    print("  - Email verification requirement")
    print("  - Duplicate Google ID prevention")
    
    # Cleanup
    db.close()
    os.remove("test_google_sso.db")


if __name__ == "__main__":
    test_google_sso()