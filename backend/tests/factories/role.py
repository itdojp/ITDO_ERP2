"""Factory for Role and Permission models."""

from typing import Dict, Any, Type, Optional, List
from datetime import datetime

from app.models.role import Role, Permission, RolePermission
from app.models.organization import Organization
from tests.factories import BaseFactory, fake
from tests.factories.organization import OrganizationFactory


class PermissionFactory(BaseFactory):
    """Factory for creating Permission test instances."""
    
    @property
    def model_class(self) -> Type[Permission]:
        """Return the Permission model class."""
        return Permission
    
    @classmethod
    def _get_default_attributes(cls) -> Dict[str, Any]:
        """Get default attributes for creating Permission instances."""
        return {
            "code": fake.unique.bothify(text="perm.###.####"),
            "name": fake.random_element(elements=(
                "ユーザー作成", "ユーザー編集", "ユーザー削除", "ユーザー表示",
                "組織作成", "組織編集", "組織削除", "組織表示",
                "部門作成", "部門編集", "部門削除", "部門表示",
                "ロール作成", "ロール編集", "ロール削除", "ロール表示"
            )),
            "description": fake.text(max_nb_chars=200),
            "category": fake.random_element(elements=(
                "users", "organizations", "departments", "roles", "system", "reports"
            )),
            "is_system": fake.boolean(chance_of_getting_true=20)
        }
    
    @classmethod
    def _get_update_attributes(cls) -> Dict[str, Any]:
        """Get default attributes for updating Permission instances."""
        return {
            "name": fake.word(),
            "description": fake.text(max_nb_chars=200),
            "category": fake.random_element(elements=(
                "users", "organizations", "departments", "roles", "system", "reports"
            ))
        }
    
    @classmethod
    def create_by_category(cls, db_session, category: str, **kwargs) -> Permission:
        """Create a permission in a specific category."""
        kwargs['category'] = category
        return cls.create(db_session, **kwargs)
    
    @classmethod
    def create_system_permission(cls, db_session, **kwargs) -> Permission:
        """Create a system permission."""
        kwargs['is_system'] = True
        return cls.create(db_session, **kwargs)
    
    @classmethod
    def create_standard_permissions(cls, db_session) -> Dict[str, List[Permission]]:
        """Create a standard set of permissions for all categories."""
        permissions = {}
        
        categories = {
            "users": ["create", "read", "update", "delete", "search"],
            "organizations": ["create", "read", "update", "delete", "manage"],
            "departments": ["create", "read", "update", "delete", "reorder"],
            "roles": ["create", "read", "update", "delete", "assign", "unassign"],
            "system": ["admin", "config", "logs", "backup"],
            "reports": ["view", "export", "schedule"]
        }
        
        for category, actions in categories.items():
            permissions[category] = []
            for action in actions:
                perm = cls.create(
                    db_session,
                    code=f"{category}.{action}",
                    name=f"{category.title()} {action.title()}",
                    description=f"Allows {action} operations on {category}",
                    category=category,
                    is_system=(category == "system")
                )
                permissions[category].append(perm)
        
        return permissions


