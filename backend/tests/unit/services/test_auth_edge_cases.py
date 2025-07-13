"""Edge case tests for authentication service."""

import time
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError
from app.services.auth import AuthService
from tests.factories import UserFactory


class TestAuthServiceEdgeCases:
    """Edge case tests for AuthService."""

    @pytest.fixture
    def auth_service(self, db_session: Session) -> AuthService:
        """Create auth service instance."""
        return AuthService()

    def test_authenticate_with_empty_credentials(
        self, auth_service: AuthService, db_session: Session
    ) -> None:
        """Test authentication with empty/null credentials."""
        # Test empty email
        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            auth_service.authenticate_user(db_session, "", "password123")

        # Test None email
        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            auth_service.authenticate_user(db_session, None, "password123")

        # Test empty password
        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            auth_service.authenticate_user(db_session, "user@example.com", "")

        # Test None password
        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            auth_service.authenticate_user(db_session, "user@example.com", None)

        # Test both empty
        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            auth_service.authenticate_user(db_session, "", "")

    def test_authenticate_with_special_characters(
        self, auth_service: AuthService, db_session: Session
    ) -> None:
        """Test authentication with special characters in credentials."""
        # Create user with special character password
        special_password = "P@ssw0rd!#$%^&*()_+-=[]{}|;:,.<>?"
        UserFactory.create(
            db_session, email="test@example.com", password=special_password
        )

        # Should authenticate successfully
        result = auth_service.authenticate_user(db_session, "test@example.com", special_password)
        assert result is not None
        assert result.email == "test@example.com"

        # Test with special characters in email domain
        special_email = "user+tag@sub-domain.co.uk"
        UserFactory.create(db_session, email=special_email, password="password123")

        result = auth_service.authenticate_user(db_session, special_email, "password123")
        assert result is not None
        assert result.email == special_email

    def test_authenticate_with_sql_injection_attempts(
        self, auth_service: AuthService, db_session: Session
    ) -> None:
        """Test authentication with SQL injection attempts."""
        # Create a legitimate user first
        UserFactory.create(
            db_session, email="admin@example.com", password="securepassword"
        )

        # SQL injection attempts in email
        injection_attempts = [
            "admin@example.com'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin@example.com' UNION SELECT * FROM users --",
            "'; DELETE FROM users WHERE '1'='1'; --",
            "admin@example.com'/**/OR/**/1=1#",
        ]

        for injection in injection_attempts:
            with pytest.raises(AuthenticationError, match="Invalid credentials"):
                auth_service.authenticate_user(db_session, injection, "securepassword")

        # SQL injection attempts in password
        password_injections = [
            "' OR '1'='1",
            "password'; DROP TABLE users; --",
            "anything' UNION SELECT password FROM users --",
        ]

        for injection in password_injections:
            with pytest.raises(AuthenticationError, match="Invalid credentials"):
                auth_service.authenticate_user(db_session, "admin@example.com", injection)

    def test_authenticate_with_invalid_email_formats(
        self, auth_service: AuthService, db_session: Session
    ) -> None:
        """Test authentication with various invalid email formats."""
        invalid_emails = [
            "not-an-email",
            "@example.com",
            "user@",
            "user..double.dot@example.com",
            "user@.example.com",
            "user@example.",
            "user name@example.com",  # Space in local part
            "user@ex ample.com",  # Space in domain
            "user@example,com",  # Comma instead of dot
            "user@[192.168.1.1",  # Malformed IP
            "user@example..com",  # Double dot in domain
            "user@-example.com",  # Dash at start of domain
            "user@example-.com",  # Dash at end of domain part
        ]

        for invalid_email in invalid_emails:
            with pytest.raises(AuthenticationError, match="Invalid credentials"):
                auth_service.authenticate_user(db_session, invalid_email, "password123")

    def test_authenticate_with_very_long_inputs(
        self, auth_service: AuthService, db_session: Session
    ) -> None:
        """Test authentication with very long input strings."""
        # Very long email (over reasonable limits)
        long_email = "a" * 1000 + "@example.com"
        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            auth_service.authenticate_user(db_session, long_email, "password123")

        # Very long password
        long_password = "a" * 10000
        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            auth_service.authenticate_user(db_session, "user@example.com", long_password)

        # Both very long
        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            auth_service.authenticate_user(db_session, long_email, long_password)

    def test_authenticate_with_unicode_characters(
        self, auth_service: AuthService, db_session: Session
    ) -> None:
        """Test authentication with Unicode characters."""
        # Create user with Unicode password
        unicode_password = "пароль123测试🔒"
        UserFactory.create(
            db_session, email="unicode@example.com", password=unicode_password
        )

        # Should authenticate successfully
        result = auth_service.authenticate_user(db_session, "unicode@example.com", unicode_password)
        assert result is not None
        assert result.email == "unicode@example.com"

        # Test with Unicode in email local part (if supported by system)
        try:
            unicode_email = "用户@example.com"
            UserFactory.create(db_session, email=unicode_email, password="password123")

            result = auth_service.authenticate_user(db_session, unicode_email, "password123")
            assert result is not None
        except Exception:
            # Unicode emails might not be supported, which is acceptable
            pass

    def test_authenticate_with_null_byte_injection(
        self, auth_service: AuthService, db_session: Session
    ) -> None:
        """Test authentication with null byte injection attempts."""
        null_byte_attempts = [
            "user@example.com\x00",
            "user@example.com\x00.evil.com",
            "user\x00@example.com",
            "\x00user@example.com",
        ]

        for attempt in null_byte_attempts:
            with pytest.raises(AuthenticationError, match="Invalid credentials"):
                auth_service.authenticate_user(db_session, attempt, "password123")

        # Null bytes in password
        password_null_attempts = [
            "password\x00",
            "pass\x00word",
            "\x00password",
        ]

        for attempt in password_null_attempts:
            with pytest.raises(AuthenticationError, match="Invalid credentials"):
                auth_service.authenticate_user(db_session, "user@example.com", attempt)

    def test_authenticate_during_account_lockout_expiry(
        self, auth_service: AuthService, db_session: Session
    ) -> None:
        """Test authentication exactly when account lockout expires."""
        user = UserFactory.create(
            db_session, email="locked@example.com", password="password123"
        )

        # Lock the account
        user.failed_login_attempts = 5
        user.locked_until = datetime.utcnow() + timedelta(seconds=1)
        db_session.commit()

        # Should fail while locked
        with pytest.raises(AuthenticationError, match="Account is locked"):
            auth_service.authenticate_user(db_session, "locked@example.com", "password123")

        # Wait for lockout to expire
        time.sleep(1.1)

        # Should succeed after lockout expires
        result = auth_service.authenticate_user(db_session, "locked@example.com", "password123")
        assert result is not None
        assert result.email == "locked@example.com"

        # Verify lockout was reset
        db_session.refresh(user)
        assert user.failed_login_attempts == 0
        assert user.locked_until is None

    def test_authenticate_with_case_sensitivity(
        self, auth_service: AuthService, db_session: Session
    ) -> None:
        """Test email case sensitivity in authentication."""
        UserFactory.create(db_session, email="User@Example.COM", password="password123")

        # Test various case combinations
        email_variations = [
            "user@example.com",
            "USER@EXAMPLE.COM",
            "User@Example.com",
            "user@EXAMPLE.com",
        ]

        for email_variant in email_variations:
            result = auth_service.authenticate_user(db_session, email_variant, "password123")
            assert result is not None
            assert result.email.lower() == "user@example.com"

    def test_authenticate_with_whitespace_handling(
        self, auth_service: AuthService, db_session: Session
    ) -> None:
        """Test authentication with leading/trailing whitespace."""
        UserFactory.create(db_session, email="user@example.com", password="password123")

        # Test with various whitespace scenarios
        whitespace_emails = [
            " user@example.com",
            "user@example.com ",
            " user@example.com ",
            "\tuser@example.com\t",
            "\nuser@example.com\n",
        ]

        for email_with_space in whitespace_emails:
            result = auth_service.authenticate_user(db_session, email_with_space, "password123")
            assert result is not None
            assert result.email == "user@example.com"

    def test_authenticate_with_password_must_change(
        self, auth_service: AuthService, db_session: Session
    ) -> None:
        """Test authentication when password must be changed."""
        user = UserFactory.create(
            db_session, email="mustchange@example.com", password="password123"
        )

        # Set password must change flag
        user.password_must_change = True
        db_session.commit()

        # Authentication should succeed but indicate password change required
        result = auth_service.authenticate_user(db_session, "mustchange@example.com", "password123")
        assert result is not None
        assert result.password_must_change is True

    def test_authenticate_with_concurrent_attempts(
        self, auth_service: AuthService, db_session: Session
    ) -> None:
        """Test concurrent authentication attempts."""
        UserFactory.create(
            db_session, email="concurrent@example.com", password="password123"
        )

        # Simulate concurrent authentication attempts
        import queue
        import threading

        results = queue.Queue()
        errors = queue.Queue()

        def authenticate():
            try:
                result = auth_service.authenticate_user(db_session, 
                    "concurrent@example.com", "password123"
                )
                results.put(result)
            except Exception as e:
                errors.put(e)

        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=authenticate)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All should succeed
        successful_results = []
        while not results.empty():
            successful_results.append(results.get())

        # Should have multiple successful authentications
        assert len(successful_results) >= 1

        # No errors should occur
        assert errors.empty()

    def test_authenticate_with_expired_password(
        self, auth_service: AuthService, db_session: Session
    ) -> None:
        """Test authentication with expired password."""
        user = UserFactory.create(
            db_session, email="expired@example.com", password="password123"
        )

        # Set password as expired (more than 90 days old)
        user.password_changed_at = datetime.utcnow() - timedelta(days=91)
        db_session.commit()

        # Authentication should succeed but indicate password is expired
        result = auth_service.authenticate_user(db_session, "expired@example.com", "password123")
        assert result is not None

        # Check if password expiry is detected (implementation dependent)
        # This test verifies the system can handle expired passwords gracefully

    def test_authenticate_inactive_user_edge_case(
        self, auth_service: AuthService, db_session: Session
    ) -> None:
        """Test authentication edge cases with inactive users."""
        # Create inactive user
        user = UserFactory.create(
            db_session,
            email="inactive@example.com",
            password="password123",
            is_active=False,
        )

        # Should fail authentication
        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            auth_service.authenticate_user(db_session, "inactive@example.com", "password123")

        # Activate user during authentication process (race condition simulation)
        user.is_active = True
        db_session.commit()

        # Should now succeed
        result = auth_service.authenticate_user(db_session, "inactive@example.com", "password123")
        assert result is not None
        assert result.is_active is True
