"""
ITDO ERP Backend - Project Management Integration Tests
Day 19: Comprehensive integration tests for all project management components
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.gantt_scheduling_api import GanttSchedulingService
from app.api.v1.project_dashboard_api import ProjectDashboardService
from app.api.v1.project_integration_api import ProjectIntegrationService
from app.api.v1.project_management_api import ProjectManagementService
from app.api.v1.task_management_api import TaskManagementService
from app.api.v1.team_management_api import TeamManagementService


class TestProjectManagementIntegration:
    """Integration tests for complete project management workflow"""

    @pytest.fixture
    async def integration_service(self):
        """Mock integration service with all components"""
        db = AsyncMock(spec=AsyncSession)
        redis = AsyncMock()
        service = ProjectIntegrationService(db, redis)

        # Mock all component services
        service.project_service = AsyncMock(spec=ProjectManagementService)
        service.task_service = AsyncMock(spec=TaskManagementService)
        service.gantt_service = AsyncMock(spec=GanttSchedulingService)
        service.team_service = AsyncMock(spec=TeamManagementService)
        service.dashboard_service = AsyncMock(spec=ProjectDashboardService)

        return service

    @pytest.fixture
    def complete_project_request(self):
        """Sample complete project creation request"""
        return {
            "project_data": {
                "code": "PROJ-INTEGRATION-001",
                "name": "Integration Test Project",
                "description": "Complete project for integration testing",
                "status": "planning",
                "priority": "high",
                "budget": "500000.00",
                "start_date": "2025-08-01",
                "end_date": "2025-12-31",
                "organization_id": 1,
            },
            "team_members": [
                {
                    "user_id": 1,
                    "role": "owner",
                    "allocation_percentage": 100,
                    "hourly_rate": "150.00",
                },
                {
                    "user_id": 2,
                    "role": "manager",
                    "allocation_percentage": 80,
                    "hourly_rate": "120.00",
                },
                {
                    "user_id": 3,
                    "role": "member",
                    "allocation_percentage": 100,
                    "hourly_rate": "80.00",
                },
            ],
            "initial_tasks": [
                {
                    "title": "Project Setup",
                    "description": "Initial project setup and configuration",
                    "priority": "high",
                    "estimated_hours": "16.0",
                    "due_date": "2025-08-05T17:00:00",
                },
                {
                    "title": "Requirements Analysis",
                    "description": "Analyze and document requirements",
                    "priority": "high",
                    "estimated_hours": "40.0",
                    "due_date": "2025-08-15T17:00:00",
                },
                {
                    "title": "Architecture Design",
                    "description": "Design system architecture",
                    "priority": "medium",
                    "estimated_hours": "24.0",
                    "due_date": "2025-08-25T17:00:00",
                },
            ],
            "milestones": [
                {
                    "title": "Phase 1 Complete",
                    "description": "First phase milestone",
                    "target_date": "2025-09-30",
                    "is_critical": True,
                },
                {
                    "title": "Beta Release",
                    "description": "Beta version release",
                    "target_date": "2025-11-15",
                    "is_critical": True,
                },
            ],
            "auto_create_gantt": True,
            "auto_setup_dashboard": True,
            "notify_team": True,
        }

    @pytest.mark.asyncio
    async def test_complete_project_creation_workflow(
        self, integration_service, complete_project_request
    ):
        """Test complete project creation workflow"""

        # Mock service responses
        mock_project = Mock(
            id=1, name="Integration Test Project", code="PROJ-INTEGRATION-001"
        )
        integration_service.project_service.create_project.return_value = mock_project

        mock_team_members = [
            Mock(id=1, user_id=1, role="owner"),
            Mock(id=2, user_id=2, role="manager"),
            Mock(id=3, user_id=3, role="member"),
        ]
        integration_service.team_service.add_team_member.side_effect = mock_team_members

        mock_tasks = [
            Mock(id=1, title="Project Setup", project_id=1),
            Mock(id=2, title="Requirements Analysis", project_id=1),
            Mock(id=3, title="Architecture Design", project_id=1),
        ]
        integration_service.task_service.create_task.side_effect = mock_tasks

        mock_milestones = [
            Mock(id=1, title="Phase 1 Complete", project_id=1),
            Mock(id=2, title="Beta Release", project_id=1),
        ]
        integration_service.gantt_service.create_milestone.side_effect = mock_milestones

        mock_gantt = Mock(project_id=1, tasks=mock_tasks, critical_path=[1, 2])
        integration_service.gantt_service.get_gantt_chart.return_value = mock_gantt

        # Execute workflow
        result = await integration_service.create_complete_project(
            complete_project_request, user_id=1
        )

        # Verify workflow execution
        assert result.project.id == 1
        assert result.project.name == "Integration Test Project"
        assert len(result.tasks_created) == 3
        assert len(result.milestones_created) == 2
        assert result.team_setup_result["members_added"] == 3
        assert result.gantt_chart is not None
        assert result.dashboard_setup["status"] == "initialized"
        assert result.workflow_id is not None

        # Verify service calls
        integration_service.project_service.create_project.assert_called_once()
        assert integration_service.team_service.add_team_member.call_count == 3
        assert integration_service.task_service.create_task.call_count == 3
        assert integration_service.gantt_service.create_milestone.call_count == 2
        integration_service.gantt_service.get_gantt_chart.assert_called_once()

    @pytest.mark.asyncio
    async def test_project_component_synchronization(self, integration_service):
        """Test project component synchronization"""

        sync_request = {
            "project_id": 1,
            "sync_tasks": True,
            "sync_team": True,
            "sync_gantt": True,
            "sync_dashboard": True,
            "force_update": False,
        }

        # Mock sync results
        integration_service._sync_project_tasks.return_value = {
            "updated": True,
            "task_count": 5,
            "completed_tasks": 2,
        }

        integration_service._sync_project_team.return_value = {
            "updated": True,
            "team_size": 4,
            "active_members": 4,
        }

        integration_service._sync_project_gantt.return_value = {
            "updated": True,
            "task_count": 5,
            "critical_path_tasks": 3,
        }

        integration_service._sync_project_dashboard.return_value = {
            "updated": True,
            "kpi_count": 5,
            "chart_count": 4,
        }

        # Execute sync
        result = await integration_service.sync_project_components(sync_request)

        # Verify sync results
        assert result.project_id == 1
        assert len(result.updated_components) == 4
        assert "tasks" in result.updated_components
        assert "team" in result.updated_components
        assert "gantt" in result.updated_components
        assert "dashboard" in result.updated_components
        assert result.sync_results["tasks"]["updated"] is True
        assert result.next_sync_time is not None

    @pytest.mark.asyncio
    async def test_integration_health_monitoring(self, integration_service):
        """Test integration system health monitoring"""

        # Mock component health checks
        integration_service.project_service.get_project_statistics.return_value = Mock()
        integration_service.task_service.get_task_statistics.return_value = Mock()
        integration_service.team_service.get_team_statistics.return_value = Mock()
        integration_service.redis.ping.return_value = True
        integration_service.db.execute.return_value = Mock()

        # Mock performance metrics
        integration_service._get_performance_metrics.return_value = {
            "avg_response_time_ms": 125.5,
            "requests_per_second": 45.2,
            "cpu_usage_percent": 23.8,
        }

        # Mock workflow counts
        integration_service._count_workflows.side_effect = [3, 1]  # active, failed

        # Execute health check
        health = await integration_service.get_integration_health()

        # Verify health status
        assert health.overall_status == "healthy"
        assert health.component_status["project_management"] == "healthy"
        assert health.component_status["task_management"] == "healthy"
        assert health.component_status["team_management"] == "healthy"
        assert health.component_status["redis"] == "healthy"
        assert health.component_status["database"] == "healthy"
        assert health.active_workflows == 3
        assert health.failed_workflows == 1
        assert len(health.issues) == 0

    @pytest.mark.asyncio
    async def test_workflow_status_tracking(self, integration_service):
        """Test workflow status tracking"""

        workflow_id = "test_workflow_123"

        # Mock workflow data in Redis
        workflow_data = {
            b"id": b"test_workflow_123",
            b"name": b"Test Workflow",
            b"status": b"completed",
            b"steps": b"[{'name': 'Step 1', 'status': 'completed'}]",
            b"current_step": b"1",
            b"total_steps": b"1",
            b"progress_percentage": b"100.0",
            b"started_at": b"2025-07-26T10:00:00",
            b"completed_at": b"2025-07-26T10:30:00",
            b"error_message": b"",
            b"metadata": b"{}",
        }

        integration_service.redis.hgetall.return_value = workflow_data

        # Get workflow status
        workflow = await integration_service.get_workflow_status(workflow_id)

        # Verify workflow data
        assert workflow is not None
        assert workflow.id == "test_workflow_123"
        assert workflow.name == "Test Workflow"
        assert workflow.status.value == "completed"
        assert workflow.progress_percentage == 100.0
        assert workflow.current_step == 1
        assert workflow.total_steps == 1
        assert workflow.completed_at is not None

    @pytest.mark.asyncio
    async def test_workflow_failure_handling(
        self, integration_service, complete_project_request
    ):
        """Test workflow failure handling"""

        # Mock project creation success
        mock_project = Mock(id=1, name="Test Project")
        integration_service.project_service.create_project.return_value = mock_project

        # Mock team member addition failure
        integration_service.team_service.add_team_member.side_effect = Exception(
            "Team addition failed"
        )

        # Execute workflow and expect failure
        with pytest.raises(Exception) as exc_info:
            await integration_service.create_complete_project(
                complete_project_request, user_id=1
            )

        assert "Project creation workflow failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self, integration_service):
        """Test concurrent workflow execution"""

        # Create multiple project requests
        requests = []
        for i in range(3):
            request = {
                "project_data": {
                    "code": f"PROJ-CONCURRENT-{i:03d}",
                    "name": f"Concurrent Project {i}",
                    "status": "planning",
                    "priority": "medium",
                },
                "team_members": [],
                "initial_tasks": [],
                "milestones": [],
                "auto_create_gantt": False,
                "auto_setup_dashboard": False,
                "notify_team": False,
            }
            requests.append(request)

        # Mock service responses
        mock_projects = [
            Mock(id=i + 1, name=f"Concurrent Project {i}") for i in range(3)
        ]
        integration_service.project_service.create_project.side_effect = mock_projects

        # Execute workflows concurrently
        tasks = [
            integration_service.create_complete_project(req, user_id=1)
            for req in requests
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all workflows completed successfully
        assert len(results) == 3
        for i, result in enumerate(results):
            assert not isinstance(result, Exception)
            assert result.project.id == i + 1
            assert result.workflow_id is not None


class TestProjectManagementPerformance:
    """Performance tests for project management integration"""

    @pytest.fixture
    def performance_service(self):
        """Service for performance testing"""
        db = AsyncMock(spec=AsyncSession)
        redis = AsyncMock()
        return ProjectIntegrationService(db, redis)

    @pytest.mark.asyncio
    async def test_large_project_creation_performance(self, performance_service):
        """Test performance with large project creation"""

        # Create large project request
        large_request = {
            "project_data": {
                "code": "PROJ-LARGE-001",
                "name": "Large Performance Test Project",
                "status": "planning",
            },
            "team_members": [{"user_id": i, "role": "member"} for i in range(50)],
            "initial_tasks": [
                {
                    "title": f"Task {i}",
                    "description": f"Performance test task {i}",
                    "priority": "medium",
                }
                for i in range(100)
            ],
            "milestones": [
                {"title": f"Milestone {i}", "target_date": f"2025-{8 + i:02d}-01"}
                for i in range(5)
            ],
            "auto_create_gantt": True,
            "auto_setup_dashboard": True,
            "notify_team": False,
        }

        # Mock service responses
        mock_project = Mock(id=1, name="Large Performance Test Project")
        performance_service.project_service.create_project.return_value = mock_project

        performance_service.team_service.add_team_member.return_value = Mock()
        performance_service.task_service.create_task.return_value = Mock()
        performance_service.gantt_service.create_milestone.return_value = Mock()
        performance_service.gantt_service.get_gantt_chart.return_value = Mock()

        # Measure execution time
        start_time = datetime.utcnow()
        result = await performance_service.create_complete_project(
            large_request, user_id=1
        )
        end_time = datetime.utcnow()

        execution_time = (end_time - start_time).total_seconds()

        # Verify performance (should complete within reasonable time)
        assert execution_time < 10.0  # Should complete within 10 seconds
        assert result.project.id == 1
        assert result.workflow_id is not None

    @pytest.mark.asyncio
    async def test_bulk_synchronization_performance(self, performance_service):
        """Test performance of bulk project synchronization"""

        # Create multiple sync requests
        sync_requests = [
            {
                "project_id": i,
                "sync_tasks": True,
                "sync_team": True,
                "sync_gantt": True,
                "sync_dashboard": True,
            }
            for i in range(20)
        ]

        # Mock sync methods
        performance_service._sync_project_tasks.return_value = {"updated": True}
        performance_service._sync_project_team.return_value = {"updated": True}
        performance_service._sync_project_gantt.return_value = {"updated": True}
        performance_service._sync_project_dashboard.return_value = {"updated": True}

        # Execute bulk synchronization
        start_time = datetime.utcnow()

        tasks = [
            performance_service.sync_project_components(req) for req in sync_requests
        ]

        results = await asyncio.gather(*tasks)
        end_time = datetime.utcnow()

        execution_time = (end_time - start_time).total_seconds()

        # Verify performance
        assert execution_time < 5.0  # Should complete within 5 seconds
        assert len(results) == 20

        for result in results:
            assert len(result.updated_components) == 4


class TestProjectManagementErrorHandling:
    """Error handling tests for project management integration"""

    @pytest.fixture
    def error_service(self):
        """Service for error testing"""
        db = AsyncMock(spec=AsyncSession)
        redis = AsyncMock()
        return ProjectIntegrationService(db, redis)

    @pytest.mark.asyncio
    async def test_database_connection_failure(self, error_service):
        """Test handling of database connection failures"""

        # Mock database connection failure
        error_service.db.execute.side_effect = Exception("Database connection failed")

        # Test health check with DB failure
        health = await error_service.get_integration_health()

        # Verify degraded status
        assert health.overall_status == "critical"
        assert health.component_status["database"] == "critical"
        assert len(health.issues) > 0

        # Verify error is captured in issues
        db_issue = next(
            (issue for issue in health.issues if issue["component"] == "database"), None
        )
        assert db_issue is not None
        assert db_issue["severity"] == "high"

    @pytest.mark.asyncio
    async def test_redis_connection_failure(self, error_service):
        """Test handling of Redis connection failures"""

        # Mock Redis connection failure
        error_service.redis.ping.side_effect = Exception("Redis connection failed")

        # Test health check with Redis failure
        health = await error_service.get_integration_health()

        # Verify critical status due to Redis failure
        assert health.overall_status == "critical"
        assert health.component_status["redis"] == "critical"

    @pytest.mark.asyncio
    async def test_partial_service_degradation(self, error_service):
        """Test handling of partial service degradation"""

        # Mock partial service failures
        error_service.task_service.get_task_statistics.side_effect = Exception(
            "Task service error"
        )
        error_service.team_service.get_team_statistics.side_effect = Exception(
            "Team service error"
        )

        # Other services working normally
        error_service.project_service.get_project_statistics.return_value = Mock()
        error_service.redis.ping.return_value = True
        error_service.db.execute.return_value = Mock()

        # Test health check
        health = await error_service.get_integration_health()

        # Should be degraded due to multiple service failures
        assert health.overall_status == "degraded"
        assert health.component_status["task_management"] == "degraded"
        assert health.component_status["team_management"] == "degraded"
        assert health.component_status["project_management"] == "healthy"

    @pytest.mark.asyncio
    async def test_workflow_recovery_mechanisms(self, error_service):
        """Test workflow recovery mechanisms"""

        # Mock intermittent failures
        failure_count = 0

        def mock_create_task(*args, **kwargs):
            nonlocal failure_count
            failure_count += 1
            if failure_count <= 2:  # Fail first 2 attempts
                raise Exception("Temporary task creation failure")
            return Mock(id=failure_count, title=f"Task {failure_count}")

        error_service.task_service.create_task.side_effect = mock_create_task
        error_service.project_service.create_project.return_value = Mock(id=1)

        # Create request with tasks
        request = {
            "project_data": {"code": "PROJ-RECOVERY", "name": "Recovery Test"},
            "initial_tasks": [
                {"title": "Task 1"},
                {"title": "Task 2"},
                {"title": "Task 3"},
            ],
            "team_members": [],
            "milestones": [],
            "auto_create_gantt": False,
            "auto_setup_dashboard": False,
            "notify_team": False,
        }

        # Execute workflow - should fail due to task creation errors
        with pytest.raises(Exception):
            await error_service.create_complete_project(request, user_id=1)

        # Verify failure was handled properly
        assert failure_count >= 1  # At least one failure occurred


class TestProjectManagementSecurity:
    """Security tests for project management integration"""

    @pytest.fixture
    def security_service(self):
        """Service for security testing"""
        db = AsyncMock(spec=AsyncSession)
        redis = AsyncMock()
        return ProjectIntegrationService(db, redis)

    @pytest.mark.asyncio
    async def test_workflow_isolation(self, security_service):
        """Test workflow isolation between users"""

        # Create workflows for different users
        workflow_ids = []

        for user_id in [1, 2, 3]:
            request = {
                "project_data": {
                    "code": f"PROJ-USER-{user_id}",
                    "name": f"User {user_id} Project",
                },
                "team_members": [],
                "initial_tasks": [],
                "milestones": [],
                "auto_create_gantt": False,
                "auto_setup_dashboard": False,
                "notify_team": False,
            }

            # Mock project creation
            security_service.project_service.create_project.return_value = Mock(
                id=user_id, name=f"User {user_id} Project"
            )

            result = await security_service.create_complete_project(
                request, user_id=user_id
            )
            workflow_ids.append(result.workflow_id)

        # Verify each workflow has unique ID
        assert len(set(workflow_ids)) == 3

        # Verify workflows are properly isolated
        for i, workflow_id in enumerate(workflow_ids):
            # Mock workflow data specific to user
            workflow_data = {
                b"id": workflow_id.encode(),
                b"name": f"User {i + 1} Project Creation".encode(),
                b"status": b"completed",
            }
            security_service.redis.hgetall.return_value = workflow_data

            workflow = await security_service.get_workflow_status(workflow_id)
            assert workflow.id == workflow_id
            assert f"User {i + 1}" in workflow.name

    @pytest.mark.asyncio
    async def test_sensitive_data_handling(self, security_service):
        """Test handling of sensitive data in workflows"""

        # Create request with sensitive data
        request = {
            "project_data": {
                "code": "PROJ-SENSITIVE",
                "name": "Sensitive Data Project",
                "budget": "1000000.00",  # Sensitive budget info
                "description": "Project with sensitive information",
            },
            "team_members": [
                {
                    "user_id": 1,
                    "role": "owner",
                    "hourly_rate": "200.00",  # Sensitive rate info
                }
            ],
            "initial_tasks": [],
            "milestones": [],
            "auto_create_gantt": False,
            "auto_setup_dashboard": False,
            "notify_team": False,
        }

        # Mock services
        security_service.project_service.create_project.return_value = Mock(
            id=1, name="Sensitive Data Project"
        )
        security_service.team_service.add_team_member.return_value = Mock(
            id=1, user_id=1
        )

        # Execute workflow
        result = await security_service.create_complete_project(request, user_id=1)

        # Verify sensitive data is handled appropriately
        assert result.project.id == 1
        assert result.team_setup_result["members_added"] == 1

        # Workflow should complete without exposing sensitive data in logs
        workflow = await security_service.get_workflow_status(result.workflow_id)
        assert workflow is not None
        assert workflow.status.value == "completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--asyncio-mode=auto"])
