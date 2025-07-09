"""Unit tests for Project API endpoints."""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch
from fastapi import status
from fastapi.testclient import TestClient

from app.models.project import ProjectStatus, ProjectPriority, ProjectType
from app.schemas.project import (
    ProjectResponse,
    ProjectCreate,
    ProjectUpdate,
    ProjectStatistics,
    PaginatedResponse,
)


class TestProjectAPI:
    """Test cases for Project API endpoints."""

    @pytest.fixture
    def mock_project_service(self):
        """Mock project service."""
        with patch("app.api.v1.projects.ProjectService") as mock:
            yield mock.return_value

    @pytest.fixture
    def mock_permission_service(self):
        """Mock permission service."""
        with patch("app.api.v1.projects.PermissionService") as mock:
            service = mock.return_value
            service.check_user_permission.return_value = True
            yield service

    @pytest.fixture
    def sample_project_response(self):
        """Sample project response data."""
        return {
            "id": 1,
            "code": "TEST-001",
            "name": "Test Project",
            "description": "A test project",
            "organization_id": 1,
            "department_id": 1,
            "owner_id": 1,
            "manager_id": 1,
            "status": ProjectStatus.ACTIVE,
            "priority": ProjectPriority.HIGH,
            "project_type": ProjectType.DEVELOPMENT,
            "start_date": str(date.today()),
            "end_date": str(date.today() + timedelta(days=90)),
            "budget": 1000000.0,
            "actual_cost": 0.0,
            "tags": ["test", "development"],
            "is_template": False,
            "is_public": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

    # Test Create Project

    def test_create_project_success(
        self, client, admin_token, mock_project_service, sample_project_response
    ):
        """Test successful project creation."""
        # Setup mock
        mock_project_service.create_project.return_value = ProjectResponse(
            **sample_project_response
        )

        # Prepare request data
        project_data = {
            "code": "TEST-001",
            "name": "Test Project",
            "description": "A test project",
            "organization_id": 1,
            "department_id": 1,
            "manager_id": 1,
            "status": "planning",
            "priority": "high",
            "project_type": "development",
            "start_date": str(date.today()),
            "end_date": str(date.today() + timedelta(days=90)),
            "budget": 1000000.0,
            "tags": ["test", "development"],
        }

        # Execute
        response = client.post(
            "/api/v1/projects/",
            json=project_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["code"] == "TEST-001"
        assert response.json()["name"] == "Test Project"
        mock_project_service.create_project.assert_called_once()

    def test_create_project_validation_error(self, client, admin_token):
        """Test project creation with validation error."""
        # Prepare invalid data (missing required fields)
        project_data = {
            "name": "Test Project",
            # Missing code, organization_id, etc.
        }

        # Execute
        response = client.post(
            "/api/v1/projects/",
            json=project_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_project_duplicate_code(
        self, client, admin_token, mock_project_service
    ):
        """Test project creation with duplicate code."""
        # Setup mock to raise ValueError
        mock_project_service.create_project.side_effect = ValueError(
            "Project code 'TEST-001' already exists"
        )

        # Prepare request data
        project_data = {
            "code": "TEST-001",
            "name": "Test Project",
            "organization_id": 1,
            "start_date": str(date.today()),
            "end_date": str(date.today() + timedelta(days=90)),
        }

        # Execute
        response = client.post(
            "/api/v1/projects/",
            json=project_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"]

    def test_create_project_permission_denied(
        self, client, admin_token, mock_project_service
    ):
        """Test project creation with permission denied."""
        # Setup mock to raise PermissionError
        mock_project_service.create_project.side_effect = PermissionError(
            "Insufficient permissions"
        )

        # Prepare request data
        project_data = {
            "code": "TEST-001",
            "name": "Test Project",
            "organization_id": 1,
            "start_date": str(date.today()),
            "end_date": str(date.today() + timedelta(days=90)),
        }

        # Execute
        response = client.post(
            "/api/v1/projects/",
            json=project_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_project_unauthorized(self, client):
        """Test project creation without authentication."""
        # Execute
        response = client.post("/api/v1/projects/", json={})

        # Verify
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Test List Projects

    def test_list_projects_success(
        self, client, user_token, mock_project_service, sample_project_response
    ):
        """Test successful project listing."""
        # Setup mock
        projects = [
            ProjectResponse(**sample_project_response),
            ProjectResponse(
                **{**sample_project_response, "id": 2, "code": "TEST-002"}
            ),
        ]
        mock_project_service.list_projects.return_value = (projects, 2)

        # Execute
        response = client.get(
            "/api/v1/projects/",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["total"] == 2
        assert len(response.json()["items"]) == 2
        assert response.json()["pages"] == 1

    def test_list_projects_with_filters(
        self, client, user_token, mock_project_service
    ):
        """Test listing projects with filters."""
        # Setup mock
        mock_project_service.list_projects.return_value = ([], 0)

        # Execute with filters
        response = client.get(
            "/api/v1/projects/",
            params={
                "organization_id": 1,
                "department_id": 1,
                "status": "active",
                "priority": "high",
                "search": "test",
                "is_overdue": True,
                "skip": 10,
                "limit": 20,
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_200_OK
        mock_project_service.list_projects.assert_called_once()
        # Check that filters were passed
        call_args = mock_project_service.list_projects.call_args
        assert call_args[1]["filters"].organization_id == 1
        assert call_args[1]["filters"].status == "active"

    def test_list_projects_permission_error(
        self, client, user_token, mock_project_service
    ):
        """Test listing projects with permission error."""
        # Setup mock
        mock_project_service.list_projects.side_effect = PermissionError(
            "Access denied"
        )

        # Execute
        response = client.get(
            "/api/v1/projects/",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # Test Get Project

    def test_get_project_success(
        self, client, user_token, mock_project_service, sample_project_response
    ):
        """Test successful project retrieval."""
        # Setup mock
        mock_project_service.get_project.return_value = ProjectResponse(
            **sample_project_response
        )

        # Execute
        response = client.get(
            "/api/v1/projects/1",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == 1
        assert response.json()["code"] == "TEST-001"

    def test_get_project_not_found(self, client, user_token, mock_project_service):
        """Test getting non-existent project."""
        # Setup mock
        mock_project_service.get_project.return_value = None

        # Execute
        response = client.get(
            "/api/v1/projects/999",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_project_permission_denied(
        self, client, user_token, mock_project_service
    ):
        """Test getting project with permission denied."""
        # Setup mock
        mock_project_service.get_project.side_effect = PermissionError("Access denied")

        # Execute
        response = client.get(
            "/api/v1/projects/1",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # Test Update Project

    def test_update_project_success(
        self, client, admin_token, mock_project_service, sample_project_response
    ):
        """Test successful project update."""
        # Setup mock
        updated_response = {
            **sample_project_response,
            "name": "Updated Project",
            "priority": ProjectPriority.CRITICAL,
        }
        mock_project_service.update_project.return_value = ProjectResponse(
            **updated_response
        )

        # Prepare update data
        update_data = {
            "name": "Updated Project",
            "priority": "critical",
        }

        # Execute
        response = client.put(
            "/api/v1/projects/1",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "Updated Project"
        assert response.json()["priority"] == "critical"

    def test_update_project_validation_error(
        self, client, admin_token, mock_project_service
    ):
        """Test project update with validation error."""
        # Setup mock
        mock_project_service.update_project.side_effect = ValueError(
            "Invalid status transition"
        )

        # Execute
        response = client.put(
            "/api/v1/projects/1",
            json={"status": "invalid"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Test Delete Project

    def test_delete_project_success(self, client, admin_token, mock_project_service):
        """Test successful project deletion."""
        # Setup mock
        mock_project_service.delete_project.return_value = True

        # Execute
        response = client.delete(
            "/api/v1/projects/1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True
        assert response.json()["deleted_id"] == 1

    def test_delete_project_not_found(self, client, admin_token, mock_project_service):
        """Test deleting non-existent project."""
        # Setup mock
        mock_project_service.delete_project.return_value = False

        # Execute
        response = client.delete(
            "/api/v1/projects/999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_project_with_active_tasks(
        self, client, admin_token, mock_project_service
    ):
        """Test deleting project with active tasks."""
        # Setup mock
        mock_project_service.delete_project.side_effect = ValueError(
            "Project has active tasks"
        )

        # Execute
        response = client.delete(
            "/api/v1/projects/1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "active tasks" in response.json()["detail"]

    # Test Project Members

    def test_get_project_members_success(
        self, client, user_token, mock_project_service
    ):
        """Test getting project members."""
        # Setup mock
        members = [
            {
                "id": 1,
                "user_id": 1,
                "user_email": "owner@example.com",
                "user_name": "Project Owner",
                "role": "owner",
                "permissions": ["project.manage"],
                "joined_at": datetime.utcnow().isoformat(),
                "is_active": True,
            },
            {
                "id": 2,
                "user_id": 2,
                "user_email": "developer@example.com",
                "user_name": "Developer",
                "role": "developer",
                "permissions": ["project.read", "tasks.update"],
                "joined_at": datetime.utcnow().isoformat(),
                "is_active": True,
            },
        ]
        mock_project_service.get_project_members.return_value = members

        # Execute
        response = client.get(
            "/api/v1/projects/1/members",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 2
        assert response.json()[0]["role"] == "owner"

    def test_add_project_member_success(
        self, client, admin_token, mock_project_service
    ):
        """Test adding project member."""
        # Setup mock
        mock_project_service.add_member.return_value = True
        mock_project_service.get_project_members.return_value = [
            {
                "id": 3,
                "user_id": 3,
                "user_email": "newmember@example.com",
                "user_name": "New Member",
                "role": "developer",
                "permissions": ["project.read"],
                "joined_at": datetime.utcnow().isoformat(),
                "is_active": True,
            }
        ]

        # Prepare member data
        member_data = {
            "user_id": 3,
            "role": "developer",
            "permissions": ["project.read"],
        }

        # Execute
        response = client.post(
            "/api/v1/projects/1/members",
            json=member_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["user_id"] == 3
        assert response.json()["role"] == "developer"

    def test_add_project_member_duplicate(
        self, client, admin_token, mock_project_service
    ):
        """Test adding duplicate member."""
        # Setup mock
        mock_project_service.add_member.side_effect = ValueError(
            "User is already a member"
        )

        # Execute
        response = client.post(
            "/api/v1/projects/1/members",
            json={"user_id": 1, "role": "developer"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already a member" in response.json()["detail"]

    def test_remove_project_member_success(
        self, client, admin_token, mock_project_service
    ):
        """Test removing project member."""
        # Setup mock
        mock_project_service.remove_member.return_value = True

        # Execute
        response = client.delete(
            "/api/v1/projects/1/members/2",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True
        assert response.json()["deleted_id"] == 2

    def test_update_project_member_role(
        self, client, admin_token, mock_project_service
    ):
        """Test updating member role."""
        # Setup mock
        mock_project_service.update_member_role.return_value = True
        mock_project_service.get_project_members.return_value = [
            {
                "id": 2,
                "user_id": 2,
                "user_email": "member@example.com",
                "user_name": "Member",
                "role": "manager",
                "permissions": ["project.update", "members.add"],
                "joined_at": datetime.utcnow().isoformat(),
                "is_active": True,
            }
        ]

        # Execute
        response = client.put(
            "/api/v1/projects/1/members/2",
            json={"role": "manager", "permissions": ["project.update", "members.add"]},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["role"] == "manager"

    # Test Project Statistics

    def test_get_project_statistics_success(
        self, client, user_token, mock_project_service
    ):
        """Test getting project statistics."""
        # Setup mock
        stats = ProjectStatistics(
            total_members=5,
            total_tasks=20,
            completed_tasks=10,
            overdue_tasks=2,
            total_milestones=4,
            completed_milestones=2,
            budget_utilization=75.0,
            time_elapsed_percentage=50.0,
            overall_progress=45.0,
            health_score=85,
            risk_factors=[],
        )
        mock_project_service.get_enhanced_project_statistics.return_value = stats

        # Execute
        response = client.get(
            "/api/v1/projects/1/statistics",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["total_members"] == 5
        assert response.json()["overall_progress"] == 45.0
        assert response.json()["health_score"] == 85

    def test_get_project_statistics_not_found(
        self, client, user_token, mock_project_service
    ):
        """Test getting statistics for non-existent project."""
        # Setup mock
        mock_project_service.get_enhanced_project_statistics.side_effect = ValueError(
            "Project not found"
        )

        # Execute
        response = client.get(
            "/api/v1/projects/999/statistics",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # Test Project Tasks

    def test_get_project_tasks_success(self, client, user_token, mock_project_service):
        """Test getting project tasks."""
        # Setup mock
        tasks = [
            {
                "id": 1,
                "title": "Task 1",
                "status": "in_progress",
                "assignee_id": 1,
            },
            {
                "id": 2,
                "title": "Task 2",
                "status": "completed",
                "assignee_id": 2,
            },
        ]
        mock_project_service.get_project_tasks.return_value = tasks

        # Execute
        response = client.get(
            "/api/v1/projects/1/tasks",
            params={"include_completed": True},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 2

    # Test Project Progress

    def test_get_project_progress_success(
        self, client, user_token, mock_project_service
    ):
        """Test getting project progress."""
        # Setup mock
        mock_project_service.get_project_progress.return_value = 65.5

        # Execute
        response = client.get(
            "/api/v1/projects/1/progress",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["project_id"] == 1
        assert response.json()["progress_percentage"] == 65.5

    # Test Budget Utilization

    def test_get_project_budget_utilization(
        self, client, user_token, mock_project_service
    ):
        """Test getting budget utilization."""
        # Setup mock
        budget_info = {
            "budget": 1000000.0,
            "actual_cost": 750000.0,
            "utilization_percentage": 75.0,
            "remaining_budget": 250000.0,
        }
        mock_project_service.get_budget_utilization.return_value = budget_info

        # Execute
        response = client.get(
            "/api/v1/projects/1/budget",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Verify
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["utilization_percentage"] == 75.0
        assert response.json()["remaining_budget"] == 250000.0