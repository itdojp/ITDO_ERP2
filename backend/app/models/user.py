"""User model."""

from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from app.core.database import Base
from app.core.security import hash_password, verify_password


class User(Base):
    """User model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user_roles = relationship(
        "UserRole", foreign_keys="UserRole.user_id", back_populates="user"
    )

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        email: str,
        password: str,
        full_name: str,
        is_active: bool = True,
        is_superuser: bool = False,
    ) -> "User":
        """Create a new user."""
        # Hash the password
        hashed_password = hash_password(password)

        # Create user instance
        user = cls(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=is_active,
            is_superuser=is_superuser,
        )

        # Add to database
        db.add(user)
        db.flush()

        return user

    @classmethod
    def get_by_email(cls, db: Session, email: str) -> Optional["User"]:
        """Get user by email."""
        return db.query(cls).filter(cls.email == email).first()

    @classmethod
    def authenticate(cls, db: Session, email: str, password: str) -> Optional["User"]:
        """Authenticate user by email and password."""
        # Get user by email
        user = cls.get_by_email(db, email)
        if not user:
            return None

        # Check if user is active
        if not user.is_active:
            return None

        # Verify password
        if not verify_password(password, user.hashed_password):
            return None

        return user

    def update(self, db: Session, **kwargs: Any) -> None:
        """Update user attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                # Hash password if updating
                if key == "password":
                    value = hash_password(value)
                    key = "hashed_password"
                setattr(self, key, value)

        db.add(self)
        db.flush()

    def get_permissions(self, organization_id: int) -> List[str]:
        """Get user permissions for a specific organization."""
        permissions = set()

        # Get all roles for this user in the organization
        for user_role in self.user_roles:
            if (
                user_role.organization_id == organization_id
                and not user_role.is_expired()
            ):
                role_permissions = user_role.role.permissions or []
                for perm in role_permissions:
                    if perm == "*":
                        # System admin has all permissions
                        permissions.add("*")
                    elif perm.endswith("*"):
                        # Wildcard permission - expand to specific permissions
                        prefix = perm[:-1]
                        permissions.add(f"{prefix}read")
                        permissions.add(f"{prefix}write")
                        permissions.add(f"{prefix}delete")
                        permissions.add(f"{prefix}create")
                    else:
                        permissions.add(perm)

        return list(permissions)

    def has_role(self, role_code: str, organization_id: int) -> bool:
        """Check if user has a specific role in an organization."""
        for user_role in self.user_roles:
            if (
                user_role.organization_id == organization_id
                and user_role.role.code == role_code
                and not user_role.is_expired()
            ):
                return True
        return False

    def has_permission(self, permission: str, organization_id: int) -> bool:
        """Check if user has a specific permission in an organization."""
        permissions = self.get_permissions(organization_id)

        # Check for exact match
        if permission in permissions:
            return True

        # Check for wildcard permissions
        if "*" in permissions:
            return True

        # Check for pattern match
        for perm in permissions:
            if perm.endswith("*"):
                prefix = perm[:-1]
                if permission.startswith(prefix):
                    return True

        return False
