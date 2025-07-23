"""
Tests for Workflow System API - CC02 v31.0 Phase 2

Comprehensive test suite for workflow management including:
- Business Process Automation & Orchestration
- Approval Workflows & State Management
- Dynamic Workflow Configuration
- Parallel & Sequential Processing
- Role-Based Task Assignment
- Workflow Analytics & Performance Tracking
- Template-Based Workflow Creation
- Integration Hooks & External Triggers
- Compliance & Audit Trail

Tests 8 main endpoint groups with 60+ individual endpoints
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.workflow_extended import (
    TaskPriority,
    TaskStatus,
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowInstanceStatus,
    WorkflowStatus,
    WorkflowTask,
    WorkflowType,
)


@pytest.fixture
def client():
    """Test client fixture."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_workflow_service():
    """Mock workflow service fixture."""
    return Mock()


@pytest.fixture
def sample_workflow_definition():
    """Sample workflow definition for testing."""
    return WorkflowDefinition(
        id="def-123",
        organization_id="org-123",
        name="Test Workflow",
        code="TEST_WF_001",
        description="Test workflow description",
        workflow_type=WorkflowType.APPROVAL,
        category="Testing",
        definition_schema={
            "steps": [{"id": "step1", "name": "Initial Review", "type": "approval"}]
        },
        auto_start=False,
        parallel_execution=False,
        max_parallel_tasks=5,
        status=WorkflowStatus.ACTIVE,
        is_public=False,
        usage_count=10,
        success_rate=Decimal("95.5"),
        version="1.0",
        created_by="user-123",
        created_at=datetime.now(),
    )


@pytest.fixture
def sample_workflow_instance():
    """Sample workflow instance for testing."""
    return WorkflowInstance(
        id="inst-123",
        organization_id="org-123",
        definition_id="def-123",
        instance_number="WF-2024-001",
        title="Test Instance",
        description="Test instance description",
        entity_type="document",
        entity_id="doc-123",
        status=WorkflowInstanceStatus.RUNNING,
        current_step_id="step-123",
        current_assignee_id="user-123",
        priority=TaskPriority.NORMAL,
        urgency_level=3,
        total_steps=3,
        completed_steps=1,
        progress_percentage=Decimal("33.33"),
        sla_breach=False,
        escalation_count=0,
        initiated_by="user-123",
        created_at=datetime.now(),
    )


@pytest.fixture
def sample_workflow_task():
    """Sample workflow task for testing."""
    return WorkflowTask(
        id="task-123",
        organization_id="org-123",
        instance_id="inst-123",
        step_id="step-123",
        task_number="TASK-001",
        name="Test Task",
        description="Test task description",
        assignee_id="user-123",
        assignee_type="user",
        status=TaskStatus.ASSIGNED,
        priority=TaskPriority.NORMAL,
        urgency_score=3,
        progress_percentage=Decimal("0.00"),
        sla_breach=False,
        attachment_count=0,
        comment_count=0,
        created_at=datetime.now(),
    )


# =============================================================================
# Workflow Definition Management Tests
# =============================================================================


