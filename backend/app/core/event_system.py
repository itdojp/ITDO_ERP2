"""Event-driven architecture system with comprehensive event management."""

import asyncio
import json
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union
from uuid import uuid4

from app.core.monitoring import monitor_performance


class EventType(str, Enum):
    """System event types."""
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    
    ORGANIZATION_CREATED = "organization.created"
    ORGANIZATION_UPDATED = "organization.updated"
    ORGANIZATION_DELETED = "organization.deleted"
    
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"
    TASK_DELETED = "task.deleted"
    
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    
    SECURITY_ALERT = "security.alert"
    SECURITY_BREACH = "security.breach"
    SECURITY_LOGIN_FAILED = "security.login_failed"
    
    AUDIT_LOG_CREATED = "audit.log_created"
    AUDIT_COMPLIANCE_CHECK = "audit.compliance_check"
    
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    SYSTEM_HEALTH_CHECK = "system.health_check"
    
    DATA_CREATED = "data.created"
    DATA_UPDATED = "data.updated"
    DATA_DELETED = "data.deleted"
    DATA_EXPORTED = "data.exported"
    DATA_IMPORTED = "data.imported"
    
    NOTIFICATION_SENT = "notification.sent"
    NOTIFICATION_FAILED = "notification.failed"
    
    CACHE_HIT = "cache.hit"
    CACHE_MISS = "cache.miss"
    CACHE_EVICTED = "cache.evicted"
    
    PERFORMANCE_METRIC = "performance.metric"
    PERFORMANCE_THRESHOLD_EXCEEDED = "performance.threshold_exceeded"
    
    CUSTOM = "custom"


class EventPriority(str, Enum):
    """Event priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class EventStatus(str, Enum):
    """Event processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    RETRY = "retry"
    DEAD_LETTER = "dead_letter"


class HandlerType(str, Enum):
    """Event handler types."""
    SYNC = "sync"
    ASYNC = "async"
    WEBHOOK = "webhook"
    QUEUE = "queue"


@dataclass
class Event:
    """System event data structure."""
    id: str
    event_type: EventType
    source: str
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    status: EventStatus = EventStatus.PENDING
    correlation_id: Optional[str] = None
    parent_event_id: Optional[str] = None
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    processing_time_ms: Optional[float] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())
        if not self.correlation_id:
            self.correlation_id = str(uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "metadata": self.metadata,
            "priority": self.priority.value,
            "status": self.status.value,
            "correlation_id": self.correlation_id,
            "parent_event_id": self.parent_event_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "processing_time_ms": self.processing_time_ms
        }

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict(), default=str)


@dataclass
class EventHandler:
    """Event handler configuration."""
    id: str
    name: str
    event_types: Set[EventType]
    handler_func: Callable
    handler_type: HandlerType = HandlerType.ASYNC
    priority: int = 100
    timeout_seconds: int = 30
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    filters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_executed: Optional[datetime] = None
    execution_count: int = 0
    error_count: int = 0
    avg_execution_time_ms: float = 0.0
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())
        if not self.retry_policy:
            self.retry_policy = {
                "max_retries": 3,
                "backoff_factor": 2.0,
                "max_delay_seconds": 300
            }

    def matches_event(self, event: Event) -> bool:
        """Check if handler matches event."""
        if not self.enabled:
            return False
        
        if event.event_type not in self.event_types:
            return False
        
        # Apply filters
        for filter_key, filter_value in self.filters.items():
            if filter_key == "tenant_id":
                if event.tenant_id != filter_value:
                    return False
            elif filter_key == "organization_id":
                if event.organization_id != filter_value:
                    return False
            elif filter_key == "priority":
                if isinstance(filter_value, list):
                    if event.priority not in filter_value:
                        return False
                elif event.priority != filter_value:
                    return False
            elif filter_key in event.data:
                if event.data[filter_key] != filter_value:
                    return False
        
        return True


@dataclass
class EventSubscription:
    """Event subscription for external systems."""
    id: str
    name: str
    event_types: Set[EventType]
    webhook_url: str
    secret_key: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    filters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_delivery: Optional[datetime] = None
    delivery_count: int = 0
    failure_count: int = 0
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


@dataclass
class EventStats:
    """Event system statistics."""
    total_events_published: int = 0
    total_events_processed: int = 0
    events_failed: int = 0
    events_retried: int = 0
    avg_processing_time_ms: float = 0.0
    handlers_registered: int = 0
    active_handlers: int = 0
    subscriptions_active: int = 0
    queue_size: int = 0
    dead_letter_queue_size: int = 0
    last_reset: datetime = field(default_factory=datetime.utcnow)


