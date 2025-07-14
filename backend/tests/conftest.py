"""Pytest configuration and fixtures."""

import os

# CRITICAL: Set test environment variables if not already set
# This must happen before any app imports
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

# Use PostgreSQL for integration tests (same as development)
import uuid
from collections.abc import Generator
from datetime import datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Import all models to ensure proper registration
# This ensures all models are registered with SQLAlchemy metadata
import app.models  # This will import all models via __init__.py

# Now import app components
from app.core import database
from app.core.dependencies import get_db
from app.core.security import create_access_token
from app.main import app

# Import base first
from app.models.base import Base
from app.models.department import Department
from app.models.organization import Organization
from app.models.permission import Permission
from app.models.role import Role

# Also import specific models we use in tests
from app.models.user import User
from tests.factories import (
    DepartmentFactory,
    OrganizationFactory,
    PermissionFactory,
    RoleFactory,
    UserFactory,
)

# Determine database URL based on environment
# CI environment always uses SQLite regardless of DATABASE_URL

# CRITICAL: Force SQLite for ANY CI environment detection
# GitHub Actions sets GITHUB_ACTIONS=true automatically
# Check multiple ways to detect CI environment

# Determine which database to use
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")
# print(f"DEBUG: DATABASE_URL from env = {DATABASE_URL}")

if "postgresql" in DATABASE_URL:
    # Use PostgreSQL (for CI or when explicitly configured)
    # print(f"DEBUG: Using PostgreSQL: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
elif "sqlite" in DATABASE_URL:
    # Use SQLite
    if DATABASE_URL == "sqlite:///:memory:":
        # print(f"DEBUG: Using in-memory SQLite")
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        # File-based SQLite
        # print(f"DEBUG: Using file-based SQLite: {DATABASE_URL}")
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,  # Use StaticPool for file-based SQLite too
        )
else:
    # Default to in-memory SQLite
    # print(f"DEBUG: Unknown database type, defaulting to in-memory SQLite")
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

# Override the app's engine with our test engine
database.engine = engine
database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create session factory with our test engine
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# CRITICAL: Ensure all tables are created immediately
# Force metadata creation after all models are imported
try:
    # Explicitly register all table metadata from imported models
    from app.models import *  # noqa: F403, F401

    Base.metadata.create_all(bind=engine, checkfirst=True)
    print(f"Created tables: {list(Base.metadata.tables.keys())}")
except Exception as e:
    print(f"ERROR: Failed to create database tables: {e}")
    print(f"Available metadata tables: {list(Base.metadata.tables.keys())}")
    raise


@pytest.fixture(autouse=True)
def isolate_test_data() -> dict[str, str]:
    """各テストで独立したデータを使用"""
    # 一意性を保証するテストデータ生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    unique_id = str(uuid.uuid4())[:8]
    return {
        "unique_email": f"test_{timestamp}_{unique_id}@example.com",
        "unique_code": f"TEST_{timestamp}_{unique_id}",
        "unique_name": f"Test Organization {timestamp}",
        "unique_id": unique_id,
        "timestamp": timestamp,
    }


@pytest.fixture(autouse=True)
def clean_test_database(db_session: Session) -> Generator[None]:
    """Ensure clean database state for each test."""
    # No pre-test cleanup needed - transaction isolation handles this
    yield  # Test execution

    # No post-test cleanup needed - transaction rollback handles this


@pytest.fixture
def db_session() -> Generator[Session]:
    """Create a clean database session for each test with transaction isolation."""
    # Ensure tables exist before each test
    try:
        # Force metadata refresh
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print(f"db_session: Created tables: {list(Base.metadata.tables.keys())}")
    except Exception as e:
        print(f"db_session: ERROR creating tables: {e}")
        raise

    # Create connection and begin transaction
    connection = engine.connect()
    transaction = connection.begin()

    # Create session bound to the transaction
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    except Exception:
        # Rollback transaction on error
        transaction.rollback()
        raise
    finally:
        # Always rollback transaction to ensure clean state
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient]:
    """Create a test client with properly isolated database dependency."""

    # Verify tables exist before creating client
    with engine.connect() as conn:
        inspector = inspect(conn)
        tables = inspector.get_table_names()
        if "departments" not in tables:
            # Recreate tables if missing
            Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session]:
        """Override database dependency to use isolated test session."""
        try:
            # CRITICAL: Use the same connection as the test session
            # This ensures all operations are part of the same transaction
            yield db_session
        finally:
            # Don't commit or rollback here - let the db_session fixture handle it
            pass

    # Override the database dependency to use our test session
    app.dependency_overrides[get_db] = override_get_db

    # Also override the app's database engine to use our test engine
    from app.core import database as app_database

    original_engine = app_database.engine
    original_session_local = app_database.SessionLocal

    app_database.engine = engine
    app_database.SessionLocal = TestingSessionLocal

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # Restore original database settings
        app_database.engine = original_engine
        app_database.SessionLocal = original_session_local
        # Clear overrides
        app.dependency_overrides.clear()


