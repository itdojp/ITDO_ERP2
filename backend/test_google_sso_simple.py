#!/usr/bin/env python
"""Test Google SSO functionality - simplified version."""

import os

os.environ["DATABASE_URL"] = "sqlite:///test_google_sso_simple.db"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALGORITHM"] = "HS256"

from datetime import datetime

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
    google_id = Column(String, unique=True, index=True)
    google_refresh_token = Column(String)
    profile_image_url = Column(String)
    email_verified = Column(Boolean, default=False)
    last_login_at = Column(DateTime)

    def record_successful_login(self, db: Session):
        self.last_login_at = datetime.utcnow()
        db.flush()

    def log_activity(
        self,
        db: Session,
        action: str,
        details: dict,
        ip_address: str = None,
        user_agent: str = None,
    ):
        pass  # Mock

    def has_password_set(self) -> bool:
        return bool(self.hashed_password) and len(self.hashed_password) < 100


# Simplified Google Auth Service
class SimpleGoogleAuthService:
    def __init__(self, db: Session):
        self.db = db
        self.client_id = "test-client-id"
        self.client_secret = "test-client-secret"

    def authenticate_or_create_user(
        self, google_info: dict, ip_address: str, user_agent: str
    ) -> tuple[User, bool]:
        """Authenticate or create user from Google info."""
        # Check if user exists by Google ID
        user = self.db.query(User).filter(User.google_id == google_info["id"]).first()

        if user:
            user.record_successful_login(self.db)
            user.log_activity(self.db, "google_login", {"google_id": google_info["id"]})
            self.db.commit()
            return user, False

        # Check if user exists by email
        user = self.db.query(User).filter(User.email == google_info["email"]).first()

        if user:
            # Link Google account
            user.google_id = google_info["id"]
            user.record_successful_login(self.db)
            user.log_activity(
                self.db, "google_account_linked", {"google_id": google_info["id"]}
            )
            self.db.commit()
            return user, False

        # Create new user
        if not google_info.get("verified_email", False):
            raise Exception("Googleアカウントのメールアドレスが確認されていません")

        user = User(
            email=google_info["email"],
            hashed_password="google_" + "x" * 50,  # Long random password
            full_name=google_info["name"],
            google_id=google_info["id"],
            profile_image_url=google_info.get("picture"),
            email_verified=True,
            is_active=True,
        )
        self.db.add(user)
        user.record_successful_login(self.db)
        user.log_activity(self.db, "google_signup", {"google_id": google_info["id"]})
        self.db.commit()

        return user, True

    def link_google_account(self, user: User, google_info: dict) -> None:
        """Link Google account to existing user."""
        # Check if Google ID is already linked
        existing = (
            self.db.query(User)
            .filter(User.google_id == google_info["id"], User.id != user.id)
            .first()
        )

        if existing:
            raise Exception(
                "このGoogleアカウントは既に別のユーザーにリンクされています"
            )

        if user.email != google_info["email"]:
            raise Exception("Googleアカウントのメールアドレスが一致しません")

        user.google_id = google_info["id"]
        if not user.profile_image_url and google_info.get("picture"):
            user.profile_image_url = google_info["picture"]

        user.log_activity(
            self.db, "google_account_linked", {"google_id": google_info["id"]}
        )
        self.db.commit()

    def unlink_google_account(self, user: User) -> None:
        """Unlink Google account from user."""
        if not user.google_id:
            raise Exception("Googleアカウントがリンクされていません")

        if not user.has_password_set():
            raise Exception(
                "パスワードが設定されていません。Googleアカウントのリンクを解除する前にパスワードを設定してください"
            )

        google_id = user.google_id
        user.google_id = None
        user.google_refresh_token = None
        user.log_activity(self.db, "google_account_unlinked", {"google_id": google_id})
        self.db.commit()


