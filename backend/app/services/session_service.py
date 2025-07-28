"""Session management service."""

import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError
from app.models.session import SessionActivity, SessionConfiguration, UserSession
from app.models.user import User


class SessionService:
    """Service for session management operations."""

    def __init__(self, db: Session) -> dict:
        """Initialize session service."""
        self.db = db

    def create_session(
        self,
        user: User,
        ip_address: str,
        user_agent: str,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
    ) -> UserSession:
        """
        Create a new user session.

        Args:
            user: User creating the session
            ip_address: Client IP address
            user_agent: Client user agent
            device_id: Optional device identifier
            device_name: Optional device name

        Returns:
            Created session

        Raises:
            BusinessLogicError: If session limit exceeded
        """
        # Get user's session configuration
        config = self.get_or_create_session_config(user)

        # Check concurrent session limit
        if not config.allow_multiple_sessions:
            # Revoke all existing sessions
            self.revoke_all_user_sessions(user, reason="Single session policy")
        else:
            # Check max concurrent sessions
            active_sessions = self.get_active_sessions(user)
            if len(active_sessions) >= config.max_concurrent_sessions:
                # Revoke oldest session
                oldest = min(active_sessions, key=lambda s: s.created_at)
                oldest.revoke(self.db, reason="Session limit exceeded")

        # Create new session
        session_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)

        session = UserSession(
            user_id=user.id,
            session_token=session_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            device_name=device_name,
            expires_at=datetime.now(UTC)
            + timedelta(hours=config.session_timeout_hours),
            refresh_expires_at=datetime.now(UTC)
            + timedelta(days=config.refresh_token_days),
        )

        self.db.add(session)
        self.db.commit()

        # Log activity
        self.log_activity(session, "login", ip_address, user_agent)

        # Check if new device
        if device_id and self.is_new_device(user, device_id):
            if config.notify_new_device_login:
                # TODO: Send notification
                pass

        return session

    def get_session_by_token(self, token: str) -> Optional[UserSession]:
        """Get session by session token."""
        return (
            self.db.query(UserSession)
            .filter(
                and_(
                    UserSession.session_token == token,
                    UserSession.is_active,
                )
            )
            .first()
        )

    def refresh_session(
        self,
        refresh_token: str,
        ip_address: str,
        user_agent: str,
    ) -> UserSession:
        """
        Refresh a session using refresh token.

        Args:
            refresh_token: Refresh token
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Refreshed session

        Raises:
            BusinessLogicError: If refresh token invalid or expired
        """
        # Find session by refresh token
        session = (
            self.db.query(UserSession)
            .filter(
                and_(
                    UserSession.refresh_token == refresh_token,
                    UserSession.is_active,
                )
            )
            .first()
        )

        if not session:
            raise BusinessLogicError("無効なリフレッシュトークン")

        if session.is_refresh_expired():
            session.revoke(self.db, reason="Refresh token expired")
            raise BusinessLogicError("リフレッシュトークンの有効期限が切れています")

        # Get user's session configuration
        config = (
            self.db.query(SessionConfiguration)
            .filter(SessionConfiguration.user_id == session.user_id)
            .first()
        )

        if not config:
            config = SessionConfiguration(user_id=session.user_id)

        # Generate new tokens
        session.session_token = secrets.token_urlsafe(32)
        session.refresh_token = secrets.token_urlsafe(32)
        session.expires_at = datetime.now(UTC) + timedelta(
            hours=config.session_timeout_hours
        )
        session.refresh_expires_at = datetime.now(UTC) + timedelta(
            days=config.refresh_token_days
        )
        session.last_activity_at = datetime.now(UTC)

        self.db.commit()

        # Log activity
        self.log_activity(session, "refresh", ip_address, user_agent)

        return session

    def validate_session(
        self,
        session: UserSession,
        update_activity: bool = True,
    ) -> bool:
        """
        Validate a session.

        Args:
            session: Session to validate
            update_activity: Whether to update last activity

        Returns:
            True if valid, False otherwise
        """
        if not session.is_active:
            return False

        if session.is_expired():
            session.revoke(self.db, reason="Session expired")
            return False

        if update_activity:
            session.update_activity(self.db)

        return True

    def revoke_session(
        self,
        session: UserSession,
        revoked_by: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> None:
        """Revoke a specific session."""
        session.revoke(self.db, revoked_by, reason)

        # Log activity
        self.log_activity(
            session,
            "logout",
            session.ip_address,
            session.user_agent,
            {"reason": reason},
        )

    def revoke_all_user_sessions(
        self,
        user: User,
        except_session: Optional[UserSession] = None,
        reason: Optional[str] = None,
    ) -> int:
        """
        Revoke all sessions for a user.

        Args:
            user: User whose sessions to revoke
            except_session: Optional session to exclude
            reason: Reason for revocation

        Returns:
            Number of sessions revoked
        """
        query = self.db.query(UserSession).filter(
            and_(
                UserSession.user_id == user.id,
                UserSession.is_active,
            )
        )

        if except_session:
            query = query.filter(UserSession.id != except_session.id)

        sessions = query.all()

        for session in sessions:
            session.revoke(self.db, user.id, reason)

        return len(sessions)

    def get_active_sessions(self, user: User) -> list[UserSession]:
        """Get all active sessions for a user."""
        return (
            self.db.query(UserSession)
            .filter(
                and_(
                    UserSession.user_id == user.id,
                    UserSession.is_active,
                )
            )
            .order_by(UserSession.created_at.desc())
            .all()
        )

    def get_session_count(self, user: User) -> int:
        """Get count of active sessions for a user."""
        return (
            self.db.query(func.count(UserSession.id))
            .filter(
                and_(
                    UserSession.user_id == user.id,
                    UserSession.is_active,
                )
            )
            .scalar()
            or 0
        )

    def get_or_create_session_config(self, user: User) -> SessionConfiguration:
        """Get or create session configuration for a user."""
        config = (
            self.db.query(SessionConfiguration)
            .filter(SessionConfiguration.user_id == user.id)
            .first()
        )

        if not config:
            # Create default configuration
            config = SessionConfiguration(
                user_id=user.id,
                max_concurrent_sessions=5 if user.is_superuser else 3,
            )
            self.db.add(config)
            self.db.commit()

        return config

    def update_session_config(
        self,
        user: User,
        session_timeout_hours: Optional[int] = None,
        allow_multiple_sessions: Optional[bool] = None,
        max_concurrent_sessions: Optional[int] = None,
        require_mfa_for_new_device: Optional[bool] = None,
        notify_new_device_login: Optional[bool] = None,
        notify_suspicious_activity: Optional[bool] = None,
    ) -> SessionConfiguration:
        """Update user's session configuration."""
        config = self.get_or_create_session_config(user)

        if session_timeout_hours is not None:
            if (
                session_timeout_hours < 1
                or session_timeout_hours > config.max_session_timeout_hours
            ):
                raise BusinessLogicError(
                    f"セッションタイムアウトは1〜{config.max_session_timeout_hours}時間の間で設定してください"
                )
            config.session_timeout_hours = session_timeout_hours

        if allow_multiple_sessions is not None:
            config.allow_multiple_sessions = allow_multiple_sessions

        if max_concurrent_sessions is not None:
            if max_concurrent_sessions < 1 or max_concurrent_sessions > 10:
                raise BusinessLogicError(
                    "同時セッション数は1〜10の間で設定してください"
                )
            config.max_concurrent_sessions = max_concurrent_sessions

        if require_mfa_for_new_device is not None:
            config.require_mfa_for_new_device = require_mfa_for_new_device

        if notify_new_device_login is not None:
            config.notify_new_device_login = notify_new_device_login

        if notify_suspicious_activity is not None:
            config.notify_suspicious_activity = notify_suspicious_activity

        config.updated_at = datetime.now(UTC)
        self.db.commit()

        return config

    def add_trusted_device(self, user: User, device_id: str) -> None:
        """Add a device to user's trusted devices."""
        config = self.get_or_create_session_config(user)

        trusted_devices = []
        if config.trusted_devices:
            trusted_devices = json.loads(config.trusted_devices)

        if device_id not in trusted_devices:
            trusted_devices.append(device_id)
            config.trusted_devices = json.dumps(trusted_devices)
            self.db.commit()

    def is_trusted_device(self, user: User, device_id: str) -> bool:
        """Check if a device is trusted."""
        config = self.get_or_create_session_config(user)

        if not config.trusted_devices:
            return False

        trusted_devices = json.loads(config.trusted_devices)
        return device_id in trusted_devices

    def is_new_device(self, user: User, device_id: str) -> bool:
        """Check if this is a new device for the user."""
        # Check if device has been used in any session
        existing = (
            self.db.query(UserSession)
            .filter(
                and_(
                    UserSession.user_id == user.id,
                    UserSession.device_id == device_id,
                )
            )
            .first()
        )

        return existing is None

    def log_activity(
        self,
        session: UserSession,
        activity_type: str,
        ip_address: str,
        user_agent: str,
        details: Optional[dict] = None,
    ) -> SessionActivity:
        """Log session activity."""
        activity = SessionActivity(
            session_id=session.id,
            user_id=session.user_id,
            activity_type=activity_type,
            ip_address=ip_address,
            user_agent=user_agent,
            details=json.dumps(details) if details else None,
        )

        self.db.add(activity)
        self.db.commit()

        return activity

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        expired_sessions = (
            self.db.query(UserSession)
            .filter(
                and_(
                    UserSession.is_active,
                    UserSession.expires_at < datetime.now(UTC),
                )
            )
            .all()
        )

        for session in expired_sessions:
            session.revoke(self.db, reason="Session expired")

        return len(expired_sessions)
