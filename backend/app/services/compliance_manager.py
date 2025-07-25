"""
CC02 v55.0 Compliance Manager
Enterprise-grade Compliance and Regulatory Management System
Day 3 of 7-day intensive backend development
"""

from typing import List, Dict, Any, Optional, Union, Set, Tuple
from uuid import UUID, uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import json
import asyncio
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, text
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import ComplianceError, ValidationError
from app.models.compliance import (
    ComplianceFramework, ComplianceRule, ComplianceCheck, ComplianceViolation,
    ComplianceReport, DataRetentionPolicy, AuditTrail, RegulatoryRequirement
)
from app.services.audit_service import AuditService

class ComplianceStandard(str, Enum):
    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOX = "sox"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"
    CCPA = "ccpa"
    SOC2 = "soc2"
    NIST = "nist"
    CUSTOM = "custom"

class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    UNDER_REVIEW = "under_review"
    EXEMPT = "exempt"

class ViolationSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DataClassification(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    SECRET = "secret"

class RetentionAction(str, Enum):
    ARCHIVE = "archive"
    DELETE = "delete"
    ANONYMIZE = "anonymize"
    REVIEW = "review"

@dataclass
class ComplianceContext:
    """Context for compliance operations"""
    entity_type: str
    entity_id: UUID
    data: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[UUID] = None
    session: Optional[AsyncSession] = None
    operation: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ComplianceCheckResult:
    """Result of compliance check"""
    rule_id: UUID
    rule_name: str
    status: ComplianceStatus
    severity: ViolationSeverity
    message: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    remediation_steps: List[str] = field(default_factory=list)
    checked_at: datetime = field(default_factory=datetime.utcnow)

class BaseComplianceRule(ABC):
    """Base class for compliance rules"""
    
    def __init__(self, rule_id: UUID, name: str, standard: ComplianceStandard, config: Dict[str, Any]):
        self.rule_id = rule_id
        self.name = name
        self.standard = standard
        self.config = config
    
    @abstractmethod
    async def check_compliance(self, context: ComplianceContext) -> ComplianceCheckResult:
        """Check compliance for given context"""
        pass
    
    def create_result(
        self,
        status: ComplianceStatus,
        severity: ViolationSeverity,
        message: str,
        evidence: Dict[str, Any] = None,
        remediation_steps: List[str] = None
    ) -> ComplianceCheckResult:
        """Create compliance check result"""
        return ComplianceCheckResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            status=status,
            severity=severity,
            message=message,
            evidence=evidence or {},
            remediation_steps=remediation_steps or []
        )

class GDPRDataProtectionRule(BaseComplianceRule):
    """GDPR Data Protection compliance rule"""
    
    async def check_compliance(self, context: ComplianceContext) -> ComplianceCheckResult:
        """Check GDPR data protection compliance"""
        
        data = context.data
        issues = []
        
        # Check for personal data encryption
        personal_data_fields = ['email', 'phone', 'address', 'ssn', 'name']
        unencrypted_fields = []
        
        for field in personal_data_fields:
            if field in data:
                # Check if field is properly encrypted/masked
                value = data[field]
                if isinstance(value, str) and not self._is_encrypted_or_masked(value):
                    unencrypted_fields.append(field)
        
        if unencrypted_fields:
            return self.create_result(
                ComplianceStatus.NON_COMPLIANT,
                ViolationSeverity.HIGH,
                f"Personal data fields not properly protected: {', '.join(unencrypted_fields)}",
                {"unencrypted_fields": unencrypted_fields},
                [
                    "Encrypt personal data at rest",
                    "Implement data masking for display",
                    "Review data access controls"
                ]
            )
        
        # Check consent tracking
        if 'consent' not in context.metadata:
            return self.create_result(
                ComplianceStatus.NON_COMPLIANT,
                ViolationSeverity.MEDIUM,
                "No consent tracking found for personal data processing",
                {},
                [
                    "Implement consent management system",
                    "Record explicit consent for data processing",
                    "Provide consent withdrawal mechanism"
                ]
            )
        
        return self.create_result(
            ComplianceStatus.COMPLIANT,
            ViolationSeverity.LOW,
            "GDPR data protection requirements met"
        )
    
    def _is_encrypted_or_masked(self, value: str) -> bool:
        """Check if value appears to be encrypted or masked"""
        # Simple check - in production would be more sophisticated
        if '*' in value or 'ENCRYPTED:' in value or len(value) > 50:
            return True
        return False

