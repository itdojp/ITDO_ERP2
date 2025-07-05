"""
Test factories for creating test data.
"""

from faker import Faker

from app.models.department import Department
from app.models.organization import Organization
from app.models.role import Role, UserRole
from app.models.user import User

fake = Faker("ja_JP")


def create_test_user(**kwargs) -> User:
    """Create a test user with optional overrides."""
    defaults = {
        "email": fake.email(),
        "full_name": fake.name(),
        "is_active": True,
        "is_superuser": False,
    }
    defaults.update(kwargs)

    return User(
        email=defaults["email"],
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        full_name=defaults["full_name"],
        is_active=defaults["is_active"],
        is_superuser=defaults["is_superuser"],
    )


def create_test_organization(**kwargs) -> Organization:
    """Create a test organization with optional overrides."""
    defaults = {
        "code": f"ORG{fake.random_int(min=1000, max=9999)}",
        "name": fake.company(),
        "name_kana": fake.name(),
        "postal_code": fake.postcode(),
        "address": fake.address(),
        "phone": fake.phone_number(),
        "email": fake.email(),
        "website": fake.url(),
        "fiscal_year_start": 4,
        "is_active": True,
    }
    defaults.update(kwargs)

    return Organization(**defaults)


def create_test_department(**kwargs) -> Department:
    """Create a test department with optional overrides."""
    # Require organization to be passed
    if "organization" not in kwargs and "organization_id" not in kwargs:
        raise ValueError("organization または organization_id が必要です")

    org = kwargs.pop("organization", None)
    org_id = kwargs.pop("organization_id", None)
    if org:
        org_id = org.id

    defaults = {
        "organization_id": org_id,
        "code": f"DEPT{fake.random_int(min=100, max=999)}",
        "name": f"{fake.word()}部",
        "name_kana": fake.name(),
        "level": 1,
        "sort_order": 0,
        "is_active": True,
    }
    defaults.update(kwargs)

    return Department(**defaults)


def create_test_role(**kwargs) -> Role:
    """Create a test role with optional overrides."""
    defaults = {
        "code": f"ROLE{fake.random_int(min=100, max=999)}",
        "name": f"ロール{fake.random_int(min=1, max=100)}",
        "description": fake.text(max_nb_chars=100),
        "permissions": ["read:*", "write:own"],
        "is_system": False,
        "is_active": True,
    }
    defaults.update(kwargs)

    return Role(**defaults)


def create_test_user_role(**kwargs) -> UserRole:
    """Create a test user role assignment with optional overrides."""
    # Extract related objects
    user = kwargs.pop("user", None)
    role = kwargs.pop("role", None)
    organization = kwargs.pop("organization", None)
    department = kwargs.pop("department", None)

    defaults = {
        "user_id": user.id if user else None,
        "role_id": role.id if role else None,
        "organization_id": organization.id if organization else None,
        "department_id": department.id if department else None,
        "assigned_by": user.id if user else None,
        "expires_at": None,
    }
    defaults.update(kwargs)

    return UserRole(**defaults)
