"""User GraphQL type definition."""

from typing import List, Optional

import strawberry
from strawberry import Info

from app.models.user import User as UserModel
from app.graphql.context import GraphQLContext


@strawberry.type
class User:
    """User GraphQL type."""

    id: strawberry.ID
    email: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    organization_id: Optional[int]
    created_at: str
    updated_at: Optional[str]

    @classmethod
    def from_model(cls, user_model: UserModel) -> "User":
        """Create GraphQL User from SQLAlchemy User model."""
        return cls(
            id=strawberry.ID(str(user_model.id)),
            email=user_model.email,
            full_name=user_model.full_name,
            is_active=user_model.is_active,
            is_superuser=user_model.is_superuser,
            organization_id=user_model.organization_id,
            created_at=user_model.created_at.isoformat() if user_model.created_at else "",
            updated_at=user_model.updated_at.isoformat() if user_model.updated_at else None,
        )

    @strawberry.field
    async def organization(self, info: Info[GraphQLContext, None]) -> Optional["Organization"]:
        """Get user's organization using DataLoader."""
        if not self.organization_id:
            return None
        
        org_model = await info.context.organization_loader.load(self.organization_id)
        if not org_model:
            return None
            
        from app.graphql.types.organization import Organization
        return Organization.from_model(org_model)

    @strawberry.field
    async def tasks(self, info: Info[GraphQLContext, None]) -> List["Task"]:
        """Get user's tasks using efficient querying."""
        # This would be implemented with proper filtering
        # For now, returning empty list
        return []


@strawberry.input
class UserCreateInput:
    """Input type for creating a user."""
    
    email: str
    full_name: Optional[str] = None
    password: str
    organization_id: Optional[int] = None


@strawberry.input
class UserUpdateInput:
    """Input type for updating a user."""
    
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    organization_id: Optional[int] = None


@strawberry.input
class UserFilters:
    """Input type for filtering users."""
    
    email: Optional[str] = None
    is_active: Optional[bool] = None
    organization_id: Optional[int] = None
    search: Optional[str] = None


@strawberry.type
class UserPayload:
    """Payload type for user mutations."""
    
    user: Optional[User]
    success: bool
    message: str