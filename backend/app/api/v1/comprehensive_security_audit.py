"""
Comprehensive Security Audit API endpoints for Issue #46.
包括的セキュリティ監査APIエンドポイント（Issue #46）
"""

import asyncio
import io
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.security_event import (
    SecurityEventType,
    SecurityIncidentStatus,
    ThreatLevel,
)
from app.models.user import User
from app.services.enhanced_security_service import EnhancedSecurityService
from app.services.realtime_alert_service import realtime_alert_service

router = APIRouter(prefix="/security-audit", tags=["Security Audit"])

# Global service instances
active_monitoring_sessions = {}


@router.post("/start-session")
async def start_monitoring_session(
    organization_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start a comprehensive security monitoring session.
    包括的セキュリティ監視セッションの開始
    """
    # Check permissions
    if not (current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Security officer privileges required."
        )

    session_id = f"session_{current_user.id}_{datetime.utcnow().timestamp()}"
    
    # Initialize enhanced security service for this session
    security_service = EnhancedSecurityService(db)
    active_monitoring_sessions[session_id] = {
        "service": security_service,
        "user_id": current_user.id,
        "organization_id": organization_id,
        "started_at": datetime.utcnow(),
        "is_active": True,
    }
    
    # Start real-time alert service if not already running
    if not realtime_alert_service.is_running:
        await realtime_alert_service.start_service()
    
    # Add user as alert subscriber
    realtime_alert_service.add_subscriber(
        user_id=current_user.id,
        severity_threshold=ThreatLevel.MEDIUM,
        alert_types=["security_incident", "threat_detection", "data_breach"],
    )
    
    return {
        "session_id": session_id,
        "status": "active",
        "started_at": active_monitoring_sessions[session_id]["started_at"].isoformat(),
        "message": "Security monitoring session started successfully",
    }


@router.post("/log-event")
async def log_security_event(
    event_type: SecurityEventType,
    title: str,
    description: str,
    threat_level: ThreatLevel = ThreatLevel.LOW,
    details: Optional[Dict[str, Any]] = None,
    source_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    session_id: Optional[str] = None,
    api_endpoint: Optional[str] = None,
    http_method: Optional[str] = None,
    evidence: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Log a comprehensive security event.
    包括的セキュリティイベントの記録
    """
    if not (current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Security officer privileges required."
        )

    security_service = EnhancedSecurityService(db)
    
    try:
        event = await security_service.log_security_event(
            event_type=event_type,
            title=title,
            description=description,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            threat_level=threat_level,
            details=details or {},
            source_ip=source_ip,
            user_agent=user_agent,
            session_id=session_id,
            api_endpoint=api_endpoint,
            http_method=http_method,
            evidence=evidence or {},
        )
        
        return {
            "event_id": event.event_id,
            "id": event.id,
            "status": "logged",
            "threat_level": event.threat_level.value,
            "risk_score": event.risk_score,
            "recommended_actions": event.recommended_actions,
            "created_at": event.created_at.isoformat(),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log security event: {str(e)}"
        )


@router.get("/detect-threats")
async def detect_comprehensive_threats(
    time_window_hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
    organization_id: Optional[int] = Query(None, description="Organization ID filter"),
    include_resolved: bool = Query(False, description="Include resolved incidents"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Detect comprehensive security threats and suspicious activities.
    包括的なセキュリティ脅威と不審なアクティビティの検知
    """
    if not (current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Security officer privileges required."
        )

    security_service = EnhancedSecurityService(db)
    
    try:
        # Detect suspicious activities
        threats = await security_service.detect_suspicious_activities(
            time_window_hours=time_window_hours,
            organization_id=organization_id or current_user.organization_id,
        )
        
        return {
            "detection_summary": threats,
            "generated_at": datetime.utcnow().isoformat(),
            "detection_scope": {
                "time_window_hours": time_window_hours,
                "organization_id": organization_id or current_user.organization_id,
                "include_resolved": include_resolved,
            },
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect threats: {str(e)}"
        )


@router.get("/user-risk-profile/{user_id}")
async def get_comprehensive_user_risk_profile(
    user_id: int,
    days_back: int = Query(30, ge=1, le=365, description="Days to analyze"),
    include_recommendations: bool = Query(True, description="Include security recommendations"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive risk profile for a user.
    ユーザーの包括的リスクプロファイル取得
    """
    # Allow users to check their own profile or require admin privileges
    if user_id != current_user.id and not (
        current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Can only view own profile or require security officer privileges."
        )

    security_service = EnhancedSecurityService(db)
    
    try:
        risk_profile = await security_service.analyze_user_risk_profile(
            user_id=user_id,
            days_back=days_back,
        )
        
        return {
            "risk_profile": risk_profile,
            "analysis_metadata": {
                "analyzed_by": current_user.id,
                "analysis_date": datetime.utcnow().isoformat(),
                "include_recommendations": include_recommendations,
            },
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze user risk profile: {str(e)}"
        )


@router.post("/create-incident")
async def create_security_incident(
    title: str,
    description: str,
    severity: ThreatLevel,
    category: str,
    assigned_to: Optional[int] = None,
    related_events: Optional[List[int]] = None,
    affected_users: Optional[List[int]] = None,
    affected_resources: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new security incident for tracking and investigation.
    追跡と調査のための新しいセキュリティインシデントの作成
    """
    if not (current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Security officer privileges required."
        )

    security_service = EnhancedSecurityService(db)
    
    try:
        incident = await security_service.create_security_incident(
            title=title,
            description=description,
            severity=severity,
            category=category,
            organization_id=current_user.organization_id,
            assigned_to=assigned_to,
            related_events=related_events or [],
            affected_users=affected_users or [],
            affected_resources=affected_resources or [],
        )
        
        return {
            "incident_id": incident.incident_id,
            "id": incident.id,
            "status": incident.status.value,
            "severity": incident.severity.value,
            "created_at": incident.created_at.isoformat(),
            "message": "Security incident created successfully",
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create security incident: {str(e)}"
        )


@router.put("/incident/{incident_id}/status")
async def update_incident_status(
    incident_id: int,
    status: SecurityIncidentStatus,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update security incident status and add investigation notes.
    セキュリティインシデントのステータス更新と調査ノートの追加
    """
    if not (current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Security officer privileges required."
        )

    security_service = EnhancedSecurityService(db)
    
    try:
        incident = await security_service.update_incident_status(
            incident_id=incident_id,
            status=status,
            notes=notes,
            updated_by=current_user.id,
        )
        
        return {
            "incident_id": incident.incident_id,
            "id": incident.id,
            "status": incident.status.value,
            "updated_at": incident.updated_at.isoformat(),
            "message": f"Incident status updated to {status.value}",
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update incident status: {str(e)}"
        )


@router.get("/dashboard")
async def get_comprehensive_security_dashboard(
    time_range_hours: int = Query(24, ge=1, le=168, description="Time range in hours"),
    organization_id: Optional[int] = Query(None, description="Organization ID filter"),
    include_recommendations: bool = Query(True, description="Include security recommendations"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive security monitoring dashboard.
    包括的セキュリティ監視ダッシュボードの取得
    """
    if not (current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Security officer privileges required."
        )

    security_service = EnhancedSecurityService(db)
    
    try:
        dashboard_data = await security_service.get_security_dashboard_data(
            organization_id=organization_id or current_user.organization_id,
            time_range_hours=time_range_hours,
        )
        
        # Add real-time service statistics
        realtime_stats = realtime_alert_service.get_service_statistics()
        recent_alerts = realtime_alert_service.get_recent_alerts(limit=20)
        
        dashboard_data["realtime_monitoring"] = {
            "service_status": realtime_stats,
            "recent_alerts": recent_alerts,
        }
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security dashboard: {str(e)}"
        )


@router.get("/export-logs")
async def export_comprehensive_security_logs(
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    event_types: Optional[List[SecurityEventType]] = Query(None, description="Event type filters"),
    threat_levels: Optional[List[ThreatLevel]] = Query(None, description="Threat level filters"),
    organization_id: Optional[int] = Query(None, description="Organization ID filter"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export comprehensive security logs in specified format.
    指定フォーマットでの包括的セキュリティログのエクスポート
    """
    if not (current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Security officer privileges required."
        )

    security_service = EnhancedSecurityService(db)
    
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        export_data = await security_service.export_security_logs(
            format=format,
            start_date=start_date,
            end_date=end_date,
            event_types=event_types,
            threat_levels=threat_levels,
            organization_id=organization_id or current_user.organization_id,
        )
        
        # Prepare response
        media_type = "application/json" if format == "json" else "text/csv"
        filename = f"security_logs_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.{format}"
        
        return StreamingResponse(
            io.StringIO(export_data),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export security logs: {str(e)}"
        )


@router.post("/alerts/create")
async def create_security_alert(
    alert_type: str,
    severity: ThreatLevel,
    title: str,
    message: str,
    related_event_id: Optional[int] = None,
    related_incident_id: Optional[int] = None,
    recipients: Optional[List[int]] = None,
    delivery_methods: Optional[List[str]] = Query(default=["email", "in_app"], description="Delivery methods"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a security alert for immediate notification.
    即座の通知のためのセキュリティアラート作成
    """
    if not (current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Security officer privileges required."
        )

    security_service = EnhancedSecurityService(db)
    
    try:
        alert = await security_service.create_security_alert(
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            related_event_id=related_event_id,
            related_incident_id=related_incident_id,
            recipients=recipients,
            delivery_methods=delivery_methods,
        )
        
        # Queue alert for real-time delivery
        await realtime_alert_service.queue_alert(alert)
        
        return {
            "alert_id": alert.alert_id,
            "id": alert.id,
            "status": "created",
            "severity": alert.severity.value,
            "delivery_methods": alert.delivery_methods,
            "created_at": alert.created_at.isoformat(),
            "message": "Security alert created and queued for delivery",
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create security alert: {str(e)}"
        )


@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_security_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Acknowledge a security alert.
    セキュリティアラートの確認
    """
    security_service = EnhancedSecurityService(db)
    
    try:
        alert = await security_service.acknowledge_alert(
            alert_id=alert_id,
            acknowledged_by=current_user.id,
        )
        
        return {
            "alert_id": alert.alert_id,
            "id": alert.id,
            "acknowledged": alert.acknowledged,
            "acknowledged_by": alert.acknowledged_by,
            "acknowledged_at": alert.acknowledged_at.isoformat(),
            "message": "Security alert acknowledged successfully",
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to acknowledge alert: {str(e)}"
        )


@router.get("/alerts/subscription-preferences")
async def get_alert_subscription_preferences(
    current_user: User = Depends(get_current_user),
):
    """
    Get user's alert subscription preferences.
    ユーザーのアラート購読設定の取得
    """
    preferences = realtime_alert_service.get_subscriber_preferences(current_user.id)
    
    if not preferences:
        return {
            "user_id": current_user.id,
            "subscribed": False,
            "message": "No alert subscription found",
        }
    
    return {
        "user_id": current_user.id,
        "subscribed": True,
        "preferences": preferences,
    }


@router.put("/alerts/subscription-preferences")
async def update_alert_subscription_preferences(
    severity_threshold: Optional[ThreatLevel] = None,
    alert_types: Optional[List[str]] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    webhook_url: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """
    Update user's alert subscription preferences.
    ユーザーのアラート購読設定の更新
    """
    result = realtime_alert_service.update_subscriber_preferences(
        user_id=current_user.id,
        severity_threshold=severity_threshold,
        alert_types=alert_types,
        email=email,
        phone=phone,
        webhook_url=webhook_url,
    )
    
    return {
        "user_id": current_user.id,
        "status": "updated",
        "message": result,
    }


@router.post("/alerts/test")
async def send_test_alert(
    severity: ThreatLevel = ThreatLevel.LOW,
    current_user: User = Depends(get_current_user),
):
    """
    Send a test alert to verify notification systems.
    通知システムを検証するためのテストアラート送信
    """
    result = await realtime_alert_service.send_test_alert(
        user_id=current_user.id,
        severity=severity,
    )
    
    return {
        "user_id": current_user.id,
        "test_alert_sent": True,
        "severity": severity.value,
        "message": result,
    }


@router.websocket("/realtime-alerts")
async def websocket_realtime_alerts(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user),
):
    """
    WebSocket endpoint for real-time security alerts.
    リアルタイムセキュリティアラート用WebSocketエンドポイント
    """
    await websocket.accept()
    
    connection_id = await realtime_alert_service.add_websocket_connection(
        websocket, current_user.id
    )
    
    try:
        while True:
            # Keep connection alive with ping/pong
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                if message == "ping":
                    await websocket.send_text("pong")
                elif message == "subscribe":
                    # Subscribe user to alerts if not already subscribed
                    if current_user.id not in realtime_alert_service.subscribers:
                        realtime_alert_service.add_subscriber(
                            user_id=current_user.id,
                            severity_threshold=ThreatLevel.MEDIUM,
                        )
                    await websocket.send_text("subscribed")
                
            except asyncio.TimeoutError:
                # Send periodic heartbeat
                await websocket.send_text('{"type": "heartbeat", "timestamp": "' + 
                                        datetime.utcnow().isoformat() + '"}')
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await realtime_alert_service.remove_websocket_connection(connection_id)


@router.get("/statistics")
async def get_comprehensive_security_statistics(
    days_back: int = Query(30, ge=1, le=365, description="Days to analyze"),
    organization_id: Optional[int] = Query(None, description="Organization ID filter"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive security statistics and metrics.
    包括的セキュリティ統計とメトリクスの取得
    """
    if not (current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Security officer privileges required."
        )

    try:
        # Get dashboard data
        security_service = EnhancedSecurityService(db)
        dashboard_data = await security_service.get_security_dashboard_data(
            organization_id=organization_id or current_user.organization_id,
            time_range_hours=days_back * 24,
        )
        
        # Get real-time service statistics
        realtime_stats = realtime_alert_service.get_service_statistics()
        
        # Get active monitoring sessions
        active_sessions = len([
            session for session in active_monitoring_sessions.values() 
            if session["is_active"]
        ])
        
        return {
            "analysis_period": {
                "days_back": days_back,
                "organization_id": organization_id or current_user.organization_id,
                "generated_at": datetime.utcnow().isoformat(),
            },
            "security_dashboard": dashboard_data,
            "realtime_monitoring": realtime_stats,
            "active_monitoring_sessions": active_sessions,
            "system_health": {
                "alert_service_running": realtime_stats["is_running"],
                "monitoring_sessions": active_sessions,
                "total_subscribers": realtime_stats["total_subscribers"],
            },
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security statistics: {str(e)}"
        )


@router.post("/stop-session/{session_id}")
async def stop_monitoring_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Stop a security monitoring session.
    セキュリティ監視セッションの停止
    """
    if session_id not in active_monitoring_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitoring session not found"
        )
    
    session = active_monitoring_sessions[session_id]
    
    # Check if user owns the session or has admin privileges
    if session["user_id"] != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Can only stop own monitoring sessions."
        )
    
    # Mark session as inactive
    session["is_active"] = False
    session["stopped_at"] = datetime.utcnow()
    
    # Remove from subscribers
    realtime_alert_service.remove_subscriber(current_user.id)
    
    return {
        "session_id": session_id,
        "status": "stopped",
        "duration_minutes": int((session["stopped_at"] - session["started_at"]).total_seconds() / 60),
        "message": "Security monitoring session stopped successfully",
    }