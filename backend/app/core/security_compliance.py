"""Enterprise Security & Compliance Framework."""

import asyncio
import hashlib
import hmac
import json
import secrets
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import uuid4

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.monitoring import monitor_performance


class ComplianceStandard(str, Enum):
    """Compliance standards."""
    GDPR = "gdpr"
    SOX = "sox"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"
    SOC2 = "soc2"
    NIST = "nist"
    CCPA = "ccpa"


class SecurityLevel(str, Enum):
    """Security levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"


class ThreatLevel(str, Enum):
    """Threat levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentType(str, Enum):
    """Security incident types."""
    DATA_BREACH = "data_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    MALWARE = "malware"
    PHISHING = "phishing"
    DDoS = "ddos"
    INSIDER_THREAT = "insider_threat"
    COMPLIANCE_VIOLATION = "compliance_violation"
    SYSTEM_COMPROMISE = "system_compromise"


@dataclass
class SecurityPolicy:
    """Security policy definition."""
    id: str
    name: str
    description: str
    compliance_standards: List[ComplianceStandard]
    security_level: SecurityLevel
    rules: List[Dict[str, Any]] = field(default_factory=list)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


@dataclass
class SecurityIncident:
    """Security incident record."""
    id: str
    incident_type: IncidentType
    threat_level: ThreatLevel
    title: str
    description: str
    affected_systems: List[str] = field(default_factory=list)
    affected_users: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    status: str = "open"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


@dataclass
class ComplianceCheck:
    """Compliance check definition."""
    id: str
    name: str
    standard: ComplianceStandard
    check_type: str
    description: str
    automated: bool = True
    frequency: str = "daily"  # daily, weekly, monthly
    last_run: Optional[datetime] = None
    enabled: bool = True
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


@dataclass
class ComplianceResult:
    """Compliance check result."""
    id: str
    check_id: str
    executed_at: datetime
    passed: bool
    score: float
    findings: List[Dict[str, Any]] = field(default_factory=list)
    remediation_actions: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


