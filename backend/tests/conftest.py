"""Pytest configuration and fixtures."""

# Use PostgreSQL for integration tests (same as development)
import os
from typing import Any, Dict, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app

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

SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://itdo_user:itdo_password@localhost:5432/itdo_erp"
)

# For SQLite tests (unit tests)
if "unit" in os.getenv("PYTEST_CURRENT_TEST", ""):
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # For integration tests, use PostgreSQL
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
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
        # Clean up test data using safe DELETE order in PostgreSQL
        if "postgresql" in str(engine.url):
            # For PostgreSQL, use DELETE in dependency order to avoid
            # foreign key violations
            with engine.begin() as conn:
                from sqlalchemy import text

                # Simple approach: Delete in safe order
                table_order = [
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
                    conn.execute(text(f'DELETE FROM "{table}"'))
        else:
            # For SQLite, drop all tables
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
def test_users_set(db_session: Session) -> Dict[str, User]:
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
def test_organization_tree(db_session: Session) -> Dict[str, Any]:
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
) -> Dict[str, Any]:
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
def test_permissions(db_session: Session) -> Dict[str, list[Permission]]:
    """Create standard permissions."""
    return PermissionFactory.create_standard_permissions(db_session)


@pytest.fixture
def test_role_system(db_session: Session) -> Dict[str, Any]:
    """Create a complete role system with permissions."""
    return RoleFactory.create_complete_role_system(db_session)


# Complete System Fixtures


@pytest.fixture
def complete_test_system(db_session: Session) -> Dict[str, Any]:
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


def create_auth_headers(token: str) -> Dict[str, str]:
    """Create authorization headers with bearer token."""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers():
    """Provide auth headers helper function."""
    return create_auth_headers