"""Common schemas used across the API."""

from typing import Any, Optional

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    detail: str
    status_code: Optional[int] = None
    error_code: Optional[str] = None


class PaginationParams(BaseModel):
    """Pagination parameters."""
    
    skip: int = 0
    limit: int = 100


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    
    items: list[Any]
    total: int
    skip: int
    limit: int


class DeleteResponse(BaseModel):
    """Standard delete response."""
    
    success: bool
    message: str