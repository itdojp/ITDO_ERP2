"""Audit service."""

<<<<<<< HEAD
from datetime import datetime
from typing import List, Optional
=======
import json
from datetime import datetime, timedelta
from typing import Any
>>>>>>> origin/main

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.audit import AuditLogSearch


class AuditLog:
    """Mock audit log model."""

    def __init__(
        self,
        organization_id: int,
        action: str,
        resource_type: str,
        resource_id: int,
        user_id: int,
    ):
        self.organization_id = organization_id
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.user_id = user_id
        self.created_at = datetime.utcnow()


class AuditLogList:
    """Mock audit log list."""

    def __init__(
        self, items: List[AuditLog], total: int, page: int = 1, limit: int = 10
    ):
        self.items = items
        self.total = total
        self.page = page
        self.limit = limit


class AuditService:
    """Audit service class."""

    def __init__(self):
        # Mock storage for audit logs
        self._logs: List[AuditLog] = []

<<<<<<< HEAD
=======
    def __init__(self, db: Session | None = None):
        """Initialize audit logger."""
        self.db = db

    @staticmethod
>>>>>>> origin/main
    def log(
        self,
        action: str,
        resource_type: str,
        resource_id: int,
        user: User,
<<<<<<< HEAD
        changes: dict,
        organization_id: Optional[int] = None,
    ) -> None:
        """Log an audit event."""
        if organization_id is None:
            # Try to get organization from user context
            organization_id = 1  # Default for mock

        log = AuditLog(
            organization_id=organization_id,
=======
        changes: dict[str, Any],
        db: Session,
        organization_id: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log an audit entry."""
        # Create audit log
        audit = AuditLog(
            user_id=user.id,
>>>>>>> origin/main
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user.id,
        )

        self._logs.append(log)

    def get_audit_logs(
        self,
        user: User,
        db: Session,
<<<<<<< HEAD
        organization_id: Optional[int] = None,
        page: int = 1,
        limit: int = 10,
    ) -> AuditLogList:
        """Get audit logs for organization."""
        # Filter logs by organization
        filtered_logs = []
        for log in self._logs:
            if organization_id is None or log.organization_id == organization_id:
                filtered_logs.append(log)
=======
        organization_id: int | None = None,
        resource_type: str | None = None,
        action: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Get audit logs with filtering."""
        query = db.query(AuditLog)
>>>>>>> origin/main

        # Apply pagination
        offset = (page - 1) * limit
        items = filtered_logs[offset : offset + limit]

<<<<<<< HEAD
        return AuditLogList(
            items=items, total=len(filtered_logs), page=page, limit=limit
        )


class AuditLogger:
    """Mock audit logger."""

    @staticmethod
    def log(
        action: str, resource_type: str, resource_id: int, user: User, changes: dict
    ) -> None:
        """Log audit event."""
        # Mock implementation
        pass
=======
        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
        }

    def search_audit_logs(
        self,
        search_criteria: AuditLogSearch,
        user: User,
        db: Session | None = None,
    ) -> dict[str, Any]:
        """Advanced search for audit logs."""
        if db is None:
            raise ValueError("Database session is required")
        query = db.query(AuditLog)

        # Filter by organization if not superuser
        if not user.is_superuser:
            user_org_ids = [o.id for o in user.get_organizations()]
            query = query.filter(AuditLog.organization_id.in_(user_org_ids))

        # Apply search filters
        if search_criteria.organization_id:
            query = query.filter(
                AuditLog.organization_id == search_criteria.organization_id
            )

        if search_criteria.resource_types:
            query = query.filter(
                AuditLog.resource_type.in_(search_criteria.resource_types)
            )

        if search_criteria.actions:
            query = query.filter(AuditLog.action.in_(search_criteria.actions))

        if search_criteria.user_ids:
            query = query.filter(AuditLog.user_id.in_(search_criteria.user_ids))

        if search_criteria.date_from:
            query = query.filter(AuditLog.created_at >= search_criteria.date_from)

        if search_criteria.date_to:
            query = query.filter(AuditLog.created_at <= search_criteria.date_to)

        # Order by newest first
        query = query.order_by(AuditLog.created_at.desc())

        # Pagination
        total = query.count()
        offset = search_criteria.offset
        items = query.offset(offset).limit(search_criteria.limit).all()

        return {
            "items": items,
            "total": total,
            "offset": offset,
            "limit": search_criteria.limit,
        }

    def get_audit_statistics(
        self,
        organization_id: int,
        date_from: datetime,
        date_to: datetime,
        requester: User,
        db: Session | None = None,
    ) -> dict[str, Any]:
        """Get audit log statistics."""
        query = db.query(AuditLog)

        # Filter by organization if not superuser
        if not requester.is_superuser:
            user_org_ids = [o.id for o in requester.get_organizations()]
            query = query.filter(AuditLog.organization_id.in_(user_org_ids))

        if organization_id:
            query = query.filter(AuditLog.organization_id == organization_id)

        # Filter by date range
        query = query.filter(AuditLog.created_at >= date_from)
        query = query.filter(AuditLog.created_at <= date_to)

        # Get statistics
        total_logs = query.count()

        # Count by action
        action_counts = (
            query.with_entities(AuditLog.action, func.count(AuditLog.id))
            .group_by(AuditLog.action)
            .all()
        )

        # Count by resource type
        resource_counts = (
            query.with_entities(AuditLog.resource_type, func.count(AuditLog.id))
            .group_by(AuditLog.resource_type)
            .all()
        )

        return {
            "total_logs": total_logs,
            "date_from": date_from,
            "date_to": date_to,
            "action_counts": {action: count for action, count in action_counts},
            "resource_counts": {resource: count for resource, count in resource_counts},
        }

    def export_audit_logs_csv(
        self,
        organization_id: int,
        requester: User,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        actions: list[str] | None = None,
        resource_types: list[str] | None = None,
        db: Session | None = None,
    ) -> str:
        """Export audit logs as CSV."""
        query = db.query(AuditLog)

        # Filter by organization if not superuser
        if not requester.is_superuser:
            user_org_ids = [o.id for o in requester.get_organizations()]
            query = query.filter(AuditLog.organization_id.in_(user_org_ids))

        if organization_id:
            query = query.filter(AuditLog.organization_id == organization_id)

        if date_from:
            query = query.filter(AuditLog.created_at >= date_from)
        if date_to:
            query = query.filter(AuditLog.created_at <= date_to)
        if actions:
            query = query.filter(AuditLog.action.in_(actions))
        if resource_types:
            query = query.filter(AuditLog.resource_type.in_(resource_types))

        logs = query.order_by(AuditLog.created_at.desc()).all()

        # Simple CSV format
        csv_rows = [
            "ID,Action,Resource Type,Resource ID,User ID,Organization ID,Created At"
        ]
        for log in logs:
            csv_rows.append(
                f"{log.id},{log.action},{log.resource_type},{log.resource_id},{log.user_id},{log.organization_id},{log.created_at}"
            )

        return "\n".join(csv_rows)

    def export_audit_logs(
        self,
        user: User,
        db: Session,
        organization_id: int | None = None,
        format: str = "json",
    ) -> str:
        """Export audit logs to specified format."""
        query = db.query(AuditLog)

        # Filter by organization if not superuser
        if not user.is_superuser:
            user_org_ids = [o.id for o in user.get_organizations()]
            query = query.filter(AuditLog.organization_id.in_(user_org_ids))

        if organization_id:
            query = query.filter(AuditLog.organization_id == organization_id)

        logs = query.order_by(AuditLog.created_at.desc()).all()

        if format == "json":
            return json.dumps(
                [
                    {
                        "id": log.id,
                        "action": log.action,
                        "resource_type": log.resource_type,
                        "resource_id": log.resource_id,
                        "user_id": log.user_id,
                        "organization_id": log.organization_id,
                        "changes": log.changes,
                        "ip_address": log.ip_address,
                        "user_agent": log.user_agent,
                        "created_at": log.created_at.isoformat(),
                    }
                    for log in logs
                ],
                indent=2,
            )
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def verify_log_integrity(
        self,
        log_id: int,
        requester: User,
        db: Session | None = None,
    ) -> bool:
        """Verify integrity of a specific audit log."""
        audit_log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
        if not audit_log:
            return False

        # Calculate current checksum
        current_checksum = audit_log.calculate_checksum()

        # Compare with stored checksum
        return current_checksum == audit_log.checksum

    def verify_audit_log_integrity(
        self,
        user: User,
        db: Session,
        audit_log_id: int,
    ) -> bool:
        """Verify integrity of a specific audit log."""
        audit_log = db.query(AuditLog).filter(AuditLog.id == audit_log_id).first()
        if not audit_log:
            return False

        # Calculate current checksum
        current_checksum = audit_log.calculate_checksum()

        # Compare with stored checksum
        return current_checksum == audit_log.checksum

    def verify_logs_integrity_bulk(
        self,
        organization_id: int,
        date_from: datetime,
        date_to: datetime,
        requester: User,
        db: Session | None = None,
    ) -> dict[str, Any]:
        """Verify integrity of multiple audit logs."""
        query = db.query(AuditLog)

        # Filter by organization if not superuser
        if not requester.is_superuser:
            user_org_ids = [o.id for o in requester.get_organizations()]
            query = query.filter(AuditLog.organization_id.in_(user_org_ids))

        if organization_id:
            query = query.filter(AuditLog.organization_id == organization_id)

        # Filter by date range
        query = query.filter(AuditLog.created_at >= date_from)
        query = query.filter(AuditLog.created_at <= date_to)

        logs = query.all()
        total = len(logs)
        verified = 0
        failed = []

        for log in logs:
            if self.verify_log_integrity(log.id, requester, db):
                verified += 1
            else:
                failed.append(log.id)

        return {
            "total_logs": total,
            "verified_logs": verified,
            "failed_logs": len(failed),
            "failed_log_ids": failed,
        }

    def bulk_verify_integrity(
        self,
        user: User,
        db: Session,
        organization_id: int | None = None,
    ) -> dict[str, Any]:
        """Bulk verify integrity of audit logs."""
        query = db.query(AuditLog)

        # Filter by organization if not superuser
        if not user.is_superuser:
            user_org_ids = [o.id for o in user.get_organizations()]
            query = query.filter(AuditLog.organization_id.in_(user_org_ids))

        if organization_id:
            query = query.filter(AuditLog.organization_id == organization_id)

        logs = query.all()
        total = len(logs)
        verified = 0
        failed = []

        for log in logs:
            if self.verify_audit_log_integrity(user, db, log.id):
                verified += 1
            else:
                failed.append(log.id)

        return {
            "total": total,
            "verified": verified,
            "failed": len(failed),
            "failed_ids": failed,
        }

    def filter_sensitive_data(
        self,
        user: User,
        db: Session,
        audit_logs: list[AuditLog],
    ) -> list[AuditLog]:
        """Filter out sensitive data from audit logs."""
        filtered_logs = []
        sensitive_fields = ["password", "token", "secret", "key"]

        for log in audit_logs:
            filtered_log = log
            if log.changes:
                filtered_changes = {}
                for key, value in log.changes.items():
                    if any(
                        sensitive_field in key.lower()
                        for sensitive_field in sensitive_fields
                    ):
                        filtered_changes[key] = "***REDACTED***"
                    else:
                        filtered_changes[key] = value
                filtered_log.changes = filtered_changes
            filtered_logs.append(filtered_log)

        return filtered_logs

    def get_organization_audit_logs(
        self,
        organization_id: int,
        requester: User,
        limit: int = 50,
        offset: int = 0,
        db: Session | None = None,
    ) -> list[AuditLog]:
        """Get audit logs for organization."""
        query = db.query(AuditLog)

        # Filter by organization if not superuser
        if not requester.is_superuser:
            user_org_ids = [o.id for o in requester.get_organizations()]
            query = query.filter(AuditLog.organization_id.in_(user_org_ids))

        if organization_id:
            query = query.filter(AuditLog.organization_id == organization_id)

        return (
            query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
        )

    def apply_retention_policy(
        self,
        organization_id: int,
        retention_days: int,
        requester: User,
        db: Session | None = None,
    ) -> int:
        """Apply retention policy to audit logs."""
        if not requester.is_superuser:
            raise PermissionError("Only superusers can apply retention policies")

        cutoff_date = datetime.now() - timedelta(days=retention_days)
        query = db.query(AuditLog).filter(AuditLog.created_at < cutoff_date)

        if organization_id:
            query = query.filter(AuditLog.organization_id == organization_id)

        deleted_count = query.count()
        query.delete(synchronize_session=False)
        db.commit()

        return deleted_count
>>>>>>> origin/main
