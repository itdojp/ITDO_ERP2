"""User privacy settings API endpoints."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.core.exceptions import NotFound
from app.models.user import User
from app.schemas.user_privacy import (
    FilteredUserData,
    PrivacyCheckResult,
    PrivacySettingsCreate,
    PrivacySettingsResponse,
    PrivacySettingsUpdate,
)
from app.services.user_privacy import UserPrivacyService

router = APIRouter()


@router.get("/me", response_model=PrivacySettingsResponse)
def get_my_privacy_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PrivacySettingsResponse:
    """Get current user's privacy settings."""
    service = UserPrivacyService(db)
    try:
        return service.get_settings(current_user.id)
    except NotFound:
        # Return defaults if none exist
        return service.get_settings_or_default(current_user.id)


@router.post(
    "/me", response_model=PrivacySettingsResponse, status_code=status.HTTP_201_CREATED
)
def create_my_privacy_settings(
    settings_data: PrivacySettingsCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PrivacySettingsResponse:
    """Create or update current user's privacy settings."""
    service = UserPrivacyService(db)
    return service.create_settings(current_user.id, settings_data)


@router.put("/me", response_model=PrivacySettingsResponse)
def update_my_privacy_settings(
    settings_data: PrivacySettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PrivacySettingsResponse:
    """Update current user's privacy settings."""
    service = UserPrivacyService(db)
    try:
        return service.update_settings(current_user.id, settings_data)
    except NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="プライバシー設定が見つかりません",
        )


@router.post("/me/set-all-private", response_model=PrivacySettingsResponse)
def set_all_private(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PrivacySettingsResponse:
    """Set all privacy settings to most restrictive."""
    service = UserPrivacyService(db)
    return service.set_all_private(current_user.id)


@router.get("/check/profile/{user_id}", response_model=PrivacyCheckResult)
def check_profile_visibility(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PrivacyCheckResult:
    """Check if current user can view target user's profile."""
    service = UserPrivacyService(db)
    allowed = service.can_view_profile(current_user.id, user_id)

    return PrivacyCheckResult(
        allowed=allowed,
        reason="Profile is visible" if allowed else "Profile is private",
        requires_permission="profile.view" if not allowed else None,
    )


@router.get("/check/email/{user_id}", response_model=PrivacyCheckResult)
def check_email_visibility(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PrivacyCheckResult:
    """Check if current user can view target user's email."""
    service = UserPrivacyService(db)
    allowed = service.can_view_email(current_user.id, user_id)

    return PrivacyCheckResult(
        allowed=allowed,
        reason="Email is visible" if allowed else "Email is private",
        requires_permission="email.view" if not allowed else None,
    )


@router.get("/check/phone/{user_id}", response_model=PrivacyCheckResult)
def check_phone_visibility(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PrivacyCheckResult:
    """Check if current user can view target user's phone."""
    service = UserPrivacyService(db)
    allowed = service.can_view_phone(current_user.id, user_id)

    return PrivacyCheckResult(
        allowed=allowed,
        reason="Phone is visible" if allowed else "Phone is private",
        requires_permission="phone.view" if not allowed else None,
    )


@router.get("/check/activity/{user_id}", response_model=PrivacyCheckResult)
def check_activity_visibility(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PrivacyCheckResult:
    """Check if current user can view target user's activity."""
    service = UserPrivacyService(db)
    allowed = service.can_view_activity(current_user.id, user_id)

    return PrivacyCheckResult(
        allowed=allowed,
        reason="Activity is visible" if allowed else "Activity is private",
        requires_permission="activity.view" if not allowed else None,
    )


@router.get("/check/online-status/{user_id}", response_model=PrivacyCheckResult)
def check_online_status_visibility(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PrivacyCheckResult:
    """Check if current user can view target user's online status."""
    service = UserPrivacyService(db)
    allowed = service.can_view_online_status(current_user.id, user_id)

    return PrivacyCheckResult(
        allowed=allowed,
        reason="Online status is visible" if allowed else "Online status is hidden",
        requires_permission=None,
    )


@router.get("/check/direct-message/{user_id}", response_model=PrivacyCheckResult)
def check_direct_message_permission(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PrivacyCheckResult:
    """Check if current user can send direct message to target user."""
    service = UserPrivacyService(db)
    allowed = service.can_send_direct_message(current_user.id, user_id)

    return PrivacyCheckResult(
        allowed=allowed,
        reason="Direct messages allowed" if allowed else "Direct messages not allowed",
        requires_permission=None,
    )


@router.get("/filter-user-data/{user_id}", response_model=FilteredUserData)
def get_filtered_user_data(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FilteredUserData:
    """Get user data filtered by privacy settings."""
    # Get target user
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="ユーザーが見つかりません"
        )

    # Prepare user data
    user_data = {
        "id": target_user.id,
        "full_name": target_user.full_name,
        "email": target_user.email,
        "phone": target_user.phone,
        "profile_image_url": target_user.profile_image_url,
        "is_online": False,  # This would come from session/activity tracking
        "last_activity": target_user.last_login_at,
    }

    # Apply privacy filter
    service = UserPrivacyService(db)
    filtered_data = service.apply_privacy_filter(
        user_data, current_user.id, target_user.id
    )

    return FilteredUserData(**filtered_data)


@router.get("/searchable/email")
def check_email_searchability(
    email: str = Query(..., description="Email to check"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Check if user with email is searchable."""
    # Find user by email
    target_user = db.query(User).filter(User.email == email).first()
    if not target_user:
        return {"searchable": False, "reason": "User not found"}

    service = UserPrivacyService(db)
    searchable = service.is_searchable_by_email(target_user.id)

    return {
        "searchable": searchable,
        "reason": "User allows email search"
        if searchable
        else "User disabled email search",
    }


@router.get("/searchable/name")
def check_name_searchability(
    name: str = Query(..., description="Name to check"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Check if users with name are searchable."""
    # Find users by name (partial match)
    users = db.query(User).filter(User.full_name.ilike(f"%{name}%")).all()

    if not users:
        return {"searchable_count": 0, "total_count": 0}

    service = UserPrivacyService(db)
    searchable_users = [
        user for user in users if service.is_searchable_by_name(user.id)
    ]

    return {
        "searchable_count": len(searchable_users),
        "total_count": len(users),
        "searchable_ids": [user.id for user in searchable_users],
    }
