"""
Basic Organization Management API for ERP v17.0
Focused on essential organization operations with simplified endpoints
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.crud.organization_basic import (
    convert_to_response,
    create_organization,
    deactivate_organization,
    get_organization_by_code,
    get_organization_by_id,
    get_organization_hierarchy,
    get_organization_statistics,
    get_organizations,
    get_root_organizations,
    update_organization,
)
from app.models.user import User
from app.schemas.organization_basic import (
    OrganizationBasic,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)

router = APIRouter(prefix="/organizations-basic", tags=["Organizations Basic"])


@router.post(
    "/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED
)
async def create_new_organization(
    org_data: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new organization - ERP v17.0."""
    # Only superusers can create organizations
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    try:
        organization = create_organization(db, org_data, created_by=current_user.id)
        return convert_to_response(organization)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[OrganizationResponse])
async def list_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    parent_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List organizations with filtering and pagination."""
    organizations, total = get_organizations(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        parent_id=parent_id,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    # Convert to response format
    return [convert_to_response(org) for org in organizations]


@router.get("/roots", response_model=List[OrganizationBasic])
async def list_root_organizations(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """Get all root organizations (no parent)."""
    root_orgs = get_root_organizations(db)

    return [
        OrganizationBasic(id=org.id, code=org.code, name=org.name) for org in root_orgs
    ]


@router.get("/statistics")
async def get_organization_stats(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """Get organization statistics."""
    return get_organization_statistics(db)


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get organization by ID."""
    organization = get_organization_by_id(db, org_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    return convert_to_response(organization)


@router.get("/{org_id}/hierarchy")
async def get_organization_hierarchy_info(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get organization with hierarchy information."""
    hierarchy_info = get_organization_hierarchy(db, org_id)
    if not hierarchy_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    return {
        "organization": convert_to_response(hierarchy_info["organization"]),
        "hierarchy_path": hierarchy_info["hierarchy_path"],
        "children": hierarchy_info["children"],
        "level": hierarchy_info["level"],
    }


@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization_info(
    org_id: int,
    org_data: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update organization information."""
    # Check if organization exists
    existing_org = get_organization_by_id(db, org_id)
    if not existing_org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    # Check permissions - only superuser or org members can update
    if not current_user.is_superuser:
        # Check if user belongs to this organization
        user_orgs = [org.id for org in current_user.get_organizations()]
        if org_id not in user_orgs:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

    try:
        updated_org = update_organization(
            db, org_id, org_data, updated_by=current_user.id
        )
        if not updated_org:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update organization",
            )

        return convert_to_response(updated_org)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{org_id}/deactivate", response_model=OrganizationResponse)
async def deactivate_organization_account(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Deactivate organization."""
    # Only superusers can deactivate organizations
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    # Check if organization exists
    existing_org = get_organization_by_id(db, org_id)
    if not existing_org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    try:
        deactivated_org = deactivate_organization(
            db, org_id, deactivated_by=current_user.id
        )
        if not deactivated_org:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deactivate organization",
            )

        return convert_to_response(deactivated_org)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/code/{code}", response_model=OrganizationBasic)
async def get_organization_by_code_endpoint(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get organization by code."""
    organization = get_organization_by_code(db, code)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    return OrganizationBasic(
        id=organization.id, code=organization.code, name=organization.name
    )


@router.get("/{org_id}/context")
async def get_organization_erp_context(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get ERP-specific context for organization."""
    organization = get_organization_by_id(db, org_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    return organization.get_erp_context()
