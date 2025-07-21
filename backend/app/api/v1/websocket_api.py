"""Real-time WebSocket API endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.core.websocket_manager import (
    websocket_manager,
    WebSocketMessage,
    MessageType,
    EventType,
    SubscriptionScope,
    check_websocket_health
)
from app.models.user import User

router = APIRouter()


# Pydantic schemas
class BroadcastRequest(BaseModel):
    """Broadcast message request."""
    event_type: EventType
    payload: Dict[str, Any]
    scope: SubscriptionScope = SubscriptionScope.ORGANIZATION
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    exclude_users: Optional[List[str]] = Field(default_factory=list)


class SendMessageRequest(BaseModel):
    """Send message to specific user request."""
    user_id: str = Field(..., max_length=100)
    event_type: EventType
    payload: Dict[str, Any]
    message_type: MessageType = MessageType.DATA


class SubscriptionRequest(BaseModel):
    """WebSocket subscription request."""
    event_type: EventType
    scope: SubscriptionScope = SubscriptionScope.USER
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ConnectionStatsResponse(BaseModel):
    """Connection statistics response."""
    total_connections: int
    active_connections: int
    authenticated_connections: int
    connections_by_organization: Dict[str, int]
    connections_by_user: Dict[str, int]


class MessageStatsResponse(BaseModel):
    """Message statistics response."""
    total_messages_sent: int
    total_messages_received: int
    messages_per_second: float
    failed_messages_count: int
    recent_activity: List[Dict[str, Any]]


class WebSocketHealthResponse(BaseModel):
    """WebSocket health response."""
    status: str
    statistics: Dict[str, Any]
    last_updated: str


# WebSocket endpoint
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = Query(None)):
    """Main WebSocket endpoint for real-time communication."""
    connection_id = None
    
    try:
        # Accept connection
        connection_id = await websocket_manager.connect(websocket)
        
        # Basic authentication if token provided
        if token:
            # In production, this would validate the JWT token
            # For now, simulate token validation
            try:
                # Simulated token validation - would use actual JWT validation
                user_data = {"user_id": "user123", "organization_id": "org456"}  # Simulated
                await websocket_manager.authenticate(
                    connection_id,
                    user_data["user_id"],
                    user_data["organization_id"]
                )
            except Exception as e:
                await websocket_manager.disconnect(connection_id, f"auth_error: {str(e)}")
                return
        
        # Message handling loop
        while True:
            try:
                # Receive message from client
                message_data = await websocket.receive_text()
                await websocket_manager.handle_message(connection_id, message_data)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                # Send error to client
                error_msg = WebSocketMessage(
                    type=MessageType.ERROR,
                    payload={"error": f"Message processing error: {str(e)}"}
                )
                await websocket_manager.send_to_connection(connection_id, error_msg)
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    
    finally:
        if connection_id:
            await websocket_manager.disconnect(connection_id, "client_disconnect")


# REST API endpoints for WebSocket management
@router.post("/broadcast")
async def broadcast_message(
    broadcast_request: BroadcastRequest,
    current_user: User = Depends(get_current_user)
):
    """Broadcast message to all matching subscriptions."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required for broadcasting"
        )
    
    try:
        # Convert exclude_users to connection IDs
        exclude_connections = set()
        if broadcast_request.exclude_users:
            for user_id in broadcast_request.exclude_users:
                user_connections = websocket_manager.user_connections.get(user_id, set())
                exclude_connections.update(user_connections)
        
        # Broadcast event
        sent_count = await websocket_manager.broadcast_event(
            event_type=broadcast_request.event_type,
            payload=broadcast_request.payload,
            scope=broadcast_request.scope,
            filters=broadcast_request.filters,
            exclude_connections=exclude_connections
        )
        
        return {
            "message": "Broadcast completed",
            "event_type": broadcast_request.event_type.value,
            "scope": broadcast_request.scope.value,
            "recipients_count": sent_count,
            "broadcast_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Broadcast failed: {str(e)}"
        )


