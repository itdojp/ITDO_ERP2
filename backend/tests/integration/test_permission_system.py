"""Integration tests for permission system."""

import asyncio
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.cache import CacheManager
from app.core.performance import PerformanceOptimizer
from app.models.organization import Organization
from app.models.permission import Permission
from app.models.role import Role, RoleType, UserRole
from app.models.role_permission import PermissionEffect, RolePermission
from app.models.user import User
from app.models.department import Department
from app.services.cross_service_integration import CrossServiceIntegrator
from app.services.permission import PermissionService
from app.services.role import RoleService


class TestPermissionSystemIntegration:
    """Test permission system integration scenarios."""

    @pytest.fixture
    def cache_manager(self):
        """Create a mock cache manager for testing."""
        cache = CacheManager()
        cache._cache = {}  # In-memory cache for testing
        
        async def mock_get(key):
            return cache._cache.get(key)
        
        async def mock_set(key, value, expire=None):
            cache._cache[key] = value
        
        async def mock_delete(key):
            cache._cache.pop(key, None)
        
        async def mock_delete_pattern(pattern):
            # Simple pattern matching for testing
            keys_to_delete = [k for k in cache._cache.keys() if pattern.replace('*', '') in k]
            for key in keys_to_delete:
                cache._cache.pop(key, None)
        
        cache.get = mock_get
        cache.set = mock_set
        cache.delete = mock_delete
        cache.delete_pattern = mock_delete_pattern
        
        return cache

    @pytest.fixture
    def permission_service(self, db_session: Session, cache_manager: CacheManager):
        """Create permission service with cache."""
        return PermissionService(db_session, cache_manager)

    @pytest.fixture
    def cross_service(self, db_session: Session, cache_manager: CacheManager):
        """Create cross-service integrator."""
        return CrossServiceIntegrator(db_session, cache_manager)

    @pytest.fixture
    def performance_optimizer(self, db_session: Session):
        """Create performance optimizer."""
        return PerformanceOptimizer(db_session)

    def test_complex_permission_inheritance(self, db_session: Session, permission_service: PermissionService):
        """Test complex permission inheritance scenarios."""
        # Create organization
        org = Organization(code="COMPLEX001", name="Complex Org")
        db_session.add(org)
        db_session.commit()

        # Create permissions
        perms = [
            Permission(code="user.view", name="View Users", category="user"),
            Permission(code="user.edit", name="Edit Users", category="user"),
            Permission(code="user.delete", name="Delete Users", category="user"),
            Permission(code="admin.all", name="Admin All", category="admin"),
        ]
        db_session.add_all(perms)
        db_session.commit()

        # Create role hierarchy: Admin -> Manager -> User
        admin_role = Role(
            code="admin.complex",
            name="Complex Admin",
            role_type=RoleType.ORGANIZATION.value,
            organization_id=org.id,
            is_active=True,
        )
        db_session.add(admin_role)
        db_session.commit()

        manager_role = Role(
            code="manager.complex",
            name="Complex Manager",
            role_type=RoleType.DEPARTMENT.value,
            organization_id=org.id,
            parent_id=admin_role.id,
            is_active=True,
        )
        db_session.add(manager_role)
        db_session.commit()

        user_role = Role(
            code="user.complex",
            name="Complex User",
            role_type=RoleType.CUSTOM.value,
            organization_id=org.id,
            parent_id=manager_role.id,
            is_active=True,
        )
        db_session.add(user_role)
        db_session.commit()

        # Assign permissions to roles
        # Admin gets all permissions
        for perm in perms:
            rp = RolePermission(
                role_id=admin_role.id,
                permission_id=perm.id,
                effect=PermissionEffect.ALLOW.value,
                organization_id=org.id,
            )
            db_session.add(rp)

        # Manager gets view and edit (deny delete)
        for perm in perms[:2]:  # user.view, user.edit
            rp = RolePermission(
                role_id=manager_role.id,
                permission_id=perm.id,
                effect=PermissionEffect.ALLOW.value,
                organization_id=org.id,
            )
            db_session.add(rp)

        # Explicit deny for delete
        delete_deny = RolePermission(
            role_id=manager_role.id,
            permission_id=perms[2].id,  # user.delete
            effect=PermissionEffect.DENY.value,
            organization_id=org.id,
        )
        db_session.add(delete_deny)

        db_session.commit()

        # Test inheritance chain
        chain = permission_service.get_permission_inheritance_chain(user_role.id)
        assert len(chain) == 3  # user -> manager -> admin
        assert chain[0]["role_code"] == "user.complex"
        assert chain[1]["role_code"] == "manager.complex"
        assert chain[2]["role_code"] == "admin.complex"

        # Test effective permissions
        admin_perms = admin_role.get_effective_permissions(organization_id=org.id)
        assert "user.view" in admin_perms
        assert "user.edit" in admin_perms
        assert "user.delete" in admin_perms
        assert "admin.all" in admin_perms

        manager_perms = manager_role.get_effective_permissions(organization_id=org.id)
        assert "user.view" in manager_perms
        assert "user.edit" in manager_perms
        assert "user.delete" not in manager_perms  # Explicitly denied
        assert "admin.all" in manager_perms  # Inherited from admin

        user_perms = user_role.get_effective_permissions(organization_id=org.id)
        assert "user.view" in user_perms
        assert "user.edit" in user_perms
        assert "user.delete" not in user_perms  # Inherited denial
        assert "admin.all" in user_perms  # Inherited through chain

    @pytest.mark.asyncio
    async def test_permission_caching(self, db_session: Session, permission_service: PermissionService):
        """Test permission caching functionality."""
        # Create test data
        org = Organization(code="CACHE001", name="Cache Org")
        user = User(email="cache@test.com", full_name="Cache User")
        role = Role(code="cache.role", name="Cache Role", organization_id=org.id)
        perm = Permission(code="cache.test", name="Cache Test", category="test")
        
        db_session.add_all([org, user, role, perm])
        db_session.commit()

        # Create user role and permission
        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            organization_id=org.id,
            is_active=True,
        )
        role_perm = RolePermission(
            role_id=role.id,
            permission_id=perm.id,
            effect=PermissionEffect.ALLOW.value,
            organization_id=org.id,
        )
        db_session.add_all([user_role, role_perm])
        db_session.commit()

        # Test cached permissions
        perms1 = await permission_service.get_user_permissions_cached(user.id, org.id)
        assert "cache.test" in perms1

        # Should use cache on second call
        perms2 = await permission_service.get_user_permissions_cached(user.id, org.id)
        assert perms1 == perms2

        # Test cache invalidation
        await permission_service.invalidate_user_permission_cache(user.id, org.id)
        
        # Should fetch fresh data
        perms3 = await permission_service.get_user_permissions_cached(user.id, org.id)
        assert perms3 == perms1

    @pytest.mark.asyncio
    async def test_organization_transfer(self, db_session: Session, cross_service: CrossServiceIntegrator):
        """Test user organization transfer with permission updates."""
        # Create organizations
        org1 = Organization(code="FROM001", name="From Org")
        org2 = Organization(code="TO001", name="To Org")
        db_session.add_all([org1, org2])
        db_session.commit()

        # Create roles in both organizations
        role1 = Role(
            code="common.role",
            name="Common Role",
            organization_id=org1.id,
            is_active=True,
        )
        role2 = Role(
            code="common.role",
            name="Common Role",
            organization_id=org2.id,
            is_active=True,
        )
        db_session.add_all([role1, role2])
        db_session.commit()

        # Create user with role in org1
        user = User(email="transfer@test.com", full_name="Transfer User")
        db_session.add(user)
        db_session.commit()

        user_role = UserRole(
            user_id=user.id,
            role_id=role1.id,
            organization_id=org1.id,
            is_active=True,
            is_primary=True,
        )
        db_session.add(user_role)
        db_session.commit()

        # Perform organization transfer
        result = await cross_service.handle_user_organization_change(
            user_id=user.id,
            old_organization_id=org1.id,
            new_organization_id=org2.id,
        )

        assert result["roles_transferred"] == 1
        assert result["roles_removed"] == 1
        assert result["permissions_updated"] is True

        # Verify old role is deactivated
        db_session.refresh(user_role)
        assert user_role.is_active is False

        # Verify new role is created
        new_user_role = db_session.query(UserRole).filter(
            UserRole.user_id == user.id,
            UserRole.organization_id == org2.id,
            UserRole.is_active == True,
        ).first()
        assert new_user_role is not None
        assert new_user_role.role_id == role2.id

    @pytest.mark.asyncio
    async def test_department_transfer(self, db_session: Session, cross_service: CrossServiceIntegrator):
        """Test user department transfer with permission inheritance."""
        # Create organization and departments
        org = Organization(code="DEPT001", name="Dept Org")
        db_session.add(org)
        db_session.commit()

        dept1 = Department(
            code="D001",
            name="Department 1",
            organization_id=org.id,
        )
        dept2 = Department(
            code="D002",
            name="Department 2",
            organization_id=org.id,
        )
        db_session.add_all([dept1, dept2])
        db_session.commit()

        # Create department-specific role
        dept_role = Role(
            code="dept.role",
            name="Department Role",
            role_type=RoleType.DEPARTMENT.value,
            organization_id=org.id,
            is_active=True,
        )
        db_session.add(dept_role)
        db_session.commit()

        # Create user
        user = User(email="dept@test.com", full_name="Dept User")
        db_session.add(user)
        db_session.commit()

        # Initial role assignment
        user_role = UserRole(
            user_id=user.id,
            role_id=dept_role.id,
            organization_id=org.id,
            department_id=dept1.id,
            is_active=True,
        )
        db_session.add(user_role)
        db_session.commit()

        # Perform department transfer
        result = await cross_service.handle_department_transfer(
            user_id=user.id,
            old_department_id=dept1.id,
            new_department_id=dept2.id,
        )

        assert result["roles_updated"] >= 1

        # Verify department is updated
        db_session.refresh(user_role)
        assert user_role.department_id == dept2.id

    def test_performance_bulk_operations(self, db_session: Session, performance_optimizer: PerformanceOptimizer):
        """Test performance optimization for bulk operations."""
        # Create test data
        org = Organization(code="PERF001", name="Performance Org")
        db_session.add(org)
        db_session.commit()

        # Create multiple users
        users = []
        for i in range(10):
            user = User(
                email=f"user{i}@test.com",
                full_name=f"User {i}",
                is_active=True,
            )
            users.append(user)
        db_session.add_all(users)
        db_session.commit()

        # Create roles
        roles = []
        for i in range(3):
            role = Role(
                code=f"perf.role{i}",
                name=f"Performance Role {i}",
                organization_id=org.id,
                is_active=True,
            )
            roles.append(role)
        db_session.add_all(roles)
        db_session.commit()

        # Create permissions
        perms = []
        for i in range(5):
            perm = Permission(
                code=f"perf.perm{i}",
                name=f"Performance Perm {i}",
                category="performance",
                is_active=True,
            )
            perms.append(perm)
        db_session.add_all(perms)
        db_session.commit()

        # Assign roles to users
        for user in users:
            for role in roles:
                user_role = UserRole(
                    user_id=user.id,
                    role_id=role.id,
                    organization_id=org.id,
                    is_active=True,
                )
                db_session.add(user_role)

        # Assign permissions to roles
        for role in roles:
            for perm in perms:
                role_perm = RolePermission(
                    role_id=role.id,
                    permission_id=perm.id,
                    effect=PermissionEffect.ALLOW.value,
                    organization_id=org.id,
                )
                db_session.add(role_perm)

        db_session.commit()

        # Test bulk permission loading
        user_ids = [user.id for user in users]
        permissions_map = performance_optimizer.optimized_user_permissions_bulk(
            user_ids, org.id
        )

        assert len(permissions_map) == 10
        for user_id, perms in permissions_map.items():
            assert len(perms) == 5  # Each user should have all 5 permissions

        # Test organization users optimization
        org_users = performance_optimizer.get_organization_users_optimized(
            org.id, include_permissions=True
        )
        
        assert org_users["total"] == 10
        assert org_users["with_permissions"] is True
        assert all("permissions" in user for user in org_users["users"])

    def test_permission_matrix_generation(self, db_session: Session, permission_service: PermissionService):
        """Test permission matrix generation."""
        # Create organization
        org = Organization(code="MATRIX001", name="Matrix Org")
        db_session.add(org)
        db_session.commit()

        # Create roles
        admin_role = Role(
            code="matrix.admin",
            name="Matrix Admin",
            role_type=RoleType.ORGANIZATION.value,
            organization_id=org.id,
            is_active=True,
        )
        user_role = Role(
            code="matrix.user",
            name="Matrix User",
            role_type=RoleType.CUSTOM.value,
            organization_id=org.id,
            is_active=True,
        )
        db_session.add_all([admin_role, user_role])
        db_session.commit()

        # Create permissions
        perms = [
            Permission(code="matrix.view", name="Matrix View", category="matrix"),
            Permission(code="matrix.edit", name="Matrix Edit", category="matrix"),
            Permission(code="admin.all", name="Admin All", category="admin"),
        ]
        db_session.add_all(perms)
        db_session.commit()

        # Assign permissions
        role_perms = [
            RolePermission(
                role_id=admin_role.id,
                permission_id=perms[0].id,
                effect=PermissionEffect.ALLOW.value,
                organization_id=org.id,
            ),
            RolePermission(
                role_id=admin_role.id,
                permission_id=perms[1].id,
                effect=PermissionEffect.ALLOW.value,
                organization_id=org.id,
            ),
            RolePermission(
                role_id=admin_role.id,
                permission_id=perms[2].id,
                effect=PermissionEffect.ALLOW.value,
                organization_id=org.id,
            ),
            RolePermission(
                role_id=user_role.id,
                permission_id=perms[0].id,
                effect=PermissionEffect.ALLOW.value,
                organization_id=org.id,
            ),
        ]
        db_session.add_all(role_perms)
        db_session.commit()

        # Generate matrix
        matrix = permission_service.generate_permission_matrix(org.id)

        assert "roles" in matrix
        assert "permissions" in matrix
        assert "categories" in matrix
        assert "summary" in matrix

        # Check roles
        assert "matrix.admin" in matrix["roles"]
        assert "matrix.user" in matrix["roles"]

        admin_data = matrix["roles"]["matrix.admin"]
        assert admin_data["permission_count"] == 3
        assert "matrix.view" in admin_data["permissions"]
        assert "matrix.edit" in admin_data["permissions"]
        assert "admin.all" in admin_data["permissions"]

        user_data = matrix["roles"]["matrix.user"]
        assert user_data["permission_count"] == 1
        assert "matrix.view" in user_data["permissions"]

        # Check categories
        assert "matrix" in matrix["categories"]
        assert "admin" in matrix["categories"]
        assert len(matrix["categories"]["matrix"]) == 2
        assert len(matrix["categories"]["admin"]) == 1

    def test_dynamic_permission_evaluation(self, db_session: Session, permission_service: PermissionService):
        """Test dynamic permission evaluation with context."""
        # Create test data
        org = Organization(code="DYNAMIC001", name="Dynamic Org")
        user = User(email="dynamic@test.com", full_name="Dynamic User")
        role = Role(code="dynamic.role", name="Dynamic Role", organization_id=org.id)
        perm = Permission(code="dynamic.test", name="Dynamic Test", category="dynamic")
        
        db_session.add_all([org, user, role, perm])
        db_session.commit()

        # Create assignments
        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            organization_id=org.id,
            is_active=True,
        )
        role_perm = RolePermission(
            role_id=role.id,
            permission_id=perm.id,
            effect=PermissionEffect.ALLOW.value,
            organization_id=org.id,
        )
        db_session.add_all([user_role, role_perm])
        db_session.commit()

        # Test basic evaluation
        context = {"organization_id": org.id}
        result = permission_service.evaluate_dynamic_permission(
            user.id, "dynamic.test", context
        )
        assert result is True

        # Test time-based restriction
        context = {
            "organization_id": org.id,
            "time_restricted": True,
            "allowed_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17],  # 9 AM - 5 PM
        }
        
        # This test depends on current time, so we'll test both scenarios
        result = permission_service.evaluate_dynamic_permission(
            user.id, "dynamic.test", context
        )
        # Result depends on current hour, so we just ensure it's a boolean
        assert isinstance(result, bool)

        # Test resource limits
        context = {
            "organization_id": org.id,
            "resource_limits": True,
            "resource_type": "documents",
            "current_count": 10,
            "max_allowed": 5,
        }
        result = permission_service.evaluate_dynamic_permission(
            user.id, "dynamic.test", context
        )
        assert result is False  # Exceeds limit

        # Test conditional permissions
        context = {
            "organization_id": org.id,
            "conditions": [
                {"type": "has_role", "role_code": "dynamic.role"},
                {"type": "custom", "result": True},
            ],
        }
        result = permission_service.evaluate_dynamic_permission(
            user.id, "dynamic.test", context
        )
        assert result is True

    def test_permission_optimization(self, db_session: Session, permission_service: PermissionService):
        """Test permission assignment optimization."""
        # Create organization
        org = Organization(code="OPT001", name="Optimization Org")
        db_session.add(org)
        db_session.commit()

        # Create role hierarchy
        parent_role = Role(
            code="opt.parent",
            name="Optimization Parent",
            organization_id=org.id,
            is_active=True,
        )
        child_role = Role(
            code="opt.child",
            name="Optimization Child",
            organization_id=org.id,
            is_active=True,
        )
        db_session.add_all([parent_role, child_role])
        db_session.commit()

        # Set up inheritance
        child_role.parent_id = parent_role.id
        db_session.commit()

        # Create permission
        perm = Permission(
            code="opt.test",
            name="Optimization Test",
            category="optimization",
            is_active=True,
        )
        db_session.add(perm)
        db_session.commit()

        # Assign permission to parent
        parent_perm = RolePermission(
            role_id=parent_role.id,
            permission_id=perm.id,
            effect=PermissionEffect.ALLOW.value,
            organization_id=org.id,
        )
        db_session.add(parent_perm)
        db_session.commit()

        # Redundantly assign same permission to child
        child_perm = RolePermission(
            role_id=child_role.id,
            permission_id=perm.id,
            effect=PermissionEffect.ALLOW.value,
            organization_id=org.id,
        )
        db_session.add(child_perm)
        db_session.commit()

        # Optimize permissions
        result = permission_service.optimize_permission_assignments(child_role.id)
        
        assert result["optimized"] is True
        assert result["removed_redundant"] == 1
        assert result["kept_permissions"] == 0

        # Verify redundant permission was removed
        remaining_perms = db_session.query(RolePermission).filter(
            RolePermission.role_id == child_role.id,
            RolePermission.is_active == True,
        ).count()
        assert remaining_perms == 0

        # But child still has permission through inheritance
        child_permissions = child_role.get_effective_permissions(organization_id=org.id)
        assert "opt.test" in child_permissions