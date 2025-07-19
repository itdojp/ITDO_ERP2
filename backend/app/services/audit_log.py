"""Audit log service implementation."""

import csv
import io
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.audit_log_extended import (
    AuditLogAlert,
    AuditLogAlertCreate,
    AuditLogCategory,
    AuditLogDetail,
    AuditLogFilter,
    AuditLogLevel,
    AuditLogRetentionPolicy,
    AuditLogSummary,
    AuditTrailReport,
)


class AuditLogService:
    """Service for managing audit logs."""

    def __init__(self, db: Session):
        """Initialize audit log service."""
        self.db = db

    def list_audit_logs(
        self, filter: AuditLogFilter, limit: int = 100, offset: int = 0
    ) -> List[AuditLogDetail]:
        """List audit logs with filtering."""
        query = self.db.query(AuditLog)

        # Apply filters
        if filter.user_id:
            query = query.filter(AuditLog.user_id == filter.user_id)
        if filter.entity_type:
            query = query.filter(AuditLog.resource_type == filter.entity_type)
        if filter.entity_id:
            query = query.filter(AuditLog.resource_id == filter.entity_id)
        if filter.action:
            query = query.filter(AuditLog.action == filter.action)
        if filter.date_from:
            query = query.filter(AuditLog.created_at >= filter.date_from)
        if filter.date_to:
            query = query.filter(AuditLog.created_at <= filter.date_to)

        # Get logs
        logs = (
            query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset).all()
        )

        # Convert to detail schema
        result = []
        for log in logs:
            # Get user info
            user = self.db.query(User).filter(User.id == log.user_id).first()

            result.append(
                AuditLogDetail(
                    id=log.id,
                    user_id=log.user_id,
                    user_email=user.email if user else None,
                    user_name=user.full_name if user else None,
                    action=log.action,
                    entity_type=log.resource_type,
                    entity_id=log.resource_id,
                    entity_name=None,  # Not available in current model
                    category=self._determine_category(log),
                    level=self._determine_level(log),
                    success=True,  # Default for now
                    ip_address=log.ip_address,
                    user_agent=log.user_agent,
                    changes=log.changes,
                    old_values=None,  # Not available in current model
                    new_values=None,  # Not available in current model
                    request_id=None,  # Required field
                    session_id=None,  # Required field
                    metadata=None,  # Required field
                    created_at=log.created_at,
                )
            )

        return result

    def get_audit_log_by_id(self, audit_log_id: int) -> Optional[AuditLogDetail]:
        """Get a specific audit log by ID."""
        audit_log = self.db.query(AuditLog).filter(AuditLog.id == audit_log_id).first()

        if not audit_log:
            return None

        return AuditLogDetail(
            id=audit_log.id,
            user_id=audit_log.user_id,
            user_email=None,  # Would need user lookup
            user_name=None,  # Would need user lookup
            entity_type=audit_log.resource_type,
            entity_id=audit_log.resource_id,
            entity_name=None,  # Not available in current model
            action=audit_log.action,
            changes=audit_log.changes,
            old_values=None,  # Not available in current model
            new_values=None,  # Not available in current model
            request_id=None,  # Required field
            session_id=None,  # Required field
            metadata=None,  # Required field
            created_at=audit_log.created_at,
            ip_address=audit_log.ip_address,
            user_agent=audit_log.user_agent,
            category=self._determine_category(audit_log),
            level=self._determine_level(audit_log),
        )

    def get_audit_log_summary(self, filter: AuditLogFilter) -> AuditLogSummary:
        """Get audit log summary statistics."""
        query = self.db.query(AuditLog)

        # Apply filters
        if filter.user_id:
            query = query.filter(AuditLog.user_id == filter.user_id)
        if filter.entity_type:
            query = query.filter(AuditLog.resource_type == filter.entity_type)
        if filter.date_from:
            query = query.filter(AuditLog.created_at >= filter.date_from)
        if filter.date_to:
            query = query.filter(AuditLog.created_at <= filter.date_to)

        # Get total count
        total_count = query.count()

        # Get date range
        base_query = self.db.query(
            func.min(AuditLog.created_at).label("min_date"),
            func.max(AuditLog.created_at).label("max_date"),
        )

        # Apply same filters as the main query
        if filter.user_id:
            base_query = base_query.filter(AuditLog.user_id == filter.user_id)
        if filter.entity_type:
            base_query = base_query.filter(AuditLog.resource_type == filter.entity_type)
        if filter.date_from:
            base_query = base_query.filter(AuditLog.created_at >= filter.date_from)
        if filter.date_to:
            base_query = base_query.filter(AuditLog.created_at <= filter.date_to)

        date_range = base_query.first()

        # Get counts by action
        by_action = {}
        action_counts = (
            query.with_entities(AuditLog.action, func.count(AuditLog.id))
            .group_by(AuditLog.action)
            .all()
        )
        for action, count in action_counts:
            by_action[action] = count

        # Get counts by entity type
        by_entity_type = {}
        entity_counts = (
            query.with_entities(AuditLog.resource_type, func.count(AuditLog.id))
            .group_by(AuditLog.resource_type)
            .all()
        )
        for entity_type, count in entity_counts:
            by_entity_type[entity_type] = count

        # Get top users
        by_user = []
        user_counts = (
            query.with_entities(AuditLog.user_id, func.count(AuditLog.id))
            .group_by(AuditLog.user_id)
            .order_by(func.count(AuditLog.id).desc())
            .limit(10)
            .all()
        )
        for user_id, count in user_counts:
            user = self.db.query(User).filter(User.id == user_id).first()
            by_user.append(
                {
                    "user_id": user_id,
                    "user_email": user.email if user else None,
                    "count": count,
                }
            )

        # Get unique counts
        unique_users = query.distinct(AuditLog.user_id).count()
        unique_ips = (
            query.filter(AuditLog.ip_address.isnot(None))
            .distinct(AuditLog.ip_address)
            .count()
        )

        # Handle date range with proper typing
        start_date = None
        end_date = None
        if (
            date_range
            and hasattr(date_range, "min_date")
            and hasattr(date_range, "max_date")
        ):
            start_date = date_range.min_date
            end_date = date_range.max_date

        return AuditLogSummary(
            total_count=total_count,
            date_range={
                "start": start_date,
                "end": end_date,
            },
            by_category={},  # Would need category field in model
            by_level={},  # Would need level field in model
            by_action=by_action,
            by_entity_type=by_entity_type,
            by_user=by_user,
            failed_attempts=0,  # Would need success field in model
            unique_users=unique_users,
            unique_ips=unique_ips,
        )

    def export_audit_logs(
        self,
        filter: AuditLogFilter,
        format: str,
        include_fields: Optional[List[str]] = None,
        exclude_fields: Optional[List[str]] = None,
        timezone: str = "UTC",
    ) -> Tuple[io.BytesIO, str, str]:
        """Export audit logs in various formats."""
        # Get filtered logs
        logs = self.list_audit_logs(filter, limit=10000, offset=0)

        if format == "csv":
            return self._export_to_csv(logs, include_fields, exclude_fields)
        elif format == "json":
            return self._export_to_json(logs, include_fields, exclude_fields)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def list_retention_policies(
        self, is_active: Optional[bool] = None
    ) -> List[AuditLogRetentionPolicy]:
        """List audit log retention policies."""
        # Mock implementation - would need actual storage
        policies = [
            AuditLogRetentionPolicy(
                id=1,
                name="Default Retention",
                description="Default retention policy for all logs",
                category=None,
                level=None,
                retention_days=90,
                archive_enabled=True,
                archive_location=None,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
            AuditLogRetentionPolicy(
                id=2,
                name="Security Events",
                description="Extended retention for security events",
                category=AuditLogCategory.SECURITY_EVENT,
                level=None,
                retention_days=365,
                archive_enabled=True,
                archive_location=None,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
        ]

        if is_active is not None:
            policies = [p for p in policies if p.is_active == is_active]

        return policies

    def create_retention_policy(
        self, policy: AuditLogRetentionPolicy, created_by: int
    ) -> AuditLogRetentionPolicy:
        """Create audit log retention policy."""
        # Mock implementation
        policy.id = 3
        policy.created_at = datetime.utcnow()
        policy.updated_at = datetime.utcnow()
        return policy

    def list_audit_alerts(
        self, is_active: Optional[bool] = None
    ) -> List[AuditLogAlert]:
        """List audit log alerts."""
        # Mock implementation
        alerts = [
            AuditLogAlert(
                id=1,
                name="Failed Login Attempts",
                description="Alert on multiple failed login attempts",
                category=AuditLogCategory.AUTHENTICATION,
                level=AuditLogLevel.WARNING,
                action_pattern="login_failed",
                threshold=5,
                time_window=10,
                alert_channels=["email"],
                alert_recipients=["security@example.com"],
                is_active=True,
                last_triggered=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
        ]

        if is_active is not None:
            alerts = [a for a in alerts if a.is_active == is_active]

        return alerts

    def create_audit_alert(
        self, alert: AuditLogAlertCreate, created_by: int
    ) -> AuditLogAlert:
        """Create audit log alert."""
        # Mock implementation
        return AuditLogAlert(
            id=2,
            **alert.dict(),
            last_triggered=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    def update_audit_alert(
        self, alert_id: int, alert: AuditLogAlertCreate, updated_by: int
    ) -> AuditLogAlert:
        """Update audit log alert."""
        # Mock implementation
        existing_alerts = self.list_audit_alerts()
        for existing in existing_alerts:
            if existing.id == alert_id:
                return AuditLogAlert(
                    id=alert_id,
                    **alert.dict(),
                    created_at=existing.created_at,
                    updated_at=datetime.utcnow(),
                )
        raise ValueError(f"Alert with id {alert_id} not found")

    def delete_audit_alert(self, alert_id: int) -> None:
        """Delete audit log alert."""
        # Mock implementation
        existing_alerts = self.list_audit_alerts()
        if not any(a.id == alert_id for a in existing_alerts):
            raise ValueError(f"Alert with id {alert_id} not found")

    def generate_audit_trail_report(
        self, period_start: datetime, period_end: datetime, generated_by: int
    ) -> AuditTrailReport:
        """Generate comprehensive audit trail report."""
        # Get summary for period
        filter = AuditLogFilter(date_from=period_start, date_to=period_end)
        summary = self.get_audit_log_summary(filter)

        # Get high risk events (mock)
        high_risk_events: List[AuditLogDetail] = []

        # Get failed access attempts (mock)
        failed_access_attempts: List[AuditLogDetail] = []

        # Get permission changes
        permission_filter = AuditLogFilter(
            date_from=period_start,
            date_to=period_end,
            entity_type="permission",
        )
        permission_changes = self.list_audit_logs(permission_filter, limit=100)

        # Get data modifications
        data_filter = AuditLogFilter(
            date_from=period_start,
            date_to=period_end,
            action="update",
        )
        data_modifications = self.list_audit_logs(data_filter, limit=100)

        # Detect anomalies (mock)
        anomalies: List[Dict[str, Any]] = []

        # Generate recommendations
        recommendations = [
            "Enable multi-factor authentication for all admin users",
            "Review and update retention policies for compliance",
            "Implement automated alert monitoring",
        ]

        return AuditTrailReport(
            report_id=str(uuid.uuid4()),
            generated_at=datetime.utcnow(),
            generated_by=generated_by,
            period_start=period_start,
            period_end=period_end,
            summary=summary,
            high_risk_events=high_risk_events,
            failed_access_attempts=failed_access_attempts,
            permission_changes=permission_changes,
            data_modifications=data_modifications,
            anomalies=anomalies,
            recommendations=recommendations,
        )

    def cleanup_audit_logs(
        self,
        apply_retention_policies: bool = True,
        archive_before_delete: bool = True,
        performed_by: int = None,
    ) -> Tuple[int, int]:
        """Clean up audit logs based on retention policies."""
        deleted_count = 0
        archived_count = 0

        if apply_retention_policies:
            # Get retention policies
            policies = self.list_retention_policies(is_active=True)

            for policy in policies:
                cutoff_date = datetime.utcnow() - timedelta(days=policy.retention_days)

                # Find logs to delete
                query = self.db.query(AuditLog).filter(
                    AuditLog.created_at < cutoff_date
                )

                if policy.category:
                    # Would need category field in model
                    pass

                logs_to_delete = query.all()

                if archive_before_delete and policy.archive_enabled:
                    # Archive logs (mock)
                    archived_count += len(logs_to_delete)

                # Delete logs
                deleted_count += query.delete()

        self.db.commit()

        return deleted_count, archived_count

    def _determine_category(self, log: AuditLog) -> Optional[AuditLogCategory]:
        """Determine audit log category based on action and entity."""
        if log.action in ["login", "logout", "login_failed"]:
            return AuditLogCategory.AUTHENTICATION
        elif log.resource_type == "permission":
            return AuditLogCategory.PERMISSION_CHANGE
        elif log.resource_type == "user":
            return AuditLogCategory.USER_MANAGEMENT
        elif log.action in ["create", "update", "delete"]:
            return AuditLogCategory.DATA_MODIFICATION
        else:
            return AuditLogCategory.DATA_ACCESS

    def _determine_level(self, log: AuditLog) -> AuditLogLevel:
        """Determine audit log level based on action."""
        if "failed" in log.action or "error" in log.action:
            return AuditLogLevel.ERROR
        elif "delete" in log.action:
            return AuditLogLevel.WARNING
        else:
            return AuditLogLevel.INFO

    def _export_to_csv(
        self,
        logs: List[AuditLogDetail],
        include_fields: Optional[List[str]] = None,
        exclude_fields: Optional[List[str]] = None,
    ) -> Tuple[io.BytesIO, str, str]:
        """Export logs to CSV format."""
        output = io.StringIO()

        # Determine fields
        if logs:
            all_fields = logs[0].dict().keys()
            if include_fields:
                fields = [f for f in include_fields if f in all_fields]
            else:
                fields = list(all_fields)

            if exclude_fields:
                fields = [f for f in fields if f not in exclude_fields]

            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()

            for log in logs:
                row = {k: v for k, v in log.dict().items() if k in fields}
                writer.writerow(row)

        # Convert to bytes
        output_bytes = io.BytesIO(output.getvalue().encode("utf-8"))
        filename = f"audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

        return output_bytes, filename, "text/csv"

    def _export_to_json(
        self,
        logs: List[AuditLogDetail],
        include_fields: Optional[List[str]] = None,
        exclude_fields: Optional[List[str]] = None,
    ) -> Tuple[io.BytesIO, str, str]:
        """Export logs to JSON format."""
        data = []

        for log in logs:
            log_dict = log.dict()

            if include_fields:
                log_dict = {k: v for k, v in log_dict.items() if k in include_fields}

            if exclude_fields:
                log_dict = {
                    k: v for k, v in log_dict.items() if k not in exclude_fields
                }

            data.append(log_dict)

        # Convert to JSON with custom encoder for datetime
        json_str = json.dumps(data, default=str, indent=2)
        output_bytes = io.BytesIO(json_str.encode("utf-8"))
        filename = f"audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

        return output_bytes, filename, "application/json"
