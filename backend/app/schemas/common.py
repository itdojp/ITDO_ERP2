"""Common schemas used across the ITDO ERP System."""

from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

# Type variable for generic responses
T = TypeVar("T")


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    detail: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    field: Optional[str] = Field(None, description="Field that caused the error")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Resource not found",
                "code": "NOT_FOUND",
                "field": None,
            }
        }


class SuccessResponse(BaseModel):
    """Standard success response schema."""

    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    data: Optional[Any] = Field(None, description="Additional data")

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
    id: Optional[int] = Field(None, description="ID of deleted item")
    count: Optional[int] = Field(None, description="Number of deleted items")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Item deleted successfully",
                "id": 123,
                "count": 1,
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response schema."""

    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum number of items returned")
    has_more: Optional[bool] = Field(
        None, description="Whether more items are available"
    )

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


class HealthCheckResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")
    database: str = Field(..., description="Database connection status")
    cache: Optional[str] = Field(None, description="Cache connection status")

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
    errors: List[ErrorResponse] = Field(
        default_factory=list, description="List of errors"
    )
    success_ids: List[int] = Field(
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

    query: Optional[str] = Field(None, description="Search query string")
    filters: List[FilterOption] = Field(
        default_factory=list, description="List of filters"
    )
    sort: List[SortOption] = Field(
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
    created_by: Optional[int] = Field(
        None, description="ID of user who created the resource"
    )
    updated_at: datetime = Field(..., description="Last update timestamp")
    updated_by: Optional[int] = Field(
        None, description="ID of user who last updated the resource"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "created_at": "2024-01-06T12:00:00Z",
                "created_by": 1,
                "updated_at": "2024-01-06T12:00:00Z",
                "updated_by": 1,
            }
        }


class SoftDeleteInfo(BaseModel):
    """Soft delete information for resources."""

    is_deleted: bool = Field(..., description="Whether the resource is soft deleted")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")
    deleted_by: Optional[int] = Field(
        None, description="ID of user who deleted the resource"
    )

    class Config:
        json_schema_extra = {
            "example": {"is_deleted": False, "deleted_at": None, "deleted_by": None}
        }


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
