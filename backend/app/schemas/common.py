"""Common schemas used across the API."""

<<<<<<< HEAD
from typing import Generic, Optional, TypeVar
=======
from datetime import datetime
from typing import Any, Generic, TypeVar
>>>>>>> origin/main

from pydantic import BaseModel

T = TypeVar("T")


class ErrorResponse(BaseModel):
    """Standard error response."""

<<<<<<< HEAD
    detail: str
    status_code: Optional[int] = None
    error_code: Optional[str] = None
=======
    detail: str = Field(..., description="Error message")
    code: str | None = Field(None, description="Error code")
    field: str | None = Field(None, description="Field that caused the error")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Resource not found",
                "code": "NOT_FOUND",
                "field": None,
            }
        }
>>>>>>> origin/main


class PaginationParams(BaseModel):
    """Pagination parameters."""

<<<<<<< HEAD
    skip: int = 0
    limit: int = 100
=======
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    data: Any | None = Field(None, description="Additional data")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": None,
            }
        }


class DeleteResponse(BaseModel):
    """Response schema for delete operations."""

    success: bool = Field(..., description="Deletion success status")
    message: str = Field(..., description="Deletion message")
    id: int | None = Field(None, description="ID of deleted item")
    count: int | None = Field(None, description="Number of deleted items")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Item deleted successfully",
                "id": 123,
                "count": 1,
            }
        }
>>>>>>> origin/main


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

<<<<<<< HEAD
    items: list[T]
    total: int
    skip: int
    limit: int
=======
    items: list[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum number of items returned")
    has_more: bool | None = Field(None, description="Whether more items are available")

    def __init__(self, **data: Any) -> None:
        """Initialize paginated response with computed has_more field."""
        if "has_more" not in data:
            data["has_more"] = data.get("total", 0) > data.get("skip", 0) + len(
                data.get("items", [])
            )
        super().__init__(**data)

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "skip": 0,
                "limit": 20,
                "has_more": True,
            }
        }
>>>>>>> origin/main


class DeleteResponse(BaseModel):
    """Standard delete response."""

<<<<<<< HEAD
    success: bool
    message: str
=======
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")
    database: str = Field(..., description="Database connection status")
    cache: str | None = Field(None, description="Cache connection status")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-06T12:00:00Z",
                "version": "1.0.0",
                "database": "connected",
                "cache": "connected",
            }
        }


class BulkOperationResult(BaseModel):
    """Result of a bulk operation."""

    success_count: int = Field(..., description="Number of successful operations")
    error_count: int = Field(..., description="Number of failed operations")
    errors: list[ErrorResponse] = Field(
        default_factory=list, description="List of errors"
    )
    success_ids: list[int] = Field(
        default_factory=list, description="IDs of successful operations"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success_count": 95,
                "error_count": 5,
                "errors": [
                    {"detail": "Duplicate entry", "code": "DUPLICATE", "field": "email"}
                ],
                "success_ids": [1, 2, 3, 4, 5],
            }
        }


class FilterOption(BaseModel):
    """Filter option for search operations."""

    field: str = Field(..., description="Field name to filter on")
    operator: str = Field(
        ..., description="Filter operator (eq, ne, gt, lt, gte, lte, like, in)"
    )
    value: Any = Field(..., description="Filter value")

    class Config:
        json_schema_extra = {
            "example": {"field": "status", "operator": "eq", "value": "active"}
        }


class SortOption(BaseModel):
    """Sort option for search operations."""

    field: str = Field(..., description="Field name to sort by")
    order: str = Field("asc", description="Sort order (asc or desc)")

    class Config:
        json_schema_extra = {"example": {"field": "created_at", "order": "desc"}}


class SearchRequest(BaseModel):
    """Advanced search request schema."""

    query: str | None = Field(None, description="Search query string")
    filters: list[FilterOption] = Field(
        default_factory=list, description="List of filters"
    )
    sort: list[SortOption] = Field(
        default_factory=list, description="List of sort options"
    )
    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(
        100, ge=1, le=1000, description="Maximum number of items to return"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "search term",
                "filters": [{"field": "status", "operator": "eq", "value": "active"}],
                "sort": [{"field": "created_at", "order": "desc"}],
                "skip": 0,
                "limit": 20,
            }
        }


# Audit information schemas
class AuditInfo(BaseModel):
    """Audit information for resources."""

    created_at: datetime = Field(..., description="Creation timestamp")
    created_by: int | None = Field(
        None, description="ID of user who created the resource"
    )
    updated_at: datetime = Field(..., description="Last update timestamp")
    updated_by: int | None = Field(
        None, description="ID of user who last updated the resource"
    )


class SoftDeleteInfo(BaseModel):
    """Soft delete information for resources."""

    is_deleted: bool = Field(..., description="Whether the resource is soft deleted")
    deleted_at: datetime | None = Field(None, description="Deletion timestamp")
    deleted_by: int | None = Field(
        None, description="ID of user who deleted the resource"
    )


# Export all common schemas
__all__ = [
    "ErrorResponse",
    "SuccessResponse",
    "DeleteResponse",
    "PaginatedResponse",
    "HealthCheckResponse",
    "BulkOperationResult",
    "FilterOption",
    "SortOption",
    "SearchRequest",
    "AuditInfo",
    "SoftDeleteInfo",
]
>>>>>>> origin/main
