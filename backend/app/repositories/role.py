"""Role and UserRole repository implementation."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.orm import joinedload

from app.models.role import Role, UserRole
from app.repositories.base import BaseRepository
from app.schemas.role import RoleCreate, RoleUpdate, UserRoleCreate, UserRoleUpdate
from app.types import DepartmentId, OrganizationId, RoleId, UserId


class RoleRepository(BaseRepository[Role, RoleCreate, RoleUpdate]):
    """Repository for role operations."""

    def get_by_code(self, code: str) -> Optional[Role]:
        """Get role by code."""
        return self.db.scalar(select(self.model).where(self.model.code == code))

    def get_system_roles(self) -> List[Role]:
        """Get system roles."""
        return list(
            self.db.scalars(
                select(self.model)
                .where(self.model.is_system)
                .where(~self.model.is_deleted)
                .order_by(self.model.display_order, self.model.name)
            )
        )

    def get_by_type(self, role_type: str) -> List[Role]:
        """Get roles by type."""
        return list(
            self.db.scalars(
                select(self.model)
                .where(self.model.role_type == role_type)
                .where(~self.model.is_deleted)
                .order_by(self.model.display_order, self.model.name)
            )
        )

    def get_root_roles(self) -> List[Role]:
        """Get root roles (without parent)."""
        return list(
            self.db.scalars(
                select(self.model)
                .where(self.model.parent_id.is_(None))
                .where(~self.model.is_deleted)
                .order_by(self.model.display_order, self.model.name)
            )
        )

    def get_child_roles(self, parent_id: RoleId) -> List[Role]:
        """Get direct child roles."""
        return list(
            self.db.scalars(
                select(self.model)
                .where(self.model.parent_id == parent_id)
                .where(~self.model.is_deleted)
                .order_by(self.model.display_order, self.model.name)
            )
        )

    def get_with_parent(self, id: int) -> Optional[Role]:
        """Get role with parent loaded."""
        return self.db.scalar(
            select(self.model)
            .options(joinedload(self.model.parent))
            .where(self.model.id == id)
        )

    def search_by_name(self, query: str) -> List[Role]:
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

    def validate_unique_code(self, code: str, exclude_id: Optional[int] = None) -> bool:
        """Validate if role code is unique."""
        query = select(func.count(self.model.id)).where(self.model.code == code)
        if exclude_id:
            query = query.where(self.model.id != exclude_id)
        count = self.db.scalar(query) or 0
        return count == 0

    def update_permissions(
        self, id: int, permissions: Dict[str, Any]
    ) -> Optional[Role]:
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
            permissions=source.permissions if include_permissions else {},
            is_system=False,
            display_order=source.display_order,
            icon=source.icon,
            color=source.color,
            is_active=True,
        )

        return self.create(role_create)


class UserRoleRepository(BaseRepository[UserRole, UserRoleCreate, UserRoleUpdate]):
    """Repository for user role assignment operations."""

    def get_user_roles(
        self, user_id: UserId, active_only: bool = True, valid_only: bool = False
    ) -> List[UserRole]:
        """Get all roles for a user."""
        query = select(self.model).where(self.model.user_id == user_id)

        if active_only:
            query = query.where(self.model.is_active)

        if valid_only:
            now = datetime.utcnow()
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

    def get_primary_role(self, user_id: UserId) -> Optional[UserRole]:
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
    ) -> List[UserRole]:
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
        organization_id: Optional[OrganizationId] = None,
        active_only: bool = True,
    ) -> List[UserRole]:
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
        department_id: Optional[DepartmentId] = None,
        assigned_by: Optional[UserId] = None,
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
                existing.assigned_at = datetime.utcnow()
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
        department_id: Optional[DepartmentId] = None,
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

    def get_expiring_roles(self, days: int = 30) -> List[UserRole]:
        """Get roles expiring within specified days."""
        future_date = datetime.utcnow() + timedelta(days=days)

        return list(
            self.db.scalars(
                select(self.model)
                .where(self.model.is_active)
                .where(self.model.expires_at.is_not(None))
                .where(self.model.expires_at <= future_date)
                .where(self.model.expires_at > datetime.utcnow())
                .options(
                    joinedload(self.model.user),
                    joinedload(self.model.role),
                    joinedload(self.model.organization),
                )
            )
        )

    def approve_role(
        self, user_role_id: int, approved_by: UserId
    ) -> Optional[UserRole]:
        """Approve a pending role assignment."""
        user_role = self.get(user_role_id)
        if user_role and user_role.approval_status == "pending":
            user_role.approval_status = "approved"
            user_role.approved_by = approved_by
            user_role.approved_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user_role)
        return user_role

    # Phase 2: Enhanced Repository Methods

    def get_roles_by_organization(self, organization_id: OrganizationId) -> List[Role]:
        """Get all roles for a specific organization."""
        return list(
            self.db.scalars(
                select(self.model)
                .where(self.model.organization_id == organization_id)
                .where(~self.model.is_deleted)
                .order_by(self.model.display_order, self.model.name)
            )
        )

    def count_role_users(self, role_id: RoleId) -> int:
        """Count active users with this role."""
        return self.db.scalar(
            select(func.count(UserRole.id)).where(
                and_(UserRole.role_id == role_id, UserRole.is_active)
            )
        ) or 0

    def get_permissions_for_role(
        self, role_id: RoleId, include_inherited: bool = True
    ) -> List[Any]:
        """Get all permissions for a role, optionally including inherited ones."""
        from app.models.permission import Permission
        from app.models.role_permission import RolePermission

        role = self.get_with_parent(role_id)
        if not role:
            return []

        permissions = set()

        # Get direct permissions
        direct_perms = list(
            self.db.scalars(
                select(Permission)
                .join(RolePermission, Permission.id == RolePermission.permission_id)
                .where(RolePermission.role_id == role_id)
                .where(RolePermission.is_active == True)
                .where(Permission.is_active == True)
            )
        )
        permissions.update(direct_perms)

        # Get inherited permissions if requested
        if include_inherited and role.parent_id:
            parent_perms = self.get_permissions_for_role(role.parent_id, True)
            permissions.update(parent_perms)

        return list(permissions)

    def get_effective_permissions(
        self,
        role_id: RoleId,
        organization_id: Optional[OrganizationId] = None,
        department_id: Optional[DepartmentId] = None
    ) -> Set[str]:
        """Get effective permission codes considering inheritance and scope."""
        role = self.get(role_id)
        if not role:
            return set()

        # Use the role model's method which handles all the logic
        return role.get_effective_permissions(organization_id, department_id)

    def check_permission(
        self,
        role_id: RoleId,
        permission_code: str,
        organization_id: Optional[OrganizationId] = None,
        department_id: Optional[DepartmentId] = None,
    ) -> bool:
        """Check if role has a specific permission."""
        role = self.get(role_id)
        if not role:
            return False

        return role.has_effective_permission(
            permission_code, organization_id, department_id
        )

    def assign_permissions_to_role(
        self,
        role_id: RoleId,
        permission_ids: List[int],
        granted_by: Optional[UserId] = None,
        effect: str = "allow",
        organization_id: Optional[OrganizationId] = None,
        department_id: Optional[DepartmentId] = None,
    ) -> List[Any]:
        """Assign multiple permissions to a role."""
        from app.models.role_permission import RolePermission

        role = self.get(role_id)
        if not role:
            raise ValueError(f"Role {role_id} not found")

        # Get existing role permissions to avoid duplicates
        existing = self.db.scalars(
            select(RolePermission).where(
                and_(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id.in_(permission_ids),
                    RolePermission.organization_id == organization_id,
                    RolePermission.department_id == department_id,
                )
            )
        ).all()

        existing_permission_ids = {rp.permission_id for rp in existing}
        new_permissions = []

        # Create new role permissions
        for permission_id in permission_ids:
            if permission_id not in existing_permission_ids:
                rp = RolePermission(
                    role_id=role_id,
                    permission_id=permission_id,
                    effect=effect,
                    granted_by=granted_by,
                    organization_id=organization_id,
                    department_id=department_id,
                    is_active=True,
                )
                self.db.add(rp)
                new_permissions.append(rp)

        self.db.flush()
        return new_permissions

    def bulk_permission_operations(
        self, operations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform bulk permission operations."""
        from app.models.role_permission import RolePermission

        results = {
            "added": 0,
            "removed": 0,
            "updated": 0,
            "errors": [],
        }

        for op in operations:
            try:
                operation_type = op.get("type")
                role_id = op.get("role_id")
                permission_ids = op.get("permission_ids", [])

                if operation_type == "add":
                    new_perms = self.assign_permissions_to_role(
                        role_id=role_id,
                        permission_ids=permission_ids,
                        granted_by=op.get("granted_by"),
                        effect=op.get("effect", "allow"),
                        organization_id=op.get("organization_id"),
                        department_id=op.get("department_id"),
                    )
                    results["added"] += len(new_perms)

                elif operation_type == "remove":
                    # Remove permissions
                    query = select(RolePermission).where(
                        and_(
                            RolePermission.role_id == role_id,
                            RolePermission.permission_id.in_(permission_ids),
                        )
                    )

                    if op.get("organization_id") is not None:
                        query = query.where(
                            RolePermission.organization_id == op.get("organization_id")
                        )
                    if op.get("department_id") is not None:
                        query = query.where(
                            RolePermission.department_id == op.get("department_id")
                        )

                    role_permissions = self.db.scalars(query).all()
                    count = len(role_permissions)

                    for rp in role_permissions:
                        self.db.delete(rp)

                    results["removed"] += count

                elif operation_type == "update":
                    # Update effect or other properties
                    query = select(RolePermission).where(
                        and_(
                            RolePermission.role_id == role_id,
                            RolePermission.permission_id.in_(permission_ids),
                        )
                    )

                    role_permissions = self.db.scalars(query).all()
                    count = 0

                    updates = op.get("updates", {})
                    for rp in role_permissions:
                        if "effect" in updates:
                            rp.effect = updates["effect"]
                        if "is_active" in updates:
                            rp.is_active = updates["is_active"]
                        if "priority" in updates:
                            rp.priority = updates["priority"]
                        if "expires_at" in updates:
                            rp.expires_at = updates["expires_at"]
                        count += 1

                    results["updated"] += count

            except Exception as e:
                results["errors"].append({"operation": op, "error": str(e)})

        self.db.flush()
        return results
