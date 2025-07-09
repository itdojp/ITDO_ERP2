"""Unit tests for Task Service permissions."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import PermissionDenied
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskPriority, TaskUpdate
from app.services.task import TaskService


class TestTaskPermissions:
    """Test suite for Task Service permission checks."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = TaskService()
        self.db = MagicMock(spec=Session)

        # Create mock users
        self.regular_user = MagicMock(spec=User)
        self.regular_user.id = 1
        self.regular_user.email = "user@example.com"
        self.regular_user.is_active = True
        self.regular_user.is_superuser = False
        self.regular_user.full_name = "Regular User"
        self.regular_user.organization_id = 1

        self.admin_user = MagicMock(spec=User)
        self.admin_user.id = 2
        self.admin_user.email = "admin@example.com"
        self.admin_user.is_active = True
        self.admin_user.is_superuser = True
        self.admin_user.full_name = "Admin User"
        self.admin_user.organization_id = 1

    def test_create_task_requires_permission(self):
        """Test that task creation requires proper permissions."""
        # Arrange
        task_data = TaskCreate(
            title="Test Task",
            project_id=1,
            priority=TaskPriority.MEDIUM,
        )
        
        # Mock project exists
        mock_project = MagicMock(spec=Project)
        mock_project.id = 1
        self.db.query.return_value.filter.return_value.first.return_value = mock_project

        # Mock permission service to deny permission
        with patch('app.services.task.permission_service') as mock_permission:
            mock_permission.require_permission.side_effect = PermissionDenied(
                "No permission"
            )
            
            # Act & Assert
            with pytest.raises(PermissionDenied):
                self.service.create_task(task_data, self.regular_user, self.db)

    def test_superuser_bypasses_permissions(self):
        """Test that superusers can create tasks without explicit permissions."""
        # Arrange
        task_data = TaskCreate(
            title="Test Task",
            project_id=1,
            priority=TaskPriority.MEDIUM,
        )
        
        # Mock project exists
        mock_project = MagicMock(spec=Project)
        mock_project.id = 1
        self.db.query.return_value.filter.return_value.first.return_value = mock_project

        # Mock permission service
        with patch('app.services.task.permission_service') as mock_permission:
            mock_permission.require_permission.return_value = None  # No exception
            
            # Mock task creation
            with patch.object(self.service, '_task_to_response') as mock_response:
                mock_response.return_value = MagicMock()
                
                # Act
                result = self.service.create_task(task_data, self.admin_user, self.db)
                
                # Assert
                mock_permission.require_permission.assert_called()
                assert result is not None

    def test_get_task_owner_access(self):
        """Test that task owners can view their tasks without general permission."""
        # Arrange
        task_id = 1
        
        # Mock task owned by user
        mock_task = MagicMock(spec=Task)
        mock_task.id = task_id
        mock_task.reporter_id = self.regular_user.id
        mock_task.assignee_id = None
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_task
        self.db.query.return_value.options.return_value = mock_query

        # Mock permission service to deny general permission but allow owner access
        with patch('app.services.task.permission_service') as mock_permission:
            mock_permission.has_permission.return_value = False  # No general permission
            
            with patch.object(self.service, '_task_to_response') as mock_response:
                mock_response.return_value = MagicMock()
                
                # Act
                result = self.service.get_task(task_id, self.regular_user, self.db)
                
                # Assert
                assert result is not None

    def test_get_task_no_access(self):
        """Test that users cannot view tasks they don't own without permission."""
        # Arrange
        task_id = 1
        
        # Mock task NOT owned by user
        mock_task = MagicMock(spec=Task)
        mock_task.id = task_id
        mock_task.reporter_id = 999  # Different user
        mock_task.assignee_id = None
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_task
        self.db.query.return_value.options.return_value = mock_query

        # Mock permission service to deny permission
        with patch('app.services.task.permission_service') as mock_permission:
            mock_permission.has_permission.return_value = False
            
            # Act & Assert
            with pytest.raises(PermissionDenied, match="No access to this task"):
                self.service.get_task(task_id, self.regular_user, self.db)

    def test_update_task_owner_access(self):
        """Test that task owners can update their tasks."""
        # Arrange
        task_id = 1
        update_data = TaskUpdate(title="Updated Task")
        
        # Mock task owned by user
        mock_task = MagicMock(spec=Task)
        mock_task.id = task_id
        mock_task.title = "Old Task"
        mock_task.description = "Old description"
        mock_task.status = "not_started"
        mock_task.priority = "medium"
        mock_task.assignee_id = None
        mock_task.due_date = None
        mock_task.estimated_hours = None
        mock_task.reporter_id = self.regular_user.id
        self.db.query.return_value.filter.return_value.first.return_value = mock_task

        # Mock permission service to deny general permission but allow owner access
        with patch('app.services.task.permission_service') as mock_permission:
            mock_permission.has_permission.return_value = False  # No general permission
            
            with patch('app.services.task.AuditLogger.log') as mock_audit_log:
                with patch.object(self.service, '_task_to_response') as mock_response:
                    mock_response.return_value = MagicMock()
                    
                    # Act
                    result = self.service.update_task(
                        task_id, update_data, self.regular_user, self.db
                    )
                
                # Assert
                assert result is not None
                assert mock_task.title == "Updated Task"

    def test_delete_task_permission_denied(self):
        """Test that users cannot delete tasks without permission."""
        # Arrange
        task_id = 1
        
        # Mock task NOT owned by user
        mock_task = MagicMock(spec=Task)
        mock_task.id = task_id
        mock_task.reporter_id = 999  # Different user
        self.db.query.return_value.filter.return_value.first.return_value = mock_task

        # Mock permission service to deny permission
        with patch('app.services.task.permission_service') as mock_permission:
            mock_permission.has_permission.return_value = False
            
            # Act & Assert
            with pytest.raises(
                PermissionDenied, match="No permission to delete this task"
            ):
                self.service.delete_task(task_id, self.regular_user, self.db)

    def test_assign_task_creator_permission(self):
        """Test that task creators can assign their tasks."""
        # Arrange
        task_id = 1
        assignee_id = 3
        
        # Mock task created by user
        mock_task = MagicMock(spec=Task)
        mock_task.id = task_id
        mock_task.reporter_id = self.regular_user.id
        mock_task.assignee_id = None  # Currently unassigned
        
        # Mock assignee user
        mock_assignee = MagicMock(spec=User)
        mock_assignee.id = assignee_id
        mock_assignee.organization_id = self.regular_user.organization_id
        
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

        # Mock permission service to deny general permission but allow creator access
        with patch('app.services.task.permission_service') as mock_permission:
            mock_permission.has_permission.return_value = False  # No general permission
            
            with patch('app.services.task.AuditLogger.log') as mock_audit_log:
                with patch.object(self.service, '_task_to_response') as mock_response:
                    mock_response.return_value = MagicMock()
                    
                    # Act
                    result = self.service.assign_user(
                        task_id, assignee_id, self.regular_user, self.db
                    )
                
                # Assert
                assert result is not None
                assert mock_task.assignee_id == assignee_id

    def test_list_tasks_permission_filtering(self):
        """Test that task listing respects permission-based filtering."""
        # Arrange
        filters = {}
        
        # Mock tasks - mix of owned and not owned
        mock_task1 = MagicMock(spec=Task)
        mock_task1.id = 1
        mock_task1.title = "Task 1"
        mock_task1.description = "Description 1"
        mock_task1.status = "not_started"
        mock_task1.priority = "medium"
        mock_task1.project_id = 1
        mock_task1.parent_task_id = None
        mock_task1.due_date = None
        mock_task1.estimated_hours = None
        mock_task1.actual_hours = None
        mock_task1.created_at = datetime.now(timezone.utc)
        mock_task1.updated_at = datetime.now(timezone.utc)
        mock_task1.reporter_id = self.regular_user.id  # Owned
        mock_task1.assignee_id = None
        mock_task1.project = MagicMock(spec=Project)
        mock_task1.project.id = 1
        mock_task1.project.name = "Test Project"
        mock_task1.assignee = None
        mock_task1.reporter = self.regular_user
        
        mock_task2 = MagicMock(spec=Task)
        mock_task2.id = 2
        mock_task2.reporter_id = 999  # Not owned
        mock_task2.assignee_id = None
        
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1  # Only owned task
        mock_query.offset.return_value.limit.return_value.all.return_value = [
            mock_task1
        ]
        self.db.query.return_value = mock_query

        # Mock permission service to deny general permission
        with patch('app.services.task.permission_service') as mock_permission:
            mock_permission.has_permission.return_value = False
            
            # Act
            result = self.service.list_tasks(filters, self.regular_user, self.db)
            
            # Assert
            # Should only return tasks owned by user
            assert result.total == 1
            # Verify that permission-based filter was applied
            mock_query.filter.assert_called()