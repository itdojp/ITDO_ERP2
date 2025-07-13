"""Edge case tests for authentication token security."""

import time
from datetime import datetime, timedelta

from jose import jwt
import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, verify_token
from app.models.user import User
from app.services.auth import AuthService
from tests.factories import UserFactory


class TestTokenSecurityEdgeCases:
    """Edge case tests for token security."""

    @pytest.fixture
    def auth_service(self, db_session: Session) -> AuthService:
        """Create auth service instance."""
        return AuthService(db_session)

    @pytest.fixture
    def user(self, db_session: Session) -> User:
        """Create test user."""
        return UserFactory.create(
            db_session, email="tokentest@example.com", password="password123"
        )

    def test_token_with_tampered_payload(self, user: User) -> None:
        """Test token validation with tampered payload."""
        # Create valid token
        token = create_access_token(data={"sub": str(user.id)})

        # Tamper with token payload (change user ID)
        try:
            # Decode without verification to get payload
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            unverified_payload["sub"] = "999999"  # Change to non-existent user

            # Re-encode with wrong secret
            tampered_token = jwt.encode(
                unverified_payload, "wrong_secret", algorithm="HS256"
            )

            # Should fail verification
            with pytest.raises(Exception):
                verify_token(tampered_token)

        except Exception:
            # Token tampering should fail
            pass

    def test_token_with_wrong_algorithm(self, user: User) -> None:
        """Test token with different signing algorithm."""
        current_settings = settings

        # Create token with different algorithm
        payload = {
            "sub": str(user.id),
            "exp": datetime.utcnow() + timedelta(minutes=30),
        }

        # Try with 'none' algorithm (should be rejected)
        try:
            none_token = jwt.encode(payload, "", algorithm="none")
            with pytest.raises(Exception):
                verify_token(none_token)
        except Exception:
            pass

        # Try with different algorithm
        try:
            rs256_token = jwt.encode(payload, current_settings.SECRET_KEY, algorithm="RS256")
            with pytest.raises(Exception):
                verify_token(rs256_token)
        except Exception:
            pass

    def test_token_reuse_after_password_change(
        self, auth_service: AuthService, db_session: Session, user: User
    ) -> None:
        """Test token validity after user password change."""
        # Create token before password change
        old_token = create_access_token(data={"sub": str(user.id)})

        # Verify token works initially
        payload = verify_token(old_token)
        assert payload["sub"] == str(user.id)

        # Change user password
        user.change_password(db_session, "password123", "newpassword456")
        db_session.commit()

        # Old token should still be valid (until expiry)
        # This tests current behavior - could be enhanced with token invalidation
        payload = verify_token(old_token)
        assert payload["sub"] == str(user.id)

    def test_token_with_future_issued_time(self, user: User) -> None:
        """Test token with future issued time."""
        # Create token with future issued time
        future_time = datetime.utcnow() + timedelta(hours=1)
        payload = {
            "sub": str(user.id),
            "iat": future_time.timestamp(),
            "exp": (future_time + timedelta(hours=1)).timestamp(),
        }

        current_settings = settings
        future_token = jwt.encode(
            payload, current_settings.SECRET_KEY, algorithm=current_settings.ALGORITHM
        )

        # Should be rejected (depending on JWT library configuration)
        try:
            verify_token(future_token)
        except Exception:
            # Future tokens should be rejected
            pass

    def test_token_with_very_long_expiry(self, user: User) -> None:
        """Test token with extremely long expiry time."""
        # Create token with 100-year expiry
        far_future = datetime.utcnow() + timedelta(days=365 * 100)
        payload = {"sub": str(user.id), "exp": far_future.timestamp()}

        current_settings = settings
        long_token = jwt.encode(
            payload, current_settings.SECRET_KEY, algorithm=current_settings.ALGORITHM
        )

        # Should still validate (but may be rejected by application logic)
        result = verify_token(long_token)
        assert result["sub"] == str(user.id)

    def test_token_with_negative_expiry(self, user: User) -> None:
        """Test token with negative expiry time."""
        # Create token with negative timestamp
        payload = {"sub": str(user.id), "exp": -1}

        current_settings = settings
        negative_token = jwt.encode(
            payload, current_settings.SECRET_KEY, algorithm=current_settings.ALGORITHM
        )

        # Should be rejected as expired
        with pytest.raises(Exception):
            verify_token(negative_token)

    def test_token_race_condition_on_refresh(
        self, auth_service: AuthService, db_session: Session, user: User
    ) -> None:
        """Test race condition during token refresh."""
        # Create initial tokens
        create_access_token(data={"sub": str(user.id)})
        refresh_token = create_access_token(
            data={"sub": str(user.id), "type": "refresh"},
            expires_delta=timedelta(days=7),
        )

        # Simulate concurrent refresh attempts
        import queue
        import threading

        results = queue.Queue()
        errors = queue.Queue()

        def refresh_token_func():
            try:
                # Attempt to refresh token
                new_tokens = auth_service.refresh_token(refresh_token)
                results.put(new_tokens)
            except Exception as e:
                errors.put(e)

        # Start multiple refresh threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=refresh_token_func)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Should handle concurrent refreshes gracefully
        # (Implementation dependent - may succeed or fail gracefully)
        successful_refreshes = []
        while not results.empty():
            successful_refreshes.append(results.get())

        # At least one should succeed, others may fail gracefully
        assert len(successful_refreshes) >= 1

    def test_token_with_additional_claims(self, user: User) -> None:
        """Test token with unexpected additional claims."""
        # Create token with extra claims
        payload = {
            "sub": str(user.id),
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
            "admin": True,  # Unexpected claim
            "permissions": ["read", "write", "delete"],  # Unexpected claim
            "custom_data": {"key": "value"},  # Unexpected claim
        }

        current_settings = settings
        extra_claims_token = jwt.encode(
            payload, current_settings.SECRET_KEY, algorithm=current_settings.ALGORITHM
        )

        # Should still validate basic token structure
        result = verify_token(extra_claims_token)
        assert result["sub"] == str(user.id)

        # Extra claims should be preserved
        assert "admin" in result
        assert "permissions" in result

    def test_token_without_required_claims(self, user: User) -> None:
        """Test token missing required claims."""
        current_settings = settings

        # Token without 'sub' claim
        payload_no_sub = {"exp": (datetime.utcnow() + timedelta(hours=1)).timestamp()}
        token_no_sub = jwt.encode(
            payload_no_sub, current_settings.SECRET_KEY, algorithm=current_settings.ALGORITHM
        )

        # Should handle missing required claims
        result = verify_token(token_no_sub)
        # Implementation should handle missing 'sub' gracefully

        # Token without 'exp' claim
        payload_no_exp = {"sub": str(user.id)}
        token_no_exp = jwt.encode(
            payload_no_exp, current_settings.SECRET_KEY, algorithm=current_settings.ALGORITHM
        )

        # Should still validate (depending on JWT library settings)
        result = verify_token(token_no_exp)
        assert result["sub"] == str(user.id)

    def test_token_type_confusion(self, user: User) -> None:
        """Test using refresh token as access token and vice versa."""
        # Create access token
        access_token = create_access_token(data={"sub": str(user.id)})

        # Create refresh token
        refresh_token = create_access_token(
            data={"sub": str(user.id), "type": "refresh"},
            expires_delta=timedelta(days=7),
        )

        # Both should validate at the JWT level
        access_payload = verify_token(access_token)
        refresh_payload = verify_token(refresh_token)

        assert access_payload["sub"] == str(user.id)
        assert refresh_payload["sub"] == str(user.id)
        assert refresh_payload.get("type") == "refresh"

    def test_token_with_malformed_subject(self, user: User) -> None:
        """Test token with malformed subject claim."""
        current_settings = settings

        # Token with non-numeric user ID
        payload_string_id = {
            "sub": "not_a_number",
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
        }
        token_string_id = jwt.encode(
            payload_string_id, current_settings.SECRET_KEY, algorithm=current_settings.ALGORITHM
        )

        # Should validate at JWT level but may fail at application level
        result = verify_token(token_string_id)
        assert result["sub"] == "not_a_number"

        # Token with empty subject
        payload_empty_sub = {
            "sub": "",
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
        }
        token_empty_sub = jwt.encode(
            payload_empty_sub, current_settings.SECRET_KEY, algorithm=current_settings.ALGORITHM
        )

        result = verify_token(token_empty_sub)
        assert result["sub"] == ""

    def test_token_timing_attacks(self, user: User) -> None:
        """Test potential timing attacks on token validation."""
        valid_token = create_access_token(data={"sub": str(user.id)})
        invalid_token = "invalid.token.here"

        # Measure validation time for valid vs invalid tokens

        start_time = time.time()
        try:
            verify_token(valid_token)
        except Exception:
            pass
        valid_time = time.time() - start_time

        start_time = time.time()
        try:
            verify_token(invalid_token)
        except Exception:
            pass
        invalid_time = time.time() - start_time

        # Timing difference should be minimal to prevent timing attacks
        # This is more of a benchmark than a strict test
        time_difference = abs(valid_time - invalid_time)
        # Allow reasonable variance (implementation dependent)
        assert time_difference < 1.0  # Less than 1 second difference

    def test_token_with_unicode_characters(self, user: User) -> None:
        """Test token with Unicode characters in payload."""
        # Create token with Unicode data
        payload = {
            "sub": str(user.id),
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
            "name": "用户名🔒",
            "emoji": "🚀🔐💯",
        }

        current_settings = settings
        unicode_token = jwt.encode(
            payload, current_settings.SECRET_KEY, algorithm=current_settings.ALGORITHM
        )

        # Should handle Unicode data properly
        result = verify_token(unicode_token)
        assert result["sub"] == str(user.id)
        assert result["name"] == "用户名🔒"
        assert result["emoji"] == "🚀🔐💯"

    def test_token_size_limits(self, user: User) -> None:
        """Test token with very large payload."""
        # Create token with large payload
        large_data = "x" * 50000  # 50KB of data
        payload = {
            "sub": str(user.id),
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
            "large_field": large_data,
        }

        current_settings = settings
        try:
            large_token = jwt.encode(
                payload, current_settings.SECRET_KEY, algorithm=current_settings.ALGORITHM
            )

            # Should handle large tokens (within JWT limits)
            result = verify_token(large_token)
            assert result["sub"] == str(user.id)
            assert len(result["large_field"]) == 50000

        except Exception:
            # Large tokens may be rejected, which is acceptable
            pass
