"""GraphQL schema definition."""

import strawberry
from typing import List, Optional

from app.graphql.queries.user_queries import UserQueries
from app.graphql.queries.organization_queries import OrganizationQueries
from app.graphql.queries.task_queries import TaskQueries
from app.graphql.types.user import User, UserFilters
from app.graphql.types.organization import Organization, OrganizationFilters
from app.graphql.types.task import Task, TaskFilters
from app.graphql.types.common import PaginationInput


@strawberry.type
class Query(UserQueries, OrganizationQueries, TaskQueries):
    """Root query type combining all query resolvers."""
    
    @strawberry.field
    async def health(self) -> str:
        """Health check endpoint for GraphQL."""
        return "GraphQL API is healthy"


@strawberry.type  
class Mutation:
    """Root mutation type for GraphQL."""
    
    @strawberry.field
    async def ping(self) -> str:
        """Ping mutation for testing."""
        return "pong"


@strawberry.type
class Subscription:
    """Root subscription type for real-time updates."""
    
    @strawberry.subscription
    async def count(self, target: int = 100) -> int:
        """Example subscription for counting."""
        for i in range(target):
            yield i


# Create GraphQL schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription
)