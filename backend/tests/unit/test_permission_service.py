"""Unit tests for Permission Service."""

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import NotFound, PermissionDenied, ValidationError
from app.models.permission import Permission, SYSTEM_PERMISSIONS
from app.models.role import Role, UserRole
from app.models.role_permission import PermissionEffect, RolePermission
from app.models.user import User
from app.models.organization import Organization
from app.models.department import Department
from app.schemas.permission import PermissionCreate, PermissionUpdate
from app.services.permission import PermissionService


class TestPermissionService:
    """Test PermissionService functionality."""

    @pytest.fixture
    def permission_service(self, db_session: Session):
        """Create permission service instance."""
        return PermissionService(db_session)

    def test_get_permission(self, permission_service: PermissionService, db_session: Session):
        """Test getting permission by ID."""
        # Create permission
        perm = Permission(code="test.perm", name="Test Permission", category="test")
        db_session.add(perm)
        db_session.commit()

        # Test get by ID
        found = permission_service.get_permission(perm.id)
        assert found is not None
        assert found.id == perm.id
        assert found.code == "test.perm"

        # Test non-existent ID
        not_found = permission_service.get_permission(999)
        assert not_found is None

    def test_get_permission_by_code(self, permission_service: PermissionService, db_session: Session):
        """Test getting permission by code."""
        # Create permission
        perm = Permission(code="code.test", name="Code Test", category="test")
        db_session.add(perm)
        db_session.commit()

        # Test get by code
        found = permission_service.get_permission_by_code("code.test")
        assert found is not None
        assert found.code == "code.test"

        # Test non-existent code
        not_found = permission_service.get_permission_by_code("non.existent")
        assert not_found is None

    def test_list_permissions(self, permission_service: PermissionService, db_session: Session):
        """Test listing permissions with filters."""
        # Create permissions
        perm1 = Permission(code="user.view", name="View Users", category="user", is_active=True)
        perm2 = Permission(code="user.create", name="Create Users", category="user", is_active=True)
        perm3 = Permission(code="admin.all", name="Admin All", category="admin", is_active=False)
        db_session.add_all([perm1, perm2, perm3])
        db_session.commit()

        # Test list all
        all_perms, total = permission_service.list_permissions()
        assert total >= 3

        # Test filter by category
        user_perms, user_total = permission_service.list_permissions(category="user")
        assert user_total == 2
        assert all(p.category == "user" for p in user_perms)

        # Test filter by active status
        active_perms, active_total = permission_service.list_permissions(is_active=True)
        assert all(p.is_active for p in active_perms)

        # Test pagination
        page1, _ = permission_service.list_permissions(skip=0, limit=1)
        assert len(page1) == 1

    def test_get_permissions_by_category(self, permission_service: PermissionService, db_session: Session):
        """Test getting permissions grouped by category."""
        # Create permissions
        perms = [
            Permission(code="user.view", name="View Users", category="user"),
            Permission(code="user.create", name="Create Users", category="user"),
            Permission(code="admin.all", name="Admin All", category="admin"),
            Permission(code="project.view", name="View Projects", category="project"),
        ]
        db_session.add_all(perms)
        db_session.commit()

        # Get grouped permissions
        grouped = permission_service.get_permissions_by_category()
        
        assert "user" in grouped
        assert len(grouped["user"]) == 2
        assert "admin" in grouped
        assert len(grouped["admin"]) == 1
        assert "project" in grouped
        assert len(grouped["project"]) == 1

    def test_create_permission(self, permission_service: PermissionService, db_session: Session):
        """Test creating a permission."""
        # Create permission data
        perm_data = PermissionCreate(
            code="custom.test",
            name="Custom Test Permission",
            category="custom",
            description="Test description",
        )

        # Create permission
        created = permission_service.create_permission(perm_data)
        assert created.id is not None
        assert created.code == "custom.test"
        assert created.name == "Custom Test Permission"
        assert created.is_system is False

        # Test duplicate code
        with pytest.raises(ValidationError) as exc_info:
            permission_service.create_permission(perm_data)
        assert "already exists" in str(exc_info.value)

    def test_update_permission(self, permission_service: PermissionService, db_session: Session):
        """Test updating a permission."""
        # Create permission
        perm = Permission(
            code="update.test",
            name="Original Name",
            category="test",
            is_system=False,
        )
        db_session.add(perm)
        db_session.commit()

        # Update permission
        update_data = PermissionUpdate(
            name="Updated Name",
            description="New description",
        )
        updated = permission_service.update_permission(perm.id, update_data)
        assert updated.name == "Updated Name"
        assert updated.description == "New description"
        assert updated.code == "update.test"  # Unchanged

        # Test updating system permission
        sys_perm = Permission(
            code="sys.test",
            name="System Permission",
            category="test",
            is_system=True,
        )
        db_session.add(sys_perm)
        db_session.commit()

        with pytest.raises(PermissionDenied) as exc_info:
            permission_service.update_permission(sys_perm.id, update_data)
        assert "Cannot modify system permissions" in str(exc_info.value)

    def test_delete_permission(self, permission_service: PermissionService, db_session: Session):
        """Test deleting a permission."""
        # Create permission
        perm = Permission(
            code="delete.test",
            name="Delete Test",
            category="test",
            is_system=False,
        )
        db_session.add(perm)
        db_session.commit()

        # Delete permission
        deleted = permission_service.delete_permission(perm.id)
        assert deleted is True

        # Verify deletion
        assert permission_service.get_permission(perm.id) is None

        # Test deleting system permission
        sys_perm = Permission(
            code="sys.delete",
            name="System Delete",
            category="test",
            is_system=True,
        )
        db_session.add(sys_perm)
        db_session.commit()

        with pytest.raises(PermissionDenied) as exc_info:
            permission_service.delete_permission(sys_perm.id)
        assert "Cannot delete system permissions" in str(exc_info.value)

    def test_initialize_system_permissions(self, permission_service: PermissionService, db_session: Session):
        """Test initializing system permissions."""
        # Initialize system permissions
        created_count = permission_service.initialize_system_permissions()
        assert created_count == len(SYSTEM_PERMISSIONS)

        # Run again - should create 0 (already exist)
        created_count2 = permission_service.initialize_system_permissions()
        assert created_count2 == 0

        # Verify some system permissions exist
        user_view = permission_service.get_permission_by_code("user.view")
        assert user_view is not None
        assert user_view.is_system is True
        assert user_view.category == "user"

    def test_get_user_permissions(self, permission_service: PermissionService, db_session: Session):
        """Test getting user permissions."""
        # Create user, role, organization
        user = User(email="perms@example.com", full_name="Perms User")
        role = Role(code="user.role", name="User Role")
        org = Organization(code="PERM001", name="Perm Org")
        db_session.add_all([user, role, org])
        db_session.commit()

        # Create permissions
        perm1 = Permission(code="test.perm1", name="Test Perm 1", category="test")
        perm2 = Permission(code="test.perm2", name="Test Perm 2", category="test")
        perm3 = Permission(code="test.perm3", name="Test Perm 3", category="test")
        db_session.add_all([perm1, perm2, perm3])
        db_session.commit()

        # Assign role to user
        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            organization_id=org.id,
            is_active=True,
        )
        db_session.add(user_role)

        # Assign permissions to role
        rp1 = RolePermission(role_id=role.id, permission_id=perm1.id)
        rp2 = RolePermission(role_id=role.id, permission_id=perm2.id)
        db_session.add_all([rp1, rp2])
        db_session.commit()

        # Get user permissions
        perms = permission_service.get_user_permissions(user.id, org.id)
        assert "test.perm1" in perms
        assert "test.perm2" in perms
        assert "test.perm3" not in perms

        # Test superuser
        superuser = User(email="super@example.com", full_name="Super User", is_superuser=True)
        db_session.add(superuser)
        db_session.commit()

        super_perms = permission_service.get_user_permissions(superuser.id)
        assert len(super_perms) >= 3  # Has all permissions

    def test_check_user_permission(self, permission_service: PermissionService, db_session: Session):
        """Test checking user permission."""
        # Create user with permission
        user = User(email="check@example.com", full_name="Check User")
        role = Role(code="check.role", name="Check Role")
        org = Organization(code="CHECK001", name="Check Org")
        perm = Permission(code="check.test", name="Check Test", category="test")
        db_session.add_all([user, role, org, perm])
        db_session.commit()

        # Set up role and permission
        user_role = UserRole(user_id=user.id, role_id=role.id, organization_id=org.id)
        role_perm = RolePermission(role_id=role.id, permission_id=perm.id)
        db_session.add_all([user_role, role_perm])
        db_session.commit()

        # Check permissions
        assert permission_service.check_user_permission(user.id, "check.test", org.id) is True
        assert permission_service.check_user_permission(user.id, "other.test", org.id) is False

    def test_assign_permission_to_role(self, permission_service: PermissionService, db_session: Session):
        """Test assigning permission to role."""
        # Create role and permission
        role = Role(code="assign.role", name="Assign Role")
        perm = Permission(code="assign.perm", name="Assign Perm", category="test")
        admin = User(email="admin@example.com", full_name="Admin")
        db_session.add_all([role, perm, admin])
        db_session.commit()

        # Assign permission
        rp = permission_service.assign_permission_to_role(
            role_id=role.id,
            permission_id=perm.id,
            granted_by=admin.id,
            effect=PermissionEffect.ALLOW,
            priority=10,
        )

        assert rp.role_id == role.id
        assert rp.permission_id == perm.id
        assert rp.granted_by == admin.id
        assert rp.effect == PermissionEffect.ALLOW.value
        assert rp.priority == 10

        # Test non-existent role
        with pytest.raises(NotFound) as exc_info:
            permission_service.assign_permission_to_role(
                role_id=999,
                permission_id=perm.id,
            )
        assert "Role 999 not found" in str(exc_info.value)

    def test_revoke_permission_from_role(self, permission_service: PermissionService, db_session: Session):
        """Test revoking permission from role."""
        # Create and assign permission
        role = Role(code="revoke.role", name="Revoke Role")
        perm = Permission(code="revoke.perm", name="Revoke Perm", category="test")
        db_session.add_all([role, perm])
        db_session.commit()

        rp = RolePermission(role_id=role.id, permission_id=perm.id)
        db_session.add(rp)
        db_session.commit()

        # Revoke permission
        revoked = permission_service.revoke_permission_from_role(role.id, perm.id)
        assert revoked is True

        # Verify revocation
        assert db_session.get(RolePermission, {"role_id": role.id, "permission_id": perm.id}) is None

        # Test revoking non-existent
        revoked2 = permission_service.revoke_permission_from_role(role.id, perm.id)
        assert revoked2 is False

    def test_get_permission_statistics(self, permission_service: PermissionService, db_session: Session):
        """Test getting permission statistics."""
        # Create permissions
        perms = [
            Permission(code="stat1", name="Stat 1", category="user", is_active=True, is_system=True),
            Permission(code="stat2", name="Stat 2", category="user", is_active=True, is_system=False),
            Permission(code="stat3", name="Stat 3", category="admin", is_active=False, is_system=False),
        ]
        db_session.add_all(perms)
        
        # Create role assignments
        role = Role(code="stat.role", name="Stat Role")
        db_session.add(role)
        db_session.commit()
        
        rp1 = RolePermission(role_id=role.id, permission_id=perms[0].id, is_active=True)
        rp2 = RolePermission(role_id=role.id, permission_id=perms[1].id, is_active=False)
        db_session.add_all([rp1, rp2])
        db_session.commit()

        # Get statistics
        stats = permission_service.get_permission_statistics()
        
        assert stats["total_permissions"] >= 3
        assert stats["active_permissions"] >= 2
        assert stats["system_permissions"] >= 1
        assert stats["custom_permissions"] >= 2
        assert "user" in stats["category_counts"]
        assert stats["category_counts"]["user"] >= 2
        assert stats["total_assignments"] >= 2
        assert stats["active_assignments"] >= 1

    def test_validate_permission_scope(self, permission_service: PermissionService, db_session: Session):
        """Test validating permission scope."""
        # Create permissions with different categories
        admin_perm = Permission(code="admin.test", name="Admin Test", category="admin")
        org_perm = Permission(code="org.test", name="Org Test", category="organization")
        dept_perm = Permission(code="dept.test", name="Dept Test", category="department")
        db_session.add_all([admin_perm, org_perm, dept_perm])
        db_session.commit()

        # Test admin permission (valid anywhere)
        assert permission_service.validate_permission_scope("admin.test") is True
        assert permission_service.validate_permission_scope("admin.test", organization_id=1) is True
        assert permission_service.validate_permission_scope("admin.test", organization_id=1, department_id=1) is True

        # Test organization permission (requires org context)
        assert permission_service.validate_permission_scope("org.test") is False
        assert permission_service.validate_permission_scope("org.test", organization_id=1) is True

        # Test department permission (requires both org and dept context)
        assert permission_service.validate_permission_scope("dept.test") is False
        assert permission_service.validate_permission_scope("dept.test", organization_id=1) is False
        assert permission_service.validate_permission_scope("dept.test", organization_id=1, department_id=1) is True

    def test_get_conflicting_permissions(self, permission_service: PermissionService, db_session: Session):
        """Test getting conflicting permissions."""
        # Create role and permissions in same category
        role = Role(code="conflict.role", name="Conflict Role")
        perm1 = Permission(code="user.view", name="View Users", category="user")
        perm2 = Permission(code="user.create", name="Create Users", category="user")
        perm3 = Permission(code="admin.view", name="View Admin", category="admin")
        db_session.add_all([role, perm1, perm2, perm3])
        db_session.commit()

        # Assign permissions
        rp1 = RolePermission(role_id=role.id, permission_id=perm1.id, effect="allow")
        rp2 = RolePermission(role_id=role.id, permission_id=perm2.id, effect="deny")
        rp3 = RolePermission(role_id=role.id, permission_id=perm3.id, effect="allow")
        db_session.add_all([rp1, rp2, rp3])
        db_session.commit()

        # Get conflicts for user.view
        conflicts = permission_service.get_conflicting_permissions(role.id, perm1.id)
        assert len(conflicts) == 1  # user.create is in same category
        assert conflicts[0].permission_id == perm2.id

        # Get conflicts for admin.view
        conflicts2 = permission_service.get_conflicting_permissions(role.id, perm3.id)
        assert len(conflicts2) == 0  # No other admin permissions