class RoleFactory(BaseFactory):
    """Factory for creating Role test instances."""
    
    @property
    def model_class(self) -> Type[Role]:
        """Return the Role model class."""
        return Role
    
    @classmethod
    def _get_default_attributes(cls) -> Dict[str, Any]:
        """Get default attributes for creating Role instances."""
        return {
            "name": fake.random_element(elements=(
                "管理者", "マネージャー", "一般ユーザー", "閲覧者", "オペレーター",
                "経理担当", "人事担当", "営業担当", "開発者", "システム管理者"
            )),
            "description": fake.text(max_nb_chars=200),
            "role_type": fake.random_element(elements=("system", "custom", "department", "project")),
            "is_active": True,
            "can_be_assigned": True
        }
    
    @classmethod
    def _get_update_attributes(cls) -> Dict[str, Any]:
        """Get default attributes for updating Role instances."""
        return {
            "name": fake.word(),
            "description": fake.text(max_nb_chars=200),
            "is_active": fake.boolean(),
            "can_be_assigned": fake.boolean()
        }
    
    @classmethod
    def create_with_organization(cls, db_session, organization: Organization, **kwargs) -> Role:
        """Create a role for a specific organization."""
        kwargs['organization_id'] = organization.id
        return cls.create(db_session, **kwargs)
    
    @classmethod
    def create_with_parent(cls, db_session, parent_role: Role, **kwargs) -> Role:
        """Create a role with a parent role."""
        kwargs['parent_id'] = parent_role.id
        kwargs['organization_id'] = parent_role.organization_id
        return cls.create(db_session, **kwargs)
    
    @classmethod
    def create_with_permissions(cls, db_session, permissions: List[Permission], **kwargs) -> Role:
        """Create a role with specific permissions."""
        role = cls.create(db_session, **kwargs)
        
        # Add permissions to role
        for permission in permissions:
            role_permission = RolePermission(
                role_id=role.id,
                permission_id=permission.id,
                granted_by=kwargs.get('created_by')
            )
            db_session.add(role_permission)
        
        db_session.commit()
        db_session.refresh(role)
        return role
    
    @classmethod
    def create_role_hierarchy(cls, db_session, organization: Organization, depth: int = 3):
        """Create a hierarchy of roles within an organization."""
        # Create root role (Admin)
        admin_role = cls.create_with_organization(
            db_session,
            organization,
            name="システム管理者",
            description="すべての権限を持つ管理者ロール",
            role_type="system"
        )
        
        # Create manager roles
        manager_role = cls.create_with_parent(
            db_session,
            admin_role,
            name="マネージャー",
            description="部門管理権限を持つロール",
            role_type="department"
        )
        
        # Create user roles
        user_role = cls.create_with_parent(
            db_session,
            manager_role,
            name="一般ユーザー",
            description="基本的な操作権限を持つロール",
            role_type="custom"
        )
        
        # Create viewer role
        viewer_role = cls.create_with_parent(
            db_session,
            user_role,
            name="閲覧者",
            description="読み取り専用権限を持つロール",
            role_type="custom"
        )
        
        return {
            'organization': organization,
            'admin': admin_role,
            'manager': manager_role,
            'user': user_role,
            'viewer': viewer_role,
            'all': [admin_role, manager_role, user_role, viewer_role]
        }
    
    @classmethod
    def create_by_type(cls, db_session, role_type: str, **kwargs) -> Role:
        """Create a role of a specific type."""
        kwargs['role_type'] = role_type
        return cls.create(db_session, **kwargs)
    
    @classmethod
    def create_inactive(cls, db_session, **kwargs) -> Role:
        """Create an inactive role."""
        kwargs['is_active'] = False
        return cls.create(db_session, **kwargs)
    
    @classmethod
    def create_system_role(cls, db_session, **kwargs) -> Role:
        """Create a system role."""
        kwargs['role_type'] = 'system'
        kwargs['can_be_assigned'] = True
        return cls.create(db_session, **kwargs)
    
    @classmethod
    def create_complete_role_system(cls, db_session):
        """Create a complete role system with permissions."""
        # Create organization
        organization = OrganizationFactory.create(db_session, name="ロールテスト会社")
        
        # Create standard permissions
        permissions = PermissionFactory.create_standard_permissions(db_session)
        
        # Create role hierarchy
        roles = cls.create_role_hierarchy(db_session, organization)
        
        # Assign permissions to roles
        # Admin gets all permissions
        all_permissions = []
        for perm_list in permissions.values():
            all_permissions.extend(perm_list)
        
        cls._assign_permissions_to_role(db_session, roles['admin'], all_permissions)
        
        # Manager gets most permissions except system
        manager_permissions = []
        for category, perm_list in permissions.items():
            if category != 'system':
                manager_permissions.extend(perm_list)
        
        cls._assign_permissions_to_role(db_session, roles['manager'], manager_permissions)
        
        # User gets basic permissions
        user_permissions = []
        for category in ['users', 'organizations', 'departments']:
            user_permissions.extend([p for p in permissions[category] if p.code.endswith('.read')])
        
        cls._assign_permissions_to_role(db_session, roles['user'], user_permissions)
        
        # Viewer gets only read permissions
        viewer_permissions = []
        for perm_list in permissions.values():
            viewer_permissions.extend([p for p in perm_list if p.code.endswith('.read')])
        
        cls._assign_permissions_to_role(db_session, roles['viewer'], viewer_permissions)
        
        return {
            'organization': organization,
            'permissions': permissions,
            'roles': roles
        }
    
    @classmethod
    def _assign_permissions_to_role(cls, db_session, role: Role, permissions: List[Permission]):
        """Helper method to assign permissions to a role."""
        for permission in permissions:
            role_permission = RolePermission(
                role_id=role.id,
                permission_id=permission.id
            )
            db_session.add(role_permission)
        
        db_session.commit()
    
    @classmethod
    def create_minimal(cls, db_session, organization_id: int, **kwargs) -> Role:
        """Create a role with minimal required fields."""
        minimal_attrs = {
            "name": fake.word(),
            "organization_id": organization_id,
            "is_active": True,
            "can_be_assigned": True
        }
        minimal_attrs.update(kwargs)
        return cls.create(db_session, **minimal_attrs)