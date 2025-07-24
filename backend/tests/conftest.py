"""Simplified pytest configuration for authentication tests."""

import os
import sys
import uuid
from collections.abc import Generator
from datetime import datetime
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment variables
if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
if not os.environ.get("SECRET_KEY"):
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-32-chars-long"
if not os.environ.get("ALGORITHM"):
    os.environ["ALGORITHM"] = "HS256"
if not os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES"):
    os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "1440"
if not os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS"):
    os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
if not os.environ.get("BCRYPT_ROUNDS"):
    os.environ["BCRYPT_ROUNDS"] = "4"

# Import all models to ensure proper registration
import app.models  # This will import all models via __init__.py

# Now import app components
from app.core import database

# Import base first
from app.models.base import Base
from tests.factories import OrganizationFactory, UserFactory

# Database configuration based on test type
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://itdo_user:itdo_password@localhost:5432/itdo_erp"
)

# For SQLite tests (unit tests) - check for both unit test patterns
if (
    "unit" in os.getenv("PYTEST_CURRENT_TEST", "")
    or "tests/unit" in os.getenv("PYTEST_CURRENT_TEST", "")
    or os.getenv("USE_SQLITE", "false").lower() == "true"
    or "tests/unit" in " ".join(sys.argv)  # Check command line args
):
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # For integration tests, use PostgreSQL
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

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
def test_permissions(db_session: Session) -> Dict[str, Any]:
    """Create test permissions for role testing."""
    from app.models.permission import Permission

    # Create permissions by category
    user_perms = [
        Permission(code="user:read", name="Read Users", category="users"),
        Permission(code="user:write", name="Write Users", category="users"),
        Permission(code="user:delete", name="Delete Users", category="users"),
    ]

    role_perms = [
        Permission(code="role:read", name="Read Roles", category="roles"),
        Permission(code="role:write", name="Write Roles", category="roles"),
        Permission(code="role:delete", name="Delete Roles", category="roles"),
    ]

    all_perms = user_perms + role_perms
    db_session.add_all(all_perms)
    db_session.commit()
    return {
        "users": user_perms,
        "roles": role_perms,
        "all": all_perms,
    }


@pytest.fixture
def test_role_system(
    db_session: Session, test_organization, test_permissions
) -> Dict[str, Any]:
    """Create a test role system with hierarchy."""
    from tests.factories import RoleFactory

    # Create roles
    admin_role = RoleFactory.create_with_organization(
        db_session, test_organization, name="システム管理者", code="ADMIN"
    )
    manager_role = RoleFactory.create_with_organization(
        db_session, test_organization, name="マネージャー", code="MANAGER"
    )
    user_role = RoleFactory.create_with_organization(
        db_session, test_organization, name="一般ユーザー", code="USER"
    )
    return {
        "organization": test_organization,
        "permissions": test_permissions,
        "roles": {
            "admin": admin_role,
            "manager": manager_role,
            "user": user_role,
        },
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
def test_admin(db_session: Session):
    """Create a test admin user."""
    unique_id = str(uuid.uuid4())[:8]
    return UserFactory.create_with_password(
        db_session,
        password="AdminPassword123!",
        email=f"admin_{unique_id}@example.com",
        full_name=f"Admin User {unique_id}",
        is_superuser=True,
    )


@pytest.fixture
def test_organization(db_session: Session):
    """Create a test organization."""
    unique_id = str(uuid.uuid4())[:8]
    return OrganizationFactory.create(
        db_session,
        name=f"Test Organization {unique_id}",
        code=f"TEST-ORG-{unique_id}",
        industry="IT",
    )


@pytest.fixture
def user_token(test_user):
    """Create a token for the test user."""
    from app.core.security import create_access_token

    return create_access_token({"sub": str(test_user.id)})


@pytest.fixture
def admin_token(test_admin):
    """Create a token for the test admin."""
    from app.core.security import create_access_token

    return create_access_token({"sub": str(test_admin.id)})


@pytest.fixture
def client():
    """Create a test client."""
    from app.main import app

    return TestClient(app)


def create_auth_headers(token: str) -> dict[str, str]:
    """Create authorization headers for API requests."""
    return {"Authorization": f"Bearer {token}"}


# Additional fixtures for CC02 v49.0 TDD Implementation
import asyncio
from typing import AsyncIterator

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Test database URL for async tests
TEST_ASYNC_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test async engine
test_async_engine = create_async_engine(
    TEST_ASYNC_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

# Create async test session factory
AsyncTestSessionLocal = async_sessionmaker(
    test_async_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_db() -> AsyncIterator[AsyncSession]:
    """Create an async test database session."""
    async with AsyncTestSessionLocal() as session:
        yield session


@pytest.fixture
async def async_client(async_db: AsyncSession) -> AsyncIterator[AsyncClient]:
    """Create an async test client with database override."""
    from app.core.database import get_db
    from app.main_super_minimal import app

    def override_get_db():
        return async_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def setup_sync_test_data():
    """Setup and cleanup test data for each test."""
    # Setup - clear any existing data
    from app.api.v1.endpoints.products import price_history_store, products_store

    products_store.clear()
    price_history_store.clear()

    yield

    # Cleanup
    products_store.clear()
    price_history_store.clear()


# Sync TestClient for TDD tests
@pytest.fixture
def sync_test_client():
    """Create a sync test client for TDD tests."""
    from fastapi.testclient import TestClient

    from app.main_super_minimal import app

    # Override the database dependency to return a mock
    def override_get_db():
        return None  # We'll use in-memory storage for TDD

    from app.core.database import get_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# Alias fixtures for backward compatibility with TDD tests
@pytest.fixture
def api_client(sync_test_client):
    """Alias for sync test client for TDD test compatibility."""
    return sync_test_client
