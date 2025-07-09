"""Basic integration tests for Role Service."""

import pytest
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.role import Role
from app.models.user import User
from app.schemas.role import RoleCreate
from app.services.role import RoleService


class TestRoleServiceBasic:
    """Basic tests for Role Service functionality."""

    @pytest.fixture
    def test_organization(self, db_session: Session) -> Organization:
        """Create test organization."""
        org = Organization.create(
            db=db_session,
            code="TEST_ORG",
            name="Test Organization",
            created_by=1,
        )
        db_session.commit()
        return org

    def test_create_role_as_superuser(
        self,
        db_session: Session,
        test_admin: User,
        test_organization: Organization,
    ) -> None:
        """Test creating a role as superuser."""
        # Given: Role service and role data
        service = RoleService()
        role_data = RoleCreate(
            code="TEST_ROLE",
            name="Test Role",
            description="Test role for integration testing",
            permissions=["read:test", "write:test"],
        )
        
        # When: Creating role as superuser
        role = service.create_role(
            data=role_data,
            user=test_admin,
            db=db_session,
            organization_id=test_organization.id,
        )
        
        # Then: Role should be created successfully
        assert role.code == "TEST_ROLE"
        assert role.name == "Test Role"
        assert role.permissions == ["read:test", "write:test"]
        assert role.created_by == test_admin.id

    def test_assign_role_to_user(
        self,
        db_session: Session,
        test_admin: User,
        test_user: User,
        test_organization: Organization,
    ) -> None:
        """Test assigning a role to a user."""
        # Given: Create a role first
        service = RoleService()
        role_data = RoleCreate(
            code="MEMBER_ROLE",
            name="Member Role",
            permissions=["read:own", "write:own"],
        )
        
        role = service.create_role(
            data=role_data,
            user=test_admin,
            db=db_session,
        )
        db_session.commit()
        
        # When: Assigning role to user
        user_role = service.assign_role_to_user(
            user_id=test_user.id,
            role_id=role.id,
            organization_id=test_organization.id,
            assigner=test_admin,
            db=db_session,
        )
        
        # Then: Role should be assigned
        assert user_role.user_id == test_user.id
        assert user_role.role_id == role.id
        assert user_role.organization_id == test_organization.id
        assert user_role.assigned_by == test_admin.id

    def test_get_user_roles(
        self,
        db_session: Session,
        test_admin: User,
        test_user: User,
        test_organization: Organization,
    ) -> None:
        """Test getting user roles."""
        # Given: Create and assign a role
        service = RoleService()
        role_data = RoleCreate(
            code="VIEWER_ROLE",
            name="Viewer Role",
            permissions=["read:public"],
        )
        
        role = service.create_role(
            data=role_data,
            user=test_admin,
            db=db_session,
        )
        db_session.commit()
        
        service.assign_role_to_user(
            user_id=test_user.id,
            role_id=role.id,
            organization_id=test_organization.id,
            assigner=test_admin,
            db=db_session,
        )
        db_session.commit()
        
        # When: Getting user roles
        user_roles = service.get_user_roles(
            user_id=test_user.id,
            requester=test_admin,
            db=db_session,
            organization_id=test_organization.id,
        )
        
        # Then: Should return the assigned role
        assert len(user_roles) == 1
        assert user_roles[0].role_id == role.id

    def test_check_user_permission(
        self,
        db_session: Session,
        test_admin: User,
        test_user: User,
        test_organization: Organization,
    ) -> None:
        """Test checking user permissions."""
        # Given: Create role with specific permissions
        service = RoleService()
        role_data = RoleCreate(
            code="EDITOR_ROLE",
            name="Editor Role",
            permissions=["read:articles", "write:articles", "delete:own_articles"],
        )
        
        role = service.create_role(
            data=role_data,
            user=test_admin,
            db=db_session,
        )
        db_session.commit()
        
        # Assign role to user
        service.assign_role_to_user(
            user_id=test_user.id,
            role_id=role.id,
            organization_id=test_organization.id,
            assigner=test_admin,
            db=db_session,
        )
        db_session.commit()
        
        # When: Checking permissions
        has_read = service.check_user_permission(
            user_id=test_user.id,
            permission="read:articles",
            requester=test_admin,
            db=db_session,
            organization_id=test_organization.id,
        )
        
        has_admin = service.check_user_permission(
            user_id=test_user.id,
            permission="admin:system",
            requester=test_admin,
            db=db_session,
            organization_id=test_organization.id,
        )
        
        # Then: Should have assigned permissions but not admin
        assert has_read is True
        assert has_admin is False