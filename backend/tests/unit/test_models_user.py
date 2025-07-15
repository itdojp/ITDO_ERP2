"""Unit tests for User model."""

from datetime import timezone

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User


class TestUserModel:
    """Test User model functionality."""

    def test_create_user(self, db_session: Session) -> None:
        """Test user creation."""
        # Given: User data
        user_data = {
            "email": "test@example.com",
            "password": "SecurePassword123!",
            "full_name": "Test User",
        }

        # When: Creating user
        user = User.create(
            db_session,
            email=user_data["email"],
            password=user_data["password"],
            full_name=user_data["full_name"],
        )

        # Then: User should be created with correct attributes
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.created_at is not None
        assert user.updated_at is not None

        # Password should be hashed
        assert user.hashed_password != "SecurePassword123!"
        assert verify_password("SecurePassword123!", user.hashed_password)

    def test_create_user_minimal(self, db_session: Session) -> None:
        """Test user creation with minimal data."""
        # When: Creating user with minimal data
        user = User.create(
            db_session,
            email="minimal@example.com",
            password="Password123!",
            full_name="Minimal",
        )

        # Then: Default values should be set
        assert user.is_active is True
        assert user.is_superuser is False

    def test_create_superuser(self, db_session: Session) -> None:
        """Test superuser creation."""
        # When: Creating superuser
        user = User.create(
            db_session,
            email="admin@example.com",
            password="AdminPass123!",
            full_name="Admin User",
            is_superuser=True,
        )

        # Then: User should be superuser
        assert user.is_superuser is True

    def test_duplicate_email_raises_error(self, db_session: Session) -> None:
        """Test that duplicate emails are rejected."""
        # Given: Existing user
        User.create(
            db_session,
            email="existing@example.com",
            password="Password123!",
            full_name="Existing User",
        )
        db_session.commit()

        # When/Then: Creating user with same email should raise error
        with pytest.raises(IntegrityError):
            User.create(
                db_session,
                email="existing@example.com",
                password="Password456!",
                full_name="Duplicate User",
            )
            db_session.commit()

    def test_get_by_email(self, db_session: Session) -> None:
        """Test getting user by email."""
        # Given: Existing user
        created_user = User.create(
            db_session,
            email="findme@example.com",
            password="Password123!",
            full_name="Find Me",
        )
        db_session.commit()

        # When: Getting user by email
        found_user = User.get_by_email(db_session, "findme@example.com")

        # Then: Correct user should be found
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == "findme@example.com"

    def test_get_by_email_not_found(self, db_session: Session) -> None:
        """Test getting non-existent user by email."""
        # When: Getting non-existent user
        user = User.get_by_email(db_session, "nonexistent@example.com")

        # Then: Should return None
        assert user is None

    def test_authenticate_success(self, db_session: Session) -> None:
        """Test successful authentication."""
        # Given: Existing user
        User.create(
            db_session,
            email="auth@example.com",
            password="AuthPass123!",
            full_name="Auth User",
        )
        db_session.commit()

        # When: Authenticating with correct credentials
        user = User.authenticate(db_session, "auth@example.com", "AuthPass123!")

        # Then: User should be returned
        assert user is not None
        assert user.email == "auth@example.com"

    def test_authenticate_wrong_password(self, db_session: Session) -> None:
        """Test authentication with wrong password."""
        # Given: Existing user
        User.create(
            db_session,
            email="auth2@example.com",
            password="CorrectPass123!",
            full_name="Auth User",
        )
        db_session.commit()

        # When: Authenticating with wrong password
        user = User.authenticate(db_session, "auth2@example.com", "WrongPass123!")

        # Then: Should return None
        assert user is None

    def test_authenticate_inactive_user(self, db_session: Session) -> None:
        """Test authentication with inactive user."""
        # Given: Inactive user
        User.create(
            db_session,
            email="inactive@example.com",
            password="InactivePass123!",
            full_name="Inactive User",
            is_active=False,
        )
        db_session.commit()

        # When: Trying to authenticate
        user = User.authenticate(db_session, "inactive@example.com", "InactivePass123!")

        # Then: Should return None
        assert user is None

    def test_update_user(self, db_session: Session) -> None:
        """Test user update."""
        # Given: Existing user
        user = User.create(
            db_session,
            email="update@example.com",
            password="Password123!",
            full_name="Original Name",
        )
        db_session.commit()

        # Record original time
        original_updated_at = user.updated_at

        # Add slight delay to ensure different timestamp
        import time

        time.sleep(0.01)

        # When: Updating user
        user.update(db_session, full_name="Updated Name")

        # Then: User should be updated
        assert user.full_name == "Updated Name"
<<<<<<< HEAD
        assert user.updated_at >= original_updated_at
=======
        # Handle timezone comparison properly
        created_at = user.created_at
        updated_at = user.updated_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        # Use >= because SQLite has lower timestamp precision
        assert updated_at >= created_at
>>>>>>> main
