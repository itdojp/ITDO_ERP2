"""User management endpoints."""

from typing import Union

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_current_superuser, get_db
from app.models.user import User
from app.schemas.error import ErrorResponse
from app.schemas.user import UserCreate, UserResponse

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
) -> Union[UserResponse, JSONResponse]:
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
