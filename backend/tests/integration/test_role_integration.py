"""Integration tests for Role API with proper authentication."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.organization import Organization
from app.models.user import User
from app.services.integration_service import ERPIntegrationService
from tests.conftest import create_auth_headers


class TestRoleIntegrationWithAuth:
    """Test suite for role integration with authentication."""

    @pytest.fixture
    def auth_user_with_role_permissions(self, db_session: Session) -> User:
        """Create authenticated user with role management permissions."""
        from app.core.security import hash_password

        user = User(
            email="role_admin@test.com",
            hashed_password=hash_password("testpassword"),
            full_name="Role Admin",
            is_active=True,
            is_superuser=True,  # Superuser for testing
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    @pytest.fixture
    def auth_headers_with_role_permissions(
        self, auth_user_with_role_permissions: User
    ) -> dict:
        """Create authentication headers for role management."""
        token = create_access_token(
            data={
                "sub": str(auth_user_with_role_permissions.id),
                "email": auth_user_with_role_permissions.email,
                "is_superuser": True,
            }
        )
        return create_auth_headers(token)

    @pytest.fixture
    def test_organization(self, db_session: Session) -> Organization:
        """Create test organization."""
        org = Organization(
            code="TEST_ORG",
            name="Test Organization",
            is_active=True,
            settings=None,  # Avoid dict serialization issue
        )
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)
        return org

    @pytest.fixture
    def integration_service(self, db_session: Session) -> ERPIntegrationService:
        """Create ERP integration service."""
        return ERPIntegrationService(db_session)

    async def test_create_role_with_proper_auth(
        self,
        client: TestClient,
        auth_headers_with_role_permissions: dict,
        test_organization: Organization,
    ):
        """Test role creation with proper authentication."""
        role_data = {
            "code": "test_role_001",
            "name": "Integration Test Role",
            "description": "Test role for integration testing",
            "organization_id": test_organization.id,
            "permissions": {"task": {"read": True, "write": True}},
            "role_type": "custom",
        }

        response = client.post(
            "/api/v1/roles/",
            json=role_data,
            headers=auth_headers_with_role_permissions,
        )

        assert response.status_code == 201
        role = response.json()
        assert role["name"] == "Integration Test Role"
        assert role["organization_id"] == test_organization.id

    async def test_assign_role_to_user_with_auth(
        self,
        client: TestClient,
        auth_headers_with_role_permissions: dict,
        test_organization: Organization,
        auth_user_with_role_permissions: User,
    ):
        """Test role assignment with authentication."""
        # First create a role
        role_data = {
            "code": "test_role_002",
            "name": "Assignable Test Role",
            "description": "Test role for assignment testing",
            "organization_id": test_organization.id,
            "permissions": {"task": {"read": True}},
            "role_type": "custom",
        }

        role_response = client.post(
            "/api/v1/roles/",
            json=role_data,
            headers=auth_headers_with_role_permissions,
        )
        assert role_response.status_code == 201
        role = role_response.json()

        # Now assign the role
        assignment_data = {
            "user_id": auth_user_with_role_permissions.id,
            "role_id": role["id"],
            "organization_id": test_organization.id,
        }

        response = client.post(
            "/api/v1/roles/assign",
            json=assignment_data,
            headers=auth_headers_with_role_permissions,
        )

        assert response.status_code == 201
        assignment = response.json()
        assert assignment["user_id"] == auth_user_with_role_permissions.id
        assert assignment["role_id"] == role["id"]

    async def test_setup_complete_organization(
        self,
        client: TestClient,
        auth_headers_with_role_permissions: dict,
    ):
        """Test complete organization setup through integration API."""
        setup_data = {
            "organization": {
                "code": "COMPLETE_ORG",
                "name": "Complete Test Organization",
                "description": "Organization created through integration API",
                "is_active": True,
                "settings": None,
            },
            "departments": [
                {
                    "code": "IT",
                    "name": "Information Technology",
                    "description": "IT Department",
                },
                {
                    "code": "HR",
                    "name": "Human Resources",
                    "description": "HR Department",
                },
            ],
            "custom_roles": [],
        }

        response = client.post(
            "/api/v1/integration/setup-organization",
            json=setup_data,
            headers=auth_headers_with_role_permissions,
        )

        assert response.status_code == 200
        result = response.json()

        # Verify organization creation
        assert "organization" in result
        assert result["organization"]["code"] == "COMPLETE_ORG"
        assert result["organization"]["name"] == "Complete Test Organization"

        # Verify default roles creation
        assert "roles" in result
        roles = result["roles"]
        assert len(roles) >= 4  # Should have 4 default roles

        # Check for expected role types
        role_codes = [role["code"] for role in roles]
        org_id = result["organization"]["id"]
        expected_roles = [
            f"org_admin_{org_id}",
            f"dept_manager_{org_id}",
            f"team_lead_{org_id}",
            f"member_{org_id}",
        ]

        for expected_role in expected_roles:
            assert expected_role in role_codes

        # Verify admin assignments
        assert "admin_assignments" in result
        assert len(result["admin_assignments"]) >= 1

        assert result["status"] == "completed"

    async def test_get_organization_structure(
        self,
        client: TestClient,
        auth_headers_with_role_permissions: dict,
        test_organization: Organization,
        auth_user_with_role_permissions: User,
        integration_service: ERPIntegrationService,
    ):
        """Test getting complete organization structure."""
        # First assign user to organization (create a role assignment)
        role_data = {
            "code": f"viewer_{test_organization.id}",
            "name": "Viewer Role",
            "description": "View-only access",
            "organization_id": test_organization.id,
            "permissions": {"organization": {"read": True}},
            "role_type": "custom",
        }

        role_response = client.post(
            "/api/v1/roles/",
            json=role_data,
            headers=auth_headers_with_role_permissions,
        )
        assert role_response.status_code == 201
        role = role_response.json()

        # Assign role to user
        assignment_data = {
            "user_id": auth_user_with_role_permissions.id,
            "role_id": role["id"],
            "organization_id": test_organization.id,
        }

        client.post(
            "/api/v1/roles/assign",
            json=assignment_data,
            headers=auth_headers_with_role_permissions,
        )

        # Now get organization structure
        response = client.get(
            f"/api/v1/integration/organizations/{test_organization.id}/structure",
            headers=auth_headers_with_role_permissions,
        )

        assert response.status_code == 200
        structure = response.json()

        # Verify structure components
        assert "organization" in structure
        assert structure["organization"]["id"] == test_organization.id

        assert "departments" in structure
        assert "roles" in structure
        assert "user_roles" in structure
        assert "tasks_summary" in structure

        # Verify user has role in organization
        user_roles = structure["user_roles"]
        assert len(user_roles) >= 1

    async def test_get_permissions_matrix(
        self,
        client: TestClient,
        auth_headers_with_role_permissions: dict,
        test_organization: Organization,
        auth_user_with_role_permissions: User,
    ):
        """Test getting organization permissions matrix."""
        # Create a role and assign it to user first
        role_data = {
            "code": f"matrix_test_{test_organization.id}",
            "name": "Matrix Test Role",
            "description": "Role for testing permissions matrix",
            "organization_id": test_organization.id,
            "permissions": {"organization": {"read": True, "update": True}},
            "role_type": "custom",
        }

        role_response = client.post(
            "/api/v1/roles/",
            json=role_data,
            headers=auth_headers_with_role_permissions,
        )
        assert role_response.status_code == 201
        role = role_response.json()

        # Assign role to user
        assignment_data = {
            "user_id": auth_user_with_role_permissions.id,
            "role_id": role["id"],
            "organization_id": test_organization.id,
        }

        client.post(
            "/api/v1/roles/assign",
            json=assignment_data,
            headers=auth_headers_with_role_permissions,
        )

        # Get permissions matrix
        response = client.get(
            f"/api/v1/integration/organizations/{test_organization.id}/permissions-matrix",
            headers=auth_headers_with_role_permissions,
        )

        assert response.status_code == 200
        matrix = response.json()

        # Verify matrix structure
        assert "organization_id" in matrix
        assert matrix["organization_id"] == test_organization.id
        assert "permission_matrix" in matrix
        assert "user_role_mapping" in matrix
        assert "summary" in matrix

        # Verify our role appears in the matrix
        permission_matrix = matrix["permission_matrix"]
        assert role["code"] in permission_matrix

        # Verify user appears in role mapping
        user_role_mapping = matrix["user_role_mapping"]
        assert str(auth_user_with_role_permissions.id) in user_role_mapping

    async def test_role_operations_permission_checks(
        self,
        client: TestClient,
        test_organization: Organization,
    ):
        """Test that role operations require proper permissions."""
        # Create a regular user (non-superuser)
        from app.core.security import create_access_token, hash_password

        regular_user = User(
            email="regular@test.com",
            hashed_password=hash_password("testpassword"),
            full_name="Regular User",
            is_active=True,
            is_superuser=False,  # Not a superuser
        )

        # Create token for regular user
        token = create_access_token(
            data={
                "sub": str(regular_user.id),
                "email": regular_user.email,
                "is_superuser": False,
            }
        )
        regular_headers = create_auth_headers(token)

        # Try to create role without sufficient permissions
        role_data = {
            "code": "unauthorized_role",
            "name": "Unauthorized Role",
            "description": "This should fail",
            "organization_id": test_organization.id,
            "permissions": {},
            "role_type": "custom",
        }

        response = client.post(
            "/api/v1/roles/",
            json=role_data,
            headers=regular_headers,
        )

        # Should get 403 Forbidden due to insufficient permissions
        assert response.status_code == 403

    async def test_401_unauthorized_without_token(
        self,
        client: TestClient,
        test_organization: Organization,
    ):
        """Test that endpoints return 401 without authentication token."""
        role_data = {
            "code": "no_auth_role",
            "name": "No Auth Role",
            "description": "This should fail with 401",
            "organization_id": test_organization.id,
            "permissions": {},
            "role_type": "custom",
        }

        # Try to create role without authentication
        response = client.post("/api/v1/roles/", json=role_data)

        # Should get 401 Unauthorized
        assert response.status_code == 401
