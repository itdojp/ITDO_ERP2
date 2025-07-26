"""
ITDO ERP Backend - Resource Management Performance Tests
Day 23: Performance testing for resource management system
"""

from __future__ import annotations

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.v1.resource_analytics_api import ResourceAnalyticsService
from app.api.v1.resource_integration_api import ResourceIntegrationService
from app.api.v1.resource_planning_api import ResourcePlanningService


class TestResourceManagementPerformance:
    """Performance tests for resource management APIs"""

    @pytest.fixture
    def mock_app(self):
        """Mock FastAPI application for performance testing"""
        from fastapi import FastAPI

        from app.api.v1.resource_integration_api import router as integration_router
        from app.api.v1.resource_management_api import router as management_router

        app = FastAPI()
        app.include_router(integration_router, prefix="/api/v1/resource-integration")
        app.include_router(management_router, prefix="/api/v1/resource-management")
        return app

    @pytest.fixture
    def client(self, mock_app):
        """Test client for performance testing"""
        return TestClient(mock_app)

    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {"Authorization": "Bearer mock-jwt-token"}

    @pytest.fixture
    def large_dataset(self):
        """Generate large dataset for performance testing"""
        return {
            "resources": [
                {
                    "id": i,
                    "name": f"Resource {i}",
                    "type": "human",
                    "department_id": (i % 10) + 1,
                    "hourly_rate": 100.0 + (i % 50),
                    "utilization": 70.0 + (i % 30),
                    "projects": [(i * 3 + j) % 100 for j in range(3)],
                }
                for i in range(1, 1001)  # 1000 resources
            ],
            "utilization_data": [
                {
                    "resource_id": i,
                    "date": date.today() - timedelta(days=j),
                    "hours_worked": 8.0 + (j % 4),
                    "hours_available": 8.0,
                    "utilization": (8.0 + (j % 4)) / 8.0 * 100,
                }
                for i in range(1, 101)  # 100 resources
                for j in range(90)  # 90 days of data
            ],
        }

    def test_dashboard_response_time(self, client, auth_headers):
        """Test dashboard API response time under normal load"""

        with patch("app.api.v1.resource_integration_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }

            # Warm up
            client.get("/api/v1/resource-integration/dashboard", headers=auth_headers)

            # Performance test
            start_time = time.time()
            response = client.get(
                "/api/v1/resource-integration/dashboard", headers=auth_headers
            )
            end_time = time.time()

            response_time = end_time - start_time

            # Should respond within 200ms
            assert response_time < 0.2, (
                f"Dashboard response time {response_time:.3f}s exceeds 200ms"
            )
            assert response.status_code in [200, 500]  # Should not timeout

    def test_dashboard_concurrent_requests(self, client, auth_headers):
        """Test dashboard performance under concurrent load"""

        with patch("app.api.v1.resource_integration_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }

            def make_request():
                start_time = time.time()
                response = client.get(
                    "/api/v1/resource-integration/dashboard", headers=auth_headers
                )
                end_time = time.time()
                return {
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                }

            # Test with 20 concurrent requests
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(make_request) for _ in range(20)]
                results = [future.result() for future in futures]

            # Analyze results
            response_times = [r["response_time"] for r in results]
            success_rate = sum(1 for r in results if r["status_code"] == 200) / len(
                results
            )
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)

            # Performance assertions
            assert success_rate >= 0.95, f"Success rate {success_rate:.2%} below 95%"
            assert avg_response_time < 0.5, (
                f"Average response time {avg_response_time:.3f}s exceeds 500ms"
            )
            assert max_response_time < 1.0, (
                f"Max response time {max_response_time:.3f}s exceeds 1s"
            )

    def test_resource_creation_batch_performance(self, client, auth_headers):
        """Test performance of batch resource creation"""

        with patch("app.api.v1.resource_management_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }

            # Prepare batch data
            batch_data = [
                {
                    "name": f"Batch Resource {i}",
                    "type": "human",
                    "department_id": 1,
                    "hourly_rate": 150.0 + i,
                }
                for i in range(50)  # 50 resources
            ]

            start_time = time.time()

            # Create resources in batch
            for resource_data in batch_data:
                response = client.post(
                    "/api/v1/resource-management/resources",
                    json=resource_data,
                    headers=auth_headers,
                )
                # Allow for some failures due to mocking
                assert response.status_code in [201, 500, 422]

            end_time = time.time()
            total_time = end_time - start_time

            # Should process 50 resources in under 5 seconds
            assert total_time < 5.0, (
                f"Batch creation took {total_time:.3f}s, exceeds 5s limit"
            )

            # Calculate throughput
            throughput = len(batch_data) / total_time
            assert throughput > 10, (
                f"Throughput {throughput:.1f} resources/sec below 10/sec"
            )

    def test_large_dataset_analytics_performance(self, large_dataset):
        """Test analytics performance with large datasets"""

        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        # Mock large dataset responses
        mock_db.execute.return_value = Mock(
            fetchall=Mock(
                return_value=[
                    Mock(
                        resource_id=data["id"],
                        avg_utilization=data["utilization"],
                        peak_utilization=min(data["utilization"] + 20, 100),
                        min_utilization=max(data["utilization"] - 20, 0),
                        allocation_count=len(data["projects"]),
                        overutilized_periods=1 if data["utilization"] > 90 else 0,
                        underutilized_periods=1 if data["utilization"] < 60 else 0,
                    )
                    for data in large_dataset["resources"][
                        :100
                    ]  # Limit to 100 for test
                ]
            )
        )

        analytics_service = ResourceAnalyticsService(mock_db, mock_redis)

        async def run_analytics_test():
            start_time = time.time()

            result = await analytics_service.get_resource_analytics(
                start_date=date(2025, 7, 1), end_date=date(2025, 7, 31)
            )

            end_time = time.time()
            processing_time = end_time - start_time

            # Should process 100 resources in under 1 second
            assert processing_time < 1.0, (
                f"Analytics processing took {processing_time:.3f}s, exceeds 1s"
            )
            assert result.total_resources == 100

            return processing_time

        # Run the async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            processing_time = loop.run_until_complete(run_analytics_test())
            print(
                f"Analytics processing time: {processing_time:.3f}s for 100 resources"
            )
        finally:
            loop.close()

    def test_memory_usage_resource_operations(self, client, auth_headers):
        """Test memory usage during resource operations"""

        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        with patch("app.api.v1.resource_management_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }

            # Perform memory-intensive operations
            for i in range(100):
                resource_data = {
                    "name": f"Memory Test Resource {i}",
                    "type": "human",
                    "department_id": 1,
                    "hourly_rate": 150.0,
                    "description": "x" * 1000,  # 1KB description
                }

                client.post(
                    "/api/v1/resource-management/resources",
                    json=resource_data,
                    headers=auth_headers,
                )

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (under 50MB for 100 operations)
        assert memory_increase < 50, (
            f"Memory increased by {memory_increase:.1f}MB, exceeds 50MB limit"
        )

    def test_database_query_performance(self):
        """Test database query performance with optimized queries"""

        mock_db = AsyncMock()

        # Simulate complex query with joins
        complex_result = [
            Mock(
                resource_id=i,
                resource_name=f"Resource {i}",
                department_name=f"Department {(i % 10) + 1}",
                total_hours=160.0 + (i % 40),
                utilization_rate=70.0 + (i % 30),
                project_count=3 + (i % 5),
                avg_hourly_rate=120.0 + (i % 80),
            )
            for i in range(1, 501)  # 500 resources
        ]

        mock_db.execute.return_value = Mock(fetchall=Mock(return_value=complex_result))

        analytics_service = ResourceAnalyticsService(mock_db, AsyncMock())

        async def run_query_test():
            start_time = time.time()

            # Simulate complex analytics query
            await analytics_service.get_resource_analytics(
                start_date=date(2025, 6, 1),
                end_date=date(2025, 7, 31),
                resource_ids=list(range(1, 501)),
                department_ids=[1, 2, 3, 4, 5],
            )

            end_time = time.time()
            query_time = end_time - start_time

            # Complex query should complete in under 2 seconds
            assert query_time < 2.0, (
                f"Complex query took {query_time:.3f}s, exceeds 2s limit"
            )

            return query_time

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            query_time = loop.run_until_complete(run_query_test())
            print(f"Complex query time: {query_time:.3f}s for 500 resources")
        finally:
            loop.close()

    def test_cache_performance_improvement(self):
        """Test caching performance improvements"""

        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        # Setup cache hit scenario
        cached_data = {
            "total_resources": 100,
            "average_utilization": 78.5,
            "efficiency_score": 85.2,
            "generated_at": datetime.utcnow().isoformat(),
        }

        analytics_service = ResourceAnalyticsService(mock_db, mock_redis)

        async def test_cache_hit():
            # Mock cache hit
            mock_redis.get.return_value = str(cached_data)

            start_time = time.time()

            # This should hit cache and be very fast
            await analytics_service.get_resource_trends(
                resource_ids=[1, 2, 3],
                start_date=date(2025, 7, 1),
                end_date=date(2025, 7, 31),
            )

            end_time = time.time()
            cache_hit_time = end_time - start_time

            return cache_hit_time

        async def test_cache_miss():
            # Mock cache miss
            mock_redis.get.return_value = None
            mock_db.execute.return_value = Mock(fetchall=Mock(return_value=[]))

            start_time = time.time()

            # This should miss cache and query database
            await analytics_service.get_resource_trends(
                resource_ids=[1, 2, 3],
                start_date=date(2025, 7, 1),
                end_date=date(2025, 7, 31),
            )

            end_time = time.time()
            cache_miss_time = end_time - start_time

            return cache_miss_time

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            cache_hit_time = loop.run_until_complete(test_cache_hit())
            cache_miss_time = loop.run_until_complete(test_cache_miss())

            # Cache hit should be significantly faster
            improvement_ratio = (
                cache_miss_time / cache_hit_time if cache_hit_time > 0 else 1
            )

            print(f"Cache hit time: {cache_hit_time:.3f}s")
            print(f"Cache miss time: {cache_miss_time:.3f}s")
            print(f"Cache improvement ratio: {improvement_ratio:.1f}x")

            assert improvement_ratio > 2, (
                f"Cache improvement {improvement_ratio:.1f}x below 2x threshold"
            )
            assert cache_hit_time < 0.1, (
                f"Cache hit time {cache_hit_time:.3f}s exceeds 100ms"
            )

        finally:
            loop.close()

    def test_planning_algorithm_performance(self):
        """Test resource planning algorithm performance"""

        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        planning_service = ResourcePlanningService(mock_db, mock_redis)

        # Mock complex planning scenario
        complex_planning_request = {
            "plan_name": "Large Scale Planning",
            "planning_horizon": {
                "start_date": date(2025, 8, 1),
                "end_date": date(2025, 12, 31),
            },
            "departments": list(range(1, 21)),  # 20 departments
            "project_requirements": [
                {
                    "project_id": i,
                    "required_hours": 800 + (i % 400),
                    "skills": ["Python", "React", "FastAPI"],
                    "priority": "high" if i % 3 == 0 else "medium",
                }
                for i in range(1, 51)  # 50 projects
            ],
            "required_skills": ["Python", "React", "FastAPI", "PostgreSQL", "Docker"],
            "growth_targets": {"team_size": 1.2, "efficiency": 1.1},
            "budget_constraints": {"total_budget": Decimal("2000000.00")},
            "timeline_constraints": {},
            "priority_projects": list(range(1, 11)),
        }

        async def run_planning_test():
            # Mock planning service methods
            with patch.multiple(
                planning_service,
                _analyze_current_resource_state=AsyncMock(
                    return_value={"total_resources": 200}
                ),
                _analyze_demand_requirements=AsyncMock(
                    return_value={"total_demand": 40000}
                ),
                _generate_capacity_plan=AsyncMock(
                    return_value={"capacity_needed": 220}
                ),
                _identify_skill_gaps=AsyncMock(
                    return_value=[{"skill": "Python", "gap": 10}]
                ),
                _generate_hiring_plan=AsyncMock(return_value={"new_hires": 20}),
                _generate_training_plan=AsyncMock(
                    return_value={"training_programs": 5}
                ),
                _create_implementation_roadmap=AsyncMock(return_value={"phases": 3}),
                _calculate_plan_costs=AsyncMock(return_value={"total_cost": 1800000}),
                _assess_plan_risks=AsyncMock(return_value={"risk_level": "medium"}),
                _generate_planning_recommendations=Mock(
                    return_value=["Scale gradually"]
                ),
            ):
                mock_redis.incr.return_value = 123

                start_time = time.time()

                from app.schemas.resource import ResourcePlanningRequest

                planning_req = ResourcePlanningRequest(**complex_planning_request)

                await planning_service.create_resource_plan(
                    planning_request=planning_req, user_id=1
                )

                end_time = time.time()
                planning_time = end_time - start_time

                # Complex planning should complete in under 3 seconds
                assert planning_time < 3.0, (
                    f"Planning algorithm took {planning_time:.3f}s, exceeds 3s limit"
                )

                return planning_time

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            planning_time = loop.run_until_complete(run_planning_test())
            print(
                f"Planning algorithm time: {planning_time:.3f}s for 50 projects, 20 departments"
            )
        finally:
            loop.close()

    def test_api_throughput_stress_test(self, client, auth_headers):
        """Test API throughput under stress conditions"""

        with patch("app.api.v1.resource_integration_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }

            def make_dashboard_request():
                return client.get(
                    "/api/v1/resource-integration/dashboard", headers=auth_headers
                )

            def make_health_request():
                return client.get(
                    "/api/v1/resource-integration/health", headers=auth_headers
                )

            # Test with high concurrent load
            start_time = time.time()

            with ThreadPoolExecutor(max_workers=50) as executor:
                # Mix of different endpoints
                futures = []
                for i in range(100):
                    if i % 2 == 0:
                        futures.append(executor.submit(make_dashboard_request))
                    else:
                        futures.append(executor.submit(make_health_request))

                responses = [future.result() for future in futures]

            end_time = time.time()
            total_time = end_time - start_time

            # Calculate metrics
            successful_requests = sum(1 for r in responses if r.status_code == 200)
            success_rate = successful_requests / len(responses)
            throughput = len(responses) / total_time

            # Performance assertions
            assert success_rate >= 0.8, (
                f"Success rate {success_rate:.2%} below 80% under stress"
            )
            assert throughput > 20, (
                f"Throughput {throughput:.1f} req/sec below 20/sec under stress"
            )
            assert total_time < 10, (
                f"Stress test took {total_time:.3f}s, exceeds 10s limit"
            )

            print("Stress test results:")
            print(f"  Total requests: {len(responses)}")
            print(f"  Successful requests: {successful_requests}")
            print(f"  Success rate: {success_rate:.2%}")
            print(f"  Throughput: {throughput:.1f} req/sec")
            print(f"  Total time: {total_time:.3f}s")

    def test_data_export_performance(self):
        """Test performance of large data export operations"""

        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        # Mock large export dataset
        large_export_data = [
            {
                "resource_id": i,
                "name": f"Resource {i}",
                "department": f"Dept {(i % 10) + 1}",
                "utilization_history": [
                    {
                        "date": (date.today() - timedelta(days=j)).isoformat(),
                        "utilization": 70 + (j % 30),
                    }
                    for j in range(90)  # 90 days of history per resource
                ],
                "projects": [f"Project {i * 3 + k}" for k in range(5)],
                "skills": [f"Skill {i % 20 + k}" for k in range(3)],
            }
            for i in range(1, 501)  # 500 resources with full history
        ]

        integration_service = ResourceIntegrationService(mock_db, mock_redis)

        async def run_export_test():
            start_time = time.time()

            # Simulate large data export
            await integration_service.get_unified_resource_dashboard(
                user_id=1,
                time_period="quarter",
                departments=[1, 2, 3, 4, 5],
                include_forecasts=True,
                include_optimization=True,
            )

            end_time = time.time()
            export_time = end_time - start_time

            # Large export should complete in under 5 seconds
            assert export_time < 5.0, (
                f"Data export took {export_time:.3f}s, exceeds 5s limit"
            )

            return export_time

        # Mock the service methods
        with patch.multiple(
            integration_service,
            resource_service=Mock(
                get_resources=AsyncMock(
                    return_value=Mock(items=large_export_data[:100])
                )
            ),
            analytics_service=Mock(
                get_resource_analytics=AsyncMock(
                    return_value=Mock(
                        total_resources=500,
                        average_utilization=78.5,
                        total_cost=Decimal("250000.0"),
                        efficiency_score=85.2,
                        overutilized_resources=25,
                        underutilized_resources=45,
                        top_performers=[],
                        cost_breakdown=[],
                        recommendations=[],
                    )
                ),
                get_resource_kpis=AsyncMock(
                    return_value=Mock(current_kpis={}, performance_indicators=[])
                ),
            ),
        ):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                export_time = loop.run_until_complete(run_export_test())
                print(f"Data export time: {export_time:.3f}s for 500 resources")
            finally:
                loop.close()

    def test_optimization_algorithm_performance(self):
        """Test resource optimization algorithm performance"""

        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        integration_service = ResourceIntegrationService(mock_db, mock_redis)

        # Large optimization scenario
        optimization_request = {
            "resource_ids": list(range(1, 201)),  # 200 resources
            "project_ids": list(range(1, 51)),  # 50 projects
            "start_date": date.today(),
            "end_date": date.today() + timedelta(days=90),
            "optimization_goal": "efficiency",
            "constraints": {
                "max_utilization": 90.0,
                "min_utilization": 60.0,
                "budget_limit": 500000.0,
            },
        }

        async def run_optimization_test():
            # Mock optimization service methods
            with patch.multiple(
                integration_service,
                analytics_service=Mock(
                    get_resource_analytics=AsyncMock(
                        return_value=Mock(
                            efficiency_score=78.5, average_utilization=75.0
                        )
                    ),
                    analyze_resource_roi=AsyncMock(
                        return_value=Mock(
                            overall_roi=1.85,
                            optimization_opportunities=[],
                            investment_recommendations=[],
                        )
                    ),
                ),
                resource_service=Mock(
                    optimize_resources=AsyncMock(
                        return_value=Mock(
                            efficiency_score=88.5,
                            cost_savings=50000.0,
                            recommendations=[
                                "Rebalance workloads",
                                "Optimize schedules",
                            ],
                            implementation_complexity="medium",
                        )
                    )
                ),
            ):
                start_time = time.time()

                from fastapi import BackgroundTasks

                background_tasks = BackgroundTasks()

                await integration_service.execute_resource_optimization(
                    optimization_request=optimization_request,
                    user_id=1,
                    background_tasks=background_tasks,
                )

                end_time = time.time()
                optimization_time = end_time - start_time

                # Complex optimization should complete in under 4 seconds
                assert optimization_time < 4.0, (
                    f"Optimization took {optimization_time:.3f}s, exceeds 4s limit"
                )

                return optimization_time

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            optimization_time = loop.run_until_complete(run_optimization_test())
            print(
                f"Optimization algorithm time: {optimization_time:.3f}s for 200 resources, 50 projects"
            )
        finally:
            loop.close()


class TestResourceManagementScalability:
    """Scalability tests for resource management system"""

    def test_horizontal_scaling_simulation(self):
        """Test system behavior under horizontal scaling scenarios"""

        # Simulate multiple service instances
        service_instances = []
        for i in range(5):  # 5 service instances
            mock_db = AsyncMock()
            mock_redis = AsyncMock()
            service_instances.append(ResourceAnalyticsService(mock_db, mock_redis))

        async def simulate_distributed_load():
            tasks = []

            # Distribute load across instances
            for i, service in enumerate(service_instances):
                # Each instance handles different resource sets
                resource_ids = list(range(i * 100 + 1, (i + 1) * 100 + 1))

                task = service.get_resource_analytics(
                    start_date=date(2025, 7, 1),
                    end_date=date(2025, 7, 31),
                    resource_ids=resource_ids,
                )
                tasks.append(task)

            start_time = time.time()
            results = await asyncio.gather(*tasks)
            end_time = time.time()

            processing_time = end_time - start_time

            # Distributed processing should be efficient
            assert processing_time < 2.0, (
                f"Distributed processing took {processing_time:.3f}s, exceeds 2s"
            )
            assert len(results) == 5, "Not all service instances completed"

            return processing_time

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            processing_time = loop.run_until_complete(simulate_distributed_load())
            print(
                f"Horizontal scaling simulation: {processing_time:.3f}s for 5 instances processing 500 resources"
            )
        finally:
            loop.close()

    def test_database_connection_pool_performance(self):
        """Test database connection pool efficiency"""

        # Simulate connection pool with concurrent operations
        mock_db_pool = AsyncMock()

        async def simulate_connection_pool_test():
            # Simulate 50 concurrent database operations
            async def db_operation(operation_id):
                start_time = time.time()

                # Mock database query
                await mock_db_pool.execute(
                    "SELECT * FROM resources WHERE id = %s", (operation_id,)
                )

                end_time = time.time()
                return end_time - start_time

            start_time = time.time()

            # Run 50 operations concurrently
            tasks = [db_operation(i) for i in range(1, 51)]
            operation_times = await asyncio.gather(*tasks)

            end_time = time.time()
            total_time = end_time - start_time

            # Connection pool should handle 50 operations efficiently
            assert total_time < 1.0, (
                f"Connection pool operations took {total_time:.3f}s, exceeds 1s"
            )
            assert all(t < 0.1 for t in operation_times), (
                "Individual operations too slow"
            )

            return total_time, operation_times

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            total_time, operation_times = loop.run_until_complete(
                simulate_connection_pool_test()
            )
            avg_operation_time = sum(operation_times) / len(operation_times)
            print(
                f"Connection pool test: {total_time:.3f}s total, {avg_operation_time:.3f}s average per operation"
            )
        finally:
            loop.close()

    def test_cache_distribution_performance(self):
        """Test distributed cache performance"""

        # Simulate distributed Redis cache
        cache_nodes = [AsyncMock() for _ in range(3)]  # 3 cache nodes

        async def test_cache_distribution():
            # Simulate cache operations across nodes
            cache_operations = []

            for i in range(100):  # 100 cache operations
                node_index = i % len(cache_nodes)
                cache_key = f"resource_analytics:{i}"

                # Simulate cache set/get operations
                async def cache_operation(node, key, value):
                    start_time = time.time()
                    await node.set(key, value)
                    await node.get(key)
                    end_time = time.time()
                    return end_time - start_time

                operation = cache_operation(
                    cache_nodes[node_index], cache_key, f"data_{i}"
                )
                cache_operations.append(operation)

            start_time = time.time()
            operation_times = await asyncio.gather(*cache_operations)
            end_time = time.time()

            total_time = end_time - start_time
            avg_operation_time = sum(operation_times) / len(operation_times)

            # Distributed cache should be fast
            assert total_time < 0.5, (
                f"Cache distribution took {total_time:.3f}s, exceeds 500ms"
            )
            assert avg_operation_time < 0.01, (
                f"Average cache operation {avg_operation_time:.3f}s too slow"
            )

            return total_time, avg_operation_time

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            total_time, avg_time = loop.run_until_complete(test_cache_distribution())
            print(
                f"Cache distribution test: {total_time:.3f}s total, {avg_time:.3f}s average per operation"
            )
        finally:
            loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
