"""Production-Grade Mobile SDK Core Architecture - CC02 v72.0 Day 17."""

from __future__ import annotations

import asyncio
import hashlib
import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar
from urllib.parse import urljoin

import aiohttp
from cryptography.fernet import Fernet
from pydantic import BaseModel, Field


# SDK Configuration and Constants
class SDKConfig(BaseModel):
    """SDK configuration settings."""

    api_base_url: str = Field(..., description="Base API URL")
    api_version: str = Field(default="v1", description="API version")
    organization_id: str = Field(..., description="Organization ID")
    app_id: str = Field(..., description="Application ID")
    api_key: str = Field(..., description="API key")

    # Connection settings
    timeout_seconds: int = Field(default=30, description="Request timeout")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay_seconds: float = Field(default=1.0, description="Retry delay")

    # Cache settings
    cache_enabled: bool = Field(default=True, description="Enable response caching")
    cache_ttl_seconds: int = Field(default=300, description="Cache TTL")

    # Security settings
    encryption_enabled: bool = Field(
        default=True, description="Enable payload encryption"
    )
    certificate_pinning: bool = Field(
        default=True, description="Enable certificate pinning"
    )

    # Logging settings
    log_level: str = Field(default="INFO", description="Log level")
    log_requests: bool = Field(default=False, description="Log API requests")
    log_responses: bool = Field(default=False, description="Log API responses")


