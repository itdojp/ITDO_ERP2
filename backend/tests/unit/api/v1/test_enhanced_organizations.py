"""
Test cases for Enhanced Organizations API endpoints.
拡張組織管理APIエンドポイントのテスト
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.main import app
from app.schemas.organization import OrganizationTree, OrganizationWithStats


@pytest.fixture
def mock_enhanced_org_service():
    """Mock enhanced organization service."""
    service = AsyncMock()

    # Default return values
    service.get_organization_tree.return_value = OrganizationTree(
        id=1,
        code="ORG001",
        name="Test Organization",
        parent_id=None,
        is_active=True,
        subsidiaries=[],
        departments=[],
        users=[],
        depth=0
    )

    service.get_organization_with_stats.return_value = OrganizationWithStats(
        id=1,
        code="ORG001",
        name="Test Organization",
        name_en="Test Organization EN",
        parent_id=None,
        is_active=True,
        industry="Technology",
        business_type="Software",
        employee_count=100,
        capital=1000000,
        statistics={
            "total_users": 100,
            "active_users": 95,
            "total_departments": 5,
            "active_departments": 5
        }
    )

    service.move_organization.return_value = True
    service.get_all_subsidiaries.return_value = []
    service.get_hierarchy_path.return_value = []
    service.validate_hierarchy.return_value = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "recommendations": []
    }

    return service


@pytest.mark.asyncio
class TestEnhancedOrganizationsAPI:
    """Test cases for Enhanced Organizations API."""

    async def test_get_organization_tree(self, mock_enhanced_org_service):
        """Test getting organization tree structure."""
        with patch('app.api.v1.enhanced_organizations.EnhancedOrganizationService',
                  return_value=mock_enhanced_org_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/organizations/1/tree")

                assert response.status_code == 200
                data = response.json()
                assert data["id"] == 1
                assert data["code"] == "ORG001"
                assert data["name"] == "Test Organization"
                assert "subsidiaries" in data
                assert "departments" in data

    async def test_get_organization_tree_with_options(self, mock_enhanced_org_service):
        """Test getting organization tree with options."""
        with patch('app.api.v1.enhanced_organizations.EnhancedOrganizationService',
                  return_value=mock_enhanced_org_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/organizations/1/tree",
                    params={
                        "include_departments": True,
                        "include_users": True,
                        "max_depth": 5
                    }
                )

                assert response.status_code == 200
                mock_enhanced_org_service.get_organization_tree.assert_called_once_with(
                    organization_id=1,
                    include_departments=True,
                    include_users=True,
                    max_depth=5
                )

    async def test_get_organization_tree_not_found(self, mock_enhanced_org_service):
        """Test getting organization tree for non-existent organization."""
        mock_enhanced_org_service.get_organization_tree.return_value = None

        with patch('app.api.v1.enhanced_organizations.EnhancedOrganizationService',
                  return_value=mock_enhanced_org_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/organizations/999/tree")

                assert response.status_code == 404

    async def test_get_organization_statistics(self, mock_enhanced_org_service):
        """Test getting organization statistics."""
        with patch('app.api.v1.enhanced_organizations.EnhancedOrganizationService',
                  return_value=mock_enhanced_org_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/organizations/1/stats")

                assert response.status_code == 200
                data = response.json()
                assert data["id"] == 1
                assert "statistics" in data
                assert data["statistics"]["total_users"] == 100
                assert data["statistics"]["active_users"] == 95

    async def test_get_organization_statistics_with_subsidiaries(self, mock_enhanced_org_service):
        """Test getting organization statistics including subsidiaries."""
        with patch('app.api.v1.enhanced_organizations.EnhancedOrganizationService',
                  return_value=mock_enhanced_org_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/organizations/1/stats",
                    params={"include_subsidiaries": True}
                )

                assert response.status_code == 200
                mock_enhanced_org_service.get_organization_with_stats.assert_called_once_with(
                    organization_id=1,
                    include_subsidiaries=True
                )

    async def test_move_organization_success(self, mock_enhanced_org_service):
        """Test successful organization move."""
        with patch('app.api.v1.enhanced_organizations.EnhancedOrganizationService',
                  return_value=mock_enhanced_org_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/organizations/1/move",
                    params={"new_parent_id": 2}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["organization_id"] == 1
                assert data["new_parent_id"] == 2

    async def test_move_organization_permission_denied(self, mock_enhanced_org_service):
        """Test organization move with insufficient permissions."""
        with patch('app.api.v1.enhanced_organizations.EnhancedOrganizationService',
                  return_value=mock_enhanced_org_service), \
             patch('app.api.v1.enhanced_organizations.get_current_user') as mock_user:

            # Mock user without admin permissions
            mock_user.return_value.is_superuser = False
            mock_user.return_value.roles = []

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/organizations/1/move",
                    params={"new_parent_id": 2}
                )

                assert response.status_code == 403

    async def test_get_all_subsidiaries(self, mock_enhanced_org_service):
        """Test getting all subsidiaries recursively."""
        mock_enhanced_org_service.get_all_subsidiaries.return_value = [
            {
                "id": 2,
                "code": "SUB001",
                "name": "Subsidiary 1",
                "parent_id": 1,
                "is_active": True
            }
        ]

        with patch('app.api.v1.enhanced_organizations.EnhancedOrganizationService',
                  return_value=mock_enhanced_org_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/organizations/1/subsidiaries/all")

                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["id"] == 2

    async def test_get_hierarchy_path(self, mock_enhanced_org_service):
        """Test getting hierarchy path."""
        mock_enhanced_org_service.get_hierarchy_path.return_value = [
            {
                "id": 1,
                "code": "ROOT",
                "name": "Root Organization",
                "parent_id": None
            },
            {
                "id": 2,
                "code": "CHILD",
                "name": "Child Organization",
                "parent_id": 1
            }
        ]

        with patch('app.api.v1.enhanced_organizations.EnhancedOrganizationService',
                  return_value=mock_enhanced_org_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/organizations/2/hierarchy-path")

                assert response.status_code == 200
                data = response.json()
                assert len(data) == 2
                assert data[0]["code"] == "ROOT"
                assert data[1]["code"] == "CHILD"

    async def test_validate_organization_hierarchy(self, mock_enhanced_org_service):
        """Test organization hierarchy validation."""
        with patch('app.api.v1.enhanced_organizations.EnhancedOrganizationService',
                  return_value=mock_enhanced_org_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/organizations/1/validation")

                assert response.status_code == 200
                data = response.json()
                assert data["organization_id"] == 1
                assert data["is_valid"] is True
                assert "errors" in data
                assert "warnings" in data

    async def test_bulk_update_organization_hierarchy(self, mock_enhanced_org_service):
        """Test bulk hierarchy update."""
        mock_enhanced_org_service.bulk_update_hierarchy.return_value = {
            "updated_count": 2,
            "errors": [],
            "validation_results": {"is_valid": True}
        }

        updates = [
            {"organization_id": 1, "name": "Updated Name 1"},
            {"organization_id": 2, "name": "Updated Name 2"}
        ]

        with patch('app.api.v1.enhanced_organizations.EnhancedOrganizationService',
                  return_value=mock_enhanced_org_service), \
             patch('app.api.v1.enhanced_organizations.get_current_user') as mock_user:

            mock_user.return_value.is_superuser = True

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/organizations/1/bulk-update",
                    json=updates
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["updated_count"] == 2

    async def test_bulk_update_permission_denied(self, mock_enhanced_org_service):
        """Test bulk update with insufficient permissions."""
        with patch('app.api.v1.enhanced_organizations.EnhancedOrganizationService',
                  return_value=mock_enhanced_org_service), \
             patch('app.api.v1.enhanced_organizations.get_current_user') as mock_user:

            mock_user.return_value.is_superuser = False

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/organizations/1/bulk-update",
                    json=[{"organization_id": 1, "name": "Updated"}]
                )

                assert response.status_code == 403

    async def test_get_organization_department_tree(self, mock_enhanced_org_service):
        """Test getting organization department tree."""
        mock_enhanced_org_service.get_organization_department_tree.return_value = {
            "organization": {
                "id": 1,
                "code": "ORG001",
                "name": "Test Organization"
            },
            "departments": [
                {
                    "id": 1,
                    "code": "DEPT001",
                    "name": "Department 1",
                    "sub_departments": []
                }
            ],
            "total_departments": 1,
            "max_depth": 5
        }

        with patch('app.api.v1.enhanced_organizations.EnhancedOrganizationService',
                  return_value=mock_enhanced_org_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/organizations/1/departments/tree")

                assert response.status_code == 200
                data = response.json()
                assert data["organization"]["id"] == 1
                assert len(data["departments"]) == 1

    async def test_advanced_organization_search(self, mock_enhanced_org_service):
        """Test advanced organization search."""
        mock_enhanced_org_service.advanced_search.return_value = {
            "organizations": [
                {
                    "id": 1,
                    "code": "ORG001",
                    "name": "Test Organization"
                }
            ],
            "total_count": 1
        }

        with patch('app.api.v1.enhanced_organizations.EnhancedOrganizationService',
                  return_value=mock_enhanced_org_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/organizations/search/advanced",
                    params={
                        "query": "test",
                        "search_fields": ["name", "code"],
                        "sort_by": "name",
                        "sort_order": "asc",
                        "limit": 50,
                        "offset": 0
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert "results" in data
                assert "total_count" in data
                assert "pagination" in data

    async def test_service_error_handling(self, mock_enhanced_org_service):
        """Test error handling from service layer."""
        mock_enhanced_org_service.get_organization_tree.side_effect = ValueError("Service error")

        with patch('app.api.v1.enhanced_organizations.EnhancedOrganizationService',
                  return_value=mock_enhanced_org_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/organizations/1/tree")

                assert response.status_code == 400

    async def test_internal_server_error(self, mock_enhanced_org_service):
        """Test internal server error handling."""
        mock_enhanced_org_service.get_organization_tree.side_effect = Exception("Internal error")

        with patch('app.api.v1.enhanced_organizations.EnhancedOrganizationService',
                  return_value=mock_enhanced_org_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/organizations/1/tree")

                assert response.status_code == 500
