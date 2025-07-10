"""Integration API endpoints for Organization-Role-Department management."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.organization import OrganizationCreate
from app.schemas.role import RoleResponse
from app.schemas.task import TaskCreate, TaskResponse
from app.services.integration_service import (
    CompleteOrganizationSetup,
    ERPIntegrationService,
)
from app.services.organization_role_integration import (
    OrganizationRoleIntegrationService,
)
from app.types import UserId

router = APIRouter(prefix="/integration", tags=["integration"])


class CompleteOrganizationCreate:
    """Schema for complete organization creation."""

    def __init__(
        self,
        organization: OrganizationCreate,
        initial_departments: Optional[List[Dict[str, Any]]] = None,
        custom_roles: Optional[List[Dict[str, Any]]] = None,
    ):
        self.organization = organization
        self.initial_departments = initial_departments or []
        self.custom_roles = custom_roles or []


class CompleteOrganizationResponse:
    """Response schema for complete organization creation."""

    def __init__(
        self,
        organization: Any,
        departments: List[Any],
        roles: List[RoleResponse],
    ):
        self.organization = organization
        self.departments = departments
        self.roles = roles


class UserDepartmentAssignment:
    """Schema for user department assignment with role."""

    def __init__(self, user_id: UserId, role: str, department_id: Optional[int] = None):
        self.user_id = user_id
        self.role = role
        self.department_id = department_id


class OrganizationStructure:
    """Schema for complete organization structure."""

    def __init__(
        self,
        organization: Any,
        departments: List[Any],
        roles: List[RoleResponse],
        members: List[Any],
        access_matrix: Dict[str, Any],
    ):
        self.organization = organization
        self.departments = departments
        self.roles = roles
        self.members = members
        self.access_matrix = access_matrix


@router.post("/organizations/complete")
async def create_complete_organization(
    org_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Create organization with departments and roles."""
    try:
        service = OrganizationRoleIntegrationService(db)

        # Extract organization data
        org_create = OrganizationCreate(**org_data["organization"])

        # Create organization with default roles
        organization = await service.create_organization_with_default_roles(
            org_create, current_user.id
        )

        # TODO: Add department creation logic here
        departments = []  # Placeholder for department creation

        # Get created roles
        roles = service.role_service.get_organization_roles(organization.id)

        return {
            "organization": {
                "id": organization.id,
                "code": organization.code,
                "name": organization.name,
                "is_active": organization.is_active,
            },
            "departments": departments,
            "roles": [
                {
                    "id": role.id,
                    "code": role.code,
                    "name": role.name,
                    "permissions": role.permissions,
                }
                for role in roles
            ],
            "status": "created",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create complete organization: {str(e)}",
        )


