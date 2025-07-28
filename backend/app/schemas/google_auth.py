"""Google OAuth2.0 authentication schemas."""

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class GoogleAuthConfig(BaseModel):
    """Google OAuth2.0 configuration."""

    client_id: str = Field(..., description="Google OAuth2 client ID")
    client_secret: str = Field(..., description="Google OAuth2 client secret")
    redirect_uri: HttpUrl = Field(..., description="OAuth2 redirect URI")
    scopes: list[str] = Field(
        default=[
            "openid",
            "email",
            "profile",
        ],
        description="OAuth2 scopes",
    )


class GoogleLoginRequest(BaseModel):
    """Google login request with authorization code."""

    code: str = Field(..., description="Google OAuth2 authorization code")
    state: str | None = Field(
        None, description="OAuth2 state parameter for CSRF protection"
    )
    device_id: str | None = Field(None, description="Device identifier")
    device_name: str | None = Field(None, description="Device name")


class GoogleTokenResponse(BaseModel):
    """Google OAuth2 token response."""

    access_token: str
    expires_in: int
    refresh_token: str | None = None
    scope: str
    token_type: str
    id_token: str


class GoogleUserInfo(BaseModel):
    """Google user profile information."""

    id: str = Field(..., description="Google user ID")
    email: EmailStr = Field(..., description="User email")
    verified_email: bool = Field(..., description="Email verification status")
    name: str = Field(..., description="User full name")
    given_name: str | None = Field(None, description="First name")
    family_name: str | None = Field(None, description="Last name")
    picture: str | None = Field(None, description="Profile picture URL")
    locale: str | None = Field(None, description="User locale")
    hd: str | None = Field(None, description="Hosted domain (for Google Workspace)")


class GoogleLinkRequest(BaseModel):
    """Request to link Google account to existing user."""

    google_id: str = Field(..., description="Google user ID")
    email: EmailStr = Field(..., description="Email to verify match")


class GoogleUnlinkRequest(BaseModel):
    """Request to unlink Google account from user."""

    confirm: bool = Field(..., description="Confirmation to unlink")
