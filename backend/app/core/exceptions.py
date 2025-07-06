"""Custom exceptions for the application."""


class AuthenticationError(Exception):
    """Base authentication error."""
    pass


class ExpiredTokenError(AuthenticationError):
    """Raised when a token has expired."""
    pass


class InvalidTokenError(AuthenticationError):
    """Raised when a token is invalid."""
    pass


class AuthorizationError(Exception):
    """Raised when user lacks required permissions."""
    pass


class BusinessLogicError(Exception):
    """Base business logic error."""
    pass


class NotFound(Exception):
    """Raised when a resource is not found."""
    pass


class PermissionDenied(Exception):
    """Raised when access is denied due to insufficient permissions."""
    pass


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass