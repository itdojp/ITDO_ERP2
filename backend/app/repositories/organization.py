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

        # Use a simple recursive approach for now to avoid complex CTE issues
        def get_children_recursive(org_id: int) -> List[Organization]:
            direct_children = list(
                self.db.scalars(
                    select(self.model)
                    .where(self.model.parent_id == org_id)
                    .where(~self.model.is_deleted)
                )
            )
            all_children = direct_children.copy()

            for child in direct_children:
                all_children.extend(get_children_recursive(child.id))

            return all_children

        return get_children_recursive(parent_id)

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
        import json

        org = self.get(id)
        if org:
            org.settings = json.dumps(settings)
            self.db.commit()
            self.db.refresh(org)
        return org
