"""Integration tests for Role API endpoints."""

from typing import Any, Dict

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.permission import Permission
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleResponse, RoleUpdate
from tests.base import BaseAPITestCase, HierarchyTestMixin, SearchTestMixin
from tests.conftest import create_auth_headers
from tests.factories import OrganizationFactory, RoleFactory, UserFactory


class TestRoleAPI(
    BaseAPITestCase[Role, RoleCreate, RoleUpdate, RoleResponse],
    SearchTestMixin,
    HierarchyTestMixin,
):
    """Test cases for Role API endpoints."""

    @property
    def endpoint_prefix(self) -> str:
        """API endpoint prefix."""
        return "/api/v1/roles"

    @property
    def factory_class(self):
        """Factory class for creating test instances."""
        return RoleFactory

    @property
    def create_schema_class(self):
        """Schema class for create operations."""
        return RoleCreate

    @property
    def update_schema_class(self):
        """Schema class for update operations."""
        return RoleUpdate

    @property
    def response_schema_class(self):
        """Schema class for API responses."""
        return RoleResponse

    def create_test_instance(self, db_session: Session, **kwargs: Any) -> Role:
        """Create a test role instance with organization."""
        if "organization_id" not in kwargs:
            organization = OrganizationFactory.create(db_session)
            kwargs["organization_id"] = organization.id
        return self.factory_class.create(db_session, **kwargs)

    def create_valid_payload(self, **overrides: Any) -> Dict[str, Any]:
        """Create a valid payload for role creation."""
        # Ensure we have an organization_id
        if "organization_id" not in overrides:
            raise ValueError("organization_id must be provided for role creation")
        return self.factory_class.build_dict(**overrides)

    # Role-specific test methods

    def test_role_tree_endpoint(
        self,
        client: TestClient,
        test_organization: Organization,
        db_session: Session,
        admin_token: str,
    ) -> None:
        """Test role tree endpoint for an organization."""
        # Create role hierarchy
        RoleFactory.create_role_hierarchy(db_session, test_organization)

        response = client.get(
            f"{self.endpoint_prefix}/organization/{test_organization.id}/tree",
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Verify tree structure
        admin_role = None
        for role in data:
            if role["name"] == "システム管理者":
                admin_role = role
                break

        assert admin_role is not None
        assert "children" in admin_role
        assert len(admin_role["children"]) >= 1

    def test_role_tree_nonexistent_organization(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Test role tree endpoint with non-existent organization."""
        response = client.get(
            f"{self.endpoint_prefix}/organization/99999/tree",
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 404

    def test_list_all_permissions(
        self,
        client: TestClient,
        test_permissions: Dict[str, list[Permission]],
        admin_token: str,
    ) -> None:
        """Test list all permissions endpoint."""
        response = client.get(
            f"{self.endpoint_prefix}/permissions",
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Verify permission structure
        permission = data[0]
        assert "id" in permission
        assert "code" in permission
        assert "name" in permission
        assert "category" in permission

    def test_list_permissions_by_category(
        self,
        client: TestClient,
        test_permissions: Dict[str, list[Permission]],
        admin_token: str,
    ) -> None:
        """Test list permissions filtered by category."""
        response = client.get(
            f"{self.endpoint_prefix}/permissions?category=users",
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data = response.json()

        # All permissions should be in 'users' category
        categories = [perm["category"] for perm in data]
        assert all(cat == "users" for cat in categories)

    def test_get_role_permissions(
        self, client: TestClient, test_role_system: Dict[str, Any], admin_token: str
    ) -> None:
        """Test get role with permissions endpoint."""
        admin_role = test_role_system["roles"]["admin"]

        response = client.get(
            f"{self.endpoint_prefix}/{admin_role.id}/permissions",
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert "direct_permissions" in data
        assert "inherited_permissions" in data
        assert "all_permission_codes" in data

        # Admin should have many permissions
        assert len(data["all_permission_codes"]) > 0

    def test_get_role_permissions_include_inherited(
        self, client: TestClient, test_role_system: Dict[str, Any], admin_token: str
    ) -> None:
        """Test get role permissions with inherited permissions."""
        user_role = test_role_system["roles"]["user"]

        # Test with inherited permissions
        response = client.get(
            f"{self.endpoint_prefix}/{user_role.id}/permissions?include_inherited=true",
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data_with_inherited = response.json()

        # Test without inherited permissions
        response = client.get(
            f"{self.endpoint_prefix}/{user_role.id}/permissions?include_inherited=false",
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data_without_inherited = response.json()

        # With inherited should have more or equal permissions
        assert len(data_with_inherited["all_permission_codes"]) >= len(
            data_without_inherited["all_permission_codes"]
        )

    def test_update_role_permissions(
        self,
        client: TestClient,
        test_organization: Organization,
        test_permissions: Dict[str, list[Permission]],
        db_session: Session,
        admin_token: str,
    ) -> None:
        """Test update role permissions endpoint."""
        # Create a role
        role = RoleFactory.create_with_organization(db_session, test_organization)

        # Select some permissions
        permission_codes = [perm.code for perm in test_permissions["users"][:3]]

        response = client.put(
            f"{self.endpoint_prefix}/{role.id}/permissions",
            json=permission_codes,
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == role.id

        # Verify permissions were assigned
        permissions_response = client.get(
            f"{self.endpoint_prefix}/{role.id}/permissions",
            headers=create_auth_headers(admin_token),
        )

        permissions_data = permissions_response.json()
        assigned_codes = permissions_data["all_permission_codes"]

        for code in permission_codes:
            assert code in assigned_codes

    def test_update_role_permissions_invalid_codes(
        self,
        client: TestClient,
        test_organization: Organization,
        db_session: Session,
        admin_token: str,
    ) -> None:
        """Test update role permissions with invalid permission codes."""
        # Create a role
        role = RoleFactory.create_with_organization(db_session, test_organization)

        # Use invalid permission codes
        invalid_codes = ["invalid.permission", "another.invalid"]

        response = client.put(
            f"{self.endpoint_prefix}/{role.id}/permissions",
            json=invalid_codes,
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 400
        data = response.json()
        assert "INVALID_PERMISSION" in data.get("code", "")

    def test_assign_role_to_user(
        self,
        client: TestClient,
        test_organization: Organization,
        db_session: Session,
        admin_token: str,
    ) -> None:
        """Test assign role to user endpoint."""
        # Create role and user
        role = RoleFactory.create_with_organization(db_session, test_organization)
        user = UserFactory.create(db_session)

        assignment_data = {"user_id": user.id, "role_id": role.id}

        response = client.post(
            f"{self.endpoint_prefix}/assign",
            json=assignment_data,
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == user.id
        assert data["role_id"] == role.id
        assert data["is_active"] is True

    def test_assign_role_duplicate_assignment(
        self,
        client: TestClient,
        test_organization: Organization,
        db_session: Session,
        admin_token: str,
    ) -> None:
        """Test assign role to user when assignment already exists."""
        # Create role and user
        role = RoleFactory.create_with_organization(db_session, test_organization)
        user = UserFactory.create(db_session)

        assignment_data = {"user_id": user.id, "role_id": role.id}

        # First assignment should succeed
        response = client.post(
            f"{self.endpoint_prefix}/assign",
            json=assignment_data,
            headers=create_auth_headers(admin_token),
        )
        assert response.status_code == 201

        # Second assignment should fail
        response = client.post(
            f"{self.endpoint_prefix}/assign",
            json=assignment_data,
            headers=create_auth_headers(admin_token),
        )
        assert response.status_code == 409
        data = response.json()
        assert "ASSIGNMENT_EXISTS" in data.get("code", "")

    def test_remove_role_from_user(
        self,
        client: TestClient,
        test_organization: Organization,
        db_session: Session,
        admin_token: str,
    ) -> None:
        """Test remove role from user endpoint."""
        # Create role and user
        role = RoleFactory.create_with_organization(db_session, test_organization)
        user = UserFactory.create(db_session)

        # First assign the role
        assignment_data = {"user_id": user.id, "role_id": role.id}

        assign_response = client.post(
            f"{self.endpoint_prefix}/assign",
            json=assignment_data,
            headers=create_auth_headers(admin_token),
        )
        assert assign_response.status_code == 201

        # Then remove the role
        response = client.delete(
            f"{self.endpoint_prefix}/assign/{user.id}/{role.id}",
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_remove_nonexistent_assignment(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Test remove role assignment that doesn't exist."""
        response = client.delete(
            f"{self.endpoint_prefix}/assign/99999/99999",
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 404
        data = response.json()
        assert "ROLE_NOT_FOUND" in data.get("code", "")

    def test_get_user_roles(
        self,
        client: TestClient,
        test_organization: Organization,
        db_session: Session,
        admin_token: str,
    ) -> None:
        """Test get user roles endpoint."""
        # Create roles and user
        role1 = RoleFactory.create_with_organization(
            db_session, test_organization, name="Role 1"
        )
        role2 = RoleFactory.create_with_organization(
            db_session, test_organization, name="Role 2"
        )
        user = UserFactory.create(db_session)

        # Assign both roles to user
        for role in [role1, role2]:
            assignment_data = {"user_id": user.id, "role_id": role.id}
            client.post(
                f"{self.endpoint_prefix}/assign",
                json=assignment_data,
                headers=create_auth_headers(admin_token),
            )

        # Get user roles
        response = client.get(
            f"{self.endpoint_prefix}/user/{user.id}",
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Verify both roles are returned
        role_ids = [assignment["role_id"] for assignment in data]
        assert role1.id in role_ids
        assert role2.id in role_ids

    def test_get_user_roles_with_organization_filter(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test get user roles filtered by organization."""
        # Create two organizations with roles
        org1 = OrganizationFactory.create(db_session)
        org2 = OrganizationFactory.create(db_session)

        role1 = RoleFactory.create_with_organization(db_session, org1)
        role2 = RoleFactory.create_with_organization(db_session, org2)

        user = UserFactory.create(db_session)

        # Assign both roles to user
        for role in [role1, role2]:
            assignment_data = {"user_id": user.id, "role_id": role.id}
            client.post(
                f"{self.endpoint_prefix}/assign",
                json=assignment_data,
                headers=create_auth_headers(admin_token),
            )

        # Get user roles filtered by org1
        response = client.get(
            f"{self.endpoint_prefix}/user/{user.id}?organization_id={org1.id}",
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["role_id"] == role1.id

    def test_create_role_with_parent(
        self,
        client: TestClient,
        test_organization: Organization,
        db_session: Session,
        admin_token: str,
    ) -> None:
        """Test create role with parent role."""
        # Create parent role
        parent = RoleFactory.create_with_organization(db_session, test_organization)

        # Create child role
        payload = RoleFactory.build_dict(
            organization_id=test_organization.id, parent_id=parent.id, name="Child Role"
        )

        response = client.post(
            self.endpoint_prefix, json=payload, headers=create_auth_headers(admin_token)
        )

        assert response.status_code == 201
        data = response.json()
        assert data["parent_id"] == parent.id
        assert data["organization_id"] == test_organization.id

    def test_create_role_invalid_parent(
        self,
        client: TestClient,
        test_organization: Organization,
        db_session: Session,
        admin_token: str,
    ) -> None:
        """Test create role with invalid parent."""
        # Create role in different organization
        other_org = OrganizationFactory.create(db_session)
        other_role = RoleFactory.create_with_organization(db_session, other_org)

        # Try to create role with parent from different organization
        payload = RoleFactory.build_dict(
            organization_id=test_organization.id,
            parent_id=other_role.id,
            name="Invalid Child",
        )

        response = client.post(
            self.endpoint_prefix, json=payload, headers=create_auth_headers(admin_token)
        )

        assert response.status_code == 400
        data = response.json()
        assert "INVALID_PARENT" in data.get("code", "")

    def test_update_role_parent_validation(
        self,
        client: TestClient,
        test_organization: Organization,
        db_session: Session,
        admin_token: str,
    ) -> None:
        """Test update role with parent validation."""
        # Create role
        role = RoleFactory.create_with_organization(db_session, test_organization)

        # Try to make role its own parent
        payload = {"parent_id": role.id}

        response = client.put(
            f"{self.endpoint_prefix}/{role.id}",
            json=payload,
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 400
        data = response.json()
        assert "INVALID_PARENT" in data.get("code", "")

    def test_delete_role_in_use(
        self,
        client: TestClient,
        test_organization: Organization,
        db_session: Session,
        admin_token: str,
    ) -> None:
        """Test delete role that is assigned to users."""
        # Create role and user
        role = RoleFactory.create_with_organization(db_session, test_organization)
        user = UserFactory.create(db_session)

        # Assign role to user
        assignment_data = {"user_id": user.id, "role_id": role.id}
        client.post(
            f"{self.endpoint_prefix}/assign",
            json=assignment_data,
            headers=create_auth_headers(admin_token),
        )

        # Try to delete role
        response = client.delete(
            f"{self.endpoint_prefix}/{role.id}",
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 409
        data = response.json()
        assert "ROLE_IN_USE" in data.get("code", "")

    def test_create_with_duplicate_name_in_organization(
        self,
        client: TestClient,
        test_organization: Organization,
        db_session: Session,
        admin_token: str,
    ) -> None:
        """Test create role with duplicate name within organization."""
        # Create first role
        RoleFactory.create_with_organization(
            db_session, test_organization, name="DUPLICATE"
        )

        # Try to create second role with same name in same organization
        payload = RoleFactory.build_dict(
            organization_id=test_organization.id, name="DUPLICATE"
        )

        response = client.post(
            self.endpoint_prefix, json=payload, headers=create_auth_headers(admin_token)
        )

        assert response.status_code == 409
        data = response.json()
        assert "DUPLICATE_NAME" in data.get("code", "")

    def test_list_with_role_type_filter(
        self,
        client: TestClient,
        test_organization: Organization,
        db_session: Session,
        admin_token: str,
    ) -> None:
        """Test list roles with role type filter."""
        # Create roles of different types
        RoleFactory.create_by_type(
            db_session, "system", organization_id=test_organization.id
        )
        RoleFactory.create_by_type(
            db_session, "custom", organization_id=test_organization.id
        )

        # Filter by system type
        response = client.get(
            f"{self.endpoint_prefix}?role_type=system",
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data = response.json()

        # Should only contain system roles
        role_types = [item["role_type"] for item in data["items"]]
        assert all(role_type == "system" for role_type in role_types)


class TestRolePermissions:
    """Test permission checks for Role API."""

    def test_role_operations_permission_checks(
        self,
        client: TestClient,
        test_organization: Organization,
        db_session: Session,
        user_token: str,
    ) -> None:
        """Test that regular users cannot perform role operations without
        permissions."""
        role = RoleFactory.create_with_organization(db_session, test_organization)
        user = UserFactory.create(db_session)

        # Test create permission
        payload = RoleFactory.build_dict(organization_id=test_organization.id)
        response = client.post(
            "/api/v1/roles", json=payload, headers=create_auth_headers(user_token)
        )
        assert response.status_code == 403

        # Test update permission
        update_payload = {"name": "Updated Name"}
        response = client.put(
            f"/api/v1/roles/{role.id}",
            json=update_payload,
            headers=create_auth_headers(user_token),
        )
        assert response.status_code == 403

        # Test delete permission
        response = client.delete(
            f"/api/v1/roles/{role.id}", headers=create_auth_headers(user_token)
        )
        assert response.status_code == 403

        # Test assign permission
        assignment_data = {"user_id": user.id, "role_id": role.id}
        response = client.post(
            "/api/v1/roles/assign",
            json=assignment_data,
            headers=create_auth_headers(user_token),
        )
        assert response.status_code == 403
