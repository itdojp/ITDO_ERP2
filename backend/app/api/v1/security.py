"""Security and advanced session API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_session, get_current_user, get_db
from app.models.session import UserSession
from app.models.user import User
from app.schemas.security import (
    DeviceTrustRequest,
    RiskAssessmentResponse,
    SecurityEventResponse,
    SessionAnalyticsResponse,
)
from app.services.security_service import SecurityService
from app.services.session_service import SessionService

router = APIRouter(prefix="/security", tags=["security"])


@router.get("/risk-assessment", response_model=RiskAssessmentResponse)
async def assess_risk(
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RiskAssessmentResponse:
    """
    Assess current session risk level.
    """
    security_service = SecurityService(db)

    # Get client info
    client_ip = http_request.client.host if http_request.client else "unknown"
    user_agent = http_request.headers.get("user-agent", "unknown")

    # Calculate risk score
    risk_score = security_service.calculate_risk_score(
        user=current_user,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    # Check if MFA should be required
    require_mfa = security_service.should_require_mfa(
        user=current_user,
        risk_score=risk_score,
        ip_address=client_ip,
    )

    # Get risk factors
    risk_factors = []
    if security_service.is_ip_suspicious(client_ip, current_user):
        risk_factors.append("suspicious_ip")

    if security_service.check_concurrent_sessions(current_user, client_ip):
        risk_factors.append("concurrent_sessions")

    device_info = security_service.analyze_user_agent(user_agent)
    if device_info["is_bot"]:
        risk_factors.append("bot_detected")

    return RiskAssessmentResponse(
        risk_score=risk_score,
        risk_level="high"
        if risk_score >= 70
        else "medium"
        if risk_score >= 40
        else "low",
        require_mfa=require_mfa,
        risk_factors=risk_factors,
        recommendations=[
            "MFAを有効にすることを推奨します"
            if not current_user.mfa_required
            else None,
            "不審なセッションを確認してください"
            if "concurrent_sessions" in risk_factors
            else None,
        ],
    )


@router.get("/session-analytics", response_model=SessionAnalyticsResponse)
async def get_session_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SessionAnalyticsResponse:
    """
    Get session analytics for current user.
    """
    security_service = SecurityService(db)
    analytics = security_service.get_session_analytics(current_user)

    # Get device breakdown
    from app.models.session import UserSession

    sessions = (
        db.query(UserSession).filter(UserSession.user_id == current_user.id).all()
    )

    device_breakdown = {}
    ip_breakdown = {}

    for session in sessions:
        if session.user_agent:
            device_info = security_service.analyze_user_agent(session.user_agent)
            device_key = f"{device_info['os']} - {device_info['browser']}"
            device_breakdown[device_key] = device_breakdown.get(device_key, 0) + 1

        if session.ip_address:
            # Group by /24 subnet for privacy
            ip_parts = session.ip_address.split(".")
            if len(ip_parts) == 4:
                subnet = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
                ip_breakdown[subnet] = ip_breakdown.get(subnet, 0) + 1

    return SessionAnalyticsResponse(
        total_sessions=analytics["total_sessions"],
        active_sessions=analytics["active_sessions"],
        unique_devices=analytics["unique_devices"],
        unique_locations=analytics["unique_ips"],
        device_breakdown=device_breakdown,
        location_breakdown=ip_breakdown,
        recent_activities=analytics["recent_activities"],
    )


@router.get("/recent-events", response_model=list[SecurityEventResponse])
async def get_recent_security_events(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SecurityEventResponse]:
    """
    Get recent security events for current user.
    """
    from app.models.session import SessionActivity

    activities = (
        db.query(SessionActivity)
        .filter(SessionActivity.user_id == current_user.id)
        .order_by(SessionActivity.created_at.desc())
        .limit(limit)
        .all()
    )

    security_service = SecurityService(db)

    events = []
    for activity in activities:
        # Analyze device
        device_info = {}
        if activity.user_agent:
            device_info = security_service.analyze_user_agent(activity.user_agent)

        events.append(
            SecurityEventResponse(
                id=activity.id,
                event_type=activity.activity_type,
                timestamp=activity.created_at,
                ip_address=activity.ip_address,
                device_info=device_info,
                details=activity.details,
                severity="high" if "failed" in activity.activity_type else "low",
            )
        )

    return events


@router.post("/trust-device", status_code=status.HTTP_204_NO_CONTENT)
async def trust_current_device(
    request: DeviceTrustRequest,
    current_user: User = Depends(get_current_user),
    current_session: UserSession = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> None:
    """
    Trust the current device.
    """
    session_service = SessionService(db)

    # Add device to trusted devices
    if request.device_fingerprint:
        session_service.add_trusted_device(current_user, request.device_fingerprint)

        # Update session with device fingerprint
        if not current_session.device_id:
            current_session.device_id = request.device_fingerprint
            current_session.device_name = request.device_name or "Trusted Device"
            db.commit()


@router.get("/check-device-trust/{device_id}")
async def check_device_trust(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Check if a device is trusted.
    """
    session_service = SessionService(db)
    is_trusted = session_service.is_trusted_device(current_user, device_id)

    security_service = SecurityService(db)
    is_known = security_service.verify_device_fingerprint(current_user, device_id)

    return {
        "device_id": device_id,
        "is_trusted": is_trusted,
        "is_known": is_known,
    }


