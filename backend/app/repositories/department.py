"""Department repository implementation."""

from typing import Any

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import joinedload

from app.models.department import Department
from app.repositories.base import BaseRepository
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.types import DepartmentId, OrganizationId, UserId


class DepartmentRepository(
    BaseRepository[Department, DepartmentCreate, DepartmentUpdate]
):
    """Repository for department operations."""

    def get_by_code(
        self, code: str, organization_id: OrganizationId
    ) -> Department | None:
        """Get department by code within organization."""
        return self.db.scalar(
            select(self.model)
            .where(self.model.code == code)
            .where(self.model.organization_id == organization_id)
        )

    def get_by_organization(
        self,
        organization_id: OrganizationId,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> list[Department]:
        """Get departments by organization."""
        query = select(self.model).where(self.model.organization_id == organization_id)

        if active_only:
            query = query.where(self.model.is_active)

        query = query.where(~self.model.is_deleted)
        query = query.order_by(self.model.display_order, self.model.name)
        query = query.offset(skip).limit(limit)

        return list(self.db.scalars(query))

    def get_root_departments(self, organization_id: OrganizationId) -> list[Department]:
        """Get root departments (without parent) in organization."""
        return list(
            self.db.scalars(
                select(self.model)
                .where(self.model.organization_id == organization_id)
                .where(self.model.parent_id.is_(None))
                .where(~self.model.is_deleted)
                .order_by(self.model.display_order, self.model.name)
            )
        )

    def get_sub_departments(self, parent_id: DepartmentId) -> list[Department]:
        """Get direct sub-departments."""
        return list(
            self.db.scalars(
                select(self.model)
                .where(self.model.parent_id == parent_id)
                .where(~self.model.is_deleted)
                .order_by(self.model.display_order, self.model.name)
            )
        )

    def get_by_manager(self, manager_id: UserId) -> list[Department]:
        """Get departments managed by a user."""
        return list(
            self.db.scalars(
                select(self.model)
                .where(self.model.manager_id == manager_id)
                .where(~self.model.is_deleted)
                .order_by(self.model.name)
            )
        )

    def get_with_relations(self, id: int) -> Department | None:
        """Get department with all relations loaded."""
        return self.db.scalar(
            select(self.model)
            .options(
                joinedload(self.model.organization),
                joinedload(self.model.parent),
                joinedload(self.model.manager),
            )
            .where(self.model.id == id)
        )

    def search_by_name(
        self, query: str, organization_id: OrganizationId | None = None
    ) -> list[Department]:
        """Search departments by name."""
        search_term = f"%{query}%"
        q = select(self.model).where(
            or_(
                self.model.name.ilike(search_term),
                self.model.name_kana.ilike(search_term),
                self.model.name_en.ilike(search_term),
                self.model.short_name.ilike(search_term),
                self.model.code.ilike(search_term),
            )
        )

        if organization_id:
            q = q.where(self.model.organization_id == organization_id)

        q = q.where(~self.model.is_deleted)
        q = q.order_by(self.model.name)

        return list(self.db.scalars(q))

    def get_by_type(
        self, department_type: str, organization_id: OrganizationId | None = None
    ) -> list[Department]:
        """Get departments by type."""
        query = select(self.model).where(self.model.department_type == department_type)

        if organization_id:
            query = query.where(self.model.organization_id == organization_id)

        query = query.where(~self.model.is_deleted)
        query = query.order_by(self.model.name)

        return list(self.db.scalars(query))

    def get_by_cost_center(self, cost_center_code: str) -> Department | None:
        """Get department by cost center code."""
        return self.db.scalar(
            select(self.model)
            .where(self.model.cost_center_code == cost_center_code)
            .where(~self.model.is_deleted)
        )

    def validate_unique_code(
        self,
        code: str,
        organization_id: OrganizationId,
        exclude_id: int | None = None,
    ) -> bool:
        """Validate if department code is unique within organization."""
        query = select(func.count(self.model.id))
        query = query.where(self.model.code == code)
        query = query.where(self.model.organization_id == organization_id)

        if exclude_id:
            query = query.where(self.model.id != exclude_id)

        count = self.db.scalar(query) or 0
        return count == 0

    def get_headcount_stats(self, department_id: DepartmentId) -> dict[str, Any]:
        """Get headcount statistics for department."""
        from app.models.role import UserRole

        # Current headcount
        current = (
            self.db.scalar(
                select(func.count(func.distinct(UserRole.user_id)))
                .where(UserRole.department_id == department_id)
                .where(UserRole.is_active)
            )
            or 0
        )

        dept = self.get(department_id)
        limit = dept.headcount_limit if dept else None

        return {
            "current": current,
            "limit": limit,
            "available": (limit - current) if limit else None,
            "is_over": current > limit if limit else False,
        }

    def update_display_order(self, department_ids: list[DepartmentId]) -> None:
        """Update display order for multiple departments."""
        for index, dept_id in enumerate(department_ids):
            self.db.execute(
                update(self.model)
                .where(self.model.id == dept_id)
                .values(display_order=index)
            )
        self.db.commit()

    def get_with_parent(self, id: int) -> Department | None:
        """Get department with parent loaded."""
        return self.db.scalar(
            select(self.model)
            .options(joinedload(self.model.parent))
            .where(self.model.id == id)
        )

    def get_tree(
        self, organization_id: OrganizationId, parent_id: Optional[DepartmentId] = None
    ) -> List[Department]:
        """Get department tree structure."""
        query = select(self.model).where(self.model.organization_id == organization_id)

        if parent_id is None:
            # Get root departments
            query = query.where(self.model.parent_id.is_(None))
        else:
            # Get departments under specific parent
            query = query.where(self.model.path.like(f"%{parent_id}%"))

        query = query.where(~self.model.is_deleted)
        query = query.order_by(
            self.model.depth, self.model.display_order, self.model.name
        )

        return list(self.db.scalars(query))

    def get_children(
        self, parent_id: DepartmentId, recursive: bool = False
    ) -> List[Department]:
        """Get child departments."""
        if not recursive:
            # Direct children only
            return self.get_sub_departments(parent_id)

        # All descendants
        parent = self.get(parent_id)
        if not parent or not parent.path:
            return []

        query = select(self.model).where(self.model.path.like(f"{parent.path}.%"))
        query = query.where(~self.model.is_deleted)
        query = query.order_by(self.model.depth, self.model.display_order)

        return list(self.db.scalars(query))

    def move_department(
        self, department_id: DepartmentId, new_parent_id: Optional[DepartmentId]
    ) -> bool:
        """Move department to new parent."""
        dept = self.get(department_id)
        if not dept:
            return False

        # Prevent moving to self or descendant
        if new_parent_id:
            new_parent = self.get(new_parent_id)
            if not new_parent:
                return False

            # Check if new parent is a descendant
            if new_parent.path and str(department_id) in new_parent.path:
                return False

        # Update parent
        dept.parent_id = new_parent_id
        dept.update_path()

        # Update all descendants' paths
        dept.update_subtree_paths()

        self.db.commit()
        return True

    def get_ancestors(self, department_id: DepartmentId) -> List[Department]:
        """Get all ancestor departments from root to parent."""
        dept = self.get(department_id)
        if not dept or not dept.path:
            return []

        ancestor_ids = [int(id_str) for id_str in dept.path.split(".")[:-1]]
        if not ancestor_ids:
            return []

        query = select(self.model).where(self.model.id.in_(ancestor_ids))
        query = query.order_by(self.model.depth)

        return list(self.db.scalars(query))

    def get_siblings(self, department_id: DepartmentId) -> List[Department]:
        """Get sibling departments (same parent)."""
        dept = self.get(department_id)
        if not dept:
            return []

        query = select(self.model).where(self.model.parent_id == dept.parent_id)
        query = query.where(self.model.id != department_id)
        query = query.where(~self.model.is_deleted)
        query = query.order_by(self.model.display_order, self.model.name)

        return list(self.db.scalars(query))
