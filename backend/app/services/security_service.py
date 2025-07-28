"""Security service for advanced session features."""

import ipaddress
import json
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session
from user_agents import parse

from app.models.session import SessionActivity, UserSession
from app.models.user import User


class SecurityService:
    """Service for security-related operations."""

    def __init__(self, db: Session) -> dict:
        """Initialize security service."""
        self.db = db

    def analyze_user_agent(self, user_agent: str) -> dict:
        """
        Analyze user agent string for device information.

        Args:
            user_agent: User agent string

        Returns:
            Device information dict
        """
        ua = parse(user_agent)

        return {
            "browser": ua.browser.family,
            "browser_version": ua.browser.version_string,
            "os": ua.os.family,
            "os_version": ua.os.version_string,
            "device": ua.device.family,
            "is_mobile": ua.is_mobile,
            "is_tablet": ua.is_tablet,
            "is_pc": ua.is_pc,
            "is_bot": ua.is_bot,
        }

    def is_ip_suspicious(self, ip_address: str, user: User) -> bool:
        """
        Check if IP address is suspicious for user.

        Args:
            ip_address: IP address to check
            user: User to check for

        Returns:
            True if suspicious
        """
        # Check if IP is in private range (trusted)
        try:
            ip = ipaddress.ip_address(ip_address)
            if ip.is_private:
                return False
        except ValueError:
            return True  # Invalid IP is suspicious

        # Check user's IP history
        recent_ips = (
            self.db.query(SessionActivity.ip_address)
            .filter(
                SessionActivity.user_id == user.id,
                SessionActivity.created_at > datetime.now() - timedelta(days=30),
            )
            .distinct()
            .all()
        )

        recent_ip_list = [ip[0] for ip in recent_ips]

        # If user has never logged in from this IP and has history
        if recent_ip_list and ip_address not in recent_ip_list:
            # Check geographic distance (would need GeoIP service)
            # For now, just flag as potentially suspicious
            return True

        return False

    def check_concurrent_sessions(self, user: User, ip_address: str) -> bool:
        """
        Check for suspicious concurrent sessions.

        Args:
            user: User to check
            ip_address: Current IP address

        Returns:
            True if suspicious pattern detected
        """
        # Get active sessions from different IPs
        active_sessions = (
            self.db.query(UserSession)
            .filter(
                UserSession.user_id == user.id,
                UserSession.is_active,
                UserSession.ip_address != ip_address,
            )
            .all()
        )

        if len(active_sessions) > 0:
            # Check if sessions are from very different locations
            # This would require GeoIP integration
            # For now, flag if more than 2 different IPs
            unique_ips = set(s.ip_address for s in active_sessions)
            if len(unique_ips) > 2:
                return True

        return False

    def detect_brute_force(self, identifier: str, window_minutes: int = 15) -> bool:
        """
        Detect brute force attempts.

        Args:
            identifier: IP address or email
            window_minutes: Time window to check

        Returns:
            True if brute force detected
        """
        # Check failed login attempts
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)

        # Count failed attempts from session activities
        failed_count = (
            self.db.query(func.count(SessionActivity.id))
            .filter(
                SessionActivity.activity_type == "failed_login",
                SessionActivity.created_at > cutoff_time,
                SessionActivity.ip_address == identifier,
            )
            .scalar()
            or 0
        )

        # Threshold: 5 attempts in 15 minutes
        return failed_count >= 5

    def calculate_risk_score(
        self,
        user: User,
        ip_address: str,
        user_agent: str,
        device_id: Optional[str] = None,
    ) -> int:
        """
        Calculate risk score for authentication attempt.

        Args:
            user: User attempting to authenticate
            ip_address: Client IP address
            user_agent: Client user agent
            device_id: Device identifier

        Returns:
            Risk score (0-100)
        """
        risk_score = 0

        # Check IP reputation
        if self.is_ip_suspicious(ip_address, user):
            risk_score += 30

        # Check for concurrent sessions
        if self.check_concurrent_sessions(user, ip_address):
            risk_score += 20

        # Check device
        device_info = self.analyze_user_agent(user_agent)
        if device_info["is_bot"]:
            risk_score += 50

        # Check if new device
        if device_id:
            existing_device = (
                self.db.query(UserSession)
                .filter(
                    UserSession.user_id == user.id,
                    UserSession.device_id == device_id,
                )
                .first()
            )
            if not existing_device:
                risk_score += 15
        else:
            # No device ID is slightly suspicious
            risk_score += 10

        # Check login time patterns
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:  # Outside normal hours
            risk_score += 10

        # Check account age
        account_age = datetime.now() - user.created_at
        if account_age < timedelta(days=7):
            risk_score += 15

        return min(risk_score, 100)

    def should_require_mfa(
        self,
        user: User,
        risk_score: int,
        ip_address: str,
    ) -> bool:
        """
        Determine if MFA should be required based on risk.

        Args:
            user: User
            risk_score: Calculated risk score
            ip_address: Client IP

        Returns:
            True if MFA should be required
        """
        # Always require if user has MFA enabled
        if user.mfa_required:
            return True

        # Require for high risk scores
        if risk_score >= 50:
            return True

        # Require for external IPs if configured
        try:
            ip = ipaddress.ip_address(ip_address)
            if not ip.is_private and risk_score >= 30:
                return True
        except ValueError:
            return True

        return False

    def log_security_event(
        self,
        user_id: int,
        event_type: str,
        ip_address: str,
        user_agent: str,
        details: Optional[dict] = None,
    ) -> None:
        """
        Log security event.

        Args:
            user_id: User ID
            event_type: Type of security event
            ip_address: Client IP
            user_agent: Client user agent
            details: Additional details
        """
        # Get or create a session for logging
        session = (
            self.db.query(UserSession)
            .filter(
                UserSession.user_id == user_id,
                UserSession.ip_address == ip_address,
                UserSession.is_active,
            )
            .first()
        )

        if session:
            activity = SessionActivity(
                session_id=session.id,
                user_id=user_id,
                activity_type=event_type,
                ip_address=ip_address,
                user_agent=user_agent,
                details=json.dumps(details) if details else None,
            )
            self.db.add(activity)
            self.db.commit()

    def verify_device_fingerprint(
        self,
        user: User,
        device_fingerprint: str,
    ) -> bool:
        """
        Verify device fingerprint.

        Args:
            user: User
            device_fingerprint: Device fingerprint to verify

        Returns:
            True if fingerprint is known
        """
        # Check if fingerprint exists in user's session history
        known_device = (
            self.db.query(UserSession)
            .filter(
                UserSession.user_id == user.id,
                UserSession.device_id == device_fingerprint,
            )
            .first()
        )

        return known_device is not None

    def get_session_analytics(self, user: User) -> dict:
        """
        Get session analytics for user.

        Args:
            user: User

        Returns:
            Analytics data
        """
        # Get session statistics
        total_sessions = (
            self.db.query(func.count(UserSession.id))
            .filter(UserSession.user_id == user.id)
            .scalar()
            or 0
        )

        active_sessions = (
            self.db.query(func.count(UserSession.id))
            .filter(
                UserSession.user_id == user.id,
                UserSession.is_active,
            )
            .scalar()
            or 0
        )

        # Get unique devices
        unique_devices = (
            self.db.query(func.count(func.distinct(UserSession.device_id)))
            .filter(
                UserSession.user_id == user.id,
                UserSession.device_id.isnot(None),
            )
            .scalar()
            or 0
        )

        # Get IP addresses
        unique_ips = (
            self.db.query(func.count(func.distinct(UserSession.ip_address)))
            .filter(UserSession.user_id == user.id)
            .scalar()
            or 0
        )

        # Get recent activities
        recent_activities = (
            self.db.query(
                SessionActivity.activity_type,
                func.count(SessionActivity.id).label("count"),
            )
            .filter(
                SessionActivity.user_id == user.id,
                SessionActivity.created_at > datetime.now() - timedelta(days=30),
            )
            .group_by(SessionActivity.activity_type)
            .all()
        )

        activity_summary = {activity[0]: activity[1] for activity in recent_activities}

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "unique_devices": unique_devices,
            "unique_ips": unique_ips,
            "recent_activities": activity_summary,
        }

    def enforce_geo_restrictions(
        self,
        user: User,
        ip_address: str,
        allowed_countries: Optional[list[str]] = None,
    ) -> bool:
        """
        Enforce geographic restrictions.

        Args:
            user: User
            ip_address: Client IP address
            allowed_countries: List of allowed country codes

        Returns:
            True if access allowed
        """
        # This would require GeoIP integration
        # For now, allow all private IPs
        try:
            ip = ipaddress.ip_address(ip_address)
            if ip.is_private:
                return True
        except ValueError:
            return False

        # In production, would check against GeoIP database
        # and compare with allowed_countries
        return True
