"""Base test classes and utilities for the ITDO ERP System."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, Type, TypeVar

from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.base import SoftDeletableModel
from tests.factories import BaseFactory

T = TypeVar("T", bound=SoftDeletableModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)


class BaseAPITestCase(
    ABC, Generic[T, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]
):
    """Base test case for API endpoints with common CRUD operations."""

    @property
    @abstractmethod
    def endpoint_prefix(self) -> str:
        """API endpoint prefix (e.g., '/api/v1/organizations')."""
        pass

    @property
    @abstractmethod
    def factory_class(self) -> Type[BaseFactory]:
        """Factory class for creating test instances."""
        pass

    @property
    @abstractmethod
    def create_schema_class(self) -> Type[CreateSchemaType]:
        """Schema class for create operations."""
        pass

    @property
    @abstractmethod
    def update_schema_class(self) -> Type[UpdateSchemaType]:
        """Schema class for update operations."""
        pass

    @property
    @abstractmethod
    def response_schema_class(self) -> Type[ResponseSchemaType]:
        """Schema class for API responses."""
        pass

    def get_auth_headers(self, token: str) -> Dict[str, str]:
        """Get authorization headers with bearer token."""
        return {"Authorization": f"Bearer {token}"}

    def create_test_instance(self, db_session: Session, **kwargs: Any) -> T:
        """Create a test instance using the factory."""
        return self.factory_class.create(db_session, **kwargs)

    def create_valid_payload(self, **overrides: Any) -> Dict[str, Any]:
        """Create a valid payload for create operations."""
        return self.factory_class.build_dict(**overrides)

    def create_update_payload(self, **overrides: Any) -> Dict[str, Any]:
        """Create a valid payload for update operations."""
        return self.factory_class.build_update_dict(**overrides)

    # CRUD Test Methods

    def test_list_endpoint_success(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test successful list operation."""
        # Create test instances
        instances = [self.create_test_instance(db_session) for _ in range(3)]

        response = client.get(
            self.endpoint_prefix, headers=self.get_auth_headers(admin_token)
        )

        print(f"Admin token: {admin_token}")
        print(f"Headers: {self.get_auth_headers(admin_token)}")
        print(f"Response status code: {response.status_code}")
        print(
            "Response body: "
            f"{response.json() if response.status_code != 204 else 'No content'}"
        )
        assert response.status_code == 200
        data = response.json()

        # Validate pagination structure
        assert "items" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert len(data["items"]) >= len(instances)

    def test_list_endpoint_pagination(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test pagination parameters."""
        # Create test instances
        for _ in range(5):
            self.create_test_instance(db_session)

        response = client.get(
            f"{self.endpoint_prefix}?skip=2&limit=2",
            headers=self.get_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 2
        assert data["limit"] == 2
        assert len(data["items"]) <= 2

    def test_list_endpoint_unauthorized(self, client: TestClient) -> None:
        """Test list operation without authentication."""
        response = client.get(self.endpoint_prefix)
        print(f"Response status code: {response.status_code}")
        print(
            "Response body: "
            f"{response.json() if response.status_code != 204 else 'No content'}"
        )
        assert response.status_code in [
            401,
            403,
        ]  # Either is acceptable for authentication failure

    def test_get_endpoint_success(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test successful get operation."""
        instance = self.create_test_instance(db_session)

        response = client.get(
            f"{self.endpoint_prefix}/{instance.id}",
            headers=self.get_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == instance.id

    def test_get_endpoint_not_found(self, client: TestClient, admin_token: str) -> None:
        """Test get operation with non-existent ID."""
        response = client.get(
            f"{self.endpoint_prefix}/99999", headers=self.get_auth_headers(admin_token)
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_create_endpoint_success(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Test successful create operation."""
        payload = self.create_valid_payload()

        response = client.post(
            self.endpoint_prefix,
            json=payload,
            headers=self.get_auth_headers(admin_token),
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data

        # Validate against response schema
        validated_data = self.response_schema_class.model_validate(data)
        assert validated_data.id is not None

    def test_create_endpoint_validation_error(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Test create operation with invalid payload."""
        payload = {}  # Empty payload should fail validation

        response = client.post(
            self.endpoint_prefix,
            json=payload,
            headers=self.get_auth_headers(admin_token),
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_update_endpoint_success(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test successful update operation."""
        instance = self.create_test_instance(db_session)
        payload = self.create_update_payload()

        response = client.put(
            f"{self.endpoint_prefix}/{instance.id}",
            json=payload,
            headers=self.get_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == instance.id

    def test_update_endpoint_not_found(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Test update operation with non-existent ID."""
        payload = self.create_update_payload()

        response = client.put(
            f"{self.endpoint_prefix}/99999",
            json=payload,
            headers=self.get_auth_headers(admin_token),
        )

        assert response.status_code == 404

    def test_delete_endpoint_success(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test successful delete operation."""
        instance = self.create_test_instance(db_session)

        response = client.delete(
            f"{self.endpoint_prefix}/{instance.id}",
            headers=self.get_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["id"] == instance.id

    def test_delete_endpoint_not_found(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Test delete operation with non-existent ID."""
        response = client.delete(
            f"{self.endpoint_prefix}/99999", headers=self.get_auth_headers(admin_token)
        )

        assert response.status_code == 404

    # Permission Tests

    def test_create_endpoint_forbidden(
        self, client: TestClient, user_token: str
    ) -> None:
        """Test create operation with insufficient permissions."""
        payload = self.create_valid_payload()

        response = client.post(
            self.endpoint_prefix,
            json=payload,
            headers=self.get_auth_headers(user_token),
        )

        # Should be forbidden unless user has specific permissions
        assert response.status_code in [403, 404]

    def test_update_endpoint_forbidden(
        self, client: TestClient, db_session: Session, user_token: str
    ) -> None:
        """Test update operation with insufficient permissions."""
        instance = self.create_test_instance(db_session)
        payload = self.create_update_payload()

        response = client.put(
            f"{self.endpoint_prefix}/{instance.id}",
            json=payload,
            headers=self.get_auth_headers(user_token),
        )

        # Should be forbidden unless user has specific permissions
        assert response.status_code in [403, 404]

    def test_delete_endpoint_forbidden(
        self, client: TestClient, db_session: Session, user_token: str
    ) -> None:
        """Test delete operation with insufficient permissions."""
        instance = self.create_test_instance(db_session)

        response = client.delete(
            f"{self.endpoint_prefix}/{instance.id}",
            headers=self.get_auth_headers(user_token),
        )

        # Should be forbidden unless user has specific permissions
        assert response.status_code in [403, 404]


class BaseServiceTestCase(ABC, Generic[T]):
    """Base test case for service layer testing."""

    @property
    @abstractmethod
    def service_class(self) -> Type:
        """Service class to test."""
        pass

    @property
    @abstractmethod
    def factory_class(self) -> Type[BaseFactory]:
        """Factory class for creating test instances."""
        pass

    def create_service(self, db_session: Session) -> Any:
        """Create service instance with database session."""
        return self.service_class(db_session)

    def create_test_instance(self, db_session: Session, **kwargs: Any) -> T:
        """Create a test instance using the factory."""
        return self.factory_class.create(db_session, **kwargs)


class BaseRepositoryTestCase(ABC, Generic[T]):
    """Base test case for repository layer testing."""

    @property
    @abstractmethod
    def repository_class(self) -> Type:
        """Repository class to test."""
        pass

    @property
    @abstractmethod
    def model_class(self) -> Type[T]:
        """Model class for the repository."""
        pass

    @property
    @abstractmethod
    def factory_class(self) -> Type[BaseFactory]:
        """Factory class for creating test instances."""
        pass

    def create_repository(self, db_session: Session) -> Any:
        """Create repository instance with database session."""
        return self.repository_class(self.model_class, db_session)

    def create_test_instance(self, db_session: Session, **kwargs: Any) -> T:
        """Create a test instance using the factory."""
        return self.factory_class.create(db_session, **kwargs)


# Test Mixins for specific functionality


class SearchTestMixin:
    """Mixin for testing search functionality."""

    def test_search_endpoint_success(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test search endpoint with valid query."""
        # Create test instance with known name
        instance = self.create_test_instance(db_session, name="SearchTest")
        # Ensure the instance is committed to the database
        db_session.commit()

        response = client.get(
            f"{self.endpoint_prefix}?search=Search",
            headers=self.get_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1

        # Verify the found instance is in results
        found_ids = [item["id"] for item in data["items"]]
        assert instance.id in found_ids


class HierarchyTestMixin:
    """Mixin for testing hierarchical data functionality."""

    def test_tree_endpoint_success(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test tree endpoint for hierarchical data."""
        # This will be implemented based on specific requirements
        # Each hierarchical API will override this method
        pass

    def test_parent_child_relationship(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test parent-child relationships."""
        # This will be implemented based on specific requirements
        pass


class BulkOperationTestMixin:
    """Mixin for testing bulk operations."""

    def test_bulk_create_success(self, client: TestClient, admin_token: str) -> None:
        """Test bulk create operation."""
        payloads = [self.create_valid_payload(name=f"Bulk{i}") for i in range(3)]

        response = client.post(
            f"{self.endpoint_prefix}/bulk",
            json={"items": payloads},
            headers=self.get_auth_headers(admin_token),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success_count"] == 3
        assert len(data["created_items"]) == 3


# Utility functions for assertions


def assert_error_response(
    response_data: Dict[str, Any], expected_code: Optional[str] = None
) -> None:
    """Assert that response contains proper error structure."""
    assert "detail" in response_data
    if expected_code:
        assert response_data.get("code") == expected_code


def assert_pagination_response(
    response_data: Dict[str, Any], expected_total: Optional[int] = None
) -> None:
    """Assert that response contains proper pagination structure."""
    assert "items" in response_data
    assert "total" in response_data
    assert "skip" in response_data
    assert "limit" in response_data
    assert "has_more" in response_data

    if expected_total is not None:
        assert response_data["total"] == expected_total


def assert_audit_fields(response_data: Dict[str, Any]) -> None:
    """Assert that response contains audit fields."""
    assert "created_at" in response_data
    assert "updated_at" in response_data
    assert response_data["created_at"] is not None
    assert response_data["updated_at"] is not None
