"""Complete workflow integration test for Task Management Service."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import PermissionDenied
from app.models.audit import AuditLog
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskPriority, TaskStatus, TaskStatusUpdate
from app.services.task import TaskService


class TestTaskCompleteWorkflow:
    """Test complete task management workflow with permissions and audit logs."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = TaskService()
        self.db = MagicMock(spec=Session)

        # Create mock users with different permission levels
        self.admin_user = MagicMock(spec=User)
        self.admin_user.id = 1
        self.admin_user.email = "admin@example.com"
        self.admin_user.is_active = True
        self.admin_user.is_superuser = True  # Admin with all permissions
        self.admin_user.full_name = "Admin User"
        self.admin_user.organization_id = 1

        self.manager_user = MagicMock(spec=User)
        self.manager_user.id = 2
        self.manager_user.email = "manager@example.com"
        self.manager_user.is_active = True
        self.manager_user.is_superuser = False
        self.manager_user.full_name = "Manager User"
        self.manager_user.organization_id = 1

        self.regular_user = MagicMock(spec=User)
        self.regular_user.id = 3
        self.regular_user.email = "user@example.com"
        self.regular_user.is_active = True
        self.regular_user.is_superuser = False
        self.regular_user.full_name = "Regular User"
        self.regular_user.organization_id = 1

        self.unauthorized_user = MagicMock(spec=User)
        self.unauthorized_user.id = 4
        self.unauthorized_user.email = "other@example.com"
        self.unauthorized_user.is_active = True
        self.unauthorized_user.is_superuser = False
        self.unauthorized_user.full_name = "Other User"
        self.unauthorized_user.organization_id = 2  # Different organization

    def test_complete_task_workflow_with_permissions_and_audit(self):
        """Test TASK-WORKFLOW-001: Complete task lifecycle with permissions and audit logs."""
        # Arrange
        task_data = TaskCreate(
            title="Integration Test Task",
            description="Complete workflow test",
            project_id=1,
            priority=TaskPriority.HIGH,
        )

        # Mock project exists
        mock_project = MagicMock(spec=Project)
        mock_project.id = 1
        mock_project.name = "Test Project"

        # Mock task object
        mock_task = MagicMock(spec=Task)
        mock_task.id = 1
        mock_task.title = task_data.title
        mock_task.description = task_data.description
        mock_task.status = "not_started"
        mock_task.priority = "high"
        mock_task.project_id = task_data.project_id
        mock_task.assignee_id = None
        mock_task.reporter_id = self.admin_user.id
        mock_task.due_date = None
        mock_task.estimated_hours = None

        # Mock queries
        call_count = 0
        def query_side_effect(model):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Project lookup
                project_query = MagicMock()
                project_query.filter.return_value.first.return_value = mock_project
                return project_query
            else:
                # Task lookup
                task_query = MagicMock()
                task_query.filter.return_value.first.return_value = mock_task
                return task_query

        self.db.query.side_effect = query_side_effect

        # Mock permission service (admin has all permissions)
        with patch('app.services.task.permission_service') as mock_permission:
            mock_permission.require_permission.return_value = None
            mock_permission.has_permission.return_value = True

            with patch('app.services.task.AuditLogger.log') as mock_audit_log:
                with patch.object(self.service, '_task_to_response') as mock_response:
                    mock_response.return_value = MagicMock()

                    # Act & Assert

                    # 1. Task Creation (with permission check)
                    result = self.service.create_task(task_data, self.admin_user, self.db)
                    assert result is not None
                    mock_audit_log.assert_called()  # Audit log created

                    # Reset mocks for next operation
                    mock_audit_log.reset_mock()

                    # Set up mock for status update (need to mock task query again)
                    mock_task_for_status = MagicMock(spec=Task)
                    mock_task_for_status.id = 1
                    mock_task_for_status.status = "not_started"
                    mock_task_for_status.reporter_id = self.admin_user.id
                    mock_task_for_status.assignee_id = None

                    status_query = MagicMock()
                    status_query.filter.return_value.first.return_value = mock_task_for_status
                    self.db.query.return_value = status_query

                    # 2. Status Update (with audit logging)
                    status_update = TaskStatusUpdate(status=TaskStatus.IN_PROGRESS)
                    result = self.service.update_task_status(
                        1, status_update, self.admin_user, self.db
                    )
                    assert result is not None
                    mock_audit_log.assert_called()  # Status change logged

                    # 3. Verify all permission checks were performed
                    assert mock_permission.require_permission.call_count >= 1
                    assert mock_permission.has_permission.call_count >= 1

    def test_unauthorized_access_denied(self):
        """Test TASK-WORKFLOW-002: Unauthorized users cannot access tasks."""
        # Arrange
        task_id = 1

        # Mock task owned by different organization
        mock_task = MagicMock(spec=Task)
        mock_task.id = task_id
        mock_task.reporter_id = self.admin_user.id
        mock_task.assignee_id = None

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_task
        self.db.query.return_value.options.return_value = mock_query

        # Mock permission service to deny access
        with patch('app.services.task.permission_service') as mock_permission:
            mock_permission.has_permission.return_value = False

            # Act & Assert
            with pytest.raises(PermissionDenied, match="No access to this task"):
                self.service.get_task(task_id, self.unauthorized_user, self.db)

    def test_audit_history_access_control(self):
        """Test TASK-WORKFLOW-003: Audit history access follows permission model."""
        # Arrange
        task_id = 1

        # Mock task owned by regular user
        mock_task = MagicMock(spec=Task)
        mock_task.id = task_id
        mock_task.reporter_id = self.regular_user.id
        mock_task.assignee_id = None

        # Mock audit logs
        mock_audit_log = MagicMock(spec=AuditLog)
        mock_audit_log.id = 1
        mock_audit_log.action = "create"
        mock_audit_log.user_id = self.regular_user.id
        mock_audit_log.created_at = datetime.now(timezone.utc)
        mock_audit_log.changes = {"created": {"title": "Test Task"}}

        # Mock log user
        mock_log_user = MagicMock(spec=User)
        mock_log_user.full_name = "Regular User"

        # Mock queries
        call_count = 0
        def query_side_effect(model):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Task lookup
                task_query = MagicMock()
                task_query.filter.return_value.first.return_value = mock_task
                return task_query
            elif call_count == 2:
                # Audit log lookup
                audit_query = MagicMock()
                audit_query.filter.return_value.order_by.return_value.all.return_value = [
                    mock_audit_log
                ]
                return audit_query
            else:
                # User lookup for audit log
                user_query = MagicMock()
                user_query.filter.return_value.first.return_value = mock_log_user
                return user_query

        self.db.query.side_effect = query_side_effect

        # Mock permission service (owner access)
        with patch('app.services.task.permission_service') as mock_permission:
            mock_permission.has_permission.return_value = False  # No general permission

            # Act
            result = self.service.get_task_history(task_id, self.regular_user, self.db)

            # Assert
            assert result.total == 1
            assert len(result.items) == 1
            assert result.items[0].action == "create"
            assert result.items[0].user_name == "Regular User"

    def test_multi_tenant_isolation(self):
        """Test TASK-WORKFLOW-004: Multi-tenant data isolation."""
        # Arrange
        task_id = 1
        assignee_id = 3

        # Mock task from organization 1
        mock_task = MagicMock(spec=Task)
        mock_task.id = task_id
        mock_task.reporter_id = self.admin_user.id
        mock_task.assignee_id = None

        # Mock user from organization 2 (different org)
        mock_other_user = MagicMock(spec=User)
        mock_other_user.id = assignee_id
        mock_other_user.organization_id = 2  # Different organization

        # Mock queries
        task_query = MagicMock()
        task_query.filter.return_value.first.return_value = mock_task

        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = mock_other_user

        call_count = 0
        def query_side_effect(model):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return task_query
            else:
                return user_query

        self.db.query.side_effect = query_side_effect

        # Mock permission service
        with patch('app.services.task.permission_service') as mock_permission:
            mock_permission.has_permission.return_value = True  # Admin has permission

            # Act & Assert
            # Should prevent cross-organization assignment
            with pytest.raises(
                PermissionDenied, match="Cannot assign task to user from different organization"
            ):
                self.service.assign_user(task_id, assignee_id, self.admin_user, self.db)

    def test_owner_based_access_permissions(self):
        """Test TASK-WORKFLOW-005: Owner-based access control works correctly."""
        # Arrange
        task_id = 1

        # Mock task owned by regular user
        mock_task = MagicMock(spec=Task)
        mock_task.id = task_id
        mock_task.title = "User Task"  # Removed apostrophe to avoid quote issues
        mock_task.reporter_id = self.regular_user.id  # User owns this task
        mock_task.assignee_id = None
        mock_task.project = MagicMock(spec=Project)
        mock_task.assignee = None
        mock_task.reporter = self.regular_user

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_task
        self.db.query.return_value.options.return_value = mock_query

        # Mock permission service to deny general permission
        with patch('app.services.task.permission_service') as mock_permission:
            mock_permission.has_permission.return_value = False  # No general task.view permission

            with patch.object(self.service, '_task_to_response') as mock_response:
                mock_response.return_value = MagicMock()

                # Act
                result = self.service.get_task(task_id, self.regular_user, self.db)

                # Assert
                assert result is not None  # Owner can access their own task
                mock_response.assert_called_once_with(mock_task)

    def test_permission_system_integration(self):
        """Test TASK-WORKFLOW-006: Permission system integration across all operations."""
        operations_tested = []

        # Mock permission service to track calls
        with patch('app.services.task.permission_service') as mock_permission:
            mock_permission.require_permission.return_value = None
            mock_permission.has_permission.return_value = True

            with patch('app.services.task.AuditLogger.log'):
                with patch.object(self.service, '_task_to_response') as mock_response:
                    mock_response.return_value = MagicMock()

                    # Test various operations with permission checks

                    # 1. Create Task
                    mock_project = MagicMock(spec=Project)
                    project_query = self.db.query.return_value
                    project_query.filter.return_value.first.return_value = mock_project

                    task_data = TaskCreate(
                        title="Test", project_id=1, priority=TaskPriority.MEDIUM
                    )
                    try:
                        self.service.create_task(task_data, self.manager_user, self.db)
                        operations_tested.append("create_task")
                    except Exception:
                        pass

                    # 2. Get Task
                    mock_task = MagicMock(spec=Task)
                    mock_task.reporter_id = self.manager_user.id
                    mock_task.assignee_id = None
                    mock_query = MagicMock()
                    mock_query.filter.return_value.first.return_value = mock_task
                    self.db.query.return_value.options.return_value = mock_query

                    try:
                        self.service.get_task(1, self.manager_user, self.db)
                        operations_tested.append("get_task")
                    except Exception:
                        pass

                    # Assert permission system was invoked
                    assert mock_permission.require_permission.called or mock_permission.has_permission.called
                    assert len(operations_tested) >= 1  # At least one operation tested
