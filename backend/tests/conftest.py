"""Pytest configuration and fixtures."""

import pytest
from typing import Generator, Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.core.security import create_access_token


# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Create a clean database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with overridden database dependency."""
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user."""
    user = User.create(
        db_session,
        email="testuser@example.com",
        password="TestPassword123!",
        full_name="Test User"
    )
    db_session.commit()
    return user


@pytest.fixture
def test_admin(db_session: Session) -> User:
    """Create a test admin user."""
    admin = User.create(
        db_session,
        email="admin@example.com",
        password="AdminPassword123!",
        full_name="Admin User",
        is_superuser=True
    )
    db_session.commit()
    return admin


@pytest.fixture
def user_token(test_user: User) -> str:
    """Create an access token for test user."""
    return create_access_token(
        data={
            "sub": str(test_user.id),
            "email": test_user.email,
            "is_superuser": False
        }
    )


@pytest.fixture
def admin_token(test_admin: User) -> str:
    """Create an access token for admin user."""
    return create_access_token(
        data={
            "sub": str(test_admin.id),
            "email": test_admin.email,
            "is_superuser": True
        }
    )


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch: Any) -> None:
    """Set up test environment variables."""
    # Set test environment variables
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-testing-only-32-chars-long")
    monkeypatch.setenv("ALGORITHM", "HS256")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
    monkeypatch.setenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
    monkeypatch.setenv("BCRYPT_ROUNDS", "4")  # Lower rounds for faster tests
    monkeypatch.setenv("DATABASE_URL", SQLALCHEMY_DATABASE_URL)


def get_test_db() -> Generator[Session, None, None]:
    """Get test database session."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


def create_test_user(
    email: str = "test@example.com",
    password: str = "TestPassword123!",
    full_name: str = "Test User",
    is_superuser: bool = False,
    organization_id: int = 1
) -> User:
    """Create a test user."""
    # Create a simple user object for testing
    user = User(
        id=1,
        email=email,
        full_name=full_name,
        is_active=True,
        is_superuser=is_superuser
    )
    return user


def create_test_jwt_token(user: User, expired: bool = False) -> str:
    """Create a test JWT token."""
    from datetime import timedelta
    
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "is_superuser": user.is_superuser
    }
    
    if expired:
        # Create expired token
        expires_delta = timedelta(minutes=-30)
    else:
        expires_delta = timedelta(minutes=30)
    
    return create_access_token(data=token_data, expires_delta=expires_delta)