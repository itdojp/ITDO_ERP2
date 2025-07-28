"""Multi-Factor Authentication service."""

import secrets
from datetime import datetime, timedelta
from typing import Optional

import pyotp
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError
from app.core.security import hash_password, verify_password
from app.models.mfa import MFABackupCode, MFAChallenge, MFADevice
from app.models.user import User


class MFAService:
    """Service for managing multi-factor authentication."""

    def __init__(self, db: Session):
        """Initialize MFA service."""
        self.db = db

    def create_challenge(
        self,
        user_id: int,
        challenge_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> MFAChallenge:
        """
        Create MFA challenge for user.
        
        Args:
            user_id: User ID
            challenge_type: Type of challenge (login, sensitive_action, verification)
            ip_address: Client IP
            user_agent: Client user agent
            
        Returns:
            Created MFA challenge
        """
        # Generate challenge token
        challenge_token = secrets.token_urlsafe(32)
        
        # Create challenge
        challenge = MFAChallenge(
            user_id=user_id,
            challenge_token=challenge_token,
            challenge_type=challenge_type,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now() + timedelta(minutes=5),  # 5 minute expiry
        )
        
        self.db.add(challenge)
        self.db.commit()
        
        return challenge

    def verify_challenge(self, challenge_token: str, code: str) -> User:
        """
        Verify MFA challenge with code.
        
        Args:
            challenge_token: Challenge token
            code: MFA code (TOTP or backup)
            
        Returns:
            Authenticated user
            
        Raises:
            BusinessLogicError: If verification fails
        """
        # Get challenge
        challenge = (
            self.db.query(MFAChallenge)
            .filter(MFAChallenge.challenge_token == challenge_token)
            .first()
        )
        
        if not challenge:
            raise BusinessLogicError("無効な認証チャレンジです")
        
        if not challenge.is_valid():
            raise BusinessLogicError("認証チャレンジの有効期限が切れています")
        
        # Increment attempts
        challenge.attempts += 1
        
        if challenge.attempts > challenge.max_attempts:
            self.db.commit()
            raise BusinessLogicError("認証試行回数の上限に達しました")
        
        # Get user
        user = self.db.query(User).filter(User.id == challenge.user_id).first()
        if not user:
            raise BusinessLogicError("ユーザーが見つかりません")
        
        # Try to verify with TOTP first
        if self._verify_totp(user, code):
            challenge.completed_at = datetime.now()
            self.db.commit()
            return user
        
        # Try backup codes
        if self._verify_backup_code(user, code):
            challenge.completed_at = datetime.now()
            self.db.commit()
            return user
        
        # Failed verification
        self.db.commit()
        raise BusinessLogicError("認証コードが正しくありません")

    def _verify_totp(self, user: User, code: str) -> bool:
        """
        Verify TOTP code.
        
        Args:
            user: User
            code: TOTP code
            
        Returns:
            True if valid
        """
        if not user.mfa_secret:
            return False
        
        # Create TOTP instance
        totp = pyotp.TOTP(user.mfa_secret)
        
        # Verify with time window (±90 seconds)
        return totp.verify(code, valid_window=3)

    def _verify_backup_code(self, user: User, code: str) -> bool:
        """
        Verify backup code.
        
        Args:
            user: User
            code: Backup code
            
        Returns:
            True if valid
        """
        # Get active MFA devices
        devices = (
            self.db.query(MFADevice)
            .filter(
                MFADevice.user_id == user.id,
                MFADevice.is_active == True,
                MFADevice.device_type == "totp",
            )
            .all()
        )
        
        for device in devices:
            # Check backup codes
            for backup_code in device.backup_codes:
                if not backup_code.is_used and verify_password(code, backup_code.code):
                    # Mark as used
                    backup_code.is_used = True
                    backup_code.used_at = datetime.now()
                    self.db.commit()
                    return True
        
        return False

    def setup_totp_device(
        self,
        user: User,
        device_name: str,
    ) -> tuple[MFADevice, str, list[str]]:
        """
        Setup TOTP device for user.
        
        Args:
            user: User
            device_name: Device name
            
        Returns:
            Tuple of (device, secret, backup_codes)
        """
        # Generate secret
        secret = pyotp.random_base32()
        
        # Create device
        device = MFADevice(
            user_id=user.id,
            device_name=device_name,
            device_type="totp",
            secret=secret,
            is_primary=not user.mfa_devices,  # First device is primary
        )
        
        self.db.add(device)
        self.db.flush()
        
        # Generate backup codes
        backup_codes = []
        for _ in range(10):
            code = secrets.token_hex(8)
            backup_codes.append(code)
            
            backup_code = MFABackupCode(
                device_id=device.id,
                code=hash_password(code),  # Store hashed
            )
            self.db.add(backup_code)
        
        # Update user
        user.mfa_secret = secret
        user.mfa_required = True
        if not user.mfa_enabled_at:
            user.mfa_enabled_at = datetime.now()
        
        self.db.commit()
        
        return device, secret, backup_codes

    def generate_qr_code(self, user: User, secret: str) -> str:
        """
        Generate QR code URL for TOTP setup.
        
        Args:
            user: User
            secret: TOTP secret
            
        Returns:
            QR code URL
        """
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="ITDO ERP",
        )
        
        # In production, generate actual QR code image
        # For now, return the URI
        return provisioning_uri

    def disable_mfa(self, user: User) -> None:
        """
        Disable MFA for user.
        
        Args:
            user: User
        """
        # Deactivate all devices
        for device in user.mfa_devices:
            device.is_active = False
        
        # Clear MFA fields
        user.mfa_required = False
        user.mfa_secret = None
        
        self.db.commit()

    def list_devices(self, user: User) -> list[MFADevice]:
        """
        List user's MFA devices.
        
        Args:
            user: User
            
        Returns:
            List of MFA devices
        """
        return [d for d in user.mfa_devices if d.is_active]
    
    def enable_mfa(
        self,
        user: User,
        device_name: str,
        device_type: str = "totp",
    ) -> list[str]:
        """
        Enable MFA for user.
        
        Args:
            user: User to enable MFA for
            device_name: Name of the device
            device_type: Type of MFA device
            
        Returns:
            List of backup codes
        """
        # Enable MFA
        user.mfa_required = True
        user.mfa_enabled_at = datetime.now()
        
        # Create MFA device
        device = MFADevice(
            user_id=user.id,
            device_name=device_name,
            device_type=device_type,
            is_primary=True,  # First device is primary
            is_active=True,
        )
        self.db.add(device)
        
        # Generate backup codes
        backup_codes = self.generate_backup_codes(user)
        
        self.db.commit()
        
        return backup_codes
    
    def generate_backup_codes(self, user: User, count: int = 10) -> list[str]:
        """Generate backup codes for user."""
        # Invalidate existing codes
        self.db.query(MFABackupCode).filter(
            MFABackupCode.user_id == user.id,
            MFABackupCode.used_at.is_(None),
        ).update({"used_at": datetime.now()})
        
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric code
            code = secrets.token_hex(4).upper()
            
            # Store hashed version
            backup_code = MFABackupCode(
                user_id=user.id,
                code_hash=hash_password(code),
            )
            self.db.add(backup_code)
            codes.append(code)
        
        self.db.commit()
        return codes
    
    def regenerate_backup_codes(self, user: User) -> list[str]:
        """Regenerate backup codes for user."""
        return self.generate_backup_codes(user)
    
    def verify_totp(self, user: User, code: str) -> bool:
        """Public method to verify TOTP code."""
        return self._verify_totp(user, code)
    
    def verify_backup_code(
        self,
        user: User,
        code: str,
        use_code: bool = True,
    ) -> bool:
        """
        Verify backup code.
        
        Args:
            user: User
            code: Backup code
            use_code: Whether to mark code as used
            
        Returns:
            True if valid
        """
        # Get active backup codes
        backup_codes = (
            self.db.query(MFABackupCode)
            .filter(
                MFABackupCode.user_id == user.id,
                MFABackupCode.used_at.is_(None),
            )
            .all()
        )
        
        for backup in backup_codes:
            if verify_password(code.upper(), backup.code_hash):
                if use_code:
                    backup.used_at = datetime.now()
                    self.db.commit()
                return True
        
        return False
    
    def count_active_backup_codes(self, user: User) -> int:
        """Count active backup codes for user."""
        return (
            self.db.query(MFABackupCode)
            .filter(
                MFABackupCode.user_id == user.id,
                MFABackupCode.used_at.is_(None),
            )
            .count()
        )
    
    def get_user_devices(self, user: User) -> list[MFADevice]:
        """Get all MFA devices for user."""
        return (
            self.db.query(MFADevice)
            .filter(MFADevice.user_id == user.id)
            .order_by(MFADevice.created_at.desc())
            .all()
        )
    
    def remove_device(self, user: User, device_id: int) -> None:
        """Remove MFA device."""
        device = (
            self.db.query(MFADevice)
            .filter(
                MFADevice.id == device_id,
                MFADevice.user_id == user.id,
            )
            .first()
        )
        
        if not device:
            raise BusinessLogicError("デバイスが見つかりません")
        
        # Check if it's the last active device
        active_count = (
            self.db.query(MFADevice)
            .filter(
                MFADevice.user_id == user.id,
                MFADevice.is_active == True,
                MFADevice.id != device_id,
            )
            .count()
        )
        
        if active_count == 0:
            raise BusinessLogicError("最後のアクティブデバイスは削除できません")
        
        device.is_active = False
        self.db.commit()
    
    def set_primary_device(self, user: User, device_id: int) -> None:
        """Set device as primary."""
        # Get device
        device = (
            self.db.query(MFADevice)
            .filter(
                MFADevice.id == device_id,
                MFADevice.user_id == user.id,
                MFADevice.is_active == True,
            )
            .first()
        )
        
        if not device:
            raise BusinessLogicError("アクティブなデバイスが見つかりません")
        
        # Remove primary from all devices
        self.db.query(MFADevice).filter(
            MFADevice.user_id == user.id
        ).update({"is_primary": False})
        
        # Set as primary
        device.is_primary = True
        self.db.commit()