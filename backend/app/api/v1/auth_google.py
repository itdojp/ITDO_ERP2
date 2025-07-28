"""Google OAuth2.0 authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import BusinessLogicError
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.schemas.google_auth import (
    GoogleLoginRequest,
    GoogleUnlinkRequest,
)
from app.services.auth import AuthService
from app.services.google_auth_service import GoogleAuthService

router = APIRouter(prefix="/auth/google", tags=["auth", "google"])


@router.get("/login")
async def google_login_url() -> dict:
    """
    Get Google OAuth2 login URL.

    Returns the authorization URL to redirect the user to Google login.
    """
    # Create temporary DB session just for service
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        google_service = GoogleAuthService(db)
        auth_url, state = google_service.get_authorization_url()

        return {
            "auth_url": auth_url,
            "state": state,
        }
    finally:
        db.close()


@router.post("/callback", response_model=TokenResponse)
async def google_callback(
    request: GoogleLoginRequest,
    http_request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Handle Google OAuth2 callback.

    Exchange authorization code for tokens and authenticate user.
    """
    google_service = GoogleAuthService(db)
    auth_service = AuthService(db)

    try:
        # Exchange code for tokens
        token_data = google_service.exchange_code_for_tokens(request.code)

        # Verify ID token and get user info
        google_info = google_service.verify_id_token(token_data["id_token"])

        # Get client info
        client_ip = http_request.client.host if http_request.client else "unknown"
        user_agent = http_request.headers.get("user-agent", "unknown")

        # Authenticate or create user
        user, is_new = google_service.authenticate_or_create_user(
            google_info=google_info,
            ip_address=client_ip,
            user_agent=user_agent,
            device_id=request.device_id,
            device_name=request.device_name,
        )

        # Store Google refresh token if provided
        if token_data.get("refresh_token"):
            user.google_refresh_token = token_data["refresh_token"]
            db.commit()

        # Check if MFA is required
        if user.mfa_required and not is_new:
            # Create MFA challenge
            from app.services.mfa_service import MFAService

            mfa_service = MFAService(db)
            challenge = mfa_service.create_challenge(user, "google_login")

            return TokenResponse(
                access_token="",
                token_type="bearer",
                expires_in=0,
                requires_mfa=True,
                mfa_token=challenge.challenge_token,
            )

        # Create session
        session = auth_service.create_user_session(
            user=user,
            ip_address=client_ip,
            user_agent=user_agent,
            device_id=request.device_id,
            device_name=request.device_name,
        )

        # Create tokens
        return auth_service.create_tokens(user, session)

    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google認証中にエラーが発生しました",
        )


@router.get("/me")
async def get_google_info(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get current user's linked Google account info.
    """
    if not current_user.google_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Googleアカウントがリンクされていません",
        )

    return {
        "google_id": current_user.google_id,
        "email": current_user.email,
        "has_refresh_token": bool(current_user.google_refresh_token),
    }


@router.post("/link")
async def link_google_account(
    request: GoogleLoginRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Link Google account to existing user.
    """
    if current_user.google_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="既にGoogleアカウントがリンクされています",
        )

    google_service = GoogleAuthService(db)

    try:
        # Exchange code for tokens
        token_data = google_service.exchange_code_for_tokens(request.code)

        # Verify ID token and get user info
        google_info = google_service.verify_id_token(token_data["id_token"])

        # Link account
        google_service.link_google_account(current_user, google_info)

        # Store refresh token if provided
        if token_data.get("refresh_token"):
            current_user.google_refresh_token = token_data["refresh_token"]
            db.commit()

        return {
            "message": "Googleアカウントをリンクしました",
            "google_id": google_info.id,
            "email": google_info.email,
        }

    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/unlink", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_google_account(
    request: GoogleUnlinkRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Unlink Google account from user.
    """
    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="リンク解除の確認が必要です",
        )

    google_service = GoogleAuthService(db)

    try:
        google_service.unlink_google_account(current_user)
    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