class DataClassificationEngine:
    """Data classification and labeling engine."""
    
    def __init__(self):
        """Initialize data classification engine."""
        self.classification_rules: Dict[str, Dict[str, Any]] = {}
        self.data_inventory: Dict[str, Dict[str, Any]] = {}
    
    @monitor_performance("security.classification.classify")
    async def classify_data(
        self,
        data_source: str,
        data_type: str,
        sample_data: Dict[str, Any]
    ) -> SecurityLevel:
        """Classify data based on content and context."""
        classification_score = 0
        
        # Check for sensitive data patterns
        sensitive_patterns = {
            "ssn": r"\d{3}-?\d{2}-?\d{4}",
            "credit_card": r"\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}",
            "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "phone": r"\+?1?[- ]?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}",
            "passport": r"[A-Z]{1,2}\d{6,9}"
        }
        
        data_str = json.dumps(sample_data, default=str).lower()
        
        for pattern_name, pattern in sensitive_patterns.items():
            import re
            if re.search(pattern, data_str):
                if pattern_name in ["ssn", "credit_card", "passport"]:
                    classification_score += 50
                elif pattern_name in ["email", "phone"]:
                    classification_score += 20
        
        # Check field names for sensitive indicators
        sensitive_fields = [
            "password", "ssn", "social_security", "credit_card", "bank_account",
            "salary", "medical", "health", "diagnosis", "treatment"
        ]
        
        for field in sample_data.keys():
            field_lower = field.lower()
            for sensitive_field in sensitive_fields:
                if sensitive_field in field_lower:
                    classification_score += 30
                    break
        
        # Determine security level
        if classification_score >= 100:
            return SecurityLevel.TOP_SECRET
        elif classification_score >= 70:
            return SecurityLevel.RESTRICTED
        elif classification_score >= 40:
            return SecurityLevel.CONFIDENTIAL
        elif classification_score >= 20:
            return SecurityLevel.INTERNAL
        else:
            return SecurityLevel.PUBLIC
    
    async def register_data_asset(
        self,
        asset_id: str,
        asset_name: str,
        data_source: str,
        classification: SecurityLevel,
        metadata: Dict[str, Any]
    ) -> None:
        """Register a data asset in the inventory."""
        self.data_inventory[asset_id] = {
            "asset_name": asset_name,
            "data_source": data_source,
            "classification": classification.value,
            "metadata": metadata,
            "registered_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def get_data_inventory(self) -> Dict[str, Any]:
        """Get complete data inventory."""
        return self.data_inventory


class EncryptionManager:
    """Enterprise encryption management."""
    
    def __init__(self):
        """Initialize encryption manager."""
        self.encryption_keys: Dict[str, bytes] = {}
        self.key_metadata: Dict[str, Dict[str, Any]] = {}
    
    def generate_key(self, key_id: str, purpose: str = "general") -> str:
        """Generate encryption key."""
        key = Fernet.generate_key()
        self.encryption_keys[key_id] = key
        self.key_metadata[key_id] = {
            "purpose": purpose,
            "created_at": datetime.utcnow().isoformat(),
            "algorithm": "Fernet",
            "key_size": 256
        }
        return key.decode()
    
    def encrypt_data(self, key_id: str, data: str) -> str:
        """Encrypt data with specified key."""
        if key_id not in self.encryption_keys:
            raise ValueError(f"Key {key_id} not found")
        
        key = self.encryption_keys[key_id]
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data.encode())
        return encrypted_data.decode()
    
    def decrypt_data(self, key_id: str, encrypted_data: str) -> str:
        """Decrypt data with specified key."""
        if key_id not in self.encryption_keys:
            raise ValueError(f"Key {key_id} not found")
        
        key = self.encryption_keys[key_id]
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted_data.encode())
        return decrypted_data.decode()
    
    def rotate_key(self, key_id: str) -> str:
        """Rotate encryption key."""
        old_key = self.encryption_keys.get(key_id)
        if not old_key:
            raise ValueError(f"Key {key_id} not found")
        
        # Generate new key
        new_key = Fernet.generate_key()
        self.encryption_keys[key_id] = new_key
        
        # Update metadata
        self.key_metadata[key_id]["rotated_at"] = datetime.utcnow().isoformat()
        self.key_metadata[key_id]["previous_key"] = old_key.decode()
        
        return new_key.decode()


