"""Authentication endpoints."""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.schemas.error import ErrorResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        401: {"model": ErrorResponse, "description": "Authentication failed"},
    },
)
def login(
    request: LoginRequest, db: Session = Depends(get_db)
) -> TokenResponse | JSONResponse:
    """User login endpoint."""
    # Authenticate user
    user = AuthService.authenticate_user(db, request.email, request.password)
    if not user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(
                detail="Invalid authentication credentials",
                code="AUTH001",
            ).model_dump(),
        )

    # Create tokens
    return AuthService.create_tokens(user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired token"},
    },
)
def refresh_token(
    request: RefreshRequest, db: Session = Depends(get_db)
) -> TokenResponse | JSONResponse:
    """Refresh access token."""
    # Refresh tokens
    tokens = AuthService.refresh_tokens(db, request.refresh_token)
    if not tokens:
        # Determine error type based on token validation
        try:
            from app.core.exceptions import ExpiredTokenError, InvalidTokenError
            from app.core.security import verify_token

            verify_token(request.refresh_token)
            # Token is valid format but user/refresh issue
            error_code = "AUTH002"
        except ExpiredTokenError:
            error_code = "AUTH002"  # Expired token
        except InvalidTokenError:
            error_code = "AUTH003"  # Invalid format
        except Exception:
            error_code = "AUTH003"  # Other invalid format

        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(
                detail="Invalid or expired refresh token",
                code=error_code,
            ).model_dump(),
        )

    return tokens
