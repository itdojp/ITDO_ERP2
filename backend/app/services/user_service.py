"""User management service."""

from typing import Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError
from app.models.user import User
from app.schemas.user_auth import UserActivitySummary, UserMFAStatus, UserProfileUpdate


class UserService:
    """Service for user management operations."""

    def __init__(self, db: Session) -> dict:
        """Initialize user service."""
        self.db = db

    def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        phone: Optional[str] = None,
        is_active: bool = True,
        created_by: Optional[int] = None,
    ) -> User:
        """
        Create a new user.

        Args:
            email: User email
            password: User password (plain text)
            full_name: User full name
            phone: User phone number
            is_active: Whether user is active
            created_by: ID of user creating this user

        Returns:
            Created user

        Raises:
            BusinessLogicError: If user already exists
        """
        # Check if user already exists
        existing = self.db.query(User).filter(User.email == email).first()
        if existing:
            raise BusinessLogicError("このメールアドレスは既に使用されています")

        # Create user
        user = User.create(
            db=self.db,
            email=email,
            password=password,
            full_name=full_name,
            phone=phone,
            is_active=is_active,
        )

        # Log activity
        if created_by:
            creator = self.db.query(User).filter(User.id == created_by).first()
            if creator:
                creator.log_activity(
                    self.db,
                    action="user_created",
                    details={"created_user_id": user.id, "email": email},
                )

        self.db.commit()
        return user

    def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[list[User], int]:
        """
        List users with pagination and filters.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            search: Search term for email or name
            is_active: Filter by active status

        Returns:
            Tuple of (users, total_count)
        """
        query = self.db.query(User)

        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.email.ilike(search_term),
                    User.full_name.ilike(search_term),
                )
            )

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        # Get total count
        total = query.count()

        # Apply pagination and get results
        users = query.offset(skip).limit(limit).all()

        return users, total

    def update_user_profile(
        self,
        user: User,
        profile_data: UserProfileUpdate,
    ) -> User:
        """
        Update user profile.

        Args:
            user: User to update
            profile_data: Profile update data

        Returns:
            Updated user
        """
        # Update fields
        update_data = profile_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)

        # Log activity
        user.log_activity(
            self.db,
            action="profile_updated",
            details={"updated_fields": list(update_data.keys())},
        )

        self.db.commit()
        self.db.refresh(user)
        return user

    def get_mfa_status(self, user: User) -> UserMFAStatus:
        """
        Get user MFA status.

        Args:
            user: User

        Returns:
            MFA status
        """
        # Count active MFA devices
        mfa_devices_count = len([d for d in user.mfa_devices if d.is_active])

        # Check for backup codes
        has_backup_codes = any(
            device.backup_codes for device in user.mfa_devices if device.is_active
        )

        # Get last MFA verification
        last_verified_at = None
        if user.mfa_devices:
            last_used_times = [
                d.last_used_at for d in user.mfa_devices if d.last_used_at
            ]
            if last_used_times:
                last_verified_at = max(last_used_times)

        return UserMFAStatus(
            mfa_enabled=user.mfa_required,
            mfa_devices_count=mfa_devices_count,
            has_backup_codes=has_backup_codes,
            last_verified_at=last_verified_at,
        )

    def get_activity_summary(self, user: User) -> UserActivitySummary:
        """
        Get user activity summary.

        Args:
            user: User

        Returns:
            Activity summary
        """
        # Count total logins
        total_logins = (
            self.db.query(func.count())
            .filter(
                User.id == user.id,
                User.last_login_at.isnot(None),
            )
            .scalar()
            or 0
        )

        # Count active sessions
        active_sessions = len(user.active_sessions)

        return UserActivitySummary(
            total_logins=total_logins,
            last_login_at=user.last_login_at,
            failed_login_attempts=user.failed_login_attempts,
            active_sessions=active_sessions,
            last_password_change=user.password_changed_at,
        )
