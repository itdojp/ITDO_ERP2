"""Enterprise Authentication & Access Control System - CC02 v73.0 Day 18."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import secrets
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import jwt
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from pydantic import BaseModel, Field

from ..sdk.mobile_sdk_core import AuthToken, DeviceInfo
from ..sdk.mobile_sdk_auth import AuthSecurityModule, SecurityPolicy


class AuthenticationMethod(str, Enum):
    """Supported authentication methods."""
    PASSWORD = "password"
    BIOMETRIC = "biometric"
    MFA_TOTP = "mfa_totp"
    MFA_SMS = "mfa_sms"
    MFA_EMAIL = "mfa_email"
    SAML_SSO = "saml_sso"
    OAUTH2 = "oauth2"
    LDAP = "ldap"
    SMART_CARD = "smart_card"
    CERTIFICATE = "certificate"


class AccessControlModel(str, Enum):
    """Access control models."""
    RBAC = "rbac"  # Role-Based Access Control
    ABAC = "abac"  # Attribute-Based Access Control
    MAC = "mac"    # Mandatory Access Control
    DAC = "dac"    # Discretionary Access Control


class SecurityClassification(str, Enum):
    """Security classification levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"


class AuthenticationFactor(BaseModel):
    """Authentication factor configuration."""
    factor_type: str
    required: bool = False
    priority: int = 1
    timeout_seconds: int = 300
    max_attempts: int = 3
    configuration: Dict[str, Any] = Field(default_factory=dict)


class EnterpriseRole(BaseModel):
    """Enterprise role definition."""
    role_id: str
    name: str
    description: str
    parent_role: Optional[str] = None
    permissions: Set[str] = Field(default_factory=set)
    resource_scopes: Dict[str, Set[str]] = Field(default_factory=dict)
    
    # Security attributes
    security_clearance: SecurityClassification = SecurityClassification.INTERNAL
    allowed_locations: Set[str] = Field(default_factory=set)
    allowed_times: Dict[str, str] = Field(default_factory=dict)  # day: time_range
    
    # Role constraints
    max_concurrent_sessions: int = 5
    session_timeout_minutes: int = 480  # 8 hours
    requires_mfa: bool = False
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


class EnterprisePermission(BaseModel):
    """Enterprise permission definition."""
    permission_id: str
    name: str
    description: str
    resource_type: str
    action: str  # create, read, update, delete, execute, approve
    
    # Permission constraints
    conditions: Dict[str, Any] = Field(default_factory=dict)
    data_filters: Dict[str, Any] = Field(default_factory=dict)
    time_restrictions: Dict[str, Any] = Field(default_factory=dict)
    
    # Delegation
    delegatable: bool = False
    max_delegation_depth: int = 0


class UserIdentity(BaseModel):
    """Enterprise user identity."""
    user_id: str
    username: str
    email: str
    employee_id: Optional[str] = None
    
    # Personal information
    first_name: str
    last_name: str
    display_name: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    manager_id: Optional[str] = None
    
    # Authentication configuration
    primary_auth_method: AuthenticationMethod = AuthenticationMethod.PASSWORD
    enabled_auth_methods: Set[AuthenticationMethod] = Field(default_factory=set)
    password_hash: Optional[str] = None
    password_salt: Optional[str] = None
    
    # Security attributes
    security_clearance: SecurityClassification = SecurityClassification.INTERNAL
    roles: Set[str] = Field(default_factory=set)
    direct_permissions: Set[str] = Field(default_factory=set)
    
    # Account status
    active: bool = True
    locked: bool = False
    password_expired: bool = False
    must_change_password: bool = False
    
    # Audit information
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    last_password_change: Optional[datetime] = None
    failed_login_attempts: int = 0
    last_failed_login: Optional[datetime] = None


class AuthenticationSession(BaseModel):
    """Enterprise authentication session."""
    session_id: str
    user_id: str
    device_id: str
    
    # Session state
    authenticated: bool = False
    authentication_methods: Set[AuthenticationMethod] = Field(default_factory=set)
    mfa_completed: bool = False
    
    # Session security
    ip_address: str
    user_agent: str
    location: Optional[Dict[str, Any]] = None
    risk_score: float = 0.0
    trust_level: str = "low"  # low, medium, high
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    expires_at: datetime
    
    # Context
    organization_id: str
    effective_roles: Set[str] = Field(default_factory=set)
    effective_permissions: Set[str] = Field(default_factory=set)
    security_context: Dict[str, Any] = Field(default_factory=dict)


