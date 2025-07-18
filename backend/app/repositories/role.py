"""Role and UserRole repository implementation."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import joinedload

from app.models.role import Role, UserRole
from app.repositories.base import BaseRepository
from app.schemas.role import RoleCreate, RoleUpdate, UserRoleCreate, UserRoleUpdate
from app.types import DepartmentId, OrganizationId, RoleId, UserId


class RoleRepository(BaseRepository[Role, RoleCreate, RoleUpdate]):
    """Repository for role operations."""

    def get_by_code(self, code: str) -> Role | None:
        """Get role by code."""
        return self.db.scalar(select(self.model).where(self.model.code == code))

    def get_by_name_and_organization(
        self, name: str, organization_id: int
    ) -> Role | None:
        """Get role by name within organization."""
        return self.db.scalar(
            select(self.model)
            .where(self.model.name == name)
            .where(self.model.organization_id == organization_id)
            .where(~self.model.is_deleted)
        )

    def get_system_roles(self) -> list[Role]:
        """Get system roles."""
        return list(
            self.db.scalars(
                select(self.model)
                .where(self.model.is_system)
                .where(~self.model.is_deleted)
                .order_by(self.model.name)
            )
        )

    def get_by_type(self, role_type: str) -> list[Role]:
        """Get roles by type."""
        return list(
            self.db.scalars(
                select(self.model)
                .where(self.model.role_type == role_type)
                .where(~self.model.is_deleted)
                .order_by(self.model.name)
            )
        )

    def get_root_roles(self) -> list[Role]:
        """Get root roles (without parent)."""
        return list(
            self.db.scalars(
                select(self.model)
                .where(self.model.parent_id.is_(None))
                .where(~self.model.is_deleted)
                .order_by(self.model.name)
            )
        )

    def get_child_roles(self, parent_id: RoleId) -> list[Role]:
        """Get direct child roles."""
        return list(
            self.db.scalars(
                select(self.model)
                .where(self.model.parent_id == parent_id)
                .where(~self.model.is_deleted)
                .order_by(self.model.name)
            )
        )

    def get_with_parent(self, id: int) -> Role | None:
        """Get role with parent loaded."""
        return self.db.scalar(
            select(self.model)
            .options(joinedload(self.model.parent))
            .where(self.model.id == id)
        )

    def search_by_name(self, query: str) -> list[Role]:
        """Search roles by name."""
        search_term = f"%{query}%"
        return list(
            self.db.scalars(
                select(self.model)
                .where(
                    or_(
                        self.model.name.ilike(search_term),
                        self.model.name_en.ilike(search_term),
                        self.model.code.ilike(search_term),
                        self.model.description.ilike(search_term),
                    )
                )
                .where(~self.model.is_deleted)
                .order_by(self.model.name)
            )
        )

    def validate_unique_code(self, code: str, exclude_id: int | None = None) -> bool:
        """Validate if role code is unique."""
        query = select(func.count(self.model.id)).where(self.model.code == code)
        if exclude_id:
            query = query.where(self.model.id != exclude_id)
        count = self.db.scalar(query) or 0
        return count == 0

    def update_permissions(self, id: int, permissions: dict[str, Any]) -> Role | None:
        """Update role permissions."""
        role = self.get(id)
        if role and not role.is_system:
            role.permissions = permissions
            self.db.commit()
            self.db.refresh(role)
        return role

    def clone_role(
        self,
        source_id: int,
        new_code: str,
        new_name: str,
        organization_id: int,
        include_permissions: bool = True,
    ) -> Role:
        """Clone a role with new code and name."""
        source = self.get(source_id)
        if not source:
            raise ValueError(f"Role {source_id} not found")

        role_create = RoleCreate(
            code=new_code,
            name=new_name,
            name_en=source.name_en,
            description=f"Cloned from {source.name}",
            role_type="custom",
            organization_id=organization_id,
            parent_id=source.parent_id,
            permissions={},
            is_system=False,
            is_active=True,
        )

        return self.create(role_create)


class UserRoleRepository(BaseRepository[UserRole, UserRoleCreate, UserRoleUpdate]):
    """Repository for user role assignment operations."""

    def get_user_roles(
        self, user_id: UserId, active_only: bool = True, valid_only: bool = False
    ) -> list[UserRole]:
        """Get all roles for a user."""
        query = select(self.model).where(self.model.user_id == user_id)

        if active_only:
            query = query.where(self.model.is_active)

        if valid_only:
            now = datetime.now(UTC)
            query = query.where(self.model.valid_from <= now)
            query = query.where(
                or_(self.model.expires_at.is_(None), self.model.expires_at > now)
            )

        query = query.options(
            joinedload(self.model.role),
            joinedload(self.model.organization),
            joinedload(self.model.department),
        )

        return list(self.db.scalars(query))

    def get_primary_role(self, user_id: UserId) -> UserRole | None:
        """Get user's primary role."""
        return self.db.scalar(
            select(self.model)
            .where(self.model.user_id == user_id)
            .where(self.model.is_primary)
            .where(self.model.is_active)
            .options(
                joinedload(self.model.role),
                joinedload(self.model.organization),
                joinedload(self.model.department),
            )
        )

    def get_by_organization(
        self, user_id: UserId, organization_id: OrganizationId
    ) -> list[UserRole]:
        """Get user roles in specific organization."""
        return list(
            self.db.scalars(
                select(self.model)
                .where(self.model.user_id == user_id)
                .where(self.model.organization_id == organization_id)
                .where(self.model.is_active)
                .options(joinedload(self.model.role), joinedload(self.model.department))
            )
        )

    def get_by_role(
        self,
        role_id: RoleId,
        organization_id: OrganizationId | None = None,
        active_only: bool = True,
    ) -> list[UserRole]:
        """Get all users with specific role."""
        query = select(self.model).where(self.model.role_id == role_id)

        if organization_id:
            query = query.where(self.model.organization_id == organization_id)

        if active_only:
            query = query.where(self.model.is_active)

        query = query.options(
            joinedload(self.model.user),
            joinedload(self.model.organization),
            joinedload(self.model.department),
        )

        return list(self.db.scalars(query))

    def assign_role(
        self,
        user_id: UserId,
        role_id: RoleId,
        organization_id: OrganizationId,
        department_id: DepartmentId | None = None,
        assigned_by: UserId | None = None,
        **kwargs: Any,
    ) -> UserRole:
        """Assign a role to user."""
        # Check if assignment already exists
        existing = self.db.scalar(
            select(self.model)
            .where(self.model.user_id == user_id)
            .where(self.model.role_id == role_id)
            .where(self.model.organization_id == organization_id)
            .where(self.model.department_id == department_id)
        )

        if existing:
            # Reactivate if inactive
            if not existing.is_active:
                existing.is_active = True
                existing.assigned_by = assigned_by
                existing.assigned_at = datetime.now(UTC)
                self.db.commit()
                self.db.refresh(existing)
            return existing

        # Create new assignment
        data = {
            "user_id": user_id,
            "role_id": role_id,
            "organization_id": organization_id,
            "department_id": department_id,
            "assigned_by": assigned_by,
            **kwargs,
        }

        return self.create(UserRoleCreate(**data))

    def revoke_role(
        self,
        user_id: UserId,
        role_id: RoleId,
        organization_id: OrganizationId,
        department_id: DepartmentId | None = None,
    ) -> bool:
        """Revoke a role from user."""
        result = self.db.execute(
            update(self.model)
            .where(self.model.user_id == user_id)
            .where(self.model.role_id == role_id)
            .where(self.model.organization_id == organization_id)
            .where(self.model.department_id == department_id)
            .values(is_active=False)
        )
        self.db.commit()
        return result.rowcount > 0

    def set_primary_role(self, user_id: UserId, user_role_id: int) -> bool:
        """Set a user role as primary."""
        # First, unset all primary roles for user
        self.db.execute(
            update(self.model)
            .where(self.model.user_id == user_id)
            .values(is_primary=False)
        )

        # Then set the specified role as primary
        result = self.db.execute(
            update(self.model)
            .where(self.model.id == user_role_id)
            .where(self.model.user_id == user_id)
            .values(is_primary=True)
        )

        self.db.commit()
        return result.rowcount > 0

    def get_expiring_roles(self, days: int = 30) -> list[UserRole]:
        """Get roles expiring within specified days."""
        future_date = datetime.now(UTC) + timedelta(days=days)

        return list(
            self.db.scalars(
                select(self.model)
                .where(self.model.is_active)
                .where(self.model.expires_at.is_not(None))
                .where(self.model.expires_at <= future_date)
                .where(self.model.expires_at > datetime.now(UTC))
                .options(
                    joinedload(self.model.user),
                    joinedload(self.model.role),
                    joinedload(self.model.organization),
                )
            )
        )

    def approve_role(self, user_role_id: int, approved_by: UserId) -> UserRole | None:
        """Approve a pending role assignment."""
        user_role = self.get(user_role_id)
        if user_role and user_role.approval_status == "pending":
            user_role.approval_status = "approved"
            user_role.approved_by = approved_by
            user_role.approved_at = datetime.now(UTC)
            self.db.commit()
            self.db.refresh(user_role)
        return user_role
