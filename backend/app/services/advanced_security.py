"""
CC02 v55.0 Advanced Security System
Enterprise-grade Security, Authentication, and Authorization Management
Day 3 of 7-day intensive backend development
"""

from typing import List, Dict, Any, Optional, Union, Set, Tuple
from uuid import UUID, uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import hashlib
import secrets
import jwt
import bcrypt
import asyncio
import json
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, text
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import SecurityError, AuthenticationError, AuthorizationError
from app.models.security import (
    SecurityPolicy, AccessToken, RefreshToken, LoginAttempt, SecurityAudit,
    RolePermission, UserRole, SecurityAlert, TwoFactorAuth, ApiKey
)
from app.models.user import User
from app.services.audit_service import AuditService

class SecurityLevel(str, Enum):
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"
    TOP_SECRET = "top_secret"

class AuthenticationMethod(str, Enum):
    PASSWORD = "password"
    TWO_FACTOR = "two_factor"
    BIOMETRIC = "biometric"
    CERTIFICATE = "certificate"
    SSO = "sso"
    API_KEY = "api_key"

class PermissionType(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"
    OWNER = "owner"

class ThreatLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityEventType(str, Enum):
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PERMISSION_DENIED = "permission_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    API_RATE_LIMIT_EXCEEDED = "api_rate_limit_exceeded"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"

@dataclass
class SecurityContext:
    """Security context for operations"""
    user_id: Optional[UUID] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    authentication_method: Optional[AuthenticationMethod] = None
    security_level: SecurityLevel = SecurityLevel.PUBLIC
    permissions: Set[str] = field(default_factory=set)
    roles: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SecurityThreat:
    """Security threat detection result"""
    threat_id: UUID
    threat_type: str
    threat_level: ThreatLevel
    source_ip: str
    user_id: Optional[UUID]
    description: str
    evidence: Dict[str, Any]
    detected_at: datetime
    mitigated: bool = False

class PasswordPolicy:
    """Password policy enforcement"""
    
    def __init__(self, config: Dict[str, Any]):
        self.min_length = config.get('min_length', 8)
        self.max_length = config.get('max_length', 128)
        self.require_uppercase = config.get('require_uppercase', True)
        self.require_lowercase = config.get('require_lowercase', True)
        self.require_digits = config.get('require_digits', True)
        self.require_special = config.get('require_special', True)
        self.special_chars = config.get('special_chars', "!@#$%^&*()_+-=[]{}|;:,.<>?")
        self.password_history = config.get('password_history', 5)
        self.max_age_days = config.get('max_age_days', 90)
    
    def validate_password(self, password: str, user_id: Optional[UUID] = None) -> Tuple[bool, List[str]]:
        """Validate password against policy"""
        
        errors = []
        
        # Length check
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")
        
        if len(password) > self.max_length:
            errors.append(f"Password must be at most {self.max_length} characters long")
        
        # Character requirements
        if self.require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.require_digits and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        
        if self.require_special and not any(c in self.special_chars for c in password):
            errors.append(f"Password must contain at least one special character: {self.special_chars}")
        
        # Common password check
        if self._is_common_password(password):
            errors.append("Password is too common, please choose a more unique password")
        
        return len(errors) == 0, errors
    
    def _is_common_password(self, password: str) -> bool:
        """Check if password is in common passwords list"""
        common_passwords = {
            "password", "123456", "123456789", "12345678", "12345", "1234567",
            "admin", "qwerty", "abc123", "password123", "welcome", "letmein"
        }
        return password.lower() in common_passwords
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

class RateLimiter:
    """Rate limiting for API endpoints"""
    
    def __init__(self):
        self.limits: Dict[str, Dict[str, Any]] = {}
        self.attempts: Dict[str, List[datetime]] = {}
    
    def set_limit(self, key: str, max_attempts: int, window_seconds: int):
        """Set rate limit for a key"""
        self.limits[key] = {
            'max_attempts': max_attempts,
            'window_seconds': window_seconds
        }
    
    def is_allowed(self, key: str, identifier: str) -> Tuple[bool, int]:
        """Check if request is allowed"""
        
        limit_key = f"{key}:{identifier}"
        now = datetime.utcnow()
        
        # Get limit configuration
        if key not in self.limits:
            return True, 0
        
        limit_config = self.limits[key]
        max_attempts = limit_config['max_attempts']
        window_seconds = limit_config['window_seconds']
        
        # Clean old attempts
        if limit_key in self.attempts:
            cutoff = now - timedelta(seconds=window_seconds)
            self.attempts[limit_key] = [
                attempt for attempt in self.attempts[limit_key]
                if attempt > cutoff
            ]
        else:
            self.attempts[limit_key] = []
        
        # Check if limit exceeded
        current_attempts = len(self.attempts[limit_key])
        
        if current_attempts >= max_attempts:
            return False, max_attempts - current_attempts
        
        # Record attempt
        self.attempts[limit_key].append(now)
        return True, max_attempts - current_attempts - 1

class SecurityTokenManager:
    """JWT token management"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire = 900  # 15 minutes
        self.refresh_token_expire = 2592000  # 30 days
    
    def create_access_token(
        self,
        user_id: UUID,
        permissions: Set[str],
        roles: Set[str],
        additional_claims: Dict[str, Any] = None
    ) -> str:
        """Create JWT access token"""
        
        now = datetime.utcnow()
        expire = now + timedelta(seconds=self.access_token_expire)
        
        payload = {
            'user_id': str(user_id),
            'permissions': list(permissions),
            'roles': list(roles),
            'iat': now.timestamp(),
            'exp': expire.timestamp(),
            'type': 'access'
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: UUID) -> str:
        """Create JWT refresh token"""
        
        now = datetime.utcnow()
        expire = now + timedelta(seconds=self.refresh_token_expire)
        
        payload = {
            'user_id': str(user_id),
            'iat': now.timestamp(),
            'exp': expire.timestamp(),
            'type': 'refresh',
            'jti': str(uuid4())  # Unique token ID
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate JWT token"""
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")
    
    def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        # In production, would check against blacklist storage
        return False

class ThreatDetector:
    """Security threat detection system"""
    
    def __init__(self):
        self.threat_patterns = {
            'brute_force': {
                'threshold': 5,
                'window_minutes': 5,
                'severity': ThreatLevel.HIGH
            },
            'sql_injection': {
                'patterns': [
                    r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
                    r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))",
                    r"(\%27)|(\')\s*((\%6F)|o|(\%4F))((\%72)|r|(\%52))"
                ],
                'severity': ThreatLevel.CRITICAL
            },
            'xss_attempt': {
                'patterns': [
                    r"<script[^>]*>.*?</script>",
                    r"javascript:",
                    r"on\w+\s*="
                ],
                'severity': ThreatLevel.HIGH
            },
            'unusual_access_pattern': {
                'threshold': 100,
                'window_minutes': 1,
                'severity': ThreatLevel.MEDIUM
            }
        }
        self.detected_threats: List[SecurityThreat] = []
    
    async def analyze_request(
        self,
        context: SecurityContext,
        request_data: Dict[str, Any]
    ) -> List[SecurityThreat]:
        """Analyze request for security threats"""
        
        threats = []
        
        # Check for SQL injection
        sql_threats = self._detect_sql_injection(context, request_data)
        threats.extend(sql_threats)
        
        # Check for XSS attempts
        xss_threats = self._detect_xss_attempts(context, request_data)
        threats.extend(xss_threats)
        
        # Check for brute force attacks
        if context.ip_address:
            brute_force_threats = await self._detect_brute_force(context)
            threats.extend(brute_force_threats)
        
        # Check for unusual access patterns
        access_pattern_threats = await self._detect_unusual_access(context)
        threats.extend(access_pattern_threats)
        
        # Store detected threats
        self.detected_threats.extend(threats)
        
        return threats
    
    def _detect_sql_injection(
        self,
        context: SecurityContext,
        request_data: Dict[str, Any]
    ) -> List[SecurityThreat]:
        """Detect SQL injection attempts"""
        
        import re
        threats = []
        patterns = self.threat_patterns['sql_injection']['patterns']
        
        def check_value(value: Any) -> bool:
            if isinstance(value, str):
                for pattern in patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        return True
            return False
        
        def check_dict(data: Dict[str, Any]):
            for key, value in data.items():
                if check_value(key) or check_value(value):
                    return True
                if isinstance(value, dict):
                    if check_dict(value):
                        return True
                elif isinstance(value, list):
                    for item in value:
                        if check_value(item):
                            return True
            return False
        
        if check_dict(request_data):
            threat = SecurityThreat(
                threat_id=uuid4(),
                threat_type="sql_injection",
                threat_level=ThreatLevel.CRITICAL,
                source_ip=context.ip_address or "unknown",
                user_id=context.user_id,
                description="SQL injection attempt detected in request data",
                evidence={"request_data": request_data},
                detected_at=datetime.utcnow()
            )
            threats.append(threat)
        
        return threats
    
    def _detect_xss_attempts(
        self,
        context: SecurityContext,
        request_data: Dict[str, Any]
    ) -> List[SecurityThreat]:
        """Detect XSS attempts"""
        
        import re
        threats = []
        patterns = self.threat_patterns['xss_attempt']['patterns']
        
        def check_value(value: Any) -> bool:
            if isinstance(value, str):
                for pattern in patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        return True
            return False
        
        def check_dict(data: Dict[str, Any]):
            for key, value in data.items():
                if check_value(key) or check_value(value):
                    return True
                if isinstance(value, dict):
                    if check_dict(value):
                        return True
                elif isinstance(value, list):
                    for item in value:
                        if check_value(item):
                            return True
            return False
        
        if check_dict(request_data):
            threat = SecurityThreat(
                threat_id=uuid4(),
                threat_type="xss_attempt",
                threat_level=ThreatLevel.HIGH,
                source_ip=context.ip_address or "unknown",
                user_id=context.user_id,
                description="Cross-site scripting (XSS) attempt detected",
                evidence={"request_data": request_data},
                detected_at=datetime.utcnow()
            )
            threats.append(threat)
        
        return threats
    
    async def _detect_brute_force(self, context: SecurityContext) -> List[SecurityThreat]:
        """Detect brute force attacks"""
        
        threats = []
        threshold = self.threat_patterns['brute_force']['threshold']
        window_minutes = self.threat_patterns['brute_force']['window_minutes']
        
        # Count recent failed login attempts from this IP
        recent_failures = len([
            t for t in self.detected_threats
            if (t.threat_type == "login_failure" and
                t.source_ip == context.ip_address and
                t.detected_at > datetime.utcnow() - timedelta(minutes=window_minutes))
        ])
        
        if recent_failures >= threshold:
            threat = SecurityThreat(
                threat_id=uuid4(),
                threat_type="brute_force",
                threat_level=ThreatLevel.HIGH,
                source_ip=context.ip_address or "unknown",
                user_id=context.user_id,
                description=f"Brute force attack detected: {recent_failures} failed attempts",
                evidence={"failed_attempts": recent_failures, "threshold": threshold},
                detected_at=datetime.utcnow()
            )
            threats.append(threat)
        
        return threats
    
    async def _detect_unusual_access(self, context: SecurityContext) -> List[SecurityThreat]:
        """Detect unusual access patterns"""
        
        threats = []
        
        # Check for unusual geographic access
        if context.user_id and context.ip_address:
            # In production, would check against user's typical locations
            # For now, simulate unusual access detection
            pass
        
        # Check for unusual time-based access
        now = datetime.utcnow()
        if now.hour < 6 or now.hour > 22:  # Outside normal business hours
            # Could indicate unusual access
            pass
        
        return threats

