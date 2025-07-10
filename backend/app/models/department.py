"""Department model."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, List, Optional

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
    from app.models.organization import Organization
    from app.models.role import UserRole
    from app.models.user import User


class Department(Base):
    """Department model."""

    __tablename__ = "departments"

    id: int = Column(Integer, primary_key=True, index=True)
    organization_id: int = Column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    parent_id: Optional[int] = Column(
        Integer, ForeignKey("departments.id"), nullable=True
    )
    code: str = Column(String(50), nullable=False, index=True)
    name: str = Column(String(255), nullable=False)
    name_kana: Optional[str] = Column(String(255))
    description: Optional[str] = Column(Text)
    level: int = Column(Integer, default=1)  # 階層レベル
    path: Optional[str] = Column(String(255))  # 階層パス (例: "1/2/3")
    sort_order: int = Column(Integer, default=0)
    is_active: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by: Optional[int] = Column(Integer, ForeignKey("users.id"))
    updated_by: Optional[int] = Column(Integer, ForeignKey("users.id"))

    # Relationships - temporarily remove back_populates to avoid circular dependencies
    organization = relationship("Organization")
    parent = relationship("Department", remote_side=[id])
    children = relationship("Department")
    # user_roles = relationship("UserRole", back_populates="department")

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        organization_id: int,
        code: str,
        name: str,
        created_by: int,
        parent_id: Optional[int] = None,
        name_kana: Optional[str] = None,
        description: Optional[str] = None,
        sort_order: int = 0,
        is_active: bool = True,
    ) -> "Department":
        """Create a new department."""
        # Calculate level and path
        level = 1
        path = ""

        if parent_id:
            parent = db.query(cls).filter(cls.id == parent_id).first()
            if parent:
                level = parent.level + 1
                path = f"{parent.path}/{parent_id}" if parent.path else str(parent_id)

        dept = cls(
            organization_id=organization_id,
            parent_id=parent_id,
            code=code,
            name=name,
            name_kana=name_kana,
            description=description,
            level=level,
            path=path,
            sort_order=sort_order,
            is_active=is_active,
            created_by=created_by,
        )

        db.add(dept)
        db.flush()

        # Update path with own ID
        if not path:
            dept.path = str(dept.id)
        else:
            dept.path = f"{path}/{dept.id}"

        db.add(dept)
        db.flush()

        return dept

    @classmethod
    def get_by_organization(
        cls, db: Session, organization_id: int
    ) -> List["Department"]:
        """Get all departments for an organization."""
        return (
            db.query(cls)
            .filter(cls.organization_id == organization_id, cls.is_active)
            .order_by(cls.sort_order, cls.code)
            .all()
        )

    @classmethod
    def get_by_code(
        cls, db: Session, organization_id: int, code: str
    ) -> Optional["Department"]:
        """Get department by code within organization."""
        return (
            db.query(cls)
            .filter(cls.organization_id == organization_id, cls.code == code)
            .first()
        )

    def get_children(self, db: Session) -> List["Department"]:
        """Get direct children departments."""
        return (
            db.query(Department)
            .filter(Department.parent_id == self.id, Department.is_active)
            .order_by(Department.sort_order, Department.code)
            .all()
        )

    def get_descendants(self, db: Session) -> List["Department"]:
        """Get all descendant departments."""
        return (
            db.query(Department)
            .filter(Department.path.like(f"{self.path}/%"), Department.is_active)
            .order_by(Department.level, Department.sort_order, Department.code)
            .all()
        )

    def get_ancestors(self, db: Session) -> List["Department"]:
        """Get all ancestor departments."""
        if not self.path:
            return []

        ancestor_ids = [int(id_str) for id_str in self.path.split("/")[:-1]]
        if not ancestor_ids:
            return []

        return (
            db.query(Department)
            .filter(Department.id.in_(ancestor_ids))
            .order_by(Department.level)
            .all()
        )

    def update(self, db: Session, updated_by: int, **kwargs: Any) -> None:
        """Update department attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key) and key not in [
                "id",
                "created_at",
                "created_by",
                "path",
                "level",
            ]:
                setattr(self, key, value)

        self.updated_by = updated_by
        db.add(self)
        db.flush()

    def soft_delete(self, db: Session, deleted_by: int) -> None:
        """Soft delete department."""
        self.is_active = False
        self.updated_by = deleted_by
        db.add(self)
        db.flush()

    def __repr__(self) -> str:
        return f"<Department(id={self.id}, code={self.code}, name={self.name})>"
