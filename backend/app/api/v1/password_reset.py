"""Password reset API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import BusinessLogicError
from app.schemas.base import MessageResponse
from app.schemas.password_reset import (
    PasswordResetRequest,
    PasswordResetResponse,
    ResetPasswordRequest,
    VerifyResetTokenRequest,
    VerifyResetTokenResponse,
)
from app.services.password_reset_service import PasswordResetService

router = APIRouter()


@router.post("/request", response_model=PasswordResetResponse)
def request_password_reset(
    request: Request,
    data: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    """
    Request password reset.

    Sends a reset email if the user exists.
    Always returns success to prevent user enumeration.
    """
    service = PasswordResetService(db)

    # Get client info
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "unknown")

    try:
        token = service.request_password_reset(
            email=data.email,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if token:
            return PasswordResetResponse(
                success=True,
                message="パスワードリセットメールを送信しました。メールをご確認ください。",
            )
    except BusinessLogicError as e:
        # Log error but don't expose to user
        print(f"Password reset error: {e}")

    # Always return success to prevent user enumeration
    return PasswordResetResponse(
        success=True,
        message="パスワードリセットメールを送信しました。メールをご確認ください。",
    )


@router.post("/verify", response_model=VerifyResetTokenResponse)
def verify_reset_token(
    data: VerifyResetTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Verify password reset token.

    Optionally verify the email code for additional security.
    """
    service = PasswordResetService(db)

    try:
        reset_token = service.verify_reset_token(
            token=data.token,
            verification_code=data.verification_code,
        )

        return VerifyResetTokenResponse(
            valid=True,
            user_email=reset_token.user.email,
            expires_at=reset_token.expires_at,
        )
    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/reset", response_model=MessageResponse)
def reset_password(
    request: Request,
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Reset password with token.

    Validates token, updates password, and invalidates all sessions.
    """
    service = PasswordResetService(db)

    # Get client info
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "unknown")

    try:
        service.reset_password(
            token=data.token,
            new_password=data.new_password,
            verification_code=data.verification_code,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return MessageResponse(
            message="パスワードがリセットされました。新しいパスワードでログインしてください。"
        )
    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