# User Fixtures


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a basic test user."""
    return UserFactory.create_with_password(
        db_session,
        password="TestPassword123!",
        email="testuser@example.com",
        full_name="Test User",
    )


@pytest.fixture
def test_admin(db_session: Session) -> User:
    """Create a test admin user."""
    return UserFactory.create_with_password(
        db_session,
        password="AdminPassword123!",
        email="admin@example.com",
        full_name="Admin User",
        is_superuser=True,
    )


@pytest.fixture
def test_manager(db_session: Session) -> User:
    """Create a test manager user."""
    return UserFactory.create_with_password(
        db_session,
        password="ManagerPassword123!",
        email="manager@example.com",
        full_name="Manager User",
    )


@pytest.fixture
def test_users_set(db_session: Session) -> dict[str, User]:
    """Create a complete set of test users."""
    return UserFactory.create_test_users_set(db_session)


# Token Fixtures


@pytest.fixture
def user_token(test_user: User) -> str:
    """Create an access token for test user."""
    return create_access_token(
        data={"sub": str(test_user.id), "email": test_user.email, "is_superuser": False}
    )


@pytest.fixture
def admin_token(test_admin: User) -> str:
    """Create an access token for admin user."""
    return create_access_token(
        data={
            "sub": str(test_admin.id),
            "email": test_admin.email,
            "is_superuser": True,
        }
    )


@pytest.fixture
def manager_token(test_manager: User) -> str:
    """Create an access token for manager user."""
    return create_access_token(
        data={
            "sub": str(test_manager.id),
            "email": test_manager.email,
            "is_superuser": False,
        }
    )


# Organization Fixtures


@pytest.fixture
def test_organization(db_session: Session) -> Organization:
    """Create a test organization."""
    return OrganizationFactory.create(
        db_session, name="テスト株式会社", code="TEST-ORG", industry="IT"
    )


@pytest.fixture
def test_organization_tree(db_session: Session) -> dict[str, Any]:
    """Create an organization tree structure."""
    return OrganizationFactory.create_subsidiary_tree(
        db_session, depth=2, children_per_level=2
    )


# Department Fixtures


@pytest.fixture
def test_department(db_session: Session, test_organization: Organization) -> Department:
    """Create a test department."""
    return DepartmentFactory.create_with_organization(
        db_session, test_organization, name="テスト部門", code="TEST-DEPT"
    )


@pytest.fixture
def test_department_tree(
    db_session: Session, test_organization: Organization
) -> dict[str, Any]:
    """Create a department tree structure."""
    return DepartmentFactory.create_department_tree(
        db_session, test_organization, depth=3, children_per_level=2
    )


# Role Fixtures


@pytest.fixture
def test_role(db_session: Session, test_organization: Organization) -> Role:
    """Create a test role."""
    return RoleFactory.create_with_organization(
        db_session, test_organization, name="テストロール", role_type="custom"
    )


@pytest.fixture
def test_permissions(db_session: Session) -> dict[str, list[Permission]]:
    """Create standard permissions."""
    return PermissionFactory.create_standard_permissions(db_session)


@pytest.fixture
def test_role_system(db_session: Session) -> dict[str, Any]:
    """Create a complete role system with permissions."""
    return RoleFactory.create_complete_role_system(db_session)


# Complete System Fixtures


@pytest.fixture
def complete_test_system(db_session: Session) -> dict[str, Any]:
    """Create a complete test system with all entities."""
    # Create role system (includes organization and permissions)
    role_system = RoleFactory.create_complete_role_system(db_session)

    # Create department structure
    dept_tree = DepartmentFactory.create_department_tree(
        db_session, role_system["organization"], depth=3, children_per_level=2
    )

    # Create test users
    users = UserFactory.create_test_users_set(db_session)

    return {
        "organization": role_system["organization"],
        "departments": dept_tree,
        "roles": role_system["roles"],
        "permissions": role_system["permissions"],
        "users": users,
    }


# Environment Setup


@pytest.fixture(autouse=True)
def setup_test_environment() -> None:
    """Set up test environment variables."""
    # Environment variables are already set at module level
    # This fixture ensures they remain set for each test
    pass


# Utility Functions for Tests


def create_auth_headers(token: str) -> dict[str, str]:
    """Create authorization headers with bearer token."""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers():
    """Provide auth headers helper function."""
    return create_auth_headers
