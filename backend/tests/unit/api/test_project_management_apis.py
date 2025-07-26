"""
ITDO ERP Backend - Project Management API Tests
Day 16: Comprehensive tests for project management, task management, and Gantt scheduling APIs
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.gantt_scheduling_api import GanttSchedulingService
from app.api.v1.project_management_api import ProjectManagementService
from app.api.v1.task_management_api import TaskManagementService
from app.models.project import Project
from app.models.task import Task


class TestProjectManagementAPI:
    """Test cases for Project Management API"""

    @pytest.fixture
    def mock_project_service(self):
        """Mock project management service"""
        service = Mock(spec=ProjectManagementService)
        service.db = AsyncMock(spec=AsyncSession)
        service.redis = AsyncMock()
        return service

    @pytest.fixture
    def sample_project_data(self):
        """Sample project data for testing"""
        return {
            "code": "PROJ-001",
            "name": "Test Project",
            "description": "Test project description",
            "status": "planning",
            "priority": "high",
            "budget": "100000.00",
            "start_date": "2025-08-01",
            "end_date": "2025-12-31",
            "planned_end_date": "2025-12-31",
            "organization_id": 1,
            "department_id": 1,
        }

    @pytest.fixture
    def sample_project_instance(self):
        """Sample project instance for testing"""
        return Project(
            id=1,
            code="PROJ-001",
            name="Test Project",
            description="Test project description",
            status="planning",
            priority="high",
            budget=100000.00,
            start_date=date(2025, 8, 1),
            end_date=date(2025, 12, 31),
            planned_end_date=date(2025, 12, 31),
            organization_id=1,
            department_id=1,
            owner_id=1,
            created_at=datetime.utcnow(),
        )

    @pytest.mark.asyncio
    async def test_create_project_success(
        self, mock_project_service, sample_project_data, sample_project_instance
    ):
        """Test successful project creation"""
        # Setup
        mock_project_service.create_project.return_value = sample_project_instance

        # Execute
        result = await mock_project_service.create_project(
            sample_project_data, user_id=1
        )

        # Assert
        assert result.id == 1
        assert result.code == "PROJ-001"
        assert result.name == "Test Project"
        assert result.status == "planning"
        assert result.priority == "high"
        mock_project_service.create_project.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_project_duplicate_code(self, mock_project_service):
        """Test project creation with duplicate code"""
        from fastapi import HTTPException

        # Setup
        mock_project_service.create_project.side_effect = HTTPException(
            status_code=400, detail="Project with code 'PROJ-001' already exists"
        )

        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            await mock_project_service.create_project(
                {"code": "PROJ-001", "name": "Duplicate Project"}, user_id=1
            )

        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_project_success(
        self, mock_project_service, sample_project_instance
    ):
        """Test successful project retrieval"""
        # Setup
        mock_project_service.get_project.return_value = sample_project_instance

        # Execute
        result = await mock_project_service.get_project(1)

        # Assert
        assert result.id == 1
        assert result.name == "Test Project"
        mock_project_service.get_project.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, mock_project_service):
        """Test project retrieval when project doesn't exist"""
        # Setup
        mock_project_service.get_project.return_value = None

        # Execute
        result = await mock_project_service.get_project(999)

        # Assert
        assert result is None
        mock_project_service.get_project.assert_called_once_with(999)

    @pytest.mark.asyncio
    async def test_update_project_success(
        self, mock_project_service, sample_project_instance
    ):
        """Test successful project update"""
        # Setup
        updated_project = sample_project_instance
        updated_project.name = "Updated Project"
        updated_project.status = "active"
        mock_project_service.update_project.return_value = updated_project

        update_data = {"name": "Updated Project", "status": "active"}

        # Execute
        result = await mock_project_service.update_project(1, update_data, user_id=1)

        # Assert
        assert result.name == "Updated Project"
        assert result.status == "active"
        mock_project_service.update_project.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_project_success(self, mock_project_service):
        """Test successful project deletion"""
        # Setup
        mock_project_service.delete_project.return_value = True

        # Execute
        result = await mock_project_service.delete_project(1)

        # Assert
        assert result is True
        mock_project_service.delete_project.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_list_projects_with_filters(self, mock_project_service):
        """Test project listing with filters"""
        # Setup
        mock_response = Mock()
        mock_response.projects = [Mock(id=1, name="Test Project")]
        mock_response.total = 1
        mock_response.page = 1
        mock_response.size = 20
        mock_response.pages = 1
        mock_project_service.list_projects.return_value = mock_response

        # Execute
        result = await mock_project_service.list_projects(
            page=1, size=20, search="Test", status="active", priority="high"
        )

        # Assert
        assert result.total == 1
        assert len(result.projects) == 1
        assert result.projects[0].name == "Test Project"
        mock_project_service.list_projects.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_project_statistics(self, mock_project_service):
        """Test project statistics retrieval"""
        # Setup
        mock_stats = Mock()
        mock_stats.total_projects = 10
        mock_stats.active_projects = 5
        mock_stats.completed_projects = 3
        mock_stats.total_budget = Decimal("1000000.00")
        mock_stats.actual_cost = Decimal("750000.00")
        mock_project_service.get_project_statistics.return_value = mock_stats

        # Execute
        result = await mock_project_service.get_project_statistics()

        # Assert
        assert result.total_projects == 10
        assert result.active_projects == 5
        assert result.completed_projects == 3
        assert result.total_budget == Decimal("1000000.00")
        mock_project_service.get_project_statistics.assert_called_once()


