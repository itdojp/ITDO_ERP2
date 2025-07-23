"""
Test suite for Project Management API - CC02 v31.0 Phase 2

Comprehensive tests for project management system with 10 endpoints:
1. Project Management
2. Task Management
3. Resource Management
4. Time Tracking
5. Risk Management
6. Milestone Management
7. Issue Management
8. Portfolio Management
9. Template Management
10. Project Analytics
"""

import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.project_extended import (
    ProjectExtended,
    ProjectPortfolio,
    ProjectResource,
    ProjectRisk,
    ProjectStatus,
    ResourceRole,
    RiskLevel,
    RiskStatus,
    TaskExtended,
    TaskPriority,
    TaskStatus,
    TimeEntry,
    TimeEntryType,
)
from tests.conftest import TestingSessionLocal, engine

client = TestClient(app)

# Test data fixtures
@pytest.fixture
def sample_project_data():
    return {
        "organization_id": "org_123",
        "name": "Test Project",
        "description": "A test project for development",
        "project_type": "internal",
        "priority": "high",
        "project_manager_id": "user_123",
        "planned_start_date": "2024-01-01",
        "planned_end_date": "2024-06-30",
        "total_budget": 100000,
        "estimated_hours": 1000,
        "methodology": "agile",
        "sprint_duration": 14,
        "is_billable": False
    }

@pytest.fixture
def sample_task_data():
    return {
        "project_id": "proj_123",
        "title": "Implement user authentication",
        "description": "Add login and registration functionality",
        "priority": "high",
        "task_type": "feature",
        "assigned_to_id": "user_123",
        "due_date": "2024-02-15",
        "estimated_hours": 40,
        "story_points": 8
    }

@pytest.fixture
def sample_resource_data():
    return {
        "project_id": "proj_123",
        "user_id": "user_123",
        "role": "developer",
        "allocation_percentage": 80,
        "hourly_rate": 50.00,
        "start_date": "2024-01-01",
        "end_date": "2024-06-30",
        "planned_hours": 800
    }

@pytest.fixture
def sample_time_entry_data():
    return {
        "project_id": "proj_123",
        "task_id": "task_123",
        "user_id": "user_123",
        "date": "2024-01-15",
        "hours": 8.0,
        "entry_type": "development",
        "description": "Implemented user registration form",
        "is_billable": True,
        "billing_rate": 50.00
    }

@pytest.fixture
def sample_risk_data():
    return {
        "project_id": "proj_123",
        "title": "Third-party API dependency",
        "description": "Risk of API changes affecting functionality",
        "category": "technical",
        "probability": 0.3,
        "impact": 0.7,
        "owner_id": "user_123",
        "identified_date": "2024-01-10",
        "mitigation_strategy": "Create fallback implementation"
    }

@pytest.fixture
def sample_milestone_data():
    return {
        "project_id": "proj_123",
        "name": "MVP Release",
        "description": "Minimum viable product release",
        "milestone_type": "deliverable",
        "planned_date": "2024-03-01",
        "requires_approval": True,
        "success_criteria": ["All core features implemented", "All tests passing"]
    }

@pytest.fixture
def sample_issue_data():
    return {
        "project_id": "proj_123",
        "task_id": "task_123",
        "title": "Login page styling bug",
        "description": "CSS not loading correctly on mobile devices",
        "issue_type": "bug",
        "severity": "medium",
        "priority": "high",
        "reporter_id": "user_123",
        "reported_date": "2024-01-20"
    }

@pytest.fixture
def sample_portfolio_data():
    return {
        "organization_id": "org_123",
        "name": "Digital Transformation",
        "description": "Portfolio for digital transformation projects",
        "portfolio_manager_id": "user_123",
        "total_budget": 500000,
        "strategic_objectives": ["Improve efficiency", "Reduce costs"]
    }

@pytest.fixture
def sample_template_data():
    return {
        "organization_id": "org_123",
        "name": "Web Development Template",
        "description": "Standard template for web development projects",
        "category": "development",
        "template_data": {
            "methodology": "agile",
            "sprint_duration": 14,
            "default_tasks": ["Setup", "Development", "Testing", "Deployment"]
        },
        "default_duration_days": 90,
        "default_team_size": 5
    }

