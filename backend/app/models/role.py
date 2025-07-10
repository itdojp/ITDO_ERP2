"""Role and UserRole models."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Session, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.organization import Organization
    from app.models.user import User


class Role(Base):
    """Role model."""

    __tablename__ = "roles"

    id: int = Column(Integer, primary_key=True, index=True)
    code: str = Column(String(50), unique=True, index=True, nullable=False)
    name: str = Column(String(255), nullable=False)
    description: Optional[str] = Column(Text)
    permissions: List[str] = Column(JSON, default=list)  # List of permission strings
    is_system: bool = Column(Boolean, default=False)  # System roles cannot be deleted
    is_active: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by: Optional[int] = Column(Integer, ForeignKey("users.id"))
    updated_by: Optional[int] = Column(Integer, ForeignKey("users.id"))

    # Relationships
    user_roles = relationship("UserRole", back_populates="role")

    @classmethod
    def init_system_roles(cls, db: Session) -> None:
        """Initialize system roles."""
        system_roles = [
            {
                "code": "SYSTEM_ADMIN",
                "name": "システム管理者",
                "description": "システム全体の管理権限",
                "permissions": ["*"],
                "is_system": True,
            },
            {
                "code": "ORG_ADMIN",
                "name": "組織管理者",
                "description": "組織内の管理権限",
                "permissions": ["org:*", "dept:*", "user:*"],
                "is_system": True,
            },
            {
                "code": "DEPT_MANAGER",
                "name": "部門管理者",
                "description": "部門内の管理権限",
                "permissions": ["dept:*", "user:read", "user:write"],
                "is_system": True,
            },
            {
                "code": "USER",
                "name": "一般ユーザー",
                "description": "基本的な利用権限",
                "permissions": ["read:own", "write:own"],
                "is_system": True,
            },
        ]

        for role_data in system_roles:
            existing = db.query(cls).filter(cls.code == role_data["code"]).first()
            if not existing:
                role = cls(**role_data)
                db.add(role)

        db.commit()

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        code: str,
        name: str,
        created_by: int,
        description: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        is_system: bool = False,
        is_active: bool = True,
    ) -> "Role":
        """Create a new role."""
        role = cls(
            code=code,
            name=name,
            description=description,
            permissions=permissions or [],
            is_system=is_system,
            is_active=is_active,
            created_by=created_by,
        )

        db.add(role)
        db.flush()

        return role

    @classmethod
    def get_by_code(cls, db: Session, code: str) -> Optional["Role"]:
        """Get role by code."""
        return db.query(cls).filter(cls.code == code).first()

    def has_permission(self, permission: str) -> bool:
        """Check if role has a specific permission."""
        if not self.permissions:
            return False

        # Check for exact match
        if permission in self.permissions:
            return True

        # Check for wildcard permissions
        for perm in self.permissions:
            if perm == "*":
                return True

            # Check for pattern match (e.g., "read:*" matches "read:users")
            if perm.endswith("*"):
                prefix = perm[:-1]
                if permission.startswith(prefix):
                    return True

        return False

    def update(self, db: Session, updated_by: int, **kwargs: Any) -> None:
        """Update role attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key) and key not in ["id", "created_at", "created_by"]:
                setattr(self, key, value)

        self.updated_by = updated_by
        db.add(self)
        db.flush()

    def delete(self) -> None:
        """Delete role (prevents deletion of system roles)."""
        if self.is_system:
            raise ValueError("システムロールは削除できません")

        self.is_active = False

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, code={self.code}, name={self.name})>"


class UserRole(Base):
    """User role assignment model."""

    __tablename__ = "user_roles"

    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id: int = Column(Integer, ForeignKey("roles.id"), nullable=False)
    organization_id: int = Column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    department_id: Optional[int] = Column(
        Integer, ForeignKey("departments.id"), nullable=True
    )
    assigned_by: Optional[int] = Column(Integer, ForeignKey("users.id"))
    assigned_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    expires_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    role = relationship("Role", back_populates="user_roles")
    organization = relationship("Organization", back_populates="user_roles")
    department = relationship("Department", back_populates="user_roles")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "role_id",
            "organization_id",
            "department_id",
            name="uix_user_role_org_dept",
        ),
    )

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        user_id: int,
        role_id: int,
        organization_id: int,
        assigned_by: int,
        department_id: Optional[int] = None,
        expires_at: Optional[datetime] = None,
    ) -> "UserRole":
        """Create a new user role assignment."""
        user_role = cls(
            user_id=user_id,
            role_id=role_id,
            organization_id=organization_id,
            department_id=department_id,
            assigned_by=assigned_by,
            expires_at=expires_at,
        )

        db.add(user_role)
        db.flush()

        return user_role

    def is_expired(self) -> bool:
        """Check if role assignment is expired."""
        if not self.expires_at:
            return False

        return datetime.utcnow() > self.expires_at

    def __repr__(self) -> str:
        return (
            f"<UserRole(id={self.id}, user_id={self.user_id}, role_id={self.role_id})>"
        )
