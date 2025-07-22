"""Multi-tenant schemas for user organization management."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class UserOrganizationBase(BaseModel):
    """Base schema for user organization membership."""

    user_id: int
    organization_id: int
    access_type: Literal["member", "guest", "temporary", "transferred"] = "member"
    is_primary: bool = False
    is_active: bool = True
    notes: Optional[str] = None


class UserOrganizationCreate(UserOrganizationBase):
    """Schema for creating user organization membership."""

    access_expires_at: Optional[datetime] = None
    invited_by: Optional[int] = None


class UserOrganizationUpdate(BaseModel):
    """Schema for updating user organization membership."""

    access_type: Optional[Literal["member", "guest", "temporary", "transferred"]] = None
    is_primary: Optional[bool] = None
    is_active: Optional[bool] = None
    access_expires_at: Optional[datetime] = None
    notes: Optional[str] = None


class UserOrganization(UserOrganizationBase):
    """Schema for user organization membership response."""

    id: int
    access_granted_at: datetime
    access_expires_at: Optional[datetime] = None
    last_access_at: Optional[datetime] = None
    transfer_requested_at: Optional[datetime] = None
    transfer_approved_at: Optional[datetime] = None
    invited_by: Optional[int] = None
    approved_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Computed properties
    is_expired: bool = False
    is_temporary: bool = False
    is_transfer_pending: bool = False

    class Config:
        from_attributes = True


class UserOrganizationWithDetails(UserOrganization):
    """Extended schema with organization and user details."""

    user_email: str
    user_full_name: str
    organization_name: str
    organization_code: str


class OrganizationInvitationBase(BaseModel):
    """Base schema for organization invitation."""

    organization_id: int
    email: EmailStr
    access_type: Literal["member", "guest", "temporary"] = "member"
    message: Optional[str] = None


class OrganizationInvitationCreate(OrganizationInvitationBase):
    """Schema for creating organization invitation."""

    expires_at: Optional[datetime] = None


class OrganizationInvitationUpdate(BaseModel):
    """Schema for updating invitation."""

    message: Optional[str] = None
    expires_at: Optional[datetime] = None


class OrganizationInvitation(OrganizationInvitationBase):
    """Schema for organization invitation response."""

    id: int
    invited_by: int
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    accepted_by: Optional[int] = None
    declined_at: Optional[datetime] = None
    created_at: datetime

    # Computed properties
    is_expired: bool = False
    is_pending: bool = False

    class Config:
        from_attributes = True


class OrganizationInvitationWithDetails(OrganizationInvitation):
    """Extended invitation schema with details."""

    organization_name: str
    organization_code: str
    inviter_name: str
    inviter_email: str


class UserTransferRequestBase(BaseModel):
    """Base schema for user transfer request."""

    user_id: int
    from_organization_id: int
    to_organization_id: int
    reason: Optional[str] = None
    transfer_type: Literal["permanent", "temporary", "guest"] = "permanent"


class UserTransferRequestCreate(UserTransferRequestBase):
    """Schema for creating transfer request."""



class UserTransferRequestUpdate(BaseModel):
    """Schema for updating transfer request."""

    reason: Optional[str] = None
    transfer_type: Optional[Literal["permanent", "temporary", "guest"]] = None


class UserTransferRequest(UserTransferRequestBase):
    """Schema for transfer request response."""

    id: int
    requested_by: int
    approved_by_source: Optional[int] = None
    approved_by_target: Optional[int] = None
    approved_at: Optional[datetime] = None
    rejected_by: Optional[int] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    executed_at: Optional[datetime] = None
    executed_by: Optional[int] = None
    created_at: datetime

    # Computed properties
    is_pending: bool = False
    is_approved: bool = False
    requires_source_approval: bool = False
    requires_target_approval: bool = False

    class Config:
        from_attributes = True


class UserTransferRequestWithDetails(UserTransferRequest):
    """Extended transfer request schema with details."""

    user_email: str
    user_full_name: str
    from_organization_name: str
    from_organization_code: str
    to_organization_name: str
    to_organization_code: str
    requester_name: str


class TransferApproval(BaseModel):
    """Schema for approving/rejecting transfer."""

    approve: bool
    reason: Optional[str] = None


class OrganizationMembershipSummary(BaseModel):
    """Summary of user's organization memberships."""

    user_id: int
    user_email: str
    user_full_name: str
    total_organizations: int
    primary_organization_id: Optional[int] = None
    primary_organization_name: Optional[str] = None
    active_memberships: int
    temporary_memberships: int
    pending_transfers: int


class OrganizationUsersSummary(BaseModel):
    """Summary of organization's users."""

    organization_id: int
    organization_name: str
    organization_code: str
    total_users: int
    active_users: int
    guest_users: int
    temporary_users: int
    pending_invitations: int
    pending_transfers_in: int
    pending_transfers_out: int


class BatchUserInvite(BaseModel):
    """Schema for batch user invitations."""

    organization_id: int
    emails: list[EmailStr] = Field(..., min_length=1, max_length=50)
    access_type: Literal["member", "guest", "temporary"] = "member"
    message: Optional[str] = None
    expires_at: Optional[datetime] = None


class BatchInviteResult(BaseModel):
    """Result of batch invitation."""

    successful_invites: int
    failed_invites: int
    duplicate_invites: int
    invitation_ids: list[int]
    errors: list[str] = []


class UserAccessLog(BaseModel):
    """Schema for user access across organizations."""

    user_id: int
    organization_id: int
    access_time: datetime
    access_type: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class CrossTenantPermission(BaseModel):
    """Schema for cross-tenant permission."""

    user_id: int
    source_organization_id: int
    target_organization_id: int
    permission_codes: list[str]
    granted_by: int
    expires_at: Optional[datetime] = None
    is_active: bool = True
    reason: Optional[str] = None


class OrganizationAccessPolicy(BaseModel):
    """Schema for organization access policy."""

    organization_id: int
    allow_guest_access: bool = True
    allow_temporary_access: bool = True
    max_temporary_duration_days: int = 30
    require_approval_for_transfers: bool = True
    allow_cross_tenant_permissions: bool = False
    allowed_source_organizations: list[int] = []
    blocked_organizations: list[int] = []
