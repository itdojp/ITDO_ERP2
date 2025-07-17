"""Password policy service for managing password security."""

import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.password_history import PasswordHistory
from app.models.password_policy import PasswordPolicy
from app.models.user import User


class PasswordPolicyService:
    """Service for managing password policies and validation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_policy_for_user(self, user_id: int) -> PasswordPolicy:
        """
        Get the applicable password policy for a user.

        Args:
            user_id: The user ID

        Returns:
            The applicable password policy (organization-specific or global)
        """
        # Get user with organization info
        user_query = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            raise ValueError(f"User {user_id} not found")

        # Try to get organization-specific policy first
        if user.organization_id:
            org_policy_query = select(PasswordPolicy).where(
                PasswordPolicy.organization_id == user.organization_id,
                PasswordPolicy.is_active
            )
            org_policy_result = await self.db.execute(org_policy_query)
            org_policy = org_policy_result.scalar_one_or_none()

            if org_policy:
                return org_policy

        # Fall back to global policy
        global_policy_query = select(PasswordPolicy).where(
            PasswordPolicy.organization_id.is_(None),
            PasswordPolicy.is_active
        )
        global_policy_result = await self.db.execute(global_policy_query)
        global_policy = global_policy_result.scalar_one_or_none()

        if global_policy:
            return global_policy

        # Create default policy if none exists
        return await self.create_default_policy()

    async def create_default_policy(self) -> PasswordPolicy:
        """Create and return the default password policy."""
        default_policy = PasswordPolicy(
            name="Default Security Policy",
            description="Default enterprise password policy",
            minimum_length=8,
            require_uppercase=True,
            require_lowercase=True,
            require_numbers=True,
            require_special_chars=True,
            password_history_count=3,
            password_expiry_days=90,
            password_warning_days=7,
            max_failed_attempts=5,
            lockout_duration_minutes=30,
            disallow_user_info=True,
            disallow_common_passwords=True,
            is_active=True
        )

        self.db.add(default_policy)
        await self.db.commit()
        await self.db.refresh(default_policy)

        return default_policy

    async def validate_password(
        self,
        password: str,
        user_id: int,
        check_history: bool = True
    ) -> Dict[str, any]:
        """
        Comprehensive password validation against policy and history.

        Args:
            password: The password to validate
            user_id: The user ID
            check_history: Whether to check against password history

        Returns:
            Dictionary with validation results
        """
        # Get user and policy
        user_query = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            return {
                "is_valid": False,
                "errors": ["User not found"],
                "strength_score": 0
            }

        policy = await self.get_policy_for_user(user_id)

        # Prepare user info for validation
        user_info = {
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone or ""
        }

        # Validate against policy
        errors = policy.validate_password_complexity(password, user_info)

        # Check against common passwords if policy requires it
        if policy.disallow_common_passwords:
            common_password_errors = await self._check_common_passwords(password)
            errors.extend(common_password_errors)

        # Check password history if requested
        if check_history:
            history_errors = await self._check_password_history(
                password, user_id, policy.password_history_count
            )
            errors.extend(history_errors)

        # Calculate strength score
        strength_score = policy.get_password_strength_score(password)

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "strength_score": strength_score,
            "policy_name": policy.name
        }

    async def _check_common_passwords(self, password: str) -> List[str]:
        """Check password against common/weak password list."""
        # Common weak passwords (in production, this should be a comprehensive database)
        common_passwords = {
            "password", "123456", "123456789", "qwerty", "abc123",
            "password123", "admin", "root", "user", "guest",
            "welcome", "login", "letmein", "monkey", "dragon"
        }

        if password.lower() in common_passwords:
            return ["Password is too common and easily guessable"]

        # Check for simple patterns
        if re.match(r'^(.)\1+$', password):  # All same character
            return ["Password cannot be all the same character"]

        if re.match(r'^(012|123|234|345|456|567|678|789|890)', password):  # Sequential numbers
            return ["Password cannot contain sequential numbers"]

        if re.match(r'^(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):  # Sequential letters
            return ["Password cannot contain sequential letters"]

        return []

    async def _check_password_history(
        self,
        password: str,
        user_id: int,
        history_count: int
    ) -> List[str]:
        """Check password against user's password history."""
        if history_count <= 0:
            return []

        # Get recent password history
        history_query = (
            select(PasswordHistory)
            .where(PasswordHistory.user_id == user_id)
            .order_by(desc(PasswordHistory.created_at))
            .limit(history_count)
        )
        history_result = await self.db.execute(history_query)
        history_records = history_result.scalars().all()

        # Check against each historical password
        for record in history_records:
            if verify_password(password, record.password_hash):
                return [f"Password cannot be the same as any of the last {history_count} passwords"]

        return []

    async def change_password(
        self,
        user_id: int,
        new_password: str,
        current_password: str = None,
        force_change: bool = False
    ) -> Dict[str, any]:
        """
        Change user password with full validation and history tracking.

        Args:
            user_id: The user ID
            new_password: The new password
            current_password: Current password for verification (if not force change)
            force_change: Whether to bypass current password verification

        Returns:
            Dictionary with operation results
        """
        # Get user
        user_query = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            return {
                "success": False,
                "errors": ["User not found"]
            }

        # Verify current password if not force change
        if not force_change and current_password:
            if not verify_password(current_password, user.hashed_password):
                return {
                    "success": False,
                    "errors": ["Current password is incorrect"]
                }

        # Validate new password
        validation_result = await self.validate_password(new_password, user_id)

        if not validation_result["is_valid"]:
            return {
                "success": False,
                "errors": validation_result["errors"]
            }

        # Save current password to history
        password_history = PasswordHistory(
            user_id=user_id,
            password_hash=user.hashed_password
        )
        self.db.add(password_history)

        # Update user password
        user.hashed_password = hash_password(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        user.password_must_change = False
        user.failed_login_attempts = 0  # Reset failed attempts
        user.locked_until = None  # Clear any lock

        # Clean up old password history
        policy = await self.get_policy_for_user(user_id)
        await self._cleanup_password_history(user_id, policy.password_history_count)

        await self.db.commit()

        return {
            "success": True,
            "message": "Password changed successfully",
            "strength_score": validation_result["strength_score"]
        }

    async def _cleanup_password_history(self, user_id: int, keep_count: int) -> None:
        """Clean up old password history entries beyond the keep count."""
        # Get all password history for user
        all_history_query = (
            select(PasswordHistory)
            .where(PasswordHistory.user_id == user_id)
            .order_by(desc(PasswordHistory.created_at))
        )
        all_history_result = await self.db.execute(all_history_query)
        all_history = all_history_result.scalars().all()

        # Delete entries beyond keep_count
        if len(all_history) > keep_count:
            entries_to_delete = all_history[keep_count:]
            for entry in entries_to_delete:
                await self.db.delete(entry)

    async def check_password_expiry(self, user_id: int) -> Dict[str, any]:
        """
        Check if user's password is expired or expiring soon.

        Args:
            user_id: The user ID

        Returns:
            Dictionary with expiry information
        """
        # Get user and policy
        user_query = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            return {
                "is_expired": False,
                "days_until_expiry": 0,
                "warning": False
            }

        policy = await self.get_policy_for_user(user_id)

        # Calculate expiry date
        password_age = datetime.now(timezone.utc) - user.password_changed_at
        days_since_change = password_age.days
        days_until_expiry = policy.password_expiry_days - days_since_change

        is_expired = days_until_expiry <= 0
        is_warning = days_until_expiry <= policy.password_warning_days and days_until_expiry > 0

        return {
            "is_expired": is_expired,
            "days_until_expiry": days_until_expiry,
            "warning": is_warning,
            "password_age_days": days_since_change,
            "policy_expiry_days": policy.password_expiry_days
        }

    async def handle_failed_login(self, user_id: int) -> Dict[str, any]:
        """
        Handle failed login attempt and check for account lockout.

        Args:
            user_id: The user ID

        Returns:
            Dictionary with lockout information
        """
        # Get user and policy
        user_query = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            return {"error": "User not found"}

        policy = await self.get_policy_for_user(user_id)

        # Increment failed attempts
        user.failed_login_attempts += 1

        # Check if lockout threshold reached
        if user.failed_login_attempts >= policy.max_failed_attempts:
            lockout_until = datetime.now(timezone.utc) + timedelta(
                minutes=policy.lockout_duration_minutes
            )
            user.locked_until = lockout_until

            await self.db.commit()

            return {
                "locked": True,
                "locked_until": lockout_until,
                "lockout_duration_minutes": policy.lockout_duration_minutes,
                "failed_attempts": user.failed_login_attempts
            }

        await self.db.commit()

        return {
            "locked": False,
            "failed_attempts": user.failed_login_attempts,
            "attempts_remaining": policy.max_failed_attempts - user.failed_login_attempts
        }

    async def unlock_account(self, user_id: int) -> bool:
        """
        Manually unlock a user account.

        Args:
            user_id: The user ID

        Returns:
            True if account was unlocked, False if user not found
        """
        user_query = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            return False

        user.failed_login_attempts = 0
        user.locked_until = None

        await self.db.commit()
        return True

    async def is_account_locked(self, user_id: int) -> bool:
        """
        Check if a user account is currently locked.

        Args:
            user_id: The user ID

        Returns:
            True if account is locked, False otherwise
        """
        user_query = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            return False

        # Check if locked_until is set and still in the future
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            return True

        # Clear expired lock
        if user.locked_until and user.locked_until <= datetime.now(timezone.utc):
            user.locked_until = None
            user.failed_login_attempts = 0
            await self.db.commit()

        return False
