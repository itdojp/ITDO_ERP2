"""Comprehensive Department Workflow Integration Tests."""

import pytest
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError
from app.models.department import Department
from app.models.department_collaboration import DepartmentCollaboration
from app.models.department_task import DepartmentTask
from app.models.task import Task
from app.models.project import Project
from app.models.user import User
from app.schemas.department import DepartmentCreate
from app.services.department import DepartmentService


class TestDepartmentWorkflowIntegration:
    """Test complete department workflow scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = None
        self.test_org = None

    def test_complete_department_lifecycle(self, db_session: Session, test_organization, test_user):
        """Test complete department lifecycle from creation to deletion."""
        self.service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # 1. Create parent department
        parent_data = DepartmentCreate(
            code="PARENT",
            name="Parent Department",
            organization_id=test_organization.id,
            department_type="operational"
        )
        parent_dept = self.service.create_department(parent_data, created_by=test_user.id)
        
        # 2. Create child department
        child_data = DepartmentCreate(
            code="CHILD",
            name="Child Department",
            organization_id=test_organization.id,
            parent_id=parent_dept.id,
            department_type="operational"
        )
        child_dept = self.service.create_department(child_data, created_by=test_user.id)
        
        # 3. Create tasks and assign to departments
        project = Project(
            code="TEST-WF-001",
            name="Workflow Test Project",
            organization_id=test_organization.id,
            owner_id=test_user.id,
            status="active"
        )
        db_session.add(project)
        db_session.flush()
        
        task1 = self._create_test_task(db_session, "Parent Task", project.id)
        task2 = self._create_test_task(db_session, "Child Task", project.id)
        
        # 4. Assign tasks to departments
        self.service.assign_task_to_department(task1.id, parent_dept.id)
        self.service.assign_task_to_department(task2.id, child_dept.id)
        
        # 5. Verify task assignments
        parent_tasks = self.service.get_department_tasks(parent_dept.id)
        child_tasks = self.service.get_department_tasks(child_dept.id)
        
        assert len(parent_tasks) == 1
        assert len(child_tasks) == 1
        assert parent_tasks[0].title == "Parent Task"
        assert child_tasks[0].title == "Child Task"
        
        # 6. Update department structure
        updated_data = DepartmentCreate(
            code="CHILD",
            name="Updated Child Department",
            organization_id=test_organization.id,
            parent_id=parent_dept.id,
            department_type="support"
        )
        
        # 7. Test validation before deletion
        self.service.validate_department_deletion(parent_dept.id)
        
        # 8. Remove tasks before deletion
        self.service.remove_task_from_department(task1.id, parent_dept.id, test_user.id)
        self.service.remove_task_from_department(task2.id, child_dept.id, test_user.id)
        
        # 9. Delete child department first
        success = self.service.delete_department(child_dept.id, deleted_by=test_user.id)
        assert success is True
        
        # 10. Delete parent department
        success = self.service.delete_department(parent_dept.id, deleted_by=test_user.id)
        assert success is True
        
        # 11. Verify departments are soft-deleted
        deleted_parent = self.service.get_department(parent_dept.id)
        deleted_child = self.service.get_department(child_dept.id)
        
        assert deleted_parent.is_deleted is True
        assert deleted_child.is_deleted is True

    def test_department_hierarchy_operations(self, db_session: Session, test_organization, test_user):
        """Test hierarchical department operations."""
        self.service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # Create 3-level hierarchy
        root_dept = self._create_test_department(db_session, "ROOT", "Root Department")
        level1_dept = self._create_test_department(db_session, "L1", "Level 1", parent_id=root_dept.id)
        level2_dept = self._create_test_department(db_session, "L2", "Level 2", parent_id=level1_dept.id)
        
        # Test tree structure
        tree = self.service.get_department_tree(test_organization.id)
        assert len(tree) > 0
        
        # Test sub-department queries
        root_subs = self.service.get_all_sub_departments(root_dept.id)
        assert len(root_subs) == 2  # level1 and level2
        
        direct_subs = self.service.get_direct_sub_departments(root_dept.id)
        assert len(direct_subs) == 1  # only level1
        
        # Test department moving
        # Move level2 to be under root directly
        moved_dept = self.service.move_department(level2_dept.id, root_dept.id)
        assert moved_dept.parent_id == root_dept.id
        
        # Verify hierarchy validation
        validation_result = self.service.validate_department_hierarchy(test_organization.id)
        assert validation_result["is_valid"] is True
        
        # Test hierarchy health status
        health_status = self.service.get_department_health_status(root_dept.id)
        assert health_status["status"] in ["healthy", "warning", "critical", "unhealthy"]

    def test_department_task_delegation_workflow(self, db_session: Session, test_organization, test_user):
        """Test task delegation between departments."""
        self.service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # Create departments
        dept_a = self._create_test_department(db_session, "DEPT_A", "Department A")
        dept_b = self._create_test_department(db_session, "DEPT_B", "Department B")
        
        # Create collaboration agreement
        collaboration = self.service.create_collaboration_agreement(
            department_a_id=dept_a.id,
            department_b_id=dept_b.id,
            collaboration_type="task_sharing",
            description="Task sharing agreement"
        )
        
        # Create project and tasks
        project = Project(
            code="TEST-DEL-001",
            name="Delegation Test Project",
            organization_id=test_organization.id,
            owner_id=test_user.id,
            status="active"
        )
        db_session.add(project)
        db_session.flush()
        
        task1 = self._create_test_task(db_session, "Task to Delegate", project.id)
        task2 = self._create_test_task(db_session, "Another Task", project.id)
        
        # Assign tasks to dept_a
        self.service.assign_task_to_department(task1.id, dept_a.id)
        self.service.assign_task_to_department(task2.id, dept_a.id)
        
        # Delegate task1 to dept_b
        delegation = self.service.delegate_task(
            task_id=task1.id,
            from_department_id=dept_a.id,
            to_department_id=dept_b.id,
            delegated_by=test_user.id,
            notes="Delegating for specialized handling"
        )
        
        # Verify delegation
        assert delegation.assignment_type == "delegated"
        assert delegation.delegated_from_department_id == dept_a.id
        assert delegation.department_id == dept_b.id
        
        # Check task assignments
        dept_a_tasks = self.service.get_department_tasks(dept_a.id)
        dept_b_tasks = self.service.get_department_tasks(dept_b.id)
        
        # dept_a should have 1 task (task2), dept_b should have 1 delegated task
        assert len(dept_a_tasks) == 1
        assert len(dept_b_tasks) == 1
        assert dept_a_tasks[0].title == "Another Task"
        assert dept_b_tasks[0].title == "Task to Delegate"
        
        # Get task statistics
        stats_a = self.service.get_department_task_statistics(dept_a.id)
        stats_b = self.service.get_department_task_statistics(dept_b.id)
        
        assert stats_a["total_tasks"] == 1
        assert stats_b["total_tasks"] == 1

    def test_department_collaboration_management(self, db_session: Session, test_organization, test_user):
        """Test department collaboration management."""
        self.service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # Create departments
        finance_dept = self._create_test_department(db_session, "FINANCE", "Finance Department")
        hr_dept = self._create_test_department(db_session, "HR", "Human Resources")
        it_dept = self._create_test_department(db_session, "IT", "IT Department")
        
        # Create collaboration agreements
        finance_hr_collab = self.service.create_collaboration_agreement(
            department_a_id=finance_dept.id,
            department_b_id=hr_dept.id,
            collaboration_type="project_sharing",
            description="Payroll processing collaboration"
        )
        
        finance_it_collab = self.service.create_collaboration_agreement(
            department_a_id=finance_dept.id,
            department_b_id=it_dept.id,
            collaboration_type="resource_sharing",
            description="Financial system maintenance"
        )
        
        # Test collaboration validation
        can_collaborate = self.service.can_departments_collaborate(finance_dept.id, hr_dept.id)
        assert can_collaborate is True
        
        cannot_collaborate = self.service.can_departments_collaborate(hr_dept.id, it_dept.id)
        assert cannot_collaborate is False  # No direct collaboration
        
        # Get collaboration partners
        finance_partners = self.service.get_collaboration_partners(finance_dept.id)
        assert len(finance_partners) == 2
        
        hr_partners = self.service.get_collaboration_partners(hr_dept.id)
        assert len(hr_partners) == 1
        
        # Test collaboration termination
        success = self.service.terminate_collaboration(finance_hr_collab.id, test_user.id)
        assert success is True
        
        # Verify collaboration is terminated
        updated_partners = self.service.get_collaboration_partners(finance_dept.id)
        assert len(updated_partners) == 1  # Only IT collaboration remains

    def test_department_bulk_operations(self, db_session: Session, test_organization, test_user):
        """Test bulk department operations."""
        self.service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # Create multiple departments
        departments = []
        for i in range(5):
            dept = self._create_test_department(
                db_session, f"BULK_{i}", f"Bulk Department {i}"
            )
            departments.append(dept)
        
        # Test bulk status update
        dept_ids = [dept.id for dept in departments[:3]]
        
        # Deactivate first 3 departments
        results = self.service.bulk_update_department_status(
            department_ids=dept_ids,
            is_active=False,
            updated_by=test_user.id
        )
        
        assert len(results["success"]) == 3
        assert len(results["failed"]) == 0
        assert len(results["skipped"]) == 0
        
        # Verify departments are inactive
        for dept_id in dept_ids:
            dept = self.service.get_department(dept_id)
            assert dept.is_active is False
        
        # Test reactivation
        results = self.service.bulk_update_department_status(
            department_ids=dept_ids,
            is_active=True,
            updated_by=test_user.id
        )
        
        assert len(results["success"]) == 3
        
        # Test display order update
        all_dept_ids = [dept.id for dept in departments]
        self.service.update_display_order(all_dept_ids)
        
        # Verify order is updated
        for i, dept_id in enumerate(all_dept_ids):
            dept = self.service.get_department(dept_id)
            assert dept.display_order == i

    def test_department_permission_inheritance(self, db_session: Session, test_organization, test_user):
        """Test permission inheritance through department hierarchy."""
        self.service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # Create hierarchy
        root_dept = self._create_test_department(db_session, "ROOT", "Root Department")
        child_dept = self._create_test_department(db_session, "CHILD", "Child Department", parent_id=root_dept.id)
        grandchild_dept = self._create_test_department(db_session, "GRANDCHILD", "Grandchild Department", parent_id=child_dept.id)
        
        # Test permission inheritance chain
        inheritance_chain = self.service.get_permission_inheritance_chain(grandchild_dept.id)
        assert len(inheritance_chain) == 3  # grandchild, child, root
        
        # Test effective permissions
        effective_permissions = self.service.get_user_effective_permissions(test_user.id, grandchild_dept.id)
        assert isinstance(effective_permissions, list)
        
        # Test permission validation
        has_permission = self.service.user_has_permission(
            test_user.id, "departments.view", test_organization.id
        )
        assert isinstance(has_permission, bool)

    def test_department_cascade_deletion(self, db_session: Session, test_organization, test_user):
        """Test cascade deletion of departments and task cleanup."""
        self.service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # Create hierarchy with tasks
        parent_dept = self._create_test_department(db_session, "PARENT", "Parent Department")
        child_dept = self._create_test_department(db_session, "CHILD", "Child Department", parent_id=parent_dept.id)
        
        # Create tasks
        project = Project(
            code="TEST-CAS-001",
            name="Cascade Test Project",
            organization_id=test_organization.id,
            owner_id=test_user.id,
            status="active"
        )
        db_session.add(project)
        db_session.flush()
        
        parent_task = self._create_test_task(db_session, "Parent Task", project.id)
        child_task = self._create_test_task(db_session, "Child Task", project.id)
        
        # Assign tasks
        self.service.assign_task_to_department(parent_task.id, parent_dept.id)
        self.service.assign_task_to_department(child_task.id, child_dept.id)
        
        # Test cascade deletion
        success = self.service.cascade_delete_department(parent_dept.id, test_user.id)
        assert success is True
        
        # Verify all departments are deleted
        deleted_parent = self.service.get_department(parent_dept.id)
        deleted_child = self.service.get_department(child_dept.id)
        
        assert deleted_parent.is_deleted is True
        assert deleted_child.is_deleted is True
        
        # Verify task assignments are deactivated
        parent_assignments = self.service.get_task_assignments_for_department(parent_dept.id)
        child_assignments = self.service.get_task_assignments_for_department(child_dept.id)
        
        assert len(parent_assignments) == 0
        assert len(child_assignments) == 0

    def test_department_promotion_workflow(self, db_session: Session, test_organization, test_user):
        """Test department promotion when parent is deleted."""
        self.service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # Create hierarchy
        grandparent_dept = self._create_test_department(db_session, "GRANDPARENT", "Grandparent Department")
        parent_dept = self._create_test_department(db_session, "PARENT", "Parent Department", parent_id=grandparent_dept.id)
        child1_dept = self._create_test_department(db_session, "CHILD1", "Child 1", parent_id=parent_dept.id)
        child2_dept = self._create_test_department(db_session, "CHILD2", "Child 2", parent_id=parent_dept.id)
        
        # Promote children when parent is deleted
        promoted_depts = self.service.promote_sub_departments(parent_dept.id, test_user.id)
        
        assert len(promoted_depts) == 2
        
        # Verify children are now under grandparent
        updated_child1 = self.service.get_department(child1_dept.id)
        updated_child2 = self.service.get_department(child2_dept.id)
        
        assert updated_child1.parent_id == grandparent_dept.id
        assert updated_child2.parent_id == grandparent_dept.id
        
        # Now delete parent
        success = self.service.delete_department(parent_dept.id, deleted_by=test_user.id)
        assert success is True
        
        # Verify hierarchy is maintained
        validation_result = self.service.validate_department_hierarchy(test_organization.id)
        assert validation_result["is_valid"] is True

    def _create_test_department(
        self, db_session: Session, code: str, name: str, parent_id: int = None
    ) -> Department:
        """Helper to create test department."""
        data = DepartmentCreate(
            code=code,
            name=name,
            organization_id=self.test_org.id,
            parent_id=parent_id,
            department_type="operational"
        )
        return self.service.create_department(data)

    def _create_test_task(
        self, 
        db_session: Session, 
        title: str, 
        project_id: int, 
        status: str = "pending",
        priority: str = "medium"
    ) -> Task:
        """Helper to create test task."""
        task = Task(
            title=title,
            description=f"Description for {title}",
            status=status,
            priority=priority,
            project_id=project_id,
            reporter_id=1,
        )
        db_session.add(task)
        db_session.flush()
        return task