"""Enterprise Security & Compliance API endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.core.security_compliance import (
    security_manager,
    SecurityPolicy,
    ComplianceStandard,
    SecurityLevel,
    ThreatLevel,
    IncidentType,
    check_security_compliance_health,
)
from app.models.user import User

router = APIRouter()


# Pydantic schemas
class SecurityPolicyRequest(BaseModel):
    """Security policy creation request."""
    name: str = Field(..., max_length=200)
    description: str = Field(..., max_length=1000)
    compliance_standards: List[ComplianceStandard]
    security_level: SecurityLevel
    rules: List[Dict[str, Any]] = []
    enabled: bool = True


class SecurityPolicyResponse(BaseModel):
    """Security policy response schema."""
    id: str
    name: str
    description: str
    compliance_standards: List[str]
    security_level: str
    rules: List[Dict[str, Any]]
    enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SecurityIncidentRequest(BaseModel):
    """Security incident report request."""
    incident_type: IncidentType
    threat_level: ThreatLevel
    title: str = Field(..., max_length=200)
    description: str = Field(..., max_length=2000)
    affected_systems: Optional[List[str]] = []
    affected_users: Optional[List[str]] = []


class SecurityIncidentResponse(BaseModel):
    """Security incident response schema."""
    id: str
    incident_type: str
    threat_level: str
    title: str
    description: str
    affected_systems: List[str]
    affected_users: List[str]
    detected_at: datetime
    resolved_at: Optional[datetime]
    status: str
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class SecurityEventRequest(BaseModel):
    """Security event analysis request."""
    event_type: str = Field(..., max_length=100)
    event_data: Dict[str, Any]
    user_id: Optional[str] = None


class DataClassificationRequest(BaseModel):
    """Data classification request."""
    data_source: str = Field(..., max_length=200)
    data_type: str = Field(..., max_length=100)
    sample_data: Dict[str, Any]


class DataAssetRegistrationRequest(BaseModel):
    """Data asset registration request."""
    asset_name: str = Field(..., max_length=200)
    data_source: str = Field(..., max_length=200)
    classification: SecurityLevel
    metadata: Dict[str, Any] = {}


class ComplianceAssessmentResponse(BaseModel):
    """Compliance assessment response schema."""
    overall_score: float
    checks_performed: int
    results: Dict[str, Any]
    assessment_date: str


class SecurityDashboardResponse(BaseModel):
    """Security dashboard response schema."""
    security_status: Dict[str, Any]
    compliance_status: Dict[str, Any]
    data_classification: Dict[str, Any]
    last_updated: str


class SecurityHealthResponse(BaseModel):
    """Security health response schema."""
    status: str
    dashboard: SecurityDashboardResponse
    audit_trail_entries: int
    threat_detection_rules: int


# Security Policy Management Endpoints
@router.post("/policies", response_model=SecurityPolicyResponse)
async def create_security_policy(
    policy_request: SecurityPolicyRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new security policy."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        policy = SecurityPolicy(
            id="",  # Will be auto-generated
            name=policy_request.name,
            description=policy_request.description,
            compliance_standards=policy_request.compliance_standards,
            security_level=policy_request.security_level,
            rules=policy_request.rules,
            enabled=policy_request.enabled
        )
        
        policy_id = await security_manager.create_security_policy(policy)
        created_policy = await security_manager.get_security_policy(policy_id)
        
        return SecurityPolicyResponse(
            id=created_policy.id,
            name=created_policy.name,
            description=created_policy.description,
            compliance_standards=[cs.value for cs in created_policy.compliance_standards],
            security_level=created_policy.security_level.value,
            rules=created_policy.rules,
            enabled=created_policy.enabled,
            created_at=created_policy.created_at,
            updated_at=created_policy.updated_at
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create security policy: {str(e)}"
        )


@router.get("/policies", response_model=List[SecurityPolicyResponse])
async def list_security_policies(
    compliance_standard: Optional[ComplianceStandard] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """List security policies."""
    try:
        policies = await security_manager.list_security_policies(compliance_standard)
        
        return [
            SecurityPolicyResponse(
                id=policy.id,
                name=policy.name,
                description=policy.description,
                compliance_standards=[cs.value for cs in policy.compliance_standards],
                security_level=policy.security_level.value,
                rules=policy.rules,
                enabled=policy.enabled,
                created_at=policy.created_at,
                updated_at=policy.updated_at
            )
            for policy in policies
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve security policies: {str(e)}"
        )


@router.get("/policies/{policy_id}", response_model=SecurityPolicyResponse)
async def get_security_policy(
    policy_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific security policy."""
    try:
        policy = await security_manager.get_security_policy(policy_id)
        
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Security policy not found"
            )
        
        return SecurityPolicyResponse(
            id=policy.id,
            name=policy.name,
            description=policy.description,
            compliance_standards=[cs.value for cs in policy.compliance_standards],
            security_level=policy.security_level.value,
            rules=policy.rules,
            enabled=policy.enabled,
            created_at=policy.created_at,
            updated_at=policy.updated_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve security policy: {str(e)}"
        )


