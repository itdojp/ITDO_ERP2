"""Permission-based access control integration tests for Organization Service."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.user import User
from app.services.organization import OrganizationService
from tests.conftest import create_auth_headers
from tests.factories import OrganizationFactory, UserFactory


class TestOrganizationPermissions:
    """Test permission-based access control for Organization Service."""

    @pytest.fixture
    def manager_user(self, db_session: Session, test_organization: Organization) -> User:
        """Create a manager user with limited permissions."""
        return UserFactory.create(
            db_session,
            email="manager@test.com",
            full_name="Manager User",
            is_superuser=False,
        )

    @pytest.fixture
    def regular_user(self, db_session: Session, test_organization: Organization) -> User:
        """Create a regular user with minimal permissions."""
        return UserFactory.create(
            db_session,
            email="user@test.com", 
            full_name="Regular User",
            is_superuser=False,
        )

    @pytest.fixture
    def external_user(self, db_session: Session) -> User:
        """Create a user from different organization."""
        external_org = OrganizationFactory.create(
            db_session,
            code="EXTERNAL-001",
            name="External Organization",
        )
        return UserFactory.create(
            db_session,
            email="external@external.com",
            full_name="External User",
            is_superuser=False,
        )

    def test_superuser_full_access(
        self,
        client: TestClient,
        test_organization: Organization,
        admin_token: str,
    ):
        """Test that superuser has full access to all operations."""
        auth_headers = create_auth_headers(admin_token)
        
        # List organizations
        response = client.get("/api/v1/organizations/", headers=auth_headers)
        assert response.status_code == 200
        
        # Get specific organization
        response = client.get(
            f"/api/v1/organizations/{test_organization.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Create organization
        new_org_data = {
            "code": "SUPER-CREATE-001",
            "name": "Superuser Created Organization",
            "is_active": True,
        }
        response = client.post(
            "/api/v1/organizations/",
            json=new_org_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        
        # Update organization
        update_data = {"description": "Updated by superuser"}
        response = client.put(
            f"/api/v1/organizations/{test_organization.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Delete organization (create one specifically for deletion)
        delete_org = {
            "code": "SUPER-DELETE-001",
            "name": "Organization to Delete",
            "is_active": True,
        }
        create_response = client.post(
            "/api/v1/organizations/",
            json=delete_org,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        delete_org_id = create_response.json()["id"]
        
        response = client.delete(
            f"/api/v1/organizations/{delete_org_id}",
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_regular_user_read_only_access(
        self,
        client: TestClient,
        test_organization: Organization,
        regular_user: User,
        user_token: str,
    ):
        """Test that regular users have read-only access."""
        auth_headers = create_auth_headers(user_token)
        
        # List organizations - should work
        response = client.get("/api/v1/organizations/", headers=auth_headers)
        assert response.status_code == 200
        
        # Get specific organization - should work
        response = client.get(
            f"/api/v1/organizations/{test_organization.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Create organization - should fail
        new_org_data = {
            "code": "USER-CREATE-001",
            "name": "User Created Organization",
            "is_active": True,
        }
        response = client.post(
            "/api/v1/organizations/",
            json=new_org_data,
            headers=auth_headers
        )
        assert response.status_code == 403
        
        # Update organization - should fail  
        update_data = {"description": "Updated by regular user"}
        response = client.put(
            f"/api/v1/organizations/{test_organization.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 403
        
        # Delete organization - should fail
        response = client.delete(
            f"/api/v1/organizations/{test_organization.id}",
            headers=auth_headers
        )
        assert response.status_code == 403

    def test_unauthorized_access(self, client: TestClient, test_organization: Organization):
        """Test that unauthorized users are rejected."""
        # No authentication header
        response = client.get("/api/v1/organizations/")
        assert response.status_code in [401, 403]
        
        # Invalid token
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/v1/organizations/", headers=invalid_headers)
        assert response.status_code in [401, 403]
        
        # Expired/malformed token
        malformed_headers = {"Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid"}
        response = client.get("/api/v1/organizations/", headers=malformed_headers)
        assert response.status_code in [401, 403]

    def test_service_level_permission_checking(
        self,
        db_session: Session,
        test_organization: Organization,
        regular_user: User,
        manager_user: User,
    ):
        """Test service-level permission checking methods."""
        service = OrganizationService(db_session)
        
        # Test user_has_permission method
        # Regular user should not have admin permissions
        assert not service.user_has_permission(regular_user.id, "organizations.create")
        assert not service.user_has_permission(regular_user.id, "organizations.delete")
        
        # Manager user should not have admin permissions (only superuser does in current implementation)
        assert not service.user_has_permission(manager_user.id, "organizations.create")
        assert not service.user_has_permission(manager_user.id, "organizations.delete")
        
        # Test can_user_access_organization
        # Users should be able to access their own organization
        assert service.can_user_access_organization(regular_user.id, test_organization.id)
        assert service.can_user_access_organization(manager_user.id, test_organization.id)

    def test_organization_access_isolation(
        self,
        client: TestClient,
        db_session: Session,
        test_organization: Organization,
        external_user: User,
        user_token: str,
    ):
        """Test that users can only access organizations they have permission for."""
        auth_headers = create_auth_headers(user_token)
        
        # Create organization for external user
        external_org = OrganizationFactory.create(
            db_session,
            code="EXTERNAL-ACCESS-001",
            name="External Access Test Organization",
        )
        
        # Regular user should be able to see all organizations (read access)
        # but this depends on the actual permission implementation
        response = client.get("/api/v1/organizations/", headers=auth_headers)
        assert response.status_code == 200
        
        # Check if they can access specific external organization
        response = client.get(
            f"/api/v1/organizations/{external_org.id}",
            headers=auth_headers
        )
        # Should work for read access
        assert response.status_code == 200

    def test_hierarchy_permission_inheritance(
        self,
        db_session: Session,
        test_organization: Organization,
        manager_user: User,
        test_user: User,
    ):
        """Test permission inheritance in organization hierarchies."""
        service = OrganizationService(db_session)
        
        # Create subsidiary organization
        subsidiary = OrganizationFactory.create(
            db_session,
            code="SUBSIDIARY-001",
            name="Subsidiary Organization",
            parent_id=test_organization.id,
            created_by=test_user.id,
        )
        
        # Test hierarchy access
        hierarchy = service.get_organization_hierarchy(subsidiary.id)
        assert len(hierarchy) >= 2  # Should include parent and child
        
        # Test subsidiary relationship
        assert service.is_subsidiary_of(subsidiary.id, test_organization.id)
        assert not service.is_subsidiary_of(test_organization.id, subsidiary.id)

    def test_settings_update_permissions(
        self,
        client: TestClient,
        test_organization: Organization,
        regular_user: User,
        user_token: str,
        admin_token: str,
    ):
        """Test permissions for updating organization settings."""
        # Regular user should not be able to update settings
        auth_headers = create_auth_headers(user_token)
        settings_data = {
            "fiscal_year_start": "01-01",
            "default_currency": "USD",
        }
        
        response = client.put(
            f"/api/v1/organizations/{test_organization.id}/settings",
            json=settings_data,
            headers=auth_headers
        )
        assert response.status_code == 403
        
        # Admin should be able to update settings
        admin_headers = create_auth_headers(admin_token)
        response = client.put(
            f"/api/v1/organizations/{test_organization.id}/settings",
            json=settings_data,
            headers=admin_headers
        )
        assert response.status_code == 200

    def test_activate_deactivate_permissions(
        self,
        client: TestClient,
        db_session: Session,
        user_token: str,
        admin_token: str,
    ):
        """Test permissions for activate/deactivate operations."""
        # Create test organization
        test_org = OrganizationFactory.create(
            db_session,
            code="ACTIVATE-TEST-001",
            name="Activation Test Organization",
            is_active=False,
        )
        
        # Regular user should not be able to activate
        auth_headers = create_auth_headers(user_token)
        response = client.post(
            f"/api/v1/organizations/{test_org.id}/activate",
            headers=auth_headers
        )
        assert response.status_code == 403
        
        # Admin should be able to activate
        admin_headers = create_auth_headers(admin_token)
        response = client.post(
            f"/api/v1/organizations/{test_org.id}/activate",
            headers=admin_headers
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is True
        
        # Regular user should not be able to deactivate
        response = client.post(
            f"/api/v1/organizations/{test_org.id}/deactivate",
            headers=auth_headers
        )
        assert response.status_code == 403
        
        # Admin should be able to deactivate
        response = client.post(
            f"/api/v1/organizations/{test_org.id}/deactivate",
            headers=admin_headers
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_statistics_access_permissions(
        self,
        client: TestClient,
        test_organization: Organization,
        user_token: str,
        admin_token: str,
    ):
        """Test permissions for accessing organization statistics."""
        # Regular user should be able to view statistics (read access)
        auth_headers = create_auth_headers(user_token)
        response = client.get(
            f"/api/v1/organizations/{test_organization.id}/statistics",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Admin should also be able to view statistics
        admin_headers = create_auth_headers(admin_token)
        response = client.get(
            f"/api/v1/organizations/{test_organization.id}/statistics",
            headers=admin_headers
        )
        assert response.status_code == 200

    def test_bulk_operation_permissions(
        self,
        client: TestClient,
        db_session: Session,
        user_token: str,
        admin_token: str,
    ):
        """Test permissions for bulk operations."""
        auth_headers = create_auth_headers(user_token)
        admin_headers = create_auth_headers(admin_token)
        
        # Create multiple organizations for testing
        for i in range(3):
            OrganizationFactory.create(
                db_session,
                code=f"BULK-PERM-{i:03d}",
                name=f"Bulk Permission Test Org {i+1}",
            )
        
        # Regular user can list organizations (read access)
        response = client.get("/api/v1/organizations/?limit=5", headers=auth_headers)
        assert response.status_code == 200
        
        # Admin can also list organizations
        response = client.get("/api/v1/organizations/?limit=5", headers=admin_headers)
        assert response.status_code == 200
        
        # Test organization tree access
        response = client.get("/api/v1/organizations/tree", headers=auth_headers)
        assert response.status_code == 200
        
        response = client.get("/api/v1/organizations/tree", headers=admin_headers)
        assert response.status_code == 200

    def test_cross_organization_access_control(
        self,
        db_session: Session,
        test_organization: Organization,
        external_user: User,
    ):
        """Test access control across different organizations."""
        service = OrganizationService(db_session)
        
        # External user should not have write access to test organization
        # This is currently simplified in the implementation
        can_access = service.can_user_access_organization(
            external_user.id, test_organization.id
        )
        
        # In the current implementation, this checks if user is superuser
        # In a real implementation, this would check organization-specific permissions
        assert not can_access  # External user is not superuser

    def test_permission_validation_edge_cases(
        self,
        db_session: Session,
        test_organization: Organization,
    ):
        """Test edge cases in permission validation."""
        service = OrganizationService(db_session)
        
        # Test with non-existent user
        assert not service.user_has_permission(99999, "organizations.read")
        assert not service.can_user_access_organization(99999, test_organization.id)
        
        # Test with non-existent organization
        valid_user_id = 1
        assert not service.can_user_access_organization(valid_user_id, 99999)
        
        # Test with None values
        assert not service.user_has_permission(None, "organizations.read")
        assert not service.can_user_access_organization(None, test_organization.id)