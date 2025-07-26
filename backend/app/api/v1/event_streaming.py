"""
CC02 v55.0 Event Streaming API
Real-time Event Processing and Messaging Management
Day 5 of 7-day intensive backend development
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.events import (
    EventHandler,
    EventStream,
    EventSubscription,
    ProcessedEvent,
)
from app.models.user import User
from app.services.event_streaming_engine import (
    DeliveryMode,
    EventPriority,
    EventType,
    ProcessingStatus,
    streaming_engine,
)

router = APIRouter(prefix="/events", tags=["event-streaming"])


# Request/Response Models
class EventPublishRequest(BaseModel):
    event_type: EventType
    source: str = Field(..., min_length=1, max_length=100)
    data: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: Optional[UUID] = None
    causation_id: Optional[UUID] = None


class EventResponse(BaseModel):
    id: UUID
    type: EventType
    source: str
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    priority: EventPriority
    correlation_id: Optional[UUID]
    causation_id: Optional[UUID]
    version: int

    class Config:
        from_attributes = True


class EventSubscriptionRequest(BaseModel):
    subscriber_id: str = Field(..., min_length=1, max_length=100)
    event_types: List[EventType]
    filters: Dict[str, Any] = Field(default_factory=dict)
    delivery_mode: DeliveryMode = DeliveryMode.AT_LEAST_ONCE
    webhook_url: Optional[str] = Field(None, regex=r"^https?://")
    retry_policy: Dict[str, Any] = Field(default_factory=dict)


class EventSubscriptionResponse(BaseModel):
    id: UUID
    subscriber_id: str
    event_types: List[EventType]
    filters: Dict[str, Any]
    delivery_mode: DeliveryMode
    webhook_url: Optional[str]
    retry_policy: Dict[str, Any]
    is_active: bool
    created_at: datetime
    last_activity: Optional[datetime]
    events_processed: int
    events_failed: int
    success_rate: float

    class Config:
        from_attributes = True


class EventHandlerRequest(BaseModel):
    handler_id: str = Field(..., min_length=1, max_length=100)
    event_types: List[EventType]
    handler_code: str = Field(..., min_length=1)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = Field(default=30, ge=1, le=300)


class EventHandlerResponse(BaseModel):
    id: UUID
    handler_id: str
    event_types: List[EventType]
    configuration: Dict[str, Any]
    timeout_seconds: int
    is_active: bool
    events_processed: int
    events_failed: int
    average_processing_time: float
    success_rate: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProcessingResultResponse(BaseModel):
    event_id: UUID
    handler_id: str
    status: ProcessingStatus
    processing_time: float
    error_message: Optional[str]
    retry_count: int
    processed_at: datetime

    class Config:
        from_attributes = True


class EventReplayRequest(BaseModel):
    event_type: EventType
    start_time: datetime
    end_time: datetime
    target_handlers: Optional[List[str]] = None
    dry_run: bool = Field(default=False)


class EventStreamFilter(BaseModel):
    event_types: Optional[List[EventType]] = None
    sources: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    priority: Optional[EventPriority] = None
    correlation_id: Optional[UUID] = None


# Event Publishing
@router.post(
    "/publish", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED
)
async def publish_event(
    request: EventPublishRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Publish event to the streaming engine"""

    # Validate event data
    if not request.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Event data cannot be empty"
        )

    # Publish event
    event_id = await streaming_engine.publish_event(
        event_type=request.event_type,
        source=request.source,
        data=request.data,
        metadata=request.metadata,
        priority=request.priority,
        correlation_id=request.correlation_id,
        causation_id=request.causation_id,
    )

    return {
        "event_id": event_id,
        "status": "published",
        "message": "Event published successfully",
        "published_at": datetime.utcnow().isoformat(),
    }


