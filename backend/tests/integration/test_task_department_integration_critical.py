"""CRITICAL: Task-Department Integration Tests for Phase 3."""

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.organization import Organization
from app.models.project import Project
from app.models.task import Task
from app.models.user import User


@pytest.mark.asyncio
class TestCriticalTaskDepartmentIntegration:
    """Critical integration tests for Task-Department functionality."""

    async def test_create_task_in_department(
        self, client: AsyncClient, db_session: Session, test_user: User, 
        test_organization: Organization
    ):
        """CRITICAL: Test creating a task assigned to a department."""
        # Create department
        department = Department(
            name="Engineering",
            code="ENG",
            organization_id=test_organization.id,
            path="1",
            depth=0,
        )
        db_session.add(department)

        # Create project
        project = Project(
            name="Test Project",
            code="TEST-PROJ",
            organization_id=test_organization.id,
            manager_id=test_user.id,
        )
        db_session.add(project)
        db_session.commit()

        # Create auth headers
        from app.core.security import create_access_token
        token = create_access_token(
            data={"sub": str(test_user.id), "email": test_user.email}
        )
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Test data
        task_data = {
            "title": "Department Task",
            "description": "Task for Engineering department",
            "project_id": project.id,
            "priority": "high",
        }

        # Create department task
        response = await client.post(
            f"/api/v1/tasks/department/{department.id}",
            json=task_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        task_response = response.json()
        
        # Verify department assignment
        assert task_response["department_id"] == department.id
        assert task_response["department_visibility"] == "department_hierarchy"
        assert task_response["department"]["name"] == "Engineering"
        assert task_response["department"]["code"] == "ENG"

        # Verify in database
        task = db_session.query(Task).filter(Task.id == task_response["id"]).first()
        assert task is not None
        assert task.department_id == department.id
        assert task.department_visibility == "department_hierarchy"

    async def test_get_department_tasks_with_hierarchy(
        self, client: AsyncClient, db_session: Session, test_user: User,
        test_organization: Organization
    ):
        """CRITICAL: Test retrieving department tasks with hierarchical support."""
        # Create parent department
        parent_dept = Department(
            name="Technology",
            code="TECH",
            organization_id=test_organization.id,
            path="1",
            depth=0,
        )
        db_session.add(parent_dept)
        db_session.flush()

        # Create child department
        child_dept = Department(
            name="Software Engineering",
            code="SE",
            organization_id=test_organization.id,
            parent_id=parent_dept.id,
            path=f"{parent_dept.path}.{parent_dept.id}",
            depth=1,
        )
        db_session.add(child_dept)

        # Create project
        project = Project(
            name="Test Project",
            code="TEST-PROJ",
            organization_id=test_organization.id,
            manager_id=test_user.id,
        )
        db_session.add(project)
        db_session.commit()

        # Create tasks in both departments
        parent_task = Task(
            title="Parent Department Task",
            description="Task in parent department",
            project_id=project.id,
            reporter_id=test_user.id,
            department_id=parent_dept.id,
            department_visibility="department_hierarchy",
            status="not_started",
            priority="medium",
            created_by=test_user.id,
        )
        
        child_task = Task(
            title="Child Department Task",
            description="Task in child department",
            project_id=project.id,
            reporter_id=test_user.id,
            department_id=child_dept.id,
            department_visibility="department_hierarchy",
            status="not_started",
            priority="high",
            created_by=test_user.id,
        )
        
        db_session.add_all([parent_task, child_task])
        db_session.commit()

        # Create auth headers
        from app.core.security import create_access_token
        token = create_access_token(
            data={"sub": str(test_user.id), "email": test_user.email}
        )
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Test: Get parent department tasks (should include child department tasks)
        response = await client.get(
            f"/api/v1/tasks/department/{parent_dept.id}?include_subdepartments=true",
            headers=auth_headers,
        )

        assert response.status_code == 200
        task_list = response.json()
        
        # Should get both parent and child tasks
        assert task_list["total"] == 2
        assert len(task_list["items"]) == 2
        
        # Verify task details
        task_titles = [task["title"] for task in task_list["items"]]
        assert "Parent Department Task" in task_titles
        assert "Child Department Task" in task_titles

        # Test: Get only parent department tasks (exclude subdepartments)
        response = await client.get(
            f"/api/v1/tasks/department/{parent_dept.id}?include_subdepartments=false",
            headers=auth_headers,
        )

        assert response.status_code == 200
        task_list = response.json()
        
        # Should get only parent task
        assert task_list["total"] == 1
        assert len(task_list["items"]) == 1
        assert task_list["items"][0]["title"] == "Parent Department Task"

    async def test_assign_task_to_department(
        self, client: AsyncClient, db_session: Session, test_user: User,
        test_organization: Organization
    ):
        """CRITICAL: Test assigning an existing task to a department."""
        # Create department
        department = Department(
            name="Marketing",
            code="MKT",
            organization_id=test_organization.id,
            path="1",
            depth=0,
        )
        db_session.add(department)

        # Create project
        project = Project(
            name="Test Project",
            code="TEST-PROJ",
            organization_id=test_organization.id,
            manager_id=test_user.id,
        )
        db_session.add(project)

        # Create task without department
        task = Task(
            title="Unassigned Task",
            description="Task without department",
            project_id=project.id,
            reporter_id=test_user.id,
            status="not_started",
            priority="medium",
            created_by=test_user.id,
        )
        db_session.add(task)
        db_session.commit()

        # Create auth headers
        from app.core.security import create_access_token
        token = create_access_token(
            data={"sub": str(test_user.id), "email": test_user.email}
        )
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Assign task to department
        response = await client.put(
            f"/api/v1/tasks/{task.id}/assign-department/{department.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        updated_task = response.json()

        # Verify assignment
        assert updated_task["department_id"] == department.id
        assert updated_task["department_visibility"] == "department_hierarchy"
        assert updated_task["department"]["name"] == "Marketing"

        # Verify in database
        db_session.refresh(task)
        assert task.department_id == department.id
        assert task.department_visibility == "department_hierarchy"

    async def test_department_tasks_via_department_endpoint(
        self, client: AsyncClient, db_session: Session, test_user: User,
        test_organization: Organization
    ):
        """CRITICAL: Test accessing department tasks via department endpoint."""
        # Create department
        department = Department(
            name="Sales",
            code="SALES",
            organization_id=test_organization.id,
            path="1",
            depth=0,
        )
        db_session.add(department)

        # Create project
        project = Project(
            name="Sales Project",
            code="SALES-PROJ",
            organization_id=test_organization.id,
            manager_id=test_user.id,
        )
        db_session.add(project)

        # Create department task
        task = Task(
            title="Sales Task",
            description="Important sales task",
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

        # Create auth headers
        from app.core.security import create_access_token
        token = create_access_token(
            data={"sub": str(test_user.id), "email": test_user.email}
        )
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Get department tasks via department endpoint
        response = await client.get(
            f"/api/v1/departments/{department.id}/tasks",
            headers=auth_headers,
        )

        assert response.status_code == 200
        task_list = response.json()
        
        # Verify response
        assert task_list["total"] == 1
        assert len(task_list["items"]) == 1
        
        task_response = task_list["items"][0]
        assert task_response["title"] == "Sales Task"
        assert task_response["department_id"] == department.id
        assert task_response["status"] == "in_progress"

    async def test_tasks_by_visibility_scope(
        self, client: AsyncClient, db_session: Session, test_user: User,
        test_organization: Organization
    ):
        """CRITICAL: Test filtering tasks by visibility scope."""
        # Create department
        department = Department(
            name="HR",
            code="HR",
            organization_id=test_organization.id,
            path="1",
            depth=0,
        )
        db_session.add(department)

        # Create project
        project = Project(
            name="HR Project",
            code="HR-PROJ",
            organization_id=test_organization.id,
            manager_id=test_user.id,
        )
        db_session.add(project)

        # Create tasks with different visibility scopes
        dept_task = Task(
            title="Department Visible Task",
            project_id=project.id,
            reporter_id=test_user.id,
            department_id=department.id,
            department_visibility="department_hierarchy",
            status="not_started",
            priority="medium",
            created_by=test_user.id,
        )
        
        personal_task = Task(
            title="Personal Task",
            project_id=project.id,
            reporter_id=test_user.id,
            department_id=department.id,
            department_visibility="personal",
            status="not_started",
            priority="low",
            created_by=test_user.id,
        )
        
        db_session.add_all([dept_task, personal_task])
        db_session.commit()

        # Create auth headers
        from app.core.security import create_access_token
        token = create_access_token(
            data={"sub": str(test_user.id), "email": test_user.email}
        )
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Test: Get department_hierarchy tasks
        response = await client.get(
            "/api/v1/tasks/by-visibility/department_hierarchy",
            headers=auth_headers,
        )

        assert response.status_code == 200
        task_list = response.json()
        
        # Should get only department_hierarchy task
        assert task_list["total"] == 1
        assert task_list["items"][0]["title"] == "Department Visible Task"
        assert task_list["items"][0]["department_visibility"] == "department_hierarchy"

        # Test: Get personal tasks
        response = await client.get(
            "/api/v1/tasks/by-visibility/personal",
            headers=auth_headers,
        )

        assert response.status_code == 200
        task_list = response.json()
        
        # Should get only personal task
        assert task_list["total"] == 1
        assert task_list["items"][0]["title"] == "Personal Task"
        assert task_list["items"][0]["department_visibility"] == "personal"


@pytest.mark.asyncio
class TestTaskDepartmentIntegrationErrors:
    """Test error cases for Task-Department integration."""

    async def test_create_task_nonexistent_department(
        self, client: AsyncClient, db_session: Session, test_user: User,
        test_organization: Organization
    ):
        """Test creating task with non-existent department."""
        # Create project
        project = Project(
            name="Test Project",
            code="TEST-PROJ",
            organization_id=test_organization.id,
            manager_id=test_user.id,
        )
        db_session.add(project)
        db_session.commit()

        # Create auth headers
        from app.core.security import create_access_token
        token = create_access_token(
            data={"sub": str(test_user.id), "email": test_user.email}
        )
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Try to create task with non-existent department
        task_data = {
            "title": "Test Task",
            "project_id": project.id,
            "priority": "medium",
        }

        response = await client.post(
            "/api/v1/tasks/department/999",  # Non-existent department
            json=task_data,
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "Department not found" in response.json()["detail"]

    async def test_assign_task_to_nonexistent_department(
        self, client: AsyncClient, db_session: Session, test_user: User,
        test_organization: Organization
    ):
        """Test assigning task to non-existent department."""
        # Create project and task
        project = Project(
            name="Test Project",
            code="TEST-PROJ",
            organization_id=test_organization.id,
            manager_id=test_user.id,
        )
        task = Task(
            title="Test Task",
            project_id=project.id,
            reporter_id=test_user.id,
            status="not_started",
            priority="medium",
            created_by=test_user.id,
        )
        db_session.add_all([project, task])
        db_session.commit()

        # Create auth headers
        from app.core.security import create_access_token
        token = create_access_token(
            data={"sub": str(test_user.id), "email": test_user.email}
        )
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Try to assign task to non-existent department
        response = await client.put(
            f"/api/v1/tasks/{task.id}/assign-department/999",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "Department not found" in response.json()["detail"]