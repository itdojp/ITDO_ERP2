"""Audit logging service."""

from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.user import User


class AuditLogger:
    """Audit logger for tracking system changes."""

    @staticmethod
    def log(
        action: str,
        resource_type: str,
        resource_id: int,
        user: User,
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
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            organization_id=organization_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Calculate checksum for integrity
        audit.checksum = audit.calculate_checksum()

        db.add(audit)
        db.flush()

        return audit


class AuditService:
    """Service for querying audit logs."""

    def get_audit_logs(
        self,
        user: User,
        db: Session,
        organization_id: int | None = None,
        resource_type: str | None = None,
        action: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Get audit logs with filtering."""
        query = db.query(AuditLog)

        # Filter by organization if not superuser
        if not user.is_superuser:
            user_org_ids = [o.id for o in user.get_organizations()]
            query = query.filter(AuditLog.organization_id.in_(user_org_ids))

        # Apply filters
        if organization_id:
            query = query.filter(AuditLog.organization_id == organization_id)

        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)

        if action:
            query = query.filter(AuditLog.action == action)

        # Order by newest first
        query = query.order_by(AuditLog.created_at.desc())

        # Pagination
        total = query.count()
        offset = (page - 1) * limit
        items = query.offset(offset).limit(limit).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
        }
