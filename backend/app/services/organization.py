"""Organization service implementation."""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.organization import Organization
from app.models.role import UserRole
from app.repositories.organization import OrganizationRepository
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationSummary,
    OrganizationTree
)
from app.types import OrganizationId, UserId


class OrganizationService:
    """Service for organization business logic."""
    
    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
        self.repository = OrganizationRepository(Organization, db)
    
    def get_organization(self, organization_id: OrganizationId) -> Optional[Organization]:
        """Get organization by ID."""
        return self.repository.get(organization_id)
    
    def list_organizations(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Organization], int]:
        """List organizations with pagination."""
        organizations = self.repository.get_multi(skip=skip, limit=limit, filters=filters)
        total = self.repository.get_count(filters=filters)
        return organizations, total
    
    def search_organizations(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Organization], int]:
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
        paginated_results = all_results[skip:skip + limit]
        
        return paginated_results, total
    
    def create_organization(
        self,
        organization_data: OrganizationCreate,
        created_by: Optional[UserId] = None
    ) -> Organization:
        """Create a new organization."""
        # Validate unique code
        if not self.repository.validate_unique_code(organization_data.code):
            raise ValueError(f"Organization code '{organization_data.code}' already exists")
        
        # Add audit fields
        data = organization_data.model_dump()
        if created_by:
            data["created_by"] = created_by
            data["updated_by"] = created_by
        
        # Create organization
        return self.repository.create(OrganizationCreate(**data))
    
    def update_organization(
        self,
        organization_id: OrganizationId,
        organization_data: OrganizationUpdate,
        updated_by: Optional[UserId] = None
    ) -> Optional[Organization]:
        """Update organization details."""
        # Check if organization exists
        organization = self.repository.get(organization_id)
        if not organization:
            return None
        
        # Validate unique code if being changed
        if organization_data.code and organization_data.code != organization.code:
            if not self.repository.validate_unique_code(organization_data.code, exclude_id=organization_id):
                raise ValueError(f"Organization code '{organization_data.code}' already exists")
        
        # Add audit fields
        data = organization_data.model_dump(exclude_unset=True)
        if updated_by:
            data["updated_by"] = updated_by
        
        # Update organization
        return self.repository.update(organization_id, OrganizationUpdate(**data))
    
    def delete_organization(
        self,
        organization_id: OrganizationId,
        deleted_by: Optional[UserId] = None
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
        self,
        organization_id: OrganizationId,
        updated_by: Optional[UserId] = None
    ) -> Optional[Organization]:
        """Activate an inactive organization."""
        data: Dict[str, Any] = {"is_active": True}
        if updated_by:
            data["updated_by"] = updated_by
        
        return self.repository.update(organization_id, OrganizationUpdate(**data))
    
    def deactivate_organization(
        self,
        organization_id: OrganizationId,
        updated_by: Optional[UserId] = None
    ) -> Optional[Organization]:
        """Deactivate an active organization."""
        data: Dict[str, Any] = {"is_active": False}
        if updated_by:
            data["updated_by"] = updated_by
        
        return self.repository.update(organization_id, OrganizationUpdate(**data))
    
    def get_direct_subsidiaries(self, parent_id: OrganizationId) -> List[Organization]:
        """Get direct subsidiaries of an organization."""
        return self.repository.get_subsidiaries(parent_id)
    
    def get_all_subsidiaries(self, parent_id: OrganizationId) -> List[Organization]:
        """Get all subsidiaries recursively."""
        return self.repository.get_all_subsidiaries(parent_id)
    
    def has_active_subsidiaries(self, organization_id: OrganizationId) -> bool:
        """Check if organization has active subsidiaries."""
        subsidiaries = self.repository.get_subsidiaries(organization_id)
        return any(sub.is_active for sub in subsidiaries)
    
    def get_organization_summary(self, organization: Organization) -> OrganizationSummary:
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
            user_count=user_count
        )
    
    def get_organization_response(self, organization: Organization) -> OrganizationResponse:
        """Get full organization response."""
        # Load parent if needed
        if organization.parent_id and not organization.parent:
            loaded_org = self.repository.get_with_parent(organization.id)
            if loaded_org:
                organization = loaded_org
        
        # Get counts
        subsidiary_count = len(self.repository.get_subsidiaries(organization.id))
        
        # Build response
        data = organization.to_dict()
        data["parent"] = organization.parent.to_dict() if organization.parent else None
        data["full_address"] = organization.full_address
        data["is_subsidiary"] = organization.is_subsidiary
        data["is_parent"] = organization.is_parent
        data["subsidiary_count"] = subsidiary_count
        
        return OrganizationResponse.model_validate(data)
    
    def get_organization_tree(self) -> List[OrganizationTree]:
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
                children=children
            )
        
        return [build_tree(root) for root in roots]
    
    def user_has_permission(
        self,
        user_id: UserId,
        permission: str,
        organization_id: Optional[OrganizationId] = None
    ) -> bool:
        """Check if user has permission for organizations."""
        # Get user roles
        user_roles = self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.is_active == True
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
        settings: Dict[str, Any],
        updated_by: Optional[UserId] = None
    ) -> Optional[Organization]:
        """Update organization settings."""
        org = self.repository.update_settings(organization_id, settings)
        if org and updated_by:
            org.updated_by = updated_by
            self.db.commit()
        return org