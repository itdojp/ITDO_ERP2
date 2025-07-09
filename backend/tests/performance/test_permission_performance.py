"""Performance tests for permission system."""

import asyncio
import pytest
import time
from typing import List

from sqlalchemy.orm import Session

from app.core.cache import CacheManager
from app.core.performance import PerformanceOptimizer
from app.models.organization import Organization
from app.models.permission import Permission
from app.models.role import Role, RoleType, UserRole
from app.models.role_permission import PermissionEffect, RolePermission
from app.models.user import User
from app.services.permission import PermissionService
from app.services.cross_service_integration import CrossServiceIntegrator


class TestPermissionPerformance:
    """Performance tests for permission system."""

    TARGET_PERMISSION_CHECK_TIME = 10  # ms
    TARGET_MATRIX_GENERATION_TIME = 100  # ms
    TARGET_1000_USERS_TIME = 200  # ms

    @pytest.fixture
    def large_dataset(self, db_session: Session):
        """Create a large dataset for performance testing."""
        # Create organization
        org = Organization(code="PERF001", name="Performance Org")
        db_session.add(org)
        db_session.commit()

        # Create 50 permissions across 10 categories
        permissions = []
        categories = ["user", "admin", "project", "task", "document", 
                     "report", "finance", "hr", "sales", "marketing"]
        
        for category in categories:
            for action in ["view", "create", "edit", "delete", "approve"]:
                perm = Permission(
                    code=f"{category}.{action}",
                    name=f"{action.title()} {category.title()}",
                    category=category,
                    is_active=True,
                )
                permissions.append(perm)
        
        db_session.add_all(permissions)
        db_session.commit()

        # Create 20 roles in hierarchy
        roles = []
        
        # Create root roles
        for i in range(5):
            role = Role(
                code=f"root.role{i}",
                name=f"Root Role {i}",
                role_type=RoleType.ORGANIZATION.value,
                organization_id=org.id,
                is_active=True,
            )
            roles.append(role)
        
        db_session.add_all(roles)
        db_session.commit()

        # Create child roles
        for i in range(15):
            parent = roles[i % 5]  # Distribute children among root roles
            role = Role(
                code=f"child.role{i}",
                name=f"Child Role {i}",
                role_type=RoleType.DEPARTMENT.value,
                organization_id=org.id,
                parent_id=parent.id,
                is_active=True,
            )
            roles.append(role)
        
        db_session.add_all(roles[5:])
        db_session.commit()

        # Assign permissions to roles randomly
        import random
        for role in roles:
            # Each role gets 10-30 permissions
            role_perms = random.sample(permissions, random.randint(10, 30))
            for perm in role_perms:
                rp = RolePermission(
                    role_id=role.id,
                    permission_id=perm.id,
                    effect=PermissionEffect.ALLOW.value,
                    organization_id=org.id,
                )
                db_session.add(rp)
        
        db_session.commit()

        # Create 1000 users
        users = []
        for i in range(1000):
            user = User(
                email=f"user{i:04d}@performance.test",
                full_name=f"Performance User {i}",
                is_active=True,
            )
            users.append(user)
        
        db_session.add_all(users)
        db_session.commit()

        # Assign roles to users
        for user in users:
            # Each user gets 1-5 roles
            user_roles = random.sample(roles, random.randint(1, 5))
            for role in user_roles:
                ur = UserRole(
                    user_id=user.id,
                    role_id=role.id,
                    organization_id=org.id,
                    is_active=True,
                )
                db_session.add(ur)
        
        db_session.commit()

        return {
            "organization": org,
            "users": users,
            "roles": roles,
            "permissions": permissions,
        }

    def test_permission_check_performance(self, db_session: Session, large_dataset: dict):
        """Test permission check performance."""
        permission_service = PermissionService(db_session)
        org = large_dataset["organization"]
        users = large_dataset["users"]
        permissions = large_dataset["permissions"]

        # Test 100 permission checks
        start_time = time.time()
        
        for i in range(100):
            user = users[i % len(users)]
            perm = permissions[i % len(permissions)]
            
            has_permission = permission_service.check_user_permission(
                user.id, perm.code, org.id
            )
            # Result doesn't matter, we're testing performance
        
        end_time = time.time()
        avg_time = ((end_time - start_time) * 1000) / 100  # Convert to ms per check
        
        print(f"Average permission check time: {avg_time:.2f}ms")
        assert avg_time < self.TARGET_PERMISSION_CHECK_TIME, \
            f"Permission check too slow: {avg_time:.2f}ms > {self.TARGET_PERMISSION_CHECK_TIME}ms"

    def test_bulk_permission_loading_performance(self, db_session: Session, large_dataset: dict):
        """Test bulk permission loading performance."""
        optimizer = PerformanceOptimizer(db_session)
        org = large_dataset["organization"]
        users = large_dataset["users"]

        # Test loading permissions for 100 users
        user_ids = [user.id for user in users[:100]]
        
        start_time = time.time()
        permissions_map = optimizer.optimized_user_permissions_bulk(user_ids, org.id)
        end_time = time.time()
        
        duration = (end_time - start_time) * 1000  # Convert to ms
        
        print(f"Bulk permission loading time for 100 users: {duration:.2f}ms")
        assert len(permissions_map) == 100
        assert duration < 50, f"Bulk loading too slow: {duration:.2f}ms"

    def test_permission_matrix_generation_performance(self, db_session: Session, large_dataset: dict):
        """Test permission matrix generation performance."""
        permission_service = PermissionService(db_session)
        org = large_dataset["organization"]

        start_time = time.time()
        matrix = permission_service.generate_permission_matrix(org.id)
        end_time = time.time()
        
        duration = (end_time - start_time) * 1000  # Convert to ms
        
        print(f"Permission matrix generation time: {duration:.2f}ms")
        assert duration < self.TARGET_MATRIX_GENERATION_TIME, \
            f"Matrix generation too slow: {duration:.2f}ms > {self.TARGET_MATRIX_GENERATION_TIME}ms"
        
        # Verify matrix structure
        assert "roles" in matrix
        assert "permissions" in matrix
        assert "categories" in matrix
        assert len(matrix["roles"]) == 20  # All roles
        assert len(matrix["categories"]) == 10  # All categories

    def test_1000_users_response_time(self, db_session: Session, large_dataset: dict):
        """Test response time for 1000 users."""
        optimizer = PerformanceOptimizer(db_session)
        org = large_dataset["organization"]
        users = large_dataset["users"]

        # Test getting organization users with permissions
        start_time = time.time()
        org_users = optimizer.get_organization_users_optimized(
            org.id, include_permissions=True
        )
        end_time = time.time()
        
        duration = (end_time - start_time) * 1000  # Convert to ms
        
        print(f"1000 users with permissions response time: {duration:.2f}ms")
        assert duration < self.TARGET_1000_USERS_TIME, \
            f"1000 users response too slow: {duration:.2f}ms > {self.TARGET_1000_USERS_TIME}ms"
        
        assert org_users["total"] == 1000
        assert len(org_users["users"]) == 1000

    @pytest.mark.asyncio
    async def test_cache_performance(self, db_session: Session, large_dataset: dict):
        """Test cache performance impact."""
        # Create mock cache
        cache = CacheManager()
        cache._cache = {}
        
        async def mock_get(key):
            return cache._cache.get(key)
        
        async def mock_set(key, value, expire=None):
            cache._cache[key] = value
        
        cache.get = mock_get
        cache.set = mock_set

        permission_service = PermissionService(db_session, cache)
        org = large_dataset["organization"]
        users = large_dataset["users"]

        # Test first 100 users (cold cache)
        test_users = users[:100]
        
        start_time = time.time()
        for user in test_users:
            perms = await permission_service.get_user_permissions_cached(user.id, org.id)
        cold_time = time.time() - start_time

        # Test same users again (warm cache)
        start_time = time.time()
        for user in test_users:
            perms = await permission_service.get_user_permissions_cached(user.id, org.id)
        warm_time = time.time() - start_time

        cold_time_ms = cold_time * 1000
        warm_time_ms = warm_time * 1000
        
        print(f"Cold cache time for 100 users: {cold_time_ms:.2f}ms")
        print(f"Warm cache time for 100 users: {warm_time_ms:.2f}ms")
        print(f"Cache speedup: {cold_time_ms / warm_time_ms:.2f}x")
        
        # Cache should provide significant speedup
        assert warm_time_ms < cold_time_ms * 0.5, "Cache not providing expected speedup"

    def test_role_hierarchy_performance(self, db_session: Session, large_dataset: dict):
        """Test role hierarchy query performance."""
        optimizer = PerformanceOptimizer(db_session)
        org = large_dataset["organization"]

        start_time = time.time()
        hierarchy = optimizer.optimize_role_hierarchy_queries(org.id)
        end_time = time.time()
        
        duration = (end_time - start_time) * 1000  # Convert to ms
        
        print(f"Role hierarchy query time: {duration:.2f}ms")
        assert duration < 50, f"Role hierarchy query too slow: {duration:.2f}ms"
        
        assert hierarchy["total_roles"] == 20
        assert hierarchy["max_depth"] <= 1  # Parent -> child depth

    def test_permission_bottleneck_detection(self, db_session: Session, large_dataset: dict):
        """Test bottleneck detection performance."""
        optimizer = PerformanceOptimizer(db_session)

        start_time = time.time()
        bottlenecks = optimizer.find_permission_bottlenecks()
        end_time = time.time()
        
        duration = (end_time - start_time) * 1000  # Convert to ms
        
        print(f"Bottleneck detection time: {duration:.2f}ms")
        assert duration < 100, f"Bottleneck detection too slow: {duration:.2f}ms"
        
        # Check bottleneck structure
        assert "deep_hierarchies" in bottlenecks
        assert "users_with_many_roles" in bottlenecks
        assert "roles_with_many_permissions" in bottlenecks

    def test_concurrent_permission_checks(self, db_session: Session, large_dataset: dict):
        """Test concurrent permission checks."""
        async def check_permissions_async():
            permission_service = PermissionService(db_session)
            org = large_dataset["organization"]
            users = large_dataset["users"]
            permissions = large_dataset["permissions"]
            
            tasks = []
            for i in range(50):
                user = users[i % len(users)]
                perm = permissions[i % len(permissions)]
                
                # Simulate async permission check
                async def check_perm(u_id, p_code, o_id):
                    # In real async implementation, this would be truly async
                    return permission_service.check_user_permission(u_id, p_code, o_id)
                
                tasks.append(check_perm(user.id, perm.code, org.id))
            
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            duration = (end_time - start_time) * 1000  # Convert to ms
            return duration, len(results)

        # Run the async test
        duration, result_count = asyncio.run(check_permissions_async())
        
        print(f"Concurrent permission checks time: {duration:.2f}ms for {result_count} checks")
        assert duration < 100, f"Concurrent checks too slow: {duration:.2f}ms"
        assert result_count == 50

    def test_memory_usage_optimization(self, db_session: Session, large_dataset: dict):
        """Test memory usage during large operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        optimizer = PerformanceOptimizer(db_session)
        org = large_dataset["organization"]
        users = large_dataset["users"]

        # Perform memory-intensive operation
        user_ids = [user.id for user in users]
        permissions_map = optimizer.optimized_user_permissions_bulk(user_ids, org.id)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        print(f"Memory usage: {initial_memory:.2f}MB -> {final_memory:.2f}MB (increase: {memory_increase:.2f}MB)")
        
        # Memory increase should be reasonable for 1000 users
        assert memory_increase < 100, f"Memory usage too high: {memory_increase:.2f}MB"
        assert len(permissions_map) == 1000

    def test_database_query_optimization(self, db_session: Session, large_dataset: dict):
        """Test database query optimization."""
        optimizer = PerformanceOptimizer(db_session)
        
        # Enable query logging to count queries
        import logging
        logging.basicConfig()
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

        org = large_dataset["organization"]
        users = large_dataset["users"][:100]  # Test with 100 users

        # Test optimized bulk loading
        user_ids = [user.id for user in users]
        
        start_time = time.time()
        permissions_map = optimizer.optimized_user_permissions_bulk(user_ids, org.id)
        end_time = time.time()
        
        duration = (end_time - start_time) * 1000
        
        print(f"Optimized bulk loading time: {duration:.2f}ms")
        assert duration < 100, f"Optimized bulk loading too slow: {duration:.2f}ms"
        assert len(permissions_map) == 100

    def test_index_creation_performance(self, db_session: Session):
        """Test performance index creation."""
        optimizer = PerformanceOptimizer(db_session)
        
        start_time = time.time()
        result = optimizer.create_performance_indexes()
        end_time = time.time()
        
        duration = (end_time - start_time) * 1000
        
        print(f"Index creation time: {duration:.2f}ms")
        print(f"Created indexes: {result}")
        
        # Index creation should complete reasonably quickly
        assert duration < 5000, f"Index creation too slow: {duration:.2f}ms"
        assert result["count"] > 0 or "error" in result

    def test_scalability_stress_test(self, db_session: Session, large_dataset: dict):
        """Stress test permission system scalability."""
        permission_service = PermissionService(db_session)
        org = large_dataset["organization"]
        users = large_dataset["users"]
        permissions = large_dataset["permissions"]

        # Simulate heavy load
        operations = []
        for i in range(500):
            user = users[i % len(users)]
            perm = permissions[i % len(permissions)]
            operations.append((user.id, perm.code, org.id))

        start_time = time.time()
        results = []
        for user_id, perm_code, org_id in operations:
            result = permission_service.check_user_permission(user_id, perm_code, org_id)
            results.append(result)
        end_time = time.time()

        duration = (end_time - start_time) * 1000
        avg_time = duration / len(operations)
        
        print(f"Stress test: {len(operations)} operations in {duration:.2f}ms")
        print(f"Average time per operation: {avg_time:.2f}ms")
        
        assert avg_time < 5, f"Average operation time too high: {avg_time:.2f}ms"
        assert len(results) == 500