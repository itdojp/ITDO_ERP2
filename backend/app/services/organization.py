"""Organization service implementation."""

from typing import Any

from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.role import UserRole
from app.repositories.organization import OrganizationRepository
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationSummary,
    OrganizationTree,
    OrganizationUpdate,
)
from app.types import OrganizationId, UserId


class OrganizationService:
    """Service for organization business logic."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
        self.repository = OrganizationRepository(Organization, db)

    def get_organization(self, organization_id: OrganizationId) -> Organization | None:
        """Get organization by ID."""
        return self.repository.get(organization_id)

    def list_organizations(
        self, skip: int = 0, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> tuple[list[Organization], int]:
        """List organizations with pagination."""
        organizations = self.repository.get_multi(
            skip=skip, limit=limit, filters=filters
        )
        total = self.repository.get_count(filters=filters)
        return organizations, total

    def search_organizations(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[Organization], int]:
        """Search organizations by name."""
        # Get all matching organizations
        all_results = self.repository.search_by_name(query)

        # Apply additional filters if provided
        if filters:
            filtered_results = []
            for org in all_results:
                match = True
                for key, value in filters.items():
                    if hasattr(org, key) and getattr(org, key) != value:
                        match = False
                        break
                if match:
                    filtered_results.append(org)
            all_results = filtered_results

        # Apply pagination
        total = len(all_results)
        paginated_results = all_results[skip : skip + limit]

        return paginated_results, total

    def create_organization(
        self, organization_data: OrganizationCreate, created_by: UserId | None = None
    ) -> Organization:
        """Create a new organization."""
        # Add audit fields
        data = organization_data.model_dump()

        # Convert settings dict to JSON string for database storage
        if data.get("settings") and isinstance(data["settings"], dict):
            import json

            data["settings"] = json.dumps(data["settings"])

        if created_by:
            data["created_by"] = created_by
            data["updated_by"] = created_by

        # Create organization - pass dict directly to avoid schema validation issues
        db_obj = self.repository.model(**data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update_organization(
        self,
        organization_id: OrganizationId,
        organization_data: OrganizationUpdate,
        updated_by: UserId | None = None,
    ) -> Organization | None:
        """Update organization details."""
        # Check if organization exists
        organization = self.repository.get(organization_id)
        if not organization:
            return None

        # Unique code validation is handled by database constraints and API layer

        # Add audit fields
        data = organization_data.model_dump(exclude_unset=True)

        # Convert settings dict to JSON string for database storage
        if data.get("settings") and isinstance(data["settings"], dict):
            import json

            data["settings"] = json.dumps(data["settings"])

        if updated_by:
            data["updated_by"] = updated_by

        # Update organization - use the repository's update method directly
        if data:
            from sqlalchemy import update

            self.db.execute(
                update(self.repository.model)
                .where(self.repository.model.id == organization_id)
                .values(**data)
            )
            self.db.commit()

        return self.repository.get(organization_id)

    def delete_organization(
        self, organization_id: OrganizationId, deleted_by: UserId | None = None
    ) -> bool:
        """Soft delete an organization."""
        organization = self.repository.get(organization_id)
        if not organization:
            return False

        # Perform soft delete
        organization.soft_delete(deleted_by=deleted_by)
        self.db.commit()
        return True

    def activate_organization(
        self, organization_id: OrganizationId, updated_by: UserId | None = None
    ) -> Organization | None:
        """Activate an inactive organization."""
        org = self.repository.update(
            organization_id, OrganizationUpdate(is_active=True)
        )
        if org and updated_by:
            org.updated_by = updated_by
            self.db.commit()
        return org

    def deactivate_organization(
        self, organization_id: OrganizationId, updated_by: UserId | None = None
    ) -> Organization | None:
        """Deactivate an active organization."""
        org = self.repository.update(
            organization_id, OrganizationUpdate(is_active=False)
        )
        if org and updated_by:
            org.updated_by = updated_by
            self.db.commit()
        return org

    def get_direct_subsidiaries(self, parent_id: OrganizationId) -> list[Organization]:
        """Get direct subsidiaries of an organization."""
        return self.repository.get_subsidiaries(parent_id)

    def get_all_subsidiaries(self, parent_id: OrganizationId) -> list[Organization]:
        """Get all subsidiaries recursively."""
        return self.repository.get_all_subsidiaries(parent_id)

    def has_active_subsidiaries(self, organization_id: OrganizationId) -> bool:
        """Check if organization has active subsidiaries."""
        subsidiaries = self.repository.get_subsidiaries(organization_id)
        return any(sub.is_active for sub in subsidiaries)

    def get_organization_summary(
        self, organization: Organization
    ) -> OrganizationSummary:
        """Get organization summary with counts."""
        parent_name = organization.parent.name if organization.parent else None
        department_count = self.repository.get_department_count(organization.id)
        user_count = self.repository.get_user_count(organization.id)

        return OrganizationSummary(
            id=organization.id,
            code=organization.code,
            name=organization.name,
            name_en=organization.name_en,
            is_active=organization.is_active,
            parent_id=organization.parent_id,
            parent_name=parent_name,
            department_count=department_count,
            user_count=user_count,
        )

    def get_organization_response(
        self, organization: Organization
    ) -> OrganizationResponse:
        """Get full organization response."""
        import json

        # Load parent if needed
        if organization.parent_id and not organization.parent:
            org_with_parent = self.repository.get_with_parent(organization.id)
            if org_with_parent:
                organization = org_with_parent

        # Get counts
        subsidiary_count = len(self.repository.get_subsidiaries(organization.id))

        # Build response
        data = organization.to_dict()

        # Parse settings JSON string to dict
        if data.get("settings") and isinstance(data["settings"], str):
            try:
                data["settings"] = json.loads(data["settings"])
            except (json.JSONDecodeError, TypeError):
                data["settings"] = {}
        elif not data.get("settings"):
            data["settings"] = {}

        data["parent"] = organization.parent.to_dict() if organization.parent else None
        data["full_address"] = organization.full_address
        data["is_subsidiary"] = organization.is_subsidiary
        data["is_parent"] = organization.is_parent
        data["subsidiary_count"] = subsidiary_count

        # Parse settings JSON string to dictionary
        import json

        if data.get("settings"):
            try:
                data["settings"] = json.loads(data["settings"])
            except (json.JSONDecodeError, TypeError):
                data["settings"] = {}
        else:
            data["settings"] = {}

        return OrganizationResponse.model_validate(data)

    def get_organization_tree(self) -> list[OrganizationTree]:
        """Get organization hierarchy tree."""
        # Get root organizations
        roots = self.repository.get_root_organizations()

        def build_tree(org: Organization, level: int = 0) -> OrganizationTree:
            """Build tree recursively."""
            children = []
            for sub in self.repository.get_subsidiaries(org.id):
                children.append(build_tree(sub, level + 1))

            return OrganizationTree(
                id=org.id,
                code=org.code,
                name=org.name,
                is_active=org.is_active,
                level=level,
                parent_id=org.parent_id,
                children=children,
            )

        return [build_tree(root) for root in roots]

    def user_has_permission(
        self,
        user_id: UserId,
        permission: str,
        organization_id: OrganizationId | None = None,
    ) -> bool:
        """Check if user has permission for organizations."""
        # Get user roles
        user_roles = self.db.query(UserRole).filter(
            UserRole.user_id == user_id, UserRole.is_active
        )

        if organization_id:
            user_roles = user_roles.filter(UserRole.organization_id == organization_id)

        # Check permissions
        for user_role in user_roles.all():
            if user_role.is_valid and user_role.role.has_permission(permission):
                return True

        return False

    def update_settings(
        self,
        organization_id: OrganizationId,
        settings: dict[str, Any],
        updated_by: UserId | None = None,
    ) -> Organization | None:
        """Update organization settings."""
        org = self.repository.update_settings(organization_id, settings)
        if org and updated_by:
            org.updated_by = updated_by
            self.db.commit()
        return org