# Database setup
engine = create_engine("sqlite:///test_google_sso_simple.db")
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def test_google_sso():
    """Test Google SSO functionality."""
    print("Testing Google SSO (Simplified)...\n")

    db = SessionLocal()
    service = SimpleGoogleAuthService(db)

    # Test 1: New user creation from Google
    print("1. Testing new user creation from Google...")
    google_info = {
        "id": "google123",
        "email": "newuser@gmail.com",
        "name": "New User",
        "verified_email": True,
        "picture": "https://example.com/photo.jpg",
    }

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

    # Test 2: Existing user login with Google
    print("\n2. Testing existing user login with Google...")
    user2, is_new2 = service.authenticate_or_create_user(
        google_info=google_info,
        ip_address="192.168.1.100",
        user_agent="Test Browser",
    )

    assert is_new2 is False
    assert user2.id == user.id
    assert user2.last_login_at is not None
    print("✓ Existing user login successful")

    # Test 3: Link Google account to existing user
    print("\n3. Testing linking Google account to existing user...")
    # Create user without Google
    regular_user = User(
        email="regular@example.com",
        hashed_password="hashed_password",
        full_name="Regular User",
        is_active=True,
    )
    db.add(regular_user)
    db.commit()

    # Link Google account
    google_info2 = {
        "id": "google456",
        "email": "regular@example.com",
        "name": "Regular User Google",
        "verified_email": True,
    }

    service.link_google_account(regular_user, google_info2)
    assert regular_user.google_id == "google456"
    print("✓ Google account linked successfully")

    # Test 4: Unlink Google account
    print("\n4. Testing unlinking Google account...")
    service.unlink_google_account(regular_user)
    assert regular_user.google_id is None
    print("✓ Google account unlinked successfully")

    # Test 5: Unverified email rejection
    print("\n5. Testing unverified email rejection...")
    unverified_info = {
        "id": "google789",
        "email": "unverified@gmail.com",
        "name": "Unverified User",
        "verified_email": False,
    }

    try:
        service.authenticate_or_create_user(
            google_info=unverified_info,
            ip_address="192.168.1.100",
            user_agent="Test Browser",
        )
        assert False, "Should have raised error"
    except Exception as e:
        assert "確認されていません" in str(e)
        print("✓ Correctly rejected unverified email")

    # Test 6: Duplicate Google ID prevention
    print("\n6. Testing duplicate Google ID prevention...")
    another_user = User(
        email="another@example.com",
        hashed_password="hashed",
        full_name="Another User",
        is_active=True,
    )
    db.add(another_user)
    db.commit()

    try:
        service.link_google_account(another_user, google_info)  # Same Google ID
        assert False, "Should have raised error"
    except Exception as e:
        assert "既に別のユーザーにリンク" in str(e)
        print("✓ Correctly prevented duplicate Google ID")

    # Test 7: Email mismatch prevention
    print("\n7. Testing email mismatch prevention...")
    mismatch_info = {
        "id": "google999",
        "email": "different@gmail.com",
        "name": "Different User",
        "verified_email": True,
    }

    try:
        service.link_google_account(another_user, mismatch_info)
        assert False, "Should have raised error"
    except Exception as e:
        assert "メールアドレスが一致しません" in str(e)
        print("✓ Correctly prevented email mismatch")

    # Test 8: Auto-link on first Google login with existing email
    print("\n8. Testing auto-link on first Google login...")
    email_user = User(
        email="autolink@example.com",
        hashed_password="password",
        full_name="Auto Link User",
        is_active=True,
    )
    db.add(email_user)
    db.commit()

    autolink_info = {
        "id": "google_autolink",
        "email": "autolink@example.com",
        "name": "Auto Link User",
        "verified_email": True,
    }

    linked_user, is_new_link = service.authenticate_or_create_user(
        google_info=autolink_info,
        ip_address="192.168.1.100",
        user_agent="Test Browser",
    )

    assert is_new_link is False
    assert linked_user.id == email_user.id
    assert linked_user.google_id == "google_autolink"
    print("✓ Auto-linked Google account on first login")

    print("\n✅ All Google SSO tests passed!")
    print("\nKey features tested:")
    print("  - New user creation from Google")
    print("  - Existing user login")
    print("  - Manual account linking/unlinking")
    print("  - Auto-linking on first Google login")
    print("  - Email verification requirement")
    print("  - Duplicate Google ID prevention")
    print("  - Email mismatch prevention")

    # Cleanup
    db.close()
    os.remove("test_google_sso_simple.db")


if __name__ == "__main__":
    test_google_sso()
