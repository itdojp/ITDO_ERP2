"""Organization GraphQL type definition."""

from typing import List, Optional

import strawberry
from strawberry import Info

from app.models.organization import Organization as OrganizationModel
from app.graphql.context import GraphQLContext


@strawberry.type
class Organization:
    """Organization GraphQL type."""

    id: strawberry.ID
    name: str
    code: Optional[str]
    description: Optional[str]
    is_active: bool
    created_at: str
    updated_at: Optional[str]

    @classmethod
    def from_model(cls, org_model: OrganizationModel) -> "Organization":
        """Create GraphQL Organization from SQLAlchemy Organization model."""
        return cls(
            id=strawberry.ID(str(org_model.id)),
            name=org_model.name,
            code=org_model.code,
            description=org_model.description,
            is_active=org_model.is_active,
            created_at=org_model.created_at.isoformat() if org_model.created_at else "",
            updated_at=org_model.updated_at.isoformat() if org_model.updated_at else None,
        )

    @strawberry.field
    async def users(self, info: Info[GraphQLContext, None]) -> List["User"]:
        """Get organization's users."""
        # This would be implemented with proper querying
        return []

    @strawberry.field
    async def departments(self, info: Info[GraphQLContext, None]) -> List["Department"]:
        """Get organization's departments."""
        # This would be implemented with proper querying
        return []


@strawberry.input
class OrganizationCreateInput:
    """Input type for creating an organization."""
    
    name: str
    code: Optional[str] = None
    description: Optional[str] = None


@strawberry.input
class OrganizationUpdateInput:
    """Input type for updating an organization."""
    
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


@strawberry.input
class OrganizationFilters:
    """Input type for filtering organizations."""
    
    name: Optional[str] = None
    code: Optional[str] = None
    is_active: Optional[bool] = None
    search: Optional[str] = None


@strawberry.type
class OrganizationPayload:
    """Payload type for organization mutations."""
    
    organization: Optional[Organization]
    success: bool
    message: str