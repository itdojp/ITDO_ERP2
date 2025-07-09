"""Unit tests for Role model."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.role import Role, RoleType, SystemRole, UserRole
from app.models.permission import Permission
from app.models.role_permission import PermissionEffect, RolePermission
from app.models.user import User
from app.models.organization import Organization
from app.models.department import Department


class TestRoleModel:
    """Test Role model functionality."""

    def test_role_creation(self, db_session: Session):
        """Test basic role creation."""
        role = Role(
            code="test.role",
            name="Test Role",
            description="Test role description",
            role_type=RoleType.CUSTOM.value,
            is_active=True,
        )
        db_session.add(role)
        db_session.commit()

        assert role.id is not None
        assert role.code == "test.role"
        assert role.name == "Test Role"
        assert role.role_type == RoleType.CUSTOM.value
        assert role.is_active is True
        assert role.is_system is False
        assert role.depth == 0
        assert role.full_path == "/"

    def test_role_type_enum(self):
        """Test RoleType enum values."""
        assert RoleType.SYSTEM.value == "system"
        assert RoleType.ORGANIZATION.value == "organization"
        assert RoleType.DEPARTMENT.value == "department"
        assert RoleType.PROJECT.value == "project"
        assert RoleType.CUSTOM.value == "custom"

    def test_system_role_enum(self):
        """Test SystemRole enum values."""
        assert SystemRole.SUPER_ADMIN.value == "system.super_admin"
        assert SystemRole.ORG_ADMIN.value == "system.org_admin"
        assert SystemRole.DEPT_MANAGER.value == "system.dept_manager"
        assert SystemRole.PROJECT_MANAGER.value == "system.project_manager"
        assert SystemRole.USER.value == "system.user"
        assert SystemRole.VIEWER.value == "system.viewer"

    def test_role_hierarchy(self, db_session: Session):
        """Test role hierarchy functionality."""
        # Create parent role
        parent_role = Role(
            code="parent.role",
            name="Parent Role",
            role_type=RoleType.ORGANIZATION.value,
        )
        db_session.add(parent_role)
        db_session.commit()

        # Create child role
        child_role = Role(
            code="child.role",
            name="Child Role",
            role_type=RoleType.DEPARTMENT.value,
            parent_id=parent_role.id,
        )
        db_session.add(child_role)
        db_session.commit()

        assert child_role.parent_id == parent_role.id
        assert child_role.is_inherited is True
        assert parent_role.is_inherited is False

    def test_role_permissions_json(self, db_session: Session):
        """Test role permissions JSON field."""
        permissions_data = {
            "users": {"view": True, "create": True, "edit": False},
            "projects": {"view": True, "create": False},
        }

        role = Role(
            code="perm.role",
            name="Permission Role",
            permissions=permissions_data,
        )
        db_session.add(role)
        db_session.commit()

        assert role.permissions == permissions_data
        assert role.has_permission("users.view") is True
        assert role.has_permission("users.create") is True
        assert role.has_permission("users.edit") is False
        assert role.has_permission("users.delete") is False

    def test_permission_inheritance(self, db_session: Session):
        """Test permission inheritance from parent roles."""
        # Create parent with permissions
        parent_role = Role(
            code="parent.perm",
            name="Parent with Permissions",
            permissions={"users": {"view": True, "create": True}},
        )
        db_session.add(parent_role)
        db_session.commit()

        # Create child with additional permissions
        child_role = Role(
            code="child.perm",
            name="Child with Permissions",
            parent_id=parent_role.id,
            permissions={"users": {"edit": True}, "projects": {"view": True}},
        )
        db_session.add(child_role)
        db_session.commit()

        # Check inherited permissions
        all_perms = child_role.get_all_permissions()
        assert all_perms["users"]["view"] is True  # Inherited
        assert all_perms["users"]["create"] is True  # Inherited
        assert all_perms["users"]["edit"] is True  # Own
        assert all_perms["projects"]["view"] is True  # Own

    def test_effective_permissions(self, db_session: Session):
        """Test effective permissions with RolePermission relationships."""
        # Create organization and permissions
        org = Organization(code="TEST001", name="Test Org")
        db_session.add(org)
        
        perm1 = Permission(code="user.view", name="View Users", category="user")
        perm2 = Permission(code="user.create", name="Create Users", category="user")
        perm3 = Permission(code="admin.all", name="Admin All", category="admin")
        db_session.add_all([perm1, perm2, perm3])
        db_session.commit()

        # Create role
        role = Role(code="test.effective", name="Test Effective")
        db_session.add(role)
        db_session.commit()

        # Add permissions with different effects
        rp1 = RolePermission(
            role_id=role.id,
            permission_id=perm1.id,
            effect=PermissionEffect.ALLOW.value,
            organization_id=org.id,
        )
        rp2 = RolePermission(
            role_id=role.id,
            permission_id=perm2.id,
            effect=PermissionEffect.DENY.value,
            organization_id=org.id,
        )
        db_session.add_all([rp1, rp2])
        db_session.commit()

        # Test effective permissions
        perms = role.get_effective_permissions(organization_id=org.id)
        assert "user.view" in perms
        assert "user.create" not in perms

    def test_permission_scope_matching(self, db_session: Session):
        """Test permission scope matching."""
        # Create organizations and department
        org1 = Organization(code="ORG001", name="Org 1")
        org2 = Organization(code="ORG002", name="Org 2")
        db_session.add_all([org1, org2])
        db_session.commit()
        
        dept = Department(code="DEPT001", name="Dept 1", organization_id=org1.id)
        db_session.add(dept)
        db_session.commit()

        # Create permission and role
        perm = Permission(code="test.scoped", name="Scoped Permission", category="test")
        db_session.add(perm)
        
        role = Role(code="scoped.role", name="Scoped Role")
        db_session.add(role)
        db_session.commit()

        # Add scoped permissions
        rp_global = RolePermission(
            role_id=role.id,
            permission_id=perm.id,
            effect=PermissionEffect.ALLOW.value,
        )
        rp_org = RolePermission(
            role_id=role.id,
            permission_id=perm.id,
            effect=PermissionEffect.ALLOW.value,
            organization_id=org1.id,
        )
        rp_dept = RolePermission(
            role_id=role.id,
            permission_id=perm.id,
            effect=PermissionEffect.ALLOW.value,
            organization_id=org1.id,
            department_id=dept.id,
        )
        db_session.add_all([rp_global, rp_org, rp_dept])
        db_session.commit()

        # Test scope matching
        assert rp_global.matches_scope()  # Global matches any scope
        assert rp_global.matches_scope(organization_id=org1.id)
        assert rp_global.matches_scope(organization_id=org2.id)
        
        assert rp_org.matches_scope(organization_id=org1.id)
        assert not rp_org.matches_scope(organization_id=org2.id)
        
        assert rp_dept.matches_scope(organization_id=org1.id, department_id=dept.id)
        assert not rp_dept.matches_scope(organization_id=org2.id, department_id=dept.id)

    def test_permission_priority(self, db_session: Session):
        """Test permission priority calculation."""
        # System role
        system_role = Role(
            code="sys.role",
            name="System Role",
            role_type=RoleType.SYSTEM.value,
            is_system=True,
        )
        db_session.add(system_role)
        
        # Organization role
        org_role = Role(
            code="org.role",
            name="Org Role",
            role_type=RoleType.ORGANIZATION.value,
            depth=1,
        )
        db_session.add(org_role)
        
        # Department role
        dept_role = Role(
            code="dept.role",
            name="Dept Role",
            role_type=RoleType.DEPARTMENT.value,
            depth=2,
        )
        db_session.add(dept_role)
        db_session.commit()

        # Test priorities
        assert system_role.get_permission_priority() == 1000  # System role
        assert org_role.get_permission_priority() == 499  # 500 - 1
        assert dept_role.get_permission_priority() == 298  # 300 - 2

    def test_circular_inheritance_check(self, db_session: Session):
        """Test circular inheritance prevention."""
        # Create roles
        role1 = Role(code="role1", name="Role 1")
        role2 = Role(code="role2", name="Role 2")
        role3 = Role(code="role3", name="Role 3")
        db_session.add_all([role1, role2, role3])
        db_session.commit()

        # Set up hierarchy: role1 -> role2 -> role3
        role2.parent_id = role1.id
        role3.parent_id = role2.id
        db_session.commit()

        # Test circular inheritance checks
        assert role1.can_inherit_from(role2) is False  # Would create cycle
        assert role1.can_inherit_from(role3) is False  # Would create cycle
        assert role3.can_inherit_from(role1) is True  # Valid

    def test_is_organization_admin(self, db_session: Session):
        """Test organization admin role detection."""
        # System org admin
        sys_admin = Role(
            code=SystemRole.ORG_ADMIN.value,
            name="System Org Admin",
            role_type=RoleType.SYSTEM.value,
        )
        
        # Custom org admin
        custom_admin = Role(
            code="custom.admin",
            name="Custom Admin",
            role_type=RoleType.ORGANIZATION.value,
        )
        
        # Non-admin role
        regular_role = Role(
            code="regular.user",
            name="Regular User",
            role_type=RoleType.CUSTOM.value,
        )
        
        db_session.add_all([sys_admin, custom_admin, regular_role])
        db_session.commit()

        assert sys_admin.is_organization_admin is True
        assert custom_admin.is_organization_admin is True
        assert regular_role.is_organization_admin is False


class TestUserRoleModel:
    """Test UserRole model functionality."""

    def test_user_role_creation(self, db_session: Session):
        """Test basic user role assignment."""
        # Create prerequisites
        user = User(email="test@example.com", full_name="Test User")
        role = Role(code="test.role", name="Test Role")
        org = Organization(code="TEST001", name="Test Org")
        db_session.add_all([user, role, org])
        db_session.commit()

        # Create user role
        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            organization_id=org.id,
            is_active=True,
            is_primary=True,
        )
        db_session.add(user_role)
        db_session.commit()

        assert user_role.id is not None
        assert user_role.user_id == user.id
        assert user_role.role_id == role.id
        assert user_role.organization_id == org.id
        assert user_role.is_active is True
        assert user_role.is_primary is True
        assert user_role.is_valid is True

    def test_user_role_expiration(self, db_session: Session):
        """Test user role expiration."""
        # Create prerequisites
        user = User(email="expire@example.com", full_name="Expire User")
        role = Role(code="expire.role", name="Expire Role")
        org = Organization(code="EXP001", name="Expire Org")
        db_session.add_all([user, role, org])
        db_session.commit()

        # Create expired role
        past_date = datetime.utcnow() - timedelta(days=1)
        expired_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            organization_id=org.id,
            expires_at=past_date,
        )
        db_session.add(expired_role)
        
        # Create future role
        future_date = datetime.utcnow() + timedelta(days=30)
        future_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            organization_id=org.id,
            expires_at=future_date,
        )
        db_session.add(future_role)
        db_session.commit()

        assert expired_role.is_expired is True
        assert expired_role.is_valid is False
        assert future_role.is_expired is False
        assert future_role.is_valid is True
        assert future_role.days_until_expiry == 29 or future_role.days_until_expiry == 30

    def test_user_role_validity(self, db_session: Session):
        """Test user role validity checks."""
        # Create prerequisites
        user = User(email="valid@example.com", full_name="Valid User")
        role = Role(code="valid.role", name="Valid Role")
        org = Organization(code="VAL001", name="Valid Org")
        db_session.add_all([user, role, org])
        db_session.commit()

        # Test various validity scenarios
        now = datetime.utcnow()
        
        # Not yet valid
        future_valid = UserRole(
            user_id=user.id,
            role_id=role.id,
            organization_id=org.id,
            valid_from=now + timedelta(days=1),
        )
        db_session.add(future_valid)
        
        # Pending approval
        pending = UserRole(
            user_id=user.id,
            role_id=role.id,
            organization_id=org.id,
            approval_status="pending",
        )
        db_session.add(pending)
        
        # Inactive
        inactive = UserRole(
            user_id=user.id,
            role_id=role.id,
            organization_id=org.id,
            is_active=False,
        )
        db_session.add(inactive)
        db_session.commit()

        assert future_valid.is_valid is False
        assert pending.is_valid is False
        assert inactive.is_valid is False