"""Google OAuth2.0 authentication service."""

import secrets
from typing import Optional

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BusinessLogicError
from app.models.user import User
from app.schemas.google_auth import GoogleUserInfo
from app.services.session_service import SessionService


class GoogleAuthService:
    """Service for Google OAuth2.0 authentication."""

    def __init__(self, db: Session):
        """Initialize Google auth service."""
        self.db = db
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        
    def get_authorization_url(self, state: Optional[str] = None) -> tuple[str, str]:
        """
        Get Google OAuth2 authorization URL.
        
        Returns:
            Tuple of (authorization_url, state)
        """
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=[
                "openid",
                "email", 
                "profile",
            ],
        )
        flow.redirect_uri = self.redirect_uri
        
        # Generate state for CSRF protection
        if not state:
            state = secrets.token_urlsafe(32)
        
        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            state=state,
            prompt="select_account",
        )
        
        return authorization_url, state

    def exchange_code_for_tokens(self, code: str) -> dict:
        """
        Exchange authorization code for tokens.
        
        Args:
            code: Authorization code from Google
            
        Returns:
            Token data including id_token
        """
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=[
                "openid",
                "email",
                "profile",
            ],
        )
        flow.redirect_uri = self.redirect_uri
        
        # Exchange code for tokens
        flow.fetch_token(code=code)
        
        return {
            "access_token": flow.credentials.token,
            "refresh_token": flow.credentials.refresh_token,
            "id_token": flow.credentials.id_token,
            "expires_at": flow.credentials.expiry.isoformat() if flow.credentials.expiry else None,
        }

    def verify_id_token(self, id_token_str: str) -> GoogleUserInfo:
        """
        Verify Google ID token and extract user info.
        
        Args:
            id_token_str: ID token from Google
            
        Returns:
            Google user information
            
        Raises:
            BusinessLogicError: If token is invalid
        """
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                id_token_str,
                google_requests.Request(),
                self.client_id,
            )
            
            # Check issuer
            if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
                raise ValueError("Invalid issuer")
            
            # Extract user info
            return GoogleUserInfo(
                id=idinfo["sub"],
                email=idinfo["email"],
                verified_email=idinfo.get("email_verified", False),
                name=idinfo.get("name", ""),
                given_name=idinfo.get("given_name"),
                family_name=idinfo.get("family_name"),
                picture=idinfo.get("picture"),
                locale=idinfo.get("locale"),
                hd=idinfo.get("hd"),
            )
            
        except Exception as e:
            raise BusinessLogicError(f"Googleトークンの検証に失敗しました: {str(e)}")

    def authenticate_or_create_user(
        self,
        google_info: GoogleUserInfo,
        ip_address: str,
        user_agent: str,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
    ) -> tuple[User, bool]:
        """
        Authenticate existing user or create new user from Google info.
        
        Args:
            google_info: Google user information
            ip_address: Client IP address
            user_agent: Client user agent
            device_id: Optional device ID
            device_name: Optional device name
            
        Returns:
            Tuple of (user, is_new_user)
        """
        # Check if user exists by Google ID
        user = self.db.query(User).filter(User.google_id == google_info.id).first()
        
        if user:
            # Existing user with Google account
            if not user.is_active:
                raise BusinessLogicError("アカウントが無効化されています")
            
            # Update last login
            user.record_successful_login(self.db)
            
            # Log activity
            user.log_activity(
                self.db,
                action="google_login",
                details={"google_id": google_info.id},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            
            self.db.commit()
            return user, False
        
        # Check if user exists by email
        user = self.db.query(User).filter(User.email == google_info.email).first()
        
        if user:
            # User exists but Google account not linked
            if not google_info.verified_email:
                raise BusinessLogicError("Googleアカウントのメールアドレスが確認されていません")
            
            # Link Google account
            user.google_id = google_info.id
            user.record_successful_login(self.db)
            
            # Log activity
            user.log_activity(
                self.db,
                action="google_account_linked",
                details={"google_id": google_info.id},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            
            self.db.commit()
            return user, False
        
        # Create new user
        if not google_info.verified_email:
            raise BusinessLogicError("Googleアカウントのメールアドレスが確認されていません")
        
        # Create user with Google info
        user = User.create(
            db=self.db,
            email=google_info.email,
            password=secrets.token_urlsafe(32),  # Random password for Google users
            full_name=google_info.name,
            is_active=True,
        )
        
        # Set Google-specific fields
        user.google_id = google_info.id
        user.profile_image_url = google_info.picture
        user.email_verified = True
        user.record_successful_login(self.db)
        
        # Log activity
        user.log_activity(
            self.db,
            action="google_signup",
            details={"google_id": google_info.id},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        self.db.commit()
        return user, True

    def link_google_account(
        self,
        user: User,
        google_info: GoogleUserInfo,
    ) -> None:
        """
        Link Google account to existing user.
        
        Args:
            user: User to link account to
            google_info: Google user information
            
        Raises:
            BusinessLogicError: If linking fails
        """
        # Check if Google ID is already linked to another user
        existing = self.db.query(User).filter(
            User.google_id == google_info.id,
            User.id != user.id,
        ).first()
        
        if existing:
            raise BusinessLogicError("このGoogleアカウントは既に別のユーザーにリンクされています")
        
        # Verify email matches
        if user.email != google_info.email:
            raise BusinessLogicError("Googleアカウントのメールアドレスが一致しません")
        
        # Link account
        user.google_id = google_info.id
        
        # Update profile if not set
        if not user.profile_image_url and google_info.picture:
            user.profile_image_url = google_info.picture
        
        # Log activity
        user.log_activity(
            self.db,
            action="google_account_linked",
            details={"google_id": google_info.id},
        )
        
        self.db.commit()

    def unlink_google_account(self, user: User) -> None:
        """
        Unlink Google account from user.
        
        Args:
            user: User to unlink account from
            
        Raises:
            BusinessLogicError: If unlinking fails
        """
        if not user.google_id:
            raise BusinessLogicError("Googleアカウントがリンクされていません")
        
        # Check if user has a password set
        if not user.has_password_set():
            raise BusinessLogicError(
                "パスワードが設定されていません。"
                "Googleアカウントのリンクを解除する前にパスワードを設定してください"
            )
        
        # Unlink account
        google_id = user.google_id
        user.google_id = None
        user.google_refresh_token = None
        
        # Log activity
        user.log_activity(
            self.db,
            action="google_account_unlinked",
            details={"google_id": google_id},
        )
        
        self.db.commit()

    def refresh_google_token(self, user: User) -> Optional[str]:
        """
        Refresh Google access token using refresh token.
        
        Args:
            user: User with Google refresh token
            
        Returns:
            New access token or None if refresh fails
        """
        if not user.google_refresh_token:
            return None
        
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                },
                scopes=[
                    "openid",
                    "email",
                    "profile",
                ],
            )
            
            # Use refresh token to get new access token
            flow.credentials.refresh_token = user.google_refresh_token
            flow.credentials.refresh(google_requests.Request())
            
            # Update refresh token if provided
            if flow.credentials.refresh_token:
                user.google_refresh_token = flow.credentials.refresh_token
                self.db.commit()
            
            return flow.credentials.token
            
        except Exception:
            # Refresh failed, invalidate refresh token
            user.google_refresh_token = None
            self.db.commit()
            return None