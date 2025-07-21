"""Advanced API Security & Protection System."""

import asyncio
import hashlib
import hmac
import json
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from ipaddress import ip_address, ip_network

from app.core.monitoring import monitor_performance


class SecurityLevel(str, Enum):
    """API security levels."""
    PUBLIC = "public"
    PROTECTED = "protected"
    PRIVATE = "private"
    HIGHLY_RESTRICTED = "highly_restricted"


class ThreatType(str, Enum):
    """Security threat types."""
    BRUTE_FORCE = "brute_force"
    DDoS = "ddos"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    MALICIOUS_PAYLOAD = "malicious_payload"


class BlockType(str, Enum):
    """Block types for security violations."""
    TEMPORARY = "temporary"
    PERMANENT = "permanent"
    WARNING = "warning"
    QUARANTINE = "quarantine"


class RateLimitScope(str, Enum):
    """Rate limit scope types."""
    IP_ADDRESS = "ip_address"
    USER = "user"
    API_KEY = "api_key"
    ENDPOINT = "endpoint"
    GLOBAL = "global"


@dataclass
class SecurityRule:
    """Security rule definition."""
    id: str
    name: str
    rule_type: ThreatType
    pattern: str
    description: str
    severity: int = 5  # 1-10 scale
    enabled: bool = True
    action: BlockType = BlockType.WARNING
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration."""
    id: str
    name: str
    scope: RateLimitScope
    endpoint_pattern: str
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_allowance: int = 0
    whitelist_ips: List[str] = field(default_factory=list)
    enabled: bool = True
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class SecurityViolation:
    """Security violation record."""
    id: str
    threat_type: ThreatType
    source_ip: str
    user_id: Optional[str]
    endpoint: str
    payload: Dict[str, Any]
    severity: int
    blocked: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class IPBlock:
    """IP address block record."""
    ip_address: str
    block_type: BlockType
    reason: str
    blocked_at: datetime
    expires_at: Optional[datetime] = None
    violation_count: int = 1
    
    def is_expired(self) -> bool:
        """Check if block has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at


