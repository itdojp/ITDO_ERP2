"""Authentication service."""

import secrets
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError
from app.core.security import (
    verify_password,
    verify_token,
)
from app.models.session import UserSession
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.services.session_service import SessionService


class AuthService:
    """Authentication service for managing user authentication and sessions."""

    def __init__(self, db: Session) -> dict:
        """Initialize authentication service."""
        self.db = db

    def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> User:
        """
        Authenticate user with email and password.

        Args:
            email: User email
            password: User password
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Authenticated user

        Raises:
            BusinessLogicError: If authentication fails
        """
        # Get user by email
        user = self.db.query(User).filter(User.email == email).first()

        if not user:
            # Record failed attempt by IP
            raise BusinessLogicError("メールアドレスまたはパスワードが正しくありません")

        # Check if account is locked
        if user.is_locked():
            raise BusinessLogicError(
                "アカウントがロックされています。30分後に再試行してください"
            )

        # Check if user is active
        if not user.is_active:
            raise BusinessLogicError("アカウントが無効化されています")

        # Verify password
        if not verify_password(password, user.hashed_password):
            # Record failed login attempt
            user.record_failed_login(self.db)
            self.db.commit()
            raise BusinessLogicError("メールアドレスまたはパスワードが正しくありません")

        # Check if password needs to be changed
        if user.password_must_change:
            raise BusinessLogicError("パスワードの変更が必要です")

        # Check if password is expired
        if user.is_password_expired():
            user.password_must_change = True
            self.db.commit()
            raise BusinessLogicError(
                "パスワードの有効期限が切れています。変更してください"
            )

        # Record successful login
        user.record_successful_login(self.db)

        # Log activity
        user.log_activity(
            self.db,
            action="login",
            details={"method": "password"},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()

        return user

    def is_mfa_required_for_ip(self, user: User, ip_address: Optional[str]) -> bool:
        """
        Check if MFA is required for the given IP address.

        Args:
            user: User to check
            ip_address: Client IP address

        Returns:
            True if MFA is required
        """
        if not ip_address:
            return True  # Unknown IP requires MFA

        # Check if IP is in trusted network (implementation needed)
        # For now, assume all external IPs require MFA
        return not self._is_internal_ip(ip_address)

    def _is_internal_ip(self, ip_address: str) -> bool:
        """Check if IP address is internal."""
        # Simple check for private IP ranges
        return (
            ip_address.startswith("10.")
            or ip_address.startswith("172.16.")
            or ip_address.startswith("192.168.")
            or ip_address == "127.0.0.1"
            or ip_address == "::1"
        )

    def create_user_session(
        self,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        remember_me: bool = False,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
    ) -> UserSession:
        """
        Create a new user session.

        Args:
            user: User to create session for
            ip_address: Client IP address
            user_agent: Client user agent
            remember_me: Whether to extend session duration
            device_id: Optional device identifier
            device_name: Optional device name

        Returns:
            Created user session
        """
        # Use SessionService to create session
        session_service = SessionService(self.db)

        # Create session with device info
        session = session_service.create_session(
            user=user,
            ip_address=ip_address or "unknown",
            user_agent=user_agent or "unknown",
            device_id=device_id,
            device_name=device_name,
        )

        # If remember_me, update session timeout
        if remember_me:
            config = session_service.get_or_create_session_config(user)
            session.extend_session(self.db, hours=config.max_session_timeout_hours)

        return session

    def create_tokens(
        self,
        user: User,
        session: UserSession,
    ) -> TokenResponse:
        """
        Create access and refresh tokens from session.

        Args:
            user: User to create tokens for
            session: User session

        Returns:
            Token response
        """
        # Use session token as access token
        access_token = session.session_token

        # Calculate expiry
        expires_in = int((session.expires_at - datetime.now()).total_seconds())

        return TokenResponse(
            access_token=access_token,
            refresh_token=session.refresh_token,
            token_type="bearer",
            expires_in=expires_in,
            requires_mfa=False,
        )

    def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New token response

        Raises:
            BusinessLogicError: If refresh fails
        """
        # Verify refresh token
        payload = verify_token(refresh_token)
        if payload.get("type") != "refresh":
            raise BusinessLogicError("無効なリフレッシュトークンです")

        # Get user and session
        user_id = payload.get("sub")
        session_id = payload.get("session_id")

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise BusinessLogicError("ユーザーが見つかりません")

        # Validate session
        session = self.validate_session(user, session_id)

        # Create new tokens
        return self.create_tokens(
            user=user,
            session_id=session.id,
            remember_me=True,  # Keep refresh token
        )

    def validate_session(self, user: User, session_id: int) -> UserSession:
        """
        Validate user session.

        Args:
            user: User
            session_id: Session ID

        Returns:
            Valid session

        Raises:
            BusinessLogicError: If session is invalid
        """
        session = (
            self.db.query(UserSession)
            .filter(
                UserSession.id == session_id,
                UserSession.user_id == user.id,
            )
            .first()
        )

        if not session or not session.is_valid():
            raise BusinessLogicError("無効なセッションです")

        # Update last activity
        session.last_activity = datetime.now()
        self.db.commit()

        return session

    def invalidate_all_sessions(self, user: User) -> None:
        """
        Invalidate all user sessions.

        Args:
            user: User whose sessions to invalidate
        """
        for session in user.sessions:
            if session.is_active:
                session.invalidate()

        # Log activity
        user.log_activity(
            self.db,
            action="logout_all",
            details={"sessions_invalidated": len(user.sessions)},
        )

        self.db.commit()

    def request_password_reset(self, email: str) -> None:
        """
        Request password reset for email.

        Args:
            email: User email
        """
        user = self.db.query(User).filter(User.email == email).first()

        if user:
            # Generate reset token
            secrets.token_urlsafe(32)

            # Store token (implementation needed)
            # Send email (implementation needed)

            # Log activity
            user.log_activity(
                self.db,
                action="password_reset_requested",
                details={"email": email},
            )

            self.db.commit()

    def reset_password(self, token: str, new_password: str) -> None:
        """
        Reset password with token.

        Args:
            token: Reset token
            new_password: New password

        Raises:
            BusinessLogicError: If reset fails
        """
        # Verify token and get user (implementation needed)
        # For now, raise error
        raise BusinessLogicError("パスワードリセット機能は実装中です")