class AccessDecision(BaseModel):
    """Access control decision."""
    granted: bool
    reason: str
    required_conditions: List[str] = Field(default_factory=list)
    
    # Decision context
    evaluated_policies: List[str] = Field(default_factory=list)
    applied_constraints: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    
    # Audit trail
    decision_time: datetime = Field(default_factory=datetime.now)
    decision_id: str = Field(default_factory=lambda: secrets.token_hex(8))


class EnterpriseAuthenticationProvider(ABC):
    """Abstract enterprise authentication provider."""
    
    @abstractmethod
    async def authenticate(
        self,
        credentials: Dict[str, Any],
        session: AuthenticationSession
    ) -> Tuple[bool, Dict[str, Any]]:
        """Authenticate user with provider."""
        pass
    
    @abstractmethod
    async def validate_session(self, session: AuthenticationSession) -> bool:
        """Validate existing session."""
        pass
    
    @abstractmethod
    async def refresh_token(self, session: AuthenticationSession) -> Optional[AuthToken]:
        """Refresh authentication token."""
        pass


class LDAPAuthenticationProvider(EnterpriseAuthenticationProvider):
    """LDAP authentication provider."""
    
    def __init__(self, ldap_config: Dict[str, Any]):
        self.server_url = ldap_config["server_url"]
        self.base_dn = ldap_config["base_dn"]
        self.bind_user = ldap_config.get("bind_user")
        self.bind_password = ldap_config.get("bind_password")
        self.user_search_filter = ldap_config.get("user_search_filter", "(uid={username})")
        
    async def authenticate(
        self,
        credentials: Dict[str, Any],
        session: AuthenticationSession
    ) -> Tuple[bool, Dict[str, Any]]:
        """Authenticate against LDAP directory."""
        username = credentials.get("username")
        password = credentials.get("password")
        
        if not username or not password:
            return False, {"error": "Username and password required"}
        
        try:
            # Simulate LDAP authentication
            # In real implementation, would use python-ldap library
            user_dn = f"uid={username},{self.base_dn}"
            
            # Mock successful authentication
            if username and password:
                user_attributes = {
                    "dn": user_dn,
                    "uid": username,
                    "email": f"{username}@company.com",
                    "displayName": f"User {username}",
                    "department": "Engineering",
                    "title": "Software Engineer",
                }
                
                return True, {"user_attributes": user_attributes}
            
            return False, {"error": "Invalid credentials"}
            
        except Exception as e:
            return False, {"error": f"LDAP authentication failed: {str(e)}"}
    
    async def validate_session(self, session: AuthenticationSession) -> bool:
        """Validate LDAP session."""
        # Check if session is still valid
        return (
            session.expires_at > datetime.now() and
            AuthenticationMethod.LDAP in session.authentication_methods
        )
    
    async def refresh_token(self, session: AuthenticationSession) -> Optional[AuthToken]:
        """LDAP doesn't typically support token refresh."""
        return None


class SAMLSSOProvider(EnterpriseAuthenticationProvider):
    """SAML SSO authentication provider."""
    
    def __init__(self, saml_config: Dict[str, Any]):
        self.idp_url = saml_config["idp_url"]
        self.sp_entity_id = saml_config["sp_entity_id"]
        self.certificate = saml_config.get("certificate")
        self.private_key = saml_config.get("private_key")
        
    async def authenticate(
        self,
        credentials: Dict[str, Any],
        session: AuthenticationSession
    ) -> Tuple[bool, Dict[str, Any]]:
        """Process SAML authentication response."""
        saml_response = credentials.get("saml_response")
        
        if not saml_response:
            return False, {"error": "SAML response required"}
        
        try:
            # Simplified SAML response validation
            # In real implementation, would use python3-saml library
            
            # Mock successful SAML authentication
            user_attributes = {
                "name_id": "user@company.com",
                "email": "user@company.com",
                "first_name": "John",
                "last_name": "Doe",
                "department": "Finance",
                "role": "manager",
            }
            
            return True, {"user_attributes": user_attributes}
            
        except Exception as e:
            return False, {"error": f"SAML validation failed: {str(e)}"}
    
    async def validate_session(self, session: AuthenticationSession) -> bool:
        """Validate SAML session."""
        return (
            session.expires_at > datetime.now() and
            AuthenticationMethod.SAML_SSO in session.authentication_methods
        )
    
    async def refresh_token(self, session: AuthenticationSession) -> Optional[AuthToken]:
        """SAML sessions typically don't support refresh."""
        return None


