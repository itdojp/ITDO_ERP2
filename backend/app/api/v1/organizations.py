"""Organization API endpoints."""

from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.core.exceptions import NotFound, ValidationError
from app.models.organization import Organization
from app.models.user import User
from app.schemas.common import DeleteResponse, ErrorResponse, PaginatedResponse
from app.schemas.organization import (
    OrganizationBasic,
    OrganizationCreate,
    OrganizationPolicy,
    OrganizationResponse,
    OrganizationSettingsResponse,
    OrganizationSettingsUpdate,
    OrganizationSummary,
    OrganizationTree,
    OrganizationUpdate,
    PermissionTemplate,
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
    search: Optional[str] = Query(None, description="Search query"),
    active_only: bool = Query(True, description="Only return active organizations"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaginatedResponse[OrganizationSummary]:
    """List organizations with pagination and filtering."""
    service = OrganizationService(db)

    # Build filters
    filters: Dict[str, Any] = {}
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
    response_model=List[OrganizationTree],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
def get_organization_tree(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
) -> List[OrganizationTree]:
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
def get_organization_subtree(
    organization_id: int = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> OrganizationTree:
    """Get organization hierarchy tree starting from a specific organization."""
    service = OrganizationService(db)
    
    # Check if organization exists
    organization = service.get_organization(organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )
    
    # Build tree from this organization
    def build_tree(org: Organization, level: int = 0) -> OrganizationTree:
        """Build tree recursively."""
        children = []
        for sub in service.get_direct_subsidiaries(org.id):
            children.append(build_tree(sub, level + 1))

        return OrganizationTree(
            id=org.id,
            code=org.code,
            name=org.name,
            is_active=org.is_active,
            level=level,
            parent_id=org.parent_id,
            children=children,
        )
    
    return build_tree(organization)


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
) -> Union[OrganizationResponse, JSONResponse]:
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
    except (ValueError, IntegrityError) as e:
        db.rollback()
        if "already exists" in str(e) or "organizations_code_key" in str(e):
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
) -> Union[OrganizationResponse, JSONResponse]:
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
    except (ValueError, IntegrityError) as e:
        db.rollback()
        if "already exists" in str(e) or "organizations_code_key" in str(e):
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
) -> Union[DeleteResponse, JSONResponse]:
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
    response_model=List[OrganizationBasic],
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
) -> List[OrganizationBasic]:
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
    "/{organization_id}/subsidiaries",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
        409: {"model": ErrorResponse, "description": "Conflict - duplicate code"},
    },
)
def add_subsidiary(
    subsidiary_data: OrganizationCreate,
    organization_id: int = Path(..., description="Parent organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> OrganizationResponse:
    """Add a new subsidiary to an organization."""
    service = OrganizationService(db)
    
    # Check permissions
    if not current_user.is_superuser:
        if not service.user_has_permission(
            current_user.id, "organizations.update", organization_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to add subsidiaries",
            )
    
    try:
        subsidiary = service.add_subsidiary(
            parent_id=organization_id,
            subsidiary_data=subsidiary_data,
            created_by=current_user.id,
        )
        return service.get_organization_response(subsidiary)
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization with this code already exists",
        )


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
) -> Union[OrganizationResponse, JSONResponse]:
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
) -> Union[OrganizationResponse, JSONResponse]:
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


