"""Unit tests for Organization Service."""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.core.exceptions import NotFound, ValidationError
from app.models.organization import Organization
from app.repositories.organization import OrganizationRepository
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.services.organization import OrganizationService


class TestOrganizationService:
    """Test cases for Organization Service."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def mock_repo(self):
        """Mock organization repository."""
        return Mock(spec=OrganizationRepository)

    @pytest.fixture
    def service(self, mock_db, mock_repo):
        """Organization service with mocked dependencies."""
        service = OrganizationService(mock_db)
        service.repository = mock_repo
        return service

    @pytest.fixture
    def sample_organization(self):
        """Sample organization for testing."""
        org = Organization()
        org.id = 1
        org.code = "TEST-ORG"
        org.name = "Test Organization"
        org.settings = {"currency": "JPY"}
        org.parent_id = None
        org.is_active = True
        return org

    def test_get_organization_by_code_success(self, service, mock_repo, sample_organization):
        """Test successful organization retrieval by code."""
        mock_repo.get_by_code.return_value = sample_organization
        
        result = service.get_organization_by_code("TEST-ORG")
        
        assert result == sample_organization
        mock_repo.get_by_code.assert_called_once_with("TEST-ORG")

    def test_get_organization_by_code_not_found(self, service, mock_repo):
        """Test organization not found by code."""
        mock_repo.get_by_code.return_value = None
        
        result = service.get_organization_by_code("NONEXISTENT")
        
        assert result is None
        mock_repo.get_by_code.assert_called_once_with("NONEXISTENT")

    def test_validate_parent_assignment_success(self, service, mock_repo):
        """Test successful parent assignment validation."""
        # Mock organization without circular reference
        parent_org = Organization()
        parent_org.id = 2
        parent_org.parent_id = None
        
        mock_repo.get.side_effect = lambda org_id: parent_org if org_id == 2 else None
        
        result = service.validate_parent_assignment(1, 2)
        
        assert result is True

    def test_validate_parent_assignment_self_reference(self, service):
        """Test parent assignment validation with self reference."""
        with pytest.raises(ValidationError, match="Organization cannot be its own parent"):
            service.validate_parent_assignment(1, 1)

    def test_validate_parent_assignment_circular_reference(self, service, mock_repo):
        """Test parent assignment validation with circular reference."""
        # Mock circular reference: org1 -> org2 -> org1
        org1 = Organization()
        org1.id = 1
        org1.parent_id = 2
        
        org2 = Organization()
        org2.id = 2
        org2.parent_id = 1
        
        mock_repo.get.side_effect = lambda org_id: org1 if org_id == 1 else org2 if org_id == 2 else None
        
        with pytest.raises(ValidationError, match="Circular reference detected"):
            service.validate_parent_assignment(1, 2)

    def test_get_organization_statistics_success(self, service, mock_repo, sample_organization):
        """Test successful organization statistics retrieval."""
        mock_repo.get.return_value = sample_organization
        mock_repo.get_department_count.return_value = 5
        mock_repo.get_user_count.return_value = 20
        
        # Mock get_direct_subsidiaries and get_all_subsidiaries
        subsidiary1 = Organization()
        subsidiary1.is_active = True
        subsidiary2 = Organization()
        subsidiary2.is_active = False
        
        service.get_direct_subsidiaries = Mock(return_value=[subsidiary1, subsidiary2])
        service.get_all_subsidiaries = Mock(return_value=[subsidiary1, subsidiary2])
        
        # Mock get_hierarchy_path
        sample_organization.get_hierarchy_path = Mock(return_value=[sample_organization])
        
        result = service.get_organization_statistics(1)
        
        expected = {
            "department_count": 5,
            "user_count": 20,
            "active_subsidiaries": 1,
            "total_subsidiaries": 2,
            "hierarchy_depth": 1,
        }
        
        assert result == expected
        mock_repo.get.assert_called_once_with(1)
        mock_repo.get_department_count.assert_called_once_with(1)
        mock_repo.get_user_count.assert_called_once_with(1)

    def test_get_organization_statistics_not_found(self, service, mock_repo):
        """Test organization statistics when organization not found."""
        mock_repo.get.return_value = None
        
        with pytest.raises(NotFound, match="Organization 1 not found"):
            service.get_organization_statistics(1)

    def test_update_settings_success(self, service, mock_repo, sample_organization):
        """Test successful settings update."""
        new_settings = {"currency": "USD", "timezone": "America/New_York"}
        mock_repo.update_settings.return_value = sample_organization
        
        result = service.update_settings(1, new_settings, updated_by=100)
        
        assert result == sample_organization
        mock_repo.update_settings.assert_called_once_with(1, new_settings)

    def test_update_settings_not_found(self, service, mock_repo):
        """Test settings update when organization not found."""
        mock_repo.update_settings.return_value = None
        
        result = service.update_settings(1, {}, updated_by=100)
        
        assert result is None

    def test_search_organizations_with_filters(self, service, mock_repo):
        """Test organization search with filters."""
        # Mock search results
        org1 = Organization()
        org1.is_active = True
        org1.industry = "IT"
        
        org2 = Organization()
        org2.is_active = False
        org2.industry = "IT"
        
        mock_repo.search_by_name.return_value = [org1, org2]
        
        filters = {"is_active": True}
        result, total = service.search_organizations("test", skip=0, limit=10, filters=filters)
        
        assert len(result) == 1
        assert total == 1
        assert result[0] == org1
        mock_repo.search_by_name.assert_called_once_with("test")

    def test_create_organization_success(self, service, mock_repo, mock_db):
        """Test successful organization creation."""
        create_data = OrganizationCreate(
            code="NEW-ORG",
            name="New Organization",
            is_active=True
        )
        
        new_org = Organization()
        new_org.id = 10
        new_org.code = "NEW-ORG"
        new_org.name = "New Organization"
        
        mock_repo.validate_unique_code.return_value = True
        mock_repo.create.return_value = new_org
        
        result = service.create_organization(create_data, created_by=100)
        
        assert result == new_org
        mock_repo.validate_unique_code.assert_called_once_with("NEW-ORG")
        mock_repo.create.assert_called_once()

    def test_create_organization_duplicate_code(self, service, mock_repo):
        """Test organization creation with duplicate code."""
        create_data = OrganizationCreate(
            code="DUPLICATE",
            name="Duplicate Organization",
            is_active=True
        )
        
        mock_repo.validate_unique_code.return_value = False
        
        with pytest.raises(ValueError, match="Organization code 'DUPLICATE' already exists"):
            service.create_organization(create_data, created_by=100)

    def test_update_organization_success(self, service, mock_repo, sample_organization):
        """Test successful organization update."""
        update_data = OrganizationUpdate(name="Updated Name")
        
        updated_org = Organization()
        updated_org.id = 1
        updated_org.name = "Updated Name"
        
        mock_repo.get.return_value = sample_organization
        mock_repo.validate_unique_code.return_value = True
        mock_repo.update.return_value = updated_org
        
        result = service.update_organization(1, update_data, updated_by=100)
        
        assert result == updated_org
        mock_repo.get.assert_called_once_with(1)
        mock_repo.update.assert_called_once()

    def test_update_organization_not_found(self, service, mock_repo):
        """Test organization update when organization not found."""
        update_data = OrganizationUpdate(name="Updated Name")
        mock_repo.get.return_value = None
        
        result = service.update_organization(1, update_data, updated_by=100)
        
        assert result is None

    def test_delete_organization_success(self, service, mock_repo, mock_db, sample_organization):
        """Test successful organization deletion."""
        mock_repo.get.return_value = sample_organization
        sample_organization.soft_delete = Mock()
        
        result = service.delete_organization(1, deleted_by=100)
        
        assert result is True
        mock_repo.get.assert_called_once_with(1)
        sample_organization.soft_delete.assert_called_once_with(deleted_by=100)
        mock_db.commit.assert_called_once()

    def test_delete_organization_not_found(self, service, mock_repo):
        """Test organization deletion when organization not found."""
        mock_repo.get.return_value = None
        
        result = service.delete_organization(1, deleted_by=100)
        
        assert result is False

    def test_add_subsidiary_success(self, service, mock_repo, mock_db, sample_organization):
        """Test successful subsidiary addition."""
        # Setup parent organization
        parent_org = Organization()
        parent_org.id = 1
        parent_org.code = "PARENT"
        parent_org.name = "Parent Org"
        parent_org.is_active = True
        parent_org.settings = {
            "fiscal_year_start": "04-01",
            "default_currency": "JPY",
            "timezone": "Asia/Tokyo"
        }
        
        # Setup subsidiary
        subsidiary = Organization()
        subsidiary.id = 2
        subsidiary.code = "SUB-001"
        subsidiary.name = "Subsidiary"
        subsidiary.parent_id = 1
        subsidiary.is_active = True
        subsidiary.settings = {}
        
        # Mock get_organization
        service.get_organization = Mock(return_value=parent_org)
        
        # Mock repository create
        mock_repo.create.return_value = subsidiary
        
        # Mock _get_permission_templates
        service._get_permission_templates = Mock(return_value=[
            {"id": 1, "name": "Template 1", "inheritable": True}
        ])
        
        # Mock _save_permission_template
        service._save_permission_template = Mock()
        
        # Test data
        subsidiary_data = OrganizationCreate(
            code="SUB-001",
            name="Subsidiary",
            is_active=True
        )
        
        # Execute
        result = service.add_subsidiary(
            parent_id=1,
            subsidiary_data=subsidiary_data,
            created_by=100
        )
        
        # Assertions
        assert result == subsidiary
        service.get_organization.assert_called_once_with(1)
        
        # Verify settings inheritance
        create_call_args = mock_repo.create.call_args[0][0]
        assert create_call_args["parent_id"] == 1
        assert create_call_args["settings"]["fiscal_year_start"] == "04-01"
        assert create_call_args["settings"]["default_currency"] == "JPY"
        
        # Verify permission template copy
        service._save_permission_template.assert_called_once()
        mock_db.commit.assert_called()

    def test_add_subsidiary_parent_not_found(self, service, mock_repo):
        """Test adding subsidiary when parent not found."""
        # Mock get_organization to return None
        service.get_organization = Mock(return_value=None)
        
        subsidiary_data = OrganizationCreate(
            code="SUB-001",
            name="Subsidiary",
            is_active=True
        )
        
        # Execute and expect exception
        with pytest.raises(NotFound, match="Parent organization 1 not found"):
            service.add_subsidiary(
                parent_id=1,
                subsidiary_data=subsidiary_data
            )

    def test_add_subsidiary_parent_inactive(self, service, mock_repo):
        """Test adding subsidiary to inactive parent."""
        # Setup inactive parent
        parent_org = Organization()
        parent_org.id = 1
        parent_org.is_active = False
        
        service.get_organization = Mock(return_value=parent_org)
        
        subsidiary_data = OrganizationCreate(
            code="SUB-001",
            name="Subsidiary",
            is_active=True
        )
        
        # Execute and expect exception
        with pytest.raises(ValidationError, match="Cannot add subsidiary to inactive organization"):
            service.add_subsidiary(
                parent_id=1,
                subsidiary_data=subsidiary_data
            )

    def test_add_subsidiary_with_existing_settings(self, service, mock_repo, mock_db):
        """Test adding subsidiary with its own settings."""
        # Setup parent organization
        parent_org = Organization()
        parent_org.id = 1
        parent_org.is_active = True
        parent_org.settings = {"default_currency": "JPY"}
        
        # Setup subsidiary with its own settings
        subsidiary = Organization()
        subsidiary.id = 2
        subsidiary.code = "SUB-001"
        subsidiary.name = "Subsidiary"
        subsidiary.parent_id = 1
        subsidiary.settings = {"default_currency": "USD"}
        
        service.get_organization = Mock(return_value=parent_org)
        mock_repo.create.return_value = subsidiary
        service._get_permission_templates = Mock(return_value=[])
        
        # Test data with settings
        subsidiary_data = OrganizationCreate(
            code="SUB-001",
            name="Subsidiary",
            is_active=True,
            settings={"default_currency": "USD"}
        )
        
        # Execute
        result = service.add_subsidiary(
            parent_id=1,
            subsidiary_data=subsidiary_data
        )
        
        # Verify settings were not overridden
        create_call_args = mock_repo.create.call_args[0][0]
        assert create_call_args["settings"]["default_currency"] == "USD"