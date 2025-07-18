"""
Enhanced Department Service for Issue #42.
拡張部門管理サービス（Issue #42 - 組織・部門管理API実装と階層構造サポート）
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.department import Department
from app.models.organization import Organization
from app.models.user import User
from app.schemas.department import (
    DepartmentResponse,
    DepartmentTree,
    DepartmentWithStats,
)


class EnhancedDepartmentService:
    """Enhanced service for department management with hierarchical support."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_department_tree(
        self,
        department_id: int,
        include_users: bool = False,
        include_inactive: bool = False,
        max_depth: int = 5,
    ) -> Optional[DepartmentTree]:
        """
        Get hierarchical department tree structure.
        階層的な部門ツリー構造を取得
        """
        try:
            # Build query with appropriate joins
            query = select(Department).where(Department.id == department_id)
            query = query.options(joinedload(Department.organization))

            if include_users:
                query = query.options(selectinload(Department.users))

            result = await self.db.execute(query)
            department = result.scalar_one_or_none()

            if not department:
                return None

            # Recursively build tree structure
            return await self._build_department_tree_node(
                department, include_users, include_inactive, max_depth, 0
            )

        except Exception as e:
            raise ValueError(f"Failed to get department tree: {str(e)}")

    async def _build_department_tree_node(
        self,
        department: Department,
        include_users: bool,
        include_inactive: bool,
        max_depth: int,
        current_depth: int,
    ) -> DepartmentTree:
        """Build a single tree node with children."""

        # Get sub-departments
        sub_departments = []
        if current_depth < max_depth:
            sub_query = select(Department).where(
                Department.parent_id == department.id
            ).order_by(Department.display_order, Department.name)

            if not include_inactive:
                sub_query = sub_query.where(Department.is_active == True)

            if include_users:
                sub_query = sub_query.options(selectinload(Department.users))

            result = await self.db.execute(sub_query)
            sub_depts = result.scalars().all()

            for sub_dept in sub_depts:
                sub_tree = await self._build_department_tree_node(
                    sub_dept, include_users, include_inactive, max_depth, current_depth + 1
                )
                sub_departments.append(sub_tree)

        # Get direct users if requested
        users = []
        if include_users:
            user_query = select(User).where(
                User.department_id == department.id
            ).order_by(User.full_name)

            if not include_inactive:
                user_query = user_query.where(User.is_active == True)

            result = await self.db.execute(user_query)
            user_list = result.scalars().all()
            users = [
                {
                    "id": u.id,
                    "name": u.full_name,
                    "email": u.email,
                    "is_active": u.is_active
                }
                for u in user_list
            ]

        return DepartmentTree(
            id=department.id,
            code=department.code,
            name=department.name,
            organization_id=department.organization_id,
            parent_id=department.parent_id,
            is_active=department.is_active,
            manager_id=department.manager_id,
            depth=department.depth,
            path=department.path,
            sub_departments=sub_departments,
            users=users,
            current_depth=current_depth
        )

    async def get_department_with_stats(
        self, department_id: int, include_sub_departments: bool = False
    ) -> Optional[DepartmentWithStats]:
        """
        Get department with comprehensive statistics.
        部門の包括的統計情報を取得
        """
        try:
            # Get department
            query = select(Department).where(Department.id == department_id)
            query = query.options(joinedload(Department.organization))
            result = await self.db.execute(query)
            department = result.scalar_one_or_none()

            if not department:
                return None

            # Calculate statistics
            stats = await self._calculate_department_stats(department_id, include_sub_departments)

            return DepartmentWithStats(
                id=department.id,
                code=department.code,
                name=department.name,
                organization_id=department.organization_id,
                parent_id=department.parent_id,
                is_active=department.is_active,
                manager_id=department.manager_id,
                department_type=department.department_type,
                budget=department.budget,
                headcount_limit=department.headcount_limit,
                depth=department.depth,
                path=department.path,
                statistics=stats
            )

        except Exception as e:
            raise ValueError(f"Failed to get department statistics: {str(e)}")

    async def _calculate_department_stats(
        self, department_id: int, include_sub_departments: bool
    ) -> Dict[str, Any]:
        """Calculate comprehensive department statistics."""

        stats = {
            "total_users": 0,
            "active_users": 0,
            "total_sub_departments": 0,
            "active_sub_departments": 0,
            "department_levels": 0,
            "budget_utilization": 0.0,
            "headcount_utilization": 0.0,
            "user_distribution": {},
            "role_distribution": {}
        }

        try:
            dept_filter = [Department.id == department_id]
            user_filter = [User.department_id == department_id]

            if include_sub_departments:
                # Get all sub-department IDs
                sub_dept_ids = await self._get_all_sub_department_ids(department_id)
                if sub_dept_ids:
                    dept_filter.append(Department.id.in_(sub_dept_ids))
                    user_filter.append(User.department_id.in_(sub_dept_ids))

            # User statistics
            user_query = select(
                func.count(User.id).label("total"),
                func.count(User.id).filter(User.is_active == True).label("active")
            ).where(or_(*user_filter))

            result = await self.db.execute(user_query)
            user_stats = result.first()

            stats["total_users"] = user_stats.total or 0
            stats["active_users"] = user_stats.active or 0

            # Sub-department statistics
            if include_sub_departments:
                subdept_query = select(
                    func.count(Department.id).label("total"),
                    func.count(Department.id).filter(Department.is_active == True).label("active"),
                    func.max(Department.depth).label("max_depth")
                ).where(Department.parent_id == department_id)

                result = await self.db.execute(subdept_query)
                subdept_stats = result.first()

                stats["total_sub_departments"] = subdept_stats.total or 0
                stats["active_sub_departments"] = subdept_stats.active or 0
                stats["department_levels"] = (subdept_stats.max_depth or 0) + 1

            # Get department for budget/headcount calculations
            dept_query = select(Department).where(Department.id == department_id)
            result = await self.db.execute(dept_query)
            department = result.scalar_one_or_none()

            if department:
                # Budget utilization calculation (placeholder - would need actual expense data)
                if department.budget and department.budget > 0:
                    stats["budget_utilization"] = 0.0  # Would calculate from expenses

                # Headcount utilization
                if department.headcount_limit and department.headcount_limit > 0:
                    stats["headcount_utilization"] = (stats["active_users"] / department.headcount_limit) * 100

            # User distribution by role
            # Simplified role distribution query
            role_dist_query = select(
                func.count(User.id).label("total_users")
            ).select_from(
                User
            ).where(
                or_(*user_filter),
                User.is_active == True
            )

            # Simplified role distribution - would need proper role join
            stats["role_distribution"] = {"users": stats["active_users"]}

            return stats

        except Exception as e:
            raise ValueError(f"Failed to calculate statistics: {str(e)}")

    async def move_department(
        self,
        department_id: int,
        new_parent_id: Optional[int],
        new_organization_id: Optional[int],
        updated_by: int,
    ) -> bool:
        """
        Move department to a different parent or organization.
        部門の親部門変更または組織間移動
        """
        try:
            # Get the department to move
            query = select(Department).where(Department.id == department_id)
            result = await self.db.execute(query)
            department = result.scalar_one_or_none()

            if not department:
                raise ValueError("Department not found")

            # Validate the move
            if new_parent_id:
                # Check if new parent exists and is in same organization (unless cross-org move)
                target_org_id = new_organization_id or department.organization_id
                parent_query = select(Department).where(
                    Department.id == new_parent_id,
                    Department.organization_id == target_org_id
                )
                parent_result = await self.db.execute(parent_query)
                new_parent = parent_result.scalar_one_or_none()

                if not new_parent:
                    raise ValueError("New parent department not found in target organization")

                # Check for circular reference
                if await self._would_create_circular_reference(department_id, new_parent_id):
                    raise ValueError("Move would create circular reference")

                # Check depth constraints
                if new_parent.depth >= 2:  # Max 3 levels (0, 1, 2)
                    raise ValueError("Move would exceed maximum department depth")

            # Validate organization change
            if new_organization_id and new_organization_id != department.organization_id:
                org_query = select(Organization).where(Organization.id == new_organization_id)
                org_result = await self.db.execute(org_query)
                new_organization = org_result.scalar_one_or_none()

                if not new_organization:
                    raise ValueError("New organization not found")

                # Update organization
                department.organization_id = new_organization_id

            # Update the department
            department.parent_id = new_parent_id
            department.updated_by = updated_by

            # Update materialized path and depth
            await self._update_department_path(department)

            # Update paths for all sub-departments
            await self._update_subtree_paths(department_id)

            await self.db.commit()
            return True

        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to move department: {str(e)}")

    async def _would_create_circular_reference(
        self, department_id: int, new_parent_id: int
    ) -> bool:
        """Check if moving department would create circular reference."""

        # Get all descendants of the department being moved
        descendants = await self._get_all_sub_department_ids(department_id)

        # If new parent is in descendants, it would create a circular reference
        return new_parent_id in descendants

    async def _update_department_path(self, department: Department) -> None:
        """Update materialized path for a department."""
        if department.parent_id is None:
            department.path = str(department.id)
            department.depth = 0
        else:
            # Get parent path
            parent_query = select(Department.path, Department.depth).where(
                Department.id == department.parent_id
            )
            result = await self.db.execute(parent_query)
            parent_data = result.first()

            if parent_data:
                department.path = f"{parent_data.path}.{department.id}"
                department.depth = (parent_data.depth or 0) + 1
            else:
                # Fallback
                department.path = f"{department.parent_id}.{department.id}"
                department.depth = 1

    async def _update_subtree_paths(self, department_id: int) -> None:
        """Update paths for all sub-departments recursively."""
        # Get direct children
        children_query = select(Department).where(Department.parent_id == department_id)
        result = await self.db.execute(children_query)
        children = result.scalars().all()

        for child in children:
            await self._update_department_path(child)
            await self._update_subtree_paths(child.id)

    async def get_all_sub_departments(
        self, department_id: int, include_inactive: bool = False, flatten: bool = False
    ) -> List[DepartmentResponse]:
        """
        Get all sub-departments recursively.
        すべての子部門を再帰的に取得
        """
        try:
            sub_dept_ids = await self._get_all_sub_department_ids(department_id)

            if not sub_dept_ids:
                return []

            query = select(Department).where(Department.id.in_(sub_dept_ids))
            query = query.options(joinedload(Department.organization))

            if not include_inactive:
                query = query.where(Department.is_active == True)

            if flatten:
                query = query.order_by(Department.path)
            else:
                query = query.order_by(Department.depth, Department.display_order, Department.name)

            result = await self.db.execute(query)
            sub_departments = result.scalars().all()

            return [
                DepartmentResponse(
                    id=dept.id,
                    code=dept.code,
                    name=dept.name,
                    organization_id=dept.organization_id,
                    parent_id=dept.parent_id,
                    is_active=dept.is_active,
                    manager_id=dept.manager_id,
                    department_type=dept.department_type,
                    depth=dept.depth,
                    path=dept.path
                )
                for dept in sub_departments
            ]

        except Exception as e:
            raise ValueError(f"Failed to get sub-departments: {str(e)}")

    async def _get_all_sub_department_ids(self, department_id: int) -> List[int]:
        """Get all sub-department IDs recursively using CTE."""

        cte_query = text("""
            WITH RECURSIVE department_tree AS (
                SELECT id, parent_id, 1 as level
                FROM departments
                WHERE parent_id = :dept_id
                
                UNION ALL
                
                SELECT d.id, d.parent_id, dt.level + 1
                FROM departments d
                INNER JOIN department_tree dt ON d.parent_id = dt.id
                WHERE dt.level < 10  -- Prevent infinite recursion
            )
            SELECT id FROM department_tree
        """)

        result = await self.db.execute(cte_query, {"dept_id": department_id})
        return [row[0] for row in result]

    async def get_hierarchy_path(self, department_id: int) -> List[DepartmentResponse]:
        """
        Get hierarchy path from root to department.
        ルートから部門までの階層パスを取得
        """
        try:
            # Use CTE to get hierarchy path
            cte_query = text("""
                WITH RECURSIVE department_path AS (
                    SELECT id, parent_id, code, name, organization_id, is_active, 
                           manager_id, department_type, depth, path, 0 as level
                    FROM departments
                    WHERE id = :dept_id
                    
                    UNION ALL
                    
                    SELECT d.id, d.parent_id, d.code, d.name, d.organization_id, d.is_active,
                           d.manager_id, d.department_type, d.depth, d.path, dp.level + 1
                    FROM departments d
                    INNER JOIN department_path dp ON d.id = dp.parent_id
                    WHERE dp.level < 10  -- Prevent infinite recursion
                )
                SELECT * FROM department_path ORDER BY level DESC
            """)

            result = await self.db.execute(cte_query, {"dept_id": department_id})
            rows = result.fetchall()

            if not rows:
                return []

            return [
                DepartmentResponse(
                    id=row.id,
                    code=row.code,
                    name=row.name,
                    organization_id=row.organization_id,
                    parent_id=row.parent_id,
                    is_active=row.is_active,
                    manager_id=row.manager_id,
                    department_type=row.department_type,
                    depth=row.depth,
                    path=row.path
                )
                for row in rows
            ]

        except Exception as e:
            raise ValueError(f"Failed to get hierarchy path: {str(e)}")

    async def validate_hierarchy(self, department_id: int) -> Dict[str, Any]:
        """
        Validate department hierarchy integrity.
        部門階層の整合性検証
        """
        errors = []
        warnings = []
        recommendations = []

        try:
            # Check for orphaned departments
            orphan_query = text("""
                SELECT d1.id, d1.code, d1.name, d1.organization_id
                FROM departments d1
                WHERE d1.parent_id IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM departments d2 
                    WHERE d2.id = d1.parent_id AND d2.organization_id = d1.organization_id
                )
            """)

            result = await self.db.execute(orphan_query)
            orphans = result.fetchall()

            if orphans:
                errors.append({
                    "type": "orphaned_departments",
                    "message": f"Found {len(orphans)} orphaned departments",
                    "details": [{"id": o.id, "code": o.code, "name": o.name} for o in orphans]
                })

            # Check for circular references
            circular_query = text("""
                WITH RECURSIVE cycle_check AS (
                    SELECT id, parent_id, ARRAY[id] as path, false as cycle
                    FROM departments
                    WHERE parent_id IS NOT NULL
                    
                    UNION ALL
                    
                    SELECT d.id, d.parent_id, 
                           path || d.id,
                           d.id = ANY(path) as cycle
                    FROM departments d, cycle_check cc
                    WHERE d.id = cc.parent_id 
                    AND NOT cc.cycle
                    AND array_length(path, 1) < 10
                )
                SELECT id, path FROM cycle_check WHERE cycle = true
            """)

            result = await self.db.execute(circular_query)
            cycles = result.fetchall()

            if cycles:
                errors.append({
                    "type": "circular_references",
                    "message": f"Found {len(cycles)} circular references",
                    "details": [{"id": c.id, "path": c.path} for c in cycles]
                })

            # Check hierarchy depth constraints
            depth_query = text("""
                SELECT id, code, name, depth
                FROM departments
                WHERE depth > 2
                ORDER BY depth DESC
            """)

            result = await self.db.execute(depth_query)
            deep_depts = result.fetchall()

            if deep_depts:
                warnings.append({
                    "type": "exceeds_depth_limit",
                    "message": f"Found {len(deep_depts)} departments exceeding depth limit",
                    "details": [{"id": d.id, "code": d.code, "name": d.name, "depth": d.depth} for d in deep_depts]
                })

            # Check path consistency
            path_query = text("""
                SELECT d.id, d.code, d.name, d.path, d.depth
                FROM departments d
                WHERE d.parent_id IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM departments p
                    WHERE p.id = d.parent_id
                    AND d.path LIKE p.path || '.%'
                )
            """)

            result = await self.db.execute(path_query)
            inconsistent_paths = result.fetchall()

            if inconsistent_paths:
                warnings.append({
                    "type": "inconsistent_paths",
                    "message": f"Found {len(inconsistent_paths)} departments with inconsistent paths",
                    "details": [{"id": p.id, "code": p.code, "path": p.path} for p in inconsistent_paths],
                    "recommendation": "Run path update operation to fix inconsistencies"
                })

            return {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "recommendations": recommendations
            }

        except Exception as e:
            return {
                "is_valid": False,
                "errors": [{"type": "validation_error", "message": str(e)}],
                "warnings": [],
                "recommendations": []
            }

    async def bulk_update_hierarchy(
        self,
        root_department_id: int,
        updates: List[Dict[str, Any]],
        validate_before_commit: bool,
        updated_by: int,
    ) -> Dict[str, Any]:
        """
        Perform bulk updates on department hierarchy.
        部門階層の一括更新
        """
        updated_count = 0
        errors = []
        validation_results = {}

        try:
            # Validate hierarchy if requested
            if validate_before_commit:
                validation_results = await self.validate_hierarchy(root_department_id)
                if not validation_results["is_valid"]:
                    raise ValueError("Hierarchy validation failed before applying updates")

            # Apply updates
            for update in updates:
                try:
                    dept_id = update.get("department_id")
                    if not dept_id:
                        errors.append({"update": update, "error": "Missing department_id"})
                        continue

                    # Get department
                    query = select(Department).where(Department.id == dept_id)
                    result = await self.db.execute(query)
                    department = result.scalar_one_or_none()

                    if not department:
                        errors.append({"update": update, "error": "Department not found"})
                        continue

                    # Apply changes
                    for field, value in update.items():
                        if field != "department_id" and hasattr(department, field):
                            setattr(department, field, value)

                    department.updated_by = updated_by

                    # Update path if parent changed
                    if "parent_id" in update:
                        await self._update_department_path(department)
                        await self._update_subtree_paths(department.id)

                    updated_count += 1

                except Exception as e:
                    errors.append({"update": update, "error": str(e)})

            # Validate after updates if requested
            if validate_before_commit and updated_count > 0:
                post_validation = await self.validate_hierarchy(root_department_id)
                if not post_validation["is_valid"]:
                    await self.db.rollback()
                    raise ValueError("Hierarchy validation failed after applying updates")

            await self.db.commit()

            return {
                "updated_count": updated_count,
                "errors": errors,
                "validation_results": validation_results
            }

        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Bulk update failed: {str(e)}")

    async def get_department_users_recursive(
        self,
        department_id: int,
        include_sub_departments: bool = True,
        include_inactive: bool = False,
        role_filter: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get all users in department and sub-departments.
        部門およびサブ部門のすべてのユーザーを取得
        """
        try:
            # Check if department exists
            dept_query = select(Department).where(Department.id == department_id)
            result = await self.db.execute(dept_query)
            department = result.scalar_one_or_none()

            if not department:
                return None

            # Build user filter
            user_filter = [User.department_id == department_id]

            if include_sub_departments:
                sub_dept_ids = await self._get_all_sub_department_ids(department_id)
                if sub_dept_ids:
                    user_filter.append(User.department_id.in_(sub_dept_ids))

            # Build query
            user_query = select(User).where(or_(*user_filter))

            if not include_inactive:
                user_query = user_query.where(User.is_active == True)

            # Apply role filter if specified
            if role_filter:
                # This would need proper role relationship join
                pass  # Placeholder for role filtering

            user_query = user_query.order_by(User.department_id, User.full_name)

            result = await self.db.execute(user_query)
            users = result.scalars().all()

            # Group users by department
            users_by_department = {}
            for user in users:
                dept_id = user.department_id
                if dept_id not in users_by_department:
                    users_by_department[dept_id] = []

                users_by_department[dept_id].append({
                    "id": user.id,
                    "name": user.full_name,
                    "email": user.email,
                    "is_active": user.is_active,
                    "department_id": user.department_id
                })

            return {
                "department_id": department_id,
                "department_name": department.name,
                "total_users": len(users),
                "active_users": sum(1 for u in users if u.is_active),
                "users_by_department": users_by_department,
                "include_sub_departments": include_sub_departments
            }

        except Exception as e:
            raise ValueError(f"Failed to get department users: {str(e)}")

    async def update_materialized_paths(
        self, department_id: int, recursive: bool = True
    ) -> Dict[str, Any]:
        """
        Update materialized paths for department hierarchy.
        部門階層のマテリアライズドパス更新
        """
        updated_count = 0
        errors = []

        try:
            # Get the department
            query = select(Department).where(Department.id == department_id)
            result = await self.db.execute(query)
            department = result.scalar_one_or_none()

            if not department:
                raise ValueError("Department not found")

            # Update the department's path
            await self._update_department_path(department)
            updated_count += 1

            # Update sub-departments if recursive
            if recursive:
                await self._update_subtree_paths(department_id)

                # Count updated sub-departments
                sub_dept_ids = await self._get_all_sub_department_ids(department_id)
                updated_count += len(sub_dept_ids)

            await self.db.commit()

            return {
                "updated_count": updated_count,
                "errors": errors
            }

        except Exception as e:
            await self.db.rollback()
            return {
                "updated_count": 0,
                "errors": [{"error": str(e)}]
            }

    async def advanced_search(
        self,
        query: str,
        organization_id: Optional[int],
        search_fields: List[str],
        filters: Dict[str, Any],
        sort_by: str,
        sort_order: str,
        limit: int,
        offset: int,
    ) -> Dict[str, Any]:
        """
        Advanced department search with multiple criteria.
        高度な部門検索（複数条件対応）
        """
        try:
            # Build base query
            base_query = select(Department)
            base_query = base_query.options(joinedload(Department.organization))

            # Add organization filter
            if organization_id:
                base_query = base_query.where(Department.organization_id == organization_id)

            # Add search conditions
            search_conditions = []
            for field in search_fields:
                if hasattr(Department, field):
                    attr = getattr(Department, field)
                    if hasattr(attr.property, 'columns'):
                        search_conditions.append(attr.ilike(f"%{query}%"))

            if search_conditions:
                base_query = base_query.where(or_(*search_conditions))

            # Add filters
            for field, value in filters.items():
                if hasattr(Department, field):
                    attr = getattr(Department, field)
                    if isinstance(value, list):
                        base_query = base_query.where(attr.in_(value))
                    else:
                        base_query = base_query.where(attr == value)

            # Add sorting
            if hasattr(Department, sort_by):
                sort_attr = getattr(Department, sort_by)
                if sort_order.lower() == "desc":
                    base_query = base_query.order_by(sort_attr.desc())
                else:
                    base_query = base_query.order_by(sort_attr)

            # Get total count
            count_query = select(func.count()).select_from(base_query.subquery())
            count_result = await self.db.execute(count_query)
            total_count = count_result.scalar()

            # Apply pagination
            paginated_query = base_query.offset(offset).limit(limit)

            # Execute query
            result = await self.db.execute(paginated_query)
            departments = result.scalars().all()

            # Convert to response format
            dept_list = [
                DepartmentResponse(
                    id=dept.id,
                    code=dept.code,
                    name=dept.name,
                    organization_id=dept.organization_id,
                    parent_id=dept.parent_id,
                    is_active=dept.is_active,
                    manager_id=dept.manager_id,
                    department_type=dept.department_type,
                    depth=dept.depth,
                    path=dept.path
                )
                for dept in departments
            ]

            return {
                "departments": dept_list,
                "total_count": total_count
            }

        except Exception as e:
            raise ValueError(f"Search failed: {str(e)}")

    async def get_performance_metrics(
        self,
        department_id: int,
        include_sub_departments: bool = False,
        metric_types: List[str] = None,
        date_range_days: int = 30,
    ) -> Optional[Dict[str, Any]]:
        """
        Get department performance metrics and KPIs.
        部門パフォーマンス指標とKPIの取得
        """
        if metric_types is None:
            metric_types = ["headcount", "budget", "tasks"]

        try:
            # Check if department exists
            dept_query = select(Department).where(Department.id == department_id)
            result = await self.db.execute(dept_query)
            department = result.scalar_one_or_none()

            if not department:
                return None

            metrics = {
                "department_id": department_id,
                "department_name": department.name,
                "organization_id": department.organization_id,
                "calculation_date": datetime.utcnow().isoformat(),
                "date_range_days": date_range_days,
                "metrics": {}
            }

            # Calculate headcount metrics
            if "headcount" in metric_types:
                headcount_data = await self._calculate_headcount_metrics(
                    department_id, include_sub_departments
                )
                metrics["metrics"]["headcount"] = headcount_data

            # Calculate budget metrics
            if "budget" in metric_types:
                budget_data = await self._calculate_budget_metrics(
                    department_id, include_sub_departments, date_range_days
                )
                metrics["metrics"]["budget"] = budget_data

            # Calculate task metrics (if task system is integrated)
            if "tasks" in metric_types:
                task_data = await self._calculate_task_metrics(
                    department_id, include_sub_departments, date_range_days
                )
                metrics["metrics"]["tasks"] = task_data

            return metrics

        except Exception as e:
            raise ValueError(f"Failed to get performance metrics: {str(e)}")

    async def _calculate_headcount_metrics(
        self, department_id: int, include_sub_departments: bool
    ) -> Dict[str, Any]:
        """Calculate headcount-related metrics."""

        user_filter = [User.department_id == department_id]

        if include_sub_departments:
            sub_dept_ids = await self._get_all_sub_department_ids(department_id)
            if sub_dept_ids:
                user_filter.append(User.department_id.in_(sub_dept_ids))

        # Get headcount statistics
        headcount_query = select(
            func.count(User.id).label("total"),
            func.count(User.id).filter(User.is_active == True).label("active"),
            func.count(User.id).filter(User.is_active == False).label("inactive")
        ).where(or_(*user_filter))

        result = await self.db.execute(headcount_query)
        headcount_stats = result.first()

        # Get department headcount limit
        dept_query = select(Department.headcount_limit).where(Department.id == department_id)
        result = await self.db.execute(dept_query)
        headcount_limit = result.scalar()

        utilization = 0.0
        if headcount_limit and headcount_limit > 0:
            utilization = (headcount_stats.active / headcount_limit) * 100

        return {
            "total_headcount": headcount_stats.total or 0,
            "active_headcount": headcount_stats.active or 0,
            "inactive_headcount": headcount_stats.inactive or 0,
            "headcount_limit": headcount_limit,
            "utilization_percentage": round(utilization, 2)
        }

    async def _calculate_budget_metrics(
        self, department_id: int, include_sub_departments: bool, date_range_days: int
    ) -> Dict[str, Any]:
        """Calculate budget-related metrics."""

        # Get department budget
        dept_query = select(Department.budget).where(Department.id == department_id)
        result = await self.db.execute(dept_query)
        budget = result.scalar()

        # Placeholder for expense calculation
        # In a real implementation, this would query expense/transaction tables
        expenses = 0.0  # Would calculate from expense records

        utilization = 0.0
        if budget and budget > 0:
            utilization = (expenses / budget) * 100

        return {
            "allocated_budget": budget or 0,
            "expenses_to_date": expenses,
            "remaining_budget": (budget or 0) - expenses,
            "utilization_percentage": round(utilization, 2),
            "date_range_days": date_range_days
        }

    async def _calculate_task_metrics(
        self, department_id: int, include_sub_departments: bool, date_range_days: int
    ) -> Dict[str, Any]:
        """Calculate task-related metrics."""

        # Placeholder for task metrics
        # In a real implementation, this would query task tables
        return {
            "total_tasks": 0,
            "completed_tasks": 0,
            "in_progress_tasks": 0,
            "overdue_tasks": 0,
            "completion_rate": 0.0,
            "average_completion_time": 0.0,
            "date_range_days": date_range_days
        }