@router.get(
    "/{organization_id}/statistics",
    response_model=Dict[str, Any],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    },
)
def get_organization_statistics(
    organization_id: int = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get detailed statistics for an organization."""
    service = OrganizationService(db)

    try:
        statistics = service.get_organization_statistics(organization_id)
        return statistics
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
            )
        raise


@router.get(
    "/code/{code}",
    response_model=OrganizationResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    },
)
def get_organization_by_code(
    code: str = Path(..., description="Organization code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> OrganizationResponse:
    """Get organization by unique code."""
    service = OrganizationService(db)
    organization = service.get_organization_by_code(code)

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with code '{code}' not found",
        )

    return service.get_organization_response(organization)


@router.put(
    "/{organization_id}/settings",
    response_model=OrganizationResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    },
)
def update_organization_settings(
    settings: Dict[str, Any],
    organization_id: int = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Union[OrganizationResponse, JSONResponse]:
    """Update organization-specific settings."""
    # Check permissions
    if not current_user.is_superuser:
        service = OrganizationService(db)
        if not service.user_has_permission(
            current_user.id, "organizations.update", organization_id
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to update organization settings",
                    code="PERMISSION_DENIED",
                ).model_dump(),
            )

    service = OrganizationService(db)
    organization = service.update_settings(
        organization_id, settings, updated_by=current_user.id
    )

    if not organization:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="Organization not found", code="NOT_FOUND"
            ).model_dump(),
        )

    return service.get_organization_response(organization)


@router.get(
    "/{organization_id}/settings",
    response_model=OrganizationSettingsResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    },
)
def get_organization_settings(
    organization_id: int = Path(..., description="Organization ID"),
    include_inherited: bool = Query(True, description="Include inherited settings"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> OrganizationSettingsResponse:
    """Get organization settings with inheritance support."""
    service = OrganizationService(db)

    try:
        settings = service.get_organization_settings(organization_id, include_inherited)
        return settings
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
            )
        raise


@router.put(
    "/{organization_id}/settings/update",
    response_model=OrganizationSettingsResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    },
)
def update_organization_settings_v2(
    settings_update: OrganizationSettingsUpdate,
    organization_id: int = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Union[OrganizationSettingsResponse, JSONResponse]:
    """Update organization settings (structured version)."""
    # Check permissions
    if not current_user.is_superuser:
        service = OrganizationService(db)
        if not service.user_has_permission(
            current_user.id, "organizations.update", organization_id
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to update organization settings",
                    code="PERMISSION_DENIED",
                ).model_dump(),
            )

    service = OrganizationService(db)

    try:
        settings = service.update_organization_settings(
            organization_id, settings_update, updated_by=current_user.id
        )
        return settings
    except Exception as e:
        if "not found" in str(e).lower():
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="Organization not found", code="NOT_FOUND"
                ).model_dump(),
            )
        raise


@router.get(
    "/{organization_id}/permission-templates",
    response_model=List[PermissionTemplate],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    },
)
def get_permission_templates(
    organization_id: int = Path(..., description="Organization ID"),
    role_type: Optional[str] = Query(None, description="Filter by role type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[PermissionTemplate]:
    """Get permission templates for the organization."""
    service = OrganizationService(db)

    try:
        templates = service.get_permission_templates(organization_id, role_type)
        return templates
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
            )
        raise


@router.post(
    "/{organization_id}/permission-templates",
    response_model=PermissionTemplate,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    },
)
def create_permission_template(
    template: PermissionTemplate,
    organization_id: int = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Union[PermissionTemplate, JSONResponse]:
    """Create a new permission template."""
    # Check permissions
    if not current_user.is_superuser:
        service = OrganizationService(db)
        if not service.user_has_permission(
            current_user.id, "organizations.update", organization_id
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to create permission templates",
                    code="PERMISSION_DENIED",
                ).model_dump(),
            )

    service = OrganizationService(db)

    try:
        template = service.create_permission_template(
            organization_id, template, created_by=current_user.id
        )
        return template
    except Exception as e:
        if "not found" in str(e).lower():
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="Organization not found", code="NOT_FOUND"
                ).model_dump(),
            )
        raise


@router.post(
    "/{organization_id}/permission-templates/{template_id}/apply",
    response_model=Dict[str, Any],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Organization or template not found"},
    },
)
def apply_permission_template(
    organization_id: int = Path(..., description="Organization ID"),
    template_id: int = Path(..., description="Template ID"),
    user_id: int = Query(..., description="User ID to apply template to"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Union[Dict[str, Any], JSONResponse]:
    """Apply a permission template to a user."""
    # Check permissions
    if not current_user.is_superuser:
        service = OrganizationService(db)
        if not service.user_has_permission(
            current_user.id, "organizations.update", organization_id
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to apply permission templates",
                    code="PERMISSION_DENIED",
                ).model_dump(),
            )

    service = OrganizationService(db)

    try:
        success = service.apply_permission_template(
            organization_id, user_id, template_id, updated_by=current_user.id
        )
        return {"success": success, "message": "Permission template applied successfully"}
    except Exception as e:
        if "not found" in str(e).lower():
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail=str(e), code="NOT_FOUND"
                ).model_dump(),
            )
        raise


@router.get(
    "/{organization_id}/policies",
    response_model=List[OrganizationPolicy],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    },
)
def get_organization_policies(
    organization_id: int = Path(..., description="Organization ID"),
    policy_type: Optional[str] = Query(None, description="Filter by policy type"),
    include_inherited: bool = Query(True, description="Include inherited policies"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[OrganizationPolicy]:
    """Get organization policies."""
    service = OrganizationService(db)

    try:
        policies = service.get_organization_policies(
            organization_id, policy_type, include_inherited
        )
        return policies
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
            )
        raise


@router.post(
    "/{organization_id}/policies",
    response_model=OrganizationPolicy,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    },
)
def create_organization_policy(
    policy: OrganizationPolicy,
    organization_id: int = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Union[OrganizationPolicy, JSONResponse]:
    """Create a new organization policy."""
    # Check permissions
    if not current_user.is_superuser:
        service = OrganizationService(db)
        if not service.user_has_permission(
            current_user.id, "organizations.update", organization_id
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to create organization policies",
                    code="PERMISSION_DENIED",
                ).model_dump(),
            )

    service = OrganizationService(db)

    try:
        policy = service.create_organization_policy(
            organization_id, policy, created_by=current_user.id
        )
        return policy
    except Exception as e:
        if "not found" in str(e).lower():
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="Organization not found", code="NOT_FOUND"
                ).model_dump(),
            )
        raise
