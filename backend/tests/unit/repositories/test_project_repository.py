"""Unit tests for Project Repository."""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStatus, ProjectPriority, ProjectType
from app.models.project_member import ProjectMember
from app.models.project_milestone import ProjectMilestone
from app.models.organization import Organization
from app.models.department import Department
from app.models.user import User
from app.repositories.project import ProjectRepository
from app.schemas.project import ProjectFilter, ProjectCreate, ProjectUpdate


class TestProjectRepository:
    """Test cases for Project Repository."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = Mock(spec=Session)
        # Setup default query chain
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.first.return_value = None
        mock_query.count.return_value = 0
        mock_query.scalar.return_value = 0
        db.query.return_value = mock_query
        return db

    @pytest.fixture
    def repository(self, mock_db):
        """Project repository with mocked database."""
        return ProjectRepository(Project, mock_db)

    @pytest.fixture
    def sample_project(self):
        """Sample project for testing."""
        project = Project()
        project.id = 1
        project.code = "TEST-001"
        project.name = "Test Project"
        project.organization_id = 1
        project.department_id = 1
        project.owner_id = 1
        project.status = ProjectStatus.ACTIVE
        project.priority = ProjectPriority.HIGH
        project.start_date = date.today()
        project.end_date = date.today() + timedelta(days=90)
        project.is_active = True
        return project

    # Test Basic CRUD Operations

    def test_get_by_code_success(self, repository, mock_db, sample_project):
        """Test getting project by code."""
        mock_db.query().filter().first.return_value = sample_project

        result = repository.get_by_code("TEST-001", organization_id=1)

        assert result == sample_project
        mock_db.query.assert_called_with(Project)

    def test_get_by_code_not_found(self, repository, mock_db):
        """Test getting project by code when not found."""
        mock_db.query().filter().first.return_value = None

        result = repository.get_by_code("NONEXISTENT", organization_id=1)

        assert result is None

    def test_validate_unique_code_true(self, repository, mock_db):
        """Test validating unique code when code is available."""
        mock_db.query().filter().first.return_value = None

        result = repository.validate_unique_code("NEW-CODE", organization_id=1)

        assert result is True

    def test_validate_unique_code_false(self, repository, mock_db, sample_project):
        """Test validating unique code when code exists."""
        mock_db.query().filter().first.return_value = sample_project

        result = repository.validate_unique_code("TEST-001", organization_id=1)

        assert result is False

    def test_validate_unique_code_with_exclude(self, repository, mock_db):
        """Test validating unique code excluding specific project."""
        mock_db.query().filter().first.return_value = None

        result = repository.validate_unique_code(
            "TEST-001", organization_id=1, exclude_id=1
        )

        assert result is True

    # Test Filtering and Search

    def test_get_filtered_query_basic(self, repository, mock_db):
        """Test building filtered query with basic filters."""
        filters = ProjectFilter(
            organization_id=1,
            department_id=2,
            status=ProjectStatus.ACTIVE,
            priority=ProjectPriority.HIGH,
        )

        query = repository.get_filtered_query(filters)

        # Verify filter calls
        assert mock_db.query.called
        assert query.filter.called

    def test_get_filtered_query_with_search(self, repository, mock_db):
        """Test building filtered query with search term."""
        filters = ProjectFilter(
            organization_id=1,
            search="test project",
        )

        query = repository.get_filtered_query(filters)

        # Verify filter calls for search
        assert mock_db.query.called
        assert query.filter.called

    def test_get_filtered_query_with_date_range(self, repository, mock_db):
        """Test building filtered query with date range."""
        filters = ProjectFilter(
            organization_id=1,
            start_date_from=date.today() - timedelta(days=30),
            start_date_to=date.today(),
            end_date_from=date.today(),
            end_date_to=date.today() + timedelta(days=90),
        )

        query = repository.get_filtered_query(filters)

        # Verify filter calls
        assert mock_db.query.called
        assert query.filter.called

    def test_get_filtered_query_with_budget_range(self, repository, mock_db):
        """Test building filtered query with budget range."""
        filters = ProjectFilter(
            organization_id=1,
            budget_min=100000.0,
            budget_max=1000000.0,
        )

        query = repository.get_filtered_query(filters)

        # Verify filter calls
        assert mock_db.query.called
        assert query.filter.called

    def test_get_filtered_query_overdue_projects(self, repository, mock_db):
        """Test filtering overdue projects."""
        filters = ProjectFilter(
            organization_id=1,
            is_overdue=True,
        )

        query = repository.get_filtered_query(filters)

        # Verify filter calls
        assert mock_db.query.called
        assert query.filter.called

    def test_get_filtered_query_with_tags(self, repository, mock_db):
        """Test filtering by tags."""
        filters = ProjectFilter(
            organization_id=1,
            tags=["development", "urgent"],
        )

        query = repository.get_filtered_query(filters)

        # Verify filter calls
        assert mock_db.query.called
        assert query.filter.called

    def test_search_projects(self, repository, mock_db):
        """Test searching projects."""
        projects = [
            Mock(id=1, name="Test Project 1"),
            Mock(id=2, name="Test Project 2"),
        ]
        mock_db.query().filter().all.return_value = projects

        result = repository.search_projects("test", organization_id=1)

        assert len(result) == 2
        assert mock_db.query.called

    # Test Tree Structure

    def test_get_project_tree(self, repository, mock_db):
        """Test getting project tree structure."""
        # Create sample hierarchy
        root_projects = [
            Mock(id=1, name="Root 1", parent_id=None),
            Mock(id=2, name="Root 2", parent_id=None),
        ]
        child_projects = [
            Mock(id=3, name="Child 1", parent_id=1),
            Mock(id=4, name="Child 2", parent_id=1),
        ]

        # Setup mock returns
        def query_side_effect(*args):
            query = Mock()
            query.filter.return_value = query
            query.all.return_value = root_projects
            return query

        mock_db.query.side_effect = query_side_effect

        # Mock get_children method
        with patch.object(repository, 'get_children', return_value=child_projects):
            result = repository.get_project_tree(organization_id=1)

        assert len(result) == 2
        assert result[0]["id"] == 1

    def test_get_children(self, repository, mock_db):
        """Test getting child projects."""
        children = [
            Mock(id=2, parent_id=1),
            Mock(id=3, parent_id=1),
        ]
        mock_db.query().filter().all.return_value = children

        result = repository.get_children(parent_id=1)

        assert len(result) == 2
        assert all(child.parent_id == 1 for child in result)

    def test_get_all_descendants(self, repository, mock_db):
        """Test getting all descendant projects."""
        # Setup mock for recursive queries
        descendants = [
            Mock(id=2, parent_id=1),
            Mock(id=3, parent_id=1),
            Mock(id=4, parent_id=2),
        ]

        # Mock the recursive behavior
        def get_children_mock(parent_id):
            if parent_id == 1:
                return [d for d in descendants if d.id in [2, 3]]
            elif parent_id == 2:
                return [d for d in descendants if d.id == 4]
            else:
                return []

        with patch.object(repository, 'get_children', side_effect=get_children_mock):
            result = repository.get_all_descendants(project_id=1)

        assert len(result) == 3

    # Test Statistics Queries

    def test_get_project_statistics(self, repository, mock_db):
        """Test getting project statistics."""
        # Mock various count queries
        mock_db.query().filter().count.return_value = 5  # members
        mock_db.query().filter().scalar.return_value = 3  # completed tasks
        mock_db.scalar.return_value = 10  # total tasks

        stats = repository.get_project_statistics(project_id=1)

        assert "member_count" in stats
        assert "task_count" in stats
        assert mock_db.query.called

    def test_get_organization_project_stats(self, repository, mock_db):
        """Test getting organization-wide project statistics."""
        # Setup mock query results
        mock_result = Mock()
        mock_result.active_count = 10
        mock_result.completed_count = 5
        mock_result.on_hold_count = 2
        mock_result.total_budget = 5000000.0
        mock_result.total_actual_cost = 3000000.0

        mock_db.query().filter().first.return_value = mock_result

        stats = repository.get_organization_project_stats(organization_id=1)

        assert stats["active_projects"] == 10
        assert stats["completed_projects"] == 5
        assert stats["total_budget"] == 5000000.0

    def test_get_department_project_stats(self, repository, mock_db):
        """Test getting department project statistics."""
        # Mock query results
        mock_db.query().filter().count.side_effect = [8, 3, 1]  # total, active, overdue
        mock_db.query().filter().scalar.side_effect = [2000000.0, 1500000.0]  # budget, cost

        stats = repository.get_department_project_stats(
            organization_id=1, department_id=1
        )

        assert stats["total_projects"] == 8
        assert stats["active_projects"] == 3
        assert stats["overdue_projects"] == 1

    def test_get_user_project_stats(self, repository, mock_db):
        """Test getting user project statistics."""
        # Mock different project counts
        mock_db.query().filter().count.side_effect = [5, 3, 10]  # owned, managed, member

        stats = repository.get_user_project_stats(user_id=1)

        assert stats["owned_projects"] == 5
        assert stats["managed_projects"] == 3
        assert stats["member_projects"] == 10

    # Test Member Queries

    def test_get_project_members(self, repository, mock_db):
        """Test getting project members."""
        members = [
            Mock(user_id=1, role="manager"),
            Mock(user_id=2, role="developer"),
        ]
        mock_db.query().filter().all.return_value = members

        result = repository.get_project_members(project_id=1)

        assert len(result) == 2
        assert result[0].role == "manager"

    def test_get_user_projects(self, repository, mock_db):
        """Test getting projects for a user."""
        projects = [
            Mock(id=1, name="Project 1"),
            Mock(id=2, name="Project 2"),
        ]
        mock_db.query().join().filter().distinct().all.return_value = projects

        result = repository.get_user_projects(user_id=1)

        assert len(result) == 2
        mock_db.query().join.assert_called()

    # Test Milestone Queries

    def test_get_project_milestones(self, repository, mock_db):
        """Test getting project milestones."""
        milestones = [
            Mock(id=1, name="Milestone 1", due_date=date.today()),
            Mock(id=2, name="Milestone 2", due_date=date.today() + timedelta(days=30)),
        ]
        mock_db.query().filter().order_by().all.return_value = milestones

        result = repository.get_project_milestones(project_id=1)

        assert len(result) == 2
        assert result[0].name == "Milestone 1"

    def test_get_upcoming_milestones(self, repository, mock_db):
        """Test getting upcoming milestones."""
        milestones = [
            Mock(id=1, due_date=date.today() + timedelta(days=7)),
            Mock(id=2, due_date=date.today() + timedelta(days=14)),
        ]
        mock_db.query().filter().order_by().limit().all.return_value = milestones

        result = repository.get_upcoming_milestones(days_ahead=30, limit=10)

        assert len(result) == 2
        mock_db.query().filter.assert_called()

    # Test Aggregation Queries

    def test_get_budget_summary_by_status(self, repository, mock_db):
        """Test getting budget summary grouped by status."""
        summary_data = [
            (ProjectStatus.ACTIVE, 5000000.0, 3000000.0, 5),
            (ProjectStatus.COMPLETED, 3000000.0, 2800000.0, 3),
        ]
        mock_db.query().filter().group_by().all.return_value = summary_data

        result = repository.get_budget_summary_by_status(organization_id=1)

        assert len(result) == 2
        assert result[0]["status"] == ProjectStatus.ACTIVE
        assert result[0]["total_budget"] == 5000000.0

    def test_get_project_timeline(self, repository, mock_db):
        """Test getting project timeline data."""
        timeline_data = [
            Mock(month="2024-01", started=3, completed=1),
            Mock(month="2024-02", started=5, completed=2),
        ]
        mock_db.query().filter().group_by().order_by().all.return_value = timeline_data

        result = repository.get_project_timeline(
            organization_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )

        assert len(result) == 2
        assert result[0]["month"] == "2024-01"

    # Test Complex Queries

    def test_get_cross_department_projects(self, repository, mock_db):
        """Test getting cross-department projects."""
        projects = [
            Mock(id=1, name="Cross Dept Project 1"),
            Mock(id=2, name="Cross Dept Project 2"),
        ]
        mock_db.query().filter().all.return_value = projects

        result = repository.get_cross_department_projects(organization_id=1)

        assert len(result) == 2

    def test_get_projects_by_member_role(self, repository, mock_db):
        """Test getting projects filtered by member role."""
        projects = [
            Mock(id=1, name="Manager Project"),
            Mock(id=2, name="Developer Project"),
        ]
        mock_db.query().join().filter().all.return_value = projects

        result = repository.get_projects_by_member_role(user_id=1, role="manager")

        assert len(result) == 2
        mock_db.query().join.assert_called()

    def test_get_project_dependencies(self, repository, mock_db):
        """Test getting project dependencies."""
        # Mock projects with parent relationships
        dependencies = [
            {"id": 1, "depends_on": [2, 3]},
            {"id": 2, "depends_on": []},
            {"id": 3, "depends_on": [2]},
        ]

        with patch.object(repository, '_analyze_dependencies', return_value=dependencies):
            result = repository.get_project_dependencies(project_id=1)

        assert len(result) == 3
        assert result[0]["depends_on"] == [2, 3]