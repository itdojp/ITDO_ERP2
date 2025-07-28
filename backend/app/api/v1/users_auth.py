"""User management API endpoints for authentication system."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import BusinessLogicError
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.schemas.user_auth import (
    AdminPasswordReset,
    PasswordChange,
    UserActivitySummary,
    UserAuthResponse,
    UserListResponse,
    UserMFAStatus,
    UserProfileUpdate,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> UserListResponse:
    """
    List users (admin only).

    - **skip**: Number of users to skip
    - **limit**: Maximum number of users to return
    - **search**: Search by email or name
    - **is_active**: Filter by active status
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="権限がありません",
        )

    user_service = UserService(db)
    users, total = user_service.list_users(
        skip=skip,
        limit=limit,
        search=search,
        is_active=is_active,
    )

    return UserListResponse(
        users=[UserResponse.from_orm(user) for user in users],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )


@router.post("", response_model=UserAuthResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserAuthResponse:
    """
    Create a new user (admin only).
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="権限がありません",
        )

    user_service = UserService(db)

    try:
        user = user_service.create_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            phone=user_data.phone,
            is_active=user_data.is_active,
            created_by=current_user.id,
        )
        return UserAuthResponse.from_orm(user)
    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/me", response_model=UserAuthResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserAuthResponse:
    """Get current user profile."""
    return UserAuthResponse.from_orm(current_user)


@router.put("/me/profile", response_model=UserAuthResponse)
async def update_current_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserAuthResponse:
    """Update current user profile."""
    user_service = UserService(db)

    updated_user = user_service.update_user_profile(
        user=current_user,
        profile_data=profile_data,
    )

    return UserAuthResponse.from_orm(updated_user)


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Change current user password."""
    try:
        current_user.change_password(
            db=db,
            current_password=password_data.current_password,
            new_password=password_data.new_password,
        )
        db.commit()
    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/me/mfa", response_model=UserMFAStatus)
async def get_mfa_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserMFAStatus:
    """Get current user MFA status."""
    user_service = UserService(db)
    return user_service.get_mfa_status(current_user)


@router.get("/me/activity", response_model=UserActivitySummary)
async def get_activity_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserActivitySummary:
    """Get current user activity summary."""
    user_service = UserService(db)
    return user_service.get_activity_summary(current_user)


@router.get("/{user_id}", response_model=UserAuthResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserAuthResponse:
    """
    Get user by ID.

    Regular users can only view their own profile.
    Admins can view any user.
    """
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="権限がありません",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません",
        )

    return UserAuthResponse.from_orm(user)


@router.put("/{user_id}", response_model=UserAuthResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserAuthResponse:
    """
    Update user (admin only).
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="権限がありません",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません",
        )

    # Update user fields
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return UserAuthResponse.from_orm(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete user (admin only).

    Actually performs a soft delete.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="権限がありません",
        )

    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="自分自身を削除することはできません",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません",
        )

    # Soft delete
    user.soft_delete(deleted_by=current_user.id)
    db.commit()


@router.post("/{user_id}/password-reset", status_code=status.HTTP_204_NO_CONTENT)
async def admin_reset_password(
    user_id: int,
    reset_data: AdminPasswordReset,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Reset user password (admin only).
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="権限がありません",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません",
        )

    # Reset password
    from app.core.security import hash_password

    user.hashed_password = hash_password(reset_data.new_password)
    user.password_must_change = reset_data.must_change
    user.failed_login_attempts = 0
    user.locked_until = None

    # Log activity
    user.log_activity(
        db=db,
        action="password_reset_by_admin",
        details={"admin_id": current_user.id, "must_change": reset_data.must_change},
    )

    db.commit()
