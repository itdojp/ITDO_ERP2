"""Session management API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_session, get_current_user, get_db
from app.core.exceptions import BusinessLogicError
from app.models.session import UserSession
from app.models.user import User
from app.schemas.session import (
    SessionConfigUpdate,
    SessionConfigurationResponse,
    SessionListResponse,
    SessionResponse,
    TrustedDeviceRequest,
)
from app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SessionListResponse:
    """
    List all active sessions for the current user.
    """
    session_service = SessionService(db)
    sessions = session_service.get_active_sessions(current_user)

    return SessionListResponse(
        sessions=[
            SessionResponse(
                id=session.id,
                ip_address=session.ip_address,
                user_agent=session.user_agent,
                device_name=session.device_name,
                created_at=session.created_at,
                last_activity_at=session.last_activity_at,
                expires_at=session.expires_at,
                is_current=False,  # Will be set by comparing with current session
            )
            for session in sessions
        ],
        total=len(sessions),
    )


@router.get("/current", response_model=SessionResponse)
async def get_current_session(
    current_session: UserSession = Depends(get_current_session),
) -> SessionResponse:
    """
    Get details of the current session.
    """
    return SessionResponse(
        id=current_session.id,
        ip_address=current_session.ip_address,
        user_agent=current_session.user_agent,
        device_name=current_session.device_name,
        created_at=current_session.created_at,
        last_activity_at=current_session.last_activity_at,
        expires_at=current_session.expires_at,
        is_current=True,
    )


@router.post("/current/extend", response_model=SessionResponse)
async def extend_current_session(
    hours: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    current_session: UserSession = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> SessionResponse:
    """
    Extend the current session.

    - **hours**: Number of hours to extend (uses user's default if not specified)
    """
    session_service = SessionService(db)
    config = session_service.get_or_create_session_config(current_user)

    # Use provided hours or user's configured timeout
    extend_hours = hours or config.session_timeout_hours

    # Validate hours
    if extend_hours < 1 or extend_hours > config.max_session_timeout_hours:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"延長時間は1〜{config.max_session_timeout_hours}時間の間で指定してください",
        )

    # Extend session
    current_session.extend_session(db, extend_hours)

    # Log activity
    session_service.log_activity(
        current_session,
        "extend",
        current_session.ip_address,
        current_session.user_agent,
        {"hours": extend_hours},
    )

    return SessionResponse(
        id=current_session.id,
        ip_address=current_session.ip_address,
        user_agent=current_session.user_agent,
        device_name=current_session.device_name,
        created_at=current_session.created_at,
        last_activity_at=current_session.last_activity_at,
        expires_at=current_session.expires_at,
        is_current=True,
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Revoke a specific session.

    Users can only revoke their own sessions.
    """
    # Find the session
    session = db.query(UserSession).filter(UserSession.id == session_id).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="セッションが見つかりません",
        )

    # Check ownership
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このセッションを無効化する権限がありません",
        )

    # Revoke the session
    session_service = SessionService(db)
    session_service.revoke_session(
        session,
        revoked_by=current_user.id,
        reason="User requested",
    )


@router.post("/revoke-all", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_all_sessions(
    keep_current: bool = True,
    current_user: User = Depends(get_current_user),
    current_session: UserSession = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> None:
    """
    Revoke all sessions for the current user.

    - **keep_current**: Whether to keep the current session active
    """
    session_service = SessionService(db)

    count = session_service.revoke_all_user_sessions(
        current_user,
        except_session=current_session if keep_current else None,
        reason="User requested all sessions revoked",
    )

    # If not keeping current session, the user will be logged out
    if not keep_current:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail=f"{count}個のセッションを無効化しました。再度ログインしてください。",
        )


@router.get("/config", response_model=SessionConfigurationResponse)
async def get_session_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SessionConfigurationResponse:
    """
    Get user's session configuration.
    """
    session_service = SessionService(db)
    config = session_service.get_or_create_session_config(current_user)

    return SessionConfigurationResponse(
        session_timeout_hours=config.session_timeout_hours,
        max_session_timeout_hours=config.max_session_timeout_hours,
        refresh_token_days=config.refresh_token_days,
        allow_multiple_sessions=config.allow_multiple_sessions,
        max_concurrent_sessions=config.max_concurrent_sessions,
        require_mfa_for_new_device=config.require_mfa_for_new_device,
        notify_new_device_login=config.notify_new_device_login,
        notify_suspicious_activity=config.notify_suspicious_activity,
    )


@router.put("/config", response_model=SessionConfigurationResponse)
async def update_session_config(
    config_update: SessionConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SessionConfigurationResponse:
    """
    Update user's session configuration.
    """
    session_service = SessionService(db)

    try:
        config = session_service.update_session_config(
            current_user,
            **config_update.dict(exclude_unset=True),
        )

        return SessionConfigurationResponse(
            session_timeout_hours=config.session_timeout_hours,
            max_session_timeout_hours=config.max_session_timeout_hours,
            refresh_token_days=config.refresh_token_days,
            allow_multiple_sessions=config.allow_multiple_sessions,
            max_concurrent_sessions=config.max_concurrent_sessions,
            require_mfa_for_new_device=config.require_mfa_for_new_device,
            notify_new_device_login=config.notify_new_device_login,
            notify_suspicious_activity=config.notify_suspicious_activity,
        )
    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/trusted-devices", status_code=status.HTTP_204_NO_CONTENT)
async def add_trusted_device(
    request: TrustedDeviceRequest,
    current_user: User = Depends(get_current_user),
    current_session: UserSession = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> None:
    """
    Add current device as a trusted device.
    """
    session_service = SessionService(db)

    # Use current session's device ID or provided one
    device_id = request.device_id or current_session.device_id

    if not device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="デバイスIDが必要です",
        )

    # Add to trusted devices
    session_service.add_trusted_device(current_user, device_id)

    # Update current session if needed
    if not current_session.device_id and request.device_id:
        current_session.device_id = request.device_id
        if request.device_name:
            current_session.device_name = request.device_name
        db.commit()


@router.get("/activities")
async def get_session_activities(
    session_id: Optional[int] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Get session activities for the current user.

    - **session_id**: Filter by specific session
    - **limit**: Maximum number of activities to return
    """
    from app.models.session import SessionActivity

    query = db.query(SessionActivity).filter(SessionActivity.user_id == current_user.id)

    if session_id:
        # Verify session belongs to user
        session = (
            db.query(UserSession)
            .filter(
                UserSession.id == session_id,
                UserSession.user_id == current_user.id,
            )
            .first()
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="セッションが見つかりません",
            )

        query = query.filter(SessionActivity.session_id == session_id)

    activities = query.order_by(SessionActivity.created_at.desc()).limit(limit).all()

    return [
        {
            "id": activity.id,
            "session_id": activity.session_id,
            "activity_type": activity.activity_type,
            "ip_address": activity.ip_address,
            "user_agent": activity.user_agent,
            "created_at": activity.created_at,
            "details": activity.details,
        }
        for activity in activities
    ]
