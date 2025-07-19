"""Multi-tenant user organization management service."""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import BusinessLogicError, NotFound, PermissionDenied
from app.models.organization import Organization
from app.models.user import User
from app.models.user_organization import (
    OrganizationInvitation,
    UserOrganization,
    UserTransferRequest,
)
from app.schemas.multi_tenant import (
    BatchInviteResult,
    BatchUserInvite,
    OrganizationInvitationCreate,
    OrganizationMembershipSummary,
    OrganizationUsersSummary,
    TransferApproval,
    UserOrganizationUpdate,
    UserTransferRequestCreate,
)


class MultiTenantService:
    """Service for managing multi-tenant user organization relationships."""

    def __init__(self, db: Session):
        self.db = db

    def add_user_to_organization(
        self,
        user_id: int,
        organization_id: int,
        added_by: User,
        access_type: str = "member",
        is_primary: bool = False,
        expires_at: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> UserOrganization:
        """Add a user to an organization."""
        # Validate user and organization exist
        user = self.db.query(User).filter(User.id == user_id).first()
        organization = (
            self.db.query(Organization)
            .filter(Organization.id == organization_id)
            .first()
        )

        if not user:
            raise NotFound(f"User with id {user_id} not found")
        if not organization:
            raise NotFound(f"Organization with id {organization_id} not found")

        # Check permissions
        if not self._can_manage_organization_membership(added_by, organization):
            raise PermissionDenied(
                "Insufficient permissions to add user to organization"
            )

        # Check if membership already exists
        existing = (
            self.db.query(UserOrganization)
            .filter(
                and_(
                    UserOrganization.user_id == user_id,
                    UserOrganization.organization_id == organization_id,
                )
            )
            .first()
        )

        if existing:
            if existing.is_active:
                raise BusinessLogicError(
                    "User is already a member of this organization"
                )
            else:
                # Reactivate existing membership
                existing.is_active = True
                existing.access_type = access_type
                existing.is_primary = is_primary
                existing.access_expires_at = expires_at
                existing.notes = notes
                existing.approved_by = added_by.id
                existing.updated_at = datetime.utcnow()
                self.db.commit()
                return existing

        # Handle primary organization logic
        if is_primary:
            # Remove primary status from other memberships
            self.db.query(UserOrganization).filter(
                and_(
                    UserOrganization.user_id == user_id,
                    UserOrganization.is_primary,
                )
            ).update({"is_primary": False})

        # Create new membership
        membership = UserOrganization(
            user_id=user_id,
            organization_id=organization_id,
            access_type=access_type,
            is_primary=is_primary,
            access_expires_at=expires_at,
            notes=notes,
            invited_by=added_by.id,
            approved_by=added_by.id,
        )

        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)

        return membership

    def update_user_organization_membership(
        self,
        membership_id: int,
        update_data: UserOrganizationUpdate,
        updated_by: User,
    ) -> UserOrganization:
        """Update user organization membership."""
        membership = (
            self.db.query(UserOrganization)
            .filter(UserOrganization.id == membership_id)
            .first()
        )

        if not membership:
            raise NotFound("Membership not found")

        # Check permissions
        organization = (
            self.db.query(Organization)
            .filter(Organization.id == membership.organization_id)
            .first()
        )

        if not organization or not self._can_manage_organization_membership(updated_by, organization):
            raise PermissionDenied("Insufficient permissions to update membership")

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)

        # Handle primary organization change
        if update_dict.get("is_primary") is True:
            # Remove primary status from other memberships
            self.db.query(UserOrganization).filter(
                and_(
                    UserOrganization.user_id == membership.user_id,
                    UserOrganization.is_primary,
                    UserOrganization.id != membership_id,
                )
            ).update({"is_primary": False})

        for field, value in update_dict.items():
            setattr(membership, field, value)

        membership.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(membership)

        return membership

    def remove_user_from_organization(
        self,
        user_id: int,
        organization_id: int,
        removed_by: User,
        soft_delete: bool = True,
    ) -> bool:
        """Remove user from organization."""
        membership = (
            self.db.query(UserOrganization)
            .filter(
                and_(
                    UserOrganization.user_id == user_id,
                    UserOrganization.organization_id == organization_id,
                    UserOrganization.is_active,
                )
            )
            .first()
        )

        if not membership:
            raise NotFound("Active membership not found")

        # Check permissions
        organization = (
            self.db.query(Organization)
            .filter(Organization.id == organization_id)
            .first()
        )

        if not organization or not self._can_manage_organization_membership(removed_by, organization):
            raise PermissionDenied("Insufficient permissions to remove user")

        if soft_delete:
            membership.is_active = False
            membership.updated_at = datetime.utcnow()
        else:
            self.db.delete(membership)

        self.db.commit()
        return True

    def invite_user_to_organization(
        self,
        invitation_data: OrganizationInvitationCreate,
        invited_by: User,
    ) -> OrganizationInvitation:
        """Send invitation to join organization."""
        # Check permissions
        organization = (
            self.db.query(Organization)
            .filter(Organization.id == invitation_data.organization_id)
            .first()
        )

        if not organization:
            raise NotFound("Organization not found")

        if not self._can_manage_organization_membership(invited_by, organization):
            raise PermissionDenied("Insufficient permissions to send invitations")

        # Check for existing invitation
        existing = (
            self.db.query(OrganizationInvitation)
            .filter(
                and_(
                    OrganizationInvitation.email == invitation_data.email,
                    OrganizationInvitation.organization_id
                    == invitation_data.organization_id,
                    OrganizationInvitation.accepted_at.is_(None),
                    OrganizationInvitation.declined_at.is_(None),
                )
            )
            .first()
        )

        if existing and not existing.is_expired:
            raise BusinessLogicError("Pending invitation already exists for this email")

        # Set default expiration if not provided
        expires_at = invitation_data.expires_at or (
            datetime.utcnow() + timedelta(days=7)
        )

        invitation = OrganizationInvitation(
            organization_id=invitation_data.organization_id,
            email=invitation_data.email,
            invited_by=invited_by.id,
            access_type=invitation_data.access_type,
            message=invitation_data.message,
            expires_at=expires_at,
        )

        self.db.add(invitation)
        self.db.commit()
        self.db.refresh(invitation)

        return invitation

    def batch_invite_users(
        self,
        batch_data: BatchUserInvite,
        invited_by: User,
    ) -> BatchInviteResult:
        """Send batch invitations to multiple users."""
        # Check permissions
        organization = (
            self.db.query(Organization)
            .filter(Organization.id == batch_data.organization_id)
            .first()
        )

        if not organization:
            raise NotFound("Organization not found")

        if not self._can_manage_organization_membership(invited_by, organization):
            raise PermissionDenied("Insufficient permissions to send invitations")

        successful_invites = 0
        failed_invites = 0
        duplicate_invites = 0
        invitation_ids = []
        errors = []

        expires_at = batch_data.expires_at or (datetime.utcnow() + timedelta(days=7))

        for email in batch_data.emails:
            try:
                # Check for existing invitation
                existing = (
                    self.db.query(OrganizationInvitation)
                    .filter(
                        and_(
                            OrganizationInvitation.email == email,
                            OrganizationInvitation.organization_id
                            == batch_data.organization_id,
                            OrganizationInvitation.accepted_at.is_(None),
                            OrganizationInvitation.declined_at.is_(None),
                        )
                    )
                    .first()
                )

                if existing and not existing.is_expired:
                    duplicate_invites += 1
                    continue

                invitation = OrganizationInvitation(
                    organization_id=batch_data.organization_id,
                    email=email,
                    invited_by=invited_by.id,
                    access_type=batch_data.access_type,
                    message=batch_data.message,
                    expires_at=expires_at,
                )

                self.db.add(invitation)
                self.db.flush()  # Get ID without committing

                invitation_ids.append(invitation.id)
                successful_invites += 1

            except Exception as e:
                failed_invites += 1
                errors.append(f"Failed to invite {email}: {str(e)}")

        self.db.commit()

        return BatchInviteResult(
            successful_invites=successful_invites,
            failed_invites=failed_invites,
            duplicate_invites=duplicate_invites,
            invitation_ids=invitation_ids,
            errors=errors,
        )

    def accept_organization_invitation(
        self,
        invitation_id: int,
        user: User,
    ) -> UserOrganization:
        """Accept organization invitation."""
        invitation = (
            self.db.query(OrganizationInvitation)
            .filter(OrganizationInvitation.id == invitation_id)
            .first()
        )

        if not invitation:
            raise NotFound("Invitation not found")

        if invitation.email != user.email:
            raise PermissionDenied("This invitation is not for your email address")

        if not invitation.is_pending:
            raise BusinessLogicError("Invitation is no longer valid")

        # For invitation acceptance, bypass normal permission checks
        # Create membership directly
        membership = UserOrganization(
            user_id=user.id,
            organization_id=invitation.organization_id,
            access_type=invitation.access_type,
            is_primary=False,  # Don't make primary by default
            invited_by=invitation.invited_by,
            approved_by=user.id,  # User approves their own membership
        )

        self.db.add(membership)
        self.db.flush()

        # Mark invitation as accepted
        invitation.accepted_at = datetime.utcnow()
        invitation.accepted_by = user.id

        self.db.commit()

        return membership

    def decline_organization_invitation(
        self,
        invitation_id: int,
        user: User,
    ) -> bool:
        """Decline organization invitation."""
        invitation = (
            self.db.query(OrganizationInvitation)
            .filter(OrganizationInvitation.id == invitation_id)
            .first()
        )

        if not invitation:
            raise NotFound("Invitation not found")

        if invitation.email != user.email:
            raise PermissionDenied("This invitation is not for your email address")

        if not invitation.is_pending:
            raise BusinessLogicError("Invitation is no longer valid")

        invitation.declined_at = datetime.utcnow()
        self.db.commit()

        return True

    def request_user_transfer(
        self,
        transfer_data: UserTransferRequestCreate,
        requested_by: User,
    ) -> UserTransferRequest:
        """Request to transfer user between organizations."""
        # Validate user and organizations
        user = self.db.query(User).filter(User.id == transfer_data.user_id).first()
        from_org = (
            self.db.query(Organization)
            .filter(Organization.id == transfer_data.from_organization_id)
            .first()
        )
        to_org = (
            self.db.query(Organization)
            .filter(Organization.id == transfer_data.to_organization_id)
            .first()
        )

        if not user:
            raise NotFound("User not found")
        if not from_org:
            raise NotFound("Source organization not found")
        if not to_org:
            raise NotFound("Target organization not found")

        # Check if user is member of source organization
        source_membership = (
            self.db.query(UserOrganization)
            .filter(
                and_(
                    UserOrganization.user_id == transfer_data.user_id,
                    UserOrganization.organization_id
                    == transfer_data.from_organization_id,
                    UserOrganization.is_active,
                )
            )
            .first()
        )

        if not source_membership:
            raise BusinessLogicError("User is not a member of the source organization")

        # Check permissions
        if not (
            self._can_manage_organization_membership(requested_by, from_org)
            or self._can_manage_organization_membership(requested_by, to_org)
            or requested_by.id
            == transfer_data.user_id  # User can request their own transfer
        ):
            raise PermissionDenied("Insufficient permissions to request transfer")

        # Check for existing pending transfer
        existing = (
            self.db.query(UserTransferRequest)
            .filter(
                and_(
                    UserTransferRequest.user_id == transfer_data.user_id,
                    UserTransferRequest.from_organization_id
                    == transfer_data.from_organization_id,
                    UserTransferRequest.to_organization_id
                    == transfer_data.to_organization_id,
                    UserTransferRequest.approved_at.is_(None),
                    UserTransferRequest.rejected_at.is_(None),
                    UserTransferRequest.executed_at.is_(None),
                )
            )
            .first()
        )

        if existing:
            raise BusinessLogicError("Transfer request already pending")

        transfer_request = UserTransferRequest(
            user_id=transfer_data.user_id,
            from_organization_id=transfer_data.from_organization_id,
            to_organization_id=transfer_data.to_organization_id,
            requested_by=requested_by.id,
            reason=transfer_data.reason,
            transfer_type=transfer_data.transfer_type,
        )

        self.db.add(transfer_request)
        self.db.commit()
        self.db.refresh(transfer_request)

        return transfer_request

    def approve_transfer_request(
        self,
        request_id: int,
        approval: TransferApproval,
        approver: User,
    ) -> UserTransferRequest:
        """Approve or reject transfer request."""
        transfer_request = (
            self.db.query(UserTransferRequest)
            .filter(UserTransferRequest.id == request_id)
            .first()
        )

        if not transfer_request:
            raise NotFound("Transfer request not found")

        if not transfer_request.is_pending:
            raise BusinessLogicError("Transfer request is not pending")

        # Check permissions
        from_org = (
            self.db.query(Organization)
            .filter(Organization.id == transfer_request.from_organization_id)
            .first()
        )
        to_org = (
            self.db.query(Organization)
            .filter(Organization.id == transfer_request.to_organization_id)
            .first()
        )

        can_approve_source = from_org and self._can_manage_organization_membership(
            approver, from_org
        )
        can_approve_target = to_org and self._can_manage_organization_membership(approver, to_org)

        if not (can_approve_source or can_approve_target):
            raise PermissionDenied("Insufficient permissions to approve transfer")

        if not approval.approve:
            # Reject the transfer
            transfer_request.rejected_by = approver.id
            transfer_request.rejected_at = datetime.utcnow()
            transfer_request.rejection_reason = approval.reason
            self.db.commit()
            return transfer_request

        # Approve the transfer
        if can_approve_source and transfer_request.approved_by_source is None:
            transfer_request.approved_by_source = approver.id
        if can_approve_target and transfer_request.approved_by_target is None:
            transfer_request.approved_by_target = approver.id

        # Check if both approvals are complete
        if (
            transfer_request.approved_by_source is not None
            and transfer_request.approved_by_target is not None
        ):
            transfer_request.approved_at = datetime.utcnow()

            # Execute the transfer
            self._execute_transfer(transfer_request, approver)

        self.db.commit()
        self.db.refresh(transfer_request)

        return transfer_request

    def _execute_transfer(
        self,
        transfer_request: UserTransferRequest,
        executor: User,
    ) -> None:
        """Execute approved transfer."""
        if transfer_request.transfer_type == "permanent":
            # Remove from source organization
            self.remove_user_from_organization(
                transfer_request.user_id,
                transfer_request.from_organization_id,
                executor,
                soft_delete=True,
            )

            # Add to target organization
            self.add_user_to_organization(
                transfer_request.user_id,
                transfer_request.to_organization_id,
                executor,
                access_type="member",
                is_primary=True,  # Make new organization primary
            )

        elif transfer_request.transfer_type == "temporary":
            # Add temporary access to target organization
            expires_at = datetime.utcnow() + timedelta(days=30)  # Default 30 days
            self.add_user_to_organization(
                transfer_request.user_id,
                transfer_request.to_organization_id,
                executor,
                access_type="temporary",
                expires_at=expires_at,
            )

        elif transfer_request.transfer_type == "guest":
            # Add guest access to target organization
            self.add_user_to_organization(
                transfer_request.user_id,
                transfer_request.to_organization_id,
                executor,
                access_type="guest",
            )

        # Mark transfer as executed
        transfer_request.executed_at = datetime.utcnow()
        transfer_request.executed_by = executor.id

    def get_user_organizations(
        self,
        user_id: int,
        include_inactive: bool = False,
    ) -> List[UserOrganization]:
        """Get all organizations for a user."""
        query = (
            self.db.query(UserOrganization)
            .options(joinedload(UserOrganization.organization))
            .filter(UserOrganization.user_id == user_id)
        )

        if not include_inactive:
            query = query.filter(UserOrganization.is_active)

        return query.all()

    def get_organization_users(
        self,
        organization_id: int,
        include_inactive: bool = False,
    ) -> List[UserOrganization]:
        """Get all users for an organization."""
        query = (
            self.db.query(UserOrganization)
            .options(joinedload(UserOrganization.user))
            .filter(UserOrganization.organization_id == organization_id)
        )

        if not include_inactive:
            query = query.filter(UserOrganization.is_active)

        return query.all()

    def get_user_membership_summary(
        self, user_id: int
    ) -> OrganizationMembershipSummary:
        """Get summary of user's organization memberships."""
        memberships = self.get_user_organizations(user_id, include_inactive=False)

        primary_membership = next((m for m in memberships if m.is_primary), None)

        pending_transfers = (
            self.db.query(UserTransferRequest)
            .filter(
                and_(
                    UserTransferRequest.user_id == user_id,
                    UserTransferRequest.approved_at.is_(None),
                    UserTransferRequest.rejected_at.is_(None),
                    UserTransferRequest.executed_at.is_(None),
                )
            )
            .count()
        )

        user = self.db.query(User).filter(User.id == user_id).first()

        return OrganizationMembershipSummary(
            user_id=user_id,
            user_email=user.email if user else "",
            user_full_name=user.full_name if user else "",
            total_organizations=len(memberships),
            primary_organization_id=primary_membership.organization_id
            if primary_membership
            else None,
            primary_organization_name=primary_membership.organization.name
            if primary_membership
            else None,
            active_memberships=len([m for m in memberships if m.is_active]),
            temporary_memberships=len(
                [m for m in memberships if m.access_type == "temporary"]
            ),
            pending_transfers=pending_transfers,
        )

    def get_organization_users_summary(
        self, organization_id: int
    ) -> OrganizationUsersSummary:
        """Get summary of organization's users."""
        memberships = self.get_organization_users(
            organization_id, include_inactive=False
        )

        now = datetime.utcnow()
        pending_invitations = (
            self.db.query(OrganizationInvitation)
            .filter(
                and_(
                    OrganizationInvitation.organization_id == organization_id,
                    OrganizationInvitation.accepted_at.is_(None),
                    OrganizationInvitation.declined_at.is_(None),
                    OrganizationInvitation.expires_at > now,
                )
            )
            .count()
        )

        pending_transfers_in = (
            self.db.query(UserTransferRequest)
            .filter(
                and_(
                    UserTransferRequest.to_organization_id == organization_id,
                    UserTransferRequest.approved_at.is_(None),
                    UserTransferRequest.rejected_at.is_(None),
                    UserTransferRequest.executed_at.is_(None),
                )
            )
            .count()
        )

        pending_transfers_out = (
            self.db.query(UserTransferRequest)
            .filter(
                and_(
                    UserTransferRequest.from_organization_id == organization_id,
                    UserTransferRequest.approved_at.is_(None),
                    UserTransferRequest.rejected_at.is_(None),
                    UserTransferRequest.executed_at.is_(None),
                )
            )
            .count()
        )

        organization = (
            self.db.query(Organization)
            .filter(Organization.id == organization_id)
            .first()
        )

        return OrganizationUsersSummary(
            organization_id=organization_id,
            organization_name=organization.name if organization else "",
            organization_code=organization.code if organization else "",
            total_users=len(memberships),
            active_users=len([m for m in memberships if m.is_active]),
            guest_users=len([m for m in memberships if m.access_type == "guest"]),
            temporary_users=len(
                [m for m in memberships if m.access_type == "temporary"]
            ),
            pending_invitations=pending_invitations,
            pending_transfers_in=pending_transfers_in,
            pending_transfers_out=pending_transfers_out,
        )

    def cleanup_expired_access(self) -> int:
        """Clean up expired temporary access and invitations."""
        now = datetime.utcnow()

        # Deactivate expired temporary memberships
        expired_memberships = (
            self.db.query(UserOrganization)
            .filter(
                and_(
                    UserOrganization.access_type == "temporary",
                    UserOrganization.access_expires_at <= now,
                    UserOrganization.is_active,
                )
            )
            .all()
        )

        for membership in expired_memberships:
            membership.is_active = False
            membership.updated_at = now

        # Clean up expired invitations (mark as declined)
        expired_invitations = (
            self.db.query(OrganizationInvitation)
            .filter(
                and_(
                    OrganizationInvitation.expires_at <= now,
                    OrganizationInvitation.accepted_at.is_(None),
                    OrganizationInvitation.declined_at.is_(None),
                )
            )
            .all()
        )

        for invitation in expired_invitations:
            invitation.declined_at = now

        self.db.commit()

        return len(expired_memberships) + len(expired_invitations)

    def _can_manage_organization_membership(
        self, user: User, organization: Organization
    ) -> bool:
        """Check if user can manage organization membership."""
        if user.is_superuser:
            return True

        # Check if user is admin/manager of the organization
        # This would typically check user roles within the organization
        # For now, simplified to superuser check
        return False

    def _can_accept_invitation(
        self, user: User, invitation: OrganizationInvitation
    ) -> bool:
        """Check if user can accept organization invitation."""
        # User can accept their own invitation
        return invitation.email == user.email
