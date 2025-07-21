"""GraphQL API endpoint integration with FastAPI."""

from typing import Union

import strawberry
from fastapi import Request, Depends
from strawberry.fastapi import GraphQLRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.graphql.context import GraphQLContext
from app.graphql.schema import schema
from app.models.user import User


async def get_graphql_context(
    request: Request,
    db: Union[Session, AsyncSession] = Depends(get_db),
) -> GraphQLContext:
    """Create GraphQL context with authentication and database session."""
    # Try to get current user (authentication is optional for some queries)
    current_user = None
    try:
        # This will handle JWT token validation
        from app.core.dependencies import get_current_active_user
        current_user = await get_current_active_user(request, db)
    except Exception:
        # Authentication failed or no token provided
        # Some GraphQL queries might not require authentication
        pass
    
    return GraphQLContext(
        request=request,
        db=db,
        current_user=current_user
    )


# Create GraphQL router with authentication
graphql_app = GraphQLRouter(
    schema=schema,
    context_getter=get_graphql_context,
    graphiql=True,  # Enable GraphiQL interface for development
)