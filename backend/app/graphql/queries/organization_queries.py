"""Organization GraphQL query resolvers."""

from typing import List, Optional

import strawberry
from strawberry import Info
from sqlalchemy import select

from app.graphql.context import GraphQLContext
from app.graphql.types.organization import Organization, OrganizationFilters
from app.models.organization import Organization as OrganizationModel
from app.core.monitoring import monitor_performance


@strawberry.type
class OrganizationQueries:
    """Organization-related GraphQL queries."""

    @strawberry.field
    @monitor_performance("graphql.organization.get_organization")
    async def organization(
        self, 
        info: Info[GraphQLContext, None], 
        id: strawberry.ID
    ) -> Optional[Organization]:
        """Get a single organization by ID."""
        context = info.context
        context.require_authentication()
        
        org_id = int(id)
        
        # Non-superusers can only view their own organization
        if (not context.current_user.is_superuser and 
            context.organization_id != org_id):
            raise PermissionError("Insufficient permissions to view organization")
        
        # Use DataLoader for efficient loading
        org_model = await context.organization_loader.load(org_id)
        
        if not org_model:
            return None
        
        return Organization.from_model(org_model)

    @strawberry.field
    @monitor_performance("graphql.organization.get_organizations")
    async def organizations(
        self,
        info: Info[GraphQLContext, None],
        filters: Optional[OrganizationFilters] = None
    ) -> List[Organization]:
        """Get multiple organizations with filtering."""
        context = info.context
        
        # Only superusers can list all organizations
        if not context.current_user.is_superuser:
            context.require_permission("organization.list")
        
        # Build query
        query = select(OrganizationModel)
        
        # Non-superusers can only see their own organization
        if not context.current_user.is_superuser and context.organization_id:
            query = query.where(OrganizationModel.id == context.organization_id)
        
        # Apply filters
        if filters:
            if filters.name:
                query = query.where(OrganizationModel.name.ilike(f"%{filters.name}%"))
            if filters.code:
                query = query.where(OrganizationModel.code.ilike(f"%{filters.code}%"))
            if filters.is_active is not None:
                query = query.where(OrganizationModel.is_active == filters.is_active)
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.where(
                    OrganizationModel.name.ilike(search_term) |
                    OrganizationModel.code.ilike(search_term) |
                    OrganizationModel.description.ilike(search_term)
                )
        
        # Execute query
        if hasattr(context.db, 'execute'):  # AsyncSession
            result = await context.db.execute(query)
            org_models = result.scalars().all()
        else:  # Session
            result = context.db.execute(query)
            org_models = result.scalars().all()
        
        return [Organization.from_model(org_model) for org_model in org_models]

    @strawberry.field
    @monitor_performance("graphql.organization.get_my_organization")
    async def my_organization(self, info: Info[GraphQLContext, None]) -> Optional[Organization]:
        """Get current user's organization."""
        context = info.context
        user = context.require_authentication()
        
        if not user.organization_id:
            return None
        
        org_model = await context.organization_loader.load(user.organization_id)
        
        if not org_model:
            return None
        
        return Organization.from_model(org_model)