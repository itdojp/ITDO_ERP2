"""
Advanced Threat Detection Algorithms for Issue #46 Enhancement.
高度な脅威検知アルゴリズム（Issue #46 拡張）
"""

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.user_activity_log import UserActivityLog


class AnomalyType(Enum):
    """Types of anomalies that can be detected."""
    BEHAVIORAL = "behavioral"
    TEMPORAL = "temporal"
    VOLUMETRIC = "volumetric"
    GEOGRAPHICAL = "geographical"
    PATTERN = "pattern"


@dataclass
class UserBehaviorProfile:
    """User behavior profile for anomaly detection."""
    user_id: int
    avg_actions_per_hour: float
    common_actions: List[str]
    typical_access_times: List[int]  # Hours of day
    usual_ip_ranges: List[str]
    frequent_resources: List[str]
    session_duration_avg: float
    login_frequency: float
    last_updated: datetime


@dataclass
class AnomalyDetection:
    """Anomaly detection result."""
    anomaly_id: str
    user_id: int
    anomaly_type: AnomalyType
    severity: float  # 0.0 to 1.0
    description: str
    evidence: Dict
    detected_at: datetime
    confidence: float  # 0.0 to 1.0
    recommended_actions: List[str]


class AdvancedThreatDetector:
    """Advanced threat detection using machine learning-inspired algorithms."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_profiles: Dict[int, UserBehaviorProfile] = {}
        self.baseline_updated: Optional[datetime] = None
        self.learning_period_days = 30
        self.anomaly_threshold = 0.7

        # IP reputation cache
        self.ip_reputation_cache: Dict[str, float] = {}

        # Known attack patterns
        self.attack_signatures = self._load_attack_signatures()

    def _load_attack_signatures(self) -> Dict[str, Dict]:
        """Load known attack patterns and signatures."""
        return {
            "sql_injection": {
                "patterns": [
                    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION)\b)",
                    r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
                    r"(\b(OR|AND)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
                    r"(/\*.*?\*/)",
                    r"(--.*$)",
                    r"(\bEXEC\s*\()",
                    r"(\bCHAR\s*\()",
                    r"(\bCAST\s*\()"
                ],
                "severity": 0.9,
                "description": "SQL injection attempt detected"
            },
            "xss_attempt": {
                "patterns": [
                    r"(<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>)",
                    r"(javascript:)",
                    r"(on\w+\s*=)",
                    r"(<iframe\b[^>]*>)",
                    r"(<object\b[^>]*>)",
                    r"(<embed\b[^>]*>)",
                    r"(<link\b[^>]*>)",
                    r"(<meta\b[^>]*>)"
                ],
                "severity": 0.8,
                "description": "Cross-site scripting attempt detected"
            },
            "path_traversal": {
                "patterns": [
                    r"(\.\./)",
                    r"(\.\.\\)",
                    r"(%2e%2e%2f)",
                    r"(%2e%2e%5c)",
                    r"(\.\.%2f)",
                    r"(\.\.%5c)"
                ],
                "severity": 0.7,
                "description": "Path traversal attempt detected"
            },
            "command_injection": {
                "patterns": [
                    r"(\b(eval|exec|system|shell_exec|passthru|proc_open|popen)\s*\()",
                    r"(\b(cat|ls|dir|type|copy|move|del|rm|mkdir|rmdir)\b)",
                    r"(\||;|&|`|\$\()",
                    r"(nc\s+-)",
                    r"(wget|curl)\s+",
                    r"(chmod|chown|su|sudo)\s+"
                ],
                "severity": 0.95,
                "description": "Command injection attempt detected"
            }
        }

    async def build_user_baselines(self) -> Dict[str, int]:
        """Build behavioral baselines for all users."""
        # Get historical data for the learning period
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=self.learning_period_days)

        # Query user activities
        activity_query = select(UserActivityLog).where(
            UserActivityLog.created_at >= start_time,
            UserActivityLog.created_at <= end_time
        )
        activity_result = await self.db.execute(activity_query)
        activities = activity_result.scalars().all()

        # Query audit logs
        audit_query = select(AuditLog).where(
            AuditLog.created_at >= start_time,
            AuditLog.created_at <= end_time
        )
        audit_result = await self.db.execute(audit_query)
        audits = audit_result.scalars().all()

        # Group by user
        user_activities = defaultdict(list)
        user_audits = defaultdict(list)

        for activity in activities:
            user_activities[activity.user_id].append(activity)

        for audit in audits:
            user_audits[audit.user_id].append(audit)

        # Build profiles for each user
        profiles_built = 0
        for user_id in set(user_activities.keys()) | set(user_audits.keys()):
            profile = await self._build_user_profile(
                user_id, user_activities[user_id], user_audits[user_id]
            )
            if profile:
                self.user_profiles[user_id] = profile
                profiles_built += 1

        self.baseline_updated = datetime.utcnow()

        return {
            "total_profiles": profiles_built,
            "learning_period_days": self.learning_period_days,
            "baseline_updated": self.baseline_updated.isoformat()
        }

    async def _build_user_profile(
        self,
        user_id: int,
        activities: List[UserActivityLog],
        audits: List[AuditLog]
    ) -> Optional[UserBehaviorProfile]:
        """Build behavioral profile for a single user."""
        if not activities and not audits:
            return None

        all_events = []

        # Process activities
        for activity in activities:
            all_events.append({
                "timestamp": activity.created_at,
                "action": activity.action,
                "ip_address": activity.ip_address,
                "user_agent": activity.user_agent,
                "type": "activity"
            })

        # Process audits
        for audit in audits:
            all_events.append({
                "timestamp": audit.created_at,
                "action": audit.action,
                "resource_type": audit.resource_type,
                "ip_address": audit.ip_address,
                "user_agent": audit.user_agent,
                "type": "audit"
            })

        if not all_events:
            return None

        # Calculate behavioral metrics
        all_events.sort(key=lambda x: x["timestamp"])

        # Actions per hour
        time_span = (all_events[-1]["timestamp"] - all_events[0]["timestamp"]).total_seconds() / 3600
        avg_actions_per_hour = len(all_events) / max(time_span, 1)

        # Common actions
        action_counts = Counter(event["action"] for event in all_events)
        common_actions = [action for action, count in action_counts.most_common(10)]

        # Typical access times
        access_hours = [event["timestamp"].hour for event in all_events]
        typical_access_times = list(set(access_hours))

        # Usual IP ranges
        ip_addresses = [event["ip_address"] for event in all_events if event["ip_address"]]
        usual_ip_ranges = list(set(ip_addresses))

        # Frequent resources
        resources = [event.get("resource_type", "") for event in all_events if event.get("resource_type")]
        frequent_resources = [res for res, count in Counter(resources).most_common(5)]

        # Session duration (approximate)
        session_duration_avg = self._calculate_avg_session_duration(all_events)

        # Login frequency
        login_events = [e for e in all_events if "login" in e["action"]]
        login_frequency = len(login_events) / max(time_span / 24, 1)  # Per day

        return UserBehaviorProfile(
            user_id=user_id,
            avg_actions_per_hour=avg_actions_per_hour,
            common_actions=common_actions,
            typical_access_times=typical_access_times,
            usual_ip_ranges=usual_ip_ranges,
            frequent_resources=frequent_resources,
            session_duration_avg=session_duration_avg,
            login_frequency=login_frequency,
            last_updated=datetime.utcnow()
        )

    def _calculate_avg_session_duration(self, events: List[Dict]) -> float:
        """Calculate average session duration in minutes."""
        if len(events) < 2:
            return 0.0

        # Simple heuristic: time between first and last activity
        events.sort(key=lambda x: x["timestamp"])
        duration = (events[-1]["timestamp"] - events[0]["timestamp"]).total_seconds() / 60
        return duration

    async def detect_behavioral_anomalies(self, user_id: int) -> List[AnomalyDetection]:
        """Detect behavioral anomalies for a user."""
        if user_id not in self.user_profiles:
            return []

        profile = self.user_profiles[user_id]
        anomalies = []

        # Get recent activity (last 24 hours)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)

        # Query recent activities
        recent_activities = await self._get_recent_user_activities(user_id, start_time, end_time)

        if not recent_activities:
            return anomalies

        # Check for volume anomalies
        volume_anomaly = await self._detect_volume_anomaly(user_id, recent_activities, profile)
        if volume_anomaly:
            anomalies.append(volume_anomaly)

        # Check for temporal anomalies
        temporal_anomaly = await self._detect_temporal_anomaly(user_id, recent_activities, profile)
        if temporal_anomaly:
            anomalies.append(temporal_anomaly)

        # Check for action pattern anomalies
        pattern_anomaly = await self._detect_action_pattern_anomaly(user_id, recent_activities, profile)
        if pattern_anomaly:
            anomalies.append(pattern_anomaly)

        # Check for geographical anomalies
        geo_anomaly = await self._detect_geographical_anomaly(user_id, recent_activities, profile)
        if geo_anomaly:
            anomalies.append(geo_anomaly)

        return anomalies

    async def _get_recent_user_activities(
        self, user_id: int, start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """Get recent user activities and audits."""
        activities = []

        # Get user activities
        activity_query = select(UserActivityLog).where(
            UserActivityLog.user_id == user_id,
            UserActivityLog.created_at >= start_time,
            UserActivityLog.created_at <= end_time
        )
        activity_result = await self.db.execute(activity_query)
        user_activities = activity_result.scalars().all()

        # Get audit logs
        audit_query = select(AuditLog).where(
            AuditLog.user_id == user_id,
            AuditLog.created_at >= start_time,
            AuditLog.created_at <= end_time
        )
        audit_result = await self.db.execute(audit_query)
        user_audits = audit_result.scalars().all()

        # Convert to common format
        for activity in user_activities:
            activities.append({
                "timestamp": activity.created_at,
                "action": activity.action,
                "ip_address": activity.ip_address,
                "user_agent": activity.user_agent,
                "type": "activity"
            })

        for audit in user_audits:
            activities.append({
                "timestamp": audit.created_at,
                "action": audit.action,
                "resource_type": audit.resource_type,
                "ip_address": audit.ip_address,
                "user_agent": audit.user_agent,
                "type": "audit"
            })

        return activities

    async def _detect_volume_anomaly(
        self, user_id: int, activities: List[Dict], profile: UserBehaviorProfile
    ) -> Optional[AnomalyDetection]:
        """Detect volume-based anomalies."""
        if not activities:
            return None

        # Calculate current activity rate
        time_span = 24  # hours
        current_actions_per_hour = len(activities) / time_span

        # Compare with baseline
        baseline = profile.avg_actions_per_hour
        if baseline == 0:
            return None

        # Calculate anomaly score
        ratio = current_actions_per_hour / baseline

        # Detect significant deviations
        if ratio > 3.0:  # 3x more activity than usual
            severity = min(1.0, ratio / 5.0)
            confidence = min(1.0, (ratio - 3.0) / 2.0)

            return AnomalyDetection(
                anomaly_id=f"volume_{user_id}_{datetime.utcnow().timestamp()}",
                user_id=user_id,
                anomaly_type=AnomalyType.VOLUMETRIC,
                severity=severity,
                description=f"Unusual activity volume: {current_actions_per_hour:.1f} actions/hour vs baseline {baseline:.1f}",
                evidence={
                    "current_rate": current_actions_per_hour,
                    "baseline_rate": baseline,
                    "ratio": ratio,
                    "total_activities": len(activities)
                },
                detected_at=datetime.utcnow(),
                confidence=confidence,
                recommended_actions=["monitor_user", "verify_legitimacy", "check_automation"]
            )

        return None

    async def _detect_temporal_anomaly(
        self, user_id: int, activities: List[Dict], profile: UserBehaviorProfile
    ) -> Optional[AnomalyDetection]:
        """Detect temporal anomalies (unusual access times)."""
        if not activities or not profile.typical_access_times:
            return None

        # Get access hours from recent activities
        recent_hours = [activity["timestamp"].hour for activity in activities]

        # Check for unusual hours
        unusual_hours = []
        for hour in set(recent_hours):
            if hour not in profile.typical_access_times:
                unusual_hours.append(hour)

        if not unusual_hours:
            return None

        # Calculate severity based on how many unusual hours
        severity = min(1.0, len(unusual_hours) / 8.0)  # Max severity if 8+ unusual hours
        confidence = min(1.0, len(unusual_hours) / 4.0)

        if severity > 0.3:  # Only report if significant
            return AnomalyDetection(
                anomaly_id=f"temporal_{user_id}_{datetime.utcnow().timestamp()}",
                user_id=user_id,
                anomaly_type=AnomalyType.TEMPORAL,
                severity=severity,
                description=f"Access during unusual hours: {unusual_hours}",
                evidence={
                    "unusual_hours": unusual_hours,
                    "typical_hours": profile.typical_access_times,
                    "recent_hours": recent_hours
                },
                detected_at=datetime.utcnow(),
                confidence=confidence,
                recommended_actions=["verify_user_identity", "check_location", "monitor_session"]
            )

        return None

    async def _detect_action_pattern_anomaly(
        self, user_id: int, activities: List[Dict], profile: UserBehaviorProfile
    ) -> Optional[AnomalyDetection]:
        """Detect unusual action patterns."""
        if not activities or not profile.common_actions:
            return None

        # Get action counts
        action_counts = Counter(activity["action"] for activity in activities)

        # Check for unusual actions
        unusual_actions = []
        for action, count in action_counts.items():
            if action not in profile.common_actions:
                unusual_actions.append({"action": action, "count": count})

        if not unusual_actions:
            return None

        # Calculate severity
        total_unusual = sum(item["count"] for item in unusual_actions)
        severity = min(1.0, total_unusual / len(activities))
        confidence = min(1.0, len(unusual_actions) / 5.0)

        if severity > 0.2:
            return AnomalyDetection(
                anomaly_id=f"pattern_{user_id}_{datetime.utcnow().timestamp()}",
                user_id=user_id,
                anomaly_type=AnomalyType.PATTERN,
                severity=severity,
                description=f"Unusual action patterns detected: {len(unusual_actions)} new actions",
                evidence={
                    "unusual_actions": unusual_actions,
                    "common_actions": profile.common_actions,
                    "total_unusual": total_unusual
                },
                detected_at=datetime.utcnow(),
                confidence=confidence,
                recommended_actions=["review_actions", "verify_authorization", "monitor_closely"]
            )

        return None

    async def _detect_geographical_anomaly(
        self, user_id: int, activities: List[Dict], profile: UserBehaviorProfile
    ) -> Optional[AnomalyDetection]:
        """Detect geographical anomalies (unusual IP addresses)."""
        if not activities or not profile.usual_ip_ranges:
            return None

        # Get IP addresses from recent activities
        recent_ips = [activity["ip_address"] for activity in activities if activity["ip_address"]]

        if not recent_ips:
            return None

        # Check for unusual IPs
        unusual_ips = []
        for ip in set(recent_ips):
            if ip not in profile.usual_ip_ranges:
                unusual_ips.append(ip)

        if not unusual_ips:
            return None

        # Calculate severity
        severity = min(1.0, len(unusual_ips) / 3.0)  # Max severity if 3+ unusual IPs
        confidence = min(1.0, len(unusual_ips) / 2.0)

        if severity > 0.3:
            return AnomalyDetection(
                anomaly_id=f"geo_{user_id}_{datetime.utcnow().timestamp()}",
                user_id=user_id,
                anomaly_type=AnomalyType.GEOGRAPHICAL,
                severity=severity,
                description=f"Access from unusual IP addresses: {unusual_ips}",
                evidence={
                    "unusual_ips": unusual_ips,
                    "usual_ips": profile.usual_ip_ranges,
                    "recent_ips": recent_ips
                },
                detected_at=datetime.utcnow(),
                confidence=confidence,
                recommended_actions=["verify_location", "check_vpn", "require_2fa"]
            )

        return None

    async def detect_attack_signatures(self, activity_logs: List[Dict]) -> List[AnomalyDetection]:
        """Detect known attack signatures in activity logs."""
        anomalies = []

        for activity in activity_logs:
            # Check user agent and request details
            user_agent = activity.get("user_agent", "")
            details = activity.get("details", {})

            # Convert details to string for pattern matching
            details_str = json.dumps(details) if details else ""

            # Check against attack signatures
            for signature_name, signature_data in self.attack_signatures.items():
                matches = self._check_signature_patterns(
                    user_agent + " " + details_str,
                    signature_data["patterns"]
                )

                if matches:
                    anomaly = AnomalyDetection(
                        anomaly_id=f"signature_{signature_name}_{datetime.utcnow().timestamp()}",
                        user_id=activity.get("user_id", 0),
                        anomaly_type=AnomalyType.PATTERN,
                        severity=signature_data["severity"],
                        description=signature_data["description"],
                        evidence={
                            "signature_name": signature_name,
                            "matches": matches,
                            "user_agent": user_agent,
                            "details": details
                        },
                        detected_at=datetime.utcnow(),
                        confidence=0.9,  # High confidence for signature matches
                        recommended_actions=["block_immediately", "investigate_incident", "notify_security"]
                    )
                    anomalies.append(anomaly)

        return anomalies

    def _check_signature_patterns(self, text: str, patterns: List[str]) -> List[str]:
        """Check text against signature patterns."""
        import re
        matches = []

        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matches.append(pattern)

        return matches

    async def calculate_user_risk_score(self, user_id: int) -> Dict:
        """Calculate comprehensive risk score for a user."""
        # Get recent anomalies
        anomalies = await self.detect_behavioral_anomalies(user_id)

        # Base risk score
        base_score = 0.0

        # Factor in anomalies
        anomaly_score = 0.0
        for anomaly in anomalies:
            anomaly_score += anomaly.severity * anomaly.confidence

        # Factor in historical behavior
        historical_score = 0.0
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]

            # High-frequency access increases risk
            if profile.avg_actions_per_hour > 50:
                historical_score += 0.2

            # Unusual access patterns
            if len(profile.typical_access_times) > 20:  # Very varied access times
                historical_score += 0.1

            # Many different IP addresses
            if len(profile.usual_ip_ranges) > 10:
                historical_score += 0.1

        # Combine scores
        total_score = min(1.0, base_score + anomaly_score + historical_score)

        # Determine risk level
        if total_score >= 0.8:
            risk_level = "critical"
        elif total_score >= 0.6:
            risk_level = "high"
        elif total_score >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "user_id": user_id,
            "risk_score": total_score,
            "risk_level": risk_level,
            "contributing_factors": {
                "anomaly_score": anomaly_score,
                "historical_score": historical_score,
                "anomaly_count": len(anomalies)
            },
            "anomalies": [
                {
                    "type": anomaly.anomaly_type.value,
                    "severity": anomaly.severity,
                    "description": anomaly.description
                }
                for anomaly in anomalies
            ],
            "calculated_at": datetime.utcnow().isoformat()
        }

    async def get_threat_intelligence_summary(self) -> Dict:
        """Get comprehensive threat intelligence summary."""
        # Get all users with profiles
        user_ids = list(self.user_profiles.keys())

        # Calculate risk scores for all users
        high_risk_users = []
        total_anomalies = 0
        risk_distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}

        for user_id in user_ids:
            risk_data = await self.calculate_user_risk_score(user_id)
            risk_distribution[risk_data["risk_level"]] += 1
            total_anomalies += risk_data["contributing_factors"]["anomaly_count"]

            if risk_data["risk_level"] in ["high", "critical"]:
                high_risk_users.append({
                    "user_id": user_id,
                    "risk_score": risk_data["risk_score"],
                    "risk_level": risk_data["risk_level"]
                })

        # Sort high-risk users by score
        high_risk_users.sort(key=lambda x: x["risk_score"], reverse=True)

        return {
            "summary": {
                "total_monitored_users": len(user_ids),
                "high_risk_users": len(high_risk_users),
                "total_anomalies": total_anomalies,
                "last_analysis": datetime.utcnow().isoformat()
            },
            "risk_distribution": risk_distribution,
            "high_risk_users": high_risk_users[:10],  # Top 10
            "threat_types": {
                "behavioral": sum(1 for uid in user_ids if self._has_behavioral_threats(uid)),
                "temporal": sum(1 for uid in user_ids if self._has_temporal_threats(uid)),
                "geographical": sum(1 for uid in user_ids if self._has_geographical_threats(uid)),
                "pattern": sum(1 for uid in user_ids if self._has_pattern_threats(uid))
            },
            "recommendations": [
                "Review high-risk users immediately",
                "Update behavioral baselines weekly",
                "Implement additional monitoring for critical users",
                "Consider enhanced authentication for high-risk accounts"
            ]
        }

    def _has_behavioral_threats(self, user_id: int) -> bool:
        """Check if user has behavioral threats (placeholder)."""
        return user_id % 10 == 0  # Example logic

    def _has_temporal_threats(self, user_id: int) -> bool:
        """Check if user has temporal threats (placeholder)."""
        return user_id % 15 == 0  # Example logic

    def _has_geographical_threats(self, user_id: int) -> bool:
        """Check if user has geographical threats (placeholder)."""
        return user_id % 20 == 0  # Example logic

    def _has_pattern_threats(self, user_id: int) -> bool:
        """Check if user has pattern threats (placeholder)."""
        return user_id % 25 == 0  # Example logic

    async def update_user_profile(self, user_id: int) -> bool:
        """Update user profile with recent activity."""
        if user_id not in self.user_profiles:
            return False

        # Get recent activity for profile update
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=7)  # Last week

        activities = await self._get_recent_user_activities(user_id, start_time, end_time)

        if not activities:
            return False

        # Update profile incrementally
        profile = self.user_profiles[user_id]

        # Update action patterns
        new_actions = [a["action"] for a in activities]
        action_counts = Counter(new_actions)

        # Merge with existing common actions
        existing_actions = Counter(profile.common_actions)
        merged_actions = existing_actions + action_counts
        profile.common_actions = [action for action, count in merged_actions.most_common(10)]

        # Update access times
        new_hours = [a["timestamp"].hour for a in activities]
        profile.typical_access_times = list(set(profile.typical_access_times + new_hours))

        # Update IP ranges
        new_ips = [a["ip_address"] for a in activities if a["ip_address"]]
        profile.usual_ip_ranges = list(set(profile.usual_ip_ranges + new_ips))

        # Update timestamp
        profile.last_updated = datetime.utcnow()

        return True