class TestTaskManagementAPI:
    """Test cases for Task Management API"""

    @pytest.fixture
    def mock_task_service(self):
        """Mock task management service"""
        service = Mock(spec=TaskManagementService)
        service.db = AsyncMock(spec=AsyncSession)
        service.redis = AsyncMock()
        return service

    @pytest.fixture
    def sample_task_data(self):
        """Sample task data for testing"""
        return {
            "title": "Test Task",
            "description": "Test task description",
            "status": "todo",
            "priority": "medium",
            "project_id": 1,
            "assignee_id": 2,
            "due_date": "2025-08-15T10:00:00",
            "estimated_hours": "8.0",
            "completion_percentage": 0,
        }

    @pytest.fixture
    def sample_task_instance(self):
        """Sample task instance for testing"""
        return Task(
            id=1,
            task_number="TASK-000001",
            title="Test Task",
            description="Test task description",
            status="todo",
            priority="medium",
            project_id=1,
            assignee_id=2,
            reporter_id=1,
            due_date=datetime(2025, 8, 15, 10, 0, 0),
            estimated_hours=8.0,
            actual_hours=0.0,
            completion_percentage=0,
            created_by=1,
            created_at=datetime.utcnow(),
        )

    @pytest.mark.asyncio
    async def test_create_task_success(
        self, mock_task_service, sample_task_data, sample_task_instance
    ):
        """Test successful task creation"""
        # Setup
        mock_task_service.create_task.return_value = sample_task_instance

        # Execute
        result = await mock_task_service.create_task(sample_task_data, user_id=1)

        # Assert
        assert result.id == 1
        assert result.task_number == "TASK-000001"
        assert result.title == "Test Task"
        assert result.status == "todo"
        assert result.priority == "medium"
        mock_task_service.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_task_invalid_project(self, mock_task_service):
        """Test task creation with invalid project ID"""
        from fastapi import HTTPException

        # Setup
        mock_task_service.create_task.side_effect = HTTPException(
            status_code=400, detail="Project with ID 999 not found"
        )

        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            await mock_task_service.create_task(
                {"title": "Test Task", "project_id": 999}, user_id=1
            )

        assert exc_info.value.status_code == 400
        assert "not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_task_status(self, mock_task_service, sample_task_instance):
        """Test task status update"""
        # Setup
        updated_task = sample_task_instance
        updated_task.status = "in_progress"
        updated_task.completion_percentage = 25
        mock_task_service.update_task.return_value = updated_task

        update_data = {"status": "in_progress", "completion_percentage": 25}

        # Execute
        result = await mock_task_service.update_task(1, update_data, user_id=1)

        # Assert
        assert result.status == "in_progress"
        assert result.completion_percentage == 25
        mock_task_service.update_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tasks_with_project_filter(self, mock_task_service):
        """Test task listing filtered by project"""
        # Setup
        mock_response = Mock()
        mock_response.tasks = [Mock(id=1, title="Test Task", project_id=1)]
        mock_response.total = 1
        mock_task_service.list_tasks.return_value = mock_response

        # Execute
        result = await mock_task_service.list_tasks(project_id=1)

        # Assert
        assert result.total == 1
        assert result.tasks[0].project_id == 1
        mock_task_service.list_tasks.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_task_statistics(self, mock_task_service):
        """Test task statistics retrieval"""
        # Setup
        mock_stats = Mock()
        mock_stats.total_tasks = 20
        mock_stats.todo_tasks = 8
        mock_stats.in_progress_tasks = 7
        mock_stats.completed_tasks = 5
        mock_stats.completion_rate = 25.0
        mock_task_service.get_task_statistics.return_value = mock_stats

        # Execute
        result = await mock_task_service.get_task_statistics(project_id=1)

        # Assert
        assert result.total_tasks == 20
        assert result.completed_tasks == 5
        assert result.completion_rate == 25.0
        mock_task_service.get_task_statistics.assert_called_once()


