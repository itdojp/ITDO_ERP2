"""Pytest configuration and fixtures."""

# Use PostgreSQL for integration tests (same as development)
import os
import uuid
from collections.abc import Generator
from datetime import datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.core.security import create_access_token

# Import all models to ensure they are registered with SQLAlchemy
from app.models import Department, Organization, Permission, Role, User
from app.models.base import Base
from tests.factories import (
    DepartmentFactory,
    OrganizationFactory,
    PermissionFactory,
    RoleFactory,
    UserFactory,
)

# Determine database URL based on environment
# CI environment always uses SQLite regardless of DATABASE_URL
if os.getenv("CI") or "GITHUB_ACTIONS" in os.environ:
    # Always use SQLite in CI environment regardless of DATABASE_URL
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
elif os.getenv("DATABASE_URL"):
    # DATABASE_URL is set in local development, check if accessible
    try:
        SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
        test_engine = create_engine(SQLALCHEMY_DATABASE_URL)
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        # Connection successful, use it
        engine = test_engine
    except Exception:
        # DATABASE_URL set but not accessible, fallback to SQLite
        SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
else:
    # For local development - try PostgreSQL first, fallback to SQLite
    try:
        SQLALCHEMY_DATABASE_URL = (
            "postgresql://itdo_user:itdo_password@localhost:5432/itdo_erp"
        )
        test_engine = create_engine(SQLALCHEMY_DATABASE_URL)
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        # Connection successful, use PostgreSQL
        engine = test_engine
    except Exception:
        # PostgreSQL not available, use SQLite for all tests
        SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
    """テスト前に関連テーブルをクリア"""
    yield  # テスト実行

    # テスト後のクリーンアップは db_session fixture で処理される


@pytest.fixture
def db_session() -> Generator[Session]:
    """Create a clean database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create session
    session = TestingSessionLocal()

    try:
        # Start transaction for test isolation
        session.begin()
        yield session
    except Exception:
        # Rollback on any exception
        session.rollback()
        raise
    finally:
        # Always rollback to ensure clean state
        session.rollback()
        session.close()

        # Enhanced cleanup for test isolation
        if "postgresql" in str(engine.url):
            # Use TRUNCATE for better performance and reset sequences
            with engine.begin() as conn:
                from sqlalchemy import text

                # TRUNCATE in safe order
                table_order = [
                    "tasks",
                    "user_roles",
                    "role_permissions",
                    "password_history",
                    "user_sessions",
                    "user_activity_logs",
                    "audit_logs",
                    "project_members",
                    "project_milestones",
                    "projects",
                    "users",
                    "roles",
                    "permissions",
                    "departments",
                    "organizations",
                ]
                for table in table_order:
                    conn.execute(
                        text(f'TRUNCATE TABLE "{table}" RESTART IDENTITY CASCADE')
                    )
        else:
            # For SQLite, drop and recreate all tables for complete isolation
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient]:
    """Create a test client with overridden database dependency."""
    # Import here to avoid circular imports
    from app.main import app
    # Also patch the app's database module
    import app.core.database as app_db
    import app.core.dependencies as app_deps
    
    # Store original engine and sessions
    original_engine = app_db.engine
    original_session_local = app_db.SessionLocal
    original_deps_session_local = app_deps.SessionLocal
    
    # Replace with test engine
    app_db.engine = engine
    app_db.SessionLocal = TestingSessionLocal
    app_deps.SessionLocal = TestingSessionLocal

    def override_get_db() -> Generator[Session]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # Restore original engine and sessions
        app_db.engine = original_engine
        app_db.SessionLocal = original_session_local
        app_deps.SessionLocal = original_deps_session_local
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
def setup_test_environment(monkeypatch: Any) -> None:
    """Set up test environment variables."""
    # Set test environment variables
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-testing-only-32-chars-long")
    monkeypatch.setenv("ALGORITHM", "HS256")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
    monkeypatch.setenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
    monkeypatch.setenv("BCRYPT_ROUNDS", "4")  # Lower rounds for faster tests
    monkeypatch.setenv("DATABASE_URL", SQLALCHEMY_DATABASE_URL)


# Utility Functions for Tests


def create_auth_headers(token: str) -> dict[str, str]:
    """Create authorization headers with bearer token."""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers():
    """Provide auth headers helper function."""
    return create_auth_headers
