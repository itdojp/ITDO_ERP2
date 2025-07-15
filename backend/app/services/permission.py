"""Permission management service."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError, PermissionDenied
from app.models.audit import AuditLog
from app.models.permission import Permission
from app.models.role import Role, RolePermission, UserRole
from app.models.user import User
from app.schemas.permission_management import (
    PermissionAuditLog,
    PermissionBulkOperationResponse,
    PermissionCheckResponse,
    PermissionDetail,
    PermissionInheritanceInfo,
    PermissionTemplate,
    UserEffectivePermissions,
)


class PermissionService:
    """Service for managing permissions."""

    def __init__(self, db: Session):
        """Initialize permission service."""
        self.db = db

    def get_user_effective_permissions(self, user_id: int) -> UserEffectivePermissions:
        """Get user's effective permissions including inheritance."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with id {user_id} not found")

        # Get direct permissions (if any custom implementation exists)
        direct_permissions = []

        # Get permissions from roles
        inherited_permissions = []
        all_permission_codes = set()

        # Get user's active roles
        user_roles = (
            self.db.query(UserRole)
            .filter(
                UserRole.user_id == user_id,
                UserRole.is_active,
                or_(
                    UserRole.expires_at.is_(None),
                    UserRole.expires_at > datetime.utcnow(),
                ),
            )
            .all()
        )

        for user_role in user_roles:
            # Get role permissions
            role_permissions = (
                self.db.query(RolePermission)
                .join(Permission)
                .filter(
                    RolePermission.role_id == user_role.role_id,
                    Permission.is_active,
                )
                .all()
            )

            for rp in role_permissions:
                perm = rp.permission
                all_permission_codes.add(perm.code)

                inherited_permissions.append(
                    PermissionInheritanceInfo(
                        permission=PermissionDetail(
                            id=perm.id,
                            code=perm.code,
                            name=perm.name,
                            description=perm.description,
                            category=perm.category,
                            is_active=perm.is_active,
                            is_system=perm.is_system,
                        ),
                        source="role",
                        source_id=user_role.role_id,
                        source_name=user_role.role.name,
                        inherited_at=rp.granted_at,
                        can_override=not perm.is_system,
                    )
                )

        # TODO: Add department and organization level permissions

        return UserEffectivePermissions(
            user_id=user_id,
            direct_permissions=direct_permissions,
            inherited_permissions=inherited_permissions,
            overridden_permissions=[],
            all_permission_codes=list(all_permission_codes),
        )

    def check_user_permissions(
        self,
        user_id: int,
        permission_codes: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> PermissionCheckResponse:
        """Check if user has specific permissions."""
        effective_perms = self.get_user_effective_permissions(user_id)

        results = {}
        missing_permissions = []

        for code in permission_codes:
            has_permission = code in effective_perms.all_permission_codes
            results[code] = has_permission
            if not has_permission:
                missing_permissions.append(code)

        return PermissionCheckResponse(
            user_id=user_id,
            results=results,
            missing_permissions=missing_permissions,
        )

    def user_has_permission(self, user_id: int, permission_code: str) -> bool:
        """Check if user has a specific permission."""
        result = self.check_user_permissions(user_id, [permission_code])
        return result.results.get(permission_code, False)

    def assign_permissions_to_role(
        self, role_id: int, permission_ids: List[int], granted_by: Optional[int] = None
    ) -> int:
        """Assign permissions to a role."""
        # Verify role exists
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise ValueError(f"Role with id {role_id} not found")

        # Verify all permissions exist
        permissions = (
            self.db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
        )

        if len(permissions) != len(permission_ids):
            raise ValueError("One or more permissions not found")

        # Remove existing permissions for this role
        self.db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()

        # Add new permissions
        count = 0
        for permission in permissions:
            role_permission = RolePermission(
                role_id=role_id,
                permission_id=permission.id,
                granted_by=granted_by,
            )
            self.db.add(role_permission)
            count += 1

            # Log the assignment
            self._log_permission_change(
                user_id=granted_by,
                permission_id=permission.id,
                action="granted",
                target_type="role",
                target_id=role_id,
                reason=f"Assigned to role {role.name}",
            )

        self.db.commit()
        return count

    def create_user_permission_override(
        self,
        user_id: int,
        permission_id: int,
        action: str,
        reason: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        created_by: Optional[int] = None,
    ) -> Any:
        """Create a user-specific permission override."""
        # Verify user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with id {user_id} not found")

        # Verify permission exists
        permission = (
            self.db.query(Permission).filter(Permission.id == permission_id).first()
        )
        if not permission:
            raise ValueError(f"Permission with id {permission_id} not found")

        if action not in ["grant", "revoke"]:
            raise BusinessLogicError("Action must be 'grant' or 'revoke'")

        # TODO: Implement actual override storage
        # For now, log the action
        self._log_permission_change(
            user_id=user_id,
            permission_id=permission_id,
            action=action,
            target_type="user",
            target_id=user_id,
            reason=reason,
            performed_by=created_by,
        )

        # Return a mock override object
        return type("obj", (object,), {"id": 1})()

    def get_permission_audit_log(
        self,
        user_id: Optional[int] = None,
        permission_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[PermissionAuditLog]:
        """Get permission change audit logs."""
        query = self.db.query(AuditLog).filter(AuditLog.resource_type == "permission")

        if user_id:
            query = query.filter(AuditLog.user_id == user_id)

        if permission_id:
            query = query.filter(AuditLog.entity_id == permission_id)

        logs = (
            query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset).all()
        )

        result = []
        for log in logs:
            result.append(
                PermissionAuditLog(
                    id=log.id,
                    user_id=log.user_id,
                    permission_id=log.entity_id,
                    action=log.action,
                    performed_by=log.user_id,
                    performed_at=log.created_at,
                    reason=log.changes.get("reason") if log.changes else None,
                    previous_state=log.old_values,
                    new_state=log.new_values,
                )
            )

        return result

    def list_permission_templates(
        self, is_active: Optional[bool] = None
    ) -> List[PermissionTemplate]:
        """List available permission templates."""
        # TODO: Implement actual template storage
        # For now, return predefined templates

        templates = []

        # Admin template
        admin_perms = self.db.query(Permission).all()
        templates.append(
            PermissionTemplate(
                id=1,
                name="System Administrator",
                description="Full system access",
                permissions=[self._permission_to_detail(p) for p in admin_perms],
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )

        # Manager template
        manager_perms = (
            self.db.query(Permission)
            .filter(Permission.category.in_(["users", "departments", "organizations"]))
            .all()
        )
        templates.append(
            PermissionTemplate(
                id=2,
                name="Department Manager",
                description="Department management permissions",
                permissions=[self._permission_to_detail(p) for p in manager_perms],
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )

        # User template
        user_perms = (
            self.db.query(Permission)
            .filter(Permission.category.in_(["users"]), Permission.code.like("%.read"))
            .all()
        )
        templates.append(
            PermissionTemplate(
                id=3,
                name="Regular User",
                description="Basic user permissions",
                permissions=[self._permission_to_detail(p) for p in user_perms],
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )

        if is_active is not None:
            templates = [t for t in templates if t.is_active == is_active]

        return templates

    def create_permission_template(
        self,
        name: str,
        permission_ids: List[int],
        description: Optional[str] = None,
        is_active: bool = True,
        created_by: Optional[int] = None,
    ) -> PermissionTemplate:
        """Create a new permission template."""
        # Verify permissions exist
        permissions = (
            self.db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
        )

        if len(permissions) != len(permission_ids):
            raise ValueError("One or more permissions not found")

        # TODO: Implement actual template storage
        # For now, return a mock template
        return PermissionTemplate(
            id=4,
            name=name,
            description=description,
            permissions=[self._permission_to_detail(p) for p in permissions],
            is_active=is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    def execute_bulk_permission_operation(
        self,
        operation: str,
        target_type: str,
        target_ids: List[int],
        permission_ids: List[int],
        reason: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        performed_by: Optional[int] = None,
    ) -> PermissionBulkOperationResponse:
        """Execute bulk permission operations."""
        if operation not in ["grant", "revoke", "sync"]:
            raise ValueError("Invalid operation type")

        if target_type not in ["users", "roles", "departments"]:
            raise ValueError("Invalid target type")

        operation_id = str(uuid.uuid4())
        success_count = 0
        failure_count = 0
        failures = []

        # Verify permissions exist
        permissions = (
            self.db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
        )

        if len(permissions) != len(permission_ids):
            raise ValueError("One or more permissions not found")

        if target_type == "roles":
            for role_id in target_ids:
                try:
                    if operation == "grant" or operation == "sync":
                        self.assign_permissions_to_role(
                            role_id, permission_ids, granted_by=performed_by
                        )
                    # TODO: Implement revoke
                    success_count += 1
                except Exception as e:
                    failure_count += 1
                    failures.append({"target_id": role_id, "error": str(e)})

        # TODO: Implement for users and departments

        return PermissionBulkOperationResponse(
            operation_id=operation_id,
            success_count=success_count,
            failure_count=failure_count,
            failures=failures if failures else None,
        )

    def _permission_to_detail(self, permission: Permission) -> PermissionDetail:
        """Convert Permission model to PermissionDetail schema."""
        return PermissionDetail(
            id=permission.id,
            code=permission.code,
            name=permission.name,
            description=permission.description,
            category=permission.category,
            is_active=permission.is_active,
            is_system=permission.is_system,
        )

    def _log_permission_change(
        self,
        user_id: Optional[int],
        permission_id: int,
        action: str,
        target_type: str,
        target_id: int,
        reason: Optional[str] = None,
        performed_by: Optional[int] = None,
    ) -> None:
        """Log permission changes to audit log."""
        audit_log = AuditLog(
            user_id=performed_by or user_id,
            action=action,
            resource_type="permission",
            resource_id=permission_id,
            changes={
                "target_type": target_type,
                "target_id": target_id,
                "reason": reason,
            },
        )
        self.db.add(audit_log)
        self.db.commit()

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
            all_permissions = db.query(Permission).filter(Permission.is_active).all()
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
