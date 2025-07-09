"""Enhanced Organization API endpoints for Sprint 2."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.common import ErrorResponse, PaginatedResponse
from app.schemas.organization import OrganizationBasic, OrganizationSummary
from app.services.organization import OrganizationService

# Enhanced router for new endpoints
enhanced_router = APIRouter(prefix="/organizations", tags=["organizations-enhanced"])


@enhanced_router.get(
    "/hierarchy/{organization_id}",
    response_model=List[OrganizationBasic],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    },
)
def get_organization_hierarchy(
    organization_id: int = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[OrganizationBasic]:
    """Get full hierarchy path for an organization."""
    service = OrganizationService(db)

    if not service.get_organization(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    hierarchy = service.get_organization_hierarchy(organization_id)
    return [OrganizationBasic.model_validate(org.to_dict()) for org in hierarchy]


@enhanced_router.get(
    "/search",
    response_model=PaginatedResponse[OrganizationSummary],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
def search_organizations_advanced(
    query: str = Query(..., description="Search query"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    has_subsidiaries: Optional[bool] = Query(None, description="Filter by subsidiary status"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaginatedResponse[OrganizationSummary]:
    """Advanced search organizations with multiple criteria."""
    service = OrganizationService(db)

    # Use repository's advanced search
    organizations = service.repository.get_organizations_by_criteria(
        tenant_id=tenant_id,
        industry=industry,
        is_active=is_active,
        has_subsidiaries=has_subsidiaries,
        skip=skip,
        limit=limit,
    )

    # Filter by search query if provided
    if query:
        search_results, _ = service.search_organizations(query, 0, 1000)
        search_ids = set(org.id for org in search_results)
        organizations = [org for org in organizations if org.id in search_ids]

    # Get total count for pagination
    total = len(organizations)

    # Convert to summary
    items = [service.get_organization_summary(org) for org in organizations]

    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@enhanced_router.get(
    "/requiring-attention",
    response_model=List[OrganizationSummary],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    },
)
def get_organizations_requiring_attention(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[OrganizationSummary]:
    """Get organizations that may require attention (admin only)."""
    # Check admin permissions
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to access this endpoint",
        )

    service = OrganizationService(db)
    organizations = service.repository.get_organizations_requiring_attention()

    return [service.get_organization_summary(org) for org in organizations]


@enhanced_router.get(
    "/depth/max",
    response_model=Dict[str, int],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
def get_max_hierarchy_depth(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, int]:
    """Get maximum hierarchy depth in the system."""
    service = OrganizationService(db)
    max_depth = service.repository.get_max_hierarchy_depth()

    return {"max_depth": max_depth}


@enhanced_router.post(
    "/bulk/status",
    response_model=Dict[str, Any],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    },
)
def bulk_update_organization_status(
    organization_ids: List[int],
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Bulk update organization status (admin only)."""
    # Check admin permissions
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to bulk update organizations",
        )

    service = OrganizationService(db)
    updated_count = service.repository.bulk_update_status(organization_ids, is_active)

    return {
        "updated_count": updated_count,
        "total_requested": len(organization_ids),
        "status": "active" if is_active else "inactive",
    }


@enhanced_router.get(
    "/{organization_id}/tree",
    response_model=Dict[str, Any],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    },
)
def get_organization_subsidiary_tree(
    organization_id: int = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get complete subsidiary tree for an organization."""
    service = OrganizationService(db)

    if not service.get_organization(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    tree = service.repository.get_subsidiary_tree(organization_id)
    return tree


@enhanced_router.get(
    "/{organization_id}/depth",
    response_model=Dict[str, int],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    },
)
def get_organization_depth(
    organization_id: int = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, int]:
    """Get organization depth in hierarchy."""
    service = OrganizationService(db)

    if not service.get_organization(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    depth = service.repository.get_organization_depth(organization_id)
    return {"depth": depth}


@enhanced_router.get(
    "/tenant/{tenant_id}",
    response_model=List[OrganizationSummary],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    },
)
def get_organizations_by_tenant(
    tenant_id: str = Path(..., description="Tenant ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[OrganizationSummary]:
    """Get all organizations for a specific tenant (admin only)."""
    # Check admin permissions
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to access tenant data",
        )

    service = OrganizationService(db)
    organizations = service.repository.get_by_tenant_id(tenant_id)

    return [service.get_organization_summary(org) for org in organizations]


@enhanced_router.post(
    "/{organization_id}/validate-parent",
    response_model=Dict[str, bool],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    },
)
def validate_parent_assignment(
    organization_id: int = Path(..., description="Organization ID"),
    parent_id: int = Query(..., description="Proposed parent ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, bool]:
    """Validate if parent assignment would be valid (no circular reference)."""
    service = OrganizationService(db)

    if not service.get_organization(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    if not service.get_organization(parent_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Parent organization not found"
        )

    is_valid = service.repository.validate_parent_assignment(organization_id, parent_id)

    return {"is_valid": is_valid}
