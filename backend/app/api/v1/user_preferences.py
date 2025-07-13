"""User preferences API endpoints."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.core.exceptions import NotFound
from app.models.user import User
from app.schemas.user_preferences import (
    UserLocaleInfo,
    UserPreferencesCreate,
    UserPreferencesResponse,
    UserPreferencesUpdate,
)
from app.services.user_preferences import UserPreferencesService

router = APIRouter()


@router.get("/me", response_model=UserPreferencesResponse)
def get_my_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserPreferencesResponse:
    """Get current user's preferences."""
    service = UserPreferencesService(db)
    try:
        return service.get_preferences(current_user.id)
    except NotFound:
        # Return default preferences if none exist
        return service.get_preferences_or_default(current_user.id)


@router.post(
    "/me", response_model=UserPreferencesResponse, status_code=status.HTTP_201_CREATED
)
def create_my_preferences(
    preferences_data: UserPreferencesCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserPreferencesResponse:
    """Create or update current user's preferences."""
    service = UserPreferencesService(db)
    try:
        return service.create_preferences(current_user.id, preferences_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/me", response_model=UserPreferencesResponse)
def update_my_preferences(
    preferences_data: UserPreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserPreferencesResponse:
    """Update current user's preferences."""
    service = UserPreferencesService(db)
    try:
        return service.update_preferences(current_user.id, preferences_data)
    except NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="ユーザー設定が見つかりません"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete current user's preferences (revert to defaults)."""
    service = UserPreferencesService(db)
    try:
        service.delete_preferences(current_user.id)
    except NotFound:
        # Already deleted, no error
        pass


@router.get("/me/locale", response_model=Dict[str, Any])
def get_my_locale_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get current user's locale information for internationalization."""
    service = UserPreferencesService(db)
    return service.get_user_locale_info(current_user.id)


@router.patch("/me/language", response_model=UserPreferencesResponse)
def set_my_language(
    language_data: Dict[str, str],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserPreferencesResponse:
    """Set current user's language preference."""
    if "language" not in language_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="言語コードが必要です"
        )

    service = UserPreferencesService(db)
    try:
        return service.set_language(current_user.id, language_data["language"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/me/timezone", response_model=UserPreferencesResponse)
def set_my_timezone(
    timezone_data: Dict[str, str],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserPreferencesResponse:
    """Set current user's timezone preference."""
    if "timezone" not in timezone_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="タイムゾーンが必要です"
        )

    service = UserPreferencesService(db)
    try:
        return service.set_timezone(current_user.id, timezone_data["timezone"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/me/theme", response_model=UserPreferencesResponse)
def set_my_theme(
    theme_data: Dict[str, str],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserPreferencesResponse:
    """Set current user's theme preference."""
    if "theme" not in theme_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="テーマが必要です"
        )

    service = UserPreferencesService(db)
    try:
        return service.set_theme(current_user.id, theme_data["theme"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/me/notifications/email/toggle", response_model=UserPreferencesResponse)
def toggle_my_email_notifications(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserPreferencesResponse:
    """Toggle current user's email notifications on/off."""
    service = UserPreferencesService(db)
    return service.toggle_email_notifications(current_user.id)


@router.patch("/me/notifications/push/toggle", response_model=UserPreferencesResponse)
def toggle_my_push_notifications(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserPreferencesResponse:
    """Toggle current user's push notifications on/off."""
    service = UserPreferencesService(db)
    return service.toggle_push_notifications(current_user.id)
