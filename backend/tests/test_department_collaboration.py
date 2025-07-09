"""Tests for Department inter-department collaboration features."""

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError
from app.models.department import Department
from app.models.user import User
from app.schemas.department import DepartmentCreate
from app.services.department import DepartmentService


class TestDepartmentCollaboration:
    """Test inter-department collaboration features."""

    def setup_method(self):
        """Set up test fixtures."""
        self.dept_service = None
        self.test_org = None
        self.test_user = None

    def test_department_has_collaboration_methods(self, db_session: Session, test_organization, test_user):
        """Test that department service has collaboration-related methods."""
        self.dept_service = DepartmentService(db_session)
        self.test_org = test_organization
        self.test_user = test_user
        
        # Create departments
        dept1_data = DepartmentCreate(
            code="DEPT1",
            name="Department 1",
            organization_id=test_organization.id,
        )
        dept1 = self.dept_service.create_department(dept1_data)
        
        dept2_data = DepartmentCreate(
            code="DEPT2",
            name="Department 2",
            organization_id=test_organization.id,
        )
        dept2 = self.dept_service.create_department(dept2_data)
        
        # Check that the service has collaboration methods
        assert hasattr(self.dept_service, 'create_collaboration_agreement')
        assert hasattr(self.dept_service, 'get_collaboration_agreements')
        assert hasattr(self.dept_service, 'get_collaborating_departments')
        assert hasattr(self.dept_service, 'can_departments_collaborate')
        assert hasattr(self.dept_service, 'get_cross_department_permissions')
        
        # Test basic collaboration methods work
        agreements = self.dept_service.get_collaboration_agreements(dept1.id)
        assert isinstance(agreements, list)
        
        collaborating = self.dept_service.get_collaborating_departments(dept1.id)
        assert isinstance(collaborating, list)
        
        can_collaborate = self.dept_service.can_departments_collaborate(dept1.id, dept2.id)
        assert isinstance(can_collaborate, bool)
        
        cross_perms = self.dept_service.get_cross_department_permissions(
            test_user.id, dept1.id, dept2.id
        )
        assert isinstance(cross_perms, list)

    def test_create_collaboration_agreement(self, db_session: Session, test_organization, test_user):
        """Test creating collaboration agreement between departments."""
        self.dept_service = DepartmentService(db_session)
        self.test_org = test_organization
        self.test_user = test_user
        
        # Create departments
        sales_data = DepartmentCreate(
            code="SALES",
            name="Sales Department",
            organization_id=test_organization.id,
        )
        sales = self.dept_service.create_department(sales_data)
        
        marketing_data = DepartmentCreate(
            code="MARKETING",
            name="Marketing Department",
            organization_id=test_organization.id,
        )
        marketing = self.dept_service.create_department(marketing_data)
        
        # Create collaboration agreement
        agreement = self.dept_service.create_collaboration_agreement(
            department_a_id=sales.id,
            department_b_id=marketing.id,
            collaboration_type="project_sharing",
            description="Sales and Marketing collaboration for campaigns",
            created_by=test_user.id
        )
        
        # Check agreement was created
        assert agreement is not None
        assert hasattr(agreement, 'id')
        assert hasattr(agreement, 'department_a_id')
        assert hasattr(agreement, 'department_b_id')
        assert hasattr(agreement, 'collaboration_type')
        assert hasattr(agreement, 'is_active')
        assert agreement.is_active is True
        
        # Check departments can now collaborate
        can_collaborate = self.dept_service.can_departments_collaborate(sales.id, marketing.id)
        assert can_collaborate is True
        
        # Check bidirectional collaboration
        can_collaborate_reverse = self.dept_service.can_departments_collaborate(marketing.id, sales.id)
        assert can_collaborate_reverse is True

    def test_collaboration_agreement_validation(self, db_session: Session, test_organization, test_user):
        """Test collaboration agreement validation."""
        self.dept_service = DepartmentService(db_session)
        self.test_org = test_organization
        self.test_user = test_user
        
        # Create departments
        dept1_data = DepartmentCreate(
            code="DEPT1",
            name="Department 1",
            organization_id=test_organization.id,
        )
        dept1 = self.dept_service.create_department(dept1_data)
        
        # Test self-collaboration prevention
        with pytest.raises(BusinessLogicError, match="cannot collaborate with itself"):
            self.dept_service.create_collaboration_agreement(
                department_a_id=dept1.id,
                department_b_id=dept1.id,
                collaboration_type="project_sharing",
                description="Invalid self-collaboration",
                created_by=test_user.id
            )

    def test_get_collaborating_departments(self, db_session: Session, test_organization, test_user):
        """Test getting list of collaborating departments."""
        self.dept_service = DepartmentService(db_session)
        self.test_org = test_organization
        self.test_user = test_user
        
        # Create departments
        it_data = DepartmentCreate(
            code="IT",
            name="IT Department",
            organization_id=test_organization.id,
        )
        it = self.dept_service.create_department(it_data)
        
        hr_data = DepartmentCreate(
            code="HR",
            name="HR Department",
            organization_id=test_organization.id,
        )
        hr = self.dept_service.create_department(hr_data)
        
        finance_data = DepartmentCreate(
            code="FINANCE",
            name="Finance Department",
            organization_id=test_organization.id,
        )
        finance = self.dept_service.create_department(finance_data)
        
        # Create collaboration agreements
        self.dept_service.create_collaboration_agreement(
            department_a_id=it.id,
            department_b_id=hr.id,
            collaboration_type="system_integration",
            description="IT and HR system integration",
            created_by=test_user.id
        )
        
        self.dept_service.create_collaboration_agreement(
            department_a_id=it.id,
            department_b_id=finance.id,
            collaboration_type="reporting",
            description="IT and Finance reporting collaboration",
            created_by=test_user.id
        )
        
        # Get collaborating departments for IT
        collaborating = self.dept_service.get_collaborating_departments(it.id)
        assert len(collaborating) == 2
        
        collaborating_ids = [dept.id for dept in collaborating]
        assert hr.id in collaborating_ids
        assert finance.id in collaborating_ids

    def test_collaboration_permissions_integration(self, db_session: Session, test_organization, test_user):
        """Test that collaboration affects permission checks."""
        self.dept_service = DepartmentService(db_session)
        self.test_org = test_organization
        self.test_user = test_user
        
        # Create departments
        dept_a_data = DepartmentCreate(
            code="DEPT_A",
            name="Department A",
            organization_id=test_organization.id,
        )
        dept_a = self.dept_service.create_department(dept_a_data)
        
        dept_b_data = DepartmentCreate(
            code="DEPT_B",
            name="Department B",
            organization_id=test_organization.id,
        )
        dept_b = self.dept_service.create_department(dept_b_data)
        
        # Create collaboration agreement
        agreement = self.dept_service.create_collaboration_agreement(
            department_a_id=dept_a.id,
            department_b_id=dept_b.id,
            collaboration_type="full_access",
            description="Full collaboration between A and B",
            created_by=test_user.id
        )
        
        # Test cross-department permissions
        cross_perms = self.dept_service.get_cross_department_permissions(
            test_user.id, dept_a.id, dept_b.id
        )
        assert isinstance(cross_perms, list)
        
        # Test collaboration affects permission inheritance
        # (This would need actual user roles and permissions to test fully)
        effective_perms = self.dept_service.get_user_effective_permissions(test_user.id, dept_a.id)
        assert isinstance(effective_perms, list)

    def test_collaboration_agreement_lifecycle(self, db_session: Session, test_organization, test_user):
        """Test collaboration agreement lifecycle (activate/deactivate)."""
        self.dept_service = DepartmentService(db_session)
        self.test_org = test_organization
        self.test_user = test_user
        
        # Create departments
        dept1_data = DepartmentCreate(
            code="DEPT1",
            name="Department 1",
            organization_id=test_organization.id,
        )
        dept1 = self.dept_service.create_department(dept1_data)
        
        dept2_data = DepartmentCreate(
            code="DEPT2",
            name="Department 2",
            organization_id=test_organization.id,
        )
        dept2 = self.dept_service.create_department(dept2_data)
        
        # Create collaboration agreement
        agreement = self.dept_service.create_collaboration_agreement(
            department_a_id=dept1.id,
            department_b_id=dept2.id,
            collaboration_type="project_sharing",
            description="Test collaboration",
            created_by=test_user.id
        )
        
        # Initially active
        assert agreement.is_active is True
        assert self.dept_service.can_departments_collaborate(dept1.id, dept2.id) is True
        
        # Test deactivate collaboration
        assert hasattr(self.dept_service, 'deactivate_collaboration_agreement')
        updated_agreement = self.dept_service.deactivate_collaboration_agreement(
            agreement.id, test_user.id
        )
        assert updated_agreement.is_active is False
        assert self.dept_service.can_departments_collaborate(dept1.id, dept2.id) is False
        
        # Test reactivate collaboration
        assert hasattr(self.dept_service, 'activate_collaboration_agreement')
        reactivated = self.dept_service.activate_collaboration_agreement(
            agreement.id, test_user.id
        )
        assert reactivated.is_active is True
        assert self.dept_service.can_departments_collaborate(dept1.id, dept2.id) is True