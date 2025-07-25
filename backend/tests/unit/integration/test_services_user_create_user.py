"""
Test for services.user.create_user
Auto-generated by CC02 v39.0
Enhanced by Claude Code to provide functional test implementation
"""

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import NotFound, PermissionDenied
from app.schemas.user_extended import UserCreateExtended
from app.services.user import UserService
from tests.factories import (
    create_test_organization,
    create_test_role,
    create_test_user,
    create_test_user_role,
)


class TestUserServiceCreateUser:
    """Test cases for UserService.create_user method."""

    @pytest.fixture
    def service(self, db_session: Session) -> UserService:
        """Create UserService instance for testing."""
        return UserService(db_session)

    @pytest.fixture
    def test_data(self, db_session: Session):
        """Create test data for user creation tests."""
        # Create organization
        org = create_test_organization(db_session, name="Test Org", code="TEST-ORG")

        # Create roles
        admin_role = create_test_role(
            db_session, code="ORG_ADMIN", name="Organization Admin"
        )
        user_role = create_test_role(db_session, code="USER", name="Regular User")

        # Create admin user
        admin_user = create_test_user(
            db_session, email="admin@test.com", is_superuser=False
        )
        create_test_user_role(
            db_session, user=admin_user, role=admin_role, organization=org
        )

        # Create superuser
        super_user = create_test_user(
            db_session, email="superuser@test.com", is_superuser=True
        )

        # Create regular user (for permission tests)
        regular_user = create_test_user(db_session, email="regular@test.com")
        create_test_user_role(
            db_session, user=regular_user, role=user_role, organization=org
        )

        db_session.commit()

        return {
            "organization": org,
            "admin_role": admin_role,
            "user_role": user_role,
            "admin_user": admin_user,
            "super_user": super_user,
            "regular_user": regular_user,
        }

    def test_create_user_as_superuser(
        self, service: UserService, test_data, db_session: Session
    ):
        """Test successful user creation by superuser."""
        # Given
        creator = test_data["super_user"]
        organization = test_data["organization"]
        role = test_data["user_role"]

        user_data = UserCreateExtended(
            email="newuser@test.com",
            full_name="New Test User",
            phone="090-1234-5678",
            password="SecurePassword123!",
            organization_id=organization.id,
            role_ids=[role.id],
            is_active=True,
        )

        # When
        created_user = service.create_user(
            data=user_data, creator=creator, db=db_session
        )

        # Then
        assert created_user.email == "newuser@test.com"
        assert created_user.full_name == "New Test User"
        assert created_user.phone == "090-1234-5678"
        assert created_user.is_active is True
        assert created_user.created_by == creator.id
        assert len(created_user.user_roles) == 1
        assert created_user.user_roles[0].organization_id == organization.id
        assert created_user.user_roles[0].role_id == role.id

    def test_create_user_as_org_admin(
        self, service: UserService, test_data, db_session: Session
    ):
        """Test successful user creation by organization admin."""
        # Given
        creator = test_data["admin_user"]
        organization = test_data["organization"]
        role = test_data["user_role"]

        user_data = UserCreateExtended(
            email="orguser@test.com",
            full_name="Org User",
            password="OrgPassword123!",
            organization_id=organization.id,
            role_ids=[role.id],
        )

        # When
        created_user = service.create_user(
            data=user_data, creator=creator, db=db_session
        )

        # Then
        assert created_user.email == "orguser@test.com"
        assert created_user.created_by == creator.id
        assert len(created_user.user_roles) == 1
        assert created_user.user_roles[0].organization_id == organization.id

    def test_create_user_permission_denied_wrong_org(
        self, service: UserService, test_data, db_session: Session
    ):
        """Test permission denied when org admin tries to create user in different org."""
        # Given
        creator = test_data["admin_user"]
        other_org = create_test_organization(
            db_session, name="Other Org", code="OTHER-ORG"
        )
        role = test_data["user_role"]
        db_session.commit()

        user_data = UserCreateExtended(
            email="crossorg@test.com",
            full_name="Cross Org User",
            password="CrossPassword123!",
            organization_id=other_org.id,  # Different organization
            role_ids=[role.id],
        )

        # When/Then
        with pytest.raises(PermissionDenied, match="組織へのアクセス権限がありません"):
            service.create_user(data=user_data, creator=creator, db=db_session)

    def test_create_user_permission_denied_no_admin_role(
        self, service: UserService, test_data, db_session: Session
    ):
        """Test permission denied when user has no admin role."""
        # Given
        creator = test_data["regular_user"]
        organization = test_data["organization"]
        role = test_data["user_role"]

        user_data = UserCreateExtended(
            email="denied@test.com",
            full_name="Denied User",
            password="DeniedPassword123!",
            organization_id=organization.id,
            role_ids=[role.id],
        )

        # When/Then
        with pytest.raises(PermissionDenied, match="組織管理者権限が必要です"):
            service.create_user(data=user_data, creator=creator, db=db_session)

    def test_create_user_organization_not_found(
        self, service: UserService, test_data, db_session: Session
    ):
        """Test error when organization doesn't exist."""
        # Given
        creator = test_data["super_user"]
        role = test_data["user_role"]

        user_data = UserCreateExtended(
            email="noorg@test.com",
            full_name="No Org User",
            password="NoOrgPassword123!",
            organization_id=999999,  # Non-existent organization
            role_ids=[role.id],
        )

        # When/Then
        with pytest.raises(NotFound, match="組織が見つかりません"):
            service.create_user(data=user_data, creator=creator, db=db_session)

    def test_create_user_with_department(
        self, service: UserService, test_data, db_session: Session
    ):
        """Test user creation with department assignment."""
        # Given
        from tests.factories import create_test_department

        creator = test_data["super_user"]
        organization = test_data["organization"]
        role = test_data["user_role"]
        department = create_test_department(
            db_session, organization=organization, name="IT Department"
        )
        db_session.commit()

        user_data = UserCreateExtended(
            email="deptuser@test.com",
            full_name="Department User",
            password="DeptPassword123!",
            organization_id=organization.id,
            department_id=department.id,
            role_ids=[role.id],
        )

        # When
        created_user = service.create_user(
            data=user_data, creator=creator, db=db_session
        )

        # Then
        assert created_user.email == "deptuser@test.com"
        assert len(created_user.user_roles) == 1
        assert created_user.user_roles[0].department_id == department.id

    def test_create_user_invalid_department(
        self, service: UserService, test_data, db_session: Session
    ):
        """Test error when department doesn't exist in organization."""
        # Given
        creator = test_data["super_user"]
        organization = test_data["organization"]
        role = test_data["user_role"]

        user_data = UserCreateExtended(
            email="invaliddept@test.com",
            full_name="Invalid Dept User",
            password="InvalidPassword123!",
            organization_id=organization.id,
            department_id=999999,  # Non-existent department
            role_ids=[role.id],
        )

        # When/Then
        with pytest.raises(NotFound, match="部門が見つかりません"):
            service.create_user(data=user_data, creator=creator, db=db_session)


def test_create_user():
    """Legacy test function - kept for compatibility."""
    # This test is now covered by the class-based tests above
    assert True


def test_create_user_error_handling():
    """Legacy test function - kept for compatibility."""
    # Error handling is now covered by the class-based tests above
    assert True