class SecurityPatternDetector:
    """Advanced security pattern detection engine."""
    
    def __init__(self):
        """Initialize pattern detector."""
        self.patterns = self._initialize_security_patterns()
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
    
    def _initialize_security_patterns(self) -> List[SecurityRule]:
        """Initialize default security patterns."""
        return [
            SecurityRule(
                id="sql_injection_1",
                name="SQL Injection - Union Based",
                rule_type=ThreatType.SQL_INJECTION,
                pattern=r"(?i)(union\s+select|or\s+1=1|drop\s+table)",
                description="Detects common SQL injection patterns",
                severity=9
            ),
            SecurityRule(
                id="xss_1",
                name="Cross-Site Scripting",
                rule_type=ThreatType.XSS,
                pattern=r"(?i)(<script|javascript:|on\w+\s*=)",
                description="Detects XSS attack patterns",
                severity=8
            ),
            SecurityRule(
                id="brute_force_1",
                name="Brute Force Attack",
                rule_type=ThreatType.BRUTE_FORCE,
                pattern=r"(password|login|auth)",
                description="Detects potential brute force attempts",
                severity=7
            ),
            SecurityRule(
                id="suspicious_1",
                name="Suspicious User Agent",
                rule_type=ThreatType.SUSPICIOUS_PATTERN,
                pattern=r"(?i)(bot|scanner|crawler|hack|exploit)",
                description="Detects suspicious user agents",
                severity=6
            ),
            SecurityRule(
                id="malicious_payload_1",
                name="Malicious File Upload",
                rule_type=ThreatType.MALICIOUS_PAYLOAD,
                pattern=r"(?i)\.(php|jsp|asp|exe|bat|sh)$",
                description="Detects potentially malicious file uploads",
                severity=8
            )
        ]
    
    @monitor_performance("security.pattern_detection")
    async def analyze_request(
        self,
        ip_address: str,
        endpoint: str,
        method: str,
        headers: Dict[str, str],
        query_params: Dict[str, Any],
        body: str,
        user_id: Optional[str] = None
    ) -> List[SecurityViolation]:
        """Analyze request for security violations."""
        violations = []
        
        # Combine all request data for analysis
        request_data = {
            "endpoint": endpoint,
            "method": method,
            "headers": headers,
            "query_params": query_params,
            "body": body
        }
        
        # Convert to string for pattern matching
        request_string = json.dumps(request_data, default=str).lower()
        
        # Check against security patterns
        for rule in self.patterns:
            if not rule.enabled:
                continue
            
            import re
            if re.search(rule.pattern, request_string):
                violation = SecurityViolation(
                    id=str(uuid.uuid4()),
                    threat_type=rule.rule_type,
                    source_ip=ip_address,
                    user_id=user_id,
                    endpoint=endpoint,
                    payload=request_data,
                    severity=rule.severity,
                    blocked=rule.action in [BlockType.TEMPORARY, BlockType.PERMANENT],
                    details={
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "pattern": rule.pattern,
                        "action": rule.action.value
                    }
                )
                violations.append(violation)
        
        # Store request history for behavioral analysis
        self.request_history[ip_address].append({
            "timestamp": datetime.utcnow(),
            "endpoint": endpoint,
            "method": method,
            "violations": len(violations)
        })
        
        # Check for behavioral patterns
        behavioral_violations = await self._analyze_behavior(ip_address, endpoint)
        violations.extend(behavioral_violations)
        
        return violations
    
    async def _analyze_behavior(self, ip_address: str, endpoint: str) -> List[SecurityViolation]:
        """Analyze behavioral patterns for anomalies."""
        violations = []
        history = self.request_history[ip_address]
        
        if len(history) < 10:
            return violations
        
        recent_requests = list(history)[-10:]
        
        # Check for rapid-fire requests (potential bot/scanner)
        time_diffs = []
        for i in range(1, len(recent_requests)):
            diff = (recent_requests[i]["timestamp"] - recent_requests[i-1]["timestamp"]).total_seconds()
            time_diffs.append(diff)
        
        avg_time_diff = sum(time_diffs) / len(time_diffs)
        if avg_time_diff < 0.1:  # Less than 100ms between requests
            violation = SecurityViolation(
                id=str(uuid.uuid4()),
                threat_type=ThreatType.SUSPICIOUS_PATTERN,
                source_ip=ip_address,
                user_id=None,
                endpoint=endpoint,
                payload={"behavior": "rapid_requests"},
                severity=7,
                blocked=False,
                details={
                    "avg_time_diff": avg_time_diff,
                    "request_count": len(recent_requests)
                }
            )
            violations.append(violation)
        
        # Check for endpoint scanning
        unique_endpoints = set(req["endpoint"] for req in recent_requests)
        if len(unique_endpoints) > 8:  # Many different endpoints
            violation = SecurityViolation(
                id=str(uuid.uuid4()),
                threat_type=ThreatType.SUSPICIOUS_PATTERN,
                source_ip=ip_address,
                user_id=None,
                endpoint=endpoint,
                payload={"behavior": "endpoint_scanning"},
                severity=6,
                blocked=False,
                details={
                    "unique_endpoints": len(unique_endpoints),
                    "endpoints": list(unique_endpoints)
                }
            )
            violations.append(violation)
        
        return violations


