"""ERP Integration Service for Organization + Role + Department + Task management."""

from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.role import Role
from app.schemas.organization import OrganizationCreate
from app.schemas.role import RoleCreate
from app.schemas.task import TaskCreate
from app.services.department import DepartmentService
from app.services.organization import OrganizationService
from app.services.role import RoleService
from app.services.task import TaskService
from app.types import OrganizationId, UserId


class CompleteOrganizationSetup:
    """Schema for complete organization setup."""

    def __init__(
        self,
        organization: OrganizationCreate,
        departments: Optional[List[Dict[str, Any]]] = None,
        custom_roles: Optional[List[Dict[str, Any]]] = None,
    ):
        self.organization = organization
        self.departments = departments or []
        self.custom_roles = custom_roles or []


class CompleteOrganizationResult:
    """Result of complete organization setup."""

    def __init__(
        self,
        organization: Organization,
        roles: List[Role],
        departments: List[Any],
        admin_assignments: List[Role],
    ):
        self.organization = organization
        self.roles = roles
        self.departments = departments
        self.admin_assignments = admin_assignments


class ERPIntegrationService:
    """ERP Integration Service (Organization + Role + Department + Task)."""

    def __init__(
        self,
        db: Session,
        org_service: Optional[OrganizationService] = None,
        role_service: Optional[RoleService] = None,
        dept_service: Optional[DepartmentService] = None,
        task_service: Optional[TaskService] = None,
    ):
        self.db = db
        self.org_service = org_service or OrganizationService(db)
        self.role_service = role_service or RoleService(db)
        self.dept_service = dept_service or DepartmentService(db)
        self.task_service = task_service or TaskService(db)

    async def setup_complete_organization(
        self,
        setup_data: CompleteOrganizationSetup,
        admin_user_id: UserId,
    ) -> CompleteOrganizationResult:
        """Complete organization setup (Phase 3 integration)."""
        # 1. Create organization
        organization = self.org_service.create_organization(
            setup_data.organization, admin_user_id
        )

        # 2. Create default roles
        default_roles = []
        role_templates = [
            {
                "name": "org_admin",
                "description": "Organization Administrator",
                "permissions": self._get_default_permissions("org_admin"),
            },
            {
                "name": "dept_manager",
                "description": "Department Manager",
                "permissions": self._get_default_permissions("dept_manager"),
            },
            {
                "name": "team_lead",
                "description": "Team Leader",
                "permissions": self._get_default_permissions("team_lead"),
            },
            {
                "name": "member",
                "description": "Team Member",
                "permissions": self._get_default_permissions("member"),
            },
        ]

        for role_template in role_templates:
            role_data = RoleCreate(
                code=f"{role_template['name']}_{organization.id}",
                name=role_template["name"],
                description=role_template["description"],
                organization_id=organization.id,
                permissions=role_template["permissions"],
                role_type="organization",
            )
            role = self.role_service.create_role(role_data, admin_user_id)
            default_roles.append(role)

        # 3. Create department structure
        departments = []
        for dept_data in setup_data.departments:
            dept = self.dept_service.create_department(
                dept_data, organization.id, admin_user_id
            )
            departments.append(dept)

        # 4. Assign admin user the org_admin role
        admin_role = next(r for r in default_roles if "org_admin" in r.code)
        self.role_service.assign_user_role(
            user_id=admin_user_id,
            role_id=admin_role.id,
            organization_id=organization.id,
            assigned_by=admin_user_id,
        )

        return CompleteOrganizationResult(
            organization=organization,
            roles=default_roles,
            departments=departments,
            admin_assignments=[admin_role],
        )

    async def create_department_task_with_permissions(
        self,
        task_data: TaskCreate,
        department_id: int,
        user_id: UserId,
    ) -> Any:
        """Create department task with permission checks."""
        # 1. Check department access permissions
        can_access = await self._can_user_access_department(user_id, department_id)
        if not can_access:
            raise HTTPException(
                status_code=403,
                detail="No access to this department",
            )

        # 2. Check task creation permissions (role-based)
        can_create_tasks = await self._has_permission(
            user_id, "task:create", {"department_id": department_id}
        )
        if not can_create_tasks:
            raise HTTPException(
                status_code=403,
                detail="No permission to create tasks in this department",
            )

        # 3. Create task
        return self.task_service.create_task(task_data, user_id)

    async def get_complete_structure(
        self, org_id: OrganizationId, user_id: UserId
    ) -> Dict[str, Any]:
        """Get complete organization structure (departments, roles, tasks)."""
        # Check organization access
        can_access = await self._can_user_access_organization(user_id, org_id)
        if not can_access:
            raise HTTPException(
                status_code=403,
                detail="No access to this organization",
            )

        # Get organization
        organization = self.org_service.get_organization(org_id)
        if not organization:
            raise HTTPException(
                status_code=404,
                detail="Organization not found",
            )

        # Get departments
        departments, _ = self.dept_service.list_departments(
            organization_id=org_id, skip=0, limit=1000
        )

        # Get roles
        roles = self.role_service.get_organization_roles(org_id)

        # Get user's roles in this organization
        user_roles = self.role_service.get_user_roles(
            user_id=user_id, organization_id=org_id
        )

        # Get task summary
        tasks_summary = await self._get_organization_tasks_summary(org_id, user_id)

        return {
            "organization": {
                "id": organization.id,
                "code": organization.code,
                "name": organization.name,
                "is_active": organization.is_active,
            },
            "departments": [
                {
                    "id": dept.id,
                    "code": dept.code,
                    "name": dept.name,
                    "is_active": dept.is_active,
                }
                for dept in departments
            ],
            "roles": [
                {
                    "id": role.id,
                    "code": role.code,
                    "name": role.name,
                    "role_type": role.role_type,
                    "permissions": role.permissions,
                }
                for role in roles
            ],
            "user_roles": [
                {
                    "id": ur.id,
                    "role_id": ur.role_id,
                    "role_name": ur.role.name if ur.role else None,
                    "is_active": ur.is_active,
                }
                for ur in user_roles
            ],
            "tasks_summary": tasks_summary,
        }

    def _get_default_permissions(self, role_name: str) -> Dict[str, Any]:
        """Get default permissions based on role name."""
        permission_map = {
            "org_admin": {
                "organization": {"*": True},
                "department": {"*": True},
                "role": {"*": True},
                "user": {"*": True},
                "task": {"*": True},
            },
            "dept_manager": {
                "department": {"read": True, "update": True},
                "role": {"read": True},
                "user": {"read": True},
                "task": {"*": True},
            },
            "team_lead": {
                "task": {"create": True, "read": True, "update": True, "assign": True},
                "user": {"read": True},
            },
            "member": {
                "task": {"read": True, "update": True},
            },
        }
        return permission_map.get(role_name, {})

    async def _can_user_access_department(
        self, user_id: UserId, department_id: int
    ) -> bool:
        """Check if user can access department."""
        # Get user's roles and check for department access
        # For now, simplified check - can be expanded with proper RBAC
        try:
            # Check if user has any role that allows department access
            user_roles = self.role_service.get_user_roles(user_id)
            return len(user_roles) > 0  # Simplified check
        except Exception:
            return False

    async def _can_user_access_organization(
        self, user_id: UserId, org_id: OrganizationId
    ) -> bool:
        """Check if user can access organization."""
        try:
            # Check if user has any role in this organization
            user_roles = self.role_service.get_user_roles(
                user_id, organization_id=org_id
            )
            return len(user_roles) > 0
        except Exception:
            return False

    async def _has_permission(
        self, user_id: UserId, permission: str, context: Dict[str, Any]
    ) -> bool:
        """Check if user has specific permission."""
        # For now, use the role service's permission check
        org_id = context.get("organization_id")
        return self.role_service.user_has_permission(user_id, permission, org_id)

    async def _get_organization_tasks_summary(
        self, org_id: OrganizationId, user_id: UserId
    ) -> Dict[str, Any]:
        """Get task summary for organization."""
        # This would integrate with task service to get task statistics
        # For now, return a placeholder structure
        return {
            "total_tasks": 0,
            "active_tasks": 0,
            "completed_tasks": 0,
            "pending_tasks": 0,
            "user_assigned_tasks": 0,
        }