@router.post("/publish/batch", response_model=Dict[str, Any])
async def publish_events_batch(
    events: List[EventPublishRequest],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Publish multiple events in batch"""

    if len(events) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch size cannot exceed 100 events",
        )

    published_events = []
    failed_events = []

    for event_request in events:
        try:
            event_id = await streaming_engine.publish_event(
                event_type=event_request.event_type,
                source=event_request.source,
                data=event_request.data,
                metadata=event_request.metadata,
                priority=event_request.priority,
                correlation_id=event_request.correlation_id,
                causation_id=event_request.causation_id,
            )
            published_events.append(str(event_id))
        except Exception as e:
            failed_events.append(
                {
                    "source": event_request.source,
                    "type": event_request.event_type.value,
                    "error": str(e),
                }
            )

    return {
        "published_count": len(published_events),
        "failed_count": len(failed_events),
        "published_events": published_events,
        "failed_events": failed_events,
        "processed_at": datetime.utcnow().isoformat(),
    }


# Event Subscriptions
@router.post(
    "/subscriptions",
    response_model=EventSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_event_subscription(
    request: EventSubscriptionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create event subscription"""

    # Create subscription
    subscription_id = await streaming_engine.subscribe_to_events(
        subscriber_id=request.subscriber_id,
        event_types=request.event_types,
        filters=request.filters,
    )

    # Store subscription in database
    subscription = EventSubscription(
        id=UUID(subscription_id),
        subscriber_id=request.subscriber_id,
        event_types=[et.value for et in request.event_types],
        filters=request.filters,
        delivery_mode=request.delivery_mode,
        webhook_url=request.webhook_url,
        retry_policy=request.retry_policy,
        is_active=True,
        created_at=datetime.utcnow(),
        created_by=current_user.id,
    )

    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)

    return EventSubscriptionResponse(
        id=subscription.id,
        subscriber_id=subscription.subscriber_id,
        event_types=[EventType(et) for et in subscription.event_types],
        filters=subscription.filters,
        delivery_mode=subscription.delivery_mode,
        webhook_url=subscription.webhook_url,
        retry_policy=subscription.retry_policy,
        is_active=subscription.is_active,
        created_at=subscription.created_at,
        last_activity=None,
        events_processed=0,
        events_failed=0,
        success_rate=0.0,
    )


@router.get("/subscriptions", response_model=List[EventSubscriptionResponse])
async def list_event_subscriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    subscriber_id: Optional[str] = Query(None),
    event_type: Optional[EventType] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List event subscriptions"""

    query = select(EventSubscription)

    if subscriber_id:
        query = query.where(EventSubscription.subscriber_id == subscriber_id)

    if event_type:
        query = query.where(EventSubscription.event_types.contains([event_type.value]))

    if is_active is not None:
        query = query.where(EventSubscription.is_active == is_active)

    query = (
        query.offset(skip).limit(limit).order_by(EventSubscription.created_at.desc())
    )

    result = await db.execute(query)
    subscriptions = result.scalars().all()

    return [
        EventSubscriptionResponse(
            id=sub.id,
            subscriber_id=sub.subscriber_id,
            event_types=[EventType(et) for et in sub.event_types],
            filters=sub.filters,
            delivery_mode=sub.delivery_mode,
            webhook_url=sub.webhook_url,
            retry_policy=sub.retry_policy,
            is_active=sub.is_active,
            created_at=sub.created_at,
            last_activity=None,  # Would calculate from processing logs
            events_processed=0,  # Would calculate from processing logs
            events_failed=0,  # Would calculate from processing logs
            success_rate=0.0,  # Would calculate from processing logs
        )
        for sub in subscriptions
    ]


@router.delete("/subscriptions/{subscription_id}")
async def delete_event_subscription(
    subscription_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete event subscription"""

    # Deactivate subscription in streaming engine
    await streaming_engine.event_bus.unsubscribe(str(subscription_id))

    # Update database record
    result = await db.execute(
        update(EventSubscription)
        .where(EventSubscription.id == subscription_id)
        .values(is_active=False, updated_at=datetime.utcnow())
    )

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    await db.commit()

    return {"message": "Subscription deleted successfully"}


