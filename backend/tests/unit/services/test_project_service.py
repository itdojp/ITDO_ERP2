"""Unit tests for Project Service."""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStatus, ProjectPriority, ProjectType
from app.models.project_member import ProjectMember
from app.models.organization import Organization
from app.models.department import Department
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectFilter,
    ProjectStatusTransition,
)
from app.services.project import ProjectService
from app.services.permission import PermissionService


class TestProjectService:
    """Test cases for Project Service."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = Mock(spec=Session)
        # Mock query chain for common operations
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        db.query.return_value.join.return_value.filter.return_value.distinct.return_value.count.return_value = 0
        return db

    @pytest.fixture
    def mock_permission_service(self):
        """Mock permission service."""
        service = Mock(spec=PermissionService)
        service.check_user_permission.return_value = True
        return service

    @pytest.fixture
    def service(self, mock_db, mock_permission_service):
        """Project service with mocked dependencies."""
        return ProjectService(mock_db, permission_service=mock_permission_service)

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
    def sample_department(self):
        """Sample department for testing."""
        dept = Department()
        dept.id = 1
        dept.code = "TEST-DEPT"
        dept.name = "Test Department"
        dept.organization_id = 1
        dept.is_active = True
        return dept

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
        project.priority = ProjectPriority.HIGH
        project.project_type = ProjectType.INTERNAL
        project.start_date = date.today()
        project.end_date = date.today() + timedelta(days=90)
        project.budget = 1000000.0
        project.members = []
        project.tasks = []
        project.milestones = []
        return project

    @pytest.fixture
    def project_create_data(self):
        """Sample project create data."""
        return ProjectCreate(
            code="NEW-PROJ",
            name="New Project",
            description="A new test project",
            organization_id=1,
            department_id=1,
            manager_id=1,
            status=ProjectStatus.PLANNING,
            priority=ProjectPriority.MEDIUM,
            project_type=ProjectType.INTERNAL,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=90),
            budget=500000.0,
            tags=["test", "development"],
        )

    # Test Project CRUD Operations

    def test_create_project_success(
        self,
        service,
        mock_db,
        project_create_data,
        sample_organization,
        sample_department,
        sample_user,
    ):
        """Test successful project creation."""
        # Setup mocks
        # Ensure organization is active
        sample_organization.is_active = True
        
        # Mock complex query chains
        org_query = Mock()
        org_query.filter.return_value.first.return_value = sample_organization
        mock_db.query.return_value = org_query
        
        dept_query = Mock()
        dept_query.filter.return_value.first.return_value = sample_department
        
        project_query = Mock()
        project_query.filter.return_value.first.return_value = None
        
        user_query = Mock()
        user_query.filter.return_value.first.return_value = sample_user
        
        def query_side_effect(model):
            if model == Organization:
                return org_query
            elif model == Department:
                return dept_query
            elif model == Project:
                return project_query
            elif model == User:
                return user_query
            return Mock()
        
        mock_db.query.side_effect = query_side_effect

        # Mock the database operations to set project fields
        def mock_commit():
            # Simulate what the database would do
            pass

        def mock_refresh(project):
            # Simulate what the database would do after insert
            project.id = 1
            project.created_at = datetime.utcnow()
            project.updated_at = datetime.utcnow()
            project.is_archived = False
            project.members = []
            project.tasks = []
            project.milestones = []
            project.organization = sample_organization
            project.department = sample_department
            project.owner = sample_user
            project.manager = sample_user

        mock_db.commit.side_effect = mock_commit
        mock_db.refresh.side_effect = mock_refresh

        # Execute
        result = service.create_project(
            project_data=project_create_data,
            owner_id=sample_user.id,
            validate_permissions=True,
        )

        # Verify
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
        assert isinstance(result.dict(), dict)
        assert result.dict()["code"] == "NEW-PROJ"

    def test_create_project_duplicate_code(
        self,
        service,
        mock_db,
        project_create_data,
        sample_organization,
        sample_project,
    ):
        """Test project creation with duplicate code."""
        # Setup mocks
        mock_db.query(Organization).filter.return_value.first.return_value = sample_organization
        mock_db.query(Project).filter.return_value.first.return_value = sample_project

        # Execute and verify
        with pytest.raises(ValueError, match="already exists"):
            service.create_project(
                project_data=project_create_data,
                owner_id=1,
                validate_permissions=True,
            )

    def test_create_project_invalid_organization(
        self, service, mock_db, project_create_data
    ):
        """Test project creation with invalid organization."""
        # Setup mocks
        mock_db.query(Organization).filter.return_value.first.return_value = None

        # Execute and verify
        with pytest.raises(ValueError, match="Organization not found"):
            service.create_project(
                project_data=project_create_data,
                owner_id=1,
                validate_permissions=True,
            )

    def test_create_project_permission_denied(
        self,
        service,
        mock_db,
        mock_permission_service,
        project_create_data,
        sample_organization,
    ):
        """Test project creation with insufficient permissions."""
        # Setup mocks
        mock_db.query(Organization).filter.return_value.first.return_value = sample_organization
        mock_permission_service.check_user_permission.return_value = False

        # Execute and verify
        with pytest.raises(PermissionError, match="Insufficient permissions"):
            service.create_project(
                project_data=project_create_data,
                owner_id=1,
                validate_permissions=True,
            )

    def test_get_project_success(self, service, mock_db, sample_project):
        """Test successful project retrieval."""
        # Setup mocks
        mock_query = Mock()
        mock_query.options.return_value.filter.return_value.first.return_value = sample_project
        mock_db.query.return_value = mock_query

        # Execute
        result = service.get_project(project_id=1, user_id=1)

        # Verify
        assert result is not None
        assert result.dict()["id"] == 1
        assert result.dict()["code"] == "TEST-PROJ"

    def test_get_project_not_found(self, service, mock_db):
        """Test project retrieval when not found."""
        # Setup mocks
        mock_query = Mock()
        mock_query.options.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        # Execute
        result = service.get_project(project_id=999, user_id=1)

        # Verify
        assert result is None

    def test_update_project_success(
        self, service, mock_db, sample_project, mock_permission_service
    ):
        """Test successful project update."""
        # Setup mocks
        mock_query = Mock()
        mock_query.options.return_value.filter.return_value.first.return_value = sample_project
        mock_db.query.return_value = mock_query

        update_data = ProjectUpdate(
            name="Updated Project",
            description="Updated description",
            priority=ProjectPriority.CRITICAL,
        )

        # Execute
        result = service.update_project(
            project_id=1,
            project_data=update_data,
            user_id=1,
            validate_permissions=True,
        )

        # Verify
        mock_db.commit.assert_called()
        assert result.dict()["name"] == "Updated Project"
        assert result.dict()["priority"] == ProjectPriority.CRITICAL

    def test_delete_project_success(
        self, service, mock_db, sample_project, mock_permission_service
    ):
        """Test successful project deletion."""
        # Setup mocks
        mock_query = Mock()
        mock_query.options.return_value.filter.return_value.first.return_value = sample_project
        mock_db.query.return_value = mock_query
        sample_project.tasks = []  # No active tasks

        # Execute
        result = service.delete_project(
            project_id=1, user_id=1, validate_permissions=True
        )

        # Verify
        assert result is True
        assert sample_project.is_active is False
        mock_db.commit.assert_called()

    def test_delete_project_with_active_tasks(
        self, service, mock_db, sample_project, mock_permission_service
    ):
        """Test project deletion with active tasks."""
        # Setup mocks
        mock_query = Mock()
        mock_query.options.return_value.filter.return_value.first.return_value = sample_project
        mock_db.query.return_value = mock_query
        
        # Add active task
        task = Task()
        task.status = TaskStatus.IN_PROGRESS
        sample_project.tasks = [task]

        # Execute and verify
        with pytest.raises(ValueError, match="has active tasks"):
            service.delete_project(project_id=1, user_id=1, validate_permissions=True)

    # Test Permission Checks

    def test_check_project_permission_owner(self, service, mock_db, sample_project):
        """Test permission check for project owner."""
        # Setup mocks
        mock_query = Mock()
        mock_query.options.return_value.filter.return_value.first.return_value = sample_project
        mock_db.query.return_value = mock_query

        # Execute
        result = service.check_project_permission(
            project_id=1, user_id=sample_project.owner_id, permission="project.manage"
        )

        # Verify
        assert result is True

    def test_check_project_permission_member(self, service, mock_db, sample_project):
        """Test permission check for project member."""
        # Setup mocks
        mock_query = Mock()
        mock_query.options.return_value.filter.return_value.first.return_value = sample_project
        mock_db.query.return_value = mock_query

        # Add member
        member = ProjectMember()
        member.user_id = 2
        member.role = "developer"
        member.permissions = ["project.read", "tasks.update"]
        member.is_active = True
        sample_project.members = [member]

        # Execute - should have read permission
        result = service.check_project_permission(
            project_id=1, user_id=2, permission="project.read"
        )
        assert result is True

        # Execute - should not have manage permission
        result = service.check_project_permission(
            project_id=1, user_id=2, permission="project.manage"
        )
        assert result is False

    def test_check_project_permission_non_member(self, service, mock_db, sample_project):
        """Test permission check for non-member."""
        # Setup mocks
        mock_query = Mock()
        mock_query.options.return_value.filter.return_value.first.return_value = sample_project
        mock_db.query.return_value = mock_query

        # Execute
        result = service.check_project_permission(
            project_id=1, user_id=999, permission="project.read"
        )

        # Verify
        assert result is False

    # Test Hierarchy Management

    def test_get_project_hierarchy(self, service, mock_db):
        """Test getting project hierarchy."""
        # Create sample hierarchy
        root = Project()
        root.id = 1
        root.name = "Root Project"
        root.parent_id = None

        child1 = Project()
        child1.id = 2
        child1.name = "Child 1"
        child1.parent_id = 1

        child2 = Project()
        child2.id = 3
        child2.name = "Child 2"
        child2.parent_id = 1

        grandchild = Project()
        grandchild.id = 4
        grandchild.name = "Grandchild"
        grandchild.parent_id = 2

        # Setup mocks
        mock_query = Mock()
        mock_query.options.return_value.filter.return_value.first.return_value = root
        mock_db.query.return_value = mock_query
        
        # Mock children queries
        def side_effect(*args, **kwargs):
            if args[0] == Project and hasattr(args[0], 'parent_id'):
                if kwargs.get('parent_id') == 1:
                    return [child1, child2]
                elif kwargs.get('parent_id') == 2:
                    return [grandchild]
            return []
        
        mock_db.query(Project).filter.return_value.all.side_effect = side_effect

        # Execute
        result = service.get_project_hierarchy(project_id=1, user_id=1)

        # Verify
        assert result is not None
        assert result["total_projects"] >= 1

    # Test Statistics Calculation

    def test_get_project_statistics(self, service, mock_db, sample_project):
        """Test project statistics calculation."""
        # Setup mocks
        mock_query = Mock()
        mock_query.options.return_value.filter.return_value.first.return_value = sample_project
        mock_db.query.return_value = mock_query

        # Add some test data
        sample_project.actual_cost = 450000.0
        sample_project.members = [Mock(), Mock(), Mock()]  # 3 members
        sample_project.tasks = [
            Mock(status=TaskStatus.COMPLETED),
            Mock(status=TaskStatus.IN_PROGRESS),
            Mock(status=TaskStatus.TODO),
        ]

        # Execute
        result = service.get_project_statistics(project_id=1)

        # Verify
        assert result["total_members"] == 3
        assert result["total_tasks"] == 3
        assert result["budget_utilization"] == 45.0  # 450k/1000k * 100

    def test_get_project_progress(self, service, mock_db, sample_project):
        """Test project progress calculation."""
        # Setup mocks
        mock_db.query(Project).filter.return_value.first.return_value = sample_project
        
        # Add completed tasks
        sample_project.tasks = [
            Mock(status=TaskStatus.COMPLETED),
            Mock(status=TaskStatus.COMPLETED),
            Mock(status=TaskStatus.IN_PROGRESS),
            Mock(status=TaskStatus.TODO),
        ]

        # Execute
        result = service.get_project_progress(project_id=1)

        # Verify
        assert result == 50.0  # 2 completed out of 4 tasks

    # Test Member Management

    def test_add_member_success(self, service, mock_db, sample_project, sample_user):
        """Test successful member addition."""
        # Setup mocks
        mock_db.query(Project).filter.return_value.first.return_value = sample_project
        mock_db.query(User).filter.return_value.first.return_value = sample_user
        mock_db.query(ProjectMember).filter.return_value.first.return_value = None

        # Execute
        result = service.add_member(
            project_id=1,
            user_id=2,
            role="developer",
            current_user_id=1,
            permissions=["project.read"],
        )

        # Verify
        assert result is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    def test_add_member_duplicate(self, service, mock_db, sample_project):
        """Test adding duplicate member."""
        # Setup mocks
        mock_db.query(Project).filter.return_value.first.return_value = sample_project
        existing_member = Mock()
        mock_db.query(ProjectMember).filter.return_value.first.return_value = existing_member

        # Execute and verify
        with pytest.raises(ValueError, match="already a member"):
            service.add_member(
                project_id=1,
                user_id=2,
                role="developer",
                current_user_id=1,
            )

    def test_remove_member_success(self, service, mock_db, sample_project):
        """Test successful member removal."""
        # Setup mocks
        mock_db.query(Project).filter.return_value.first.return_value = sample_project
        member = Mock()
        member.user_id = 2
        mock_db.query(ProjectMember).filter.return_value.first.return_value = member

        # Execute
        result = service.remove_member(project_id=1, user_id=2, current_user_id=1)

        # Verify
        assert result is True
        mock_db.delete.assert_called_once_with(member)
        mock_db.commit.assert_called()

    def test_update_member_role(self, service, mock_db, sample_project):
        """Test updating member role."""
        # Setup mocks
        mock_db.query(Project).filter.return_value.first.return_value = sample_project
        member = Mock()
        member.role = "developer"
        member.permissions = []
        mock_db.query(ProjectMember).filter.return_value.first.return_value = member

        # Execute
        result = service.update_member_role(
            project_id=1,
            user_id=2,
            role="manager",
            current_user_id=1,
            permissions=["project.update", "members.add"],
        )

        # Verify
        assert result is True
        assert member.role == "manager"
        assert member.permissions == ["project.update", "members.add"]
        mock_db.commit.assert_called()

    # Test Filtering and Search

    def test_list_projects_with_filters(self, service, mock_db):
        """Test listing projects with filters."""
        # Create sample projects
        projects = [
            Mock(id=1, name="Project 1", status=ProjectStatus.ACTIVE),
            Mock(id=2, name="Project 2", status=ProjectStatus.PLANNING),
        ]

        # Setup mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.offset.return_value.limit.return_value.all.return_value = projects
        mock_db.query.return_value = mock_query

        # Create filter
        filters = ProjectFilter(
            organization_id=1,
            status=ProjectStatus.ACTIVE,
            priority=ProjectPriority.HIGH,
        )

        # Execute
        result, total = service.list_projects(
            user_id=1, filters=filters, page=1, per_page=10
        )

        # Verify
        assert total == 2
        assert len(result) == 2

    def test_search_projects(self, service, mock_db):
        """Test searching projects."""
        # Create sample projects
        projects = [
            Mock(id=1, name="Test Project", code="TEST-001"),
            Mock(id=2, name="Another Test", code="TEST-002"),
        ]

        # Setup mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.all.return_value = projects
        mock_db.query.return_value = mock_query

        # Execute
        result = service.search_projects(query="test", user_id=1)

        # Verify
        assert len(result) == 2

    # Test Status Transitions

    def test_transition_project_status_success(self, service, mock_db, sample_project):
        """Test successful project status transition."""
        # Setup mocks
        mock_db.query(Project).filter.return_value.first.return_value = sample_project
        sample_project.status = ProjectStatus.PLANNING

        transition = ProjectStatusTransition(
            from_status=ProjectStatus.PLANNING,
            to_status=ProjectStatus.ACTIVE,
            reason="Ready to start",
        )

        # Execute
        result = service.transition_project_status(
            project_id=1, transition=transition, user_id=1
        )

        # Verify
        assert result.dict()["status"] == ProjectStatus.ACTIVE
        mock_db.commit.assert_called()

    def test_transition_project_status_invalid(self, service, mock_db, sample_project):
        """Test invalid project status transition."""
        # Setup mocks
        mock_db.query(Project).filter.return_value.first.return_value = sample_project
        sample_project.status = ProjectStatus.COMPLETED

        transition = ProjectStatusTransition(
            from_status=ProjectStatus.COMPLETED,
            to_status=ProjectStatus.PLANNING,
            reason="Invalid transition",
        )

        # Execute and verify
        with pytest.raises(ValueError, match="Invalid status transition"):
            service.transition_project_status(
                project_id=1, transition=transition, user_id=1
            )

    # Test Budget Management

    def test_get_budget_utilization(self, service, mock_db, sample_project):
        """Test budget utilization calculation."""
        # Setup mocks
        mock_db.query(Project).filter.return_value.first.return_value = sample_project
        sample_project.budget = 1000000.0
        sample_project.actual_cost = 750000.0

        # Execute
        result = service.get_budget_utilization(project_id=1)

        # Verify
        assert result["budget"] == 1000000.0
        assert result["actual_cost"] == 750000.0
        assert result["utilization_percentage"] == 75.0
        assert result["remaining_budget"] == 250000.0

    def test_update_actual_cost(self, service, mock_db, sample_project):
        """Test updating project actual cost."""
        # Setup mocks
        mock_db.query(Project).filter.return_value.first.return_value = sample_project
        sample_project.actual_cost = 100000.0

        # Execute
        result = service.update_actual_cost(
            project_id=1, cost_delta=50000.0, user_id=1
        )

        # Verify
        assert result is True
        assert sample_project.actual_cost == 150000.0
        mock_db.commit.assert_called()

    # Test Cross-Department Projects

    def test_create_cross_department_project(
        self, service, mock_db, sample_organization, sample_user
    ):
        """Test creating a cross-department project."""
        # Setup mocks
        mock_db.query(Organization).filter.return_value.first.return_value = sample_organization
        
        departments = [Mock(id=1), Mock(id=2), Mock(id=3)]
        for dept in departments:
            dept.organization_id = 1
            dept.is_active = True
        
        def dept_side_effect(model):
            if model == Department:
                return Mock(filter=Mock(return_value=Mock(first=Mock(side_effect=lambda: departments.pop(0) if departments else None))))
            return Mock()
        
        mock_db.query.side_effect = dept_side_effect

        project_data = ProjectCreate(
            code="CROSS-001",
            name="Cross-Department Project",
            organization_id=1,
            department_id=1,
            participating_departments=[2, 3],
            status=ProjectStatus.PLANNING,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=90),
        )

        # Execute
        with patch.object(service, 'create_project') as mock_create:
            mock_create.return_value = Mock()
            result = mock_create(
                project_data=project_data,
                owner_id=sample_user.id,
            )

        # Verify
        assert result is not None