# Incident Management Endpoints
@router.post("/incidents")
async def report_security_incident(
    incident_request: SecurityIncidentRequest,
    current_user: User = Depends(get_current_user)
):
    """Report a security incident."""
    try:
        incident_id = await security_manager.report_security_incident(
            incident_type=incident_request.incident_type,
            threat_level=incident_request.threat_level,
            title=incident_request.title,
            description=incident_request.description,
            affected_systems=incident_request.affected_systems or [],
            affected_users=incident_request.affected_users or []
        )
        
        return {
            "message": "Security incident reported successfully",
            "incident_id": incident_id,
            "reported_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to report security incident: {str(e)}"
        )


@router.get("/incidents")
async def list_security_incidents(
    threat_level: Optional[ThreatLevel] = Query(None),
    incident_type: Optional[IncidentType] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """List security incidents."""
    try:
        active_threats = security_manager.threat_detector.active_threats
        
        incidents = []
        for incident in active_threats.values():
            # Apply filters
            if threat_level and incident.threat_level != threat_level:
                continue
            if incident_type and incident.incident_type != incident_type:
                continue
            
            incidents.append(SecurityIncidentResponse(
                id=incident.id,
                incident_type=incident.incident_type.value,
                threat_level=incident.threat_level.value,
                title=incident.title,
                description=incident.description,
                affected_systems=incident.affected_systems,
                affected_users=incident.affected_users,
                detected_at=incident.detected_at,
                resolved_at=incident.resolved_at,
                status=incident.status,
                metadata=incident.metadata
            ))
        
        return {
            "incidents": incidents,
            "total_count": len(incidents),
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve security incidents: {str(e)}"
        )


# Threat Detection Endpoints
@router.post("/events/analyze")
async def analyze_security_event(
    event_request: SecurityEventRequest,
    current_user: User = Depends(get_current_user)
):
    """Analyze a security event for potential threats."""
    try:
        incident_id = await security_manager.analyze_security_event(
            event_type=event_request.event_type,
            event_data=event_request.event_data,
            user_id=event_request.user_id
        )
        
        if incident_id:
            return {
                "threat_detected": True,
                "incident_id": incident_id,
                "message": "Security threat detected and incident created",
                "analyzed_at": datetime.utcnow().isoformat()
            }
        else:
            return {
                "threat_detected": False,
                "message": "No security threat detected",
                "analyzed_at": datetime.utcnow().isoformat()
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze security event: {str(e)}"
        )


# Data Classification Endpoints
@router.post("/data/classify")
async def classify_data(
    classification_request: DataClassificationRequest,
    current_user: User = Depends(get_current_user)
):
    """Classify data and determine security level."""
    try:
        classification = await security_manager.data_classifier.classify_data(
            data_source=classification_request.data_source,
            data_type=classification_request.data_type,
            sample_data=classification_request.sample_data
        )
        
        return {
            "data_source": classification_request.data_source,
            "data_type": classification_request.data_type,
            "classification": classification.value,
            "classified_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to classify data: {str(e)}"
        )


@router.post("/data/assets/register")
async def register_data_asset(
    asset_request: DataAssetRegistrationRequest,
    current_user: User = Depends(get_current_user)
):
    """Register a data asset in the inventory."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        asset_id = str(len(security_manager.data_classifier.data_inventory) + 1)
        
        await security_manager.data_classifier.register_data_asset(
            asset_id=asset_id,
            asset_name=asset_request.asset_name,
            data_source=asset_request.data_source,
            classification=asset_request.classification,
            metadata=asset_request.metadata
        )
        
        return {
            "message": "Data asset registered successfully",
            "asset_id": asset_id,
            "asset_name": asset_request.asset_name,
            "classification": asset_request.classification.value,
            "registered_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register data asset: {str(e)}"
        )


@router.get("/data/inventory")
async def get_data_inventory(
    current_user: User = Depends(get_current_user)
):
    """Get data asset inventory."""
    try:
        inventory = await security_manager.data_classifier.get_data_inventory()
        
        return {
            "inventory": inventory,
            "total_assets": len(inventory),
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve data inventory: {str(e)}"
        )


# Compliance Management Endpoints
@router.post("/compliance/assess", response_model=ComplianceAssessmentResponse)
async def run_compliance_assessment(
    standard: Optional[ComplianceStandard] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Run compliance assessment."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        assessment_result = await security_manager.run_compliance_assessment(standard)
        
        return ComplianceAssessmentResponse(
            overall_score=assessment_result["overall_score"],
            checks_performed=assessment_result["checks_performed"],
            results=assessment_result["results"],
            assessment_date=assessment_result["assessment_date"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run compliance assessment: {str(e)}"
        )


@router.get("/compliance/checks")
async def list_compliance_checks(
    standard: Optional[ComplianceStandard] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """List available compliance checks."""
    try:
        checks = security_manager.compliance_engine.compliance_checks
        
        check_list = []
        for check_id, check in checks.items():
            if standard and check.standard != standard:
                continue
            
            check_list.append({
                "id": check.id,
                "name": check.name,
                "standard": check.standard.value,
                "check_type": check.check_type,
                "description": check.description,
                "automated": check.automated,
                "frequency": check.frequency,
                "last_run": check.last_run.isoformat() if check.last_run else None,
                "enabled": check.enabled
            })
        
        return {
            "checks": check_list,
            "total_count": len(check_list),
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve compliance checks: {str(e)}"
        )


# Encryption Management Endpoints
@router.post("/encryption/keys")
async def generate_encryption_key(
    key_id: str = Query(...),
    purpose: str = Query("general"),
    current_user: User = Depends(get_current_user)
):
    """Generate a new encryption key."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        key = security_manager.encryption_manager.generate_key(key_id, purpose)
        
        return {
            "message": "Encryption key generated successfully",
            "key_id": key_id,
            "purpose": purpose,
            "generated_at": datetime.utcnow().isoformat()
            # Note: Key value is not returned for security reasons
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate encryption key: {str(e)}"
        )


@router.post("/encryption/keys/{key_id}/rotate")
async def rotate_encryption_key(
    key_id: str,
    current_user: User = Depends(get_current_user)
):
    """Rotate an encryption key."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        new_key = security_manager.encryption_manager.rotate_key(key_id)
        
        return {
            "message": "Encryption key rotated successfully",
            "key_id": key_id,
            "rotated_at": datetime.utcnow().isoformat()
            # Note: Key value is not returned for security reasons
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rotate encryption key: {str(e)}"
        )


# Dashboard and System Information Endpoints
@router.get("/dashboard", response_model=SecurityDashboardResponse)
async def get_security_dashboard(
    current_user: User = Depends(get_current_user)
):
    """Get security and compliance dashboard."""
    try:
        dashboard_data = await security_manager.get_security_dashboard()
        
        return SecurityDashboardResponse(
            security_status=dashboard_data["security_status"],
            compliance_status=dashboard_data["compliance_status"],
            data_classification=dashboard_data["data_classification"],
            last_updated=dashboard_data["last_updated"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve security dashboard: {str(e)}"
        )


@router.get("/system/types")
async def list_system_types():
    """List available compliance standards, security levels, and threat types."""
    return {
        "compliance_standards": [cs.value for cs in ComplianceStandard],
        "security_levels": [sl.value for sl in SecurityLevel],
        "threat_levels": [tl.value for tl in ThreatLevel],
        "incident_types": [it.value for it in IncidentType]
    }


@router.get("/audit/trail")
async def get_audit_trail(
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """Get security audit trail."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        audit_events = list(security_manager.audit_trail)[-limit:]
        
        return {
            "audit_events": audit_events,
            "total_events": len(security_manager.audit_trail),
            "retrieved_count": len(audit_events),
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit trail: {str(e)}"
        )


# Health check endpoint
@router.get("/health", response_model=SecurityHealthResponse)
async def security_compliance_health_check():
    """Check security and compliance system health."""
    try:
        health_info = await check_security_compliance_health()
        
        dashboard_data = health_info["dashboard"]
        
        return SecurityHealthResponse(
            status=health_info["status"],
            dashboard=SecurityDashboardResponse(
                security_status=dashboard_data["security_status"],
                compliance_status=dashboard_data["compliance_status"],
                data_classification=dashboard_data["data_classification"],
                last_updated=dashboard_data["last_updated"]
            ),
            audit_trail_entries=health_info["audit_trail_entries"],
            threat_detection_rules=health_info["threat_detection_rules"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Security compliance health check failed: {str(e)}"
        )