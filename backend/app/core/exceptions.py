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
    """Raised when business logic validation fails."""

    pass


class NotFound(Exception):
    """Raised when a resource is not found."""

    pass


class PermissionDenied(Exception):
    """Raised when user lacks permission for an action."""

    pass


class AlreadyExists(Exception):
    """Raised when attempting to create a resource that already exists."""

    pass


class ValidationError(Exception):
    """Raised when validation fails."""

    pass
