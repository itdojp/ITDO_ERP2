"""User organization relationship model for multi-tenant support."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class UserOrganization(BaseModel):
    """User-Organization relationship for multi-tenant support.
    
    This model manages user membership across multiple organizations,
    including access permissions, temporary access, and transfer history.
    """

    __tablename__ = "user_organizations"

    # Primary relationship
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )

    # Access control
    access_type: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default="member",
        comment="Types: member, guest, temporary, transferred"
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Primary organization for user"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Temporal access control
    access_granted_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    access_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="For temporary access"
    )
    last_access_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    # Transfer and approval
    transfer_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    transfer_approved_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    transfer_approved_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    
    # Administrative fields
    invited_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    approved_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(
        Text, comment="Administrative notes"
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", 
        foreign_keys=[user_id],
        back_populates="organization_memberships"
    )
    organization: Mapped["Organization"] = relationship(
        "Organization",
        foreign_keys=[organization_id],
        back_populates="user_memberships"
    )
    
    inviter: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[invited_by],
        overlaps="user"
    )
    approver: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[approved_by],
        overlaps="user"
    )
    transfer_approver: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[transfer_approved_by],
        overlaps="user"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "user_id", 
            "organization_id", 
            name="uq_user_organization"
        ),
    )

    def __repr__(self) -> str:
        return f"<UserOrganization(user_id={self.user_id}, org_id={self.organization_id}, type={self.access_type})>"

    @property
    def is_expired(self) -> bool:
        """Check if temporary access has expired."""
        if self.access_expires_at is None:
            return False
        return datetime.utcnow() >= self.access_expires_at

    @property
    def is_temporary(self) -> bool:
        """Check if this is temporary access."""
        return self.access_type == "temporary"

    @property
    def is_transfer_pending(self) -> bool:
        """Check if transfer is pending approval."""
        return (
            self.transfer_requested_at is not None 
            and self.transfer_approved_at is None
        )


class OrganizationInvitation(BaseModel):
    """Invitation to join an organization."""

    __tablename__ = "organization_invitations"

    # Core fields
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    email: Mapped[str] = mapped_column(String, nullable=False, index=True)
    invited_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    
    # Invitation details
    access_type: Mapped[str] = mapped_column(
        String(20), default="member", nullable=False
    )
    message: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # Status tracking
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime)
    accepted_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id")
    )
    declined_at: Mapped[datetime | None] = mapped_column(DateTime)
    
    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="invitations"
    )
    inviter: Mapped["User"] = relationship(
        "User",
        foreign_keys=[invited_by]
    )
    accepter: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[accepted_by]
    )

    def __repr__(self) -> str:
        return f"<OrganizationInvitation(email={self.email}, org_id={self.organization_id})>"

    @property
    def is_expired(self) -> bool:
        """Check if invitation has expired."""
        return datetime.utcnow() >= self.expires_at

    @property
    def is_pending(self) -> bool:
        """Check if invitation is still pending."""
        return (
            self.accepted_at is None 
            and self.declined_at is None 
            and not self.is_expired
        )


class UserTransferRequest(BaseModel):
    """Request to transfer user between organizations."""

    __tablename__ = "user_transfer_requests"

    # Core fields
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    from_organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    to_organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    
    # Request details
    requested_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    reason: Mapped[str | None] = mapped_column(Text)
    transfer_type: Mapped[str] = mapped_column(
        String(20), 
        default="permanent",
        comment="permanent, temporary, guest"
    )
    
    # Approval workflow
    approved_by_source: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id")
    )
    approved_by_target: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)
    rejected_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id")
    )
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    
    # Execution
    executed_at: Mapped[datetime | None] = mapped_column(DateTime)
    executed_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id")
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id]
    )
    from_organization: Mapped["Organization"] = relationship(
        "Organization",
        foreign_keys=[from_organization_id]
    )
    to_organization: Mapped["Organization"] = relationship(
        "Organization",
        foreign_keys=[to_organization_id]
    )
    requester: Mapped["User"] = relationship(
        "User",
        foreign_keys=[requested_by]
    )

    def __repr__(self) -> str:
        return f"<UserTransferRequest(user_id={self.user_id}, from_org={self.from_organization_id}, to_org={self.to_organization_id})>"

    @property
    def is_pending(self) -> bool:
        """Check if transfer is pending approval."""
        return (
            self.approved_at is None 
            and self.rejected_at is None 
            and self.executed_at is None
        )

    @property
    def is_approved(self) -> bool:
        """Check if transfer is approved by both organizations."""
        return (
            self.approved_by_source is not None 
            and self.approved_by_target is not None 
            and self.approved_at is not None
        )

    @property
    def requires_source_approval(self) -> bool:
        """Check if source organization approval is still needed."""
        return self.approved_by_source is None and self.rejected_at is None

    @property
    def requires_target_approval(self) -> bool:
        """Check if target organization approval is still needed."""
        return self.approved_by_target is None and self.rejected_at is None