@router.post("/send-to-user")
async def send_message_to_user(
    message_request: SendMessageRequest,
    current_user: User = Depends(get_current_user)
):
    """Send message to specific user's connections."""
    try:
        message = WebSocketMessage(
            type=message_request.message_type,
            event_type=message_request.event_type,
            payload=message_request.payload
        )
        
        sent_count = await websocket_manager.send_to_user(
            message_request.user_id,
            message
        )
        
        return {
            "message": "Message sent to user",
            "user_id": message_request.user_id,
            "connections_count": sent_count,
            "sent_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )


@router.post("/send-to-organization")
async def send_message_to_organization(
    organization_id: str = Field(..., max_length=100),
    event_type: EventType = EventType.SYSTEM_NOTIFICATION,
    payload: Dict[str, Any] = Field(default_factory=dict),
    current_user: User = Depends(get_current_user)
):
    """Send message to all connections in an organization."""
    if not current_user.is_superuser and str(current_user.organization_id) != organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    try:
        message = WebSocketMessage(
            type=MessageType.DATA,
            event_type=event_type,
            payload=payload
        )
        
        sent_count = await websocket_manager.send_to_organization(
            organization_id,
            message
        )
        
        return {
            "message": "Message sent to organization",
            "organization_id": organization_id,
            "connections_count": sent_count,
            "sent_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )


# Connection management endpoints
@router.get("/connections")
async def get_active_connections(
    organization_filter: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Get list of active WebSocket connections."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    connections = []
    
    for connection_id, connection in websocket_manager.connections.items():
        # Apply organization filter
        if organization_filter and connection.organization_id != organization_filter:
            continue
        
        connection_info = websocket_manager.get_connection_info(connection_id)
        if connection_info:
            connections.append(connection_info)
    
    return {
        "connections": connections,
        "total_count": len(connections),
        "retrieved_at": datetime.utcnow().isoformat()
    }


@router.get("/connections/{connection_id}")
async def get_connection_details(
    connection_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get details of specific WebSocket connection."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    connection_info = websocket_manager.get_connection_info(connection_id)
    
    if not connection_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    # Get subscription details
    if connection_id in websocket_manager.connections:
        connection = websocket_manager.connections[connection_id]
        subscriptions = []
        
        for sub_id in connection.subscriptions:
            if sub_id in websocket_manager.subscriptions:
                subscription = websocket_manager.subscriptions[sub_id]
                subscriptions.append({
                    "id": subscription.id,
                    "event_type": subscription.event_type.value,
                    "scope": subscription.scope.value,
                    "filters": subscription.filters,
                    "created_at": subscription.created_at.isoformat(),
                    "message_count": subscription.message_count
                })
        
        connection_info["subscriptions"] = subscriptions
    
    return connection_info


@router.delete("/connections/{connection_id}")
async def disconnect_connection(
    connection_id: str,
    reason: str = Query("admin_disconnect"),
    current_user: User = Depends(get_current_user)
):
    """Forcefully disconnect a WebSocket connection."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    if connection_id not in websocket_manager.connections:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    await websocket_manager.disconnect(connection_id, reason)
    
    return {
        "message": "Connection disconnected",
        "connection_id": connection_id,
        "reason": reason,
        "disconnected_at": datetime.utcnow().isoformat()
    }


# Statistics and monitoring endpoints
@router.get("/stats/connections", response_model=ConnectionStatsResponse)
async def get_connection_statistics(
    current_user: User = Depends(get_current_user)
):
    """Get WebSocket connection statistics."""
    stats = websocket_manager.get_statistics()
    
    # Count connections by organization
    org_counts = {}
    user_counts = {}
    
    for connection in websocket_manager.connections.values():
        if connection.organization_id:
            org_counts[connection.organization_id] = org_counts.get(connection.organization_id, 0) + 1
        if connection.user_id:
            user_counts[connection.user_id] = user_counts.get(connection.user_id, 0) + 1
    
    return ConnectionStatsResponse(
        total_connections=stats["connections"]["total"],
        active_connections=stats["connections"]["active"],
        authenticated_connections=stats["connections"]["authenticated"],
        connections_by_organization=org_counts,
        connections_by_user=user_counts
    )


@router.get("/stats/messages", response_model=MessageStatsResponse)
async def get_message_statistics(
    current_user: User = Depends(get_current_user)
):
    """Get WebSocket message statistics."""
    stats = websocket_manager.get_statistics()
    
    # Get recent message activity
    recent_activity = []
    for entry in list(websocket_manager.message_history)[-10:]:
        recent_activity.append({
            "type": entry["type"],
            "message_type": entry["message_type"],
            "timestamp": entry["timestamp"].isoformat(),
            "size_bytes": entry.get("size_bytes", 0)
        })
    
    return MessageStatsResponse(
        total_messages_sent=stats["messages"]["total_sent"],
        total_messages_received=stats["messages"]["total_received"],
        messages_per_second=stats["messages"]["per_second"],
        failed_messages_count=stats["messages"]["failed_count"],
        recent_activity=recent_activity
    )


@router.get("/stats/subscriptions")
async def get_subscription_statistics(
    current_user: User = Depends(get_current_user)
):
    """Get WebSocket subscription statistics."""
    stats = websocket_manager.get_statistics()
    
    # Get detailed subscription breakdown
    subscription_details = []
    
    for event_type, subscription_ids in websocket_manager.event_subscriptions.items():
        for sub_id in list(subscription_ids)[:10]:  # Limit to prevent overflow
            if sub_id in websocket_manager.subscriptions:
                subscription = websocket_manager.subscriptions[sub_id]
                subscription_details.append({
                    "id": subscription.id,
                    "event_type": subscription.event_type.value,
                    "scope": subscription.scope.value,
                    "connection_id": subscription.connection_id,
                    "created_at": subscription.created_at.isoformat(),
                    "message_count": subscription.message_count
                })
    
    return {
        "total_subscriptions": stats["subscriptions"]["total"],
        "by_event_type": stats["subscriptions"]["by_event_type"],
        "by_scope": stats["subscriptions"]["by_scope"],
        "recent_subscriptions": subscription_details,
        "retrieved_at": datetime.utcnow().isoformat()
    }


@router.get("/stats/performance")
async def get_performance_statistics(
    current_user: User = Depends(get_current_user)
):
    """Get WebSocket performance statistics."""
    stats = websocket_manager.get_statistics()
    
    # Get recent connection events
    recent_connections = []
    for entry in list(websocket_manager.connection_history)[-20:]:
        recent_connections.append({
            "event": entry["event"],
            "connection_id": entry["connection_id"],
            "timestamp": entry["timestamp"].isoformat(),
            "duration_seconds": entry.get("duration_seconds"),
            "message_count": entry.get("message_count")
        })
    
    # Get recent failures
    recent_failures = []
    for entry in list(websocket_manager.failed_messages)[-10:]:
        recent_failures.append({
            "connection_id": entry["connection_id"],
            "error": entry["error"],
            "timestamp": entry["timestamp"].isoformat()
        })
    
    return {
        "performance": stats["performance"],
        "configuration": stats["configuration"],
        "recent_connections": recent_connections,
        "recent_failures": recent_failures,
        "uptime_info": {
            "manager_started": websocket_manager.stats.last_reset.isoformat(),
            "background_tasks_running": len(websocket_manager._background_tasks)
        }
    }


# Health and system endpoints
@router.get("/health", response_model=WebSocketHealthResponse)
async def websocket_health_check():
    """Check WebSocket system health."""
    try:
        health_info = await check_websocket_health()
        
        return WebSocketHealthResponse(
            status=health_info["status"],
            statistics=health_info["statistics"],
            last_updated=health_info["last_updated"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"WebSocket health check failed: {str(e)}"
        )


@router.get("/capabilities")
async def get_websocket_capabilities():
    """Get WebSocket system capabilities."""
    return {
        "message_types": [msg_type.value for msg_type in MessageType],
        "event_types": [event_type.value for event_type in EventType],
        "subscription_scopes": [scope.value for scope in SubscriptionScope],
        "features": {
            "real_time_messaging": True,
            "event_broadcasting": True,
            "subscription_management": True,
            "rate_limiting": True,
            "authentication": True,
            "connection_management": True,
            "heartbeat_monitoring": True,
            "message_queuing": True,
            "scope_based_filtering": True,
            "custom_event_handlers": True,
            "statistics_tracking": True,
            "health_monitoring": True
        },
        "limits": {
            "max_connections": 10000,
            "max_subscriptions_per_connection": websocket_manager.max_subscriptions_per_connection,
            "rate_limit_per_minute": websocket_manager.rate_limit_per_minute,
            "connection_timeout_seconds": websocket_manager.connection_timeout,
            "heartbeat_interval_seconds": websocket_manager.heartbeat_interval,
            "message_queue_size": 10000,
            "history_retention_hours": 24
        },
        "protocols": {
            "websocket_version": "13",
            "message_format": "JSON",
            "compression": False,
            "subprotocols": []
        }
    }


# Administrative endpoints
@router.post("/admin/shutdown")
async def shutdown_websocket_manager(
    current_user: User = Depends(get_current_user)
):
    """Shutdown WebSocket manager gracefully."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        await websocket_manager.shutdown()
        
        return {
            "message": "WebSocket manager shutdown completed",
            "shutdown_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Shutdown failed: {str(e)}"
        )


@router.post("/admin/broadcast-system-message")
async def broadcast_system_message(
    message: str = Field(..., max_length=1000),
    priority: str = Field("normal", regex="^(low|normal|high|critical)$"),
    current_user: User = Depends(get_current_user)
):
    """Broadcast system message to all connections."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        payload = {
            "message": message,
            "priority": priority,
            "from": "system",
            "broadcast_type": "system_announcement"
        }
        
        sent_count = await websocket_manager.broadcast_event(
            event_type=EventType.SYSTEM_NOTIFICATION,
            payload=payload,
            scope=SubscriptionScope.GLOBAL
        )
        
        return {
            "message": "System message broadcasted",
            "content": message,
            "priority": priority,
            "recipients_count": sent_count,
            "broadcast_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Broadcast failed: {str(e)}"
        )