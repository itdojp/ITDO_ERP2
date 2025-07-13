"""Cross-tenant permissions models."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class CrossTenantPermissionRule(BaseModel):
    """Cross-tenant permission rule model.
    
    Defines rules for allowing or denying permissions across organizations.
    """
    
    __tablename__ = "cross_tenant_permission_rules"
    
    # Organizations involved
    source_organization_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
        comment="Source organization granting access"
    )
    target_organization_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
        comment="Target organization receiving access"
    )
    
    # Permission pattern and rule
    permission_pattern: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Permission pattern (e.g., 'read:*', 'user:view', specific permission)"
    )
    rule_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="allow",
        comment="Rule type: allow, deny"
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        comment="Rule priority (higher number = higher priority)"
    )
    
    # Status and metadata
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether the rule is active"
    )
    created_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="User who created the rule"
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the rule expires"
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Additional notes about the rule"
    )
    
    # Relationships
    source_organization: Mapped["Organization"] = relationship(
        "Organization",
        foreign_keys=[source_organization_id],
        lazy="joined"
    )
    target_organization: Mapped["Organization"] = relationship(
        "Organization",
        foreign_keys=[target_organization_id],
        lazy="joined"
    )
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by],
        lazy="joined"
    )
    
    def __repr__(self) -> str:
        return (
            f"<CrossTenantPermissionRule(id={self.id}, "
            f"source_org={self.source_organization_id}, "
            f"target_org={self.target_organization_id}, "
            f"pattern='{self.permission_pattern}')>"
        )
    
    @property
    def is_expired(self) -> bool:
        """Check if the rule has expired."""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    def matches_permission(self, permission: str) -> bool:
        """Check if this rule matches a specific permission.
        
        Supports wildcards:
        - 'read:*' matches 'read:users', 'read:projects', etc.
        - '*' matches any permission
        - 'user:*' matches 'user:view', 'user:edit', etc.
        """
        if self.permission_pattern == "*":
            return True
        
        if "*" in self.permission_pattern:
            # Handle wildcard patterns
            pattern_parts = self.permission_pattern.split("*")
            if len(pattern_parts) == 2:
                prefix, suffix = pattern_parts
                return permission.startswith(prefix) and permission.endswith(suffix)
        
        # Exact match
        return self.permission_pattern == permission


class CrossTenantAuditLog(BaseModel):
    """Audit log for cross-tenant permission activities."""
    
    __tablename__ = "cross_tenant_audit_logs"
    
    # User and organizations
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="User performing the action"
    )
    source_organization_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
        comment="Source organization"
    )
    target_organization_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
        comment="Target organization"
    )
    
    # Action details
    permission: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Permission that was checked/used"
    )
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Action: check, grant, deny, revoke"
    )
    result: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Result: allowed, denied"
    )
    rule_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("cross_tenant_permission_rules.id"),
        nullable=True,
        comment="Rule that was applied (if any)"
    )
    
    # Request metadata
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="IP address of the request"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="User agent of the request"
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="joined"
    )
    source_organization: Mapped["Organization"] = relationship(
        "Organization",
        foreign_keys=[source_organization_id],
        lazy="joined"
    )
    target_organization: Mapped["Organization"] = relationship(
        "Organization",
        foreign_keys=[target_organization_id],
        lazy="joined"
    )
    rule: Mapped[Optional["CrossTenantPermissionRule"]] = relationship(
        "CrossTenantPermissionRule",
        foreign_keys=[rule_id],
        lazy="joined"
    )
    
    def __repr__(self) -> str:
        return (
            f"<CrossTenantAuditLog(id={self.id}, "
            f"user={self.user_id}, "
            f"action='{self.action}', "
            f"result='{self.result}')>"
        )