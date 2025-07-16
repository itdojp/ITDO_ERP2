"""Authentication and authorization module."""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User

security = HTTPBearer()


async def get_current_user(
    token: str = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Get current authenticated user.

    This is a placeholder implementation for authentication.
    In a real application, this would validate JWT tokens and return the user.
    """
    # For development/testing purposes, return a mock user
    # In production, this should validate the token and fetch the actual user

    # Mock user for testing - replace with actual authentication logic
    user = db.query(User).filter(User.is_active == True).first()

    if not user:
        # Create a mock user if none exists (for testing)
        user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user


def get_optional_current_user(
    token: Optional[str] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None.
    For endpoints that optionally require authentication.
    """
    if not token:
        return None

    try:
        return get_current_user(token, db)
    except HTTPException:
        return None
