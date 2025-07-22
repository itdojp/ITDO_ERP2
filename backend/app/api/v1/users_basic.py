"""
Basic User Management API for ERP v17.0
Focused on essential ERP user operations with simplified endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.schemas.user import UserCreate, UserUpdate, UserERPResponse, UserBasic
from app.models.user import User
from app.crud.user_basic import (
    create_user,
    get_user_by_id,
    get_user_by_email,
    get_users,
    update_user,
    deactivate_user,
    get_user_statistics,
    convert_to_erp_response
)

router = APIRouter(prefix="/users-basic", tags=["Users Basic"])


@router.post("/", response_model=UserERPResponse, status_code=status.HTTP_201_CREATED)
async def create_new_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new user - ERP v17.0."""
    try:
        user = create_user(db, user_data, created_by=current_user.id)
        return convert_to_erp_response(user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[UserERPResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    organization_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    sort_by: str = Query("full_name"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List users with filtering and pagination."""
    users, total = get_users(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        organization_id=organization_id,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Convert to ERP response format
    return [convert_to_erp_response(user) for user in users]


@router.get("/statistics")
async def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user statistics."""
    return get_user_statistics(db)


@router.get("/{user_id}", response_model=UserERPResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user by ID."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if current user can access this user
    if not current_user.can_access_user(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return convert_to_erp_response(user)


@router.put("/{user_id}", response_model=UserERPResponse)
async def update_user_info(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update user information."""
    # Check if user exists
    existing_user = get_user_by_id(db, user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    if not current_user.can_access_user(existing_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Update user
    updated_user = update_user(db, user_id, user_data, updated_by=current_user.id)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )
    
    return convert_to_erp_response(updated_user)


@router.post("/{user_id}/deactivate", response_model=UserERPResponse)
async def deactivate_user_account(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Deactivate user account."""
    # Check if user exists
    existing_user = get_user_by_id(db, user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions (only admins can deactivate)
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Deactivate user
    deactivated_user = deactivate_user(db, user_id, deactivated_by=current_user.id)
    if not deactivated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )
    
    return convert_to_erp_response(deactivated_user)


@router.get("/email/{email}", response_model=UserBasic)
async def get_user_by_email_endpoint(
    email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user by email address."""
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    if not current_user.can_access_user(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Return basic info only for privacy
    return UserBasic(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active
    )


@router.get("/{user_id}/context")
async def get_user_erp_context(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get ERP-specific context for user."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    if not current_user.can_access_user(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return user.get_erp_context()