@router.get("/organizations/{org_id}/structure")
async def get_organization_complete_structure(
    org_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get complete organization structure with departments, roles, and members."""
    try:
        service = OrganizationRoleIntegrationService(db)

        # Get organization with roles
        org_with_roles = await service.get_organization_with_roles(
            org_id, current_user.id
        )

        # Get access matrix
        access_matrix = service.get_organization_access_matrix(org_id)

        # TODO: Add department loading logic here
        departments = []  # Placeholder

        return {
            "organization": {
                "id": org_with_roles.organization.id,
                "code": org_with_roles.organization.code,
                "name": org_with_roles.organization.name,
                "is_active": org_with_roles.organization.is_active,
            },
            "departments": departments,
            "roles": [
                {
                    "id": role.id,
                    "code": role.code,
                    "name": role.name,
                    "permissions": role.permissions,
                }
                for role in org_with_roles.available_roles
            ],
            "user_roles": [
                {
                    "id": ur.id,
                    "user_id": ur.user_id,
                    "role_id": ur.role_id,
                    "is_active": ur.is_active,
                }
                for ur in org_with_roles.user_roles
            ],
            "access_matrix": access_matrix,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization structure not found: {str(e)}",
        )


@router.post("/departments/{dept_id}/assign-user")
async def assign_user_to_department_with_role(
    dept_id: int,
    assignment: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Assign user to department with specific role."""
    try:
        service = OrganizationRoleIntegrationService(db)

        user_id = assignment["user_id"]
        role_code = assignment["role"]

        # TODO: Get department and organization info
        # For now, assume organization_id is provided or derived from dept_id
        organization_id = assignment.get("organization_id", 1)  # Placeholder

        # Get role by code
        role = service.role_service.get_role_by_code(role_code)
        if not role:
            raise ValueError(f"Role {role_code} not found")

        # Assign user role
        user_role = service.role_service.assign_user_role(
            user_id=user_id,
            role_id=role.id,
            organization_id=organization_id,
            department_id=dept_id,
            assigned_by=current_user.id,
        )

        return {
            "user_id": user_id,
            "department_id": dept_id,
            "role_code": role_code,
            "assignment_id": user_role.id,
            "status": "assigned",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to assign user: {str(e)}",
        )


@router.get("/organizations/hierarchy")
async def get_organization_hierarchy_with_roles(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Get organization hierarchy with role information."""
    try:
        service = OrganizationRoleIntegrationService(db)
        return service.get_organization_hierarchy_with_roles()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get hierarchy: {str(e)}",
        )


@router.post("/organizations/{org_id}/bulk-assign-roles")
async def bulk_assign_roles(
    org_id: int,
    assignments: List[Dict[str, Any]],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Perform bulk role assignments for organization."""
    try:
        service = OrganizationRoleIntegrationService(db)

        result = service.bulk_role_assignment(
            organization_id=org_id,
            role_assignments=assignments,
            assigned_by=current_user.id,
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bulk assignment failed: {str(e)}",
        )


@router.post("/organizations/{org_id}/clone")
async def clone_organization_structure(
    org_id: int,
    target_org_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Clone organization structure to new organization."""
    try:
        service = OrganizationRoleIntegrationService(db)

        target_create = OrganizationCreate(**target_org_data)
        new_org = service.clone_organization_structure(
            source_org_id=org_id,
            target_org_data=target_create,
            user_id=current_user.id,
        )

        return {
            "source_organization_id": org_id,
            "new_organization": {
                "id": new_org.id,
                "code": new_org.code,
                "name": new_org.name,
            },
            "status": "cloned",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Organization cloning failed: {str(e)}",
        )


@router.post("/users/{user_id}/transfer-organization")
async def transfer_user_organization(
    user_id: int,
    transfer_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Transfer user from one organization to another."""
    try:
        service = OrganizationRoleIntegrationService(db)

        result = service.transfer_user_organization(
            user_id=user_id,
            from_org_id=transfer_data["from_organization_id"],
            to_org_id=transfer_data["to_organization_id"],
            new_role_code=transfer_data["new_role_code"],
            transferred_by=current_user.id,
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User transfer failed: {str(e)}",
        )


@router.get("/organizations/{org_id}/access-matrix")
async def get_organization_access_matrix(
    org_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get comprehensive access matrix for organization."""
    try:
        service = OrganizationRoleIntegrationService(db)
        return service.get_organization_access_matrix(org_id)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get access matrix: {str(e)}",
        )


# New ERP Integration Endpoints


def get_integration_service(db: Session = Depends(get_db)) -> ERPIntegrationService:
    """Get ERP integration service."""
    return ERPIntegrationService(db)


@router.post("/setup-organization")
async def setup_complete_organization(
    setup_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    integration_service: ERPIntegrationService = Depends(get_integration_service),
) -> Dict[str, Any]:
    """Complete organization setup (Organization + Roles + Departments)."""
    try:
        # Convert to setup object
        org_create = OrganizationCreate(**setup_data["organization"])
        complete_setup = CompleteOrganizationSetup(
            organization=org_create,
            departments=setup_data.get("departments", []),
            custom_roles=setup_data.get("custom_roles", []),
        )

        # Setup organization
        result = await integration_service.setup_complete_organization(
            complete_setup, current_user.id
        )

        return {
            "organization": {
                "id": result.organization.id,
                "code": result.organization.code,
                "name": result.organization.name,
                "is_active": result.organization.is_active,
            },
            "roles": [
                {
                    "id": role.id,
                    "code": role.code,
                    "name": role.name,
                    "role_type": role.role_type,
                }
                for role in result.roles
            ],
            "departments": [
                {
                    "id": dept.id if hasattr(dept, "id") else None,
                    "name": dept.name if hasattr(dept, "name") else str(dept),
                }
                for dept in result.departments
            ],
            "admin_assignments": [
                {
                    "role_id": role.id,
                    "role_name": role.name,
                }
                for role in result.admin_assignments
            ],
            "status": "completed",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to setup organization: {str(e)}",
        )


@router.post("/departments/{department_id}/tasks")
async def create_department_task_with_permissions(
    department_id: int,
    task_data: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    integration_service: ERPIntegrationService = Depends(get_integration_service),
) -> TaskResponse:
    """Create task in department with permission checks."""
    try:
        task = await integration_service.create_department_task_with_permissions(
            task_data, department_id, current_user.id
        )

        return TaskResponse.model_validate(task, from_attributes=True)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create task: {str(e)}",
        )


@router.get("/organizations/{org_id}/structure")
async def get_complete_organization_structure(
    org_id: int,
    current_user: User = Depends(get_current_active_user),
    integration_service: ERPIntegrationService = Depends(get_integration_service),
) -> Dict[str, Any]:
    """Get complete organization structure (Departments + Roles + Tasks)."""
    try:
        return await integration_service.get_complete_structure(org_id, current_user.id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get organization structure: {str(e)}",
        )


@router.get("/organizations/{org_id}/permissions-matrix")
async def get_organization_permissions_matrix(
    org_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get comprehensive permissions matrix for organization."""
    try:
        # Use existing organization-role integration service for permission matrix
        service = OrganizationRoleIntegrationService(db)
        return service.get_organization_access_matrix(org_id)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get permissions matrix: {str(e)}",
        )

