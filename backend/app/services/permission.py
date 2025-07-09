"""Permission checking service for RBAC system."""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import PermissionDenied
from app.models.permission import Permission
from app.models.role import RolePermission, UserRole
from app.models.user import User


class PermissionService:
    """Service for checking user permissions."""

    def has_permission(
        self,
        user: User,
        permission_code: str,
        organization_id: Optional[int] = None,
        department_id: Optional[int] = None,
        db: Session = None,
    ) -> bool:
        """Check if user has specific permission.

        Args:
            user: User to check permissions for
            permission_code: Permission code to check (e.g., "task.create")
            organization_id: Optional organization context
            department_id: Optional department context
            db: Database session

        Returns:
            True if user has permission, False otherwise
        """
        if not user.is_active:
            return False

        # Superusers have all permissions
        if user.is_superuser:
            return True

        # If no db session provided, can't check role-based permissions
        if db is None:
            return False

        # Use user's organization if not specified
        if organization_id is None:
            organization_id = getattr(user, "organization_id", None)

        # Check if user has the permission through their roles
        return self._check_role_permissions(
            user.id, permission_code, organization_id, department_id, db
        )

    def _check_role_permissions(
        self,
        user_id: int,
        permission_code: str,
        organization_id: Optional[int],
        department_id: Optional[int],
        db: Session,
    ) -> bool:
        """Check permissions through user roles."""
        # Get user's active roles in the specified context
        user_roles_query = db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.is_active,
            UserRole.organization_id == organization_id,
        )

        if department_id:
            user_roles_query = user_roles_query.filter(
                UserRole.department_id == department_id
            )

        user_roles = user_roles_query.all()

        if not user_roles:
            return False

        # Get permission ID
        permission = (
            db.query(Permission)
            .filter(Permission.code == permission_code, Permission.is_active)
            .first()
        )

        if not permission:
            return False

        # Check if any of the user's roles has this permission
        role_ids = [ur.role_id for ur in user_roles]

        role_permission = (
            db.query(RolePermission)
            .filter(
                RolePermission.role_id.in_(role_ids),
                RolePermission.permission_id == permission.id,
            )
            .first()
        )

        return role_permission is not None

    def require_permission(
        self,
        user: User,
        permission_code: str,
        organization_id: Optional[int] = None,
        department_id: Optional[int] = None,
        db: Session = None,
    ) -> None:
        """Require user to have specific permission, raise exception if not.

        Args:
            user: User to check permissions for
            permission_code: Permission code to check (e.g., "task.create")
            organization_id: Optional organization context
            department_id: Optional department context
            db: Database session

        Raises:
            PermissionDenied: If user doesn't have permission
        """
        if not self.has_permission(
            user, permission_code, organization_id, department_id, db
        ):
            raise PermissionDenied(f"User does not have permission: {permission_code}")

    def get_user_permissions(
        self,
        user: User,
        organization_id: Optional[int] = None,
        department_id: Optional[int] = None,
        db: Session = None,
    ) -> List[str]:
        """Get list of all permissions for a user.

        Args:
            user: User to get permissions for
            organization_id: Optional organization context
            department_id: Optional department context
            db: Database session

        Returns:
            List of permission codes
        """
        if not user.is_active:
            return []

        # Superusers have all permissions
        if user.is_superuser:
            if db is None:
                return []
            all_permissions = (
                db.query(Permission).filter(Permission.is_active).all()
            )
            return [p.code for p in all_permissions]

        if db is None:
            return []

        # Use user's organization if not specified
        if organization_id is None:
            organization_id = getattr(user, "organization_id", None)

        # Get user's active roles
        user_roles_query = db.query(UserRole).filter(
            UserRole.user_id == user.id,
            UserRole.is_active,
            UserRole.organization_id == organization_id,
        )

        if department_id:
            user_roles_query = user_roles_query.filter(
                UserRole.department_id == department_id
            )

        user_roles = user_roles_query.all()

        if not user_roles:
            return []

        # Get all permissions for these roles
        role_ids = [ur.role_id for ur in user_roles]

        permissions = (
            db.query(Permission)
            .join(RolePermission)
            .filter(
                RolePermission.role_id.in_(role_ids),
                Permission.is_active,
            )
            .distinct()
            .all()
        )

        return [p.code for p in permissions]


# Global permission service instance
permission_service = PermissionService()
