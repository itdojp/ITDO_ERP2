"""Role Management API endpoints."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.common import DeleteResponse, ErrorResponse
from app.schemas.role import (
    RoleCreate,
    RoleList,
    RoleResponse,
    RoleUpdate,
    UserRoleCreate,
    UserRoleResponse,
)
from app.services.role import RoleService

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get(
    "/",
    response_model=RoleList,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    },
)
def list_roles(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search query"),
    include_system: bool = Query(True, description="Include system roles"),
    organization_id: Optional[int] = Query(None, description="Organization context"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RoleList:
    """
    List roles with pagination and filtering.
    
    Returns a paginated list of roles with optional search and filtering.
    """
    try:
        service = RoleService()
        return service.get_roles(
            requester=current_user,
            db=db,
            organization_id=organization_id,
            page=page,
            limit=limit,
            search=search,
            include_system=include_system,
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED",
                timestamp=datetime.utcnow(),
            ).model_dump(),
        )


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Role not found"},
    },
)
def get_role(
    role_id: int = Path(..., description="Role ID"),
    organization_id: Optional[int] = Query(None, description="Organization context"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RoleResponse:
    """
    Get role details by ID.
    
    Returns detailed information about a specific role.
    """
    try:
        service = RoleService()
        role = service.get_role_by_id(
            role_id=role_id,
            requester=current_user,
            db=db,
            organization_id=organization_id,
        )
        return RoleResponse.from_orm(role)
    except Exception as e:
        if "見つかりません" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail=str(e),
                    code="NOT_FOUND",
                    timestamp=datetime.utcnow(),
                ).model_dump(),
            )
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED",
                timestamp=datetime.utcnow(),
            ).model_dump(),
        )


@router.post(
    "/",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        409: {"model": ErrorResponse, "description": "Role code already exists"},
    },
)
def create_role(
    role_data: RoleCreate,
    organization_id: Optional[int] = Query(None, description="Organization context"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RoleResponse:
    """
    Create a new role.
    
    Creates a new role with the specified permissions and metadata.
    """
    try:
        service = RoleService()
        role = service.create_role(
            data=role_data,
            user=current_user,
            db=db,
            organization_id=organization_id,
        )
        return RoleResponse.from_orm(role)
    except ValueError as e:
        if "既に存在します" in str(e):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=ErrorResponse(
                    detail=str(e),
                    code="DUPLICATE_CODE",
                    timestamp=datetime.utcnow(),
                ).model_dump(),
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED",
                timestamp=datetime.utcnow(),
            ).model_dump(),
        )


@router.put(
    "/{role_id}",
    response_model=RoleResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Role not found"},
    },
)
def update_role(
    role_id: int = Path(..., description="Role ID"),
    role_data: RoleUpdate = ...,
    organization_id: Optional[int] = Query(None, description="Organization context"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RoleResponse:
    """
    Update role details.
    
    Updates role information including name, description, and permissions.
    """
    try:
        service = RoleService()
        role = service.update_role(
            role_id=role_id,
            data=role_data,
            updater=current_user,
            db=db,
            organization_id=organization_id,
        )
        return RoleResponse.from_orm(role)
    except Exception as e:
        if "見つかりません" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail=str(e),
                    code="NOT_FOUND",
                    timestamp=datetime.utcnow(),
                ).model_dump(),
            )
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED",
                timestamp=datetime.utcnow(),
            ).model_dump(),
        )


@router.delete(
    "/{role_id}",
    response_model=DeleteResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Role not found"},
        409: {"model": ErrorResponse, "description": "Role has active assignments"},
    },
)
def delete_role(
    role_id: int = Path(..., description="Role ID"),
    organization_id: Optional[int] = Query(None, description="Organization context"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DeleteResponse:
    """
    Delete a role.
    
    Performs soft delete on the role. Cannot delete system roles or roles with active assignments.
    """
    try:
        service = RoleService()
        success = service.delete_role(
            role_id=role_id,
            deleter=current_user,
            db=db,
            organization_id=organization_id,
        )
        return DeleteResponse(
            success=success,
            message="Role deleted successfully",
            id=role_id,
        )
    except ValueError as e:
        if "削除できません" in str(e):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=ErrorResponse(
                    detail=str(e),
                    code="CANNOT_DELETE",
                    timestamp=datetime.utcnow(),
                ).model_dump(),
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        if "見つかりません" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail=str(e),
                    code="NOT_FOUND",
                    timestamp=datetime.utcnow(),
                ).model_dump(),
            )
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED",
                timestamp=datetime.utcnow(),
            ).model_dump(),
        )


@router.get(
    "/{role_id}/permissions",
    response_model=List[str],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Role not found"},
    },
)
def get_role_permissions(
    role_id: int = Path(..., description="Role ID"),
    organization_id: Optional[int] = Query(None, description="Organization context"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[str]:
    """
    Get permissions for a specific role.
    
    Returns the list of permissions granted to the role.
    """
    try:
        service = RoleService()
        return service.get_role_permissions(
            role_id=role_id,
            requester=current_user,
            db=db,
            organization_id=organization_id,
        )
    except Exception as e:
        if "見つかりません" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail=str(e),
                    code="NOT_FOUND",
                    timestamp=datetime.utcnow(),
                ).model_dump(),
            )
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED",
                timestamp=datetime.utcnow(),
            ).model_dump(),
        )


@router.put(
    "/{role_id}/permissions",
    response_model=RoleResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Role not found"},
    },
)
def update_role_permissions(
    role_id: int = Path(..., description="Role ID"),
    permissions: List[str] = ...,
    organization_id: Optional[int] = Query(None, description="Organization context"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RoleResponse:
    """
    Update permissions for a role.
    
    Updates the list of permissions granted to the role.
    """
    try:
        service = RoleService()
        role = service.update_role_permissions(
            role_id=role_id,
            permissions=permissions,
            updater=current_user,
            db=db,
            organization_id=organization_id,
        )
        return RoleResponse.from_orm(role)
    except Exception as e:
        if "見つかりません" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail=str(e),
                    code="NOT_FOUND",
                    timestamp=datetime.utcnow(),
                ).model_dump(),
            )
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED",
                timestamp=datetime.utcnow(),
            ).model_dump(),
        )


@router.post(
    "/assignments",
    response_model=UserRoleResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "User or role not found"},
        409: {"model": ErrorResponse, "description": "Role assignment already exists"},
    },
)
def assign_role_to_user(
    assignment_data: UserRoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserRoleResponse:
    """
    Assign a role to a user.
    
    Creates a new role assignment for a user within an organization/department context.
    """
    try:
        service = RoleService()
        user_role = service.assign_role_to_user(
            user_id=assignment_data.user_id,
            role_id=assignment_data.role_id,
            organization_id=assignment_data.organization_id,
            assigner=current_user,
            db=db,
            department_id=assignment_data.department_id,
            expires_at=assignment_data.expires_at,
        )
        return UserRoleResponse.from_orm(user_role)
    except ValueError as e:
        if "既に存在します" in str(e):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=ErrorResponse(
                    detail=str(e),
                    code="DUPLICATE_ASSIGNMENT",
                    timestamp=datetime.utcnow(),
                ).model_dump(),
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        if "見つかりません" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail=str(e),
                    code="NOT_FOUND",
                    timestamp=datetime.utcnow(),
                ).model_dump(),
            )
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED",
                timestamp=datetime.utcnow(),
            ).model_dump(),
        )


@router.get(
    "/assignments/users/{user_id}",
    response_model=List[UserRoleResponse],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
def get_user_roles(
    user_id: int = Path(..., description="User ID"),
    organization_id: Optional[int] = Query(None, description="Organization filter"),
    include_expired: bool = Query(False, description="Include expired assignments"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[UserRoleResponse]:
    """
    Get roles assigned to a user.
    
    Returns all role assignments for a specific user, optionally filtered by organization.
    """
    try:
        service = RoleService()
        return service.get_user_roles(
            user_id=user_id,
            requester=current_user,
            db=db,
            organization_id=organization_id,
            include_expired=include_expired,
        )
    except Exception as e:
        if "見つかりません" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail=str(e),
                    code="NOT_FOUND",
                    timestamp=datetime.utcnow(),
                ).model_dump(),
            )
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED",
                timestamp=datetime.utcnow(),
            ).model_dump(),
        )


@router.delete(
    "/assignments/users/{user_id}/roles/{role_id}",
    response_model=DeleteResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Assignment not found"},
    },
)
def remove_role_from_user(
    user_id: int = Path(..., description="User ID"),
    role_id: int = Path(..., description="Role ID"),
    organization_id: int = Query(..., description="Organization ID"),
    department_id: Optional[int] = Query(None, description="Department ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DeleteResponse:
    """
    Remove a role assignment from a user.
    
    Removes a specific role assignment for a user within the given organization/department context.
    """
    try:
        service = RoleService()
        success = service.remove_role_from_user(
            user_id=user_id,
            role_id=role_id,
            organization_id=organization_id,
            remover=current_user,
            db=db,
            department_id=department_id,
        )
        
        if not success:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="Role assignment not found",
                    code="NOT_FOUND",
                    timestamp=datetime.utcnow(),
                ).model_dump(),
            )
        
        return DeleteResponse(
            success=success,
            message="Role assignment removed successfully",
            id=f"user_{user_id}_role_{role_id}",
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED",
                timestamp=datetime.utcnow(),
            ).model_dump(),
        )


@router.get(
    "/{role_id}/users",
    response_model=List[dict],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Role not found"},
    },
)
def get_users_with_role(
    role_id: int = Path(..., description="Role ID"),
    organization_id: int = Query(..., description="Organization ID"),
    department_id: Optional[int] = Query(None, description="Department ID"),
    include_expired: bool = Query(False, description="Include expired assignments"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[dict]:
    """
    Get users with a specific role.
    
    Returns all users that have been assigned the specified role within the given context.
    """
    try:
        service = RoleService()
        users = service.get_users_with_role(
            role_id=role_id,
            organization_id=organization_id,
            requester=current_user,
            db=db,
            department_id=department_id,
            include_expired=include_expired,
        )
        
        return [
            {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
            }
            for user in users
        ]
    except Exception as e:
        if "見つかりません" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail=str(e),
                    code="NOT_FOUND",
                    timestamp=datetime.utcnow(),
                ).model_dump(),
            )
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED",
                timestamp=datetime.utcnow(),
            ).model_dump(),
        )


@router.post(
    "/check-permission",
    response_model=dict,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
def check_user_permission(
    user_id: int = Query(..., description="User ID"),
    permission: str = Query(..., description="Permission to check"),
    organization_id: int = Query(..., description="Organization ID"),
    department_id: Optional[int] = Query(None, description="Department ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Check if a user has a specific permission.
    
    Validates whether a user has the specified permission within the given organization/department context.
    """
    try:
        service = RoleService()
        has_permission = service.check_user_permission(
            user_id=user_id,
            permission=permission,
            organization_id=organization_id,
            requester=current_user,
            db=db,
            department_id=department_id,
        )
        
        return {
            "user_id": user_id,
            "permission": permission,
            "organization_id": organization_id,
            "department_id": department_id,
            "has_permission": has_permission,
        }
    except Exception as e:
        if "見つかりません" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail=str(e),
                    code="NOT_FOUND",
                    timestamp=datetime.utcnow(),
                ).model_dump(),
            )
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED",
                timestamp=datetime.utcnow(),
            ).model_dump(),
        )