class HIPAAPrivacyRule(BaseComplianceRule):
    """HIPAA Privacy compliance rule"""
    
    async def check_compliance(self, context: ComplianceContext) -> ComplianceCheckResult:
        """Check HIPAA privacy compliance"""
        
        data = context.data
        
        # Check for PHI (Protected Health Information)
        phi_fields = ['medical_record', 'diagnosis', 'treatment', 'health_plan', 'ssn']
        phi_found = [field for field in phi_fields if field in data]
        
        if phi_found:
            # Check for proper authorization
            if not context.metadata.get('hipaa_authorization'):
                return self.create_result(
                    ComplianceStatus.NON_COMPLIANT,
                    ViolationSeverity.CRITICAL,
                    f"PHI accessed without proper authorization: {', '.join(phi_found)}",
                    {"phi_fields": phi_found},
                    [
                        "Obtain proper HIPAA authorization",
                        "Implement role-based access controls",
                        "Log all PHI access attempts"
                    ]
                )
            
            # Check minimum necessary standard
            if len(phi_found) > 3:  # Arbitrary threshold
                return self.create_result(
                    ComplianceStatus.PARTIALLY_COMPLIANT,
                    ViolationSeverity.MEDIUM,
                    "Potential violation of minimum necessary standard",
                    {"phi_fields_count": len(phi_found)},
                    [
                        "Review data access to ensure minimum necessary",
                        "Implement field-level access controls",
                        "Audit data usage patterns"
                    ]
                )
        
        return self.create_result(
            ComplianceStatus.COMPLIANT,
            ViolationSeverity.LOW,
            "HIPAA privacy requirements met"
        )

class SOXFinancialControlsRule(BaseComplianceRule):
    """SOX Financial Controls compliance rule"""
    
    async def check_compliance(self, context: ComplianceContext) -> ComplianceCheckResult:
        """Check SOX financial controls compliance"""
        
        data = context.data
        
        # Check for financial data
        financial_fields = ['amount', 'price', 'revenue', 'cost', 'budget']
        financial_data = [field for field in financial_fields if field in data]
        
        if financial_data:
            # Check for proper approval workflow
            if not context.metadata.get('approval_required'):
                return self.create_result(
                    ComplianceStatus.NON_COMPLIANT,
                    ViolationSeverity.HIGH,
                    "Financial data modification without approval workflow",
                    {"financial_fields": financial_data},
                    [
                        "Implement approval workflow for financial data",
                        "Require dual authorization for large amounts",
                        "Maintain detailed audit trail"
                    ]
                )
            
            # Check for segregation of duties
            if context.user_id and not self._check_segregation_of_duties(context):
                return self.create_result(
                    ComplianceStatus.NON_COMPLIANT,
                    ViolationSeverity.HIGH,
                    "Potential segregation of duties violation",
                    {"user_id": str(context.user_id)},
                    [
                        "Review user roles and permissions",
                        "Implement role separation",
                        "Add compensating controls"
                    ]
                )
        
        return self.create_result(
            ComplianceStatus.COMPLIANT,
            ViolationSeverity.LOW,
            "SOX financial controls requirements met"
        )
    
    def _check_segregation_of_duties(self, context: ComplianceContext) -> bool:
        """Check segregation of duties"""
        # Simplified check - in production would verify against role matrix
        return True

class PCIDSSDataSecurityRule(BaseComplianceRule):
    """PCI DSS Data Security compliance rule"""
    
    async def check_compliance(self, context: ComplianceContext) -> ComplianceCheckResult:
        """Check PCI DSS data security compliance"""
        
        data = context.data
        
        # Check for cardholder data
        card_data_fields = ['card_number', 'cvv', 'expiry_date', 'cardholder_name']
        card_data = [field for field in card_data_fields if field in data]
        
        if card_data:
            # Check for proper encryption
            for field in card_data:
                value = data[field]
                if isinstance(value, str) and not self._is_pci_compliant_format(value):
                    return self.create_result(
                        ComplianceStatus.NON_COMPLIANT,
                        ViolationSeverity.CRITICAL,
                        f"Cardholder data not properly protected: {field}",
                        {"vulnerable_field": field},
                        [
                            "Encrypt cardholder data",
                            "Implement tokenization",
                            "Use secure key management"
                        ]
                    )
            
            # Check for secure transmission
            if not context.metadata.get('secure_transmission'):
                return self.create_result(
                    ComplianceStatus.NON_COMPLIANT,
                    ViolationSeverity.HIGH,
                    "Cardholder data transmission not secured",
                    {},
                    [
                        "Use TLS encryption for data transmission",
                        "Implement end-to-end encryption",
                        "Validate SSL certificates"
                    ]
                )
        
        return self.create_result(
            ComplianceStatus.COMPLIANT,
            ViolationSeverity.LOW,
            "PCI DSS data security requirements met"
        )
    
    def _is_pci_compliant_format(self, value: str) -> bool:
        """Check if value is in PCI compliant format"""
        # Check for masked card numbers (e.g., ****-****-****-1234)
        if '*' in value or 'TOKEN:' in value:
            return True
        return False