class RateLimitManager:
    """Advanced rate limiting management."""
    
    def __init__(self):
        """Initialize rate limit manager."""
        self.rules: Dict[str, RateLimitRule] = {}
        self.counters: Dict[str, Dict[str, Any]] = defaultdict(lambda: defaultdict(dict))
        self.whitelist_networks: List[Any] = []
        self._initialize_default_rules()
    
    def _initialize_default_rules(self) -> None:
        """Initialize default rate limiting rules."""
        default_rules = [
            RateLimitRule(
                id="global_api",
                name="Global API Rate Limit",
                scope=RateLimitScope.IP_ADDRESS,
                endpoint_pattern="*",
                requests_per_minute=100,
                requests_per_hour=1000,
                requests_per_day=10000,
                burst_allowance=20
            ),
            RateLimitRule(
                id="auth_endpoints",
                name="Authentication Endpoints",
                scope=RateLimitScope.IP_ADDRESS,
                endpoint_pattern="/api/v1/auth/*",
                requests_per_minute=10,
                requests_per_hour=50,
                requests_per_day=500,
                burst_allowance=5
            ),
            RateLimitRule(
                id="user_specific",
                name="User-Specific Rate Limit",
                scope=RateLimitScope.USER,
                endpoint_pattern="*",
                requests_per_minute=200,
                requests_per_hour=2000,
                requests_per_day=20000,
                burst_allowance=50
            )
        ]
        
        for rule in default_rules:
            self.rules[rule.id] = rule
    
    def add_whitelist_network(self, network: str) -> None:
        """Add network to whitelist."""
        try:
            self.whitelist_networks.append(ip_network(network))
        except Exception as e:
            print(f"Invalid network format: {network}")
    
    def is_whitelisted(self, ip_addr: str) -> bool:
        """Check if IP is whitelisted."""
        try:
            ip = ip_address(ip_addr)
            return any(ip in network for network in self.whitelist_networks)
        except:
            return False
    
    @monitor_performance("security.rate_limit_check")
    async def check_rate_limit(
        self,
        ip_address: str,
        endpoint: str,
        user_id: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> Tuple[bool, Optional[RateLimitRule], Dict[str, Any]]:
        """Check if request exceeds rate limits."""
        
        # Skip rate limiting for whitelisted IPs
        if self.is_whitelisted(ip_address):
            return True, None, {"whitelisted": True}
        
        current_time = datetime.utcnow()
        
        # Find applicable rules
        applicable_rules = self._find_applicable_rules(endpoint)
        
        for rule in applicable_rules:
            if not rule.enabled:
                continue
            
            # Determine counter key based on scope
            counter_key = self._get_counter_key(rule, ip_address, user_id, api_key)
            
            # Check rate limits
            exceeded, info = await self._check_rule_limits(
                rule, counter_key, current_time
            )
            
            if exceeded:
                return False, rule, info
        
        # Update counters for all applicable rules
        for rule in applicable_rules:
            if rule.enabled:
                counter_key = self._get_counter_key(rule, ip_address, user_id, api_key)
                await self._update_counter(rule, counter_key, current_time)
        
        return True, None, {"allowed": True}
    
    def _find_applicable_rules(self, endpoint: str) -> List[RateLimitRule]:
        """Find rate limiting rules applicable to endpoint."""
        applicable_rules = []
        
        for rule in self.rules.values():
            if self._matches_pattern(endpoint, rule.endpoint_pattern):
                applicable_rules.append(rule)
        
        # Sort by specificity (more specific patterns first)
        applicable_rules.sort(key=lambda r: (
            -len(r.endpoint_pattern.replace("*", "")),
            r.requests_per_minute
        ))
        
        return applicable_rules
    
    def _matches_pattern(self, endpoint: str, pattern: str) -> bool:
        """Check if endpoint matches pattern."""
        if pattern == "*":
            return True
        
        # Simple wildcard matching
        if pattern.endswith("*"):
            return endpoint.startswith(pattern[:-1])
        
        return endpoint == pattern
    
    def _get_counter_key(
        self,
        rule: RateLimitRule,
        ip_address: str,
        user_id: Optional[str],
        api_key: Optional[str]
    ) -> str:
        """Get counter key based on rule scope."""
        if rule.scope == RateLimitScope.IP_ADDRESS:
            return f"ip:{ip_address}:{rule.id}"
        elif rule.scope == RateLimitScope.USER and user_id:
            return f"user:{user_id}:{rule.id}"
        elif rule.scope == RateLimitScope.API_KEY and api_key:
            return f"api_key:{api_key}:{rule.id}"
        elif rule.scope == RateLimitScope.ENDPOINT:
            return f"endpoint:{rule.endpoint_pattern}:{rule.id}"
        elif rule.scope == RateLimitScope.GLOBAL:
            return f"global:{rule.id}"
        else:
            return f"ip:{ip_address}:{rule.id}"  # Fallback to IP
    
    async def _check_rule_limits(
        self,
        rule: RateLimitRule,
        counter_key: str,
        current_time: datetime
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if rule limits are exceeded."""
        counter_data = self.counters[counter_key]
        
        # Initialize counter if not exists
        if not counter_data:
            counter_data["requests"] = []
            counter_data["last_reset"] = current_time
        
        # Clean old requests
        cutoff_time = current_time - timedelta(days=1)
        counter_data["requests"] = [
            req_time for req_time in counter_data["requests"]
            if req_time > cutoff_time
        ]
        
        # Count requests in different time windows
        minute_ago = current_time - timedelta(minutes=1)
        hour_ago = current_time - timedelta(hours=1)
        day_ago = current_time - timedelta(days=1)
        
        minute_requests = len([t for t in counter_data["requests"] if t > minute_ago])
        hour_requests = len([t for t in counter_data["requests"] if t > hour_ago])
        day_requests = len([t for t in counter_data["requests"] if t > day_ago])
        
        # Check limits
        if minute_requests >= rule.requests_per_minute:
            return True, {
                "limit_type": "per_minute",
                "current": minute_requests,
                "limit": rule.requests_per_minute,
                "reset_time": minute_ago + timedelta(minutes=1)
            }
        
        if hour_requests >= rule.requests_per_hour:
            return True, {
                "limit_type": "per_hour",
                "current": hour_requests,
                "limit": rule.requests_per_hour,
                "reset_time": hour_ago + timedelta(hours=1)
            }
        
        if day_requests >= rule.requests_per_day:
            return True, {
                "limit_type": "per_day",
                "current": day_requests,
                "limit": rule.requests_per_day,
                "reset_time": day_ago + timedelta(days=1)
            }
        
        return False, {
            "minute_remaining": rule.requests_per_minute - minute_requests,
            "hour_remaining": rule.requests_per_hour - hour_requests,
            "day_remaining": rule.requests_per_day - day_requests
        }
    
    async def _update_counter(
        self,
        rule: RateLimitRule,
        counter_key: str,
        current_time: datetime
    ) -> None:
        """Update request counter."""
        counter_data = self.counters[counter_key]
        counter_data["requests"].append(current_time)


class IPBlockManager:
    """IP address blocking and management."""
    
    def __init__(self):
        """Initialize IP block manager."""
        self.blocked_ips: Dict[str, IPBlock] = {}
        self.violation_counts: Dict[str, int] = defaultdict(int)
    
    async def check_ip_blocked(self, ip_address: str) -> Tuple[bool, Optional[IPBlock]]:
        """Check if IP address is blocked."""
        if ip_address in self.blocked_ips:
            block = self.blocked_ips[ip_address]
            
            # Check if block has expired
            if block.is_expired():
                del self.blocked_ips[ip_address]
                return False, None
            
            return True, block
        
        return False, None
    
    async def block_ip(
        self,
        ip_address: str,
        reason: str,
        block_type: BlockType = BlockType.TEMPORARY,
        duration_minutes: Optional[int] = None
    ) -> IPBlock:
        """Block an IP address."""
        
        # Calculate expiration time
        expires_at = None
        if block_type == BlockType.TEMPORARY:
            duration = duration_minutes or 60  # Default 1 hour
            expires_at = datetime.utcnow() + timedelta(minutes=duration)
        
        # Update violation count
        self.violation_counts[ip_address] += 1
        
        # Create or update block
        block = IPBlock(
            ip_address=ip_address,
            block_type=block_type,
            reason=reason,
            blocked_at=datetime.utcnow(),
            expires_at=expires_at,
            violation_count=self.violation_counts[ip_address]
        )
        
        self.blocked_ips[ip_address] = block
        return block
    
    async def unblock_ip(self, ip_address: str) -> bool:
        """Unblock an IP address."""
        if ip_address in self.blocked_ips:
            del self.blocked_ips[ip_address]
            return True
        return False
    
    async def get_blocked_ips(self) -> List[IPBlock]:
        """Get list of blocked IP addresses."""
        # Clean expired blocks
        expired_ips = [
            ip for ip, block in self.blocked_ips.items()
            if block.is_expired()
        ]
        for ip in expired_ips:
            del self.blocked_ips[ip]
        
        return list(self.blocked_ips.values())


class AdvancedAPISecurityManager:
    """Main advanced API security management system."""
    
    def __init__(self):
        """Initialize advanced API security manager."""
        self.pattern_detector = SecurityPatternDetector()
        self.rate_limit_manager = RateLimitManager()
        self.ip_block_manager = IPBlockManager()
        self.security_violations: deque = deque(maxlen=10000)
        self.security_metrics: Dict[str, Any] = defaultdict(int)
        
        # Initialize whitelist
        self.rate_limit_manager.add_whitelist_network("127.0.0.0/8")  # Localhost
        self.rate_limit_manager.add_whitelist_network("10.0.0.0/8")   # Private networks
    
    @monitor_performance("security.analyze_request")
    async def analyze_request(
        self,
        ip_address: str,
        endpoint: str,
        method: str,
        headers: Dict[str, str],
        query_params: Dict[str, Any],
        body: str = "",
        user_id: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Comprehensive request security analysis."""
        
        # Check if IP is blocked
        is_blocked, block_info = await self.ip_block_manager.check_ip_blocked(ip_address)
        if is_blocked:
            self.security_metrics["blocked_requests"] += 1
            return {
                "allowed": False,
                "reason": "ip_blocked",
                "block_info": {
                    "block_type": block_info.block_type.value,
                    "reason": block_info.reason,
                    "blocked_at": block_info.blocked_at.isoformat(),
                    "expires_at": block_info.expires_at.isoformat() if block_info.expires_at else None
                }
            }
        
        # Check rate limits
        rate_limit_ok, violated_rule, rate_info = await self.rate_limit_manager.check_rate_limit(
            ip_address, endpoint, user_id, api_key
        )
        
        if not rate_limit_ok:
            self.security_metrics["rate_limit_violations"] += 1
            
            # Consider blocking IP for repeated violations
            violation_count = self.rate_limit_manager.counters.get(
                f"ip:{ip_address}:violations", {"count": 0}
            )["count"]
            
            if violation_count > 10:  # Block after 10 violations
                await self.ip_block_manager.block_ip(
                    ip_address,
                    f"Repeated rate limit violations: {violation_count}",
                    BlockType.TEMPORARY,
                    120  # 2 hours
                )
            
            return {
                "allowed": False,
                "reason": "rate_limit_exceeded",
                "rule": violated_rule.name if violated_rule else "unknown",
                "rate_info": rate_info
            }
        
        # Analyze for security patterns
        violations = await self.pattern_detector.analyze_request(
            ip_address, endpoint, method, headers, query_params, body, user_id
        )
        
        # Process violations
        high_severity_violations = [v for v in violations if v.severity >= 8]
        
        if high_severity_violations:
            self.security_metrics["security_violations"] += len(high_severity_violations)
            
            # Block IP for critical violations
            for violation in high_severity_violations:
                if violation.threat_type in [ThreatType.SQL_INJECTION, ThreatType.MALICIOUS_PAYLOAD]:
                    await self.ip_block_manager.block_ip(
                        ip_address,
                        f"Critical security violation: {violation.threat_type.value}",
                        BlockType.TEMPORARY,
                        240  # 4 hours
                    )
                    break
        
        # Store violations
        for violation in violations:
            self.security_violations.append(violation)
        
        self.security_metrics["total_requests"] += 1
        
        return {
            "allowed": len(high_severity_violations) == 0,
            "violations": [
                {
                    "id": v.id,
                    "type": v.threat_type.value,
                    "severity": v.severity,
                    "blocked": v.blocked,
                    "details": v.details
                }
                for v in violations
            ],
            "security_score": self._calculate_security_score(violations),
            "rate_info": rate_info
        }
    
    def _calculate_security_score(self, violations: List[SecurityViolation]) -> int:
        """Calculate overall security score for request."""
        if not violations:
            return 100
        
        total_severity = sum(v.severity for v in violations)
        max_possible = len(violations) * 10
        
        score = max(0, 100 - int((total_severity / max_possible) * 100))
        return score
    
    async def get_security_dashboard(self) -> Dict[str, Any]:
        """Get security metrics dashboard."""
        recent_violations = [
            v for v in self.security_violations
            if v.timestamp > datetime.utcnow() - timedelta(hours=24)
        ]
        
        violation_types = defaultdict(int)
        for violation in recent_violations:
            violation_types[violation.threat_type.value] += 1
        
        blocked_ips = await self.ip_block_manager.get_blocked_ips()
        
        return {
            "total_requests": self.security_metrics["total_requests"],
            "blocked_requests": self.security_metrics["blocked_requests"],
            "rate_limit_violations": self.security_metrics["rate_limit_violations"],
            "security_violations": self.security_metrics["security_violations"],
            "recent_violations_24h": len(recent_violations),
            "violation_types": dict(violation_types),
            "blocked_ips": len(blocked_ips),
            "active_rate_limits": len(self.rate_limit_manager.rules),
            "security_rules": len(self.pattern_detector.patterns),
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def add_security_rule(self, rule: SecurityRule) -> str:
        """Add custom security rule."""
        self.pattern_detector.patterns.append(rule)
        return rule.id
    
    async def add_rate_limit_rule(self, rule: RateLimitRule) -> str:
        """Add custom rate limit rule."""
        self.rate_limit_manager.rules[rule.id] = rule
        return rule.id


# Global advanced API security manager instance
api_security = AdvancedAPISecurityManager()


# Health check for advanced API security
async def check_advanced_api_security_health() -> Dict[str, Any]:
    """Check advanced API security system health."""
    dashboard = await api_security.get_security_dashboard()
    
    # Determine health status
    health_status = "healthy"
    
    if dashboard["blocked_requests"] > dashboard["total_requests"] * 0.1:
        health_status = "degraded"
    
    if dashboard["recent_violations_24h"] > 1000:
        health_status = "warning"
    
    return {
        "status": health_status,
        "dashboard": dashboard,
        "pattern_detector_rules": len(api_security.pattern_detector.patterns),
        "rate_limit_rules": len(api_security.rate_limit_manager.rules),
        "violation_history_size": len(api_security.security_violations)
    }