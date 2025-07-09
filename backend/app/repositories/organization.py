"""Organization repository implementation."""

from typing import Any, Dict, List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload

from app.models.organization import Organization
from app.repositories.base import BaseRepository
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.types import OrganizationId


class OrganizationRepository(
    BaseRepository[Organization, OrganizationCreate, OrganizationUpdate]
):
    """Repository for organization operations."""

    def get_by_code(self, code: str) -> Optional[Organization]:
        """Get organization by code."""
        return self.db.scalar(select(self.model).where(self.model.code == code))

    def get_active(self, skip: int = 0, limit: int = 100) -> List[Organization]:
        """Get active organizations."""
        return list(
            self.db.scalars(
                select(self.model)
                .where(self.model.is_active)
                .where(~self.model.is_deleted)
                .offset(skip)
                .limit(limit)
            )
        )

    def get_with_parent(self, id: int) -> Optional[Organization]:
        """Get organization with parent loaded."""
        return self.db.scalar(
            select(self.model)
            .options(joinedload(self.model.parent))
            .where(self.model.id == id)
        )

    def get_subsidiaries(self, parent_id: OrganizationId) -> List[Organization]:
        """Get direct subsidiaries of an organization."""
        return list(
            self.db.scalars(
                select(self.model)
                .where(self.model.parent_id == parent_id)
                .where(~self.model.is_deleted)
                .order_by(self.model.name)
            )
        )

    def get_all_subsidiaries(self, parent_id: OrganizationId) -> List[Organization]:
        """Get all subsidiaries recursively."""
        # Use a simpler recursive approach
        result = []

        def get_children(pid: OrganizationId) -> None:
            children = self.get_subsidiaries(pid)
            for child in children:
                result.append(child)
                get_children(child.id)

        get_children(parent_id)
        return result

    def get_root_organizations(self) -> List[Organization]:
        """Get organizations without parent (root level)."""
        return list(
            self.db.scalars(
                select(self.model)
                .where(self.model.parent_id.is_(None))
                .where(~self.model.is_deleted)
                .order_by(self.model.name)
            )
        )

    def search_by_name(self, query: str) -> List[Organization]:
        """Search organizations by name (including kana and English)."""
        search_term = f"%{query}%"
        return list(
            self.db.scalars(
                select(self.model)
                .where(
                    or_(
                        self.model.name.ilike(search_term),
                        self.model.name_kana.ilike(search_term),
                        self.model.name_en.ilike(search_term),
                        self.model.code.ilike(search_term),
                    )
                )
                .where(~self.model.is_deleted)
                .order_by(self.model.name)
            )
        )

    def get_by_industry(self, industry: str) -> List[Organization]:
        """Get organizations by industry."""
        return list(
            self.db.scalars(
                select(self.model)
                .where(self.model.industry == industry)
                .where(~self.model.is_deleted)
                .order_by(self.model.name)
            )
        )

    def get_department_count(self, org_id: OrganizationId) -> int:
        """Get count of departments in organization."""
        from app.models.department import Department

        return (
            self.db.scalar(
                select(func.count(Department.id))
                .where(Department.organization_id == org_id)
                .where(~Department.is_deleted)
            )
            or 0
        )

    def get_user_count(self, org_id: OrganizationId) -> int:
        """Get count of users in organization."""
        from app.models.role import UserRole

        return (
            self.db.scalar(
                select(func.count(func.distinct(UserRole.user_id)))
                .where(UserRole.organization_id == org_id)
                .where(UserRole.is_active)
            )
            or 0
        )

    def validate_unique_code(self, code: str, exclude_id: Optional[int] = None) -> bool:
        """Validate if organization code is unique."""
        query = select(func.count(self.model.id)).where(self.model.code == code)
        if exclude_id:
            query = query.where(self.model.id != exclude_id)
        count = self.db.scalar(query) or 0
        return count == 0

    def update_settings(
        self, id: int, settings: Dict[str, Any]
    ) -> Optional[Organization]:
        """Update organization settings."""
        org = self.get(id)
        if org:
            org.settings = settings  # Now directly assigns dict, thanks to JSON column type
            self.db.commit()
            self.db.refresh(org)
        return org

    def get_by_tenant_id(self, tenant_id: str) -> List[Organization]:
        """Get organizations by tenant ID from settings."""
        return list(
            self.db.scalars(
                select(self.model)
                .where(self.model.settings.op('->>')('tenant_id') == tenant_id)
                .where(~self.model.is_deleted)
                .order_by(self.model.name)
            )
        )

    def get_hierarchy_path(self, org_id: OrganizationId) -> List[Organization]:
        """Get full hierarchy path from root to organization."""
        path: List[Organization] = []
        current_org = self.get(org_id)

        while current_org:
            path.insert(0, current_org)  # Insert at beginning to build path from root
            if current_org.parent_id:
                current_org = self.get(current_org.parent_id)
            else:
                break

        return path

    def get_organization_depth(self, org_id: OrganizationId) -> int:
        """Get organization depth in hierarchy (root = 0)."""
        return len(self.get_hierarchy_path(org_id)) - 1

    def get_max_hierarchy_depth(self) -> int:
        """Get maximum hierarchy depth in the system."""
        # Use recursive CTE to calculate depth efficiently
        from sqlalchemy import text

        result = self.db.execute(text("""
            WITH RECURSIVE org_hierarchy AS (
                -- Base case: root organizations (depth 0)
                SELECT id, parent_id, 0 as depth
                FROM organizations 
                WHERE parent_id IS NULL AND is_deleted = false
                
                UNION ALL
                
                -- Recursive case: children organizations
                SELECT o.id, o.parent_id, h.depth + 1
                FROM organizations o
                INNER JOIN org_hierarchy h ON o.parent_id = h.id
                WHERE o.is_deleted = false
            )
            SELECT COALESCE(MAX(depth), 0) as max_depth FROM org_hierarchy
        """)).scalar()

        return result or 0

    def bulk_update_status(self, org_ids: List[int], is_active: bool) -> int:
        """Bulk update organization status."""
        from sqlalchemy import update

        result = self.db.execute(
            update(self.model)
            .where(self.model.id.in_(org_ids))
            .where(~self.model.is_deleted)
            .values(is_active=is_active)
        )
        self.db.commit()
        return result.rowcount

    def get_organizations_by_criteria(
        self,
        tenant_id: Optional[str] = None,
        industry: Optional[str] = None,
        is_active: Optional[bool] = None,
        has_subsidiaries: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Organization]:
        """Get organizations by multiple criteria with tenant isolation."""
        query = select(self.model).where(~self.model.is_deleted)

        if tenant_id:
            query = query.where(
                self.model.settings.op('->>')('tenant_id') == tenant_id
            )

        if industry:
            query = query.where(self.model.industry == industry)

        if is_active is not None:
            query = query.where(self.model.is_active == is_active)

        if has_subsidiaries is not None:
            if has_subsidiaries:
                # Organizations that have subsidiaries
                subquery = select(self.model.id).where(
                    self.model.parent_id.isnot(None)
                ).where(~self.model.is_deleted).distinct()
                query = query.where(self.model.id.in_(subquery))
            else:
                # Organizations that don't have subsidiaries
                subquery = select(self.model.id).where(
                    self.model.parent_id.isnot(None)
                ).where(~self.model.is_deleted)
                query = query.where(~self.model.id.in_(subquery))

        return list(
            self.db.scalars(
                query.order_by(self.model.name).offset(skip).limit(limit)
            )
        )

    def get_subsidiary_tree(self, parent_id: OrganizationId) -> Dict[str, Any]:
        """Get complete subsidiary tree as nested structure."""
        def build_tree(org_id: OrganizationId) -> Dict[str, Any]:
            org = self.get(org_id)
            if not org:
                return {}

            children = self.get_subsidiaries(org_id)
            return {
                "id": org.id,
                "code": org.code,
                "name": org.name,
                "is_active": org.is_active,
                "children": [build_tree(child.id) for child in children]
            }

        return build_tree(parent_id)

    def validate_parent_assignment(
        self, org_id: OrganizationId, new_parent_id: OrganizationId
    ) -> bool:
        """Validate if parent assignment would create circular reference."""
        if org_id == new_parent_id:
            return False

        # Check if new_parent_id is already a descendant of org_id
        descendants = self.get_all_subsidiaries(org_id)
        descendant_ids = [desc.id for desc in descendants]

        return new_parent_id not in descendant_ids

    def get_organizations_requiring_attention(self) -> List[Organization]:
        """Get organizations that may need attention (inactive with active children, etc.)."""
        # Organizations that are inactive but have active subsidiaries
        inactive_orgs = list(
            self.db.scalars(
                select(self.model)
                .where(~self.model.is_active)
                .where(~self.model.is_deleted)
            )
        )

        result = []
        for org in inactive_orgs:
            active_children = [
                child for child in self.get_subsidiaries(org.id)
                if child.is_active
            ]
            if active_children:
                result.append(org)

        return result
