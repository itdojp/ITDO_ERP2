"""Cross-tenant permissions API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.core.exceptions import BusinessLogicError, NotFound, PermissionDenied
from app.models.user import User
from app.schemas.cross_tenant_permissions import (
    BatchCrossTenantPermissionCheck,
    BatchCrossTenantPermissionResult,
    CrossTenantPermissionCheck,
    CrossTenantPermissionResult,
    CrossTenantPermissionRule,
    CrossTenantPermissionRuleCreate,
    CrossTenantPermissionRuleUpdate,
    OrganizationCrossTenantSummary,
    UserCrossTenantAccess,
)
from app.services.cross_tenant_permissions import CrossTenantPermissionService

router = APIRouter()


def get_client_info(request: Request) -> tuple[str, str]:
    """Extract client IP and user agent from request."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")
    return ip_address, user_agent


@router.post("/rules", response_model=CrossTenantPermissionRule)
def create_cross_tenant_rule(
    rule_data: CrossTenantPermissionRuleCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CrossTenantPermissionRule:
    """Create a new cross-tenant permission rule."""
    service = CrossTenantPermissionService(db)
    try:
        return service.create_permission_rule(rule_data, current_user)
    except (NotFound, PermissionDenied, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/rules/{rule_id}", response_model=CrossTenantPermissionRule)
def update_cross_tenant_rule(
    rule_id: int,
    update_data: CrossTenantPermissionRuleUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CrossTenantPermissionRule:
    """Update an existing cross-tenant permission rule."""
    service = CrossTenantPermissionService(db)
    try:
        return service.update_permission_rule(rule_id, update_data, current_user)
    except (NotFound, PermissionDenied, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/rules/{rule_id}")
def delete_cross_tenant_rule(
    rule_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Delete a cross-tenant permission rule."""
    service = CrossTenantPermissionService(db)
    try:
        service.delete_permission_rule(rule_id, current_user)
        return {"message": "Rule deleted successfully"}
    except (NotFound, PermissionDenied, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/check", response_model=CrossTenantPermissionResult)
def check_cross_tenant_permission(
    check_data: CrossTenantPermissionCheck,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CrossTenantPermissionResult:
    """Check if a user has cross-tenant permission."""
    # Only allow users to check their own permissions or superusers to check any
    if not current_user.is_superuser and current_user.id != check_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to check user permissions",
        )

    service = CrossTenantPermissionService(db)
    ip_address, user_agent = get_client_info(request)

    try:
        return service.check_cross_tenant_permission(
            user_id=check_data.user_id,
            source_organization_id=check_data.source_organization_id,
            target_organization_id=check_data.target_organization_id,
            permission=check_data.permission,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except (NotFound, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/batch-check", response_model=BatchCrossTenantPermissionResult)
def batch_check_cross_tenant_permissions(
    check_data: BatchCrossTenantPermissionCheck,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> BatchCrossTenantPermissionResult:
    """Check multiple cross-tenant permissions in batch."""
    # Only allow users to check their own permissions or superusers to check any
    if not current_user.is_superuser and current_user.id != check_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to check user permissions",
        )

    service = CrossTenantPermissionService(db)
    ip_address, user_agent = get_client_info(request)

    try:
        return service.batch_check_permissions(
            user_id=check_data.user_id,
            source_organization_id=check_data.source_organization_id,
            target_organization_id=check_data.target_organization_id,
            permissions=check_data.permissions,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except (NotFound, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/users/{user_id}/access", response_model=UserCrossTenantAccess)
def get_user_cross_tenant_access(
    user_id: int,
    source_organization_id: int = Query(..., description="Source organization ID"),
    target_organization_id: int = Query(..., description="Target organization ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserCrossTenantAccess:
    """Get comprehensive cross-tenant access information for a user."""
    # Only allow users to view their own access or superusers to view any
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view user access",
        )

    service = CrossTenantPermissionService(db)
    try:
        return service.get_user_cross_tenant_access(
            user_id=user_id,
            source_organization_id=source_organization_id,
            target_organization_id=target_organization_id,
        )
    except (NotFound, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/organizations/{organization_id}/summary",
    response_model=OrganizationCrossTenantSummary,
)
def get_organization_cross_tenant_summary(
    organization_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> OrganizationCrossTenantSummary:
    """Get cross-tenant permission summary for an organization."""

    # Check organization-level permissions
    if not current_user.is_superuser:
        # Check if user has permission in this organization
        user_orgs = [org.id for org in current_user.get_organizations()]
        if organization_id not in user_orgs:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view organization summary",
            )

    # TODO: Add proper organization-level permission checking
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view organization summary",
        )


    service = CrossTenantPermissionService(db)
    try:
        return service.get_organization_cross_tenant_summary(organization_id)
    except (NotFound, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/cleanup-expired")
def cleanup_expired_rules(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    """Clean up expired cross-tenant permission rules."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can run cleanup operations",
        )

    service = CrossTenantPermissionService(db)
    cleaned_count = service.cleanup_expired_rules()

    return {"cleaned_count": cleaned_count}


# Convenience endpoints for common operations


@router.get("/users/{user_id}/cross-tenant-organizations")
def get_user_cross_tenant_organizations(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, list]:
    """Get organizations that user can access via cross-tenant permissions."""
    # Only allow users to view their own access or superusers to view any
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view user access",
        )

    # This is a simplified implementation
    # In a real scenario, you'd query all organizations where the user has
    # cross-tenant access based on their memberships and existing rules

    return {
        "accessible_organizations": [],
        "source_organizations": [],
        "message": "Cross-tenant organization access requires specific permission "
        "checks",
    }


@router.post("/quick-check")
def quick_permission_check(
    request: Request,
    user_id: int = Query(..., description="User ID"),
    source_org_id: int = Query(..., description="Source organization ID"),
    target_org_id: int = Query(..., description="Target organization ID"),
    permission: str = Query(..., description="Permission to check"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    """Quick permission check endpoint."""
    # Only allow users to check their own permissions or superusers to check any
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to check user permissions",
        )

    service = CrossTenantPermissionService(db)
    ip_address, user_agent = get_client_info(request)

    try:
        result = service.check_cross_tenant_permission(
            user_id=user_id,
            source_organization_id=source_org_id,
            target_organization_id=target_org_id,
            permission=permission,
            log_check=False,  # Don't log quick checks
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return {
            "allowed": result.allowed,
            "reason": result.reason,
        }
    except (NotFound, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
