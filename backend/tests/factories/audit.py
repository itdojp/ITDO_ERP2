"""Audit log factory for testing."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from faker import Faker
from sqlalchemy.orm import Session

from app.models.audit import AuditLog

fake = Faker("ja_JP")


class AuditLogFactory:
    """Factory for creating audit log test instances."""

    @staticmethod
    def create(
        db: Session,
        user_id: int,
        action: str = "test.action",
        resource_type: str = "TestResource",
        resource_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        created_at: Optional[datetime] = None,
        **kwargs,
    ) -> AuditLog:
        """Create an audit log instance."""

        # Default values
        if changes is None:
            changes = {"test_field": "test_value"}

        if ip_address is None:
            ip_address = fake.ipv4()

        if user_agent is None:
            user_agent = fake.user_agent()

        if created_at is None:
            created_at = datetime.now(timezone.utc)

        if resource_id is None:
            resource_id = fake.random_int(min=1, max=1000)

        # Create audit log
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            organization_id=organization_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=created_at,
            **kwargs,
        )

        # Calculate checksum
        audit_log.checksum = audit_log.calculate_checksum()

        # Save to database
        db.add(audit_log)
        db.flush()

        return audit_log

    @staticmethod
    def create_batch(
        db: Session, count: int, user_id: int, organization_id: int, **kwargs
    ) -> list[AuditLog]:
        """Create multiple audit log instances."""
        audit_logs = []

        actions = [
            "user.create",
            "user.update",
            "user.delete",
            "role.assign",
            "role.revoke",
            "organization.update",
            "department.create",
        ]

        resource_types = ["User", "Role", "Organization", "Department", "Task"]

        for i in range(count):
            action = fake.random_element(actions)
            resource_type = fake.random_element(resource_types)

            audit_log = AuditLogFactory.create(
                db=db,
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                organization_id=organization_id,
                changes={
                    "field_1": fake.word(),
                    "field_2": fake.random_int(min=1, max=100),
                    "timestamp": fake.date_time().isoformat(),
                },
                **kwargs,
            )
            audit_logs.append(audit_log)

        return audit_logs
