"""
Security Monitoring Service for Issue #46 - Security Audit Log and Monitoring Features.
セキュリティ監視サービス（Issue #46 - セキュリティ監査ログとモニタリング機能）
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog, UserActivityLog
from app.models.user import User


class SecurityMonitoringService:
    """Security monitoring and threat detection service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_suspicious_activity(
        self, 
        time_window_hours: int = 24,
        max_failed_logins: int = 5,
        max_privilege_escalations: int = 3
    ) -> Dict:
        """
        Detect suspicious activity patterns.
        不審なアクティビティパターンの検知
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=time_window_hours)
        
        # Initialize result structure
        suspicious_activities = {
            "detection_time": end_time.isoformat(),
            "time_window_hours": time_window_hours,
            "failed_logins": [],
            "privilege_escalations": [],
            "bulk_data_access": [],
            "after_hours_access": [],
            "suspicious_ip_patterns": [],
            "summary": {
                "total_threats": 0,
                "high_risk_users": [],
                "threat_score": 0
            }
        }

        # Detect multiple failed login attempts
        failed_logins = await self._detect_failed_logins(
            start_time, end_time, max_failed_logins
        )
        suspicious_activities["failed_logins"] = failed_logins

        # Detect privilege escalation attempts
        privilege_escalations = await self._detect_privilege_escalations(
            start_time, end_time, max_privilege_escalations
        )
        suspicious_activities["privilege_escalations"] = privilege_escalations

        # Detect bulk data access patterns
        bulk_access = await self._detect_bulk_data_access(start_time, end_time)
        suspicious_activities["bulk_data_access"] = bulk_access

        # Detect after-hours access
        after_hours = await self._detect_after_hours_access(start_time, end_time)
        suspicious_activities["after_hours_access"] = after_hours

        # Detect suspicious IP patterns
        ip_patterns = await self._detect_suspicious_ip_patterns(start_time, end_time)
        suspicious_activities["suspicious_ip_patterns"] = ip_patterns

        # Calculate summary
        await self._calculate_threat_summary(suspicious_activities)

        return suspicious_activities

    async def _detect_failed_logins(
        self, start_time: datetime, end_time: datetime, max_attempts: int
    ) -> List[Dict]:
        """Detect users with excessive failed login attempts."""
        query = (
            select(
                UserActivityLog.user_id,
                func.count(UserActivityLog.id).label("failed_count"),
                func.max(UserActivityLog.created_at).label("last_attempt"),
                func.array_agg(UserActivityLog.ip_address).label("ip_addresses")
            )
            .where(
                and_(
                    UserActivityLog.action == "login_failed",
                    UserActivityLog.created_at >= start_time,
                    UserActivityLog.created_at <= end_time
                )
            )
            .group_by(UserActivityLog.user_id)
            .having(func.count(UserActivityLog.id) >= max_attempts)
        )

        result = await self.db.execute(query)
        failed_logins = []

        for row in result:
            # Get user details
            user_query = select(User).where(User.id == row.user_id)
            user_result = await self.db.execute(user_query)
            user = user_result.scalar_one_or_none()

            if user:
                failed_logins.append({
                    "user_id": row.user_id,
                    "username": user.email,
                    "failed_count": row.failed_count,
                    "last_attempt": row.last_attempt.isoformat(),
                    "ip_addresses": list(set(row.ip_addresses)) if row.ip_addresses else [],
                    "risk_level": "high" if row.failed_count >= max_attempts * 2 else "medium",
                    "recommended_action": "lock_account" if row.failed_count >= max_attempts * 2 else "monitor"
                })

        return failed_logins

    async def _detect_privilege_escalations(
        self, start_time: datetime, end_time: datetime, max_escalations: int
    ) -> List[Dict]:
        """Detect users with suspicious privilege escalation patterns."""
        # Look for role/permission changes
        query = (
            select(
                AuditLog.user_id,
                func.count(AuditLog.id).label("escalation_count"),
                func.max(AuditLog.created_at).label("last_escalation"),
                func.array_agg(AuditLog.resource_type).label("resources_modified")
            )
            .where(
                and_(
                    AuditLog.action.in_(["create", "update"]),
                    AuditLog.resource_type.in_(["role", "permission", "user_role"]),
                    AuditLog.created_at >= start_time,
                    AuditLog.created_at <= end_time
                )
            )
            .group_by(AuditLog.user_id)
            .having(func.count(AuditLog.id) >= max_escalations)
        )

        result = await self.db.execute(query)
        escalations = []

        for row in result:
            # Get user details
            user_query = select(User).where(User.id == row.user_id)
            user_result = await self.db.execute(user_query)
            user = user_result.scalar_one_or_none()

            if user:
                escalations.append({
                    "user_id": row.user_id,
                    "username": user.email,
                    "escalation_count": row.escalation_count,
                    "last_escalation": row.last_escalation.isoformat(),
                    "resources_modified": list(set(row.resources_modified)),
                    "risk_level": "high",
                    "recommended_action": "review_permissions"
                })

        return escalations

    async def _detect_bulk_data_access(
        self, start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """Detect users accessing large amounts of data."""
        # Look for users with high number of read operations
        query = (
            select(
                AuditLog.user_id,
                func.count(AuditLog.id).label("access_count"),
                func.count(func.distinct(AuditLog.resource_type)).label("resource_types"),
                func.max(AuditLog.created_at).label("last_access")
            )
            .where(
                and_(
                    AuditLog.action == "read",
                    AuditLog.created_at >= start_time,
                    AuditLog.created_at <= end_time
                )
            )
            .group_by(AuditLog.user_id)
            .having(func.count(AuditLog.id) >= 100)  # Threshold for bulk access
        )

        result = await self.db.execute(query)
        bulk_access = []

        for row in result:
            # Get user details
            user_query = select(User).where(User.id == row.user_id)
            user_result = await self.db.execute(user_query)
            user = user_result.scalar_one_or_none()

            if user:
                risk_level = "high" if row.access_count >= 500 else "medium"
                bulk_access.append({
                    "user_id": row.user_id,
                    "username": user.email,
                    "access_count": row.access_count,
                    "resource_types": row.resource_types,
                    "last_access": row.last_access.isoformat(),
                    "risk_level": risk_level,
                    "recommended_action": "review_access_pattern"
                })

        return bulk_access

    async def _detect_after_hours_access(
        self, start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """Detect access during unusual hours (22:00-06:00)."""
        query = (
            select(
                UserActivityLog.user_id,
                func.count(UserActivityLog.id).label("after_hours_count"),
                func.max(UserActivityLog.created_at).label("last_access"),
                func.array_agg(UserActivityLog.ip_address).label("ip_addresses")
            )
            .where(
                and_(
                    UserActivityLog.action.in_(["login_success", "api_access"]),
                    UserActivityLog.created_at >= start_time,
                    UserActivityLog.created_at <= end_time,
                    func.extract("hour", UserActivityLog.created_at).in_([22, 23, 0, 1, 2, 3, 4, 5, 6])
                )
            )
            .group_by(UserActivityLog.user_id)
            .having(func.count(UserActivityLog.id) >= 3)  # Multiple after-hours access
        )

        result = await self.db.execute(query)
        after_hours = []

        for row in result:
            # Get user details
            user_query = select(User).where(User.id == row.user_id)
            user_result = await self.db.execute(user_query)
            user = user_result.scalar_one_or_none()

            if user:
                after_hours.append({
                    "user_id": row.user_id,
                    "username": user.email,
                    "after_hours_count": row.after_hours_count,
                    "last_access": row.last_access.isoformat(),
                    "ip_addresses": list(set(row.ip_addresses)) if row.ip_addresses else [],
                    "risk_level": "medium",
                    "recommended_action": "verify_legitimacy"
                })

        return after_hours

    async def _detect_suspicious_ip_patterns(
        self, start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """Detect suspicious IP address patterns."""
        # Look for users accessing from multiple IPs
        query = (
            select(
                UserActivityLog.user_id,
                func.count(func.distinct(UserActivityLog.ip_address)).label("unique_ips"),
                func.array_agg(func.distinct(UserActivityLog.ip_address)).label("ip_addresses"),
                func.max(UserActivityLog.created_at).label("last_access")
            )
            .where(
                and_(
                    UserActivityLog.created_at >= start_time,
                    UserActivityLog.created_at <= end_time,
                    UserActivityLog.ip_address.isnot(None)
                )
            )
            .group_by(UserActivityLog.user_id)
            .having(func.count(func.distinct(UserActivityLog.ip_address)) >= 5)
        )

        result = await self.db.execute(query)
        ip_patterns = []

        for row in result:
            # Get user details
            user_query = select(User).where(User.id == row.user_id)
            user_result = await self.db.execute(user_query)
            user = user_result.scalar_one_or_none()

            if user:
                risk_level = "high" if row.unique_ips >= 10 else "medium"
                ip_patterns.append({
                    "user_id": row.user_id,
                    "username": user.email,
                    "unique_ips": row.unique_ips,
                    "ip_addresses": row.ip_addresses,
                    "last_access": row.last_access.isoformat(),
                    "risk_level": risk_level,
                    "recommended_action": "verify_locations"
                })

        return ip_patterns

    async def _calculate_threat_summary(self, suspicious_activities: Dict) -> None:
        """Calculate overall threat summary and scores."""
        total_threats = 0
        high_risk_users = set()
        threat_score = 0

        # Count threats and identify high-risk users
        for category, threats in suspicious_activities.items():
            if isinstance(threats, list):
                total_threats += len(threats)
                for threat in threats:
                    if threat.get("risk_level") == "high":
                        high_risk_users.add(threat["user_id"])
                        threat_score += 10
                    elif threat.get("risk_level") == "medium":
                        threat_score += 5

        suspicious_activities["summary"] = {
            "total_threats": total_threats,
            "high_risk_users": list(high_risk_users),
            "threat_score": min(threat_score, 100),  # Cap at 100
            "risk_level": (
                "critical" if threat_score >= 50
                else "high" if threat_score >= 30
                else "medium" if threat_score >= 10
                else "low"
            )
        }

    async def generate_security_alert(
        self, threat_data: Dict, alert_type: str = "security_incident"
    ) -> Dict:
        """
        Generate security alert for immediate notification.
        セキュリティアラートの生成
        """
        alert = {
            "alert_id": f"SEC_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "alert_type": alert_type,
            "severity": threat_data["summary"]["risk_level"],
            "generated_at": datetime.utcnow().isoformat(),
            "threat_score": threat_data["summary"]["threat_score"],
            "affected_users": len(threat_data["summary"]["high_risk_users"]),
            "total_incidents": threat_data["summary"]["total_threats"],
            "recommended_actions": [],
            "details": threat_data
        }

        # Generate specific recommendations
        if threat_data["failed_logins"]:
            alert["recommended_actions"].append("Lock accounts with excessive failed logins")
        if threat_data["privilege_escalations"]:
            alert["recommended_actions"].append("Review recent permission changes")
        if threat_data["bulk_data_access"]:
            alert["recommended_actions"].append("Investigate bulk data access patterns")
        if threat_data["after_hours_access"]:
            alert["recommended_actions"].append("Verify legitimacy of after-hours access")
        if threat_data["suspicious_ip_patterns"]:
            alert["recommended_actions"].append("Verify user access from multiple locations")

        return alert

    async def get_security_metrics(
        self, days_back: int = 30
    ) -> Dict:
        """
        Get security metrics for the specified time period.
        セキュリティメトリクスの取得
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)

        # Total audit logs
        audit_count_query = select(func.count(AuditLog.id)).where(
            AuditLog.created_at >= start_time
        )
        audit_count_result = await self.db.execute(audit_count_query)
        total_audit_logs = audit_count_result.scalar()

        # Failed login attempts
        failed_login_query = select(func.count(UserActivityLog.id)).where(
            and_(
                UserActivityLog.action == "login_failed",
                UserActivityLog.created_at >= start_time
            )
        )
        failed_login_result = await self.db.execute(failed_login_query)
        failed_logins = failed_login_result.scalar()

        # Successful logins
        success_login_query = select(func.count(UserActivityLog.id)).where(
            and_(
                UserActivityLog.action == "login_success",
                UserActivityLog.created_at >= start_time
            )
        )
        success_login_result = await self.db.execute(success_login_query)
        successful_logins = success_login_result.scalar()

        # Unique active users
        active_users_query = select(func.count(func.distinct(UserActivityLog.user_id))).where(
            UserActivityLog.created_at >= start_time
        )
        active_users_result = await self.db.execute(active_users_query)
        active_users = active_users_result.scalar()

        # Permission changes
        permission_changes_query = select(func.count(AuditLog.id)).where(
            and_(
                AuditLog.resource_type.in_(["role", "permission", "user_role"]),
                AuditLog.created_at >= start_time
            )
        )
        permission_changes_result = await self.db.execute(permission_changes_query)
        permission_changes = permission_changes_result.scalar()

        return {
            "period": {
                "start_date": start_time.isoformat(),
                "end_date": end_time.isoformat(),
                "days": days_back
            },
            "metrics": {
                "total_audit_logs": total_audit_logs or 0,
                "failed_logins": failed_logins or 0,
                "successful_logins": successful_logins or 0,
                "active_users": active_users or 0,
                "permission_changes": permission_changes or 0,
                "login_failure_rate": (
                    failed_logins / (failed_logins + successful_logins) * 100
                    if (failed_logins + successful_logins) > 0 else 0
                )
            },
            "security_health": {
                "status": (
                    "good" if (failed_logins or 0) < (successful_logins or 1) * 0.1
                    else "warning" if (failed_logins or 0) < (successful_logins or 1) * 0.2
                    else "critical"
                ),
                "recommendations": [
                    "Monitor failed login patterns",
                    "Review permission changes regularly",
                    "Implement automated alerting"
                ]
            }
        }

    async def log_security_event(
        self,
        event_type: str,
        details: Dict,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log security-related events.
        セキュリティイベントのログ記録
        """
        if user_id:
            activity_log = UserActivityLog(
                user_id=user_id,
                action=f"security_{event_type}",
                details=details,
                ip_address=ip_address
            )
            self.db.add(activity_log)
            await self.db.commit()

    async def check_user_risk_level(self, user_id: int) -> Dict:
        """
        Check risk level for a specific user.
        特定ユーザーのリスクレベル確認
        """
        # Get recent activity (last 7 days)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=7)

        # Failed logins
        failed_query = select(func.count(UserActivityLog.id)).where(
            and_(
                UserActivityLog.user_id == user_id,
                UserActivityLog.action == "login_failed",
                UserActivityLog.created_at >= start_time
            )
        )
        failed_result = await self.db.execute(failed_query)
        failed_logins = failed_result.scalar() or 0

        # Permission changes
        perm_query = select(func.count(AuditLog.id)).where(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.resource_type.in_(["role", "permission"]),
                AuditLog.created_at >= start_time
            )
        )
        perm_result = await self.db.execute(perm_query)
        permission_changes = perm_result.scalar() or 0

        # Calculate risk score
        risk_score = 0
        risk_factors = []

        if failed_logins >= 5:
            risk_score += 30
            risk_factors.append("Multiple failed login attempts")

        if permission_changes >= 3:
            risk_score += 20
            risk_factors.append("Frequent permission changes")

        # Determine risk level
        if risk_score >= 40:
            risk_level = "high"
        elif risk_score >= 20:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "user_id": user_id,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "recent_activity": {
                "failed_logins": failed_logins,
                "permission_changes": permission_changes
            },
            "assessment_date": end_time.isoformat()
        }