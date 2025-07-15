"""Organization model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

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
from sqlalchemy.orm import Session, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.department import Department  # noqa: F401
    from app.models.role import UserRole  # noqa: F401
    from app.models.user import User  # noqa: F401


class Organization(Base):
    """Organization model."""

    __tablename__ = "organizations"

    id: int = Column(Integer, primary_key=True, index=True)
    code: str = Column(String(50), unique=True, index=True, nullable=False)
    name: str = Column(String(200), nullable=False)
    name_kana: Optional[str] = Column(String(200))
    name_en: Optional[str] = Column(String(200))
    phone: Optional[str] = Column(String(20))
    fax: Optional[str] = Column(String(20))
    email: Optional[str] = Column(String(255))
    website: Optional[str] = Column(String(255))
    postal_code: Optional[str] = Column(String(10))
    prefecture: Optional[str] = Column(String(50))
    city: Optional[str] = Column(String(100))
    address_line1: Optional[str] = Column(String(255))
    address_line2: Optional[str] = Column(String(255))
    business_type: Optional[str] = Column(String(100))
    industry: Optional[str] = Column(String(100))
    capital: Optional[int] = Column(Integer)
    employee_count: Optional[int] = Column(Integer)
    fiscal_year_end: Optional[str] = Column(String(5))
    parent_id: Optional[int] = Column(Integer, ForeignKey("organizations.id"))
    is_active: bool = Column(Boolean, default=True)
    settings: Optional[str] = Column(Text)
    description: Optional[str] = Column(Text)
    logo_url: Optional[str] = Column(String(255))
    is_deleted: bool = Column(Boolean, default=False)
    deleted_at: Optional[datetime] = Column(DateTime(timezone=True))
    deleted_by: Optional[int] = Column(Integer, ForeignKey("users.id"))
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by: Optional[int] = Column(Integer, ForeignKey("users.id"))
    updated_by: Optional[int] = Column(Integer, ForeignKey("users.id"))

    # Relationships
    departments = relationship("Department", back_populates="organization")
    user_roles = relationship("UserRole", back_populates="organization")
    roles = relationship("Role", back_populates="organization")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    parent = relationship("Organization", remote_side=[id])
    children = relationship("Organization", back_populates="parent")

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        code: str,
        name: str,
        created_by: int,
        name_kana: Optional[str] = None,
        name_en: Optional[str] = None,
        postal_code: Optional[str] = None,
        prefecture: Optional[str] = None,
        city: Optional[str] = None,
        address_line1: Optional[str] = None,
        address_line2: Optional[str] = None,
        phone: Optional[str] = None,
        fax: Optional[str] = None,
        email: Optional[str] = None,
        website: Optional[str] = None,
        business_type: Optional[str] = None,
        industry: Optional[str] = None,
        capital: Optional[int] = None,
        employee_count: Optional[int] = None,
        fiscal_year_end: Optional[str] = None,
        parent_id: Optional[int] = None,
        is_active: bool = True,
    ) -> "Organization":
        """Create a new organization."""
        org = cls(
            code=code,
            name=name,
            name_kana=name_kana,
            name_en=name_en,
            postal_code=postal_code,
            prefecture=prefecture,
            city=city,
            address_line1=address_line1,
            address_line2=address_line2,
            phone=phone,
            fax=fax,
            email=email,
            website=website,
            business_type=business_type,
            industry=industry,
            capital=capital,
            employee_count=employee_count,
            fiscal_year_end=fiscal_year_end,
            parent_id=parent_id,
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
        return db.query(cls).filter(cls.is_active).all()

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

        if self.fiscal_year_end and len(self.fiscal_year_end) > 0:
            import re

            if not re.match(r"^\d{2}-\d{2}$", self.fiscal_year_end):
                raise ValueError("会計年度終了日はMM-DD形式で入力してください")

    def to_dict(self) -> Dict[str, Any]:
        """Convert organization to dictionary."""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "name_kana": self.name_kana,
            "postal_code": self.postal_code,
            "address": self.address_line1,
            "phone": self.phone,
            "email": self.email,
            "website": self.website,
            "fiscal_year_end": self.fiscal_year_end,
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
