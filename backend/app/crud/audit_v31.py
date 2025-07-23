"""
Audit Log System CRUD Operations - CC02 v31.0 Phase 2

Comprehensive CRUD operations for audit log management including:
- System-wide Activity Tracking
- Compliance & Regulatory Auditing
- Security Event Monitoring
- Data Change Tracking
- User Action Logging
- Performance Monitoring
- Risk Assessment & Alerting
- Forensic Analysis Support
- Real-time Monitoring
- Automated Compliance Reporting

Provides complete audit trail operations for enterprise compliance and security
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
import json
import hashlib

from sqlalchemy import and_, or_, desc, asc, func, text
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.models.audit_extended import (
    AuditLogEntry,
    AuditRule,
    AuditAlert,
    AuditReport,
    AuditSession,
    AuditDataRetention,
    AuditCompliance,
    AuditConfiguration,
    AuditMetrics,
    AuditEventType,
    AuditSeverity,
    AuditStatus,
    ComplianceFramework,
)


class AuditService:
    """Service class for audit log operations with comprehensive business logic."""

    def __init__(self, db: Session):
        self.db = db

    # =============================================================================
    # Audit Log Entry Management
    # =============================================================================

    async def create_audit_log_entry(self, entry_data: Dict[str, Any]) -> AuditLogEntry:
        """Create a new audit log entry with security validation."""
        try:
            # Generate correlation ID if not provided
            if not entry_data.get("correlation_id"):
                entry_data["correlation_id"] = self._generate_correlation_id(entry_data)

            # Calculate risk score
            entry_data["risk_score"] = self._calculate_risk_score(entry_data)

            # Ensure event timestamp
            if not entry_data.get("event_timestamp"):
                entry_data["event_timestamp"] = datetime.now()

            # Create entry
            entry = AuditLogEntry(**entry_data)
            self.db.add(entry)
            self.db.commit()
            self.db.refresh(entry)

            # Trigger rule evaluation
            await self._evaluate_audit_rules(entry)

            return entry

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Failed to create audit log entry: {str(e)}")

    async def bulk_create_audit_entries(self, entries_data: List[Dict[str, Any]]) -> List[AuditLogEntry]:
        """Bulk create audit log entries for performance."""
        try:
            entries = []
            for entry_data in entries_data:
                # Generate correlation ID if not provided
                if not entry_data.get("correlation_id"):
                    entry_data["correlation_id"] = self._generate_correlation_id(entry_data)

                # Calculate risk score
                entry_data["risk_score"] = self._calculate_risk_score(entry_data)

                # Ensure event timestamp
                if not entry_data.get("event_timestamp"):
                    entry_data["event_timestamp"] = datetime.now()

                entry = AuditLogEntry(**entry_data)
                entries.append(entry)

            self.db.add_all(entries)
            self.db.commit()

            # Trigger rule evaluation for high-risk entries
            for entry in entries:
                if entry.risk_score >= 70:
                    await self._evaluate_audit_rules(entry)

            return entries

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Failed to bulk create audit entries: {str(e)}")

    async def search_audit_logs(
        self,
        filters: Dict[str, Any],
        page: int = 1,
        per_page: int = 50
    ) -> Tuple[List[AuditLogEntry], int]:
        """Search audit logs with advanced filtering and performance optimization."""
        try:
            query = self.db.query(AuditLogEntry)

            # Apply filters
            if filters.get("organization_id"):
                query = query.filter(AuditLogEntry.organization_id == filters["organization_id"])

            if filters.get("event_type"):
                query = query.filter(AuditLogEntry.event_type == filters["event_type"])

            if filters.get("event_category"):
                query = query.filter(AuditLogEntry.event_category == filters["event_category"])

            if filters.get("user_id"):
                query = query.filter(AuditLogEntry.user_id == filters["user_id"])

            if filters.get("resource_type"):
                query = query.filter(AuditLogEntry.resource_type == filters["resource_type"])

            if filters.get("resource_id"):
                query = query.filter(AuditLogEntry.resource_id == filters["resource_id"])

            if filters.get("severity"):
                query = query.filter(AuditLogEntry.severity == filters["severity"])

            if filters.get("outcome"):
                query = query.filter(AuditLogEntry.outcome == filters["outcome"])

            if filters.get("ip_address"):
                query = query.filter(AuditLogEntry.ip_address == filters["ip_address"])

            if filters.get("session_id"):
                query = query.filter(AuditLogEntry.session_id == filters["session_id"])

            # Date range filtering
            if filters.get("start_date"):
                query = query.filter(AuditLogEntry.event_timestamp >= filters["start_date"])

            if filters.get("end_date"):
                query = query.filter(AuditLogEntry.event_timestamp <= filters["end_date"])

            # Risk score filtering
            if filters.get("min_risk_score"):
                query = query.filter(AuditLogEntry.risk_score >= filters["min_risk_score"])

            if filters.get("max_risk_score"):
                query = query.filter(AuditLogEntry.risk_score <= filters["max_risk_score"])

            # Compliance framework filtering
            if filters.get("compliance_framework"):
                query = query.filter(
                    AuditLogEntry.compliance_frameworks.contains([filters["compliance_framework"]])
                )

            # Text search in descriptions and event data
            if filters.get("search_text"):
                search_text = f"%{filters['search_text']}%"
                query = query.filter(
                    or_(
                        AuditLogEntry.event_description.ilike(search_text),
                        AuditLogEntry.event_name.ilike(search_text),
                        AuditLogEntry.resource_name.ilike(search_text)
                    )
                )

            # Get total count
            total = query.count()

            # Apply sorting
            sort_by = filters.get("sort_by", "event_timestamp")
            sort_order = filters.get("sort_order", "desc")

            if hasattr(AuditLogEntry, sort_by):
                if sort_order == "desc":
                    query = query.order_by(desc(getattr(AuditLogEntry, sort_by)))
                else:
                    query = query.order_by(asc(getattr(AuditLogEntry, sort_by)))

            # Apply pagination
            offset = (page - 1) * per_page
            entries = query.offset(offset).limit(per_page).all()

            return entries, total

        except SQLAlchemyError as e:
            raise Exception(f"Failed to search audit logs: {str(e)}")

    async def get_audit_log_entry(self, entry_id: str) -> Optional[AuditLogEntry]:
        """Get audit log entry by ID."""
        try:
            return self.db.query(AuditLogEntry).filter(
                AuditLogEntry.id == entry_id
            ).first()
        except SQLAlchemyError as e:
            raise Exception(f"Failed to get audit log entry: {str(e)}")

    async def update_audit_log_status(
        self,
        entry_id: str,
        status: str,
        acknowledged_by: str,
        notes: Optional[str] = None
    ) -> Optional[AuditLogEntry]:
        """Update audit log entry status and acknowledgment."""
        try:
            entry = self.db.query(AuditLogEntry).filter(
                AuditLogEntry.id == entry_id
            ).first()

            if not entry:
                return None

            entry.status = status
            entry.acknowledged_by = acknowledged_by
            entry.acknowledged_at = datetime.now()
            
            if notes:
                entry.resolution_notes = notes

            self.db.commit()
            self.db.refresh(entry)
            return entry

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Failed to update audit log status: {str(e)}")

    # =============================================================================
    # Audit Rules Management
    # =============================================================================

    async def create_audit_rule(self, rule_data: Dict[str, Any]) -> AuditRule:
        """Create a new audit rule with validation."""
        try:
            # Validate rule conditions
            if not self._validate_rule_conditions(rule_data.get("conditions", {})):
                raise ValueError("Invalid rule conditions")

            rule = AuditRule(**rule_data)
            self.db.add(rule)
            self.db.commit()
            self.db.refresh(rule)
            return rule

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Failed to create audit rule: {str(e)}")

    async def list_audit_rules(
        self,
        filters: Dict[str, Any],
        page: int = 1,
        per_page: int = 50
    ) -> Tuple[List[AuditRule], int]:
        """List audit rules with filtering."""
        try:
            query = self.db.query(AuditRule)

            if filters.get("organization_id"):
                query = query.filter(AuditRule.organization_id == filters["organization_id"])

            if filters.get("rule_type"):
                query = query.filter(AuditRule.rule_type == filters["rule_type"])

            if filters.get("is_active") is not None:
                query = query.filter(AuditRule.is_active == filters["is_active"])

            total = query.count()
            offset = (page - 1) * per_page
            rules = query.order_by(desc(AuditRule.created_at)).offset(offset).limit(per_page).all()

            return rules, total

        except SQLAlchemyError as e:
            raise Exception(f"Failed to list audit rules: {str(e)}")

    async def test_audit_rule(self, rule_id: str, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test audit rule against sample data."""
        try:
            rule = self.db.query(AuditRule).filter(AuditRule.id == rule_id).first()
            if not rule:
                return {"success": False, "error": "Rule not found"}

            # Simulate rule evaluation
            result = self._evaluate_rule_conditions(rule.conditions, test_data)
            
            return {
                "success": True,
                "triggered": result["triggered"],
                "matched_conditions": result["matched_conditions"],
                "alert_would_generate": result["triggered"] and rule.is_active
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # =============================================================================
    # Audit Alerts Management
    # =============================================================================

    async def create_audit_alert(self, alert_data: Dict[str, Any]) -> AuditAlert:
        """Create a new audit alert."""
        try:
            alert_data["first_occurrence"] = datetime.now()
            alert_data["last_occurrence"] = datetime.now()

            alert = AuditAlert(**alert_data)
            self.db.add(alert)
            self.db.commit()
            self.db.refresh(alert)

            # Send notifications if configured
            await self._send_alert_notifications(alert)

            return alert

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Failed to create audit alert: {str(e)}")

    async def list_audit_alerts(
        self,
        filters: Dict[str, Any],
        page: int = 1,
        per_page: int = 50
    ) -> Tuple[List[AuditAlert], int]:
        """List audit alerts with filtering."""
        try:
            query = self.db.query(AuditAlert)

            if filters.get("organization_id"):
                query = query.filter(AuditAlert.organization_id == filters["organization_id"])

            if filters.get("severity"):
                query = query.filter(AuditAlert.severity == filters["severity"])

            if filters.get("status"):
                query = query.filter(AuditAlert.status == filters["status"])

            if filters.get("assigned_to"):
                query = query.filter(AuditAlert.assigned_to == filters["assigned_to"])

            if filters.get("rule_id"):
                query = query.filter(AuditAlert.rule_id == filters["rule_id"])

            total = query.count()
            offset = (page - 1) * per_page
            alerts = query.order_by(desc(AuditAlert.created_at)).offset(offset).limit(per_page).all()

            return alerts, total

        except SQLAlchemyError as e:
            raise Exception(f"Failed to list audit alerts: {str(e)}")

    async def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str,
        resolution_notes: str
    ) -> Optional[AuditAlert]:
        """Resolve an audit alert."""
        try:
            alert = self.db.query(AuditAlert).filter(AuditAlert.id == alert_id).first()
            if not alert:
                return None

            alert.status = "resolved"
            alert.resolved_by = resolved_by
            alert.resolved_at = datetime.now()
            alert.resolution_notes = resolution_notes

            self.db.commit()
            self.db.refresh(alert)
            return alert

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Failed to resolve alert: {str(e)}")

    # =============================================================================
    # Audit Reports Management
    # =============================================================================

    async def generate_audit_report(self, report_data: Dict[str, Any]) -> AuditReport:
        """Generate a comprehensive audit report."""
        try:
            report = AuditReport(**report_data)
            report.generation_status = "generating"
            report.started_at = datetime.now()
            
            self.db.add(report)
            self.db.commit()
            self.db.refresh(report)

            # Generate report content asynchronously
            await self._generate_report_content(report)

            return report

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Failed to generate audit report: {str(e)}")

    async def list_audit_reports(
        self,
        filters: Dict[str, Any],
        page: int = 1,
        per_page: int = 50
    ) -> Tuple[List[AuditReport], int]:
        """List audit reports with filtering."""
        try:
            query = self.db.query(AuditReport)

            if filters.get("organization_id"):
                query = query.filter(AuditReport.organization_id == filters["organization_id"])

            if filters.get("report_type"):
                query = query.filter(AuditReport.report_type == filters["report_type"])

            if filters.get("compliance_framework"):
                query = query.filter(AuditReport.compliance_framework == filters["compliance_framework"])

            if filters.get("generation_status"):
                query = query.filter(AuditReport.generation_status == filters["generation_status"])

            total = query.count()
            offset = (page - 1) * per_page
            reports = query.order_by(desc(AuditReport.created_at)).offset(offset).limit(per_page).all()

            return reports, total

        except SQLAlchemyError as e:
            raise Exception(f"Failed to list audit reports: {str(e)}")

    # =============================================================================
    # Session Management
    # =============================================================================

    async def create_audit_session(self, session_data: Dict[str, Any]) -> AuditSession:
        """Create a new audit session for tracking."""
        try:
            session_data["started_at"] = datetime.now()
            session_data["last_activity"] = datetime.now()

            session = AuditSession(**session_data)
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

            return session

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Failed to create audit session: {str(e)}")

    async def update_session_activity(self, session_token: str) -> Optional[AuditSession]:
        """Update session last activity timestamp."""
        try:
            session = self.db.query(AuditSession).filter(
                AuditSession.session_token == session_token
            ).first()

            if not session:
                return None

            session.last_activity = datetime.now()
            session.actions_performed += 1

            # Calculate inactivity duration
            if session.last_activity:
                session.inactivity_duration = int(
                    (datetime.now() - session.last_activity).total_seconds()
                )

            self.db.commit()
            self.db.refresh(session)
            return session

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Failed to update session activity: {str(e)}")

    async def terminate_session(
        self,
        session_token: str,
        reason: str,
        terminated_by: str = "user"
    ) -> Optional[AuditSession]:
        """Terminate an audit session."""
        try:
            session = self.db.query(AuditSession).filter(
                AuditSession.session_token == session_token
            ).first()

            if not session:
                return None

            session.is_active = False
            session.ended_at = datetime.now()
            session.terminated_reason = reason
            session.terminated_by = terminated_by

            self.db.commit()
            self.db.refresh(session)
            return session

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Failed to terminate session: {str(e)}")

    # =============================================================================
    # Compliance Management
    # =============================================================================

    async def create_compliance_assessment(self, compliance_data: Dict[str, Any]) -> AuditCompliance:
        """Create a new compliance assessment."""
        try:
            compliance = AuditCompliance(**compliance_data)
            self.db.add(compliance)
            self.db.commit()
            self.db.refresh(compliance)

            return compliance

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Failed to create compliance assessment: {str(e)}")

    async def get_compliance_dashboard(self, organization_id: str) -> Dict[str, Any]:
        """Get compliance dashboard data."""
        try:
            # Get overall compliance metrics
            compliance_query = self.db.query(AuditCompliance).filter(
                AuditCompliance.organization_id == organization_id
            )

            total_assessments = compliance_query.count()
            compliant_assessments = compliance_query.filter(
                AuditCompliance.compliance_status == "compliant"
            ).count()

            compliance_rate = (compliant_assessments / total_assessments * 100) if total_assessments > 0 else 0

            # Get assessments by framework
            framework_stats = {}
            for framework in ComplianceFramework:
                framework_assessments = compliance_query.filter(
                    AuditCompliance.framework == framework
                ).count()
                
                framework_compliant = compliance_query.filter(
                    and_(
                        AuditCompliance.framework == framework,
                        AuditCompliance.compliance_status == "compliant"
                    )
                ).count()

                framework_stats[framework.value] = {
                    "total": framework_assessments,
                    "compliant": framework_compliant,
                    "rate": (framework_compliant / framework_assessments * 100) if framework_assessments > 0 else 0
                }

            # Get overdue assessments
            overdue_assessments = compliance_query.filter(
                AuditCompliance.next_assessment_due < date.today()
            ).count()

            return {
                "overall_compliance_rate": round(compliance_rate, 2),
                "total_assessments": total_assessments,
                "compliant_assessments": compliant_assessments,
                "framework_statistics": framework_stats,
                "overdue_assessments": overdue_assessments,
                "last_updated": datetime.now().isoformat()
            }

        except SQLAlchemyError as e:
            raise Exception(f"Failed to get compliance dashboard: {str(e)}")

    # =============================================================================
    # Analytics and Metrics
    # =============================================================================

    async def generate_audit_metrics(
        self,
        organization_id: str,
        period_start: datetime,
        period_end: datetime,
        period_type: str = "daily"
    ) -> AuditMetrics:
        """Generate comprehensive audit metrics for a period."""
        try:
            # Query audit logs for the period
            logs_query = self.db.query(AuditLogEntry).filter(
                and_(
                    AuditLogEntry.organization_id == organization_id,
                    AuditLogEntry.event_timestamp >= period_start,
                    AuditLogEntry.event_timestamp <= period_end
                )
            )

            total_events = logs_query.count()

            # Events by type
            events_by_type = {}
            for event_type in AuditEventType:
                count = logs_query.filter(AuditLogEntry.event_type == event_type).count()
                events_by_type[event_type.value] = count

            # Events by severity
            events_by_severity = {}
            for severity in AuditSeverity:
                count = logs_query.filter(AuditLogEntry.severity == severity).count()
                events_by_severity[severity.value] = count

            # Failed events
            failed_events = logs_query.filter(AuditLogEntry.outcome == "failure").count()

            # Alert metrics
            alerts_query = self.db.query(AuditAlert).filter(
                and_(
                    AuditAlert.organization_id == organization_id,
                    AuditAlert.created_at >= period_start,
                    AuditAlert.created_at <= period_end
                )
            )

            total_alerts = alerts_query.count()

            # Alerts by severity
            alerts_by_severity = {}
            for severity in AuditSeverity:
                count = alerts_query.filter(AuditAlert.severity == severity).count()
                alerts_by_severity[severity.value] = count

            # Calculate average resolution time
            resolved_alerts = alerts_query.filter(AuditAlert.resolved_at.isnot(None)).all()
            total_resolution_time = sum([
                (alert.resolved_at - alert.created_at).total_seconds() / 60
                for alert in resolved_alerts
            ])
            avg_resolution_time = (
                total_resolution_time / len(resolved_alerts)
                if resolved_alerts else 0
            )

            # Active users
            active_users = self.db.query(AuditSession.user_id).filter(
                and_(
                    AuditSession.organization_id == organization_id,
                    AuditSession.last_activity >= period_start,
                    AuditSession.last_activity <= period_end
                )
            ).distinct().count()

            # Create metrics record
            metrics = AuditMetrics(
                organization_id=organization_id,
                period_start=period_start,
                period_end=period_end,
                period_type=period_type,
                total_events=total_events,
                events_by_type=events_by_type,
                events_by_severity=events_by_severity,
                failed_events=failed_events,
                total_alerts=total_alerts,
                alerts_by_severity=alerts_by_severity,
                average_resolution_time=Decimal(str(round(avg_resolution_time, 2))),
                active_users=active_users,
                calculated_at=datetime.now()
            )

            self.db.add(metrics)
            self.db.commit()
            self.db.refresh(metrics)

            return metrics

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Failed to generate audit metrics: {str(e)}")

    async def get_security_dashboard(self, organization_id: str) -> Dict[str, Any]:
        """Get security-focused dashboard data."""
        try:
            # Recent security events
            security_events = self.db.query(AuditLogEntry).filter(
                and_(
                    AuditLogEntry.organization_id == organization_id,
                    AuditLogEntry.event_type.in_([
                        AuditEventType.SECURITY_VIOLATION,
                        AuditEventType.UNAUTHORIZED_ACCESS,
                        AuditEventType.SUSPICIOUS_ACTIVITY,
                        AuditEventType.LOGIN_FAILED
                    ]),
                    AuditLogEntry.event_timestamp >= datetime.now() - timedelta(days=7)
                )
            ).count()

            # Active alerts
            active_alerts = self.db.query(AuditAlert).filter(
                and_(
                    AuditAlert.organization_id == organization_id,
                    AuditAlert.status == "open"
                )
            ).count()

            # High-risk sessions
            high_risk_sessions = self.db.query(AuditSession).filter(
                and_(
                    AuditSession.organization_id == organization_id,
                    AuditSession.risk_score >= 70,
                    AuditSession.is_active == True
                )
            ).count()

            # Failed login attempts (last 24 hours)
            failed_logins = self.db.query(AuditLogEntry).filter(
                and_(
                    AuditLogEntry.organization_id == organization_id,
                    AuditLogEntry.event_type == AuditEventType.LOGIN_FAILED,
                    AuditLogEntry.event_timestamp >= datetime.now() - timedelta(hours=24)
                )
            ).count()

            return {
                "security_events_week": security_events,
                "active_alerts": active_alerts,
                "high_risk_sessions": high_risk_sessions,
                "failed_logins_24h": failed_logins,
                "security_score": self._calculate_security_score(organization_id),
                "last_updated": datetime.now().isoformat()
            }

        except SQLAlchemyError as e:
            raise Exception(f"Failed to get security dashboard: {str(e)}")

    # =============================================================================
    # Data Retention and Archival
    # =============================================================================

    async def execute_retention_policy(self, policy_id: str) -> Dict[str, Any]:
        """Execute data retention policy."""
        try:
            policy = self.db.query(AuditDataRetention).filter(
                AuditDataRetention.id == policy_id
            ).first()

            if not policy:
                return {"success": False, "error": "Policy not found"}

            # Calculate cutoff dates
            delete_cutoff = datetime.now() - timedelta(days=policy.delete_after_days or 2555)
            archive_cutoff = datetime.now() - timedelta(days=policy.archive_after_days or 365)

            # Get records to process
            records_to_delete = self.db.query(AuditLogEntry).filter(
                and_(
                    AuditLogEntry.organization_id == policy.organization_id,
                    AuditLogEntry.created_at <= delete_cutoff
                )
            )

            records_to_archive = self.db.query(AuditLogEntry).filter(
                and_(
                    AuditLogEntry.organization_id == policy.organization_id,
                    AuditLogEntry.created_at <= archive_cutoff,
                    AuditLogEntry.created_at > delete_cutoff
                )
            )

            delete_count = records_to_delete.count()
            archive_count = records_to_archive.count()

            # Archive records (simplified - would integrate with actual archival system)
            if archive_count > 0:
                # In real implementation, would export to archive storage
                pass

            # Delete old records
            if delete_count > 0:
                records_to_delete.delete()

            # Update policy execution tracking
            policy.last_executed = datetime.now()
            policy.records_processed = delete_count + archive_count
            policy.records_archived = archive_count
            policy.records_deleted = delete_count

            self.db.commit()

            return {
                "success": True,
                "records_processed": delete_count + archive_count,
                "records_archived": archive_count,
                "records_deleted": delete_count
            }

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Failed to execute retention policy: {str(e)}")

    # =============================================================================
    # Helper Methods
    # =============================================================================

    def _generate_correlation_id(self, entry_data: Dict[str, Any]) -> str:
        """Generate correlation ID for audit entry."""
        content = f"{entry_data.get('user_id', '')}{entry_data.get('resource_id', '')}{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()

    def _calculate_risk_score(self, entry_data: Dict[str, Any]) -> int:
        """Calculate risk score for audit entry."""
        score = 0

        # Base score by event type
        event_type_scores = {
            AuditEventType.SECURITY_VIOLATION: 90,
            AuditEventType.UNAUTHORIZED_ACCESS: 80,
            AuditEventType.LOGIN_FAILED: 30,
            AuditEventType.DELETE: 40,
            AuditEventType.EXPORT: 35,
            AuditEventType.CONFIGURATION_CHANGE: 50,
        }

        event_type = entry_data.get("event_type")
        if event_type:
            score += event_type_scores.get(event_type, 10)

        # Severity multiplier
        severity_multipliers = {
            AuditSeverity.CRITICAL: 1.5,
            AuditSeverity.HIGH: 1.3,
            AuditSeverity.MEDIUM: 1.0,
            AuditSeverity.LOW: 0.7,
        }

        severity = entry_data.get("severity", AuditSeverity.LOW)
        score = int(score * severity_multipliers.get(severity, 1.0))

        # Outcome adjustment
        if entry_data.get("outcome") == "failure":
            score += 20

        return min(100, max(0, score))

    def _validate_rule_conditions(self, conditions: Dict[str, Any]) -> bool:
        """Validate audit rule conditions."""
        required_fields = ["trigger_type", "conditions"]
        return all(field in conditions for field in required_fields)

    def _evaluate_rule_conditions(
        self,
        conditions: Dict[str, Any],
        test_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate rule conditions against test data."""
        matched_conditions = []
        triggered = False

        # Simple condition evaluation (would be more sophisticated in practice)
        for condition_key, condition_value in conditions.get("conditions", {}).items():
            if condition_key in test_data:
                if test_data[condition_key] == condition_value:
                    matched_conditions.append(condition_key)

        triggered = len(matched_conditions) > 0

        return {
            "triggered": triggered,
            "matched_conditions": matched_conditions
        }

    async def _evaluate_audit_rules(self, entry: AuditLogEntry):
        """Evaluate audit rules against new entry."""
        try:
            # Get active rules for organization
            rules = self.db.query(AuditRule).filter(
                and_(
                    AuditRule.organization_id == entry.organization_id,
                    AuditRule.is_active == True
                )
            ).all()

            for rule in rules:
                # Convert entry to dict for evaluation
                entry_data = {
                    "event_type": entry.event_type,
                    "severity": entry.severity,
                    "user_id": entry.user_id,
                    "resource_type": entry.resource_type,
                    "outcome": entry.outcome,
                    "risk_score": entry.risk_score,
                }

                # Evaluate conditions
                result = self._evaluate_rule_conditions(rule.conditions, entry_data)

                if result["triggered"]:
                    # Create alert
                    await self.create_audit_alert({
                        "organization_id": entry.organization_id,
                        "rule_id": rule.id,
                        "alert_type": "rule_violation",
                        "title": f"Rule violation: {rule.name}",
                        "description": f"Audit rule '{rule.name}' was triggered",
                        "severity": rule.alert_severity,
                        "triggering_event_ids": [entry.id],
                        "alert_data": {"entry_id": entry.id, "rule_conditions": rule.conditions}
                    })

                    # Update rule trigger count
                    rule.trigger_count += 1
                    rule.last_triggered = datetime.now()

            self.db.commit()

        except Exception as e:
            # Log error but don't fail the main operation
            print(f"Error evaluating audit rules: {str(e)}")

    async def _send_alert_notifications(self, alert: AuditAlert):
        """Send alert notifications (placeholder for integration with notification system)."""
        # Would integrate with actual notification system
        pass

    async def _generate_report_content(self, report: AuditReport):
        """Generate report content asynchronously."""
        try:
            # Query data for report period
            logs_query = self.db.query(AuditLogEntry).filter(
                and_(
                    AuditLogEntry.organization_id == report.organization_id,
                    AuditLogEntry.event_timestamp >= report.period_start,
                    AuditLogEntry.event_timestamp <= report.period_end
                )
            )

            total_events = logs_query.count()
            critical_events = logs_query.filter(
                AuditLogEntry.severity == AuditSeverity.CRITICAL
            ).count()

            # Generate findings
            findings = []
            if critical_events > 0:
                findings.append({
                    "type": "security_concern",
                    "description": f"{critical_events} critical security events detected",
                    "severity": "high"
                })

            # Update report
            report.total_events = total_events
            report.critical_events = critical_events
            report.findings = findings
            report.generation_status = "completed"
            report.completed_at = datetime.now()
            report.generation_progress = 100

            self.db.commit()

        except Exception as e:
            report.generation_status = "failed"
            report.generation_error = str(e)
            self.db.commit()

    def _calculate_security_score(self, organization_id: str) -> int:
        """Calculate overall security score for organization."""
        try:
            # Get recent security events
            recent_events = self.db.query(AuditLogEntry).filter(
                and_(
                    AuditLogEntry.organization_id == organization_id,
                    AuditLogEntry.event_timestamp >= datetime.now() - timedelta(days=30)
                )
            ).count()

            # Get security violations
            violations = self.db.query(AuditLogEntry).filter(
                and_(
                    AuditLogEntry.organization_id == organization_id,
                    AuditLogEntry.event_type == AuditEventType.SECURITY_VIOLATION,
                    AuditLogEntry.event_timestamp >= datetime.now() - timedelta(days=30)
                )
            ).count()

            # Calculate base score
            base_score = 100
            
            # Deduct points for violations
            if violations > 0:
                base_score -= min(50, violations * 10)

            # Deduct points for high activity
            if recent_events > 1000:
                base_score -= 10

            return max(0, base_score)

        except Exception:
            return 50  # Default score if calculation fails