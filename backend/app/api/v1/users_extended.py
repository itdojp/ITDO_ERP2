"""Extended user management API endpoints."""

import csv
import io
from datetime import datetime
from typing import Any, Dict, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_current_superuser, get_db
from app.core.exceptions import BusinessLogicError, NotFoundError, PermissionDeniedError
from app.models.user import User
from app.schemas.error import ErrorResponse
from app.schemas.user_extended import (
    BulkImportRequest,
    BulkImportResponse,
    PasswordChange,
    PermissionListResponse,
    RoleAssignment,
    UserActivityListResponse,
    UserCreateExtended,
    UserListResponse,
    UserResponseExtended,
    UserSearchParams,
    UserUpdate,
)
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "",
    response_model=UserResponseExtended,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        409: {"model": ErrorResponse, "description": "User already exists"},
    },
)
def create_user_extended(
    user_data: UserCreateExtended,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Union[UserResponseExtended, JSONResponse]:
    """Create a new user with organization and role assignment."""
    service = UserService(db)

    try:
        user = service.create_user(
            data=user_data,
            creator=current_user,
            db=db
        )
        db.commit()

        return service._user_to_extended_response(user, db)

    except PermissionDeniedError as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="INSUFFICIENT_PERMISSIONS",
                timestamp=datetime.utcnow()
            ).model_dump()
        )
    except Exception as e:
        db.rollback()
        if "already exists" in str(e):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=ErrorResponse(
                    detail="User with this email already exists",
                    code="USER_ALREADY_EXISTS",
                    timestamp=datetime.utcnow()
                ).model_dump()
            )
        raise


@router.get(
    "",
    response_model=UserListResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Access denied"},
    },
)
def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    organization_id: Optional[int] = None,
    department_id: Optional[int] = None,
    role_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserListResponse:
    """List users with filtering and pagination."""
    service = UserService(db)

    # Build search params
    search_params = UserSearchParams(
        search=search,
        organization_id=organization_id,
        department_id=department_id,
        role_id=role_id,
        is_active=is_active
    )

    result = service.search_users(
        params=search_params,
        searcher=current_user,
        db=db
    )

    # Override pagination from query params
    result.page = page
    result.limit = limit

    return result


@router.get(
    "/{user_id}",
    response_model=UserResponseExtended,
    responses={
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Union[UserResponseExtended, JSONResponse]:
    """Get user details with roles and organizations."""
    service = UserService(db)

    try:
        return service.get_user_detail(
            user_id=user_id,
            viewer=current_user,
            db=db
        )
    except NotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="User not found",
                code="USER_NOT_FOUND",
                timestamp=datetime.utcnow()
            ).model_dump()
        )
    except PermissionDeniedError:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail="Access denied",
                code="ACCESS_DENIED",
                timestamp=datetime.utcnow()
            ).model_dump()
        )


@router.put(
    "/{user_id}",
    response_model=UserResponseExtended,
    responses={
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Union[UserResponseExtended, JSONResponse]:
    """Update user information."""
    service = UserService(db)

    try:
        user = service.update_user(
            user_id=user_id,
            data=user_data,
            updater=current_user,
            db=db
        )
        db.commit()

        # Log activity
        user.log_activity(
            db,
            action="profile_update",
            details=user_data.model_dump(exclude_unset=True)
        )

        return service._user_to_extended_response(user, db)

    except NotFoundError:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="User not found",
                code="USER_NOT_FOUND",
                timestamp=datetime.utcnow()
            ).model_dump()
        )
    except PermissionDeniedError:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail="Access denied",
                code="ACCESS_DENIED",
                timestamp=datetime.utcnow()
            ).model_dump()
        )


@router.put(
    "/{user_id}/password",
    response_model=Dict[str, Any],
    responses={
        400: {"model": ErrorResponse, "description": "Invalid password"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
def change_password(
    user_id: int,
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Union[Dict[str, Any], JSONResponse]:
    """Change user password."""
    service = UserService(db)

    try:
        service.change_password(
            user_id=user_id,
            current_password=password_data.current_password,
            new_password=password_data.new_password,
            changer=current_user,
            db=db
        )
        db.commit()

        return {"message": "パスワードが変更されました"}

    except BusinessLogicError as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                detail=str(e),
                code="INVALID_PASSWORD",
                timestamp=datetime.utcnow()
            ).model_dump()
        )
    except PermissionDeniedError:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail="Access denied",
                code="ACCESS_DENIED",
                timestamp=datetime.utcnow()
            ).model_dump()
        )


@router.post(
    "/{user_id}/password/reset",
    response_model=Dict[str, Any],
    responses={
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
def reset_password(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Union[Dict[str, Any], JSONResponse]:
    """Reset user password (admin only)."""
    service = UserService(db)

    try:
        temp_password = service.reset_password(
            user_id=user_id,
            resetter=current_user,
            db=db
        )
        db.commit()

        return {"temporary_password": temp_password}

    except NotFoundError:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="User not found",
                code="USER_NOT_FOUND",
                timestamp=datetime.utcnow()
            ).model_dump()
        )
    except PermissionDeniedError:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail="Access denied",
                code="ACCESS_DENIED",
                timestamp=datetime.utcnow()
            ).model_dump()
        )


