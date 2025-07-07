"""Unit tests for security utilities."""

from datetime import timedelta

import pytest

from app.core.exceptions import ExpiredTokenError, InvalidTokenError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)


class TestPasswordHashing:
    """Test password hashing functionality."""

    def test_password_hashing(self) -> None:
        """Test that passwords are correctly hashed."""
        # Given: A plain text password
        password = "SecurePassword123!"

        # When: Hashing the password
        hashed = hash_password(password)

        # Then: Hash should be generated and different from original
        assert hashed is not None
        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt format

    def test_password_verification_success(self) -> None:
        """Test that correct passwords are verified."""
        # Given: A password and its hash
        password = "SecurePassword123!"
        hashed = hash_password(password)

        # When: Verifying the password
        result = verify_password(password, hashed)

        # Then: Verification should succeed
        assert result is True

    def test_password_verification_failure(self) -> None:
        """Test that incorrect passwords are rejected."""
        # Given: A password and a hash of a different password
        password = "SecurePassword123!"
        wrong_password = "WrongPassword123!"
        hashed = hash_password(password)

        # When: Verifying with wrong password
        result = verify_password(wrong_password, hashed)

        # Then: Verification should fail
        assert result is False

    def test_password_hash_uniqueness(self) -> None:
        """Test that same password generates different hashes."""
        # Given: Same password
        password = "SecurePassword123!"

        # When: Hashing twice
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Then: Hashes should be different (due to salt)
        assert hash1 != hash2


class TestJWTTokens:
    """Test JWT token functionality."""

    def test_create_access_token(self) -> None:
        """Test access token creation."""
        # Given: User data
        data = {"sub": "123", "email": "test@example.com"}

        # When: Creating access token
        token = create_access_token(data)

        # Then: Token should be created
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self) -> None:
        """Test access token with custom expiry."""
        # Given: User data and custom expiry
        data = {"sub": "123"}
        expires_delta = timedelta(hours=2)

        # When: Creating token with custom expiry
        token = create_access_token(data, expires_delta)

        # Then: Token should be created
        assert token is not None

    def test_verify_valid_token(self) -> None:
        """Test verification of valid token."""
        # Given: A valid token
        data = {"sub": "123", "email": "test@example.com"}
        token = create_access_token(data)

        # When: Verifying the token
        payload = verify_token(token)

        # Then: Payload should be returned with correct data
        assert payload is not None
        assert payload["sub"] == "123"
        assert payload["email"] == "test@example.com"
        assert "exp" in payload
        assert "iat" in payload
        assert payload["type"] == "access"

    def test_verify_expired_token(self) -> None:
        """Test that expired tokens are rejected."""
        # Given: An expired token (negative expiry)
        data = {"sub": "123"}
        token = create_access_token(data, expires_delta=timedelta(hours=-1))

        # When/Then: Verification should raise ExpiredTokenError
        with pytest.raises(ExpiredTokenError):
            verify_token(token)

    def test_verify_invalid_token(self) -> None:
        """Test that invalid tokens are rejected."""
        # Given: An invalid token
        invalid_token = "invalid.token.here"

        # When/Then: Verification should raise InvalidTokenError
        with pytest.raises(InvalidTokenError):
            verify_token(invalid_token)

    def test_create_refresh_token(self) -> None:
        """Test refresh token creation."""
        # Given: User data
        data = {"sub": "123", "email": "test@example.com"}

        # When: Creating refresh token
        token = create_refresh_token(data)

        # Then: Token should be created
        assert token is not None
        assert isinstance(token, str)

    def test_refresh_token_has_correct_type(self) -> None:
        """Test that refresh tokens have correct type."""
        # Given: User data
        data = {"sub": "123"}
        token = create_refresh_token(data)

        # When: Verifying the token
        payload = verify_token(token)

        # Then: Token type should be refresh
        assert payload["type"] == "refresh"
