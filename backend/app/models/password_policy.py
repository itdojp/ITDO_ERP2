"""Password policy configuration model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.organization import Organization


class PasswordPolicy(BaseModel):
    """Password policy configuration model."""

    __tablename__ = "password_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Organization-specific policies (None for global policy)
    organization_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=True, index=True,
        comment="Organization ID (NULL for global policy)"
    )

    # Password complexity requirements
    minimum_length: Mapped[int] = mapped_column(
        Integer, default=8, nullable=False,
        comment="Minimum password length"
    )
    require_uppercase: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
        comment="Require at least one uppercase letter"
    )
    require_lowercase: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
        comment="Require at least one lowercase letter"
    )
    require_numbers: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
        comment="Require at least one number"
    )
    require_special_chars: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
        comment="Require at least one special character"
    )
    special_chars_set: Mapped[str] = mapped_column(
        String(100), default="!@#$%^&*()_+-=[]{}|;:,.<>?",
        comment="Allowed special characters"
    )

    # Password history and expiration
    password_history_count: Mapped[int] = mapped_column(
        Integer, default=3, nullable=False,
        comment="Number of previous passwords to remember"
    )
    password_expiry_days: Mapped[int] = mapped_column(
        Integer, default=90, nullable=False,
        comment="Days until password expires"
    )
    password_warning_days: Mapped[int] = mapped_column(
        Integer, default=7, nullable=False,
        comment="Days before expiry to start warning user"
    )

    # Account lockout settings
    max_failed_attempts: Mapped[int] = mapped_column(
        Integer, default=5, nullable=False,
        comment="Maximum failed login attempts before lockout"
    )
    lockout_duration_minutes: Mapped[int] = mapped_column(
        Integer, default=30, nullable=False,
        comment="Account lockout duration in minutes"
    )

    # Common password restrictions
    disallow_user_info: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
        comment="Disallow passwords containing user information"
    )
    disallow_common_passwords: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
        comment="Disallow common/weak passwords"
    )

    # Policy metadata
    name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Policy name for identification"
    )
    description: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
        comment="Policy description"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
        comment="Whether this policy is active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    organization: Mapped["Organization | None"] = relationship(
        "Organization",
        foreign_keys=[organization_id],
        lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<PasswordPolicy(id={self.id}, name='{self.name}', org_id={self.organization_id})>"

    @property
    def is_global_policy(self) -> bool:
        """Check if this is a global policy (applies to all organizations)."""
        return self.organization_id is None

    def validate_password_complexity(self, password: str, user_info: dict = None) -> list[str]:
        """
        Validate password against this policy.
        
        Args:
            password: The password to validate
            user_info: Optional user information to check against
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Length check
        if len(password) < self.minimum_length:
            errors.append(f"Password must be at least {self.minimum_length} characters long")

        # Character type requirements
        if self.require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")

        if self.require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")

        if self.require_numbers and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")

        if self.require_special_chars:
            if not any(c in self.special_chars_set for c in password):
                errors.append(f"Password must contain at least one special character: {self.special_chars_set}")

        # User information check
        if self.disallow_user_info and user_info:
            password_lower = password.lower()
            for key, value in user_info.items():
                if value and isinstance(value, str) and len(value) >= 3:
                    if value.lower() in password_lower:
                        errors.append(f"Password cannot contain {key}")

        return errors

    def get_password_strength_score(self, password: str) -> int:
        """
        Calculate password strength score (0-100).
        
        Args:
            password: The password to evaluate
            
        Returns:
            Strength score from 0 (weakest) to 100 (strongest)
        """
        score = 0

        # Length scoring (up to 25 points)
        if len(password) >= self.minimum_length:
            score += min(25, (len(password) - self.minimum_length + 1) * 5)

        # Character variety scoring (up to 60 points)
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in self.special_chars_set for c in password)

        variety_score = sum([has_upper, has_lower, has_digit, has_special]) * 15
        score += variety_score

        # Additional complexity (up to 15 points)
        unique_chars = len(set(password))
        if unique_chars >= len(password) * 0.7:  # High character uniqueness
            score += 15
        elif unique_chars >= len(password) * 0.5:  # Medium character uniqueness
            score += 10
        elif unique_chars >= len(password) * 0.3:  # Low character uniqueness
            score += 5

        return min(100, score)