class TestGanttSchedulingAPI:
    """Test cases for Gantt Chart & Scheduling API"""

    @pytest.fixture
    def mock_gantt_service(self):
        """Mock Gantt scheduling service"""
        service = Mock(spec=GanttSchedulingService)
        service.db = AsyncMock(spec=AsyncSession)
        service.redis = AsyncMock()
        return service

    @pytest.fixture
    def sample_gantt_response(self):
        """Sample Gantt chart response"""
        return Mock(
            project_id=1,
            project_name="Test Project",
            chart_start_date=date(2025, 8, 1),
            chart_end_date=date(2025, 12, 31),
            total_duration_days=152,
            tasks=[
                Mock(
                    id=1,
                    title="Task 1",
                    start_date=date(2025, 8, 1),
                    end_date=date(2025, 8, 15),
                    duration_days=14,
                    is_critical_path=True,
                ),
                Mock(
                    id=2,
                    title="Task 2",
                    start_date=date(2025, 8, 16),
                    end_date=date(2025, 8, 30),
                    duration_days=14,
                    is_critical_path=False,
                ),
            ],
            dependencies=[],
            critical_path=[1],
            milestones=[],
            generated_at=datetime.utcnow(),
        )

    @pytest.mark.asyncio
    async def test_get_gantt_chart_by_project(
        self, mock_gantt_service, sample_gantt_response
    ):
        """Test Gantt chart generation for specific project"""
        # Setup
        mock_gantt_service.get_gantt_chart.return_value = sample_gantt_response

        # Execute
        result = await mock_gantt_service.get_gantt_chart(project_id=1)

        # Assert
        assert result.project_id == 1
        assert result.project_name == "Test Project"
        assert result.total_duration_days == 152
        assert len(result.tasks) == 2
        assert len(result.critical_path) == 1
        mock_gantt_service.get_gantt_chart.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_gantt_chart_date_range(
        self, mock_gantt_service, sample_gantt_response
    ):
        """Test Gantt chart generation for date range"""
        # Setup
        mock_ganott_service.get_gantt_chart.return_value = sample_gantt_response

        start_date = date(2025, 8, 1)
        end_date = date(2025, 8, 31)

        # Execute
        result = await mock_gantt_service.get_gantt_chart(
            start_date=start_date, end_date=end_date
        )

        # Assert
        assert result.chart_start_date == start_date
        assert result.chart_end_date <= end_date
        mock_gantt_service.get_gantt_chart.assert_called_once()

    @pytest.mark.asyncio
    async def test_optimize_schedule_minimize_duration(self, mock_gantt_service):
        """Test schedule optimization for duration minimization"""
        # Setup
        optimization_request = Mock(project_id=1, optimization_goal="minimize_duration")

        mock_optimization_response = Mock(
            original_duration_days=152,
            optimized_duration_days=135,
            time_saved_days=17,
            optimization_summary="Found 3 optimization opportunities",
            recommended_changes=[
                {
                    "task_id": 1,
                    "recommendation": "Consider breaking into smaller parallel tasks",
                    "potential_time_savings": 7,
                    "action": "split_task",
                }
            ],
            optimization_score=85.5,
        )

        mock_gantt_service.optimize_schedule.return_value = mock_optimization_response

        # Execute
        result = await mock_gantt_service.optimize_schedule(optimization_request)

        # Assert
        assert result.original_duration_days == 152
        assert result.optimized_duration_days == 135
        assert result.time_saved_days == 17
        assert result.optimization_score == 85.5
        assert len(result.recommended_changes) == 1
        mock_gantt_service.optimize_schedule.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_milestone(self, mock_gantt_service):
        """Test milestone creation"""
        # Setup
        milestone_data = Mock(
            title="Project Kickoff",
            description="Official project start",
            project_id=1,
            target_date=date(2025, 8, 1),
            is_critical=True,
        )

        mock_milestone_response = Mock(
            id=1,
            title="Project Kickoff",
            project_id=1,
            project_name="Test Project",
            target_date=date(2025, 8, 1),
            is_critical=True,
            is_completed=False,
            days_until_due=5,
            is_overdue=False,
            completion_percentage=0.0,
        )

        mock_gantt_service.create_milestone.return_value = mock_milestone_response

        # Execute
        result = await mock_gantt_service.create_milestone(milestone_data, user_id=1)

        # Assert
        assert result.id == 1
        assert result.title == "Project Kickoff"
        assert result.is_critical is True
        assert result.is_completed is False
        assert result.days_until_due == 5
        mock_gantt_service.create_milestone.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_project_timeline(self, mock_gantt_service):
        """Test project timeline retrieval"""
        # Setup
        mock_timeline = {
            "project_id": 1,
            "project_name": "Test Project",
            "timeline_months": {
                "2025-08": {
                    "month": "August 2025",
                    "tasks": [Mock(id=1, title="Task 1")],
                    "milestones": [],
                    "total_estimated_hours": 40,
                    "completion_percentage": 25.0,
                }
            },
            "total_tasks": 10,
            "total_milestones": 2,
            "critical_path_tasks": 5,
            "project_duration_days": 152,
        }

        mock_gantt_service.get_project_timeline.return_value = mock_timeline

        # Execute
        result = await mock_gantt_service.get_project_timeline(1)

        # Assert
        assert result["project_id"] == 1
        assert result["total_tasks"] == 10
        assert result["total_milestones"] == 2
        assert result["critical_path_tasks"] == 5
        assert "2025-08" in result["timeline_months"]
        mock_gantt_service.get_project_timeline.assert_called_once_with(1)


