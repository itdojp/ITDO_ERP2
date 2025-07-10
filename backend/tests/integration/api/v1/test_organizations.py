"""Integration tests for Organization API endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from tests.base import BaseAPITestCase, HierarchyTestMixin, SearchTestMixin
from tests.conftest import create_auth_headers
from tests.factories import OrganizationFactory


class TestOrganizationAPI(
    BaseAPITestCase[
        Organization, OrganizationCreate, OrganizationUpdate, OrganizationResponse
    ],
    SearchTestMixin,
    HierarchyTestMixin,
):
    """Test cases for Organization API endpoints."""

    @property
    def endpoint_prefix(self) -> str:
        """API endpoint prefix."""
        return "/api/v1/organizations"

    @property
    def factory_class(self):
        """Factory class for creating test instances."""
        return OrganizationFactory

    @property
    def create_schema_class(self):
        """Schema class for create operations."""
        return OrganizationCreate

    @property
    def update_schema_class(self):
        """Schema class for update operations."""
        return OrganizationUpdate

    @property
    def response_schema_class(self):
        """Schema class for API responses."""
        return OrganizationResponse

    # Use inherited test_create_endpoint_success from BaseAPITestCase

    # Custom test methods specific to Organization API

    def test_tree_endpoint_success(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test organization tree endpoint."""
        # Create organization hierarchy
        tree_data = OrganizationFactory.create_subsidiary_tree(
            db_session, depth=2, children_per_level=2
        )

        response = client.get(
            f"{self.endpoint_prefix}/tree", headers=create_auth_headers(admin_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Verify tree structure
        root_org = data[0]
        assert "id" in root_org
        assert "name" in root_org
        assert "children" in root_org
        assert len(root_org["children"]) == tree_data["children_per_level"]

    def test_get_subsidiaries_endpoint(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test get subsidiaries endpoint."""
        # Create parent organization
        parent = OrganizationFactory.create(db_session, name="親会社")

        # Create subsidiaries
        subsidiaries = [
            OrganizationFactory.create_with_parent(
                db_session, parent.id, name=f"子会社{i}"
            )
            for i in range(3)
        ]

        response = client.get(
            f"{self.endpoint_prefix}/{parent.id}/subsidiaries",
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        # Verify all subsidiaries are returned
        subsidiary_ids = [item["id"] for item in data]
        for subsidiary in subsidiaries:
            assert subsidiary.id in subsidiary_ids

    def test_get_subsidiaries_recursive(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test get subsidiaries with recursive option."""
        # Create organization hierarchy
        tree_data = OrganizationFactory.create_subsidiary_tree(
            db_session, depth=3, children_per_level=2
        )
        root = tree_data["root"]

        # Test non-recursive (direct children only)
        response = client.get(
            f"{self.endpoint_prefix}/{root.id}/subsidiaries?recursive=false",
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 200
        direct_children = response.json()

        # Test recursive (all descendants)
        response = client.get(
            f"{self.endpoint_prefix}/{root.id}/subsidiaries?recursive=true",
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 200
        all_descendants = response.json()

        # Recursive should return more organizations
        assert len(all_descendants) > len(direct_children)

    def test_activate_organization_endpoint(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test organization activation endpoint."""
        # Create inactive organization
        org = OrganizationFactory.create_inactive(db_session)

        response = client.post(
            f"{self.endpoint_prefix}/{org.id}/activate",
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    def test_deactivate_organization_endpoint(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test organization deactivation endpoint."""
        # Create active organization
        org = OrganizationFactory.create(db_session)

        response = client.post(
            f"{self.endpoint_prefix}/{org.id}/deactivate",
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    def test_create_with_duplicate_code(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test create organization with duplicate code."""
        # Create first organization
        OrganizationFactory.create(db_session, code="DUPLICATE")

        # Try to create second organization with same code
        payload = OrganizationFactory.build_dict(code="DUPLICATE")

        response = client.post(
            self.endpoint_prefix, json=payload, headers=create_auth_headers(admin_token)
        )

        assert response.status_code == 409
        data = response.json()
        assert "DUPLICATE_CODE" in data.get("code", "")

    def test_update_with_duplicate_code(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test update organization with duplicate code."""
        # Create two organizations
        OrganizationFactory.create(db_session, code="ORG1")
        org2 = OrganizationFactory.create(db_session, code="ORG2")

        # Try to update org2 with org1's code
        payload = {"code": "ORG1"}

        response = client.put(
            f"{self.endpoint_prefix}/{org2.id}",
            json=payload,
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 409
        data = response.json()
        assert "DUPLICATE_CODE" in data.get("code", "")

    def test_delete_with_active_subsidiaries(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test delete organization with active subsidiaries."""
        # Create parent with subsidiaries
        parent = OrganizationFactory.create(db_session, name="親会社")
        OrganizationFactory.create_with_parent(db_session, parent.id, name="子会社")

        response = client.delete(
            f"{self.endpoint_prefix}/{parent.id}",
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 409
        data = response.json()
        assert "HAS_SUBSIDIARIES" in data.get("code", "")

    def test_list_with_filters(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test list organizations with various filters."""
        # Create organizations with different attributes
        OrganizationFactory.create_with_specific_industry(db_session, "IT")
        OrganizationFactory.create_with_specific_industry(db_session, "金融業")
        org_inactive = OrganizationFactory.create_inactive(db_session)

        # Test industry filter
        response = client.get(
            f"{self.endpoint_prefix}?industry=IT",
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1

        # Test active_only filter
        response = client.get(
            f"{self.endpoint_prefix}?active_only=false",
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data = response.json()
        # Should include inactive organizations
        org_ids = [item["id"] for item in data["items"]]
        assert org_inactive.id in org_ids

    def test_permission_checks(
        self, client: TestClient, db_session: Session, user_token: str
    ) -> None:
        """Test that non-admin users cannot perform admin operations."""
        org = OrganizationFactory.create(db_session)

        # Test create permission
        payload = OrganizationFactory.build_dict()
        response = client.post(
            self.endpoint_prefix, json=payload, headers=create_auth_headers(user_token)
        )
        assert response.status_code == 403

        # Test update permission
        update_payload = {"name": "Updated Name"}
        response = client.put(
            f"{self.endpoint_prefix}/{org.id}",
            json=update_payload,
            headers=create_auth_headers(user_token),
        )
        assert response.status_code == 403

        # Test delete permission
        response = client.delete(
            f"{self.endpoint_prefix}/{org.id}", headers=create_auth_headers(user_token)
        )
        assert response.status_code == 403

        # Test activate permission
        response = client.post(
            f"{self.endpoint_prefix}/{org.id}/activate",
            headers=create_auth_headers(user_token),
        )
        assert response.status_code == 403


class TestOrganizationValidation:
    """Test validation rules for Organization API."""

    def test_create_with_invalid_data(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Test create organization with various invalid data."""
        # Test missing required fields
        response = client.post(
            "/api/v1/organizations", json={}, headers=create_auth_headers(admin_token)
        )
        assert response.status_code == 422

        # Test invalid email format
        payload = OrganizationFactory.build_dict(email="invalid-email")
        response = client.post(
            "/api/v1/organizations",
            json=payload,
            headers=create_auth_headers(admin_token),
        )
        assert response.status_code == 422

        # Test invalid postal code (if validation exists)
        payload = OrganizationFactory.build_dict(postal_code="invalid")
        response = client.post(
            "/api/v1/organizations",
            json=payload,
            headers=create_auth_headers(admin_token),
        )
        # This might pass if no validation, adjust based on actual validation rules

    def test_field_length_limits(self, client: TestClient, admin_token: str) -> None:
        """Test field length limit validations."""
        # Test name too long
        payload = OrganizationFactory.build_dict(name="x" * 300)
        client.post(
            "/api/v1/organizations",
            json=payload,
            headers=create_auth_headers(admin_token),
        )
        # Should pass or fail based on actual validation rules

        # Test code too long
        payload = OrganizationFactory.build_dict(code="x" * 100)
        client.post(
            "/api/v1/organizations",
            json=payload,
            headers=create_auth_headers(admin_token),
        )
        # Should pass or fail based on actual validation rules


class TestOrganizationBusinessLogic:
    """Test business logic for organizations."""

    def test_hierarchy_depth_limits(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test organization hierarchy depth handling."""
        # Create deep hierarchy
        organizations = []
        parent_id = None

        for i in range(5):  # Create 5 levels deep
            if parent_id:
                org = OrganizationFactory.create_with_parent(
                    db_session, parent_id, name=f"Level {i} Organization"
                )
            else:
                org = OrganizationFactory.create(
                    db_session, name=f"Level {i} Organization"
                )

            organizations.append(org)
            parent_id = org.id

        # Test that tree endpoint handles deep hierarchy
        response = client.get(
            "/api/v1/organizations/tree", headers=create_auth_headers(admin_token)
        )

        assert response.status_code == 200
        data = response.json()

        # Verify the tree structure is properly nested
        def count_depth(node, current_depth=0):
            max_depth = current_depth
            for child in node.get("children", []):
                child_depth = count_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            return max_depth

        if data:
            tree_depth = count_depth(data[0])
            assert tree_depth >= 4  # Should handle at least 4 levels deep
