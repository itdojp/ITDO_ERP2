"""Authentication service."""

from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ExpiredTokenError, InvalidTokenError
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.models.user import User
from app.schemas.auth import TokenResponse


class AuthService:
    """Authentication service."""

    @staticmethod
    def authenticate_user(
        db: Session,
        email: str,
        password: str
    ) -> Optional[User]:
        """Authenticate user and return user object."""
        return User.authenticate(db, email, password)

    @staticmethod
    def create_tokens(user: User) -> TokenResponse:
        """Create access and refresh tokens for user."""
        # Token data
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "is_superuser": user.is_superuser
        }

        # Create tokens
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # Return response
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    @staticmethod
    def refresh_tokens(
        db: Session,
        refresh_token: str
    ) -> Optional[TokenResponse]:
        """Refresh tokens using refresh token."""
        try:
            # Verify refresh token
            payload = verify_token(refresh_token)

            # Check token type
            if payload.get("type") != "refresh":
                return None

            # Get user
            user_id = payload.get("sub")
            if not user_id:
                return None

            user = db.query(User).filter(User.id == int(user_id)).first()
            if not user or not user.is_active:
                return None

            # Create new tokens
            return AuthService.create_tokens(user)

        except (ExpiredTokenError, InvalidTokenError):
            return None

    @staticmethod
    def get_current_user(db: Session, token: str) -> Optional[User]:
        """Get current user from access token."""
        try:
            # Verify token
            payload = verify_token(token)

            # Check token type
            if payload.get("type") != "access":
                return None

            # Get user
            user_id = payload.get("sub")
            if not user_id:
                return None

            user = db.query(User).filter(User.id == int(user_id)).first()
            if not user or not user.is_active:
                return None

            return user

        except (ExpiredTokenError, InvalidTokenError):
            return None