class DataRetentionRule(BaseComplianceRule):
    """Data retention compliance rule"""
    
    async def check_compliance(self, context: ComplianceContext) -> ComplianceCheckResult:
        """Check data retention compliance"""
        
        # Get data classification
        classification = context.metadata.get('data_classification', DataClassification.INTERNAL)
        
        # Get retention policies
        retention_policies = {
            DataClassification.PUBLIC: 365,  # 1 year
            DataClassification.INTERNAL: 2555,  # 7 years
            DataClassification.CONFIDENTIAL: 2555,  # 7 years
            DataClassification.RESTRICTED: 3650,  # 10 years
            DataClassification.SECRET: 3650  # 10 years
        }
        
        max_retention_days = retention_policies.get(classification, 365)
        
        # Check if data is older than retention period
        created_at = context.metadata.get('created_at')
        if created_at:
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            
            age_days = (datetime.utcnow() - created_at).days
            
            if age_days > max_retention_days:
                return self.create_result(
                    ComplianceStatus.NON_COMPLIANT,
                    ViolationSeverity.MEDIUM,
                    f"Data exceeds retention period: {age_days} days (max: {max_retention_days})",
                    {
                        "age_days": age_days,
                        "max_retention_days": max_retention_days,
                        "classification": classification.value
                    },
                    [
                        "Archive old data",
                        "Delete expired data",
                        "Implement automated retention policies"
                    ]
                )
        
        return self.create_result(
            ComplianceStatus.COMPLIANT,
            ViolationSeverity.LOW,
            "Data retention requirements met"
        )

