"""Role service implementation."""

<<<<<<< HEAD
from datetime import datetime, timezone
from typing import List, Optional
=======
from datetime import UTC, datetime
from typing import Any
>>>>>>> origin/main

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

<<<<<<< HEAD
from app.core.exceptions import NotFound, PermissionDenied
from app.models.role import Role, UserRole
from app.models.user import User
=======
from app.core.exceptions import (
    AlreadyExists,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from app.models.organization import Organization
from app.models.permission import Permission
from app.models.role import Role, RolePermission, UserRole
from app.models.user import User
from app.repositories.role import RoleRepository
>>>>>>> origin/main
from app.schemas.role import (
    RoleCreate,
    RoleList,
    RoleResponse,
    RoleUpdate,
    UserRoleResponse,
)


class RoleService:
    """Role service for managing roles and user role assignments."""

    def create_role(
        self,
        data: RoleCreate,
        user: User,
        db: Session,
        organization_id: Optional[int] = None,
    ) -> Role:
        """
        Create a new role.

        Args:
            data: Role creation data
            user: User creating the role
            db: Database session
            organization_id: Organization context (for permission check)

        Returns:
            Created role

        Raises:
            PermissionDenied: If user lacks permission to create roles
        """
        # Check permissions
        if not user.is_superuser:
            if organization_id and not user.has_permission(
                "role:create", organization_id
            ):
                raise PermissionDenied("ロール作成権限がありません")
            elif not organization_id and not user.is_superuser:
                raise PermissionDenied("システムロール作成には管理者権限が必要です")

        # Check if role code already exists
<<<<<<< HEAD
        existing_role = db.query(Role).filter(Role.code == data.code).first()
        if existing_role:
            raise ValueError(f"ロールコード '{data.code}' は既に存在します")

        # Create role
        role = Role(
            code=data.code,
            name=data.name,
            description=data.description,
            created_by=user.id,
=======
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
>>>>>>> origin/main
        )

        # Convert permissions list to dict
        if data.permissions:
            role.permissions = {perm: True for perm in data.permissions}

        db.add(role)
        db.commit()
        db.refresh(role)

        return role

<<<<<<< HEAD
    def assign_role_to_user(
=======
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

        self.db.commit()
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
>>>>>>> origin/main
        self,
        user_id: int,
        role_id: int,
        organization_id: int,
        assigner: User,
        db: Session,
        department_id: Optional[int] = None,
        expires_at: Optional[datetime] = None,
    ) -> UserRole:
        """
        Assign a role to a user within an organization/department context.

        Args:
            user_id: ID of user to assign role to
            role_id: ID of role to assign
            organization_id: Organization context
            assigner: User performing the assignment
            db: Database session
            department_id: Optional department context
            expires_at: Optional expiration date

        Returns:
            Created user role assignment

        Raises:
            NotFound: If user or role not found
            PermissionDenied: If assigner lacks permission
        """
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFound("ユーザーが見つかりません")

        # Check if role exists
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise NotFound("ロールが見つかりません")

        # Check permissions
        if not assigner.is_superuser:
            if not assigner.has_permission("role:assign", organization_id):
                raise PermissionDenied("ロール割り当て権限がありません")

        # Check if assignment already exists
        existing_assignment = (
            db.query(UserRole)
            .filter(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role_id,
                    UserRole.organization_id == organization_id,
                    UserRole.department_id == department_id,
                )
            )
            .first()
        )

        if existing_assignment:
            raise ValueError("このロール割り当ては既に存在します")

        # Create user role assignment
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            organization_id=organization_id,
            department_id=department_id,
            assigned_by=assigner.id,
            expires_at=expires_at,
        )
        db.add(user_role)
        db.commit()
        db.refresh(user_role)

        return user_role

    def get_user_roles(
        self,
        user_id: int,
        requester: User,
        db: Session,
        organization_id: Optional[int] = None,
        include_expired: bool = False,
    ) -> List[UserRoleResponse]:
        """
        Get roles assigned to a user.

        Args:
            user_id: ID of user to get roles for
            requester: User requesting the information
            db: Database session
            organization_id: Optional organization filter
            include_expired: Whether to include expired roles

        Returns:
            List of user role assignments

        Raises:
            NotFound: If user not found
            PermissionDenied: If requester lacks permission
        """
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFound("ユーザーが見つかりません")

        # Check permissions
        if not requester.is_superuser and requester.id != user_id:
            if organization_id and not requester.has_permission(
                "role:read", organization_id
            ):
                raise PermissionDenied("ロール情報の閲覧権限がありません")

        # Build query
        query = db.query(UserRole).filter(UserRole.user_id == user_id)

        if organization_id:
            query = query.filter(UserRole.organization_id == organization_id)

        if not include_expired:
            query = query.filter(
                or_(
                    UserRole.expires_at.is_(None),
                    UserRole.expires_at > datetime.now(timezone.utc),
                )
            )

        user_roles = query.all()

        return [UserRoleResponse.model_validate(ur) for ur in user_roles]

    def remove_role_from_user(
        self,
        user_id: int,
        role_id: int,
        organization_id: int,
        remover: User,
        db: Session,
        department_id: Optional[int] = None,
    ) -> bool:
        """
        Remove a role assignment from a user.

        Args:
            user_id: ID of user to remove role from
            role_id: ID of role to remove
            organization_id: Organization context
            remover: User performing the removal
            db: Database session
            department_id: Optional department context

        Returns:
            True if role was removed, False if not found

        Raises:
            PermissionDenied: If remover lacks permission
        """
        # Check permissions
        if not remover.is_superuser:
            if not remover.has_permission("role:remove", organization_id):
                raise PermissionDenied("ロール削除権限がありません")

        # Find the user role assignment
        user_role = (
            db.query(UserRole)
            .filter(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role_id,
                    UserRole.organization_id == organization_id,
                    UserRole.department_id == department_id,
                )
            )
            .first()
        )

        if not user_role:
            return False

