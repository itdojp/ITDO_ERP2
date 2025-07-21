"""Base service class with common functionality for all business services."""

import logging
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.monitoring import monitor_performance
from app.models.base import BaseModel

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class BaseService(Generic[T]):
    """Base service class providing common CRUD operations and utilities."""

    def __init__(self, model: Type[T], db: Union[AsyncSession, Session]):
        """Initialize base service with model class and database session."""
        self.model = model
        self.db = db
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    @monitor_performance("service.get_by_id")
    async def get_by_id(self, id: int, organization_id: Optional[int] = None) -> Optional[T]:
        """Get entity by ID with optional organization filtering."""
        query = select(self.model).where(self.model.id == id)
        
        # Add organization filter if model has organization_id and it's provided
        if hasattr(self.model, 'organization_id') and organization_id is not None:
            query = query.where(self.model.organization_id == organization_id)
        
        if hasattr(self.db, 'execute'):  # AsyncSession
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        else:  # Session
            return self.db.execute(query).scalar_one_or_none()

    @monitor_performance("service.get_all")
    async def get_all(
        self, 
        organization_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Get all entities with optional filtering and pagination."""
        query = select(self.model)
        
        # Add organization filter
        if hasattr(self.model, 'organization_id') and organization_id is not None:
            query = query.where(self.model.organization_id == organization_id)
        
        # Apply additional filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    column = getattr(self.model, field)
                    if isinstance(value, list):
                        query = query.where(column.in_(value))
                    else:
                        query = query.where(column == value)
        
        # Apply pagination
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        
        # Add default ordering
        if hasattr(self.model, 'created_at'):
            query = query.order_by(self.model.created_at.desc())
        elif hasattr(self.model, 'id'):
            query = query.order_by(self.model.id.desc())
        
        if hasattr(self.db, 'execute'):  # AsyncSession
            result = await self.db.execute(query)
            return list(result.scalars().all())
        else:  # Session
            return list(self.db.execute(query).scalars().all())

    @monitor_performance("service.create")
    async def create(self, data: Dict[str, Any], organization_id: Optional[int] = None) -> T:
        """Create new entity."""
        # Add organization_id if model supports it
        if hasattr(self.model, 'organization_id') and organization_id is not None:
            data['organization_id'] = organization_id
        
        entity = self.model(**data)
        self.db.add(entity)
        
        if hasattr(self.db, 'commit'):  # AsyncSession
            await self.db.commit()
            await self.db.refresh(entity)
        else:  # Session
            self.db.commit()
            self.db.refresh(entity)
        
        self.logger.info(f"Created {self.model.__name__} with ID {entity.id}")
        return entity

    @monitor_performance("service.update")
    async def update(
        self, 
        id: int, 
        data: Dict[str, Any], 
        organization_id: Optional[int] = None
    ) -> Optional[T]:
        """Update entity by ID."""
        # Build update query
        query = update(self.model).where(self.model.id == id)
        
        # Add organization filter
        if hasattr(self.model, 'organization_id') and organization_id is not None:
            query = query.where(self.model.organization_id == organization_id)
        
        query = query.values(**data)
        
        if hasattr(self.db, 'execute'):  # AsyncSession
            result = await self.db.execute(query)
            if result.rowcount == 0:
                return None
            await self.db.commit()
            # Get updated entity
            return await self.get_by_id(id, organization_id)
        else:  # Session
            result = self.db.execute(query)
            if result.rowcount == 0:
                return None
            self.db.commit()
            return self.get_by_id(id, organization_id)

    @monitor_performance("service.delete")
    async def delete(self, id: int, organization_id: Optional[int] = None) -> bool:
        """Delete entity by ID."""
        query = delete(self.model).where(self.model.id == id)
        
        # Add organization filter
        if hasattr(self.model, 'organization_id') and organization_id is not None:
            query = query.where(self.model.organization_id == organization_id)
        
        if hasattr(self.db, 'execute'):  # AsyncSession
            result = await self.db.execute(query)
            await self.db.commit()
            success = result.rowcount > 0
        else:  # Session
            result = self.db.execute(query)
            self.db.commit()
            success = result.rowcount > 0
        
        if success:
            self.logger.info(f"Deleted {self.model.__name__} with ID {id}")
        
        return success

    @monitor_performance("service.count")
    async def count(
        self, 
        organization_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Count entities with optional filtering."""
        query = select(func.count(self.model.id))
        
        # Add organization filter
        if hasattr(self.model, 'organization_id') and organization_id is not None:
            query = query.where(self.model.organization_id == organization_id)
        
        # Apply additional filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    column = getattr(self.model, field)
                    if isinstance(value, list):
                        query = query.where(column.in_(value))
                    else:
                        query = query.where(column == value)
        
        if hasattr(self.db, 'execute'):  # AsyncSession
            result = await self.db.execute(query)
            return result.scalar()
        else:  # Session
            return self.db.execute(query).scalar()

    @monitor_performance("service.exists")
    async def exists(self, id: int, organization_id: Optional[int] = None) -> bool:
        """Check if entity exists."""
        query = select(func.count(self.model.id)).where(self.model.id == id)
        
        # Add organization filter
        if hasattr(self.model, 'organization_id') and organization_id is not None:
            query = query.where(self.model.organization_id == organization_id)
        
        if hasattr(self.db, 'execute'):  # AsyncSession
            result = await self.db.execute(query)
            return result.scalar() > 0
        else:  # Session
            return self.db.execute(query).scalar() > 0

    async def bulk_create(self, data_list: List[Dict[str, Any]], organization_id: Optional[int] = None) -> List[T]:
        """Bulk create multiple entities."""
        entities = []
        for data in data_list:
            if hasattr(self.model, 'organization_id') and organization_id is not None:
                data['organization_id'] = organization_id
            entities.append(self.model(**data))
        
        self.db.add_all(entities)
        
        if hasattr(self.db, 'commit'):  # AsyncSession
            await self.db.commit()
            for entity in entities:
                await self.db.refresh(entity)
        else:  # Session
            self.db.commit()
            for entity in entities:
                self.db.refresh(entity)
        
        self.logger.info(f"Bulk created {len(entities)} {self.model.__name__} entities")
        return entities

    def get_organization_filter(self, organization_id: Optional[int] = None) -> Optional[Any]:
        """Get organization filter condition if applicable."""
        if hasattr(self.model, 'organization_id') and organization_id is not None:
            return self.model.organization_id == organization_id
        return None


class CachedService(BaseService[T]):
    """Service with caching capabilities."""

    def __init__(self, model: Type[T], db: Union[AsyncSession, Session], cache_ttl: int = 300):
        """Initialize cached service."""
        super().__init__(model, db)
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Any] = {}

    def _get_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
        return f"{self.model.__name__}:{':'.join(key_parts)}"

    def _set_cache(self, key: str, value: Any) -> None:
        """Set cache value."""
        # Simple in-memory cache (in production, use Redis)
        self._cache[key] = value

    def _get_cache(self, key: str) -> Optional[Any]:
        """Get cached value."""
        return self._cache.get(key)

    def _clear_cache_pattern(self, pattern: str) -> None:
        """Clear cache entries matching pattern."""
        keys_to_remove = [key for key in self._cache.keys() if pattern in key]
        for key in keys_to_remove:
            del self._cache[key]

    async def get_by_id(self, id: int, organization_id: Optional[int] = None) -> Optional[T]:
        """Get entity by ID with caching."""
        cache_key = self._get_cache_key("get_by_id", id, organization_id)
        cached_result = self._get_cache(cache_key)
        
        if cached_result is not None:
            return cached_result
        
        result = await super().get_by_id(id, organization_id)
        self._set_cache(cache_key, result)
        return result

    async def create(self, data: Dict[str, Any], organization_id: Optional[int] = None) -> T:
        """Create entity and clear relevant cache."""
        result = await super().create(data, organization_id)
        # Clear cache for list operations
        self._clear_cache_pattern("get_all")
        self._clear_cache_pattern("count")
        return result

    async def update(
        self, 
        id: int, 
        data: Dict[str, Any], 
        organization_id: Optional[int] = None
    ) -> Optional[T]:
        """Update entity and clear relevant cache."""
        result = await super().update(id, data, organization_id)
        # Clear cache for this entity and list operations
        self._clear_cache_pattern(f"get_by_id:{id}")
        self._clear_cache_pattern("get_all")
        return result

    async def delete(self, id: int, organization_id: Optional[int] = None) -> bool:
        """Delete entity and clear relevant cache."""
        result = await super().delete(id, organization_id)
        if result:
            # Clear cache for this entity and list operations
            self._clear_cache_pattern(f"get_by_id:{id}")
            self._clear_cache_pattern("get_all")
            self._clear_cache_pattern("count")
        return result