"""Factory classes for creating test data."""

from abc import ABC, abstractmethod
from typing import Any, TypeVar

from faker import Faker
from sqlalchemy.orm import Session

from app.models.base import SoftDeletableModel

fake = Faker("ja_JP")  # Japanese locale for more realistic test data

T = TypeVar("T", bound=SoftDeletableModel)


class BaseFactory(ABC):
    """Base factory class for creating test model instances."""

    model_class: type[T]  # Abstract class variable to be overridden in subclasses

    @classmethod
    def build_dict(cls, **kwargs: Any) -> dict[str, Any]:
        """Build a dictionary of attributes for model creation."""
        defaults = cls._get_default_attributes()
        defaults.update(kwargs)
        return defaults

    @classmethod
    def build_update_dict(cls, **kwargs: Any) -> dict[str, Any]:
        """Build a dictionary of attributes for model updates."""
        # For updates, we typically want a subset of fields
        defaults = cls._get_update_attributes()
        defaults.update(kwargs)
        return defaults

    @classmethod
    def build(cls, **kwargs: Any) -> Any:
        """Build a model instance without saving to database."""
        attributes = cls.build_dict(**kwargs)
        # Use the class variable directly
        return cls.model_class(**attributes)

    @classmethod
    def create(cls, db_session: Session, **kwargs: Any) -> T:
        """Create and save a model instance to database."""
        instance = cls.build(**kwargs)
        db_session.add(instance)
        db_session.commit()
        db_session.refresh(instance)
        return instance

    @classmethod
    def create_batch(cls, db_session: Session, count: int, **kwargs: Any) -> list[T]:
        """Create multiple instances."""
        instances = []
        for i in range(count):
            instance_kwargs = kwargs.copy()
            # Add sequence number to make names unique
            if "name" in instance_kwargs:
                instance_kwargs["name"] = f"{instance_kwargs['name']}{i}"
            elif "code" in instance_kwargs:
                instance_kwargs["code"] = f"{instance_kwargs['code']}{i}"
            instances.append(cls.create(db_session, **instance_kwargs))
        return instances

    @classmethod
    @abstractmethod
    def _get_default_attributes(cls) -> dict[str, Any]:
        """Get default attributes for creating instances."""
        pass

    @classmethod
    def _get_update_attributes(cls) -> dict[str, Any]:
        """Get default attributes for updating instances."""
        # By default, return a subset of create attributes
        defaults = cls._get_default_attributes()
        # Remove fields that shouldn't be updated
        excluded_fields = {"id", "created_at", "created_by"}
        return {k: v for k, v in defaults.items() if k not in excluded_fields}


# Re-export factory classes
from tests.factories.audit import AuditLogFactory
from tests.factories.department import DepartmentFactory, create_test_department
from tests.factories.organization import OrganizationFactory, create_test_organization
from tests.factories.role import (
    PermissionFactory,
    RoleFactory,
    UserRoleFactory,
    create_test_role,
    create_test_user_role,
)
from tests.factories.user import UserFactory, create_test_user

__all__ = [
    "BaseFactory",
    "AuditLogFactory",
    "OrganizationFactory",
    "DepartmentFactory",
    "RoleFactory",
    "UserRoleFactory",
    "PermissionFactory",
    "UserFactory",
    "create_test_user",
    "create_test_organization",
    "create_test_department",
    "create_test_role",
    "create_test_user_role",
    "fake",
]