<<<<<<< HEAD
        # Remove the assignment
        db.delete(user_role)
        db.commit()
=======
        user_role.is_active = False
        user_role.updated_by = removed_by
        user_role.updated_at = datetime.now(UTC)
>>>>>>> origin/main

        return True

<<<<<<< HEAD
    def get_role_permissions(
        self,
        role_id: int,
        requester: User,
        db: Session,
        organization_id: Optional[int] = None,
    ) -> List[str]:
        """
        Get permissions for a specific role.
=======
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
            children = [build_tree(child) for child in role.children if child.is_active]

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
>>>>>>> origin/main

        Args:
            role_id: ID of role to get permissions for
            requester: User requesting the information
            db: Database session
            organization_id: Optional organization context for permission check

        Returns:
            List of permissions

        Raises:
            NotFound: If role not found
            PermissionDenied: If requester lacks permission
        """
        # Check if role exists
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise NotFound("ロールが見つかりません")

        # Check permissions
        if not requester.is_superuser:
            if organization_id and not requester.has_permission(
                "role:read", organization_id
            ):
                raise PermissionDenied("ロール情報の閲覧権限がありません")

        return role.permissions or []

    def update_role_permissions(
        self,
        role_id: int,
        permissions: List[str],
        updater: User,
        db: Session,
        organization_id: Optional[int] = None,
    ) -> Role:
        """
        Update permissions for a role.

        Args:
            role_id: ID of role to update
            permissions: New list of permissions
            updater: User performing the update
            db: Database session
            organization_id: Optional organization context for permission check

        Returns:
            Updated role

        Raises:
            NotFound: If role not found
            PermissionDenied: If updater lacks permission
        """
        # Check if role exists
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise NotFound("ロールが見つかりません")

        # Check if it's a system role
        if role.is_system:
            raise PermissionDenied("システムロールの権限は変更できません")

        # Check permissions
        if not updater.is_superuser:
            if organization_id and not updater.has_permission(
                "role:update", organization_id
            ):
                raise PermissionDenied("ロール更新権限がありません")

        # Update permissions
        role.permissions = permissions
        role.updated_by = updater.id
        db.add(role)
        db.commit()

        return role

    def check_user_permission(
        self,
        user_id: int,
        permission: str,
        organization_id: int,
        requester: User,
        db: Session,
        department_id: Optional[int] = None,
    ) -> bool:
        """
        Check if a user has a specific permission in a given context.

        Args:
            user_id: ID of user to check
            permission: Permission to check for
            organization_id: Organization context
            requester: User requesting the check
            db: Database session
            department_id: Optional department context

        Returns:
            True if user has permission, False otherwise

        Raises:
            NotFound: If user not found
            PermissionDenied: If requester lacks permission to check
        """
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFound("ユーザーが見つかりません")

        # Check permissions for the requester
        if not requester.is_superuser and requester.id != user_id:
            if not requester.has_permission("role:read", organization_id):
                raise PermissionDenied("権限確認の実行権限がありません")

        # Check if user has the permission
        return user.has_permission(permission, organization_id)

    def get_users_with_role(
        self,
        role_id: int,
        organization_id: int,
        requester: User,
        db: Session,
        department_id: Optional[int] = None,
        include_expired: bool = False,
    ) -> List[User]:
        """
        Get all users that have a specific role.

        Args:
            role_id: ID of role to search for
            organization_id: Organization context
            requester: User requesting the information
            db: Database session
            department_id: Optional department context
            include_expired: Whether to include expired assignments

        Returns:
            List of users with the role

        Raises:
            NotFound: If role not found
            PermissionDenied: If requester lacks permission
        """
        # Check if role exists
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise NotFound("ロールが見つかりません")

        # Check permissions
        if not requester.is_superuser:
            if not requester.has_permission("role:read", organization_id):
                raise PermissionDenied("ロール情報の閲覧権限がありません")

        # Build query
        query = (
            db.query(User)
            .join(UserRole, User.id == UserRole.user_id)
            .filter(
                and_(
                    UserRole.role_id == role_id,
                    UserRole.organization_id == organization_id,
                )
            )
<<<<<<< HEAD
        )
