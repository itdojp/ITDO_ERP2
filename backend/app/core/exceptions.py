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


class CircularDependency(BusinessLogicError):
    """Raised when a circular dependency is detected."""
    pass


class InvalidTransition(BusinessLogicError):
    """Raised when an invalid status transition is attempted."""
    pass


class DependencyExists(BusinessLogicError):
    """Raised when trying to delete a task that has dependencies."""
    pass


class OptimisticLockError(BusinessLogicError):
    """Raised when optimistic locking fails due to concurrent modification."""
    pass