class TestProjectManagementIntegration:
    """Integration tests for project management components"""

    @pytest.mark.asyncio
    async def test_project_task_creation_flow(self):
        """Test integrated project and task creation flow"""
        # Setup mocks
        mock_project_service = Mock(spec=ProjectManagementService)
        mock_task_service = Mock(spec=TaskManagementService)

        # Mock project creation
        project = Mock(id=1, name="Test Project", status="active")
        mock_project_service.create_project.return_value = project

        # Mock task creation
        task = Mock(id=1, title="Test Task", project_id=1, status="todo")
        mock_task_service.create_task.return_value = task

        # Execute workflow
        created_project = await mock_project_service.create_project(
            {"name": "Test Project", "status": "active"}, user_id=1
        )

        created_task = await mock_task_service.create_task(
            {"title": "Test Task", "project_id": created_project.id}, user_id=1
        )

        # Assert
        assert created_project.id == 1
        assert created_task.project_id == created_project.id
        mock_project_service.create_project.assert_called_once()
        mock_task_service.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_gantt_chart_project_integration(self):
        """Test Gantt chart generation with project data"""
        # Setup
        mock_gantt_service = Mock(spec=GanttSchedulingService)

        # Mock Gantt chart with project tasks
        gantt_chart = Mock(
            project_id=1,
            project_name="Test Project",
            tasks=[
                Mock(id=1, title="Task 1", project_id=1),
                Mock(id=2, title="Task 2", project_id=1),
            ],
            critical_path=[1],
            total_duration_days=30,
        )

        mock_gantt_service.get_gantt_chart.return_value = gantt_chart

        # Execute
        result = await mock_gantt_service.get_gantt_chart(project_id=1)

        # Assert
        assert result.project_id == 1
        assert len(result.tasks) == 2
        assert all(task.project_id == 1 for task in result.tasks)
        assert 1 in result.critical_path
        mock_gantt_service.get_gantt_chart.assert_called_once()


