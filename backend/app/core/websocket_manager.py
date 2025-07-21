"""Real-time WebSocket management system with comprehensive features."""

import asyncio
import json
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.core.monitoring import monitor_performance


class ConnectionState(str, Enum):
    """WebSocket connection states."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    SUBSCRIBED = "subscribed"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class MessageType(str, Enum):
    """WebSocket message types."""
    PING = "ping"
    PONG = "pong"
    AUTH = "auth"
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILED = "auth_failed"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    SUBSCRIPTION_SUCCESS = "subscription_success"
    SUBSCRIPTION_FAILED = "subscription_failed"
    DATA = "data"
    NOTIFICATION = "notification"
    BROADCAST = "broadcast"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    RATE_LIMIT = "rate_limit"


class EventType(str, Enum):
    """Real-time event types."""
    USER_ACTIVITY = "user_activity"
    SYSTEM_NOTIFICATION = "system_notification"
    DATA_UPDATE = "data_update"
    SECURITY_ALERT = "security_alert"
    PERFORMANCE_METRIC = "performance_metric"
    AUDIT_EVENT = "audit_event"
    WORKFLOW_STATUS = "workflow_status"
    TASK_UPDATE = "task_update"
    COLLABORATION = "collaboration"
    CUSTOM = "custom"


class SubscriptionScope(str, Enum):
    """Subscription scope levels."""
    GLOBAL = "global"
    ORGANIZATION = "organization"
    PROJECT = "project"
    USER = "user"
    ROOM = "room"


@dataclass
class WebSocketMessage:
    """WebSocket message structure."""
    type: MessageType
    event_type: Optional[EventType] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message_id: str = field(default_factory=lambda: str(uuid4()))
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "type": self.type.value,
            "event_type": self.event_type.value if self.event_type else None,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class Subscription:
    """WebSocket subscription configuration."""
    id: str
    connection_id: str
    event_type: EventType
    scope: SubscriptionScope
    filters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    message_count: int = 0
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())

    def matches_event(self, event: Dict[str, Any]) -> bool:
        """Check if subscription matches event."""
        # Check event type
        if event.get("event_type") != self.event_type.value:
            return False
        
        # Apply filters
        for filter_key, filter_value in self.filters.items():
            if filter_key not in event.get("payload", {}):
                return False
            
            event_value = event["payload"][filter_key]
            
            if isinstance(filter_value, list):
                if event_value not in filter_value:
                    return False
            elif event_value != filter_value:
                return False
        
        return True


@dataclass
class ConnectionInfo:
    """WebSocket connection information."""
    id: str
    websocket: WebSocket
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    session_id: Optional[str] = None
    state: ConnectionState = ConnectionState.CONNECTING
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_ping: datetime = field(default_factory=datetime.utcnow)
    last_pong: datetime = field(default_factory=datetime.utcnow)
    message_count: int = 0
    subscriptions: Set[str] = field(default_factory=set)
    rate_limit_tokens: int = 100
    rate_limit_reset: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())

    @property
    def is_authenticated(self) -> bool:
        """Check if connection is authenticated."""
        return self.state in [ConnectionState.AUTHENTICATED, ConnectionState.SUBSCRIBED]

    @property
    def uptime_seconds(self) -> float:
        """Get connection uptime in seconds."""
        return (datetime.utcnow() - self.connected_at).total_seconds()

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_ping = datetime.utcnow()
        self.message_count += 1


@dataclass
class WebSocketStats:
    """WebSocket statistics."""
    total_connections: int = 0
    active_connections: int = 0
    authenticated_connections: int = 0
    total_messages_sent: int = 0
    total_messages_received: int = 0
    total_subscriptions: int = 0
    avg_connection_duration: float = 0.0
    messages_per_second: float = 0.0
    connection_errors: int = 0
    rate_limit_hits: int = 0
    last_reset: datetime = field(default_factory=datetime.utcnow)


class WebSocketManager:
    """Advanced WebSocket connection and message management."""
    
    def __init__(
        self,
        heartbeat_interval: int = 30,
        connection_timeout: int = 300,
        rate_limit_per_minute: int = 100,
        max_subscriptions_per_connection: int = 50
    ):
        """Initialize WebSocket manager."""
        self.heartbeat_interval = heartbeat_interval
        self.connection_timeout = connection_timeout
        self.rate_limit_per_minute = rate_limit_per_minute
        self.max_subscriptions_per_connection = max_subscriptions_per_connection
        
        # Connection management
        self.connections: Dict[str, ConnectionInfo] = {}
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)
        self.organization_connections: Dict[str, Set[str]] = defaultdict(set)
        
        # Subscription management
        self.subscriptions: Dict[str, Subscription] = {}
        self.event_subscriptions: Dict[EventType, Set[str]] = defaultdict(set)
        self.scope_subscriptions: Dict[SubscriptionScope, Set[str]] = defaultdict(set)
        
        # Message queuing and routing
        self.message_queue: deque = deque(maxlen=10000)
        self.broadcast_queue: deque = deque(maxlen=1000)
        self.failed_messages: deque = deque(maxlen=1000)
        
        # Statistics and monitoring
        self.stats = WebSocketStats()
        self.connection_history: deque = deque(maxlen=1000)
        self.message_history: deque = deque(maxlen=10000)
        
        # Event handlers
        self.event_handlers: Dict[EventType, List[Callable]] = defaultdict(list)
        self.message_filters: List[Callable] = []
        
        # Background tasks
        self._background_tasks: Set[asyncio.Task] = set()
        self._start_background_tasks()

    def _start_background_tasks(self) -> None:
        """Start background maintenance tasks."""
        tasks = [
            self._heartbeat_task(),
            self._cleanup_task(),
            self._stats_update_task(),
            self._message_processor_task()
        ]
        
        for task_coro in tasks:
            task = asyncio.create_task(task_coro)
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

    async def connect(self, websocket: WebSocket, connection_id: Optional[str] = None) -> str:
        """Accept new WebSocket connection."""
        if not connection_id:
            connection_id = str(uuid4())
        
        await websocket.accept()
        
        connection = ConnectionInfo(
            id=connection_id,
            websocket=websocket,
            state=ConnectionState.CONNECTED
        )
        
        self.connections[connection_id] = connection
        self.stats.total_connections += 1
        self.stats.active_connections += 1
        
        # Record connection event
        self.connection_history.append({
            "event": "connected",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow(),
            "remote_addr": getattr(websocket.client, 'host', 'unknown') if websocket.client else 'unknown'
        })
        
        # Send welcome message
        welcome_msg = WebSocketMessage(
            type=MessageType.DATA,
            event_type=EventType.SYSTEM_NOTIFICATION,
            payload={
                "message": "WebSocket connection established",
                "connection_id": connection_id,
                "server_time": datetime.utcnow().isoformat()
            }
        )
        
        await self.send_to_connection(connection_id, welcome_msg)
        
        return connection_id

    async def disconnect(self, connection_id: str, reason: str = "client_disconnect") -> None:
        """Handle WebSocket disconnection."""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        connection.state = ConnectionState.DISCONNECTING
        
        # Remove from user/organization mappings
        if connection.user_id:
            self.user_connections[connection.user_id].discard(connection_id)
            if not self.user_connections[connection.user_id]:
                del self.user_connections[connection.user_id]
        
        if connection.organization_id:
            self.organization_connections[connection.organization_id].discard(connection_id)
            if not self.organization_connections[connection.organization_id]:
                del self.organization_connections[connection.organization_id]
        
        # Remove subscriptions
        for subscription_id in connection.subscriptions.copy():
            await self.unsubscribe(connection_id, subscription_id)
        
        # Record disconnection
        self.connection_history.append({
            "event": "disconnected",
            "connection_id": connection_id,
            "reason": reason,
            "duration_seconds": connection.uptime_seconds,
            "message_count": connection.message_count,
            "timestamp": datetime.utcnow()
        })
        
        # Remove connection
        del self.connections[connection_id]
        self.stats.active_connections -= 1
        connection.state = ConnectionState.DISCONNECTED

    @monitor_performance("websocket.authenticate")
    async def authenticate(self, connection_id: str, user_id: str, organization_id: Optional[str] = None, session_data: Optional[Dict[str, Any]] = None) -> bool:
        """Authenticate WebSocket connection."""
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        connection.user_id = user_id
        connection.organization_id = organization_id
        connection.session_id = session_data.get("session_id") if session_data else None
        connection.state = ConnectionState.AUTHENTICATED
        connection.metadata.update(session_data or {})
        
        # Add to user/organization mappings
        self.user_connections[user_id].add(connection_id)
        if organization_id:
            self.organization_connections[organization_id].add(connection_id)
        
        self.stats.authenticated_connections += 1
        
        # Send authentication success
        auth_msg = WebSocketMessage(
            type=MessageType.AUTH_SUCCESS,
            payload={
                "user_id": user_id,
                "organization_id": organization_id,
                "session_id": connection.session_id,
                "capabilities": {
                    "max_subscriptions": self.max_subscriptions_per_connection,
                    "rate_limit_per_minute": self.rate_limit_per_minute,
                    "supported_events": [event.value for event in EventType],
                    "supported_scopes": [scope.value for scope in SubscriptionScope]
                }
            }
        )
        
        await self.send_to_connection(connection_id, auth_msg)
        return True

    @monitor_performance("websocket.subscribe")
    async def subscribe(
        self,
        connection_id: str,
        event_type: EventType,
        scope: SubscriptionScope = SubscriptionScope.USER,
        filters: Optional[Dict[str, Any]] = None,
        subscription_id: Optional[str] = None
    ) -> Optional[str]:
        """Subscribe connection to events."""
        if connection_id not in self.connections:
            return None
        
        connection = self.connections[connection_id]
        
        if not connection.is_authenticated:
            await self._send_error(connection_id, "Authentication required for subscriptions")
            return None
        
        if len(connection.subscriptions) >= self.max_subscriptions_per_connection:
            await self._send_error(connection_id, "Maximum subscriptions limit reached")
            return None
        
        if not subscription_id:
            subscription_id = str(uuid4())
        
        subscription = Subscription(
            id=subscription_id,
            connection_id=connection_id,
            event_type=event_type,
            scope=scope,
            filters=filters or {}
        )
        
        # Validate scope permissions
        if not await self._validate_subscription_scope(connection, subscription):
            await self._send_error(connection_id, "Insufficient permissions for subscription scope")
            return None
        
        # Store subscription
        self.subscriptions[subscription_id] = subscription
        connection.subscriptions.add(subscription_id)
        self.event_subscriptions[event_type].add(subscription_id)
        self.scope_subscriptions[scope].add(subscription_id)
        
        connection.state = ConnectionState.SUBSCRIBED
        self.stats.total_subscriptions += 1
        
        # Send subscription success
        success_msg = WebSocketMessage(
            type=MessageType.SUBSCRIPTION_SUCCESS,
            payload={
                "subscription_id": subscription_id,
                "event_type": event_type.value,
                "scope": scope.value,
                "filters": filters or {}
            }
        )
        
        await self.send_to_connection(connection_id, success_msg)
        return subscription_id

    async def unsubscribe(self, connection_id: str, subscription_id: str) -> bool:
        """Unsubscribe from events."""
        if subscription_id not in self.subscriptions:
            return False
        
        subscription = self.subscriptions[subscription_id]
        
        if subscription.connection_id != connection_id:
            return False
        
        # Remove subscription
        connection = self.connections.get(connection_id)
        if connection:
            connection.subscriptions.discard(subscription_id)
        
        self.event_subscriptions[subscription.event_type].discard(subscription_id)
        self.scope_subscriptions[subscription.scope].discard(subscription_id)
        
        del self.subscriptions[subscription_id]
        
        # Send unsubscribe confirmation
        if connection:
            confirm_msg = WebSocketMessage(
                type=MessageType.DATA,
                event_type=EventType.SYSTEM_NOTIFICATION,
                payload={
                    "message": "Unsubscribed successfully",
                    "subscription_id": subscription_id
                }
            )
            await self.send_to_connection(connection_id, confirm_msg)
        
        return True

    @monitor_performance("websocket.send_message")
    async def send_to_connection(self, connection_id: str, message: WebSocketMessage) -> bool:
        """Send message to specific connection."""
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        
        # Apply rate limiting
        if not self._check_rate_limit(connection):
            await self._send_rate_limit_message(connection_id)
            return False
        
        try:
            await connection.websocket.send_text(message.to_json())
            connection.update_activity()
            self.stats.total_messages_sent += 1
            
            # Record message
            self.message_history.append({
                "type": "sent",
                "connection_id": connection_id,
                "message_type": message.type.value,
                "event_type": message.event_type.value if message.event_type else None,
                "timestamp": datetime.utcnow(),
                "size_bytes": len(message.to_json())
            })
            
            return True
            
        except Exception as e:
            self.stats.connection_errors += 1
            self.failed_messages.append({
                "connection_id": connection_id,
                "message": message.to_dict(),
                "error": str(e),
                "timestamp": datetime.utcnow()
            })
            await self.disconnect(connection_id, f"send_error: {str(e)}")
            return False

    async def send_to_user(self, user_id: str, message: WebSocketMessage) -> int:
        """Send message to all connections of a user."""
        sent_count = 0
        connection_ids = self.user_connections.get(user_id, set()).copy()
        
        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
        
        return sent_count

    async def send_to_organization(self, organization_id: str, message: WebSocketMessage) -> int:
        """Send message to all connections in an organization."""
        sent_count = 0
        connection_ids = self.organization_connections.get(organization_id, set()).copy()
        
        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
        
        return sent_count

    @monitor_performance("websocket.broadcast_event")
    async def broadcast_event(
        self,
        event_type: EventType,
        payload: Dict[str, Any],
        scope: SubscriptionScope = SubscriptionScope.GLOBAL,
        filters: Optional[Dict[str, Any]] = None,
        exclude_connections: Optional[Set[str]] = None
    ) -> int:
        """Broadcast event to matching subscriptions."""
        event = {
            "event_type": event_type.value,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
            "scope": scope.value,
            "filters": filters or {}
        }
        
        sent_count = 0
        exclude_set = exclude_connections or set()
        
        # Find matching subscriptions
        matching_subscriptions = []
        for subscription_id in self.event_subscriptions.get(event_type, set()):
            if subscription_id in self.subscriptions:
                subscription = self.subscriptions[subscription_id]
                if subscription.scope == scope and subscription.matches_event(event):
                    if subscription.connection_id not in exclude_set:
                        matching_subscriptions.append(subscription)
        
        # Send to matching connections
        message = WebSocketMessage(
            type=MessageType.DATA,
            event_type=event_type,
            payload=payload
        )
        
        for subscription in matching_subscriptions:
            if await self.send_to_connection(subscription.connection_id, message):
                subscription.message_count += 1
                subscription.last_activity = datetime.utcnow()
                sent_count += 1
        
        # Queue for persistent delivery
        self.broadcast_queue.append({
            "event": event,
            "sent_count": sent_count,
            "timestamp": datetime.utcnow()
        })
        
        return sent_count

    async def handle_message(self, connection_id: str, message_data: str) -> None:
        """Handle incoming WebSocket message."""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        try:
            data = json.loads(message_data)
            message_type = MessageType(data.get("type", ""))
            
            # Apply message filters
            for filter_func in self.message_filters:
                if not filter_func(connection, data):
                    return
            
            # Handle different message types
            if message_type == MessageType.PING:
                await self._handle_ping(connection_id, data)
            elif message_type == MessageType.AUTH:
                await self._handle_auth_request(connection_id, data)
            elif message_type == MessageType.SUBSCRIBE:
                await self._handle_subscribe_request(connection_id, data)
            elif message_type == MessageType.UNSUBSCRIBE:
                await self._handle_unsubscribe_request(connection_id, data)
            elif message_type == MessageType.DATA:
                await self._handle_data_message(connection_id, data)
            else:
                await self._send_error(connection_id, f"Unknown message type: {message_type}")
            
            connection.update_activity()
            self.stats.total_messages_received += 1
            
        except json.JSONDecodeError:
            await self._send_error(connection_id, "Invalid JSON format")
        except ValueError as e:
            await self._send_error(connection_id, f"Invalid message: {str(e)}")
        except Exception as e:
            await self._send_error(connection_id, f"Message processing error: {str(e)}")

    async def _handle_ping(self, connection_id: str, data: Dict[str, Any]) -> None:
        """Handle ping message."""
        pong_msg = WebSocketMessage(
            type=MessageType.PONG,
            payload={"timestamp": datetime.utcnow().isoformat()},
            correlation_id=data.get("message_id")
        )
        await self.send_to_connection(connection_id, pong_msg)

    async def _handle_auth_request(self, connection_id: str, data: Dict[str, Any]) -> None:
        """Handle authentication request."""
        # This would integrate with actual authentication system
        # For now, simulate authentication
        user_id = data.get("payload", {}).get("user_id")
        organization_id = data.get("payload", {}).get("organization_id")
        
        if user_id:
            success = await self.authenticate(connection_id, user_id, organization_id)
            if not success:
                auth_failed_msg = WebSocketMessage(
                    type=MessageType.AUTH_FAILED,
                    payload={"error": "Authentication failed"}
                )
                await self.send_to_connection(connection_id, auth_failed_msg)
        else:
            await self._send_error(connection_id, "Missing user_id in authentication request")

    async def _handle_subscribe_request(self, connection_id: str, data: Dict[str, Any]) -> None:
        """Handle subscription request."""
        payload = data.get("payload", {})
        
        try:
            event_type = EventType(payload.get("event_type"))
            scope = SubscriptionScope(payload.get("scope", SubscriptionScope.USER.value))
            filters = payload.get("filters")
            
            subscription_id = await self.subscribe(connection_id, event_type, scope, filters)
            
            if not subscription_id:
                sub_failed_msg = WebSocketMessage(
                    type=MessageType.SUBSCRIPTION_FAILED,
                    payload={"error": "Subscription failed"}
                )
                await self.send_to_connection(connection_id, sub_failed_msg)
                
        except ValueError as e:
            await self._send_error(connection_id, f"Invalid subscription parameters: {str(e)}")

    async def _handle_unsubscribe_request(self, connection_id: str, data: Dict[str, Any]) -> None:
        """Handle unsubscribe request."""
        subscription_id = data.get("payload", {}).get("subscription_id")
        
        if subscription_id:
            success = await self.unsubscribe(connection_id, subscription_id)
            if not success:
                await self._send_error(connection_id, "Unsubscribe failed")
        else:
            await self._send_error(connection_id, "Missing subscription_id")

    async def _handle_data_message(self, connection_id: str, data: Dict[str, Any]) -> None:
        """Handle data message from client."""
        # Process custom data messages
        # This can be extended for application-specific message handling
        payload = data.get("payload", {})
        
        # Example: Echo message back
        echo_msg = WebSocketMessage(
            type=MessageType.DATA,
            event_type=EventType.CUSTOM,
            payload={"echo": payload, "processed_at": datetime.utcnow().isoformat()}
        )
        await self.send_to_connection(connection_id, echo_msg)

    async def _send_error(self, connection_id: str, error_message: str) -> None:
        """Send error message to connection."""
        error_msg = WebSocketMessage(
            type=MessageType.ERROR,
            payload={"error": error_message, "timestamp": datetime.utcnow().isoformat()}
        )
        await self.send_to_connection(connection_id, error_msg)

    async def _send_rate_limit_message(self, connection_id: str) -> None:
        """Send rate limit message."""
        rate_limit_msg = WebSocketMessage(
            type=MessageType.RATE_LIMIT,
            payload={
                "error": "Rate limit exceeded",
                "retry_after_seconds": 60,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        await self.send_to_connection(connection_id, rate_limit_msg)

    def _check_rate_limit(self, connection: ConnectionInfo) -> bool:
        """Check if connection is within rate limits."""
        now = datetime.utcnow()
        
        # Reset rate limit if minute has passed
        if now >= connection.rate_limit_reset:
            connection.rate_limit_tokens = self.rate_limit_per_minute
            connection.rate_limit_reset = now + timedelta(minutes=1)
        
        if connection.rate_limit_tokens > 0:
            connection.rate_limit_tokens -= 1
            return True
        else:
            self.stats.rate_limit_hits += 1
            return False

    async def _validate_subscription_scope(self, connection: ConnectionInfo, subscription: Subscription) -> bool:
        """Validate subscription scope permissions."""
        # Basic validation - would be more sophisticated in production
        if subscription.scope == SubscriptionScope.GLOBAL:
            # Only superusers can subscribe to global events
            return connection.metadata.get("is_superuser", False)
        
        elif subscription.scope == SubscriptionScope.ORGANIZATION:
            # Must be in the same organization
            return connection.organization_id is not None
        
        elif subscription.scope == SubscriptionScope.USER:
            # Always allowed for authenticated users
            return connection.is_authenticated
        
        return True

    async def _heartbeat_task(self) -> None:
        """Background task for connection heartbeat."""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                now = datetime.utcnow()
                stale_connections = []
                
                for connection_id, connection in self.connections.items():
                    # Check for stale connections
                    time_since_ping = (now - connection.last_ping).total_seconds()
                    
                    if time_since_ping > self.connection_timeout:
                        stale_connections.append(connection_id)
                    elif time_since_ping > self.heartbeat_interval:
                        # Send heartbeat
                        heartbeat_msg = WebSocketMessage(
                            type=MessageType.HEARTBEAT,
                            payload={"timestamp": now.isoformat()}
                        )
                        await self.send_to_connection(connection_id, heartbeat_msg)
                
                # Disconnect stale connections
                for connection_id in stale_connections:
                    await self.disconnect(connection_id, "heartbeat_timeout")
                    
            except Exception as e:
                print(f"Heartbeat task error: {e}")

    async def _cleanup_task(self) -> None:
        """Background task for cleanup operations."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Clean up old connection history
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                self.connection_history = deque(
                    [entry for entry in self.connection_history if entry["timestamp"] > cutoff_time],
                    maxlen=1000
                )
                
                # Clean up old message history
                self.message_history = deque(
                    [entry for entry in self.message_history if entry["timestamp"] > cutoff_time],
                    maxlen=10000
                )
                
                # Clean up failed messages
                self.failed_messages = deque(
                    [entry for entry in self.failed_messages if entry["timestamp"] > cutoff_time],
                    maxlen=1000
                )
                
            except Exception as e:
                print(f"Cleanup task error: {e}")

    async def _stats_update_task(self) -> None:
        """Background task for statistics updates."""
        while True:
            try:
                await asyncio.sleep(60)  # Update every minute
                
                # Update connection stats
                self.stats.active_connections = len(self.connections)
                self.stats.authenticated_connections = len([
                    c for c in self.connections.values() if c.is_authenticated
                ])
                
                # Calculate messages per second
                recent_messages = [
                    msg for msg in self.message_history
                    if (datetime.utcnow() - msg["timestamp"]).total_seconds() < 60
                ]
                self.stats.messages_per_second = len(recent_messages) / 60
                
                # Calculate average connection duration
                if self.connection_history:
                    durations = [
                        entry["duration_seconds"] for entry in self.connection_history
                        if "duration_seconds" in entry
                    ]
                    if durations:
                        self.stats.avg_connection_duration = sum(durations) / len(durations)
                
            except Exception as e:
                print(f"Stats update task error: {e}")

    async def _message_processor_task(self) -> None:
        """Background task for processing queued messages."""
        while True:
            try:
                await asyncio.sleep(1)  # Process every second
                
                # Process broadcast queue
                if self.broadcast_queue:
                    # Could implement persistent delivery, retry logic, etc.
                    pass
                
                # Process failed messages
                if self.failed_messages:
                    # Could implement retry logic for failed messages
                    pass
                    
            except Exception as e:
                print(f"Message processor task error: {e}")

    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get connection information."""
        if connection_id not in self.connections:
            return None
        
        connection = self.connections[connection_id]
        
        return {
            "id": connection.id,
            "user_id": connection.user_id,
            "organization_id": connection.organization_id,
            "state": connection.state.value,
            "connected_at": connection.connected_at.isoformat(),
            "uptime_seconds": connection.uptime_seconds,
            "message_count": connection.message_count,
            "subscription_count": len(connection.subscriptions),
            "rate_limit_tokens": connection.rate_limit_tokens,
            "metadata": connection.metadata
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics."""
        return {
            "connections": {
                "total": self.stats.total_connections,
                "active": self.stats.active_connections,
                "authenticated": self.stats.authenticated_connections
            },
            "messages": {
                "total_sent": self.stats.total_messages_sent,
                "total_received": self.stats.total_messages_received,
                "per_second": round(self.stats.messages_per_second, 2),
                "failed_count": len(self.failed_messages)
            },
            "subscriptions": {
                "total": self.stats.total_subscriptions,
                "by_event_type": {
                    event_type.value: len(subscriptions)
                    for event_type, subscriptions in self.event_subscriptions.items()
                },
                "by_scope": {
                    scope.value: len(subscriptions)
                    for scope, subscriptions in self.scope_subscriptions.items()
                }
            },
            "performance": {
                "avg_connection_duration": round(self.stats.avg_connection_duration, 2),
                "connection_errors": self.stats.connection_errors,
                "rate_limit_hits": self.stats.rate_limit_hits
            },
            "configuration": {
                "heartbeat_interval": self.heartbeat_interval,
                "connection_timeout": self.connection_timeout,
                "rate_limit_per_minute": self.rate_limit_per_minute,
                "max_subscriptions_per_connection": self.max_subscriptions_per_connection
            }
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform WebSocket manager health check."""
        stats = self.get_statistics()
        
        # Determine health status
        active_connections = stats["connections"]["active"]
        error_rate = stats["performance"]["connection_errors"] / max(stats["connections"]["total"], 1)
        
        if error_rate > 0.1:
            status = "critical"
        elif error_rate > 0.05:
            status = "degraded"
        elif active_connections > 1000:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "statistics": stats,
            "last_updated": datetime.utcnow().isoformat()
        }

    def add_event_handler(self, event_type: EventType, handler: Callable) -> None:
        """Add custom event handler."""
        self.event_handlers[event_type].append(handler)

    def add_message_filter(self, filter_func: Callable) -> None:
        """Add message filter function."""
        self.message_filters.append(filter_func)

    async def shutdown(self) -> None:
        """Shutdown WebSocket manager gracefully."""
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Disconnect all connections
        connection_ids = list(self.connections.keys())
        for connection_id in connection_ids:
            await self.disconnect(connection_id, "server_shutdown")
        
        # Wait for tasks to complete
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)


# Global WebSocket manager instance
websocket_manager = WebSocketManager(
    heartbeat_interval=30,
    connection_timeout=300,
    rate_limit_per_minute=100,
    max_subscriptions_per_connection=50
)


# Health check function
async def check_websocket_health() -> Dict[str, Any]:
    """Check WebSocket system health."""
    return await websocket_manager.health_check()