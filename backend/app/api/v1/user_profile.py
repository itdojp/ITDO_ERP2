"""User profile API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.user_profile import (
    ProfileImageUploadResponse,
    UserPrivacySettings,
    UserPrivacySettingsUpdate,
    UserProfileResponse,
    UserProfileSettings,
    UserProfileSettingsUpdate,
    UserProfileUpdate,
)
from app.services.user_profile import UserProfileService

router = APIRouter()


@router.post(
    "/users/{user_id}/profile-image",
    response_model=ProfileImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_profile_image(
    user_id: int,
    file: UploadFile = File(...),
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db),
) -> ProfileImageUploadResponse:
    """Upload user profile image."""
    # Validate file
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )

    # Read file data
    file_data = await file.read()

    service = UserProfileService(db)
    return service.upload_profile_image(
        user_id=user_id,
        file_data=file_data,
        filename=file.filename or "profile.png",
        content_type=file.content_type,
        uploader=current_user,
        db=db,
    )


@router.delete(
    "/users/{user_id}/profile-image",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_profile_image(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db),
) -> None:
    """Delete user profile image."""
    service = UserProfileService(db)
    service.delete_profile_image(
        user_id=user_id,
        deleter=current_user,
        db=db,
    )


@router.get(
    "/users/{user_id}/profile",
    response_model=UserProfileResponse,
)
async def get_user_profile(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    """Get user profile with privacy rules applied."""
    service = UserProfileService(db)
    return service.get_user_profile(
        user_id=user_id,
        viewer=current_user,
        db=db,
    )


@router.patch(
    "/users/{user_id}/profile",
    response_model=UserProfileResponse,
)
async def update_user_profile(
    user_id: int,
    data: UserProfileUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    """Update user profile information."""
    service = UserProfileService(db)
    return service.update_profile(
        user_id=user_id,
        data=data,
        updater=current_user,
        db=db,
    )


@router.get(
    "/users/{user_id}/settings/profile",
    response_model=UserProfileSettings,
)
async def get_profile_settings(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db),
) -> UserProfileSettings:
    """Get user profile settings."""
    service = UserProfileService(db)
    return service.get_profile_settings(
        user_id=user_id,
        viewer=current_user,
        db=db,
    )


@router.patch(
    "/users/{user_id}/settings/profile",
    response_model=UserProfileSettings,
)
async def update_profile_settings(
    user_id: int,
    settings: UserProfileSettingsUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db),
) -> UserProfileSettings:
    """Update user profile settings."""
    service = UserProfileService(db)
    return service.update_profile_settings(
        user_id=user_id,
        settings=settings,
        updater=current_user,
        db=db,
    )


@router.get(
    "/users/{user_id}/settings/privacy",
    response_model=UserPrivacySettings,
)
async def get_privacy_settings(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db),
) -> UserPrivacySettings:
    """Get user privacy settings."""
    service = UserProfileService(db)
    return service.get_privacy_settings(
        user_id=user_id,
        viewer=current_user,
        db=db,
    )


@router.patch(
    "/users/{user_id}/settings/privacy",
    response_model=UserPrivacySettings,
)
async def update_privacy_settings(
    user_id: int,
    settings: UserPrivacySettingsUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db),
) -> UserPrivacySettings:
    """Update user privacy settings."""
    service = UserProfileService(db)
    return service.update_privacy_settings(
        user_id=user_id,
        settings=settings,
        updater=current_user,
        db=db,
    )
