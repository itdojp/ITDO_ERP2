"""Unit tests for Role Service."""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import NotFound, PermissionDenied
from app.models.organization import Organization
from app.models.role import Role, UserRole
from app.models.user import User
from app.schemas.role import RoleCreate, RoleUpdate
from app.services.role import RoleService


class TestRoleService:
    """Test Role Service functionality."""

    @pytest.fixture
    def role_service(self):
        """Create role service instance."""
        return RoleService()

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
    def test_role(self, db_session: Session, test_admin: User):
        """Create test role."""
        role = Role(
            code="TEST_ROLE",
            name="Test Role",
            description="Test role description",
            permissions={"read:test": True, "write:test": True},
            created_by=test_admin.id,
        )
        db_session.add(role)
        db_session.commit()
        db_session.refresh(role)
        return role

    def test_create_role_success(
        self,
        role_service: RoleService,
        db_session: Session,
        test_admin: User,
        test_organization: Organization,
    ):
        """Test successful role creation."""
        # Given: Role creation data
        role_data = RoleCreate(
            code="NEW_ROLE",
            name="New Role",
            description="New role description",
            permissions=["read:new", "write:new"],
        )

        # When: Creating role
        role = role_service.create_role(
            data=role_data,
            user=test_admin,
            db=db_session,
            organization_id=test_organization.id,
        )

        # Then: Role should be created
        assert role.code == "NEW_ROLE"
        assert role.name == "New Role"
        assert role.description == "New role description"
        assert role.permissions == {"read:new": True, "write:new": True}
        assert role.created_by == test_admin.id
        assert not role.is_system

    def test_create_role_permission_denied(
        self,
        role_service: RoleService,
        db_session: Session,
        test_user: User,
        test_organization: Organization,
    ):
        """Test role creation with insufficient permissions."""
        # Given: Role creation data and non-admin user
        role_data = RoleCreate(
            code="DENIED_ROLE",
            name="Denied Role",
            permissions=["read:denied"],
        )

        # When/Then: Creating role should raise PermissionDenied
        with pytest.raises(PermissionDenied):
            role_service.create_role(
                data=role_data,
                user=test_user,
                db=db_session,
                organization_id=test_organization.id,
            )

    def test_create_role_duplicate_code(
        self,
        role_service: RoleService,
        db_session: Session,
        test_admin: User,
        test_role: Role,
        test_organization: Organization,
    ):
        """Test role creation with duplicate code."""
        # Given: Role creation data with existing code
        role_data = RoleCreate(
            code=test_role.code,
            name="Duplicate Role",
            permissions=["read:duplicate"],
        )

        # When/Then: Creating role should raise ValueError
        with pytest.raises(ValueError, match="既に存在します"):
            role_service.create_role(
                data=role_data,
                user=test_admin,
                db=db_session,
                organization_id=test_organization.id,
            )

    def test_assign_role_to_user_success(
        self,
        role_service: RoleService,
        db_session: Session,
        test_admin: User,
        test_user: User,
        test_role: Role,
        test_organization: Organization,
    ):
        """Test successful role assignment."""
        # Given: User and role
        expires_at = datetime.utcnow() + timedelta(days=30)

        # When: Assigning role to user
        user_role = role_service.assign_role_to_user(
            user_id=test_user.id,
            role_id=test_role.id,
            organization_id=test_organization.id,
            assigner=test_admin,
            db=db_session,
            expires_at=expires_at,
        )

        # Then: Role should be assigned
        assert user_role.user_id == test_user.id
        assert user_role.role_id == test_role.id
        assert user_role.organization_id == test_organization.id
        assert user_role.assigned_by == test_admin.id
        assert user_role.expires_at == expires_at

    def test_assign_role_user_not_found(
        self,
        role_service: RoleService,
        db_session: Session,
        test_admin: User,
        test_role: Role,
        test_organization: Organization,
    ):
        """Test role assignment to non-existent user."""
        # When/Then: Assigning role to non-existent user should raise NotFound
        with pytest.raises(NotFound, match="ユーザーが見つかりません"):
            role_service.assign_role_to_user(
                user_id=99999,
                role_id=test_role.id,
                organization_id=test_organization.id,
                assigner=test_admin,
                db=db_session,
            )

    def test_assign_role_permission_denied(
        self,
        role_service: RoleService,
        db_session: Session,
        test_user: User,
        test_role: Role,
        test_organization: Organization,
    ):
        """Test role assignment with insufficient permissions."""
        # Given: Non-admin user trying to assign role
        another_user = User.create(
            db_session,
            email="another@example.com",
            password="Password123!",
            full_name="Another User",
        )
        db_session.commit()

        # When/Then: Assigning role should raise PermissionDenied
        with pytest.raises(PermissionDenied, match="ロール割り当て権限がありません"):
            role_service.assign_role_to_user(
                user_id=another_user.id,
                role_id=test_role.id,
                organization_id=test_organization.id,
                assigner=test_user,
                db=db_session,
            )

    def test_get_user_roles_success(
        self,
        role_service: RoleService,
        db_session: Session,
        test_admin: User,
        test_user: User,
        test_role: Role,
        test_organization: Organization,
    ):
        """Test getting user roles."""
        # Given: User with assigned role
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
        )
        db_session.add(user_role)
        db_session.commit()

        # When: Getting user roles
        roles = role_service.get_user_roles(
            user_id=test_user.id,
            requester=test_admin,
            db=db_session,
            organization_id=test_organization.id,
        )

        # Then: Should return user roles
        assert len(roles) == 1
        assert roles[0].user_id == test_user.id
        assert roles[0].role_id == test_role.id
        assert roles[0].organization_id == test_organization.id

    def test_get_user_roles_user_not_found(
        self,
        role_service: RoleService,
        db_session: Session,
        test_admin: User,
        test_organization: Organization,
    ):
        """Test getting roles for non-existent user."""
        # When/Then: Getting roles for non-existent user should raise NotFound
        with pytest.raises(NotFound, match="ユーザーが見つかりません"):
            role_service.get_user_roles(
                user_id=99999,
                requester=test_admin,
                db=db_session,
                organization_id=test_organization.id,
            )

    def test_get_user_roles_permission_denied(
        self,
        role_service: RoleService,
        db_session: Session,
        test_user: User,
        test_organization: Organization,
    ):
        """Test getting user roles with insufficient permissions."""
        # Given: Non-admin user trying to get another user's roles
        another_user = User.create(
            db_session,
            email="another@example.com",
            password="Password123!",
            full_name="Another User",
        )
        db_session.commit()

        # When/Then: Getting roles should raise PermissionDenied
        with pytest.raises(PermissionDenied, match="ロール情報の閲覧権限がありません"):
            role_service.get_user_roles(
                user_id=another_user.id,
                requester=test_user,
                db=db_session,
                organization_id=test_organization.id,
            )

    def test_remove_role_from_user_success(
        self,
        role_service: RoleService,
        db_session: Session,
        test_admin: User,
        test_user: User,
        test_role: Role,
        test_organization: Organization,
    ):
        """Test successful role removal."""
        # Given: User with assigned role
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
        )
        db_session.add(user_role)
        db_session.commit()

        # When: Removing role from user
        result = role_service.remove_role_from_user(
            user_id=test_user.id,
            role_id=test_role.id,
            organization_id=test_organization.id,
            remover=test_admin,
            db=db_session,
        )

        # Then: Role should be removed
        assert result is True

        # Verify role is actually removed
        user_role = (
            db_session.query(UserRole)
            .filter(
                UserRole.user_id == test_user.id,
                UserRole.role_id == test_role.id,
                UserRole.organization_id == test_organization.id,
            )
            .first()
        )
        assert user_role is None

    def test_remove_role_from_user_not_found(
        self,
        role_service: RoleService,
        db_session: Session,
        test_admin: User,
        test_user: User,
        test_role: Role,
        test_organization: Organization,
    ):
        """Test removing non-existent role assignment."""
        # When: Removing non-existent role assignment
        result = role_service.remove_role_from_user(
            user_id=test_user.id,
            role_id=test_role.id,
            organization_id=test_organization.id,
            remover=test_admin,
            db=db_session,
        )

        # Then: Should return False
        assert result is False

    def test_get_role_permissions_success(
        self,
        role_service: RoleService,
        db_session: Session,
        test_admin: User,
        test_role: Role,
        test_organization: Organization,
    ):
        """Test getting role permissions."""
        # When: Getting role permissions
        permissions = role_service.get_role_permissions(
            role_id=test_role.id,
            requester=test_admin,
            db=db_session,
            organization_id=test_organization.id,
        )

        # Then: Should return role permissions
        assert permissions == ["read:test", "write:test"]

    def test_get_role_permissions_role_not_found(
        self,
        role_service: RoleService,
        db_session: Session,
        test_admin: User,
        test_organization: Organization,
    ):
        """Test getting permissions for non-existent role."""
        # When/Then: Getting permissions for non-existent role should raise NotFound
        with pytest.raises(NotFound, match="ロールが見つかりません"):
            role_service.get_role_permissions(
                role_id=99999,
                requester=test_admin,
                db=db_session,
                organization_id=test_organization.id,
            )

    def test_update_role_permissions_success(
        self,
        role_service: RoleService,
        db_session: Session,
        test_admin: User,
        test_role: Role,
        test_organization: Organization,
    ):
        """Test updating role permissions."""
        # Given: New permissions
        new_permissions = ["read:updated", "write:updated", "admin:updated"]

        # When: Updating role permissions
        updated_role = role_service.update_role_permissions(
            role_id=test_role.id,
            permissions=new_permissions,
            updater=test_admin,
            db=db_session,
            organization_id=test_organization.id,
        )

        # Then: Permissions should be updated
        assert updated_role.permissions == new_permissions
        assert updated_role.updated_by == test_admin.id

    def test_update_role_permissions_system_role(
        self,
        role_service: RoleService,
        db_session: Session,
        test_admin: User,
        test_organization: Organization,
    ):
        """Test updating permissions for system role."""
        # Given: System role
        system_role = Role(
            code="SYSTEM_ROLE",
            name="System Role",
            permissions={"*": True},
            is_system=True,
            created_by=test_admin.id,
        )
        db_session.add(system_role)
        db_session.commit()
        db_session.refresh(system_role)

        # When/Then: Updating system role permissions should raise PermissionDenied
        with pytest.raises(
            PermissionDenied, match="システムロールの権限は変更できません"
        ):
            role_service.update_role_permissions(
                role_id=system_role.id,
                permissions=["read:only"],
                updater=test_admin,
                db=db_session,
                organization_id=test_organization.id,
            )

    def test_check_user_permission_success(
        self,
        role_service: RoleService,
        db_session: Session,
        test_admin: User,
        test_user: User,
        test_role: Role,
        test_organization: Organization,
    ):
        """Test checking user permission."""
        # Given: User with role that has specific permission
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
        )
        db_session.add(user_role)
        db_session.commit()

        # Mock the user.has_permission method
        test_user.has_permission = Mock(return_value=True)

        # When: Checking user permission
        has_permission = role_service.check_user_permission(
            user_id=test_user.id,
            permission="read:test",
            organization_id=test_organization.id,
            requester=test_admin,
            db=db_session,
        )

        # Then: Should return True
        assert has_permission is True
        test_user.has_permission.assert_called_once_with(
            "read:test", test_organization.id
        )

    def test_get_users_with_role_success(
        self,
        role_service: RoleService,
        db_session: Session,
        test_admin: User,
        test_user: User,
        test_role: Role,
        test_organization: Organization,
    ):
        """Test getting users with specific role."""
        # Given: User with assigned role
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
        )
        db_session.add(user_role)
        db_session.commit()

        # When: Getting users with role
        users = role_service.get_users_with_role(
            role_id=test_role.id,
            organization_id=test_organization.id,
            requester=test_admin,
            db=db_session,
        )

        # Then: Should return users with the role
        assert len(users) == 1
        assert users[0].id == test_user.id

    def test_get_users_with_role_expired_excluded(
        self,
        role_service: RoleService,
        db_session: Session,
        test_admin: User,
        test_user: User,
        test_role: Role,
        test_organization: Organization,
    ):
        """Test getting users with role excludes expired assignments."""
        # Given: User with expired role assignment
        expired_date = datetime.utcnow() - timedelta(days=1)
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
            expires_at=expired_date,
        )
        db_session.add(user_role)
        db_session.commit()

        # When: Getting users with role (excluding expired)
        users = role_service.get_users_with_role(
            role_id=test_role.id,
            organization_id=test_organization.id,
            requester=test_admin,
            db=db_session,
            include_expired=False,
        )

        # Then: Should return no users
        assert len(users) == 0

    def test_get_roles_success(
        self,
        role_service: RoleService,
        db_session: Session,
        test_admin: User,
        test_role: Role,
        test_organization: Organization,
    ):
        """Test getting roles with pagination."""
        # When: Getting roles
        result = role_service.get_roles(
            requester=test_admin,
            db=db_session,
            organization_id=test_organization.id,
            page=1,
            limit=10,
        )

        # Then: Should return roles
        assert result.total > 0
        assert len(result.items) > 0
        assert result.page == 1
        assert result.limit == 10

    def test_get_role_by_id_success(
        self,
        role_service: RoleService,
        db_session: Session,
        test_admin: User,
        test_role: Role,
        test_organization: Organization,
    ):
        """Test getting role by ID."""
        # When: Getting role by ID
        role = role_service.get_role_by_id(
            role_id=test_role.id,
            requester=test_admin,
            db=db_session,
            organization_id=test_organization.id,
        )

        # Then: Should return the role
        assert role.id == test_role.id
        assert role.code == test_role.code
        assert role.name == test_role.name

    def test_update_role_success(
        self,
        role_service: RoleService,
        db_session: Session,
        test_admin: User,
        test_role: Role,
        test_organization: Organization,
    ):
        """Test updating role."""
        # Given: Role update data
        update_data = RoleUpdate(
            name="Updated Role Name",
            description="Updated description",
            permissions=["read:updated", "write:updated"],
        )

        # When: Updating role
        updated_role = role_service.update_role(
            role_id=test_role.id,
            data=update_data,
            updater=test_admin,
            db=db_session,
            organization_id=test_organization.id,
        )

        # Then: Role should be updated
        assert updated_role.name == "Updated Role Name"
        assert updated_role.description == "Updated description"
        assert updated_role.permissions == ["read:updated", "write:updated"]
        assert updated_role.updated_by == test_admin.id

    def test_update_role_system_role(
        self,
        role_service: RoleService,
        db_session: Session,
        test_admin: User,
        test_organization: Organization,
    ):
        """Test updating system role."""
        # Given: System role
        system_role = Role(
            code="SYSTEM_ROLE",
            name="System Role",
            permissions={"*": True},
            is_system=True,
            created_by=test_admin.id,
        )
        db_session.add(system_role)
        db_session.commit()
        db_session.refresh(system_role)

        update_data = RoleUpdate(name="Updated System Role")

        # When/Then: Updating system role should raise PermissionDenied
        with pytest.raises(PermissionDenied, match="システムロールは変更できません"):
            role_service.update_role(
                role_id=system_role.id,
                data=update_data,
                updater=test_admin,
                db=db_session,
                organization_id=test_organization.id,
            )

    def test_delete_role_success(
        self,
        role_service: RoleService,
        db_session: Session,
        test_admin: User,
        test_role: Role,
        test_organization: Organization,
    ):
        """Test deleting role."""
        # When: Deleting role
        result = role_service.delete_role(
            role_id=test_role.id,
            deleter=test_admin,
            db=db_session,
            organization_id=test_organization.id,
        )

        # Then: Role should be deleted
        assert result is True

        # Verify role is soft deleted
        db_session.refresh(test_role)
        assert test_role.is_active is False

    def test_delete_role_with_active_assignments(
        self,
        role_service: RoleService,
        db_session: Session,
        test_admin: User,
        test_user: User,
        test_role: Role,
        test_organization: Organization,
    ):
        """Test deleting role with active assignments."""
        # Given: Role with active assignment
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_role.id,
            organization_id=test_organization.id,
            assigned_by=test_admin.id,
        )
        db_session.add(user_role)
        db_session.commit()

        # When/Then: Deleting role with active assignments should raise ValueError
        with pytest.raises(
            ValueError, match="現在ユーザーに割り当てられているため削除できません"
        ):
            role_service.delete_role(
                role_id=test_role.id,
                deleter=test_admin,
                db=db_session,
                organization_id=test_organization.id,
            )

    def test_delete_role_system_role(
        self,
        role_service: RoleService,
        db_session: Session,
        test_admin: User,
        test_organization: Organization,
    ):
        """Test deleting system role."""
        # Given: System role
        system_role = Role(
            code="SYSTEM_ROLE",
            name="System Role",
            permissions={"*": True},
            is_system=True,
            created_by=test_admin.id,
        )
        db_session.add(system_role)
        db_session.commit()
        db_session.refresh(system_role)

        # When/Then: Deleting system role should raise PermissionDenied
        with pytest.raises(PermissionDenied, match="システムロールは削除できません"):
            role_service.delete_role(
                role_id=system_role.id,
                deleter=test_admin,
                db=db_session,
                organization_id=test_organization.id,
            )
