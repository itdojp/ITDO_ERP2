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
    UserRoleResponse,
    BulkRoleAssignment
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
        """Search roles by name."""
        # Build search conditions
        search_condition = or_(
            Role.name.ilike(f"%{query}%"),
            Role.description.ilike(f"%{query}%")
        )
        
        conditions = [search_condition]
        
        # Apply additional filters
        if filters:
            for key, value in filters.items():
                if hasattr(Role, key):
                    conditions.append(getattr(Role, key) == value)
        
        # Get all matching roles
        all_results = self.db.query(Role).filter(
            and_(*conditions),
            Role.is_deleted == False
        ).order_by(Role.updated_at.desc()).all()
        
        # Apply pagination
        total = len(all_results)
        paginated_results = all_results[skip:skip + limit]
        
        return paginated_results, total
    
    def create_role(
        self,
        role_data: RoleCreate,
        created_by: Optional[UserId] = None
    ) -> Role:
        """Create a new role."""
        # Validate unique name within organization
        existing = self.db.query(Role).filter(
            Role.organization_id == role_data.organization_id,
            Role.name == role_data.name,
            Role.is_deleted == False
        ).first()
        
        if existing:
            raise ValueError(f"Role name '{role_data.name}' already exists in this organization")
        
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
                Role.organization_id == role.organization_id,
                Role.name == role_data.name,
                Role.id != role_id,
                Role.is_deleted == False
            ).first()
            
            if existing:
                raise ValueError(f"Role name '{role_data.name}' already exists in this organization")
        
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
    
    def get_role_tree(self, organization_id: OrganizationId) -> List[RoleTree]:
        """Get role hierarchy tree for an organization."""
        # Get root roles
        roots = self.db.query(Role).filter(
            Role.organization_id == organization_id,
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
            
            user_count = self.get_role_user_count(role.id)
            permission_count = len(role.get_all_permissions())
            
            return RoleTree(
                id=role.id,
                name=role.name,
                description=role.description,
                is_active=role.is_active,
                level=level,
                parent_id=role.parent_id,
                user_count=user_count,
                permission_count=permission_count,
                children=children
            )
        
        return [build_tree(root) for root in roots]
    
    def get_role_summary(self, role: Role) -> RoleSummary:
        """Get role summary with counts."""
        parent_name = role.parent.name if role.parent else None
        user_count = self.get_role_user_count(role.id)
        permission_count = len(role.get_all_permissions())
        
        return RoleSummary(
            id=role.id,
            name=role.name,
            description=role.description,
            organization_id=role.organization_id,
            is_active=role.is_active,
            parent_id=role.parent_id,
            parent_name=parent_name,
            user_count=user_count,
            permission_count=permission_count,
            role_type=role.role_type
        )
    
    def get_role_response(self, role: Role) -> RoleResponse:
        """Get full role response."""
        # Load parent if needed
        if role.parent_id and not role.parent:
            role = self.repository.get_with_parent(role.id)
        
        # Build response
        data = role.to_dict()
        data["parent"] = role.parent.to_dict() if role.parent else None
        data["full_path"] = role.full_path
        data["depth"] = role.depth
        
        return RoleResponse.model_validate(data)
    
    def get_role_with_permissions(
        self,
        role: Role,
        include_inherited: bool = True
    ) -> RoleWithPermissions:
        """Get role with permission details."""
        # Get direct permissions
        direct_permissions = [
            PermissionBasic(
                id=rp.permission.id,
                code=rp.permission.code,
                name=rp.permission.name,
                description=rp.permission.description,
                category=rp.permission.category
            )
            for rp in role.role_permissions
            if rp.is_active
        ]
        
        # Get all permissions (including inherited)
        all_permission_codes = set()
        inherited_permissions = []
        
        if include_inherited:
            all_permissions = role.get_all_permissions()
            all_permission_codes = {p.code for p in all_permissions}
            
            # Identify inherited permissions
            direct_codes = {p.code for p in direct_permissions}
            for perm in all_permissions:
                if perm.code not in direct_codes:
                    inherited_permissions.append(
                        PermissionBasic(
                            id=perm.id,
                            code=perm.code,
                            name=perm.name,
                            description=perm.description,
                            category=perm.category
                        )
                    )
        else:
            all_permission_codes = {p.code for p in direct_permissions}
        
        # Get role response
        role_response = self.get_role_response(role)
        
        return RoleWithPermissions(
            **role_response.model_dump(),
            direct_permissions=direct_permissions,
            inherited_permissions=inherited_permissions,
            all_permission_codes=list(all_permission_codes)
        )
    
    def list_all_permissions(self, category: Optional[str] = None) -> List[PermissionBasic]:
        """List all available permissions."""
        query = self.db.query(Permission)
        
        if category:
            query = query.filter(Permission.category == category)
        
        permissions = query.order_by(Permission.category, Permission.name).all()
        
        return [
            PermissionBasic(
                id=p.id,
                code=p.code,
                name=p.name,
                description=p.description,
                category=p.category
            )
            for p in permissions
        ]
    
    def update_role_permissions(
        self,
        role_id: int,
        permission_codes: List[str],
        updated_by: Optional[UserId] = None
    ) -> Role:
        """Update role permissions."""
        role = self.repository.get(role_id)
        if not role:
            raise ValueError("Role not found")
        
        # Validate all permission codes exist
        permissions = self.db.query(Permission).filter(
            Permission.code.in_(permission_codes)
        ).all()
        
        if len(permissions) != len(permission_codes):
            found_codes = {p.code for p in permissions}
            invalid_codes = set(permission_codes) - found_codes
            raise ValueError(f"Invalid permission codes: {invalid_codes}")
        
        # Remove existing permissions
        self.db.query(RolePermission).filter(
            RolePermission.role_id == role_id
        ).delete()
        
        # Add new permissions
        for permission in permissions:
            role_permission = RolePermission(
                role_id=role_id,
                permission_id=permission.id,
                granted_by=updated_by
            )
            self.db.add(role_permission)
        
        # Update audit fields
        if updated_by:
            role.updated_by = updated_by
            role.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(role)
        
        return role
    
    def is_role_in_use(self, role_id: int) -> bool:
        """Check if role is assigned to any users."""
        return self.db.query(UserRole).filter(
            UserRole.role_id == role_id,
            UserRole.is_active == True
        ).first() is not None
    
    def get_role_user_count(self, role_id: int) -> int:
        """Get count of users with this role."""
        return self.db.query(UserRole).filter(
            UserRole.role_id == role_id,
            UserRole.is_active == True
        ).count()
    
    def assign_role_to_user(
        self,
        assignment: UserRoleAssignment,
        assigned_by: Optional[UserId] = None
    ) -> UserRole:
        """Assign a role to a user."""
        # Check if assignment already exists
        existing = self.db.query(UserRole).filter(
            UserRole.user_id == assignment.user_id,
            UserRole.role_id == assignment.role_id
        ).first()
        
        if existing:
            if existing.is_active:
                raise ValueError("User already has this role")
            else:
                # Reactivate existing assignment
                existing.is_active = True
                existing.valid_from = assignment.valid_from or datetime.utcnow()
                existing.valid_to = assignment.valid_to
                existing.assigned_by = assigned_by
                self.db.commit()
                self.db.refresh(existing)
                return existing
        
        # Get role to determine organization
        role = self.repository.get(assignment.role_id)
        if not role:
            raise ValueError("Role not found")
        
        # Create new assignment
        user_role = UserRole(
            user_id=assignment.user_id,
            role_id=assignment.role_id,
            organization_id=role.organization_id,
            valid_from=assignment.valid_from or datetime.utcnow(),
            valid_to=assignment.valid_to,
            assigned_by=assigned_by
        )
        
        self.db.add(user_role)
        self.db.commit()
        self.db.refresh(user_role)
        
        return user_role
    
    def remove_role_from_user(self, user_id: UserId, role_id: int) -> bool:
        """Remove a role from a user."""
        user_role = self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
            UserRole.is_active == True
        ).first()
        
        if not user_role:
            return False
        
        # Deactivate assignment
        user_role.is_active = False
        self.db.commit()
        
        return True
    
    def get_user_roles(
        self,
        user_id: UserId,
        organization_id: Optional[OrganizationId] = None,
        active_only: bool = True
    ) -> List[UserRole]:
        """Get all roles assigned to a user."""
        query = self.db.query(UserRole).filter(UserRole.user_id == user_id)
        
        if organization_id:
            query = query.filter(UserRole.organization_id == organization_id)
        
        if active_only:
            query = query.filter(UserRole.is_active == True)
        
        return query.all()
    
    def get_user_role_response(self, user_role: UserRole) -> UserRoleResponse:
        """Get user role assignment response."""
        # Load related data
        if not user_role.role:
            user_role = self.db.query(UserRole).filter(
                UserRole.id == user_role.id
            ).first()
        
        role_basic = {
            "id": user_role.role.id,
            "name": user_role.role.name,
            "description": user_role.role.description,
            "is_active": user_role.role.is_active
        }
        
        assigner_name = None
        if user_role.assigned_by:
            assigner = self.db.query(User).filter(
                User.id == user_role.assigned_by
            ).first()
            if assigner:
                assigner_name = assigner.full_name
        
        return UserRoleResponse(
            id=user_role.id,
            user_id=user_role.user_id,
            role_id=user_role.role_id,
            organization_id=user_role.organization_id,
            role=role_basic,
            valid_from=user_role.valid_from,
            valid_to=user_role.valid_to,
            is_active=user_role.is_active,
            is_valid=user_role.is_valid,
            assigned_by=user_role.assigned_by,
            assigner_name=assigner_name,
            created_at=user_role.created_at
        )
    
    def user_has_permission(
        self,
        user_id: UserId,
        permission: str,
        organization_id: Optional[OrganizationId] = None
    ) -> bool:
        """Check if user has permission for roles."""
        # Get user roles
        user_roles = self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.is_active == True
        )
        
        if organization_id:
            user_roles = user_roles.filter(UserRole.organization_id == organization_id)
        
        # Check permissions
        for user_role in user_roles.all():
            if user_role.is_valid and user_role.role.has_permission(permission):
                return True
        
        return False