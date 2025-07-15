"""Unit tests for Task Service Department Integration functionality."""

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import NotFound
from app.models.organization import Organization
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskPriority
from app.services.task import TaskService
from tests.factories import DepartmentFactory


class TestTaskServiceDepartmentIntegration:
    """Unit tests for Task Service department integration features."""

    def test_create_department_task_success(
        self,
        db_session: Session,
        test_user: User,
        test_organization: Organization,
    ):
        """Test creating a task assigned to a department."""
        # Setup
        service = TaskService()

        # Create department using factory
        department = DepartmentFactory.create_with_organization(
            db_session, test_organization, name="Engineering", code="ENG"
        )

        # Create project
        project = Project(
            name="Test Project",
            code="TEST-PROJ",
            organization_id=test_organization.id,
            owner_id=test_user.id,
        )
        db_session.add(project)
        db_session.commit()

        # Prepare task data
        task_data = TaskCreate(
            title="Department Task",
            description="Task for Engineering department",
            project_id=project.id,
            priority=TaskPriority.HIGH,
        )

        # Execute: Create department task
        result = service.create_department_task(
            task_data=task_data,
            user=test_user,
            db=db_session,
            department_id=department.id,
        )

        # Verify: Task response
        assert result.title == "Department Task"
        assert result.description == "Task for Engineering department"
        assert result.department_id == department.id
        assert result.department_visibility == "department_hierarchy"
        assert result.priority == TaskPriority.HIGH
        assert result.status.value == "not_started"

        # Verify: Database record
        task = db_session.query(Task).filter(Task.id == result.id).first()
        assert task is not None
        assert task.title == "Department Task"
        assert task.department_id == department.id
        assert task.department_visibility == "department_hierarchy"
        assert task.project_id == project.id
        assert task.reporter_id == test_user.id

    def test_create_department_task_nonexistent_department(
        self,
        db_session: Session,
        test_user: User,
        test_organization: Organization,
    ):
        """Test creating task with non-existent department fails."""
        # Setup
        service = TaskService()

        # Create project
        project = Project(
            name="Test Project",
            code="TEST-PROJ",
            organization_id=test_organization.id,
            owner_id=test_user.id,
        )
        db_session.add(project)
        db_session.commit()

        # Prepare task data
        task_data = TaskCreate(
            title="Department Task",
            project_id=project.id,
            priority=TaskPriority.MEDIUM,
        )

        # Execute & Verify: Should raise NotFound
        with pytest.raises(NotFound, match="Department not found"):
            service.create_department_task(
                task_data=task_data,
                user=test_user,
                db=db_session,
                department_id=999,  # Non-existent department
            )

    def test_create_department_task_nonexistent_project(
        self,
        db_session: Session,
        test_user: User,
        test_organization: Organization,
    ):
        """Test creating department task with non-existent project fails."""
        # Setup
        service = TaskService()

        # Create department
        department = DepartmentFactory.create_with_organization(
            db_session, test_organization, name="Engineering", code="ENG"
        )

        # Prepare task data with non-existent project
        task_data = TaskCreate(
            title="Department Task",
            project_id=999,  # Non-existent project
            priority=TaskPriority.MEDIUM,
        )

        # Execute & Verify: Should raise NotFound
        with pytest.raises(NotFound, match="Project not found"):
            service.create_department_task(
                task_data=task_data,
                user=test_user,
                db=db_session,
                department_id=department.id,
            )

    def test_assign_task_to_department_success(
        self,
        db_session: Session,
        test_user: User,
        test_organization: Organization,
    ):
        """Test assigning an existing task to a department."""
        # Setup
        service = TaskService()

        # Create department
        department = DepartmentFactory.create_with_organization(
            db_session, test_organization, name="Marketing", code="MKT"
        )

        # Create project and task
        project = Project(
            name="Test Project",
            code="TEST-PROJ",
            organization_id=test_organization.id,
            owner_id=test_user.id,
        )
        db_session.add(project)
        db_session.commit()

        task = Task(
            title="Unassigned Task",
            project_id=project.id,
            reporter_id=test_user.id,
            status="not_started",
            priority="medium",
            created_by=test_user.id,
        )
        db_session.add(task)
        db_session.commit()

        # Execute: Assign to department
        result = service.assign_task_to_department(
            task_id=task.id,
            department_id=department.id,
            user=test_user,
            db=db_session,
        )

        # Verify: Task response
        assert result.department_id == department.id
        assert result.department_visibility == "department_hierarchy"

        # Verify: Database record
        db_session.refresh(task)
        assert task.department_id == department.id
        assert task.department_visibility == "department_hierarchy"

    def test_assign_task_to_nonexistent_department(
        self,
        db_session: Session,
        test_user: User,
        test_organization: Organization,
    ):
        """Test assigning task to non-existent department fails."""
        # Setup
        service = TaskService()

        # Create project and task
        project = Project(
            name="Test Project",
            code="TEST-PROJ",
            organization_id=test_organization.id,
            owner_id=test_user.id,
        )
        db_session.add(project)
        db_session.commit()

        task = Task(
            title="Test Task",
            project_id=project.id,
            reporter_id=test_user.id,
            status="not_started",
            priority="medium",
            created_by=test_user.id,
        )
        db_session.add(task)
        db_session.commit()

        # Execute & Verify: Should raise NotFound
        with pytest.raises(NotFound, match="Department not found"):
            service.assign_task_to_department(
                task_id=task.id,
                department_id=999,  # Non-existent department
                user=test_user,
                db=db_session,
            )

    def test_get_department_tasks_basic(
        self,
        db_session: Session,
        test_user: User,
        test_organization: Organization,
    ):
        """Test retrieving tasks for a department."""
        # Setup
        service = TaskService()

        # Create department
        department = DepartmentFactory.create_with_organization(
            db_session, test_organization, name="Sales", code="SALES"
        )

        # Create project
        project = Project(
            name="Sales Project",
            code="SALES-PROJ",
            organization_id=test_organization.id,
            owner_id=test_user.id,
        )
        db_session.add(project)
        db_session.commit()

        # Create department task
        task = Task(
            title="Sales Task",
            project_id=project.id,
            reporter_id=test_user.id,
            department_id=department.id,
            department_visibility="department_hierarchy",
            status="in_progress",
            priority="high",
            created_by=test_user.id,
        )
        db_session.add(task)
        db_session.commit()

        # Execute: Get department tasks
        result = service.get_department_tasks(
            department_id=department.id,
            user=test_user,
            db=db_session,
            include_subdepartments=False,
        )

        # Verify: Response
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].title == "Sales Task"
        assert result.items[0].department_id == department.id

    def test_get_department_tasks_nonexistent_department(
        self,
        db_session: Session,
        test_user: User,
    ):
        """Test getting tasks for non-existent department fails."""
        # Setup
        service = TaskService()

        # Execute & Verify: Should raise NotFound
        with pytest.raises(NotFound, match="Department not found"):
            service.get_department_tasks(
                department_id=999,  # Non-existent department
                user=test_user,
                db=db_session,
            )
