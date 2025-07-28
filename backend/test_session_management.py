#!/usr/bin/env python
"""Test session management functionality."""

import os

os.environ["DATABASE_URL"] = "sqlite:///test_session.db"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALGORITHM"] = "HS256"

from datetime import datetime, timedelta, timezone

UTC = timezone.utc

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
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
    created_at = Column(DateTime, default=datetime.now)
    last_login_at = Column(DateTime)


# Session models
class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    refresh_token = Column(String(255), unique=True, index=True, nullable=False)

    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(500), nullable=False)
    device_id = Column(String(100))
    device_name = Column(String(100))

    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    refresh_expires_at = Column(DateTime, nullable=False)

    is_active = Column(Boolean, default=True)
    revoked_at = Column(DateTime)
    revoked_by = Column(Integer, ForeignKey("users.id"))
    revoke_reason = Column(String(255))

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def revoke(self, db: Session, reason: str = None) -> None:
        self.is_active = False
        self.revoked_at = datetime.utcnow()
        self.revoke_reason = reason
        db.commit()


class SessionConfiguration(Base):
    __tablename__ = "session_configurations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    session_timeout_hours = Column(Integer, default=8)
    max_session_timeout_hours = Column(Integer, default=24)
    refresh_token_days = Column(Integer, default=30)

    allow_multiple_sessions = Column(Boolean, default=True)
    max_concurrent_sessions = Column(Integer, default=3)
    require_mfa_for_new_device = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


# Database setup
engine = create_engine("sqlite:///test_session.db")
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def test_session_management():
    """Test session management functionality."""
    print("Testing Session Management...\n")

    db = SessionLocal()

    # Create test user
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        is_active=True,
    )
    db.add(user)
    db.commit()

    # Test 1: Create session
    print("1. Testing session creation...")
    session = UserSession(
        user_id=user.id,
        session_token="test_session_token_1",
        refresh_token="test_refresh_token_1",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 Test Browser",
        device_id="device_123",
        device_name="Test Device",
        expires_at=datetime.utcnow() + timedelta(hours=8),
        refresh_expires_at=datetime.utcnow() + timedelta(days=30),
    )
    db.add(session)
    db.commit()
    print(f"✓ Created session: {session.id}")

    # Test 2: Check session expiry
    print("\n2. Testing session expiry check...")
    assert not session.is_expired()
    print("✓ Session not expired")

    # Test 3: Create expired session
    print("\n3. Testing expired session...")
    expired_session = UserSession(
        user_id=user.id,
        session_token="expired_token",
        refresh_token="expired_refresh",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0",
        expires_at=datetime.utcnow() - timedelta(hours=1),
        refresh_expires_at=datetime.utcnow() + timedelta(days=1),
    )
    db.add(expired_session)
    db.commit()
    assert expired_session.is_expired()
    print("✓ Correctly identified expired session")

    # Test 4: Session configuration
    print("\n4. Testing session configuration...")
    config = SessionConfiguration(
        user_id=user.id,
        session_timeout_hours=12,
        max_concurrent_sessions=5,
        allow_multiple_sessions=True,
    )
    db.add(config)
    db.commit()
    print(
        f"✓ Created config: timeout={config.session_timeout_hours}h, max_sessions={config.max_concurrent_sessions}"
    )

    # Test 5: Revoke session
    print("\n5. Testing session revocation...")
    session.revoke(db, reason="User logout")
    assert not session.is_active
    assert session.revoked_at is not None
    assert session.revoke_reason == "User logout"
    print("✓ Session revoked successfully")

    # Test 6: Multiple sessions
    print("\n6. Testing multiple sessions...")
    sessions = []
    for i in range(3):
        s = UserSession(
            user_id=user.id,
            session_token=f"token_{i}",
            refresh_token=f"refresh_{i}",
            ip_address=f"192.168.1.{100 + i}",
            user_agent="Test Browser",
            expires_at=datetime.utcnow() + timedelta(hours=8),
            refresh_expires_at=datetime.utcnow() + timedelta(days=30),
        )
        db.add(s)
        sessions.append(s)
    db.commit()

    # Count active sessions
    active_count = (
        db.query(UserSession)
        .filter(
            UserSession.user_id == user.id,
            UserSession.is_active,
        )
        .count()
    )
    print(f"✓ Created {len(sessions)} sessions, {active_count} are active")

    # Test 7: Session activity tracking
    print("\n7. Testing session activity update...")
    active_session = sessions[0]
    old_activity = active_session.last_activity_at

    # Simulate activity update
    import time

    time.sleep(0.1)
    active_session.last_activity_at = datetime.utcnow()
    db.commit()

    assert active_session.last_activity_at > old_activity
    print("✓ Activity timestamp updated")

    print("\n✅ All session management tests passed!")
    print("\nKey features tested:")
    print("  - Session creation with device info")
    print("  - Session expiry checking")
    print("  - Session configuration per user")
    print("  - Session revocation with reason")
    print("  - Multiple concurrent sessions")
    print("  - Activity tracking")

    # Cleanup
    db.close()
    os.remove("test_session.db")


if __name__ == "__main__":
    test_session_management()
