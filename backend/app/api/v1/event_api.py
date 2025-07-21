"""Event-driven architecture API endpoints."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.core.event_system import (
    event_bus,
    Event,
    EventType,
    EventPriority,
    EventStatus,
    HandlerType,
    check_event_system_health,
    publish_user_event,
    publish_system_event,
    publish_audit_event,
    publish_security_event
)
from app.models.user import User

router = APIRouter()


# Pydantic schemas
class PublishEventRequest(BaseModel):
    """Publish event request."""
    event_type: EventType
    source: str = Field(..., max_length=100)
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: Optional[str] = None
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    organization_id: Optional[str] = None


class SubscribeHandlerRequest(BaseModel):
    """Subscribe event handler request."""
    name: str = Field(..., max_length=100)
    event_types: List[EventType]
    webhook_url: Optional[str] = None
    handler_type: HandlerType = HandlerType.WEBHOOK
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    priority: int = Field(100, ge=1, le=1000)
    timeout_seconds: int = Field(30, ge=1, le=300)


class WebhookSubscriptionRequest(BaseModel):
    """Webhook subscription request."""
    name: str = Field(..., max_length=100)
    event_types: List[EventType]
    webhook_url: str = Field(..., max_length=500)
    secret_key: Optional[str] = Field(None, max_length=100)
    headers: Optional[Dict[str, str]] = Field(default_factory=dict)
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EventQueryRequest(BaseModel):
    """Event query request."""
    event_types: Optional[List[EventType]] = None
    source: Optional[str] = None
    from_time: Optional[datetime] = None
    to_time: Optional[datetime] = None
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class EventResponse(BaseModel):
    """Event response."""
    id: str
    event_type: str
    source: str
    timestamp: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    priority: str
    status: str
    correlation_id: Optional[str]
    user_id: Optional[str]
    organization_id: Optional[str]
    retry_count: int
    processing_time_ms: Optional[float]


class HandlerResponse(BaseModel):
    """Event handler response."""
    id: str
    name: str
    event_types: List[str]
    handler_type: str
    priority: int
    enabled: bool
    execution_count: int
    error_count: int
    avg_execution_time_ms: float
    last_executed: Optional[str]
    created_at: str


class EventStatsResponse(BaseModel):
    """Event statistics response."""
    total_published: int
    total_processed: int
    failed: int
    retried: int
    avg_processing_time_ms: float
    queue_size: int
    handlers_active: int
    subscriptions_active: int


class EventHealthResponse(BaseModel):
    """Event health response."""
    status: str
    is_running: bool
    statistics: Dict[str, Any]
    last_updated: str


# Event publishing endpoints
@router.post("/events/publish")
async def publish_event(
    event_request: PublishEventRequest,
    current_user: User = Depends(get_current_user)
):
    """Publish event to the event bus."""
    try:
        # Create event
        event = Event(
            id="",  # Will be auto-generated
            event_type=event_request.event_type,
            source=event_request.source,
            timestamp=datetime.utcnow(),
            data=event_request.data,
            metadata=event_request.metadata,
            priority=event_request.priority,
            correlation_id=event_request.correlation_id,
            tenant_id=event_request.tenant_id,
            user_id=event_request.user_id or str(current_user.id),
            organization_id=event_request.organization_id or str(current_user.organization_id) if current_user.organization_id else None
        )
        
        # Publish event
        success = await event_bus.publish(event)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to publish event"
            )
        
        return {
            "message": "Event published successfully",
            "event_id": event.id,
            "event_type": event.event_type.value,
            "published_at": event.timestamp.isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish event: {str(e)}"
        )


@router.post("/events/publish/user")
async def publish_user_activity_event(
    event_type: EventType,
    data: Dict[str, Any],
    target_user_id: Optional[str] = None,
    priority: EventPriority = EventPriority.NORMAL,
    current_user: User = Depends(get_current_user)
):
    """Publish user activity event."""
    try:
        user_id = target_user_id or str(current_user.id)
        organization_id = str(current_user.organization_id) if current_user.organization_id else None
        
        success = await publish_user_event(
            event_type=event_type,
            user_id=user_id,
            data=data,
            organization_id=organization_id,
            priority=priority
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to publish user event"
            )
        
        return {
            "message": "User event published successfully",
            "event_type": event_type.value,
            "user_id": user_id,
            "published_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish user event: {str(e)}"
        )


@router.post("/events/publish/system")
async def publish_system_notification(
    event_type: EventType,
    data: Dict[str, Any],
    priority: EventPriority = EventPriority.NORMAL,
    current_user: User = Depends(get_current_user)
):
    """Publish system event."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        success = await publish_system_event(
            event_type=event_type,
            data=data,
            priority=priority
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to publish system event"
            )
        
        return {
            "message": "System event published successfully",
            "event_type": event_type.value,
            "published_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish system event: {str(e)}"
        )


