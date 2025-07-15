"""Enhanced audit service tests."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import PermissionDenied
from app.models.audit import AuditLog
from app.models.organization import Organization
from app.models.user import User
from app.schemas.audit import (
    AuditLogCreate,
    AuditLogSearch,
)
from app.services.audit import AuditLogger, AuditService
from tests.factories import AuditLogFactory, OrganizationFactory, UserFactory


class TestEnhancedAuditService:
    """Enhanced audit service functionality tests."""

    @pytest.fixture
    def audit_service(self, db_session: Session) -> AuditService:
        """Create audit service instance."""
        return AuditService()

    @pytest.fixture
    def audit_logger(self, db_session: Session) -> AuditLogger:
        """Create audit logger instance."""
        return AuditLogger(db_session)

    @pytest.fixture
    def organization(self, db_session: Session) -> Organization:
        """Create test organization."""
        return OrganizationFactory.create(db_session, name="Test Org")

    @pytest.fixture
    def admin_user(self, db_session: Session) -> User:
        """Create admin user."""
        return UserFactory.create_with_password(
            db_session,
            password="password123",
            email="admin@example.com",
            is_superuser=True,
        )

    @pytest.fixture
    def regular_user(self, db_session: Session, organization: Organization) -> User:
        """Create regular user."""
        return UserFactory.create_with_password(
            db_session, password="password123", email="user@example.com"
        )

    @pytest.mark.skip(reason="AuditService.search_audit_logs not yet implemented")
    def test_advanced_search_functionality(
        self,
        audit_service: AuditService,
        organization: Organization,
        admin_user: User,
        db_session: Session,
    ) -> None:
        """Test advanced search functionality."""
        # Create test audit logs
        base_time = datetime.now(timezone.utc)

        [
            AuditLogFactory.create(
                db_session,
                user_id=admin_user.id,
                action="user.create",
                resource_type="User",
                resource_id=1,
                organization_id=organization.id,
                created_at=base_time - timedelta(days=1),
                changes={"email": "test1@example.com", "status": "active"},
            ),
            AuditLogFactory.create(
                db_session,
                user_id=admin_user.id,
                action="user.update",
                resource_type="User",
                resource_id=1,
                organization_id=organization.id,
                created_at=base_time - timedelta(hours=12),
                changes={"status": {"old": "active", "new": "inactive"}},
            ),
            AuditLogFactory.create(
                db_session,
                user_id=admin_user.id,
                action="role.assign",
                resource_type="Role",
                resource_id=2,
                organization_id=organization.id,
                created_at=base_time - timedelta(hours=6),
                changes={"role": "admin", "target_user": 1},
            ),
        ]

        # Test date range search
        search_filter = AuditLogSearch(
            date_from=base_time - timedelta(days=2),
            date_to=base_time,
            organization_id=organization.id,
        )

        results = audit_service.search_audit_logs(search_filter, admin_user)
        assert len(results.items) == 3

        # Test action filter
        search_filter = AuditLogSearch(
            actions=["user.create", "user.update"], organization_id=organization.id
        )

        results = audit_service.search_audit_logs(search_filter, admin_user)
        assert len(results.items) == 2
        assert all(
            log.action in ["user.create", "user.update"] for log in results.items
        )

        # Test resource type filter
        search_filter = AuditLogSearch(
            resource_types=["User"], organization_id=organization.id
        )

        results = audit_service.search_audit_logs(search_filter, admin_user)
        assert len(results.items) == 2
        assert all(log.resource_type == "User" for log in results.items)

        # Test changes search
        search_filter = AuditLogSearch(
            changes_contain="status", organization_id=organization.id
        )

        results = audit_service.search_audit_logs(search_filter, admin_user)
        assert len(results.items) == 2

    @pytest.mark.skip(reason="AuditService.get_audit_statistics not yet implemented")
    def test_audit_log_statistics(
        self,
        audit_service: AuditService,
        organization: Organization,
        admin_user: User,
        db_session: Session,
    ) -> None:
        """Test audit log statistics generation."""
        # Create diverse audit logs
        base_time = datetime.now(timezone.utc)

        for i in range(10):
            AuditLogFactory.create(
                db_session,
                user_id=admin_user.id,
                action=f"user.{'create' if i % 2 == 0 else 'update'}",
                resource_type="User",
                resource_id=i + 1,
                organization_id=organization.id,
                created_at=base_time - timedelta(hours=i),
            )

        # Get statistics
        stats = audit_service.get_audit_statistics(
            organization_id=organization.id,
            date_from=base_time - timedelta(days=1),
            date_to=base_time,
            requester=admin_user,
        )

        # Verify statistics
        assert stats.total_logs == 10
        assert stats.unique_users == 1
        assert len(stats.action_counts) == 2
        assert stats.action_counts["user.create"] == 5
        assert stats.action_counts["user.update"] == 5
        assert len(stats.resource_type_counts) == 1
        assert stats.resource_type_counts["User"] == 10

    @pytest.mark.skip(reason="AuditService.export_audit_logs not yet implemented")
    def test_audit_log_export(
        self,
        audit_service: AuditService,
        organization: Organization,
        admin_user: User,
        db_session: Session,
    ) -> None:
        """Test audit log CSV export functionality."""
        # Create test data
        AuditLogFactory.create(
            db_session,
            user_id=admin_user.id,
            action="user.create",
            resource_type="User",
            resource_id=1,
            organization_id=organization.id,
            changes={"email": "test@example.com"},
        )

        # Test CSV export
        csv_data = audit_service.export_audit_logs_csv(
            organization_id=organization.id, requester=admin_user
        )

        # Verify CSV structure
        lines = csv_data.strip().split("\n")
        assert len(lines) >= 2  # Header + at least one data row

        # Check header
        header = lines[0]
        expected_columns = [
            "timestamp",
            "user_email",
            "action",
            "resource_type",
            "resource_id",
            "ip_address",
            "changes",
        ]
        for column in expected_columns:
            assert column in header

        # Check data row
        data_row = lines[1]
        assert "user.create" in data_row
        assert "User" in data_row
        assert admin_user.email in data_row

    @pytest.mark.skip(
        reason="AuditService.verify_audit_log_integrity not yet implemented"
    )
    def test_audit_log_integrity_verification(
        self,
        audit_service: AuditService,
        organization: Organization,
        admin_user: User,
        db_session: Session,
    ) -> None:
        """Test audit log integrity verification."""
        # Create audit log
        log = AuditLogFactory.create(
            db_session,
            user_id=admin_user.id,
            action="user.create",
            resource_type="User",
            resource_id=1,
            organization_id=organization.id,
            changes={"email": "test@example.com"},
        )

        # Verify integrity (should pass)
        is_valid = audit_service.verify_log_integrity(log.id, admin_user)
        assert is_valid is True

        # Tamper with the log (simulate corruption)
        from sqlalchemy import text

        db_session.execute(
            text("UPDATE audit_logs SET changes = :changes WHERE id = :log_id"),
            {"changes": '{"email": "tampered@example.com"}', "log_id": log.id},
        )
        db_session.commit()

        # Verify integrity (should fail)
        is_valid = audit_service.verify_log_integrity(log.id, admin_user)
        assert is_valid is False

    @pytest.mark.skip(reason="AuditService.bulk_verify_integrity not yet implemented")
    def test_audit_log_bulk_verification(
        self,
        audit_service: AuditService,
        organization: Organization,
        admin_user: User,
        db_session: Session,
    ) -> None:
        """Test bulk audit log integrity verification."""
        # Create multiple audit logs
        logs = []
        for i in range(5):
            log = AuditLogFactory.create(
                db_session,
                user_id=admin_user.id,
                action="user.create",
                resource_type="User",
                resource_id=i + 1,
                organization_id=organization.id,
                changes={"email": f"test{i}@example.com"},
            )
            logs.append(log)

        # Tamper with one log
        tampered_log = logs[2]
        from sqlalchemy import text

        db_session.execute(
            text("UPDATE audit_logs SET changes = :changes WHERE id = :log_id"),
            {"changes": '{"email": "tampered@example.com"}', "log_id": tampered_log.id},
        )
        db_session.commit()

        # Bulk verification
        results = audit_service.verify_logs_integrity_bulk(
            organization_id=organization.id,
            date_from=datetime.now(timezone.utc) - timedelta(days=1),
            date_to=datetime.now(timezone.utc),
            requester=admin_user,
        )

        # Check results
        assert results.total_checked == 5
        assert results.corrupted_count == 1
        assert results.integrity_percentage == 80.0
        assert len(results.corrupted_log_ids) == 1
        assert tampered_log.id in results.corrupted_log_ids

    @pytest.mark.skip(reason="AuditService.filter_sensitive_data not yet implemented")
    def test_sensitive_data_filtering(
        self,
        audit_service: AuditService,
        organization: Organization,
        admin_user: User,
        regular_user: User,
        db_session: Session,
    ) -> None:
        """Test sensitive data filtering for non-admin users."""
        # Create audit log with sensitive data
        AuditLogFactory.create(
            db_session,
            user_id=admin_user.id,
            action="user.update",
            resource_type="User",
            resource_id=1,
            organization_id=organization.id,
            changes={
                "email": {"old": "old@example.com", "new": "new@example.com"},
                "password": {"old": "***", "new": "***"},
                "phone": {"old": "123-456-7890", "new": "098-765-4321"},
            },
        )

        # Admin should see all data
        admin_results = audit_service.get_organization_audit_logs(
            organization_id=organization.id, requester=admin_user, limit=10, offset=0
        )
        admin_log = admin_results.items[0]
        assert "password" in admin_log.changes
        assert "phone" in admin_log.changes

        # Regular user should see filtered data
        user_results = audit_service.get_organization_audit_logs(
            organization_id=organization.id, requester=regular_user, limit=10, offset=0
        )
        user_log = user_results.items[0]
        assert (
            "password" not in user_log.changes or user_log.changes["password"] == "***"
        )
        assert "email" in user_log.changes  # Non-sensitive data should be visible

    @pytest.mark.skip(reason="AuditService.apply_retention_policy not yet implemented")
    def test_audit_log_retention_policy(
        self,
        audit_service: AuditService,
        organization: Organization,
        admin_user: User,
        db_session: Session,
    ) -> None:
        """Test audit log retention policy enforcement."""
        # Create old audit logs
        old_date = datetime.now(timezone.utc) - timedelta(days=400)  # Older than 1 year

        old_logs = []
        for i in range(3):
            log = AuditLogFactory.create(
                db_session,
                user_id=admin_user.id,
                action="user.create",
                resource_type="User",
                resource_id=i + 1,
                organization_id=organization.id,
                created_at=old_date,
            )
            old_logs.append(log)

        # Create recent logs
        recent_logs = []
        for i in range(2):
            log = AuditLogFactory.create(
                db_session,
                user_id=admin_user.id,
                action="user.update",
                resource_type="User",
                resource_id=i + 1,
                organization_id=organization.id,
                created_at=datetime.now(timezone.utc),
            )
            recent_logs.append(log)

        # Apply retention policy (365 days)
        archived_count = audit_service.apply_retention_policy(
            organization_id=organization.id, retention_days=365, requester=admin_user
        )

        # Verify old logs are archived/deleted
        assert archived_count == 3

        # Verify recent logs are still accessible
        results = audit_service.get_organization_audit_logs(
            organization_id=organization.id, requester=admin_user, limit=10, offset=0
        )
        assert len(results.items) == 2

    @pytest.mark.skip(reason="Permission checks for audit logs not yet implemented")
    def test_audit_log_permission_checks(
        self,
        audit_service: AuditService,
        organization: Organization,
        regular_user: User,
        db_session: Session,
    ) -> None:
        """Test permission checks for audit log access."""
        # Regular user should not access other organization's logs
        other_org = OrganizationFactory.create(db_session, name="Other Org")

        with pytest.raises(PermissionDenied):
            audit_service.get_organization_audit_logs(
                organization_id=other_org.id, requester=regular_user, limit=10, offset=0
            )

        # Regular user should not perform admin operations
        with pytest.raises(PermissionDenied):
            audit_service.apply_retention_policy(
                organization_id=organization.id,
                retention_days=365,
                requester=regular_user,
            )

        with pytest.raises(PermissionDenied):
            audit_service.verify_logs_integrity_bulk(
                organization_id=organization.id,
                date_from=datetime.now(timezone.utc) - timedelta(days=1),
                date_to=datetime.now(timezone.utc),
                requester=regular_user,
            )

    @pytest.mark.skip(reason="Performance testing for audit logs deferred")
    def test_high_frequency_logging_performance(
        self,
        audit_logger: AuditLogger,
        organization: Organization,
        admin_user: User,
        db_session: Session,
    ) -> None:
        """Test performance with high-frequency logging."""
        import time

        # Record start time
        start_time = time.time()

        # Create many audit logs quickly
        for i in range(100):
            audit_create = AuditLogCreate(
                user_id=admin_user.id,
                action=f"batch.operation_{i}",
                resource_type="BatchOperation",
                resource_id=i,
                organization_id=organization.id,
                changes={"operation": f"batch_{i}", "status": "completed"},
                ip_address="127.0.0.1",
                user_agent="TestAgent/1.0",
            )
            audit_logger.log(audit_create)

        # Record end time
        end_time = time.time()
        duration = end_time - start_time

        # Performance assertion (should complete within reasonable time)
        assert duration < 10.0  # 100 logs in less than 10 seconds

        # Verify all logs were created
        count = (
            db_session.query(AuditLog)
            .filter(
                AuditLog.organization_id == organization.id,
                AuditLog.action.like("batch.operation_%"),
            )
            .count()
        )
        assert count == 100
