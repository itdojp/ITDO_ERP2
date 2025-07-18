"""
Enhanced Security Monitoring API endpoints for Issue #46.
拡張セキュリティ監視APIエンドポイント（Issue #46）
"""

import asyncio
from datetime import datetime, timedelta

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.advanced_threat_detector import AdvancedThreatDetector
from app.services.realtime_security_monitor import RealTimeSecurityMonitor

router = APIRouter()

# Global monitoring instances
monitoring_instances = {}
websocket_connections = {}


@router.get("/realtime/status")
async def get_realtime_monitoring_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get real-time monitoring system status.
    リアルタイム監視システムのステータス取得
    """
    # Check permissions
    has_security_role = "security_officer" in [role.name for role in current_user.roles]
    if not (current_user.is_superuser or has_security_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Security officer privileges required.",
        )

    # Get or create monitoring instance
    monitor_key = f"monitor_{current_user.organization_id or 'global'}"

    if monitor_key not in monitoring_instances:
        monitoring_instances[monitor_key] = RealTimeSecurityMonitor(db)

    monitor = monitoring_instances[monitor_key]

    try:
        stats = await monitor.get_threat_statistics()
        return {
            "status": "active" if monitor.is_monitoring else "inactive",
            "statistics": stats,
            "monitor_id": monitor_key,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitoring status: {str(e)}",
        )


@router.post("/realtime/start")
async def start_realtime_monitoring(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start real-time security monitoring.
    リアルタイムセキュリティ監視の開始
    """
    # Check permissions
    has_security_role = "security_officer" in [role.name for role in current_user.roles]
    if not (current_user.is_superuser or has_security_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Security officer privileges required.",
        )

    monitor_key = f"monitor_{current_user.organization_id or 'global'}"

    try:
        if monitor_key not in monitoring_instances:
            monitoring_instances[monitor_key] = RealTimeSecurityMonitor(db)

        monitor = monitoring_instances[monitor_key]

        if not monitor.is_monitoring:
            await monitor.start_monitoring()

        return {
            "status": "started",
            "monitor_id": monitor_key,
            "message": "Real-time monitoring started successfully",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start monitoring: {str(e)}",
        )


@router.post("/realtime/stop")
async def stop_realtime_monitoring(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Stop real-time security monitoring.
    リアルタイムセキュリティ監視の停止
    """
    # Check permissions
    has_security_role = "security_officer" in [role.name for role in current_user.roles]
    if not (current_user.is_superuser or has_security_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Security officer privileges required.",
        )

    monitor_key = f"monitor_{current_user.organization_id or 'global'}"

    try:
        if monitor_key in monitoring_instances:
            monitor = monitoring_instances[monitor_key]
            await monitor.stop_monitoring()

        return {
            "status": "stopped",
            "monitor_id": monitor_key,
            "message": "Real-time monitoring stopped successfully",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop monitoring: {str(e)}",
        )


@router.get("/threat-intelligence/baselines/build")
async def build_behavioral_baselines(
    learning_days: int = Query(
        30, ge=7, le=90, description="Days of historical data to analyze"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Build behavioral baselines for anomaly detection.
    異常検知のための行動ベースライン構築
    """
    # Check permissions
    has_security_role = "security_officer" in [role.name for role in current_user.roles]
    if not (current_user.is_superuser or has_security_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Security officer privileges required.",
        )

    try:
        detector = AdvancedThreatDetector(db)
        detector.learning_period_days = learning_days

        result = await detector.build_user_baselines()

        return {
            "status": "completed",
            "baselines_built": result,
            "message": (
                f"Behavioral baselines built for {result['total_profiles']} users"
            ),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build baselines: {str(e)}",
        )


@router.get("/threat-intelligence/anomalies/{user_id}")
async def detect_user_anomalies(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Detect behavioral anomalies for a specific user.
    特定ユーザーの行動異常検知
    """
    # Check permissions
    has_security_role = "security_officer" in [role.name for role in current_user.roles]
    if user_id != current_user.id and not (
        current_user.is_superuser or has_security_role
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Access denied. Can only check own anomalies or require "
                "security officer privileges."
            ),
        )

    try:
        detector = AdvancedThreatDetector(db)
        anomalies = await detector.detect_behavioral_anomalies(user_id)

        return {
            "user_id": user_id,
            "anomalies_detected": len(anomalies),
            "anomalies": [
                {
                    "anomaly_id": anomaly.anomaly_id,
                    "type": anomaly.anomaly_type.value,
                    "severity": anomaly.severity,
                    "confidence": anomaly.confidence,
                    "description": anomaly.description,
                    "detected_at": anomaly.detected_at.isoformat(),
                    "recommended_actions": anomaly.recommended_actions,
                    "evidence": anomaly.evidence,
                }
                for anomaly in anomalies
            ],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect anomalies: {str(e)}",
        )


@router.get("/threat-intelligence/risk-score/{user_id}")
async def get_user_risk_score(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive risk score for a user.
    ユーザーの包括的リスクスコア取得
    """
    # Check permissions
    has_security_role = "security_officer" in [role.name for role in current_user.roles]
    if user_id != current_user.id and not (
        current_user.is_superuser or has_security_role
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Access denied. Can only check own risk score or require "
                "security officer privileges."
            ),
        )

    try:
        detector = AdvancedThreatDetector(db)
        risk_data = await detector.calculate_user_risk_score(user_id)

        return risk_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate risk score: {str(e)}",
        )