class EventBus:
    """Advanced event bus with comprehensive event management."""
    
    def __init__(
        self,
        max_queue_size: int = 10000,
        worker_count: int = 10,
        batch_size: int = 100,
        enable_dead_letter_queue: bool = True
    ):
        """Initialize event bus."""
        self.max_queue_size = max_queue_size
        self.worker_count = worker_count
        self.batch_size = batch_size
        self.enable_dead_letter_queue = enable_dead_letter_queue
        
        # Event management
        self.event_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.dead_letter_queue: deque = deque(maxlen=1000)
        self.processing_events: Dict[str, Event] = {}
        
        # Handler management
        self.handlers: Dict[str, EventHandler] = {}
        self.event_type_handlers: Dict[EventType, List[str]] = defaultdict(list)
        
        # Subscription management
        self.subscriptions: Dict[str, EventSubscription] = {}
        
        # Event storage and history
        self.event_history: deque = deque(maxlen=10000)
        self.failed_events: deque = deque(maxlen=1000)
        
        # Statistics and monitoring
        self.stats = EventStats()
        self.performance_metrics: deque = deque(maxlen=1000)
        
        # Background workers
        self.workers: List[asyncio.Task] = []
        self.is_running = False
        
        # Event replay and recovery
        self.replay_buffer: deque = deque(maxlen=1000)
        self.checkpoint_interval = 100
        self.last_checkpoint = 0

    async def start(self) -> None:
        """Start the event bus."""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start worker tasks
        for i in range(self.worker_count):
            worker = asyncio.create_task(self._event_worker(f"worker-{i}"))
            self.workers.append(worker)
        
        # Start background tasks
        self.workers.append(asyncio.create_task(self._stats_collector()))
        self.workers.append(asyncio.create_task(self._dead_letter_processor()))
        self.workers.append(asyncio.create_task(self._subscription_processor()))
        
        # Publish startup event
        await self.publish(Event(
            id=str(uuid4()),
            event_type=EventType.SYSTEM_STARTUP,
            source="event_bus",
            timestamp=datetime.utcnow(),
            data={"worker_count": self.worker_count, "queue_size": self.max_queue_size}
        ))

    async def stop(self) -> None:
        """Stop the event bus gracefully."""
        if not self.is_running:
            return
        
        # Publish shutdown event
        await self.publish(Event(
            id=str(uuid4()),
            event_type=EventType.SYSTEM_SHUTDOWN,
            source="event_bus",
            timestamp=datetime.utcnow(),
            data={"reason": "graceful_shutdown"}
        ))
        
        self.is_running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
        
        self.workers.clear()

    @monitor_performance("event_bus.publish")
    async def publish(self, event: Event) -> bool:
        """Publish event to the bus."""
        try:
            # Add to replay buffer for recovery
            self.replay_buffer.append(event)
            
            # Validate event
            if not await self._validate_event(event):
                return False
            
            # Check queue capacity
            if self.event_queue.qsize() >= self.max_queue_size:
                # Handle queue overflow
                await self._handle_queue_overflow(event)
                return False
            
            # Add to queue
            await self.event_queue.put(event)
            self.stats.total_events_published += 1
            
            # Add to history
            self.event_history.append({
                "event_id": event.id,
                "event_type": event.event_type.value,
                "source": event.source,
                "timestamp": event.timestamp,
                "priority": event.priority.value
            })
            
            return True
            
        except Exception as e:
            self.stats.events_failed += 1
            await self._handle_publish_error(event, e)
            return False

    async def subscribe(
        self,
        event_types: Union[EventType, List[EventType]],
        handler_func: Callable,
        handler_name: Optional[str] = None,
        handler_type: HandlerType = HandlerType.ASYNC,
        filters: Optional[Dict[str, Any]] = None,
        priority: int = 100,
        timeout_seconds: int = 30
    ) -> str:
        """Subscribe to events with a handler function."""
        if isinstance(event_types, EventType):
            event_types = [event_types]
        
        handler_id = str(uuid4())
        handler = EventHandler(
            id=handler_id,
            name=handler_name or f"handler_{handler_id[:8]}",
            event_types=set(event_types),
            handler_func=handler_func,
            handler_type=handler_type,
            filters=filters or {},
            priority=priority,
            timeout_seconds=timeout_seconds
        )
        
        self.handlers[handler_id] = handler
        
        # Map event types to handlers
        for event_type in event_types:
            self.event_type_handlers[event_type].append(handler_id)
            # Sort by priority
            self.event_type_handlers[event_type].sort(
                key=lambda h_id: self.handlers[h_id].priority
            )
        
        self.stats.handlers_registered += 1
        self.stats.active_handlers = len([h for h in self.handlers.values() if h.enabled])
        
        return handler_id

    async def unsubscribe(self, handler_id: str) -> bool:
        """Unsubscribe handler from events."""
        if handler_id not in self.handlers:
            return False
        
        handler = self.handlers[handler_id]
        
        # Remove from event type mappings
        for event_type in handler.event_types:
            if handler_id in self.event_type_handlers[event_type]:
                self.event_type_handlers[event_type].remove(handler_id)
        
        # Remove handler
        del self.handlers[handler_id]
        
        self.stats.active_handlers = len([h for h in self.handlers.values() if h.enabled])
        
        return True

    async def add_webhook_subscription(
        self,
        name: str,
        event_types: Union[EventType, List[EventType]],
        webhook_url: str,
        secret_key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add webhook subscription for events."""
        if isinstance(event_types, EventType):
            event_types = [event_types]
        
        subscription = EventSubscription(
            id=str(uuid4()),
            name=name,
            event_types=set(event_types),
            webhook_url=webhook_url,
            secret_key=secret_key,
            headers=headers or {},
            filters=filters or {}
        )
        
        self.subscriptions[subscription.id] = subscription
        self.stats.subscriptions_active += 1
        
        return subscription.id

    async def remove_webhook_subscription(self, subscription_id: str) -> bool:
        """Remove webhook subscription."""
        if subscription_id not in self.subscriptions:
            return False
        
        del self.subscriptions[subscription_id]
        self.stats.subscriptions_active -= 1
        
        return True

    async def _event_worker(self, worker_name: str) -> None:
        """Event processing worker."""
        while self.is_running:
            try:
                # Get event from queue with timeout
                try:
                    event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # Track processing
                self.processing_events[event.id] = event
                event.status = EventStatus.PROCESSING
                
                # Process event
                start_time = time.time()
                success = await self._process_event(event)
                processing_time = (time.time() - start_time) * 1000
                
                # Update event
                event.processing_time_ms = processing_time
                event.status = EventStatus.PROCESSED if success else EventStatus.FAILED
                
                # Record metrics
                self.performance_metrics.append({
                    "worker": worker_name,
                    "event_id": event.id,
                    "event_type": event.event_type.value,
                    "processing_time_ms": processing_time,
                    "success": success,
                    "timestamp": datetime.utcnow()
                })
                
                # Update statistics
                if success:
                    self.stats.total_events_processed += 1
                else:
                    self.stats.events_failed += 1
                    
                    # Handle retry logic
                    if event.retry_count < event.max_retries:
                        event.retry_count += 1
                        event.status = EventStatus.RETRY
                        await self._schedule_retry(event)
                        self.stats.events_retried += 1
                    elif self.enable_dead_letter_queue:
                        event.status = EventStatus.DEAD_LETTER
                        self.dead_letter_queue.append(event)
                
                # Remove from processing
                self.processing_events.pop(event.id, None)
                
            except Exception as e:
                print(f"Event worker {worker_name} error: {e}")
                await asyncio.sleep(1)

    async def _process_event(self, event: Event) -> bool:
        """Process single event through all matching handlers."""
        success = True
        
        # Get matching handlers
        matching_handlers = []
        for handler_id in self.event_type_handlers.get(event.event_type, []):
            if handler_id in self.handlers:
                handler = self.handlers[handler_id]
                if handler.matches_event(event):
                    matching_handlers.append(handler)
        
        # Process with each matching handler
        for handler in matching_handlers:
            try:
                # Update handler stats
                handler.last_executed = datetime.utcnow()
                handler.execution_count += 1
                
                # Execute handler
                start_time = time.time()
                
                if handler.handler_type == HandlerType.ASYNC:
                    await asyncio.wait_for(
                        handler.handler_func(event),
                        timeout=handler.timeout_seconds
                    )
                elif handler.handler_type == HandlerType.SYNC:
                    # Run sync handler in thread pool
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, handler.handler_func, event)
                
                # Update handler performance
                execution_time = (time.time() - start_time) * 1000
                handler.avg_execution_time_ms = (
                    (handler.avg_execution_time_ms * (handler.execution_count - 1) + execution_time)
                    / handler.execution_count
                )
                
            except asyncio.TimeoutError:
                handler.error_count += 1
                success = False
                print(f"Handler {handler.name} timed out processing event {event.id}")
                
            except Exception as e:
                handler.error_count += 1
                success = False
                print(f"Handler {handler.name} failed processing event {event.id}: {e}")
        
        return success

    async def _schedule_retry(self, event: Event) -> None:
        """Schedule event retry with exponential backoff."""
        backoff_factor = 2.0
        max_delay = 300  # 5 minutes
        
        delay = min(backoff_factor ** event.retry_count, max_delay)
        
        # Schedule retry
        async def retry_event():
            await asyncio.sleep(delay)
            if self.is_running:
                await self.event_queue.put(event)
        
        asyncio.create_task(retry_event())

    async def _stats_collector(self) -> None:
        """Background task to collect statistics."""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Update every minute
                
                # Update queue size
                self.stats.queue_size = self.event_queue.qsize()
                self.stats.dead_letter_queue_size = len(self.dead_letter_queue)
                
                # Calculate average processing time
                recent_metrics = [
                    m for m in self.performance_metrics
                    if (datetime.utcnow() - m["timestamp"]).total_seconds() < 300  # Last 5 minutes
                ]
                
                if recent_metrics:
                    self.stats.avg_processing_time_ms = sum(
                        m["processing_time_ms"] for m in recent_metrics
                    ) / len(recent_metrics)
                
            except Exception as e:
                print(f"Stats collector error: {e}")

    async def _dead_letter_processor(self) -> None:
        """Background task to process dead letter queue."""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Process every 5 minutes
                
                # Process dead letter queue
                if self.dead_letter_queue:
                    # Could implement logic to retry dead letter events
                    # or send them to external systems for manual processing
                    pass
                
            except Exception as e:
                print(f"Dead letter processor error: {e}")

    async def _subscription_processor(self) -> None:
        """Background task to process webhook subscriptions."""
        while self.is_running:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds
                
                # Process webhook subscriptions
                # This would integrate with HTTP client to send webhooks
                for subscription in self.subscriptions.values():
                    if subscription.enabled:
                        # Check for pending events for this subscription
                        pass
                
            except Exception as e:
                print(f"Subscription processor error: {e}")

    async def _validate_event(self, event: Event) -> bool:
        """Validate event before processing."""
        if not event.id:
            return False
        
        if not event.event_type:
            return False
        
        if not event.source:
            return False
        
        if not event.timestamp:
            return False
        
        return True

    async def _handle_queue_overflow(self, event: Event) -> None:
        """Handle queue overflow situation."""
        # Could implement priority-based dropping or external queue
        if event.priority in [EventPriority.CRITICAL, EventPriority.EMERGENCY]:
            # Force add critical events
            try:
                self.event_queue.put_nowait(event)
            except asyncio.QueueFull:
                # Drop oldest low priority event
                await self._drop_lowest_priority_event()
                self.event_queue.put_nowait(event)
        else:
            # Drop the event
            self.failed_events.append({
                "event": event,
                "reason": "queue_overflow",
                "timestamp": datetime.utcnow()
            })

    async def _drop_lowest_priority_event(self) -> None:
        """Drop lowest priority event from queue."""
        # This is a simplified implementation
        # In production, would need a priority queue
        pass

    async def _handle_publish_error(self, event: Event, error: Exception) -> None:
        """Handle event publish errors."""
        self.failed_events.append({
            "event": event,
            "error": str(error),
            "timestamp": datetime.utcnow()
        })

    def get_handler_info(self, handler_id: str) -> Optional[Dict[str, Any]]:
        """Get handler information."""
        if handler_id not in self.handlers:
            return None
        
        handler = self.handlers[handler_id]
        
        return {
            "id": handler.id,
            "name": handler.name,
            "event_types": [et.value for et in handler.event_types],
            "handler_type": handler.handler_type.value,
            "priority": handler.priority,
            "enabled": handler.enabled,
            "execution_count": handler.execution_count,
            "error_count": handler.error_count,
            "avg_execution_time_ms": round(handler.avg_execution_time_ms, 2),
            "last_executed": handler.last_executed.isoformat() if handler.last_executed else None,
            "created_at": handler.created_at.isoformat()
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        return {
            "events": {
                "total_published": self.stats.total_events_published,
                "total_processed": self.stats.total_events_processed,
                "failed": self.stats.events_failed,
                "retried": self.stats.events_retried,
                "avg_processing_time_ms": round(self.stats.avg_processing_time_ms, 2)
            },
            "queue": {
                "current_size": self.stats.queue_size,
                "max_size": self.max_queue_size,
                "dead_letter_size": self.stats.dead_letter_queue_size,
                "processing_events": len(self.processing_events)
            },
            "handlers": {
                "registered": self.stats.handlers_registered,
                "active": self.stats.active_handlers,
                "by_event_type": {
                    event_type.value: len(handlers)
                    for event_type, handlers in self.event_type_handlers.items()
                }
            },
            "subscriptions": {
                "active": self.stats.subscriptions_active
            },
            "workers": {
                "count": self.worker_count,
                "running": len(self.workers),
                "batch_size": self.batch_size
            },
            "performance": {
                "recent_events": len([
                    m for m in self.performance_metrics
                    if (datetime.utcnow() - m["timestamp"]).total_seconds() < 300
                ]),
                "replay_buffer_size": len(self.replay_buffer),
                "failed_events": len(self.failed_events)
            }
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform event bus health check."""
        stats = self.get_statistics()
        
        # Determine health status
        queue_utilization = stats["queue"]["current_size"] / stats["queue"]["max_size"]
        error_rate = (
            stats["events"]["failed"] / max(stats["events"]["total_published"], 1)
        )
        
        if error_rate > 0.1:
            status = "critical"
        elif error_rate > 0.05 or queue_utilization > 0.8:
            status = "degraded"
        elif queue_utilization > 0.6:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "is_running": self.is_running,
            "statistics": stats,
            "last_updated": datetime.utcnow().isoformat()
        }

    async def replay_events(
        self,
        from_time: datetime,
        to_time: Optional[datetime] = None,
        event_types: Optional[List[EventType]] = None
    ) -> int:
        """Replay events from a time range."""
        if not to_time:
            to_time = datetime.utcnow()
        
        replayed_count = 0
        
        for event in self.replay_buffer:
            if (from_time <= event.timestamp <= to_time and
                (not event_types or event.event_type in event_types)):
                
                # Create new event for replay
                replay_event = Event(
                    id=str(uuid4()),
                    event_type=event.event_type,
                    source=f"replay:{event.source}",
                    timestamp=datetime.utcnow(),
                    data=event.data.copy(),
                    metadata={**event.metadata, "replayed_from": event.id},
                    priority=event.priority,
                    correlation_id=event.correlation_id,
                    parent_event_id=event.id,
                    tenant_id=event.tenant_id,
                    user_id=event.user_id,
                    organization_id=event.organization_id
                )
                
                if await self.publish(replay_event):
                    replayed_count += 1
        
        return replayed_count


