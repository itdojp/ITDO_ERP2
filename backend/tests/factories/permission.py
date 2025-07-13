"""Permission factory for testing."""

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.permission import Permission
from tests.factories import BaseFactory, fake


class PermissionFactory(BaseFactory):
    """Factory for creating Permission test instances."""

    model_class = Permission

    @classmethod
    def _get_default_attributes(cls) -> dict[str, Any]:
        """Get default attributes for creating Permission instances."""
        unique_id = str(uuid.uuid4())[:8]
        return {
            "code": f"test.{unique_id}",
            "name": fake.words(2, unique=True)[0],
            "description": fake.text(max_nb_chars=200),
            "category": fake.random_element(elements=["user", "role", "organization", "department", "project", "task"]),
            "is_active": True,
            "is_system": False,
        }

    @classmethod
    def create_system_permission(cls, db_session: Session, **kwargs) -> Permission:
        """Create a system permission."""
        kwargs["is_system"] = True
        return cls.create(db_session, **kwargs)

    @classmethod
    def create_with_category(cls, db_session: Session, category: str, **kwargs) -> Permission:
        """Create a permission with a specific category."""
        kwargs["category"] = category
        return cls.create(db_session, **kwargs)


# Helper function for backward compatibility
def create_test_permission(db_session: Session, **kwargs) -> Permission:
    """Create a test permission (backward compatibility wrapper)."""
    return PermissionFactory.create(db_session, **kwargs)