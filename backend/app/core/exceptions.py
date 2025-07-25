"""Custom exceptions for the application."""

from fastapi import HTTPException


class AuthenticationError(Exception):
    """Base authentication error."""


class ExpiredTokenError(AuthenticationError):
    """Raised when a token has expired."""


class InvalidTokenError(AuthenticationError):
    """Raised when a token is invalid."""


class AuthorizationError(Exception):
    """Raised when user lacks required permissions."""


class BusinessLogicError(Exception):
    """Raised when business logic validation fails."""


class NotFound(Exception):  # noqa: N818
    """Raised when a resource is not found."""


class PermissionDenied(Exception):  # noqa: N818
    """Raised when user lacks permission for an action."""


class AlreadyExists(Exception):  # noqa: N818
    """Raised when attempting to create a resource that already exists."""


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


class BusinessRuleError(Exception):
    """Raised when business rule validation fails."""

    pass


class NotFoundError(Exception):
    """Raised when a requested resource is not found."""

    pass


# Additional HTTP exceptions for Issue #568 - ERPビジネスAPI
class NotFoundException(HTTPException):
    """Resource not found exception."""
    
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)


class ValidationException(HTTPException):
    """Business validation exception."""
    
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(status_code=400, detail=detail)


class DuplicateException(HTTPException):
    """Duplicate resource exception."""
    
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status_code=400, detail=detail)


class BusinessLogicException(HTTPException):
    """Business logic validation exception."""
    
    def __init__(self, detail: str = "Business logic validation failed"):
        super().__init__(status_code=400, detail=detail)


class InsufficientStockException(HTTPException):
    """Insufficient stock exception."""
    
    def __init__(self, detail: str = "Insufficient stock"):
        super().__init__(status_code=400, detail=detail)


class PermissionDeniedException(HTTPException):
    """Permission denied exception."""
    
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status_code=403, detail=detail)
