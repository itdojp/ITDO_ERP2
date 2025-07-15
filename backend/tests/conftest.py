"""Simplified pytest configuration for authentication tests."""

import os
import uuid
from collections.abc import Generator
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment variables
if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
if not os.environ.get("SECRET_KEY"):
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-32-chars-long"

# Import base first
from app.models.base import Base

# Import all models to ensure proper registration
import app.models  # This will import all models via __init__.py

# Now import app components  
from app.core import database
from tests.factories import UserFactory, OrganizationFactory

# Create in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Override the app's engine with our test engine
database.engine = engine
database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
try:
    Base.metadata.create_all(bind=engine, checkfirst=True)
    print(f"Created tables: {list(Base.metadata.tables.keys())}")
except Exception as e:
    print(f"ERROR: Failed to create database tables: {e}")
    raise


@pytest.fixture(autouse=True)
def isolate_test_data() -> dict[str, str]:
    """Generate unique test data for each test."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    unique_id = str(uuid.uuid4())[:8]
    return {
        "unique_email": f"test_{timestamp}_{unique_id}@example.com",
        "unique_code": f"TEST_{timestamp}_{unique_id}",
        "unique_name": f"Test Organization {timestamp}",
        "unique_id": unique_id,
        "timestamp": timestamp,
    }


@pytest.fixture
def db_session() -> Generator[Session]:
    """Create a clean database session for each test."""
    # Ensure tables exist
    Base.metadata.create_all(bind=engine, checkfirst=True)
    
    # Use transaction isolation for better test performance
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    try:
        yield session
    except Exception:
        transaction.rollback()
        raise
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def test_user(db_session: Session):
    """Create a basic test user."""
    unique_id = str(uuid.uuid4())[:8]
    return UserFactory.create_with_password(
        db_session,
        password="TestPassword123!",
        email=f"testuser_{unique_id}@example.com",
        full_name=f"Test User {unique_id}",
    )


@pytest.fixture
def test_organization(db_session: Session):
    """Create a test organization."""
    unique_id = str(uuid.uuid4())[:8]
    return OrganizationFactory.create(
        db_session,
        name=f"Test Organization {unique_id}",
        code=f"TEST-ORG-{unique_id}",
        industry="IT"
    )