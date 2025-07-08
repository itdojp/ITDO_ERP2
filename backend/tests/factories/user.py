"""Factory for User model."""

from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models.user import User
from tests.factories import BaseFactory, fake


class UserFactory(BaseFactory):
    """Factory for creating User test instances."""

    model_class = User  # Model class for this factory

    @classmethod
    def _get_default_attributes(cls) -> Dict[str, Any]:
        """Get default attributes for creating User instances."""
        return {
            "email": fake.unique.email(),
            "full_name": fake.name(),
            "phone": fake.phone_number(),
            "is_active": True,
            "is_superuser": False,
            "hashed_password": fake.password(length=60),  # Simulated bcrypt hash length
        }

    @classmethod
    def _get_update_attributes(cls) -> Dict[str, Any]:
        """Get default attributes for updating User instances."""
        return {
            "full_name": fake.name(),
            "phone": fake.phone_number(),
            "is_active": fake.boolean(),
        }

    @classmethod
    def create_with_password(cls, db_session, password: str, **kwargs) -> User:
        """Create a user with a specific password."""
        from app.core.security import hash_password

        kwargs["hashed_password"] = hash_password(password)
        return cls.create(db_session, **kwargs)

    @classmethod
    def create_admin(cls, db_session, **kwargs) -> User:
        """Create an admin user."""
        kwargs["is_superuser"] = True
        kwargs["email"] = kwargs.get("email", fake.unique.email())
        return cls.create(db_session, **kwargs)

    @classmethod
    def create_inactive(cls, db_session, **kwargs) -> User:
        """Create an inactive user."""
        kwargs["is_active"] = False
        return cls.create(db_session, **kwargs)

    @classmethod
    def create_with_department(cls, db_session, department_id: int, **kwargs) -> User:
        """Create a user in a specific department."""
        kwargs["department_id"] = department_id
        return cls.create(db_session, **kwargs)

    @classmethod
    def create_with_email_domain(cls, db_session, domain: str, **kwargs) -> User:
        """Create a user with a specific email domain."""
        username = fake.user_name()
        kwargs["email"] = f"{username}@{domain}"
        return cls.create(db_session, **kwargs)

    @classmethod
    def create_test_users_set(cls, db_session):
        """Create a standard set of test users."""
        users = {}

        # Admin user
        users["admin"] = cls.create_admin(
            db_session, email="admin@example.com", full_name="Admin User"
        )

        # Manager user
        users["manager"] = cls.create(
            db_session, email="manager@example.com", full_name="Manager User"
        )

        # Regular user
        users["user"] = cls.create(
            db_session, email="user@example.com", full_name="Regular User"
        )

        # Inactive user
        users["inactive"] = cls.create_inactive(
            db_session, email="inactive@example.com", full_name="Inactive User"
        )

        return users

    @classmethod
    def create_minimal(cls, db_session, **kwargs) -> User:
        """Create a user with minimal required fields."""
        minimal_attrs = {
            "email": fake.unique.email(),
            "full_name": fake.name(),
            "is_active": True,
            "is_superuser": False,
            "hashed_password": fake.password(length=60),
        }
        minimal_attrs.update(kwargs)
        return cls.create(db_session, **minimal_attrs)


# Helper function for backward compatibility
def create_test_user(db_session: Session, **kwargs) -> User:
    """Create a test user (backward compatibility wrapper)."""
    # Extract password if provided, otherwise use default
    password = kwargs.pop("password", "TestPassword123!")
    return UserFactory.create_with_password(db_session, password, **kwargs)
