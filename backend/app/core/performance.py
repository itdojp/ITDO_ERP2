"""Performance optimization utilities for RBAC system."""

import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.role import UserRole
from app.models.user import User
from app.types import OrganizationId, UserId


class PerformanceOptimizer:
    """Performance optimization utilities for RBAC operations."""

    def __init__(self, db: Session):
        """Initialize performance optimizer."""
        self.db = db
        self._query_cache: Dict[str, Any] = {}

    @contextmanager
    def measure_time(self, operation_name: str):
        """Context manager to measure operation time."""
        start_time = time.time()
        try:
            yield
        finally:
            end_time = time.time()
            duration = (end_time - start_time) * 1000  # Convert to ms
            print(f"[PERF] {operation_name}: {duration:.2f}ms")

    def batch_load_user_roles(
        self, user_ids: List[UserId], organization_id: Optional[OrganizationId] = None
    ) -> Dict[UserId, List[UserRole]]:
        """Batch load user roles to avoid N+1 queries."""
        with self.measure_time(f"batch_load_user_roles({len(user_ids)} users)"):
            query = self.db.query(UserRole).options(
                joinedload(UserRole.role),
                joinedload(UserRole.organization),
                joinedload(UserRole.department),
            ).filter(
                UserRole.user_id.in_(user_ids),
                UserRole.is_active == True,
            )

            if organization_id:
                query = query.filter(UserRole.organization_id == organization_id)

            user_roles = query.all()

            # Group by user_id
            result = {}
            for user_role in user_roles:
                if user_role.user_id not in result:
                    result[user_role.user_id] = []
                result[user_role.user_id].append(user_role)

            return result

    def batch_load_role_permissions(
        self, role_ids: List[int]
    ) -> Dict[int, Set[str]]:
        """Batch load role permissions to avoid N+1 queries."""
        with self.measure_time(f"batch_load_role_permissions({len(role_ids)} roles)"):
            # Use raw SQL for better performance
            sql = text("""
                SELECT DISTINCT r.id as role_id, p.code as permission_code
                FROM roles r
                JOIN role_permissions rp ON r.id = rp.role_id
                JOIN permissions p ON rp.permission_id = p.id
                WHERE r.id = ANY(:role_ids)
                AND rp.is_active = true
                AND p.is_active = true
                
                UNION
                
                -- Include inherited permissions
                WITH RECURSIVE role_hierarchy AS (
                    SELECT id, parent_id, code FROM roles WHERE id = ANY(:role_ids)
                    UNION ALL
                    SELECT r.id, r.parent_id, r.code 
                    FROM roles r
                    INNER JOIN role_hierarchy rh ON r.id = rh.parent_id
                )
                SELECT DISTINCT rh.id as role_id, p.code as permission_code
                FROM role_hierarchy rh
                JOIN role_permissions rp ON rh.id = rp.role_id
                JOIN permissions p ON rp.permission_id = p.id
                WHERE rp.is_active = true
                AND p.is_active = true
            """)

            result = {}
            for row in self.db.execute(sql, {"role_ids": role_ids}):
                role_id, permission_code = row
                if role_id not in result:
                    result[role_id] = set()
                result[role_id].add(permission_code)

            return result

    def optimized_user_permissions_bulk(
        self, user_ids: List[UserId], organization_id: Optional[OrganizationId] = None
    ) -> Dict[UserId, Set[str]]:
        """Get permissions for multiple users with optimized queries."""
        with self.measure_time(f"optimized_user_permissions_bulk({len(user_ids)} users)"):
            # Step 1: Batch load user roles
            user_roles_map = self.batch_load_user_roles(user_ids, organization_id)

            # Step 2: Extract all unique role IDs
            all_role_ids = set()
            for user_roles in user_roles_map.values():
                for user_role in user_roles:
                    if user_role.role:
                        all_role_ids.add(user_role.role.id)

            # Step 3: Batch load role permissions
            role_permissions_map = self.batch_load_role_permissions(list(all_role_ids))

            # Step 4: Combine permissions for each user
            result = {}
            for user_id in user_ids:
                user_permissions = set()
                user_roles = user_roles_map.get(user_id, [])

                for user_role in user_roles:
                    if user_role.role and user_role.is_valid:
                        role_perms = role_permissions_map.get(user_role.role.id, set())
                        user_permissions.update(role_perms)

                result[user_id] = user_permissions

            return result

    def get_organization_users_optimized(
        self, organization_id: OrganizationId, include_permissions: bool = False
    ) -> Dict[str, Any]:
        """Get organization users with optimized loading."""
        with self.measure_time(f"get_organization_users_optimized(org:{organization_id})"):
            # Use a single query with proper joins
            query = self.db.query(User).options(
                selectinload(User.user_roles).joinedload(UserRole.role),
                selectinload(User.user_roles).joinedload(UserRole.department),
            ).join(UserRole).filter(
                UserRole.organization_id == organization_id,
                UserRole.is_active == True,
                User.is_active == True,
            ).distinct()

            users = query.all()

            result = {
                "users": [],
                "total": len(users),
                "with_permissions": include_permissions,
            }

            if include_permissions:
                # Batch load permissions for all users
                user_ids = [user.id for user in users]
                permissions_map = self.optimized_user_permissions_bulk(
                    user_ids, organization_id
                )

            for user in users:
                user_data = {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "roles": [
                        {
                            "id": ur.role.id,
                            "code": ur.role.code,
                            "name": ur.role.name,
                            "is_primary": ur.is_primary,
                        }
                        for ur in user.user_roles
                        if ur.organization_id == organization_id and ur.is_active
                    ],
                }

                if include_permissions:
                    user_data["permissions"] = list(permissions_map.get(user.id, set()))

                result["users"].append(user_data)

            return result

    def optimize_role_hierarchy_queries(self, organization_id: OrganizationId) -> Dict[str, Any]:
        """Optimize role hierarchy queries using CTE."""
        with self.measure_time(f"optimize_role_hierarchy_queries(org:{organization_id})"):
            # Use recursive CTE for efficient hierarchy traversal
            sql = text("""
                WITH RECURSIVE role_hierarchy AS (
                    -- Base case: root roles
                    SELECT id, code, name, parent_id, role_type, 0 as level,
                           ARRAY[id] as path, id::text as path_string
                    FROM roles 
                    WHERE parent_id IS NULL 
                    AND (organization_id = :org_id OR organization_id IS NULL)
                    AND is_active = true AND is_deleted = false
                    
                    UNION ALL
                    
                    -- Recursive case: child roles
                    SELECT r.id, r.code, r.name, r.parent_id, r.role_type, 
                           rh.level + 1, rh.path || r.id, 
                           rh.path_string || '/' || r.id::text
                    FROM roles r
                    INNER JOIN role_hierarchy rh ON r.parent_id = rh.id
                    WHERE r.is_active = true AND r.is_deleted = false
                    AND rh.level < 10  -- Prevent infinite recursion
                )
                SELECT * FROM role_hierarchy ORDER BY path_string
            """)

            result = {
                "hierarchy": [],
                "max_depth": 0,
                "total_roles": 0,
            }

            for row in self.db.execute(sql, {"org_id": organization_id}):
                role_data = {
                    "id": row.id,
                    "code": row.code,
                    "name": row.name,
                    "parent_id": row.parent_id,
                    "role_type": row.role_type,
                    "level": row.level,
                    "path": row.path,
                }
                result["hierarchy"].append(role_data)
                result["max_depth"] = max(result["max_depth"], row.level)
                result["total_roles"] += 1

            return result

    def get_permission_usage_stats(self) -> Dict[str, Any]:
        """Get permission usage statistics with optimized queries."""
        with self.measure_time("get_permission_usage_stats"):
            stats = {}

            # Most used permissions
            sql = text("""
                SELECT p.code, p.name, p.category, COUNT(rp.role_id) as usage_count
                FROM permissions p
                LEFT JOIN role_permissions rp ON p.id = rp.permission_id AND rp.is_active = true
                WHERE p.is_active = true
                GROUP BY p.id, p.code, p.name, p.category
                ORDER BY usage_count DESC
                LIMIT 20
            """)

            stats["most_used_permissions"] = [
                {
                    "code": row.code,
                    "name": row.name,
                    "category": row.category,
                    "usage_count": row.usage_count,
                }
                for row in self.db.execute(sql)
            ]

            # Role distribution
            sql = text("""
                SELECT r.role_type, COUNT(ur.user_id) as user_count,
                       COUNT(DISTINCT r.id) as role_count
                FROM roles r
                LEFT JOIN user_roles ur ON r.id = ur.role_id AND ur.is_active = true
                WHERE r.is_active = true AND r.is_deleted = false
                GROUP BY r.role_type
                ORDER BY user_count DESC
            """)

            stats["role_distribution"] = [
                {
                    "role_type": row.role_type,
                    "user_count": row.user_count,
                    "role_count": row.role_count,
                }
                for row in self.db.execute(sql)
            ]

            # Permission by category
            sql = text("""
                SELECT p.category, COUNT(p.id) as permission_count,
                       COUNT(rp.role_id) as assignment_count
                FROM permissions p
                LEFT JOIN role_permissions rp ON p.id = rp.permission_id AND rp.is_active = true
                WHERE p.is_active = true
                GROUP BY p.category
                ORDER BY assignment_count DESC
            """)

            stats["permissions_by_category"] = [
                {
                    "category": row.category,
                    "permission_count": row.permission_count,
                    "assignment_count": row.assignment_count,
                }
                for row in self.db.execute(sql)
            ]

            return stats

    def find_permission_bottlenecks(self) -> Dict[str, Any]:
        """Find potential performance bottlenecks in permission system."""
        with self.measure_time("find_permission_bottlenecks"):
            bottlenecks = {}

            # Deep role hierarchies
            sql = text("""
                WITH RECURSIVE role_depth AS (
                    SELECT id, code, name, parent_id, 0 as depth
                    FROM roles WHERE parent_id IS NULL
                    UNION ALL
                    SELECT r.id, r.code, r.name, r.parent_id, rd.depth + 1
                    FROM roles r
                    JOIN role_depth rd ON r.parent_id = rd.id
                    WHERE rd.depth < 20
                )
                SELECT code, name, depth FROM role_depth 
                WHERE depth > 5 
                ORDER BY depth DESC
                LIMIT 10
            """)

            bottlenecks["deep_hierarchies"] = [
                {"code": row.code, "name": row.name, "depth": row.depth}
                for row in self.db.execute(sql)
            ]

            # Users with many roles
            sql = text("""
                SELECT u.id, u.email, COUNT(ur.role_id) as role_count
                FROM users u
                JOIN user_roles ur ON u.id = ur.user_id
                WHERE ur.is_active = true
                GROUP BY u.id, u.email
                HAVING COUNT(ur.role_id) > 10
                ORDER BY role_count DESC
                LIMIT 10
            """)

            bottlenecks["users_with_many_roles"] = [
                {
                    "user_id": row.id,
                    "email": row.email,
                    "role_count": row.role_count,
                }
                for row in self.db.execute(sql)
            ]

            # Roles with many permissions
            sql = text("""
                SELECT r.id, r.code, r.name, COUNT(rp.permission_id) as permission_count
                FROM roles r
                JOIN role_permissions rp ON r.id = rp.role_id
                WHERE rp.is_active = true
                GROUP BY r.id, r.code, r.name
                HAVING COUNT(rp.permission_id) > 50
                ORDER BY permission_count DESC
                LIMIT 10
            """)

            bottlenecks["roles_with_many_permissions"] = [
                {
                    "role_id": row.id,
                    "code": row.code,
                    "name": row.name,
                    "permission_count": row.permission_count,
                }
                for row in self.db.execute(sql)
            ]

            return bottlenecks

    def create_performance_indexes(self) -> Dict[str, Any]:
        """Create performance indexes for RBAC queries."""
        indexes = []

        try:
            # Composite index for user role lookups
            self.db.execute(text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_roles_user_org_active 
                ON user_roles (user_id, organization_id, is_active) 
                WHERE is_active = true
            """))
            indexes.append("idx_user_roles_user_org_active")

            # Index for role hierarchy traversal
            self.db.execute(text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_roles_parent_active 
                ON roles (parent_id, is_active, is_deleted) 
                WHERE is_active = true AND is_deleted = false
            """))
            indexes.append("idx_roles_parent_active")

            # Index for permission lookups
            self.db.execute(text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_role_permissions_role_active 
                ON role_permissions (role_id, is_active) 
                WHERE is_active = true
            """))
            indexes.append("idx_role_permissions_role_active")

            # Index for organization-specific queries
            self.db.execute(text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_roles_org_type_active 
                ON roles (organization_id, role_type, is_active) 
                WHERE is_active = true AND is_deleted = false
            """))
            indexes.append("idx_roles_org_type_active")

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            return {"created": indexes, "error": str(e)}

        return {"created": indexes, "count": len(indexes)}
