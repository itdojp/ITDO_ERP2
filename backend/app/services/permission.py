"""Permission service implementation with advanced caching."""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session

from app.core.cache import CacheManager
from app.core.exceptions import NotFound, PermissionDenied, ValidationError
from app.models.permission import SYSTEM_PERMISSIONS, Permission
from app.models.role import Role, UserRole
from app.models.role_permission import PermissionEffect, RolePermission
from app.models.user import User
from app.repositories.role import RoleRepository
from app.schemas.permission import PermissionCreate, PermissionUpdate
from app.types import OrganizationId, RoleId, UserId


class PermissionService:
    """Service for permission management and evaluation with advanced caching."""

    # Cache TTL settings
    CACHE_TTL_ORGANIZATION = 3600  # 1 hour
    CACHE_TTL_ROLE = 1800  # 30 minutes
    CACHE_TTL_USER = 300  # 5 minutes
    CACHE_TTL_MATRIX = 600  # 10 minutes

    def __init__(self, db: Session, cache_manager: Optional[CacheManager] = None):
        """Initialize permission service."""
        self.db = db
        self.role_repository = RoleRepository(Role, db)
        self.cache_manager = cache_manager
        self._permission_cache: Dict[str, Permission] = {}

    def get_permission(self, permission_id: int) -> Optional[Permission]:
        """Get permission by ID."""
        return self.db.get(Permission, permission_id)

    def get_permission_by_code(self, code: str) -> Optional[Permission]:
        """Get permission by unique code."""
        return self.db.query(Permission).filter(Permission.code == code).first()

    def list_permissions(
        self,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Permission], int]:
        """List permissions with filters."""
        query = self.db.query(Permission)

        if category:
            query = query.filter(Permission.category == category)
        if is_active is not None:
            query = query.filter(Permission.is_active == is_active)

        total = query.count()
        permissions = query.offset(skip).limit(limit).all()

        return permissions, total

    def get_permissions_by_category(self) -> Dict[str, List[Permission]]:
        """Get permissions grouped by category."""
        permissions = self.db.query(Permission).filter(Permission.is_active == True).all()

        grouped = {}
        for perm in permissions:
            if perm.category not in grouped:
                grouped[perm.category] = []
            grouped[perm.category].append(perm)

        return grouped

    def create_permission(
        self, permission_data: PermissionCreate
    ) -> Permission:
        """Create a new permission."""
        # Check if permission code already exists
        existing = self.get_permission_by_code(permission_data.code)
        if existing:
            raise ValidationError(f"Permission with code '{permission_data.code}' already exists")

        permission = Permission(**permission_data.model_dump())
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)

        return permission

    def update_permission(
        self, permission_id: int, permission_data: PermissionUpdate
    ) -> Optional[Permission]:
        """Update permission details."""
        permission = self.get_permission(permission_id)
        if not permission:
            return None

        if permission.is_system:
            raise PermissionDenied("Cannot modify system permissions")

        # Update permission
        update_data = permission_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(permission, field, value)

        self.db.commit()
        self.db.refresh(permission)

        return permission

    def delete_permission(self, permission_id: int) -> bool:
        """Delete a permission."""
        permission = self.get_permission(permission_id)
        if not permission:
            return False

        if permission.is_system:
            raise PermissionDenied("Cannot delete system permissions")

        self.db.delete(permission)
        self.db.commit()

        return True

    def initialize_system_permissions(self) -> int:
        """Initialize system permissions from predefined list."""
        created_count = 0

        for perm_data in SYSTEM_PERMISSIONS:
            existing = self.get_permission_by_code(perm_data["code"])
            if not existing:
                permission = Permission(
                    code=perm_data["code"],
                    name=perm_data["name"],
                    category=perm_data["category"],
                    description=perm_data.get("description"),
                    is_system=True,
                    is_active=True,
                )
                self.db.add(permission)
                created_count += 1

        self.db.commit()
        return created_count

    def get_user_permissions(
        self,
        user_id: UserId,
        organization_id: Optional[OrganizationId] = None,
        department_id: Optional[int] = None,
    ) -> Set[str]:
        """Get all effective permissions for a user."""
        # Get user
        user = self.db.get(User, user_id)
        if not user:
            return set()

        # Superusers have all permissions
        if user.is_superuser:
            all_permissions = self.db.query(Permission).filter(Permission.is_active == True).all()
            return {perm.code for perm in all_permissions}

        # Get user's roles
        user_roles = self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.is_active == True,
        )

        if organization_id:
            user_roles = user_roles.filter(UserRole.organization_id == organization_id)

        user_roles = user_roles.all()

        # Collect permissions from all roles
        permissions = set()
        for user_role in user_roles:
            if user_role.is_valid:
                role_permissions = self.role_repository.get_effective_permissions(
                    user_role.role_id, organization_id, department_id
                )
                permissions.update(role_permissions)

        return permissions

    def check_user_permission(
        self,
        user_id: UserId,
        permission_code: str,
        organization_id: Optional[OrganizationId] = None,
        department_id: Optional[int] = None,
    ) -> bool:
        """Check if user has a specific permission."""
        permissions = self.get_user_permissions(user_id, organization_id, department_id)
        return permission_code in permissions

    def get_role_permissions(
        self,
        role_id: RoleId,
        organization_id: Optional[OrganizationId] = None,
        department_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get permissions for a role with details."""
        role_permissions = self.db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.is_active == True,
        )

        if organization_id is not None:
            role_permissions = role_permissions.filter(
                RolePermission.organization_id == organization_id
            )
        if department_id is not None:
            role_permissions = role_permissions.filter(
                RolePermission.department_id == department_id
            )

        role_permissions = role_permissions.all()

        result = []
        for rp in role_permissions:
            if rp.permission and rp.permission.is_active:
                result.append({
                    "permission_id": rp.permission_id,
                    "code": rp.permission.code,
                    "name": rp.permission.name,
                    "category": rp.permission.category,
                    "effect": rp.effect,
                    "organization_id": rp.organization_id,
                    "department_id": rp.department_id,
                    "granted_at": rp.granted_at,
                    "expires_at": rp.expires_at,
                    "is_override": rp.is_override,
                    "priority": rp.priority,
                })

        return result

    def assign_permission_to_role(
        self,
        role_id: RoleId,
        permission_id: int,
        granted_by: Optional[UserId] = None,
        effect: PermissionEffect = PermissionEffect.ALLOW,
        organization_id: Optional[OrganizationId] = None,
        department_id: Optional[int] = None,
        priority: int = 0,
        expires_at: Optional[str] = None,
    ) -> RolePermission:
        """Assign a permission to a role."""
        # Validate role exists
        role = self.db.get(Role, role_id)
        if not role:
            raise NotFound(f"Role {role_id} not found")

        # Validate permission exists
        permission = self.get_permission(permission_id)
        if not permission:
            raise NotFound(f"Permission {permission_id} not found")

        # Check for existing assignment
        existing = self.db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
            RolePermission.organization_id == organization_id,
            RolePermission.department_id == department_id,
        ).first()

        if existing:
            # Update existing
            existing.effect = effect.value
            existing.granted_by = granted_by
            existing.is_active = True
            existing.priority = priority
            existing.expires_at = expires_at
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # Create new assignment
        role_permission = RolePermission(
            role_id=role_id,
            permission_id=permission_id,
            effect=effect.value,
            granted_by=granted_by,
            organization_id=organization_id,
            department_id=department_id,
            is_active=True,
            priority=priority,
            expires_at=expires_at,
        )

        self.db.add(role_permission)
        self.db.commit()
        self.db.refresh(role_permission)

        return role_permission

    def revoke_permission_from_role(
        self,
        role_id: RoleId,
        permission_id: int,
        organization_id: Optional[OrganizationId] = None,
        department_id: Optional[int] = None,
    ) -> bool:
        """Revoke a permission from a role."""
        role_permission = self.db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
            RolePermission.organization_id == organization_id,
            RolePermission.department_id == department_id,
        ).first()

        if not role_permission:
            return False

        self.db.delete(role_permission)
        self.db.commit()

        return True

    def get_permission_statistics(self) -> Dict[str, Any]:
        """Get system-wide permission statistics."""
        total_permissions = self.db.query(Permission).count()
        active_permissions = self.db.query(Permission).filter(Permission.is_active == True).count()
        system_permissions = self.db.query(Permission).filter(Permission.is_system == True).count()

        # Count by category
        category_counts = {}
        categories = self.db.query(Permission.category).distinct().all()
        for (category,) in categories:
            count = self.db.query(Permission).filter(Permission.category == category).count()
            category_counts[category] = count

        # Count role assignments
        total_assignments = self.db.query(RolePermission).count()
        active_assignments = self.db.query(RolePermission).filter(RolePermission.is_active == True).count()

        return {
            "total_permissions": total_permissions,
            "active_permissions": active_permissions,
            "system_permissions": system_permissions,
            "custom_permissions": total_permissions - system_permissions,
            "category_counts": category_counts,
            "total_assignments": total_assignments,
            "active_assignments": active_assignments,
        }

    def validate_permission_scope(
        self,
        permission_code: str,
        organization_id: Optional[OrganizationId] = None,
        department_id: Optional[int] = None,
    ) -> bool:
        """Validate if permission can be applied at given scope."""
        permission = self.get_permission_by_code(permission_code)
        if not permission:
            return False

        # Admin permissions can be applied anywhere
        if permission.category == "admin":
            return True

        # Organization permissions require organization context
        if permission.category == "organization" and not organization_id:
            return False

        # Department permissions require both organization and department context
        if permission.category == "department":
            return organization_id is not None and department_id is not None

        return True

    def get_conflicting_permissions(
        self, role_id: RoleId, permission_id: int
    ) -> List[RolePermission]:
        """Get permissions that might conflict with the given permission."""
        permission = self.get_permission(permission_id)
        if not permission:
            return []

        # Find permissions in the same category with opposite effects
        conflicting = self.db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.is_active == True,
        ).join(Permission).filter(
            Permission.category == permission.category,
            Permission.id != permission_id,
        ).all()

        return conflicting

    # Advanced caching methods

    async def get_user_permissions_cached(
        self,
        user_id: UserId,
        organization_id: Optional[OrganizationId] = None,
        department_id: Optional[int] = None,
    ) -> Set[str]:
        """Get user permissions with caching."""
        if not self.cache_manager:
            return self.get_user_permissions(user_id, organization_id, department_id)

        # Generate cache key
        cache_key = self._get_user_permissions_cache_key(user_id, organization_id, department_id)

        # Try cache first
        cached = await self.cache_manager.get(cache_key)
        if cached:
            return set(json.loads(cached))

        # Get from database
        permissions = self.get_user_permissions(user_id, organization_id, department_id)

        # Cache the result
        if permissions:
            await self.cache_manager.set(
                cache_key,
                json.dumps(list(permissions)),
                expire=self.CACHE_TTL_USER
            )

        return permissions

    async def get_permission_matrix_cached(
        self,
        organization_id: OrganizationId,
        force_refresh: bool = False
    ) -> Dict[str, Dict[str, Any]]:
        """Get organization permission matrix with caching."""
        if not self.cache_manager:
            return self.generate_permission_matrix(organization_id)

        cache_key = f"permission_matrix:org:{organization_id}"

        if not force_refresh:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return json.loads(cached)

        # Generate matrix
        matrix = self.generate_permission_matrix(organization_id)

        # Cache the result
        await self.cache_manager.set(
            cache_key,
            json.dumps(matrix),
            expire=self.CACHE_TTL_MATRIX
        )

        return matrix

    def generate_permission_matrix(
        self, organization_id: OrganizationId
    ) -> Dict[str, Dict[str, Any]]:
        """Generate permission matrix for an organization."""
        # Get all roles in organization
        org_roles = self.db.query(Role).filter(
            Role.organization_id == organization_id,
            Role.is_active == True,
            Role.is_deleted == False,
        ).all()

        # Include system roles
        system_roles = self.db.query(Role).filter(
            Role.is_system == True,
            Role.is_active == True,
            Role.is_deleted == False,
        ).all()

        all_roles = org_roles + system_roles

        # Get all permissions
        permissions = self.db.query(Permission).filter(
            Permission.is_active == True
        ).all()

        # Build matrix
        matrix = {
            "roles": {},
            "permissions": {},
            "categories": {},
        }

        # Map permissions by category
        for perm in permissions:
            if perm.category not in matrix["categories"]:
                matrix["categories"][perm.category] = []
            matrix["categories"][perm.category].append({
                "id": perm.id,
                "code": perm.code,
                "name": perm.name,
            })
            matrix["permissions"][perm.code] = {
                "id": perm.id,
                "name": perm.name,
                "category": perm.category,
            }

        # Build role permissions
        for role in all_roles:
            role_perms = self.role_repository.get_effective_permissions(
                role.id, organization_id
            )
            matrix["roles"][role.code] = {
                "id": role.id,
                "name": role.name,
                "type": role.role_type,
                "permissions": list(role_perms),
                "permission_count": len(role_perms),
            }

        matrix["summary"] = {
            "total_roles": len(all_roles),
            "total_permissions": len(permissions),
            "total_categories": len(matrix["categories"]),
            "generated_at": datetime.utcnow().isoformat(),
        }

        return matrix

    async def invalidate_user_permission_cache(
        self,
        user_id: UserId,
        organization_id: Optional[OrganizationId] = None
    ) -> None:
        """Invalidate user permission cache."""
        if not self.cache_manager:
            return

        # Invalidate specific cache
        if organization_id:
            cache_key = self._get_user_permissions_cache_key(user_id, organization_id)
            await self.cache_manager.delete(cache_key)

        # Invalidate all user caches
        pattern = f"permissions:user:{user_id}:*"
        await self.cache_manager.delete_pattern(pattern)

    async def invalidate_role_permission_cache(self, role_id: RoleId) -> None:
        """Invalidate cache for all users with a role."""
        if not self.cache_manager:
            return

        # Get all users with this role
        user_roles = self.db.query(UserRole).filter(
            UserRole.role_id == role_id,
            UserRole.is_active == True,
        ).all()

        # Invalidate each user's cache
        tasks = []
        for ur in user_roles:
            tasks.append(
                self.invalidate_user_permission_cache(
                    ur.user_id, ur.organization_id
                )
            )

        if tasks:
            await asyncio.gather(*tasks)

    async def invalidate_organization_cache(
        self, organization_id: OrganizationId
    ) -> None:
        """Invalidate all caches for an organization."""
        if not self.cache_manager:
            return

        # Invalidate matrix cache
        matrix_key = f"permission_matrix:org:{organization_id}"
        await self.cache_manager.delete(matrix_key)

        # Invalidate user caches for this org
        pattern = f"permissions:*:org:{organization_id}:*"
        await self.cache_manager.delete_pattern(pattern)

    def _get_user_permissions_cache_key(
        self,
        user_id: UserId,
        organization_id: Optional[OrganizationId] = None,
        department_id: Optional[int] = None,
    ) -> str:
        """Generate cache key for user permissions."""
        parts = [f"permissions:user:{user_id}"]
        if organization_id:
            parts.append(f"org:{organization_id}")
        if department_id:
            parts.append(f"dept:{department_id}")
        return ":".join(parts)

    async def warm_cache_for_organization(
        self, organization_id: OrganizationId
    ) -> Dict[str, int]:
        """Warm permission caches for an organization."""
        if not self.cache_manager:
            return {"warmed": 0}

        results = {"warmed": 0, "errors": 0}

        # Get all active users in organization
        users = self.db.query(User).join(UserRole).filter(
            UserRole.organization_id == organization_id,
            UserRole.is_active == True,
            User.is_active == True,
        ).distinct().all()

        # Warm cache for each user
        tasks = []
        for user in users:
            tasks.append(
                self.get_user_permissions_cached(
                    user.id, organization_id
                )
            )

        if tasks:
            completed = await asyncio.gather(*tasks, return_exceptions=True)
            for result in completed:
                if isinstance(result, Exception):
                    results["errors"] += 1
                else:
                    results["warmed"] += 1

        # Warm matrix cache
        await self.get_permission_matrix_cached(organization_id)
        results["warmed"] += 1

        return results

    def evaluate_dynamic_permission(
        self,
        user_id: UserId,
        permission_code: str,
        context: Dict[str, Any],
    ) -> bool:
        """Evaluate permission with dynamic context."""
        # Get base permission
        has_base = self.check_user_permission(
            user_id,
            permission_code,
            context.get("organization_id"),
            context.get("department_id")
        )

        if not has_base:
            return False

        # Apply dynamic rules
        permission = self.get_permission_by_code(permission_code)
        if not permission:
            return False

        # Check time-based restrictions
        if context.get("time_restricted"):
            current_hour = datetime.utcnow().hour
            allowed_hours = context.get("allowed_hours", [])
            if allowed_hours and current_hour not in allowed_hours:
                return False

        # Check resource limits
        if context.get("resource_limits"):
            # Example: Check if user has exceeded resource limits
            resource_type = context.get("resource_type")
            current_count = context.get("current_count", 0)
            max_allowed = context.get("max_allowed", float('inf'))
            if current_count >= max_allowed:
                return False

        # Check conditional permissions
        if context.get("conditions"):
            for condition in context["conditions"]:
                if not self._evaluate_condition(user_id, condition):
                    return False

        return True

    def _evaluate_condition(
        self, user_id: UserId, condition: Dict[str, Any]
    ) -> bool:
        """Evaluate a single permission condition."""
        condition_type = condition.get("type")

        if condition_type == "has_role":
            required_role = condition.get("role_code")
            user_roles = self.db.query(UserRole).join(Role).filter(
                UserRole.user_id == user_id,
                UserRole.is_active == True,
                Role.code == required_role,
            ).first()
            return user_roles is not None

        elif condition_type == "in_department":
            required_dept = condition.get("department_id")
            user_roles = self.db.query(UserRole).filter(
                UserRole.user_id == user_id,
                UserRole.department_id == required_dept,
                UserRole.is_active == True,
            ).first()
            return user_roles is not None

        elif condition_type == "custom":
            # Custom condition evaluation
            return condition.get("result", False)

        return True

    def get_permission_inheritance_chain(
        self, role_id: RoleId
    ) -> List[Dict[str, Any]]:
        """Get the complete permission inheritance chain for a role."""
        chain = []
        current_role = self.db.get(Role, role_id)

        while current_role:
            permissions = self.get_role_permissions(current_role.id)
            chain.append({
                "role_id": current_role.id,
                "role_code": current_role.code,
                "role_name": current_role.name,
                "permissions": permissions,
                "permission_count": len(permissions),
                "is_system": current_role.is_system,
            })

            # Move to parent
            current_role = current_role.parent if current_role.parent_id else None

        return chain

    def optimize_permission_assignments(
        self, role_id: RoleId
    ) -> Dict[str, Any]:
        """Optimize permission assignments by removing redundant permissions."""
        role = self.db.get(Role, role_id)
        if not role:
            raise NotFound(f"Role {role_id} not found")

        results = {
            "role_id": role_id,
            "removed_redundant": 0,
            "kept_permissions": 0,
            "optimized": False,
        }

        if role.is_system:
            results["error"] = "Cannot optimize system roles"
            return results

        # Get direct permissions
        direct_perms = self.db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.is_active == True,
        ).all()

        # Get inherited permissions
        inherited_perms = set()
        if role.parent_id:
            inherited_perms = self.role_repository.get_effective_permissions(
                role.parent_id
            )

        # Check for redundancy
        for rp in direct_perms:
            if rp.permission and rp.permission.code in inherited_perms:
                # This permission is redundant
                self.db.delete(rp)
                results["removed_redundant"] += 1
            else:
                results["kept_permissions"] += 1

        if results["removed_redundant"] > 0:
            self.db.commit()
            results["optimized"] = True

        return results