@router.get("/threat-intelligence/summary")
async def get_threat_intelligence_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive threat intelligence summary.
    包括的脅威インテリジェンスサマリー取得
    """
    # Check permissions
    has_security_role = "security_officer" in [role.name for role in current_user.roles]
    if not (current_user.is_superuser or has_security_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Security officer privileges required.",
        )

    try:
        detector = AdvancedThreatDetector(db)
        summary = await detector.get_threat_intelligence_summary()

        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get threat intelligence: {str(e)}",
        )


@router.get("/realtime/user-profile/{user_id}")
async def get_user_behavior_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user behavior profile for monitoring.
    監視用ユーザー行動プロファイル取得
    """
    # Check permissions
    has_security_role = "security_officer" in [role.name for role in current_user.roles]
    if user_id != current_user.id and not (
        current_user.is_superuser or has_security_role
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Access denied. Can only view own profile or require "
                "security officer privileges."
            ),
        )

    monitor_key = f"monitor_{current_user.organization_id or 'global'}"

    try:
        if monitor_key in monitoring_instances:
            monitor = monitoring_instances[monitor_key]
            profile = await monitor.get_user_risk_profile(user_id)
            return profile
        else:
            return {
                "user_id": user_id,
                "error": "Real-time monitoring not active",
                "message": "Start real-time monitoring to get user profiles",
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user profile: {str(e)}",
        )


