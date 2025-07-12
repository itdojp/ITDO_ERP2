"""Pytest configuration and fixtures."""

import os

# CRITICAL: Set test environment variables immediately to prevent PostgreSQL usage in CI
# This must happen before any app imports
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-32-chars-long"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "1440"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
os.environ["BCRYPT_ROUNDS"] = "4"

# Use PostgreSQL for integration tests (same as development)
import uuid
from collections.abc import Generator
from datetime import datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Import base first, then individual models to ensure proper registration
from app.models.base import Base

# Import all models individually to ensure proper registration
from app.models.user import User
from app.models.organization import Organization
from app.models.department import Department
from app.models.role import Role
from app.models.permission import Permission
from app.models.task import Task
from app.models.audit import AuditLog
from app.models.password_history import PasswordHistory
from app.models.user_session import UserSession
from app.models.user_activity_log import UserActivityLog
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.project_milestone import ProjectMilestone

# Now import app components
from app.core import database
from app.core.dependencies import get_db
from app.core.security import create_access_token
from app.main import app
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

# CRITICAL: Always force SQLite for CI to avoid PostgreSQL dependency issues
# This is a temporary fix until proper CI database setup is implemented
FORCE_SQLITE_IN_TESTS = True

is_ci = (
    os.getenv("CI") == "true"
    or os.getenv("GITHUB_ACTIONS") == "true"
    or os.getenv("GITHUB_WORKFLOW") is not None
    or os.getenv("RUNNER_OS") is not None
    or "runner" in os.getenv("HOME", "").lower()
    or os.getenv("PYTHONPATH", "").find("runner") != -1
    or FORCE_SQLITE_IN_TESTS
)

# Use SQLite for tests
if os.getenv("DATABASE_URL") and "sqlite" in os.getenv("DATABASE_URL"):
    # Use file-based SQLite if specified (for CI)
    SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # Use in-memory SQLite for local tests
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

# Override the app's engine with our test engine
database.engine = engine
database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create session factory with our test engine
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# CRITICAL: Ensure all tables are created immediately
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"ERROR: Failed to create database tables: {e}")
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
    """テスト前に関連テーブルをクリア"""
    yield  # テスト実行

    # テスト後のクリーンアップは db_session fixture で処理される


@pytest.fixture
def db_session() -> Generator[Session]:
    """Create a clean database session for each test."""
    # Ensure tables exist before each test
    Base.metadata.create_all(bind=engine)

    # Create session
    session = TestingSessionLocal()

    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        # Always rollback to ensure clean state
        session.rollback()
        session.close()

        # For SQLite, just clear data without dropping tables to preserve structure
        with engine.begin() as conn:
            # Clear data in reverse order to respect foreign keys
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
                try:
                    conn.execute(text(f"DELETE FROM {table}"))
                except Exception:
                    # Table might not exist, ignore
                    pass
            # Reset autoincrement for SQLite (if exists)
            try:
                conn.execute(text("DELETE FROM sqlite_sequence"))
            except Exception:
                # sqlite_sequence might not exist, ignore
                pass


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient]:
    """Create a test client with overridden database dependency."""

    def override_get_db() -> Generator[Session]:
        try:
            yield db_session
        finally:
            pass

    # Override the database dependency to use our test session
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

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