class PermissionManager:
    """Permission and role management"""
    
    def __init__(self):
        self.permission_hierarchy = {
            PermissionType.OWNER: [
                PermissionType.ADMIN, PermissionType.DELETE,
                PermissionType.WRITE, PermissionType.READ, PermissionType.EXECUTE
            ],
            PermissionType.ADMIN: [
                PermissionType.DELETE, PermissionType.WRITE,
                PermissionType.READ, PermissionType.EXECUTE
            ],
            PermissionType.DELETE: [PermissionType.WRITE, PermissionType.READ],
            PermissionType.WRITE: [PermissionType.READ],
            PermissionType.EXECUTE: [PermissionType.READ],
            PermissionType.READ: []
        }
    
    async def check_permission(
        self,
        user_id: UUID,
        resource: str,
        permission: str,
        session: AsyncSession
    ) -> bool:
        """Check if user has permission for resource"""
        
        # Get user permissions
        user_permissions = await self._get_user_permissions(user_id, session)
        
        # Check direct permission
        permission_key = f"{resource}:{permission}"
        if permission_key in user_permissions:
            return True
        
        # Check wildcard permissions
        wildcard_key = f"{resource}:*"
        if wildcard_key in user_permissions:
            return True
        
        global_key = f"*:{permission}"
        if global_key in user_permissions:
            return True
        
        # Check hierarchical permissions
        for higher_perm in self.permission_hierarchy.get(PermissionType(permission), []):
            higher_key = f"{resource}:{higher_perm.value}"
            if higher_key in user_permissions:
                return True
        
        return False
    
    async def _get_user_permissions(
        self,
        user_id: UUID,
        session: AsyncSession
    ) -> Set[str]:
        """Get all permissions for a user"""
        
        permissions = set()
        
        # Get direct user permissions
        direct_perms = await session.execute(
            select(RolePermission.resource, RolePermission.permission)
            .join(UserRole)
            .where(UserRole.user_id == user_id)
        )
        
        for resource, permission in direct_perms.fetchall():
            permissions.add(f"{resource}:{permission}")
        
        return permissions
    
    async def grant_permission(
        self,
        user_id: UUID,
        role_id: UUID,
        resource: str,
        permission: str,
        granted_by: UUID,
        session: AsyncSession
    ):
        """Grant permission to user"""
        
        # Check if permission already exists
        existing = await session.execute(
            select(RolePermission)
            .where(
                and_(
                    RolePermission.role_id == role_id,
                    RolePermission.resource == resource,
                    RolePermission.permission == permission
                )
            )
        )
        
        if not existing.scalar_one_or_none():
            new_permission = RolePermission(
                id=uuid4(),
                role_id=role_id,
                resource=resource,
                permission=permission,
                granted_by=granted_by,
                granted_at=datetime.utcnow()
            )
            session.add(new_permission)
    
    async def revoke_permission(
        self,
        role_id: UUID,
        resource: str,
        permission: str,
        session: AsyncSession
    ):
        """Revoke permission from role"""
        
        await session.execute(
            delete(RolePermission)
            .where(
                and_(
                    RolePermission.role_id == role_id,
                    RolePermission.resource == resource,
                    RolePermission.permission == permission
                )
            )
        )