class TestWorkflowDefinitionManagement:
    """Test workflow definition management endpoints."""

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_create_workflow_definition_success(
        self, mock_get_service, client, sample_workflow_definition
    ):
        """Test successful workflow definition creation."""
        mock_service = Mock()
        mock_service.create_workflow_definition = AsyncMock(
            return_value=sample_workflow_definition
        )
        mock_get_service.return_value = mock_service

        definition_data = {
            "organization_id": "org-123",
            "name": "Test Workflow",
            "code": "TEST_WF_001",
            "description": "Test workflow description",
            "workflow_type": "approval",
            "definition_schema": {
                "steps": [{"id": "step1", "name": "Review", "type": "approval"}]
            },
            "created_by": "user-123",
        }

        response = client.post("/definitions", json=definition_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Workflow"
        assert data["code"] == "TEST_WF_001"
        mock_service.create_workflow_definition.assert_called_once()

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_create_workflow_definition_failure(self, mock_get_service, client):
        """Test workflow definition creation failure."""
        mock_service = Mock()
        mock_service.create_workflow_definition = AsyncMock(
            side_effect=Exception("Creation failed")
        )
        mock_get_service.return_value = mock_service

        definition_data = {
            "organization_id": "org-123",
            "name": "Test Workflow",
            "code": "TEST_WF_001",
            "definition_schema": {"steps": []},
            "created_by": "user-123",
        }

        response = client.post("/definitions", json=definition_data)
        assert response.status_code == 400
        assert "Failed to create workflow definition" in response.json()["detail"]

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_list_workflow_definitions_success(
        self, mock_get_service, client, sample_workflow_definition
    ):
        """Test successful workflow definitions listing."""
        mock_service = Mock()
        mock_service.list_workflow_definitions = AsyncMock(
            return_value=([sample_workflow_definition], 1)
        )
        mock_get_service.return_value = mock_service

        response = client.get("/definitions?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["definitions"]) == 1
        assert data["definitions"][0]["name"] == "Test Workflow"

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_get_workflow_definition_success(
        self, mock_get_service, client, sample_workflow_definition
    ):
        """Test successful workflow definition retrieval."""
        mock_service = Mock()
        mock_service.get_workflow_definition = AsyncMock(
            return_value=sample_workflow_definition
        )
        mock_get_service.return_value = mock_service

        response = client.get("/definitions/def-123")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "def-123"
        assert data["name"] == "Test Workflow"

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_get_workflow_definition_not_found(self, mock_get_service, client):
        """Test workflow definition not found."""
        mock_service = Mock()
        mock_service.get_workflow_definition = AsyncMock(return_value=None)
        mock_get_service.return_value = mock_service

        response = client.get("/definitions/nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_update_workflow_definition_success(
        self, mock_get_service, client, sample_workflow_definition
    ):
        """Test successful workflow definition update."""
        mock_service = Mock()
        mock_service.update_workflow_definition = AsyncMock(
            return_value=sample_workflow_definition
        )
        mock_get_service.return_value = mock_service

        update_data = {"name": "Updated Workflow", "description": "Updated description"}

        response = client.put("/definitions/def-123", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "def-123"

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_delete_workflow_definition_success(self, mock_get_service, client):
        """Test successful workflow definition deletion."""
        mock_service = Mock()
        mock_service.delete_workflow_definition = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service

        response = client.delete("/definitions/def-123")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_activate_workflow_definition_success(self, mock_get_service, client):
        """Test successful workflow definition activation."""
        mock_service = Mock()
        mock_service.activate_workflow_definition = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service

        response = client.post("/definitions/def-123/activate")
        assert response.status_code == 200
        assert "activated successfully" in response.json()["message"]

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_duplicate_workflow_definition_success(
        self, mock_get_service, client, sample_workflow_definition
    ):
        """Test successful workflow definition duplication."""
        mock_service = Mock()
        mock_service.duplicate_workflow_definition = AsyncMock(
            return_value=sample_workflow_definition
        )
        mock_get_service.return_value = mock_service

        response = client.post(
            "/definitions/def-123/duplicate?new_name=Duplicated&new_code=DUP_001"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "def-123"

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_validate_workflow_definition_success(self, mock_get_service, client):
        """Test successful workflow definition validation."""
        mock_service = Mock()
        mock_service.validate_workflow_definition = AsyncMock(
            return_value={"valid": True, "warnings": [], "errors": []}
        )
        mock_get_service.return_value = mock_service

        response = client.post("/definitions/def-123/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True


# =============================================================================
# Workflow Instance Management Tests
# =============================================================================


class TestWorkflowInstanceManagement:
    """Test workflow instance management endpoints."""

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_start_workflow_instance_success(
        self, mock_get_service, client, sample_workflow_instance
    ):
        """Test successful workflow instance start."""
        mock_service = Mock()
        mock_service.start_workflow_instance = AsyncMock(
            return_value=sample_workflow_instance
        )
        mock_get_service.return_value = mock_service

        instance_data = {
            "definition_id": "def-123",
            "title": "Test Instance",
            "entity_type": "document",
            "entity_id": "doc-123",
            "priority": "normal",
            "initiated_by": "user-123",
        }

        response = client.post("/instances", json=instance_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Instance"
        assert data["status"] == "running"

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_list_workflow_instances_success(
        self, mock_get_service, client, sample_workflow_instance
    ):
        """Test successful workflow instances listing."""
        mock_service = Mock()
        mock_service.list_workflow_instances = AsyncMock(
            return_value=([sample_workflow_instance], 1)
        )
        mock_get_service.return_value = mock_service

        response = client.get("/instances?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["instances"]) == 1

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_get_workflow_instance_success(
        self, mock_get_service, client, sample_workflow_instance
    ):
        """Test successful workflow instance retrieval."""
        mock_service = Mock()
        mock_service.get_workflow_instance = AsyncMock(
            return_value=sample_workflow_instance
        )
        mock_get_service.return_value = mock_service

        response = client.get("/instances/inst-123")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "inst-123"
        assert data["title"] == "Test Instance"

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_cancel_workflow_instance_success(self, mock_get_service, client):
        """Test successful workflow instance cancellation."""
        mock_service = Mock()
        mock_service.cancel_workflow_instance = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service

        response = client.post(
            "/instances/inst-123/cancel?reason=Test+cancellation&cancelled_by=user-123"
        )
        assert response.status_code == 200
        assert "cancelled successfully" in response.json()["message"]

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_suspend_workflow_instance_success(self, mock_get_service, client):
        """Test successful workflow instance suspension."""
        mock_service = Mock()
        mock_service.suspend_workflow_instance = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service

        response = client.post(
            "/instances/inst-123/suspend?reason=Test+suspension&suspended_by=user-123"
        )
        assert response.status_code == 200
        assert "suspended successfully" in response.json()["message"]

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_get_workflow_progress_success(self, mock_get_service, client):
        """Test successful workflow progress retrieval."""
        mock_service = Mock()
        mock_service.get_workflow_progress = AsyncMock(
            return_value={
                "progress_percentage": 33.33,
                "current_step": "Review",
                "remaining_steps": 2,
            }
        )
        mock_get_service.return_value = mock_service

        response = client.get("/instances/inst-123/progress")
        assert response.status_code == 200
        data = response.json()
        assert data["progress_percentage"] == 33.33

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_reassign_workflow_instance_success(self, mock_get_service, client):
        """Test successful workflow instance reassignment."""
        mock_service = Mock()
        mock_service.reassign_workflow_instance = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service

        response = client.post(
            "/instances/inst-123/reassign?new_assignee_id=user-456&reassigned_by=user-123"
        )
        assert response.status_code == 200
        assert "reassigned successfully" in response.json()["message"]


# =============================================================================
# Task Management Tests
# =============================================================================


class TestTaskManagement:
    """Test task management endpoints."""

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_list_workflow_tasks_success(
        self, mock_get_service, client, sample_workflow_task
    ):
        """Test successful workflow tasks listing."""
        mock_service = Mock()
        mock_service.list_workflow_tasks = AsyncMock(
            return_value=([sample_workflow_task], 1)
        )
        mock_get_service.return_value = mock_service

        response = client.get("/tasks?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["tasks"]) == 1

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_get_workflow_task_success(
        self, mock_get_service, client, sample_workflow_task
    ):
        """Test successful workflow task retrieval."""
        mock_service = Mock()
        mock_service.get_workflow_task = AsyncMock(return_value=sample_workflow_task)
        mock_get_service.return_value = mock_service

        response = client.get("/tasks/task-123")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "task-123"
        assert data["name"] == "Test Task"

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_perform_task_action_success(self, mock_get_service, client):
        """Test successful task action performance."""
        mock_service = Mock()
        mock_service.perform_task_action = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service

        action_data = {
            "action_type": "approve",
            "result": "approved",
            "notes": "Task approved",
            "performed_by": "user-123",
        }

        response = client.post("/tasks/task-123/action", json=action_data)
        assert response.status_code == 200
        assert "performed successfully" in response.json()["message"]

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_assign_task_success(self, mock_get_service, client):
        """Test successful task assignment."""
        mock_service = Mock()
        mock_service.assign_task = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service

        assignment_data = {
            "assignee_id": "user-456",
            "assigned_by": "user-123",
            "assignment_reason": "Expert in this area",
            "notify_assignee": True,
        }

        response = client.post("/tasks/task-123/assign", json=assignment_data)
        assert response.status_code == 200
        assert "assigned successfully" in response.json()["message"]

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_delegate_task_success(self, mock_get_service, client):
        """Test successful task delegation."""
        mock_service = Mock()
        mock_service.delegate_task = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service

        delegation_data = {
            "delegate_to": "user-456",
            "delegated_by": "user-123",
            "delegation_reason": "Temporary delegation",
            "temporary": True,
        }

        response = client.post("/tasks/task-123/delegate", json=delegation_data)
        assert response.status_code == 200
        assert "delegated successfully" in response.json()["message"]

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_escalate_task_success(self, mock_get_service, client):
        """Test successful task escalation."""
        mock_service = Mock()
        mock_service.escalate_task = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service

        escalation_data = {
            "escalate_to": "manager-123",
            "escalation_reason": "Requires management approval",
            "escalation_type": "manual",
            "priority_increase": True,
        }

        response = client.post("/tasks/task-123/escalate", json=escalation_data)
        assert response.status_code == 200
        assert "escalated successfully" in response.json()["message"]

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_start_task_success(self, mock_get_service, client):
        """Test successful task start."""
        mock_service = Mock()
        mock_service.start_task = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service

        response = client.post("/tasks/task-123/start?started_by=user-123")
        assert response.status_code == 200
        assert "started successfully" in response.json()["message"]

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_complete_task_success(self, mock_get_service, client):
        """Test successful task completion."""
        mock_service = Mock()
        mock_service.complete_task = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service

        response = client.post(
            "/tasks/task-123/complete?result=completed&completed_by=user-123"
        )
        assert response.status_code == 200
        assert "completed successfully" in response.json()["message"]

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_get_my_tasks_success(self, mock_get_service, client, sample_workflow_task):
        """Test successful user tasks retrieval."""
        mock_service = Mock()
        mock_service.list_workflow_tasks = AsyncMock(
            return_value=([sample_workflow_task], 1)
        )
        mock_get_service.return_value = mock_service

        response = client.get(
            "/tasks/my-tasks?user_id=user-123&organization_id=org-123"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1


# =============================================================================
# Comments Management Tests
# =============================================================================


class TestCommentsManagement:
    """Test comments management endpoints."""

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_create_comment_success(self, mock_get_service, client):
        """Test successful comment creation."""
        mock_service = Mock()
        mock_comment = Mock()
        mock_comment.__dict__ = {
            "id": "comment-123",
            "task_id": "task-123",
            "comment_text": "Test comment",
            "author_id": "user-123",
            "created_at": datetime.now(),
        }
        mock_service.create_comment = AsyncMock(return_value=mock_comment)
        mock_get_service.return_value = mock_service

        comment_data = {
            "organization_id": "org-123",
            "comment_text": "Test comment",
            "comment_type": "general",
            "is_internal": False,
            "author_id": "user-123",
        }

        response = client.post("/tasks/task-123/comments", json=comment_data)
        assert response.status_code == 200
        data = response.json()
        assert data["comment_text"] == "Test comment"

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_list_task_comments_success(self, mock_get_service, client):
        """Test successful task comments listing."""
        mock_service = Mock()
        mock_comment = Mock()
        mock_comment.__dict__ = {
            "id": "comment-123",
            "task_id": "task-123",
            "comment_text": "Test comment",
            "author_id": "user-123",
        }
        mock_service.list_task_comments = AsyncMock(return_value=([mock_comment], 1))
        mock_get_service.return_value = mock_service

        response = client.get("/tasks/task-123/comments")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_update_comment_success(self, mock_get_service, client):
        """Test successful comment update."""
        mock_service = Mock()
        mock_comment = Mock()
        mock_comment.__dict__ = {
            "id": "comment-123",
            "comment_text": "Updated comment",
            "is_edited": True,
        }
        mock_service.update_comment = AsyncMock(return_value=mock_comment)
        mock_get_service.return_value = mock_service

        response = client.put(
            "/comments/comment-123?comment_text=Updated+comment&updated_by=user-123"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["comment_text"] == "Updated comment"

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_delete_comment_success(self, mock_get_service, client):
        """Test successful comment deletion."""
        mock_service = Mock()
        mock_service.delete_comment = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service

        response = client.delete("/comments/comment-123?deleted_by=user-123")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]


# =============================================================================
# Attachments Management Tests
# =============================================================================


class TestAttachmentsManagement:
    """Test attachments management endpoints."""

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_upload_attachment_success(self, mock_get_service, client):
        """Test successful attachment upload."""
        mock_service = Mock()
        mock_attachment = Mock()
        mock_attachment.__dict__ = {
            "id": "attach-123",
            "task_id": "task-123",
            "filename": "test.pdf",
            "file_size": 1024,
            "uploaded_by": "user-123",
        }
        mock_service.upload_attachment = AsyncMock(return_value=mock_attachment)
        mock_get_service.return_value = mock_service

        attachment_data = {
            "organization_id": "org-123",
            "filename": "test.pdf",
            "file_path": "/uploads/test.pdf",
            "file_size": 1024,
            "mime_type": "application/pdf",
            "uploaded_by": "user-123",
        }

        response = client.post("/tasks/task-123/attachments", json=attachment_data)
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.pdf"

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_list_task_attachments_success(self, mock_get_service, client):
        """Test successful task attachments listing."""
        mock_service = Mock()
        mock_attachment = Mock()
        mock_attachment.__dict__ = {
            "id": "attach-123",
            "task_id": "task-123",
            "filename": "test.pdf",
        }
        mock_service.list_task_attachments = AsyncMock(
            return_value=([mock_attachment], 1)
        )
        mock_get_service.return_value = mock_service

        response = client.get("/tasks/task-123/attachments")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_download_attachment_success(self, mock_get_service, client):
        """Test successful attachment download."""
        mock_service = Mock()
        mock_service.download_attachment = AsyncMock(
            return_value={
                "filename": "test.pdf",
                "file_path": "/uploads/test.pdf",
                "mime_type": "application/pdf",
            }
        )
        mock_get_service.return_value = mock_service

        response = client.get("/attachments/attach-123/download")
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.pdf"

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_delete_attachment_success(self, mock_get_service, client):
        """Test successful attachment deletion."""
        mock_service = Mock()
        mock_service.delete_attachment = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service

        response = client.delete("/attachments/attach-123?deleted_by=user-123")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]


# =============================================================================
# Analytics & Reporting Tests
# =============================================================================


class TestAnalyticsReporting:
    """Test analytics and reporting endpoints."""

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_generate_workflow_analytics_success(self, mock_get_service, client):
        """Test successful workflow analytics generation."""
        mock_service = Mock()
        mock_service.generate_workflow_analytics = AsyncMock(
            return_value={
                "organization_id": "org-123",
                "period_start": date.today() - timedelta(days=30),
                "period_end": date.today(),
                "total_instances": 100,
                "completed_instances": 85,
                "sla_compliance_rate": Decimal("95.5"),
            }
        )
        mock_get_service.return_value = mock_service

        analytics_request = {
            "organization_id": "org-123",
            "period_start": str(date.today() - timedelta(days=30)),
            "period_end": str(date.today()),
        }

        response = client.post("/analytics", json=analytics_request)
        assert response.status_code == 200
        data = response.json()
        assert data["total_instances"] == 100

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_get_workflow_dashboard_success(self, mock_get_service, client):
        """Test successful workflow dashboard retrieval."""
        mock_service = Mock()
        mock_service.get_workflow_dashboard = AsyncMock(
            return_value={
                "active_instances": 25,
                "overdue_tasks": 5,
                "completed_instances_period": 100,
                "average_completion_time_hours": 48.5,
                "top_bottlenecks": [],
                "period_start": str(date.today() - timedelta(days=30)),
                "period_end": str(date.today()),
            }
        )
        mock_get_service.return_value = mock_service

        response = client.get("/analytics/dashboard?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert data["active_instances"] == 25

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_get_performance_metrics_success(self, mock_get_service, client):
        """Test successful performance metrics retrieval."""
        mock_service = Mock()
        mock_service.get_performance_metrics = AsyncMock(
            return_value={
                "average_completion_time": 45.2,
                "sla_compliance_rate": 95.5,
                "throughput": 125,
            }
        )
        mock_get_service.return_value = mock_service

        period_start = date.today() - timedelta(days=30)
        period_end = date.today()

        response = client.get(
            f"/analytics/performance?organization_id=org-123&period_start={period_start}&period_end={period_end}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["average_completion_time"] == 45.2

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_analyze_bottlenecks_success(self, mock_get_service, client):
        """Test successful bottleneck analysis."""
        mock_service = Mock()
        mock_service.analyze_bottlenecks = AsyncMock(
            return_value={
                "bottlenecks": [
                    {
                        "step_name": "Manager Review",
                        "average_time": 72.5,
                        "frequency": 15,
                    }
                ],
                "recommendations": ["Consider parallel approval process"],
            }
        )
        mock_get_service.return_value = mock_service

        response = client.get("/analytics/bottlenecks?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert len(data["bottlenecks"]) == 1

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_get_sla_compliance_success(self, mock_get_service, client):
        """Test successful SLA compliance retrieval."""
        mock_service = Mock()
        mock_service.get_sla_compliance = AsyncMock(
            return_value={
                "compliance_rate": 95.5,
                "total_instances": 100,
                "breached_instances": 4,
                "average_deviation": 2.5,
            }
        )
        mock_get_service.return_value = mock_service

        period_start = date.today() - timedelta(days=30)
        period_end = date.today()

        response = client.get(
            f"/analytics/sla-compliance?organization_id=org-123&period_start={period_start}&period_end={period_end}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["compliance_rate"] == 95.5


# =============================================================================
# Templates Management Tests
# =============================================================================


class TestTemplatesManagement:
    """Test templates management endpoints."""

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_list_workflow_templates_success(self, mock_get_service, client):
        """Test successful workflow templates listing."""
        mock_service = Mock()
        mock_template = Mock()
        mock_template.__dict__ = {
            "id": "template-123",
            "name": "Test Template",
            "category": "Approval",
            "usage_count": 25,
        }
        mock_service.list_workflow_templates = AsyncMock(
            return_value=([mock_template], 1)
        )
        mock_get_service.return_value = mock_service

        response = client.get("/templates?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_get_workflow_template_success(self, mock_get_service, client):
        """Test successful workflow template retrieval."""
        mock_service = Mock()
        mock_template = Mock()
        mock_template.__dict__ = {
            "id": "template-123",
            "name": "Test Template",
            "description": "Template description",
        }
        mock_service.get_workflow_template = AsyncMock(return_value=mock_template)
        mock_get_service.return_value = mock_service

        response = client.get("/templates/template-123")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Template"

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_instantiate_template_success(
        self, mock_get_service, client, sample_workflow_definition
    ):
        """Test successful template instantiation."""
        mock_service = Mock()
        mock_service.instantiate_template = AsyncMock(
            return_value=sample_workflow_definition
        )
        mock_get_service.return_value = mock_service

        response = client.post(
            "/templates/template-123/instantiate?name=From+Template&code=TMPL_001&organization_id=org-123&created_by=user-123"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Workflow"

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_get_popular_templates_success(self, mock_get_service, client):
        """Test successful popular templates retrieval."""
        mock_service = Mock()
        mock_template = Mock()
        mock_template.__dict__ = {
            "id": "template-123",
            "name": "Popular Template",
            "usage_count": 100,
        }
        mock_service.get_popular_templates = AsyncMock(
            return_value=([mock_template], 1)
        )
        mock_get_service.return_value = mock_service

        response = client.get("/templates/popular?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1


# =============================================================================
# Activity Log & Audit Tests
# =============================================================================


class TestActivityLogAudit:
    """Test activity log and audit endpoints."""

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_get_instance_activities_success(self, mock_get_service, client):
        """Test successful instance activities retrieval."""
        mock_service = Mock()
        mock_activity = Mock()
        mock_activity.__dict__ = {
            "id": "activity-123",
            "instance_id": "inst-123",
            "activity_type": "task_assigned",
            "performed_by": "user-123",
        }
        mock_service.get_instance_activities = AsyncMock(
            return_value=([mock_activity], 1)
        )
        mock_get_service.return_value = mock_service

        response = client.get("/instances/inst-123/activities")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_get_task_activities_success(self, mock_get_service, client):
        """Test successful task activities retrieval."""
        mock_service = Mock()
        mock_activity = Mock()
        mock_activity.__dict__ = {
            "id": "activity-123",
            "task_id": "task-123",
            "activity_type": "task_completed",
            "performed_by": "user-123",
        }
        mock_service.get_task_activities = AsyncMock(return_value=([mock_activity], 1))
        mock_get_service.return_value = mock_service

        response = client.get("/tasks/task-123/activities")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_get_audit_trail_success(self, mock_get_service, client):
        """Test successful audit trail retrieval."""
        mock_service = Mock()
        mock_service.get_audit_trail = AsyncMock(
            return_value={
                "audit_entries": [
                    {
                        "timestamp": datetime.now().isoformat(),
                        "action": "workflow_started",
                        "user": "user-123",
                        "entity": "workflow_instance",
                    }
                ],
                "total_count": 1,
            }
        )
        mock_get_service.return_value = mock_service

        response = client.get("/activities/audit-trail?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert len(data["audit_entries"]) == 1

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_get_user_activity_success(self, mock_get_service, client):
        """Test successful user activity retrieval."""
        mock_service = Mock()
        mock_service.get_user_activity = AsyncMock(
            return_value={
                "user_id": "user-123",
                "total_actions": 50,
                "recent_activities": [],
                "productivity_score": 85.5,
            }
        )
        mock_get_service.return_value = mock_service

        response = client.get(
            "/activities/user-activity?user_id=user-123&organization_id=org-123"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_actions"] == 50

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_export_activities_success(self, mock_get_service, client):
        """Test successful activities export."""
        mock_service = Mock()
        mock_service.export_activities = AsyncMock(
            return_value={
                "export_id": "export-123",
                "format": "csv",
                "download_url": "/downloads/activities.csv",
                "row_count": 500,
            }
        )
        mock_get_service.return_value = mock_service

        response = client.post("/activities/export?organization_id=org-123&format=csv")
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "csv"
        assert data["row_count"] == 500


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Test error handling scenarios."""

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_service_error_handling(self, mock_get_service, client):
        """Test service error handling."""
        mock_service = Mock()
        mock_service.get_workflow_definition = AsyncMock(
            side_effect=Exception("Service error")
        )
        mock_get_service.return_value = mock_service

        response = client.get("/definitions/def-123")
        assert response.status_code == 400
        assert "Failed to get workflow definition" in response.json()["detail"]

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_not_found_error_handling(self, mock_get_service, client):
        """Test not found error handling."""
        mock_service = Mock()
        mock_service.get_workflow_instance = AsyncMock(return_value=None)
        mock_get_service.return_value = mock_service

        response = client.get("/instances/nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_validation_error_handling(self, client):
        """Test validation error handling."""
        # Test with missing required fields
        response = client.post("/definitions", json={})
        assert response.status_code == 422  # Unprocessable Entity

    def test_query_parameter_validation(self, client):
        """Test query parameter validation."""
        # Test with invalid page number
        response = client.get("/definitions?organization_id=org-123&page=0")
        assert response.status_code == 422  # Unprocessable Entity


# =============================================================================
# Integration Tests
# =============================================================================


class TestWorkflowIntegration:
    """Test workflow system integration scenarios."""

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_complete_workflow_lifecycle(
        self,
        mock_get_service,
        client,
        sample_workflow_definition,
        sample_workflow_instance,
        sample_workflow_task,
    ):
        """Test complete workflow lifecycle."""
        mock_service = Mock()

        # Mock sequential operations
        mock_service.create_workflow_definition = AsyncMock(
            return_value=sample_workflow_definition
        )
        mock_service.start_workflow_instance = AsyncMock(
            return_value=sample_workflow_instance
        )
        mock_service.get_workflow_task = AsyncMock(return_value=sample_workflow_task)
        mock_service.complete_task = AsyncMock(return_value=True)
        mock_service.get_workflow_instance = AsyncMock(
            return_value=sample_workflow_instance
        )

        mock_get_service.return_value = mock_service

        # 1. Create workflow definition
        definition_data = {
            "organization_id": "org-123",
            "name": "Test Workflow",
            "code": "TEST_WF_001",
            "definition_schema": {"steps": [{"id": "step1", "name": "Review"}]},
            "created_by": "user-123",
        }

        response = client.post("/definitions", json=definition_data)
        assert response.status_code == 200

        # 2. Start workflow instance
        instance_data = {
            "definition_id": "def-123",
            "title": "Test Instance",
            "initiated_by": "user-123",
        }

        response = client.post("/instances", json=instance_data)
        assert response.status_code == 200

        # 3. Get and complete task
        response = client.get("/tasks/task-123")
        assert response.status_code == 200

        response = client.post(
            "/tasks/task-123/complete?result=completed&completed_by=user-123"
        )
        assert response.status_code == 200

        # 4. Check instance status
        response = client.get("/instances/inst-123")
        assert response.status_code == 200

    @patch("app.api.v1.workflow_v31.get_workflow_service")
    def test_workflow_with_comments_and_attachments(self, mock_get_service, client):
        """Test workflow with comments and attachments."""
        mock_service = Mock()

        # Mock comment creation
        mock_comment = Mock()
        mock_comment.__dict__ = {
            "id": "comment-123",
            "comment_text": "Progress update",
            "author_id": "user-123",
        }
        mock_service.create_comment = AsyncMock(return_value=mock_comment)

        # Mock attachment upload
        mock_attachment = Mock()
        mock_attachment.__dict__ = {
            "id": "attach-123",
            "filename": "document.pdf",
            "uploaded_by": "user-123",
        }
        mock_service.upload_attachment = AsyncMock(return_value=mock_attachment)

        mock_get_service.return_value = mock_service

        # Add comment
        comment_data = {
            "organization_id": "org-123",
            "comment_text": "Progress update",
            "author_id": "user-123",
        }

        response = client.post("/tasks/task-123/comments", json=comment_data)
        assert response.status_code == 200

        # Add attachment
        attachment_data = {
            "organization_id": "org-123",
            "filename": "document.pdf",
            "file_path": "/uploads/document.pdf",
            "file_size": 2048,
            "uploaded_by": "user-123",
        }

        response = client.post("/tasks/task-123/attachments", json=attachment_data)
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__])
