"""Tests for Department-Task Management integration."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError
from app.models.department import Department
from app.models.department_task import DepartmentTask
from app.models.task import Task
from app.models.project import Project
from app.schemas.department import DepartmentCreate
from app.services.department import DepartmentService


class TestDepartmentTaskIntegration:
    """Test department task management integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = None  # Will be initialized with db session
        self.test_org = None  # Will store test organization

    def test_assign_task_to_department(self, db_session: Session, test_organization, test_user):
        """Test assigning a task to a department."""
        self.service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # Create department
        dept = self._create_test_department(db_session, "IT", "IT Department")
        
        # Create a test project and task
        project = Project(
            code="TEST-001",
            name="Test Project",
            organization_id=test_organization.id,
            owner_id=test_user.id,
            status="active"
        )
        db_session.add(project)
        db_session.flush()
        
        task = Task(
            title="Test Task",
            description="A test task",
            status="pending",
            priority="medium",
            project_id=project.id,
            reporter_id=test_user.id,
        )
        db_session.add(task)
        db_session.flush()
        
        # Assign task to department
        assignment = self.service.assign_task_to_department(
            task_id=task.id,
            department_id=dept.id,
            assignment_type="department",
            visibility_scope="department",
            notes="Initial assignment"
        )
        
        assert assignment.task_id == task.id
        assert assignment.department_id == dept.id
        assert assignment.assignment_type == "department"
        assert assignment.visibility_scope == "department"
        assert assignment.is_active is True

    def test_get_department_tasks(self, db_session: Session, test_organization):
        """Test getting tasks assigned to a department."""
        self.service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # Create departments
        parent_dept = self._create_test_department(db_session, "PARENT", "Parent Department")
        child_dept = self._create_test_department(db_session, "CHILD", "Child Department", parent_id=parent_dept.id)
        
        # Create project and tasks
        project = Project(
            code="TEST-002",
            name="Test Project",
            organization_id=test_organization.id,
            owner_id=1,
            status="active"
        )
        db_session.add(project)
        db_session.flush()
        
        task1 = self._create_test_task(db_session, "Task 1", project.id)
        task2 = self._create_test_task(db_session, "Task 2", project.id)
        task3 = self._create_test_task(db_session, "Task 3", project.id)
        
        # Assign tasks
        self.service.assign_task_to_department(task1.id, parent_dept.id, "department", "department")
        self.service.assign_task_to_department(task2.id, child_dept.id, "department", "department")
        self.service.assign_task_to_department(task3.id, parent_dept.id, "department", "organization")
        
        # Get department tasks
        parent_tasks = self.service.get_department_tasks(parent_dept.id, include_inherited=False)
        child_tasks = self.service.get_department_tasks(child_dept.id, include_inherited=True)
        
        # Parent should have 2 direct tasks
        assert len(parent_tasks) == 2
        
        # Child should have 1 direct + inherited tasks from parent
        assert len(child_tasks) >= 1  # At least the direct one

    def test_delegate_task_between_departments(self, db_session: Session, test_organization):
        """Test delegating a task from one department to another."""
        self.service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # Create departments with collaboration
        dept_a = self._create_test_department(db_session, "DEPT_A", "Department A")
        dept_b = self._create_test_department(db_session, "DEPT_B", "Department B")
        
        # Create collaboration
        collaboration = self.service.create_collaboration_agreement(
            department_a_id=dept_a.id,
            department_b_id=dept_b.id,
            collaboration_type="project_sharing",
            description="Test collaboration"
        )
        
        # Create task and assign to dept_a
        project = Project(
            code="TEST-003",
            name="Test Project",
            organization_id=test_organization.id,
            owner_id=1,
            status="active"
        )
        db_session.add(project)
        db_session.flush()
        
        task = self._create_test_task(db_session, "Task to Delegate", project.id)
        
        # Assign to dept_a first
        self.service.assign_task_to_department(task.id, dept_a.id)
        
        # Delegate to dept_b
        delegation = self.service.delegate_task(
            task_id=task.id,
            from_department_id=dept_a.id,
            to_department_id=dept_b.id,
            delegated_by=1,
            notes="Delegating for better expertise"
        )
        
        assert delegation.assignment_type == "delegated"
        assert delegation.delegated_from_department_id == dept_a.id
        assert delegation.department_id == dept_b.id

    def test_department_task_statistics(self, db_session: Session, test_organization):
        """Test getting task statistics for a department."""
        self.service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # Create department
        dept = self._create_test_department(db_session, "STATS", "Statistics Department")
        
        # Create project and tasks with different statuses and priorities
        project = Project(
            code="TEST-004",
            name="Stats Project",
            organization_id=test_organization.id,
            owner_id=1,
            status="active"
        )
        db_session.add(project)
        db_session.flush()
        
        # Create tasks with different statuses and priorities
        task1 = self._create_test_task(db_session, "High Priority", project.id, status="pending", priority="high")
        task2 = self._create_test_task(db_session, "Medium Priority", project.id, status="in_progress", priority="medium")
        task3 = self._create_test_task(db_session, "Completed Task", project.id, status="completed", priority="low")
        task4 = self._create_test_task(db_session, "Overdue Task", project.id, status="pending", priority="high")
        
        # Make task4 overdue
        task4.due_date = datetime.utcnow() - timedelta(days=1)
        db_session.commit()
        
        # Assign all tasks to department
        self.service.assign_task_to_department(task1.id, dept.id)
        self.service.assign_task_to_department(task2.id, dept.id)
        self.service.assign_task_to_department(task3.id, dept.id)
        self.service.assign_task_to_department(task4.id, dept.id)
        
        # Get statistics
        stats = self.service.get_department_task_statistics(dept.id)
        
        assert stats["total_tasks"] == 4
        assert stats["by_status"]["pending"] == 2
        assert stats["by_status"]["in_progress"] == 1
        assert stats["by_status"]["completed"] == 1
        assert stats["by_priority"]["high"] == 2
        assert stats["by_priority"]["medium"] == 1
        assert stats["by_priority"]["low"] == 1
        assert stats["overdue_tasks"] == 1

    def test_task_inheritance_in_hierarchy(self, db_session: Session, test_organization):
        """Test task inheritance through department hierarchy."""
        self.service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # Create hierarchy: Root -> Level1 -> Level2
        root = self._create_test_department(db_session, "ROOT", "Root Department")
        level1 = self._create_test_department(db_session, "L1", "Level 1", parent_id=root.id)
        level2 = self._create_test_department(db_session, "L2", "Level 2", parent_id=level1.id)
        
        # Create project and task
        project = Project(
            code="TEST-005",
            name="Hierarchy Project",
            organization_id=test_organization.id,
            owner_id=1,
            status="active"
        )
        db_session.add(project)
        db_session.flush()
        
        task = self._create_test_task(db_session, "Inheritable Task", project.id)
        
        # Assign task to root with organization visibility
        self.service.assign_task_to_department(
            task.id, root.id, "department", "organization"
        )
        
        # Level2 should inherit the task if inheritance is enabled
        level2_tasks = self.service.get_department_tasks(level2.id, include_inherited=True)
        
        # Should have the inherited task
        task_titles = [t.title for t in level2_tasks]
        assert "Inheritable Task" in task_titles

    def test_remove_task_from_department(self, db_session: Session, test_organization):
        """Test removing a task assignment from a department."""
        self.service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # Create department and task
        dept = self._create_test_department(db_session, "REMOVE", "Remove Department")
        
        project = Project(
            code="TEST-006",
            name="Remove Project",
            organization_id=test_organization.id,
            owner_id=1,
            status="active"
        )
        db_session.add(project)
        db_session.flush()
        
        task = self._create_test_task(db_session, "Task to Remove", project.id)
        
        # Assign task
        self.service.assign_task_to_department(task.id, dept.id)
        
        # Verify assignment exists
        assignments_before = self.service.get_task_assignments_for_department(dept.id)
        assert len(assignments_before) == 1
        
        # Remove task
        success = self.service.remove_task_from_department(task.id, dept.id)
        assert success is True
        
        # Verify assignment is removed
        assignments_after = self.service.get_task_assignments_for_department(dept.id)
        assert len(assignments_after) == 0

    def test_delegation_requires_collaboration_or_hierarchy(self, db_session: Session, test_organization):
        """Test that delegation requires collaboration agreement or hierarchy relationship."""
        self.service = DepartmentService(db_session)
        self.test_org = test_organization
        
        # Create two unrelated departments
        dept_a = self._create_test_department(db_session, "UNREL_A", "Unrelated A")
        dept_b = self._create_test_department(db_session, "UNREL_B", "Unrelated B")
        
        # Create task and assign to dept_a
        project = Project(
            code="TEST-007",
            name="Unrelated Project",
            organization_id=test_organization.id,
            owner_id=1,
            status="active"
        )
        db_session.add(project)
        db_session.flush()
        
        task = self._create_test_task(db_session, "Unrelated Task", project.id)
        self.service.assign_task_to_department(task.id, dept_a.id)
        
        # Try to delegate without collaboration - should fail
        with pytest.raises(BusinessLogicError, match="collaboration agreement"):
            self.service.delegate_task(
                task_id=task.id,
                from_department_id=dept_a.id,
                to_department_id=dept_b.id,
                delegated_by=1
            )

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
            reporter_id=1,  # Assuming user ID 1 exists
        )
        db_session.add(task)
        db_session.flush()
        return task