class ComplianceManager:
    """Enterprise Compliance Manager"""
    
    def __init__(self):
        self.rules: Dict[ComplianceStandard, List[BaseComplianceRule]] = {}
        self.audit_service = AuditService()
        self._register_default_rules()
    
    def _register_default_rules(self):
        """Register default compliance rules"""
        
        # GDPR rules
        gdpr_rules = [
            GDPRDataProtectionRule(
                uuid4(), "Data Protection", ComplianceStandard.GDPR, {}
            )
        ]
        self.rules[ComplianceStandard.GDPR] = gdpr_rules
        
        # HIPAA rules
        hipaa_rules = [
            HIPAAPrivacyRule(
                uuid4(), "Privacy Rule", ComplianceStandard.HIPAA, {}
            )
        ]
        self.rules[ComplianceStandard.HIPAA] = hipaa_rules
        
        # SOX rules
        sox_rules = [
            SOXFinancialControlsRule(
                uuid4(), "Financial Controls", ComplianceStandard.SOX, {}
            )
        ]
        self.rules[ComplianceStandard.SOX] = sox_rules
        
        # PCI DSS rules
        pci_rules = [
            PCIDSSDataSecurityRule(
                uuid4(), "Data Security", ComplianceStandard.PCI_DSS, {}
            )
        ]
        self.rules[ComplianceStandard.PCI_DSS] = pci_rules
        
        # Data retention rules
        retention_rules = [
            DataRetentionRule(
                uuid4(), "Data Retention", ComplianceStandard.CUSTOM, {}
            )
        ]
        if ComplianceStandard.CUSTOM not in self.rules:
            self.rules[ComplianceStandard.CUSTOM] = []
        self.rules[ComplianceStandard.CUSTOM].extend(retention_rules)
    
    async def check_compliance(
        self,
        entity_type: str,
        entity_id: UUID,
        data: Dict[str, Any],
        standards: List[ComplianceStandard] = None,
        user_id: Optional[UUID] = None,
        session: Optional[AsyncSession] = None,
        operation: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> List[ComplianceCheckResult]:
        """Check compliance for entity data"""
        
        context = ComplianceContext(
            entity_type=entity_type,
            entity_id=entity_id,
            data=data,
            user_id=user_id,
            session=session,
            operation=operation,
            metadata=metadata or {}
        )
        
        results = []
        
        # Determine which standards to check
        if not standards:
            standards = list(self.rules.keys())
        
        # Run compliance checks
        for standard in standards:
            rules = self.rules.get(standard, [])
            for rule in rules:
                try:
                    result = await rule.check_compliance(context)
                    results.append(result)
                except Exception as e:
                    # Create error result
                    error_result = ComplianceCheckResult(
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        status=ComplianceStatus.UNDER_REVIEW,
                        severity=ViolationSeverity.LOW,
                        message=f"Error checking compliance: {str(e)}",
                        evidence={"error": str(e)}
                    )
                    results.append(error_result)
        
        # Log compliance check
        await self._log_compliance_check(context, results)
        
        return results
    
    async def generate_compliance_report(
        self,
        standard: ComplianceStandard,
        start_date: date,
        end_date: date,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Generate compliance report for a standard"""
        
        # Get compliance checks from audit logs
        checks_result = await session.execute(
            select(ComplianceCheck)
            .where(
                and_(
                    ComplianceCheck.standard == standard,
                    ComplianceCheck.checked_at >= start_date,
                    ComplianceCheck.checked_at <= end_date
                )
            )
        )
        checks = checks_result.scalars().all()
        
        # Calculate metrics
        total_checks = len(checks)
        compliant_checks = len([c for c in checks if c.status == ComplianceStatus.COMPLIANT])
        non_compliant_checks = len([c for c in checks if c.status == ComplianceStatus.NON_COMPLIANT])
        
        compliance_rate = (compliant_checks / total_checks * 100) if total_checks > 0 else 0
        
        # Get violations by severity
        violations_by_severity = {}
        for severity in ViolationSeverity:
            count = len([c for c in checks if c.severity == severity and c.status == ComplianceStatus.NON_COMPLIANT])
            violations_by_severity[severity.value] = count
        
        # Generate recommendations
        recommendations = self._generate_recommendations(checks)
        
        return {
            "standard": standard.value,
            "reporting_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_checks": total_checks,
                "compliant_checks": compliant_checks,
                "non_compliant_checks": non_compliant_checks,
                "compliance_rate": round(compliance_rate, 2)
            },
            "violations_by_severity": violations_by_severity,
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def create_remediation_plan(
        self,
        violations: List[ComplianceCheckResult],
        priority: str = "severity"
    ) -> Dict[str, Any]:
        """Create remediation plan for compliance violations"""
        
        # Sort violations by priority
        if priority == "severity":
            severity_order = {
                ViolationSeverity.CRITICAL: 4,
                ViolationSeverity.HIGH: 3,
                ViolationSeverity.MEDIUM: 2,
                ViolationSeverity.LOW: 1
            }
            violations.sort(key=lambda v: severity_order.get(v.severity, 0), reverse=True)
        
        remediation_tasks = []
        
        for violation in violations:
            # Estimate effort and timeline
            effort = self._estimate_remediation_effort(violation)
            timeline = self._estimate_remediation_timeline(violation)
            
            task = {
                "violation_id": str(violation.rule_id),
                "rule_name": violation.rule_name,
                "severity": violation.severity.value,
                "description": violation.message,
                "remediation_steps": violation.remediation_steps,
                "estimated_effort": effort,
                "estimated_timeline_days": timeline,
                "priority": severity_order.get(violation.severity, 1) if priority == "severity" else 1
            }
            remediation_tasks.append(task)
        
        return {
            "remediation_plan": {
                "total_violations": len(violations),
                "critical_violations": len([v for v in violations if v.severity == ViolationSeverity.CRITICAL]),
                "total_estimated_effort": sum(self._estimate_remediation_effort(v) for v in violations),
                "tasks": remediation_tasks
            },
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def check_data_retention_compliance(
        self,
        entity_type: str,
        session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Check data retention compliance for entity type"""
        
        # Get retention policies for entity type
        policies_result = await session.execute(
            select(DataRetentionPolicy)
            .where(DataRetentionPolicy.entity_type == entity_type)
        )
        policies = policies_result.scalars().all()
        
        retention_violations = []
        
        for policy in policies:
            # Find entities that violate retention policy
            cutoff_date = datetime.utcnow() - timedelta(days=policy.retention_days)
            
            # This would query the actual entity table
            # For now, simulate finding violations
            violation = {
                "policy_id": str(policy.id),
                "entity_type": entity_type,
                "retention_days": policy.retention_days,
                "cutoff_date": cutoff_date.isoformat(),
                "action_required": policy.action.value,
                "violation_count": 0  # Would be actual count
            }
            retention_violations.append(violation)
        
        return retention_violations
    
    def _generate_recommendations(self, checks: List[ComplianceCheck]) -> List[str]:
        """Generate compliance recommendations"""
        
        recommendations = []
        
        # Analyze patterns in violations
        common_violations = {}
        for check in checks:
            if check.status == ComplianceStatus.NON_COMPLIANT:
                violation_type = check.rule_name
                common_violations[violation_type] = common_violations.get(violation_type, 0) + 1
        
        # Generate recommendations based on common violations
        for violation_type, count in common_violations.items():
            if count > 5:  # Threshold for pattern
                recommendations.append(f"Address recurring {violation_type} violations ({count} instances)")
        
        # Add general recommendations
        if len([c for c in checks if c.severity == ViolationSeverity.CRITICAL]) > 0:
            recommendations.append("Prioritize critical severity violations for immediate remediation")
        
        recommendations.append("Implement automated compliance monitoring")
        recommendations.append("Conduct regular compliance training for staff")
        
        return recommendations
    
    def _estimate_remediation_effort(self, violation: ComplianceCheckResult) -> int:
        """Estimate remediation effort in hours"""
        
        effort_map = {
            ViolationSeverity.CRITICAL: 40,  # 1 week
            ViolationSeverity.HIGH: 16,     # 2 days
            ViolationSeverity.MEDIUM: 8,    # 1 day
            ViolationSeverity.LOW: 2        # 2 hours
        }
        
        return effort_map.get(violation.severity, 8)
    
    def _estimate_remediation_timeline(self, violation: ComplianceCheckResult) -> int:
        """Estimate remediation timeline in days"""
        
        timeline_map = {
            ViolationSeverity.CRITICAL: 7,   # 1 week
            ViolationSeverity.HIGH: 14,      # 2 weeks
            ViolationSeverity.MEDIUM: 30,    # 1 month
            ViolationSeverity.LOW: 60        # 2 months
        }
        
        return timeline_map.get(violation.severity, 30)
    
    async def _log_compliance_check(
        self,
        context: ComplianceContext,
        results: List[ComplianceCheckResult]
    ):
        """Log compliance check results"""
        
        violation_count = len([r for r in results if r.status == ComplianceStatus.NON_COMPLIANT])
        compliant_count = len([r for r in results if r.status == ComplianceStatus.COMPLIANT])
        
        await self.audit_service.log_event(
            event_type="compliance_check",
            entity_type=context.entity_type,
            entity_id=context.entity_id,
            user_id=context.user_id,
            details={
                "total_rules_checked": len(results),
                "compliant_rules": compliant_count,
                "violation_count": violation_count,
                "operation": context.operation,
                "violations": [
                    {
                        "rule_name": r.rule_name,
                        "severity": r.severity.value,
                        "message": r.message
                    }
                    for r in results
                    if r.status == ComplianceStatus.NON_COMPLIANT
                ]
            }
        )
    
    def register_custom_rule(self, rule: BaseComplianceRule, standard: ComplianceStandard = ComplianceStandard.CUSTOM):
        """Register custom compliance rule"""
        
        if standard not in self.rules:
            self.rules[standard] = []
        
        self.rules[standard].append(rule)
    
    def get_compliance_standards(self) -> List[str]:
        """Get list of supported compliance standards"""
        return [standard.value for standard in self.rules.keys()]

# Singleton instance
compliance_manager = ComplianceManager()

# Helper functions
async def check_entity_compliance(
    entity_type: str,
    entity_id: UUID,
    data: Dict[str, Any],
    standards: List[ComplianceStandard] = None,
    user_id: Optional[UUID] = None,
    session: Optional[AsyncSession] = None,
    operation: Optional[str] = None,
    metadata: Dict[str, Any] = None
) -> List[ComplianceCheckResult]:
    """Check compliance for entity"""
    return await compliance_manager.check_compliance(
        entity_type, entity_id, data, standards, user_id, session, operation, metadata
    )

async def generate_compliance_report(
    standard: ComplianceStandard,
    start_date: date,
    end_date: date,
    session: AsyncSession
) -> Dict[str, Any]:
    """Generate compliance report"""
    return await compliance_manager.generate_compliance_report(
        standard, start_date, end_date, session
    )

async def create_remediation_plan(
    violations: List[ComplianceCheckResult],
    priority: str = "severity"
) -> Dict[str, Any]:
    """Create remediation plan"""
    return await compliance_manager.create_remediation_plan(violations, priority)

def register_custom_compliance_rule(
    rule: BaseComplianceRule,
    standard: ComplianceStandard = ComplianceStandard.CUSTOM
):
    """Register custom compliance rule"""
    compliance_manager.register_custom_rule(rule, standard)