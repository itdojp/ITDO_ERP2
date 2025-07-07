"""Base API router implementation for ITDO ERP System.

This module provides a generic API router with full type safety and standard CRUD operations.
"""
from typing import TypeVar, Generic, Optional, List, Dict, Any, Type, Callable, Sequence
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.repositories.base import BaseRepository
from app.core.dependencies import get_db, get_current_active_user as get_current_user
from app.types import (
    ModelType,
    CreateSchemaType,
    UpdateSchemaType,
    ResponseSchemaType,
    ServiceResult,
    PaginationParams,
    SearchParams
)
from app.schemas.common import (
    ErrorResponse,
    PaginatedResponse,
    SuccessResponse,
    DeleteResponse
)
from app.models.user import User

class BaseAPIRouter(Generic[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]):
    """Base API router providing standard CRUD operations with type safety."""
    
    def __init__(
        self,
        *,
        prefix: str,
        tags: Sequence[str],
        model: Type[ModelType],
        repository: Type[BaseRepository[ModelType, CreateSchemaType, UpdateSchemaType]],
        create_schema: Type[CreateSchemaType],
        update_schema: Type[UpdateSchemaType],
        response_schema: Type[ResponseSchemaType],
        get_current_user_fn: Optional[Callable[..., Any]] = None,
        dependencies: Optional[List[Any]] = None
    ):
        """Initialize base API router with configurations."""
        self.model = model
        self.repository = repository
        self.create_schema = create_schema
        self.update_schema = update_schema
        self.response_schema = response_schema
        self.get_current_user_fn = get_current_user_fn or get_current_user
        
        # Create router with optional dependencies
        router_dependencies = dependencies or []
        if self.get_current_user_fn:
            router_dependencies.append(Depends(self.get_current_user_fn))
        
        self.router = APIRouter(
            prefix=prefix,
            tags=tags,
            dependencies=router_dependencies
        )
        
        # Setup all routes
        self._setup_routes()
    
    def _setup_routes(self) -> None:
        """Setup all CRUD routes."""
        
        @self.router.get("/", response_model=PaginatedResponse[ResponseSchemaType])
        async def list_items(
            skip: int = Query(0, ge=0, description="Number of items to skip"),
            limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
            search: Optional[str] = Query(None, description="Search query"),
            sort_by: Optional[str] = Query(None, description="Field to sort by"),
            sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
            db: Session = Depends(get_db),
            current_user: User = Depends(self.get_current_user_fn)
        ) -> PaginatedResponse[ResponseSchemaType]:
            """List items with pagination and search."""
            repo = self.repository(self.model, db)
            
            # Build search parameters
            search_params = SearchParams(
                query=search,
                pagination=PaginationParams(
                    skip=skip,
                    limit=limit,
                    sort_by=sort_by,
                    sort_order=sort_order
                )
            )
            
            # Get items and total count
            items, total_count = repo.search(search_params)
            
            # Convert to response schema
            items_data = [
                self.response_schema.model_validate(item.to_dict())
                for item in items
            ]
            
            return PaginatedResponse(
                items=items_data,
                total=total_count,
                skip=skip,
                limit=limit
            )
        
        @self.router.get("/{item_id}", response_model=self.response_schema)
        async def get_item(
            item_id: int,
            db: Session = Depends(get_db),
            current_user: User = Depends(self.get_current_user_fn)
        ) -> ResponseSchemaType:
            """Get a single item by ID."""
            repo = self.repository(self.model, db)
            item = repo.get(item_id)
            
            if not item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{self.model.__name__} not found"
                )
            
            return self.response_schema.model_validate(item.to_dict())
        
        @self.router.post("/", response_model=self.response_schema, status_code=status.HTTP_201_CREATED)
        async def create_item(
            item_in: CreateSchemaType,
            db: Session = Depends(get_db),
            current_user: User = Depends(self.get_current_user_fn)
        ) -> ResponseSchemaType:
            """Create a new item."""
            repo = self.repository(self.model, db)
            
            # Add audit fields if model supports them
            item_data = item_in.model_dump()
            if hasattr(self.model, 'created_by'):
                item_data['created_by'] = current_user.id
            if hasattr(self.model, 'updated_by'):
                item_data['updated_by'] = current_user.id
            
            # Create item
            item = repo.create(self.create_schema(**item_data))
            
            return self.response_schema.model_validate(item.to_dict())
        
        @self.router.put("/{item_id}", response_model=self.response_schema)
        async def update_item(
            item_id: int,
            item_in: UpdateSchemaType,
            db: Session = Depends(get_db),
            current_user: User = Depends(self.get_current_user_fn)
        ) -> ResponseSchemaType:
            """Update an existing item."""
            repo = self.repository(self.model, db)
            
            # Check if item exists
            existing_item = repo.get(item_id)
            if not existing_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{self.model.__name__} not found"
                )
            
            # Add audit fields if model supports them
            item_data = item_in.model_dump(exclude_unset=True)
            if hasattr(self.model, 'updated_by'):
                item_data['updated_by'] = current_user.id
            
            # Update item
            item = repo.update(item_id, self.update_schema(**item_data))
            
            if not item:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update item"
                )
            
            return self.response_schema.model_validate(item.to_dict())
        
        @self.router.delete("/{item_id}", response_model=DeleteResponse)
        async def delete_item(
            item_id: int,
            db: Session = Depends(get_db),
            current_user: User = Depends(self.get_current_user_fn)
        ) -> DeleteResponse:
            """Delete an item."""
            repo = self.repository(self.model, db)
            
            # Check if item exists
            existing_item = repo.get(item_id)
            if not existing_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{self.model.__name__} not found"
                )
            
            # Check if model supports soft delete
            if hasattr(existing_item, 'soft_delete'):
                existing_item.soft_delete(deleted_by=current_user.id)
                db.commit()
                message = f"{self.model.__name__} soft deleted successfully"
            else:
                # Hard delete
                success = repo.delete(item_id)
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to delete item"
                    )
                message = f"{self.model.__name__} deleted successfully"
            
            return DeleteResponse(
                success=True,
                message=message,
                id=item_id
            )
        
        @self.router.post("/bulk", response_model=List[ResponseSchemaType])
        async def create_items_bulk(
            items_in: List[CreateSchemaType],
            db: Session = Depends(get_db),
            current_user: User = Depends(self.get_current_user_fn)
        ) -> List[ResponseSchemaType]:
            """Create multiple items in bulk."""
            if not items_in:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No items provided"
                )
            
            if len(items_in) > 1000:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Too many items. Maximum 1000 items allowed"
                )
            
            repo = self.repository(self.model, db)
            
            # Add audit fields to all items
            items_data = []
            for item_in in items_in:
                item_data = item_in.model_dump()
                if hasattr(self.model, 'created_by'):
                    item_data['created_by'] = current_user.id
                if hasattr(self.model, 'updated_by'):
                    item_data['updated_by'] = current_user.id
                items_data.append(self.create_schema(**item_data))
            
            # Create items
            items = repo.create_multi(items_data)
            
            return [
                self.response_schema.model_validate(item.to_dict())
                for item in items
            ]
        
        @self.router.delete("/bulk", response_model=DeleteResponse)
        async def delete_items_bulk(
            item_ids: List[int] = Query(..., description="List of item IDs to delete"),
            db: Session = Depends(get_db),
            current_user: User = Depends(self.get_current_user_fn)
        ) -> DeleteResponse:
            """Delete multiple items in bulk."""
            if not item_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No item IDs provided"
                )
            
            if len(item_ids) > 1000:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Too many items. Maximum 1000 items allowed"
                )
            
            repo = self.repository(self.model, db)
            
            # Check if all items exist
            existing_items = repo.get_by_ids(item_ids)
            if len(existing_items) != len(item_ids):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Some items not found"
                )
            
            # Delete items
            deleted_count = 0
            for item in existing_items:
                if hasattr(item, 'soft_delete'):
                    item.soft_delete(deleted_by=current_user.id)
                    deleted_count += 1
                else:
                    if repo.delete(item.id):
                        deleted_count += 1
            
            db.commit()
            
            return DeleteResponse(
                success=True,
                message=f"{deleted_count} items deleted successfully",
                count=deleted_count
            )
    
    def get_router(self) -> APIRouter:
        """Get the configured router instance."""
        return self.router


# Export base router
__all__ = ['BaseAPIRouter']