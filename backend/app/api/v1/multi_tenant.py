"""Multi-tenant management API endpoints."""

from typing import List, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.core.exceptions import BusinessLogicError, NotFound, PermissionDenied
from app.models.user import User
from app.schemas.multi_tenant import (
    BatchInviteResult,
    BatchUserInvite,
    OrganizationInvitation,
    OrganizationInvitationCreate,
    OrganizationMembershipSummary,
    OrganizationUsersSummary,
    TransferApproval,
    UserOrganization,
    UserOrganizationCreate,
    UserOrganizationUpdate,
    UserTransferRequest,
    UserTransferRequestCreate,
)
from app.services.multi_tenant import MultiTenantService

router = APIRouter()


@router.post("/organizations/{organization_id}/users", response_model=UserOrganization)
def add_user_to_organization(
    organization_id: int,
    user_data: UserOrganizationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserOrganization:
    """Add a user to an organization."""
    service = MultiTenantService(db)
    try:
        user_org_model = service.add_user_to_organization(
            user_id=user_data.user_id,
            organization_id=organization_id,
            added_by=current_user,
            access_type=user_data.access_type,
            is_primary=user_data.is_primary,
            expires_at=user_data.access_expires_at,
            notes=user_data.notes,
        )
        # Convert model to schema
        return UserOrganization(
            id=user_org_model.id,
            user_id=user_org_model.user_id,
            organization_id=user_org_model.organization_id,
            access_type=cast(Literal["member", "guest", "temporary", "transferred"], user_org_model.access_type if user_org_model.access_type in ["member", "guest", "temporary", "transferred"] else "member"),
            is_primary=user_org_model.is_primary,
            is_active=user_org_model.is_active,
            access_granted_at=user_org_model.created_at,  # Add missing field
            access_expires_at=user_org_model.access_expires_at,
            last_access_at=getattr(user_org_model, 'last_access_at', None),
            transfer_requested_at=getattr(user_org_model, 'transfer_requested_at', None),
            transfer_approved_at=getattr(user_org_model, 'transfer_approved_at', None),
            invited_by=getattr(user_org_model, 'invited_by', None),
            approved_by=getattr(user_org_model, 'approved_by', None),
            created_at=user_org_model.created_at,
            updated_at=user_org_model.updated_at,
            notes=user_org_model.notes,
        )
    except (NotFound, PermissionDenied, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/memberships/{membership_id}", response_model=UserOrganization)
def update_user_organization_membership(
    membership_id: int,
    update_data: UserOrganizationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserOrganization:
    """Update user organization membership."""
    service = MultiTenantService(db)
    try:
        result = service.update_user_organization_membership(
            membership_id=membership_id,
            update_data=update_data,
            updated_by=current_user,
        )
        return UserOrganization.model_validate(result)
    except (NotFound, PermissionDenied, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/organizations/{organization_id}/users/{user_id}")
def remove_user_from_organization(
    organization_id: int,
    user_id: int,
    soft_delete: bool = Query(
        True, description="Soft delete membership instead of hard delete"
    ),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Remove user from organization."""
    service = MultiTenantService(db)
    try:
        service.remove_user_from_organization(
            user_id=user_id,
            organization_id=organization_id,
            removed_by=current_user,
            soft_delete=soft_delete,
        )
        return {"message": "User removed from organization successfully"}
    except (NotFound, PermissionDenied, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/organizations/{organization_id}/invitations",
    response_model=OrganizationInvitation,
)
def invite_user_to_organization(
    organization_id: int,
    invitation_data: OrganizationInvitationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> OrganizationInvitation:
    """Send invitation to join organization."""
    service = MultiTenantService(db)
    # Override organization_id from URL
    invitation_data.organization_id = organization_id
    try:
        result = service.invite_user_to_organization(invitation_data, current_user)
        return OrganizationInvitation.model_validate(result)
    except (NotFound, PermissionDenied, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/organizations/{organization_id}/batch-invitations",
    response_model=BatchInviteResult,
)
def batch_invite_users(
    organization_id: int,
    batch_data: BatchUserInvite,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> BatchInviteResult:
    """Send batch invitations to multiple users."""
    service = MultiTenantService(db)
    # Override organization_id from URL
    batch_data.organization_id = organization_id
    try:
        return service.batch_invite_users(batch_data, current_user)
    except (NotFound, PermissionDenied, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/invitations/{invitation_id}/accept", response_model=UserOrganization)
def accept_organization_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserOrganization:
    """Accept organization invitation."""
    service = MultiTenantService(db)
    try:
        result = service.accept_organization_invitation(invitation_id, current_user)
        return UserOrganization.model_validate(result)
    except (NotFound, PermissionDenied, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/invitations/{invitation_id}/decline")
def decline_organization_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Decline organization invitation."""
    service = MultiTenantService(db)
    try:
        service.decline_organization_invitation(invitation_id, current_user)
        return {"message": "Invitation declined successfully"}
    except (NotFound, PermissionDenied, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/transfer-requests", response_model=UserTransferRequest)
def request_user_transfer(
    transfer_data: UserTransferRequestCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserTransferRequest:
    """Request to transfer user between organizations."""
    service = MultiTenantService(db)
    try:
        result = service.request_user_transfer(transfer_data, current_user)
        return UserTransferRequest.model_validate(result)
    except (NotFound, PermissionDenied, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/transfer-requests/{request_id}/approve", response_model=UserTransferRequest
)
def approve_transfer_request(
    request_id: int,
    approval: TransferApproval,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserTransferRequest:
    """Approve or reject transfer request."""
    service = MultiTenantService(db)
    try:
        result = service.approve_transfer_request(request_id, approval, current_user)
        return UserTransferRequest.model_validate(result)
    except (NotFound, PermissionDenied, BusinessLogicError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/users/{user_id}/organizations", response_model=List[UserOrganization])
def get_user_organizations(
    user_id: int,
    include_inactive: bool = Query(False, description="Include inactive memberships"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[UserOrganization]:
    """Get all organizations for a user."""
    service = MultiTenantService(db)
    # Basic permission check - users can view their own organizations,
    # admins can view any
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view user organizations",
        )

    results = service.get_user_organizations(user_id, include_inactive)
    return [UserOrganization.model_validate(result) for result in results]


@router.get(
    "/organizations/{organization_id}/users", response_model=List[UserOrganization]
)
def get_organization_users(
    organization_id: int,
    include_inactive: bool = Query(False, description="Include inactive memberships"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[UserOrganization]:
    """Get all users for an organization."""
    service = MultiTenantService(db)

    # Check organization-level permissions
    if not current_user.is_superuser:
        # Check if user has permission in this organization
        user_orgs = [org.id for org in current_user.get_organizations()]
        if organization_id not in user_orgs:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view organization users",
            )

    # TODO: Add proper organization-level permission checking
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view organization users",
        )

    results = service.get_organization_users(organization_id, include_inactive)
    return [UserOrganization.model_validate(result) for result in results]


@router.get(
    "/users/{user_id}/membership-summary", response_model=OrganizationMembershipSummary
)
def get_user_membership_summary(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> OrganizationMembershipSummary:
    """Get summary of user's organization memberships."""
    service = MultiTenantService(db)
    # Basic permission check - users can view their own summary, admins can view any
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view membership summary",
        )

    return service.get_user_membership_summary(user_id)


@router.get(
    "/organizations/{organization_id}/users-summary",
    response_model=OrganizationUsersSummary,
)
def get_organization_users_summary(
    organization_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> OrganizationUsersSummary:
    """Get summary of organization's users."""
    service = MultiTenantService(db)

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

    return service.get_organization_users_summary(organization_id)


@router.post("/cleanup-expired-access")
def cleanup_expired_access(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    """Clean up expired temporary access and invitations."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can run cleanup operations",
        )

    service = MultiTenantService(db)
    cleaned_count = service.cleanup_expired_access()

    return {"cleaned_count": cleaned_count}
