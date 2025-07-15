<<<<<<< HEAD
"""User profile management API endpoints."""
=======
"""User profile API endpoints."""

from typing import Annotated
>>>>>>> origin/main

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
<<<<<<< HEAD
from app.core.exceptions import NotFound, PermissionDenied
=======
>>>>>>> origin/main
from app.models.user import User
from app.schemas.user_profile import (
    ProfileImageUploadResponse,
    UserPrivacySettings,
<<<<<<< HEAD
    UserProfileResponse,
    UserProfileUpdate,
    UserSettings,
)
from app.services.user import UserService

router = APIRouter(prefix="/profile", tags=["User Profile"])


@router.get("/me", response_model=UserProfileResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserProfileResponse:
    """Get current user's profile."""
    service = UserService(db)

    # Get user settings and privacy settings
    settings = service.get_user_settings(current_user.id, current_user, db)
    privacy_settings = service.get_privacy_settings(current_user.id, current_user, db)

    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        profile_image_url=current_user.profile_image_url,
        settings=UserSettings(**settings),
        privacy_settings=UserPrivacySettings(**privacy_settings),
    )


@router.get("/{user_id}", response_model=UserProfileResponse)
def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserProfileResponse:
    """Get user profile by ID."""
    service = UserService(db)

    try:
        # Get user settings and privacy settings
        settings = service.get_user_settings(user_id, current_user, db)
        privacy_settings = service.get_privacy_settings(user_id, current_user, db)

        # Get the target user
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="ユーザーが見つかりません"
            )

        return UserProfileResponse(
            id=target_user.id,
            email=target_user.email,
            full_name=target_user.full_name,
            phone=target_user.phone,
            profile_image_url=target_user.profile_image_url,
            settings=UserSettings(**settings),
            privacy_settings=UserPrivacySettings(**privacy_settings),
        )
    except (NotFound, PermissionDenied) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
            if isinstance(e, NotFound)
            else status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.put("/me", response_model=UserProfileResponse)
def update_my_profile(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserProfileResponse:
    """Update current user's profile."""
    service = UserService(db)

    try:
        # Update profile
        if profile_data.profile_image_url is not None:
            service.update_profile_image(
                current_user.id, profile_data.profile_image_url, current_user, db
            )

        # Update other profile fields using existing update_user method
        from app.schemas.user_extended import UserUpdate

        update_data = UserUpdate(
            full_name=profile_data.full_name,
            phone=profile_data.phone,
        )
        service.update_user(current_user.id, update_data, current_user, db)

        # Return updated profile
        return get_my_profile(db, current_user)

    except (NotFound, PermissionDenied) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
            if isinstance(e, NotFound)
            else status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.post("/me/image", response_model=ProfileImageUploadResponse)
async def upload_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ProfileImageUploadResponse:
    """Upload profile image."""
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="画像ファイルをアップロードしてください",
        )

    # Validate file size (max 5MB)
    if file.size and file.size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ファイルサイズは5MB以下にしてください",
        )

    try:
        # In a real implementation, save file to storage (S3, local storage, etc.)
        # For now, return a mock URL
        mock_image_url = f"/static/profile_images/{current_user.id}_{file.filename}"

        service = UserService(db)
        service.update_profile_image(current_user.id, mock_image_url, current_user, db)

        return ProfileImageUploadResponse(image_url=mock_image_url)

    except (NotFound, PermissionDenied) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
            if isinstance(e, NotFound)
            else status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get("/me/settings", response_model=UserSettings)
def get_my_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserSettings:
    """Get current user's settings."""
    service = UserService(db)
    settings = service.get_user_settings(current_user.id, current_user, db)
    return UserSettings(**settings)


@router.put("/me/settings", response_model=UserSettings)
def update_my_settings(
    settings: UserSettings,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserSettings:
    """Update current user's settings."""
    service = UserService(db)

    try:
        updated_settings = service.update_user_settings(
            current_user.id, settings.model_dump(), current_user, db
        )
        return UserSettings(**updated_settings)

    except (NotFound, PermissionDenied) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
            if isinstance(e, NotFound)
            else status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get("/me/privacy", response_model=UserPrivacySettings)
def get_my_privacy_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserPrivacySettings:
    """Get current user's privacy settings."""
    service = UserService(db)
    privacy_settings = service.get_privacy_settings(current_user.id, current_user, db)
    return UserPrivacySettings(**privacy_settings)


@router.put("/me/privacy", response_model=UserPrivacySettings)
def update_my_privacy_settings(
    privacy_settings: UserPrivacySettings,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserPrivacySettings:
    """Update current user's privacy settings."""
    service = UserService(db)

    try:
        updated_privacy = service.update_privacy_settings(
            current_user.id, privacy_settings.model_dump(), current_user, db
        )
        return UserPrivacySettings(**updated_privacy)

    except (NotFound, PermissionDenied) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
            if isinstance(e, NotFound)
            else status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
=======
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
>>>>>>> origin/main