=======

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
        self,
        user_id: UserId,
        organization_id: OrganizationId | None = None,
        active_only: bool = True,
    ) -> list[UserRoleResponse]:
        """Get all roles for a user."""
        query = select(UserRole).where(UserRole.user_id == user_id)

        if active_only:
            query = query.where(UserRole.is_active)
>>>>>>> origin/main

        if department_id is not None:
            query = query.filter(UserRole.department_id == department_id)

        if not include_expired:
            query = query.filter(
                or_(
                    UserRole.expires_at.is_(None),
                    UserRole.expires_at > datetime.now(timezone.utc),
                )
            )

<<<<<<< HEAD
        return query.all()
=======
        responses = []
        for ur in user_roles:
            if ur.is_valid:
                responses.append(self.get_user_role_response(ur))
>>>>>>> origin/main

    # Additional utility methods for role management

<<<<<<< HEAD
    def get_roles(
        self,
        requester: User,
        db: Session,
        organization_id: Optional[int] = None,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        include_system: bool = True,
    ) -> RoleList:
        """Get roles with pagination and filtering."""
        # Check permissions
        if not requester.is_superuser:
            if organization_id and not requester.has_permission(
                "role:read", organization_id
            ):
                raise PermissionDenied("ロール情報の閲覧権限がありません")
=======
    def get_available_permissions(self) -> list[PermissionBasic]:
        """Get all available permissions."""
        permissions = self.db.scalars(
            select(Permission)
            .where(Permission.is_active)
            .order_by(Permission.category, Permission.code)
        ).all()
>>>>>>> origin/main

        # Build query
        query = db.query(Role).filter(Role.is_active)

<<<<<<< HEAD
        if not include_system:
            query = query.filter(~Role.is_system)
=======
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
>>>>>>> origin/main

        if search:
            query = query.filter(
                or_(
                    Role.name.ilike(f"%{search}%"),
                    Role.code.ilike(f"%{search}%"),
                )
            )

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * limit
        items = query.order_by(Role.name).offset(offset).limit(limit).all()