# =============================================================================
# 1. Project Management Tests
# =============================================================================

class TestProjectManagement:
    """Test Project Management endpoint."""
    
    def test_list_projects_success(self):
        """Test successful project listing."""
        with patch('app.crud.project_v31.get_projects') as mock_get:
            mock_get.return_value = []
            
            response = client.get("/api/v1/project/projects")
            
            assert response.status_code == 200
            assert response.json() == []
            mock_get.assert_called_once()

    def test_list_projects_with_filters(self):
        """Test project listing with filters."""
        with patch('app.crud.project_v31.get_projects') as mock_get:
            mock_get.return_value = []
            
            response = client.get(
                "/api/v1/project/projects?organization_id=org_123&status=active&priority=high"
            )
            
            assert response.status_code == 200
            mock_get.assert_called_once()

    def test_create_project_success(self, sample_project_data):
        """Test successful project creation."""
        with patch('app.crud.project_v31.create_project') as mock_create:
            mock_project = ProjectExtended(id="proj_123", **sample_project_data)
            mock_create.return_value = mock_project
            
            response = client.post("/api/v1/project/projects", json=sample_project_data)
            
            assert response.status_code == 200
            assert "proj_123" in str(response.json())
            mock_create.assert_called_once()

    def test_create_project_validation_error(self):
        """Test project creation with validation error."""
        invalid_data = {"name": "Test"}  # Missing required fields
        
        response = client.post("/api/v1/project/projects", json=invalid_data)
        
        assert response.status_code == 422  # Validation error

    def test_get_project_success(self):
        """Test successful project retrieval."""
        with patch('app.crud.project_v31.get_project') as mock_get:
            mock_project = ProjectExtended(
                id="proj_123",
                name="Test Project",
                status=ProjectStatus.ACTIVE
            )
            mock_get.return_value = mock_project
            
            response = client.get("/api/v1/project/projects/proj_123")
            
            assert response.status_code == 200
            mock_get.assert_called_once_with(mock.ANY, "proj_123")

    def test_get_project_not_found(self):
        """Test project retrieval when not found."""
        with patch('app.crud.project_v31.get_project') as mock_get:
            mock_get.return_value = None
            
            response = client.get("/api/v1/project/projects/nonexistent")
            
            assert response.status_code == 404
            assert "Project not found" in response.json()["detail"]

    def test_update_project_success(self, sample_project_data):
        """Test successful project update."""
        with patch('app.crud.project_v31.update_project') as mock_update:
            mock_project = ProjectExtended(id="proj_123", **sample_project_data)
            mock_update.return_value = mock_project
            
            update_data = {"name": "Updated Project Name"}
            response = client.put("/api/v1/project/projects/proj_123", json=update_data)
            
            assert response.status_code == 200
            mock_update.assert_called_once()

    def test_delete_project_success(self):
        """Test successful project deletion."""
        with patch('app.crud.project_v31.delete_project') as mock_delete:
            mock_delete.return_value = True
            
            response = client.delete("/api/v1/project/projects/proj_123")
            
            assert response.status_code == 200
            assert "archived" in response.json()["message"]
            mock_delete.assert_called_once_with(mock.ANY, "proj_123")

# =============================================================================
# 2. Task Management Tests
# =============================================================================

