"""User management endpoints."""

from datetime import datetime
from typing import Union, List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.dependencies import get_db, get_current_active_user, get_current_superuser
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate, PasswordChange
from app.schemas.common import PaginatedResponse, DeleteResponse
from app.schemas.error import ErrorResponse
from app.services.user import UserService
from app.core.exceptions import BusinessLogicError, NotFound, PermissionDenied


router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        409: {"model": ErrorResponse, "description": "User already exists"},
    }
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
) -> Union[UserResponse, JSONResponse]:
    """Create a new user (admin only)."""
    service = UserService(db)
    
    try:
        user = service.create_basic_user(
            user_data,
            created_by=current_user.id
        )
        
        return UserResponse.model_validate(user)
        
    except BusinessLogicError as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                detail=str(e),
                code="USER_EXISTS"
            ).model_dump()
        )
    except NotFound as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail=str(e),
                code="NOT_FOUND"
            ).model_dump()
        )
    except IntegrityError:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                detail="User with this email already exists",
                code="USER_EXISTS"
            ).model_dump()
        )


@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    }
)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """Get current user information."""
    return UserResponse.model_validate(current_user)


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    }
)
def list_users(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    search: Optional[str] = Query(None, description="Search query"),
    active_only: bool = Query(True, description="Only return active users"),
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> PaginatedResponse[UserResponse]:
    """List users with pagination and filtering."""
    service = UserService(db)
    
    # Only superusers can see all users
    if not current_user.is_superuser:
        # Regular users can only see users in their organizations
        user_orgs = [o.id for o in current_user.get_organizations()]
        if organization_id and organization_id not in user_orgs:
            # Return empty if trying to filter by org they don't belong to
            return PaginatedResponse(items=[], total=0, skip=skip, limit=limit)
        # If no org filter, we'll filter by their orgs in the service
        if not organization_id and user_orgs:
            organization_id = user_orgs[0]  # Default to first org
    
    users, total = service.list_users(
        skip=skip,
        limit=limit,
        active_only=active_only,
        organization_id=organization_id,
        department_id=department_id,
        search=search
    )
    
    return PaginatedResponse(
        items=[UserResponse.model_validate(user) for user in users],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "User not found"},
    }
)
def get_user(
    user_id: int = Path(..., description="User ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[UserResponse, JSONResponse]:
    """Get user details."""
    service = UserService(db)
    user = service.get_user(user_id)
    
    if not user:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="User not found",
                code="USER_NOT_FOUND"
            ).model_dump()
        )
    
    # Check permissions
    if not current_user.can_access_user(user):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail="Insufficient permissions to access this user",
                code="PERMISSION_DENIED"
            ).model_dump()
        )
    
    return UserResponse.model_validate(user)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "User not found"},
    }
)
def update_user(
    user_id: int = Path(..., description="User ID"),
    user_data: UserUpdate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[UserResponse, JSONResponse]:
    """Update user information."""
    service = UserService(db)
    
    # Check if user exists
    user = service.get_user(user_id)
    if not user:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="User not found",
                code="USER_NOT_FOUND"
            ).model_dump()
        )
    
    # Check permissions (users can update themselves, admins can update anyone)
    if user_id != current_user.id and not current_user.is_superuser:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail="Insufficient permissions to update this user",
                code="PERMISSION_DENIED"
            ).model_dump()
        )
    
    try:
        updated_user = service.update_basic_user(
            user_id,
            user_data,
            updated_by=current_user.id
        )
        
        if not updated_user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="User not found",
                    code="USER_NOT_FOUND"
                ).model_dump()
            )
            
        return UserResponse.model_validate(updated_user)
        
    except NotFound as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail=str(e),
                code="NOT_FOUND"
            ).model_dump()
        )


@router.delete(
    "/{user_id}",
    response_model=DeleteResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "User not found"},
    }
)
def delete_user(
    user_id: int = Path(..., description="User ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)  # Only superusers can delete
) -> Union[DeleteResponse, JSONResponse]:
    """Delete (soft delete) a user."""
    service = UserService(db)
    
    try:
        success = service.delete_user(user_id, deleted_by=current_user.id)
        
        if not success:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="User not found",
                    code="USER_NOT_FOUND"
                ).model_dump()
            )
            
        return DeleteResponse(
            success=True,
            message="User deleted successfully",
            id=user_id
        )
        
    except PermissionDenied as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED"
            ).model_dump()
        )


@router.put(
    "/{user_id}/password",
    response_model=None,
    responses={
        200: {"description": "Password changed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid password"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "User not found"},
    }
)
def change_password(
    user_id: int = Path(..., description="User ID"),
    password_data: PasswordChange = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[Dict[str, Any], JSONResponse]:
    """Change user password."""
    # Users can only change their own password
    if user_id != current_user.id:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail="You can only change your own password",
                code="PERMISSION_DENIED"
            ).model_dump()
        )
    
    service = UserService(db)
    
    try:
        service.change_user_password(
            user_id,
            password_data.current_password,
            password_data.new_password
        )
        
        return {"message": "Password changed successfully"}
        
    except NotFound as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail=str(e),
                code="USER_NOT_FOUND"
            ).model_dump()
        )
    except BusinessLogicError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                detail=str(e),
                code="INVALID_PASSWORD"
            ).model_dump()
        )