# Global event bus instance
event_bus = EventBus(
    max_queue_size=10000,
    worker_count=10,
    batch_size=100,
    enable_dead_letter_queue=True
)


# Health check function
async def check_event_system_health() -> Dict[str, Any]:
    """Check event system health."""
    return await event_bus.health_check()


# Convenience functions for common event operations
async def publish_user_event(
    event_type: EventType,
    user_id: str,
    data: Dict[str, Any],
    organization_id: Optional[str] = None,
    priority: EventPriority = EventPriority.NORMAL
) -> bool:
    """Publish user-related event."""
    event = Event(
        id=str(uuid4()),
        event_type=event_type,
        source="user_service",
        timestamp=datetime.utcnow(),
        data=data,
        user_id=user_id,
        organization_id=organization_id,
        priority=priority
    )
    
    return await event_bus.publish(event)


async def publish_system_event(
    event_type: EventType,
    data: Dict[str, Any],
    priority: EventPriority = EventPriority.NORMAL
) -> bool:
    """Publish system-related event."""
    event = Event(
        id=str(uuid4()),
        event_type=event_type,
        source="system",
        timestamp=datetime.utcnow(),
        data=data,
        priority=priority
    )
    
    return await event_bus.publish(event)


async def publish_audit_event(
    action: str,
    resource: str,
    user_id: str,
    organization_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> bool:
    """Publish audit event."""
    event = Event(
        id=str(uuid4()),
        event_type=EventType.AUDIT_LOG_CREATED,
        source="audit_service",
        timestamp=datetime.utcnow(),
        data={
            "action": action,
            "resource": resource,
            "details": details or {}
        },
        user_id=user_id,
        organization_id=organization_id,
        priority=EventPriority.HIGH
    )
    
    return await event_bus.publish(event)


async def publish_security_event(
    event_type: EventType,
    user_id: Optional[str],
    details: Dict[str, Any],
    priority: EventPriority = EventPriority.CRITICAL
) -> bool:
    """Publish security-related event."""
    event = Event(
        id=str(uuid4()),
        event_type=event_type,
        source="security_service",
        timestamp=datetime.utcnow(),
        data=details,
        user_id=user_id,
        priority=priority
    )
    
    return await event_bus.publish(event)