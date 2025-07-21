"""Security middleware for comprehensive audit logging and monitoring."""

import asyncio
import time
import uuid
from datetime import datetime
from typing import Callable, Dict, List, Optional

from fastapi import Request, Response
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

from app.models.security_event import SecurityEventType, ThreatLevel
from app.services.enhanced_security_service import EnhancedSecurityService
from app.services.realtime_alert_service import realtime_alert_service


class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive security auditing and monitoring."""

    def __init__(
        self,
        app,
        excluded_paths: Optional[List[str]] = None,
        log_all_requests: bool = True,
        detect_suspicious_patterns: bool = True,
        rate_limit_enabled: bool = True,
        max_requests_per_minute: int = 100,
    ):
        """Initialize security audit middleware."""
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/health",
            "/ping",
        ]
        self.log_all_requests = log_all_requests
        self.detect_suspicious_patterns = detect_suspicious_patterns
        self.rate_limit_enabled = rate_limit_enabled
        self.max_requests_per_minute = max_requests_per_minute
        
        # Rate limiting storage (in production, use Redis)
        self.request_counts: Dict[str, Dict[str, int]] = {}
        self.failed_login_attempts: Dict[str, List[datetime]] = {}
        self.suspicious_ips: set = set()
        
        # Security patterns
        self.sensitive_endpoints = [
            "/auth/login",
            "/auth/logout",
            "/users",
            "/roles",
            "/permissions",
            "/security-audit",
            "/admin",
        ]
        
        self.high_risk_actions = [
            "POST /users",
            "PUT /users/",
            "DELETE /users/",
            "POST /roles",
            "PUT /roles/",
            "DELETE /roles/",
            "POST /permissions",
            "PUT /permissions/",
            "DELETE /permissions/",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security middleware."""
        start_time = time.time()
        session_id = str(uuid.uuid4())
        
        # Skip processing for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Extract request information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        method = request.method
        path = request.url.path
        
        # Rate limiting check
        if self.rate_limit_enabled and self._is_rate_limited(client_ip):
            await self._log_security_event(
                request=request,
                event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
                title="Rate limit exceeded",
                description=f"Client {client_ip} exceeded rate limit",
                threat_level=ThreatLevel.MEDIUM,
                session_id=session_id,
            )
            
            # Return rate limit response
            return Response(
                content='{"detail": "Rate limit exceeded"}',
                status_code=429,
                headers={"Content-Type": "application/json"},
            )
        
        # Pre-request security checks
        await self._pre_request_security_checks(
            request, client_ip, user_agent, session_id
        )
        
        # Process request
        try:
            response = await call_next(request)
            processing_time = time.time() - start_time
            
            # Post-request security analysis
            await self._post_request_security_analysis(
                request, response, processing_time, session_id
            )
            
            return response
            
        except Exception as e:
            # Log exception as security event
            await self._log_security_event(
                request=request,
                event_type=SecurityEventType.API_ABUSE,
                title="API request exception",
                description=f"Exception during API request: {str(e)}",
                threat_level=ThreatLevel.MEDIUM,
                session_id=session_id,
                evidence={"exception": str(e), "path": path, "method": method},
            )
            raise

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"

    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client IP is rate limited."""
        current_minute = int(time.time() // 60)
        
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = {}
        
        # Clean old entries
        self.request_counts[client_ip] = {
            minute: count
            for minute, count in self.request_counts[client_ip].items()
            if minute >= current_minute - 1
        }
        
        # Check current minute count
        current_count = self.request_counts[client_ip].get(current_minute, 0)
        
        if current_count >= self.max_requests_per_minute:
            return True
        
        # Increment count
        self.request_counts[client_ip][current_minute] = current_count + 1
        return False

    async def _pre_request_security_checks(
        self, request: Request, client_ip: str, user_agent: str, session_id: str
    ) -> None:
        """Perform security checks before processing request."""
        method = request.method
        path = request.url.path
        
        # Check for suspicious IP
        if client_ip in self.suspicious_ips:
            await self._log_security_event(
                request=request,
                event_type=SecurityEventType.SUSPICIOUS_IP,
                title="Request from suspicious IP",
                description=f"Request from known suspicious IP: {client_ip}",
                threat_level=ThreatLevel.HIGH,
                session_id=session_id,
            )
        
        # Check for suspicious user agent
        if self._is_suspicious_user_agent(user_agent):
            await self._log_security_event(
                request=request,
                event_type=SecurityEventType.SUSPICIOUS_IP,
                title="Suspicious user agent detected",
                description=f"Suspicious user agent: {user_agent}",
                threat_level=ThreatLevel.MEDIUM,
                session_id=session_id,
                evidence={"user_agent": user_agent},
            )
        
        # Check for after-hours access
        if self._is_after_hours() and self._is_sensitive_endpoint(path):
            await self._log_security_event(
                request=request,
                event_type=SecurityEventType.AFTER_HOURS_ACCESS,
                title="After-hours access to sensitive endpoint",
                description=f"After-hours access to {method} {path}",
                threat_level=ThreatLevel.MEDIUM,
                session_id=session_id,
            )
        
        # Check for high-risk actions
        action = f"{method} {path}"
        if any(action.startswith(risk_action) for risk_action in self.high_risk_actions):
            await self._log_security_event(
                request=request,
                event_type=SecurityEventType.ADMIN_ACTION,
                title="High-risk administrative action",
                description=f"High-risk action attempted: {action}",
                threat_level=ThreatLevel.MEDIUM,
                session_id=session_id,
            )

    async def _post_request_security_analysis(
        self,
        request: Request,
        response: Response,
        processing_time: float,
        session_id: str,
    ) -> None:
        """Analyze request after processing for security implications."""
        method = request.method
        path = request.url.path
        status_code = response.status_code
        client_ip = self._get_client_ip(request)
        
        # Log all requests if enabled
        if self.log_all_requests and self._is_sensitive_endpoint(path):
            await self._log_security_event(
                request=request,
                event_type=SecurityEventType.DATA_ACCESS,
                title=f"API access: {method} {path}",
                description=f"API endpoint accessed with status {status_code}",
                threat_level=ThreatLevel.LOW,
                session_id=session_id,
                evidence={
                    "status_code": status_code,
                    "processing_time": processing_time,
                },
            )
        
        # Analyze failed authentication
        if path == "/auth/login" and status_code in [401, 403]:
            await self._handle_failed_login(request, client_ip, session_id)
        
        # Analyze successful authentication
        elif path == "/auth/login" and status_code == 200:
            await self._handle_successful_login(request, client_ip, session_id)
        
        # Analyze data modification operations
        elif method in ["POST", "PUT", "DELETE"] and status_code in [200, 201]:
            await self._handle_data_modification(request, response, session_id)
        
        # Analyze suspicious response times
        if processing_time > 5.0:  # More than 5 seconds
            await self._log_security_event(
                request=request,
                event_type=SecurityEventType.ANOMALY_DETECTED,
                title="Unusually long processing time",
                description=f"Request took {processing_time:.2f} seconds to process",
                threat_level=ThreatLevel.LOW,
                session_id=session_id,
                evidence={"processing_time": processing_time},
            )

    async def _handle_failed_login(
        self, request: Request, client_ip: str, session_id: str
    ) -> None:
        """Handle failed login attempts."""
        current_time = datetime.utcnow()
        
        # Track failed attempts per IP
        if client_ip not in self.failed_login_attempts:
            self.failed_login_attempts[client_ip] = []
        
        self.failed_login_attempts[client_ip].append(current_time)
        
        # Clean old attempts (older than 1 hour)
        cutoff_time = current_time.replace(hour=current_time.hour - 1)
        self.failed_login_attempts[client_ip] = [
            attempt for attempt in self.failed_login_attempts[client_ip]
            if attempt > cutoff_time
        ]
        
        recent_attempts = len(self.failed_login_attempts[client_ip])
        
        # Determine threat level based on attempt count
        if recent_attempts >= 10:
            threat_level = ThreatLevel.CRITICAL
            self.suspicious_ips.add(client_ip)
        elif recent_attempts >= 5:
            threat_level = ThreatLevel.HIGH
        elif recent_attempts >= 3:
            threat_level = ThreatLevel.MEDIUM
        else:
            threat_level = ThreatLevel.LOW
        
        await self._log_security_event(
            request=request,
            event_type=SecurityEventType.LOGIN_FAILURE,
            title=f"Failed login attempt ({recent_attempts} recent)",
            description=f"Failed login from {client_ip}, {recent_attempts} recent attempts",
            threat_level=threat_level,
            session_id=session_id,
            evidence={"recent_attempts": recent_attempts, "client_ip": client_ip},
        )
        
        # Generate alert for multiple failures
        if recent_attempts >= 5:
            await self._create_security_alert(
                alert_type="multiple_failed_logins",
                severity=threat_level,
                title=f"Multiple Failed Login Attempts from {client_ip}",
                message=f"IP address {client_ip} has {recent_attempts} failed login attempts in the last hour",
                evidence={"client_ip": client_ip, "attempt_count": recent_attempts},
            )

    async def _handle_successful_login(
        self, request: Request, client_ip: str, session_id: str
    ) -> None:
        """Handle successful login attempts."""
        # Check if this IP had previous failed attempts
        recent_failures = len(self.failed_login_attempts.get(client_ip, []))
        
        if recent_failures > 0:
            await self._log_security_event(
                request=request,
                event_type=SecurityEventType.LOGIN_SUCCESS,
                title=f"Successful login after {recent_failures} failures",
                description=f"Successful login from {client_ip} after {recent_failures} failed attempts",
                threat_level=ThreatLevel.MEDIUM if recent_failures >= 3 else ThreatLevel.LOW,
                session_id=session_id,
                evidence={"previous_failures": recent_failures},
            )
            
            # Clear failed attempts for this IP
            self.failed_login_attempts[client_ip] = []
        else:
            await self._log_security_event(
                request=request,
                event_type=SecurityEventType.LOGIN_SUCCESS,
                title="Successful login",
                description=f"User successfully logged in from {client_ip}",
                threat_level=ThreatLevel.LOW,
                session_id=session_id,
            )

    async def _handle_data_modification(
        self, request: Request, response: Response, session_id: str
    ) -> None:
        """Handle data modification operations."""
        method = request.method
        path = request.url.path
        
        # Determine event type
        if method == "POST":
            event_type = SecurityEventType.DATA_MODIFICATION
            action = "created"
        elif method == "PUT":
            event_type = SecurityEventType.DATA_MODIFICATION
            action = "updated"
        elif method == "DELETE":
            event_type = SecurityEventType.DATA_DELETION
            action = "deleted"
        else:
            return
        
        # Determine threat level based on resource type
        if any(sensitive in path for sensitive in ["/users", "/roles", "/permissions"]):
            threat_level = ThreatLevel.HIGH
        elif any(important in path for important in ["/organizations", "/departments"]):
            threat_level = ThreatLevel.MEDIUM
        else:
            threat_level = ThreatLevel.LOW
        
        await self._log_security_event(
            request=request,
            event_type=event_type,
            title=f"Data {action}: {method} {path}",
            description=f"Data {action} operation performed on {path}",
            threat_level=threat_level,
            session_id=session_id,
        )

    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent appears suspicious."""
        suspicious_patterns = [
            "bot",
            "crawler",
            "spider",
            "scraper",
            "scanner",
            "sqlmap",
            "nikto",
            "nmap",
        ]
        
        user_agent_lower = user_agent.lower()
        return any(pattern in user_agent_lower for pattern in suspicious_patterns)

    def _is_after_hours(self) -> bool:
        """Check if current time is after business hours."""
        current_hour = datetime.utcnow().hour
        # Consider after hours: before 6 AM or after 10 PM UTC
        return current_hour < 6 or current_hour > 22

    def _is_sensitive_endpoint(self, path: str) -> bool:
        """Check if endpoint is considered sensitive."""
        return any(sensitive in path for sensitive in self.sensitive_endpoints)

    async def _log_security_event(
        self,
        request: Request,
        event_type: SecurityEventType,
        title: str,
        description: str,
        threat_level: ThreatLevel,
        session_id: str,
        evidence: Optional[Dict] = None,
    ) -> None:
        """Log a security event."""
        try:
            # Create enhanced security service instance
            # In a real implementation, you would get this from dependency injection
            # For now, we'll create a minimal event logging mechanism
            
            client_ip = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent", "")
            
            event_data = {
                "event_type": event_type.value,
                "title": title,
                "description": description,
                "threat_level": threat_level.value,
                "source_ip": client_ip,
                "user_agent": user_agent,
                "session_id": session_id,
                "api_endpoint": str(request.url.path),
                "http_method": request.method,
                "evidence": evidence or {},
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            # In a production environment, you would:
            # 1. Get database session from request state
            # 2. Create EnhancedSecurityService instance
            # 3. Log the event properly
            
            # For now, we'll print to console (in production, use proper logging)
            print(f"SECURITY EVENT: {event_data}")
            
        except Exception as e:
            # Don't let security logging break the application
            print(f"Error logging security event: {e}")

    async def _create_security_alert(
        self,
        alert_type: str,
        severity: ThreatLevel,
        title: str,
        message: str,
        evidence: Optional[Dict] = None,
    ) -> None:
        """Create and queue a security alert."""
        try:
            # Create alert and queue it
            if realtime_alert_service.is_running:
                from app.models.security_event import SecurityAlert
                
                alert = SecurityAlert(
                    alert_id=str(uuid.uuid4()),
                    alert_type=alert_type,
                    severity=severity,
                    title=title,
                    message=message,
                    delivery_methods=["email", "in_app"],
                )
                alert.created_at = datetime.utcnow()
                
                await realtime_alert_service.queue_alert(alert)
            
        except Exception as e:
            print(f"Error creating security alert: {e}")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers to responses."""

    def __init__(self, app):
        """Initialize security headers middleware."""
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        return response


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """Middleware for IP whitelisting (optional security feature)."""

    def __init__(self, app, whitelisted_ips: Optional[List[str]] = None, enabled: bool = False):
        """Initialize IP whitelist middleware."""
        super().__init__(app)
        self.whitelisted_ips = set(whitelisted_ips or [])
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check IP whitelist if enabled."""
        if not self.enabled:
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        
        if client_ip not in self.whitelisted_ips:
            return Response(
                content='{"detail": "IP address not whitelisted"}',
                status_code=403,
                headers={"Content-Type": "application/json"},
            )
        
        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"