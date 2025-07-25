"""
Claude Code Python Template - Copy this structure when creating new files.

This template ensures Code Quality compliance from the start.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.models.base import Base
from app.schemas.base import BaseSchema


class ExampleService:
    """Example service class with proper type annotations and docstrings."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service with database session.

        Args:
            db: Async database session
        """
        self.db = db

    async def get_item(self, item_id: int) -> Optional[dict[str, Any]]:
        """Retrieve item by ID.

        Args:
            item_id: The ID of the item to retrieve

        Returns:
            Item data if found, None otherwise

        Raises:
            HTTPException: If database error occurs
        """
        try:
            # Implementation here
            return {"id": item_id, "name": "Example"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            ) from e


# API endpoint example with proper formatting
async def create_item(
    data: BaseSchema,
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Create a new item.

    Args:
        data: Item creation data
        db: Database session dependency

    Returns:
        Created item data
    """
    service = ExampleService(db)
    # Line break for long function calls
    result = await service.create_item_with_long_parameters(
        name=data.name,
        description=data.description,
        category=data.category,
        tags=data.tags,
    )
    return result