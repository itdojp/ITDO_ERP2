"""Audit service."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.user import User


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

    def log(
        self,
        action: str,
        resource_type: str,
        resource_id: int,
        user: User,
        changes: dict,
        organization_id: Optional[int] = None,
    ) -> None:
        """Log an audit event."""
        if organization_id is None:
            # Try to get organization from user context
            organization_id = 1  # Default for mock

        log = AuditLog(
            organization_id=organization_id,
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

        # Apply pagination
        offset = (page - 1) * limit
        items = filtered_logs[offset : offset + limit]

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
