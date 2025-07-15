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

    def test_assign_role_to_user(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_role: Role,
        test_user: User,
    ) -> None:
        """Test role assignment to user."""
        # Given: Valid assignment data
        assignment_data = {
            "user_id": test_user.id,
            "role_id": test_role.id,
            "organization_id": test_organization.id,
        }

        # When: Assigning role to user
        response = client.post(
            "/api/v1/roles/assign",
            json=assignment_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: Should succeed
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == test_user.id
        assert data["role_id"] == test_role.id
        assert data["organization_id"] == test_organization.id
        assert data["assigned_by"] is not None

    def test_assign_role_duplicate_assignment(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_role: Role,
        test_user: User,
        db_session: Session,
    ) -> None:
        """Test duplicate role assignment."""
        # Given: Existing assignment
        existing_assignment = UserRole.create(
            db=db_session,
            user_id=test_user.id,
            role_id=test_role.id,
            organization_id=test_organization.id,
            assigned_by=1,  # Admin user ID
        )
        db_session.commit()

        # When: Attempting duplicate assignment
        assignment_data = {
            "user_id": test_user.id,
            "role_id": test_role.id,
            "organization_id": test_organization.id,
        }

        response = client.post(
            "/api/v1/roles/assign",
            json=assignment_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: Should fail with 409 conflict
        assert response.status_code == 409

    def test_get_user_roles(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_role: Role,
        test_user: User,
        db_session: Session,
    ) -> None:
        """Test getting user roles."""
        # Given: User with assigned role
        user_role = UserRole.create(
            db=db_session,
            user_id=test_user.id,
            role_id=test_role.id,
            organization_id=test_organization.id,
            assigned_by=1,  # Admin user ID
        )
        db_session.commit()

        # When: Getting user roles
        response = client.get(
            f"/api/v1/roles/users/{test_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"organization_id": test_organization.id},
        )

        # Then: Should return roles
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["user_id"] == test_user.id
        assert data[0]["role_id"] == test_role.id
        assert data[0]["organization_id"] == test_organization.id

    def test_remove_role_from_user(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_role: Role,
        test_user: User,
        db_session: Session,
    ) -> None:
        """Test removing role from user."""
        # Given: User with assigned role
        user_role = UserRole.create(
            db=db_session,
            user_id=test_user.id,
            role_id=test_role.id,
            organization_id=test_organization.id,
            assigned_by=1,  # Admin user ID
        )
        db_session.commit()

        # When: Removing role from user
        response = client.delete(
            f"/api/v1/roles/users/{test_user.id}/roles/{test_role.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"organization_id": test_organization.id},
        )

        # Then: Should succeed
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

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
            json=role_data,
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"organization_id": test_organization.id},
        )

        # Then: Should succeed
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "NEW_ROLE"
        assert data["name"] == "New Role"
        assert data["description"] == "A new role for testing"
        assert data["permissions"] == ["read:new", "write:new"]

    def test_create_role_duplicate_code(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_role: Role,
    ) -> None:
        """Test role creation with duplicate code."""
        # Given: Role creation data with existing code
        role_data = {
            "code": "TEST_ROLE",  # Same as existing test_role
            "name": "Duplicate Role",
            "description": "Role with duplicate code",
            "permissions": ["read:duplicate"],
        }

        # When: Creating role with duplicate code
        response = client.post(
            "/api/v1/roles",
            json=role_data,
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"organization_id": test_organization.id},
        )

        # Then: Should fail with 422 validation error
        assert response.status_code == 422

    def test_get_role_by_id(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
        test_role: Role,
    ) -> None:
        """Test getting role by ID."""
        # When: Getting role by ID
        response = client.get(
            f"/api/v1/roles/{test_role.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"organization_id": test_organization.id},
        )

        # Then: Should return role
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_role.id
        assert data["code"] == "TEST_ROLE"
        assert data["name"] == "Test Role"

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

        # Then: Should return 404
        assert response.status_code == 404

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
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"organization_id": test_organization.id},
        )

        # Then: Should succeed
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
        test_role: Role,
    ) -> None:
        """Test successful role deletion."""
        # When: Deleting role
        response = client.delete(
            f"/api/v1/roles/{test_role.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"organization_id": test_organization.id},
        )

        # Then: Should succeed
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_role_not_found(
        self,
        client: TestClient,
        admin_token: str,
        test_organization: Organization,
    ) -> None:
        """Test deleting non-existent role."""
        # When: Deleting non-existent role
        response = client.delete(
            "/api/v1/roles/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"organization_id": test_organization.id},
        )

        # Then: Should return 404
        assert response.status_code == 404