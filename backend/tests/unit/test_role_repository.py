"""Unit tests for Role Repository."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.role import Role, RoleType, UserRole
from app.models.permission import Permission
from app.models.role_permission import PermissionEffect, RolePermission
from app.models.user import User
from app.models.organization import Organization
from app.models.department import Department
from app.repositories.role import RoleRepository, UserRoleRepository
from app.schemas.role import RoleCreate, RoleUpdate, UserRoleCreate


class TestRoleRepository:
    """Test RoleRepository functionality."""

    @pytest.fixture
    def role_repo(self, db_session: Session):
        """Create role repository instance."""
        return RoleRepository(Role, db_session)

    def test_get_by_code(self, role_repo: RoleRepository, db_session: Session):
        """Test getting role by code."""
        # Create role
        role = Role(code="test.code", name="Test Role")
        db_session.add(role)
        db_session.commit()

        # Test get by code
        found = role_repo.get_by_code("test.code")
        assert found is not None
        assert found.id == role.id
        assert found.code == "test.code"

        # Test non-existent code
        not_found = role_repo.get_by_code("non.existent")
        assert not_found is None

    def test_get_system_roles(self, role_repo: RoleRepository, db_session: Session):
        """Test getting system roles."""
        # Create system and non-system roles
        sys_role1 = Role(
            code="sys.role1",
            name="System Role 1",
            is_system=True,
            display_order=1,
        )
        sys_role2 = Role(
            code="sys.role2",
            name="System Role 2",
            is_system=True,
            display_order=2,
        )
        custom_role = Role(
            code="custom.role",
            name="Custom Role",
            is_system=False,
        )
        db_session.add_all([sys_role1, sys_role2, custom_role])
        db_session.commit()

        # Get system roles
        system_roles = role_repo.get_system_roles()
        assert len(system_roles) == 2
        assert all(role.is_system for role in system_roles)
        assert system_roles[0].display_order <= system_roles[1].display_order

    def test_get_roles_by_type(self, role_repo: RoleRepository, db_session: Session):
        """Test getting roles by type."""
        # Create roles of different types
        org_role = Role(
            code="org.role",
            name="Org Role",
            role_type=RoleType.ORGANIZATION.value,
        )
        dept_role = Role(
            code="dept.role",
            name="Dept Role",
            role_type=RoleType.DEPARTMENT.value,
        )
        custom_role = Role(
            code="custom.role",
            name="Custom Role",
            role_type=RoleType.CUSTOM.value,
        )
        db_session.add_all([org_role, dept_role, custom_role])
        db_session.commit()

        # Test by type
        org_roles = role_repo.get_by_type(RoleType.ORGANIZATION.value)
        assert len(org_roles) == 1
        assert org_roles[0].role_type == RoleType.ORGANIZATION.value

        dept_roles = role_repo.get_by_type(RoleType.DEPARTMENT.value)
        assert len(dept_roles) == 1
        assert dept_roles[0].role_type == RoleType.DEPARTMENT.value

    def test_get_permissions_for_role(self, role_repo: RoleRepository, db_session: Session):
        """Test getting permissions for a role."""
        # Create roles with hierarchy
        parent_role = Role(code="parent", name="Parent Role")
        child_role = Role(code="child", name="Child Role", parent_id=parent_role.id)
        db_session.add_all([parent_role, child_role])
        db_session.commit()

        # Create permissions
        perm1 = Permission(code="perm1", name="Permission 1", category="test")
        perm2 = Permission(code="perm2", name="Permission 2", category="test")
        perm3 = Permission(code="perm3", name="Permission 3", category="test")
        db_session.add_all([perm1, perm2, perm3])
        db_session.commit()

        # Assign permissions
        rp1 = RolePermission(role_id=parent_role.id, permission_id=perm1.id)
        rp2 = RolePermission(role_id=parent_role.id, permission_id=perm2.id)
        rp3 = RolePermission(role_id=child_role.id, permission_id=perm3.id)
        db_session.add_all([rp1, rp2, rp3])
        db_session.commit()

        # Test with inheritance
        child_perms = role_repo.get_permissions_for_role(child_role.id, include_inherited=True)
        assert len(child_perms) == 3  # 2 from parent + 1 own

        # Test without inheritance
        child_perms_direct = role_repo.get_permissions_for_role(child_role.id, include_inherited=False)
        assert len(child_perms_direct) == 1  # Only own permission

    def test_check_permission(self, role_repo: RoleRepository, db_session: Session):
        """Test checking role permissions."""
        # Create role and permissions
        role = Role(code="check.role", name="Check Role")
        db_session.add(role)
        
        perm1 = Permission(code="user.view", name="View Users", category="user")
        perm2 = Permission(code="user.create", name="Create Users", category="user")
        db_session.add_all([perm1, perm2])
        db_session.commit()

        # Assign one permission
        rp = RolePermission(role_id=role.id, permission_id=perm1.id)
        db_session.add(rp)
        db_session.commit()

        # Test permission checks
        assert role_repo.check_permission(role.id, "user.view") is True
        assert role_repo.check_permission(role.id, "user.create") is False
        assert role_repo.check_permission(999, "user.view") is False  # Non-existent role

    def test_assign_permissions_to_role(self, role_repo: RoleRepository, db_session: Session):
        """Test assigning permissions to role."""
        # Create role and permissions
        role = Role(code="assign.role", name="Assign Role")
        db_session.add(role)
        
        perm1 = Permission(code="perm1", name="Permission 1", category="test")
        perm2 = Permission(code="perm2", name="Permission 2", category="test")
        perm3 = Permission(code="perm3", name="Permission 3", category="test")
        db_session.add_all([perm1, perm2, perm3])
        db_session.commit()

        # Assign multiple permissions
        new_perms = role_repo.assign_permissions_to_role(
            role_id=role.id,
            permission_ids=[perm1.id, perm2.id],
            effect="allow",
        )
        assert len(new_perms) == 2

        # Try to assign again (should not duplicate)
        new_perms2 = role_repo.assign_permissions_to_role(
            role_id=role.id,
            permission_ids=[perm1.id, perm3.id],
            effect="allow",
        )
        assert len(new_perms2) == 1  # Only perm3 is new

    def test_bulk_permission_operations(self, role_repo: RoleRepository, db_session: Session):
        """Test bulk permission operations."""
        # Create roles and permissions
        role1 = Role(code="bulk1", name="Bulk Role 1")
        role2 = Role(code="bulk2", name="Bulk Role 2")
        db_session.add_all([role1, role2])
        
        perm1 = Permission(code="bulk.perm1", name="Bulk Perm 1", category="test")
        perm2 = Permission(code="bulk.perm2", name="Bulk Perm 2", category="test")
        perm3 = Permission(code="bulk.perm3", name="Bulk Perm 3", category="test")
        db_session.add_all([perm1, perm2, perm3])
        db_session.commit()

        # Prepare bulk operations
        operations = [
            {
                "type": "add",
                "role_id": role1.id,
                "permission_ids": [perm1.id, perm2.id],
                "effect": "allow",
            },
            {
                "type": "add",
                "role_id": role2.id,
                "permission_ids": [perm2.id, perm3.id],
                "effect": "allow",
            },
        ]

        # Execute bulk operations
        results = role_repo.bulk_permission_operations(operations)
        assert results["added"] == 4  # 2 + 2 permissions
        assert results["removed"] == 0
        assert results["updated"] == 0
        assert len(results["errors"]) == 0

        # Test remove operation
        remove_ops = [
            {
                "type": "remove",
                "role_id": role1.id,
                "permission_ids": [perm1.id],
            }
        ]
        
        remove_results = role_repo.bulk_permission_operations(remove_ops)
        assert remove_results["removed"] == 1

    def test_clone_role(self, role_repo: RoleRepository, db_session: Session):
        """Test cloning a role."""
        # Create organization
        org = Organization(code="CLONE001", name="Clone Org")
        db_session.add(org)
        
        # Create source role with permissions
        source = Role(
            code="source.role",
            name="Source Role",
            description="Original description",
            permissions={"users": {"view": True, "create": True}},
            display_order=10,
            icon="users",
            color="#FF0000",
        )
        db_session.add(source)
        db_session.commit()

        # Clone the role
        cloned = role_repo.clone_role(
            source_id=source.id,
            new_code="cloned.role",
            new_name="Cloned Role",
            organization_id=org.id,
            include_permissions=True,
        )

        assert cloned.code == "cloned.role"
        assert cloned.name == "Cloned Role"
        assert cloned.permissions == source.permissions
        assert cloned.display_order == source.display_order
        assert cloned.icon == source.icon
        assert cloned.color == source.color
        assert cloned.is_system is False
        assert "Cloned from" in cloned.description

    def test_search_by_name(self, role_repo: RoleRepository, db_session: Session):
        """Test searching roles by name."""
        # Create roles
        role1 = Role(code="search1", name="Admin Role", description="System administrator")
        role2 = Role(code="search2", name="User Role", description="Regular user")
        role3 = Role(code="search3", name="Manager", name_en="Manager Role")
        db_session.add_all([role1, role2, role3])
        db_session.commit()

        # Search tests
        admin_results = role_repo.search_by_name("Admin")
        assert len(admin_results) == 1
        assert admin_results[0].code == "search1"

        role_results = role_repo.search_by_name("Role")
        assert len(role_results) == 3  # All have "Role" in name or name_en

        manager_results = role_repo.search_by_name("Manager")
        assert len(manager_results) == 1
        assert manager_results[0].code == "search3"


class TestUserRoleRepository:
    """Test UserRoleRepository functionality."""

    @pytest.fixture
    def user_role_repo(self, db_session: Session):
        """Create user role repository instance."""
        return UserRoleRepository(UserRole, db_session)

    def test_get_user_roles(self, user_role_repo: UserRoleRepository, db_session: Session):
        """Test getting user roles."""
        # Create user, roles, and organization
        user = User(email="roles@example.com", full_name="Roles User")
        role1 = Role(code="role1", name="Role 1")
        role2 = Role(code="role2", name="Role 2")
        org = Organization(code="ROLES001", name="Roles Org")
        db_session.add_all([user, role1, role2, org])
        db_session.commit()

        # Assign roles
        ur1 = UserRole(
            user_id=user.id,
            role_id=role1.id,
            organization_id=org.id,
            is_active=True,
        )
        ur2 = UserRole(
            user_id=user.id,
            role_id=role2.id,
            organization_id=org.id,
            is_active=False,  # Inactive
        )
        db_session.add_all([ur1, ur2])
        db_session.commit()

        # Test active only (default)
        active_roles = user_role_repo.get_user_roles(user.id, active_only=True)
        assert len(active_roles) == 1
        assert active_roles[0].role_id == role1.id

        # Test all roles
        all_roles = user_role_repo.get_user_roles(user.id, active_only=False)
        assert len(all_roles) == 2

    def test_get_primary_role(self, user_role_repo: UserRoleRepository, db_session: Session):
        """Test getting primary role."""
        # Create user and roles
        user = User(email="primary@example.com", full_name="Primary User")
        role1 = Role(code="primary1", name="Primary Role")
        role2 = Role(code="secondary", name="Secondary Role")
        org = Organization(code="PRIM001", name="Primary Org")
        db_session.add_all([user, role1, role2, org])
        db_session.commit()

        # Assign roles
        ur1 = UserRole(
            user_id=user.id,
            role_id=role1.id,
            organization_id=org.id,
            is_primary=True,
        )
        ur2 = UserRole(
            user_id=user.id,
            role_id=role2.id,
            organization_id=org.id,
            is_primary=False,
        )
        db_session.add_all([ur1, ur2])
        db_session.commit()

        # Get primary role
        primary = user_role_repo.get_primary_role(user.id)
        assert primary is not None
        assert primary.role_id == role1.id
        assert primary.is_primary is True

    def test_assign_role(self, user_role_repo: UserRoleRepository, db_session: Session):
        """Test assigning role to user."""
        # Create user, role, and organization
        user = User(email="assign@example.com", full_name="Assign User")
        role = Role(code="assign", name="Assign Role")
        org = Organization(code="ASSIGN001", name="Assign Org")
        admin = User(email="admin@example.com", full_name="Admin User")
        db_session.add_all([user, role, org, admin])
        db_session.commit()

        # Assign role
        user_role = user_role_repo.assign_role(
            user_id=user.id,
            role_id=role.id,
            organization_id=org.id,
            assigned_by=admin.id,
        )

        assert user_role.user_id == user.id
        assert user_role.role_id == role.id
        assert user_role.organization_id == org.id
        assert user_role.assigned_by == admin.id
        assert user_role.is_active is True

        # Try to assign again (should reactivate)
        user_role2 = user_role_repo.assign_role(
            user_id=user.id,
            role_id=role.id,
            organization_id=org.id,
            assigned_by=admin.id,
        )
        assert user_role2.id == user_role.id  # Same record

    def test_revoke_role(self, user_role_repo: UserRoleRepository, db_session: Session):
        """Test revoking role from user."""
        # Create and assign role
        user = User(email="revoke@example.com", full_name="Revoke User")
        role = Role(code="revoke", name="Revoke Role")
        org = Organization(code="REVOKE001", name="Revoke Org")
        db_session.add_all([user, role, org])
        db_session.commit()

        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            organization_id=org.id,
            is_active=True,
        )
        db_session.add(user_role)
        db_session.commit()

        # Revoke role
        revoked = user_role_repo.revoke_role(
            user_id=user.id,
            role_id=role.id,
            organization_id=org.id,
        )
        assert revoked is True

        # Check it's inactive
        db_session.refresh(user_role)
        assert user_role.is_active is False

    def test_get_expiring_roles(self, user_role_repo: UserRoleRepository, db_session: Session):
        """Test getting expiring roles."""
        # Create users and role
        user1 = User(email="expire1@example.com", full_name="Expire User 1")
        user2 = User(email="expire2@example.com", full_name="Expire User 2")
        role = Role(code="expire", name="Expire Role")
        org = Organization(code="EXPIRE001", name="Expire Org")
        db_session.add_all([user1, user2, role, org])
        db_session.commit()

        # Create user roles with different expiration dates
        now = datetime.utcnow()
        
        # Expires in 10 days
        ur1 = UserRole(
            user_id=user1.id,
            role_id=role.id,
            organization_id=org.id,
            expires_at=now + timedelta(days=10),
        )
        
        # Expires in 40 days (outside 30-day window)
        ur2 = UserRole(
            user_id=user2.id,
            role_id=role.id,
            organization_id=org.id,
            expires_at=now + timedelta(days=40),
        )
        
        # Already expired
        ur3 = UserRole(
            user_id=user1.id,
            role_id=role.id,
            organization_id=org.id,
            expires_at=now - timedelta(days=1),
        )
        
        db_session.add_all([ur1, ur2, ur3])
        db_session.commit()

        # Get expiring roles within 30 days
        expiring = user_role_repo.get_expiring_roles(days=30)
        assert len(expiring) == 1
        assert expiring[0].id == ur1.id