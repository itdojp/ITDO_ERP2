"""Tests for Department hierarchical structure management."""

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError
from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.services.department import DepartmentService


class TestDepartmentHierarchy:
    """Test department hierarchical structure management."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = None  # Will be initialized with db session
        self.test_org = None  # Will store test organization

    def test_create_department_with_path_depth(self, db_session: Session, test_organization):
        """Test creating department automatically sets path and depth."""
        self.service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # Create root department
        root_data = DepartmentCreate(
            code="HQ",
            name="Headquarters",
            organization_id=test_organization.id,
        )
        root = self.service.create_department(root_data)
        
        assert root.path == str(root.id)
        assert root.depth == 0
        
        # Create child department
        child_data = DepartmentCreate(
            code="IT",
            name="IT Department",
            organization_id=test_organization.id,
            parent_id=root.id,
        )
        child = self.service.create_department(child_data)
        
        assert child.path == f"{root.id}.{child.id}"
        assert child.depth == 1
        
        # Create grandchild department
        grandchild_data = DepartmentCreate(
            code="DEV",
            name="Development Team",
            organization_id=test_organization.id,
            parent_id=child.id,
        )
        grandchild = self.service.create_department(grandchild_data)
        
        assert grandchild.path == f"{root.id}.{child.id}.{grandchild.id}"
        assert grandchild.depth == 2

    def test_move_department_updates_hierarchy(self, db_session: Session, test_organization):
        """Test moving department updates path and depth for entire subtree."""
        self.service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # Create departments
        root1 = self._create_test_department(db_session, "ROOT1", "Root 1")
        root2 = self._create_test_department(db_session, "ROOT2", "Root 2")
        child = self._create_test_department(db_session, "CHILD", "Child", parent_id=root1.id)
        grandchild = self._create_test_department(
            db_session, "GCHILD", "Grandchild", parent_id=child.id
        )
        
        # Move child from root1 to root2
        moved_child = self.service.move_department(child.id, root2.id)
        
        # Refresh to get updated values
        db_session.refresh(child)
        db_session.refresh(grandchild)
        
        # Check updated paths
        assert child.path == f"{root2.id}.{child.id}"
        assert child.depth == 1
        assert grandchild.path == f"{root2.id}.{child.id}.{grandchild.id}"
        assert grandchild.depth == 2

    def test_circular_reference_prevention(self, db_session: Session, test_organization):
        """Test that circular references are prevented."""
        self.service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # Create hierarchy
        parent = self._create_test_department(db_session, "PARENT", "Parent")
        child = self._create_test_department(db_session, "CHILD", "Child", parent_id=parent.id)
        grandchild = self._create_test_department(
            db_session, "GCHILD", "Grandchild", parent_id=child.id
        )
        
        # Try to make parent a child of grandchild (circular reference)
        with pytest.raises(BusinessLogicError, match="circular reference"):
            self.service.move_department(parent.id, grandchild.id)
        
        # Try to make child a child of grandchild (circular reference)
        with pytest.raises(BusinessLogicError, match="circular reference"):
            self.service.move_department(child.id, grandchild.id)
        
        # Try to make department its own parent
        with pytest.raises(BusinessLogicError, match="cannot be its own parent"):
            self.service.move_department(child.id, child.id)

    def test_get_ancestors_path(self, db_session: Session, test_organization):
        """Test getting all ancestors of a department."""
        self.service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # Create hierarchy
        root = self._create_test_department(db_session, "ROOT", "Root")
        level1 = self._create_test_department(db_session, "L1", "Level 1", parent_id=root.id)
        level2 = self._create_test_department(db_session, "L2", "Level 2", parent_id=level1.id)
        level3 = self._create_test_department(db_session, "L3", "Level 3", parent_id=level2.id)
        
        # Get ancestors
        ancestors = self.service.get_ancestors(level3.id)
        
        assert len(ancestors) == 3
        assert ancestors[0].id == root.id
        assert ancestors[1].id == level1.id
        assert ancestors[2].id == level2.id

    def test_get_descendants_recursive(self, db_session: Session, test_organization):
        """Test getting all descendants recursively."""
        self.service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # Create hierarchy
        root = self._create_test_department(db_session, "ROOT", "Root")
        child1 = self._create_test_department(db_session, "C1", "Child 1", parent_id=root.id)
        child2 = self._create_test_department(db_session, "C2", "Child 2", parent_id=root.id)
        grandchild1 = self._create_test_department(
            db_session, "GC1", "Grandchild 1", parent_id=child1.id
        )
        grandchild2 = self._create_test_department(
            db_session, "GC2", "Grandchild 2", parent_id=child2.id
        )
        
        # Get all descendants
        descendants = self.service.get_descendants(root.id, recursive=True)
        
        assert len(descendants) == 4
        descendant_ids = {d.id for d in descendants}
        assert child1.id in descendant_ids
        assert child2.id in descendant_ids
        assert grandchild1.id in descendant_ids
        assert grandchild2.id in descendant_ids

    def test_delete_department_with_children_fails(self, db_session: Session, test_organization):
        """Test that deleting department with active children fails."""
        self.service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # Create hierarchy
        parent = self._create_test_department(db_session, "PARENT", "Parent")
        child = self._create_test_department(db_session, "CHILD", "Child", parent_id=parent.id)
        
        # Try to delete parent with active child
        with pytest.raises(BusinessLogicError, match="has active sub-departments"):
            self.service.delete_department(parent.id)
        
        # Should be able to delete child
        assert self.service.delete_department(child.id) is True
        
        # Now should be able to delete parent
        assert self.service.delete_department(parent.id) is True

    def test_max_depth_validation(self, db_session: Session, test_organization):
        """Test maximum depth validation (e.g., max 5 levels)."""
        self.service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # Create 5 levels (0-4)
        current_parent = None
        for i in range(5):
            dept = self._create_test_department(
                db_session, f"L{i}", f"Level {i}", parent_id=current_parent
            )
            current_parent = dept.id
        
        # Try to create 6th level (depth 5)
        with pytest.raises(BusinessLogicError, match="maximum depth"):
            self._create_test_department(
                db_session, "L5", "Level 5", parent_id=current_parent
            )

    def test_path_based_queries(self, db_session: Session, test_organization):
        """Test efficient path-based queries."""
        self.service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # Create hierarchy
        root = self._create_test_department(db_session, "ROOT", "Root")
        branch1 = self._create_test_department(db_session, "B1", "Branch 1", parent_id=root.id)
        branch2 = self._create_test_department(db_session, "B2", "Branch 2", parent_id=root.id)
        leaf1 = self._create_test_department(db_session, "L1", "Leaf 1", parent_id=branch1.id)
        leaf2 = self._create_test_department(db_session, "L2", "Leaf 2", parent_id=branch2.id)
        
        # Get all departments under branch1
        branch1_tree = self.service.get_subtree(branch1.id)
        assert len(branch1_tree) == 2  # branch1 + leaf1
        
        # Get all departments at depth 2
        depth2_depts = self.service.get_departments_at_depth(2, self.test_org.id)
        assert len(depth2_depts) == 2  # leaf1 and leaf2

    def _create_test_department(
        self, db_session: Session, code: str, name: str, parent_id: int = None
    ) -> Department:
        """Helper to create test department."""
        data = DepartmentCreate(
            code=code,
            name=name,
            organization_id=self.test_org.id,
            parent_id=parent_id,
        )
        return self.service.create_department(data)