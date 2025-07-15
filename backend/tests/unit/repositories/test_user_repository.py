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
        user = UserFactory.create(db_session, email="unique@example.com")

        found_user = repository.get_by_email("unique@example.com")

        assert found_user is not None
        assert found_user.id == user.id
        assert found_user.email == "unique@example.com"

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

        # Create test users
        UserFactory.create(db_session, full_name="John Doe", email="john@example.com")
        UserFactory.create(db_session, full_name="Jane Smith", email="jane@example.com")
        UserFactory.create(db_session, full_name="Bob Johnson", email="bob@example.com")

        # Search by name
        results, count = repository.search_users(query="John")

        assert count == 2
        assert len(results) == 2
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

        # Create users with different lock states
        locked_user = UserFactory.create(
            db_session, locked_until=datetime.now(timezone.utc) + timedelta(minutes=30)
        )
        UserFactory.create(
            db_session, locked_until=datetime.now(timezone.utc) - timedelta(minutes=1)
        )
        UserFactory.create(db_session, locked_until=None)

        locked_users = repository.get_locked_users()

        assert len(locked_users) == 1
        assert locked_users[0].id == locked_user.id

    def test_get_users_with_expired_passwords(self, db_session: Session) -> None:
        """Test getting users with expired passwords."""
        repository = UserRepository(db_session)

        # Create users with different password ages
        old_password = UserFactory.create(
            db_session,
            password_changed_at=datetime.now(timezone.utc) - timedelta(days=100),
        )
        UserFactory.create(
            db_session,
            password_changed_at=datetime.now(timezone.utc) - timedelta(days=30),
        )

        expired_users = repository.get_users_with_expired_passwords(days=90)

        assert len(expired_users) == 1
        assert expired_users[0].id == old_password.id

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
        # Just verify that locked_until was set
        # (SQLite timezone issues make precise comparison unreliable)
=======
        # Handle timezone comparison properly
        now = datetime.now(timezone.utc)
        locked_until = locked_user.locked_until
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        assert locked_until > now
>>>>>>> main

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
        UserFactory.create(db_session, email="exists@example.com")

        assert repository.exists_by_email("exists@example.com") is True
        assert repository.exists_by_email("notexists@example.com") is False

    def test_get_superusers(self, db_session: Session) -> None:
        """Test getting superuser accounts."""
        repository = UserRepository(db_session)

        # Create different types of users
        superuser = UserFactory.create(db_session, is_superuser=True, is_active=True)
        UserFactory.create(db_session, is_superuser=True, is_active=False)
        UserFactory.create(db_session, is_superuser=False)

        superusers = repository.get_superusers()

        assert len(superusers) == 1
        assert superusers[0].id == superuser.id
