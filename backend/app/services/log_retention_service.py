"""Log retention and cleanup service for audit logs and security events."""

import asyncio
import gzip
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.security_event import SecurityAlert, SecurityEvent, SecurityIncident
from app.models.user_activity_log import UserActivityLog


class LogRetentionPolicy:
    """Defines retention policy for different types of logs."""

    def __init__(
        self,
        audit_logs_days: int = 2555,  # 7 years for compliance
        security_events_days: int = 1095,  # 3 years
        security_incidents_days: int = 2555,  # 7 years for compliance
        security_alerts_days: int = 365,  # 1 year
        activity_logs_days: int = 730,  # 2 years
        enable_compression: bool = True,
        archive_before_deletion: bool = True,
        archive_path: str = "/var/log/erp/archives",
    ):
        """Initialize retention policy."""
        self.audit_logs_days = audit_logs_days
        self.security_events_days = security_events_days
        self.security_incidents_days = security_incidents_days
        self.security_alerts_days = security_alerts_days
        self.activity_logs_days = activity_logs_days
        self.enable_compression = enable_compression
        self.archive_before_deletion = archive_before_deletion
        self.archive_path = archive_path
        
        # Ensure archive directory exists
        if self.archive_before_deletion:
            os.makedirs(self.archive_path, exist_ok=True)