class SDKError(Exception):
    """Base SDK exception."""

    def __init__(
        self,
        message: str,
        error_code: str = "SDK_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now()


class AuthenticationError(SDKError):
    """Authentication related errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> dict:
        super().__init__(message, "AUTH_ERROR", details)


class NetworkError(SDKError):
    """Network related errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> dict:
        super().__init__(message, "NETWORK_ERROR", details)


class ValidationError(SDKError):
    """Validation related errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> dict:
        super().__init__(message, "VALIDATION_ERROR", details)


class RateLimitError(SDKError):
    """Rate limiting errors."""

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "RATE_LIMIT_ERROR", details)
        self.retry_after = retry_after


# Authentication and Session Management
class AuthenticationState(str, Enum):
    """Authentication states."""

    UNAUTHENTICATED = "unauthenticated"
    AUTHENTICATING = "authenticating"
    AUTHENTICATED = "authenticated"
    REFRESHING = "refreshing"
    EXPIRED = "expired"
    INVALID = "invalid"


class AuthToken(BaseModel):
    """Authentication token."""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_at: datetime
    scope: List[str] = Field(default_factory=list)


class DeviceInfo(BaseModel):
    """Device information."""

    device_id: str
    platform: str  # ios, android, web
    os_version: str
    app_version: str
    device_model: str
    screen_resolution: str
    timezone: str
    locale: str


T = TypeVar("T")


class AsyncCache:
    """Simple async cache implementation."""

    def __init__(self, default_ttl: int = 300) -> dict:
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}

    async def get(self, key: str) -> Optional[Any]:
        """Get cached value."""
        if key in self._cache:
            entry = self._cache[key]
            if datetime.now() < entry["expires_at"]:
                return entry["value"]
            else:
                del self._cache[key]
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cached value."""
        ttl = ttl or self.default_ttl
        self._cache[key] = {
            "value": value,
            "expires_at": datetime.now() + timedelta(seconds=ttl),
        }

    async def delete(self, key: str) -> None:
        """Delete cached value."""
        self._cache.pop(key, None)

    async def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()


class RequestInterceptor(ABC):
    """Base class for request interceptors."""

    @abstractmethod
    async def before_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Called before making a request."""
        pass

    @abstractmethod
    async def after_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Called after receiving a response."""
        pass

    @abstractmethod
    async def on_error(self, error: Exception) -> Optional[Exception]:
        """Called when an error occurs. Return None to suppress the error."""
        pass


class LoggingInterceptor(RequestInterceptor):
    """Logging interceptor."""

    def __init__(self, config: SDKConfig) -> dict:
        self.config = config

    async def before_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log request details."""
        if self.config.log_requests:
            print(f"[SDK] Request: {request_data['method']} {request_data['url']}")
            if request_data.get("data"):
                print(
                    f"[SDK] Request Body: {json.dumps(request_data['data'], indent=2)}"
                )
        return request_data

    async def after_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log response details."""
        if self.config.log_responses:
            print(
                f"[SDK] Response: {response_data['status']} {response_data.get('url', '')}"
            )
            if response_data.get("data"):
                print(
                    f"[SDK] Response Body: {json.dumps(response_data['data'], indent=2)}"
                )
        return response_data

    async def on_error(self, error: Exception) -> Optional[Exception]:
        """Log error details."""
        print(f"[SDK] Error: {type(error).__name__}: {str(error)}")
        return error


class AuthenticationInterceptor(RequestInterceptor):
    """Authentication interceptor."""

    def __init__(self, auth_manager: "AuthManager") -> dict:
        self.auth_manager = auth_manager

    async def before_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add authentication headers."""
        if self.auth_manager.is_authenticated():
            token = await self.auth_manager.get_valid_token()
            if token:
                headers = request_data.setdefault("headers", {})
                headers["Authorization"] = f"{token.token_type} {token.access_token}"
        return request_data

    async def after_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle authentication in response."""
        if response_data["status"] == 401:
            await self.auth_manager.handle_authentication_error()
        return response_data

    async def on_error(self, error: Exception) -> Optional[Exception]:
        """Handle authentication errors."""
        if isinstance(error, AuthenticationError):
            await self.auth_manager.handle_authentication_error()
        return error


class HTTPClient:
    """Advanced HTTP client with retry, caching, and interceptors."""

    def __init__(self, config: SDKConfig) -> dict:
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache = AsyncCache(config.cache_ttl_seconds)
        self.interceptors: List[RequestInterceptor] = []
        self.encryption_key = (
            Fernet.generate_key() if config.encryption_enabled else None
        )
        self.cipher_suite = Fernet(self.encryption_key) if self.encryption_key else None

    def add_interceptor(self, interceptor: RequestInterceptor) -> None:
        """Add request interceptor."""
        self.interceptors.append(interceptor)

    async def __aenter__(self) -> dict:
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> dict:
        """Async context manager exit."""
        await self.close()

    async def _ensure_session(self) -> None:
        """Ensure HTTP session is created."""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(
                ssl=self.config.certificate_pinning,
                limit=100,
                limit_per_host=20,
            )

            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)

            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "User-Agent": f"ITDO-ERP-SDK/1.0 ({self.config.app_id})",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )

    async def close(self) -> None:
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()

    def _get_cache_key(
        self, method: str, url: str, params: Optional[Dict] = None
    ) -> str:
        """Generate cache key for request."""
        key_data = f"{method}:{url}"
        if params:
            key_data += f":{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _encrypt_payload(self, data: Any) -> str:
        """Encrypt request payload."""
        if not self.cipher_suite:
            return data

        json_data = json.dumps(data) if not isinstance(data, str) else data
        encrypted_data = self.cipher_suite.encrypt(json_data.encode())
        return encrypted_data.decode()

    def _decrypt_payload(self, encrypted_data: str) -> Any:
        """Decrypt response payload."""
        if not self.cipher_suite:
            return encrypted_data

        try:
            decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
            return json.loads(decrypted_data.decode())
        except Exception:
            return encrypted_data

    async def _make_request_with_retry(
        self, method: str, url: str, **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic."""
        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            try:
                await self._ensure_session()

                # Apply request interceptors
                request_data = {"method": method, "url": url, **kwargs}

                for interceptor in self.interceptors:
                    request_data = await interceptor.before_request(request_data)

                # Extract updated values
                method = request_data["method"]
                url = request_data["url"]
                request_kwargs = {
                    k: v for k, v in request_data.items() if k not in ["method", "url"]
                }

                # Make the request
                async with self.session.request(
                    method, url, **request_kwargs
                ) as response:
                    response_data = {
                        "status": response.status,
                        "headers": dict(response.headers),
                        "url": str(response.url),
                    }

                    # Handle response content
                    if response.content_type == "application/json":
                        response_data["data"] = await response.json()
                    else:
                        response_data["data"] = await response.text()

                    # Apply response interceptors
                    for interceptor in self.interceptors:
                        response_data = await interceptor.after_response(response_data)

                    # Handle HTTP errors
                    if response.status >= 400:
                        if response.status == 401:
                            raise AuthenticationError("Authentication failed")
                        elif response.status == 429:
                            retry_after = int(response.headers.get("Retry-After", 60))
                            raise RateLimitError("Rate limit exceeded", retry_after)
                        elif response.status >= 500:
                            raise NetworkError(f"Server error: {response.status}")
                        else:
                            error_data = response_data.get("data", {})
                            error_message = error_data.get(
                                "message", f"HTTP {response.status}"
                            )
                            raise SDKError(error_message, f"HTTP_{response.status}")

                    return response_data

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = NetworkError(f"Network error: {str(e)}")

                # Apply error interceptors
                for interceptor in self.interceptors:
                    handled_error = await interceptor.on_error(last_exception)
                    if handled_error is None:
                        return {}  # Error was handled/suppressed
                    last_exception = handled_error

                if attempt < self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay_seconds * (2**attempt))
                    continue

            except Exception as e:
                last_exception = e

                # Apply error interceptors
                for interceptor in self.interceptors:
                    handled_error = await interceptor.on_error(last_exception)
                    if handled_error is None:
                        return {}  # Error was handled/suppressed
                    last_exception = handled_error

                break

        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        else:
            raise NetworkError("Request failed after all retries")

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make GET request."""
        url = urljoin(
            self.config.api_base_url, f"api/{self.config.api_version}/{endpoint}"
        )

        # Check cache for GET requests
        cache_key = None
        if use_cache and self.config.cache_enabled:
            cache_key = self._get_cache_key("GET", url, params)
            cached_response = await self.cache.get(cache_key)
            if cached_response:
                return cached_response

        response = await self._make_request_with_retry(
            "GET", url, params=params, **kwargs
        )

        # Cache successful GET responses
        if (
            use_cache
            and self.config.cache_enabled
            and cache_key
            and response["status"] == 200
        ):
            await self.cache.set(cache_key, response)

        return response

    async def post(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Dict[str, Any]:
        """Make POST request."""
        url = urljoin(
            self.config.api_base_url, f"api/{self.config.api_version}/{endpoint}"
        )

        if data and self.config.encryption_enabled:
            data = self._encrypt_payload(data)

        return await self._make_request_with_retry("POST", url, json=data, **kwargs)

    async def put(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Dict[str, Any]:
        """Make PUT request."""
        url = urljoin(
            self.config.api_base_url, f"api/{self.config.api_version}/{endpoint}"
        )

        if data and self.config.encryption_enabled:
            data = self._encrypt_payload(data)

        return await self._make_request_with_retry("PUT", url, json=data, **kwargs)

    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make DELETE request."""
        url = urljoin(
            self.config.api_base_url, f"api/{self.config.api_version}/{endpoint}"
        )
        return await self._make_request_with_retry("DELETE", url, **kwargs)


class AuthManager:
    """Authentication manager."""

    def __init__(self, config: SDKConfig, http_client: HTTPClient) -> dict:
        self.config = config
        self.http_client = http_client
        self.current_token: Optional[AuthToken] = None
        self.state = AuthenticationState.UNAUTHENTICATED
        self.device_info: Optional[DeviceInfo] = None
        self._auth_lock = asyncio.Lock()
        self._token_refresh_task: Optional[asyncio.Task] = None

    def set_device_info(self, device_info: DeviceInfo) -> None:
        """Set device information."""
        self.device_info = device_info

    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return (
            self.state == AuthenticationState.AUTHENTICATED
            and self.current_token is not None
            and self.current_token.expires_at > datetime.now()
        )

    async def authenticate_with_credentials(
        self,
        username: str,
        password: str,
        additional_factors: Optional[Dict[str, str]] = None,
    ) -> AuthToken:
        """Authenticate with username/password."""
        async with self._auth_lock:
            self.state = AuthenticationState.AUTHENTICATING

            try:
                auth_data = {
                    "grant_type": "password",
                    "username": username,
                    "password": password,
                    "organization_id": self.config.organization_id,
                    "app_id": self.config.app_id,
                }

                if self.device_info:
                    auth_data["device_info"] = self.device_info.dict()

                if additional_factors:
                    auth_data["additional_factors"] = additional_factors

                response = await self.http_client.post("auth/token", auth_data)

                if response["status"] != 200:
                    raise AuthenticationError("Authentication failed")

                token_data = response["data"]
                self.current_token = AuthToken(
                    access_token=token_data["access_token"],
                    refresh_token=token_data.get("refresh_token"),
                    token_type=token_data.get("token_type", "Bearer"),
                    expires_at=datetime.fromisoformat(token_data["expires_at"]),
                    scope=token_data.get("scope", []),
                )

                self.state = AuthenticationState.AUTHENTICATED
                self._schedule_token_refresh()

                return self.current_token

            except Exception as e:
                self.state = AuthenticationState.INVALID
                if isinstance(e, AuthenticationError):
                    raise
                else:
                    raise AuthenticationError(f"Authentication failed: {str(e)}")

    async def authenticate_with_biometric(
        self, device_id: str, biometric_data: Dict[str, Any]
    ) -> AuthToken:
        """Authenticate with biometric data."""
        async with self._auth_lock:
            self.state = AuthenticationState.AUTHENTICATING

            try:
                auth_data = {
                    "grant_type": "biometric",
                    "device_id": device_id,
                    "biometric_data": biometric_data,
                    "organization_id": self.config.organization_id,
                    "app_id": self.config.app_id,
                }

                if self.device_info:
                    auth_data["device_info"] = self.device_info.dict()

                response = await self.http_client.post(
                    "mobile-erp/security/biometric/authenticate", auth_data
                )

                if (
                    response["status"] != 200
                    or not response["data"]["authentication_successful"]
                ):
                    raise AuthenticationError("Biometric authentication failed")

                token_data = response["data"]
                self.current_token = AuthToken(
                    access_token=token_data["session_token"],
                    token_type="Bearer",
                    expires_at=datetime.fromisoformat(token_data["expires_at"]),
                )

                self.state = AuthenticationState.AUTHENTICATED
                self._schedule_token_refresh()

                return self.current_token

            except Exception as e:
                self.state = AuthenticationState.INVALID
                if isinstance(e, AuthenticationError):
                    raise
                else:
                    raise AuthenticationError(
                        f"Biometric authentication failed: {str(e)}"
                    )

    async def refresh_token(self) -> Optional[AuthToken]:
        """Refresh authentication token."""
        if not self.current_token or not self.current_token.refresh_token:
            return None

        async with self._auth_lock:
            self.state = AuthenticationState.REFRESHING

            try:
                refresh_data = {
                    "grant_type": "refresh_token",
                    "refresh_token": self.current_token.refresh_token,
                    "organization_id": self.config.organization_id,
                    "app_id": self.config.app_id,
                }

                response = await self.http_client.post("auth/refresh", refresh_data)

                if response["status"] != 200:
                    self.state = AuthenticationState.EXPIRED
                    return None

                token_data = response["data"]
                self.current_token = AuthToken(
                    access_token=token_data["access_token"],
                    refresh_token=token_data.get(
                        "refresh_token", self.current_token.refresh_token
                    ),
                    token_type=token_data.get("token_type", "Bearer"),
                    expires_at=datetime.fromisoformat(token_data["expires_at"]),
                    scope=token_data.get("scope", []),
                )

                self.state = AuthenticationState.AUTHENTICATED
                self._schedule_token_refresh()

                return self.current_token

            except Exception:
                self.state = AuthenticationState.EXPIRED
                return None

    async def get_valid_token(self) -> Optional[AuthToken]:
        """Get valid authentication token, refreshing if necessary."""
        if not self.current_token:
            return None

        # Check if token is about to expire (5 minutes buffer)
        if self.current_token.expires_at <= datetime.now() + timedelta(minutes=5):
            refreshed_token = await self.refresh_token()
            return refreshed_token

        return self.current_token

    async def logout(self) -> None:
        """Logout and invalidate tokens."""
        async with self._auth_lock:
            if self._token_refresh_task:
                self._token_refresh_task.cancel()
                self._token_refresh_task = None

            if self.current_token:
                try:
                    await self.http_client.post(
                        "auth/logout", {"token": self.current_token.access_token}
                    )
                except Exception:
                    pass  # Ignore logout errors

            self.current_token = None
            self.state = AuthenticationState.UNAUTHENTICATED

    async def handle_authentication_error(self) -> None:
        """Handle authentication errors."""
        self.state = AuthenticationState.EXPIRED
        # Could trigger re-authentication flow here

    def _schedule_token_refresh(self) -> None:
        """Schedule automatic token refresh."""
        if self._token_refresh_task:
            self._token_refresh_task.cancel()

        if self.current_token:
            # Schedule refresh 10 minutes before expiration
            refresh_time = (
                self.current_token.expires_at - datetime.now() - timedelta(minutes=10)
            )
            if refresh_time.total_seconds() > 0:
                self._token_refresh_task = asyncio.create_task(
                    self._auto_refresh_token(refresh_time.total_seconds())
                )

    async def _auto_refresh_token(self, delay_seconds: float) -> None:
        """Automatically refresh token after delay."""
        try:
            await asyncio.sleep(delay_seconds)
            await self.refresh_token()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[SDK] Auto token refresh failed: {e}")


class EventEmitter:
    """Simple event emitter for SDK events."""

    def __init__(self) -> dict:
        self._listeners: Dict[str, List[Callable]] = {}

    def on(self, event: str, callback: Callable) -> None:
        """Register event listener."""
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    def off(self, event: str, callback: Callable) -> None:
        """Remove event listener."""
        if event in self._listeners:
            try:
                self._listeners[event].remove(callback)
            except ValueError:
                pass

    def emit(self, event: str, *args, **kwargs) -> None:
        """Emit event to all listeners."""
        if event in self._listeners:
            for callback in self._listeners[event]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    print(f"[SDK] Event listener error: {e}")


class MobileERPSDK:
    """Main SDK class."""

    def __init__(self, config: SDKConfig) -> dict:
        self.config = config
        self.http_client = HTTPClient(config)
        self.auth_manager = AuthManager(config, self.http_client)
        self.events = EventEmitter()

        # Add default interceptors
        self.http_client.add_interceptor(LoggingInterceptor(config))
        self.http_client.add_interceptor(AuthenticationInterceptor(self.auth_manager))

        # SDK modules will be initialized here
        self._modules: Dict[str, Any] = {}

    async def initialize(self, device_info: DeviceInfo) -> None:
        """Initialize SDK with device information."""
        self.auth_manager.set_device_info(device_info)

        # Initialize HTTP client
        await self.http_client._ensure_session()

        # Emit initialization event
        self.events.emit("sdk.initialized", device_info)

    async def authenticate(
        self,
        username: str,
        password: str,
        additional_factors: Optional[Dict[str, str]] = None,
    ) -> AuthToken:
        """Authenticate with credentials."""
        token = await self.auth_manager.authenticate_with_credentials(
            username, password, additional_factors
        )

        self.events.emit("auth.success", token)
        return token

    async def authenticate_biometric(
        self, device_id: str, biometric_data: Dict[str, Any]
    ) -> AuthToken:
        """Authenticate with biometric data."""
        token = await self.auth_manager.authenticate_with_biometric(
            device_id, biometric_data
        )

        self.events.emit("auth.success", token)
        return token

    async def logout(self) -> None:
        """Logout from SDK."""
        await self.auth_manager.logout()
        self.events.emit("auth.logout")

    def is_authenticated(self) -> bool:
        """Check if authenticated."""
        return self.auth_manager.is_authenticated()

    def get_module(self, module_name: str) -> Any:
        """Get SDK module."""
        return self._modules.get(module_name)

    def register_module(self, module_name: str, module_instance: Any) -> None:
        """Register SDK module."""
        self._modules[module_name] = module_instance

    async def close(self) -> None:
        """Close SDK and cleanup resources."""
        await self.auth_manager.logout()
        await self.http_client.close()
        self.events.emit("sdk.closed")
