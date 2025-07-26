"""
ITDO ERP Backend - Resource Management Integration Tests
Day 21: Integration tests for resource management with project and task systems
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.project_management_api import ProjectManagementService
from app.api.v1.resource_management_api import ResourceManagementService
from app.api.v1.task_management_api import TaskManagementService


class TestResourceProjectIntegration:
    """Integration tests between resource management and project systems"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client"""
        return AsyncMock()

    @pytest.fixture
    def resource_service(self, mock_db_session, mock_redis_client):
        """Resource management service"""
        return ResourceManagementService(mock_db_session, mock_redis_client)

    @pytest.fixture
    def project_service(self, mock_db_session, mock_redis_client):
        """Project management service"""
        return ProjectManagementService(mock_db_session, mock_redis_client)

    @pytest.fixture
    def task_service(self, mock_db_session, mock_redis_client):
        """Task management service"""
        return TaskManagementService(mock_db_session, mock_redis_client)

    @pytest.fixture
    def sample_project_data(self):
        """Sample project with resource requirements"""
        return {
            "id": 1,
            "code": "PROJ-RES-001",
            "name": "Resource Integration Test Project",
            "estimated_hours": 320.0,
            "budget": Decimal("800000.00"),
            "start_date": date(2025, 8, 1),
            "end_date": date(2025, 12, 31),
            "required_skills": ["Python", "FastAPI", "React", "PostgreSQL"],
            "team_size": 4,
        }

    @pytest.fixture
    def sample_resources(self):
        """Sample resources for allocation"""
        return [
            {
                "id": 1,
                "code": "DEV-001",
                "name": "Senior Python Developer",
                "type": "human",
                "capacity": 40.0,
                "hourly_rate": Decimal("150.00"),
                "skills": ["Python", "FastAPI", "PostgreSQL"],
                "status": "available",
            },
            {
                "id": 2,
                "code": "DEV-002",
                "name": "Frontend Developer",
                "type": "human",
                "capacity": 35.0,
                "hourly_rate": Decimal("120.00"),
                "skills": ["React", "TypeScript", "CSS"],
                "status": "available",
            },
            {
                "id": 3,
                "code": "DEV-003",
                "name": "Full-Stack Developer",
                "type": "human",
                "capacity": 38.0,
                "hourly_rate": Decimal("130.00"),
                "skills": ["Python", "React", "PostgreSQL"],
                "status": "available",
            },
            {
                "id": 4,
                "code": "EQ-001",
                "name": "Development Server",
                "type": "equipment",
                "capacity": 24.0,
                "hourly_rate": Decimal("25.00"),
                "skills": [],
                "status": "available",
            },
        ]

    @pytest.mark.asyncio
    async def test_project_resource_allocation_workflow(
        self, resource_service, project_service, sample_project_data, sample_resources
    ):
        """Test complete workflow of allocating resources to a project"""

        # Step 1: Mock project exists
        mock_project = Mock(**sample_project_data)
        project_service.get_project = AsyncMock(return_value=mock_project)

        # Step 2: Mock available resources
        mock_resources = [Mock(**res) for res in sample_resources]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_resources
        resource_service.db.execute = AsyncMock(return_value=mock_result)

        # Step 3: Mock allocation creation
        resource_service._check_resource_availability = AsyncMock(return_value=True)
        resource_service._check_allocation_conflicts = AsyncMock(return_value=[])
        resource_service.db.add = Mock()
        resource_service.db.commit = AsyncMock()
        resource_service.db.refresh = AsyncMock()
        resource_service.redis.incr = AsyncMock(return_value=1)
        resource_service.redis.hset = AsyncMock()
        resource_service.redis.expire = AsyncMock()

        # Step 4: Create allocations for each resource
        allocations = []
        allocation_percentages = [80.0, 75.0, 70.0, 50.0]  # Different allocation levels

        for i, (resource, percentage) in enumerate(
            zip(sample_resources, allocation_percentages)
        ):
            allocation_data = {
                "resource_id": resource["id"],
                "project_id": sample_project_data["id"],
                "allocation_percentage": percentage,
                "start_date": sample_project_data["start_date"],
                "end_date": sample_project_data["end_date"],
                "hourly_rate": resource["hourly_rate"],
            }

            mock_allocation = Mock()
            mock_allocation.id = i + 1
            mock_allocation.resource_id = resource["id"]
            mock_allocation.project_id = sample_project_data["id"]
            mock_allocation.allocation_percentage = percentage
            mock_allocation.status = "active"

            with patch(
                "app.api.v1.resource_management_api.ResourceAllocation",
                return_value=mock_allocation,
            ):
                allocation = await resource_service.create_allocation(
                    allocation_data, user_id=1
                )
                allocations.append(allocation)

        # Step 5: Verify all allocations were created
        assert len(allocations) == 4

        for i, allocation in enumerate(allocations):
            assert allocation.resource_id == sample_resources[i]["id"]
            assert allocation.project_id == sample_project_data["id"]
            assert allocation.allocation_percentage == allocation_percentages[i]

        # Step 6: Verify database operations
        assert resource_service.db.add.call_count == 4
        assert resource_service.db.commit.call_count == 4

        # Step 7: Verify Redis operations for caching
        assert resource_service.redis.hset.call_count == 4

    @pytest.mark.asyncio
    async def test_resource_capacity_planning_for_project(
        self, resource_service, sample_project_data, sample_resources
    ):
        """Test resource capacity planning for project requirements"""

        # Mock project resource requirements analysis
        project_requirements = {
            "total_hours": 320.0,
            "duration_weeks": 20,
            "required_skills": ["Python", "FastAPI", "React", "PostgreSQL"],
            "preferred_team_size": 4,
            "max_budget": Decimal("800000.00"),
        }

        # Mock available resources
        mock_resources = [Mock(**res) for res in sample_resources]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_resources
        resource_service.db.execute = AsyncMock(return_value=mock_result)

        # Mock capacity planning calculation
        resource_service._calculate_capacity_requirements = AsyncMock(
            return_value={
                "recommended_allocations": [
                    {
                        "resource_id": 1,
                        "allocation_percentage": 80.0,
                        "weekly_hours": 32.0,
                    },
                    {
                        "resource_id": 2,
                        "allocation_percentage": 75.0,
                        "weekly_hours": 26.25,
                    },
                    {
                        "resource_id": 3,
                        "allocation_percentage": 70.0,
                        "weekly_hours": 26.6,
                    },
                    {
                        "resource_id": 4,
                        "allocation_percentage": 50.0,
                        "weekly_hours": 12.0,
                    },
                ],
                "total_capacity_hours": 1940.0,  # 20 weeks * sum of weekly hours
                "capacity_utilization": 82.5,
                "budget_estimate": Decimal("755000.00"),
                "skill_coverage": {
                    "Python": ["DEV-001", "DEV-003"],
                    "FastAPI": ["DEV-001"],
                    "React": ["DEV-002", "DEV-003"],
                    "PostgreSQL": ["DEV-001", "DEV-003"],
                },
            }
        )

        # Execute capacity planning
        capacity_plan = await resource_service.plan_project_capacity(
            project_id=sample_project_data["id"], requirements=project_requirements
        )

        # Verify capacity planning results
        assert capacity_plan is not None
        assert len(capacity_plan["recommended_allocations"]) == 4
        assert (
            capacity_plan["total_capacity_hours"] >= project_requirements["total_hours"]
        )
        assert capacity_plan["budget_estimate"] <= project_requirements["max_budget"]

        # Verify skill coverage
        skill_coverage = capacity_plan["skill_coverage"]
        for required_skill in project_requirements["required_skills"]:
            assert required_skill in skill_coverage
            assert len(skill_coverage[required_skill]) > 0

    @pytest.mark.asyncio
    async def test_resource_reallocation_between_projects(
        self, resource_service, project_service
    ):
        """Test resource reallocation between multiple projects"""

        # Mock two projects
        Mock(id=1, name="Project Alpha", priority="high", end_date=date(2025, 10, 31))
        Mock(id=2, name="Project Beta", priority="medium", end_date=date(2025, 12, 31))

        # Mock existing allocations for Project 1
        existing_allocations = [
            Mock(
                id=1,
                resource_id=1,
                project_id=1,
                allocation_percentage=80.0,
                start_date=date(2025, 8, 1),
                end_date=date(2025, 10, 31),
                status="active",
            ),
            Mock(
                id=2,
                resource_id=2,
                project_id=1,
                allocation_percentage=75.0,
                start_date=date(2025, 8, 1),
                end_date=date(2025, 10, 31),
                status="active",
            ),
        ]

        # Mock database queries
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = existing_allocations
        resource_service.db.execute = AsyncMock(return_value=mock_result)
        resource_service.db.commit = AsyncMock()

        # Mock Redis operations
        resource_service.redis.hset = AsyncMock()
        resource_service.redis.expire = AsyncMock()

        # Execute reallocation (Project 1 ends, resources move to Project 2)
        reallocation_plan = {
            "source_project_id": 1,
            "target_project_id": 2,
            "transition_date": date(2025, 11, 1),
            "resource_allocations": [
                {"resource_id": 1, "new_allocation_percentage": 70.0},
                {"resource_id": 2, "new_allocation_percentage": 80.0},
            ],
        }

        # Mock reallocation execution
        resource_service._execute_reallocation = AsyncMock(
            return_value={
                "reallocated_resources": 2,
                "updated_allocations": [
                    {
                        "resource_id": 1,
                        "old_project": 1,
                        "new_project": 2,
                        "allocation": 70.0,
                    },
                    {
                        "resource_id": 2,
                        "old_project": 1,
                        "new_project": 2,
                        "allocation": 80.0,
                    },
                ],
                "transition_date": date(2025, 11, 1),
                "efficiency_gain": 12.5,
            }
        )

        result = await resource_service.reallocate_resources(
            reallocation_plan, user_id=1
        )

        # Verify reallocation results
        assert result["reallocated_resources"] == 2
        assert len(result["updated_allocations"]) == 2

        for allocation in result["updated_allocations"]:
            assert allocation["old_project"] == 1
            assert allocation["new_project"] == 2
            assert allocation["allocation"] in [70.0, 80.0]

        # Verify database operations
        resource_service.db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_resource_utilization_across_projects(
        self, resource_service, sample_resources
    ):
        """Test resource utilization calculation across multiple projects"""

        # Mock allocations across multiple projects
        cross_project_allocations = [
            Mock(
                id=1,
                resource_id=1,
                project_id=1,
                allocation_percentage=60.0,
                start_date=date(2025, 8, 1),
                end_date=date(2025, 9, 30),
                status="active",
            ),
            Mock(
                id=2,
                resource_id=1,
                project_id=2,
                allocation_percentage=30.0,
                start_date=date(2025, 8, 15),
                end_date=date(2025, 10, 15),
                status="active",
            ),
            Mock(
                id=3,
                resource_id=2,
                project_id=1,
                allocation_percentage=75.0,
                start_date=date(2025, 8, 1),
                end_date=date(2025, 11, 30),
                status="active",
            ),
            Mock(
                id=4,
                resource_id=2,
                project_id=3,
                allocation_percentage=20.0,
                start_date=date(2025, 10, 1),
                end_date=date(2025, 12, 31),
                status="active",
            ),
        ]

        # Mock database query
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = cross_project_allocations
        resource_service.db.execute = AsyncMock(return_value=mock_result)

        # Mock Redis cache
        resource_service.redis.get = AsyncMock(return_value=None)
        resource_service.redis.setex = AsyncMock()

        # Execute utilization analysis
        utilization_report = await resource_service.get_cross_project_utilization(
            start_date=date(2025, 8, 1), end_date=date(2025, 12, 31)
        )

        # Verify utilization calculations
        assert utilization_report is not None
        assert "resource_utilization" in utilization_report
        assert "project_breakdown" in utilization_report
        assert "overallocation_warnings" in utilization_report

        # Verify resource 1 utilization (should show 90% peak during overlap period)
        resource_1_util = next(
            (
                r
                for r in utilization_report["resource_utilization"]
                if r["resource_id"] == 1
            ),
            None,
        )
        assert resource_1_util is not None
        assert resource_1_util["peak_utilization"] == 90.0  # 60% + 30%

        # Verify overallocation warning for resource 2 (95% during October overlap)
        warnings = utilization_report["overallocation_warnings"]
        resource_2_warning = next((w for w in warnings if w["resource_id"] == 2), None)
        assert resource_2_warning is not None
        assert resource_2_warning["peak_utilization"] == 95.0  # 75% + 20%

    @pytest.mark.asyncio
    async def test_resource_skill_matching_optimization(
        self, resource_service, sample_resources
    ):
        """Test skill-based resource optimization for projects"""

        # Mock project requirements with specific skills
        project_requirements = [
            {
                "project_id": 1,
                "required_skills": ["Python", "FastAPI", "PostgreSQL"],
                "skill_weights": {"Python": 0.4, "FastAPI": 0.3, "PostgreSQL": 0.3},
                "hours_needed": 160,
            },
            {
                "project_id": 2,
                "required_skills": ["React", "TypeScript", "CSS"],
                "skill_weights": {"React": 0.5, "TypeScript": 0.3, "CSS": 0.2},
                "hours_needed": 120,
            },
            {
                "project_id": 3,
                "required_skills": ["Python", "React"],
                "skill_weights": {"Python": 0.6, "React": 0.4},
                "hours_needed": 80,
            },
        ]

        # Mock available resources with skills
        mock_resources = [Mock(**res) for res in sample_resources]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_resources
        resource_service.db.execute = AsyncMock(return_value=mock_result)

        # Mock skill matching optimization
        resource_service._optimize_skill_matching = AsyncMock(
            return_value={
                "optimal_assignments": [
                    {
                        "resource_id": 1,  # Senior Python Developer
                        "project_id": 1,
                        "skill_match_score": 95.0,
                        "allocation_percentage": 80.0,
                        "matched_skills": ["Python", "FastAPI", "PostgreSQL"],
                    },
                    {
                        "resource_id": 2,  # Frontend Developer
                        "project_id": 2,
                        "skill_match_score": 90.0,
                        "allocation_percentage": 75.0,
                        "matched_skills": ["React", "TypeScript", "CSS"],
                    },
                    {
                        "resource_id": 3,  # Full-Stack Developer
                        "project_id": 3,
                        "skill_match_score": 85.0,
                        "allocation_percentage": 70.0,
                        "matched_skills": ["Python", "React"],
                    },
                ],
                "overall_skill_coverage": 92.3,
                "unmatched_requirements": [],
                "optimization_score": 88.5,
            }
        )

        # Execute skill matching optimization
        optimization_result = await resource_service.optimize_skill_matching(
            project_requirements=project_requirements, optimization_goal="skill_match"
        )

        # Verify optimization results
        assert optimization_result is not None
        assert len(optimization_result["optimal_assignments"]) == 3
        assert optimization_result["overall_skill_coverage"] > 90.0
        assert len(optimization_result["unmatched_requirements"]) == 0

        # Verify each assignment has high skill match
        for assignment in optimization_result["optimal_assignments"]:
            assert assignment["skill_match_score"] >= 85.0
            assert len(assignment["matched_skills"]) >= 2

    @pytest.mark.asyncio
    async def test_resource_cost_optimization(self, resource_service, sample_resources):
        """Test cost-based resource optimization"""

        # Mock project budget constraints
        budget_constraints = {
            "total_budget": Decimal("500000.00"),
            "max_hourly_rate": Decimal("140.00"),
            "project_duration_weeks": 16,
            "required_hours": 2048,  # 16 weeks * 32 hours/week * 4 resources
        }

        # Mock resources with different rates
        mock_resources = [Mock(**res) for res in sample_resources]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_resources
        resource_service.db.execute = AsyncMock(return_value=mock_result)

        # Mock cost optimization algorithm
        resource_service._optimize_resource_costs = AsyncMock(
            return_value={
                "optimized_allocation": [
                    {
                        "resource_id": 2,  # Frontend Developer - $120/hr
                        "allocation_percentage": 85.0,
                        "weekly_hours": 29.75,  # 85% of 35 hours
                        "total_cost": Decimal("76160.00"),  # 16 weeks * 29.75 * $120
                    },
                    {
                        "resource_id": 3,  # Full-Stack Developer - $130/hr
                        "allocation_percentage": 80.0,
                        "weekly_hours": 30.4,  # 80% of 38 hours
                        "total_cost": Decimal("63232.00"),  # 16 weeks * 30.4 * $130
                    },
                    {
                        "resource_id": 1,  # Senior Python Developer - $150/hr (limited allocation)
                        "allocation_percentage": 60.0,
                        "weekly_hours": 24.0,  # 60% of 40 hours
                        "total_cost": Decimal("57600.00"),  # 16 weeks * 24 * $150
                    },
                ],
                "total_cost": Decimal("196992.00"),
                "budget_savings": Decimal("303008.00"),  # Under budget
                "cost_efficiency_score": 94.2,
                "skill_coverage_maintained": True,
            }
        )

        # Execute cost optimization
        cost_optimization = await resource_service.optimize_resource_costs(
            budget_constraints=budget_constraints, optimization_goal="cost_efficiency"
        )

        # Verify cost optimization results
        assert cost_optimization is not None
        assert cost_optimization["total_cost"] <= budget_constraints["total_budget"]
        assert cost_optimization["budget_savings"] > 0
        assert cost_optimization["cost_efficiency_score"] > 90.0
        assert cost_optimization["skill_coverage_maintained"] is True

        # Verify resource allocation respects hourly rate constraints
        for allocation in cost_optimization["optimized_allocation"]:
            resource = next(
                r for r in sample_resources if r["id"] == allocation["resource_id"]
            )
            assert resource["hourly_rate"] <= budget_constraints["max_hourly_rate"]


