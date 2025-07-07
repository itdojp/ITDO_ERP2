"""Factory for Role models."""

from typing import Dict, Any, Type, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.role import Role, UserRole
from app.models.organization import Organization
from tests.factories import BaseFactory, fake
from tests.factories.organization import OrganizationFactory


class RoleFactory(BaseFactory[Role]):
    """Factory for creating Role test instances."""
    
    @property
    def model_class(self) -> Type[Role]:
        """Return the Role model class."""
        return Role
    
    @classmethod
    def _get_default_attributes(cls) -> Dict[str, Any]:
        """Get default attributes for creating Role instances."""
        return {
            "code": fake.unique.bothify(text="ROLE_###_####"),
            "name": fake.random_element(elements=(
                "管理者", "マネージャー", "一般ユーザー", "閲覧者", "オペレーター",
                "経理担当", "人事担当", "営業担当", "開発者", "システム管理者"
            )),
            "description": fake.text(max_nb_chars=200),
            "role_type": fake.random_element(elements=("system", "custom", "department", "project")),
            "is_active": True,
            "permissions": {
                "users": {"read": True, "create": False, "update": False, "delete": False},
                "organizations": {"read": True, "create": False, "update": False, "delete": False},
                "departments": {"read": True, "create": False, "update": False, "delete": False},
            }
        }
    
    @classmethod
    def _get_update_attributes(cls) -> Dict[str, Any]:
        """Get default attributes for updating Role instances."""
        return {
            "name": fake.word(),
            "description": fake.text(max_nb_chars=200),
            "is_active": fake.boolean(),
        }
    
    @classmethod
    def create_with_parent(cls, db_session: Session, parent_role: Role, **kwargs: Any) -> Role:
        """Create a role with a parent role."""
        kwargs['parent_id'] = parent_role.id
        return cls.create(db_session, **kwargs)
    
    @classmethod
    def create_role_hierarchy(cls, db_session: Session, depth: int = 3) -> Dict[str, Any]:
        """Create a hierarchy of roles."""
        # Create root role (Admin)
        admin_role: Role = cls.create(
            db_session,
            code="ADMIN",
            name="システム管理者",
            description="すべての権限を持つ管理者ロール",
            role_type="system",
            permissions={
                "users": {"read": True, "create": True, "update": True, "delete": True},
                "organizations": {"read": True, "create": True, "update": True, "delete": True},
                "departments": {"read": True, "create": True, "update": True, "delete": True},
                "roles": {"read": True, "create": True, "update": True, "delete": True},
                "system": {"admin": True, "config": True, "logs": True, "backup": True},
            }
        )
        
        # Create manager roles
        manager_role = cls.create_with_parent(
            db_session,
            admin_role,
            code="MANAGER",
            name="マネージャー",
            description="部門管理権限を持つロール",
            role_type="department",
            permissions={
                "users": {"read": True, "create": True, "update": True, "delete": False},
                "departments": {"read": True, "create": True, "update": True, "delete": False},
                "roles": {"read": True, "create": False, "update": False, "delete": False},
            }
        )
        
        # Create user roles
        user_role = cls.create_with_parent(
            db_session,
            manager_role,
            code="USER",
            name="一般ユーザー",
            description="基本的な操作権限を持つロール",
            role_type="custom",
            permissions={
                "users": {"read": True, "create": False, "update": False, "delete": False},
                "departments": {"read": True, "create": False, "update": False, "delete": False},
            }
        )
        
        # Create viewer role
        viewer_role = cls.create_with_parent(
            db_session,
            user_role,
            code="VIEWER",
            name="閲覧者",
            description="読み取り専用権限を持つロール",
            role_type="custom",
            permissions={
                "users": {"read": True},
                "organizations": {"read": True},
                "departments": {"read": True},
            }
        )
        
        return {
            'admin': admin_role,
            'manager': manager_role,
            'user': user_role,
            'viewer': viewer_role,
            'all': [admin_role, manager_role, user_role, viewer_role]
        }
    
    @classmethod
    def create_by_type(cls, db_session: Session, role_type: str, **kwargs: Any) -> Role:
        """Create a role of a specific type."""
        kwargs['role_type'] = role_type
        return cls.create(db_session, **kwargs)
    
    @classmethod
    def create_inactive(cls, db_session: Session, **kwargs: Any) -> Role:
        """Create an inactive role."""
        kwargs['is_active'] = False
        return cls.create(db_session, **kwargs)
    
    @classmethod
    def create_system_role(cls, db_session: Session, **kwargs: Any) -> Role:
        """Create a system role."""
        kwargs['role_type'] = 'system'
        kwargs['is_system'] = True
        return cls.create(db_session, **kwargs)