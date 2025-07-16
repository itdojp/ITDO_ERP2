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
import uuid
from collections.abc import Generator
from datetime import datetime
from typing import Any

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Import all models to ensure proper registration
# This ensures all models are registered with SQLAlchemy metadata
# Now import app components
from app.core import database
from app.core.security import create_access_token

# Import base first
from app.models.base import Base
from app.models.department import Department
from app.models.organization import Organization
from app.models.permission import Permission
from app.models.role import Role

# Also import specific models we use in tests
from app.models.user import User

# from app.main import app  # Temporarily disabled due to syntax errors in API modules
from tests.factories import (
    DepartmentFactory,
    OrganizationFactory,
    PermissionFactory,
    RoleFactory,
    UserFactory,
)

# Determine database URL based on environment
# For SQLite tests (unit tests) - check for both unit test patterns
if (
    "unit" in os.getenv("PYTEST_CURRENT_TEST", "")
    or "tests/unit" in os.getenv("PYTEST_CURRENT_TEST", "")
    or os.getenv("USE_SQLITE", "false").lower() == "true"
):
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
# CI environment uses PostgreSQL from containers when available
elif os.getenv("CI") or "GITHUB_ACTIONS" in os.environ:
    # In CI, try PostgreSQL service first, fallback to SQLite
    if os.getenv("DATABASE_URL"):
        try:
            SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
            test_engine = create_engine(SQLALCHEMY_DATABASE_URL)
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            # Connection successful, use PostgreSQL service
            engine = test_engine
        except Exception:
            # PostgreSQL service not available, use SQLite
            SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
            engine = create_engine(
                SQLALCHEMY_DATABASE_URL,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
    else:
        # No DATABASE_URL set, use SQLite
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

# Override the app's engine with our test engine
database.engine = engine
database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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
    Base.metadata.create_all(bind=engine, checkfirst=True)

    # Use transaction isolation for better test performance and isolation
    if "sqlite" in str(engine.url):
        # For SQLite, use transaction isolation
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
    else:
        # For PostgreSQL, clean database before test for complete isolation
        with engine.begin() as conn:
            # TRUNCATE in safe order (cleanup before test)
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
                    conn.execute(
                        text(f'TRUNCATE TABLE "{table}" RESTART IDENTITY CASCADE')
                    )
                except Exception:
                    # Table might not exist, skip
                    pass
        # Create regular session for PostgreSQL
        session = TestingSessionLocal()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# @pytest.fixture
# def client(db_session: Session) -> Generator[TestClient]:
#     """Create a test client with overridden database dependency."""
#     # Temporarily disabled due to app import issues
#     pass


# User Fixtures


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a basic test user."""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    return UserFactory.create_with_password(
        db_session,
        password="TestPassword123!",
        email=f"testuser_{unique_id}@example.com",
        full_name=f"Test User {unique_id}",
    )


@pytest.fixture
def test_admin(db_session: Session) -> User:
    """Create a test admin user."""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    return UserFactory.create_with_password(
        db_session,
        password="AdminPassword123!",
        email=f"admin_{unique_id}@example.com",
        full_name=f"Admin User {unique_id}",
        is_superuser=True,
    )


@pytest.fixture
def test_manager(db_session: Session) -> User:
    """Create a test manager user."""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    return UserFactory.create_with_password(
        db_session,
        password="ManagerPassword123!",
        email=f"manager_{unique_id}@example.com",
        full_name=f"Manager User {unique_id}",
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
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    return OrganizationFactory.create(
        db_session,
        name=f"テスト株式会社-{unique_id}",
        code=f"TEST-ORG-{unique_id}",
        industry="IT",
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
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    return DepartmentFactory.create_with_organization(
        db_session,
        test_organization,
        name=f"テスト部門-{unique_id}",
        code=f"TEST-DEPT-{unique_id}",
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
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    return RoleFactory.create_with_organization(
        db_session,
        test_organization,
        name=f"テストロール-{unique_id}",
        role_type="custom",
    )


@pytest.fixture
def test_permissions(db_session: Session) -> dict[str, list[Permission]]:
    """Create standard permissions."""
    return PermissionFactory.create_standard_permissions(db_session)


@pytest.fixture
def test_role_system(db_session: Session) -> dict[str, Any]:
    """Create a complete role system with permissions."""
    return RoleFactory.create_complete_role_system(db_session)


# Database Cleanup Fixtures


@pytest.fixture(autouse=True)
def cleanup_database(db_session: Session) -> Generator[None, None, None]:
    """Automatically clean up database after each test to ensure isolation."""
    yield
    # Clean up test data after each test
    if "postgresql" in str(engine.url):
        # For PostgreSQL, use DELETE in dependency order
        with engine.begin() as conn:
            from sqlalchemy import text

            # Tables to clean in reverse dependency order
            table_order = [
                "tasks",  # Add tasks table
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
                    conn.execute(text(f'DELETE FROM "{table}"'))
                except Exception:
                    # Table might not exist, skip
                    pass

            conn.commit()
    else:
        # For SQLite, recreate all tables
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)


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
def reset_faker_unique() -> Generator[None, None, None]:
    """Reset Faker unique state before each test to prevent duplicate key errors."""
    from tests.factories import fake

    fake.unique.clear()
    yield
    fake.unique.clear()


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