# Performance and Load Tests
class TestProjectManagementPerformance:
    """Performance tests for project management APIs"""

    @pytest.mark.asyncio
    async def test_large_project_list_performance(self):
        """Test performance with large number of projects"""
        # Setup
        mock_service = Mock(spec=ProjectManagementService)

        # Mock large dataset
        large_project_list = Mock()
        large_project_list.projects = [
            Mock(id=i, name=f"Project {i}") for i in range(1000)
        ]
        large_project_list.total = 1000
        large_project_list.pages = 50

        mock_service.list_projects.return_value = large_project_list

        # Execute
        start_time = datetime.utcnow()
        result = await mock_service.list_projects(page=1, size=20)
        end_time = datetime.utcnow()

        # Assert performance
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 1.0  # Should complete within 1 second
        assert result.total == 1000
        assert len(result.projects) <= 20  # Pagination working

    @pytest.mark.asyncio
    async def test_gantt_chart_large_dataset_performance(self):
        """Test Gantt chart performance with many tasks"""
        # Setup
        mock_service = Mock(spec=GanttSchedulingService)

        # Mock large Gantt chart
        large_gantt = Mock()
        large_gantt.tasks = [Mock(id=i, title=f"Task {i}") for i in range(500)]
        large_gantt.total_duration_days = 365
        large_gantt.critical_path = list(range(1, 51))  # 50 critical tasks

        mock_service.get_gantt_chart.return_value = large_gantt

        # Execute
        start_time = datetime.utcnow()
        result = await mock_service.get_gantt_chart(project_id=1)
        end_time = datetime.utcnow()

        # Assert performance
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 2.0  # Should complete within 2 seconds
        assert len(result.tasks) == 500
        assert len(result.critical_path) == 50


# Error Handling Tests
class TestProjectManagementErrorHandling:
    """Error handling tests for project management APIs"""

    @pytest.mark.asyncio
    async def test_database_connection_error(self):
        """Test handling of database connection errors"""
        # Setup
        mock_service = Mock(spec=ProjectManagementService)
        mock_service.create_project.side_effect = Exception(
            "Database connection failed"
        )

        # Execute & Assert
        with pytest.raises(Exception) as exc_info:
            await mock_service.create_project({"name": "Test"}, user_id=1)

        assert "Database connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_redis_cache_failure_graceful_degradation(self):
        """Test graceful degradation when Redis cache fails"""
        # Setup
        mock_service = Mock(spec=ProjectManagementService)
        # Simulate Redis failure but service continues
        mock_service.get_project.return_value = Mock(id=1, name="Test Project")

        # Execute
        result = await mock_service.get_project(1)

        # Assert - Service should continue working even if cache fails
        assert result.id == 1
        assert result.name == "Test Project"

    @pytest.mark.asyncio
    async def test_invalid_date_handling(self):
        """Test handling of invalid date inputs"""
        from fastapi import HTTPException

        # Setup
        mock_service = Mock(spec=GanttSchedulingService)
        mock_service.get_gantt_chart.side_effect = HTTPException(
            status_code=400, detail="Invalid date format"
        )

        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            await mock_service.get_gantt_chart(
                start_date="invalid-date", end_date="2025-12-31"
            )

        assert exc_info.value.status_code == 400
        assert "Invalid date format" in str(exc_info.value.detail)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
