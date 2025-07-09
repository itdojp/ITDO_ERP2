"""Integration tests for Project API endpoints."""

import pytest
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.organization import Organization
from app.models.project import Project, ProjectStatus, ProjectPriority, ProjectType
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate


class TestProjectAPI:
    """Test Project API endpoints."""

    def test_create_project_success(self, client: TestClient, db_session: Session, auth_headers: Dict[str, str]):
        """Test successful project creation."""
        # Create organization first
        org = Organization(code="TEST001", name="Test Organization", is_active=True)
        db_session.add(org)
        db_session.commit()

        project_data = {
            "code": "PROJ001",
            "name": "Test Project",
            "description": "Test project description",
            "organization_id": org.id,
            "status": ProjectStatus.PLANNING.value,
            "priority": ProjectPriority.HIGH.value,
            "project_type": ProjectType.INTERNAL.value,
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "budget": 50000.00,
            "estimated_hours": 1000.0,
            "is_public": True,
        }

        response = client.post("/api/v1/projects/", json=project_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "PROJ001"
        assert data["name"] == "Test Project"
        assert data["organization_id"] == org.id
        assert data["status"] == ProjectStatus.PLANNING.value
        assert data["priority"] == ProjectPriority.HIGH.value
        assert data["project_type"] == ProjectType.INTERNAL.value
        assert data["member_count"] >= 1  # Creator should be a member
        assert data["task_count"] == 0  # No tasks yet
        assert data["progress_percentage"] == 0.0

    def test_create_project_validation_error(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test project creation with validation errors."""
        # Missing required fields
        project_data = {
            "name": "Test Project",
            # Missing code and organization_id
        }

        response = client.post("/api/v1/projects/", json=project_data, headers=auth_headers)
        
        assert response.status_code == 422  # Validation error

    def test_list_projects(self, client: TestClient, db_session: Session, auth_headers: Dict[str, str]):
        """Test listing projects."""
        # Create organization and projects
        org = Organization(code="TEST002", name="Test Organization 2", is_active=True)
        db_session.add(org)
        db_session.commit()

        user = db_session.query(User).first()
        project1 = Project(
            code="PROJ001",
            name="Project 1",
            organization_id=org.id,
            owner_id=user.id,
            status=ProjectStatus.PLANNING.value,
            priority=ProjectPriority.HIGH.value,
            project_type=ProjectType.INTERNAL.value,
            start_date=date(2024, 1, 1),
            is_active=True,
        )
        project2 = Project(
            code="PROJ002",
            name="Project 2",
            organization_id=org.id,
            owner_id=user.id,
            status=ProjectStatus.IN_PROGRESS.value,
            priority=ProjectPriority.MEDIUM.value,
            project_type=ProjectType.CLIENT.value,
            start_date=date(2024, 2, 1),
            is_active=True,
        )
        db_session.add_all([project1, project2])
        db_session.commit()

        response = client.get("/api/v1/projects/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "pages" in data
        assert data["total"] >= 2
        assert len(data["items"]) >= 2

    def test_list_projects_with_filters(self, client: TestClient, db_session: Session, auth_headers: Dict[str, str]):
        """Test listing projects with filters."""
        response = client.get(
            "/api/v1/projects/?status=planning&priority=high&limit=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_get_project_success(self, client: TestClient, db_session: Session, auth_headers: Dict[str, str]):
        """Test getting a specific project."""
        # Create organization and project
        org = Organization(code="TEST003", name="Test Organization 3", is_active=True)
        db_session.add(org)
        db_session.commit()

        user = db_session.query(User).first()
        project = Project(
            code="PROJ003",
            name="Project 3",
            description="Test project 3",
            organization_id=org.id,
            owner_id=user.id,
            status=ProjectStatus.PLANNING.value,
            priority=ProjectPriority.HIGH.value,
            project_type=ProjectType.INTERNAL.value,
            start_date=date(2024, 1, 1),
            is_active=True,
        )
        db_session.add(project)
        db_session.commit()

        response = client.get(f"/api/v1/projects/{project.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project.id
        assert data["code"] == "PROJ003"
        assert data["name"] == "Project 3"
        assert data["description"] == "Test project 3"
        assert data["organization_id"] == org.id
        assert data["owner_id"] == user.id

    def test_get_project_not_found(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test getting a non-existent project."""
        response = client.get("/api/v1/projects/99999", headers=auth_headers)
        
        assert response.status_code == 404

    def test_update_project_success(self, client: TestClient, db_session: Session, auth_headers: Dict[str, str]):
        """Test updating a project."""
        # Create organization and project
        org = Organization(code="TEST004", name="Test Organization 4", is_active=True)
        db_session.add(org)
        db_session.commit()

        user = db_session.query(User).first()
        project = Project(
            code="PROJ004",
            name="Project 4",
            organization_id=org.id,
            owner_id=user.id,
            status=ProjectStatus.PLANNING.value,
            priority=ProjectPriority.MEDIUM.value,
            project_type=ProjectType.INTERNAL.value,
            start_date=date(2024, 1, 1),
            is_active=True,
        )
        db_session.add(project)
        db_session.commit()

        update_data = {
            "name": "Updated Project 4",
            "description": "Updated description",
            "status": ProjectStatus.IN_PROGRESS.value,
            "priority": ProjectPriority.HIGH.value,
        }

        response = client.put(
            f"/api/v1/projects/{project.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project.id
        assert data["name"] == "Updated Project 4"
        assert data["description"] == "Updated description"
        assert data["status"] == ProjectStatus.IN_PROGRESS.value
        assert data["priority"] == ProjectPriority.HIGH.value

    def test_delete_project_success(self, client: TestClient, db_session: Session, auth_headers: Dict[str, str]):
        """Test deleting a project."""
        # Create organization and project
        org = Organization(code="TEST005", name="Test Organization 5", is_active=True)
        db_session.add(org)
        db_session.commit()

        user = db_session.query(User).first()
        project = Project(
            code="PROJ005",
            name="Project 5",
            organization_id=org.id,
            owner_id=user.id,
            status=ProjectStatus.PLANNING.value,
            priority=ProjectPriority.MEDIUM.value,
            project_type=ProjectType.INTERNAL.value,
            start_date=date(2024, 1, 1),
            is_active=True,
        )
        db_session.add(project)
        db_session.commit()

        response = client.delete(f"/api/v1/projects/{project.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Project deleted successfully"
        assert data["deleted_id"] == project.id

        # Verify project is soft-deleted
        db_session.refresh(project)
        assert project.is_active is False

    def test_get_project_statistics(self, client: TestClient, db_session: Session, auth_headers: Dict[str, str]):
        """Test getting project statistics."""
        # Create organization and project
        org = Organization(code="TEST006", name="Test Organization 6", is_active=True)
        db_session.add(org)
        db_session.commit()

        user = db_session.query(User).first()
        project = Project(
            code="PROJ006",
            name="Project 6",
            organization_id=org.id,
            owner_id=user.id,
            status=ProjectStatus.IN_PROGRESS.value,
            priority=ProjectPriority.HIGH.value,
            project_type=ProjectType.INTERNAL.value,
            start_date=date(2024, 1, 1),
            progress_percentage=25,
            is_active=True,
        )
        db_session.add(project)
        db_session.commit()

        response = client.get(f"/api/v1/projects/{project.id}/statistics", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project.id
        assert data["member_count"] >= 0
        assert data["task_count"] >= 0
        assert data["completed_tasks"] >= 0
        assert data["active_tasks"] >= 0
        assert data["overdue_tasks"] >= 0
        assert data["progress_percentage"] == 25.0
        assert data["health_status"] in ["excellent", "good", "fair", "poor"]
        assert isinstance(data["is_on_schedule"], bool)

    def test_get_project_tasks(self, client: TestClient, db_session: Session, auth_headers: Dict[str, str]):
        """Test getting project tasks."""
        # Create organization and project
        org = Organization(code="TEST007", name="Test Organization 7", is_active=True)
        db_session.add(org)
        db_session.commit()

        user = db_session.query(User).first()
        project = Project(
            code="PROJ007",
            name="Project 7",
            organization_id=org.id,
            owner_id=user.id,
            status=ProjectStatus.IN_PROGRESS.value,
            priority=ProjectPriority.HIGH.value,
            project_type=ProjectType.INTERNAL.value,
            start_date=date(2024, 1, 1),
            is_active=True,
        )
        db_session.add(project)
        db_session.commit()

        response = client.get(f"/api/v1/projects/{project.id}/tasks", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Initially empty since no tasks are added yet

    def test_get_project_progress(self, client: TestClient, db_session: Session, auth_headers: Dict[str, str]):
        """Test getting project progress."""
        # Create organization and project
        org = Organization(code="TEST008", name="Test Organization 8", is_active=True)
        db_session.add(org)
        db_session.commit()

        user = db_session.query(User).first()
        project = Project(
            code="PROJ008",
            name="Project 8",
            organization_id=org.id,
            owner_id=user.id,
            status=ProjectStatus.IN_PROGRESS.value,
            priority=ProjectPriority.HIGH.value,
            project_type=ProjectType.INTERNAL.value,
            start_date=date(2024, 1, 1),
            progress_percentage=50,
            is_active=True,
        )
        db_session.add(project)
        db_session.commit()

        response = client.get(f"/api/v1/projects/{project.id}/progress", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project.id
        assert data["progress_percentage"] == 50.0

    def test_get_project_budget(self, client: TestClient, db_session: Session, auth_headers: Dict[str, str]):
        """Test getting project budget utilization."""
        # Create organization and project
        org = Organization(code="TEST009", name="Test Organization 9", is_active=True)
        db_session.add(org)
        db_session.commit()

        user = db_session.query(User).first()
        project = Project(
            code="PROJ009",
            name="Project 9",
            organization_id=org.id,
            owner_id=user.id,
            status=ProjectStatus.IN_PROGRESS.value,
            priority=ProjectPriority.HIGH.value,
            project_type=ProjectType.INTERNAL.value,
            start_date=date(2024, 1, 1),
            budget=100000.0,
            spent_budget=25000.0,
            is_active=True,
        )
        db_session.add(project)
        db_session.commit()

        response = client.get(f"/api/v1/projects/{project.id}/budget", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_budget"] == 100000.0
        assert data["spent_budget"] == 25000.0
        assert data["remaining_budget"] == 75000.0
        assert data["utilization_percentage"] == 25.0


class TestProjectMemberAPI:
    """Test Project Member API endpoints."""

    def test_get_project_members(self, client: TestClient, db_session: Session, auth_headers: Dict[str, str]):
        """Test getting project members."""
        # Create organization and project
        org = Organization(code="TEST010", name="Test Organization 10", is_active=True)
        db_session.add(org)
        db_session.commit()

        user = db_session.query(User).first()
        project = Project(
            code="PROJ010",
            name="Project 10",
            organization_id=org.id,
            owner_id=user.id,
            status=ProjectStatus.PLANNING.value,
            priority=ProjectPriority.HIGH.value,
            project_type=ProjectType.INTERNAL.value,
            start_date=date(2024, 1, 1),
            is_active=True,
        )
        db_session.add(project)
        db_session.commit()

        response = client.get(f"/api/v1/projects/{project.id}/members", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least the owner as a member if auto-created

    def test_authentication_required(self, client: TestClient):
        """Test that authentication is required for all endpoints."""
        # Test without authentication headers
        response = client.get("/api/v1/projects/")
        assert response.status_code == 401

        response = client.post("/api/v1/projects/", json={"name": "Test"})
        assert response.status_code == 401

        response = client.get("/api/v1/projects/1")
        assert response.status_code == 401

        response = client.put("/api/v1/projects/1", json={"name": "Test"})
        assert response.status_code == 401

        response = client.delete("/api/v1/projects/1")
        assert response.status_code == 401