class OAuthProvider(EnterpriseAuthenticationProvider):
    """OAuth2/OpenID Connect provider."""
    
    def __init__(self, oauth_config: Dict[str, Any]):
        self.client_id = oauth_config["client_id"]
        self.client_secret = oauth_config["client_secret"]
        self.authorization_url = oauth_config["authorization_url"]
        self.token_url = oauth_config["token_url"]
        self.userinfo_url = oauth_config.get("userinfo_url")
        self.scopes = oauth_config.get("scopes", ["openid", "profile", "email"])
        
    async def authenticate(
        self,
        credentials: Dict[str, Any],
        session: AuthenticationSession
    ) -> Tuple[bool, Dict[str, Any]]:
        """Process OAuth authorization code."""
        auth_code = credentials.get("authorization_code")
        
        if not auth_code:
            return False, {"error": "Authorization code required"}
        
        try:
            # Exchange authorization code for access token
            # Mock token exchange
            access_token = secrets.token_urlsafe(32)
            id_token = self._create_mock_id_token()
            
            # Get user information
            user_info = await self._get_user_info(access_token)
            
            return True, {
                "access_token": access_token,
                "id_token": id_token,
                "user_info": user_info,
            }
            
        except Exception as e:
            return False, {"error": f"OAuth authentication failed: {str(e)}"}
    
    def _create_mock_id_token(self) -> str:
        """Create mock ID token for testing."""
        payload = {
            "iss": "https://auth.company.com",
            "sub": "user123",
            "aud": self.client_id,
            "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.now().timestamp()),
            "email": "user@company.com",
            "name": "John Doe",
        }
        
        # Use HS256 for simplicity (real implementation would use RS256)
        return jwt.encode(payload, self.client_secret, algorithm="HS256")
    
    async def _get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from OAuth provider."""
        # Mock user info response
        return {
            "sub": "user123",
            "email": "user@company.com",
            "email_verified": True,
            "name": "John Doe",
            "given_name": "John",
            "family_name": "Doe",
            "picture": "https://example.com/avatar.jpg",
        }
    
    async def validate_session(self, session: AuthenticationSession) -> bool:
        """Validate OAuth session."""
        return (
            session.expires_at > datetime.now() and
            AuthenticationMethod.OAUTH2 in session.authentication_methods
        )
    
    async def refresh_token(self, session: AuthenticationSession) -> Optional[AuthToken]:
        """Refresh OAuth access token."""
        # Mock token refresh
        new_token = AuthToken(
            access_token=secrets.token_urlsafe(32),
            token_type="Bearer",
            expires_at=datetime.now() + timedelta(hours=1),
        )
        
        return new_token


class RoleBasedAccessControl:
    """Role-Based Access Control (RBAC) implementation."""
    
    def __init__(self):
        self.roles: Dict[str, EnterpriseRole] = {}
        self.permissions: Dict[str, EnterprisePermission] = {}
        self.role_hierarchy: Dict[str, Set[str]] = {}  # parent -> children
        
    def define_role(self, role: EnterpriseRole) -> None:
        """Define a new role."""
        self.roles[role.role_id] = role
        
        # Build role hierarchy
        if role.parent_role:
            if role.parent_role not in self.role_hierarchy:
                self.role_hierarchy[role.parent_role] = set()
            self.role_hierarchy[role.parent_role].add(role.role_id)
    
    def define_permission(self, permission: EnterprisePermission) -> None:
        """Define a new permission."""
        self.permissions[permission.permission_id] = permission
    
    def assign_permission_to_role(self, role_id: str, permission_id: str) -> None:
        """Assign permission to role."""
        if role_id in self.roles and permission_id in self.permissions:
            self.roles[role_id].permissions.add(permission_id)
    
    def get_effective_permissions(self, role_ids: Set[str]) -> Set[str]:
        """Get all effective permissions for given roles."""
        effective_permissions = set()
        
        for role_id in role_ids:
            role = self.roles.get(role_id)
            if role:
                # Add direct permissions
                effective_permissions.update(role.permissions)
                
                # Add inherited permissions from parent roles
                parent_permissions = self._get_inherited_permissions(role_id)
                effective_permissions.update(parent_permissions)
        
        return effective_permissions
    
    def _get_inherited_permissions(self, role_id: str) -> Set[str]:
        """Get permissions inherited from parent roles."""
        inherited_permissions = set()
        role = self.roles.get(role_id)
        
        if role and role.parent_role:
            parent_role = self.roles.get(role.parent_role)
            if parent_role:
                inherited_permissions.update(parent_role.permissions)
                # Recursively get permissions from grandparent roles
                inherited_permissions.update(self._get_inherited_permissions(role.parent_role))
        
        return inherited_permissions
    
    def check_permission(
        self,
        user_roles: Set[str],
        required_permission: str,
        resource_context: Optional[Dict[str, Any]] = None
    ) -> AccessDecision:
        """Check if user has required permission."""
        effective_permissions = self.get_effective_permissions(user_roles)
        
        if required_permission not in effective_permissions:
            return AccessDecision(
                granted=False,
                reason=f"Permission {required_permission} not granted to user roles"
            )
        
        # Check permission conditions
        permission = self.permissions.get(required_permission)
        if permission and permission.conditions:
            condition_met = self._evaluate_permission_conditions(
                permission.conditions,
                resource_context or {}
            )
            
            if not condition_met:
                return AccessDecision(
                    granted=False,
                    reason=f"Permission conditions not met for {required_permission}"
                )
        
        return AccessDecision(
            granted=True,
            reason=f"Permission {required_permission} granted"
        )
    
    def _evaluate_permission_conditions(
        self,
        conditions: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate permission conditions."""
        for condition_type, condition_value in conditions.items():
            if condition_type == "time_range":
                current_time = datetime.now().time()
                start_time = datetime.strptime(condition_value["start"], "%H:%M").time()
                end_time = datetime.strptime(condition_value["end"], "%H:%M").time()
                
                if not (start_time <= current_time <= end_time):
                    return False
            
            elif condition_type == "location":
                user_location = context.get("location", {}).get("country")
                allowed_locations = condition_value.get("allowed_countries", [])
                
                if user_location and allowed_locations and user_location not in allowed_locations:
                    return False
            
            elif condition_type == "data_classification":
                resource_classification = context.get("data_classification")
                max_classification = condition_value.get("max_classification")
                
                if resource_classification and max_classification:
                    # Check if user can access this classification level
                    classification_levels = [
                        SecurityClassification.PUBLIC,
                        SecurityClassification.INTERNAL,
                        SecurityClassification.CONFIDENTIAL,
                        SecurityClassification.RESTRICTED,
                        SecurityClassification.TOP_SECRET,
                    ]
                    
                    resource_level = classification_levels.index(SecurityClassification(resource_classification))
                    max_level = classification_levels.index(SecurityClassification(max_classification))
                    
                    if resource_level > max_level:
                        return False
        
        return True


