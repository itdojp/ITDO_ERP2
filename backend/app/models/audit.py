"""Audit log models."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.organization import Organization  # noqa: F401
    from app.models.user import User  # noqa: F401

# Re-export for backwards compatibility
from app.models.user_activity_log import UserActivityLog

__all__ = ["AuditLog", "UserActivityLog"]


class AuditLog(BaseModel):
    """Audit log for tracking all system changes."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    organization_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("organizations.id"), index=True
    )
    changes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)
    checksum: Mapped[str | None] = mapped_column(
        String(64)
    )  # SHA-256 hash for integrity
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id], lazy="joined")
    organization = relationship(
        "Organization", foreign_keys=[organization_id], lazy="select"
    )

    def calculate_checksum(self) -> str:
        """Calculate checksum for audit log integrity."""
        data = {
            "user_id": self.user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "changes": self.changes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        # Create hash
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify audit log has not been tampered with."""
        if not self.checksum:
            return False

        calculated = self.calculate_checksum()
        return calculated == self.checksum

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, user={self.user_id}, "
            f"action={self.action}, resource={self.resource_type}:{self.resource_id})>"
        )
