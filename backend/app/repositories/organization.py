"""Organization repository implementation."""

import json
from typing import Any

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

    def get_by_code(self, code: str) -> Organization | None:
        """Get organization by code."""
        return self.db.scalar(select(self.model).where(self.model.code == code))

    def get_active(self, skip: int = 0, limit: int = 100) -> list[Organization]:
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

    def get_with_parent(self, id: int) -> Organization | None:
        """Get organization with parent loaded."""
        return self.db.scalar(
            select(self.model)
            .options(joinedload(self.model.parent))
            .where(self.model.id == id)
        )

    def get_subsidiaries(self, parent_id: OrganizationId) -> list[Organization]:
        """Get direct subsidiaries of an organization."""
        return list(
            self.db.scalars(
                select(self.model)
                .where(self.model.parent_id == parent_id)
                .where(~self.model.is_deleted)
                .order_by(self.model.name)
            )
        )

    def get_all_subsidiaries(self, parent_id: OrganizationId) -> list[Organization]:
        """Get all subsidiaries recursively."""
        # Use CTE for recursive query - PostgreSQL requires proper CTE syntax
        org_cte = (
            select(
                self.model.id,
                self.model.code,
                self.model.name,
                self.model.parent_id,
                self.model.is_active,
                self.model.is_deleted
            )
            .where(self.model.parent_id == parent_id)
            .where(~self.model.is_deleted)
            .cte(name="subsidiaries_cte", recursive=True)
        )
        
        # Recursive part - join with the CTE directly
        recursive_part = (
            select(
                self.model.id,
                self.model.code,
                self.model.name,
                self.model.parent_id,
                self.model.is_active,
                self.model.is_deleted
            )
            .select_from(self.model)
            .join(org_cte, self.model.parent_id == org_cte.c.id)
            .where(~self.model.is_deleted)
        )
        
        org_cte = org_cte.union_all(recursive_part)

        # Final query to get the full organization objects
        return list(
            self.db.scalars(
                select(self.model)
                .join(org_cte, self.model.id == org_cte.c.id)
            )
        )

    def get_root_organizations(self) -> list[Organization]:
        """Get organizations without parent (root level)."""
        return list(
            self.db.scalars(
                select(self.model)
                .where(self.model.parent_id.is_(None))
                .where(~self.model.is_deleted)
                .order_by(self.model.name)
            )
        )

    def search_by_name(self, query: str) -> list[Organization]:
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

    def get_by_industry(self, industry: str) -> list[Organization]:
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

    def validate_unique_code(self, code: str, exclude_id: int | None = None) -> bool:
        """Validate if organization code is unique."""
        query = select(func.count(self.model.id)).where(self.model.code == code)
        if exclude_id:
            query = query.where(self.model.id != exclude_id)
        count = self.db.scalar(query) or 0
        return count == 0

    def create(self, obj_in: OrganizationCreate) -> Organization:
        """Create a new organization with proper settings handling."""
        obj_data = obj_in.model_dump()

        # Convert settings dict to JSON string for database storage
        if "settings" in obj_data and isinstance(obj_data["settings"], dict):
            obj_data["settings"] = json.dumps(obj_data["settings"])

        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update_settings(self, id: int, settings: dict[str, Any]) -> Organization | None:
        """Update organization settings."""
        org = self.get(id)
        if org:
            org.settings = json.dumps(settings)
            self.db.commit()
            self.db.refresh(org)
        return org