class AdvancedSecurityManager:
    """Enterprise Advanced Security Manager"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.password_policy = PasswordPolicy(config.get('password_policy', {}))
        self.rate_limiter = RateLimiter()
        self.token_manager = SecurityTokenManager(
            config.get('jwt_secret', secrets.token_urlsafe(32))
        )
        self.threat_detector = ThreatDetector()
        self.permission_manager = PermissionManager()
        self.audit_service = AuditService()
        
        # Initialize rate limits
        self._setup_rate_limits()
    
    def _setup_rate_limits(self):
        """Setup default rate limits"""
        self.rate_limiter.set_limit('login', 5, 300)  # 5 attempts per 5 minutes
        self.rate_limiter.set_limit('api', 1000, 3600)  # 1000 requests per hour
        self.rate_limiter.set_limit('password_reset', 3, 3600)  # 3 resets per hour
    
    async def authenticate_user(
        self,
        username: str,
        password: str,
        context: SecurityContext,
        session: AsyncSession
    ) -> Tuple[bool, Optional[User], List[str]]:
        """Authenticate user with advanced security checks"""
        
        errors = []
        
        # Rate limiting check
        allowed, remaining = self.rate_limiter.is_allowed('login', context.ip_address or 'unknown')
        if not allowed:
            errors.append("Too many login attempts. Please try again later.")
            await self._log_security_event(
                SecurityEventType.LOGIN_FAILURE,
                context,
                {"reason": "rate_limit_exceeded"}
            )
            return False, None, errors
        
        # Threat detection
        threats = await self.threat_detector.analyze_request(
            context,
            {"username": username, "password": "***"}
        )
        
        if any(t.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL] for t in threats):
            errors.append("Security threat detected. Access denied.")
            await self._log_security_event(
                SecurityEventType.SUSPICIOUS_ACTIVITY,
                context,
                {"threats": [t.threat_type for t in threats]}
            )
            return False, None, errors
        
        # Get user
        user_result = await session.execute(
            select(User).where(User.username == username)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            errors.append("Invalid credentials")
            await self._log_security_event(
                SecurityEventType.LOGIN_FAILURE,
                context,
                {"reason": "user_not_found", "username": username}
            )
            return False, None, errors
        
        # Check if account is locked
        if user.is_locked:
            errors.append("Account is locked. Please contact administrator.")
            await self._log_security_event(
                SecurityEventType.LOGIN_FAILURE,
                context,
                {"reason": "account_locked", "user_id": str(user.id)}
            )
            return False, None, errors
        
        # Verify password
        if not self.password_policy.verify_password(password, user.password_hash):
            errors.append("Invalid credentials")
            
            # Increment failed attempts
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            user.last_failed_login = datetime.utcnow()
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.is_locked = True
                user.locked_at = datetime.utcnow()
                await self._log_security_event(
                    SecurityEventType.ACCOUNT_LOCKED,
                    context,
                    {"user_id": str(user.id), "failed_attempts": user.failed_login_attempts}
                )
            
            await self._log_security_event(
                SecurityEventType.LOGIN_FAILURE,
                context,
                {"reason": "invalid_password", "user_id": str(user.id)}
            )
            return False, None, errors
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        
        await self._log_security_event(
            SecurityEventType.LOGIN_SUCCESS,
            context,
            {"user_id": str(user.id)}
        )
        
        return True, user, []
    
    async def authorize_access(
        self,
        user_id: UUID,
        resource: str,
        permission: str,
        context: SecurityContext,
        session: AsyncSession
    ) -> bool:
        """Authorize user access to resource"""
        
        # Check permission
        has_permission = await self.permission_manager.check_permission(
            user_id, resource, permission, session
        )
        
        if not has_permission:
            await self._log_security_event(
                SecurityEventType.PERMISSION_DENIED,
                context,
                {
                    "user_id": str(user_id),
                    "resource": resource,
                    "permission": permission
                }
            )
        
        return has_permission
    
    async def create_session(
        self,
        user: User,
        context: SecurityContext,
        session: AsyncSession
    ) -> Dict[str, str]:
        """Create secure session for user"""
        
        # Get user permissions and roles
        permissions = await self._get_user_permissions(user.id, session)
        roles = await self._get_user_roles(user.id, session)
        
        # Create tokens
        access_token = self.token_manager.create_access_token(
            user.id, permissions, roles
        )
        refresh_token = self.token_manager.create_refresh_token(user.id)
        
        # Store session info
        session_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.token_manager.access_token_expire
        }
        
        return session_data
    
    async def validate_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate JWT token"""
        
        try:
            payload = self.token_manager.decode_token(token)
            
            # Check if token is blacklisted
            if self.token_manager.is_token_blacklisted(token):
                return False, None
            
            return True, payload
        
        except AuthenticationError:
            return False, None
    
    async def change_password(
        self,
        user_id: UUID,
        old_password: str,
        new_password: str,
        context: SecurityContext,
        session: AsyncSession
    ) -> Tuple[bool, List[str]]:
        """Change user password with security validation"""
        
        errors = []
        
        # Get user
        user_result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            errors.append("User not found")
            return False, errors
        
        # Verify old password
        if not self.password_policy.verify_password(old_password, user.password_hash):
            errors.append("Current password is incorrect")
            await self._log_security_event(
                SecurityEventType.PASSWORD_CHANGE,
                context,
                {"user_id": str(user_id), "success": False, "reason": "invalid_old_password"}
            )
            return False, errors
        
        # Validate new password
        is_valid, validation_errors = self.password_policy.validate_password(new_password, user_id)
        if not is_valid:
            errors.extend(validation_errors)
            return False, errors
        
        # Check password history (prevent reuse)
        # In production, would check against password history table
        
        # Update password
        user.password_hash = self.password_policy.hash_password(new_password)
        user.password_changed_at = datetime.utcnow()
        user.password_expires_at = datetime.utcnow() + timedelta(days=self.password_policy.max_age_days)
        
        await self._log_security_event(
            SecurityEventType.PASSWORD_CHANGE,
            context,
            {"user_id": str(user_id), "success": True}
        )
        
        return True, []
    
    async def _get_user_permissions(self, user_id: UUID, session: AsyncSession) -> Set[str]:
        """Get user permissions"""
        return await self.permission_manager._get_user_permissions(user_id, session)
    
    async def _get_user_roles(self, user_id: UUID, session: AsyncSession) -> Set[str]:
        """Get user roles"""
        roles_result = await session.execute(
            select(UserRole.role_name).where(UserRole.user_id == user_id)
        )
        return {role[0] for role in roles_result.fetchall()}
    
    async def _log_security_event(
        self,
        event_type: SecurityEventType,
        context: SecurityContext,
        details: Dict[str, Any]
    ):
        """Log security event"""
        
        await self.audit_service.log_event(
            event_type=event_type.value,
            entity_type="security",
            entity_id=context.user_id,
            user_id=context.user_id,
            details={
                **details,
                "ip_address": context.ip_address,
                "user_agent": context.user_agent,
                "session_id": context.session_id
            }
        )
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics"""
        
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        
        # Calculate metrics from detected threats
        recent_threats = [
            t for t in self.threat_detector.detected_threats
            if t.detected_at > last_24h
        ]
        
        threat_counts = {}
        for threat in recent_threats:
            threat_counts[threat.threat_type] = threat_counts.get(threat.threat_type, 0) + 1
        
        return {
            "total_threats_24h": len(recent_threats),
            "threat_breakdown": threat_counts,
            "critical_threats": len([t for t in recent_threats if t.threat_level == ThreatLevel.CRITICAL]),
            "high_threats": len([t for t in recent_threats if t.threat_level == ThreatLevel.HIGH]),
            "active_sessions": 0,  # Would count from session storage
            "failed_logins_24h": len([t for t in recent_threats if t.threat_type == "login_failure"]),
            "metrics_generated_at": now.isoformat()
        }

# Singleton instance
security_manager = AdvancedSecurityManager({
    'password_policy': {
        'min_length': 8,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_digits': True,
        'require_special': True,
        'password_history': 5,
        'max_age_days': 90
    }
})

# Helper functions
async def authenticate_user(
    username: str,
    password: str,
    ip_address: str = None,
    user_agent: str = None,
    session: AsyncSession = None
) -> Tuple[bool, Optional[User], List[str]]:
    """Authenticate user"""
    context = SecurityContext(
        ip_address=ip_address,
        user_agent=user_agent
    )
    return await security_manager.authenticate_user(username, password, context, session)

async def authorize_user_access(
    user_id: UUID,
    resource: str,
    permission: str,
    session: AsyncSession
) -> bool:
    """Check user authorization"""
    context = SecurityContext(user_id=user_id)
    return await security_manager.authorize_access(user_id, resource, permission, context, session)

async def create_user_session(
    user: User,
    ip_address: str = None,
    user_agent: str = None,
    session: AsyncSession = None
) -> Dict[str, str]:
    """Create user session"""
    context = SecurityContext(
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    return await security_manager.create_session(user, context, session)