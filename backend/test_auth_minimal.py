#!/usr/bin/env python
"""Minimal test for authentication without full model dependencies."""

import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "1440"

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    """Base model."""

    pass


class User(Base):
    """Minimal User model for testing."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    # MFA fields
    mfa_required: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(32))
    google_id: Mapped[str | None] = mapped_column(String(255))

    # Security fields
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def is_locked(self) -> bool:
        """Check if account is locked."""
        if not self.locked_until:
            return False
        return datetime.now() < self.locked_until.replace(tzinfo=None)

    def record_failed_login(self, db):
        """Record failed login."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            from datetime import timedelta

            self.locked_until = datetime.now() + timedelta(minutes=30)

    def record_successful_login(self, db):
        """Record successful login."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login_at = datetime.now()

    def log_activity(self, db, action, details=None, ip_address=None, user_agent=None):
        """Placeholder for activity logging."""
        pass


class UserSession(Base):
    """Minimal UserSession model."""

    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    session_token: Mapped[str] = mapped_column(String(255), unique=True)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# Import security functions
from app.core.security import (
    create_access_token,
    generate_session_token,
    hash_password,
    verify_password,
)


def test_authentication():
    """Test basic authentication."""
    # Create database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    print("✓ Database created")

    # Create test user
    user = User(
        email="test@example.com",
        hashed_password=hash_password("SecurePass123!"),
        full_name="Test User",
        is_active=True,
        mfa_required=False,
    )
    session.add(user)
    session.commit()

    print("✓ User created")

    # Test password verification
    assert verify_password("SecurePass123!", user.hashed_password)
    assert not verify_password("WrongPassword", user.hashed_password)
    print("✓ Password verification works")

    # Test session creation
    user_session = UserSession(
        user_id=user.id,
        session_token=generate_session_token(),
        ip_address="127.0.0.1",
        user_agent="TestAgent",
        expires_at=datetime.now().replace(hour=23, minute=59),
    )
    session.add(user_session)
    session.commit()

    print("✓ Session created")

    # Test token creation
    token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "session_id": user_session.id,
        }
    )
    assert len(token) > 50
    print("✓ JWT token created")

    # Test MFA fields
    user.mfa_required = True
    user.mfa_secret = "TESTMFASECRET123"
    session.commit()

    assert user.mfa_required is True
    assert user.mfa_secret == "TESTMFASECRET123"
    print("✓ MFA fields work")

    # Test account locking
    for _ in range(5):
        user.record_failed_login(session)
    session.commit()

    assert user.is_locked()
    print("✓ Account locking works")

    session.close()
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    print("Running minimal authentication tests...\n")
    test_authentication()
