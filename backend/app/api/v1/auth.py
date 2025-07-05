"""Authentication endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
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
    }
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """User login endpoint."""
    # Authenticate user
    user = AuthService.authenticate_user(db, request.email, request.password)
    if not user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(
                detail="Invalid authentication credentials",
                code="AUTH001",
                timestamp=datetime.utcnow()
            ).model_dump()
        )
    
    # Create tokens
    return AuthService.create_tokens(user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired token"},
    }
)
def refresh_token(
    request: RefreshRequest,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """Refresh access token."""
    # Refresh tokens
    tokens = AuthService.refresh_tokens(db, request.refresh_token)
    if not tokens:
        # Determine error type based on token validation
        try:
            from app.core.security import verify_token
            verify_token(request.refresh_token)
            # Token is valid but not a refresh token or user issue
            error_code = "AUTH003"
        except Exception:
            # Token is expired or invalid
            error_code = "AUTH002"
        
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(
                detail="Invalid or expired refresh token",
                code=error_code,
                timestamp=datetime.utcnow()
            ).model_dump()
        )
    
    return tokens