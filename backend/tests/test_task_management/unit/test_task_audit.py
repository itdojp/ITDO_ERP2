"""Unit tests for Task Service audit log functionality."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import PermissionDenied
from app.models.audit import AuditLog
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskPriority, TaskUpdate
from app.services.task import TaskService


class TestTaskAuditLog:
    """Test suite for Task Service audit logging."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = TaskService()
        self.db = MagicMock(spec=Session)

        # Create mock user
        self.test_user = MagicMock(spec=User)
        self.test_user.id = 1
        self.test_user.email = "test@example.com"
        self.test_user.is_active = True
        self.test_user.is_superuser = False
        self.test_user.full_name = "Test User"
        self.test_user.organization_id = 1

    def test_create_task_logs_audit_entry(self):
        """Test that task creation creates audit log entry."""
        # Arrange
        task_data = TaskCreate(
            title="New Task",
            description="Task description",
            project_id=1,
            priority=TaskPriority.MEDIUM,
        )

        # Mock project exists
        from app.models.project import Project

        mock_project = MagicMock(spec=Project)
        mock_project.id = 1
        self.db.query.return_value.filter.return_value.first.return_value = mock_project

        # Mock permission service
        with patch("app.services.task.permission_service") as mock_permission:
            mock_permission.require_permission.return_value = None

            # Mock AuditLogger
            with patch("app.services.task.AuditLogger") as mock_audit_logger:
                with patch.object(self.service, "_task_to_response") as mock_response:
                    mock_response.return_value = MagicMock()

                    # Act
                    self.service.create_task(
                        task_data, self.test_user, self.db
                    )

        # Assert audit log was called
        mock_audit_logger.log.assert_called_once()
        call_args = mock_audit_logger.log.call_args
        assert call_args[1]["action"] == "create"
        assert call_args[1]["resource_type"] == "task"
        # The resource_id will be the ID of whatever task object was created
        assert call_args[1]["user"] == self.test_user
        assert "created" in call_args[1]["changes"]
        assert "title" in call_args[1]["changes"]["created"]

    def test_update_task_logs_changes(self):
        """Test that task updates log field changes."""
        # Arrange
        task_id = 1
        update_data = TaskUpdate(
            title="Updated Task", description="Updated description"
        )

        # Mock existing task
        mock_task = MagicMock(spec=Task)
        mock_task.id = task_id
        mock_task.title = "Old Task"
        mock_task.description = "Old description"
        mock_task.status = "not_started"
        mock_task.priority = "medium"
        mock_task.assignee_id = None
        mock_task.due_date = None
        mock_task.estimated_hours = None
        mock_task.reporter_id = self.test_user.id
        mock_task.assignee_id = None
        self.db.query.return_value.filter.return_value.first.return_value = mock_task

        # Mock permission service
        with patch("app.services.task.permission_service") as mock_permission:
            mock_permission.has_permission.return_value = False  # Owner access

            # Mock AuditLogger
            with patch("app.services.task.AuditLogger") as mock_audit_logger:
                with patch.object(self.service, "_task_to_response") as mock_response:
                    mock_response.return_value = MagicMock()

                    # Act
                    self.service.update_task(
                        task_id, update_data, self.test_user, self.db
                    )

        # Assert audit log was called
        mock_audit_logger.log.assert_called_once()
        call_args = mock_audit_logger.log.call_args
        assert call_args[1]["action"] == "update"
        assert call_args[1]["resource_type"] == "task"
        assert call_args[1]["resource_id"] == mock_task.id
        assert call_args[1]["user"] == self.test_user

        # Check that changes are recorded
        changes = call_args[1]["changes"]
        assert "title" in changes
        assert changes["title"]["old"] == "Old Task"
        assert changes["title"]["new"] == "Updated Task"

    def test_delete_task_logs_deletion(self):
        """Test that task deletion creates audit log entry."""
        # Arrange
        task_id = 1

        # Mock existing task
        mock_task = MagicMock(spec=Task)
        mock_task.id = task_id
        mock_task.title = "Task to delete"
        mock_task.description = "Description"
        mock_task.status = "not_started"
        mock_task.priority = "medium"
        mock_task.project_id = 1
        mock_task.assignee_id = None
        mock_task.due_date = None
        mock_task.estimated_hours = None
        mock_task.reporter_id = self.test_user.id
        self.db.query.return_value.filter.return_value.first.return_value = mock_task

        # Mock permission service
        with patch("app.services.task.permission_service") as mock_permission:
            mock_permission.has_permission.return_value = False  # Creator access

            # Mock AuditLogger
            with patch("app.services.task.AuditLogger") as mock_audit_logger:
                # Act
                self.service.delete_task(task_id, self.test_user, self.db)

        # Assert audit log was called
        mock_audit_logger.log.assert_called_once()
        call_args = mock_audit_logger.log.call_args
        assert call_args[1]["action"] == "delete"
        assert call_args[1]["resource_type"] == "task"
        assert call_args[1]["resource_id"] == mock_task.id
        assert call_args[1]["user"] == self.test_user
        assert "deleted" in call_args[1]["changes"]

    def test_assign_user_logs_assignment(self):
        """Test that user assignment creates audit log entry."""
        # Arrange
        task_id = 1
        assignee_id = 2

        # Mock existing task
        mock_task = MagicMock(spec=Task)
        mock_task.id = task_id
        mock_task.assignee_id = None  # Currently unassigned
        mock_task.reporter_id = self.test_user.id

        # Mock assignee user
        mock_assignee = MagicMock(spec=User)
        mock_assignee.id = assignee_id
        mock_assignee.organization_id = self.test_user.organization_id

        # Mock queries
        task_query = MagicMock()
        task_query.filter.return_value.first.return_value = mock_task

        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = mock_assignee

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
        with patch("app.services.task.permission_service") as mock_permission:
            mock_permission.has_permission.return_value = False  # Creator access

            # Mock AuditLogger
            with patch("app.services.task.AuditLogger") as mock_audit_logger:
                with patch.object(self.service, "_task_to_response") as mock_response:
                    mock_response.return_value = MagicMock()

                    # Act
                    self.service.assign_user(
                        task_id, assignee_id, self.test_user, self.db
                    )

        # Assert audit log was called
        mock_audit_logger.log.assert_called_once()
        call_args = mock_audit_logger.log.call_args
        assert call_args[1]["action"] == "assign_user"
        assert call_args[1]["resource_type"] == "task"
        assert call_args[1]["resource_id"] == mock_task.id
        assert call_args[1]["user"] == self.test_user

        # Check assignment change
        changes = call_args[1]["changes"]
        assert "assignee_id" in changes
        assert changes["assignee_id"]["old"] is None
        assert changes["assignee_id"]["new"] == assignee_id

    def test_get_task_history_returns_audit_logs(self):
        """Test that get_task_history returns audit log entries."""
        # Arrange
        task_id = 1

        # Mock existing task owned by user
        mock_task = MagicMock(spec=Task)
        mock_task.id = task_id
        mock_task.reporter_id = self.test_user.id
        mock_task.assignee_id = None

        # Mock audit logs
        mock_audit_log = MagicMock(spec=AuditLog)
        mock_audit_log.id = 1
        mock_audit_log.action = "create"
        mock_audit_log.user_id = self.test_user.id
        mock_audit_log.created_at = datetime.now(timezone.utc)
        mock_audit_log.changes = {"created": {"title": "Test Task"}}

        # Mock log user
        mock_log_user = MagicMock(spec=User)
        mock_log_user.full_name = "Test User"

        # Mock queries
        call_count = 0

        def query_side_effect(model):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call for Task
                task_query = MagicMock()
                task_query.filter.return_value.first.return_value = mock_task
                return task_query
            elif call_count == 2:
                # Second call for AuditLog
                audit_query = MagicMock()
                audit_chain = audit_query.filter.return_value.order_by.return_value
                audit_chain.all.return_value = [mock_audit_log]
                return audit_query
            else:
                # Third call for User (log user)
                user_query = MagicMock()
                user_query.filter.return_value.first.return_value = mock_log_user
                return user_query

        self.db.query.side_effect = query_side_effect

        # Mock permission service
        with patch("app.services.task.permission_service") as mock_permission:
            mock_permission.has_permission.return_value = False  # Owner access

            # Act
            result = self.service.get_task_history(task_id, self.test_user, self.db)

        # Assert
        assert result.total == 1
        assert len(result.items) == 1

        history_item = result.items[0]
        assert history_item.id == mock_audit_log.id
        assert history_item.action == "create"
        assert history_item.user_name == "Test User"
        assert history_item.timestamp == mock_audit_log.created_at
        assert history_item.changes == mock_audit_log.changes

    def test_get_task_history_permission_denied(self):
        """Test that get_task_history checks permissions."""
        # Arrange
        task_id = 1

        # Mock existing task NOT owned by user
        mock_task = MagicMock(spec=Task)
        mock_task.id = task_id
        mock_task.reporter_id = 999  # Different user
        mock_task.assignee_id = None

        task_query = MagicMock()
        task_query.filter.return_value.first.return_value = mock_task
        self.db.query.return_value = task_query

        # Mock permission service
        with patch("app.services.task.permission_service") as mock_permission:
            mock_permission.has_permission.return_value = False  # No general permission

            # Act & Assert
            with pytest.raises(
                PermissionDenied, match="No access to this task history"
            ):
                self.service.get_task_history(task_id, self.test_user, self.db)
