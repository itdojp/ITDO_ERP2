"""
Keycloak integration module.

Provides OAuth2/OpenID Connect authentication via Keycloak.
"""

import secrets
import hashlib
import base64
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlencode
import logging

from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakError

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class InvalidTokenError(Exception):
    """Raised when a token is invalid or expired."""
    pass


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


def generate_pkce_pair() -> Tuple[str, str]:
    """
    Generate PKCE (Proof Key for Code Exchange) verifier and challenge.
    
    Returns:
        Tuple of (verifier, challenge)
    """
    # Generate cryptographically secure random verifier
    # Length between 43-128 characters as per RFC 7636
    verifier_bytes = secrets.token_bytes(64)
    verifier = base64.urlsafe_b64encode(verifier_bytes).decode('utf-8').rstrip('=')
    
    # Generate challenge as SHA256 hash of verifier
    challenge_bytes = hashlib.sha256(verifier.encode('utf-8')).digest()
    challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')
    
    return verifier, challenge


def verify_pkce_pair(verifier: str, challenge: str) -> bool:
    """
    Verify that a PKCE verifier matches the challenge.
    
    Args:
        verifier: The PKCE verifier
        challenge: The PKCE challenge
        
    Returns:
        True if the verifier matches the challenge
    """
    # Compute expected challenge from verifier
    expected_challenge_bytes = hashlib.sha256(verifier.encode('utf-8')).digest()
    expected_challenge = base64.urlsafe_b64encode(expected_challenge_bytes).decode('utf-8').rstrip('=')
    
    return challenge == expected_challenge


def is_base64url(s: str) -> bool:
    """
    Check if a string is valid base64url encoding.
    
    Args:
        s: String to check
        
    Returns:
        True if valid base64url
    """
    if not s:
        return True
    
    # Base64url alphabet
    valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_')
    return all(c in valid_chars for c in s)


def validate_redirect_uri(uri: str, allowed_uris: list[str]) -> bool:
    """
    Validate a redirect URI against a whitelist.
    
    Args:
        uri: The redirect URI to validate
        allowed_uris: List of allowed URIs
        
    Returns:
        True if the URI is allowed
    """
    return uri in allowed_uris


def is_safe_url(url: str, allowed_hosts: Optional[list[str]] = None) -> bool:
    """
    Check if a URL is safe for redirection.
    
    Args:
        url: The URL to check
        allowed_hosts: Optional list of allowed hosts
        
    Returns:
        True if the URL is safe
    """
    if not url:
        return False
    
    # Reject URLs with dangerous schemes
    dangerous_schemes = ['javascript:', 'data:', 'vbscript:', 'file:']
    for scheme in dangerous_schemes:
        if url.lower().startswith(scheme):
            return False
    
    # Reject protocol-relative URLs
    if url.startswith('//'):
        return False
    
    # If allowed_hosts is specified, validate the host
    if allowed_hosts and not url.startswith('/'):
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.hostname and parsed.hostname not in allowed_hosts:
            return False
    
    return True