class LogRetentionService:
    """Service for managing log retention and cleanup."""

    def __init__(self, db: AsyncSession | Session, policy: Optional[LogRetentionPolicy] = None):
        """Initialize log retention service."""
        self.db = db
        self.policy = policy or LogRetentionPolicy()

    async def apply_retention_policy(
        self,
        organization_id: Optional[int] = None,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """Apply retention policy to all log types."""
        results = {
            "execution_time": datetime.utcnow().isoformat(),
            "dry_run": dry_run,
            "organization_id": organization_id,
            "cleanup_results": {},
        }
        
        # Cleanup audit logs
        audit_result = await self._cleanup_audit_logs(organization_id, dry_run)
        results["cleanup_results"]["audit_logs"] = audit_result
        
        # Cleanup security events
        events_result = await self._cleanup_security_events(organization_id, dry_run)
        results["cleanup_results"]["security_events"] = events_result
        
        # Cleanup security incidents
        incidents_result = await self._cleanup_security_incidents(organization_id, dry_run)
        results["cleanup_results"]["security_incidents"] = incidents_result
        
        # Cleanup security alerts
        alerts_result = await self._cleanup_security_alerts(organization_id, dry_run)
        results["cleanup_results"]["security_alerts"] = alerts_result
        
        # Cleanup activity logs
        activity_result = await self._cleanup_activity_logs(organization_id, dry_run)
        results["cleanup_results"]["activity_logs"] = activity_result
        
        # Calculate totals
        total_archived = sum(
            result.get("archived_count", 0) for result in results["cleanup_results"].values()
        )
        total_deleted = sum(
            result.get("deleted_count", 0) for result in results["cleanup_results"].values()
        )
        
        results["summary"] = {
            "total_archived": total_archived,
            "total_deleted": total_deleted,
            "policy_applied": not dry_run,
        }
        
        return results

    async def _cleanup_audit_logs(
        self, organization_id: Optional[int], dry_run: bool
    ) -> Dict[str, Any]:
        """Cleanup audit logs according to retention policy."""
        cutoff_date = datetime.utcnow() - timedelta(days=self.policy.audit_logs_days)
        
        # Build query
        query = select(AuditLog).where(AuditLog.created_at < cutoff_date)
        if organization_id:
            query = query.where(AuditLog.organization_id == organization_id)
        
        # Get logs to be processed
        result = await self.db.execute(query)
        logs_to_process = result.scalars().all()
        
        archived_count = 0
        deleted_count = 0
        
        if logs_to_process and not dry_run:
            # Archive if enabled
            if self.policy.archive_before_deletion:
                archived_count = await self._archive_audit_logs(logs_to_process)
            
            # Delete logs
            delete_query = delete(AuditLog).where(AuditLog.created_at < cutoff_date)
            if organization_id:
                delete_query = delete_query.where(AuditLog.organization_id == organization_id)
            
            await self.db.execute(delete_query)
            deleted_count = len(logs_to_process)
            
            await self._async_commit()
        
        return {
            "log_type": "audit_logs",
            "cutoff_date": cutoff_date.isoformat(),
            "retention_days": self.policy.audit_logs_days,
            "found_count": len(logs_to_process),
            "archived_count": archived_count,
            "deleted_count": deleted_count if not dry_run else 0,
        }

    async def _cleanup_security_events(
        self, organization_id: Optional[int], dry_run: bool
    ) -> Dict[str, Any]:
        """Cleanup security events according to retention policy."""
        cutoff_date = datetime.utcnow() - timedelta(days=self.policy.security_events_days)
        
        # Build query
        query = select(SecurityEvent).where(SecurityEvent.created_at < cutoff_date)
        if organization_id:
            query = query.where(SecurityEvent.organization_id == organization_id)
        
        # Get events to be processed
        result = await self.db.execute(query)
        events_to_process = result.scalars().all()
        
        archived_count = 0
        deleted_count = 0
        
        if events_to_process and not dry_run:
            # Archive if enabled
            if self.policy.archive_before_deletion:
                archived_count = await self._archive_security_events(events_to_process)
            
            # Delete events
            delete_query = delete(SecurityEvent).where(SecurityEvent.created_at < cutoff_date)
            if organization_id:
                delete_query = delete_query.where(SecurityEvent.organization_id == organization_id)
            
            await self.db.execute(delete_query)
            deleted_count = len(events_to_process)
            
            await self._async_commit()
        
        return {
            "log_type": "security_events",
            "cutoff_date": cutoff_date.isoformat(),
            "retention_days": self.policy.security_events_days,
            "found_count": len(events_to_process),
            "archived_count": archived_count,
            "deleted_count": deleted_count if not dry_run else 0,
        }

    async def _cleanup_security_incidents(
        self, organization_id: Optional[int], dry_run: bool
    ) -> Dict[str, Any]:
        """Cleanup security incidents according to retention policy."""
        cutoff_date = datetime.utcnow() - timedelta(days=self.policy.security_incidents_days)
        
        # Build query - only cleanup resolved incidents
        query = select(SecurityIncident).where(
            and_(
                SecurityIncident.created_at < cutoff_date,
                SecurityIncident.resolved_at.isnot(None),
            )
        )
        if organization_id:
            query = query.where(SecurityIncident.organization_id == organization_id)
        
        # Get incidents to be processed
        result = await self.db.execute(query)
        incidents_to_process = result.scalars().all()
        
        archived_count = 0
        deleted_count = 0
        
        if incidents_to_process and not dry_run:
            # Archive if enabled
            if self.policy.archive_before_deletion:
                archived_count = await self._archive_security_incidents(incidents_to_process)
            
            # Delete incidents
            incident_ids = [incident.id for incident in incidents_to_process]
            delete_query = delete(SecurityIncident).where(SecurityIncident.id.in_(incident_ids))
            
            await self.db.execute(delete_query)
            deleted_count = len(incidents_to_process)
            
            await self._async_commit()
        
        return {
            "log_type": "security_incidents",
            "cutoff_date": cutoff_date.isoformat(),
            "retention_days": self.policy.security_incidents_days,
            "found_count": len(incidents_to_process),
            "archived_count": archived_count,
            "deleted_count": deleted_count if not dry_run else 0,
        }

    async def _cleanup_security_alerts(
        self, organization_id: Optional[int], dry_run: bool
    ) -> Dict[str, Any]:
        """Cleanup security alerts according to retention policy."""
        cutoff_date = datetime.utcnow() - timedelta(days=self.policy.security_alerts_days)
        
        # Build query - only cleanup acknowledged alerts
        query = select(SecurityAlert).where(
            and_(
                SecurityAlert.created_at < cutoff_date,
                SecurityAlert.acknowledged == True,  # noqa: E712
            )
        )
        if organization_id:
            query = query.where(SecurityAlert.organization_id == organization_id)
        
        # Get alerts to be processed
        result = await self.db.execute(query)
        alerts_to_process = result.scalars().all()
        
        archived_count = 0
        deleted_count = 0
        
        if alerts_to_process and not dry_run:
            # Archive if enabled
            if self.policy.archive_before_deletion:
                archived_count = await self._archive_security_alerts(alerts_to_process)
            
            # Delete alerts
            alert_ids = [alert.id for alert in alerts_to_process]
            delete_query = delete(SecurityAlert).where(SecurityAlert.id.in_(alert_ids))
            
            await self.db.execute(delete_query)
            deleted_count = len(alerts_to_process)
            
            await self._async_commit()
        
        return {
            "log_type": "security_alerts",
            "cutoff_date": cutoff_date.isoformat(),
            "retention_days": self.policy.security_alerts_days,
            "found_count": len(alerts_to_process),
            "archived_count": archived_count,
            "deleted_count": deleted_count if not dry_run else 0,
        }

    async def _cleanup_activity_logs(
        self, organization_id: Optional[int], dry_run: bool
    ) -> Dict[str, Any]:
        """Cleanup activity logs according to retention policy."""
        cutoff_date = datetime.utcnow() - timedelta(days=self.policy.activity_logs_days)
        
        # Build query
        query = select(UserActivityLog).where(UserActivityLog.created_at < cutoff_date)
        if organization_id:
            # Assuming UserActivityLog has organization context through user
            # This might need adjustment based on actual model structure
            pass
        
        # Get logs to be processed
        result = await self.db.execute(query)
        logs_to_process = result.scalars().all()
        
        archived_count = 0
        deleted_count = 0
        
        if logs_to_process and not dry_run:
            # Archive if enabled
            if self.policy.archive_before_deletion:
                archived_count = await self._archive_activity_logs(logs_to_process)
            
            # Delete logs
            delete_query = delete(UserActivityLog).where(UserActivityLog.created_at < cutoff_date)
            
            await self.db.execute(delete_query)
            deleted_count = len(logs_to_process)
            
            await self._async_commit()
        
        return {
            "log_type": "activity_logs",
            "cutoff_date": cutoff_date.isoformat(),
            "retention_days": self.policy.activity_logs_days,
            "found_count": len(logs_to_process),
            "archived_count": archived_count,
            "deleted_count": deleted_count if not dry_run else 0,
        }

    # Archive methods

    async def _archive_audit_logs(self, logs: List[AuditLog]) -> int:
        """Archive audit logs to file system."""
        archive_data = []
        
        for log in logs:
            archive_data.append({
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "organization_id": log.organization_id,
                "changes": log.changes,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "checksum": log.checksum,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            })
        
        await self._write_archive_file("audit_logs", archive_data)
        return len(logs)

    async def _archive_security_events(self, events: List[SecurityEvent]) -> int:
        """Archive security events to file system."""
        archive_data = []
        
        for event in events:
            archive_data.append({
                "id": event.id,
                "event_id": event.event_id,
                "event_type": event.event_type.value if event.event_type else None,
                "threat_level": event.threat_level.value if event.threat_level else None,
                "user_id": event.user_id,
                "organization_id": event.organization_id,
                "title": event.title,
                "description": event.description,
                "details": event.details,
                "source_ip": event.source_ip,
                "user_agent": event.user_agent,
                "session_id": event.session_id,
                "api_endpoint": event.api_endpoint,
                "http_method": event.http_method,
                "risk_score": event.risk_score,
                "confidence": event.confidence,
                "evidence": event.evidence,
                "recommended_actions": event.recommended_actions,
                "auto_response_taken": event.auto_response_taken,
                "resolved": event.resolved,
                "resolved_by": event.resolved_by,
                "resolved_at": event.resolved_at.isoformat() if event.resolved_at else None,
                "resolution_notes": event.resolution_notes,
                "checksum": event.checksum,
                "created_at": event.created_at.isoformat() if event.created_at else None,
                "updated_at": event.updated_at.isoformat() if event.updated_at else None,
            })
        
        await self._write_archive_file("security_events", archive_data)
        return len(events)

    async def _archive_security_incidents(self, incidents: List[SecurityIncident]) -> int:
        """Archive security incidents to file system."""
        archive_data = []
        
        for incident in incidents:
            archive_data.append({
                "id": incident.id,
                "incident_id": incident.incident_id,
                "title": incident.title,
                "description": incident.description,
                "severity": incident.severity.value if incident.severity else None,
                "status": incident.status.value if incident.status else None,
                "category": incident.category,
                "organization_id": incident.organization_id,
                "affected_users": incident.affected_users,
                "affected_resources": incident.affected_resources,
                "assigned_to": incident.assigned_to,
                "investigation_notes": incident.investigation_notes,
                "timeline": incident.timeline,
                "related_events": incident.related_events,
                "resolution": incident.resolution,
                "lessons_learned": incident.lessons_learned,
                "created_at": incident.created_at.isoformat() if incident.created_at else None,
                "updated_at": incident.updated_at.isoformat() if incident.updated_at else None,
                "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
            })
        
        await self._write_archive_file("security_incidents", archive_data)
        return len(incidents)

    async def _archive_security_alerts(self, alerts: List[SecurityAlert]) -> int:
        """Archive security alerts to file system."""
        archive_data = []
        
        for alert in alerts:
            archive_data.append({
                "id": alert.id,
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type,
                "severity": alert.severity.value if alert.severity else None,
                "title": alert.title,
                "message": alert.message,
                "user_id": alert.user_id,
                "organization_id": alert.organization_id,
                "related_event_id": alert.related_event_id,
                "related_incident_id": alert.related_incident_id,
                "recipients": alert.recipients,
                "delivery_methods": alert.delivery_methods,
                "delivered_at": alert.delivered_at.isoformat() if alert.delivered_at else None,
                "acknowledged": alert.acknowledged,
                "acknowledged_by": alert.acknowledged_by,
                "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
            })
        
        await self._write_archive_file("security_alerts", archive_data)
        return len(alerts)

    async def _archive_activity_logs(self, logs: List[UserActivityLog]) -> int:
        """Archive activity logs to file system."""
        archive_data = []
        
        for log in logs:
            archive_data.append({
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "details": log.details,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            })
        
        await self._write_archive_file("activity_logs", archive_data)
        return len(logs)

    async def _write_archive_file(self, log_type: str, data: List[Dict[str, Any]]) -> None:
        """Write archive data to compressed file."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{log_type}_archive_{timestamp}.json"
        
        if self.policy.enable_compression:
            filename += ".gz"
            filepath = os.path.join(self.policy.archive_path, filename)
            
            with gzip.open(filepath, "wt", encoding="utf-8") as f:
                json.dump({
                    "archive_metadata": {
                        "log_type": log_type,
                        "archive_timestamp": timestamp,
                        "record_count": len(data),
                        "compressed": True,
                    },
                    "records": data,
                }, f, indent=2)
        else:
            filepath = os.path.join(self.policy.archive_path, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "archive_metadata": {
                        "log_type": log_type,
                        "archive_timestamp": timestamp,
                        "record_count": len(data),
                        "compressed": False,
                    },
                    "records": data,
                }, f, indent=2)

    # Utility methods

    async def get_storage_statistics(self, organization_id: Optional[int] = None) -> Dict[str, Any]:
        """Get storage statistics for all log types."""
        stats = {
            "organization_id": organization_id,
            "generated_at": datetime.utcnow().isoformat(),
            "log_counts": {},
            "estimated_storage": {},
        }
        
        # Audit logs
        audit_query = select(func.count(AuditLog.id))
        if organization_id:
            audit_query = audit_query.where(AuditLog.organization_id == organization_id)
        audit_result = await self.db.execute(audit_query)
        audit_count = audit_result.scalar()
        
        stats["log_counts"]["audit_logs"] = audit_count
        stats["estimated_storage"]["audit_logs_mb"] = audit_count * 1024 / (1024 * 1024)  # 1KB per log
        
        # Security events
        events_query = select(func.count(SecurityEvent.id))
        if organization_id:
            events_query = events_query.where(SecurityEvent.organization_id == organization_id)
        events_result = await self.db.execute(events_query)
        events_count = events_result.scalar()
        
        stats["log_counts"]["security_events"] = events_count
        stats["estimated_storage"]["security_events_mb"] = events_count * 2048 / (1024 * 1024)  # 2KB per event
        
        # Security incidents
        incidents_query = select(func.count(SecurityIncident.id))
        if organization_id:
            incidents_query = incidents_query.where(SecurityIncident.organization_id == organization_id)
        incidents_result = await self.db.execute(incidents_query)
        incidents_count = incidents_result.scalar()
        
        stats["log_counts"]["security_incidents"] = incidents_count
        stats["estimated_storage"]["security_incidents_mb"] = incidents_count * 4096 / (1024 * 1024)  # 4KB per incident
        
        # Security alerts
        alerts_query = select(func.count(SecurityAlert.id))
        if organization_id:
            alerts_query = alerts_query.where(SecurityAlert.organization_id == organization_id)
        alerts_result = await self.db.execute(alerts_query)
        alerts_count = alerts_result.scalar()
        
        stats["log_counts"]["security_alerts"] = alerts_count
        stats["estimated_storage"]["security_alerts_mb"] = alerts_count * 1024 / (1024 * 1024)  # 1KB per alert
        
        # Activity logs
        activity_query = select(func.count(UserActivityLog.id))
        activity_result = await self.db.execute(activity_query)
        activity_count = activity_result.scalar()
        
        stats["log_counts"]["activity_logs"] = activity_count
        stats["estimated_storage"]["activity_logs_mb"] = activity_count * 512 / (1024 * 1024)  # 0.5KB per log
        
        # Calculate totals
        total_logs = sum(stats["log_counts"].values())
        total_storage_mb = sum(stats["estimated_storage"].values())
        
        stats["totals"] = {
            "total_logs": total_logs,
            "total_storage_mb": round(total_storage_mb, 2),
            "total_storage_gb": round(total_storage_mb / 1024, 2),
        }
        
        return stats

    async def get_retention_policy_status(self) -> Dict[str, Any]:
        """Get current retention policy configuration."""
        return {
            "policy_configuration": {
                "audit_logs_retention_days": self.policy.audit_logs_days,
                "security_events_retention_days": self.policy.security_events_days,
                "security_incidents_retention_days": self.policy.security_incidents_days,
                "security_alerts_retention_days": self.policy.security_alerts_days,
                "activity_logs_retention_days": self.policy.activity_logs_days,
                "enable_compression": self.policy.enable_compression,
                "archive_before_deletion": self.policy.archive_before_deletion,
                "archive_path": self.policy.archive_path,
            },
            "compliance_notes": {
                "audit_logs": "7 years retention for regulatory compliance",
                "security_incidents": "7 years retention for regulatory compliance",
                "security_events": "3 years retention for security analysis",
                "security_alerts": "1 year retention for operational needs",
                "activity_logs": "2 years retention for audit purposes",
            },
        }

    async def _async_commit(self):
        """Handle async commit for AsyncSession."""
        if hasattr(self.db, 'commit'):
            await self.db.commit()
        else:
            self.db.commit()


# Scheduled task runner
class LogRetentionScheduler:
    """Scheduler for automated log retention tasks."""

    def __init__(self, db_factory: callable, policy: Optional[LogRetentionPolicy] = None):
        """Initialize retention scheduler."""
        self.db_factory = db_factory
        self.policy = policy or LogRetentionPolicy()
        self.is_running = False

    async def start_scheduled_cleanup(
        self,
        interval_hours: int = 24,
        organization_id: Optional[int] = None,
    ) -> None:
        """Start scheduled cleanup process."""
        self.is_running = True
        
        while self.is_running:
            try:
                # Create new database session for this cleanup run
                async with self.db_factory() as db:
                    retention_service = LogRetentionService(db, self.policy)
                    
                    result = await retention_service.apply_retention_policy(
                        organization_id=organization_id,
                        dry_run=False,
                    )
                    
                    print(f"Scheduled log cleanup completed: {result['summary']}")
                
                # Wait for next interval
                await asyncio.sleep(interval_hours * 3600)
                
            except Exception as e:
                print(f"Error during scheduled log cleanup: {e}")
                # Wait before retrying
                await asyncio.sleep(300)  # 5 minutes

    def stop_scheduled_cleanup(self) -> None:
        """Stop scheduled cleanup process."""
        self.is_running = False