"""Dependency injection utilities."""

from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.session import UserSession
from app.models.user import User
from app.services.auth import AuthService

# Security scheme
security = HTTPBearer()


def get_db() -> Generator[Session]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user."""
    # Extract token
    token = credentials.credentials

    # Get user from token
    user = AuthService.get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return current_user


def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current superuser."""
    if not current_user.is_superuser:
        from datetime import datetime

        from app.schemas.error import ErrorResponse

        # Create error response compatible with test expectations
        error_detail = ErrorResponse(
            detail="Not enough permissions",
            code="AUTH004",
            timestamp=datetime.utcnow(),
        ).model_dump()

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_detail,
        )
    return current_user


def get_current_session(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> UserSession:
    """Get current session from token."""
    token = credentials.credentials

    # Get session from token
    from app.services.session_service import SessionService

    session_service = SessionService(db)
    session = session_service.get_session_by_token(token)

    if not session or not session.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate session
    if not session_service.validate_session(session):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return session
