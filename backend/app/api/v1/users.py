"""User management endpoints."""

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_current_superuser, get_db
from app.models.user import User
from app.schemas.error import ErrorResponse
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        409: {"model": ErrorResponse, "description": "User already exists"},
    },
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> UserResponse | JSONResponse:
    """Create a new user (admin only)."""
    try:
        # Create user
        user = User.create(
            db,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            is_active=user_data.is_active,
        )
        db.commit()
        db.refresh(user)

        return UserResponse.model_validate(user)

    except IntegrityError:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                detail="User with this email already exists",
                code="USER001",
            ).model_dump(),
        )


@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Get current user information."""
    return UserResponse.model_validate(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
def update_current_user_profile(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Update current user profile."""
    # Update user fields
    if user_data.full_name is not None:
        current_user.full_name = user_data.full_name
    if user_data.phone is not None:
        current_user.phone = user_data.phone
    if user_data.profile_image_url is not None:
        current_user.profile_image_url = user_data.profile_image_url

    db.commit()
    db.refresh(current_user)

    return UserResponse.model_validate(current_user)


@router.post(
    "/me/profile-image",
    response_model=dict[str, Any],
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        413: {"model": ErrorResponse, "description": "File too large"},
    },
)
async def upload_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Upload profile image for current user."""
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, and GIF images are allowed"
        )

    # Validate file size (5MB max)
    max_size = 5 * 1024 * 1024  # 5MB
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size must be less than 5MB"
        )

    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads/profile-images")
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_extension = Path(file.filename or "").suffix
    filename = f"user_{current_user.id}_{int(os.urandom(4).hex(), 16)}{file_extension}"
    file_path = upload_dir / filename

    # Save file
    with open(file_path, "wb") as f:
        f.write(contents)

    # Update user profile image URL
    profile_image_url = f"/uploads/profile-images/{filename}"
    current_user.profile_image_url = profile_image_url
    db.commit()

    return {
        "message": "Profile image uploaded successfully",
        "profile_image_url": profile_image_url,
        "filename": filename
    }