@router.post(
    "/{user_id}/roles",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    responses={
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "User or role not found"},
    },
)
def assign_role(
    user_id: int,
    assignment: RoleAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Union[Dict[str, Any], JSONResponse]:
    """Assign role to user."""
    service = UserService(db)

    try:
        service.assign_role(
            user_id=user_id,
            role_id=assignment.role_id,
            organization_id=assignment.organization_id,
            assigner=current_user,
            db=db,
            department_id=assignment.department_id,
            expires_at=assignment.expires_at,
        )
        db.commit()

        # Build response
        from app.models.role import Role
        role = db.query(Role).filter(Role.id == assignment.role_id).first()

        if not role:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="Role not found",
                    code="ROLE_NOT_FOUND"
                ).model_dump()
            )

        response = {
            "role": {
                "id": role.id,
                "code": role.code,
                "name": role.name,
            },
            "organization_id": assignment.organization_id,
            "department_id": assignment.department_id,
            "expires_at": assignment.expires_at.isoformat() if assignment.expires_at else None,
        }

        return response

    except NotFoundError as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail=str(e),
                code="NOT_FOUND",
                timestamp=datetime.utcnow()
            ).model_dump()
        )
    except PermissionDeniedError:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail="Access denied",
                code="ACCESS_DENIED",
                timestamp=datetime.utcnow()
            ).model_dump()
        )


@router.delete(
    "/{user_id}/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Role assignment not found"},
    },
)
def remove_role(
    user_id: int,
    role_id: int,
    organization_id: int = Query(..., description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Remove role from user."""
    service = UserService(db)

    try:
        service.remove_role(
            user_id=user_id,
            role_id=role_id,
            organization_id=organization_id,
            remover=current_user,
            db=db
        )
        db.commit()

    except PermissionDeniedError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )


@router.get(
    "/{user_id}/permissions",
    response_model=PermissionListResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
def get_user_permissions(
    user_id: int,
    organization_id: int = Query(..., description="Organization context"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PermissionListResponse:
    """Get user's effective permissions in organization."""
    service = UserService(db)

    # Permission check - user can view own permissions
    if current_user.id != user_id and not current_user.is_superuser:
        # Check if viewer has permission in the organization
        viewer_orgs = [o.id for o in current_user.get_organizations()]
        if organization_id not in viewer_orgs:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

    try:
        permissions = service.get_user_permissions(
            user_id=user_id,
            organization_id=organization_id,
            db=db
        )

        return PermissionListResponse(
            permissions=permissions,
            organization_id=organization_id
        )

    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: {"model": ErrorResponse, "description": "Cannot delete self"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> None:
    """Soft delete user (admin only)."""
    service = UserService(db)

    try:
        service.delete_user(
            user_id=user_id,
            deleter=current_user,
            db=db
        )
        db.commit()

    except BusinessLogicError as e:
        db.rollback()
        if "自分自身" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete self",
                headers={"X-Error-Code": "CANNOT_DELETE_SELF"}
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.post(
    "/import",
    response_model=BulkImportResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Access denied"},
    },
)
def bulk_import_users(
    import_data: BulkImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BulkImportResponse:
    """Bulk import users."""
    service = UserService(db)

    try:
        # Convert import data to dict format
        users_data = [
            {
                "email": user.email,
                "full_name": user.full_name,
                "phone": user.phone,
            }
            for user in import_data.users
        ]

        result = service.bulk_import_users(
            data=users_data,
            organization_id=import_data.organization_id,
            role_id=import_data.role_id,
            importer=current_user,
            db=db
        )
        db.commit()

        return result

    except PermissionDeniedError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )


@router.get(
    "/export",
    response_model=None,
    responses={
        403: {"model": ErrorResponse, "description": "Access denied"},
    },
)
def export_users(
    organization_id: int = Query(..., description="Organization to export"),
    format: str = Query("csv", pattern="^(csv|xlsx|json)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Union[StreamingResponse, JSONResponse]:
    """Export user list."""
    service = UserService(db)

    try:
        export_data = service.export_users(
            organization_id=organization_id,
            format=format,
            exporter=current_user,
            db=db
        )

        if format == "csv":
            # Create CSV content
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(export_data["headers"])
            writer.writerows(export_data["rows"])

            return StreamingResponse(
                io.BytesIO(output.getvalue().encode()),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=users_{organization_id}_{datetime.now().strftime('%Y%m%d')}.csv"
                }
            )

        # For other formats, return the data structure
        return JSONResponse(content=export_data)

    except PermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )


@router.get(
    "/{user_id}/activities",
    response_model=UserActivityListResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
def get_user_activities(
    user_id: int,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserActivityListResponse:
    """Get user activity log."""
    # Permission check - user can view own activities
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get activities
    from app.models.user_activity_log import UserActivityLog
    from app.schemas.user_extended import UserActivity

    activities = db.query(UserActivityLog).filter(
        UserActivityLog.user_id == user_id
    ).order_by(UserActivityLog.created_at.desc()).limit(limit).all()

    return UserActivityListResponse(
        items=[
            UserActivity(
                action=a.action,
                details=a.details,
                ip_address=a.ip_address,
                created_at=a.created_at
            )
            for a in activities
        ],
        total=len(activities)
    )
