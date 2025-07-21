"""Advanced API Security & Protection API endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.core.advanced_api_security import (
    api_security,
    SecurityRule,
    RateLimitRule,
    ThreatType,
    BlockType,
    RateLimitScope,
    SecurityLevel,
    check_advanced_api_security_health,
)
from app.models.user import User

router = APIRouter()


# Pydantic schemas
class SecurityRuleRequest(BaseModel):
    """Security rule creation request."""
    name: str = Field(..., max_length=200)
    rule_type: ThreatType
    pattern: str = Field(..., max_length=1000)
    description: str = Field(..., max_length=500)
    severity: int = Field(5, ge=1, le=10)
    enabled: bool = True
    action: BlockType = BlockType.WARNING


class SecurityRuleResponse(BaseModel):
    """Security rule response."""
    id: str
    name: str
    rule_type: str
    pattern: str
    description: str
    severity: int
    enabled: bool
    action: str
    created_at: datetime

    class Config:
        from_attributes = True


class RateLimitRuleRequest(BaseModel):
    """Rate limit rule creation request."""
    name: str = Field(..., max_length=200)
    scope: RateLimitScope
    endpoint_pattern: str = Field(..., max_length=500)
    requests_per_minute: int = Field(..., ge=1, le=10000)
    requests_per_hour: int = Field(..., ge=1, le=100000)
    requests_per_day: int = Field(..., ge=1, le=1000000)
    burst_allowance: int = Field(0, ge=0, le=1000)
    whitelist_ips: List[str] = []
    enabled: bool = True


class RateLimitRuleResponse(BaseModel):
    """Rate limit rule response."""
    id: str
    name: str
    scope: str
    endpoint_pattern: str
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_allowance: int
    whitelist_ips: List[str]
    enabled: bool

    class Config:
        from_attributes = True


class SecurityAnalysisRequest(BaseModel):
    """Security analysis request."""
    ip_address: str = Field(..., max_length=45)
    endpoint: str = Field(..., max_length=500)
    method: str = Field(..., max_length=10)
    headers: Dict[str, str] = {}
    query_params: Dict[str, Any] = {}
    body: str = ""
    user_id: Optional[str] = None
    api_key: Optional[str] = None


class SecurityViolationResponse(BaseModel):
    """Security violation response."""
    id: str
    type: str
    severity: int
    blocked: bool
    details: Dict[str, Any]


class SecurityAnalysisResponse(BaseModel):
    """Security analysis response."""
    allowed: bool
    violations: List[SecurityViolationResponse]
    security_score: int
    rate_info: Dict[str, Any]
    reason: Optional[str] = None


class IPBlockRequest(BaseModel):
    """IP block request."""
    ip_address: str = Field(..., max_length=45)
    reason: str = Field(..., max_length=500)
    block_type: BlockType = BlockType.TEMPORARY
    duration_minutes: Optional[int] = Field(None, ge=1, le=43200)  # Max 30 days


class IPBlockResponse(BaseModel):
    """IP block response."""
    ip_address: str
    block_type: str
    reason: str
    blocked_at: datetime
    expires_at: Optional[datetime]
    violation_count: int

    class Config:
        from_attributes = True


class SecurityDashboardResponse(BaseModel):
    """Security dashboard response."""
    total_requests: int
    blocked_requests: int
    rate_limit_violations: int
    security_violations: int
    recent_violations_24h: int
    violation_types: Dict[str, int]
    blocked_ips: int
    active_rate_limits: int
    security_rules: int
    last_updated: str


class SecurityHealthResponse(BaseModel):
    """Security health response."""
    status: str
    dashboard: SecurityDashboardResponse
    pattern_detector_rules: int
    rate_limit_rules: int
    violation_history_size: int


# Security Rule Management Endpoints
@router.post("/rules", response_model=SecurityRuleResponse)
async def create_security_rule(
    rule_request: SecurityRuleRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new security rule."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        rule = SecurityRule(
            id="",  # Will be auto-generated
            name=rule_request.name,
            rule_type=rule_request.rule_type,
            pattern=rule_request.pattern,
            description=rule_request.description,
            severity=rule_request.severity,
            enabled=rule_request.enabled,
            action=rule_request.action
        )
        
        rule_id = await api_security.add_security_rule(rule)
        
        return SecurityRuleResponse(
            id=rule.id,
            name=rule.name,
            rule_type=rule.rule_type.value,
            pattern=rule.pattern,
            description=rule.description,
            severity=rule.severity,
            enabled=rule.enabled,
            action=rule.action.value,
            created_at=rule.created_at
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create security rule: {str(e)}"
        )


@router.get("/rules", response_model=List[SecurityRuleResponse])
async def list_security_rules(
    current_user: User = Depends(get_current_user)
):
    """List all security rules."""
    try:
        rules = api_security.pattern_detector.patterns
        
        return [
            SecurityRuleResponse(
                id=rule.id,
                name=rule.name,
                rule_type=rule.rule_type.value,
                pattern=rule.pattern,
                description=rule.description,
                severity=rule.severity,
                enabled=rule.enabled,
                action=rule.action.value,
                created_at=rule.created_at
            )
            for rule in rules
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve security rules: {str(e)}"
        )


# Rate Limit Management Endpoints
@router.post("/rate-limits", response_model=RateLimitRuleResponse)
async def create_rate_limit_rule(
    rule_request: RateLimitRuleRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new rate limit rule."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        rule = RateLimitRule(
            id="",  # Will be auto-generated
            name=rule_request.name,
            scope=rule_request.scope,
            endpoint_pattern=rule_request.endpoint_pattern,
            requests_per_minute=rule_request.requests_per_minute,
            requests_per_hour=rule_request.requests_per_hour,
            requests_per_day=rule_request.requests_per_day,
            burst_allowance=rule_request.burst_allowance,
            whitelist_ips=rule_request.whitelist_ips,
            enabled=rule_request.enabled
        )
        
        rule_id = await api_security.add_rate_limit_rule(rule)
        
        return RateLimitRuleResponse(
            id=rule.id,
            name=rule.name,
            scope=rule.scope.value,
            endpoint_pattern=rule.endpoint_pattern,
            requests_per_minute=rule.requests_per_minute,
            requests_per_hour=rule.requests_per_hour,
            requests_per_day=rule.requests_per_day,
            burst_allowance=rule.burst_allowance,
            whitelist_ips=rule.whitelist_ips,
            enabled=rule.enabled
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create rate limit rule: {str(e)}"
        )


@router.get("/rate-limits", response_model=List[RateLimitRuleResponse])
async def list_rate_limit_rules(
    current_user: User = Depends(get_current_user)
):
    """List all rate limit rules."""
    try:
        rules = api_security.rate_limit_manager.rules
        
        return [
            RateLimitRuleResponse(
                id=rule.id,
                name=rule.name,
                scope=rule.scope.value,
                endpoint_pattern=rule.endpoint_pattern,
                requests_per_minute=rule.requests_per_minute,
                requests_per_hour=rule.requests_per_hour,
                requests_per_day=rule.requests_per_day,
                burst_allowance=rule.burst_allowance,
                whitelist_ips=rule.whitelist_ips,
                enabled=rule.enabled
            )
            for rule in rules.values()
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve rate limit rules: {str(e)}"
        )


# Security Analysis Endpoints
@router.post("/analyze", response_model=SecurityAnalysisResponse)
async def analyze_request_security(
    analysis_request: SecurityAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Analyze request for security threats."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        result = await api_security.analyze_request(
            ip_address=analysis_request.ip_address,
            endpoint=analysis_request.endpoint,
            method=analysis_request.method,
            headers=analysis_request.headers,
            query_params=analysis_request.query_params,
            body=analysis_request.body,
            user_id=analysis_request.user_id,
            api_key=analysis_request.api_key
        )
        
        violations = [
            SecurityViolationResponse(
                id=v["id"],
                type=v["type"],
                severity=v["severity"],
                blocked=v["blocked"],
                details=v["details"]
            )
            for v in result.get("violations", [])
        ]
        
        return SecurityAnalysisResponse(
            allowed=result["allowed"],
            violations=violations,
            security_score=result.get("security_score", 100),
            rate_info=result.get("rate_info", {}),
            reason=result.get("reason")
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security analysis failed: {str(e)}"
        )


@router.post("/analyze/current")
async def analyze_current_request(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Analyze the current request for security threats."""
    try:
        # Extract request information
        client_ip = request.client.host if request.client else "127.0.0.1"
        endpoint = str(request.url.path)
        method = request.method
        headers = dict(request.headers)
        query_params = dict(request.query_params)
        
        # Get request body if available
        body = ""
        try:
            body_bytes = await request.body()
            body = body_bytes.decode('utf-8') if body_bytes else ""
        except:
            body = ""
        
        result = await api_security.analyze_request(
            ip_address=client_ip,
            endpoint=endpoint,
            method=method,
            headers=headers,
            query_params=query_params,
            body=body,
            user_id=str(current_user.id) if current_user else None
        )
        
        violations = [
            SecurityViolationResponse(
                id=v["id"],
                type=v["type"],
                severity=v["severity"],
                blocked=v["blocked"],
                details=v["details"]
            )
            for v in result.get("violations", [])
        ]
        
        return SecurityAnalysisResponse(
            allowed=result["allowed"],
            violations=violations,
            security_score=result.get("security_score", 100),
            rate_info=result.get("rate_info", {}),
            reason=result.get("reason")
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Current request analysis failed: {str(e)}"
        )


