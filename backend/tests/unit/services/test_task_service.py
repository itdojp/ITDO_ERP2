"""Unit tests for Task Service."""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus, TaskPriority, TaskType
from app.models.project import Project, ProjectStatus, ProjectType
from app.models.organization import Organization
from app.models.user import User
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskFilter,
    TaskStatusTransition,
    TaskBulkOperation,
    TaskResponse,
)
from app.services.task import TaskService
from app.services.permission import PermissionService


class TestTaskService:
    """Test cases for Task Service."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = Mock(spec=Session)
        # Mock query chain for common operations
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        db.query.return_value.join.return_value.filter.return_value.distinct.return_value.count.return_value = 0
        db.query.return_value.offset.return_value.limit.return_value.all.return_value = []
        return db

    @pytest.fixture
    def mock_permission_service(self):
        """Mock permission service."""
        service = Mock(spec=PermissionService)
        service.check_user_permission.return_value = True
        return service

    @pytest.fixture
    def service(self, mock_db, mock_permission_service):
        """Task service with mocked dependencies."""
        return TaskService(mock_db, permission_service=mock_permission_service)

    @pytest.fixture
    def sample_organization(self):
        """Sample organization for testing."""
        org = Organization()
        org.id = 1
        org.code = "TEST-ORG"
        org.name = "Test Organization"
        org.is_active = True
        return org

    @pytest.fixture
    def sample_user(self):
        """Sample user for testing."""
        user = User()
        user.id = 1
        user.email = "test@example.com"
        user.full_name = "Test User"
        user.is_active = True
        return user

    @pytest.fixture
    def sample_assignee(self):
        """Sample assignee for testing."""
        user = User()
        user.id = 2
        user.email = "assignee@example.com"
        user.full_name = "Test Assignee"
        user.is_active = True
        return user

    @pytest.fixture
    def sample_project(self, sample_organization, sample_user):
        """Sample project for testing."""
        project = Project()
        project.id = 1
        project.code = "TEST-PROJ"
        project.name = "Test Project"
        project.description = "A test project"
        project.organization_id = sample_organization.id
        project.organization = sample_organization
        project.owner_id = sample_user.id
        project.owner = sample_user
        project.manager_id = sample_user.id
        project.manager = sample_user
        project.status = ProjectStatus.IN_PROGRESS
        project.project_type = ProjectType.INTERNAL
        project.start_date = date.today()
        project.end_date = date.today() + timedelta(days=90)
        project.budget = 1000000.0
        project.is_active = True
        return project

    @pytest.fixture
    def sample_task(self, sample_project, sample_user, sample_assignee):
        """Sample task for testing."""
        task = Task()
        task.id = 1
        task.title = "Test Task"
        task.description = "A test task"
        task.project_id = sample_project.id
        task.project = sample_project
        task.reporter_id = sample_user.id
        task.reporter = sample_user
        task.assignee_id = sample_assignee.id
        task.assignee = sample_assignee
        task.status = TaskStatus.TODO
        task.priority = TaskPriority.MEDIUM
        task.task_type = TaskType.FEATURE
        task.estimated_hours = 8.0
        task.actual_hours = 0.0
        task.due_date = date.today() + timedelta(days=7)
        task.labels = ["test", "development"]
        task.tags = ["test", "development"]
        task.metadata = {"test": True}
        task.is_deleted = False
        return task

    @pytest.fixture
    def sample_task_create(self, sample_project, sample_assignee):
        """Sample task create data."""
        return TaskCreate(
            title="New Task",
            description="A new task",
            project_id=sample_project.id,
            assignee_id=sample_assignee.id,
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            task_type=TaskType.FEATURE,
            estimated_hours=8.0,
            due_date=date.today() + timedelta(days=7),
            labels=["test", "new"],
            tags=["test", "new"],
        )

    @pytest.fixture
    def sample_task_update(self):
        """Sample task update data."""
        return TaskUpdate(
            title="Updated Task",
            description="An updated task",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            estimated_hours=10.0,
            labels=["test", "updated"],
        )

    def test_create_task_success(self, service, mock_db, sample_task_create, sample_project, sample_user, sample_assignee):
        """Test successful task creation."""
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_project,  # Project lookup
            sample_assignee,  # Assignee lookup
            sample_user,  # Reporter lookup
        ]
        
        # Mock database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Mock the created task with all required fields
        created_task = Mock()
        created_task.id = 1
        created_task.title = sample_task_create.title
        created_task.description = sample_task_create.description
        created_task.project_id = sample_task_create.project_id
        created_task.assignee_id = sample_task_create.assignee_id
        created_task.status = sample_task_create.status
        created_task.priority = sample_task_create.priority
        created_task.task_type = sample_task_create.task_type
        created_task.estimated_hours = sample_task_create.estimated_hours
        created_task.due_date = sample_task_create.due_date
        created_task.labels = sample_task_create.labels
        created_task.tags = sample_task_create.tags
        created_task.reporter_id = sample_user.id
        created_task.is_deleted = False
        created_task.metadata = None
        created_task.created_at = datetime.utcnow()
        created_task.updated_at = datetime.utcnow()
        created_task.epic_id = None
        created_task.start_date = None
        created_task.completed_date = None
        created_task.actual_hours = 0.0
        created_task.story_points = None
        created_task.progress_percentage = 0
        created_task.depends_on = []
        created_task.is_overdue = False
        created_task.days_remaining = 7
        created_task.completion_rate = 0.0
        created_task.time_spent_percentage = None
        created_task.assignee = sample_assignee
        created_task.reporter = sample_user
        created_task.project = sample_project
        created_task.epic = None
        created_task.subtasks = []
        
        mock_db.refresh.side_effect = lambda task: None
        
        # Create task
        result = service.create_task(
            task_data=sample_task_create,
            creator_id=sample_user.id,
            validate_permissions=True
        )
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # Verify result
        assert result is not None

    def test_create_task_project_not_found(self, service, mock_db, sample_task_create, sample_user):
        """Test task creation with non-existent project."""
        # Mock project not found
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Expect ValueError
        with pytest.raises(ValueError, match="Project not found"):
            service.create_task(
                task_data=sample_task_create,
                creator_id=sample_user.id,
                validate_permissions=True
            )

    def test_create_task_assignee_not_found(self, service, mock_db, sample_task_create, sample_project, sample_user):
        """Test task creation with non-existent assignee."""
        # Mock project found but assignee not found
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_project,  # Project lookup
            None,  # Assignee lookup
        ]
        
        # Expect ValueError
        with pytest.raises(ValueError, match="Assignee not found"):
            service.create_task(
                task_data=sample_task_create,
                creator_id=sample_user.id,
                validate_permissions=True
            )

    def test_create_task_permission_denied(self, service, mock_db, mock_permission_service, sample_task_create, sample_project, sample_user):
        """Test task creation without permissions."""
        # Mock permission check failure
        mock_permission_service.check_user_permission.return_value = False
        
        # Mock project found
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        
        # Expect PermissionError
        with pytest.raises(PermissionError, match="Insufficient permissions"):
            service.create_task(
                task_data=sample_task_create,
                creator_id=sample_user.id,
                validate_permissions=True
            )

    def test_get_task_success(self, service, mock_db, sample_task, sample_user):
        """Test successful task retrieval."""
        # Mock database query
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = sample_task
        
        # Get task
        result = service.get_task(
            task_id=sample_task.id,
            user_id=sample_user.id,
            validate_permissions=True
        )
        
        # Verify result
        assert result is not None
        assert result.id == sample_task.id
        assert result.title == sample_task.title

    def test_get_task_not_found(self, service, mock_db, sample_user):
        """Test task retrieval with non-existent task."""
        # Mock task not found
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        
        # Get task
        result = service.get_task(
            task_id=999,
            user_id=sample_user.id,
            validate_permissions=True
        )
        
        # Verify result
        assert result is None

    def test_get_task_permission_denied(self, service, mock_db, mock_permission_service, sample_task, sample_user):
        """Test task retrieval without permissions."""
        # Mock permission check failure
        mock_permission_service.check_user_permission.return_value = False
        
        # Mock task found
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = sample_task
        
        # Expect PermissionError
        with pytest.raises(PermissionError, match="Insufficient permissions"):
            service.get_task(
                task_id=sample_task.id,
                user_id=sample_user.id,
                validate_permissions=True
            )

    def test_update_task_success(self, service, mock_db, sample_task, sample_task_update, sample_user):
        """Test successful task update."""
        # Mock database query
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = sample_task
        
        # Mock database operations
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Update task
        result = service.update_task(
            task_id=sample_task.id,
            task_data=sample_task_update,
            user_id=sample_user.id,
            validate_permissions=True
        )
        
        # Verify database operations
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # Verify result
        assert result is not None
        assert result.title == sample_task_update.title

    def test_update_task_not_found(self, service, mock_db, sample_task_update, sample_user):
        """Test task update with non-existent task."""
        # Mock task not found
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        
        # Expect ValueError
        with pytest.raises(ValueError, match="Task not found"):
            service.update_task(
                task_id=999,
                task_data=sample_task_update,
                user_id=sample_user.id,
                validate_permissions=True
            )

    def test_update_task_permission_denied(self, service, mock_db, mock_permission_service, sample_task, sample_task_update, sample_user):
        """Test task update without permissions."""
        # Mock permission check failure
        mock_permission_service.check_user_permission.return_value = False
        
        # Mock task found
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = sample_task
        
        # Expect PermissionError
        with pytest.raises(PermissionError, match="Insufficient permissions"):
            service.update_task(
                task_id=sample_task.id,
                task_data=sample_task_update,
                user_id=sample_user.id,
                validate_permissions=True
            )

    def test_delete_task_success(self, service, mock_db, sample_task, sample_user):
        """Test successful task deletion."""
        # Mock database query
        mock_db.query.return_value.filter.return_value.first.return_value = sample_task
        
        # Mock database operations
        mock_db.commit = Mock()
        
        # Delete task
        result = service.delete_task(
            task_id=sample_task.id,
            user_id=sample_user.id,
            validate_permissions=True
        )
        
        # Verify database operations
        mock_db.commit.assert_called_once()
        
        # Verify result
        assert result is True
        assert sample_task.is_deleted is True

    def test_delete_task_not_found(self, service, mock_db, sample_user):
        """Test task deletion with non-existent task."""
        # Mock task not found
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Expect ValueError
        with pytest.raises(ValueError, match="Task not found"):
            service.delete_task(
                task_id=999,
                user_id=sample_user.id,
                validate_permissions=True
            )

    def test_delete_task_permission_denied(self, service, mock_db, mock_permission_service, sample_task, sample_user):
        """Test task deletion without permissions."""
        # Mock permission check failure
        mock_permission_service.check_user_permission.return_value = False
        
        # Mock task found
        mock_db.query.return_value.filter.return_value.first.return_value = sample_task
        
        # Expect PermissionError
        with pytest.raises(PermissionError, match="Insufficient permissions"):
            service.delete_task(
                task_id=sample_task.id,
                user_id=sample_user.id,
                validate_permissions=True
            )

    def test_list_tasks_success(self, service, mock_db, sample_task, sample_user):
        """Test successful task listing."""
        # Mock database query
        mock_tasks = [sample_task]
        mock_db.query.return_value.join.return_value.filter.return_value.distinct.return_value.count.return_value = 1
        mock_db.query.return_value.options.return_value.join.return_value.filter.return_value.distinct.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_tasks
        
        # Create filter
        task_filter = TaskFilter(
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
        )
        
        # List tasks
        tasks, total = service.list_tasks(
            user_id=sample_user.id,
            filters=task_filter,
            page=1,
            per_page=10,
            validate_permissions=True
        )
        
        # Verify results
        assert len(tasks) == 1
        assert total == 1
        assert tasks[0].id == sample_task.id

    def test_list_tasks_with_project_filter(self, service, mock_db, sample_task, sample_user, sample_project):
        """Test task listing with project filter."""
        # Mock database query
        mock_tasks = [sample_task]
        mock_db.query.return_value.join.return_value.filter.return_value.distinct.return_value.count.return_value = 1
        mock_db.query.return_value.options.return_value.join.return_value.filter.return_value.distinct.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_tasks
        
        # Create filter with project
        task_filter = TaskFilter(
            project_id=sample_project.id,
            status=TaskStatus.TODO,
        )
        
        # List tasks
        tasks, total = service.list_tasks(
            user_id=sample_user.id,
            filters=task_filter,
            page=1,
            per_page=10,
            validate_permissions=True
        )
        
        # Verify results
        assert len(tasks) == 1
        assert total == 1
        assert tasks[0].project_id == sample_project.id

    def test_list_tasks_with_search(self, service, mock_db, sample_task, sample_user):
        """Test task listing with search query."""
        # Mock database query
        mock_tasks = [sample_task]
        mock_db.query.return_value.join.return_value.filter.return_value.distinct.return_value.count.return_value = 1
        mock_db.query.return_value.options.return_value.join.return_value.filter.return_value.distinct.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_tasks
        
        # Create filter with search
        task_filter = TaskFilter(
            search="Test",
        )
        
        # List tasks
        tasks, total = service.list_tasks(
            user_id=sample_user.id,
            filters=task_filter,
            page=1,
            per_page=10,
            validate_permissions=True
        )
        
        # Verify results
        assert len(tasks) == 1
        assert total == 1
        assert "Test" in tasks[0].title

    def test_list_tasks_overdue_filter(self, service, mock_db, sample_task, sample_user):
        """Test task listing with overdue filter."""
        # Set task as overdue
        sample_task.due_date = date.today() - timedelta(days=1)
        
        # Mock database query
        mock_tasks = [sample_task]
        mock_db.query.return_value.join.return_value.filter.return_value.distinct.return_value.count.return_value = 1
        mock_db.query.return_value.options.return_value.join.return_value.filter.return_value.distinct.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_tasks
        
        # Create filter for overdue tasks
        task_filter = TaskFilter(
            is_overdue=True,
        )
        
        # List tasks
        tasks, total = service.list_tasks(
            user_id=sample_user.id,
            filters=task_filter,
            page=1,
            per_page=10,
            validate_permissions=True
        )
        
        # Verify results
        assert len(tasks) == 1
        assert total == 1
        assert tasks[0].is_overdue

    def test_search_tasks_success(self, service, mock_db, sample_task, sample_user):
        """Test successful task search."""
        # Mock database query
        mock_tasks = [sample_task]
        mock_db.query.return_value.options.return_value.join.return_value.filter.return_value.limit.return_value.all.return_value = mock_tasks
        
        # Search tasks
        results = service.search_tasks(
            query="Test",
            user_id=sample_user.id,
            project_id=None,
            limit=10
        )
        
        # Verify results
        assert len(results) == 1
        assert results[0].title == sample_task.title

    def test_search_tasks_with_project_filter(self, service, mock_db, sample_task, sample_user, sample_project):
        """Test task search with project filter."""
        # Mock database query
        mock_tasks = [sample_task]
        mock_db.query.return_value.options.return_value.join.return_value.filter.return_value.limit.return_value.all.return_value = mock_tasks
        
        # Search tasks with project filter
        results = service.search_tasks(
            query="Test",
            user_id=sample_user.id,
            project_id=sample_project.id,
            limit=10
        )
        
        # Verify results
        assert len(results) == 1
        assert results[0].project_id == sample_project.id

    def test_transition_task_status_success(self, service, mock_db, sample_task, sample_user):
        """Test successful task status transition."""
        # Mock database query
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = sample_task
        
        # Mock database operations
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Create transition
        transition = TaskStatusTransition(
            from_status=TaskStatus.TODO,
            to_status=TaskStatus.IN_PROGRESS,
            reason="Starting work"
        )
        
        # Transition status
        result = service.transition_task_status(
            task_id=sample_task.id,
            transition=transition,
            user_id=sample_user.id
        )
        
        # Verify database operations
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # Verify result
        assert result is not None
        assert result.status == TaskStatus.IN_PROGRESS

    def test_transition_task_status_invalid_transition(self, service, mock_db, sample_task, sample_user):
        """Test invalid task status transition."""
        # Set task to done status
        sample_task.status = TaskStatus.DONE
        
        # Mock database query
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = sample_task
        
        # Create invalid transition
        transition = TaskStatusTransition(
            from_status=TaskStatus.DONE,
            to_status=TaskStatus.TODO,
            reason="Invalid transition"
        )
        
        # Expect ValueError
        with pytest.raises(ValueError, match="Invalid status transition"):
            service.transition_task_status(
                task_id=sample_task.id,
                transition=transition,
                user_id=sample_user.id
            )

    def test_get_task_statistics_success(self, service, mock_db, sample_task, sample_user):
        """Test successful task statistics retrieval."""
        # Mock database query
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = sample_task
        
        # Get statistics
        result = service.get_task_statistics(
            task_id=sample_task.id,
            user_id=sample_user.id
        )
        
        # Verify result
        assert result is not None
        assert result.task_id == sample_task.id
        assert result.estimated_hours == sample_task.estimated_hours
        assert result.actual_hours == sample_task.actual_hours

    def test_get_task_statistics_not_found(self, service, mock_db, sample_user):
        """Test task statistics with non-existent task."""
        # Mock task not found
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        
        # Expect ValueError
        with pytest.raises(ValueError, match="Task not found"):
            service.get_task_statistics(
                task_id=999,
                user_id=sample_user.id
            )

    def test_get_task_dependencies_success(self, service, mock_db, sample_task, sample_user):
        """Test successful task dependencies retrieval."""
        # Mock database query
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = sample_task
        
        # Mock dependencies
        dependency_task = Mock()
        dependency_task.id = 2
        dependency_task.title = "Dependency Task"
        
        mock_db.query.return_value.options.return_value.filter.return_value.all.return_value = [dependency_task]
        
        # Get dependencies
        result = service.get_task_dependencies(
            task_id=sample_task.id,
            user_id=sample_user.id
        )
        
        # Verify result
        assert len(result) == 1
        assert result[0].id == dependency_task.id

    def test_get_task_subtasks_success(self, service, mock_db, sample_task, sample_user):
        """Test successful task subtasks retrieval."""
        # Mock database query
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = sample_task
        
        # Mock subtasks
        subtask = Mock()
        subtask.id = 3
        subtask.title = "Subtask"
        subtask.epic_id = sample_task.id
        
        mock_db.query.return_value.options.return_value.filter.return_value.all.return_value = [subtask]
        
        # Get subtasks
        result = service.get_task_subtasks(
            task_id=sample_task.id,
            user_id=sample_user.id
        )
        
        # Verify result
        assert len(result) == 1
        assert result[0].id == subtask.id

    def test_bulk_update_tasks_success(self, service, mock_db, sample_task, sample_user):
        """Test successful bulk task update."""
        # Mock database query
        mock_tasks = [sample_task]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_tasks
        
        # Mock database operations
        mock_db.commit = Mock()
        
        # Create bulk operation
        bulk_op = TaskBulkOperation(
            task_ids=[sample_task.id],
            operation="update_status",
            data={"status": TaskStatus.IN_PROGRESS}
        )
        
        # Bulk update
        result = service.bulk_update_tasks(
            bulk_operation=bulk_op,
            user_id=sample_user.id
        )
        
        # Verify database operations
        mock_db.commit.assert_called_once()
        
        # Verify result
        assert result["success"] is True
        assert result["updated_count"] == 1

    def test_bulk_update_tasks_invalid_operation(self, service, mock_db, sample_task, sample_user):
        """Test bulk update with invalid operation."""
        # Create invalid bulk operation
        bulk_op = TaskBulkOperation(
            task_ids=[sample_task.id],
            operation="invalid_operation",
            data={"status": TaskStatus.IN_PROGRESS}
        )
        
        # Expect ValueError
        with pytest.raises(ValueError, match="Invalid bulk operation"):
            service.bulk_update_tasks(
                bulk_operation=bulk_op,
                user_id=sample_user.id
            )

    def test_bulk_update_tasks_no_tasks(self, service, mock_db, sample_user):
        """Test bulk update with no tasks."""
        # Mock empty task list
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Create bulk operation
        bulk_op = TaskBulkOperation(
            task_ids=[999],
            operation="update_status",
            data={"status": TaskStatus.IN_PROGRESS}
        )
        
        # Bulk update
        result = service.bulk_update_tasks(
            bulk_operation=bulk_op,
            user_id=sample_user.id
        )
        
        # Verify result
        assert result["success"] is True
        assert result["updated_count"] == 0

    def test_create_task_with_epic(self, service, mock_db, sample_task_create, sample_project, sample_user, sample_assignee):
        """Test task creation with epic."""
        # Create epic task
        epic_task = Mock()
        epic_task.id = 10
        epic_task.task_type = TaskType.EPIC
        epic_task.project_id = sample_project.id
        
        # Add epic_id to task_create
        sample_task_create.epic_id = epic_task.id
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_project,  # Project lookup
            sample_assignee,  # Assignee lookup
            sample_user,  # Reporter lookup
            epic_task,  # Epic lookup
        ]
        
        # Mock database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Create task
        result = service.create_task(
            task_data=sample_task_create,
            creator_id=sample_user.id,
            validate_permissions=True
        )
        
        # Verify result
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_task_with_parent_task(self, service, mock_db, sample_task_create, sample_project, sample_user, sample_assignee):
        """Test task creation with parent task."""
        # Create parent task
        parent_task = Mock()
        parent_task.id = 5
        parent_task.project_id = sample_project.id
        
        # Add parent_task_id to task_create (this will be mapped to epic_id)
        sample_task_create.parent_task_id = parent_task.id
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_project,  # Project lookup
            sample_assignee,  # Assignee lookup
            sample_user,  # Reporter lookup
            parent_task,  # Parent task lookup
        ]
        
        # Mock database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Create task
        result = service.create_task(
            task_data=sample_task_create,
            creator_id=sample_user.id,
            validate_permissions=True
        )
        
        # Verify result
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_task_with_dependencies(self, service, mock_db, sample_task_create, sample_project, sample_user, sample_assignee):
        """Test task creation with dependencies."""
        # Create dependency task
        dependency_task = Mock()
        dependency_task.id = 8
        dependency_task.project_id = sample_project.id
        
        # Add dependencies to task_create
        sample_task_create.dependencies = [dependency_task.id]
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_project,  # Project lookup
            sample_assignee,  # Assignee lookup
            sample_user,  # Reporter lookup
        ]
        
        # Mock dependency validation
        mock_db.query.return_value.filter.return_value.all.return_value = [dependency_task]
        
        # Mock database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Create task
        result = service.create_task(
            task_data=sample_task_create,
            creator_id=sample_user.id,
            validate_permissions=True
        )
        
        # Verify result
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_task_invalid_dependency(self, service, mock_db, sample_task_create, sample_project, sample_user, sample_assignee):
        """Test task creation with invalid dependency."""
        # Add invalid dependency to task_create
        sample_task_create.dependencies = [999]  # Non-existent task
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_project,  # Project lookup
            sample_assignee,  # Assignee lookup
            sample_user,  # Reporter lookup
        ]
        
        # Mock dependency validation - return empty list
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Expect ValueError
        with pytest.raises(ValueError, match="Invalid dependency"):
            service.create_task(
                task_data=sample_task_create,
                creator_id=sample_user.id,
                validate_permissions=True
            )

    def test_bulk_update_tasks_assign_users(self, service, mock_db, sample_task, sample_user, sample_assignee):
        """Test bulk assignment of tasks to users."""
        # Mock database query
        mock_tasks = [sample_task]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_tasks
        
        # Mock user lookup
        mock_db.query.return_value.filter.return_value.first.return_value = sample_assignee
        
        # Mock database operations
        mock_db.commit = Mock()
        
        # Create bulk operation
        bulk_op = TaskBulkOperation(
            task_ids=[sample_task.id],
            operation="assign_to",
            data={"assignee_id": sample_assignee.id}
        )
        
        # Bulk update
        result = service.bulk_update_tasks(
            bulk_operation=bulk_op,
            user_id=sample_user.id
        )
        
        # Verify database operations
        mock_db.commit.assert_called_once()
        
        # Verify result
        assert result["success"] is True
        assert result["updated_count"] == 1
        assert sample_task.assignee_id == sample_assignee.id

    def test_bulk_update_tasks_update_priority(self, service, mock_db, sample_task, sample_user):
        """Test bulk priority update."""
        # Mock database query
        mock_tasks = [sample_task]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_tasks
        
        # Mock database operations
        mock_db.commit = Mock()
        
        # Create bulk operation
        bulk_op = TaskBulkOperation(
            task_ids=[sample_task.id],
            operation="update_priority",
            data={"priority": TaskPriority.HIGH}
        )
        
        # Bulk update
        result = service.bulk_update_tasks(
            bulk_operation=bulk_op,
            user_id=sample_user.id
        )
        
        # Verify database operations
        mock_db.commit.assert_called_once()
        
        # Verify result
        assert result["success"] is True
        assert result["updated_count"] == 1
        assert sample_task.priority == TaskPriority.HIGH

    def test_list_tasks_permission_denied(self, service, mock_db, mock_permission_service, sample_user):
        """Test task listing without permissions."""
        # Mock permission check failure
        mock_permission_service.check_user_permission.return_value = False
        
        # Create filter
        task_filter = TaskFilter(
            status=TaskStatus.TODO,
        )
        
        # Expect PermissionError
        with pytest.raises(PermissionError, match="Insufficient permissions"):
            service.list_tasks(
                user_id=sample_user.id,
                filters=task_filter,
                page=1,
                per_page=10,
                validate_permissions=True
            )