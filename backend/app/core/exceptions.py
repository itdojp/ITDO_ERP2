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