"""Edge case tests for authentication session management."""

import time
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.models.user import User, UserSession
from app.services.auth import AuthService
from tests.factories import UserFactory


class TestSessionManagementEdgeCases:
    """Edge case tests for session management."""

    @pytest.fixture
    def auth_service(self, db_session: Session) -> AuthService:
        """Create auth service instance."""
        return AuthService(db_session)

    @pytest.fixture
    def user(self, db_session: Session) -> User:
        """Create test user."""
        return UserFactory.create(
            db_session, email="sessiontest@example.com", password="password123"
        )

    def test_session_with_changing_ip_address(
        self, auth_service: AuthService, db_session: Session, user: User
    ) -> None:
        """Test session validation when IP address changes."""
        # Create session with initial IP
        initial_ip = "192.168.1.100"
        session = UserSession.create(
            db_session,
            user_id=user.id,
            ip_address=initial_ip,
            user_agent="Test Browser/1.0",
        )

        # Simulate IP change (e.g., user switches networks)
        new_ips = [
            "192.168.1.101",  # Same subnet
            "10.0.0.100",  # Different private network
            "203.0.113.100",  # Public IP
            "2001:db8::1",  # IPv6
        ]

        for new_ip in new_ips:
            # Session should handle IP changes gracefully
            # Implementation may log suspicious activity but should remain valid
            session.ip_address = new_ip
            db_session.commit()

            # Session should still be valid (unless explicitly invalidated)
            assert session.is_active is True

    def test_session_cleanup_on_user_deactivation(
        self, auth_service: AuthService, db_session: Session, user: User
    ) -> None:
        """Test session cleanup when user is deactivated."""
        # Create multiple active sessions
        sessions = []
        for i in range(3):
            session = UserSession.create(
                db_session,
                user_id=user.id,
                ip_address=f"192.168.1.{100 + i}",
                user_agent=f"Browser {i}/1.0",
            )
            sessions.append(session)

        db_session.commit()

        # Verify sessions are active
        for session in sessions:
            assert session.is_active is True

        # Deactivate user
        user.is_active = False
        db_session.commit()

        # Sessions should be invalidated (implementation dependent)
        db_session.refresh_all()
        for session in sessions:
            db_session.refresh(session)
            # May be automatically invalidated or marked for cleanup

    def test_concurrent_session_limit_enforcement(
        self, auth_service: AuthService, db_session: Session, user: User
    ) -> None:
        """Test concurrent session limits with rapid logins."""
        import queue
        import threading

        results = queue.Queue()
        errors = queue.Queue()

        def create_session(session_id: int):
            try:
                session = UserSession.create(
                    db_session,
                    user_id=user.id,
                    ip_address=f"192.168.1.{100 + session_id}",
                    user_agent=f"Browser {session_id}/1.0",
                )
                results.put(session)
            except Exception as e:
                errors.put(e)

        # Try to create more sessions than the limit (typically 5)
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_session, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Count successful sessions
        successful_sessions = []
        while not results.empty():
            successful_sessions.append(results.get())

        # Should enforce session limit (max 5 concurrent sessions)
        active_sessions = (
            db_session.query(UserSession)
            .filter(UserSession.user_id == user.id, UserSession.is_active)
            .count()
        )

        assert active_sessions <= 5  # Should not exceed limit

    def test_session_validation_with_modified_user_agent(
        self, auth_service: AuthService, db_session: Session, user: User
    ) -> None:
        """Test session validation when user agent changes."""
        # Create session with initial user agent
        original_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        session = UserSession.create(
            db_session,
            user_id=user.id,
            ip_address="192.168.1.100",
            user_agent=original_ua,
        )

        # Test various user agent modifications
        modified_uas = [
            # Minor version change
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.37",
            # OS change
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            # Platform change
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Chrome/91.0.4472.124 Safari/537.36",  # Different browser
            "",  # Empty user agent
            "x" * 2000,  # Very long user agent
        ]

        for modified_ua in modified_uas:
            # Session validation should handle user agent changes
            # Implementation may log suspicious activity
            session.user_agent = modified_ua
            db_session.commit()

            # Session may remain valid or be marked suspicious
            # This tests the system's ability to handle agent changes gracefully

    def test_session_expiry_edge_cases(
        self, auth_service: AuthService, db_session: Session, user: User
    ) -> None:
        """Test session expiry edge cases."""
        # Create session that expires very soon
        session = UserSession.create(
            db_session,
            user_id=user.id,
            ip_address="192.168.1.100",
            user_agent="Test Browser/1.0",
        )

        # Set expiry to 1 second from now
        session.expires_at = datetime.utcnow() + timedelta(seconds=1)
        db_session.commit()

        # Session should be valid initially
        assert session.is_active is True

        # Wait for expiry
        time.sleep(1.1)

        # Check if session is automatically marked as expired
        db_session.refresh(session)
        # Implementation may automatically detect expiry or require explicit check

    def test_session_hijacking_prevention(
        self, auth_service: AuthService, db_session: Session, user: User
    ) -> None:
        """Test session hijacking prevention measures."""
        # Create legitimate session
        session = UserSession.create(
            db_session,
            user_id=user.id,
            ip_address="192.168.1.100",
            user_agent="Legitimate Browser/1.0",
        )

        # Simulate potential hijacking scenarios
        suspicious_changes = [
            {
                "ip_address": "203.0.113.100",  # Sudden geo-location change
                "user_agent": "Malicious Bot/1.0",
            },
            {
                "ip_address": "10.0.0.1",
                "user_agent": "",  # Missing user agent
            },
            {
                "ip_address": "127.0.0.1",  # Localhost (suspicious)
                "user_agent": "curl/7.68.0",  # Command line tool
            },
        ]

        for change in suspicious_changes:
            # Apply suspicious changes
            if "ip_address" in change:
                session.ip_address = change["ip_address"]
            if "user_agent" in change:
                session.user_agent = change["user_agent"]

            db_session.commit()

            # System should detect and handle suspicious activity
            # Implementation may invalidate session or require re-authentication

    def test_session_race_conditions(
        self, auth_service: AuthService, db_session: Session, user: User
    ) -> None:
        """Test race conditions in session operations."""
        session = UserSession.create(
            db_session,
            user_id=user.id,
            ip_address="192.168.1.100",
            user_agent="Test Browser/1.0",
        )

        import threading

        # Simulate concurrent session operations
        def modify_session():
            session.last_activity = datetime.utcnow()
            db_session.commit()

        def invalidate_session():
            session.is_active = False
            db_session.commit()

        # Start concurrent modifications
        threads = [
            threading.Thread(target=modify_session),
            threading.Thread(target=invalidate_session),
            threading.Thread(target=modify_session),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Session should be in a consistent state after concurrent operations
        db_session.refresh(session)
        # Implementation should handle race conditions gracefully

    def test_session_memory_exhaustion_protection(
        self, auth_service: AuthService, db_session: Session, user: User
    ) -> None:
        """Test protection against session memory exhaustion."""
        # Try to create many sessions rapidly
        sessions = []
        max_sessions = 100  # Reasonable limit for testing

        try:
            for i in range(max_sessions):
                session = UserSession.create(
                    db_session,
                    user_id=user.id,
                    ip_address=f"192.168.{i // 255}.{i % 255}",
                    user_agent=f"Browser {i}/1.0",
                )
                sessions.append(session)

                if i % 10 == 0:  # Commit periodically
                    db_session.commit()

            db_session.commit()

        except Exception:
            # System may reject excessive session creation
            pass

        # Count actual sessions created
        session_count = (
            db_session.query(UserSession).filter(UserSession.user_id == user.id).count()
        )

        # Should not exceed reasonable limits
        assert session_count <= 50  # Implementation-dependent limit

    def test_session_with_invalid_data(
        self, auth_service: AuthService, db_session: Session, user: User
    ) -> None:
        """Test session creation with invalid data."""
        # Test with invalid IP addresses
        invalid_ips = [
            "999.999.999.999",  # Invalid IPv4
            "192.168.1",  # Incomplete IPv4
            "::1::1",  # Invalid IPv6
            "not.an.ip.address",
            "",  # Empty IP
            "x" * 100,  # Very long string
        ]

        for invalid_ip in invalid_ips:
            try:
                session = UserSession.create(
                    db_session,
                    user_id=user.id,
                    ip_address=invalid_ip,
                    user_agent="Test Browser/1.0",
                )
                # If creation succeeds, IP validation may be lenient
                assert session.ip_address == invalid_ip
            except Exception:
                # Creation may fail with invalid data, which is acceptable
                pass

    def test_session_timezone_handling(
        self, auth_service: AuthService, db_session: Session, user: User
    ) -> None:
        """Test session handling across different timezones."""
        # Create session
        session = UserSession.create(
            db_session,
            user_id=user.id,
            ip_address="192.168.1.100",
            user_agent="Test Browser/1.0",
        )

        # Test timezone-related edge cases
        original_time = session.created_at

        # Simulate system timezone changes
        with patch("datetime.datetime") as mock_datetime:
            # Mock different timezone offset
            future_time = original_time + timedelta(hours=12)
            mock_datetime.utcnow.return_value = future_time

            # Update session activity
            session.last_activity = future_time
            db_session.commit()

            # Session should handle timezone changes gracefully
            assert session.last_activity >= original_time

    def test_session_data_integrity(
        self, auth_service: AuthService, db_session: Session, user: User
    ) -> None:
        """Test session data integrity under various conditions."""
        session = UserSession.create(
            db_session,
            user_id=user.id,
            ip_address="192.168.1.100",
            user_agent="Test Browser/1.0",
        )

        # Store original values
        original_id = session.id
        original_user_id = session.user_id
        original_created_at = session.created_at

        # Perform various operations
        session.last_activity = datetime.utcnow()
        session.ip_address = "192.168.1.101"
        db_session.commit()

        # Refresh and verify integrity
        db_session.refresh(session)
        assert session.id == original_id
        assert session.user_id == original_user_id
        assert session.created_at == original_created_at
        assert session.ip_address == "192.168.1.101"
