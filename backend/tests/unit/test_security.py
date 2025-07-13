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


class TestPasswordHashingEdgeCases:
    """Test edge cases for password hashing."""

    def test_hash_empty_password(self) -> None:
        """Test hashing an empty password."""
        # Given: Empty password
        password = ""

        # When: Hashing empty password
        hashed = hash_password(password)

        # Then: Should still generate a hash
        assert hashed is not None
        assert hashed != password
        assert verify_password(password, hashed)

    def test_hash_very_long_password(self) -> None:
        """Test hashing a very long password."""
        # Given: Very long password (over 1000 characters)
        password = "a" * 1500

        # When: Hashing long password
        hashed = hash_password(password)

        # Then: Should handle long passwords correctly
        assert hashed is not None
        assert verify_password(password, hashed)

    def test_hash_unicode_password(self) -> None:
        """Test hashing password with unicode characters."""
        # Given: Password with unicode characters
        password = "パスワード123!@#$%^&*()_+{}|:<>?[]\\;'\",./"

        # When: Hashing unicode password
        hashed = hash_password(password)

        # Then: Should handle unicode correctly
        assert hashed is not None
        assert verify_password(password, hashed)

    def test_hash_special_characters(self) -> None:
        """Test hashing password with all special characters."""
        # Given: Password with special characters
        password = "!@#$%^&*()_+-={}[]|\\:;\"'<>?,./"

        # When: Hashing
        hashed = hash_password(password)

        # Then: Should handle special characters
        assert hashed is not None
        assert verify_password(password, hashed)

    def test_verify_password_with_malformed_hash(self) -> None:
        """Test password verification with malformed hash."""
        # Given: Valid password and malformed hash
        password = "ValidPassword123!"
        malformed_hash = "not_a_valid_bcrypt_hash"

        # When/Then: Verifying with malformed hash should raise an exception
        # This is expected behavior as passlib cannot identify the hash format
        from passlib.exc import UnknownHashError
        with pytest.raises(UnknownHashError):
            verify_password(password, malformed_hash)


class TestJWTTokenEdgeCases:
    """Test edge cases for JWT tokens."""

    def test_create_token_with_empty_data(self) -> None:
        """Test creating token with empty data."""
        # Given: Empty data
        data = {}

        # When: Creating token with empty data
        token = create_access_token(data)

        # Then: Should still create valid token
        assert token is not None
        payload = verify_token(token)
        assert "exp" in payload
        assert "iat" in payload
        assert payload["type"] == "access"

    def test_create_token_with_string_values(self) -> None:
        """Test creating token with various string values."""
        # Given: Data with string values
        data = {"sub": "user123", "email": "user@example.com", "role": "admin"}

        # When: Creating token
        token = create_access_token(data)

        # Then: Should handle string values correctly
        assert token is not None
        payload = verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["email"] == "user@example.com"
        assert payload["role"] == "admin"

    def test_create_token_with_very_large_payload(self) -> None:
        """Test creating token with large payload."""
        # Given: Large data payload
        data = {
            "sub": "123",
            "large_data": "x" * 10000,  # 10KB of data
            "permissions": ["read", "write", "admin"] * 100
        }

        # When: Creating token
        token = create_access_token(data)

        # Then: Should handle large payloads
        assert token is not None
        payload = verify_token(token)
        assert payload["sub"] == "123"
        assert len(payload["large_data"]) == 10000

    def test_verify_token_with_tampered_signature(self) -> None:
        """Test verification of token with tampered signature."""
        # Given: Valid token with tampered signature
        data = {"sub": "123"}
        token = create_access_token(data)
        
        # Tamper with the signature (last part after last dot)
        parts = token.split(".")
        tampered_token = ".".join(parts[:-1]) + ".tampered_signature"

        # When/Then: Should raise InvalidTokenError
        with pytest.raises(InvalidTokenError):
            verify_token(tampered_token)

    def test_verify_token_with_missing_parts(self) -> None:
        """Test verification of malformed token (missing parts)."""
        # Given: Token with missing parts
        incomplete_token = "header.payload"  # Missing signature

        # When/Then: Should raise InvalidTokenError
        with pytest.raises(InvalidTokenError):
            verify_token(incomplete_token)

    def test_create_refresh_token_with_custom_expiry(self) -> None:
        """Test refresh token with custom expiry."""
        # Given: User data and custom expiry
        data = {"sub": "123"}
        expires_delta = timedelta(days=30)

        # When: Creating refresh token with custom expiry
        token = create_refresh_token(data, expires_delta)

        # Then: Token should be created
        assert token is not None
        payload = verify_token(token)
        assert payload["type"] == "refresh"

    def test_token_metadata_consistency(self) -> None:
        """Test that token metadata is consistent."""
        # Given: User data
        data = {"sub": "123"}

        # When: Creating tokens
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        # Then: Both should have required metadata
        access_payload = verify_token(access_token)
        refresh_payload = verify_token(refresh_token)

        # Check metadata presence
        for payload in [access_payload, refresh_payload]:
            assert "exp" in payload  # Expiration
            assert "iat" in payload  # Issued at
            assert "type" in payload  # Token type

        # Check token types
        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"


class TestSecurityUtilitiesIntegration:
    """Test integration scenarios for security utilities."""

    def test_password_and_token_workflow(self) -> None:
        """Test complete password and token workflow."""
        # Given: User registration data
        email = "test@example.com"
        password = "SecurePassword123!"

        # When: Hashing password and creating tokens
        hashed_password = hash_password(password)
        token_data = {"sub": "123", "email": email}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # Then: All operations should work together
        assert verify_password(password, hashed_password)
        
        access_payload = verify_token(access_token)
        refresh_payload = verify_token(refresh_token)
        
        assert access_payload["email"] == email
        assert refresh_payload["email"] == email

    def test_password_change_scenario(self) -> None:
        """Test password change scenario."""
        # Given: Original and new passwords
        old_password = "OldPassword123!"
        new_password = "NewPassword456!"

        # When: Hashing both passwords
        old_hash = hash_password(old_password)
        new_hash = hash_password(new_password)

        # Then: Old password should not verify against new hash
        assert verify_password(old_password, old_hash)
        assert verify_password(new_password, new_hash)
        assert not verify_password(old_password, new_hash)
        assert not verify_password(new_password, old_hash)

    def test_token_uniqueness_with_different_data(self) -> None:
        """Test that tokens with different data are different."""
        # Given: Different user data
        data1 = {"sub": "123", "email": "test1@example.com"}
        data2 = {"sub": "456", "email": "test2@example.com"}

        # When: Creating tokens with different data
        token1 = create_access_token(data1)
        token2 = create_access_token(data2)

        # Then: Tokens should be different
        assert token1 != token2
        
        payload1 = verify_token(token1)
        payload2 = verify_token(token2)
        
        assert payload1["sub"] != payload2["sub"]
        assert payload1["email"] != payload2["email"]
        assert payload1["type"] == payload2["type"] == "access"
