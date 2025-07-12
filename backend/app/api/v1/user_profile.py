"""User profile management API endpoints."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.core.exceptions import NotFound, PermissionDenied
from app.models.user import User
from app.schemas.user_profile import (
    ProfileImageUploadResponse,
    UserProfileResponse,
    UserProfileUpdate,
    UserSettings,
    UserPrivacySettings,
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません"
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
            status_code=status.HTTP_404_NOT_FOUND if isinstance(e, NotFound) 
                        else status.HTTP_403_FORBIDDEN,
            detail=str(e)
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
            status_code=status.HTTP_404_NOT_FOUND if isinstance(e, NotFound) 
                        else status.HTTP_403_FORBIDDEN,
            detail=str(e)
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
            detail="画像ファイルをアップロードしてください"
        )
    
    # Validate file size (max 5MB)
    if file.size and file.size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ファイルサイズは5MB以下にしてください"
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
            status_code=status.HTTP_404_NOT_FOUND if isinstance(e, NotFound) 
                        else status.HTTP_403_FORBIDDEN,
            detail=str(e)
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
            status_code=status.HTTP_404_NOT_FOUND if isinstance(e, NotFound) 
                        else status.HTTP_403_FORBIDDEN,
            detail=str(e)
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
            status_code=status.HTTP_404_NOT_FOUND if isinstance(e, NotFound) 
                        else status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )