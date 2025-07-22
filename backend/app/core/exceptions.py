"""Custom exceptions for the application."""


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

