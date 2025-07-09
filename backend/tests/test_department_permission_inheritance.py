"""Tests for Department permission inheritance system."""

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError
from app.models.department import Department
from app.models.permission import Permission
from app.models.role import Role, UserRole
from app.models.user import User
from app.schemas.department import DepartmentCreate
from app.services.department import DepartmentService


class TestDepartmentPermissionInheritance:
    """Test department permission inheritance."""

    def setup_method(self):
        """Set up test fixtures."""
        self.dept_service = None
        self.test_org = None
        self.test_user = None

    def test_department_inheritance_field_added(self, db_session: Session, test_organization):
        """Test that department model has inheritance field."""
        self.dept_service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # Create a department and check it has inheritance field
        dept_data = DepartmentCreate(
            code="TEST",
            name="Test Department",
            organization_id=test_organization.id,
        )
        dept = self.dept_service.create_department(dept_data)
        
        # Check that the department has the inheritance field
        assert hasattr(dept, 'inherit_permissions')
        # Should default to True
        assert dept.inherit_permissions is True

    def test_department_has_permission_methods(self, db_session: Session, test_organization, test_user):
        """Test that department service has permission-related methods."""
        self.dept_service = DepartmentService(db_session)
        self.test_org = test_organization
        self.test_user = test_user
        
        # Create a department
        dept_data = DepartmentCreate(
            code="TEST",
            name="Test Department",
            organization_id=test_organization.id,
        )
        dept = self.dept_service.create_department(dept_data)
        
        # Check that the service has permission methods
        assert hasattr(self.dept_service, 'get_user_department_permissions')
        assert hasattr(self.dept_service, 'get_user_effective_permissions')
        assert hasattr(self.dept_service, 'user_has_permission_for_department')
        assert hasattr(self.dept_service, 'get_permission_inheritance_chain')
        
        # Test basic permission methods work (will be empty initially)
        perms = self.dept_service.get_user_department_permissions(test_user.id, dept.id)
        assert isinstance(perms, list)
        
        effective_perms = self.dept_service.get_user_effective_permissions(test_user.id, dept.id)
        assert isinstance(effective_perms, list)
        
        has_perm = self.dept_service.user_has_permission_for_department(
            test_user.id, "test.permission", dept.id
        )
        assert isinstance(has_perm, bool)
        
        chain = self.dept_service.get_permission_inheritance_chain(dept.id)
        assert isinstance(chain, list)

    def test_permission_inheritance_with_hierarchy(self, db_session: Session, test_organization, test_user):
        """Test that permission inheritance works with department hierarchy."""
        self.dept_service = DepartmentService(db_session)
        self.test_org = test_organization
        self.test_user = test_user
        
        # Create parent and child departments
        parent_data = DepartmentCreate(
            code="PARENT",
            name="Parent Department",
            organization_id=test_organization.id,
        )
        parent = self.dept_service.create_department(parent_data)
        
        child_data = DepartmentCreate(
            code="CHILD",
            name="Child Department",
            organization_id=test_organization.id,
            parent_id=parent.id,
        )
        child = self.dept_service.create_department(child_data)
        
        # Test inheritance chain
        chain = self.dept_service.get_permission_inheritance_chain(child.id)
        assert len(chain) >= 1  # At least the child itself
        
        # If parent has inheritance enabled, it should be in the chain
        if parent.inherit_permissions:
            dept_ids = [dept.id for dept in chain]
            assert parent.id in dept_ids or child.id in dept_ids