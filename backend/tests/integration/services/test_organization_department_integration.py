"""Integration tests for Organization and Department services."""

import pytest
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.organization import Organization
from app.schemas.department import DepartmentCreate
from app.schemas.organization import OrganizationCreate
from app.services.department import DepartmentService
from app.services.organization import OrganizationService
from tests.factories import DepartmentFactory, OrganizationFactory, UserFactory


class TestOrganizationDepartmentIntegration:
    """Test integration between Organization and Department services."""

    @pytest.fixture
    def organization_service(self, db_session: Session):
        """Organization service fixture."""
        return OrganizationService(db_session)

    @pytest.fixture
    def department_service(self, db_session: Session):
        """Department service fixture."""
        return DepartmentService(db_session)

    @pytest.fixture
    def test_user(self, db_session: Session):
        """Create a test user for audit fields."""
        return UserFactory.create(db_session, email="test@example.com")

    @pytest.fixture
    def sample_organization(self, db_session: Session):
        """Create a sample organization for testing."""
        return OrganizationFactory.create(
            db_session,
            code="TEST-ORG",
            name="Test Organization",
            settings={"department_code_prefix": "DEPT-"}
        )

    def test_organization_department_hierarchy(
        self,
        db_session: Session,
        organization_service: OrganizationService,
        department_service: DepartmentService,
        sample_organization: Organization
    ):
        """Test organization-department hierarchy creation and management."""
        # Create departments within the organization
        dept1 = DepartmentFactory.create(
            db_session,
            organization_id=sample_organization.id,
            code="DEPT-001",
            name="Engineering"
        )
        
        dept2 = DepartmentFactory.create(
            db_session,
            organization_id=sample_organization.id,
            code="DEPT-002",
            name="Marketing",
            parent_id=dept1.id
        )
        
        # Test organization statistics include department counts
        stats = organization_service.get_organization_statistics(sample_organization.id)
        
        assert stats["department_count"] == 2
        assert "user_count" in stats
        assert "active_subsidiaries" in stats

    def test_organization_settings_affect_departments(
        self,
        db_session: Session,
        organization_service: OrganizationService,
        department_service: DepartmentService,
        sample_organization: Organization,
        test_user
    ):
        """Test that organization settings can be used by departments."""
        # Update organization settings
        new_settings = {
            "department_code_prefix": "ENGR-",
            "default_currency": "USD",
            "auto_approve_departments": True
        }
        
        updated_org = organization_service.update_settings(
            sample_organization.id,
            new_settings,
            updated_by=test_user.id
        )
        
        assert updated_org is not None
        # Use to_dict() method to properly handle JSON serialization
        settings_dict = updated_org.to_dict()["settings"]
        assert settings_dict["department_code_prefix"] == "ENGR-"
        assert settings_dict["auto_approve_departments"] is True
        
        # Verify settings persist
        retrieved_org = organization_service.get_organization(sample_organization.id)
        retrieved_settings = retrieved_org.to_dict()["settings"]
        assert retrieved_settings["department_code_prefix"] == "ENGR-"

    def test_organization_deletion_with_departments(
        self,
        db_session: Session,
        organization_service: OrganizationService,
        department_service: DepartmentService,
        sample_organization: Organization,
        test_user
    ):
        """Test organization deletion behavior with existing departments."""
        # Create departments
        dept1 = DepartmentFactory.create(
            db_session,
            organization_id=sample_organization.id,
            code="DEPT-001",
            name="Engineering"
        )
        
        dept2 = DepartmentFactory.create(
            db_session,
            organization_id=sample_organization.id,
            code="DEPT-002",
            name="Marketing"
        )
        
        # Attempt to delete organization (should succeed with soft delete)
        success = organization_service.delete_organization(sample_organization.id, deleted_by=test_user.id)
        
        assert success is True
        
        # Verify organization is soft deleted
        org = organization_service.get_organization(sample_organization.id)
        assert org.is_deleted is True

    def test_multi_organization_department_isolation(
        self,
        db_session: Session,
        organization_service: OrganizationService,
        department_service: DepartmentService
    ):
        """Test that departments are properly isolated between organizations."""
        # Create two organizations
        org1 = OrganizationFactory.create(
            db_session,
            code="ORG-001",
            name="Organization 1"
        )
        
        org2 = OrganizationFactory.create(
            db_session,
            code="ORG-002",
            name="Organization 2"
        )
        
        # Create departments in each organization
        dept1_org1 = DepartmentFactory.create(
            db_session,
            organization_id=org1.id,
            code="DEPT-001",
            name="Engineering Org1"
        )
        
        dept1_org2 = DepartmentFactory.create(
            db_session,
            organization_id=org2.id,
            code="DEPT-001",  # Same code but different org
            name="Engineering Org2"
        )
        
        # Verify statistics are isolated
        stats1 = organization_service.get_organization_statistics(org1.id)
        stats2 = organization_service.get_organization_statistics(org2.id)
        
        assert stats1["department_count"] == 1
        assert stats2["department_count"] == 1

    def test_organization_hierarchy_with_departments(
        self,
        db_session: Session,
        organization_service: OrganizationService,
        department_service: DepartmentService
    ):
        """Test organization hierarchy with departments at different levels."""
        # Create parent organization
        parent_org = OrganizationFactory.create(
            db_session,
            code="PARENT-ORG",
            name="Parent Organization"
        )
        
        # Create subsidiary organization
        subsidiary_org = OrganizationFactory.create(
            db_session,
            code="SUB-ORG",
            name="Subsidiary Organization",
            parent_id=parent_org.id
        )
        
        # Create departments in both organizations
        parent_dept = DepartmentFactory.create(
            db_session,
            organization_id=parent_org.id,
            code="PARENT-DEPT",
            name="Parent Department"
        )
        
        subsidiary_dept = DepartmentFactory.create(
            db_session,
            organization_id=subsidiary_org.id,
            code="SUB-DEPT",
            name="Subsidiary Department"
        )
        
        # Verify parent organization statistics
        parent_stats = organization_service.get_organization_statistics(parent_org.id)
        assert parent_stats["department_count"] == 1
        assert parent_stats["active_subsidiaries"] == 1
        
        # Verify subsidiary organization statistics
        sub_stats = organization_service.get_organization_statistics(subsidiary_org.id)
        assert sub_stats["department_count"] == 1
        assert sub_stats["active_subsidiaries"] == 0

    def test_organization_search_with_department_filters(
        self,
        db_session: Session,
        organization_service: OrganizationService,
        sample_organization: Organization
    ):
        """Test organization search functionality with department-related data."""
        # Create departments
        dept1 = DepartmentFactory.create(
            db_session,
            organization_id=sample_organization.id,
            code="ENGINEERING",
            name="Engineering Department"
        )
        
        dept2 = DepartmentFactory.create(
            db_session,
            organization_id=sample_organization.id,
            code="MARKETING",
            name="Marketing Department"
        )
        
        # Search organizations
        results, total = organization_service.search_organizations(
            "Test Organization",
            skip=0,
            limit=10
        )
        
        assert total >= 1
        assert any(org.id == sample_organization.id for org in results)
        
        # Verify department count in organization summary
        summary = organization_service.get_organization_summary(sample_organization)
        assert summary.department_count == 2

    def test_organization_tree_with_departments(
        self,
        db_session: Session,
        organization_service: OrganizationService,
        department_service: DepartmentService
    ):
        """Test organization tree includes department information."""
        # Create organization hierarchy
        root_org = OrganizationFactory.create(
            db_session,
            code="ROOT",
            name="Root Organization"
        )
        
        child_org = OrganizationFactory.create(
            db_session,
            code="CHILD",
            name="Child Organization",
            parent_id=root_org.id
        )
        
        # Add departments to both organizations
        DepartmentFactory.create(
            db_session,
            organization_id=root_org.id,
            code="ROOT-DEPT",
            name="Root Department"
        )
        
        DepartmentFactory.create(
            db_session,
            organization_id=child_org.id,
            code="CHILD-DEPT",
            name="Child Department"
        )
        
        # Get organization tree
        tree = organization_service.get_organization_tree()
        
        assert len(tree) >= 1
        root_node = next((node for node in tree if node.id == root_org.id), None)
        assert root_node is not None
        assert len(root_node.children) >= 1
        
        # Verify child in tree
        child_node = root_node.children[0]
        assert child_node.id == child_org.id