class KeycloakClient:
    """Client for interacting with Keycloak server."""
    
    def __init__(self, settings: Settings) -> None:
        """
        Initialize Keycloak client.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.server_url = settings.KEYCLOAK_SERVER_URL
        self.realm_name = settings.KEYCLOAK_REALM
        self.client_id = settings.KEYCLOAK_CLIENT_ID
        self.client_secret = settings.KEYCLOAK_CLIENT_SECRET
        
        # Initialize Keycloak OpenID client
        self.keycloak_openid = KeycloakOpenID(
            server_url=self.server_url,
            client_id=self.client_id,
            realm_name=self.realm_name,
            client_secret_key=self.client_secret,
        )
    
    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        """
        Generate Keycloak authorization URL.
        
        Args:
            redirect_uri: URI to redirect after authentication
            state: CSRF protection state parameter
            
        Returns:
            Authorization URL
        """
        auth_url = f"{self.server_url}/auth/realms/{self.realm_name}/protocol/openid-connect/auth"
        
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "openid email profile",
        }
        
        return f"{auth_url}?{urlencode(params)}"
    
    def get_auth_url_with_pkce(self, redirect_uri: str, state: str) -> Tuple[str, str]:
        """
        Generate Keycloak authorization URL with PKCE.
        
        Args:
            redirect_uri: URI to redirect after authentication
            state: CSRF protection state parameter
            
        Returns:
            Tuple of (authorization URL, PKCE verifier)
        """
        verifier, challenge = generate_pkce_pair()
        
        auth_url = f"{self.server_url}/auth/realms/{self.realm_name}/protocol/openid-connect/auth"
        
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "openid email profile",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
        
        return f"{auth_url}?{urlencode(params)}", verifier
    
    def exchange_code(
        self,
        code: str,
        redirect_uri: str,
        code_verifier: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens.
        
        Args:
            code: Authorization code
            redirect_uri: Redirect URI used in authorization
            code_verifier: Optional PKCE verifier
            
        Returns:
            Token response containing access_token, refresh_token, etc.
            
        Raises:
            AuthenticationError: If code exchange fails
        """
        try:
            params = {
                "code": code,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }
            
            if code_verifier:
                params["code_verifier"] = code_verifier
            
            return self.keycloak_openid.token(**params)
        except KeycloakError as e:
            logger.error(f"Token exchange failed: {e}")
            raise AuthenticationError(f"Token exchange failed: {str(e)}")
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and introspect a Keycloak token.
        
        Args:
            token: Access token to verify
            
        Returns:
            Token introspection result with user info
            
        Raises:
            InvalidTokenError: If token is invalid or inactive
        """
        try:
            # Introspect token
            token_info = self.keycloak_openid.introspect(token)
            
            if not token_info.get("active"):
                raise InvalidTokenError("Token is not active")
            
            # Get full user info
            userinfo = self.keycloak_openid.userinfo(token)
            
            return userinfo
        except KeycloakError as e:
            logger.error(f"Token verification failed: {e}")
            raise InvalidTokenError(f"Token verification failed: {str(e)}")
    
    def get_userinfo(self, token: str) -> Dict[str, Any]:
        """
        Get user information from Keycloak.
        
        Args:
            token: Access token
            
        Returns:
            User information including roles and groups
        """
        try:
            userinfo = self.keycloak_openid.userinfo(token)
            
            # Extract roles from realm_access if available
            if "realm_access" in userinfo and "roles" in userinfo["realm_access"]:
                userinfo["roles"] = userinfo["realm_access"]["roles"]
            else:
                userinfo["roles"] = []
            
            return userinfo
        except KeycloakError as e:
            logger.error(f"Failed to get user info: {e}")
            raise AuthenticationError(f"Failed to get user info: {str(e)}")
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New token response
            
        Raises:
            AuthenticationError: If refresh fails
        """
        try:
            return self.keycloak_openid.refresh_token(refresh_token)
        except KeycloakError as e:
            logger.error(f"Token refresh failed: {e}")
            raise AuthenticationError(f"Token refresh failed: {str(e)}")
    
    def logout(self, refresh_token: str) -> None:
        """
        Logout user from Keycloak.
        
        Args:
            refresh_token: Refresh token to revoke
        """
        try:
            self.keycloak_openid.logout(refresh_token)
        except KeycloakError as e:
            logger.error(f"Logout failed: {e}")
            # Don't raise error on logout failure


# Singleton instance
_keycloak_client: Optional[KeycloakClient] = None


def get_keycloak_client() -> KeycloakClient:
    """
    Get or create Keycloak client instance.
    
    Returns:
        Keycloak client instance
    """
    global _keycloak_client
    
    if _keycloak_client is None:
        settings = get_settings()
        _keycloak_client = KeycloakClient(settings)
    
    return _keycloak_client