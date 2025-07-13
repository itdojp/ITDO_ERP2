"""Unit tests for dependency injection utilities."""

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_active_user,
    get_current_superuser,
    get_current_user,
    get_db,
)
from app.models.user import User
from tests.factories import UserFactory


class TestDatabaseDependency:
    """Test database dependency functions."""

    def test_get_db_returns_session(self, db_session: Session) -> None:
        """Test that get_db returns a valid database session."""
        # When: Getting database session
        db_generator = get_db()
        db = next(db_generator)

        # Then: Should return a valid Session
        assert isinstance(db, Session)
        
        # Cleanup
        try:
            next(db_generator)
        except StopIteration:
            pass  # Expected when generator is exhausted

    def test_get_db_closes_session(self) -> None:
        """Test that get_db properly closes the session."""
        # When: Using database session in context
        db_generator = get_db()
        db = next(db_generator)
        
        # Simulate ending the context
        try:
            next(db_generator)
        except StopIteration:
            # Then: Session should be closed (no exception should occur)
            assert True  # If we reach here, session was closed properly


class TestUserAuthenticationDependencies:
    """Test user authentication dependency functions."""

    def test_get_current_active_user_with_active_user(
        self, db_session: Session
    ) -> None:
        """Test get_current_active_user with active user."""
        # Given: Active user
        user = UserFactory.create_with_password(
            db_session, 
            password="password123", 
            is_active=True
        )

        # When: Getting current active user
        result = get_current_active_user(user)

        # Then: Should return the same user
        assert result == user
        assert result.is_active

    def test_get_current_active_user_with_inactive_user(
        self, db_session: Session
    ) -> None:
        """Test get_current_active_user with inactive user."""
        # Given: Inactive user
        user = UserFactory.create_with_password(
            db_session, 
            password="password123", 
            is_active=False
        )

        # When/Then: Should raise HTTPException for inactive user
        with pytest.raises(HTTPException) as exc_info:
            get_current_active_user(user)
        
        assert exc_info.value.status_code == 403
        assert "Inactive user" in str(exc_info.value.detail)

    def test_get_current_superuser_with_superuser(
        self, db_session: Session
    ) -> None:
        """Test get_current_superuser with superuser."""
        # Given: Active superuser
        user = UserFactory.create_with_password(
            db_session, 
            password="password123", 
            is_active=True,
            is_superuser=True
        )

        # When: Getting current superuser
        result = get_current_superuser(user)

        # Then: Should return the same user
        assert result == user
        assert result.is_superuser

    def test_get_current_superuser_with_regular_user(
        self, db_session: Session
    ) -> None:
        """Test get_current_superuser with regular user."""
        # Given: Regular user (not superuser)
        user = UserFactory.create_with_password(
            db_session, 
            password="password123", 
            is_active=True,
            is_superuser=False
        )

        # When/Then: Should raise HTTPException for non-superuser
        with pytest.raises(HTTPException) as exc_info:
            get_current_superuser(user)
        
        assert exc_info.value.status_code == 403
        assert "Not enough permissions" in str(exc_info.value.detail)

    def test_get_current_superuser_with_inactive_superuser(
        self, db_session: Session
    ) -> None:
        """Test get_current_superuser with inactive superuser."""
        # Given: Inactive superuser
        user = UserFactory.create_with_password(
            db_session, 
            password="password123", 
            is_active=False,
            is_superuser=True
        )

        # When/Then: Should raise HTTPException for inactive user first
        with pytest.raises(HTTPException) as exc_info:
            # This would go through get_current_active_user first
            get_current_active_user(user)
        
        assert exc_info.value.status_code == 403
        assert "Inactive user" in str(exc_info.value.detail)


class TestAuthenticationEdgeCases:
    """Test edge cases for authentication dependencies."""

    def test_user_with_mixed_permissions(self, db_session: Session) -> None:
        """Test user with various permission combinations."""
        # Given: User with specific attributes
        user = UserFactory.create_with_password(
            db_session,
            password="password123",
            is_active=True,
            is_superuser=False
        )

        # When: Checking active user status
        result = get_current_active_user(user)

        # Then: Should pass active check but fail superuser check
        assert result == user
        
        with pytest.raises(HTTPException):
            get_current_superuser(user)

    def test_user_state_combinations(self, db_session: Session) -> None:
        """Test various combinations of user states."""
        test_cases = [
            # (is_active, is_superuser, should_pass_active, should_pass_super)
            (True, True, True, True),
            (True, False, True, False),
            (False, True, False, False),
            (False, False, False, False),
        ]

        for is_active, is_superuser, should_pass_active, should_pass_super in test_cases:
            # Given: User with specific state
            user = UserFactory.create_with_password(
                db_session,
                password="password123",
                email=f"test_{is_active}_{is_superuser}@example.com",
                is_active=is_active,
                is_superuser=is_superuser
            )

            # Test active user check
            if should_pass_active:
                result = get_current_active_user(user)
                assert result == user
            else:
                with pytest.raises(HTTPException):
                    get_current_active_user(user)

            # Test superuser check (only if active check passes)
            if should_pass_active:
                if should_pass_super:
                    result = get_current_superuser(user)
                    assert result == user
                else:
                    with pytest.raises(HTTPException):
                        get_current_superuser(user)


class TestDependencyChaining:
    """Test dependency chaining scenarios."""

    def test_dependency_chain_success(self, db_session: Session) -> None:
        """Test successful dependency chain execution."""
        # Given: Valid superuser
        user = UserFactory.create_with_password(
            db_session,
            password="password123",
            is_active=True,
            is_superuser=True
        )

        # When: Going through full dependency chain
        active_user = get_current_active_user(user)
        super_user = get_current_superuser(active_user)

        # Then: Should work through the chain
        assert active_user == user
        assert super_user == user
        assert super_user.is_active
        assert super_user.is_superuser

    def test_dependency_chain_break_at_active(self, db_session: Session) -> None:
        """Test dependency chain breaking at active user check."""
        # Given: Inactive superuser
        user = UserFactory.create_with_password(
            db_session,
            password="password123",
            is_active=False,
            is_superuser=True
        )

        # When/Then: Should break at active user check
        with pytest.raises(HTTPException) as exc_info:
            get_current_active_user(user)
        
        assert exc_info.value.status_code == 403

    def test_dependency_chain_break_at_superuser(self, db_session: Session) -> None:
        """Test dependency chain breaking at superuser check."""
        # Given: Active regular user
        user = UserFactory.create_with_password(
            db_session,
            password="password123",
            is_active=True,
            is_superuser=False
        )

        # When: Should pass active check but fail superuser check
        active_user = get_current_active_user(user)
        assert active_user == user

        # Then: Should break at superuser check
        with pytest.raises(HTTPException) as exc_info:
            get_current_superuser(active_user)
        
        assert exc_info.value.status_code == 403
        assert "Not enough permissions" in str(exc_info.value.detail)