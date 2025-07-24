"""Organization API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.models.department import Department
from app.models.user import User
from app.schemas.common import DeleteResponse, ErrorResponse, PaginatedResponse
from app.schemas.department import UserSummary
from app.schemas.organization import (
    OrganizationBasic,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationSummary,
    OrganizationTree,
    OrganizationUpdate,
)
from app.services.organization import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get(
    "/",
    response_model=PaginatedResponse[OrganizationSummary],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
def list_organizations(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    search: str | None = Query(None, description="Search query"),
    active_only: bool = Query(True, description="Only return active organizations"),
    industry: str | None = Query(None, description="Filter by industry"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaginatedResponse[OrganizationSummary]:
    """List organizations with pagination and filtering."""
    service = OrganizationService(db)

    # Build filters
    filters: dict[str, Any] = {}
    if active_only:
        filters["is_active"] = True
    if industry:
        filters["industry"] = industry

    # Get organizations
    if search:
        organizations, total = service.search_organizations(
            search, skip, limit, filters
        )
    else:
        organizations, total = service.list_organizations(skip, limit, filters)

    # Convert to summary
    items = [service.get_organization_summary(org) for org in organizations]

    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.get(
    "/tree",
    response_model=list[OrganizationTree],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
def get_organization_tree(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
) -> list[OrganizationTree]:
    """Get organization hierarchy tree."""
    service = OrganizationService(db)
    return service.get_organization_tree()


@router.get(
    "/{organization_id}/tree",
    response_model=OrganizationTree,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    },
)
def get_organization_tree_by_id(
    organization_id: int = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> OrganizationTree | JSONResponse:
    """Get organization hierarchy tree for a specific organization."""
    service = OrganizationService(db)

    # Check if organization exists
    organization = service.get_organization(organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    # Get organization tree for this specific organization
    tree = service.get_organization_tree_by_id(organization_id)
    if tree is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization tree not found"
        )
    return tree


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    },
)
def get_organization(
    organization_id: int = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> OrganizationResponse:
    """Get organization details."""
    service = OrganizationService(db)
    organization = service.get_organization(organization_id)

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    return service.get_organization_response(organization)


@router.post(
    "/",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        409: {
            "model": ErrorResponse,
            "description": "Organization code already exists",
        },
    },
)
def create_organization(
    organization_data: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> OrganizationResponse | JSONResponse:
    """Create a new organization (requires admin role)."""
    # Check permissions
    if not current_user.is_superuser:
        service = OrganizationService(db)
        if not service.user_has_permission(current_user.id, "organizations.create"):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to create organizations",
                    code="PERMISSION_DENIED",
                ).model_dump(),
            )

    try:
        service = OrganizationService(db)
        organization = service.create_organization(
            organization_data, created_by=current_user.id
        )
        return service.get_organization_response(organization)
    except ValueError as e:
        # Handle duplicate code validation error
        if "already exists" in str(e):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=ErrorResponse(
                    detail=str(e),
                    code="DUPLICATE_CODE",
                ).model_dump(),
            )
        raise
    except IntegrityError as e:
        db.rollback()
        # Check for duplicate code constraint
        error_str = str(e)
        if (
            "organizations_code_key" in error_str
            or "duplicate key value violates unique constraint" in error_str.lower()
            or "unique constraint" in error_str.lower()
        ):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=ErrorResponse(
                    detail=(
                        f"Organization with code '{organization_data.code}' "
                        "already exists"
                    ),
                    code="DUPLICATE_CODE",
                ).model_dump(),
            )
        raise


@router.put(
    "/{organization_id}",
    response_model=OrganizationResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
        409: {
            "model": ErrorResponse,
            "description": "Organization code already exists",
        },
    },
)
def update_organization(
    organization_id: int = Path(..., description="Organization ID"),
    *,
    organization_data: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> OrganizationResponse | JSONResponse:
    """Update organization details."""
    # Check permissions
    if not current_user.is_superuser:
        service = OrganizationService(db)
        if not service.user_has_permission(
            current_user.id, "organizations.update", organization_id
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to update this organization",
                    code="PERMISSION_DENIED",
                ).model_dump(),
            )

    try:
        service = OrganizationService(db)
        organization = service.update_organization(
            organization_id, organization_data, updated_by=current_user.id
        )

        if not organization:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="Organization not found", code="NOT_FOUND"
                ).model_dump(),
            )

        return service.get_organization_response(organization)
    except ValueError as e:
        # Handle duplicate code validation error
        if "already exists" in str(e):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=ErrorResponse(
                    detail=str(e),
                    code="DUPLICATE_CODE",
                ).model_dump(),
            )
        raise
    except IntegrityError as e:
        db.rollback()
        # Check for duplicate code constraint
        error_str = str(e)
        if (
            "organizations_code_key" in error_str
            or "duplicate key value violates unique constraint" in error_str.lower()
            or "unique constraint" in error_str.lower()
        ):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=ErrorResponse(
                    detail=(
                        f"Organization with code '{organization_data.code}' "
                        "already exists"
                    ),
                    code="DUPLICATE_CODE",
                ).model_dump(),
            )
        raise


@router.delete(
    "/{organization_id}",
    response_model=DeleteResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
        409: {
            "model": ErrorResponse,
            "description": "Organization has active subsidiaries",
        },
    },
)
def delete_organization(
    organization_id: int = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DeleteResponse | JSONResponse:
    """Delete (soft delete) an organization."""
    # Check permissions
    if not current_user.is_superuser:
        service = OrganizationService(db)
        if not service.user_has_permission(current_user.id, "organizations.delete"):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to delete organizations",
                    code="PERMISSION_DENIED",
                ).model_dump(),
            )

    service = OrganizationService(db)
    organization = service.get_organization(organization_id)

    if not organization:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="Organization not found", code="NOT_FOUND"
            ).model_dump(),
        )

    # Check for active subsidiaries
    if service.has_active_subsidiaries(organization_id):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                detail="Cannot delete organization with active subsidiaries",
                code="HAS_SUBSIDIARIES",
            ).model_dump(),
        )

    # Perform soft delete
    success = service.delete_organization(organization_id, deleted_by=current_user.id)

    return DeleteResponse(
        success=success, message="Organization deleted successfully", id=organization_id
    )


@router.get(
    "/{organization_id}/subsidiaries",
    response_model=list[OrganizationBasic],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    },
)
def get_subsidiaries(
    organization_id: int = Path(..., description="Organization ID"),
    recursive: bool = Query(False, description="Get all subsidiaries recursively"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[OrganizationBasic]:
    """Get subsidiaries of an organization."""
    service = OrganizationService(db)

    # Check if organization exists
    if not service.get_organization(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    if recursive:
        subsidiaries = service.get_all_subsidiaries(organization_id)
    else:
        subsidiaries = service.get_direct_subsidiaries(organization_id)

    return [OrganizationBasic.model_validate(sub.to_dict()) for sub in subsidiaries]


@router.post(
    "/{organization_id}/activate",
    response_model=OrganizationResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    },
)
def activate_organization(
    organization_id: int = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> OrganizationResponse | JSONResponse:
    """Activate an inactive organization."""
    # Check permissions
    if not current_user.is_superuser:
        service = OrganizationService(db)
        if not service.user_has_permission(current_user.id, "organizations.activate"):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to activate organizations",
                    code="PERMISSION_DENIED",
                ).model_dump(),
            )

    service = OrganizationService(db)
    organization = service.activate_organization(
        organization_id, updated_by=current_user.id
    )

    if not organization:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="Organization not found", code="NOT_FOUND"
            ).model_dump(),
        )

    return service.get_organization_response(organization)


@router.post(
    "/{organization_id}/deactivate",
    response_model=OrganizationResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    },
)
def deactivate_organization(
    organization_id: int = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> OrganizationResponse | JSONResponse:
    """Deactivate an active organization."""
    # Check permissions
    if not current_user.is_superuser:
        service = OrganizationService(db)
        if not service.user_has_permission(current_user.id, "organizations.deactivate"):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to deactivate organizations",
                    code="PERMISSION_DENIED",
                ).model_dump(),
            )

    service = OrganizationService(db)
    organization = service.deactivate_organization(
        organization_id, updated_by=current_user.id
    )

    if not organization:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="Organization not found", code="NOT_FOUND"
            ).model_dump(),
        )

    return service.get_organization_response(organization)


# Organization User Management APIs


@router.get(
    "/{organization_id}/users",
    response_model=PaginatedResponse[UserSummary],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    },
)
def get_organization_users(
    organization_id: int = Path(..., description="Organization ID"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    active_only: bool = Query(True, description="Only return active users"),
    department_id: int | None = Query(None, description="Filter by department"),
    search: str | None = Query(None, description="Search by name or email"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaginatedResponse[Any] | JSONResponse:
    """Get users within an organization."""
    service = OrganizationService(db)

    # Check if organization exists
    organization = service.get_organization(organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    # Check permissions
    if not current_user.is_superuser:
        if not service.user_has_permission(
            current_user.id, "organizations.read", organization_id
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to view organization users",
                    code="PERMISSION_DENIED",
                ).model_dump(),
            )

    # Build filters
    filters = {"organization_id": organization_id}
    if active_only:
        filters["is_active"] = True
    if department_id:
        filters["department_id"] = department_id

    # Get users using direct database query since UserService has different interface
    # Use the organization_id property to filter users
    users_query = db.query(User).all()
    organization_users = [
        user for user in users_query if user.organization_id == organization_id
    ]

    # Apply filters
    if active_only:
        organization_users = [user for user in organization_users if user.is_active]
    if department_id:
        organization_users = [
            user for user in organization_users if user.department_id == department_id
        ]
    if search:
        search_term = search.lower()
        organization_users = [
            user
            for user in organization_users
            if search_term in user.full_name.lower()
            or search_term in user.email.lower()
        ]

    total = len(organization_users)
    users = organization_users[skip : skip + limit]

    # Convert to summary format

    user_summaries = []
    for user in users:
        department_name = None
        if user.department_id:
            department = (
                db.query(Department).filter(Department.id == user.department_id).first()
            )
            if department:
                department_name = department.name

        user_summaries.append(
            UserSummary(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                phone=user.phone,
                is_active=user.is_active,
                department_id=user.department_id,
                department_name=department_name,
            )
        )

    return PaginatedResponse[UserSummary](
        items=user_summaries,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit,
    )
