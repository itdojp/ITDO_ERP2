"""Advanced GraphQL subscriptions with real-time capabilities."""

import asyncio
import json
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Set
from uuid import uuid4

import strawberry
from strawberry.types import Info

from app.core.monitoring import monitor_performance


class SubscriptionEventType(str, Enum):
    """Subscription event types."""
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_ASSIGNED = "task_assigned"
    NOTIFICATION_SENT = "notification_sent"
    SYSTEM_ALERT = "system_alert"
    REAL_TIME_METRICS = "real_time_metrics"
    ORGANIZATION_UPDATED = "organization_updated"


class SubscriptionStatus(str, Enum):
    """Subscription connection status."""
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    ERROR = "error"
    DISCONNECTED = "disconnected"


@dataclass
class SubscriptionEvent:
    """Subscription event data."""
    id: str
    event_type: SubscriptionEventType
    payload: Dict[str, Any]
    timestamp: datetime
    source: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


@dataclass
class SubscriptionConnection:
    """Active subscription connection."""
    id: str
    user_id: Optional[str]
    event_types: Set[SubscriptionEventType]
    filters: Dict[str, Any]
    status: SubscriptionStatus
    created_at: datetime
    last_activity: datetime
    message_count: int = 0
    error_count: int = 0
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


@dataclass
class SubscriptionMetrics:
    """Subscription system metrics."""
    total_connections: int
    active_connections: int
    events_published_24h: int
    events_delivered_24h: int
    average_delivery_time_ms: float
    error_rate_percentage: float
    connection_duration_avg_minutes: float
    popular_event_types: Dict[str, int]


class SubscriptionHandler:
    """Individual subscription handler for specific event types."""
    
    def __init__(
        self,
        event_types: Set[SubscriptionEventType],
        handler_func: Callable,
        filters: Optional[Dict[str, Any]] = None
    ):
        """Initialize subscription handler."""
        self.id = str(uuid4())
        self.event_types = event_types
        self.handler_func = handler_func
        self.filters = filters or {}
        self.created_at = datetime.utcnow()
        self.execution_count = 0
        self.error_count = 0
        self.last_execution: Optional[datetime] = None
    
    async def can_handle(self, event: SubscriptionEvent) -> bool:
        """Check if handler can process this event."""
        if event.event_type not in self.event_types:
            return False
        
        # Apply filters
        for filter_key, filter_value in self.filters.items():
            if filter_key in event.payload:
                if event.payload[filter_key] != filter_value:
                    return False
        
        return True
    
    async def handle_event(self, event: SubscriptionEvent) -> Any:
        """Handle subscription event."""
        try:
            self.execution_count += 1
            self.last_execution = datetime.utcnow()
            
            result = await self.handler_func(event)
            return result
        
        except Exception as e:
            self.error_count += 1
            raise e


