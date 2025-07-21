"""User GraphQL query resolvers."""

from typing import List, Optional

import strawberry
from strawberry import Info
from sqlalchemy import select

from app.graphql.context import GraphQLContext
from app.graphql.types.user import User, UserFilters
from app.graphql.types.common import PaginationInput
from app.models.user import User as UserModel
from app.core.monitoring import monitor_performance


@strawberry.type
class UserQueries:
    """User-related GraphQL queries."""

    @strawberry.field
    @monitor_performance("graphql.user.get_user")
    async def user(
        self, 
        info: Info[GraphQLContext, None], 
        id: strawberry.ID
    ) -> Optional[User]:
        """Get a single user by ID."""
        context = info.context
        context.require_authentication()
        
        user_id = int(id)
        
        # Use DataLoader for efficient loading
        user_model = await context.user_loader.load(user_id)
        
        if not user_model:
            return None
        
        # Check permissions - users can view their own profile
        if (user_id != context.user_id and 
            not context.current_user.is_superuser and
            not context.current_user.has_permission("user.view")):
            raise PermissionError("Insufficient permissions to view user")
        
        return User.from_model(user_model)

    @strawberry.field
    @monitor_performance("graphql.user.get_users")
    async def users(
        self,
        info: Info[GraphQLContext, None],
        filters: Optional[UserFilters] = None,
        pagination: Optional[PaginationInput] = None
    ) -> List[User]:
        """Get multiple users with filtering and pagination."""
        context = info.context
        context.require_permission("user.list")
        
        # Build query
        query = select(UserModel)
        
        # Apply organization filter for non-superusers
        if not context.current_user.is_superuser and context.organization_id:
            query = query.where(UserModel.organization_id == context.organization_id)
        
        # Apply filters
        if filters:
            if filters.email:
                query = query.where(UserModel.email.ilike(f"%{filters.email}%"))
            if filters.is_active is not None:
                query = query.where(UserModel.is_active == filters.is_active)
            if filters.organization_id:
                query = query.where(UserModel.organization_id == filters.organization_id)
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.where(
                    UserModel.email.ilike(search_term) |
                    UserModel.full_name.ilike(search_term)
                )
        
        # Apply pagination
        if pagination:
            if pagination.first:
                query = query.limit(pagination.first)
            # Note: Full Relay pagination would require cursor implementation
        
        # Execute query
        if hasattr(context.db, 'execute'):  # AsyncSession
            result = await context.db.execute(query)
            user_models = result.scalars().all()
        else:  # Session
            result = context.db.execute(query)
            user_models = result.scalars().all()
        
        # Convert to GraphQL types
        return [User.from_model(user_model) for user_model in user_models]

    @strawberry.field
    @monitor_performance("graphql.user.get_me")
    async def me(self, info: Info[GraphQLContext, None]) -> Optional[User]:
        """Get current authenticated user."""
        context = info.context
        user = context.require_authentication()
        
        return User.from_model(user)

    @strawberry.field
    @monitor_performance("graphql.user.search_users")
    async def search_users(
        self,
        info: Info[GraphQLContext, None],
        query: str,
        limit: int = 10
    ) -> List[User]:
        """Search users by email or name."""
        context = info.context
        context.require_permission("user.search")
        
        search_term = f"%{query}%"
        db_query = select(UserModel).where(
            UserModel.email.ilike(search_term) |
            UserModel.full_name.ilike(search_term)
        ).limit(limit)
        
        # Apply organization filter for non-superusers
        if not context.current_user.is_superuser and context.organization_id:
            db_query = db_query.where(UserModel.organization_id == context.organization_id)
        
        # Execute query
        if hasattr(context.db, 'execute'):  # AsyncSession
            result = await context.db.execute(db_query)
            user_models = result.scalars().all()
        else:  # Session
            result = context.db.execute(db_query)
            user_models = result.scalars().all()
        
        return [User.from_model(user_model) for user_model in user_models]