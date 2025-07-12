"""Integration tests for Role Management API."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.role import Role, UserRole
from app.models.user import User


class TestRoleManagementAPI:
    """Test Role Management API endpoints."""

    @pytest.fixture
    def test_organization(self, db_session: Session, test_admin: User) -> Organization:
        """Create test organization."""
        org = Organization.create(
            db=db_session,
            code="TEST_ORG",
            name="Test Organization",
            created_by=test_admin.id,
        )
        db_session.commit()
        return org

    @pytest.fixture
    def test_role(self, db_session: Session, test_admin: User) -> Role:
        """Create test role."""
        role = Role.create(
            db=db_session,
            code="TEST_ROLE",
            name="Test Role",
            description="Test role for API testing",
            permissions=["read:test", "write:test"],
            created_by=test_admin.id,
        )
        db_session.commit()
        return role

    def test_list_roles_success(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_role: Role,
    ) -> None:
        """Test successful roles listing."""
        # When: Listing roles
        response = client.get(
            "/api/v1/roles",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"organization_id": test_organization.id},
        )

        # Then: Should return roles
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] > 0
        assert len(data["items"]) > 0

        # Check if our test role is in the list
        role_codes = [item["code"] for item in data["items"]]
        assert "TEST_ROLE" in role_codes

    def test_list_roles_with_search(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_role: Role,
    ) -> None:
        """Test roles listing with search."""
        # When: Listing roles with search
        response = client.get(
            "/api/v1/roles",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"search": "Test", "organization_id": test_organization.id},
        )

        # Then: Should return filtered roles
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0

        # All returned roles should match the search
        for item in data["items"]:
            assert "Test" in item["name"] or "Test" in item["code"]

    def test_list_roles_permission_denied(
        self,
        client: TestClient,
        user_token: str,
        test_organization: Organization,
    ) -> None:
        """Test roles listing with insufficient permissions."""
        # When: Listing roles without permission
        response = client.get(
            "/api/v1/roles",
            headers={"Authorization": f"Bearer {user_token}"},
            params={"organization_id": test_organization.id},
        )

        # Then: Should return permission denied
        assert response.status_code == 403
        data = response.json()
        assert data["code"] == "PERMISSION_DENIED"

    def test_get_role_success(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_role: Role,
    ) -> None:
        """Test successful role retrieval."""
        # When: Getting role by ID
        response = client.get(
            f"/api/v1/roles/{test_role.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"organization_id": test_organization.id},
        )

        # Then: Should return role details
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_role.id
        assert data["code"] == "TEST_ROLE"
        assert data["name"] == "Test Role"
        assert data["description"] == "Test role for API testing"
        assert data["permissions"] == ["read:test", "write:test"]

    def test_get_role_not_found(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
    ) -> None:
        """Test getting non-existent role."""
        # When: Getting non-existent role
        response = client.get(
            "/api/v1/roles/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"organization_id": test_organization.id},
        )

        # Then: Should return not found
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == "NOT_FOUND"

    def test_create_role_success(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
    ) -> None:
        """Test successful role creation."""
        # Given: Role creation data
        role_data = {
            "code": "NEW_ROLE",
            "name": "New Role",
            "description": "A new role for testing",
            "permissions": ["read:new", "write:new"],
        }

        # When: Creating role
        response = client.post(
            "/api/v1/roles",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=role_data,
            params={"organization_id": test_organization.id},
        )

        # Then: Should create role successfully
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "NEW_ROLE"
        assert data["name"] == "New Role"
        assert data["description"] == "A new role for testing"
        assert data["permissions"] == ["read:new", "write:new"]
        assert "id" in data
        assert "created_at" in data

    def test_create_role_duplicate_code(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_role: Role,
    ) -> None:
        """Test creating role with duplicate code."""
        # Given: Role data with existing code
        role_data = {
            "code": "TEST_ROLE",
            "name": "Duplicate Role",
            "permissions": ["read:duplicate"],
        }

        # When: Creating role with duplicate code
        response = client.post(
            "/api/v1/roles",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=role_data,
            params={"organization_id": test_organization.id},
        )

        # Then: Should return conflict
        assert response.status_code == 409
        data = response.json()
        assert data["code"] == "DUPLICATE_CODE"

    def test_create_role_permission_denied(
        self,
        client: TestClient,
        user_token: str,
        test_organization: Organization,
    ) -> None:
        """Test role creation with insufficient permissions."""
        # Given: Role creation data
        role_data = {
            "code": "DENIED_ROLE",
            "name": "Denied Role",
            "permissions": ["read:denied"],
        }

        # When: Creating role without permission
        response = client.post(
            "/api/v1/roles",
            headers={"Authorization": f"Bearer {user_token}"},
            json=role_data,
            params={"organization_id": test_organization.id},
        )

        # Then: Should return permission denied
        assert response.status_code == 403
        data = response.json()
        assert data["code"] == "PERMISSION_DENIED"

    def test_update_role_success(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_role: Role,
    ) -> None:
        """Test successful role update."""
        # Given: Role update data
        update_data = {
            "name": "Updated Role Name",
            "description": "Updated description",
            "permissions": ["read:updated", "write:updated"],
        }

        # When: Updating role
        response = client.put(
            f"/api/v1/roles/{test_role.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=update_data,
            params={"organization_id": test_organization.id},
        )

        # Then: Should update role successfully
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Role Name"
        assert data["description"] == "Updated description"
        assert data["permissions"] == ["read:updated", "write:updated"]

    def test_delete_role_success(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        db_session: Session,
        test_admin: User,
    ) -> None:
        """Test successful role deletion."""
        # Given: Role without assignments
        role = Role.create(
            db=db_session,
            code="DELETE_ROLE",
            name="Delete Role",
            permissions=["read:delete"],
            created_by=test_admin.id,
        )
        db_session.commit()

        # When: Deleting role
        response = client.delete(
            f"/api/v1/roles/{role.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"organization_id": test_organization.id},
        )

        # Then: Should delete role successfully
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Role deleted successfully"

    def test_get_role_permissions_success(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_role: Role,
    ) -> None:
        """Test getting role permissions."""
        # When: Getting role permissions
        response = client.get(
            f"/api/v1/roles/{test_role.id}/permissions",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"organization_id": test_organization.id},
        )

        # Then: Should return permissions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "read:test" in data
        assert "write:test" in data

    def test_update_role_permissions_success(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_role: Role,
    ) -> None:
        """Test updating role permissions."""
        # Given: New permissions
        new_permissions = ["read:updated", "write:updated", "admin:updated"]

        # When: Updating role permissions
        response = client.put(
            f"/api/v1/roles/{test_role.id}/permissions",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=new_permissions,
            params={"organization_id": test_organization.id},
        )

        # Then: Should update permissions successfully
        assert response.status_code == 200
        data = response.json()
        assert data["permissions"] == new_permissions

    def test_assign_role_to_user_success(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_role: Role,
        test_user: User,
    ) -> None:
        """Test successful role assignment."""
        # Given: Role assignment data
        assignment_data = {
            "user_id": test_user.id,
            "role_id": test_role.id,
            "organization_id": test_organization.id,
        }

        # When: Assigning role to user
        response = client.post(
            "/api/v1/roles/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=assignment_data,
        )

        # Then: Should assign role successfully
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == test_user.id
        assert data["role_id"] == test_role.id
        assert data["organization_id"] == test_organization.id

    def test_assign_role_duplicate_assignment(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_role: Role,
        test_user: User,
        db_session: Session,
        test_admin: User,
    ) -> None:
        """Test assigning role with duplicate assignment."""
        # Given: Existing role assignment
        UserRole.create(
            db=db_session,
            user_id=test_user.id,
            role_id=test_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
        )
        db_session.commit()

        assignment_data = {
            "user_id": test_user.id,
            "role_id": test_role.id,
            "organization_id": test_organization.id,
        }

        # When: Assigning duplicate role
        response = client.post(
            "/api/v1/roles/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=assignment_data,
        )

        # Then: Should return conflict
        assert response.status_code == 409
        data = response.json()
        assert data["code"] == "DUPLICATE_ASSIGNMENT"

    def test_get_user_roles_success(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_role: Role,
        test_user: User,
        db_session: Session,
        test_admin: User,
    ) -> None:
        """Test getting user roles."""
        # Given: User with assigned role
        UserRole.create(
            db=db_session,
            user_id=test_user.id,
            role_id=test_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
        )
        db_session.commit()

        # When: Getting user roles
        response = client.get(
            f"/api/v1/roles/assignments/users/{test_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"organization_id": test_organization.id},
        )

        # Then: Should return user roles
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["user_id"] == test_user.id
        assert data[0]["role_id"] == test_role.id

    def test_remove_role_from_user_success(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_role: Role,
        test_user: User,
        db_session: Session,
        test_admin: User,
    ) -> None:
        """Test removing role from user."""
        # Given: User with assigned role
        UserRole.create(
            db=db_session,
            user_id=test_user.id,
            role_id=test_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
        )
        db_session.commit()

        # When: Removing role from user
        response = client.delete(
            f"/api/v1/roles/assignments/users/{test_user.id}/roles/{test_role.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"organization_id": test_organization.id},
        )

        # Then: Should remove role successfully
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Role assignment removed successfully"

    def test_get_users_with_role_success(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_role: Role,
        test_user: User,
        db_session: Session,
        test_admin: User,
    ) -> None:
        """Test getting users with specific role."""
        # Given: User with assigned role
        UserRole.create(
            db=db_session,
            user_id=test_user.id,
            role_id=test_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
        )
        db_session.commit()

        # When: Getting users with role
        response = client.get(
            f"/api/v1/roles/{test_role.id}/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"organization_id": test_organization.id},
        )

        # Then: Should return users with role
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == test_user.id
        assert data[0]["email"] == test_user.email

    def test_check_user_permission_success(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_role: Role,
        test_user: User,
        db_session: Session,
        test_admin: User,
    ) -> None:
        """Test checking user permission."""
        # Given: User with assigned role
        UserRole.create(
            db=db_session,
            user_id=test_user.id,
            role_id=test_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
        )
        db_session.commit()

        # When: Checking user permission
        response = client.post(
            "/api/v1/roles/check-permission",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "user_id": test_user.id,
                "permission": "read:test",
                "organization_id": test_organization.id,
            },
        )

        # Then: Should return permission check result
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == test_user.id
        assert data["permission"] == "read:test"
        assert data["organization_id"] == test_organization.id
        assert "has_permission" in data

    def test_role_assignment_with_expiry(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_role: Role,
        test_user: User,
    ) -> None:
        """Test role assignment with expiry date."""
        # Given: Role assignment data with expiry
        expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()
        assignment_data = {
            "user_id": test_user.id,
            "role_id": test_role.id,
            "organization_id": test_organization.id,
            "expires_at": expires_at,
        }

        # When: Assigning role with expiry
        response = client.post(
            "/api/v1/roles/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=assignment_data,
        )

        # Then: Should assign role with expiry successfully
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == test_user.id
        assert data["role_id"] == test_role.id
        assert data["organization_id"] == test_organization.id
        assert "expires_at" in data

    def test_get_user_roles_include_expired(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_role: Role,
        test_user: User,
        db_session: Session,
        test_admin: User,
    ) -> None:
        """Test getting user roles including expired ones."""
        # Given: User with expired role assignment
        expired_date = datetime.utcnow() - timedelta(days=1)
        UserRole.create(
            db=db_session,
            user_id=test_user.id,
            role_id=test_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
            expires_at=expired_date,
        )
        db_session.commit()

        # When: Getting user roles including expired
        response = client.get(
            f"/api/v1/roles/assignments/users/{test_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "organization_id": test_organization.id,
                "include_expired": True,
            },
        )

        # Then: Should return expired roles
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

        # When: Getting user roles without expired
        response = client.get(
            f"/api/v1/roles/assignments/users/{test_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "organization_id": test_organization.id,
                "include_expired": False,
            },
        )

        # Then: Should not return expired roles
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
