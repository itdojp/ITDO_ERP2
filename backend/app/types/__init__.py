"""Type definitions for ITDO ERP System.

This module provides common type definitions and protocols used throughout
the application.
"""

from datetime import datetime
from typing import Any, Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel
from sqlalchemy.orm import Session

# Generic type variables
T = TypeVar("T")
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)

# ID types for better type safety
UserId = int
OrganizationId = int
DepartmentId = int
RoleId = int
ProductId = int
CustomerId = int
SupplierId = int


@runtime_checkable
class DatabaseProtocol(Protocol):
    """Protocol for database session management."""

    def get_session(self) -> Session: ...
    def close(self) -> None: ...


@runtime_checkable
class CacheProtocol(Protocol):
    """Protocol for cache operations."""

    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str, expire: int = 3600) -> None: ...
    def delete(self, key: str) -> None: ...
    def exists(self, key: str) -> bool: ...


@runtime_checkable
class AuditableProtocol(Protocol):
    """Protocol for auditable entities."""

    created_at: datetime
    updated_at: datetime
    created_by: UserId | None
    updated_by: UserId | None


@runtime_checkable
class SoftDeletableProtocol(Protocol):
    """Protocol for soft-deletable entities."""

    deleted_at: datetime | None
    deleted_by: UserId | None
    is_deleted: bool


# Result types for service layer
class ServiceResult(BaseModel):
    """Generic service operation result."""

    success: bool
    data: Any | None = None
    error: str | None = None
    error_code: str | None = None


class PaginationParams(BaseModel):
    """Common pagination parameters."""

    skip: int = 0
    limit: int = 100
    sort_by: str | None = None
    sort_order: str = "asc"


class SearchParams(BaseModel):
    """Common search parameters."""

    query: str | None = None
    filters: dict[str, Any] = {}
    pagination: PaginationParams = PaginationParams()


# Export all types
__all__ = [
    # Type variables
    "T",
    "ModelType",
    "CreateSchemaType",
    "UpdateSchemaType",
    "ResponseSchemaType",
    # ID types
    "UserId",
    "OrganizationId",
    "DepartmentId",
    "RoleId",
    "ProductId",
    "CustomerId",
    "SupplierId",
    # Protocols
    "DatabaseProtocol",
    "CacheProtocol",
    "AuditableProtocol",
    "SoftDeletableProtocol",
    # Result types
    "ServiceResult",
    "PaginationParams",
    "SearchParams",
]
