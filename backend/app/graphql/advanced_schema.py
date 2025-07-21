"""Enhanced GraphQL schema with advanced features."""

import strawberry
from typing import List, Optional

from app.graphql.queries.user_queries import UserQueries
from app.graphql.queries.organization_queries import OrganizationQueries
from app.graphql.queries.task_queries import TaskQueries
from app.graphql.types.user import User, UserFilters
from app.graphql.types.organization import Organization, OrganizationFilters
from app.graphql.types.task import Task, TaskFilters
from app.graphql.types.common import PaginationInput
from app.graphql.advanced.subscriptions import AdvancedSubscriptions


@strawberry.type
class AdvancedQuery(UserQueries, OrganizationQueries, TaskQueries):
    """Enhanced query type with advanced GraphQL capabilities."""
    
    @strawberry.field
    async def health(self) -> str:
        """Health check endpoint for GraphQL."""
        return "Advanced GraphQL API is healthy"
    
    @strawberry.field
    async def federation_status(self) -> str:
        """Federation status endpoint."""
        from app.graphql.advanced.federation import federation_registry
        status = federation_registry.get_federation_status()
        return f"Federation status: {status['overall_status']}"
    
    @strawberry.field
    async def cache_stats(self) -> str:
        """Cache statistics endpoint."""
        from app.graphql.advanced.caching import query_cache_manager
        status = query_cache_manager.get_comprehensive_status()
        hit_rate = status["analytics"]["performance_metrics"]["hit_rate_percentage"]
        return f"Cache hit rate: {hit_rate}%"


@strawberry.type  
class AdvancedMutation:
    """Enhanced mutation type with advanced capabilities."""
    
    @strawberry.field
    async def ping(self) -> str:
        """Ping mutation for testing."""
        return "pong"
    
    @strawberry.field
    async def invalidate_cache(self, pattern: Optional[str] = None) -> str:
        """Invalidate cache entries."""
        from app.graphql.advanced.caching import query_cache_manager
        
        if pattern:
            count = query_cache_manager.cache.invalidate_by_pattern(pattern)
            return f"Invalidated {count} cache entries matching pattern: {pattern}"
        else:
            count = query_cache_manager.cache.clear()
            return f"Cleared all {count} cache entries"
    
    @strawberry.field
    async def publish_event(self, event_type: str, message: str) -> str:
        """Publish subscription event."""
        from app.graphql.advanced.subscriptions import subscription_manager, SubscriptionEventType
        
        # Convert string to enum
        try:
            event_enum = SubscriptionEventType(event_type)
        except ValueError:
            return f"Invalid event type: {event_type}"
        
        event_id = await subscription_manager.publish_event(
            event_enum,
            {"message": message, "source": "graphql_mutation"},
            source="graphql"
        )
        
        return f"Published event {event_id} of type {event_type}"


@strawberry.type
class AdvancedSubscription(AdvancedSubscriptions):
    """Enhanced subscription type with advanced real-time capabilities."""
    
    @strawberry.subscription
    async def count(self, target: int = 100) -> int:
        """Example subscription for counting."""
        for i in range(target):
            yield i


# Create enhanced GraphQL schema
advanced_schema = strawberry.Schema(
    query=AdvancedQuery,
    mutation=AdvancedMutation,
    subscription=AdvancedSubscription,
    extensions=[
        # Add middleware extensions here
    ]
)