"""
Keycloak-related schemas.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class KeycloakUserInfo(BaseModel):
    """Keycloak user information schema."""
    sub: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    name: str = Field(..., description="User full name")
    preferred_username: Optional[str] = Field(None, description="Preferred username")
    given_name: Optional[str] = Field(None, description="Given name")
    family_name: Optional[str] = Field(None, description="Family name")
    email_verified: bool = Field(False, description="Email verification status")
    roles: List[str] = Field(default_factory=list, description="User roles")
    groups: List[str] = Field(default_factory=list, description="User groups")
    realm_access: Optional[Dict[str, Any]] = Field(None, description="Realm access info")


class KeycloakTokenResponse(BaseModel):
    """Keycloak token response schema."""
    access_token: str = Field(..., description="Access token")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    token_type: str = Field("Bearer", description="Token type")
    id_token: Optional[str] = Field(None, description="OpenID Connect ID token")
    scope: Optional[str] = Field(None, description="Token scope")


class KeycloakError(BaseModel):
    """Keycloak error response schema."""
    error: str = Field(..., description="Error code")
    error_description: Optional[str] = Field(None, description="Error description")