"""
Common pagination utilities for ERP API
"""

from typing import TypeVar, Generic, List, Any, Optional
from math import ceil
from pydantic import BaseModel
from sqlalchemy.orm import Query

T = TypeVar('T')


class Page(BaseModel, Generic[T]):
    """Generic pagination response model"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool
    next_page: Optional[int] = None
    prev_page: Optional[int] = None


class PaginationParams(BaseModel):
    """Pagination parameters for API requests"""
    page: int = 1
    size: int = 20
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size
    
    @property
    def limit(self) -> int:
        return self.size


def paginate(
    query: Query,
    page: int = 1,
    size: int = 20,
    max_size: int = 100
) -> tuple[List[Any], int]:
    """
    Paginate a SQLAlchemy query
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-based)
        size: Items per page
        max_size: Maximum items per page allowed
        
    Returns:
        Tuple of (items, total_count)
    """
    # Validate parameters
    page = max(1, page)
    size = min(max(1, size), max_size)
    
    # Calculate offset
    offset = (page - 1) * size
    
    # Get total count
    total = query.count()
    
    # Get items for current page
    items = query.offset(offset).limit(size).all()
    
    return items, total


def create_page_response(
    items: List[T],
    total: int,
    page: int = 1,
    size: int = 20
) -> Page[T]:
    """
    Create a paginated response
    
    Args:
        items: List of items for current page
        total: Total number of items
        page: Current page number
        size: Items per page
        
    Returns:
        Page response object
    """
    pages = ceil(total / size) if size > 0 else 0
    has_next = page < pages
    has_prev = page > 1
    
    return Page[T](
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
        has_next=has_next,
        has_prev=has_prev,
        next_page=page + 1 if has_next else None,
        prev_page=page - 1 if has_prev else None
    )


def get_pagination_metadata(
    total: int,
    page: int = 1,
    size: int = 20
) -> dict:
    """
    Get pagination metadata without items
    
    Args:
        total: Total number of items
        page: Current page number
        size: Items per page
        
    Returns:
        Dictionary with pagination metadata
    """
    pages = ceil(total / size) if size > 0 else 0
    offset = (page - 1) * size
    
    return {
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
        "offset": offset,
        "limit": size,
        "has_next": page < pages,
        "has_prev": page > 1,
        "next_page": page + 1 if page < pages else None,
        "prev_page": page - 1 if page > 1 else None
    }


class CursorPagination:
    """Cursor-based pagination for large datasets"""
    
    def __init__(self, cursor_field: str = "id"):
        self.cursor_field = cursor_field
    
    def paginate(
        self,
        query: Query,
        cursor: Optional[Any] = None,
        size: int = 20,
        direction: str = "next"
    ) -> tuple[List[Any], Optional[str]]:
        """
        Paginate using cursor-based approach
        
        Args:
            query: SQLAlchemy query
            cursor: Current cursor value
            size: Number of items to return
            direction: "next" or "prev"
            
        Returns:
            Tuple of (items, next_cursor)
        """
        if cursor is not None:
            cursor_column = getattr(query.column_descriptions[0]['type'], self.cursor_field)
            if direction == "next":
                query = query.filter(cursor_column > cursor)
            else:
                query = query.filter(cursor_column < cursor)
        
        # Get one extra item to determine if there are more
        items = query.limit(size + 1).all()
        
        has_more = len(items) > size
        if has_more:
            items = items[:size]
        
        next_cursor = None
        if has_more and items:
            next_cursor = str(getattr(items[-1], self.cursor_field))
        
        return items, next_cursor