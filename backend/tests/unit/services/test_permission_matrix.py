"""Unit tests for Permission Matrix."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.role import Role, UserRole
from app.models.user import User
from app.services.permission_matrix import (
    PermissionLevel,
    PermissionMatrix,
    check_permission,
    get_permission_level,
    get_user_permissions,
)


class TestPermissionMatrix:
    """Test Permission Matrix functionality."""

    @pytest.fixture
    def permission_matrix(self):
        """Create permission matrix instance."""
        return PermissionMatrix()

    @pytest.fixture
    def test_organization(self, db_session: Session):
        """Create test organization."""
        org = Organization.create(
            db=db_session,
            code="TEST_ORG",
            name="Test Organization",
            created_by=1,
        )
        db_session.commit()
        return org

    @pytest.fixture
    def admin_role(self, db_session: Session, test_admin: User):
        """Create admin role."""
        role = Role.create(
            db=db_session,
            code="ADMIN_ROLE",
            name="Admin Role",
            permissions=["*"],
            created_by=test_admin.id,
        )
        db_session.commit()
        return role

    @pytest.fixture
    def manager_role(self, db_session: Session, test_admin: User):
        """Create manager role."""
        role = Role.create(
            db=db_session,
            code="MANAGER",
            name="Manager Role",
            permissions=["read:*", "write:team"],
            created_by=test_admin.id,
        )
        db_session.commit()
        return role

    @pytest.fixture
    def member_role(self, db_session: Session, test_admin: User):
        """Create member role."""
        role = Role.create(
            db=db_session,
            code="MEMBER",
            name="Member Role",
            permissions=["read:own", "write:own"],
            created_by=test_admin.id,
        )
        db_session.commit()
        return role

    def test_permission_hierarchy_order(self, permission_matrix: PermissionMatrix):
        """Test that permission hierarchy is correctly ordered."""
        # Given: Permission hierarchy
        hierarchy = permission_matrix.PERMISSION_HIERARCHY

        # Then: Should be in correct order
        assert hierarchy[0] == PermissionLevel.VIEWER
        assert hierarchy[1] == PermissionLevel.MEMBER
        assert hierarchy[2] == PermissionLevel.MANAGER
        assert hierarchy[3] == PermissionLevel.ADMIN

    def test_get_permissions_for_level_viewer(
        self, permission_matrix: PermissionMatrix
    ):
        """Test getting permissions for viewer level."""
        # When: Getting viewer permissions
        permissions = permission_matrix.get_permissions_for_level(
            PermissionLevel.VIEWER
        )

        # Then: Should contain only viewer permissions
        assert "read:own_profile" in permissions
        assert "read:organization_basic" in permissions
        assert "read:department_basic" in permissions
        assert "read:public_announcements" in permissions

        # Should not contain higher level permissions
        assert "write:own_profile" not in permissions
        assert "admin:system" not in permissions

    def test_get_permissions_for_level_member(
        self, permission_matrix: PermissionMatrix
    ):
        """Test getting permissions for member level."""
        # When: Getting member permissions
        permissions = permission_matrix.get_permissions_for_level(
            PermissionLevel.MEMBER
        )

        # Then: Should contain viewer + member permissions
        # Viewer permissions
        assert "read:own_profile" in permissions
        assert "read:organization_basic" in permissions

        # Member permissions
        assert "write:own_profile" in permissions
        assert "write:own_timesheet" in permissions
        assert "read:team_members" in permissions

        # Should not contain higher level permissions
        assert "admin:system" not in permissions
        assert "write:all_organizations" not in permissions

    def test_get_permissions_for_level_manager(
        self, permission_matrix: PermissionMatrix
    ):
        """Test getting permissions for manager level."""
        # When: Getting manager permissions
        permissions = permission_matrix.get_permissions_for_level(
            PermissionLevel.MANAGER
        )

        # Then: Should contain viewer + member + manager permissions
        # Viewer permissions
        assert "read:own_profile" in permissions

        # Member permissions
        assert "write:own_profile" in permissions

        # Manager permissions
        assert "read:team_performance" in permissions
        assert "write:team_assignments" in permissions
        assert "read:user_profiles" in permissions

        # Should not contain admin permissions
        assert "admin:system" not in permissions

    def test_get_permissions_for_level_admin(self, permission_matrix: PermissionMatrix):
        """Test getting permissions for admin level."""
        # When: Getting admin permissions
        permissions = permission_matrix.get_permissions_for_level(PermissionLevel.ADMIN)

        # Then: Should contain all permissions
        # Viewer permissions
        assert "read:own_profile" in permissions

        # Member permissions
        assert "write:own_profile" in permissions

        # Manager permissions
        assert "read:team_performance" in permissions

        # Admin permissions
        assert "admin:system" in permissions
        assert "read:all_organizations" in permissions
        assert "write:all_organizations" in permissions

    def test_get_context_permissions_organization(
        self, permission_matrix: PermissionMatrix
    ):
        """Test getting context-specific permissions for organization."""
        # When: Getting organization context permissions for manager
        permissions = permission_matrix.get_context_permissions(
            PermissionLevel.MANAGER, "organization"
        )

        # Then: Should contain viewer + member + manager org permissions
        assert "org:read:basic" in permissions
        assert "org:read:members" in permissions
        assert "org:read:reports" in permissions
        assert "org:write:members" in permissions

        # Should not contain admin permissions
        assert "org:admin:all" not in permissions

    def test_get_context_permissions_department(
        self, permission_matrix: PermissionMatrix
    ):
        """Test getting context-specific permissions for department."""
        # When: Getting department context permissions for member
        permissions = permission_matrix.get_context_permissions(
            PermissionLevel.MEMBER, "department"
        )

        # Then: Should contain viewer + member dept permissions
        assert "dept:read:basic" in permissions
        assert "dept:read:members" in permissions
        assert "dept:read:tasks" in permissions

        # Should not contain manager permissions
        assert "dept:write:members" not in permissions
        assert "dept:admin:all" not in permissions

    def test_has_permission_base_permission(self, permission_matrix: PermissionMatrix):
        """Test checking base permission."""
        # When: Checking base permission
        has_perm = permission_matrix.has_permission(
            PermissionLevel.MEMBER, "write:own_profile"
        )

        # Then: Should return True
        assert has_perm is True

    def test_has_permission_no_permission(self, permission_matrix: PermissionMatrix):
        """Test checking permission user doesn't have."""
        # When: Checking permission user doesn't have
        has_perm = permission_matrix.has_permission(
            PermissionLevel.VIEWER, "admin:system"
        )

        # Then: Should return False
        assert has_perm is False

    def test_has_permission_context_permission(
        self, permission_matrix: PermissionMatrix
    ):
        """Test checking context-specific permission."""
        # When: Checking context permission
        has_perm = permission_matrix.has_permission(
            PermissionLevel.MANAGER, "org:write:members", "organization"
        )

        # Then: Should return True
        assert has_perm is True

    def test_has_permission_wildcard(self, permission_matrix: PermissionMatrix):
        """Test wildcard permission checking."""
        # Given: Mock permission matrix with wildcard permissions
        pm = PermissionMatrix()
        pm._permission_cache = {"admin": {"read:*", "write:*", "admin:*"}}

        # When: Checking specific permission against wildcard
        has_perm = pm.has_permission(PermissionLevel.ADMIN, "read:specific_resource")

        # Then: Should return True due to wildcard
        assert has_perm is True

    def test_get_user_effective_level_superuser(
        self,
        permission_matrix: PermissionMatrix,
        test_admin: User,
        test_organization: Organization,
    ):
        """Test getting effective level for superuser."""
        # When: Getting effective level for superuser
        level = permission_matrix.get_user_effective_level(
            test_admin, test_organization.id
        )

        # Then: Should return ADMIN
        assert level == PermissionLevel.ADMIN

    def test_get_user_effective_level_with_roles(
        self,
        permission_matrix: PermissionMatrix,
        test_user: User,
        test_organization: Organization,
        manager_role: Role,
        member_role: Role,
        db_session: Session,
        test_admin: User,
    ):
        """Test getting effective level for user with multiple roles."""
        # Given: User with multiple roles
        # Add manager role
        UserRole.create(
            db=db_session,
            user_id=test_user.id,
            role_id=manager_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
        )

        # Add member role
        UserRole.create(
            db=db_session,
            user_id=test_user.id,
            role_id=member_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
        )
        db_session.commit()

        # When: Getting effective level
        level = permission_matrix.get_user_effective_level(
            test_user, test_organization.id
        )

        # Then: Should return highest level (MANAGER)
        assert level == PermissionLevel.MANAGER

    def test_get_user_effective_level_no_roles(
        self,
        permission_matrix: PermissionMatrix,
        test_user: User,
        test_organization: Organization,
    ):
        """Test getting effective level for user with no roles."""
        # When: Getting effective level for user with no roles
        level = permission_matrix.get_user_effective_level(
            test_user, test_organization.id
        )

        # Then: Should return VIEWER (default)
        assert level == PermissionLevel.VIEWER

    def test_get_user_effective_level_expired_roles(
        self,
        permission_matrix: PermissionMatrix,
        test_user: User,
        test_organization: Organization,
        manager_role: Role,
        db_session: Session,
        test_admin: User,
    ):
        """Test getting effective level with expired roles."""
        # Given: User with expired role
        expired_date = datetime.utcnow() - timedelta(days=1)
        UserRole.create(
            db=db_session,
            user_id=test_user.id,
            role_id=manager_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
            expires_at=expired_date,
        )
        db_session.commit()

        # When: Getting effective level
        level = permission_matrix.get_user_effective_level(
            test_user, test_organization.id
        )

        # Then: Should return VIEWER (default, ignoring expired roles)
        assert level == PermissionLevel.VIEWER

    def test_check_user_permission_success(
        self,
        permission_matrix: PermissionMatrix,
        test_user: User,
        test_organization: Organization,
        manager_role: Role,
        db_session: Session,
        test_admin: User,
    ):
        """Test checking user permission successfully."""
        # Given: User with manager role
        UserRole.create(
            db=db_session,
            user_id=test_user.id,
            role_id=manager_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
        )
        db_session.commit()

        # When: Checking permission
        has_perm = permission_matrix.check_user_permission(
            test_user, "read:team_performance", test_organization.id
        )

        # Then: Should return True
        assert has_perm is True

    def test_check_user_permission_denied(
        self,
        permission_matrix: PermissionMatrix,
        test_user: User,
        test_organization: Organization,
        member_role: Role,
        db_session: Session,
        test_admin: User,
    ):
        """Test checking user permission denied."""
        # Given: User with member role
        UserRole.create(
            db=db_session,
            user_id=test_user.id,
            role_id=member_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
        )
        db_session.commit()

        # When: Checking admin permission
        has_perm = permission_matrix.check_user_permission(
            test_user, "admin:system", test_organization.id
        )

        # Then: Should return False
        assert has_perm is False

    def test_get_all_permissions(self, permission_matrix: PermissionMatrix):
        """Test getting all permissions for a level."""
        # When: Getting all permissions for manager
        all_perms = permission_matrix.get_all_permissions(PermissionLevel.MANAGER)

        # Then: Should contain base and context permissions
        assert "base" in all_perms
        assert "contexts" in all_perms
        assert "organization" in all_perms["contexts"]
        assert "department" in all_perms["contexts"]

        # Check base permissions
        assert "read:team_performance" in all_perms["base"]

        # Check context permissions
        assert "org:read:reports" in all_perms["contexts"]["organization"]
        assert "dept:write:members" in all_perms["contexts"]["department"]

    def test_validate_permission_hierarchy(self, permission_matrix: PermissionMatrix):
        """Test permission hierarchy validation."""
        # When: Validating permission hierarchy
        is_valid = permission_matrix.validate_permission_hierarchy()

        # Then: Should be valid
        assert is_valid is True

    def test_get_permission_differences(self, permission_matrix: PermissionMatrix):
        """Test getting permission differences between levels."""
        # When: Getting differences between VIEWER and MEMBER
        differences = permission_matrix.get_permission_differences(
            PermissionLevel.VIEWER, PermissionLevel.MEMBER
        )

        # Then: Should contain differences
        assert "viewer_only" in differences
        assert "member_only" in differences
        assert "common" in differences

        # Member should have additional permissions
        assert len(differences["member_only"]) > 0
        assert "write:own_profile" in differences["member_only"]

        # Common permissions should include viewer permissions
        assert "read:own_profile" in differences["common"]

    def test_generate_permission_report(self, permission_matrix: PermissionMatrix):
        """Test generating permission report."""
        # When: Generating permission report
        report = permission_matrix.generate_permission_report()

        # Then: Should contain comprehensive report
        assert "hierarchy" in report
        assert "levels" in report
        assert "validation" in report
        assert "total_permissions" in report

        # Check hierarchy
        assert report["hierarchy"] == ["viewer", "member", "manager", "admin"]

        # Check levels
        assert "viewer" in report["levels"]
        assert "admin" in report["levels"]

        # Check validation
        assert report["validation"] is True

        # Check total permissions
        assert report["total_permissions"] > 0

    def test_convenience_functions(
        self,
        test_user: User,
        test_organization: Organization,
        manager_role: Role,
        db_session: Session,
        test_admin: User,
    ):
        """Test convenience functions."""
        # Given: User with manager role
        UserRole.create(
            db=db_session,
            user_id=test_user.id,
            role_id=manager_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
        )
        db_session.commit()

        # When: Using convenience functions
        has_perm = check_permission(
            test_user, "read:team_performance", test_organization.id
        )
        user_level = get_permission_level(test_user, test_organization.id)
        user_perms = get_user_permissions(test_user, test_organization.id)

        # Then: Should work correctly
        assert has_perm is True
        assert user_level == PermissionLevel.MANAGER
        assert "base" in user_perms
        assert "contexts" in user_perms

    def test_role_level_mapping(self, permission_matrix: PermissionMatrix):
        """Test role code to permission level mapping."""
        # When: Getting permission level for different role codes
        admin_level = permission_matrix._get_role_permission_level("SYSTEM_ADMIN")
        manager_level = permission_matrix._get_role_permission_level("DEPT_MANAGER")
        member_level = permission_matrix._get_role_permission_level("USER")
        unknown_level = permission_matrix._get_role_permission_level("UNKNOWN_ROLE")

        # Then: Should map correctly
        assert admin_level == PermissionLevel.ADMIN
        assert manager_level == PermissionLevel.MANAGER
        assert member_level == PermissionLevel.MEMBER
        assert unknown_level == PermissionLevel.VIEWER  # Default

    def test_permission_inheritance(self, permission_matrix: PermissionMatrix):
        """Test that higher levels inherit permissions from lower levels."""
        # Given: Different permission levels
        viewer_perms = permission_matrix.get_permissions_for_level(
            PermissionLevel.VIEWER
        )
        member_perms = permission_matrix.get_permissions_for_level(
            PermissionLevel.MEMBER
        )
        manager_perms = permission_matrix.get_permissions_for_level(
            PermissionLevel.MANAGER
        )
        admin_perms = permission_matrix.get_permissions_for_level(PermissionLevel.ADMIN)

        # Then: Higher levels should contain all lower level permissions
        assert viewer_perms.issubset(member_perms)
        assert member_perms.issubset(manager_perms)
        assert manager_perms.issubset(admin_perms)

    def test_context_permission_inheritance(self, permission_matrix: PermissionMatrix):
        """Test that context permissions also follow inheritance."""
        # Given: Context permissions for different levels
        viewer_org_perms = permission_matrix.get_context_permissions(
            PermissionLevel.VIEWER, "organization"
        )
        member_org_perms = permission_matrix.get_context_permissions(
            PermissionLevel.MEMBER, "organization"
        )
        manager_org_perms = permission_matrix.get_context_permissions(
            PermissionLevel.MANAGER, "organization"
        )

        # Then: Higher levels should contain all lower level context permissions
        assert viewer_org_perms.issubset(member_org_perms)
        assert member_org_perms.issubset(manager_org_perms)

    def test_department_context_permissions(
        self,
        permission_matrix: PermissionMatrix,
        test_user: User,
        test_organization: Organization,
        manager_role: Role,
        db_session: Session,
        test_admin: User,
    ):
        """Test department context permissions."""
        # Given: User with manager role in specific department
        UserRole.create(
            db=db_session,
            user_id=test_user.id,
            role_id=manager_role.id,
            organization_id=test_organization.id,
            department_id=1,  # Specific department
            assigned_by=test_admin.id,
        )
        db_session.commit()

        # When: Checking department context permission
        has_perm = permission_matrix.check_user_permission(
            test_user, "dept:write:members", test_organization.id, 1, "department"
        )

        # Then: Should have permission
        assert has_perm is True
