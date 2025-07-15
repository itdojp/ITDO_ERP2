"""Unit tests for User repository."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.role import UserRole
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate
from tests.factories import OrganizationFactory, RoleFactory, UserFactory


class TestUserRepository:
    """Test cases for UserRepository."""

    def test_create_user(self, db_session: Session) -> None:
        """Test creating a user."""
        repository = UserRepository(db_session)
        user_data = UserCreate(
            email="test@example.com", password="Test123!@#", full_name="Test User"
        )

        user = repository.create(user_data)

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.is_deleted is False

    def test_get_by_email(self, db_session: Session) -> None:
        """Test getting user by email."""
        repository = UserRepository(db_session)
        test_email = f"unique-{id(self)}-{id(db_session)}@example.com"
        user = UserFactory.create(db_session, email=test_email)

        found_user = repository.get_by_email(test_email)

        assert found_user is not None
        assert found_user.id == user.id
        assert found_user.email == test_email

    def test_get_by_email_not_found(self, db_session: Session) -> None:
        """Test getting non-existent user by email."""
        repository = UserRepository(db_session)

        found_user = repository.get_by_email("nonexistent@example.com")

        assert found_user is None

    def test_get_active(self, db_session: Session) -> None:
        """Test getting active user."""
        repository = UserRepository(db_session)
        active_user = UserFactory.create(db_session, is_active=True)
        inactive_user = UserFactory.create(db_session, is_active=False)

        found_user = repository.get_active(active_user.id)
        not_found = repository.get_active(inactive_user.id)

        assert found_user is not None
        assert found_user.id == active_user.id
        assert not_found is None

    def test_search_users(self, db_session: Session) -> None:
        """Test searching users."""
        repository = UserRepository(db_session)
        test_id = f"{id(self)}-{id(db_session)}"

        # Create test users
        UserFactory.create(
            db_session, full_name="John Doe", email=f"john-{test_id}@example.com"
        )
        UserFactory.create(
            db_session, full_name="Jane Smith", email=f"jane-{test_id}@example.com"
        )
        UserFactory.create(
            db_session, full_name="Bob Johnson", email=f"bob-{test_id}@example.com"
        )

        # Search by name
        results, count = repository.search_users(query="John")

        assert count >= 2  # May include other Johns from different tests
        user_names = [u.full_name for u in results]
        assert "John Doe" in user_names
        assert "Bob Johnson" in user_names

    def test_search_users_by_organization(self, db_session: Session) -> None:
        """Test searching users by organization."""
        repository = UserRepository(db_session)

        # Create organizations and users
        org1 = OrganizationFactory.create(db_session)
        org2 = OrganizationFactory.create(db_session)
        role = RoleFactory.create(db_session, organization_id=org1.id)

        user1 = UserFactory.create(db_session)
        user2 = UserFactory.create(db_session)

        # Assign users to organizations
        user_role1 = UserRole(
            user_id=user1.id,
            role_id=role.id,
            organization_id=org1.id,
            assigned_by=user1.id,
        )
        user_role2 = UserRole(
            user_id=user2.id,
            role_id=role.id,
            organization_id=org2.id,
            assigned_by=user2.id,
        )
        db_session.add_all([user_role1, user_role2])
        db_session.commit()

        # Search by organization
        results, count = repository.search_users(organization_id=org1.id)

        assert count == 1
        assert results[0].id == user1.id

    def test_get_locked_users(self, db_session: Session) -> None:
        """Test getting locked users."""
        repository = UserRepository(db_session)
        test_id = f"{id(self)}-{id(db_session)}"

        # Create users with different lock states
        locked_user = UserFactory.create(
            db_session,
            email=f"locked-{test_id}@test.example",
            locked_until=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
        expired_lock_user = UserFactory.create(
            db_session,
            email=f"expired-{test_id}@test.example",
            locked_until=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        normal_user = UserFactory.create(
            db_session, email=f"normal-{test_id}@test.example", locked_until=None
        )

        locked_users = repository.get_locked_users()

        # Check that our locked user is in the results
        locked_user_ids = [user.id for user in locked_users]
        assert locked_user.id in locked_user_ids

        # Verify that expired lock and normal users are not in results
        assert expired_lock_user.id not in locked_user_ids
        assert normal_user.id not in locked_user_ids

    def test_get_users_with_expired_passwords(self, db_session: Session) -> None:
        """Test getting users with expired passwords."""
        repository = UserRepository(db_session)
        test_id = f"{id(self)}-{id(db_session)}"

        # Create users with different password ages
        old_password = UserFactory.create(
            db_session,
            email=f"expired-{test_id}@test.example",
            password_changed_at=datetime.now(timezone.utc) - timedelta(days=100),
        )
        recent_password = UserFactory.create(
            db_session,
            email=f"recent-{test_id}@test.example",
            password_changed_at=datetime.now(timezone.utc) - timedelta(days=30),
        )

        expired_users = repository.get_users_with_expired_passwords(days=90)

        # Check that our expired user is in the results
        expired_user_ids = [user.id for user in expired_users]
        assert old_password.id in expired_user_ids

        # Verify that recent password user is not in results
        assert recent_password.id not in expired_user_ids

    def test_increment_failed_login(self, db_session: Session) -> None:
        """Test incrementing failed login attempts."""
        repository = UserRepository(db_session)
        user = UserFactory.create(db_session, failed_login_attempts=0)

        # First failed attempt
        updated_user = repository.increment_failed_login(user.email)
        assert updated_user is not None
        assert updated_user.failed_login_attempts == 1
        assert updated_user.locked_until is None

        # Lock after 5 attempts
        for _ in range(4):
            repository.increment_failed_login(user.email)

        locked_user = repository.get(user.id)
        assert locked_user is not None
        assert locked_user.failed_login_attempts == 5
        assert locked_user.locked_until is not None
<<<<<<< HEAD
        # Handle timezone comparison properly
        now = datetime.now(timezone.utc)
        locked_until = locked_user.locked_until
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        assert locked_until > now
=======
>>>>>>> main

        # Handle timezone comparison properly
        now = datetime.now(timezone.utc)
        locked_until = locked_user.locked_until
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        assert locked_until > now
    def test_reset_failed_login(self, db_session: Session) -> None:
        """Test resetting failed login attempts."""
        repository = UserRepository(db_session)
        user = UserFactory.create(
            db_session,
            failed_login_attempts=5,
            locked_until=datetime.now(timezone.utc) + timedelta(minutes=30),
        )

        repository.reset_failed_login(user.id)

        updated_user = repository.get(user.id)
        assert updated_user is not None
        assert updated_user.failed_login_attempts == 0
        assert updated_user.locked_until is None

    def test_exists_by_email(self, db_session: Session) -> None:
        """Test checking if user exists by email."""
        repository = UserRepository(db_session)
        test_id = f"{id(self)}-{id(db_session)}"
        test_email = f"exists-{test_id}@example.com"
        UserFactory.create(db_session, email=test_email)

        assert repository.exists_by_email(test_email) is True
        assert repository.exists_by_email(f"notexists-{test_id}@example.com") is False

    def test_get_superusers(self, db_session: Session) -> None:
        """Test getting superuser accounts."""
        repository = UserRepository(db_session)
        test_id = f"{id(self)}-{id(db_session)}"

        # Create different types of users
        active_superuser = UserFactory.create(
            db_session,
            email=f"superuser-{test_id}@test.example",
            is_superuser=True,
            is_active=True,
        )
        inactive_superuser = UserFactory.create(
            db_session,
            email=f"inactive.superuser-{test_id}@test.example",
            is_superuser=True,
            is_active=False,
        )
        regular_user = UserFactory.create(
            db_session, email=f"regular-{test_id}@test.example", is_superuser=False
        )

        superusers = repository.get_superusers()

        # Check that our active superuser is in the results
        superuser_ids = [user.id for user in superusers]
        assert active_superuser.id in superuser_ids

        # Verify that inactive superuser and regular user are not in results
        assert inactive_superuser.id not in superuser_ids
        assert regular_user.id not in superuser_ids
