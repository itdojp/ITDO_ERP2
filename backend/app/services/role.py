"""Role service implementation."""
from typing import List, Optional, Dict, Any, Tuple, Set
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.role import Role, UserRole
from app.models.user import User
from app.repositories.role import RoleRepository
from app.schemas.role import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleTree,
    UserRoleInfo,
    UserRoleResponse
)
from app.types import UserId, OrganizationId


class RoleService:
    """Service for role business logic."""
    
    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
        self.repository = RoleRepository(Role, db)
    
    def get_role(self, role_id: int) -> Optional[Role]:
        """Get role by ID."""
        return self.repository.get(role_id)
    
    def list_roles(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Role], int]:
        """List roles with pagination."""
        roles = self.repository.get_multi(skip=skip, limit=limit, filters=filters)
        total = self.repository.get_count(filters=filters)
        return roles, total
    
    def search_roles(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Role], int]:
        """Search roles by name or description."""
        search_filters = {
            "or": [
                {"name": {"ilike": f"%{query}%"}},
                {"description": {"ilike": f"%{query}%"}}
            ]
        }
        if filters:
            search_filters.update(filters)
        return self.list_roles(skip=skip, limit=limit, filters=search_filters)
    
    def get_role_user_count(self, role_id: int) -> int:
        """Get count of users with this role."""
        return self.db.query(UserRole).filter(
            UserRole.role_id == role_id,
            UserRole.is_active == True
        ).count()
    
    def create_role(
        self,
        role_data: RoleCreate,
        created_by: Optional[UserId] = None
    ) -> Role:
        """Create a new role."""
        # Validate unique name
        existing = self.db.query(Role).filter(
            Role.name == role_data.name,
            Role.is_deleted == False
        ).first()
        
        if existing:
            raise ValueError(f"Role name '{role_data.name}' already exists")
        
        # Add audit fields
        data = role_data.model_dump()
        if created_by:
            data["created_by"] = created_by
            data["updated_by"] = created_by
        
        # Create role
        return self.repository.create(RoleCreate(**data))
    
    def update_role(
        self,
        role_id: int,
        role_data: RoleUpdate,
        updated_by: Optional[UserId] = None
    ) -> Optional[Role]:
        """Update role details."""
        # Check if role exists
        role = self.repository.get(role_id)
        if not role:
            return None
        
        # Validate unique name if being changed
        if role_data.name and role_data.name != role.name:
            existing = self.db.query(Role).filter(
                Role.name == role_data.name,
                Role.id != role_id,
                Role.is_deleted == False
            ).first()
            
            if existing:
                raise ValueError(f"Role name '{role_data.name}' already exists")
        
        # Add audit fields
        data = role_data.model_dump(exclude_unset=True)
        if updated_by:
            data["updated_by"] = updated_by
        
        # Update role
        return self.repository.update(role_id, RoleUpdate(**data))
    
    def delete_role(
        self,
        role_id: int,
        deleted_by: Optional[UserId] = None
    ) -> bool:
        """Soft delete a role."""
        role = self.repository.get(role_id)
        if not role:
            return False
        
        # Perform soft delete
        role.soft_delete(deleted_by=deleted_by)
        self.db.commit()
        return True
    
    def get_role_tree(self) -> List[RoleTree]:
        """Get role hierarchy tree."""
        # Get root roles
        roots = self.db.query(Role).filter(
            Role.parent_id == None,
            Role.is_deleted == False
        ).order_by(Role.name).all()
        
        def build_tree(role: Role, level: int = 0) -> RoleTree:
            """Build tree recursively."""
            children = []
            sub_roles = self.db.query(Role).filter(
                Role.parent_id == role.id,
                Role.is_deleted == False
            ).order_by(Role.name).all()
            
            for sub in sub_roles:
                children.append(build_tree(sub, level + 1))
            
            return RoleTree(
                id=role.id,
                code=role.code,
                name=role.name,
                role_type=role.role_type,
                is_active=role.is_active,
                level=level,
                parent_id=role.parent_id,
                children=children
            )
        
        return [build_tree(root) for root in roots]
    
    def assign_user_role(
        self,
        user_id: UserId,
        role_id: int,
        organization_id: OrganizationId,
        assigned_by: Optional[UserId] = None,
        expires_at: Optional[datetime] = None
    ) -> UserRole:
        """Assign a role to a user within an organization context."""
        # Check if assignment already exists
        existing = self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
            UserRole.organization_id == organization_id,
            UserRole.is_active == True
        ).first()
        
        if existing:
            # Update expiry if needed
            if expires_at and existing.expires_at != expires_at:
                existing.expires_at = expires_at
                self.db.commit()
            return existing
        
        # Create new assignment
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            organization_id=organization_id,
            assigned_by=assigned_by,
            expires_at=expires_at
        )
        self.db.add(user_role)
        self.db.commit()
        self.db.refresh(user_role)
        
        return user_role
    
    def remove_user_role(
        self,
        user_id: UserId,
        role_id: int,
        organization_id: OrganizationId
    ) -> bool:
        """Remove a role from a user within an organization context."""
        user_role = self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
            UserRole.organization_id == organization_id,
            UserRole.is_active == True
        ).first()
        
        if user_role:
            user_role.is_active = False
            self.db.commit()
            return True
        
        return False
    
    def get_user_roles(
        self,
        user_id: UserId,
        organization_id: Optional[OrganizationId] = None
    ) -> List[UserRoleInfo]:
        """Get roles assigned to a user, optionally filtered by organization."""
        query = self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.is_active == True
        )
        
        if organization_id:
            query = query.filter(UserRole.organization_id == organization_id)
        
        user_roles = query.all()
        result = []
        
        for ur in user_roles:
            # Check if expired
            if ur.expires_at and ur.expires_at < datetime.utcnow():
                continue
            
            result.append(UserRoleInfo.model_validate(ur))
        
        return result
    
    def get_role_summary(self, role: Role) -> "RoleSummary":
        """Get role summary with counts."""
        from app.schemas.role import RoleSummary
        
        user_count = self.get_role_user_count(role.id)
        sub_role_count = len(role.child_roles) if hasattr(role, 'child_roles') else 0
        
        return RoleSummary(
            id=role.id,
            code=role.code,
            name=role.name,
            name_en=role.name_en,
            is_active=role.is_active,
            user_count=user_count,
            sub_role_count=sub_role_count
        )
    
    def get_role_response(self, role: Role) -> RoleResponse:
        """Get full role response."""
        data = role.to_dict()
        data["parent"] = role.parent.to_dict() if role.parent else None
        
        return RoleResponse.model_validate(data)
    
    def get_role_with_permissions(
        self,
        role: Role,
        include_inherited: bool = False
    ) -> "RoleWithPermissions":
        """Get role with permissions details."""
        from app.schemas.role import RoleWithPermissions
        
        effective_permissions = role.permissions or {}
        inherited_permissions = {}
        
        if include_inherited and role.parent:
            parent = role.parent
            while parent:
                inherited_permissions.update(parent.permissions or {})
                parent = parent.parent
        
        return RoleWithPermissions(
            **self.get_role_response(role).model_dump(),
            effective_permissions=effective_permissions,
            inherited_permissions=inherited_permissions
        )
    
    def list_all_permissions(self, category: Optional[str] = None) -> List["PermissionBasic"]:
        """List all available permissions."""
        from app.schemas.role import PermissionBasic
        
        # This is a placeholder - in a real system, permissions would come from a database or configuration
        permissions = [
            {"code": "user.read", "name": "View Users", "category": "user", "description": "View user information"},
            {"code": "user.create", "name": "Create Users", "category": "user", "description": "Create new users"},
            {"code": "user.update", "name": "Update Users", "category": "user", "description": "Update user information"},
            {"code": "user.delete", "name": "Delete Users", "category": "user", "description": "Delete users"},
            {"code": "role.read", "name": "View Roles", "category": "role", "description": "View role information"},
            {"code": "role.create", "name": "Create Roles", "category": "role", "description": "Create new roles"},
            {"code": "role.update", "name": "Update Roles", "category": "role", "description": "Update role information"},
            {"code": "role.delete", "name": "Delete Roles", "category": "role", "description": "Delete roles"},
        ]
        
        if category:
            permissions = [p for p in permissions if p["category"] == category]
        
        return [PermissionBasic(**p) for p in permissions]
    
    def user_has_permission(
        self,
        user_id: UserId,
        permission: str,
        organization_id: OrganizationId
    ) -> bool:
        """Check if user has a specific permission in an organization."""
        user_roles = self.get_user_roles(user_id, organization_id)
        
        for ur in user_roles:
            role = self.get_role(ur.role_id)
            if role and role.has_permission(permission):
                return True
        
        return False
    
    def update_role_permissions(
        self,
        role_id: int,
        permissions: Dict[str, Any]
    ) -> Optional[Role]:
        """Update role permissions."""
        role = self.get_role(role_id)
        if not role:
            return None
        
        role.permissions = permissions
        self.db.commit()
        self.db.refresh(role)
        
        return role
    
    def get_user_role_response(self, user_role: UserRole) -> UserRoleResponse:
        """Get user role response with full details."""
        role = user_role.role
        effective_permissions = role.get_all_permissions() if hasattr(role, 'get_all_permissions') else {}
        
        return UserRoleResponse(
            **user_role.to_dict(),
            effective_permissions=effective_permissions
        )