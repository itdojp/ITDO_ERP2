"""Common GraphQL types for pagination and connections."""

from typing import Generic, List, Optional, TypeVar

import strawberry

T = TypeVar("T")


@strawberry.type
class PageInfo:
    """Page information for Relay-style pagination."""
    
    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str] = None
    end_cursor: Optional[str] = None


@strawberry.type
class Edge(Generic[T]):
    """Edge type for Relay-style connections."""
    
    node: T
    cursor: str


@strawberry.type
class Connection(Generic[T]):
    """Connection type for Relay-style pagination."""
    
    edges: List[Edge[T]]
    page_info: PageInfo
    total_count: int


@strawberry.input
class PaginationInput:
    """Input type for pagination parameters."""
    
    first: Optional[int] = None
    after: Optional[str] = None
    last: Optional[int] = None
    before: Optional[str] = None


@strawberry.input
class SortInput:
    """Input type for sorting parameters."""
    
    field: str
    direction: str = "ASC"  # ASC or DESC


@strawberry.enum
class SortDirection:
    """Sort direction enumeration."""
    
    ASC = "ASC"
    DESC = "DESC"