@router.post("/report-suspicious-activity", status_code=status.HTTP_204_NO_CONTENT)
async def report_suspicious_activity(
    session_id: int,
    reason: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Report suspicious activity on a session.
    """
    # Verify session belongs to user
    session = (
        db.query(UserSession)
        .filter(
            UserSession.id == session_id,
            UserSession.user_id == current_user.id,
        )
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="セッションが見つかりません",
        )

    # Log security event
    security_service = SecurityService(db)
    security_service.log_security_event(
        user_id=current_user.id,
        event_type="suspicious_activity_reported",
        ip_address=session.ip_address,
        user_agent=session.user_agent,
        details={
            "session_id": session_id,
            "reason": reason,
        },
    )

    # Optionally revoke the session
    if reason in ["unauthorized_access", "account_compromise"]:
        session_service = SessionService(db)
        session_service.revoke_session(
            session,
            revoked_by=current_user.id,
            reason=f"Suspicious activity: {reason}",
        )


@router.get("/security-recommendations")
async def get_security_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get personalized security recommendations.
    """
    recommendations = []

    # Check MFA status
    if not current_user.mfa_required:
        recommendations.append(
            {
                "priority": "high",
                "title": "多要素認証を有効にする",
                "description": "アカウントのセキュリティを強化するため、MFAを有効にすることを強く推奨します",
                "action": "/settings/security/mfa",
            }
        )

    # Check password age
    from datetime import datetime, timedelta

    password_age = datetime.now() - current_user.password_changed_at
    if password_age > timedelta(days=90):
        recommendations.append(
            {
                "priority": "medium",
                "title": "パスワードを更新する",
                "description": "パスワードが90日以上変更されていません",
                "action": "/settings/security/password",
            }
        )

    # Check active sessions
    session_service = SessionService(db)
    active_sessions = session_service.get_active_sessions(current_user)

    if len(active_sessions) > 5:
        recommendations.append(
            {
                "priority": "medium",
                "title": "アクティブセッションを確認する",
                "description": f"{len(active_sessions)}個のアクティブセッションがあります",
                "action": "/settings/sessions",
            }
        )

    # Check for suspicious activities
    security_service = SecurityService(db)
    analytics = security_service.get_session_analytics(current_user)

    if analytics["recent_activities"].get("failed_login", 0) > 5:
        recommendations.append(
            {
                "priority": "high",
                "title": "不正なログイン試行を確認",
                "description": "最近、複数の失敗したログイン試行が検出されました",
                "action": "/settings/security/activity",
            }
        )

    return {
        "recommendations": recommendations,
        "security_score": calculate_security_score(current_user, analytics),
    }


def calculate_security_score(user: User, analytics: dict) -> int:
    """Calculate user's security score."""
    score = 100

    # Deduct for no MFA
    if not user.mfa_required:
        score -= 30

    # Deduct for old password
    from datetime import datetime, timedelta

    password_age = datetime.now() - user.password_changed_at
    if password_age > timedelta(days=180):
        score -= 20
    elif password_age > timedelta(days=90):
        score -= 10

    # Deduct for too many active sessions
    if analytics["active_sessions"] > 5:
        score -= 10

    # Deduct for failed login attempts
    failed_logins = analytics["recent_activities"].get("failed_login", 0)
    if failed_logins > 10:
        score -= 20
    elif failed_logins > 5:
        score -= 10

    return max(score, 0)
