"""
Enhanced Organization Service for Issue #42.
拡張組織管理サービス（Issue #42 - 組織・部門管理API実装と階層構造サポート）
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.department import Department
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import (
    OrganizationResponse,
    OrganizationTree,
    OrganizationWithStats,
)


class EnhancedOrganizationService:
    """Enhanced service for organization management with hierarchical support."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_organization_tree(
        self,
        organization_id: int,
        include_departments: bool = True,
        include_users: bool = False,
        max_depth: int = 10,
    ) -> Optional[OrganizationTree]:
        """
        Get hierarchical organization tree structure.
        階層的な組織ツリー構造を取得
        """
        try:
            # Build query with appropriate joins
            query = select(Organization).where(Organization.id == organization_id)
            
            if include_departments:
                query = query.options(selectinload(Organization.departments))
            
            if include_users:
                query = query.options(selectinload(Organization.users))
            
            result = await self.db.execute(query)
            organization = result.scalar_one_or_none()
            
            if not organization:
                return None
            
            # Recursively build tree structure
            return await self._build_organization_tree_node(
                organization, include_departments, include_users, max_depth, 0
            )
            
        except Exception as e:
            raise ValueError(f"Failed to get organization tree: {str(e)}")

    async def _build_organization_tree_node(
        self,
        organization: Organization,
        include_departments: bool,
        include_users: bool,
        max_depth: int,
        current_depth: int,
    ) -> OrganizationTree:
        """Build a single tree node with children."""
        
        # Get subsidiaries
        subsidiaries = []
        if current_depth < max_depth:
            sub_query = select(Organization).where(
                Organization.parent_id == organization.id
            ).order_by(Organization.name)
            
            if include_departments:
                sub_query = sub_query.options(selectinload(Organization.departments))
            if include_users:
                sub_query = sub_query.options(selectinload(Organization.users))
            
            result = await self.db.execute(sub_query)
            sub_orgs = result.scalars().all()
            
            for sub_org in sub_orgs:
                sub_tree = await self._build_organization_tree_node(
                    sub_org, include_departments, include_users, max_depth, current_depth + 1
                )
                subsidiaries.append(sub_tree)
        
        # Get departments if requested
        departments = []
        if include_departments:
            dept_query = select(Department).where(
                Department.organization_id == organization.id,
                Department.parent_id.is_(None)  # Only root departments
            ).order_by(Department.display_order, Department.name)
            
            if include_users:
                dept_query = dept_query.options(selectinload(Department.users))
            
            result = await self.db.execute(dept_query)
            root_departments = result.scalars().all()
            
            for dept in root_departments:
                dept_tree = await self._build_department_tree_node(dept, include_users, 3, 0)
                departments.append(dept_tree)
        
        # Get direct users if requested
        users = []
        if include_users:
            user_query = select(User).where(
                User.organization_id == organization.id,
                User.is_active == True
            ).order_by(User.full_name)
            
            result = await self.db.execute(user_query)
            user_list = result.scalars().all()
            users = [{"id": u.id, "name": u.full_name, "email": u.email} for u in user_list]
        
        return OrganizationTree(
            id=organization.id,
            code=organization.code,
            name=organization.name,
            parent_id=organization.parent_id,
            is_active=organization.is_active,
            subsidiaries=subsidiaries,
            departments=departments,
            users=users,
            depth=current_depth
        )

    async def _build_department_tree_node(
        self, department: Department, include_users: bool, max_depth: int, current_depth: int
    ) -> Dict[str, Any]:
        """Build department tree node."""
        
        # Get sub-departments
        sub_departments = []
        if current_depth < max_depth:
            sub_query = select(Department).where(
                Department.parent_id == department.id
            ).order_by(Department.display_order, Department.name)
            
            if include_users:
                sub_query = sub_query.options(selectinload(Department.users))
            
            result = await self.db.execute(sub_query)
            sub_depts = result.scalars().all()
            
            for sub_dept in sub_depts:
                sub_tree = await self._build_department_tree_node(
                    sub_dept, include_users, max_depth, current_depth + 1
                )
                sub_departments.append(sub_tree)
        
        # Get users if requested
        users = []
        if include_users:
            user_query = select(User).where(
                User.department_id == department.id,
                User.is_active == True
            ).order_by(User.full_name)
            
            result = await self.db.execute(user_query)
            user_list = result.scalars().all()
            users = [{"id": u.id, "name": u.full_name, "email": u.email} for u in user_list]
        
        return {
            "id": department.id,
            "code": department.code,
            "name": department.name,
            "parent_id": department.parent_id,
            "is_active": department.is_active,
            "manager_id": department.manager_id,
            "sub_departments": sub_departments,
            "users": users,
            "depth": current_depth
        }

    async def get_organization_with_stats(
        self, organization_id: int, include_subsidiaries: bool = False
    ) -> Optional[OrganizationWithStats]:
        """
        Get organization with comprehensive statistics.
        組織の包括的統計情報を取得
        """
        try:
            # Get organization
            query = select(Organization).where(Organization.id == organization_id)
            result = await self.db.execute(query)
            organization = result.scalar_one_or_none()
            
            if not organization:
                return None
            
            # Calculate statistics
            stats = await self._calculate_organization_stats(organization_id, include_subsidiaries)
            
            return OrganizationWithStats(
                id=organization.id,
                code=organization.code,
                name=organization.name,
                name_en=organization.name_en,
                parent_id=organization.parent_id,
                is_active=organization.is_active,
                industry=organization.industry,
                business_type=organization.business_type,
                employee_count=organization.employee_count,
                capital=organization.capital,
                statistics=stats
            )
            
        except Exception as e:
            raise ValueError(f"Failed to get organization statistics: {str(e)}")

    async def _calculate_organization_stats(
        self, organization_id: int, include_subsidiaries: bool
    ) -> Dict[str, Any]:
        """Calculate comprehensive organization statistics."""
        
        stats = {
            "total_users": 0,
            "active_users": 0,
            "total_departments": 0,
            "active_departments": 0,
            "total_subsidiaries": 0,
            "active_subsidiaries": 0,
            "department_levels": 0,
            "user_distribution": {},
            "department_distribution": {}
        }
        
        try:
            org_filter = [Organization.id == organization_id]
            dept_filter = [Department.organization_id == organization_id]
            user_filter = [User.organization_id == organization_id]
            
            if include_subsidiaries:
                # Get all subsidiary IDs
                subsidiary_ids = await self._get_all_subsidiary_ids(organization_id)
                if subsidiary_ids:
                    org_filter.append(Organization.id.in_(subsidiary_ids))
                    dept_filter.append(Department.organization_id.in_(subsidiary_ids))
                    user_filter.append(User.organization_id.in_(subsidiary_ids))
            
            # User statistics
            user_query = select(
                func.count(User.id).label("total"),
                func.count(User.id).filter(User.is_active == True).label("active")
            ).where(or_(*user_filter))
            
            result = await self.db.execute(user_query)
            user_stats = result.first()
            
            stats["total_users"] = user_stats.total or 0
            stats["active_users"] = user_stats.active or 0
            
            # Department statistics
            dept_query = select(
                func.count(Department.id).label("total"),
                func.count(Department.id).filter(Department.is_active == True).label("active"),
                func.max(Department.depth).label("max_depth")
            ).where(or_(*dept_filter))
            
            result = await self.db.execute(dept_query)
            dept_stats = result.first()
            
            stats["total_departments"] = dept_stats.total or 0
            stats["active_departments"] = dept_stats.active or 0
            stats["department_levels"] = (dept_stats.max_depth or 0) + 1
            
            # Subsidiary statistics
            if include_subsidiaries:
                sub_query = select(
                    func.count(Organization.id).label("total"),
                    func.count(Organization.id).filter(Organization.is_active == True).label("active")
                ).where(Organization.parent_id == organization_id)
                
                result = await self.db.execute(sub_query)
                sub_stats = result.first()
                
                stats["total_subsidiaries"] = sub_stats.total or 0
                stats["active_subsidiaries"] = sub_stats.active or 0
            
            # User distribution by department
            user_dist_query = select(
                Department.name.label("department_name"),
                func.count(User.id).label("user_count")
            ).select_from(
                Department
            ).outerjoin(
                User, User.department_id == Department.id
            ).where(
                or_(*dept_filter),
                User.is_active == True
            ).group_by(Department.id, Department.name)
            
            result = await self.db.execute(user_dist_query)
            for row in result:
                stats["user_distribution"][row.department_name] = row.user_count
            
            # Department distribution by type
            dept_dist_query = select(
                Department.department_type.label("dept_type"),
                func.count(Department.id).label("dept_count")
            ).where(
                or_(*dept_filter),
                Department.is_active == True,
                Department.department_type.isnot(None)
            ).group_by(Department.department_type)
            
            result = await self.db.execute(dept_dist_query)
            for row in result:
                stats["department_distribution"][row.dept_type or "Other"] = row.dept_count
            
            return stats
            
        except Exception as e:
            raise ValueError(f"Failed to calculate statistics: {str(e)}")

    async def move_organization(
        self, organization_id: int, new_parent_id: Optional[int], updated_by: int
    ) -> bool:
        """
        Move organization to a different parent.
        組織の親組織変更
        """
        try:
            # Get the organization to move
            query = select(Organization).where(Organization.id == organization_id)
            result = await self.db.execute(query)
            organization = result.scalar_one_or_none()
            
            if not organization:
                raise ValueError("Organization not found")
            
            # Validate the move
            if new_parent_id:
                # Check if new parent exists
                parent_query = select(Organization).where(Organization.id == new_parent_id)
                parent_result = await self.db.execute(parent_query)
                new_parent = parent_result.scalar_one_or_none()
                
                if not new_parent:
                    raise ValueError("New parent organization not found")
                
                # Check for circular reference
                if await self._would_create_circular_reference(organization_id, new_parent_id):
                    raise ValueError("Move would create circular reference")
            
            # Update the organization
            organization.parent_id = new_parent_id
            organization.updated_by = updated_by
            
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to move organization: {str(e)}")

    async def _would_create_circular_reference(
        self, organization_id: int, new_parent_id: int
    ) -> bool:
        """Check if moving organization would create circular reference."""
        
        # Get all descendants of the organization being moved
        descendants = await self._get_all_subsidiary_ids(organization_id)
        
        # If new parent is in descendants, it would create a circular reference
        return new_parent_id in descendants

    async def get_all_subsidiaries(
        self, organization_id: int, include_inactive: bool = False
    ) -> List[OrganizationResponse]:
        """
        Get all subsidiaries recursively.
        すべての子会社を再帰的に取得
        """
        try:
            subsidiary_ids = await self._get_all_subsidiary_ids(organization_id)
            
            if not subsidiary_ids:
                return []
            
            query = select(Organization).where(Organization.id.in_(subsidiary_ids))
            
            if not include_inactive:
                query = query.where(Organization.is_active == True)
            
            query = query.order_by(Organization.name)
            
            result = await self.db.execute(query)
            subsidiaries = result.scalars().all()
            
            return [
                OrganizationResponse(
                    id=org.id,
                    code=org.code,
                    name=org.name,
                    name_en=org.name_en,
                    parent_id=org.parent_id,
                    is_active=org.is_active,
                    industry=org.industry,
                    business_type=org.business_type,
                    employee_count=org.employee_count
                )
                for org in subsidiaries
            ]
            
        except Exception as e:
            raise ValueError(f"Failed to get subsidiaries: {str(e)}")

    async def _get_all_subsidiary_ids(self, organization_id: int) -> List[int]:
        """Get all subsidiary IDs recursively using CTE."""
        
        cte_query = text("""
            WITH RECURSIVE organization_tree AS (
                SELECT id, parent_id, 1 as level
                FROM organizations
                WHERE parent_id = :org_id
                
                UNION ALL
                
                SELECT o.id, o.parent_id, ot.level + 1
                FROM organizations o
                INNER JOIN organization_tree ot ON o.parent_id = ot.id
                WHERE ot.level < 10  -- Prevent infinite recursion
            )
            SELECT id FROM organization_tree
        """)
        
        result = await self.db.execute(cte_query, {"org_id": organization_id})
        return [row[0] for row in result]

    async def get_hierarchy_path(self, organization_id: int) -> List[OrganizationResponse]:
        """
        Get hierarchy path from root to organization.
        ルートから組織までの階層パスを取得
        """
        try:
            # Use CTE to get hierarchy path
            cte_query = text("""
                WITH RECURSIVE organization_path AS (
                    SELECT id, parent_id, code, name, name_en, is_active, 
                           industry, business_type, employee_count, 0 as level
                    FROM organizations
                    WHERE id = :org_id
                    
                    UNION ALL
                    
                    SELECT o.id, o.parent_id, o.code, o.name, o.name_en, o.is_active,
                           o.industry, o.business_type, o.employee_count, op.level + 1
                    FROM organizations o
                    INNER JOIN organization_path op ON o.id = op.parent_id
                    WHERE op.level < 10  -- Prevent infinite recursion
                )
                SELECT * FROM organization_path ORDER BY level DESC
            """)
            
            result = await self.db.execute(cte_query, {"org_id": organization_id})
            rows = result.fetchall()
            
            if not rows:
                return []
            
            return [
                OrganizationResponse(
                    id=row.id,
                    code=row.code,
                    name=row.name,
                    name_en=row.name_en,
                    parent_id=row.parent_id,
                    is_active=row.is_active,
                    industry=row.industry,
                    business_type=row.business_type,
                    employee_count=row.employee_count
                )
                for row in rows
            ]
            
        except Exception as e:
            raise ValueError(f"Failed to get hierarchy path: {str(e)}")

    async def validate_hierarchy(self, organization_id: int) -> Dict[str, Any]:
        """
        Validate organization hierarchy integrity.
        組織階層の整合性検証
        """
        errors = []
        warnings = []
        recommendations = []
        
        try:
            # Check for orphaned organizations
            orphan_query = text("""
                SELECT o1.id, o1.code, o1.name
                FROM organizations o1
                WHERE o1.parent_id IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM organizations o2 
                    WHERE o2.id = o1.parent_id
                )
            """)
            
            result = await self.db.execute(orphan_query)
            orphans = result.fetchall()
            
            if orphans:
                errors.append({
                    "type": "orphaned_organizations",
                    "message": f"Found {len(orphans)} orphaned organizations",
                    "details": [{"id": o.id, "code": o.code, "name": o.name} for o in orphans]
                })
            
            # Check for circular references
            circular_query = text("""
                WITH RECURSIVE cycle_check AS (
                    SELECT id, parent_id, ARRAY[id] as path, false as cycle
                    FROM organizations
                    WHERE parent_id IS NOT NULL
                    
                    UNION ALL
                    
                    SELECT o.id, o.parent_id, 
                           path || o.id,
                           o.id = ANY(path) as cycle
                    FROM organizations o, cycle_check cc
                    WHERE o.id = cc.parent_id 
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
            
            # Check hierarchy depth
            depth_query = text("""
                WITH RECURSIVE org_depth AS (
                    SELECT id, parent_id, 0 as depth
                    FROM organizations
                    WHERE parent_id IS NULL
                    
                    UNION ALL
                    
                    SELECT o.id, o.parent_id, od.depth + 1
                    FROM organizations o
                    INNER JOIN org_depth od ON o.parent_id = od.id
                    WHERE od.depth < 20
                )
                SELECT MAX(depth) as max_depth FROM org_depth
            """)
            
            result = await self.db.execute(depth_query)
            max_depth = result.scalar()
            
            if max_depth and max_depth > 5:
                warnings.append({
                    "type": "deep_hierarchy",
                    "message": f"Organization hierarchy is {max_depth} levels deep",
                    "recommendation": "Consider flattening the hierarchy for better management"
                })
            
            # Check for inactive parent organizations with active children
            inactive_parent_query = text("""
                SELECT p.id, p.code, p.name, COUNT(c.id) as active_children
                FROM organizations p
                INNER JOIN organizations c ON c.parent_id = p.id
                WHERE p.is_active = false AND c.is_active = true
                GROUP BY p.id, p.code, p.name
            """)
            
            result = await self.db.execute(inactive_parent_query)
            inactive_parents = result.fetchall()
            
            if inactive_parents:
                warnings.append({
                    "type": "inactive_parent_with_active_children",
                    "message": f"Found {len(inactive_parents)} inactive parents with active children",
                    "details": [
                        {"id": p.id, "code": p.code, "name": p.name, "active_children": p.active_children}
                        for p in inactive_parents
                    ]
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
        root_organization_id: int,
        updates: List[Dict[str, Any]],
        validate_before_commit: bool,
        updated_by: int,
    ) -> Dict[str, Any]:
        """
        Perform bulk updates on organization hierarchy.
        組織階層の一括更新
        """
        updated_count = 0
        errors = []
        validation_results = {}
        
        try:
            # Validate updates if requested
            if validate_before_commit:
                validation_results = await self.validate_hierarchy(root_organization_id)
                if not validation_results["is_valid"]:
                    raise ValueError("Hierarchy validation failed before applying updates")
            
            # Apply updates
            for update in updates:
                try:
                    org_id = update.get("organization_id")
                    if not org_id:
                        errors.append({"update": update, "error": "Missing organization_id"})
                        continue
                    
                    # Get organization
                    query = select(Organization).where(Organization.id == org_id)
                    result = await self.db.execute(query)
                    organization = result.scalar_one_or_none()
                    
                    if not organization:
                        errors.append({"update": update, "error": "Organization not found"})
                        continue
                    
                    # Apply changes
                    for field, value in update.items():
                        if field != "organization_id" and hasattr(organization, field):
                            setattr(organization, field, value)
                    
                    organization.updated_by = updated_by
                    updated_count += 1
                    
                except Exception as e:
                    errors.append({"update": update, "error": str(e)})
            
            # Validate after updates if requested
            if validate_before_commit and updated_count > 0:
                post_validation = await self.validate_hierarchy(root_organization_id)
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

    async def get_organization_department_tree(
        self,
        organization_id: int,
        include_users: bool = False,
        include_inactive: bool = False,
        max_depth: int = 5,
    ) -> Optional[Dict[str, Any]]:
        """
        Get complete department tree for an organization.
        組織の部門ツリー構造を取得
        """
        try:
            # Get organization
            org_query = select(Organization).where(Organization.id == organization_id)
            result = await self.db.execute(org_query)
            organization = result.scalar_one_or_none()
            
            if not organization:
                return None
            
            # Get root departments
            dept_query = select(Department).where(
                Department.organization_id == organization_id,
                Department.parent_id.is_(None)
            )
            
            if not include_inactive:
                dept_query = dept_query.where(Department.is_active == True)
            
            dept_query = dept_query.order_by(Department.display_order, Department.name)
            
            result = await self.db.execute(dept_query)
            root_departments = result.scalars().all()
            
            # Build department tree
            department_tree = []
            for dept in root_departments:
                dept_node = await self._build_department_tree_node(dept, include_users, max_depth, 0)
                department_tree.append(dept_node)
            
            return {
                "organization": {
                    "id": organization.id,
                    "code": organization.code,
                    "name": organization.name,
                    "is_active": organization.is_active
                },
                "departments": department_tree,
                "total_departments": len(root_departments),
                "max_depth": max_depth
            }
            
        except Exception as e:
            raise ValueError(f"Failed to get department tree: {str(e)}")

    async def advanced_search(
        self,
        query: str,
        search_fields: List[str],
        filters: Dict[str, Any],
        sort_by: str,
        sort_order: str,
        limit: int,
        offset: int,
    ) -> Dict[str, Any]:
        """
        Advanced organization search with multiple criteria.
        高度な組織検索（複数条件対応）
        """
        try:
            # Build base query
            base_query = select(Organization)
            
            # Add search conditions
            search_conditions = []
            for field in search_fields:
                if hasattr(Organization, field):
                    attr = getattr(Organization, field)
                    if hasattr(attr.property, 'columns'):
                        search_conditions.append(attr.ilike(f"%{query}%"))
            
            if search_conditions:
                base_query = base_query.where(or_(*search_conditions))
            
            # Add filters
            for field, value in filters.items():
                if hasattr(Organization, field):
                    attr = getattr(Organization, field)
                    if isinstance(value, list):
                        base_query = base_query.where(attr.in_(value))
                    else:
                        base_query = base_query.where(attr == value)
            
            # Add sorting
            if hasattr(Organization, sort_by):
                sort_attr = getattr(Organization, sort_by)
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
            organizations = result.scalars().all()
            
            # Convert to response format
            org_list = [
                OrganizationResponse(
                    id=org.id,
                    code=org.code,
                    name=org.name,
                    name_en=org.name_en,
                    parent_id=org.parent_id,
                    is_active=org.is_active,
                    industry=org.industry,
                    business_type=org.business_type,
                    employee_count=org.employee_count
                )
                for org in organizations
            ]
            
            return {
                "organizations": org_list,
                "total_count": total_count
            }
            
        except Exception as e:
            raise ValueError(f"Search failed: {str(e)}")