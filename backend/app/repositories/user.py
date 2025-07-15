"""User repository with type-safe CRUD operations."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate, UserUpdate
from app.types import UserId


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """Repository for User model with specialized queries."""

    def __init__(self, db: Session):
        """Initialize repository with User model."""
        super().__init__(User, db)

    def create(self, obj_in: UserCreate) -> User:
        """Create a new user with password hashing."""
        # Extract data from schema
        obj_data = obj_in.model_dump()
        password = obj_data.pop("password")

        # Use User.create method which handles password hashing
        user = User.create(
            self.db,
            email=obj_data["email"],
            password=password,
            full_name=obj_data["full_name"],
            is_active=obj_data.get("is_active", True),
        )

        return user

    def get_by_email(self, email: str) -> User | None:
        """Get user by email address."""
        return self.db.scalar(select(User).where(User.email == email))

    def get_active(self, id: int) -> User | None:
        """Get active user by ID."""
        return self.db.scalar(
            select(User).where(and_(User.id == id, User.is_active, ~User.is_deleted))
        )

    def get_with_relationships(self, id: int) -> User | None:
        """Get user with all relationships loaded."""
        return self.db.scalar(
            select(User)
            .options(
                selectinload(User.user_roles),
                selectinload(User.password_history),
                selectinload(User.sessions),
                selectinload(User.activity_logs),
            )
            .where(User.id == id)
        )

    def search_users(
        self,
        query: str | None = None,
        organization_id: int | None = None,
        department_id: int | None = None,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[User], int]:
        """Search users with filters."""
        stmt = select(User).where(~User.is_deleted)

        # Text search
        if query:
            search_term = f"%{query}%"
            stmt = stmt.where(
                or_(
                    User.email.ilike(search_term),
                    User.full_name.ilike(search_term),
                    User.phone.ilike(search_term),
                )
            )

        # Filter by organization or department (need to handle joins properly)
        user_role_joined = False

        if organization_id is not None:
            from app.models.role import UserRole

            stmt = stmt.join(UserRole, User.id == UserRole.user_id).where(
                UserRole.organization_id == organization_id
            )
            user_role_joined = True

        if department_id is not None:
            from app.models.role import UserRole

            if not user_role_joined:
                stmt = stmt.join(UserRole, User.id == UserRole.user_id)

            stmt = stmt.where(UserRole.department_id == department_id)

        # Filter by active status
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = self.db.scalar(count_stmt) or 0

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)
        results = list(self.db.scalars(stmt))

        return results, total_count

    def get_locked_users(self) -> list[User]:
        """Get all locked users."""
        return list(
            self.db.scalars(
                select(User).where(
                    and_(
                        User.locked_until.is_not(None),
                        User.locked_until > datetime.now(timezone.utc),
                    )
                )
            )
        )

    def get_users_with_expired_passwords(self, days: int = 90) -> list[User]:
        """Get users with expired passwords."""
        expiry_date = datetime.now(timezone.utc) - timedelta(days=days)
        return list(
            self.db.scalars(
                select(User).where(
                    and_(
                        User.password_changed_at < expiry_date,
                        User.is_active,
                        ~User.is_deleted,
                    )
                )
            )
        )

    def get_inactive_users(self, days: int = 30) -> list[User]:
        """Get users who haven't logged in for specified days."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        return list(
            self.db.scalars(
                select(User).where(
                    and_(
                        or_(
                            User.last_login_at.is_(None),
                            User.last_login_at < cutoff_date,
                        ),
                        User.is_active,
                        ~User.is_deleted,
                    )
                )
            )
        )

    def update_last_login(self, user_id: UserId) -> None:
        """Update user's last login timestamp."""
        from sqlalchemy import update

        self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=datetime.now(timezone.utc))
        )
        self.db.commit()

    def increment_failed_login(self, email: str) -> User | None:
        """Increment failed login attempts and lock if necessary."""
        user = self.get_by_email(email)
        if not user:
            return None

        user.failed_login_attempts += 1

        # Lock after 5 attempts
        if user.failed_login_attempts >= 5:
            # Use timezone-aware datetime for consistency
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)

        self.db.commit()
        return user

    def reset_failed_login(self, user_id: UserId) -> None:
        """Reset failed login attempts."""
        user = self.get(user_id)
        if user:
            user.failed_login_attempts = 0
            user.locked_until = None
            self.db.commit()

    def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email."""
        count = self.db.scalar(select(func.count(User.id)).where(User.email == email))
        return bool(count and count > 0)

    def get_superusers(self) -> list[User]:
        """Get all superuser accounts."""
        return list(
            self.db.scalars(
                select(User).where(
                    and_(User.is_superuser, User.is_active, ~User.is_deleted)
                )
            )
        )
