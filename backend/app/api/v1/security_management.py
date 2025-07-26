"""
CC02 v55.0 Security Management API
Enterprise-grade Security Administration and Monitoring System
Day 3 of 7-day intensive backend development
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, validator
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.security import (
    ApiKey,
    LoginAttempt,
    RolePermission,
    SecurityAlert,
    SecurityAudit,
    SecurityPolicy,
    TwoFactorAuth,
    UserRole,
)
from app.services.advanced_security import (
    AuthenticationMethod,
    SecurityContext,
    SecurityLevel,
    ThreatLevel,
    security_manager,
)

router = APIRouter(prefix="/security", tags=["security-management"])
security_scheme = HTTPBearer()


# Request/Response Models
class SecurityPolicyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    policy_type: str = Field(..., regex="^(password|access|session|audit)$")
    rules: Dict[str, Any] = Field(default_factory=dict)
    is_enforced: bool = Field(default=True)
    severity_level: SecurityLevel = Field(default=SecurityLevel.AUTHENTICATED)


class SecurityPolicyResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    policy_type: str
    rules: Dict[str, Any]
    is_enforced: bool
    severity_level: SecurityLevel
    violations_count: int
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permissions: List[str] = Field(default_factory=list)
    is_system_role: bool = Field(default=False)


class RoleResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    permissions: List[str]
    user_count: int
    is_system_role: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PermissionCreate(BaseModel):
    resource: str = Field(..., min_length=1, max_length=100)
    action: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)


class PermissionResponse(BaseModel):
    id: UUID
    resource: str
    action: str
    description: Optional[str]
    full_permission: str
    granted_roles: List[str]
    granted_users: List[str]

    class Config:
        from_attributes = True


class SecurityAlertCreate(BaseModel):
    alert_type: str = Field(..., min_length=1, max_length=50)
    severity: ThreatLevel
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    source_ip: Optional[str] = Field(None, max_length=45)
    affected_user_id: Optional[UUID] = None
    alert_data: Dict[str, Any] = Field(default_factory=dict)


class SecurityAlertResponse(BaseModel):
    id: UUID
    alert_type: str
    severity: ThreatLevel
    title: str
    description: str
    source_ip: Optional[str]
    affected_user_id: Optional[UUID]
    affected_user_name: Optional[str]
    alert_data: Dict[str, Any]
    status: str
    acknowledged: bool
    acknowledged_by: Optional[UUID]
    acknowledged_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class LoginAttemptResponse(BaseModel):
    id: UUID
    username: str
    ip_address: str
    user_agent: Optional[str]
    success: bool
    failure_reason: Optional[str]
    geolocation: Optional[Dict[str, Any]]
    attempted_at: datetime

    class Config:
        from_attributes = True


class SecurityAuditResponse(BaseModel):
    id: UUID
    event_type: str
    user_id: Optional[UUID]
    user_name: Optional[str]
    resource: str
    action: str
    ip_address: Optional[str]
    success: bool
    details: Dict[str, Any]
    risk_score: int
    created_at: datetime

    class Config:
        from_attributes = True


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @validator("confirm_password")
    def passwords_match(cls, v, values) -> dict:
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class TwoFactorSetupRequest(BaseModel):
    method: AuthenticationMethod = Field(default=AuthenticationMethod.TWO_FACTOR)
    phone_number: Optional[str] = Field(None, max_length=20)
    backup_codes_count: int = Field(default=10, ge=5, le=20)


class TwoFactorResponse(BaseModel):
    enabled: bool
    method: AuthenticationMethod
    backup_codes: Optional[List[str]]
    qr_code_url: Optional[str]
    secret_key: Optional[str]

    class Config:
        from_attributes = True


class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permissions: List[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None
    rate_limit: int = Field(default=1000, ge=1, le=10000)


class ApiKeyResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    key_prefix: str
    permissions: List[str]
    expires_at: Optional[datetime]
    rate_limit: int
    usage_count: int
    last_used: Optional[datetime]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Helper Functions
async def get_current_security_context(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> SecurityContext:
    """Get current security context from token"""

    token = credentials.credentials
    is_valid, payload = await security_manager.validate_token(token)

    if not is_valid or not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    user_id = UUID(payload.get("user_id"))
    permissions = set(payload.get("permissions", []))
    roles = set(payload.get("roles", []))

    return SecurityContext(
        user_id=user_id,
        permissions=permissions,
        roles=roles,
        security_level=SecurityLevel.AUTHENTICATED,
    )


async def require_permission(permission: str) -> dict:
    """Dependency to require specific permission"""

    async def permission_checker(
        context: SecurityContext = Depends(get_current_security_context),
    ):
        if permission not in context.permissions and "*" not in context.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required",
            )
        return context

    return permission_checker


# Security Policy Management
@router.post(
    "/policies",
    response_model=SecurityPolicyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_security_policy(
    policy: SecurityPolicyCreate,
    db: AsyncSession = Depends(get_db),
    context: SecurityContext = Depends(require_permission("security:admin")),
):
    """Create a new security policy"""

    db_policy = SecurityPolicy(
        id=uuid4(),
        name=policy.name,
        description=policy.description,
        policy_type=policy.policy_type,
        rules=policy.rules,
        is_enforced=policy.is_enforced,
        severity_level=policy.severity_level,
        created_by=context.user_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(db_policy)
    await db.commit()
    await db.refresh(db_policy)

    return SecurityPolicyResponse(
        id=db_policy.id,
        name=db_policy.name,
        description=db_policy.description,
        policy_type=db_policy.policy_type,
        rules=db_policy.rules,
        is_enforced=db_policy.is_enforced,
        severity_level=db_policy.severity_level,
        violations_count=0,
        created_by=db_policy.created_by,
        created_at=db_policy.created_at,
        updated_at=db_policy.updated_at,
    )


@router.get("/policies", response_model=List[SecurityPolicyResponse])
async def list_security_policies(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    policy_type: Optional[str] = Query(None),
    is_enforced: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    context: SecurityContext = Depends(require_permission("security:read")),
):
    """List security policies"""

    query = select(SecurityPolicy)

    if policy_type:
        query = query.where(SecurityPolicy.policy_type == policy_type)

    if is_enforced is not None:
        query = query.where(SecurityPolicy.is_enforced == is_enforced)

    query = query.offset(skip).limit(limit).order_by(SecurityPolicy.created_at.desc())

    result = await db.execute(query)
    policies = result.scalars().all()

    return [
        SecurityPolicyResponse(
            id=policy.id,
            name=policy.name,
            description=policy.description,
            policy_type=policy.policy_type,
            rules=policy.rules,
            is_enforced=policy.is_enforced,
            severity_level=policy.severity_level,
            violations_count=0,  # Would calculate from audit logs
            created_by=policy.created_by,
            created_at=policy.created_at,
            updated_at=policy.updated_at,
        )
        for policy in policies
    ]


# Role Management
@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role: RoleCreate,
    db: AsyncSession = Depends(get_db),
    context: SecurityContext = Depends(require_permission("security:admin")),
):
    """Create a new role"""

    # Check if role name already exists
    existing = await db.execute(select(UserRole).where(UserRole.role_name == role.name))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Role name already exists"
        )

    role_id = uuid4()

    # Create role permissions
    for permission in role.permissions:
        parts = permission.split(":")
        if len(parts) != 2:
            continue

        resource, action = parts
        role_permission = RolePermission(
            id=uuid4(),
            role_id=role_id,
            resource=resource,
            permission=action,
            granted_by=context.user_id,
            granted_at=datetime.utcnow(),
        )
        db.add(role_permission)

    await db.commit()

    return RoleResponse(
        id=role_id,
        name=role.name,
        description=role.description,
        permissions=role.permissions,
        user_count=0,
        is_system_role=role.is_system_role,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    include_system: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    context: SecurityContext = Depends(require_permission("security:read")),
):
    """List roles"""

    # Get unique roles with user counts
    query = select(
        UserRole.role_name, func.count(UserRole.user_id).label("user_count")
    ).group_by(UserRole.role_name)

    if not include_system:
        # Would filter system roles if we had that field
        pass

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    roles_data = result.fetchall()

    roles = []
    for role_name, user_count in roles_data:
        # Get permissions for this role
        perms_result = await db.execute(
            select(RolePermission.resource, RolePermission.permission).where(
                RolePermission.role_id.in_(
                    select(UserRole.role_id).where(UserRole.role_name == role_name)
                )
            )
        )

        permissions = [
            f"{resource}:{permission}"
            for resource, permission in perms_result.fetchall()
        ]

        roles.append(
            RoleResponse(
                id=uuid4(),  # Would use actual role ID
                name=role_name,
                description=None,
                permissions=permissions,
                user_count=user_count,
                is_system_role=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )

    return roles


# Permission Management
@router.post(
    "/permissions",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_permission(
    permission: PermissionCreate,
    db: AsyncSession = Depends(get_db),
    context: SecurityContext = Depends(require_permission("security:admin")),
):
    """Create a new permission"""

    permission_id = uuid4()
    full_permission = f"{permission.resource}:{permission.action}"

    return PermissionResponse(
        id=permission_id,
        resource=permission.resource,
        action=permission.action,
        description=permission.description,
        full_permission=full_permission,
        granted_roles=[],
        granted_users=[],
    )


@router.get("/permissions", response_model=List[PermissionResponse])
async def list_permissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    resource: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    context: SecurityContext = Depends(require_permission("security:read")),
):
    """List permissions"""

    query = select(RolePermission.resource, RolePermission.permission).distinct()

    if resource:
        query = query.where(RolePermission.resource == resource)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    permissions_data = result.fetchall()

    permissions = []
    for resource_name, action in permissions_data:
        permission_id = uuid4()
        full_permission = f"{resource_name}:{action}"

        # Get roles with this permission
        roles_result = await db.execute(
            select(UserRole.role_name)
            .distinct()
            .join(RolePermission)
            .where(
                and_(
                    RolePermission.resource == resource_name,
                    RolePermission.permission == action,
                )
            )
        )
        granted_roles = [role[0] for role in roles_result.fetchall()]

        permissions.append(
            PermissionResponse(
                id=permission_id,
                resource=resource_name,
                action=action,
                description=None,
                full_permission=full_permission,
                granted_roles=granted_roles,
                granted_users=[],
            )
        )

    return permissions


# Security Alerts
@router.post(
    "/alerts", response_model=SecurityAlertResponse, status_code=status.HTTP_201_CREATED
)
async def create_security_alert(
    alert: SecurityAlertCreate,
    db: AsyncSession = Depends(get_db),
    context: SecurityContext = Depends(require_permission("security:admin")),
):
    """Create a security alert"""

    db_alert = SecurityAlert(
        id=uuid4(),
        alert_type=alert.alert_type,
        severity=alert.severity,
        title=alert.title,
        description=alert.description,
        source_ip=alert.source_ip,
        affected_user_id=alert.affected_user_id,
        alert_data=alert.alert_data,
        status="open",
        acknowledged=False,
        created_at=datetime.utcnow(),
    )

    db.add(db_alert)
    await db.commit()
    await db.refresh(db_alert)

    return SecurityAlertResponse(
        id=db_alert.id,
        alert_type=db_alert.alert_type,
        severity=db_alert.severity,
        title=db_alert.title,
        description=db_alert.description,
        source_ip=db_alert.source_ip,
        affected_user_id=db_alert.affected_user_id,
        affected_user_name=None,
        alert_data=db_alert.alert_data,
        status=db_alert.status,
        acknowledged=db_alert.acknowledged,
        acknowledged_by=db_alert.acknowledged_by,
        acknowledged_at=db_alert.acknowledged_at,
        created_at=db_alert.created_at,
    )


@router.get("/alerts", response_model=List[SecurityAlertResponse])
async def list_security_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    severity: Optional[ThreatLevel] = Query(None),
    acknowledged: Optional[bool] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    context: SecurityContext = Depends(require_permission("security:read")),
):
    """List security alerts"""

    query = select(SecurityAlert)

    if severity:
        query = query.where(SecurityAlert.severity == severity)

    if acknowledged is not None:
        query = query.where(SecurityAlert.acknowledged == acknowledged)

    if date_from:
        query = query.where(SecurityAlert.created_at >= date_from)

    if date_to:
        query = query.where(SecurityAlert.created_at <= date_to)

    query = query.offset(skip).limit(limit).order_by(SecurityAlert.created_at.desc())

    result = await db.execute(query)
    alerts = result.scalars().all()

    return [
        SecurityAlertResponse(
            id=alert.id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            title=alert.title,
            description=alert.description,
            source_ip=alert.source_ip,
            affected_user_id=alert.affected_user_id,
            affected_user_name=None,
            alert_data=alert.alert_data,
            status=alert.status,
            acknowledged=alert.acknowledged,
            acknowledged_by=alert.acknowledged_by,
            acknowledged_at=alert.acknowledged_at,
            created_at=alert.created_at,
        )
        for alert in alerts
    ]


@router.patch("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    context: SecurityContext = Depends(require_permission("security:admin")),
):
    """Acknowledge a security alert"""

    alert_result = await db.execute(
        select(SecurityAlert).where(SecurityAlert.id == alert_id)
    )
    alert = alert_result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found"
        )

    alert.acknowledged = True
    alert.acknowledged_by = context.user_id
    alert.acknowledged_at = datetime.utcnow()

    await db.commit()

    return {"message": "Alert acknowledged successfully"}


# Login Attempts and Audit
@router.get("/login-attempts", response_model=List[LoginAttemptResponse])
async def list_login_attempts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    username: Optional[str] = Query(None),
    ip_address: Optional[str] = Query(None),
    success: Optional[bool] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    context: SecurityContext = Depends(require_permission("security:read")),
):
    """List login attempts"""

    query = select(LoginAttempt)

    if username:
        query = query.where(LoginAttempt.username.ilike(f"%{username}%"))

    if ip_address:
        query = query.where(LoginAttempt.ip_address == ip_address)

    if success is not None:
        query = query.where(LoginAttempt.success == success)

    if date_from:
        query = query.where(LoginAttempt.attempted_at >= date_from)

    if date_to:
        query = query.where(LoginAttempt.attempted_at <= date_to)

    query = query.offset(skip).limit(limit).order_by(LoginAttempt.attempted_at.desc())

    result = await db.execute(query)
    attempts = result.scalars().all()

    return [
        LoginAttemptResponse(
            id=attempt.id,
            username=attempt.username,
            ip_address=attempt.ip_address,
            user_agent=attempt.user_agent,
            success=attempt.success,
            failure_reason=attempt.failure_reason,
            geolocation=attempt.geolocation,
            attempted_at=attempt.attempted_at,
        )
        for attempt in attempts
    ]


@router.get("/audit-log", response_model=List[SecurityAuditResponse])
async def get_security_audit_log(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    user_id: Optional[UUID] = Query(None),
    event_type: Optional[str] = Query(None),
    resource: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    context: SecurityContext = Depends(require_permission("security:audit")),
):
    """Get security audit log"""

    query = select(SecurityAudit)

    if user_id:
        query = query.where(SecurityAudit.user_id == user_id)

    if event_type:
        query = query.where(SecurityAudit.event_type == event_type)

    if resource:
        query = query.where(SecurityAudit.resource == resource)

    if date_from:
        query = query.where(SecurityAudit.created_at >= date_from)

    if date_to:
        query = query.where(SecurityAudit.created_at <= date_to)

    query = query.offset(skip).limit(limit).order_by(SecurityAudit.created_at.desc())

    result = await db.execute(query)
    audits = result.scalars().all()

    return [
        SecurityAuditResponse(
            id=audit.id,
            event_type=audit.event_type,
            user_id=audit.user_id,
            user_name=None,  # Would load from user table
            resource=audit.resource,
            action=audit.action,
            ip_address=audit.ip_address,
            success=audit.success,
            details=audit.details,
            risk_score=audit.risk_score or 0,
            created_at=audit.created_at,
        )
        for audit in audits
    ]


# Password Management
@router.post("/password/change")
async def change_password(
    request: PasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
    context: SecurityContext = Depends(get_current_security_context),
):
    """Change user password"""

    success, errors = await security_manager.change_password(
        context.user_id, request.current_password, request.new_password, context, db
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail={"errors": errors}
        )

    return {"message": "Password changed successfully"}


# Two-Factor Authentication
@router.post("/2fa/setup", response_model=TwoFactorResponse)
async def setup_two_factor_auth(
    request: TwoFactorSetupRequest,
    db: AsyncSession = Depends(get_db),
    context: SecurityContext = Depends(get_current_security_context),
):
    """Setup two-factor authentication"""

    # Generate backup codes
    backup_codes = [secrets.token_hex(8) for _ in range(request.backup_codes_count)]

    # Generate TOTP secret
    secret_key = secrets.token_urlsafe(32)

    # Create 2FA record
    two_fa = TwoFactorAuth(
        id=uuid4(),
        user_id=context.user_id,
        method=request.method,
        secret_key=secret_key,
        backup_codes=backup_codes,
        phone_number=request.phone_number,
        enabled=True,
        created_at=datetime.utcnow(),
    )

    db.add(two_fa)
    await db.commit()

    # Generate QR code URL for TOTP
    qr_code_url = (
        f"otpauth://totp/ITDO_ERP:{context.user_id}?secret={secret_key}&issuer=ITDO_ERP"
    )

    return TwoFactorResponse(
        enabled=True,
        method=request.method,
        backup_codes=backup_codes,
        qr_code_url=qr_code_url,
        secret_key=secret_key,
    )


# API Key Management
@router.post(
    "/api-keys", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED
)
async def create_api_key(
    request: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    context: SecurityContext = Depends(require_permission("security:admin")),
):
    """Create a new API key"""

    # Generate API key
    key = f"itdo_{secrets.token_urlsafe(32)}"
    key_prefix = key[:12] + "..."

    db_key = ApiKey(
        id=uuid4(),
        name=request.name,
        description=request.description,
        key_hash=security_manager.password_policy.hash_password(key),
        key_prefix=key_prefix,
        permissions=request.permissions,
        expires_at=request.expires_at,
        rate_limit=request.rate_limit,
        usage_count=0,
        is_active=True,
        created_by=context.user_id,
        created_at=datetime.utcnow(),
    )

    db.add(db_key)
    await db.commit()
    await db.refresh(db_key)

    return ApiKeyResponse(
        id=db_key.id,
        name=db_key.name,
        description=db_key.description,
        key_prefix=db_key.key_prefix,
        permissions=db_key.permissions,
        expires_at=db_key.expires_at,
        rate_limit=db_key.rate_limit,
        usage_count=db_key.usage_count,
        last_used=db_key.last_used,
        is_active=db_key.is_active,
        created_at=db_key.created_at,
    )


@router.get("/api-keys", response_model=List[ApiKeyResponse])
async def list_api_keys(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    context: SecurityContext = Depends(require_permission("security:read")),
):
    """List API keys"""

    query = select(ApiKey)

    if is_active is not None:
        query = query.where(ApiKey.is_active == is_active)

    query = query.offset(skip).limit(limit).order_by(ApiKey.created_at.desc())

    result = await db.execute(query)
    keys = result.scalars().all()

    return [
        ApiKeyResponse(
            id=key.id,
            name=key.name,
            description=key.description,
            key_prefix=key.key_prefix,
            permissions=key.permissions,
            expires_at=key.expires_at,
            rate_limit=key.rate_limit,
            usage_count=key.usage_count,
            last_used=key.last_used,
            is_active=key.is_active,
            created_at=key.created_at,
        )
        for key in keys
    ]


# Security Metrics and Dashboard
@router.get("/metrics")
async def get_security_metrics(
    period_days: int = Query(7, ge=1, le=365),
    context: SecurityContext = Depends(require_permission("security:read")),
):
    """Get security metrics"""

    metrics = security_manager.get_security_metrics()

    return {
        "period_days": period_days,
        "metrics": metrics,
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/dashboard")
async def get_security_dashboard(
    db: AsyncSession = Depends(get_db),
    context: SecurityContext = Depends(require_permission("security:read")),
):
    """Get security dashboard data"""

    # Get recent alerts
    recent_alerts = await db.execute(
        select(SecurityAlert)
        .where(SecurityAlert.created_at >= datetime.utcnow() - timedelta(days=7))
        .order_by(SecurityAlert.created_at.desc())
        .limit(10)
    )

    # Get failed login attempts
    failed_logins = await db.execute(
        select(func.count(LoginAttempt.id)).where(
            and_(
                not LoginAttempt.success,
                LoginAttempt.attempted_at >= datetime.utcnow() - timedelta(hours=24),
            )
        )
    )

    # Get active sessions count (would be from session storage)
    active_sessions = 0

    return {
        "alerts": {
            "recent_count": len(recent_alerts.scalars().all()),
            "critical_count": 0,  # Would calculate
            "unacknowledged_count": 0,  # Would calculate
        },
        "authentication": {
            "failed_logins_24h": failed_logins.scalar() or 0,
            "active_sessions": active_sessions,
            "locked_accounts": 0,  # Would calculate
        },
        "threats": security_manager.get_security_metrics(),
        "compliance": {
            "password_policy_violations": 0,
            "inactive_users": 0,
            "expired_api_keys": 0,
        },
    }
