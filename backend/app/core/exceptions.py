"""Custom exceptions for the application."""

from typing import Any, Optional
from fastapi import HTTPException, status


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


class BaseAPIException(HTTPException):
    """Base exception for API errors."""
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[dict] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class ValidationError(BaseAPIException):
    """Raised when validation fails."""
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class PermissionDenied(BaseAPIException):
    """Raised when user doesn't have permission."""
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class NotFound(BaseAPIException):
    """Raised when resource is not found."""
    def __init__(self, resource: str = "Resource"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} not found"
        )


class TaskNotFound(NotFound):
    """Raised when task is not found."""
    def __init__(self, task_id: Optional[int] = None):
        detail = f"Task {task_id} not found" if task_id else "Task not found"
        super().__init__(resource="Task")
        self.detail = detail


class ProjectNotFound(NotFound):
    """Raised when project is not found."""
    def __init__(self, project_id: Optional[int] = None):
        detail = f"Project {project_id} not found" if project_id else "Project not found"
        super().__init__(resource="Project")
        self.detail = detail


class UserNotFound(NotFound):
    """Raised when user is not found."""
    def __init__(self, user_id: Optional[int] = None):
        detail = f"User {user_id} not found" if user_id else "User not found"
        super().__init__(resource="User")
        self.detail = detail


class DependencyError(BaseAPIException):
    """Raised when there's a dependency conflict."""
    def __init__(self, detail: str = "Dependency conflict"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class CircularDependencyError(DependencyError):
    """Raised when circular dependency is detected."""
    def __init__(self):
        super().__init__(detail="Circular dependency detected")


class InvalidTransition(BaseAPIException):
    """Raised when status transition is invalid."""
    def __init__(self, from_status: str, to_status: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from '{from_status}' to '{to_status}'"
        )


class RateLimitExceeded(BaseAPIException):
    """Raised when rate limit is exceeded."""
    def __init__(self, retry_after: Optional[int] = None):
        headers = {"Retry-After": str(retry_after)} if retry_after else None
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers=headers
        )


class DatabaseError(BaseAPIException):
    """Raised when database operation fails."""
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class TokenExpired(AuthenticationError):
    """Raised when token has expired."""
    def __init__(self):
        super().__init__("Token has expired")


class InvalidToken(AuthenticationError):
    """Raised when token is invalid."""
    def __init__(self):
        super().__init__("Invalid token")


class OrganizationNotFound(NotFound):
    """Raised when organization is not found."""
    def __init__(self, org_id: Optional[int] = None):
        detail = f"Organization {org_id} not found" if org_id else "Organization not found"
        super().__init__(resource="Organization")
        self.detail = detail


class DuplicateError(BaseAPIException):
    """Raised when trying to create duplicate resource."""
    def __init__(self, resource: str = "Resource", field: Optional[str] = None):
        detail = f"{resource} already exists"
        if field:
            detail += f" with this {field}"
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )