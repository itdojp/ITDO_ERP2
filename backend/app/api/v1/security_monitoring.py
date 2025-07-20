"""Security monitoring API endpoints for Issue #46."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.services.security_monitoring import SecurityMonitoringService

router = APIRouter()


@router.get("/dashboard")
async def get_security_dashboard(
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get real-time security monitoring dashboard."""
    # Check permissions - only admins and security officers
    if not (current_user.is_superuser or "security_admin" in getattr(current_user, "roles", [])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for security monitoring"
        )

    # Use user's organization if not specified and not superuser
    if not current_user.is_superuser and organization_id is None:
        organization_id = current_user.organization_id

    service = SecurityMonitoringService(db)
    dashboard_data = await service.get_security_dashboard(organization_id)
    
    return dashboard_data


@router.get("/threats")
async def get_current_threats(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    ip_address: Optional[str] = Query(None, description="Filter by IP address"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get current security threats."""
    # Check permissions
    if not (current_user.is_superuser or "security_admin" in getattr(current_user, "roles", [])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for security monitoring"
        )

    service = SecurityMonitoringService(db)
    
    # Collect all threats
    threats = []
    threats.extend(await service.monitor_failed_logins(user_id, ip_address))
    threats.extend(await service.monitor_bulk_data_access(user_id))
    threats.extend(await service.monitor_privilege_escalation(user_id))
    threats.extend(await service.monitor_unusual_access_patterns(user_id))
    
    # Filter by severity if specified
    if severity:
        threats = [t for t in threats if t.severity == severity]
    
    return {
        "threats": [
            {
                "type": threat.threat_type,
                "severity": threat.severity,
                "description": threat.description,
                "details": threat.details,
                "timestamp": threat.timestamp.isoformat(),
            }
            for threat in threats
        ],
        "total_count": len(threats),
        "filters_applied": {
            "user_id": user_id,
            "ip_address": ip_address,
            "severity": severity,
        },
    }


@router.get("/failed-logins")
async def monitor_failed_logins(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    ip_address: Optional[str] = Query(None, description="Filter by IP address"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Monitor failed login attempts."""
    # Check permissions
    if not (current_user.is_superuser or "security_admin" in getattr(current_user, "roles", [])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for security monitoring"
        )

    service = SecurityMonitoringService(db)
    threats = await service.monitor_failed_logins(user_id, ip_address)
    
    return {
        "failed_login_threats": [
            {
                "type": threat.threat_type,
                "severity": threat.severity,
                "description": threat.description,
                "details": threat.details,
                "timestamp": threat.timestamp.isoformat(),
            }
            for threat in threats
        ],
        "monitoring_config": {
            "threshold": service.FAILED_LOGIN_THRESHOLD,
            "time_window": str(service.FAILED_LOGIN_TIME_WINDOW),
        },
    }


@router.get("/bulk-access")
async def monitor_bulk_access(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Monitor bulk data access patterns."""
    # Check permissions
    if not (current_user.is_superuser or "security_admin" in getattr(current_user, "roles", [])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for security monitoring"
        )

    service = SecurityMonitoringService(db)
    threats = await service.monitor_bulk_data_access(user_id)
    
    return {
        "bulk_access_threats": [
            {
                "type": threat.threat_type,
                "severity": threat.severity,
                "description": threat.description,
                "details": threat.details,
                "timestamp": threat.timestamp.isoformat(),
            }
            for threat in threats
        ],
        "monitoring_config": {
            "threshold": service.BULK_ACCESS_THRESHOLD,
            "time_window": str(service.BULK_ACCESS_TIME_WINDOW),
        },
    }


@router.get("/privilege-escalation")
async def monitor_privilege_escalation(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Monitor privilege escalation attempts."""
    # Check permissions
    if not (current_user.is_superuser or "security_admin" in getattr(current_user, "roles", [])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for security monitoring"
        )

    service = SecurityMonitoringService(db)
    threats = await service.monitor_privilege_escalation(user_id)
    
    return {
        "privilege_escalation_threats": [
            {
                "type": threat.threat_type,
                "severity": threat.severity,
                "description": threat.description,
                "details": threat.details,
                "timestamp": threat.timestamp.isoformat(),
            }
            for threat in threats
        ],
        "monitoring_enabled": service.PRIVILEGE_ESCALATION_MONITORING,
    }


@router.get("/reports/security")
async def generate_security_report(
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    start_date: Optional[datetime] = Query(None, description="Report start date"),
    end_date: Optional[datetime] = Query(None, description="Report end date"),
    format: str = Query("json", description="Export format: json, csv"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Generate comprehensive security report."""
    # Check permissions
    if not (current_user.is_superuser or "security_admin" in getattr(current_user, "roles", [])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for security reporting"
        )

    # Use user's organization if not specified and not superuser
    if not current_user.is_superuser and organization_id is None:
        organization_id = current_user.organization_id

    # Default to last 7 days if no dates specified
    if not start_date:
        start_date = datetime.now(timezone.utc) - timedelta(days=7)
    if not end_date:
        end_date = datetime.now(timezone.utc)

    service = SecurityMonitoringService(db)
    report = await service.generate_security_report(organization_id, start_date, end_date)
    
    return report


@router.post("/alerts/test")
async def test_security_alert(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Test security alert system."""
    # Check permissions - only superusers can test alerts
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can test security alerts"
        )

    # Add background task to test alert system
    background_tasks.add_task(_test_alert_system, current_user, db)
    
    return {"message": "Security alert test initiated"}


async def _test_alert_system(user: User, db: Session) -> None:
    """Background task to test alert system."""
    from app.services.security_monitoring import SecurityThreat
    
    service = SecurityMonitoringService(db)
    
    # Create test threat
    test_threat = SecurityThreat(
        threat_type="test_alert",
        severity=SecurityThreat.MEDIUM,
        description="Test security alert - system functioning normally",
        details={
            "test_initiated_by": user.id,
            "test_timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    
    # Log the test event
    await service.log_security_event(
        threat=test_threat,
        user=user,
        organization_id=user.organization_id,
    )


@router.get("/status")
async def get_monitoring_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get security monitoring system status."""
    # Basic status check available to authenticated users
    service = SecurityMonitoringService(db)
    
    return {
        "monitoring_active": True,
        "service_status": "operational",
        "features": {
            "failed_login_monitoring": True,
            "bulk_access_monitoring": True,
            "privilege_escalation_monitoring": service.PRIVILEGE_ESCALATION_MONITORING,
            "unusual_pattern_monitoring": True,
        },
        "thresholds": {
            "failed_login_threshold": service.FAILED_LOGIN_THRESHOLD,
            "failed_login_time_window": str(service.FAILED_LOGIN_TIME_WINDOW),
            "bulk_access_threshold": service.BULK_ACCESS_THRESHOLD,
            "bulk_access_time_window": str(service.BULK_ACCESS_TIME_WINDOW),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }