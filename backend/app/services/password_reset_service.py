"""Password reset service."""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError
from app.core.security import hash_password, verify_password
from app.models.password_history import PasswordHistory
from app.models.password_reset import PasswordResetToken
from app.models.user import User


class PasswordResetService:
    """Service for password reset operations."""

    def __init__(self, db: Session) -> dict:
        """Initialize password reset service."""
        self.db = db

    def request_password_reset(
        self,
        email: str,
        ip_address: str,
        user_agent: str,
    ) -> Optional[str]:
        """
        Request password reset for email.

        Args:
            email: User email
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Reset token if successful, None if user not found
        """
        # Find user by email
        user = self.db.query(User).filter(User.email == email).first()

        if not user:
            # Don't reveal if user exists
            return None

        if not user.is_active:
            raise BusinessLogicError("アカウントが無効化されています")

        # Check for recent reset requests
        recent_cutoff = datetime.now(UTC) - timedelta(minutes=5)
        recent_request = (
            self.db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.created_at > recent_cutoff,
            )
            .first()
        )

        if recent_request:
            raise BusinessLogicError("パスワードリセットは5分に1回のみ要求できます")

        # Invalidate any existing tokens
        self.db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        ).update({"used_at": datetime.now(UTC)})

        # Generate new token
        token = secrets.token_urlsafe(32)
        verification_code = self._generate_verification_code()

        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            ip_address=ip_address,
            user_agent=user_agent,
            verification_code=verification_code,
        )

        self.db.add(reset_token)

        # Log activity
        user.log_activity(
            self.db,
            action="password_reset_requested",
            details={"method": "email"},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()

        # Send email (would be async in production)
        self._send_reset_email(user, token, verification_code)

        return token

    def verify_reset_token(
        self,
        token: str,
        verification_code: Optional[str] = None,
    ) -> PasswordResetToken:
        """
        Verify password reset token.

        Args:
            token: Reset token
            verification_code: Optional verification code

        Returns:
            Valid reset token

        Raises:
            BusinessLogicError: If token is invalid
        """
        reset_token = (
            self.db.query(PasswordResetToken)
            .filter(PasswordResetToken.token == token)
            .first()
        )

        if not reset_token:
            raise BusinessLogicError("無効なリセットトークンです")

        if not reset_token.can_use():
            if reset_token.is_expired():
                raise BusinessLogicError("リセットトークンの有効期限が切れています")
            elif reset_token.is_used():
                raise BusinessLogicError("このリセットトークンは既に使用されています")
            else:
                raise BusinessLogicError("リセット試行回数の上限に達しました")

        # Verify code if provided
        if reset_token.verification_code and verification_code:
            if reset_token.verification_code != verification_code:
                reset_token.increment_attempts()
                self.db.commit()
                raise BusinessLogicError("確認コードが正しくありません")

        return reset_token

    def reset_password(
        self,
        token: str,
        new_password: str,
        verification_code: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> User:
        """
        Reset password using token.

        Args:
            token: Reset token
            new_password: New password
            verification_code: Optional verification code
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Updated user

        Raises:
            BusinessLogicError: If reset fails
        """
        # Verify token
        reset_token = self.verify_reset_token(token, verification_code)

        # Get user
        user = reset_token.user

        # Validate new password
        self._validate_password(user, new_password)

        # Check password history
        if self._is_password_in_history(user, new_password):
            raise BusinessLogicError(
                "このパスワードは最近使用されています。別のパスワードを選択してください"
            )

        # Store old password in history
        self._add_to_password_history(user, user.hashed_password)

        # Update password
        user.hashed_password = hash_password(new_password)
        user.password_changed_at = datetime.now(UTC)
        user.password_must_change = False
        user.failed_login_attempts = 0
        user.locked_until = None

        # Mark token as used
        reset_token.used_at = datetime.now(UTC)

        # Log activity
        user.log_activity(
            self.db,
            action="password_reset_completed",
            details={"token_id": reset_token.id},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Invalidate all sessions for security
        from app.services.session_service import SessionService

        session_service = SessionService(self.db)
        session_service.revoke_all_user_sessions(
            user,
            reason="Password reset",
        )

        self.db.commit()

        # Send confirmation email
        self._send_reset_confirmation_email(user)

        return user

    def _generate_verification_code(self) -> str:
        """Generate 6-digit verification code."""
        return f"{secrets.randbelow(1000000):06d}"

    def _validate_password(self, user: User, password: str) -> None:
        """Validate password meets requirements."""
        if len(password) < 8:
            raise BusinessLogicError("パスワードは8文字以上である必要があります")

        # Check complexity (same as user model)
        import re

        checks = [
            bool(re.search(r"[A-Z]", password)),
            bool(re.search(r"[a-z]", password)),
            bool(re.search(r"\d", password)),
            bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)),
        ]

        if sum(checks) < 3:
            raise BusinessLogicError(
                "パスワードは大文字・小文字・数字・特殊文字のうち3種類以上を含む必要があります"
            )

        # Check not same as current
        if verify_password(password, user.hashed_password):
            raise BusinessLogicError(
                "新しいパスワードは現在のパスワードと異なる必要があります"
            )

    def _is_password_in_history(self, user: User, password: str) -> bool:
        """Check if password was recently used."""
        # Get last 3 passwords
        recent_passwords = (
            self.db.query(PasswordHistory)
            .filter(PasswordHistory.user_id == user.id)
            .order_by(PasswordHistory.created_at.desc())
            .limit(3)
            .all()
        )

        for history in recent_passwords:
            if verify_password(password, history.password_hash):
                return True

        return False

    def _add_to_password_history(self, user: User, password_hash: str) -> None:
        """Add password to history."""
        history = PasswordHistory(
            user_id=user.id,
            password_hash=password_hash,
        )
        self.db.add(history)

        # Keep only last 10 passwords
        old_passwords = (
            self.db.query(PasswordHistory)
            .filter(PasswordHistory.user_id == user.id)
            .order_by(PasswordHistory.created_at.desc())
            .offset(10)
            .all()
        )

        for old in old_passwords:
            self.db.delete(old)

    def _send_reset_email(
        self,
        user: User,
        token: str,
        verification_code: str,
    ) -> None:
        """Send password reset email."""
        # In production, this would use email service
        print(f"Password reset email would be sent to {user.email}")
        print(f"Reset link: /reset-password?token={token}")
        print(f"Verification code: {verification_code}")

    def _send_reset_confirmation_email(self, user: User) -> None:
        """Send password reset confirmation email."""
        # In production, this would use email service
        print(f"Password reset confirmation would be sent to {user.email}")

    def cleanup_expired_tokens(self) -> int:
        """Clean up expired reset tokens."""
        expired_tokens = (
            self.db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.expires_at < datetime.now(UTC),
                PasswordResetToken.used_at.is_(None),
            )
            .all()
        )

        for token in expired_tokens:
            self.db.delete(token)

        self.db.commit()
        return len(expired_tokens)
