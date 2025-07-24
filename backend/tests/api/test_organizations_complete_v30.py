from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from httpx import AsyncClient

from app.main import app
from app.models.organization_extended import Department, Organization
from app.models.user_extended import User


class TestOrganizationsCompleteV30:
    """Complete Organization Management API Tests"""

    @pytest.fixture
    async def mock_user(self):
        """Create a mock user for testing"""
        user = User()
        user.id = "test-user-123"
        user.is_superuser = True
        return user

    @pytest.fixture
    async def mock_organization(self):
        """Create a mock organization for testing"""
        org = Organization()
        org.id = "test-org-123"
        org.name = "Test Corporation"
        org.code = "TEST_CORP"
        org.organization_type = "corporation"
        org.industry = "Technology"
        org.email = "info@testcorp.com"
        org.phone = "+81-3-1234-5678"
        org.country = "Japan"
        org.is_active = True
        org.is_headquarters = True
        org.level = 0
        org.path = "/TEST_CORP"
        org.annual_revenue = Decimal("1000000000")
        org.employee_count = 500
        org.created_at = datetime.utcnow()
        return org

    @pytest.fixture
    async def mock_department(self):
        """Create a mock department for testing"""
        dept = Department()
        dept.id = "test-dept-123"
        dept.name = "Engineering Department"
        dept.code = "ENG"
        dept.organization_id = "test-org-123"
        dept.department_type = "operational"
        dept.cost_center = "CC001"
        dept.budget = Decimal("50000000")
        dept.is_active = True
        dept.created_at = datetime.utcnow()
        return dept

    @pytest.mark.asyncio
    async def test_create_organization_success(self, mock_user):
        """Test successful organization creation"""
        with (
            patch(
                "app.api.v1.organizations_complete_v30.require_admin",
                return_value=mock_user,
            ),
            patch("app.api.v1.organizations_complete_v30.get_db"),
            patch("app.crud.organization_extended_v30.OrganizationCRUD") as mock_crud,
        ):
            # Setup mocks
            mock_org = Organization()
            mock_org.id = "new-org-123"
            mock_org.name = "New Corporation"
            mock_org.code = "NEW_CORP"

            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.create.return_value = mock_org

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/organizations",
                    json={
                        "name": "New Corporation",
                        "code": "NEW_CORP",
                        "organization_type": "corporation",
                        "industry": "Technology",
                        "email": "info@newcorp.com",
                        "country": "Japan",
                    },
                )

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "New Corporation"
            assert data["code"] == "NEW_CORP"

    @pytest.mark.asyncio
    async def test_create_organization_duplicate_code(self, mock_user):
        """Test organization creation with duplicate code"""
        with (
            patch(
                "app.api.v1.organizations_complete_v30.require_admin",
                return_value=mock_user,
            ),
            patch("app.api.v1.organizations_complete_v30.get_db"),
            patch("app.crud.organization_extended_v30.OrganizationCRUD") as mock_crud,
        ):
            # Setup mocks
            from app.crud.organization_extended_v30 import DuplicateError

            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.create.side_effect = DuplicateError(
                "Organization code already exists"
            )

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/organizations",
                    json={
                        "name": "Duplicate Corporation",
                        "code": "EXISTING_CODE",
                        "organization_type": "corporation",
                    },
                )

            assert response.status_code == 400
            assert "Organization code already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_organizations_with_filters(self, mock_user, mock_organization):
        """Test organizations list with filters"""
        with (
            patch(
                "app.api.v1.organizations_complete_v30.get_current_user",
                return_value=mock_user,
            ),
            patch("app.api.v1.organizations_complete_v30.get_db"),
            patch("app.crud.organization_extended_v30.OrganizationCRUD") as mock_crud,
        ):
            # Setup mocks
            mock_orgs = [mock_organization]
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_multi.return_value = (mock_orgs, 1)

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get(
                    "/api/v1/organizations?search=test&organization_type=corporation&is_active=true"
                )

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert len(data["items"]) == 1

            # Verify filters were passed correctly
            mock_crud_instance.get_multi.assert_called_once()
            call_args = mock_crud_instance.get_multi.call_args
            filters = call_args[1]["filters"]
            assert filters["search"] == "test"
            assert filters["organization_type"] == "corporation"
            assert filters["is_active"]

    @pytest.mark.asyncio
    async def test_get_organization_by_id(self, mock_user, mock_organization):
        """Test get organization by ID"""
        with (
            patch(
                "app.api.v1.organizations_complete_v30.get_current_user",
                return_value=mock_user,
            ),
            patch("app.api.v1.organizations_complete_v30.get_db"),
            patch("app.crud.organization_extended_v30.OrganizationCRUD") as mock_crud,
        ):
            # Setup mocks
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_by_id.return_value = mock_organization

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get(f"/api/v1/organizations/{mock_organization.id}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == mock_organization.id
            assert data["name"] == mock_organization.name

    @pytest.mark.asyncio
    async def test_get_organization_not_found(self, mock_user):
        """Test get organization with non-existent ID"""
        with (
            patch(
                "app.api.v1.organizations_complete_v30.get_current_user",
                return_value=mock_user,
            ),
            patch("app.api.v1.organizations_complete_v30.get_db"),
            patch("app.crud.organization_extended_v30.OrganizationCRUD") as mock_crud,
        ):
            # Setup mocks
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_by_id.return_value = None

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get("/api/v1/organizations/non-existent-id")

            assert response.status_code == 404
            assert "Organization not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_organization_success(self, mock_user, mock_organization):
        """Test successful organization update"""
        with (
            patch(
                "app.api.v1.organizations_complete_v30.require_admin",
                return_value=mock_user,
            ),
            patch("app.api.v1.organizations_complete_v30.get_db"),
            patch("app.crud.organization_extended_v30.OrganizationCRUD") as mock_crud,
        ):
            # Setup mocks
            updated_org = Organization()
            updated_org.id = mock_organization.id
            updated_org.name = "Updated Corporation"
            updated_org.code = mock_organization.code

            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.update.return_value = updated_org

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.put(
                    f"/api/v1/organizations/{mock_organization.id}",
                    json={"name": "Updated Corporation"},
                )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Corporation"

    @pytest.mark.asyncio
    async def test_delete_organization_success(self, mock_user, mock_organization):
        """Test successful organization deletion"""
        with (
            patch(
                "app.api.v1.organizations_complete_v30.require_admin",
                return_value=mock_user,
            ),
            patch("app.api.v1.organizations_complete_v30.get_db"),
            patch("app.crud.organization_extended_v30.OrganizationCRUD") as mock_crud,
        ):
            # Setup mocks
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.delete.return_value = True

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.delete(
                    f"/api/v1/organizations/{mock_organization.id}"
                )

            assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_organization_with_children(
        self, mock_user, mock_organization
    ):
        """Test organization deletion with child organizations"""
        with (
            patch(
                "app.api.v1.organizations_complete_v30.require_admin",
                return_value=mock_user,
            ),
            patch("app.api.v1.organizations_complete_v30.get_db"),
            patch("app.crud.organization_extended_v30.OrganizationCRUD") as mock_crud,
        ):
            # Setup mocks
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.delete.side_effect = ValueError(
                "Cannot delete organization with child organizations"
            )

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.delete(
                    f"/api/v1/organizations/{mock_organization.id}"
                )

            assert response.status_code == 400
            assert (
                "Cannot delete organization with child organizations"
                in response.json()["detail"]
            )

    @pytest.mark.asyncio
    async def test_get_organization_hierarchy(self, mock_user, mock_organization):
        """Test get organization hierarchy"""
        with (
            patch(
                "app.api.v1.organizations_complete_v30.get_current_user",
                return_value=mock_user,
            ),
            patch("app.api.v1.organizations_complete_v30.get_db"),
            patch("app.crud.organization_extended_v30.OrganizationCRUD") as mock_crud,
        ):
            # Setup mocks
            mock_organization.departments = []
            mock_organization.children = []

            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_hierarchy.return_value = mock_organization

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get(
                    f"/api/v1/organizations/{mock_organization.id}/hierarchy"
                )

            assert response.status_code == 200
            data = response.json()
            assert "organization" in data
            assert "departments" in data
            assert "children" in data

    @pytest.mark.asyncio
    async def test_get_organization_tree(self, mock_user, mock_organization):
        """Test get organization tree"""
        with (
            patch(
                "app.api.v1.organizations_complete_v30.get_current_user",
                return_value=mock_user,
            ),
            patch("app.api.v1.organizations_complete_v30.get_db"),
            patch("app.crud.organization_extended_v30.OrganizationCRUD") as mock_crud,
        ):
            # Setup mocks
            mock_orgs = [mock_organization]
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_tree.return_value = mock_orgs

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get("/api/v1/organizations/tree")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["id"] == mock_organization.id

    @pytest.mark.asyncio
    async def test_get_organization_statistics(self, mock_user):
        """Test get organization statistics"""
        with (
            patch(
                "app.api.v1.organizations_complete_v30.require_admin",
                return_value=mock_user,
            ),
            patch("app.api.v1.organizations_complete_v30.get_db"),
            patch("app.crud.organization_extended_v30.OrganizationCRUD") as mock_crud,
        ):
            # Setup mocks
            mock_stats = {
                "total_organizations": 25,
                "active_organizations": 20,
                "inactive_organizations": 5,
                "headquarters_count": 3,
                "by_type": {"corporation": 10, "division": 8, "department": 7},
                "by_industry": {"Technology": 12, "Manufacturing": 8, "Services": 5},
                "by_country": {"Japan": 20, "USA": 3, "Singapore": 2},
                "total_employees": 5000,
                "total_departments": 150,
            }
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_statistics.return_value = mock_stats

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get("/api/v1/organizations/stats/summary")

            assert response.status_code == 200
            data = response.json()
            assert data["total_organizations"] == 25
            assert data["active_organizations"] == 20
            assert "by_type" in data
            assert "by_industry" in data

    @pytest.mark.asyncio
    async def test_list_departments(
        self, mock_user, mock_organization, mock_department
    ):
        """Test list departments for organization"""
        with (
            patch(
                "app.api.v1.organizations_complete_v30.get_current_user",
                return_value=mock_user,
            ),
            patch("app.api.v1.organizations_complete_v30.get_db"),
            patch("app.crud.organization_extended_v30.DepartmentCRUD") as mock_crud,
        ):
            # Setup mocks
            mock_departments = [mock_department]
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_multi.return_value = (mock_departments, 1)

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get(
                    f"/api/v1/organizations/{mock_organization.id}/departments"
                )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1

    @pytest.mark.asyncio
    async def test_create_department_success(
        self, mock_user, mock_organization, mock_department
    ):
        """Test successful department creation"""
        with (
            patch(
                "app.api.v1.organizations_complete_v30.require_admin",
                return_value=mock_user,
            ),
            patch("app.api.v1.organizations_complete_v30.get_db"),
            patch("app.crud.organization_extended_v30.DepartmentCRUD") as mock_crud,
        ):
            # Setup mocks
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.create.return_value = mock_department

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    f"/api/v1/organizations/{mock_organization.id}/departments",
                    json={
                        "name": "New Department",
                        "code": "NEW_DEPT",
                        "department_type": "operational",
                        "budget": "25000000",
                    },
                )

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == mock_department.name

    @pytest.mark.asyncio
    async def test_list_organization_addresses(self, mock_user, mock_organization):
        """Test list organization addresses"""
        with (
            patch(
                "app.api.v1.organizations_complete_v30.get_current_user",
                return_value=mock_user,
            ),
            patch("app.api.v1.organizations_complete_v30.get_db"),
            patch("app.crud.organization_extended_v30.AddressCRUD") as mock_crud,
        ):
            # Setup mocks
            mock_addresses = []
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_by_organization.return_value = mock_addresses

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get(
                    f"/api/v1/organizations/{mock_organization.id}/addresses"
                )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_create_organization_address(self, mock_user, mock_organization):
        """Test create organization address"""
        with (
            patch(
                "app.api.v1.organizations_complete_v30.require_admin",
                return_value=mock_user,
            ),
            patch("app.api.v1.organizations_complete_v30.get_db"),
            patch("app.crud.organization_extended_v30.AddressCRUD") as mock_crud,
        ):
            # Setup mocks
            from app.models.organization_extended import OrganizationAddress

            mock_address = OrganizationAddress()
            mock_address.id = "address-123"
            mock_address.address_type = "headquarters"
            mock_address.address_line1 = "1-1-1 Tokyo"

            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.create.return_value = mock_address

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    f"/api/v1/organizations/{mock_organization.id}/addresses",
                    json={
                        "address_type": "headquarters",
                        "address_line1": "1-1-1 Tokyo",
                        "city": "Tokyo",
                        "postal_code": "100-0001",
                        "country": "Japan",
                    },
                )

            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_list_organization_contacts(self, mock_user, mock_organization):
        """Test list organization contacts"""
        with (
            patch(
                "app.api.v1.organizations_complete_v30.get_current_user",
                return_value=mock_user,
            ),
            patch("app.api.v1.organizations_complete_v30.get_db"),
            patch("app.crud.organization_extended_v30.ContactCRUD") as mock_crud,
        ):
            # Setup mocks
            mock_contacts = []
            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.get_by_organization.return_value = mock_contacts

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get(
                    f"/api/v1/organizations/{mock_organization.id}/contacts"
                )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_create_organization_contact(self, mock_user, mock_organization):
        """Test create organization contact"""
        with (
            patch(
                "app.api.v1.organizations_complete_v30.require_admin",
                return_value=mock_user,
            ),
            patch("app.api.v1.organizations_complete_v30.get_db"),
            patch("app.crud.organization_extended_v30.ContactCRUD") as mock_crud,
        ):
            # Setup mocks
            from app.models.organization_extended import OrganizationContact

            mock_contact = OrganizationContact()
            mock_contact.id = "contact-123"
            mock_contact.name = "John Doe"
            mock_contact.contact_type = "primary"

            mock_crud_instance = Mock()
            mock_crud.return_value = mock_crud_instance
            mock_crud_instance.create.return_value = mock_contact

            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    f"/api/v1/organizations/{mock_organization.id}/contacts",
                    json={
                        "name": "John Doe",
                        "title": "CEO",
                        "email": "john@testcorp.com",
                        "phone": "+81-3-1234-5678",
                        "contact_type": "primary",
                    },
                )

            assert response.status_code == 201
