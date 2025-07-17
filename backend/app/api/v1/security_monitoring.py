"""
Security Monitoring API endpoints for Issue #46.
セキュリティ監視APIエンドポイント（Issue #46）
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.security_monitoring_service import SecurityMonitoringService

router = APIRouter()


@router.get("/threat-detection")
async def detect_threats(
    time_window_hours: int = Query(24, ge=1, le=168, description="Time window in hours (1-168)"),
    max_failed_logins: int = Query(5, ge=1, le=50, description="Max failed login threshold"),
    max_privilege_escalations: int = Query(3, ge=1, le=20, description="Max privilege escalation threshold"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Detect suspicious activities and security threats.
    不審なアクティビティとセキュリティ脅威の検知
    """
    # Only allow admins and security officers to access this endpoint
    if not (current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Security officer privileges required."
        )

    service = SecurityMonitoringService(db)

    try:
        threats = await service.detect_suspicious_activity(
            time_window_hours=time_window_hours,
            max_failed_logins=max_failed_logins,
            max_privilege_escalations=max_privilege_escalations
        )
        return threats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect threats: {str(e)}"
        )


@router.post("/alerts/generate")
async def generate_security_alert(
    threat_data: dict,
    alert_type: str = Query("security_incident", description="Type of security alert"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate security alert for identified threats.
    特定された脅威に対するセキュリティアラートの生成
    """
    if not (current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Security officer privileges required."
        )

    service = SecurityMonitoringService(db)

    try:
        alert = await service.generate_security_alert(
            threat_data=threat_data,
            alert_type=alert_type
        )

        # Log the alert generation
        await service.log_security_event(
            event_type="alert_generated",
            details={"alert_id": alert["alert_id"], "severity": alert["severity"]},
            user_id=current_user.id
        )

        return alert

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate alert: {str(e)}"
        )


@router.get("/metrics")
async def get_security_metrics(
    days_back: int = Query(30, ge=1, le=365, description="Days to look back (1-365)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get security metrics and statistics.
    セキュリティメトリクスと統計の取得
    """
    if not (current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Security officer privileges required."
        )

    service = SecurityMonitoringService(db)

    try:
        metrics = await service.get_security_metrics(days_back=days_back)
        return metrics

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security metrics: {str(e)}"
        )


@router.get("/users/{user_id}/risk-assessment")
async def assess_user_risk(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Assess risk level for a specific user.
    特定ユーザーのリスクレベル評価
    """
    # Allow users to check their own risk or require admin privileges
    if user_id != current_user.id and not (
        current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Can only assess own risk or require security officer privileges."
        )

    service = SecurityMonitoringService(db)

    try:
        risk_assessment = await service.check_user_risk_level(user_id=user_id)
        return risk_assessment

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assess user risk: {str(e)}"
        )


@router.post("/events/log")
async def log_security_event(
    event_type: str,
    details: dict,
    target_user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Log a security event manually.
    セキュリティイベントの手動記録
    """
    if not (current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Security officer privileges required."
        )

    service = SecurityMonitoringService(db)

    try:
        await service.log_security_event(
            event_type=event_type,
            details=details,
            user_id=target_user_id or current_user.id
        )

        return {
            "status": "success",
            "message": "Security event logged successfully",
            "event_type": event_type,
            "logged_by": current_user.id,
            "target_user": target_user_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log security event: {str(e)}"
        )


@router.get("/dashboard")
async def get_security_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive security monitoring dashboard data.
    包括的なセキュリティ監視ダッシュボードデータの取得
    """
    if not (current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Security officer privileges required."
        )

    service = SecurityMonitoringService(db)

    try:
        # Get recent threats (last 24 hours)
        recent_threats = await service.detect_suspicious_activity(
            time_window_hours=24,
            max_failed_logins=5,
            max_privilege_escalations=3
        )

        # Get security metrics (last 7 days)
        metrics = await service.get_security_metrics(days_back=7)

        # Combine into dashboard
        dashboard = {
            "dashboard_type": "security_monitoring",
            "generated_at": recent_threats["detection_time"],
            "threat_summary": recent_threats["summary"],
            "recent_threats": {
                "failed_logins": len(recent_threats["failed_logins"]),
                "privilege_escalations": len(recent_threats["privilege_escalations"]),
                "bulk_data_access": len(recent_threats["bulk_data_access"]),
                "after_hours_access": len(recent_threats["after_hours_access"]),
                "suspicious_ip_patterns": len(recent_threats["suspicious_ip_patterns"])
            },
            "security_metrics": metrics["metrics"],
            "security_health": metrics["security_health"],
            "high_risk_users": recent_threats["summary"]["high_risk_users"],
            "recommendations": [
                "Review high-risk users immediately",
                "Monitor failed login patterns",
                "Verify after-hours access legitimacy",
                "Check privilege escalation patterns"
            ]
        }

        return dashboard

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate security dashboard: {str(e)}"
        )