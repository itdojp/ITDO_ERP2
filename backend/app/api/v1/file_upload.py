"""File upload API endpoints."""

from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.common import DeleteResponse, ErrorResponse
from app.services.file_upload import FileUploadService
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["file-upload"])


@router.post(
    "/me/profile-image",
    response_model=Dict[str, Any],
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        413: {"model": ErrorResponse, "description": "File too large"},
    },
)
async def upload_profile_image(
    file: UploadFile = File(..., description="Profile image file"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Upload user's profile image.

    Supported formats: JPEG, PNG, GIF, WebP
    Maximum file size: 5MB
    """
    upload_service = FileUploadService()
    user_service = UserService(db)

    # Upload file
    result = await upload_service.upload_profile_image(file, current_user.id)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    # Update user's profile image URL in database
    try:
        user_service.update_user_profile_image(
            current_user.id,
            result["url"]
        )
        db.commit()
    except Exception as e:
        # If database update fails, clean up uploaded file
        upload_service.delete_file(result["file_path"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile image: {str(e)}"
        )

    return {
        "success": True,
        "message": "Profile image uploaded successfully",
        "filename": result["filename"],
        "url": result["url"],
        "size": result["size"]
    }


@router.delete(
    "/me/profile-image",
    response_model=DeleteResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "No profile image found"},
    },
)
async def delete_profile_image(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DeleteResponse:
    """Delete user's current profile image."""
    user_service = UserService(db)
    upload_service = FileUploadService()

    # Get current profile image URL
    if not current_user.profile_image_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No profile image found"
        )

    # Extract filename from URL
    filename = Path(current_user.profile_image_url).name
    file_path = upload_service.upload_dir / filename

    # Delete file from disk
    upload_service.delete_file(str(file_path))

    # Remove profile image URL from database
    try:
        user_service.update_user_profile_image(current_user.id, None)
        db.commit()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove profile image reference: {str(e)}"
        )

    return DeleteResponse(
        success=True,
        message="Profile image deleted successfully",
        id=current_user.id
    )


# Static file serving endpoint
file_router = APIRouter()


@file_router.get("/uploads/{filename}")
async def get_uploaded_file(filename: str) -> FileResponse:
    """Serve uploaded files."""
    upload_service = FileUploadService()
    file_path = upload_service.upload_dir / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Determine media type based on file extension
    media_type_mapping = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
    }

    file_extension = file_path.suffix.lower()
    media_type = media_type_mapping.get(file_extension, 'application/octet-stream')

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename
    )
