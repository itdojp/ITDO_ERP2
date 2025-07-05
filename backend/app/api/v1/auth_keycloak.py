"""
Keycloak authentication endpoints.

Provides OAuth2/OpenID Connect authentication via Keycloak.
"""

import secrets
import logging
from typing import Optional, Dict, Any
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.database import get_db
from app.core.keycloak import get_keycloak_client, InvalidTokenError, AuthenticationError
from app.core.security import create_access_token
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import TokenResponse

logger = logging.getLogger(__name__)
router = APIRouter()


class KeycloakCallbackRequest(BaseModel):
    """Request model for Keycloak callback."""
    code: str
    state: str


class KeycloakRefreshRequest(BaseModel):
    """Request model for token refresh."""
    refresh_token: str


class KeycloakLogoutRequest(BaseModel):
    """Request model for logout."""
    refresh_token: str


# In-memory state storage (should use Redis in production)
_state_store: Dict[str, Dict[str, Any]] = {}


def generate_state() -> str:
    """Generate secure state parameter for CSRF protection."""
    return secrets.token_urlsafe(32)


def store_state(state: str, data: Dict[str, Any]) -> None:
    """Store state data temporarily."""
    _state_store[state] = data


def verify_state(state: str) -> Optional[Dict[str, Any]]:
    """Verify and retrieve state data."""
    return _state_store.pop(state, None)


@router.get("/login")
async def keycloak_login(
    request: Request,
    redirect_uri: Optional[str] = None,
) -> RedirectResponse:
    """
    Initiate Keycloak OAuth2 authentication flow.
    
    Args:
        request: FastAPI request object
        redirect_uri: Optional custom redirect URI after auth
        
    Returns:
        Redirect to Keycloak authorization URL
    """
    settings = get_settings()
    keycloak_client = get_keycloak_client()
    
    try:
        # Generate state for CSRF protection
        state = generate_state()
        
        # Store state data
        state_data = {
            "redirect_uri": redirect_uri or "/",
            "timestamp": secrets.randbits(32),
        }
        store_state(state, state_data)
        
        # Generate authorization URL
        auth_url = keycloak_client.get_auth_url(
            redirect_uri=settings.KEYCLOAK_CALLBACK_URL,
            state=state,
        )
        
        return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)
    
    except Exception as e:
        logger.error(f"Failed to initiate Keycloak login: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Keycloak service is temporarily unavailable",
            headers={"X-Error-Code": "KEYCLOAK_UNAVAILABLE"},
        )


@router.post("/callback", response_model=TokenResponse)
async def keycloak_callback(
    request: KeycloakCallbackRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Handle Keycloak OAuth2 callback.
    
    Args:
        request: Callback request with code and state
        db: Database session
        
    Returns:
        JWT tokens for the authenticated user
    """
    settings = get_settings()
    keycloak_client = get_keycloak_client()
    
    # Verify state parameter
    state_data = verify_state(request.state)
    if not state_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter",
            headers={"X-Error-Code": "INVALID_STATE"},
        )
    
    try:
        # Exchange authorization code for tokens
        token_response = keycloak_client.exchange_code(
            code=request.code,
            redirect_uri=settings.KEYCLOAK_CALLBACK_URL,
        )
        
        # Get user info from Keycloak
        userinfo = keycloak_client.get_userinfo(token_response["access_token"])
        
        # Find or create user in local database
        user = db.query(User).filter(User.email == userinfo["email"]).first()
        
        if not user:
            # Create new user from Keycloak info
            user = User(
                email=userinfo["email"],
                full_name=userinfo.get("name", userinfo["email"]),
                is_active=True,
                is_superuser="admin" in userinfo.get("roles", []),
                hashed_password="keycloak",  # Placeholder for Keycloak users
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Create JWT token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "roles": userinfo.get("roles", []),
            },
            expires_delta=access_token_expires,
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=token_response.get("refresh_token"),
        )
    
    except AuthenticationError as e:
        logger.error(f"Keycloak authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"X-Error-Code": "AUTH_FAILED"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during Keycloak callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed",
        )


@router.get("/userinfo")
async def keycloak_userinfo(
    current_user: User = Depends(get_current_user),
    token: str = Depends(lambda: None),  # We'll get this from the auth header
) -> Dict[str, Any]:
    """
    Get user information from Keycloak.
    
    Args:
        current_user: Current authenticated user
        token: Bearer token from header
        
    Returns:
        User information including roles and groups
    """
    keycloak_client = get_keycloak_client()
    
    try:
        # In a real implementation, we'd extract the Keycloak token
        # For now, return user info from database
        return {
            "sub": str(current_user.id),
            "email": current_user.email,
            "name": current_user.full_name,
            "roles": ["user"],  # Would come from Keycloak
            "groups": [],  # Would come from Keycloak
        }
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information",
        )


@router.post("/refresh", response_model=TokenResponse)
async def keycloak_refresh(
    request: KeycloakRefreshRequest,
) -> TokenResponse:
    """
    Refresh access token using refresh token.
    
    Args:
        request: Refresh token request
        
    Returns:
        New JWT tokens
    """
    settings = get_settings()
    keycloak_client = get_keycloak_client()
    
    try:
        # Refresh token with Keycloak
        token_response = keycloak_client.refresh_token(request.refresh_token)
        
        # Get updated user info
        userinfo = keycloak_client.get_userinfo(token_response["access_token"])
        
        # Create new JWT token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": userinfo["sub"],
                "email": userinfo["email"],
                "roles": userinfo.get("roles", []),
            },
            expires_delta=access_token_expires,
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=token_response.get("refresh_token"),
        )
    
    except AuthenticationError as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.post("/logout")
async def keycloak_logout(
    request: KeycloakLogoutRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """
    Logout user from Keycloak.
    
    Args:
        request: Logout request with refresh token
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    keycloak_client = get_keycloak_client()
    
    try:
        # Logout from Keycloak
        keycloak_client.logout(request.refresh_token)
        
        return {"message": "Logged out successfully"}
    
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        # Don't fail on logout errors
        return {"message": "Logged out successfully"}