"""Common schemas used across the API."""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    detail: str
    status_code: Optional[int] = None
    error_code: Optional[str] = None


class PaginationParams(BaseModel):
    """Pagination parameters."""
    
    skip: int = 0
    limit: int = 100


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    
    items: list[T]
    total: int
    skip: int
    limit: int


class DeleteResponse(BaseModel):
    """Standard delete response."""
    
    success: bool
    message: str