@router.post("/events/publish/audit")
async def publish_audit_action(
    action: str = Field(..., max_length=100),
    resource: str = Field(..., max_length=100),
    target_user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user)
):
    """Publish audit event."""
    try:
        user_id = target_user_id or str(current_user.id)
        organization_id = str(current_user.organization_id) if current_user.organization_id else None
        
        success = await publish_audit_event(
            action=action,
            resource=resource,
            user_id=user_id,
            organization_id=organization_id,
            details=details
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to publish audit event"
            )
        
        return {
            "message": "Audit event published successfully",
            "action": action,
            "resource": resource,
            "user_id": user_id,
            "published_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish audit event: {str(e)}"
        )


@router.post("/events/publish/security")
async def publish_security_alert(
    event_type: EventType,
    details: Dict[str, Any],
    target_user_id: Optional[str] = None,
    priority: EventPriority = EventPriority.CRITICAL,
    current_user: User = Depends(get_current_user)
):
    """Publish security event."""
    try:
        user_id = target_user_id or str(current_user.id)
        
        success = await publish_security_event(
            event_type=event_type,
            user_id=user_id,
            details=details,
            priority=priority
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to publish security event"
            )
        
        return {
            "message": "Security event published successfully",
            "event_type": event_type.value,
            "user_id": user_id,
            "priority": priority.value,
            "published_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish security event: {str(e)}"
        )


# Event subscription management endpoints
@router.post("/events/subscribe/webhook")
async def add_webhook_subscription(
    subscription_request: WebhookSubscriptionRequest,
    current_user: User = Depends(get_current_user)
):
    """Add webhook subscription for events."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        subscription_id = await event_bus.add_webhook_subscription(
            name=subscription_request.name,
            event_types=subscription_request.event_types,
            webhook_url=subscription_request.webhook_url,
            secret_key=subscription_request.secret_key,
            headers=subscription_request.headers,
            filters=subscription_request.filters
        )
        
        return {
            "message": "Webhook subscription created",
            "subscription_id": subscription_id,
            "name": subscription_request.name,
            "event_types": [et.value for et in subscription_request.event_types],
            "webhook_url": subscription_request.webhook_url,
            "created_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create webhook subscription: {str(e)}"
        )


@router.delete("/events/subscriptions/{subscription_id}")
async def remove_webhook_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove webhook subscription."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        success = await event_bus.remove_webhook_subscription(subscription_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        
        return {
            "message": "Webhook subscription removed",
            "subscription_id": subscription_id,
            "removed_at": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove webhook subscription: {str(e)}"
        )


# Event handler management endpoints
@router.get("/events/handlers")
async def get_event_handlers(
    current_user: User = Depends(get_current_user)
):
    """Get list of registered event handlers."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    handlers = []
    
    for handler_id in event_bus.handlers:
        handler_info = event_bus.get_handler_info(handler_id)
        if handler_info:
            handlers.append(HandlerResponse(**handler_info))
    
    return {
        "handlers": handlers,
        "total_count": len(handlers),
        "retrieved_at": datetime.utcnow().isoformat()
    }


@router.get("/events/handlers/{handler_id}")
async def get_event_handler_details(
    handler_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get event handler details."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    handler_info = event_bus.get_handler_info(handler_id)
    
    if not handler_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Handler not found"
        )
    
    return handler_info