<<<<<<< HEAD
        return RoleList(
            items=[RoleResponse.model_validate(role) for role in items],
            total=total,
            page=page,
            limit=limit,
=======
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
        # Get user
        user = self.db.scalar(select(User).where(User.id == user_id))
        if not user:
            return False

        # Check if user is superuser (has all permissions)
        if user.is_superuser:
            return True

        # Check if user has the specific permission through role assignments
        query = (
            select(Permission)
            .join(RolePermission)
            .join(Role)
            .join(UserRole)
            .where(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.is_active,
                    Role.is_active,
                    Permission.code == permission_code,
                    Permission.is_active,
                )
            )
        )

        # Filter by organization if provided
        if organization_id:
            query = query.where(UserRole.organization_id == organization_id)

        # Check if any matching permission exists
        permission = self.db.scalar(query)
        return permission is not None

    def is_role_in_use(self, role_id: RoleId) -> bool:
        """Check if role is assigned to any users."""
        count = self.db.scalar(
            select(func.count(UserRole.id)).where(
                and_(UserRole.role_id == role_id, UserRole.is_active)
            )
>>>>>>> origin/main
        )

<<<<<<< HEAD
    def get_role_by_id(
        self,
        role_id: int,
        requester: User,
        db: Session,
        organization_id: Optional[int] = None,
    ) -> Role:
        """Get role by ID."""
        # Check permissions
        if not requester.is_superuser:
            if organization_id and not requester.has_permission(
                "role:read", organization_id
            ):
                raise PermissionDenied("ロール情報の閲覧権限がありません")

        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise NotFound("ロールが見つかりません")

        return role

    def update_role(
        self,
        role_id: int,
        data: RoleUpdate,
        updater: User,
        db: Session,
        organization_id: Optional[int] = None,
    ) -> Role:
        """Update role details."""
        # Check if role exists
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise NotFound("ロールが見つかりません")

        # Check if it's a system role
        if role.is_system:
            raise PermissionDenied("システムロールは変更できません")

        # Check permissions
        if not updater.is_superuser:
            if organization_id and not updater.has_permission(
                "role:update", organization_id
            ):
                raise PermissionDenied("ロール更新権限がありません")

        # Update role
        update_data = data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(role, field, value)
        role.updated_by = updater.id
        db.commit()
        db.refresh(role)

        return role

    def delete_role(
        self,
        role_id: int,
        deleter: User,
        db: Session,
        organization_id: Optional[int] = None,
    ) -> bool:
        """Delete a role (soft delete)."""
        # Check if role exists
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise NotFound("ロールが見つかりません")

        # Check if it's a system role
        if role.is_system:
            raise PermissionDenied("システムロールは削除できません")

        # Check permissions
        if not deleter.is_superuser:
            if organization_id and not deleter.has_permission(
                "role:delete", organization_id
            ):
                raise PermissionDenied("ロール削除権限がありません")

        # Check if role is assigned to any users
        active_assignments = (
            db.query(UserRole)
            .filter(UserRole.role_id == role_id)
            .filter(
                or_(
                    UserRole.expires_at.is_(None),
                    UserRole.expires_at > datetime.now(timezone.utc),
                )
            )
            .first()
        )

        if active_assignments:
            raise ValueError(
                "このロールは現在ユーザーに割り当てられているため削除できません"
            )

        # Soft delete
        role.soft_delete(deleter.id)
        db.commit()

        return True
=======
    def get_user_role_response(self, user_role: UserRole) -> UserRoleResponse:
        """Get user role response."""
        # Load relationships if not already loaded
        user_role_with_relations = self.db.get(
            UserRole,
            user_role.id,
            options=[
                selectinload(UserRole.role),
                selectinload(UserRole.organization),
                selectinload(UserRole.department),
                selectinload(UserRole.assigned_by_user),
                selectinload(UserRole.approved_by_user),
            ],
        )

        # Use the new factory method to properly handle relationships
        from app.schemas.role import UserRoleInfo

        user_role_info = UserRoleInfo.from_user_role_model(user_role_with_relations)

        # Add audit info and convert to UserRoleResponse
        return UserRoleResponse(
            **user_role_info.model_dump(),
            effective_permissions=user_role_with_relations.get_effective_permissions(),
            created_at=user_role_with_relations.created_at,
            created_by=user_role_with_relations.created_by,
            updated_at=user_role_with_relations.updated_at,
            updated_by=user_role_with_relations.updated_by,
        )
>>>>>>> origin/main
