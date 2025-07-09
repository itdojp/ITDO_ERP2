"""Cross-service integration for permission system."""

import asyncio
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Session

from app.core.cache import CacheManager
from app.models.department import Department
from app.models.organization import Organization
from app.models.role import Role, UserRole
from app.models.user import User
from app.services.organization import OrganizationService
from app.services.permission import PermissionService
from app.services.role import RoleService
from app.types import DepartmentId, OrganizationId, UserId


class CrossServiceIntegrator:
    """Manages cross-service interactions and permission propagation."""

    def __init__(
        self,
        db: Session,
        cache_manager: Optional[CacheManager] = None,
    ):
        """Initialize cross-service integrator."""
        self.db = db
        self.cache_manager = cache_manager
        self.organization_service = OrganizationService(db)
        self.permission_service = PermissionService(db, cache_manager)
        self.role_service = RoleService(db)

    async def handle_user_organization_change(
        self,
        user_id: UserId,
        old_organization_id: Optional[OrganizationId],
        new_organization_id: OrganizationId,
        transferred_by: Optional[UserId] = None,
    ) -> Dict[str, Any]:
        """Handle user organization change with permission updates."""
        results: Dict[str, Any] = {
            "user_id": user_id,
            "old_organization_id": old_organization_id,
            "new_organization_id": new_organization_id,
            "roles_transferred": 0,
            "roles_added": 0,
            "roles_removed": 0,
            "permissions_updated": False,
        }

        # Get user
        user = self.db.get(User, user_id)
        if not user:
            results["error"] = "User not found"
            return results

        # Validate new organization
        if not self.organization_service.validate_organization_exists(new_organization_id):
            results["error"] = "New organization not found or inactive"
            return results

        # Get current roles in old organization
        old_roles = []
        if old_organization_id:
            old_roles = self.db.query(UserRole).filter(
                UserRole.user_id == user_id,
                UserRole.organization_id == old_organization_id,
                UserRole.is_active == True,
            ).all()

        # Check which roles can be transferred
        transferable_roles = []
        for user_role in old_roles:
            role = user_role.role
            if role and not role.is_system:
                # Check if equivalent role exists in new organization
                equivalent_role = self.db.query(Role).filter(
                    Role.code == role.code,
                    Role.organization_id == new_organization_id,
                    Role.is_active == True,
                    Role.is_deleted == False,
                ).first()

                if equivalent_role:
                    transferable_roles.append((user_role, equivalent_role))

        # Deactivate old roles
        for user_role in old_roles:
            user_role.is_active = False
            results["roles_removed"] = results["roles_removed"] + 1

        # Create new role assignments
        for old_user_role, new_role in transferable_roles:
            new_user_role = UserRole(
                user_id=user_id,
                role_id=new_role.id,
                organization_id=new_organization_id,
                department_id=None,  # Will be set later if needed
                assigned_by=transferred_by,
                is_active=True,
                is_primary=old_user_role.is_primary,
                notes=f"Transferred from org {old_organization_id}",
            )
            self.db.add(new_user_role)
            results["roles_transferred"] = results["roles_transferred"] + 1

        # Add default role if no roles transferred
        if not transferable_roles:
            default_role = self.db.query(Role).filter(
                Role.code == "system.user",
                Role.is_system == True,
                Role.is_active == True,
            ).first()

            if default_role:
                default_user_role = UserRole(
                    user_id=user_id,
                    role_id=default_role.id,
                    organization_id=new_organization_id,
                    assigned_by=transferred_by,
                    is_active=True,
                    is_primary=True,
                    notes="Default role assigned during organization transfer",
                )
                self.db.add(default_user_role)
                results["roles_added"] = results["roles_added"] + 1

        # Commit changes
        self.db.commit()

        # Invalidate permission caches
        await self.permission_service.invalidate_user_permission_cache(
            user_id, old_organization_id
        )
        await self.permission_service.invalidate_user_permission_cache(
            user_id, new_organization_id
        )

        results["permissions_updated"] = True

        return results

    async def handle_department_transfer(
        self,
        user_id: UserId,
        old_department_id: Optional[DepartmentId],
        new_department_id: DepartmentId,
        transferred_by: Optional[UserId] = None,
    ) -> Dict[str, Any]:
        """Handle user department transfer with permission inheritance."""
        results: Dict[str, Any] = {
            "user_id": user_id,
            "old_department_id": old_department_id,
            "new_department_id": new_department_id,
            "roles_updated": 0,
            "permissions_inherited": 0,
        }

        # Get department and organization info
        new_dept = self.db.get(Department, new_department_id)
        if not new_dept:
            results["error"] = "New department not found"
            return results

        organization_id = new_dept.organization_id

        # Update user roles with new department
        user_roles = self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.organization_id == organization_id,
            UserRole.is_active == True,
        ).all()

        for user_role in user_roles:
            # Check if role is department-specific
            if user_role.role.role_type == "department":
                user_role.department_id = new_department_id
                results["roles_updated"] = results["roles_updated"] + 1

        # Check for department-specific roles to inherit
        dept_roles = self.db.query(Role).filter(
            Role.role_type == "department",
            Role.organization_id == organization_id,
            Role.is_active == True,
            Role.is_deleted == False,
        ).all()

        for role in dept_roles:
            # Check if user should get this role
            existing = self.db.query(UserRole).filter(
                UserRole.user_id == user_id,
                UserRole.role_id == role.id,
                UserRole.organization_id == organization_id,
                UserRole.department_id == new_department_id,
            ).first()

            if not existing:
                new_user_role = UserRole(
                    user_id=user_id,
                    role_id=role.id,
                    organization_id=organization_id,
                    department_id=new_department_id,
                    assigned_by=transferred_by,
                    is_active=True,
                    notes="Inherited from department transfer",
                )
                self.db.add(new_user_role)
                results["permissions_inherited"] = results["permissions_inherited"] + 1

        self.db.commit()

        # Invalidate caches
        await self.permission_service.invalidate_user_permission_cache(
            user_id, organization_id
        )

        return results

    async def handle_organization_hierarchy_change(
        self, organization_id: OrganizationId, changed_by: Optional[UserId] = None
    ) -> Dict[str, Any]:
        """Handle organization hierarchy changes and recalculate permissions."""
        results: Dict[str, Any] = {
            "organization_id": organization_id,
            "users_affected": 0,
            "roles_recalculated": 0,
            "permissions_updated": False,
        }

        # Get all users in organization and its subsidiaries
        affected_users = self.db.query(User).join(UserRole).filter(
            UserRole.organization_id == organization_id,
            UserRole.is_active == True,
            User.is_active == True,
        ).distinct().all()

        # Get organization hierarchy
        org_hierarchy = self.organization_service.get_organization_hierarchy(organization_id)

        # Recalculate permissions for each user
        for user in affected_users:
            # Get user's roles
            user_roles = self.db.query(UserRole).filter(
                UserRole.user_id == user.id,
                UserRole.organization_id == organization_id,
                UserRole.is_active == True,
            ).all()

            for user_role in user_roles:
                if user_role.role:
                    # Trigger permission recalculation by clearing cache
                    await self.permission_service.invalidate_user_permission_cache(
                        user.id, organization_id
                    )
                    results["roles_recalculated"] = results["roles_recalculated"] + 1

            results["users_affected"] = results["users_affected"] + 1

        # Invalidate organization cache
        await self.permission_service.invalidate_organization_cache(organization_id)
        results["permissions_updated"] = True

        return results

    def integrate_task_permissions(
        self,
        user_id: UserId,
        task_data: Dict[str, Any],
        organization_id: OrganizationId,
        department_id: Optional[DepartmentId] = None,
    ) -> Dict[str, bool]:
        """Integrate task permissions with role-based access control."""
        permissions = {
            "can_view": False,
            "can_edit": False,
            "can_delete": False,
            "can_assign": False,
            "can_approve": False,
        }

        # Get user permissions
        user_perms = self.permission_service.get_user_permissions(
            user_id, organization_id, department_id
        )

        # Check task-specific permissions
        task_status = task_data.get("status", "")
        task_priority = task_data.get("priority", "")
        task_assignee = task_data.get("assigned_to")

        # Basic view permission
        if "task.view" in user_perms or "task.*" in user_perms:
            permissions["can_view"] = True

        # Edit permission
        if "task.edit" in user_perms or "task.*" in user_perms:
            permissions["can_edit"] = True

            # Additional checks for edit
            if task_status == "completed" and "task.edit.completed" not in user_perms:
                permissions["can_edit"] = False

        # Delete permission
        if "task.delete" in user_perms or "task.*" in user_perms:
            permissions["can_delete"] = True

            # Cannot delete if task is in progress by someone else
            if task_assignee and task_assignee != user_id and task_status == "in_progress":
                permissions["can_delete"] = False

        # Assignment permission
        if "task.assign" in user_perms or "task.*" in user_perms:
            permissions["can_assign"] = True

        # Approval permission
        if ("task.approve" in user_perms or
            "task.*" in user_perms or
            "admin.all" in user_perms):
            permissions["can_approve"] = True

        # Special rules for task owners
        if task_assignee == user_id:
            permissions["can_view"] = True
            permissions["can_edit"] = True

        # High priority tasks require special permission
        if task_priority == "high" and "task.high_priority" not in user_perms:
            permissions["can_edit"] = False
            permissions["can_delete"] = False

        return permissions

    def get_filtered_tasks_for_user(
        self,
        user_id: UserId,
        organization_id: OrganizationId,
        department_id: Optional[DepartmentId] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Get tasks filtered by user permissions."""
        filters = filters or {}

        # Get user permissions
        user_perms = self.permission_service.get_user_permissions(
            user_id, organization_id, department_id
        )

        # Build base query constraints
        constraints: Dict[str, Any] = {
            "organization_id": organization_id,
        }

        # Department-level filtering
        if department_id and "task.view.all_departments" not in user_perms:
            constraints["department_id"] = department_id

        # Status-based filtering
        if "task.view.all_status" not in user_perms:
            # Can only see own tasks and assigned tasks
            constraints["visibility_filter"] = {
                "or": [
                    {"created_by": user_id},
                    {"assigned_to": user_id},
                ]
            }

        # Priority-based filtering
        if "task.view.high_priority" not in user_perms:
            constraints["priority_filter"] = {"ne": "high"}

        return {
            "constraints": constraints,
            "permissions": user_perms,
            "can_create": "task.create" in user_perms or "task.*" in user_perms,
            "can_bulk_edit": "task.bulk_edit" in user_perms or "admin.all" in user_perms,
        }

    async def bulk_update_user_permissions(
        self,
        user_ids: List[UserId],
        organization_id: OrganizationId,
        operation: str,
        role_changes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Bulk update permissions for multiple users."""
        results: Dict[str, Any] = {
            "operation": operation,
            "total_users": len(user_ids),
            "successful": 0,
            "failed": 0,
            "errors": [],
        }

        tasks = []
        for user_id in user_ids:
            if operation == "refresh_cache":
                tasks.append(
                    self.permission_service.invalidate_user_permission_cache(
                        user_id, organization_id
                    )
                )
            elif operation == "recalculate_permissions":
                # This would trigger recalculation on next access
                tasks.append(
                    self.permission_service.invalidate_user_permission_cache(
                        user_id, organization_id
                    )
                )

        if tasks:
            completed = await asyncio.gather(*tasks, return_exceptions=True)
            for result in completed:
                if isinstance(result, Exception):
                    results["failed"] = results["failed"] + 1
                    results["errors"].append(str(result))
                else:
                    results["successful"] = results["successful"] + 1

        return results

    def validate_cross_service_permissions(
        self,
        user_id: UserId,
        action: str,
        resource_type: str,
        resource_id: int,
        organization_id: OrganizationId,
    ) -> bool:
        """Validate permissions across different services."""
        # Get user permissions
        user_perms = self.permission_service.get_user_permissions(
            user_id, organization_id
        )

        # Define permission mapping
        permission_map = {
            "organization": {
                "view": ["org.view", "admin.all"],
                "edit": ["org.edit", "admin.all"],
                "delete": ["org.delete", "admin.all"],
            },
            "department": {
                "view": ["dept.view", "org.view", "admin.all"],
                "edit": ["dept.edit", "org.edit", "admin.all"],
                "delete": ["dept.delete", "org.delete", "admin.all"],
            },
            "user": {
                "view": ["user.view", "admin.all"],
                "edit": ["user.edit", "admin.all"],
                "delete": ["user.delete", "admin.all"],
            },
            "task": {
                "view": ["task.view", "task.*", "admin.all"],
                "edit": ["task.edit", "task.*", "admin.all"],
                "delete": ["task.delete", "task.*", "admin.all"],
                "assign": ["task.assign", "task.*", "admin.all"],
            },
        }

        required_perms = permission_map.get(resource_type, {}).get(action, [])

        # Check if user has any of the required permissions
        return any(perm in user_perms for perm in required_perms)

    def get_service_integration_health(self) -> Dict[str, Any]:
        """Get health status of cross-service integration."""
        health: Dict[str, Any] = {
            "status": "healthy",
            "services": {},
            "cache_status": "unknown",
            "integration_points": 0,
        }

        try:
            # Check organization service
            org_count = self.db.query(Organization).filter(
                Organization.is_active == True
            ).count()
            health["services"]["organization"] = {
                "status": "healthy",
                "active_count": org_count,
            }

            # Check role service
            role_count = self.db.query(Role).filter(
                Role.is_active == True,
                Role.is_deleted == False,
            ).count()
            health["services"]["role"] = {
                "status": "healthy",
                "active_count": role_count,
            }

            # Check permission service
            perm_count = self.db.query(UserRole).filter(
                UserRole.is_active == True
            ).count()
            health["services"]["permission"] = {
                "status": "healthy",
                "active_assignments": perm_count,
            }

            # Check cache if available
            if self.cache_manager:
                health["cache_status"] = "available"
            else:
                health["cache_status"] = "not_configured"

            health["integration_points"] = 4  # Number of integration methods

        except Exception as e:
            health["status"] = "degraded"
            health["error"] = str(e)

        return health