class SubscriptionManager:
    """Advanced subscription management system."""
    
    def __init__(self):
        """Initialize subscription manager."""
        self.connections: Dict[str, SubscriptionConnection] = {}
        self.handlers: Dict[str, SubscriptionHandler] = {}
        self.event_queue: deque = deque(maxlen=10000)
        self.published_events: deque = deque(maxlen=50000)
        self.delivery_stats: Dict[str, List[float]] = defaultdict(list)
        self.connection_queues: Dict[str, asyncio.Queue] = {}
        self.background_tasks: Set[asyncio.Task] = set()
        
        # Start background event processor
        self._start_event_processor()
    
    def _start_event_processor(self) -> None:
        """Start background event processing."""
        task = asyncio.create_task(self._process_events())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
    
    async def _process_events(self) -> None:
        """Background event processing loop."""
        while True:
            try:
                if not self.event_queue:
                    await asyncio.sleep(0.1)
                    continue
                
                event = self.event_queue.popleft()
                await self._deliver_event(event)
                
            except Exception as e:
                print(f"Event processing error: {e}")
                await asyncio.sleep(1)
    
    async def _deliver_event(self, event: SubscriptionEvent) -> None:
        """Deliver event to subscribed connections."""
        start_time = datetime.utcnow()
        delivered_count = 0
        
        # Find matching connections
        matching_connections = []
        for connection in self.connections.values():
            if (connection.status == SubscriptionStatus.ACTIVE and
                event.event_type in connection.event_types):
                
                # Apply connection filters
                if self._event_matches_filters(event, connection.filters):
                    matching_connections.append(connection)
        
        # Deliver to matching connections
        for connection in matching_connections:
            try:
                if connection.id in self.connection_queues:
                    queue = self.connection_queues[connection.id]
                    await queue.put(event)
                    
                    connection.message_count += 1
                    connection.last_activity = datetime.utcnow()
                    delivered_count += 1
            
            except Exception as e:
                connection.error_count += 1
                print(f"Delivery error for connection {connection.id}: {e}")
        
        # Record delivery metrics
        end_time = datetime.utcnow()
        delivery_time = (end_time - start_time).total_seconds() * 1000
        self.delivery_stats[event.event_type.value].append(delivery_time)
        
        # Limit delivery stats size
        if len(self.delivery_stats[event.event_type.value]) > 1000:
            self.delivery_stats[event.event_type.value] = \
                self.delivery_stats[event.event_type.value][-500:]
    
    def _event_matches_filters(
        self,
        event: SubscriptionEvent,
        filters: Dict[str, Any]
    ) -> bool:
        """Check if event matches connection filters."""
        for filter_key, filter_value in filters.items():
            if filter_key == "user_id":
                # Special handling for user-specific events
                if event.payload.get("user_id") != filter_value:
                    return False
            elif filter_key == "organization_id":
                # Organization-specific events
                if event.payload.get("organization_id") != filter_value:
                    return False
            elif filter_key in event.payload:
                if event.payload[filter_key] != filter_value:
                    return False
        
        return True
    
    @monitor_performance("graphql.subscription.create_connection")
    async def create_connection(
        self,
        user_id: Optional[str],
        event_types: Set[SubscriptionEventType],
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create new subscription connection."""
        connection = SubscriptionConnection(
            id=str(uuid4()),
            user_id=user_id,
            event_types=event_types,
            filters=filters or {},
            status=SubscriptionStatus.ACTIVE,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        
        self.connections[connection.id] = connection
        self.connection_queues[connection.id] = asyncio.Queue()
        
        return connection.id
    
    async def close_connection(self, connection_id: str) -> bool:
        """Close subscription connection."""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            connection.status = SubscriptionStatus.DISCONNECTED
            
            # Clean up queue
            if connection_id in self.connection_queues:
                del self.connection_queues[connection_id]
            
            del self.connections[connection_id]
            return True
        
        return False
    
    @monitor_performance("graphql.subscription.publish_event")
    async def publish_event(
        self,
        event_type: SubscriptionEventType,
        payload: Dict[str, Any],
        source: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish event to subscription system."""
        event = SubscriptionEvent(
            id=str(uuid4()),
            event_type=event_type,
            payload=payload,
            timestamp=datetime.utcnow(),
            source=source,
            metadata=metadata or {}
        )
        
        # Add to event queue for processing
        self.event_queue.append(event)
        
        # Store for metrics
        self.published_events.append(event)
        
        return event.id
    
    async def get_connection_events(
        self,
        connection_id: str,
        timeout: float = 30.0
    ) -> AsyncIterator[SubscriptionEvent]:
        """Get events for a specific connection."""
        if connection_id not in self.connection_queues:
            return
        
        queue = self.connection_queues[connection_id]
        connection = self.connections.get(connection_id)
        
        if not connection or connection.status != SubscriptionStatus.ACTIVE:
            return
        
        try:
            while True:
                try:
                    # Wait for event with timeout
                    event = await asyncio.wait_for(queue.get(), timeout=timeout)
                    yield event
                    
                    # Update connection activity
                    connection.last_activity = datetime.utcnow()
                
                except asyncio.TimeoutError:
                    # Send keep-alive or break
                    break
        
        except Exception as e:
            connection.status = SubscriptionStatus.ERROR
            connection.error_count += 1
            raise e
    
    def register_handler(
        self,
        event_types: Set[SubscriptionEventType],
        handler_func: Callable,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Register subscription event handler."""
        handler = SubscriptionHandler(event_types, handler_func, filters)
        self.handlers[handler.id] = handler
        return handler.id
    
    def unregister_handler(self, handler_id: str) -> bool:
        """Unregister subscription handler."""
        if handler_id in self.handlers:
            del self.handlers[handler_id]
            return True
        return False
    
    async def cleanup_expired_connections(self) -> int:
        """Clean up expired and inactive connections."""
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        expired_connections = []
        
        for connection_id, connection in self.connections.items():
            if (connection.last_activity < cutoff_time or
                connection.status in [SubscriptionStatus.EXPIRED, SubscriptionStatus.ERROR]):
                expired_connections.append(connection_id)
        
        # Clean up expired connections
        for connection_id in expired_connections:
            await self.close_connection(connection_id)
        
        return len(expired_connections)
    
    def get_subscription_metrics(self) -> SubscriptionMetrics:
        """Get subscription system metrics."""
        active_connections = len([
            c for c in self.connections.values()
            if c.status == SubscriptionStatus.ACTIVE
        ])
        
        # Events in last 24 hours
        day_ago = datetime.utcnow() - timedelta(hours=24)
        recent_events = [
            e for e in self.published_events
            if e.timestamp > day_ago
        ]
        
        # Calculate average delivery time
        all_delivery_times = []
        for times in self.delivery_stats.values():
            all_delivery_times.extend(times)
        
        avg_delivery_time = (
            sum(all_delivery_times) / len(all_delivery_times)
            if all_delivery_times else 0.0
        )
        
        # Popular event types
        event_type_counts = defaultdict(int)
        for event in recent_events:
            event_type_counts[event.event_type.value] += 1
        
        # Error rate
        total_messages = sum(c.message_count for c in self.connections.values())
        total_errors = sum(c.error_count for c in self.connections.values())
        error_rate = (total_errors / total_messages * 100) if total_messages > 0 else 0.0
        
        # Average connection duration
        connection_durations = []
        now = datetime.utcnow()
        for connection in self.connections.values():
            duration = (now - connection.created_at).total_seconds() / 60
            connection_durations.append(duration)
        
        avg_duration = (
            sum(connection_durations) / len(connection_durations)
            if connection_durations else 0.0
        )
        
        return SubscriptionMetrics(
            total_connections=len(self.connections),
            active_connections=active_connections,
            events_published_24h=len(recent_events),
            events_delivered_24h=total_messages,
            average_delivery_time_ms=avg_delivery_time,
            error_rate_percentage=error_rate,
            connection_duration_avg_minutes=avg_duration,
            popular_event_types=dict(event_type_counts)
        )
    
    async def broadcast_system_alert(
        self,
        message: str,
        severity: str = "info",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Broadcast system-wide alert."""
        return await self.publish_event(
            SubscriptionEventType.SYSTEM_ALERT,
            {
                "message": message,
                "severity": severity,
                "alert_id": str(uuid4()),
                "timestamp": datetime.utcnow().isoformat()
            },
            source="system",
            metadata=metadata
        )
    
    async def notify_user_activity(
        self,
        user_id: str,
        activity_type: str,
        details: Dict[str, Any]
    ) -> str:
        """Notify about user activity."""
        return await self.publish_event(
            SubscriptionEventType.USER_UPDATED,
            {
                "user_id": user_id,
                "activity_type": activity_type,
                "details": details,
                "timestamp": datetime.utcnow().isoformat()
            },
            source="user_activity"
        )


# Global subscription manager instance
subscription_manager = SubscriptionManager()


# Strawberry subscription types
@strawberry.type
class SubscriptionEventPayload:
    """GraphQL subscription event payload."""
    id: str
    event_type: str
    data: strawberry.scalars.JSON
    timestamp: str
    source: str


@strawberry.type
class SystemAlert:
    """System alert subscription payload."""
    message: str
    severity: str
    alert_id: str
    timestamp: str


# GraphQL Subscription resolvers
@strawberry.type
class AdvancedSubscriptions:
    """Advanced GraphQL subscription resolvers."""
    
    @strawberry.subscription
    async def user_activity(
        self,
        info: Info,
        user_id: Optional[str] = None
    ) -> AsyncIterator[SubscriptionEventPayload]:
        """Subscribe to user activity events."""
        # Get user context
        current_user = getattr(info.context, 'current_user', None)
        if not current_user:
            raise PermissionError("Authentication required")
        
        # Set up event types and filters
        event_types = {
            SubscriptionEventType.USER_CREATED,
            SubscriptionEventType.USER_UPDATED,
            SubscriptionEventType.USER_DELETED
        }
        
        filters = {}
        if user_id:
            # Check permission to monitor specific user
            if (user_id != str(current_user.id) and
                not current_user.is_superuser):
                raise PermissionError("Cannot monitor other users")
            filters["user_id"] = user_id
        elif not current_user.is_superuser:
            # Non-superusers can only monitor themselves
            filters["user_id"] = str(current_user.id)
        
        # Create subscription connection
        connection_id = await subscription_manager.create_connection(
            str(current_user.id),
            event_types,
            filters
        )
        
        try:
            async for event in subscription_manager.get_connection_events(connection_id):
                yield SubscriptionEventPayload(
                    id=event.id,
                    event_type=event.event_type.value,
                    data=event.payload,
                    timestamp=event.timestamp.isoformat(),
                    source=event.source
                )
        finally:
            await subscription_manager.close_connection(connection_id)
    
    @strawberry.subscription
    async def task_updates(
        self,
        info: Info,
        task_id: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> AsyncIterator[SubscriptionEventPayload]:
        """Subscribe to task update events."""
        current_user = getattr(info.context, 'current_user', None)
        if not current_user:
            raise PermissionError("Authentication required")
        
        event_types = {
            SubscriptionEventType.TASK_CREATED,
            SubscriptionEventType.TASK_UPDATED,
            SubscriptionEventType.TASK_ASSIGNED
        }
        
        filters = {}
        if task_id:
            filters["task_id"] = task_id
        
        if organization_id:
            # Check organization access
            if (str(current_user.organization_id) != organization_id and
                not current_user.is_superuser):
                raise PermissionError("Cannot access other organization's tasks")
            filters["organization_id"] = organization_id
        elif not current_user.is_superuser:
            filters["organization_id"] = str(current_user.organization_id)
        
        connection_id = await subscription_manager.create_connection(
            str(current_user.id),
            event_types,
            filters
        )
        
        try:
            async for event in subscription_manager.get_connection_events(connection_id):
                yield SubscriptionEventPayload(
                    id=event.id,
                    event_type=event.event_type.value,
                    data=event.payload,
                    timestamp=event.timestamp.isoformat(),
                    source=event.source
                )
        finally:
            await subscription_manager.close_connection(connection_id)
    
    @strawberry.subscription
    async def system_alerts(
        self,
        info: Info,
        severity_filter: Optional[str] = None
    ) -> AsyncIterator[SystemAlert]:
        """Subscribe to system alerts."""
        current_user = getattr(info.context, 'current_user', None)
        if not current_user:
            raise PermissionError("Authentication required")
        
        event_types = {SubscriptionEventType.SYSTEM_ALERT}
        filters = {}
        if severity_filter:
            filters["severity"] = severity_filter
        
        connection_id = await subscription_manager.create_connection(
            str(current_user.id),
            event_types,
            filters
        )
        
        try:
            async for event in subscription_manager.get_connection_events(connection_id):
                payload = event.payload
                yield SystemAlert(
                    message=payload["message"],
                    severity=payload["severity"],
                    alert_id=payload["alert_id"],
                    timestamp=payload["timestamp"]
                )
        finally:
            await subscription_manager.close_connection(connection_id)
    
    @strawberry.subscription
    async def real_time_metrics(
        self,
        info: Info,
        metric_types: Optional[List[str]] = None
    ) -> AsyncIterator[SubscriptionEventPayload]:
        """Subscribe to real-time system metrics."""
        current_user = getattr(info.context, 'current_user', None)
        if not current_user or not current_user.is_superuser:
            raise PermissionError("Admin permissions required")
        
        event_types = {SubscriptionEventType.REAL_TIME_METRICS}
        filters = {}
        if metric_types:
            filters["metric_types"] = metric_types
        
        connection_id = await subscription_manager.create_connection(
            str(current_user.id),
            event_types,
            filters
        )
        
        try:
            async for event in subscription_manager.get_connection_events(connection_id):
                yield SubscriptionEventPayload(
                    id=event.id,
                    event_type=event.event_type.value,
                    data=event.payload,
                    timestamp=event.timestamp.isoformat(),
                    source=event.source
                )
        finally:
            await subscription_manager.close_connection(connection_id)


# Health check for subscription system
async def check_graphql_subscriptions_health() -> Dict[str, Any]:
    """Check GraphQL subscriptions system health."""
    # Clean up expired connections
    cleaned_up = await subscription_manager.cleanup_expired_connections()
    
    # Get metrics
    metrics = subscription_manager.get_subscription_metrics()
    
    # Determine health status
    health_status = "healthy"
    if metrics.error_rate_percentage > 10:
        health_status = "degraded"
    if metrics.active_connections == 0 and metrics.total_connections > 0:
        health_status = "warning"
    
    return {
        "status": health_status,
        "subscription_metrics": {
            "total_connections": metrics.total_connections,
            "active_connections": metrics.active_connections,
            "events_published_24h": metrics.events_published_24h,
            "events_delivered_24h": metrics.events_delivered_24h,
            "average_delivery_time_ms": metrics.average_delivery_time_ms,
            "error_rate_percentage": metrics.error_rate_percentage,
            "connection_duration_avg_minutes": metrics.connection_duration_avg_minutes,
            "popular_event_types": metrics.popular_event_types
        },
        "cleanup_stats": {
            "expired_connections_cleaned": cleaned_up
        },
        "background_tasks": len(subscription_manager.background_tasks)
    }