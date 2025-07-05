"""
Role-Based Access Control (RBAC) utilities.
"""

from typing import List, Optional
from functools import wraps

from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError

from app.core.config import get_settings
from app.core.dependencies import get_current_active_user
from app.models.user import User


class RoleChecker:
    """
    Dependency class for checking user roles.
    
    Usage:
        @router.get("/admin", dependencies=[Depends(RoleChecker(["admin"]))])
        def admin_endpoint():
            ...
    """
    
    def __init__(self, allowed_roles: List[str]) -> None:
        """
        Initialize role checker.
        
        Args:
            allowed_roles: List of roles that are allowed to access the resource
        """
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        """
        Check if current user has required role.
        
        Args:
            current_user: Current authenticated user
            
        Returns:
            The current user if they have the required role
            
        Raises:
            HTTPException: If user doesn't have required role
        """
        # Extract roles from JWT token
        token_roles = getattr(current_user, "_token_roles", [])
        
        # Check if user is superuser (has all permissions)
        if current_user.is_superuser:
            return current_user
        
        # Check if user has any of the required roles
        if not any(role in self.allowed_roles for role in token_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
                headers={"X-Error-Code": "INSUFFICIENT_PERMISSIONS"},
            )
        
        return current_user


def require_roles(allowed_roles: List[str]) -> RoleChecker:
    """
    Convenience function to create a RoleChecker dependency.
    
    Args:
        allowed_roles: List of roles that are allowed
        
    Returns:
        RoleChecker instance
    """
    return RoleChecker(allowed_roles)


def extract_roles_from_token(token: str) -> List[str]:
    """
    Extract roles from JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        List of roles
    """
    settings = get_settings()
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload.get("roles", [])
    except JWTError:
        return []


# Pre-defined role checkers for common use cases
require_admin = RoleChecker(["admin"])
require_manager = RoleChecker(["admin", "manager"])
require_user = RoleChecker(["admin", "manager", "user"])