# IP Blocking Endpoints
@router.post("/ip-blocks", response_model=IPBlockResponse)
async def block_ip_address(
    block_request: IPBlockRequest,
    current_user: User = Depends(get_current_user)
):
    """Block an IP address."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        block = await api_security.ip_block_manager.block_ip(
            ip_address=block_request.ip_address,
            reason=block_request.reason,
            block_type=block_request.block_type,
            duration_minutes=block_request.duration_minutes
        )
        
        return IPBlockResponse(
            ip_address=block.ip_address,
            block_type=block.block_type.value,
            reason=block.reason,
            blocked_at=block.blocked_at,
            expires_at=block.expires_at,
            violation_count=block.violation_count
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to block IP address: {str(e)}"
        )


@router.delete("/ip-blocks/{ip_address}")
async def unblock_ip_address(
    ip_address: str,
    current_user: User = Depends(get_current_user)
):
    """Unblock an IP address."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        success = await api_security.ip_block_manager.unblock_ip(ip_address)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="IP address not found in block list"
            )
        
        return {
            "message": f"IP address {ip_address} unblocked successfully",
            "unblocked_at": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unblock IP address: {str(e)}"
        )


@router.get("/ip-blocks", response_model=List[IPBlockResponse])
async def list_blocked_ips(
    current_user: User = Depends(get_current_user)
):
    """List all blocked IP addresses."""
    try:
        blocked_ips = await api_security.ip_block_manager.get_blocked_ips()
        
        return [
            IPBlockResponse(
                ip_address=block.ip_address,
                block_type=block.block_type.value,
                reason=block.reason,
                blocked_at=block.blocked_at,
                expires_at=block.expires_at,
                violation_count=block.violation_count
            )
            for block in blocked_ips
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve blocked IPs: {str(e)}"
        )