@router.delete("/events/handlers/{handler_id}")
async def unsubscribe_event_handler(
    handler_id: str,
    current_user: User = Depends(get_current_user)
):
    """Unsubscribe event handler."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        success = await event_bus.unsubscribe(handler_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Handler not found"
            )
        
        return {
            "message": "Event handler unsubscribed",
            "handler_id": handler_id,
            "unsubscribed_at": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unsubscribe handler: {str(e)}"
        )


# Event history and querying endpoints
@router.get("/events/history")
async def get_event_history(
    event_types: Optional[List[EventType]] = Query(None),
    source: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    organization_id: Optional[str] = Query(None),
    from_time: Optional[datetime] = Query(None),
    to_time: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """Get event history with filtering options."""
    try:
        # Apply organization filter for non-superusers
        if not current_user.is_superuser:
            organization_id = str(current_user.organization_id) if current_user.organization_id else None
        
        # Filter events from history
        filtered_events = []
        
        for event_entry in list(event_bus.event_history):
            # Apply filters
            if event_types and EventType(event_entry["event_type"]) not in event_types:
                continue
            
            if source and event_entry["source"] != source:
                continue
            
            if from_time and event_entry["timestamp"] < from_time:
                continue
            
            if to_time and event_entry["timestamp"] > to_time:
                continue
            
            # Note: user_id and organization_id filtering would require
            # storing this info in event_history, which is not currently done
            
            filtered_events.append({
                "event_id": event_entry["event_id"],
                "event_type": event_entry["event_type"],
                "source": event_entry["source"],
                "timestamp": event_entry["timestamp"].isoformat(),
                "priority": event_entry["priority"]
            })
        
        # Apply pagination
        paginated_events = filtered_events[offset:offset + limit]
        
        return {
            "events": paginated_events,
            "total_count": len(filtered_events),
            "limit": limit,
            "offset": offset,
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve event history: {str(e)}"
        )


@router.get("/events/failed")
async def get_failed_events(
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """Get failed events."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    failed_events = []
    
    for entry in list(event_bus.failed_events)[-limit:]:
        failed_events.append({
            "event": entry["event"].to_dict() if hasattr(entry["event"], "to_dict") else str(entry["event"]),
            "reason": entry.get("reason", "unknown"),
            "error": entry.get("error"),
            "timestamp": entry["timestamp"].isoformat()
        })
    
    return {
        "failed_events": failed_events,
        "total_count": len(failed_events),
        "retrieved_at": datetime.utcnow().isoformat()
    }


