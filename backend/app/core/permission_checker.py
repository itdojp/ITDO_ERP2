"""Permission checker with caching support."""

import json
from typing import Any, Dict, List, Optional, Set

from sqlalchemy.orm import Session

from app.core.cache import CacheManager
from app.models.user import User
from app.services.permission import PermissionService
from app.types import OrganizationId, UserId


class PermissionChecker:
    """High-performance permission checker with caching."""

    def __init__(self, db: Session, cache_manager: Optional[CacheManager] = None):
        """Initialize permission checker."""
        self.db = db
        self.permission_service = PermissionService(db)
        self.cache_manager = cache_manager
        self.cache_ttl = 300  # 5 minutes default TTL

    def _get_cache_key(
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

    def _get_permission_cache_key(
        self,
        user_id: UserId,
        permission_code: str,
        organization_id: Optional[OrganizationId] = None,
        department_id: Optional[int] = None,
    ) -> str:
        """Generate cache key for specific permission check."""
        parts = [f"permission_check:user:{user_id}:perm:{permission_code}"]
        if organization_id:
            parts.append(f"org:{organization_id}")
        if department_id:
            parts.append(f"dept:{department_id}")
        return ":".join(parts)

    async def get_user_permissions(
        self,
        user_id: UserId,
        organization_id: Optional[OrganizationId] = None,
        department_id: Optional[int] = None,
        use_cache: bool = True,
    ) -> Set[str]:
        """Get user permissions with caching."""
        if use_cache and self.cache_manager:
            cache_key = self._get_cache_key(user_id, organization_id, department_id)

            # Try to get from cache
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return set(json.loads(cached))

        # Get from database
        permissions = self.permission_service.get_user_permissions(
            user_id, organization_id, department_id
        )

        # Store in cache
        if use_cache and self.cache_manager and permissions:
            await self.cache_manager.set(
                cache_key,
                json.dumps(list(permissions)),
                expire=self.cache_ttl,
            )

        return permissions

    async def check_permission(
        self,
        user_id: UserId,
        permission_code: str,
        organization_id: Optional[OrganizationId] = None,
        department_id: Optional[int] = None,
        use_cache: bool = True,
    ) -> bool:
        """Check if user has specific permission with caching."""
        # Check if user is superuser
        user = self.db.get(User, user_id)
        if user and user.is_superuser:
            return True

        if use_cache and self.cache_manager:
            cache_key = self._get_permission_cache_key(
                user_id, permission_code, organization_id, department_id
            )

            # Try to get from cache
            cached = await self.cache_manager.get(cache_key)
            if cached is not None:
                return cached == "1"

        # Check permission
        has_permission = self.permission_service.check_user_permission(
            user_id, permission_code, organization_id, department_id
        )

        # Store in cache
        if use_cache and self.cache_manager:
            await self.cache_manager.set(
                cache_key,
                "1" if has_permission else "0",
                expire=self.cache_ttl,
            )

        return has_permission

    async def check_permissions(
        self,
        user_id: UserId,
        permission_codes: List[str],
        organization_id: Optional[OrganizationId] = None,
        department_id: Optional[int] = None,
        require_all: bool = True,
        use_cache: bool = True,
    ) -> bool:
        """Check multiple permissions at once."""
        results = []

        for permission_code in permission_codes:
            has_permission = await self.check_permission(
                user_id, permission_code, organization_id, department_id, use_cache
            )
            results.append(has_permission)

        if require_all:
            return all(results)
        else:
            return any(results)

    async def invalidate_user_cache(
        self,
        user_id: UserId,
        organization_id: Optional[OrganizationId] = None,
        department_id: Optional[int] = None,
    ) -> None:
        """Invalidate permission cache for a user."""
        if not self.cache_manager:
            return

        # Invalidate general permissions cache
        cache_key = self._get_cache_key(user_id, organization_id, department_id)
        await self.cache_manager.delete(cache_key)

        # Also invalidate pattern-based keys for specific permission checks
        pattern = f"permission_check:user:{user_id}:*"
        await self.cache_manager.delete_pattern(pattern)

    async def invalidate_role_cache(self, role_id: int) -> None:
        """Invalidate cache for all users with a specific role."""
        if not self.cache_manager:
            return

        # Get all users with this role
        from app.models.role import UserRole

        user_roles = self.db.query(UserRole).filter(
            UserRole.role_id == role_id,
            UserRole.is_active == True,
        ).all()

        # Invalidate cache for each user
        for user_role in user_roles:
            await self.invalidate_user_cache(
                user_role.user_id,
                user_role.organization_id,
                user_role.department_id,
            )

    def get_permission_matrix(
        self,
        user_id: UserId,
        organization_id: Optional[OrganizationId] = None,
    ) -> Dict[str, Dict[str, bool]]:
        """Get permission matrix for user (grouped by category)."""
        # Get all permissions
        permissions = self.permission_service.list_permissions(is_active=True)[0]
        user_permissions = self.permission_service.get_user_permissions(
            user_id, organization_id
        )

        # Build matrix
        matrix = {}
        for perm in permissions:
            if perm.category not in matrix:
                matrix[perm.category] = {}

            matrix[perm.category][perm.code] = perm.code in user_permissions

        return matrix

    def evaluate_permission_expression(
        self,
        user_id: UserId,
        expression: str,
        organization_id: Optional[OrganizationId] = None,
        department_id: Optional[int] = None,
    ) -> bool:
        """Evaluate complex permission expression.
        
        Examples:
        - "user.view" - Simple permission check
        - "user.view AND user.edit" - Both permissions required
        - "user.view OR user.edit" - Either permission required
        - "admin.all OR (user.view AND user.edit)" - Complex expression
        """
        # Get user permissions
        user_permissions = self.permission_service.get_user_permissions(
            user_id, organization_id, department_id
        )

        # Simple implementation - can be enhanced with proper expression parser
        expression = expression.strip()

        # Handle simple permission
        if " " not in expression:
            return expression in user_permissions

        # Handle AND/OR operations
        if " AND " in expression:
            parts = expression.split(" AND ")
            return all(part.strip() in user_permissions for part in parts)

        if " OR " in expression:
            parts = expression.split(" OR ")
            return any(part.strip() in user_permissions for part in parts)

        # Default to simple check
        return expression in user_permissions

    def get_permission_summary(
        self, user_id: UserId, organization_id: Optional[OrganizationId] = None
    ) -> Dict[str, Any]:
        """Get permission summary for user."""
        user = self.db.get(User, user_id)
        if not user:
            return {"error": "User not found"}

        # Get permissions
        permissions = self.permission_service.get_user_permissions(user_id, organization_id)

        # Get roles
        from app.models.role import UserRole

        user_roles = self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.is_active == True,
        )

        if organization_id:
            user_roles = user_roles.filter(UserRole.organization_id == organization_id)

        user_roles = user_roles.all()

        # Build summary
        summary = {
            "user_id": user_id,
            "user_email": user.email,
            "is_superuser": user.is_superuser,
            "organization_id": organization_id,
            "total_permissions": len(permissions),
            "permissions": sorted(list(permissions)),
            "roles": [
                {
                    "role_id": ur.role_id,
                    "role_name": ur.role.name,
                    "role_code": ur.role.code,
                    "organization_id": ur.organization_id,
                    "department_id": ur.department_id,
                    "is_primary": ur.is_primary,
                }
                for ur in user_roles
            ],
            "permission_categories": {},
        }

        # Group permissions by category
        for perm in permissions:
            if "." in perm:
                category = perm.split(".")[0]
                if category not in summary["permission_categories"]:
                    summary["permission_categories"][category] = []
                summary["permission_categories"][category].append(perm)

        return summary