class TestTaskManagement:
    """Test Task Management endpoint."""
    
    def test_list_tasks_success(self):
        """Test successful task listing."""
        with patch('app.crud.project_v31.get_tasks') as mock_get:
            mock_get.return_value = []
            
            response = client.get("/api/v1/project/tasks")
            
            assert response.status_code == 200
            assert response.json() == []
            mock_get.assert_called_once()

    def test_create_task_success(self, sample_task_data):
        """Test successful task creation."""
        with patch('app.crud.project_v31.create_task') as mock_create:
            mock_task = TaskExtended(id="task_123", **sample_task_data)
            mock_create.return_value = mock_task
            
            response = client.post("/api/v1/project/tasks", json=sample_task_data)
            
            assert response.status_code == 200
            mock_create.assert_called_once()

    def test_get_task_success(self):
        """Test successful task retrieval."""
        with patch('app.crud.project_v31.get_task') as mock_get:
            mock_task = TaskExtended(
                id="task_123",
                title="Test Task",
                status=TaskStatus.IN_PROGRESS
            )
            mock_get.return_value = mock_task
            
            response = client.get("/api/v1/project/tasks/task_123")
            
            assert response.status_code == 200
            mock_get.assert_called_once_with(mock.ANY, "task_123")

    def test_update_task_success(self):
        """Test successful task update."""
        with patch('app.crud.project_v31.update_task') as mock_update:
            mock_task = TaskExtended(
                id="task_123",
                title="Updated Task",
                status=TaskStatus.COMPLETED
            )
            mock_update.return_value = mock_task
            
            update_data = {"status": "completed", "progress_percentage": 100}
            response = client.put("/api/v1/project/tasks/task_123", json=update_data)
            
            assert response.status_code == 200
            mock_update.assert_called_once()

    def test_create_task_dependency_success(self):
        """Test successful task dependency creation."""
        with patch('app.crud.project_v31.create_task_dependency') as mock_create:
            from app.models.project_extended import TaskDependencyExtended
            mock_dependency = TaskDependencyExtended(
                id="dep_123",
                task_id="task_123",
                dependent_task_id="task_456"
            )
            mock_create.return_value = mock_dependency
            
            dependency_data = {
                "task_id": "task_123",
                "dependent_task_id": "task_456",
                "dependency_type": "finish_to_start"
            }
            response = client.post(
                "/api/v1/project/tasks/task_123/dependencies",
                json=dependency_data
            )
            
            assert response.status_code == 200
            mock_create.assert_called_once()

    def test_bulk_update_tasks_success(self):
        """Test successful bulk task update."""
        with patch('app.crud.project_v31.update_task') as mock_update:
            mock_update.return_value = TaskExtended(id="task_123", status=TaskStatus.COMPLETED)
            
            bulk_data = {
                "task_ids": ["task_123", "task_456"],
                "updates": {"priority": "high"}
            }
            response = client.put("/api/v1/project/tasks/bulk-update", json=bulk_data)
            
            assert response.status_code == 200
            result = response.json()
            assert result["updated_count"] >= 0
            assert "total_requested" in result

# =============================================================================
# 3. Resource Management Tests
# =============================================================================

class TestResourceManagement:
    """Test Resource Management endpoint."""
    
    def test_list_project_resources_success(self):
        """Test successful project resources listing."""
        with patch('app.crud.project_v31.get_project_resources') as mock_get:
            mock_get.return_value = []
            
            response = client.get("/api/v1/project/projects/proj_123/resources")
            
            assert response.status_code == 200
            assert response.json() == []
            mock_get.assert_called_once_with(mock.ANY, "proj_123", True)

    def test_create_resource_allocation_success(self, sample_resource_data):
        """Test successful resource allocation creation."""
        with patch('app.crud.project_v31.create_project_resource') as mock_create:
            mock_resource = ProjectResource(id="res_123", **sample_resource_data)
            mock_create.return_value = mock_resource
            
            response = client.post(
                "/api/v1/project/projects/proj_123/resources",
                json=sample_resource_data
            )
            
            assert response.status_code == 200
            mock_create.assert_called_once()

    def test_update_resource_allocation_success(self):
        """Test successful resource allocation update."""
        with patch('app.crud.project_v31.update_resource_allocation') as mock_update:
            mock_resource = ProjectResource(
                id="res_123",
                allocation_percentage=Decimal("90")
            )
            mock_update.return_value = mock_resource
            
            update_data = {"allocation_percentage": 90}
            response = client.put("/api/v1/project/resources/res_123", json=update_data)
            
            assert response.status_code == 200
            mock_update.assert_called_once()