class ThreatDetectionEngine:
    """Advanced threat detection and response."""
    
    def __init__(self):
        """Initialize threat detection engine."""
        self.threat_patterns: Dict[str, Dict[str, Any]] = {}
        self.active_threats: Dict[str, SecurityIncident] = {}
        self.detection_rules: List[Dict[str, Any]] = []
        self._initialize_detection_rules()
    
    def _initialize_detection_rules(self) -> None:
        """Initialize default detection rules."""
        self.detection_rules = [
            {
                "name": "Multiple Failed Logins",
                "pattern": "failed_login_attempts > 5",
                "threat_level": ThreatLevel.MEDIUM,
                "incident_type": IncidentType.UNAUTHORIZED_ACCESS
            },
            {
                "name": "Unusual Data Access",
                "pattern": "data_access_volume > normal_baseline * 3",
                "threat_level": ThreatLevel.HIGH,
                "incident_type": IncidentType.DATA_BREACH
            },
            {
                "name": "Privileged Account Misuse",
                "pattern": "admin_actions_outside_hours",
                "threat_level": ThreatLevel.HIGH,
                "incident_type": IncidentType.INSIDER_THREAT
            },
            {
                "name": "Suspicious API Calls",
                "pattern": "api_calls_per_minute > 1000",
                "threat_level": ThreatLevel.MEDIUM,
                "incident_type": IncidentType.DDoS
            }
        ]
    
    @monitor_performance("security.threat_detection.analyze")
    async def analyze_security_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Optional[SecurityIncident]:
        """Analyze security event for threats."""
        # Simulate threat analysis
        threat_score = 0
        triggered_rules = []
        
        # Check against detection rules
        for rule in self.detection_rules:
            if self._evaluate_rule(rule, event_data):
                threat_score += 25
                triggered_rules.append(rule["name"])
        
        # Additional heuristic analysis
        if event_type == "login_attempt":
            if event_data.get("failed_attempts", 0) > 3:
                threat_score += 20
            if event_data.get("location_anomaly", False):
                threat_score += 30
        
        elif event_type == "data_access":
            if event_data.get("large_volume", False):
                threat_score += 40
            if event_data.get("sensitive_data", False):
                threat_score += 50
        
        # Determine if incident should be created
        if threat_score >= 50:
            incident_type = self._determine_incident_type(event_type, event_data)
            threat_level = self._calculate_threat_level(threat_score)
            
            incident = SecurityIncident(
                id=str(uuid4()),
                incident_type=incident_type,
                threat_level=threat_level,
                title=f"Security threat detected: {event_type}",
                description=f"Triggered rules: {', '.join(triggered_rules)}",
                affected_systems=event_data.get("systems", []),
                affected_users=[user_id] if user_id else [],
                metadata={
                    "threat_score": threat_score,
                    "triggered_rules": triggered_rules,
                    "event_data": event_data
                }
            )
            
            self.active_threats[incident.id] = incident
            return incident
        
        return None
    
    def _evaluate_rule(self, rule: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """Evaluate detection rule against event data."""
        # Simplified rule evaluation
        pattern = rule["pattern"]
        
        if "failed_login_attempts > 5" in pattern:
            return event_data.get("failed_attempts", 0) > 5
        elif "data_access_volume > normal_baseline * 3" in pattern:
            return event_data.get("access_volume", 0) > 1000
        elif "admin_actions_outside_hours" in pattern:
            return event_data.get("outside_hours", False) and event_data.get("admin_action", False)
        elif "api_calls_per_minute > 1000" in pattern:
            return event_data.get("api_calls_per_minute", 0) > 1000
        
        return False
    
    def _determine_incident_type(self, event_type: str, event_data: Dict[str, Any]) -> IncidentType:
        """Determine incident type based on event."""
        if event_type in ["login_attempt", "access_denied"]:
            return IncidentType.UNAUTHORIZED_ACCESS
        elif event_type == "data_access":
            return IncidentType.DATA_BREACH
        elif event_type == "api_request":
            return IncidentType.DDoS
        else:
            return IncidentType.SYSTEM_COMPROMISE
    
    def _calculate_threat_level(self, threat_score: int) -> ThreatLevel:
        """Calculate threat level from score."""
        if threat_score >= 100:
            return ThreatLevel.CRITICAL
        elif threat_score >= 75:
            return ThreatLevel.HIGH
        elif threat_score >= 50:
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW


class ComplianceEngine:
    """Compliance monitoring and reporting engine."""
    
    def __init__(self):
        """Initialize compliance engine."""
        self.compliance_checks: Dict[str, ComplianceCheck] = {}
        self.compliance_results: Dict[str, ComplianceResult] = {}
        self.policy_violations: List[Dict[str, Any]] = []
        self._initialize_compliance_checks()
    
    def _initialize_compliance_checks(self) -> None:
        """Initialize default compliance checks."""
        default_checks = [
            {
                "name": "GDPR Data Retention",
                "standard": ComplianceStandard.GDPR,
                "check_type": "data_retention",
                "description": "Verify data retention policies comply with GDPR"
            },
            {
                "name": "SOX Financial Controls",
                "standard": ComplianceStandard.SOX,
                "check_type": "access_controls",
                "description": "Validate financial system access controls"
            },
            {
                "name": "PCI DSS Encryption",
                "standard": ComplianceStandard.PCI_DSS,
                "check_type": "encryption",
                "description": "Ensure payment data encryption compliance"
            },
            {
                "name": "ISO27001 Risk Assessment",
                "standard": ComplianceStandard.ISO27001,
                "check_type": "risk_assessment",
                "description": "Validate information security risk assessments"
            }
        ]
        
        for check_data in default_checks:
            check = ComplianceCheck(
                id=str(uuid4()),
                name=check_data["name"],
                standard=check_data["standard"],
                check_type=check_data["check_type"],
                description=check_data["description"]
            )
            self.compliance_checks[check.id] = check
    
    @monitor_performance("security.compliance.run_check")
    async def run_compliance_check(self, check_id: str) -> ComplianceResult:
        """Run a specific compliance check."""
        check = self.compliance_checks.get(check_id)
        if not check:
            raise ValueError(f"Compliance check {check_id} not found")
        
        # Simulate compliance check execution
        findings = []
        score = 85.0  # Base compliance score
        
        if check.standard == ComplianceStandard.GDPR:
            findings = await self._check_gdpr_compliance()
        elif check.standard == ComplianceStandard.SOX:
            findings = await self._check_sox_compliance()
        elif check.standard == ComplianceStandard.PCI_DSS:
            findings = await self._check_pci_compliance()
        elif check.standard == ComplianceStandard.ISO27001:
            findings = await self._check_iso27001_compliance()
        
        # Adjust score based on findings
        score -= len(findings) * 10
        score = max(0.0, min(100.0, score))
        
        result = ComplianceResult(
            id=str(uuid4()),
            check_id=check_id,
            executed_at=datetime.utcnow(),
            passed=score >= 70,
            score=score,
            findings=findings,
            remediation_actions=self._generate_remediation_actions(findings)
        )
        
        self.compliance_results[result.id] = result
        check.last_run = result.executed_at
        
        return result
    
    async def _check_gdpr_compliance(self) -> List[Dict[str, Any]]:
        """Check GDPR compliance."""
        findings = []
        
        # Simulate GDPR checks
        findings.append({
            "type": "data_retention",
            "severity": "medium",
            "description": "Some user data lacks proper retention timestamps",
            "count": 15
        })
        
        return findings
    
    async def _check_sox_compliance(self) -> List[Dict[str, Any]]:
        """Check SOX compliance."""
        findings = []
        
        # Simulate SOX checks
        findings.append({
            "type": "access_control",
            "severity": "high",
            "description": "Segregation of duties violation in financial module",
            "count": 3
        })
        
        return findings
    
    async def _check_pci_compliance(self) -> List[Dict[str, Any]]:
        """Check PCI DSS compliance."""
        findings = []
        
        # Simulate PCI checks
        findings.append({
            "type": "encryption",
            "severity": "low",
            "description": "Some payment logs lack proper encryption",
            "count": 8
        })
        
        return findings
    
    async def _check_iso27001_compliance(self) -> List[Dict[str, Any]]:
        """Check ISO27001 compliance."""
        findings = []
        
        # Simulate ISO27001 checks
        findings.append({
            "type": "risk_assessment",
            "severity": "medium",
            "description": "Annual risk assessment documentation incomplete",
            "count": 1
        })
        
        return findings
    
    def _generate_remediation_actions(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate remediation actions for findings."""
        actions = []
        
        for finding in findings:
            if finding["type"] == "data_retention":
                actions.append("Update data retention policies and add timestamps")
            elif finding["type"] == "access_control":
                actions.append("Review and fix segregation of duties violations")
            elif finding["type"] == "encryption":
                actions.append("Implement encryption for identified data")
            elif finding["type"] == "risk_assessment":
                actions.append("Complete missing risk assessment documentation")
        
        return actions


class SecurityComplianceManager:
    """Main security and compliance management system."""
    
    def __init__(self):
        """Initialize security compliance manager."""
        self.security_policies: Dict[str, SecurityPolicy] = {}
        self.data_classifier = DataClassificationEngine()
        self.encryption_manager = EncryptionManager()
        self.threat_detector = ThreatDetectionEngine()
        self.compliance_engine = ComplianceEngine()
        self.audit_trail: deque = deque(maxlen=10000)
        
        self._initialize_default_policies()
    
    def _initialize_default_policies(self) -> None:
        """Initialize default security policies."""
        default_policies = [
            {
                "name": "Data Classification Policy",
                "description": "Mandatory data classification for all organizational data",
                "compliance_standards": [ComplianceStandard.GDPR, ComplianceStandard.ISO27001],
                "security_level": SecurityLevel.INTERNAL,
                "rules": [
                    {"type": "classification_required", "applies_to": "all_data"},
                    {"type": "retention_limit", "duration_days": 2555}  # 7 years
                ]
            },
            {
                "name": "Access Control Policy",
                "description": "Role-based access control and authentication requirements",
                "compliance_standards": [ComplianceStandard.SOX, ComplianceStandard.SOC2],
                "security_level": SecurityLevel.CONFIDENTIAL,
                "rules": [
                    {"type": "mfa_required", "applies_to": "admin_users"},
                    {"type": "session_timeout", "duration_minutes": 30}
                ]
            },
            {
                "name": "Encryption Policy",
                "description": "Data encryption requirements for sensitive information",
                "compliance_standards": [ComplianceStandard.PCI_DSS, ComplianceStandard.HIPAA],
                "security_level": SecurityLevel.RESTRICTED,
                "rules": [
                    {"type": "encryption_at_rest", "algorithm": "AES-256"},
                    {"type": "encryption_in_transit", "protocol": "TLS 1.3"}
                ]
            }
        ]
        
        for policy_data in default_policies:
            policy = SecurityPolicy(
                id=str(uuid4()),
                name=policy_data["name"],
                description=policy_data["description"],
                compliance_standards=policy_data["compliance_standards"],
                security_level=policy_data["security_level"],
                rules=policy_data["rules"]
            )
            self.security_policies[policy.id] = policy
    
    # Policy Management
    async def create_security_policy(self, policy: SecurityPolicy) -> str:
        """Create a new security policy."""
        self.security_policies[policy.id] = policy
        
        self._log_audit_event("security_policy_created", {
            "policy_id": policy.id,
            "policy_name": policy.name,
            "security_level": policy.security_level.value
        })
        
        return policy.id
    
    async def get_security_policy(self, policy_id: str) -> Optional[SecurityPolicy]:
        """Get security policy by ID."""
        return self.security_policies.get(policy_id)
    
    async def list_security_policies(
        self,
        compliance_standard: Optional[ComplianceStandard] = None
    ) -> List[SecurityPolicy]:
        """List security policies."""
        policies = list(self.security_policies.values())
        
        if compliance_standard:
            policies = [
                p for p in policies 
                if compliance_standard in p.compliance_standards
            ]
        
        return policies
    
    # Incident Management
    async def report_security_incident(
        self,
        incident_type: IncidentType,
        threat_level: ThreatLevel,
        title: str,
        description: str,
        affected_systems: List[str] = None,
        affected_users: List[str] = None
    ) -> str:
        """Report a security incident."""
        incident = SecurityIncident(
            id=str(uuid4()),
            incident_type=incident_type,
            threat_level=threat_level,
            title=title,
            description=description,
            affected_systems=affected_systems or [],
            affected_users=affected_users or []
        )
        
        self.threat_detector.active_threats[incident.id] = incident
        
        self._log_audit_event("security_incident_reported", {
            "incident_id": incident.id,
            "incident_type": incident_type.value,
            "threat_level": threat_level.value
        })
        
        return incident.id
    
    # Security Analysis
    async def analyze_security_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Optional[str]:
        """Analyze security event and potentially create incident."""
        incident = await self.threat_detector.analyze_security_event(
            event_type, event_data, user_id
        )
        
        if incident:
            self._log_audit_event("security_threat_detected", {
                "incident_id": incident.id,
                "event_type": event_type,
                "threat_score": incident.metadata.get("threat_score", 0)
            })
            return incident.id
        
        return None
    
    # Compliance Management
    async def run_compliance_assessment(
        self,
        standard: Optional[ComplianceStandard] = None
    ) -> Dict[str, Any]:
        """Run comprehensive compliance assessment."""
        results = {}
        total_score = 0
        check_count = 0
        
        for check_id, check in self.compliance_engine.compliance_checks.items():
            if standard and check.standard != standard:
                continue
            
            result = await self.compliance_engine.run_compliance_check(check_id)
            results[check_id] = {
                "check_name": check.name,
                "standard": check.standard.value,
                "passed": result.passed,
                "score": result.score,
                "findings_count": len(result.findings)
            }
            
            total_score += result.score
            check_count += 1
        
        overall_score = total_score / check_count if check_count > 0 else 0
        
        self._log_audit_event("compliance_assessment_completed", {
            "standard": standard.value if standard else "all",
            "overall_score": overall_score,
            "checks_performed": check_count
        })
        
        return {
            "overall_score": overall_score,
            "checks_performed": check_count,
            "results": results,
            "assessment_date": datetime.utcnow().isoformat()
        }
    
    # System Status
    async def get_security_dashboard(self) -> Dict[str, Any]:
        """Get security and compliance dashboard data."""
        active_incidents = len(self.threat_detector.active_threats)
        critical_incidents = len([
            i for i in self.threat_detector.active_threats.values()
            if i.threat_level == ThreatLevel.CRITICAL
        ])
        
        recent_compliance_results = [
            r for r in self.compliance_engine.compliance_results.values()
            if r.executed_at > datetime.utcnow() - timedelta(days=30)
        ]
        
        avg_compliance_score = (
            sum(r.score for r in recent_compliance_results) / len(recent_compliance_results)
            if recent_compliance_results else 0
        )
        
        return {
            "security_status": {
                "active_incidents": active_incidents,
                "critical_incidents": critical_incidents,
                "security_policies": len(self.security_policies),
                "encryption_keys": len(self.encryption_manager.encryption_keys)
            },
            "compliance_status": {
                "average_score": avg_compliance_score,
                "recent_assessments": len(recent_compliance_results),
                "compliance_checks": len(self.compliance_engine.compliance_checks),
                "policy_violations": len(self.compliance_engine.policy_violations)
            },
            "data_classification": {
                "classified_assets": len(self.data_classifier.data_inventory),
                "classification_rules": len(self.data_classifier.classification_rules)
            },
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def _log_audit_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Log audit event."""
        self.audit_trail.append({
            "event_type": event_type,
            "event_data": event_data,
            "timestamp": datetime.utcnow().isoformat(),
            "event_id": str(uuid4())
        })


# Global security compliance manager instance
security_manager = SecurityComplianceManager()


# Health check for security compliance system
async def check_security_compliance_health() -> Dict[str, Any]:
    """Check security compliance system health."""
    dashboard = await security_manager.get_security_dashboard()
    
    # Determine health status
    health_status = "healthy"
    
    if dashboard["security_status"]["critical_incidents"] > 0:
        health_status = "critical"
    elif dashboard["security_status"]["active_incidents"] > 5:
        health_status = "degraded"
    elif dashboard["compliance_status"]["average_score"] < 70:
        health_status = "warning"
    
    return {
        "status": health_status,
        "dashboard": dashboard,
        "audit_trail_entries": len(security_manager.audit_trail),
        "threat_detection_rules": len(security_manager.threat_detector.detection_rules)
    }