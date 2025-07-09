"""API tests for Organization endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.organization import Organization
from tests.conftest import create_auth_headers
from tests.factories import OrganizationFactory


class TestOrganizationAPI:
    """Test Organization API endpoints."""

    def test_list_organizations(
        self, 
        client: TestClient, 
        test_organization: Organization,
        admin_token: str
    ):
        """Test listing organizations."""
        auth_headers = create_auth_headers(admin_token)
        response = client.get("/api/v1/organizations/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        
        # Check organization structure
        org = data["items"][0]
        assert "id" in org
        assert "code" in org
        assert "name" in org
        assert "is_active" in org

    def test_list_organizations_with_search(
        self, 
        client: TestClient, 
        test_organization: Organization,
        admin_token: str
    ):
        """Test listing organizations with search."""
        auth_headers = create_auth_headers(admin_token)
        response = client.get(
            "/api/v1/organizations/?search=テスト",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_list_organizations_with_filters(
        self, 
        client: TestClient, 
        test_organization: Organization,
        admin_token: str
    ):
        """Test listing organizations with filters."""
        auth_headers = create_auth_headers(admin_token)
        response = client.get(
            "/api/v1/organizations/?industry=IT&active_only=true",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_get_organization(
        self, 
        client: TestClient, 
        test_organization: Organization,
        admin_token: str
    ):
        """Test getting organization by ID."""
        auth_headers = create_auth_headers(admin_token)
        response = client.get(
            f"/api/v1/organizations/{test_organization.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == test_organization.id
        assert data["code"] == test_organization.code
        assert data["name"] == test_organization.name

    def test_get_organization_not_found(
        self, 
        client: TestClient, 
        admin_token: str
    ):
        """Test getting non-existent organization."""
        auth_headers = create_auth_headers(admin_token)
        response = client.get("/api/v1/organizations/99999", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_get_organization_by_code(
        self, 
        client: TestClient, 
        test_organization: Organization,
        admin_token: str
    ):
        """Test getting organization by code."""
        auth_headers = create_auth_headers(admin_token)
        response = client.get(
            f"/api/v1/organizations/code/{test_organization.code}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == test_organization.id
        assert data["code"] == test_organization.code

    def test_get_organization_by_code_not_found(
        self, 
        client: TestClient, 
        admin_token: str
    ):
        """Test getting organization by non-existent code."""
        auth_headers = create_auth_headers(admin_token)
        response = client.get(
            "/api/v1/organizations/code/NONEXISTENT",
            headers=auth_headers
        )
        
        assert response.status_code == 404

    def test_create_organization(
        self, 
        client: TestClient, 
        admin_token: str
    ):
        """Test creating a new organization."""
        auth_headers = create_auth_headers(admin_token)
        organization_data = {
            "code": "NEW-ORG-001",
            "name": "New Organization",
            "name_en": "New Organization",
            "industry": "Technology",
            "business_type": "株式会社",
            "is_active": True,
            "settings": {
                "fiscal_year_start": "04-01",
                "default_currency": "JPY"
            }
        }
        
        response = client.post(
            "/api/v1/organizations/",
            json=organization_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["code"] == organization_data["code"]
        assert data["name"] == organization_data["name"]
        assert data["industry"] == organization_data["industry"]
        assert data["is_active"] == organization_data["is_active"]

    def test_create_organization_duplicate_code(
        self, 
        client: TestClient, 
        test_organization: Organization,
        admin_token: str
    ):
        """Test creating organization with duplicate code."""
        auth_headers = create_auth_headers(admin_token)
        organization_data = {
            "code": test_organization.code,  # Duplicate code
            "name": "Duplicate Code Organization",
            "is_active": True
        }
        
        response = client.post(
            "/api/v1/organizations/",
            json=organization_data,
            headers=auth_headers
        )
        
        assert response.status_code == 409
        data = response.json()
        assert "code" in data
        assert data["code"] == "DUPLICATE_CODE"

    def test_update_organization(
        self, 
        client: TestClient, 
        test_organization: Organization,
        admin_token: str
    ):
        """Test updating an organization."""
        auth_headers = create_auth_headers(admin_token)
        update_data = {
            "name": "Updated Organization Name",
            "description": "Updated description",
            "industry": "Finance"
        }
        
        response = client.put(
            f"/api/v1/organizations/{test_organization.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["industry"] == update_data["industry"]

    def test_update_organization_not_found(
        self, 
        client: TestClient, 
        admin_token: str
    ):
        """Test updating non-existent organization."""
        auth_headers = create_auth_headers(admin_token)
        update_data = {"name": "Updated Name"}
        
        response = client.put(
            "/api/v1/organizations/99999",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404

    def test_delete_organization(
        self, 
        client: TestClient, 
        db_session: Session,
        admin_token: str
    ):
        """Test deleting an organization."""
        auth_headers = create_auth_headers(admin_token)
        # Create organization specifically for deletion test
        org = OrganizationFactory.create(
            db_session,
            code="DELETE-TEST",
            name="Organization to Delete"
        )
        
        response = client.delete(
            f"/api/v1/organizations/{org.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["id"] == org.id

    def test_delete_organization_not_found(
        self, 
        client: TestClient, 
        admin_token: str
    ):
        """Test deleting non-existent organization."""
        auth_headers = create_auth_headers(admin_token)
        response = client.delete("/api/v1/organizations/99999", headers=auth_headers)
        
        assert response.status_code == 404

    def test_get_organization_tree(
        self, 
        client: TestClient, 
        db_session: Session,
        admin_token: str
    ):
        """Test getting organization hierarchy tree."""
        auth_headers = create_auth_headers(admin_token)
        # Create parent and child organizations
        parent = OrganizationFactory.create(
            db_session,
            code="PARENT-001",
            name="Parent Organization"
        )
        child = OrganizationFactory.create(
            db_session,
            code="CHILD-001",
            name="Child Organization",
            parent_id=parent.id
        )
        
        response = client.get("/api/v1/organizations/tree", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_subsidiaries(
        self, 
        client: TestClient, 
        db_session: Session,
        admin_token: str
    ):
        """Test getting organization subsidiaries."""
        auth_headers = create_auth_headers(admin_token)
        # Create parent and child organizations
        parent = OrganizationFactory.create(
            db_session,
            code="PARENT-002",
            name="Parent Organization 2"
        )
        child = OrganizationFactory.create(
            db_session,
            code="CHILD-002",
            name="Child Organization 2",
            parent_id=parent.id
        )
        
        response = client.get(
            f"/api/v1/organizations/{parent.id}/subsidiaries",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["id"] == child.id

    def test_get_subsidiaries_recursive(
        self, 
        client: TestClient, 
        db_session: Session,
        admin_token: str
    ):
        """Test getting organization subsidiaries recursively."""
        auth_headers = create_auth_headers(admin_token)
        # Create parent -> child -> grandchild hierarchy
        parent = OrganizationFactory.create(
            db_session,
            code="PARENT-003",
            name="Parent Organization 3"
        )
        child = OrganizationFactory.create(
            db_session,
            code="CHILD-003",
            name="Child Organization 3",
            parent_id=parent.id
        )
        grandchild = OrganizationFactory.create(
            db_session,
            code="GRANDCHILD-003",
            name="Grandchild Organization 3",
            parent_id=child.id
        )
        
        response = client.get(
            f"/api/v1/organizations/{parent.id}/subsidiaries?recursive=true",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 2  # Should include both child and grandchild

    def test_activate_organization(
        self, 
        client: TestClient, 
        db_session: Session,
        admin_token: str
    ):
        """Test activating an organization."""
        auth_headers = create_auth_headers(admin_token)
        # Create inactive organization
        org = OrganizationFactory.create(
            db_session,
            code="INACTIVE-001",
            name="Inactive Organization",
            is_active=False
        )
        
        response = client.post(
            f"/api/v1/organizations/{org.id}/activate",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    def test_deactivate_organization(
        self, 
        client: TestClient, 
        test_organization: Organization,
        admin_token: str
    ):
        """Test deactivating an organization."""
        auth_headers = create_auth_headers(admin_token)
        response = client.post(
            f"/api/v1/organizations/{test_organization.id}/deactivate",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    def test_get_organization_statistics(
        self, 
        client: TestClient, 
        test_organization: Organization,
        admin_token: str
    ):
        """Test getting organization statistics."""
        auth_headers = create_auth_headers(admin_token)
        response = client.get(
            f"/api/v1/organizations/{test_organization.id}/statistics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "department_count" in data
        assert "user_count" in data
        assert "active_subsidiaries" in data
        assert "total_subsidiaries" in data
        assert "hierarchy_depth" in data

    def test_update_organization_settings(
        self, 
        client: TestClient, 
        test_organization: Organization,
        admin_token: str
    ):
        """Test updating organization settings."""
        auth_headers = create_auth_headers(admin_token)
        settings_data = {
            "fiscal_year_start": "01-01",
            "default_currency": "USD",
            "time_zone": "America/New_York",
            "department_prefix": "DEPT-"
        }
        
        response = client.put(
            f"/api/v1/organizations/{test_organization.id}/settings",
            json=settings_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Settings should be updated
        settings = data["settings"]
        assert settings["fiscal_year_start"] == "01-01"
        assert settings["default_currency"] == "USD"

    def test_unauthorized_access(self, client: TestClient):
        """Test unauthorized access to organization endpoints."""
        # Test without headers
        response = client.get("/api/v1/organizations/")
        # Could be 401 (unauthorized) or 403 (forbidden) depending on implementation
        assert response.status_code in [401, 403]

        # Test with invalid token
        response = client.get(
            "/api/v1/organizations/",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code in [401, 403]

    def test_pagination_parameters(
        self, 
        client: TestClient, 
        db_session: Session,
        admin_token: str
    ):
        """Test pagination parameters."""
        auth_headers = create_auth_headers(admin_token)
        # Create multiple organizations
        for i in range(5):
            OrganizationFactory.create(
                db_session,
                code=f"PAGINATE-{i:03d}",
                name=f"Pagination Test Org {i+1}"
            )
        
        # Test with custom pagination
        response = client.get(
            "/api/v1/organizations/?skip=2&limit=2",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["skip"] == 2
        assert data["limit"] == 2
        assert len(data["items"]) <= 2

    def test_invalid_pagination_parameters(
        self, 
        client: TestClient, 
        admin_token: str
    ):
        """Test invalid pagination parameters."""
        auth_headers = create_auth_headers(admin_token)
        # Test negative skip
        response = client.get(
            "/api/v1/organizations/?skip=-1",
            headers=auth_headers
        )
        assert response.status_code == 422

        # Test limit too high
        response = client.get(
            "/api/v1/organizations/?limit=1001",
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_create_organization_validation(
        self, 
        client: TestClient, 
        admin_token: str
    ):
        """Test organization creation validation."""
        auth_headers = create_auth_headers(admin_token)
        # Test missing required fields
        invalid_data = {"name": "Incomplete Organization"}  # Missing code
        
        response = client.post(
            "/api/v1/organizations/",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422

        # Test invalid data types
        invalid_data = {
            "code": "TEST-001",
            "name": "Test Organization",
            "is_active": "not_a_boolean"  # Should be boolean
        }
        
        response = client.post(
            "/api/v1/organizations/",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422

    def test_user_permissions(
        self, 
        client: TestClient, 
        test_organization: Organization,
        user_token: str
    ):
        """Test user permissions for organization endpoints."""
        auth_headers = create_auth_headers(user_token)
        
        # Normal user should be able to read organizations
        response = client.get("/api/v1/organizations/", headers=auth_headers)
        assert response.status_code == 200
        
        # But not create organizations (needs admin permission)
        organization_data = {
            "code": "USER-TEST-001",
            "name": "User Test Organization",
            "is_active": True
        }
        
        response = client.post(
            "/api/v1/organizations/",
            json=organization_data,
            headers=auth_headers
        )
        assert response.status_code == 403

    def test_get_organization_tree_by_id(
        self,
        client: TestClient,
        db_session: Session,
        admin_token: str
    ):
        """Test getting organization tree from a specific organization."""
        # Create a hierarchy of organizations
        auth_headers = create_auth_headers(admin_token)
        
        # Create parent organization
        parent_data = {
            "code": "PARENT-001",
            "name": "Parent Organization",
            "is_active": True
        }
        parent_response = client.post(
            "/api/v1/organizations/",
            json=parent_data,
            headers=auth_headers
        )
        assert parent_response.status_code == 201
        parent_id = parent_response.json()["id"]
        
        # Create child organizations
        child1_data = {
            "code": "CHILD-001",
            "name": "Child Organization 1",
            "parent_id": parent_id,
            "is_active": True
        }
        child1_response = client.post(
            "/api/v1/organizations/",
            json=child1_data,
            headers=auth_headers
        )
        assert child1_response.status_code == 201
        
        # Get tree from parent
        response = client.get(
            f"/api/v1/organizations/{parent_id}/tree",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        tree = response.json()
        
        assert tree["id"] == parent_id
        assert tree["code"] == "PARENT-001"
        assert tree["name"] == "Parent Organization"
        assert len(tree["children"]) == 1
        assert tree["children"][0]["code"] == "CHILD-001"

    def test_add_subsidiary(
        self,
        client: TestClient,
        test_organization: Organization,
        admin_token: str
    ):
        """Test adding a subsidiary to an organization."""
        auth_headers = create_auth_headers(admin_token)
        
        # Create subsidiary data
        subsidiary_data = {
            "code": "SUB-001",
            "name": "Subsidiary Organization",
            "is_active": True,
            "description": "A subsidiary of the test organization"
        }
        
        # Add subsidiary
        response = client.post(
            f"/api/v1/organizations/{test_organization.id}/subsidiaries",
            json=subsidiary_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        subsidiary = response.json()
        
        assert subsidiary["code"] == "SUB-001"
        assert subsidiary["name"] == "Subsidiary Organization"
        assert subsidiary["parent_id"] == test_organization.id
        
        # Verify the subsidiary appears in the parent's subsidiaries
        response = client.get(
            f"/api/v1/organizations/{test_organization.id}/subsidiaries",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        subsidiaries = response.json()
        assert len(subsidiaries) >= 1
        assert any(s["code"] == "SUB-001" for s in subsidiaries)

    def test_add_subsidiary_with_inherited_settings(
        self,
        client: TestClient,
        db_session: Session,
        admin_token: str
    ):
        """Test that subsidiary inherits settings from parent."""
        auth_headers = create_auth_headers(admin_token)
        
        # Create parent organization with specific settings
        parent_data = {
            "code": "PARENT-SETTINGS",
            "name": "Parent with Settings",
            "is_active": True,
            "settings": {
                "fiscal_year_start": "01-01",
                "default_currency": "USD",
                "timezone": "America/New_York"
            }
        }
        parent_response = client.post(
            "/api/v1/organizations/",
            json=parent_data,
            headers=auth_headers
        )
        assert parent_response.status_code == 201
        parent_id = parent_response.json()["id"]
        
        # Add subsidiary without specifying settings
        subsidiary_data = {
            "code": "SUB-INHERIT",
            "name": "Subsidiary with Inherited Settings",
            "is_active": True
        }
        
        response = client.post(
            f"/api/v1/organizations/{parent_id}/subsidiaries",
            json=subsidiary_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        subsidiary = response.json()
        
        # Check that settings were inherited
        assert subsidiary["settings"]["fiscal_year_start"] == "01-01"
        assert subsidiary["settings"]["default_currency"] == "USD"
        assert subsidiary["settings"]["timezone"] == "America/New_York"

    def test_add_subsidiary_permission_denied(
        self,
        client: TestClient,
        test_organization: Organization,
        user_token: str
    ):
        """Test that non-admin users cannot add subsidiaries."""
        auth_headers = create_auth_headers(user_token)
        
        subsidiary_data = {
            "code": "SUB-DENIED",
            "name": "Denied Subsidiary",
            "is_active": True
        }
        
        response = client.post(
            f"/api/v1/organizations/{test_organization.id}/subsidiaries",
            json=subsidiary_data,
            headers=auth_headers
        )
        
        assert response.status_code == 403

    def test_get_organization_tree_not_found(
        self,
        client: TestClient,
        admin_token: str
    ):
        """Test getting tree for non-existent organization."""
        auth_headers = create_auth_headers(admin_token)
        
        response = client.get(
            "/api/v1/organizations/99999/tree",
            headers=auth_headers
        )
        
        assert response.status_code == 404