"""Organization model."""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING, Dict, Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Organization(Base):
    """Organization model."""

    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_kana: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    fiscal_year_start: Mapped[int] = mapped_column(Integer, default=4)  # 会計年度開始月
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    departments = relationship("Department", back_populates="organization")
    user_roles = relationship("UserRole", back_populates="organization")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        code: str,
        name: str,
        created_by: int,
        name_kana: Optional[str] = None,
        postal_code: Optional[str] = None,
        address: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        website: Optional[str] = None,
        fiscal_year_start: int = 4,
        is_active: bool = True,
    ) -> "Organization":
        """Create a new organization."""
        org = cls(
            code=code,
            name=name,
            name_kana=name_kana,
            postal_code=postal_code,
            address=address,
            phone=phone,
            email=email,
            website=website,
            fiscal_year_start=fiscal_year_start,
            is_active=is_active,
            created_by=created_by,
        )

        db.add(org)
        db.flush()

        return org

    @classmethod
    def get_by_code(cls, db: Session, code: str) -> Optional["Organization"]:
        """Get organization by code."""
        return db.query(cls).filter(cls.code == code).first()

    @classmethod
    def get_active_organizations(cls, db: Session) -> List["Organization"]:
        """Get all active organizations."""
        return db.query(cls).filter(cls.is_active.is_(True)).all()

    def update(self, db: Session, updated_by: int, **kwargs: Any) -> None:
        """Update organization attributes."""
        from datetime import datetime

        for key, value in kwargs.items():
            if hasattr(self, key) and key not in ["id", "created_at", "created_by"]:
                setattr(self, key, value)

        self.updated_by = updated_by
        self.updated_at = datetime.utcnow()
        db.add(self)
        db.flush()

    def soft_delete(self, db: Session, deleted_by: int) -> None:
        """Soft delete organization."""
        self.is_active = False
        self.updated_by = deleted_by
        db.add(self)
        db.flush()

    def validate(self) -> None:
        """Validate organization data."""
        if not self.code or len(self.code.strip()) == 0:
            raise ValueError("組織コードは必須です")

        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("組織名は必須です")

        if self.fiscal_year_start < 1 or self.fiscal_year_start > 12:
            raise ValueError("会計年度開始月は1-12の範囲で入力してください")

    def to_dict(self) -> Dict[str, Any]:
        """Convert organization to dictionary."""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "name_kana": self.name_kana,
            "postal_code": self.postal_code,
            "address": self.address,
            "phone": self.phone,
            "email": self.email,
            "website": self.website,
            "fiscal_year_start": self.fiscal_year_start,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
        }

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, code={self.code}, name={self.name})>"
