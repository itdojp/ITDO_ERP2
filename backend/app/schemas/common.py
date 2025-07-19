"""Common schemas used across the ITDO ERP System."""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

# Type variable for generic responses
T = TypeVar("T")


class ErrorResponse(BaseModel):
    """Standard error response schema."""

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


class SuccessResponse(BaseModel):
    """Standard success response schema."""

    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    data: dict[str, Any] | list[Any] | str | int | float | bool | None = Field(None, description="Additional data")

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


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response schema."""

    items: list[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum number of items returned")
    has_more: bool | None = Field(None, description="Whether more items are available")

    def __init__(self, **data: dict[str, Any]) -> None:
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
    value: str | int | float | bool | list[Any] | None = Field(..., description="Filter value")

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


class AgentStatusResponse(BaseModel):
    """Agent status response schema for cost optimization monitoring."""

    agent_id: str = Field(..., description="Agent identifier")
    status: str = Field(..., description="Agent status (online, offline, busy)")
    environment: str = Field(
        ..., description="Environment (development, staging, production)"
    )
    last_seen: datetime = Field(..., description="Last activity timestamp")
    task_count: int = Field(..., description="Number of active tasks")
    cost_reduction: float | None = Field(None, description="Cost reduction percentage")
    escalation_level: int = Field(0, description="Current escalation level (0-3)")
    performance_metrics: dict[str, Any] | None = Field(
        None, description="Performance metrics"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "CC01",
                "status": "online",
                "environment": "production",
                "last_seen": "2024-01-06T12:00:00Z",
                "task_count": 3,
                "cost_reduction": 68.4,
                "escalation_level": 0,
                "performance_metrics": {
                    "response_time_ms": 1200,
                    "success_rate": 0.95,
                    "error_count": 1,
                },
            }
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
    "AgentStatusResponse",
]
