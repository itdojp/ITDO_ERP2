"""Role service implementation."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.exceptions import NotFound, PermissionDenied
from app.models.role import Role, UserRole
from app.models.user import User
from app.schemas.role import (
    RoleCreate,
    RoleList,
    RoleResponse,
    RoleUpdate,
    UserRoleCreate,
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
            if organization_id and not user.has_permission("role:create", organization_id):
                raise PermissionDenied("ロール作成権限がありません")
            elif not organization_id and not user.is_superuser:
                raise PermissionDenied("システムロール作成には管理者権限が必要です")

        # Check if role code already exists
        existing_role = Role.get_by_code(db, data.code)
        if existing_role:
            raise ValueError(f"ロールコード '{data.code}' は既に存在します")

        # Create role
        role = Role.create(
            db=db,
            code=data.code,
            name=data.name,
            description=data.description,
            permissions=data.permissions,
            created_by=user.id,
        )

        return role

    def assign_role_to_user(
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
        user_role = UserRole.create(
            db=db,
            user_id=user_id,
            role_id=role_id,
            organization_id=organization_id,
            department_id=department_id,
            assigned_by=assigner.id,
            expires_at=expires_at,
        )

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
            if organization_id and not requester.has_permission("role:read", organization_id):
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

        # Remove the assignment
        db.delete(user_role)
        db.commit()

        return True

    def get_role_permissions(
        self,
        role_id: int,
        requester: User,
        db: Session,
        organization_id: Optional[int] = None,
    ) -> List[str]:
        """
        Get permissions for a specific role.
        
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
            if organization_id and not requester.has_permission("role:read", organization_id):
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
            if organization_id and not updater.has_permission("role:update", organization_id):
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
        )

        if department_id is not None:
            query = query.filter(UserRole.department_id == department_id)

        if not include_expired:
            query = query.filter(
                or_(
                    UserRole.expires_at.is_(None),
                    UserRole.expires_at > datetime.now(timezone.utc),
                )
            )

        return query.all()

    # Additional utility methods for role management

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
            if organization_id and not requester.has_permission("role:read", organization_id):
                raise PermissionDenied("ロール情報の閲覧権限がありません")

        # Build query
        query = db.query(Role).filter(Role.is_active == True)

        if not include_system:
            query = query.filter(Role.is_system == False)

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

        return RoleList(
            items=[RoleResponse.model_validate(role) for role in items],
            total=total,
            page=page,
            limit=limit,
        )

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
            if organization_id and not requester.has_permission("role:read", organization_id):
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
            if organization_id and not updater.has_permission("role:update", organization_id):
                raise PermissionDenied("ロール更新権限がありません")

        # Update role
        update_data = data.dict(exclude_unset=True)
        role.update(db=db, updated_by=updater.id, **update_data)

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
            if organization_id and not deleter.has_permission("role:delete", organization_id):
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
            raise ValueError("このロールは現在ユーザーに割り当てられているため削除できません")

        # Soft delete
        role.delete()
        db.add(role)
        db.commit()

        return True