"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import BusinessLogicError
from app.models.user import User
from app.schemas.auth import (
    AuthenticatedUser,
    LoginRequest,
    LogoutRequest,
    MFAVerifyRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RefreshRequest,
    TokenResponse,
)
from app.schemas.error import ErrorResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        401: {"model": ErrorResponse, "description": "Authentication failed"},
    },
)
async def login(
    http_request: Request,
    request: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse | JSONResponse:
    """User login endpoint."""
    auth_service = AuthService(db)

    # Get client info
    client_ip = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")

    try:
        # Authenticate user
        user = auth_service.authenticate_user(
            email=request.email,
            password=request.password,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        # Check if MFA is required
        if user.mfa_required or auth_service.is_mfa_required_for_ip(user, client_ip):
            # Create MFA challenge
            from app.services.mfa_service import MFAService

            mfa_service = MFAService(db)
            challenge = mfa_service.create_challenge(
                user_id=user.id,
                challenge_type="login",
                ip_address=client_ip,
                user_agent=user_agent,
            )

            # Return MFA challenge response
            return TokenResponse(
                access_token="",  # Empty until MFA is completed
                token_type="bearer",
                expires_in=0,
                requires_mfa=True,
                mfa_token=challenge.challenge_token,
            )

        # Create session and tokens
        session = auth_service.create_user_session(
            user=user,
            ip_address=client_ip,
            user_agent=user_agent,
            remember_me=request.remember_me,
        )

        # Generate tokens
        tokens = auth_service.create_tokens(
            user=user,
            session_id=session.id,
            remember_me=request.remember_me,
        )

        return tokens

    except BusinessLogicError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(
                detail=str(e),
                code="AUTH001",
            ).model_dump(),
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                detail="ログイン処理中にエラーが発生しました",
                code="AUTH999",
            ).model_dump(),
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired token"},
    },
)
async def refresh_token(
    request: RefreshRequest, db: Session = Depends(get_db)
) -> TokenResponse | JSONResponse:
    """Refresh access token."""
    auth_service = AuthService(db)

    try:
        # Refresh tokens
        tokens = auth_service.refresh_tokens(request.refresh_token)
        return tokens
    except BusinessLogicError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(
                detail=str(e),
                code="AUTH002",
            ).model_dump(),
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(
                detail="Invalid or expired refresh token",
                code="AUTH003",
            ).model_dump(),
        )


@router.post("/mfa/verify", response_model=TokenResponse)
async def verify_mfa(
    request: Request,
    mfa_data: MFAVerifyRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Verify MFA code and complete login."""
    from app.services.mfa_service import MFAService

    mfa_service = MFAService(db)
    auth_service = AuthService(db)

    try:
        # Verify MFA challenge
        user = mfa_service.verify_challenge(
            challenge_token=mfa_data.challenge_token or mfa_data.challenge_token,
            code=mfa_data.code,
        )

        # Create session
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        session = auth_service.create_user_session(
            user=user,
            ip_address=client_ip,
            user_agent=user_agent,
            remember_me=True,  # Default to remember after MFA
        )

        # Generate tokens
        tokens = auth_service.create_tokens(
            user=user,
            session_id=session.id,
            remember_me=True,
        )

        return tokens

    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    logout_data: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Logout current session or all sessions."""
    auth_service = AuthService(db)

    if logout_data.all_sessions:
        # Invalidate all user sessions
        auth_service.invalidate_all_sessions(current_user)
    else:
        # Invalidate current session
        # Get session from token context
        # This would need to be implemented in get_current_user
        pass

    db.commit()


@router.get("/me", response_model=AuthenticatedUser)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> AuthenticatedUser:
    """Get current authenticated user information."""
    return AuthenticatedUser(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        mfa_enabled=current_user.mfa_required,
        last_login_at=current_user.last_login_at,
        session_timeout_hours=8,  # Default value
        idle_timeout_minutes=30,  # Default value
    )


@router.post("/password-reset", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Request password reset email."""
    auth_service = AuthService(db)

    try:
        auth_service.request_password_reset(reset_data.email)
        return {"message": "パスワードリセットメールを送信しました"}
    except Exception:
        # Don't reveal if email exists or not
        return {"message": "パスワードリセットメールを送信しました"}


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_password_reset(
    confirm_data: PasswordResetConfirmRequest,
    db: Session = Depends(get_db),
) -> None:
    """Confirm password reset with token."""
    auth_service = AuthService(db)

    try:
        auth_service.reset_password(
            token=confirm_data.token,
            new_password=confirm_data.new_password,
        )
    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="パスワードリセットに失敗しました",
        )
