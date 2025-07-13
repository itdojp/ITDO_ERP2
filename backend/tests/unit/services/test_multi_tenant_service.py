"""Tests for multi-tenant service."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError, NotFound, PermissionDenied
from app.schemas.multi_tenant import (
    BatchUserInvite,
    OrganizationInvitationCreate,
    TransferApproval,
    UserOrganizationCreate,
    UserTransferRequestCreate,
)
from app.services.multi_tenant import MultiTenantService
from tests.factories import create_test_organization, create_test_user


class TestMultiTenantService:
    """Test multi-tenant service functionality."""

    @pytest.fixture
    def service(self, db_session: Session) -> MultiTenantService:
        """Create service instance."""
        return MultiTenantService(db_session)

    def test_add_user_to_organization_success(
        self, service: MultiTenantService, db_session: Session
    ) -> None:
        """Test successfully adding user to organization."""
        # Given: User and organization
        user = create_test_user(db_session)
        organization = create_test_organization(db_session)
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # When: Adding user to organization
        membership = service.add_user_to_organization(
            user_id=user.id,
            organization_id=organization.id,
            added_by=admin,
            access_type="member",
            is_primary=True,
        )

        # Then: Membership should be created
        assert membership.user_id == user.id
        assert membership.organization_id == organization.id
        assert membership.access_type == "member"
        assert membership.is_primary is True
        assert membership.is_active is True

    def test_add_user_to_organization_duplicate_error(
        self, service: MultiTenantService, db_session: Session
    ) -> None:
        """Test error when adding user to organization they're already in."""
        # Given: User already in organization
        user = create_test_user(db_session)
        organization = create_test_organization(db_session)
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        service.add_user_to_organization(
            user_id=user.id,
            organization_id=organization.id,
            added_by=admin,
        )

        # When/Then: Adding again should fail
        with pytest.raises(BusinessLogicError, match="already a member"):
            service.add_user_to_organization(
                user_id=user.id,
                organization_id=organization.id,
                added_by=admin,
            )

    def test_invite_user_to_organization_success(
        self, service: MultiTenantService, db_session: Session
    ) -> None:
        """Test successfully inviting user to organization."""
        # Given: Organization and admin
        organization = create_test_organization(db_session)
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # When: Sending invitation
        invitation_data = OrganizationInvitationCreate(
            organization_id=organization.id,
            email="newuser@example.com",
            access_type="member",
            message="Welcome to our organization!",
        )

        invitation = service.invite_user_to_organization(invitation_data, admin)

        # Then: Invitation should be created
        assert invitation.organization_id == organization.id
        assert invitation.email == "newuser@example.com"
        assert invitation.access_type == "member"
        assert invitation.invited_by == admin.id
        assert invitation.is_pending is True

    def test_batch_invite_users_success(
        self, service: MultiTenantService, db_session: Session
    ) -> None:
        """Test batch user invitations."""
        # Given: Organization and admin
        organization = create_test_organization(db_session)
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # When: Sending batch invitations
        batch_data = BatchUserInvite(
            organization_id=organization.id,
            emails=["user1@example.com", "user2@example.com", "user3@example.com"],
            access_type="member",
            message="Join our team!",
        )

        result = service.batch_invite_users(batch_data, admin)

        # Then: All invitations should be successful
        assert result.successful_invites == 3
        assert result.failed_invites == 0
        assert result.duplicate_invites == 0
        assert len(result.invitation_ids) == 3

    def test_accept_organization_invitation(
        self, service: MultiTenantService, db_session: Session
    ) -> None:
        """Test accepting organization invitation."""
        # Given: User and invitation
        user = create_test_user(db_session, email="invited@example.com")
        organization = create_test_organization(db_session)
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        invitation_data = OrganizationInvitationCreate(
            organization_id=organization.id,
            email="invited@example.com",
            access_type="member",
        )
        invitation = service.invite_user_to_organization(invitation_data, admin)

        # When: User accepts invitation
        membership = service.accept_organization_invitation(invitation.id, user)

        # Then: Membership should be created
        assert membership.user_id == user.id
        assert membership.organization_id == organization.id
        assert membership.access_type == "member"

        # And invitation should be marked as accepted
        db_session.refresh(invitation)
        assert invitation.accepted_at is not None
        assert invitation.accepted_by == user.id

    def test_decline_organization_invitation(
        self, service: MultiTenantService, db_session: Session
    ) -> None:
        """Test declining organization invitation."""
        # Given: User and invitation
        user = create_test_user(db_session, email="invited@example.com")
        organization = create_test_organization(db_session)
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        invitation_data = OrganizationInvitationCreate(
            organization_id=organization.id,
            email="invited@example.com",
        )
        invitation = service.invite_user_to_organization(invitation_data, admin)

        # When: User declines invitation
        result = service.decline_organization_invitation(invitation.id, user)

        # Then: Should succeed
        assert result is True

        # And invitation should be marked as declined
        db_session.refresh(invitation)
        assert invitation.declined_at is not None

    def test_request_user_transfer(
        self, service: MultiTenantService, db_session: Session
    ) -> None:
        """Test requesting user transfer between organizations."""
        # Given: User in source organization, target organization
        user = create_test_user(db_session)
        source_org = create_test_organization(db_session, code="SOURCE")
        target_org = create_test_organization(db_session, code="TARGET")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # Add user to source organization
        service.add_user_to_organization(
            user_id=user.id,
            organization_id=source_org.id,
            added_by=admin,
        )

        # When: Requesting transfer
        transfer_data = UserTransferRequestCreate(
            user_id=user.id,
            from_organization_id=source_org.id,
            to_organization_id=target_org.id,
            reason="User wants to transfer",
            transfer_type="permanent",
        )

        transfer_request = service.request_user_transfer(transfer_data, admin)

        # Then: Transfer request should be created
        assert transfer_request.user_id == user.id
        assert transfer_request.from_organization_id == source_org.id
        assert transfer_request.to_organization_id == target_org.id
        assert transfer_request.requested_by == admin.id
        assert transfer_request.is_pending is True

    def test_approve_transfer_request(
        self, service: MultiTenantService, db_session: Session
    ) -> None:
        """Test approving transfer request."""
        # Given: Pending transfer request
        user = create_test_user(db_session)
        source_org = create_test_organization(db_session, code="SOURCE")
        target_org = create_test_organization(db_session, code="TARGET")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # Add user to source organization
        service.add_user_to_organization(
            user_id=user.id,
            organization_id=source_org.id,
            added_by=admin,
        )

        transfer_data = UserTransferRequestCreate(
            user_id=user.id,
            from_organization_id=source_org.id,
            to_organization_id=target_org.id,
            transfer_type="permanent",
        )
        transfer_request = service.request_user_transfer(transfer_data, admin)

        # When: Approving transfer (as admin with access to both orgs)
        approval = TransferApproval(approve=True, reason="Approved by admin")
        approved_request = service.approve_transfer_request(
            transfer_request.id, approval, admin
        )

        # Then: Transfer should be approved and executed
        assert approved_request.approved_by_source == admin.id
        assert approved_request.approved_by_target == admin.id
        assert approved_request.approved_at is not None
        assert approved_request.executed_at is not None

    def test_reject_transfer_request(
        self, service: MultiTenantService, db_session: Session
    ) -> None:
        """Test rejecting transfer request."""
        # Given: Pending transfer request
        user = create_test_user(db_session)
        source_org = create_test_organization(db_session, code="SOURCE")
        target_org = create_test_organization(db_session, code="TARGET")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        service.add_user_to_organization(
            user_id=user.id,
            organization_id=source_org.id,
            added_by=admin,
        )

        transfer_data = UserTransferRequestCreate(
            user_id=user.id,
            from_organization_id=source_org.id,
            to_organization_id=target_org.id,
            transfer_type="permanent",
        )
        transfer_request = service.request_user_transfer(transfer_data, admin)

        # When: Rejecting transfer
        approval = TransferApproval(approve=False, reason="Not approved")
        rejected_request = service.approve_transfer_request(
            transfer_request.id, approval, admin
        )

        # Then: Transfer should be rejected
        assert rejected_request.rejected_by == admin.id
        assert rejected_request.rejected_at is not None
        assert rejected_request.rejection_reason == "Not approved"

    def test_get_user_organizations(
        self, service: MultiTenantService, db_session: Session
    ) -> None:
        """Test getting user's organizations."""
        # Given: User in multiple organizations
        user = create_test_user(db_session)
        org1 = create_test_organization(db_session, code="ORG1")
        org2 = create_test_organization(db_session, code="ORG2")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        service.add_user_to_organization(
            user_id=user.id,
            organization_id=org1.id,
            added_by=admin,
            is_primary=True,
        )
        service.add_user_to_organization(
            user_id=user.id,
            organization_id=org2.id,
            added_by=admin,
            access_type="guest",
        )

        # When: Getting user organizations
        memberships = service.get_user_organizations(user.id)

        # Then: Should return both memberships
        assert len(memberships) == 2
        membership_org_ids = [m.organization_id for m in memberships]
        assert org1.id in membership_org_ids
        assert org2.id in membership_org_ids

    def test_get_user_membership_summary(
        self, service: MultiTenantService, db_session: Session
    ) -> None:
        """Test getting user membership summary."""
        # Given: User with multiple organization memberships
        user = create_test_user(db_session)
        org1 = create_test_organization(db_session, code="ORG1")
        org2 = create_test_organization(db_session, code="ORG2")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        service.add_user_to_organization(
            user_id=user.id,
            organization_id=org1.id,
            added_by=admin,
            is_primary=True,
        )
        service.add_user_to_organization(
            user_id=user.id,
            organization_id=org2.id,
            added_by=admin,
            access_type="temporary",
        )

        # When: Getting membership summary
        summary = service.get_user_membership_summary(user.id)

        # Then: Summary should be correct
        assert summary.user_id == user.id
        assert summary.total_organizations == 2
        assert summary.primary_organization_id == org1.id
        assert summary.active_memberships == 2
        assert summary.temporary_memberships == 1

    def test_cleanup_expired_access(
        self, service: MultiTenantService, db_session: Session
    ) -> None:
        """Test cleanup of expired access."""
        # Given: User with expired temporary access
        user = create_test_user(db_session)
        organization = create_test_organization(db_session)
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # Add temporary access that expires in the past
        expired_time = datetime.utcnow() - timedelta(days=1)
        service.add_user_to_organization(
            user_id=user.id,
            organization_id=organization.id,
            added_by=admin,
            access_type="temporary",
            expires_at=expired_time,
        )

        # When: Running cleanup
        cleaned_count = service.cleanup_expired_access()

        # Then: Expired access should be cleaned up
        assert cleaned_count == 1

        # And membership should be deactivated
        memberships = service.get_user_organizations(user.id, include_inactive=True)
        assert len(memberships) == 1
        assert memberships[0].is_active is False