@router.websocket("/realtime/events")
async def websocket_security_events(
    websocket: WebSocket, db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time security event streaming.
    リアルタイムセキュリティイベントストリーミング用WebSocket
    """
    await websocket.accept()

    # TODO: Add authentication for WebSocket connections
    # For now, we'll use a simple connection tracking

    connection_id = f"ws_{datetime.utcnow().timestamp()}"
    websocket_connections[connection_id] = websocket

    try:
        # Subscribe to security events
        monitor_key = "monitor_global"  # For now, use global monitoring

        if monitor_key not in monitoring_instances:
            monitoring_instances[monitor_key] = RealTimeSecurityMonitor(db)

        monitor = monitoring_instances[monitor_key]

        # Event handler for WebSocket
        async def event_handler(event):
            try:
                event_data = {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "user_id": event.user_id,
                    "threat_level": event.threat_level.value,
                    "timestamp": event.timestamp.isoformat(),
                    "description": event.details,
                    "source_ip": event.source_ip,
                }
                await websocket.send_json(event_data)
            except Exception as e:
                print(f"WebSocket send error: {e}")

        # Subscribe to events
        monitor.subscribe(event_handler)

        # Keep connection alive
        while True:
            try:
                # Wait for client messages or ping
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                # Handle ping/pong
                if message == "ping":
                    await websocket.send_text("pong")

            except asyncio.TimeoutError:
                # Send periodic status updates
                stats = await monitor.get_threat_statistics()
                await websocket.send_json({"type": "status", "data": stats})
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Clean up
        if connection_id in websocket_connections:
            del websocket_connections[connection_id]

        # Unsubscribe from events
        if monitor_key in monitoring_instances:
            monitor = monitoring_instances[monitor_key]
            monitor.unsubscribe(event_handler)


@router.get("/logs/storage-status")
async def get_log_storage_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get audit log storage status and capacity.
    監査ログストレージ状況と容量の取得
    """
    # Check permissions
    has_security_role = "security_officer" in [role.name for role in current_user.roles]
    if not (current_user.is_superuser or has_security_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Security officer privileges required.",
        )

    try:
        # Query log counts and sizes
        from sqlalchemy import func, select

        from app.models.audit import AuditLog
        from app.models.user_activity_log import UserActivityLog

        # Get audit log statistics
        audit_count_query = select(func.count(AuditLog.id))
        audit_count_result = await db.execute(audit_count_query)
        audit_count = audit_count_result.scalar()

        # Get activity log statistics
        activity_count_query = select(func.count(UserActivityLog.id))
        activity_count_result = await db.execute(activity_count_query)
        activity_count = activity_count_result.scalar()

        # Calculate estimated storage usage (rough estimate)
        estimated_audit_size = audit_count * 1024  # Rough estimate: 1KB per audit log
        # Rough estimate: 0.5KB per activity log
        estimated_activity_size = activity_count * 512
        total_estimated_size = estimated_audit_size + estimated_activity_size

        # Get oldest logs
        oldest_audit_query = select(func.min(AuditLog.created_at))
        oldest_audit_result = await db.execute(oldest_audit_query)
        oldest_audit = oldest_audit_result.scalar()

        oldest_activity_query = select(func.min(UserActivityLog.created_at))
        oldest_activity_result = await db.execute(oldest_activity_query)
        oldest_activity = oldest_activity_result.scalar()

        return {
            "storage_status": {
                "audit_logs_count": audit_count,
                "activity_logs_count": activity_count,
                "total_logs": audit_count + activity_count,
                "estimated_size_bytes": total_estimated_size,
                "estimated_size_mb": round(total_estimated_size / (1024 * 1024), 2),
            },
            "retention": {
                "oldest_audit_log": oldest_audit.isoformat() if oldest_audit else None,
                "oldest_activity_log": (
                    oldest_activity.isoformat() if oldest_activity else None
                ),
            },
            "recommendations": [
                "Consider implementing log archiving for logs older than 1 year",
                "Set up automated log rotation policies",
                "Monitor storage growth trends",
                "Implement log compression for archived data",
            ],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get storage status: {str(e)}",
        )


@router.post("/logs/cleanup")
async def cleanup_old_logs(
    days_to_keep: int = Query(
        365, ge=30, le=2555, description="Days of logs to keep (30-2555)"
    ),
    dry_run: bool = Query(True, description="Perform dry run without actual deletion"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Clean up old audit and activity logs.
    古い監査ログとアクティビティログのクリーンアップ
    """
    # Check permissions
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Superuser privileges required for log cleanup.",
        )

    try:
        from sqlalchemy import delete, func, select

        from app.models.audit import AuditLog
        from app.models.user_activity_log import UserActivityLog

        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        # Count logs to be deleted
        audit_delete_query = select(func.count(AuditLog.id)).where(
            AuditLog.created_at < cutoff_date
        )
        audit_delete_result = await db.execute(audit_delete_query)
        audit_delete_count = audit_delete_result.scalar()

        activity_delete_query = select(func.count(UserActivityLog.id)).where(
            UserActivityLog.created_at < cutoff_date
        )
        activity_delete_result = await db.execute(activity_delete_query)
        activity_delete_count = activity_delete_result.scalar()

        if not dry_run:
            # Actually delete old logs
            await db.execute(delete(AuditLog).where(AuditLog.created_at < cutoff_date))
            await db.execute(
                delete(UserActivityLog).where(UserActivityLog.created_at < cutoff_date)
            )
            await db.commit()

        return {
            "cleanup_status": "completed" if not dry_run else "dry_run",
            "cutoff_date": cutoff_date.isoformat(),
            "deleted_counts": {
                "audit_logs": audit_delete_count,
                "activity_logs": activity_delete_count,
                "total": audit_delete_count + activity_delete_count,
            },
            "message": (
                f"{'Would delete' if dry_run else 'Deleted'} "
                f"{audit_delete_count + activity_delete_count} logs older than "
                f"{days_to_keep} days"
            ),
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup logs: {str(e)}",
        )
