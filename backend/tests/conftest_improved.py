"""Improved pytest configuration and fixtures."""

import pytest
import asyncio
from typing import Generator, Any, Dict
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db
from app.models.base import Base
# Import all models to ensure they are registered with SQLAlchemy
from app.models import (
    User, Organization, Department, Role, UserRole, RolePermission,
    Permission, PasswordHistory, UserSession, UserActivityLog,
    AuditLog, Project, ProjectMember, ProjectMilestone
)
from app.core.security import create_access_token
from tests.factories import (
    UserFactory, 
    OrganizationFactory, 
    DepartmentFactory, 
    RoleFactory, 
    PermissionFactory
)


# Test database configuration
import os
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://itdo_user:itdo_password@localhost:5432/itdo_erp_test")

# Force SQLite for unit tests, PostgreSQL for integration
if "unit" in os.getenv("PYTEST_CURRENT_TEST", "") or os.getenv("USE_SQLITE_TESTS", "false").lower() == "true":
    TEST_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # For integration tests, use PostgreSQL with proper isolation
    engine = create_engine(
        TEST_DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False  # Disable SQL echo in CI
    )

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def setup_test_database():
    """Set up test database once per session."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up after all tests
    if "postgresql" in str(engine.url):
        with engine.begin() as conn:
            # Drop all tables
            Base.metadata.drop_all(bind=conn)


@pytest.fixture
def db_session(setup_test_database) -> Generator[Session, None, None]:
    """Create a clean database session for each test with improved cleanup."""
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        
        # Improved cleanup for PostgreSQL
        if "postgresql" in str(engine.url):
            with engine.begin() as conn:
                # Disable foreign key checks temporarily
                conn.execute(text("SET session_replication_role = replica;"))
                
                # Get all table names in dependency order (reverse of creation)
                tables = list(reversed(Base.metadata.sorted_tables))
                
                # Delete all data from tables
                for table in tables:
                    conn.execute(text(f'DELETE FROM "{table.name}"'))
                
                # Reset sequences (for auto-incrementing IDs)
                for table in tables:
                    # Reset sequence if table has an auto-incrementing primary key
                    pk_cols = [col for col in table.columns if col.primary_key and col.autoincrement]
                    if pk_cols:
                        seq_name = f"{table.name}_{pk_cols[0].name}_seq"
                        try:
                            conn.execute(text(f'ALTER SEQUENCE "{seq_name}" RESTART WITH 1'))
                        except Exception:
                            # Sequence might not exist, ignore
                            pass
                
                # Re-enable foreign key checks
                conn.execute(text("SET session_replication_role = DEFAULT;"))
        else:
            # For SQLite, recreate tables
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)


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


# User Fixtures with unique identifiers

@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a basic test user with unique email."""
    unique_id = id(db_session) % 10000  # Use session id for uniqueness
    return UserFactory.create_with_password(
        db_session,
        password="TestPassword123!",
        email=f"testuser{unique_id}@example.com",
        full_name="Test User"
    )


@pytest.fixture
def test_admin(db_session: Session) -> User:
    """Create a test admin user with unique email."""
    unique_id = id(db_session) % 10000  # Use session id for uniqueness
    return UserFactory.create_with_password(
        db_session,
        password="AdminPassword123!",
        email=f"admin{unique_id}@example.com",
        full_name="Admin User",
        is_superuser=True
    )


@pytest.fixture
def test_manager(db_session: Session) -> User:
    """Create a test manager user with unique email."""
    unique_id = id(db_session) % 10000  # Use session id for uniqueness
    return UserFactory.create_with_password(
        db_session,
        password="ManagerPassword123!",
        email=f"manager{unique_id}@example.com",
        full_name="Manager User"
    )


@pytest.fixture
def test_users_set(db_session: Session) -> Dict[str, User]:
    """Create a complete set of test users with unique emails."""
    unique_id = id(db_session) % 10000
    return UserFactory.create_test_users_set(db_session, email_suffix=f"{unique_id}")


# Token Fixtures

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


@pytest.fixture
def manager_token(test_manager: User) -> str:
    """Create an access token for manager user."""
    return create_access_token(
        data={
            "sub": str(test_manager.id),
            "email": test_manager.email,
            "is_superuser": False
        }
    )


# Organization Fixtures

@pytest.fixture
def test_organization(db_session: Session) -> Organization:
    """Create a test organization with unique code."""
    unique_id = id(db_session) % 10000
    return OrganizationFactory.create(
        db_session,
        name=f"テスト株式会社{unique_id}",
        code=f"TEST-ORG-{unique_id}",
        industry="IT"
    )


@pytest.fixture
def test_organization_tree(db_session: Session) -> Dict[str, Any]:
    """Create an organization tree structure."""
    return OrganizationFactory.create_subsidiary_tree(db_session, depth=2, children_per_level=2)


# Department Fixtures

@pytest.fixture
def test_department(db_session: Session, test_organization: Organization) -> Department:
    """Create a test department with unique code."""
    unique_id = id(db_session) % 10000
    return DepartmentFactory.create_with_organization(
        db_session,
        test_organization,
        name=f"テスト部門{unique_id}",
        code=f"TEST-DEPT-{unique_id}"
    )


@pytest.fixture
def test_department_tree(db_session: Session, test_organization: Organization) -> Dict[str, Any]:
    """Create a department tree structure."""
    return DepartmentFactory.create_department_tree(
        db_session, 
        test_organization, 
        depth=3, 
        children_per_level=2
    )


# Role Fixtures

@pytest.fixture
def test_role(db_session: Session, test_organization: Organization) -> Role:
    """Create a test role with unique name."""
    unique_id = id(db_session) % 10000
    return RoleFactory.create_with_organization(
        db_session,
        test_organization,
        name=f"テストロール{unique_id}",
        role_type="custom"
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
        db_session,
        role_system['organization'],
        depth=3,
        children_per_level=2
    )
    
    # Create test users
    users = UserFactory.create_test_users_set(db_session)
    
    return {
        'organization': role_system['organization'],
        'departments': dept_tree,
        'roles': role_system['roles'],
        'permissions': role_system['permissions'],
        'users': users
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
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)


# Utility Functions for Tests

def create_auth_headers(token: str) -> Dict[str, str]:
    """Create authorization headers with bearer token."""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers():
    """Provide auth headers helper function."""
    return create_auth_headers