# Security Monitoring Endpoints
@router.get("/violations")
async def list_security_violations(
    limit: int = Query(100, ge=1, le=1000),
    threat_type: Optional[ThreatType] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """List recent security violations."""
    try:
        violations = list(api_security.security_violations)
        
        # Apply filters
        if threat_type:
            violations = [v for v in violations if v.threat_type == threat_type]
        
        # Sort by timestamp, newest first
        violations.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Limit results
        violations = violations[:limit]
        
        violation_list = []
        for violation in violations:
            violation_list.append({
                "id": violation.id,
                "threat_type": violation.threat_type.value,
                "source_ip": violation.source_ip,
                "user_id": violation.user_id,
                "endpoint": violation.endpoint,
                "severity": violation.severity,
                "blocked": violation.blocked,
                "timestamp": violation.timestamp.isoformat(),
                "details": violation.details
            })
        
        return {
            "violations": violation_list,
            "total_count": len(violation_list),
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve security violations: {str(e)}"
        )


@router.get("/dashboard", response_model=SecurityDashboardResponse)
async def get_security_dashboard(
    current_user: User = Depends(get_current_user)
):
    """Get security monitoring dashboard."""
    try:
        dashboard_data = await api_security.get_security_dashboard()
        
        return SecurityDashboardResponse(
            total_requests=dashboard_data["total_requests"],
            blocked_requests=dashboard_data["blocked_requests"],
            rate_limit_violations=dashboard_data["rate_limit_violations"],
            security_violations=dashboard_data["security_violations"],
            recent_violations_24h=dashboard_data["recent_violations_24h"],
            violation_types=dashboard_data["violation_types"],
            blocked_ips=dashboard_data["blocked_ips"],
            active_rate_limits=dashboard_data["active_rate_limits"],
            security_rules=dashboard_data["security_rules"],
            last_updated=dashboard_data["last_updated"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve security dashboard: {str(e)}"
        )


# System Information Endpoints
@router.get("/system/types")
async def list_security_types():
    """List available security types and enums."""
    return {
        "threat_types": [tt.value for tt in ThreatType],
        "block_types": [bt.value for bt in BlockType],
        "rate_limit_scopes": [rls.value for rls in RateLimitScope],
        "security_levels": [sl.value for sl in SecurityLevel]
    }


# Health check endpoint
@router.get("/health", response_model=SecurityHealthResponse)
async def api_security_health_check():
    """Check advanced API security system health."""
    try:
        health_info = await check_advanced_api_security_health()
        
        dashboard_data = health_info["dashboard"]
        
        return SecurityHealthResponse(
            status=health_info["status"],
            dashboard=SecurityDashboardResponse(
                total_requests=dashboard_data["total_requests"],
                blocked_requests=dashboard_data["blocked_requests"],
                rate_limit_violations=dashboard_data["rate_limit_violations"],
                security_violations=dashboard_data["security_violations"],
                recent_violations_24h=dashboard_data["recent_violations_24h"],
                violation_types=dashboard_data["violation_types"],
                blocked_ips=dashboard_data["blocked_ips"],
                active_rate_limits=dashboard_data["active_rate_limits"],
                security_rules=dashboard_data["security_rules"],
                last_updated=dashboard_data["last_updated"]
            ),
            pattern_detector_rules=health_info["pattern_detector_rules"],
            rate_limit_rules=health_info["rate_limit_rules"],
            violation_history_size=health_info["violation_history_size"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"API security health check failed: {str(e)}"
        )