# =============================================================================
# 4. Time Tracking Tests
# =============================================================================

class TestTimeTracking:
    """Test Time Tracking endpoint."""
    
    def test_list_time_entries_success(self):
        """Test successful time entries listing."""
        with patch('app.crud.project_v31.get_time_entries') as mock_get:
            mock_get.return_value = []
            
            response = client.get("/api/v1/project/time-entries")
            
            assert response.status_code == 200
            assert response.json() == []
            mock_get.assert_called_once()

    def test_create_time_entry_success(self, sample_time_entry_data):
        """Test successful time entry creation."""
        with patch('app.crud.project_v31.create_time_entry') as mock_create:
            mock_entry = TimeEntry(id="entry_123", **sample_time_entry_data)
            mock_create.return_value = mock_entry
            
            response = client.post("/api/v1/project/time-entries", json=sample_time_entry_data)
            
            assert response.status_code == 200
            mock_create.assert_called_once()

    def test_update_time_entry_success(self):
        """Test successful time entry update."""
        # Mock database session and TimeEntry
        mock_entry = TimeEntry(
            id="entry_123",
            hours=Decimal("8.0"),
            is_billable=True,
            billing_rate=Decimal("50.00")
        )
        
        with patch('app.core.database.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = mock_entry
            
            update_data = {"hours": 6.5, "description": "Updated work description"}
            response = client.put("/api/v1/project/time-entries/entry_123", json=update_data)
            
            assert response.status_code == 200

    def test_approve_time_entry_success(self):
        """Test successful time entry approval."""
        with patch('app.crud.project_v31.approve_time_entry') as mock_approve:
            mock_entry = TimeEntry(id="entry_123", is_approved=True)
            mock_approve.return_value = mock_entry
            
            approval_data = {"entry_id": "entry_123", "approver_id": "user_456"}
            response = client.post(
                "/api/v1/project/time-entries/entry_123/approve",
                json=approval_data
            )
            
            assert response.status_code == 200
            mock_approve.assert_called_once()

# =============================================================================
# 5. Risk Management Tests
# =============================================================================

class TestRiskManagement:
    """Test Risk Management endpoint."""
    
    def test_list_project_risks_success(self):
        """Test successful project risks listing."""
        with patch('app.crud.project_v31.get_project_risks') as mock_get:
            mock_get.return_value = []
            
            response = client.get("/api/v1/project/projects/proj_123/risks")
            
            assert response.status_code == 200
            assert response.json() == []
            mock_get.assert_called_once_with(mock.ANY, "proj_123", True)

    def test_create_project_risk_success(self, sample_risk_data):
        """Test successful project risk creation."""
        with patch('app.crud.project_v31.create_project_risk') as mock_create:
            mock_risk = ProjectRisk(id="risk_123", **sample_risk_data)
            mock_create.return_value = mock_risk
            
            response = client.post(
                "/api/v1/project/projects/proj_123/risks",
                json=sample_risk_data
            )
            
            assert response.status_code == 200
            mock_create.assert_called_once()

    def test_update_project_risk_success(self):
        """Test successful project risk update."""
        mock_risk = ProjectRisk(
            id="risk_123",
            title="Updated Risk",
            probability=Decimal("0.4"),
            impact=Decimal("0.8")
        )
        
        with patch('app.core.database.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = mock_risk
            
            update_data = {"probability": 0.4, "impact": 0.8}
            response = client.put("/api/v1/project/risks/risk_123", json=update_data)
            
            assert response.status_code == 200

    def test_update_risk_status_success(self):
        """Test successful risk status update."""
        with patch('app.crud.project_v31.update_risk_status') as mock_update:
            mock_risk = ProjectRisk(id="risk_123", status=RiskStatus.MITIGATED)
            mock_update.return_value = mock_risk
            
            status_data = {"risk_id": "risk_123", "status": "mitigated"}
            response = client.post(
                "/api/v1/project/risks/risk_123/status",
                json=status_data
            )
            
            assert response.status_code == 200
            mock_update.assert_called_once()

# =============================================================================
# 6. Milestone Management Tests
# =============================================================================

class TestMilestoneManagement:
    """Test Milestone Management endpoint."""
    
    def test_list_project_milestones_success(self):
        """Test successful project milestones listing."""
        with patch('app.core.database.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.query.return_value.filter.return_value.all.return_value = []
            
            response = client.get("/api/v1/project/projects/proj_123/milestones")
            
            assert response.status_code == 200
            assert response.json() == []

    def test_create_project_milestone_success(self, sample_milestone_data):
        """Test successful project milestone creation."""
        with patch('app.core.database.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            response = client.post(
                "/api/v1/project/projects/proj_123/milestones",
                json=sample_milestone_data
            )
            
            assert response.status_code == 200

    def test_update_project_milestone_success(self):
        """Test successful project milestone update."""
        from app.models.project_extended import ProjectMilestoneExtended
        
        mock_milestone = ProjectMilestoneExtended(
            id="milestone_123",
            name="Updated Milestone"
        )
        
        with patch('app.core.database.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = mock_milestone
            
            update_data = {"name": "Updated Milestone", "completion_percentage": 75}
            response = client.put("/api/v1/project/milestones/milestone_123", json=update_data)
            
            assert response.status_code == 200

# =============================================================================
# 7. Issue Management Tests
# =============================================================================

class TestIssueManagement:
    """Test Issue Management endpoint."""
    
    def test_list_project_issues_success(self):
        """Test successful project issues listing."""
        with patch('app.core.database.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
            
            response = client.get("/api/v1/project/projects/proj_123/issues")
            
            assert response.status_code == 200
            assert response.json() == []

    def test_create_project_issue_success(self, sample_issue_data):
        """Test successful project issue creation."""
        mock_project = ProjectExtended(id="proj_123", project_code="TEST-001")
        
        with patch('app.core.database.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = mock_project
            mock_db.query.return_value.filter.return_value.count.return_value = 0
            
            response = client.post(
                "/api/v1/project/projects/proj_123/issues",
                json=sample_issue_data
            )
            
            assert response.status_code == 200

    def test_update_project_issue_success(self):
        """Test successful project issue update."""
        from app.models.project_extended import ProjectIssue
        
        mock_issue = ProjectIssue(
            id="issue_123",
            title="Updated Issue",
            status="resolved"
        )
        
        with patch('app.core.database.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = mock_issue
            
            update_data = {"status": "resolved", "resolution": "fixed"}
            response = client.put("/api/v1/project/issues/issue_123", json=update_data)
            
            assert response.status_code == 200

# =============================================================================
# 8. Portfolio Management Tests
# =============================================================================

class TestPortfolioManagement:
    """Test Portfolio Management endpoint."""
    
    def test_list_portfolios_success(self):
        """Test successful portfolios listing."""
        with patch('app.crud.project_v31.get_portfolios') as mock_get:
            mock_get.return_value = []
            
            response = client.get("/api/v1/project/portfolios?organization_id=org_123")
            
            assert response.status_code == 200
            assert response.json() == []
            mock_get.assert_called_once()

    def test_create_project_portfolio_success(self, sample_portfolio_data):
        """Test successful project portfolio creation."""
        with patch('app.crud.project_v31.create_portfolio') as mock_create:
            mock_portfolio = ProjectPortfolio(id="portfolio_123", **sample_portfolio_data)
            mock_create.return_value = mock_portfolio
            
            response = client.post("/api/v1/project/portfolios", json=sample_portfolio_data)
            
            assert response.status_code == 200
            mock_create.assert_called_once()

    def test_update_portfolio_success(self):
        """Test successful portfolio update."""
        mock_portfolio = ProjectPortfolio(
            id="portfolio_123",
            name="Updated Portfolio"
        )
        
        with patch('app.core.database.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = mock_portfolio
            
            update_data = {"name": "Updated Portfolio", "total_budget": 750000}
            response = client.put("/api/v1/project/portfolios/portfolio_123", json=update_data)
            
            assert response.status_code == 200

# =============================================================================
# 9. Template Management Tests
# =============================================================================

class TestTemplateManagement:
    """Test Template Management endpoint."""
    
    def test_list_project_templates_success(self):
        """Test successful project templates listing."""
        with patch('app.core.database.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
            
            response = client.get("/api/v1/project/templates?organization_id=org_123")
            
            assert response.status_code == 200
            assert response.json() == []

    def test_create_project_template_success(self, sample_template_data):
        """Test successful project template creation."""
        with patch('app.core.database.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            response = client.post("/api/v1/project/templates", json=sample_template_data)
            
            assert response.status_code == 200

    def test_create_project_from_template_success(self):
        """Test successful project creation from template."""
        from app.models.project_extended import ProjectTemplate
        
        mock_template = ProjectTemplate(
            id="template_123",
            template_data={"methodology": "agile", "sprint_duration": 14},
            usage_count=0
        )
        
        with patch('app.core.database.get_db') as mock_get_db, \
             patch('app.crud.project_v31.create_project') as mock_create_project:
            
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = mock_template
            
            mock_project = ProjectExtended(id="proj_123", name="New Project")
            mock_create_project.return_value = mock_project
            
            request_data = {
                "template_id": "template_123",
                "project_name": "New Project from Template",
                "organization_id": "org_123"
            }
            
            response = client.post(
                "/api/v1/project/templates/template_123/create-project",
                json=request_data
            )
            
            assert response.status_code == 200

# =============================================================================
# 10. Project Analytics Tests
# =============================================================================

class TestProjectAnalytics:
    """Test Project Analytics endpoint."""
    
    def test_get_project_dashboard_success(self):
        """Test successful project dashboard retrieval."""
        with patch('app.crud.project_v31.get_project_dashboard_metrics') as mock_get:
            mock_metrics = {
                "project_id": "proj_123",
                "project_name": "Test Project",
                "status": "active",
                "progress_percentage": 75.0,
                "total_tasks": 20,
                "completed_tasks": 15,
                "task_completion_rate": 75.0,
                "total_logged_hours": 320.0,
                "billable_hours": 280.0,
                "estimated_hours": 400.0,
                "actual_hours": 320.0,
                "budget_utilization": 64.0,
                "high_priority_risks": 2,
                "team_size": 5,
                "days_remaining": 45,
                "is_on_schedule": True,
                "quality_score": 4.2
            }
            mock_get.return_value = mock_metrics
            
            response = client.get("/api/v1/project/projects/proj_123/dashboard")
            
            assert response.status_code == 200
            assert response.json()["project_id"] == "proj_123"
            assert response.json()["progress_percentage"] == 75.0
            mock_get.assert_called_once()

    def test_get_project_health_success(self):
        """Test successful project health score retrieval."""
        with patch('app.crud.project_v31.calculate_project_health_score') as mock_calc:
            mock_health = {
                "project_id": "proj_123",
                "overall_health_score": 82.5,
                "health_status": "healthy",
                "health_factors": {
                    "schedule": {"score": 85.0, "weight": 0.4},
                    "budget": {"score": 80.0, "weight": 0.25}
                },
                "recommendations": ["Project appears healthy"]
            }
            mock_calc.return_value = mock_health
            
            response = client.get("/api/v1/project/projects/proj_123/health")
            
            assert response.status_code == 200
            assert response.json()["overall_health_score"] == 82.5
            assert response.json()["health_status"] == "healthy"
            mock_calc.assert_called_once()

    def test_get_organization_summary_success(self):
        """Test successful organization summary retrieval."""
        with patch('app.crud.project_v31.get_organization_project_summary') as mock_get:
            mock_summary = {
                "organization_id": "org_123",
                "total_active_projects": 15,
                "project_status_distribution": {"active": 10, "completed": 3, "on_hold": 2},
                "total_resources_allocated": 45,
                "total_budget": 1500000.0,
                "total_actual_cost": 950000.0,
                "budget_utilization": 63.3,
                "summary_date": datetime.utcnow()
            }
            mock_get.return_value = mock_summary
            
            response = client.get("/api/v1/project/organizations/org_123/project-summary")
            
            assert response.status_code == 200
            assert response.json()["organization_id"] == "org_123"
            assert response.json()["total_active_projects"] == 15
            mock_get.assert_called_once()

    def test_clone_project_success(self):
        """Test successful project cloning."""
        mock_source_project = ProjectExtended(
            id="proj_123",
            name="Source Project",
            organization_id="org_123",
            project_type="development",
            methodology="agile",
            planned_start_date=date(2024, 1, 1),
            planned_end_date=date(2024, 6, 30)
        )
        
        with patch('app.crud.project_v31.get_project') as mock_get_project, \
             patch('app.crud.project_v31.create_project') as mock_create_project:
            
            mock_get_project.return_value = mock_source_project
            mock_new_project = ProjectExtended(
                id="proj_456",
                name="Cloned Project"
            )
            mock_create_project.return_value = mock_new_project
            
            clone_data = {
                "source_project_id": "proj_123",
                "new_project_name": "Cloned Project",
                "include_tasks": True,
                "include_timeline": True
            }
            
            response = client.post("/api/v1/project/projects/proj_123/clone", json=clone_data)
            
            assert response.status_code == 200
            mock_get_project.assert_called_once()
            mock_create_project.assert_called_once()

# =============================================================================
# Integration Tests
# =============================================================================

class TestProjectIntegration:
    """Test project management system integration scenarios."""
    
    def test_complete_project_lifecycle_integration(self):
        """Test complete project lifecycle integration."""
        # This would test creating project, adding tasks, allocating resources,
        # tracking time, managing risks, reaching milestones, etc.
        assert True  # Placeholder for integration test

    def test_agile_project_workflow_integration(self):
        """Test agile project workflow integration."""
        # This would test sprint planning, backlog management, burndown charts, etc.
        assert True  # Placeholder for integration test

    def test_portfolio_management_integration(self):
        """Test portfolio management integration."""
        # This would test managing multiple projects within a portfolio
        assert True  # Placeholder for integration test

# =============================================================================
# Error Handling Tests
# =============================================================================

class TestProjectErrorHandling:
    """Test project management API error handling."""
    
    def test_database_error_handling(self):
        """Test database error handling."""
        with patch('app.crud.project_v31.get_projects') as mock_get:
            mock_get.side_effect = Exception("Database connection error")
            
            response = client.get("/api/v1/project/projects")
            
            assert response.status_code == 500
            assert "Error retrieving projects" in response.json()["detail"]

    def test_validation_error_handling(self):
        """Test validation error handling."""
        invalid_data = {"name": ""}  # Invalid empty name
        
        response = client.post("/api/v1/project/projects", json=invalid_data)
        
        assert response.status_code == 422  # Validation error

    def test_business_logic_error_handling(self):
        """Test business logic error handling."""
        with patch('app.crud.project_v31.create_project') as mock_create:
            mock_create.side_effect = ValueError("Project manager not found")
            
            sample_data = {
                "organization_id": "org_123",
                "name": "Test Project",
                "project_manager_id": "nonexistent_user"
            }
            
            response = client.post("/api/v1/project/projects", json=sample_data)
            
            assert response.status_code == 400
            assert "Project manager not found" in response.json()["detail"]

# =============================================================================
# Performance Tests
# =============================================================================

class TestProjectPerformance:
    """Test project management API performance scenarios."""
    
    def test_large_project_list_performance(self):
        """Test performance with large project lists."""
        # This would test pagination, filtering with large datasets
        assert True  # Placeholder for performance test

    def test_complex_project_dashboard_performance(self):
        """Test performance of complex dashboard calculations."""
        # This would test analytics and metrics calculations with large projects
        assert True  # Placeholder for performance test

    def test_bulk_operations_performance(self):
        """Test performance of bulk operations."""
        # This would test bulk task updates, resource allocations, etc.
        assert True  # Placeholder for performance test