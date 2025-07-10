"""Organization-Role integration service for complete management."""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.role import Role, UserRole
from app.schemas.organization import OrganizationCreate
from app.schemas.role import RoleCreate
from app.services.organization import OrganizationService
from app.services.role import RoleService
from app.types import OrganizationId, UserId


class OrganizationWithRoles:
    """Response model for organization with role information."""

    def __init__(
        self,
        organization: Organization,
        available_roles: List[Role],
        user_roles: List[UserRole],
    ):
        self.organization = organization
        self.available_roles = available_roles
        self.user_roles = user_roles


class OrganizationRoleIntegrationService:
    """Service for integrated organization and role management."""

    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
        self.org_service = OrganizationService(db)
        self.role_service = RoleService(db)

    async def create_organization_with_default_roles(
        self,
        org_data: OrganizationCreate,
        user_id: UserId,
    ) -> Organization:
        """Create organization with default role structure."""
        # Create the organization
        organization = self.org_service.create_organization(
            org_data, created_by=user_id
        )

        # Default roles for new organization
        default_roles = [
            {
                "code": f"org_admin_{organization.id}",
                "name": "Organization Administrator",
                "description": "Full administrative access to organization",
                "permissions": {
                    "organization": {"*": True},
                    "departments": {"*": True},
                    "users": {"*": True},
                    "roles": {"*": True},
                },
                "role_type": "organization",
                "organization_id": organization.id,
            },
            {
                "code": f"org_manager_{organization.id}",
                "name": "Organization Manager",
                "description": "Management access to organization operations",
                "permissions": {
                    "organization": {"read": True, "update": True},
                    "departments": {"*": True},
                    "users": {"read": True, "update": True},
                    "projects": {"*": True},
                },
                "role_type": "organization",
                "organization_id": organization.id,
            },
            {
                "code": f"org_member_{organization.id}",
                "name": "Organization Member",
                "description": "Standard member access",
                "permissions": {
                    "organization": {"read": True},
                    "departments": {"read": True},
                    "users": {"read": True},
                    "projects": {"read": True, "create": True},
                },
                "role_type": "organization",
                "organization_id": organization.id,
            },
            {
                "code": f"org_viewer_{organization.id}",
                "name": "Organization Viewer",
                "description": "Read-only access to organization",
                "permissions": {
                    "organization": {"read": True},
                    "departments": {"read": True},
                    "users": {"read": True},
                },
                "role_type": "organization",
                "organization_id": organization.id,
            },
        ]

        # Create default roles
        created_roles = []
        for role_data in default_roles:
            role_create = RoleCreate(**role_data)
            role = self.role_service.create_role(role_create, created_by=user_id)
            created_roles.append(role)

        # Assign creator as organization admin
        admin_role = created_roles[0]  # First role is admin
        self.role_service.assign_user_role(
            user_id=user_id,
            role_id=admin_role.id,
            organization_id=organization.id,
            assigned_by=user_id,
        )

        return organization

    async def get_organization_with_roles(
        self,
        org_id: OrganizationId,
        user_id: UserId,
    ) -> OrganizationWithRoles:
        """Get organization with comprehensive role information."""
        # Get organization
        organization = self.org_service.get_organization(org_id)
        if not organization:
            raise ValueError(f"Organization {org_id} not found")

        # Get all roles for this organization
        available_roles = self.role_service.get_organization_roles(org_id)

        # Get user's roles in this organization
        user_roles = self.role_service.get_user_roles(
            user_id=user_id, organization_id=org_id
        )

        return OrganizationWithRoles(
            organization=organization,
            available_roles=available_roles,
            user_roles=user_roles,
        )

    def clone_organization_structure(
        self,
        source_org_id: OrganizationId,
        target_org_data: OrganizationCreate,
        user_id: UserId,
    ) -> Organization:
        """Clone organization structure including roles."""
        # Get source organization roles
        source_roles = self.role_service.get_organization_roles(source_org_id)

        # Create target organization
        target_org = self.org_service.create_organization(
            target_org_data, created_by=user_id
        )

        # Clone roles to target organization
        for source_role in source_roles:
            if not source_role.is_system:  # Don't clone system roles
                role_data = RoleCreate(
                    code=f"{source_role.code}_{target_org.id}",
                    name=source_role.name,
                    description=source_role.description,
                    permissions=source_role.permissions,
                    role_type=source_role.role_type,
                    organization_id=target_org.id,
                    display_order=source_role.display_order,
                    icon=source_role.icon,
                    color=source_role.color,
                )
                self.role_service.create_role(role_data, created_by=user_id)

        return target_org

    def transfer_user_organization(
        self,
        user_id: UserId,
        from_org_id: OrganizationId,
        to_org_id: OrganizationId,
        new_role_code: str,
        transferred_by: UserId,
    ) -> Dict[str, Any]:
        """Transfer user from one organization to another."""
        # Deactivate roles in source organization
        old_roles = self.role_service.get_user_roles(
            user_id=user_id, organization_id=from_org_id
        )

        deactivated_count = 0
        for user_role in old_roles:
            if user_role.is_active:
                self.role_service.deactivate_user_role(
                    user_role.id, deactivated_by=transferred_by
                )
                deactivated_count += 1

        # Find new role in target organization
        target_role = self.role_service.get_role_by_code(new_role_code)
        if not target_role or target_role.organization_id != to_org_id:
            raise ValueError(f"Role {new_role_code} not found in target organization")

        # Assign new role in target organization
        new_user_role = self.role_service.assign_user_role(
            user_id=user_id,
            role_id=target_role.id,
            organization_id=to_org_id,
            assigned_by=transferred_by,
        )

        return {
            "user_id": user_id,
            "from_organization_id": from_org_id,
            "to_organization_id": to_org_id,
            "old_roles_deactivated": deactivated_count,
            "new_role_assigned": new_user_role.id,
            "status": "completed",
        }

    def get_organization_hierarchy_with_roles(
        self, root_org_id: Optional[OrganizationId] = None
    ) -> List[Dict[str, Any]]:
        """Get organization hierarchy with role counts."""
        # Get organization tree
        org_tree = self.org_service.get_organization_tree()

        def enrich_with_roles(org_node):
            """Add role information to organization node."""
            org_roles = self.role_service.get_organization_roles(org_node["id"])
            active_roles = [r for r in org_roles if r.is_active]

            # Count users by role
            role_user_counts = {}
            for role in active_roles:
                user_count = len(
                    self.role_service.get_users_with_role(
                        role.id, organization_id=org_node["id"]
                    )
                )
                role_user_counts[role.code] = user_count

            org_node["role_summary"] = {
                "total_roles": len(active_roles),
                "role_counts": role_user_counts,
                "admin_count": role_user_counts.get(
                    f"org_admin_{org_node['id']}", 0
                ),
                "member_count": sum(role_user_counts.values()),
            }

            # Process children recursively
            if "children" in org_node:
                for child in org_node["children"]:
                    enrich_with_roles(child)

            return org_node

        # Enrich tree with role information
        enriched_tree = []
        for root in org_tree:
            enriched_tree.append(enrich_with_roles(root.model_dump()))

        return enriched_tree

    def bulk_role_assignment(
        self,
        organization_id: OrganizationId,
        role_assignments: List[Dict[str, Any]],
        assigned_by: UserId,
    ) -> Dict[str, Any]:
        """Perform bulk role assignments for an organization."""
        results = {
            "total_assignments": len(role_assignments),
            "successful": 0,
            "failed": 0,
            "errors": [],
        }

        for assignment in role_assignments:
            try:
                user_id = assignment["user_id"]
                role_code = assignment["role_code"]
                department_id = assignment.get("department_id")

                # Get role by code
                role = self.role_service.get_role_by_code(role_code)
                if not role or role.organization_id != organization_id:
                    raise ValueError(f"Role {role_code} not found in organization")

                # Assign role
                self.role_service.assign_user_role(
                    user_id=user_id,
                    role_id=role.id,
                    organization_id=organization_id,
                    department_id=department_id,
                    assigned_by=assigned_by,
                    expires_at=assignment.get("expires_at"),
                )

                results["successful"] += 1

            except Exception as e:
                results["failed"] += 1
                results["errors"].append(
                    {
                        "assignment": assignment,
                        "error": str(e),
                    }
                )

        return results

    def get_organization_access_matrix(
        self, organization_id: OrganizationId
    ) -> Dict[str, Any]:
        """Get comprehensive access matrix for organization."""
        # Get organization roles
        roles = self.role_service.get_organization_roles(organization_id)

        # Build permission matrix
        permission_matrix = {}
        user_role_map = {}

        for role in roles:
            if role.is_active:
                # Get users with this role
                users = self.role_service.get_users_with_role(
                    role.id, organization_id=organization_id
                )

                permission_matrix[role.code] = {
                    "role_name": role.name,
                    "permissions": role.get_all_permissions(),
                    "user_count": len(users),
                    "users": [
                        {"id": u.id, "name": u.full_name, "email": u.email}
                        for u in users
                    ],
                }

                # Map users to roles
                for user in users:
                    if user.id not in user_role_map:
                        user_role_map[user.id] = []
                    user_role_map[user.id].append(role.code)

        return {
            "organization_id": organization_id,
            "permission_matrix": permission_matrix,
            "user_role_mapping": user_role_map,
            "summary": {
                "total_roles": len(permission_matrix),
                "total_users": len(user_role_map),
                "average_roles_per_user": (
                    sum(len(roles) for roles in user_role_map.values())
                    / len(user_role_map)
                    if user_role_map
                    else 0
                ),
            },
        }