# Event Handlers
@router.post(
    "/handlers",
    response_model=EventHandlerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_event_handler(
    request: EventHandlerRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create custom event handler"""

    # Create handler record
    handler = EventHandler(
        id=uuid4(),
        handler_id=request.handler_id,
        event_types=[et.value for et in request.event_types],
        handler_code=request.handler_code,
        configuration=request.configuration,
        timeout_seconds=request.timeout_seconds,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by=current_user.id,
    )

    db.add(handler)
    await db.commit()
    await db.refresh(handler)

    # TODO: Register handler with streaming engine
    # This would involve creating a dynamic handler class from the handler_code

    return EventHandlerResponse(
        id=handler.id,
        handler_id=handler.handler_id,
        event_types=[EventType(et) for et in handler.event_types],
        configuration=handler.configuration,
        timeout_seconds=handler.timeout_seconds,
        is_active=handler.is_active,
        events_processed=0,
        events_failed=0,
        average_processing_time=0.0,
        success_rate=0.0,
        created_at=handler.created_at,
        updated_at=handler.updated_at,
    )


@router.get("/handlers", response_model=List[EventHandlerResponse])
async def list_event_handlers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    event_type: Optional[EventType] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List event handlers"""

    query = select(EventHandler)

    if event_type:
        query = query.where(EventHandler.event_types.contains([event_type.value]))

    if is_active is not None:
        query = query.where(EventHandler.is_active == is_active)

    query = query.offset(skip).limit(limit).order_by(EventHandler.created_at.desc())

    result = await db.execute(query)
    handlers = result.scalars().all()

    return [
        EventHandlerResponse(
            id=handler.id,
            handler_id=handler.handler_id,
            event_types=[EventType(et) for et in handler.event_types],
            configuration=handler.configuration,
            timeout_seconds=handler.timeout_seconds,
            is_active=handler.is_active,
            events_processed=0,  # Would calculate from processing logs
            events_failed=0,  # Would calculate from processing logs
            average_processing_time=0.0,  # Would calculate from processing logs
            success_rate=0.0,  # Would calculate from processing logs
            created_at=handler.created_at,
            updated_at=handler.updated_at,
        )
        for handler in handlers
    ]


# Event History and Querying
@router.get("/history", response_model=List[EventResponse])
async def get_event_history(
    event_type: Optional[EventType] = Query(None),
    source: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    priority: Optional[EventPriority] = Query(None),
    correlation_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get event history"""

    # If event_type is specified, get from streaming engine
    if event_type:
        events = await streaming_engine.get_event_history(
            event_type=event_type, start_time=start_time, end_time=end_time, limit=limit
        )

        filtered_events = []
        for event in events:
            # Apply additional filters
            if source and event.source != source:
                continue
            if priority and event.priority != priority:
                continue
            if correlation_id and event.correlation_id != correlation_id:
                continue

            filtered_events.append(
                EventResponse(
                    id=event.id,
                    type=event.type,
                    source=event.source,
                    timestamp=event.timestamp,
                    data=event.data,
                    metadata=event.metadata,
                    priority=event.priority,
                    correlation_id=event.correlation_id,
                    causation_id=event.causation_id,
                    version=event.version,
                )
            )

        return filtered_events[skip : skip + limit]

    # Otherwise query from database
    query = select(EventStream)

    if source:
        query = query.where(EventStream.source == source)

    if start_time:
        query = query.where(EventStream.timestamp >= start_time)

    if end_time:
        query = query.where(EventStream.timestamp <= end_time)

    if priority:
        query = query.where(EventStream.priority == priority)

    if correlation_id:
        query = query.where(EventStream.correlation_id == correlation_id)

    query = query.offset(skip).limit(limit).order_by(EventStream.timestamp.desc())

    result = await db.execute(query)
    events = result.scalars().all()

    return [
        EventResponse(
            id=event.id,
            type=EventType(event.event_type),
            source=event.source,
            timestamp=event.timestamp,
            data=event.data,
            metadata=event.metadata,
            priority=EventPriority(event.priority),
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            version=event.version,
        )
        for event in events
    ]


@router.get("/stream")
async def stream_events(
    event_type: EventType = Query(...),
    source: Optional[str] = Query(None),
    priority: Optional[EventPriority] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Stream events in real-time (Server-Sent Events)"""

    async def event_generator() -> None:
        """Generate SSE events"""
        # Subscribe to events
        subscription_id = await streaming_engine.subscribe_to_events(
            subscriber_id=f"sse_{current_user.id}_{datetime.utcnow().timestamp()}",
            event_types=[event_type],
        )

        try:
            # Stream events from Redis
            async for event in streaming_engine.event_bus.get_event_stream(event_type):
                # Apply filters
                if source and event.source != source:
                    continue
                if priority and event.priority != priority:
                    continue

                # Format as SSE
                event_data = {
                    "id": str(event.id),
                    "type": event.type.value,
                    "source": event.source,
                    "timestamp": event.timestamp.isoformat(),
                    "data": event.data,
                    "metadata": event.metadata,
                    "priority": event.priority.value,
                }

                yield f"data: {json.dumps(event_data)}\n\n"

                # Add small delay to prevent overwhelming the client
                await asyncio.sleep(0.1)

        finally:
            # Cleanup subscription
            await streaming_engine.event_bus.unsubscribe(subscription_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )


# Event Processing and Analytics
@router.get("/processing/status")
async def get_processing_status(
    event_id: Optional[UUID] = Query(None),
    handler_id: Optional[str] = Query(None),
    status: Optional[ProcessingStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get event processing status"""

    query = select(ProcessedEvent)

    if event_id:
        query = query.where(ProcessedEvent.event_id == event_id)

    if handler_id:
        query = query.where(ProcessedEvent.handler_id == handler_id)

    if status:
        query = query.where(ProcessedEvent.status == status)

    query = query.offset(skip).limit(limit).order_by(ProcessedEvent.processed_at.desc())

    result = await db.execute(query)
    processed_events = result.scalars().all()

    return [
        ProcessingResultResponse(
            event_id=pe.event_id,
            handler_id=pe.handler_id,
            status=ProcessingStatus(pe.status),
            processing_time=pe.processing_time,
            error_message=pe.error_message,
            retry_count=pe.retry_count,
            processed_at=pe.processed_at,
        )
        for pe in processed_events
    ]


@router.get("/metrics")
async def get_event_metrics(
    period_hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get event processing metrics"""

    # Get metrics from streaming engine
    engine_metrics = await streaming_engine.get_processing_metrics()

    # Get additional metrics from database
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=period_hours)

    # Event counts by type
    event_counts = await db.execute(
        select(EventStream.event_type, func.count(EventStream.id).label("count"))
        .where(
            and_(EventStream.timestamp >= start_time, EventStream.timestamp <= end_time)
        )
        .group_by(EventStream.event_type)
    )

    # Processing statistics
    processing_stats = await db.execute(
        select(
            func.count(ProcessedEvent.id).label("total_processed"),
            func.count(ProcessedEvent.id)
            .filter(ProcessedEvent.status == ProcessingStatus.SUCCESS)
            .label("successful"),
            func.count(ProcessedEvent.id)
            .filter(ProcessedEvent.status == ProcessingStatus.FAILED)
            .label("failed"),
            func.avg(ProcessedEvent.processing_time).label("avg_processing_time"),
        ).where(
            and_(
                ProcessedEvent.processed_at >= start_time,
                ProcessedEvent.processed_at <= end_time,
            )
        )
    )

    event_type_counts = {row.event_type: row.count for row in event_counts.fetchall()}
    stats = processing_stats.first()

    total_processed = stats.total_processed or 0
    successful = stats.successful or 0

    return {
        "period": {
            "hours": period_hours,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        },
        "events": {
            "by_type": event_type_counts,
            "total_published": sum(event_type_counts.values()),
        },
        "processing": {
            "total_processed": total_processed,
            "successful": successful,
            "failed": stats.failed or 0,
            "success_rate": (successful / total_processed * 100)
            if total_processed > 0
            else 0,
            "average_processing_time": float(stats.avg_processing_time or 0),
        },
        "engine_metrics": engine_metrics,
        "generated_at": datetime.utcnow().isoformat(),
    }


# Event Replay and Recovery
@router.post("/replay")
async def replay_events(
    request: EventReplayRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Replay events for reprocessing"""

    if request.dry_run:
        # Count events that would be replayed
        events = await streaming_engine.get_event_history(
            event_type=request.event_type,
            start_time=request.start_time,
            end_time=request.end_time,
            limit=10000,
        )

        return {
            "dry_run": True,
            "events_to_replay": len(events),
            "event_type": request.event_type.value,
            "time_range": {
                "start": request.start_time.isoformat(),
                "end": request.end_time.isoformat(),
            },
            "target_handlers": request.target_handlers,
        }

    # Execute replay in background
    background_tasks.add_task(
        _execute_event_replay,
        request.event_type,
        request.start_time,
        request.end_time,
        request.target_handlers,
    )

    return {
        "status": "replay_started",
        "message": "Event replay has been initiated in the background",
        "event_type": request.event_type.value,
        "time_range": {
            "start": request.start_time.isoformat(),
            "end": request.end_time.isoformat(),
        },
        "target_handlers": request.target_handlers,
        "initiated_at": datetime.utcnow().isoformat(),
    }


async def _execute_event_replay(
    event_type: EventType,
    start_time: datetime,
    end_time: datetime,
    target_handlers: Optional[List[str]],
):
    """Execute event replay in background"""
    try:
        result = await streaming_engine.replay_events(
            event_type, start_time, end_time, target_handlers
        )
        # Log replay completion
        print(f"Event replay completed: {result}")
    except Exception as e:
        # Log replay error
        print(f"Event replay failed: {e}")


# System Management
@router.post("/system/start")
async def start_event_processing(current_user: User = Depends(get_current_active_user)):
    """Start event processing system"""

    # This would typically be handled by a system administrator
    # For demo purposes, we'll return success

    return {
        "status": "started",
        "message": "Event processing system started",
        "started_at": datetime.utcnow().isoformat(),
    }


@router.post("/system/stop")
async def stop_event_processing(current_user: User = Depends(get_current_active_user)):
    """Stop event processing system"""

    await streaming_engine.shutdown()

    return {
        "status": "stopped",
        "message": "Event processing system stopped",
        "stopped_at": datetime.utcnow().isoformat(),
    }


@router.get("/system/health")
async def get_system_health() -> None:
    """Get event system health status"""

    metrics = await streaming_engine.get_processing_metrics()

    # Determine health status
    health_status = "healthy"
    issues = []

    if metrics.get("dead_letter_queue_size", 0) > 100:
        health_status = "degraded"
        issues.append("High number of events in dead letter queue")

    if metrics.get("success_rate", 100) < 90:
        health_status = "degraded"
        issues.append("Low event processing success rate")

    return {
        "status": health_status,
        "issues": issues,
        "metrics": metrics,
        "checked_at": datetime.utcnow().isoformat(),
    }
