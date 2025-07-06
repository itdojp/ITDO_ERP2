"""Base repository implementation for ITDO ERP System.

This module provides a generic repository pattern implementation with full type safety.
"""
from typing import TypeVar, Generic, Optional, List, Dict, Any, Type
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.sql import Select
from app.models.base import Base
from app.types import (
    ModelType,
    CreateSchemaType,
    UpdateSchemaType,
    PaginationParams,
    SearchParams,
    ServiceResult
)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository providing CRUD operations with type safety."""
    
    def __init__(self, model: Type[ModelType], db: Session):
        """Initialize repository with model class and database session."""
        self.model = model
        self.db = db
    
    def get(self, id: int) -> Optional[ModelType]:
        """Get a single record by ID."""
        return self.db.scalar(select(self.model).where(self.model.id == id))
    
    def get_by_ids(self, ids: List[int]) -> List[ModelType]:
        """Get multiple records by IDs."""
        return list(self.db.scalars(select(self.model).where(self.model.id.in_(ids))))
    
    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """Get multiple records with optional filtering."""
        query = select(self.model)
        
        if filters:
            conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    conditions.append(getattr(self.model, key) == value)
            if conditions:
                query = query.where(and_(*conditions))
        
        query = query.offset(skip).limit(limit)
        return list(self.db.scalars(query))
    
    def get_count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Get total count of records with optional filtering."""
        query = select(func.count(self.model.id))
        
        if filters:
            conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    conditions.append(getattr(self.model, key) == value)
            if conditions:
                query = query.where(and_(*conditions))
        
        return self.db.scalar(query) or 0
    
    def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record."""
        obj_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else dict(obj_in)
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def create_multi(self, objs_in: List[CreateSchemaType]) -> List[ModelType]:
        """Create multiple records in a single transaction."""
        db_objs = []
        for obj_in in objs_in:
            obj_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else dict(obj_in)
            db_obj = self.model(**obj_data)
            self.db.add(db_obj)
            db_objs.append(db_obj)
        
        self.db.commit()
        for db_obj in db_objs:
            self.db.refresh(db_obj)
        return db_objs
    
    def update(self, id: int, obj_in: UpdateSchemaType) -> Optional[ModelType]:
        """Update a record by ID."""
        obj_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, 'model_dump') else dict(obj_in)
        
        # Remove None values to avoid overwriting with NULL
        obj_data = {k: v for k, v in obj_data.items() if v is not None}
        
        if obj_data:
            self.db.execute(
                update(self.model)
                .where(self.model.id == id)
                .values(**obj_data)
            )
            self.db.commit()
        
        return self.get(id)
    
    def update_multi(
        self,
        ids: List[int],
        obj_in: UpdateSchemaType
    ) -> List[ModelType]:
        """Update multiple records by IDs."""
        obj_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, 'model_dump') else dict(obj_in)
        obj_data = {k: v for k, v in obj_data.items() if v is not None}
        
        if obj_data and ids:
            self.db.execute(
                update(self.model)
                .where(self.model.id.in_(ids))
                .values(**obj_data)
            )
            self.db.commit()
        
        return self.get_by_ids(ids)
    
    def delete(self, id: int) -> bool:
        """Delete a record by ID (hard delete)."""
        result = self.db.execute(
            delete(self.model).where(self.model.id == id)
        )
        self.db.commit()
        return result.rowcount > 0
    
    def delete_multi(self, ids: List[int]) -> int:
        """Delete multiple records by IDs (hard delete)."""
        if not ids:
            return 0
        
        result = self.db.execute(
            delete(self.model).where(self.model.id.in_(ids))
        )
        self.db.commit()
        return result.rowcount
    
    def exists(self, id: int) -> bool:
        """Check if a record exists by ID."""
        return self.db.scalar(
            select(func.count(self.model.id))
            .where(self.model.id == id)
        ) > 0
    
    def search(self, params: SearchParams) -> tuple[List[ModelType], int]:
        """Search records with pagination."""
        query = select(self.model)
        
        # Apply search query if provided
        if params.query and hasattr(self.model, 'name'):
            query = query.where(
                self.model.name.ilike(f"%{params.query}%")
            )
        
        # Apply filters
        if params.filters:
            conditions = []
            for key, value in params.filters.items():
                if hasattr(self.model, key):
                    conditions.append(getattr(self.model, key) == value)
            if conditions:
                query = query.where(and_(*conditions))
        
        # Get total count before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_count = self.db.scalar(count_query) or 0
        
        # Apply sorting
        if params.pagination.sort_by and hasattr(self.model, params.pagination.sort_by):
            sort_column = getattr(self.model, params.pagination.sort_by)
            if params.pagination.sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        
        # Apply pagination
        query = query.offset(params.pagination.skip).limit(params.pagination.limit)
        
        results = list(self.db.scalars(query))
        return results, total_count
    
    def bulk_upsert(
        self,
        objs_in: List[CreateSchemaType],
        unique_fields: List[str]
    ) -> List[ModelType]:
        """Bulk insert or update records based on unique fields."""
        created = []
        updated = []
        
        for obj_in in objs_in:
            obj_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else dict(obj_in)
            
            # Build query to find existing record
            conditions = []
            for field in unique_fields:
                if field in obj_data and hasattr(self.model, field):
                    conditions.append(getattr(self.model, field) == obj_data[field])
            
            if conditions:
                existing = self.db.scalar(
                    select(self.model).where(and_(*conditions))
                )
                
                if existing:
                    # Update existing record
                    for key, value in obj_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    updated.append(existing)
                else:
                    # Create new record
                    db_obj = self.model(**obj_data)
                    self.db.add(db_obj)
                    created.append(db_obj)
        
        self.db.commit()
        
        # Refresh all objects
        for obj in created + updated:
            self.db.refresh(obj)
        
        return created + updated