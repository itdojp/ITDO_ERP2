"""Organization API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.common import DeleteResponse, ErrorResponse, PaginatedResponse
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
        if "organizations_code_key" in str(e):
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
        if "organizations_code_key" in str(e):
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