class EnterpriseAuthenticationSystem:
    """Enterprise authentication and access control system."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.users: Dict[str, UserIdentity] = {}
        self.sessions: Dict[str, AuthenticationSession] = {}
        self.rbac = RoleBasedAccessControl()
        
        # Authentication providers
        self.auth_providers: Dict[AuthenticationMethod, EnterpriseAuthenticationProvider] = {}
        
        # Security policies
        self.security_policy = SecurityPolicy()
        self.failed_attempts: Dict[str, List[datetime]] = {}
        
        # Initialize authentication providers
        self._initialize_auth_providers()
        
        # Setup default roles and permissions
        self._setup_default_rbac()
    
    def _initialize_auth_providers(self) -> None:
        """Initialize authentication providers."""
        # LDAP provider
        if "ldap" in self.config:
            self.auth_providers[AuthenticationMethod.LDAP] = LDAPAuthenticationProvider(
                self.config["ldap"]
            )
        
        # SAML SSO provider
        if "saml" in self.config:
            self.auth_providers[AuthenticationMethod.SAML_SSO] = SAMLSSOProvider(
                self.config["saml"]
            )
        
        # OAuth provider
        if "oauth" in self.config:
            self.auth_providers[AuthenticationMethod.OAUTH2] = OAuthProvider(
                self.config["oauth"]
            )
    
    def _setup_default_rbac(self) -> None:
        """Setup default RBAC roles and permissions."""
        # Define permissions
        permissions = [
            EnterprisePermission(
                permission_id="finance.read",
                name="Finance Read",
                description="Read financial data",
                resource_type="finance",
                action="read"
            ),
            EnterprisePermission(
                permission_id="finance.write",
                name="Finance Write",
                description="Create/update financial data",
                resource_type="finance",
                action="write"
            ),
            EnterprisePermission(
                permission_id="finance.approve",
                name="Finance Approve",
                description="Approve financial transactions",
                resource_type="finance",
                action="approve",
                conditions={
                    "time_range": {"start": "09:00", "end": "17:00"},
                    "data_classification": {"max_classification": "confidential"}
                }
            ),
            EnterprisePermission(
                permission_id="hr.employee.read",
                name="Employee Read",
                description="Read employee information",
                resource_type="employee",
                action="read"
            ),
            EnterprisePermission(
                permission_id="hr.employee.write",
                name="Employee Write",
                description="Create/update employee information",
                resource_type="employee",
                action="write"
            ),
            EnterprisePermission(
                permission_id="system.admin",
                name="System Administration",
                description="Full system administration access",
                resource_type="system",
                action="admin"
            ),
        ]
        
        for permission in permissions:
            self.rbac.define_permission(permission)
        
        # Define roles
        roles = [
            EnterpriseRole(
                role_id="finance_user",
                name="Finance User",
                description="Basic finance operations",
                permissions={"finance.read"},
                security_clearance=SecurityClassification.INTERNAL
            ),
            EnterpriseRole(
                role_id="finance_manager",
                name="Finance Manager",
                description="Finance management operations",
                parent_role="finance_user",
                permissions={"finance.write", "finance.approve"},
                security_clearance=SecurityClassification.CONFIDENTIAL,
                requires_mfa=True
            ),
            EnterpriseRole(
                role_id="hr_user",
                name="HR User",
                description="Basic HR operations",
                permissions={"hr.employee.read"},
                security_clearance=SecurityClassification.CONFIDENTIAL
            ),
            EnterpriseRole(
                role_id="hr_manager",
                name="HR Manager",
                description="HR management operations",
                parent_role="hr_user",
                permissions={"hr.employee.write"},
                security_clearance=SecurityClassification.CONFIDENTIAL,
                requires_mfa=True
            ),
            EnterpriseRole(
                role_id="system_admin",
                name="System Administrator",
                description="Full system administration",
                permissions={"system.admin"},
                security_clearance=SecurityClassification.RESTRICTED,
                requires_mfa=True,
                max_concurrent_sessions=2
            ),
        ]
        
        for role in roles:
            self.rbac.define_role(role)
    
    async def create_user(self, user_data: Dict[str, Any]) -> UserIdentity:
        """Create a new enterprise user."""
        user = UserIdentity(
            user_id=user_data["user_id"],
            username=user_data["username"],
            email=user_data["email"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            department=user_data.get("department"),
            job_title=user_data.get("job_title"),
            security_clearance=SecurityClassification(
                user_data.get("security_clearance", "internal")
            ),
            roles=set(user_data.get("roles", [])),
        )
        
        # Set password if provided
        if "password" in user_data:
            await self._set_user_password(user, user_data["password"])
        
        self.users[user.user_id] = user
        return user
    
    async def _set_user_password(self, user: UserIdentity, password: str) -> None:
        """Set user password with secure hashing."""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        
        user.password_salt = salt
        user.password_hash = password_hash.hex()
        user.last_password_change = datetime.now()
    
    async def authenticate_user(
        self,
        username: str,
        credentials: Dict[str, Any],
        device_info: DeviceInfo,
        auth_method: AuthenticationMethod = AuthenticationMethod.PASSWORD
    ) -> Tuple[bool, Optional[AuthenticationSession]]:
        """Authenticate user with specified method."""
        # Find user
        user = None
        for u in self.users.values():
            if u.username == username or u.email == username:
                user = u
                break
        
        if not user:
            return False, None
        
        # Check account status
        if not user.active or user.locked:
            return False, None
        
        # Check failed login attempts
        if not self._check_login_attempts(user.user_id):
            return False, None
        
        # Create authentication session
        session = AuthenticationSession(
            session_id=secrets.token_urlsafe(32),
            user_id=user.user_id,
            device_id=device_info.device_id,
            ip_address=credentials.get("ip_address", "unknown"),
            user_agent=credentials.get("user_agent", "unknown"),
            organization_id=credentials.get("organization_id", "default"),
            expires_at=datetime.now() + timedelta(hours=8),
        )
        
        # Authenticate with provider or built-in method
        auth_success = False
        auth_result = {}
        
        if auth_method in self.auth_providers:
            # Use external authentication provider
            provider = self.auth_providers[auth_method]
            auth_success, auth_result = await provider.authenticate(credentials, session)
        else:
            # Use built-in authentication
            auth_success, auth_result = await self._built_in_authenticate(
                user, credentials, auth_method
            )
        
        if auth_success:
            # Update session
            session.authenticated = True
            session.authentication_methods.add(auth_method)
            session.effective_roles = user.roles.copy()
            session.effective_permissions = self.rbac.get_effective_permissions(user.roles)
            
            # Calculate risk score and trust level
            session.risk_score = await self._calculate_risk_score(session, device_info)
            session.trust_level = self._determine_trust_level(session.risk_score)
            
            # Check if MFA is required
            mfa_required = await self._is_mfa_required(user, session)
            if mfa_required and auth_method != AuthenticationMethod.MFA_TOTP:
                session.authenticated = False  # Require MFA completion
            else:
                session.mfa_completed = True
            
            # Store session
            self.sessions[session.session_id] = session
            
            # Update user login info
            user.last_login = datetime.now()
            user.failed_login_attempts = 0
            
            return True, session
        else:
            # Record failed attempt
            user.failed_login_attempts += 1
            user.last_failed_login = datetime.now()
            
            # Lock account if too many failures
            if user.failed_login_attempts >= self.security_policy.lockout_threshold:
                user.locked = True
            
            return False, None
    
    async def _built_in_authenticate(
        self,
        user: UserIdentity,
        credentials: Dict[str, Any],
        auth_method: AuthenticationMethod
    ) -> Tuple[bool, Dict[str, Any]]:
        """Built-in authentication methods."""
        if auth_method == AuthenticationMethod.PASSWORD:
            password = credentials.get("password")
            if not password or not user.password_hash:
                return False, {"error": "Password required"}
            
            # Verify password
            password_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                user.password_salt.encode('utf-8'),
                100000
            )
            
            if hmac.compare_digest(user.password_hash, password_hash.hex()):
                return True, {}
            else:
                return False, {"error": "Invalid password"}
        
        elif auth_method == AuthenticationMethod.MFA_TOTP:
            totp_code = credentials.get("totp_code")
            if not totp_code:
                return False, {"error": "TOTP code required"}
            
            # Verify TOTP code (simplified)
            # In real implementation, would use proper TOTP library
            expected_code = self._generate_totp_code(user.user_id)
            if totp_code == expected_code:
                return True, {}
            else:
                return False, {"error": "Invalid TOTP code"}
        
        return False, {"error": f"Unsupported authentication method: {auth_method}"}
    
    def _generate_totp_code(self, user_id: str) -> str:
        """Generate TOTP code for testing."""
        # Simplified TOTP generation for testing
        timestamp = int(time.time()) // 30
        secret = f"secret_{user_id}"
        
        hmac_hash = hmac.new(
            secret.encode(),
            timestamp.to_bytes(8, byteorder='big'),
            hashlib.sha1
        ).digest()
        
        offset = hmac_hash[-1] & 0xf
        code = ((hmac_hash[offset] & 0x7f) << 24 |
                (hmac_hash[offset + 1] & 0xff) << 16 |
                (hmac_hash[offset + 2] & 0xff) << 8 |
                (hmac_hash[offset + 3] & 0xff))
        
        return str(code % 1000000).zfill(6)
    
    def _check_login_attempts(self, user_id: str) -> bool:
        """Check if user has exceeded login attempt limits."""
        if user_id not in self.failed_attempts:
            return True
        
        # Clean old attempts
        cutoff_time = datetime.now() - timedelta(minutes=self.security_policy.lockout_duration_minutes)
        self.failed_attempts[user_id] = [
            attempt for attempt in self.failed_attempts[user_id]
            if attempt > cutoff_time
        ]
        
        return len(self.failed_attempts[user_id]) < self.security_policy.lockout_threshold
    
    async def _calculate_risk_score(
        self,
        session: AuthenticationSession,
        device_info: DeviceInfo
    ) -> float:
        """Calculate authentication risk score."""
        risk_score = 0.0
        
        # Device risk factors
        if not device_info.device_id:
            risk_score += 0.3
        
        # Location risk (simplified)
        if session.ip_address == "unknown":
            risk_score += 0.2
        
        # Time-based risk
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:  # Outside business hours
            risk_score += 0.1
        
        # Authentication method risk
        if AuthenticationMethod.PASSWORD in session.authentication_methods:
            if not session.mfa_completed:
                risk_score += 0.3
        
        return min(1.0, risk_score)
    
    def _determine_trust_level(self, risk_score: float) -> str:
        """Determine trust level based on risk score."""
        if risk_score <= 0.3:
            return "high"
        elif risk_score <= 0.6:
            return "medium"
        else:
            return "low"
    
    async def _is_mfa_required(self, user: UserIdentity, session: AuthenticationSession) -> bool:
        """Check if MFA is required for user/session."""
        # Check user roles for MFA requirement
        for role_id in user.roles:
            role = self.rbac.roles.get(role_id)
            if role and role.requires_mfa:
                return True
        
        # Check risk-based MFA
        if session.risk_score > 0.5:
            return True
        
        # Check security classification
        if user.security_clearance in [SecurityClassification.CONFIDENTIAL, SecurityClassification.RESTRICTED]:
            return True
        
        return False
    
    async def check_access(
        self,
        session_id: str,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AccessDecision:
        """Check if session has access to perform action on resource."""
        session = self.sessions.get(session_id)
        if not session or not session.authenticated:
            return AccessDecision(
                granted=False,
                reason="Session not found or not authenticated"
            )
        
        # Check session validity
        if session.expires_at <= datetime.now():
            return AccessDecision(
                granted=False,
                reason="Session expired"
            )
        
        # Check permission
        required_permission = f"{resource}.{action}"
        decision = self.rbac.check_permission(
            session.effective_roles,
            required_permission,
            context
        )
        
        # Additional security checks
        if decision.granted:
            # Check trust level requirements
            if context and context.get("requires_high_trust") and session.trust_level != "high":
                decision.granted = False
                decision.reason = "High trust level required"
            
            # Check security classification
            if context and "data_classification" in context:
                user = self.users.get(session.user_id)
                if user:
                    resource_classification = SecurityClassification(context["data_classification"])
                    if user.security_clearance.value < resource_classification.value:
                        decision.granted = False
                        decision.reason = "Insufficient security clearance"
        
        # Update session activity
        session.last_activity = datetime.now()
        
        return decision
    
    async def complete_mfa(
        self,
        session_id: str,
        mfa_method: AuthenticationMethod,
        mfa_credentials: Dict[str, Any]
    ) -> bool:
        """Complete MFA for session."""
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        user = self.users.get(session.user_id)
        if not user:
            return False
        
        # Verify MFA
        auth_success, _ = await self._built_in_authenticate(
            user, mfa_credentials, mfa_method
        )
        
        if auth_success:
            session.authentication_methods.add(mfa_method)
            session.mfa_completed = True
            session.authenticated = True
            
            # Recalculate risk score
            session.risk_score = await self._calculate_risk_score(session, None)
            session.trust_level = self._determine_trust_level(session.risk_score)
            
            return True
        
        return False
    
    async def logout_session(self, session_id: str) -> bool:
        """Logout and invalidate session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information."""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "authenticated": session.authenticated,
            "mfa_completed": session.mfa_completed,
            "trust_level": session.trust_level,
            "risk_score": session.risk_score,
            "expires_at": session.expires_at.isoformat(),
            "effective_roles": list(session.effective_roles),
            "authentication_methods": list(session.authentication_methods),
        }
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information."""
        user = self.users.get(user_id)
        if not user:
            return None
        
        return {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name or f"{user.first_name} {user.last_name}",
            "department": user.department,
            "job_title": user.job_title,
            "roles": list(user.roles),
            "security_clearance": user.security_clearance,
            "active": user.active,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        }