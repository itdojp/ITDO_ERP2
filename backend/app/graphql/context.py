"""GraphQL context for dependency injection and authentication."""

from functools import partial
from typing import Optional, Union

import strawberry
from aiodataloader import DataLoader
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.user import User
from app.graphql.dataloaders.user_loader import load_users_batch
from app.graphql.dataloaders.organization_loader import load_organizations_batch
from app.graphql.dataloaders.task_loader import load_tasks_batch


@strawberry.type
class GraphQLContext:
    """GraphQL context with authentication and DataLoaders."""

    def __init__(
        self,
        request: Request,
        db: Union[Session, AsyncSession],
        current_user: Optional[User] = None
    ):
        """Initialize GraphQL context."""
        self.request = request
        self.db = db
        self.current_user = current_user
        
        # Initialize DataLoaders for N+1 problem prevention
        self.user_loader = DataLoader(
            load_fn=partial(load_users_batch, db)
        )
        self.organization_loader = DataLoader(
            load_fn=partial(load_organizations_batch, db)
        )
        self.task_loader = DataLoader(
            load_fn=partial(load_tasks_batch, db)
        )

    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.current_user is not None

    @property
    def user_id(self) -> Optional[int]:
        """Get current user ID."""
        return self.current_user.id if self.current_user else None

    @property
    def organization_id(self) -> Optional[int]:
        """Get current user's organization ID."""
        return self.current_user.organization_id if self.current_user else None

    def require_authentication(self) -> User:
        """Require authentication and return user."""
        if not self.is_authenticated:
            raise PermissionError("Authentication required")
        return self.current_user

    def require_permission(self, permission: str) -> User:
        """Require specific permission and return user."""
        user = self.require_authentication()
        if not user.has_permission(permission):
            raise PermissionError(f"Permission '{permission}' required")
        return user

    def require_superuser(self) -> User:
        """Require superuser privileges and return user."""
        user = self.require_authentication()
        if not user.is_superuser:
            raise PermissionError("Superuser privileges required")
        return user