@router.get("/events/dead-letter")
async def get_dead_letter_queue(
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """Get dead letter queue events."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    dead_letter_events = []
    
    for event in list(event_bus.dead_letter_queue)[-limit:]:
        dead_letter_events.append(event.to_dict())
    
    return {
        "dead_letter_events": dead_letter_events,
        "total_count": len(dead_letter_events),
        "retrieved_at": datetime.utcnow().isoformat()
    }


# Statistics and monitoring endpoints
@router.get("/events/stats", response_model=EventStatsResponse)
async def get_event_statistics(
    current_user: User = Depends(get_current_user)
):
    """Get event system statistics."""
    stats = event_bus.get_statistics()
    
    return EventStatsResponse(
        total_published=stats["events"]["total_published"],
        total_processed=stats["events"]["total_processed"],
        failed=stats["events"]["failed"],
        retried=stats["events"]["retried"],
        avg_processing_time_ms=stats["events"]["avg_processing_time_ms"],
        queue_size=stats["queue"]["current_size"],
        handlers_active=stats["handlers"]["active"],
        subscriptions_active=stats["subscriptions"]["active"]
    )


@router.get("/events/performance")
async def get_event_performance_metrics(
    hours: int = Query(1, ge=1, le=24),
    current_user: User = Depends(get_current_user)
):
    """Get event system performance metrics."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    # Get recent performance metrics
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    recent_metrics = [
        metric for metric in event_bus.performance_metrics
        if metric["timestamp"] > cutoff_time
    ]
    
    # Calculate aggregated metrics
    if recent_metrics:
        avg_processing_time = sum(m["processing_time_ms"] for m in recent_metrics) / len(recent_metrics)
        success_rate = len([m for m in recent_metrics if m["success"]]) / len(recent_metrics)
        
        # Group by event type
        event_type_metrics = {}
        for metric in recent_metrics:
            event_type = metric["event_type"]
            if event_type not in event_type_metrics:
                event_type_metrics[event_type] = {"count": 0, "avg_time": 0, "success_count": 0}
            
            event_type_metrics[event_type]["count"] += 1
            event_type_metrics[event_type]["avg_time"] += metric["processing_time_ms"]
            if metric["success"]:
                event_type_metrics[event_type]["success_count"] += 1
        
        # Finalize averages
        for event_type, metrics in event_type_metrics.items():
            metrics["avg_time"] = metrics["avg_time"] / metrics["count"]
            metrics["success_rate"] = metrics["success_count"] / metrics["count"]
    else:
        avg_processing_time = 0
        success_rate = 0
        event_type_metrics = {}
    
    return {
        "period_hours": hours,
        "total_events": len(recent_metrics),
        "avg_processing_time_ms": round(avg_processing_time, 2),
        "success_rate": round(success_rate * 100, 2),
        "event_type_breakdown": event_type_metrics,
        "recent_events": recent_metrics[-20:],  # Last 20 events
        "generated_at": datetime.utcnow().isoformat()
    }


# System control endpoints
@router.post("/events/replay")
async def replay_events(
    from_time: datetime,
    to_time: Optional[datetime] = None,
    event_types: Optional[List[EventType]] = None,
    current_user: User = Depends(get_current_user)
):
    """Replay events from a time range."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        replayed_count = await event_bus.replay_events(
            from_time=from_time,
            to_time=to_time,
            event_types=event_types
        )
        
        return {
            "message": "Event replay completed",
            "replayed_count": replayed_count,
            "from_time": from_time.isoformat(),
            "to_time": to_time.isoformat() if to_time else None,
            "event_types": [et.value for et in event_types] if event_types else None,
            "replayed_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Event replay failed: {str(e)}"
        )


# Health check endpoint
@router.get("/events/health", response_model=EventHealthResponse)
async def event_system_health_check():
    """Check event system health."""
    try:
        health_info = await check_event_system_health()
        
        return EventHealthResponse(
            status=health_info["status"],
            is_running=health_info["is_running"],
            statistics=health_info["statistics"],
            last_updated=health_info["last_updated"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Event health check failed: {str(e)}"
        )


@router.get("/events/capabilities")
async def get_event_system_capabilities():
    """Get event system capabilities."""
    return {
        "event_types": [event_type.value for event_type in EventType],
        "event_priorities": [priority.value for priority in EventPriority],
        "event_statuses": [status.value for status in EventStatus],
        "handler_types": [handler_type.value for handler_type in HandlerType],
        "features": {
            "async_processing": True,
            "event_replay": True,
            "dead_letter_queue": True,
            "webhook_subscriptions": True,
            "priority_queuing": True,
            "retry_logic": True,
            "event_filtering": True,
            "performance_monitoring": True,
            "health_monitoring": True,
            "statistics_tracking": True
        },
        "limits": {
            "max_queue_size": event_bus.max_queue_size,
            "worker_count": event_bus.worker_count,
            "batch_size": event_bus.batch_size,
            "max_retry_attempts": 3,
            "default_timeout_seconds": 30,
            "replay_buffer_size": 1000,
            "history_retention_count": 10000
        },
        "configuration": {
            "enable_dead_letter_queue": event_bus.enable_dead_letter_queue,
            "checkpoint_interval": event_bus.checkpoint_interval
        }
    }


# Administrative endpoints
@router.post("/events/admin/start")
async def start_event_system(
    current_user: User = Depends(get_current_user)
):
    """Start event system."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        await event_bus.start()
        
        return {
            "message": "Event system started",
            "is_running": event_bus.is_running,
            "worker_count": len(event_bus.workers),
            "started_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start event system: {str(e)}"
        )


@router.post("/events/admin/stop")
async def stop_event_system(
    current_user: User = Depends(get_current_user)
):
    """Stop event system gracefully."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        await event_bus.stop()
        
        return {
            "message": "Event system stopped",
            "is_running": event_bus.is_running,
            "stopped_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop event system: {str(e)}"
        )