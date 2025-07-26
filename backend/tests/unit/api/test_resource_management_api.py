"""
ITDO ERP Backend - Resource Management API Unit Tests
Day 21: Comprehensive unit tests for resource management functionality
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.resource_management_api import ResourceManagementService
from app.schemas.resource import (
    ResourceAllocationCreate,
    ResourceCreate,
    ResourceOptimizationRequest,
    ResourceUpdate,
)


class TestResourceManagementService:
    """Unit tests for ResourceManagementService"""

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
        """Resource management service instance"""
        return ResourceManagementService(mock_db_session, mock_redis_client)

    @pytest.fixture
    def sample_resource_data(self):
        """Sample resource creation data"""
        return ResourceCreate(
            code="RES-001",
            name="Senior Developer",
            type="human",
            status="available",
            capacity=40.0,
            hourly_rate=Decimal("150.00"),
            availability_start=date(2025, 8, 1),
            availability_end=date(2025, 12, 31),
            skills=["Python", "FastAPI", "PostgreSQL"],
            location="Tokyo",
            department_id=1,
            manager_id=2,
        )

    @pytest.fixture
    def sample_allocation_data(self):
        """Sample resource allocation data"""
        return ResourceAllocationCreate(
            resource_id=1,
            project_id=1,
            task_id=1,
            allocation_percentage=75.0,
            start_date=date(2025, 8, 1),
            end_date=date(2025, 8, 31),
            hourly_rate=Decimal("150.00"),
            notes="Primary developer assignment",
        )

    @pytest.mark.asyncio
    async def test_create_resource_success(
        self, resource_service, sample_resource_data
    ):
        """Test successful resource creation"""

        # Mock database operations
        resource_service._check_resource_code_exists = AsyncMock(return_value=False)

        mock_resource = Mock()
        mock_resource.id = 1
        mock_resource.code = "RES-001"
        mock_resource.name = "Senior Developer"
        mock_resource.type = "human"
        mock_resource.status = "available"
        mock_resource.capacity = 40.0
        mock_resource.hourly_rate = Decimal("150.00")
        mock_resource.created_at = datetime.utcnow()

        resource_service.db.add = Mock()
        resource_service.db.commit = AsyncMock()
        resource_service.db.refresh = AsyncMock()

        # Mock Redis operations
        resource_service.redis.incr = AsyncMock(return_value=1)
        resource_service.redis.hset = AsyncMock()
        resource_service.redis.expire = AsyncMock()

        # Mock database query result
        with patch(
            "app.api.v1.resource_management_api.Resource", return_value=mock_resource
        ):
            result = await resource_service.create_resource(
                sample_resource_data, user_id=1
            )

        # Verify result
        assert result is not None
        assert result.code == "RES-001"
        assert result.name == "Senior Developer"
        assert result.type == "human"
        assert result.capacity == 40.0

        # Verify database operations
        resource_service.db.add.assert_called_once()
        resource_service.db.commit.assert_called_once()
        resource_service.db.refresh.assert_called_once()

        # Verify Redis operations
        resource_service.redis.incr.assert_called_once_with("resource_counter")
        resource_service.redis.hset.assert_called()
        resource_service.redis.expire.assert_called()

    @pytest.mark.asyncio
    async def test_create_resource_duplicate_code(
        self, resource_service, sample_resource_data
    ):
        """Test resource creation with duplicate code"""

        # Mock existing resource with same code
        resource_service._check_resource_code_exists = AsyncMock(return_value=True)

        # Should raise HTTPException for duplicate code
        with pytest.raises(Exception) as exc_info:
            await resource_service.create_resource(sample_resource_data, user_id=1)

        assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_resource_success(self, resource_service):
        """Test successful resource retrieval"""

        mock_resource = Mock()
        mock_resource.id = 1
        mock_resource.code = "RES-001"
        mock_resource.name = "Senior Developer"
        mock_resource.is_deleted = False

        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_resource
        resource_service.db.execute = AsyncMock(return_value=mock_result)

        result = await resource_service.get_resource(1)

        assert result is not None
        assert result.id == 1
        assert result.code == "RES-001"
        assert result.name == "Senior Developer"

    @pytest.mark.asyncio
    async def test_get_resource_not_found(self, resource_service):
        """Test resource retrieval when not found"""

        # Mock database query returning None
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        resource_service.db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(Exception) as exc_info:
            await resource_service.get_resource(999)

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_resource_success(self, resource_service):
        """Test successful resource update"""

        update_data = ResourceUpdate(
            name="Senior Full-Stack Developer",
            capacity=35.0,
            hourly_rate=Decimal("160.00"),
            skills=["Python", "FastAPI", "React", "PostgreSQL"],
        )

        mock_resource = Mock()
        mock_resource.id = 1
        mock_resource.code = "RES-001"
        mock_resource.name = "Senior Developer"
        mock_resource.capacity = 40.0
        mock_resource.hourly_rate = Decimal("150.00")
        mock_resource.is_deleted = False

        # Mock database operations
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_resource
        resource_service.db.execute = AsyncMock(return_value=mock_result)
        resource_service.db.commit = AsyncMock()
        resource_service.db.refresh = AsyncMock()

        # Mock Redis operations
        resource_service.redis.hset = AsyncMock()
        resource_service.redis.expire = AsyncMock()

        await resource_service.update_resource(1, update_data, user_id=1)

        # Verify resource was updated
        assert mock_resource.name == "Senior Full-Stack Developer"
        assert mock_resource.capacity == 35.0
        assert mock_resource.hourly_rate == Decimal("160.00")

        # Verify database operations
        resource_service.db.commit.assert_called_once()
        resource_service.db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_resource_success(self, resource_service):
        """Test successful resource deletion (soft delete)"""

        mock_resource = Mock()
        mock_resource.id = 1
        mock_resource.code = "RES-001"
        mock_resource.is_deleted = False

        # Mock database operations
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_resource
        resource_service.db.execute = AsyncMock(return_value=mock_result)
        resource_service.db.commit = AsyncMock()

        # Mock Redis operations
        resource_service.redis.delete = AsyncMock()

        await resource_service.delete_resource(1, user_id=1)

        # Verify soft delete
        assert mock_resource.is_deleted is True
        assert mock_resource.deleted_at is not None
        assert mock_resource.deleted_by == 1

        # Verify database operations
        resource_service.db.commit.assert_called_once()

        # Verify Redis cleanup
        resource_service.redis.delete.assert_called_with("resource:1")

    @pytest.mark.asyncio
    async def test_create_allocation_success(
        self, resource_service, sample_allocation_data
    ):
        """Test successful resource allocation creation"""

        # Mock resource availability check
        resource_service._check_resource_availability = AsyncMock(return_value=True)
        resource_service._check_allocation_conflicts = AsyncMock(return_value=[])

        mock_allocation = Mock()
        mock_allocation.id = 1
        mock_allocation.resource_id = 1
        mock_allocation.project_id = 1
        mock_allocation.allocation_percentage = 75.0
        mock_allocation.status = "active"
        mock_allocation.created_at = datetime.utcnow()

        # Mock database operations
        resource_service.db.add = Mock()
        resource_service.db.commit = AsyncMock()
        resource_service.db.refresh = AsyncMock()

        # Mock Redis operations
        resource_service.redis.incr = AsyncMock(return_value=1)
        resource_service.redis.hset = AsyncMock()
        resource_service.redis.expire = AsyncMock()

        with patch(
            "app.api.v1.resource_management_api.ResourceAllocation",
            return_value=mock_allocation,
        ):
            result = await resource_service.create_allocation(
                sample_allocation_data, user_id=1
            )

        # Verify result
        assert result is not None
        assert result.resource_id == 1
        assert result.project_id == 1
        assert result.allocation_percentage == 75.0

        # Verify checks were performed
        resource_service._check_resource_availability.assert_called_once()
        resource_service._check_allocation_conflicts.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_allocation_overallocation(
        self, resource_service, sample_allocation_data
    ):
        """Test allocation creation with overallocation conflict"""

        # Mock resource availability check
        resource_service._check_resource_availability = AsyncMock(return_value=True)

        # Mock allocation conflict (overallocation)
        conflicts = [
            {
                "allocation_id": 2,
                "conflict_type": "overallocation",
                "message": "Resource allocation would exceed 100%",
            }
        ]
        resource_service._check_allocation_conflicts = AsyncMock(return_value=conflicts)

        with pytest.raises(Exception) as exc_info:
            await resource_service.create_allocation(sample_allocation_data, user_id=1)

        assert "allocation conflicts" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_resource_utilization(self, resource_service):
        """Test resource utilization calculation"""

        # Mock database query for allocations
        mock_allocations = [
            Mock(
                id=1,
                allocation_percentage=75.0,
                start_date=date(2025, 8, 1),
                end_date=date(2025, 8, 31),
                status="active",
            ),
            Mock(
                id=2,
                allocation_percentage=25.0,
                start_date=date(2025, 9, 1),
                end_date=date(2025, 9, 30),
                status="active",
            ),
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_allocations
        resource_service.db.execute = AsyncMock(return_value=mock_result)

        # Mock Redis cache
        resource_service.redis.get = AsyncMock(return_value=None)
        resource_service.redis.setex = AsyncMock()

        result = await resource_service.get_resource_utilization(
            resource_id=1, start_date=date(2025, 8, 1), end_date=date(2025, 9, 30)
        )

        # Verify utilization calculation
        assert result is not None
        assert result.resource_id == 1
        assert result.total_allocations == 2
        assert result.average_utilization_percentage > 0

        # Verify Redis caching
        resource_service.redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_optimize_resource_allocation(self, resource_service):
        """Test resource allocation optimization"""

        optimization_request = ResourceOptimizationRequest(
            resource_ids=[1, 2, 3],
            project_ids=[1, 2],
            start_date=date(2025, 8, 1),
            end_date=date(2025, 12, 31),
            optimization_goal="efficiency",
            constraints={
                "max_allocation_percentage": 90.0,
                "min_allocation_percentage": 10.0,
                "skill_matching_required": True,
            },
        )

        # Mock resource data
        mock_resources = [
            Mock(id=1, type="human", capacity=40.0, skills=["Python", "FastAPI"]),
            Mock(id=2, type="human", capacity=35.0, skills=["React", "TypeScript"]),
            Mock(id=3, type="equipment", capacity=24.0, skills=[]),
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_resources
        resource_service.db.execute = AsyncMock(return_value=mock_result)

        # Mock optimization algorithm
        resource_service._run_optimization_algorithm = AsyncMock(
            return_value={
                "optimized_allocations": [
                    {"resource_id": 1, "project_id": 1, "allocation_percentage": 80.0},
                    {"resource_id": 2, "project_id": 2, "allocation_percentage": 75.0},
                    {"resource_id": 3, "project_id": 1, "allocation_percentage": 50.0},
                ],
                "efficiency_score": 92.5,
                "cost_savings": 15.3,
                "time_savings_days": 8,
            }
        )

        result = await resource_service.optimize_resource_allocation(
            optimization_request
        )

        # Verify optimization result
        assert result is not None
        assert len(result.optimized_allocations) == 3
        assert result.efficiency_score == 92.5
        assert result.cost_savings == 15.3
        assert result.time_savings_days == 8

        # Verify optimization algorithm was called
        resource_service._run_optimization_algorithm.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_resource_statistics(self, resource_service):
        """Test resource statistics calculation"""

        # Mock database aggregation queries
        resource_service.db.execute = AsyncMock()

        # Mock total resources count
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 15

        # Mock available resources count
        mock_available_result = Mock()
        mock_available_result.scalar.return_value = 12

        # Mock average utilization
        mock_utilization_result = Mock()
        mock_utilization_result.scalar.return_value = 78.5

        # Mock top utilized resources
        mock_top_resources = [
            Mock(id=1, name="Senior Developer", utilization=95.0),
            Mock(id=2, name="DevOps Engineer", utilization=90.0),
            Mock(id=3, name="UI/UX Designer", utilization=85.0),
        ]
        mock_top_result = Mock()
        mock_top_result.fetchall.return_value = mock_top_resources

        resource_service.db.execute.side_effect = [
            mock_count_result,
            mock_available_result,
            mock_utilization_result,
            mock_top_result,
        ]

        # Mock Redis cache
        resource_service.redis.get = AsyncMock(return_value=None)
        resource_service.redis.setex = AsyncMock()

        result = await resource_service.get_resource_statistics()

        # Verify statistics
        assert result is not None
        assert result.total_resources == 15
        assert result.available_resources == 12
        assert result.average_utilization == 78.5
        assert len(result.top_utilized_resources) == 3

        # Verify database queries
        assert resource_service.db.execute.call_count == 4

        # Verify Redis caching
        resource_service.redis.setex.assert_called_once()


class TestResourceManagementHelpers:
    """Unit tests for resource management helper functions"""

    @pytest.fixture
    def resource_service(self):
        """Resource service for helper testing"""
        db = AsyncMock(spec=AsyncSession)
        redis = AsyncMock()
        return ResourceManagementService(db, redis)

    @pytest.mark.asyncio
    async def test_check_resource_code_exists(self, resource_service):
        """Test resource code existence check"""

        # Mock existing resource
        mock_resource = Mock(id=1, code="RES-001")
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_resource
        resource_service.db.execute = AsyncMock(return_value=mock_result)

        result = await resource_service._check_resource_code_exists("RES-001")
        assert result is True

        # Mock non-existing resource
        mock_result.scalar_one_or_none.return_value = None
        result = await resource_service._check_resource_code_exists("RES-999")
        assert result is False

    @pytest.mark.asyncio
    async def test_check_resource_availability(self, resource_service):
        """Test resource availability check"""

        # Mock available resource
        mock_resource = Mock(
            id=1,
            status="available",
            availability_start=date(2025, 8, 1),
            availability_end=date(2025, 12, 31),
        )
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_resource
        resource_service.db.execute = AsyncMock(return_value=mock_result)

        result = await resource_service._check_resource_availability(
            resource_id=1, start_date=date(2025, 8, 15), end_date=date(2025, 9, 15)
        )
        assert result is True

        # Mock unavailable resource (outside availability window)
        result = await resource_service._check_resource_availability(
            resource_id=1, start_date=date(2024, 8, 15), end_date=date(2024, 9, 15)
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_check_allocation_conflicts(self, resource_service):
        """Test allocation conflict detection"""

        # Mock existing allocations
        mock_allocations = [
            Mock(
                id=1,
                allocation_percentage=60.0,
                start_date=date(2025, 8, 1),
                end_date=date(2025, 8, 31),
                status="active",
            ),
            Mock(
                id=2,
                allocation_percentage=30.0,
                start_date=date(2025, 8, 15),
                end_date=date(2025, 9, 15),
                status="active",
            ),
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_allocations
        resource_service.db.execute = AsyncMock(return_value=mock_result)

        # Test overallocation conflict
        conflicts = await resource_service._check_allocation_conflicts(
            resource_id=1,
            start_date=date(2025, 8, 15),
            end_date=date(2025, 8, 31),
            allocation_percentage=50.0,  # Would cause 140% allocation (60+30+50)
        )

        assert len(conflicts) > 0
        assert conflicts[0]["conflict_type"] == "overallocation"

        # Test no conflict
        conflicts = await resource_service._check_allocation_conflicts(
            resource_id=1,
            start_date=date(2025, 10, 1),
            end_date=date(2025, 10, 31),
            allocation_percentage=50.0,  # No overlapping allocations
        )

        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_calculate_utilization_metrics(self, resource_service):
        """Test utilization metrics calculation"""

        # Mock allocation data
        allocations = [
            Mock(
                allocation_percentage=75.0,
                start_date=date(2025, 8, 1),
                end_date=date(2025, 8, 31),
                hourly_rate=Decimal("150.00"),
            ),
            Mock(
                allocation_percentage=50.0,
                start_date=date(2025, 9, 1),
                end_date=date(2025, 9, 30),
                hourly_rate=Decimal("150.00"),
            ),
        ]

        metrics = resource_service._calculate_utilization_metrics(
            allocations=allocations,
            resource_capacity=40.0,
            start_date=date(2025, 8, 1),
            end_date=date(2025, 9, 30),
        )

        # Verify metrics calculation
        assert metrics["total_allocations"] == 2
        assert metrics["average_utilization_percentage"] == 62.5  # (75+50)/2
        assert metrics["peak_utilization_percentage"] == 75.0
        assert metrics["total_allocated_hours"] > 0
        assert metrics["efficiency_score"] > 0

    @pytest.mark.asyncio
    async def test_run_optimization_algorithm(self, resource_service):
        """Test resource optimization algorithm"""

        # Mock optimization data
        resources = [
            Mock(id=1, capacity=40.0, hourly_rate=Decimal("150.00"), skills=["Python"]),
            Mock(id=2, capacity=35.0, hourly_rate=Decimal("120.00"), skills=["React"]),
        ]

        projects = [
            Mock(id=1, required_skills=["Python"], estimated_hours=160),
            Mock(id=2, required_skills=["React"], estimated_hours=140),
        ]

        constraints = {
            "max_allocation_percentage": 90.0,
            "skill_matching_required": True,
        }

        result = await resource_service._run_optimization_algorithm(
            resources=resources,
            projects=projects,
            optimization_goal="efficiency",
            constraints=constraints,
        )

        # Verify optimization result structure
        assert "optimized_allocations" in result
        assert "efficiency_score" in result
        assert "cost_savings" in result
        assert "time_savings_days" in result

        # Verify allocations respect constraints
        for allocation in result["optimized_allocations"]:
            assert allocation["allocation_percentage"] <= 90.0
            assert allocation["resource_id"] in [1, 2]
            assert allocation["project_id"] in [1, 2]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--asyncio-mode=auto"])