class TestResourceTaskIntegration:
    """Integration tests between resource management and task systems"""

    @pytest.fixture
    def mock_services(self):
        """Mock services for testing"""
        db = AsyncMock(spec=AsyncSession)
        redis = AsyncMock()

        resource_service = ResourceManagementService(db, redis)
        task_service = TaskManagementService(db, redis)

        return resource_service, task_service

    @pytest.mark.asyncio
    async def test_task_resource_assignment_workflow(self, mock_services):
        """Test assigning resources to specific tasks"""

        resource_service, task_service = mock_services

        # Mock task with resource requirements
        mock_task = Mock(
            id=1,
            title="Implement User Authentication",
            project_id=1,
            estimated_hours=40.0,
            required_skills=["Python", "FastAPI", "OAuth"],
            priority="high",
            due_date=date(2025, 8, 31),
        )

        task_service.get_task = AsyncMock(return_value=mock_task)

        # Mock suitable resource
        mock_resource = Mock(
            id=1,
            name="Senior Backend Developer",
            skills=["Python", "FastAPI", "OAuth", "PostgreSQL"],
            hourly_rate=Decimal("150.00"),
            capacity=40.0,
            status="available",
        )

        # Mock resource availability and assignment
        resource_service._find_suitable_resources = AsyncMock(
            return_value=[mock_resource]
        )
        resource_service._check_resource_availability = AsyncMock(return_value=True)
        resource_service._check_allocation_conflicts = AsyncMock(return_value=[])

        # Mock allocation creation
        resource_service.db.add = Mock()
        resource_service.db.commit = AsyncMock()
        resource_service.redis.incr = AsyncMock(return_value=1)
        resource_service.redis.hset = AsyncMock()

        # Execute task-resource assignment
        assignment_data = {
            "task_id": 1,
            "resource_requirements": {
                "required_skills": ["Python", "FastAPI", "OAuth"],
                "estimated_hours": 40.0,
                "max_hourly_rate": Decimal("160.00"),
                "preferred_start_date": date(2025, 8, 1),
            },
        }

        mock_assignment = Mock(
            id=1,
            resource_id=1,
            task_id=1,
            allocation_percentage=100.0,
            estimated_hours=40.0,
            status="assigned",
        )

        with patch(
            "app.api.v1.resource_management_api.ResourceAllocation",
            return_value=mock_assignment,
        ):
            assignment = await resource_service.assign_resource_to_task(
                assignment_data, user_id=1
            )

        # Verify assignment
        assert assignment.resource_id == 1
        assert assignment.task_id == 1
        assert assignment.allocation_percentage == 100.0

        # Verify services were called appropriately
        task_service.get_task.assert_called_once_with(1)
        resource_service._find_suitable_resources.assert_called_once()

    @pytest.mark.asyncio
    async def test_task_progress_resource_utilization_tracking(self, mock_services):
        """Test tracking resource utilization as tasks progress"""

        resource_service, task_service = mock_services

        # Mock task with resource allocation
        mock_task = Mock(
            id=1,
            completion_percentage=60.0,
            actual_hours=24.0,  # 60% of 40 estimated hours
            estimated_hours=40.0,
            status="in_progress",
        )

        # Mock resource allocation
        mock_allocation = Mock(
            id=1,
            resource_id=1,
            task_id=1,
            estimated_hours=40.0,
            actual_hours=24.0,
            allocation_percentage=100.0,
            status="active",
        )

        # Mock database queries
        mock_task_result = Mock()
        mock_task_result.scalar_one_or_none.return_value = mock_task

        mock_allocation_result = Mock()
        mock_allocation_result.scalars.return_value.all.return_value = [mock_allocation]

        resource_service.db.execute = AsyncMock(
            side_effect=[mock_task_result, mock_allocation_result]
        )

        # Mock Redis cache
        resource_service.redis.get = AsyncMock(return_value=None)
        resource_service.redis.setex = AsyncMock()

        # Execute utilization tracking
        utilization_data = await resource_service.track_task_resource_utilization(
            task_id=1, reporting_date=date(2025, 8, 15)
        )

        # Verify utilization tracking
        assert utilization_data is not None
        assert utilization_data["task_id"] == 1
        assert utilization_data["completion_percentage"] == 60.0
        assert (
            utilization_data["resource_efficiency"] == 100.0
        )  # On track (60% complete, 60% time used)
        assert len(utilization_data["resource_allocations"]) == 1

        resource_alloc = utilization_data["resource_allocations"][0]
        assert resource_alloc["resource_id"] == 1
        assert resource_alloc["hours_used"] == 24.0
        assert resource_alloc["efficiency_rating"] == "on_track"

    @pytest.mark.asyncio
    async def test_resource_workload_balancing_across_tasks(self, mock_services):
        """Test balancing resource workload across multiple tasks"""

        resource_service, task_service = mock_services

        # Mock multiple tasks for same resource
        mock_tasks = [
            Mock(
                id=1,
                title="Task A",
                estimated_hours=40.0,
                priority="high",
                due_date=date(2025, 8, 31),
            ),
            Mock(
                id=2,
                title="Task B",
                estimated_hours=30.0,
                priority="medium",
                due_date=date(2025, 9, 15),
            ),
            Mock(
                id=3,
                title="Task C",
                estimated_hours=25.0,
                priority="low",
                due_date=date(2025, 9, 30),
            ),
        ]

        # Mock current allocations for resource
        current_allocations = [
            Mock(
                id=1,
                resource_id=1,
                task_id=1,
                allocation_percentage=60.0,
                estimated_hours=40.0,
                status="active",
            ),
            Mock(
                id=2,
                resource_id=1,
                task_id=2,
                allocation_percentage=30.0,
                estimated_hours=30.0,
                status="active",
            ),
        ]  # Total: 90% allocated

        # Mock database queries
        mock_task_result = Mock()
        mock_task_result.scalars.return_value.all.return_value = mock_tasks

        mock_allocation_result = Mock()
        mock_allocation_result.scalars.return_value.all.return_value = (
            current_allocations
        )

        resource_service.db.execute = AsyncMock(
            side_effect=[mock_task_result, mock_allocation_result]
        )

        # Mock workload balancing calculation
        resource_service._calculate_optimal_workload_distribution = AsyncMock(
            return_value={
                "resource_id": 1,
                "current_utilization": 90.0,
                "recommended_adjustments": [
                    {
                        "task_id": 1,
                        "current_allocation": 60.0,
                        "recommended_allocation": 50.0,
                        "adjustment_reason": "reduce_overallocation",
                    },
                    {
                        "task_id": 2,
                        "current_allocation": 30.0,
                        "recommended_allocation": 35.0,
                        "adjustment_reason": "priority_adjustment",
                    },
                    {
                        "task_id": 3,
                        "current_allocation": 0.0,
                        "recommended_allocation": 15.0,
                        "adjustment_reason": "new_assignment",
                    },
                ],
                "target_utilization": 100.0,
                "workload_balance_score": 85.0,
                "efficiency_improvement": 12.5,
            }
        )

        # Execute workload balancing
        balancing_result = await resource_service.balance_resource_workload(
            resource_id=1,
            time_period={"start_date": date(2025, 8, 1), "end_date": date(2025, 9, 30)},
        )

        # Verify workload balancing
        assert balancing_result is not None
        assert balancing_result["resource_id"] == 1
        assert balancing_result["current_utilization"] == 90.0
        assert len(balancing_result["recommended_adjustments"]) == 3
        assert balancing_result["target_utilization"] == 100.0
        assert balancing_result["efficiency_improvement"] > 0

        # Verify recommendations address overallocation
        task_1_adjustment = next(
            adj
            for adj in balancing_result["recommended_adjustments"]
            if adj["task_id"] == 1
        )
        assert (
            task_1_adjustment["recommended_allocation"]
            < task_1_adjustment["current_allocation"]
        )
        assert task_1_adjustment["adjustment_reason"] == "reduce_overallocation"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--asyncio-mode=auto"])
