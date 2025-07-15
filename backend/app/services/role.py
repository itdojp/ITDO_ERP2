"""Role service implementation with complete type safety."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import (
    AlreadyExists,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from app.models.organization import Organization
from app.models.permission import Permission
from app.models.role import Role, RolePermission, UserRole
from app.repositories.role import RoleRepository
from app.schemas.role import (
    BulkRoleAssignment,
    PermissionBasic,
    RoleCreate,
    RoleResponse,
    RoleSummary,
    RoleTree,
    RoleUpdate,
    RoleWithPermissions,
    UserRoleAssignment,
    UserRoleResponse,
)
from app.types import OrganizationId, RoleId, UserId


class RoleService:
    """Service for managing roles and permissions."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
        self.repository = RoleRepository(Role, db)

    # Role CRUD operations

    def create_role(self, role_data: RoleCreate, created_by: UserId) -> Role:
        """Create a new role."""
        # Check if role code already exists
        if self.repository.get_by_code(role_data.code):
            raise AlreadyExists(f"Role with code '{role_data.code}' already exists")

        # Check if role name already exists within organization
        if hasattr(role_data, "organization_id") and role_data.organization_id:
            if self.repository.get_by_name_and_organization(
                role_data.name, role_data.organization_id
            ):
                raise AlreadyExists(
                    f"Role with name '{role_data.name}' already exists in "
                    "this organization"
                )

        # Check if organization exists if specified
        if hasattr(role_data, "organization_id") and role_data.organization_id:
            org = self.db.get(Organization, role_data.organization_id)
            if not org:
                raise NotFound(f"Organization {role_data.organization_id} not found")

        # Create role
        role = Role(
            code=role_data.code,
            name=role_data.name,
            name_en=role_data.name_en,
            description=role_data.description,
            role_type=role_data.role_type,
            organization_id=getattr(role_data, "organization_id", None),
            parent_id=role_data.parent_id,
            is_system=role_data.is_system,
            created_by=created_by,
            updated_by=created_by,
        )

        # Update hierarchy metadata
        if role_data.parent_id:
            parent = self.db.get(Role, role_data.parent_id)
            if parent:
                role.full_path = f"{parent.full_path}{role_data.parent_id}/"
                role.depth = parent.depth + 1
        else:
            role.full_path = "/"
            role.depth = 0

        self.db.add(role)
        self.db.flush()

        return role

    def update_role(
        self, role_id: RoleId, role_data: RoleUpdate, updated_by: UserId
    ) -> Role | None:
        """Update an existing role."""
        role = self.repository.get(role_id)
        if not role:
            raise NotFound(f"Role {role_id} not found")

        # System roles cannot be modified
        if role.is_system:
            raise PermissionDenied("System roles cannot be modified")

        # Check if new code conflicts
        if role_data.code and role_data.code != role.code:
            existing = self.repository.get_by_code(role_data.code)
            if existing and existing.id != role_id:
                raise AlreadyExists(f"Role with code '{role_data.code}' already exists")

        # Update fields
        update_fields = role_data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(role, field, value)

        role.updated_by = updated_by
        role.updated_at = datetime.now(UTC)

        self.db.flush()
        return role

    def delete_role(self, role_id: RoleId, deleted_by: UserId) -> bool:
        """Soft delete a role."""
        role = self.repository.get(role_id)
        if not role:
            raise NotFound(f"Role {role_id} not found")

        # System roles cannot be deleted
        if role.is_system:
            raise PermissionDenied("System roles cannot be deleted")

        # Check if role has active assignments
        active_count = self.db.scalar(
            select(func.count(UserRole.id)).where(
                and_(UserRole.role_id == role_id, UserRole.is_active)
            )
        )

        if active_count and active_count > 0:
            raise ValidationError(
                f"Cannot delete role with {active_count} active assignments"
            )

        role.soft_delete(deleted_by=deleted_by)
        self.db.flush()

        return True

    # Permission management

    def get_role_permissions(self, role_id: RoleId) -> list[Permission]:
        """Get all permissions for a role."""
        role_perms = self.db.scalars(
            select(Permission)
            .join(RolePermission)
            .where(RolePermission.role_id == role_id)
            .order_by(Permission.category, Permission.code)
        ).all()

        return list(role_perms)

    def update_role_permissions(
        self, role_id: RoleId, permission_codes: list[str], updated_by: UserId
    ) -> Role:
        """Update role permissions."""
        role = self.repository.get(role_id)
        if not role:
            raise NotFound(f"Role {role_id} not found")

        # Validate all permission codes exist
        permission_ids = []
        invalid_codes = []
        for code in permission_codes:
            perm = self.db.scalar(select(Permission).where(Permission.code == code))
            if perm:
                permission_ids.append(perm.id)
            else:
                invalid_codes.append(code)

        # Raise error if any invalid codes found
        if invalid_codes:
            raise ValueError(f"Invalid permission codes: {', '.join(invalid_codes)}")

        # Clear existing permissions
        from sqlalchemy import delete

        self.db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))

        # Add new permissions
        for perm_id in permission_ids:
            role_perm = RolePermission(
                role_id=role_id, permission_id=perm_id, granted_by=updated_by
            )
            self.db.add(role_perm)

        self.db.flush()
        return role

    # Role assignment

    def assign_role_to_user(
        self, assignment: UserRoleAssignment, assigned_by: UserId
    ) -> UserRole:
        """Assign a role to a user."""
        # Check if assignment already exists
        existing = self.db.scalar(
            select(UserRole).where(
                and_(
                    UserRole.user_id == assignment.user_id,
                    UserRole.role_id == assignment.role_id,
                    UserRole.organization_id == assignment.organization_id,
                    UserRole.is_active,
                )
            )
        )

        if existing:
            raise AlreadyExists("User already has this role assignment")

        # Create assignment
        user_role = UserRole(
            user_id=assignment.user_id,
            role_id=assignment.role_id,
            organization_id=assignment.organization_id,
            department_id=assignment.department_id,
            assigned_by=assigned_by,
            expires_at=assignment.expires_at,
            is_active=True,
            created_by=assigned_by,
            updated_by=assigned_by,
        )

        self.db.add(user_role)
        self.db.flush()

        return user_role

    def remove_role_from_user(
        self,
        user_id: UserId,
        role_id: RoleId,
        organization_id: OrganizationId,
        removed_by: UserId,
    ) -> bool:
        """Remove a role from a user."""
        user_role = self.db.scalar(
            select(UserRole).where(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role_id,
                    UserRole.organization_id == organization_id,
                    UserRole.is_active,
                )
            )
        )

        if not user_role:
            raise NotFound("Role assignment not found")

        user_role.is_active = False
        user_role.updated_by = removed_by
        user_role.updated_at = datetime.now(UTC)

        self.db.flush()
        return True

    # Query methods

    def get_role(self, role_id: RoleId) -> Role | None:
        """Get a role by ID."""
        return self.repository.get_with_parent(role_id)

    def get_role_response(self, role: Role) -> RoleResponse:
        """Convert role to response schema."""
        # Convert role to dict and handle permissions field
        role_dict = {
            "id": role.id,
            "code": role.code,
            "name": role.name,
            "name_en": getattr(role, "name_en", None),
            "description": role.description,
            "is_active": role.is_active,
            "role_type": role.role_type,
            "parent_id": role.parent_id,
            "parent": role.parent,
            "is_system": role.is_system,
            "is_inherited": False,
            "users_count": len(role.user_roles) if role.user_roles else 0,
            "display_order": 0,
            "icon": None,
            "color": None,
            "permissions": {},  # Initialize as empty dict instead of InstrumentedList
            "all_permissions": {},
            "created_at": role.created_at,
            "updated_at": role.updated_at,
            "deleted_at": role.deleted_at,
            "created_by": role.created_by,
            "updated_by": role.updated_by,
            "deleted_by": role.deleted_by,
            "is_deleted": role.is_deleted,
        }
        return RoleResponse.model_validate(role_dict)

    def get_role_tree(
        self, organization_id: OrganizationId | None = None
    ) -> list[RoleTree]:
        """Get hierarchical role tree."""
        # Get root roles
        query = select(Role).where(Role.parent_id.is_(None))

        if organization_id:
            query = query.where(
                or_(
                    Role.organization_id == organization_id,
                    Role.organization_id.is_(None),
                )
            )

        roots = self.db.scalars(query).all()

        # Build tree recursively
        def build_tree(role: Role) -> RoleTree:
            children = [
                build_tree(child) for child in role.children if child.is_active
            ]

            return RoleTree(
                id=role.id,
                code=role.code,
                name=role.name,
                description=role.description,
                role_type=role.role_type,
                is_active=role.is_active,
                user_count=len([ur for ur in role.user_roles if ur.is_active]),
                permission_count=len(role.role_permissions),
                children=children,
            )

        return [build_tree(root) for root in roots if root.is_active]

    def list_roles(
        self,
        skip: int = 0,
        active_only: bool = True,
        limit: int = 100,
        organization_id: OrganizationId | None = None,
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[Role], int]:
        """List roles with filtering."""
        query = select(Role).where(~Role.is_deleted)

        if active_only:
            query = query.where(Role.is_active)

        if organization_id:
            query = query.where(
                or_(
                    Role.organization_id == organization_id,
                    Role.organization_id.is_(None),
                )
            )

        # Apply additional filters
        if filters:
            for key, value in filters.items():
                if key == "role_type":
                    query = query.where(Role.role_type == value)
                elif key == "is_active":
                    query = query.where(Role.is_active == value)
                elif key == "organization_id":
                    # Already handled above
                    pass

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_query) or 0

        # Get paginated results
        roles = self.db.scalars(
            query.order_by(Role.name).offset(skip).limit(limit)
        ).all()

        return list(roles), total

    def get_user_roles(
        self, user_id: UserId, organization_id: OrganizationId | None = None
    ) -> list[UserRoleResponse]:
        """Get all roles for a user."""
        query = select(UserRole).where(
            and_(UserRole.user_id == user_id, UserRole.is_active)
        )

        if organization_id:
            query = query.where(UserRole.organization_id == organization_id)

        user_roles = self.db.scalars(
            query.options(
                selectinload(UserRole.role),
                selectinload(UserRole.organization),
                selectinload(UserRole.department),
            )
        ).all()

        responses = []
        for ur in user_roles:
            if ur.is_valid:
                responses.append(
                    UserRoleResponse.model_validate(ur, from_attributes=True)
                )

        return responses

    def get_available_permissions(self) -> list[PermissionBasic]:
        """Get all available permissions."""
        permissions = self.db.scalars(
            select(Permission)
            .where(Permission.is_active)
            .order_by(Permission.category, Permission.code)
        ).all()

        return [
            PermissionBasic.model_validate(perm, from_attributes=True)
            for perm in permissions
        ]

    def bulk_assign_roles(
        self, assignment: BulkRoleAssignment, assigned_by: UserId
    ) -> dict[str, Any]:
        """Bulk assign roles to multiple users."""
        success_count = 0
        error_count = 0
        errors = []

        for user_id in assignment.user_ids:
            try:
                self.assign_role_to_user(
                    UserRoleAssignment(
                        user_id=user_id,
                        role_id=assignment.role_id,
                        organization_id=assignment.organization_id,
                        department_id=assignment.department_id,
                        valid_from=assignment.valid_from,
                        expires_at=assignment.expires_at,
                    ),
                    assigned_by,
                )
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append({"user_id": user_id, "error": str(e)})

        return {
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors,
        }

    def search_roles(
        self, search: str, skip: int, limit: int, filters: dict[str, Any]
    ) -> tuple[list[Role], int]:
        """Search roles by name or description."""
        # Stub implementation for API compatibility
        query = select(Role).where(~Role.is_deleted)

        if search:
            query = query.where(
                or_(Role.name.contains(search), Role.description.contains(search))
            )

        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        roles = self.db.scalars(query.offset(skip).limit(limit)).all()

        return list(roles), total

    def get_role_summary(self, role: Role) -> RoleSummary:
        """Get role summary."""
        return RoleSummary.model_validate(role, from_attributes=True)

    def list_all_permissions(
        self, category: str | None = None
    ) -> list[PermissionBasic]:
        """List all available permissions."""
        query = select(Permission)

        if category:
            query = query.where(Permission.category == category)

        permissions = self.db.scalars(query).all()
        return [
            PermissionBasic.model_validate(p, from_attributes=True) for p in permissions
        ]

    def get_role_with_permissions(
        self, role: Role, include_inherited: bool = False
    ) -> RoleWithPermissions:
        """Get role with its permissions."""
        permissions = self.get_role_permissions(role.id)
        # Create base role response first
        role_response = self.get_role_response(role)
        # Convert to dict and add permission_list
        role_data = role_response.model_dump()
        role_data["permission_list"] = [
            PermissionBasic.model_validate(p, from_attributes=True) for p in permissions
        ]
        return RoleWithPermissions(**role_data)

    def user_has_permission(
        self,
        user_id: UserId,
        permission_code: str,
        organization_id: OrganizationId | None = None,
    ) -> bool:
        """Check if user has specific permission."""
        # Get user's active roles
        query = (
            select(UserRole)
            .join(Role)
            .where(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.is_active,
                    Role.is_active,
                )
            )
        )

        if organization_id:
            query = query.where(
                or_(
                    UserRole.organization_id == organization_id,
                    UserRole.organization_id.is_(None),
                )
            )

        user_roles = self.db.scalars(query).all()

        # Check each role for the permission
        for user_role in user_roles:
            # Get role with permissions
            role = user_role.role

            # Check direct permissions
            for perm in role.permissions:
                if perm.code == permission_code:
                    return True

            # Check inherited permissions from parent roles
            parent = role.parent
            while parent:
                for perm in parent.permissions:
                    if perm.code == permission_code:
                        return True
                parent = parent.parent

        return False

    def is_role_in_use(self, role_id: RoleId) -> bool:
        """Check if role is assigned to any users."""
        count = self.db.scalar(
            select(func.count(UserRole.id)).where(
                and_(UserRole.role_id == role_id, UserRole.is_active)
            )
        )
        return (count or 0) > 0

    def get_user_role_response(self, user_role: UserRole) -> UserRoleResponse:
        """Get user role response."""
        return UserRoleResponse.model_validate(user_role, from_attributes=True)
