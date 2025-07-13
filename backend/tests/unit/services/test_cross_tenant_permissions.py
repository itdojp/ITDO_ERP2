"""Tests for cross-tenant permissions service."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError, NotFound, PermissionDenied
from app.schemas.cross_tenant_permissions import (
    CrossTenantPermissionCheck,
    CrossTenantPermissionRuleCreate,
)
from app.services.cross_tenant_permissions import CrossTenantPermissionService
from tests.factories import create_test_organization, create_test_user


class TestCrossTenantPermissionService:
    """Test cross-tenant permission service functionality."""

    @pytest.fixture
    def service(self, db_session: Session) -> CrossTenantPermissionService:
        """Create service instance."""
        return CrossTenantPermissionService(db_session)

    def test_create_permission_rule_success(
        self, service: CrossTenantPermissionService, db_session: Session
    ) -> None:
        """Test successfully creating cross-tenant permission rule."""
        # Given: Two organizations and a superuser
        source_org = create_test_organization(db_session, code="SOURCE")
        target_org = create_test_organization(db_session, code="TARGET")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # When: Creating permission rule
        rule_data = CrossTenantPermissionRuleCreate(
            source_organization_id=source_org.id,
            target_organization_id=target_org.id,
            permission_pattern="read:*",
            rule_type="allow",
            priority=100,
        )

        rule = service.create_permission_rule(rule_data, admin)

        # Then: Rule should be created
        assert rule.source_organization_id == source_org.id
        assert rule.target_organization_id == target_org.id
        assert rule.permission_pattern == "read:*"
        assert rule.rule_type == "allow"
        assert rule.priority == 100
        assert rule.created_by == admin.id
        assert rule.is_active is True

    def test_create_permission_rule_permission_denied(
        self, service: CrossTenantPermissionService, db_session: Session
    ) -> None:
        """Test creating permission rule without proper permissions."""
        # Given: Two organizations and a regular user
        source_org = create_test_organization(db_session, code="SOURCE")
        target_org = create_test_organization(db_session, code="TARGET")
        user = create_test_user(db_session)
        db_session.commit()

        # When/Then: Creating rule should fail
        rule_data = CrossTenantPermissionRuleCreate(
            source_organization_id=source_org.id,
            target_organization_id=target_org.id,
            permission_pattern="read:*",
            rule_type="allow",
        )

        with pytest.raises(PermissionDenied, match="Insufficient permissions"):
            service.create_permission_rule(rule_data, user)

    def test_check_cross_tenant_permission_allow(
        self, service: CrossTenantPermissionService, db_session: Session
    ) -> None:
        """Test checking cross-tenant permission with allow rule."""
        # Given: User, organizations, and permission rule
        user = create_test_user(db_session)
        source_org = create_test_organization(db_session, code="SOURCE")
        target_org = create_test_organization(db_session, code="TARGET")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # Add user to source organization
        from app.services.multi_tenant import MultiTenantService
        multi_tenant_service = MultiTenantService(db_session)
        multi_tenant_service.add_user_to_organization(
            user_id=user.id,
            organization_id=source_org.id,
            added_by=admin,
        )

        # Create permission rule
        rule_data = CrossTenantPermissionRuleCreate(
            source_organization_id=source_org.id,
            target_organization_id=target_org.id,
            permission_pattern="read:*",
            rule_type="allow",
        )
        service.create_permission_rule(rule_data, admin)

        # When: Checking permission
        result = service.check_cross_tenant_permission(
            user_id=user.id,
            source_organization_id=source_org.id,
            target_organization_id=target_org.id,
            permission="read:users",
            log_check=False,
        )

        # Then: Permission should be allowed
        assert result.allowed is True
        assert "Allowed by rule" in result.reason
        assert len(result.matching_rules) == 1

    def test_check_cross_tenant_permission_deny(
        self, service: CrossTenantPermissionService, db_session: Session
    ) -> None:
        """Test checking cross-tenant permission with deny rule."""
        # Given: User, organizations, and deny rule
        user = create_test_user(db_session)
        source_org = create_test_organization(db_session, code="SOURCE")
        target_org = create_test_organization(db_session, code="TARGET")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # Add user to source organization
        from app.services.multi_tenant import MultiTenantService
        multi_tenant_service = MultiTenantService(db_session)
        multi_tenant_service.add_user_to_organization(
            user_id=user.id,
            organization_id=source_org.id,
            added_by=admin,
        )

        # Create deny rule
        rule_data = CrossTenantPermissionRuleCreate(
            source_organization_id=source_org.id,
            target_organization_id=target_org.id,
            permission_pattern="write:*",
            rule_type="deny",
        )
        service.create_permission_rule(rule_data, admin)

        # When: Checking permission
        result = service.check_cross_tenant_permission(
            user_id=user.id,
            source_organization_id=source_org.id,
            target_organization_id=target_org.id,
            permission="write:users",
            log_check=False,
        )

        # Then: Permission should be denied
        assert result.allowed is False
        assert "Denied by rule" in result.reason
        assert len(result.matching_rules) == 1

    def test_check_cross_tenant_permission_not_member(
        self, service: CrossTenantPermissionService, db_session: Session
    ) -> None:
        """Test checking permission when user is not member of source org."""
        # Given: User not in source organization
        user = create_test_user(db_session)
        source_org = create_test_organization(db_session, code="SOURCE")
        target_org = create_test_organization(db_session, code="TARGET")
        db_session.commit()

        # When: Checking permission
        result = service.check_cross_tenant_permission(
            user_id=user.id,
            source_organization_id=source_org.id,
            target_organization_id=target_org.id,
            permission="read:users",
            log_check=False,
        )

        # Then: Permission should be denied
        assert result.allowed is False
        assert "not a member of the source organization" in result.reason

    def test_batch_check_permissions(
        self, service: CrossTenantPermissionService, db_session: Session
    ) -> None:
        """Test batch permission checking."""
        # Given: User, organizations, and mixed rules
        user = create_test_user(db_session)
        source_org = create_test_organization(db_session, code="SOURCE")
        target_org = create_test_organization(db_session, code="TARGET")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # Add user to source organization
        from app.services.multi_tenant import MultiTenantService
        multi_tenant_service = MultiTenantService(db_session)
        multi_tenant_service.add_user_to_organization(
            user_id=user.id,
            organization_id=source_org.id,
            added_by=admin,
        )

        # Create allow rule for read permissions
        read_rule = CrossTenantPermissionRuleCreate(
            source_organization_id=source_org.id,
            target_organization_id=target_org.id,
            permission_pattern="read:*",
            rule_type="allow",
            priority=100,
        )
        service.create_permission_rule(read_rule, admin)

        # Create deny rule for write permissions (higher priority)
        write_rule = CrossTenantPermissionRuleCreate(
            source_organization_id=source_org.id,
            target_organization_id=target_org.id,
            permission_pattern="write:*",
            rule_type="deny",
            priority=200,
        )
        service.create_permission_rule(write_rule, admin)

        # When: Batch checking permissions
        permissions = ["read:users", "read:projects", "write:users", "admin:delete"]
        result = service.batch_check_permissions(
            user_id=user.id,
            source_organization_id=source_org.id,
            target_organization_id=target_org.id,
            permissions=permissions,
        )

        # Then: Should have mixed results
        assert len(result.results) == 4
        assert result.summary["total_permissions"] == 4
        assert result.summary["allowed"] == 2  # read permissions
        assert result.summary["denied"] == 2   # write and admin permissions

        # Check individual results
        read_results = [r for r in result.results if r.permission.startswith("read:")]
        write_results = [r for r in result.results if r.permission.startswith("write:")]
        
        assert all(r.allowed for r in read_results)
        assert not any(r.allowed for r in write_results)

    def test_get_user_cross_tenant_access(
        self, service: CrossTenantPermissionService, db_session: Session
    ) -> None:
        """Test getting user cross-tenant access summary."""
        # Given: User, organizations, and permission rules
        user = create_test_user(db_session)
        source_org = create_test_organization(db_session, code="SOURCE")
        target_org = create_test_organization(db_session, code="TARGET")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # Create permission rules
        read_rule = CrossTenantPermissionRuleCreate(
            source_organization_id=source_org.id,
            target_organization_id=target_org.id,
            permission_pattern="read:*",
            rule_type="allow",
        )
        service.create_permission_rule(read_rule, admin)

        write_rule = CrossTenantPermissionRuleCreate(
            source_organization_id=source_org.id,
            target_organization_id=target_org.id,
            permission_pattern="write:*",
            rule_type="deny",
        )
        service.create_permission_rule(write_rule, admin)

        # When: Getting access summary
        access = service.get_user_cross_tenant_access(
            user_id=user.id,
            source_organization_id=source_org.id,
            target_organization_id=target_org.id,
        )

        # Then: Access summary should be correct
        assert access.user_id == user.id
        assert access.source_organization_id == source_org.id
        assert access.target_organization_id == target_org.id
        assert "read:*" in access.allowed_permissions
        assert "write:*" in access.denied_permissions
        assert access.access_level in ["read_only", "restricted"]

    def test_get_organization_cross_tenant_summary(
        self, service: CrossTenantPermissionService, db_session: Session
    ) -> None:
        """Test getting organization cross-tenant summary."""
        # Given: Organization with some rules
        source_org = create_test_organization(db_session, code="SOURCE")
        target_org1 = create_test_organization(db_session, code="TARGET1")
        target_org2 = create_test_organization(db_session, code="TARGET2")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # Create outbound rules (source org granting access)
        rule1 = CrossTenantPermissionRuleCreate(
            source_organization_id=source_org.id,
            target_organization_id=target_org1.id,
            permission_pattern="read:*",
            rule_type="allow",
        )
        service.create_permission_rule(rule1, admin)

        rule2 = CrossTenantPermissionRuleCreate(
            source_organization_id=source_org.id,
            target_organization_id=target_org2.id,
            permission_pattern="view:*",
            rule_type="allow",
        )
        service.create_permission_rule(rule2, admin)

        # Create inbound rule (other org granting access to source org)
        rule3 = CrossTenantPermissionRuleCreate(
            source_organization_id=target_org1.id,
            target_organization_id=source_org.id,
            permission_pattern="admin:*",
            rule_type="allow",
        )
        service.create_permission_rule(rule3, admin)

        # When: Getting summary
        summary = service.get_organization_cross_tenant_summary(source_org.id)

        # Then: Summary should be correct
        assert summary.organization_id == source_org.id
        assert summary.organization_name == source_org.name
        assert summary.outbound_rules == 2  # Rules granting access to others
        assert summary.inbound_rules == 1   # Rules allowing access from others
        assert summary.total_shared_permissions == 3

    def test_cleanup_expired_rules(
        self, service: CrossTenantPermissionService, db_session: Session
    ) -> None:
        """Test cleanup of expired permission rules."""
        # Given: Organization with expired rule
        source_org = create_test_organization(db_session, code="SOURCE")
        target_org = create_test_organization(db_session, code="TARGET")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # Create expired rule
        expired_time = datetime.now() - timedelta(days=1)
        expired_rule = CrossTenantPermissionRuleCreate(
            source_organization_id=source_org.id,
            target_organization_id=target_org.id,
            permission_pattern="read:*",
            rule_type="allow",
            expires_at=expired_time,
        )
        service.create_permission_rule(expired_rule, admin)

        # Create active rule
        active_rule = CrossTenantPermissionRuleCreate(
            source_organization_id=source_org.id,
            target_organization_id=target_org.id,
            permission_pattern="write:*",
            rule_type="allow",
        )
        service.create_permission_rule(active_rule, admin)

        # When: Running cleanup
        cleaned_count = service.cleanup_expired_rules()

        # Then: Only expired rule should be deactivated
        assert cleaned_count == 1