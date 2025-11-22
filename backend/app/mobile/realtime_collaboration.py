"""Realtime Data Synchronization & Collaboration System - CC02 v73.0 Day 18."""

from __future__ import annotations

import json
import uuid
from collections import defaultdict, deque
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import websockets
from pydantic import BaseModel, Field

from ..sdk.mobile_sdk_core import MobileERPSDK
from .erp_app_architecture import ApplicationContext, ERPEntityType


class CollaborationEventType(str, Enum):
    """Types of collaboration events."""

    # Document events
    DOCUMENT_OPEN = "document_open"
    DOCUMENT_CLOSE = "document_close"
    DOCUMENT_EDIT = "document_edit"
    DOCUMENT_SAVE = "document_save"
    DOCUMENT_LOCK = "document_lock"
    DOCUMENT_UNLOCK = "document_unlock"

    # User events
    USER_JOIN = "user_join"
    USER_LEAVE = "user_leave"
    USER_TYPING = "user_typing"
    USER_CURSOR = "user_cursor"

    # Data events
    DATA_CREATE = "data_create"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    DATA_CONFLICT = "data_conflict"

    # Communication events
    COMMENT_ADD = "comment_add"
    COMMENT_UPDATE = "comment_update"
    COMMENT_DELETE = "comment_delete"
    MESSAGE_SEND = "message_send"

    # System events
    SYNC_START = "sync_start"
    SYNC_COMPLETE = "sync_complete"
    CONFLICT_DETECTED = "conflict_detected"
    PERMISSION_CHANGED = "permission_changed"


class ConflictResolutionStrategy(str, Enum):
    """Conflict resolution strategies."""

    LAST_WRITE_WINS = "last_write_wins"
    FIRST_WRITE_WINS = "first_write_wins"
    MERGE_AUTOMATIC = "merge_automatic"
    MERGE_MANUAL = "merge_manual"
    USER_CHOICE = "user_choice"
    ROLE_BASED = "role_based"


class SynchronizationMode(str, Enum):
    """Data synchronization modes."""

    REALTIME = "realtime"  # Immediate sync
    PERIODIC = "periodic"  # Scheduled sync
    ON_DEMAND = "on_demand"  # Manual sync
    EVENTUAL = "eventual"  # Eventually consistent


class PresenceStatus(str, Enum):
    """User presence status."""

    ONLINE = "online"
    AWAY = "away"
    BUSY = "busy"
    OFFLINE = "offline"
    DO_NOT_DISTURB = "do_not_disturb"


class CollaborationEvent(BaseModel):
    """Collaboration event model."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: CollaborationEventType
    timestamp: datetime = Field(default_factory=datetime.now)

    # Event source
    user_id: str
    session_id: str
    device_id: str

    # Event target
    resource_type: str
    resource_id: str
    workspace_id: Optional[str] = None

    # Event data
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Collaboration context
    version: int = 1
    parent_event_id: Optional[str] = None
    conflict_resolution: Optional[ConflictResolutionStrategy] = None


class UserPresence(BaseModel):
    """User presence information."""

    user_id: str
    status: PresenceStatus
    status_message: Optional[str] = None

    # Location context
    workspace_id: Optional[str] = None
    resource_id: Optional[str] = None
    cursor_position: Optional[Dict[str, Any]] = None

    # Device context
    device_info: Dict[str, Any] = Field(default_factory=dict)
    capabilities: Set[str] = Field(default_factory=set)

    # Timing
    last_seen: datetime = Field(default_factory=datetime.now)
    online_since: datetime = Field(default_factory=datetime.now)
    total_session_time: int = 0  # seconds


class DataVersion(BaseModel):
    """Data version for conflict resolution."""

    version_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_id: str
    entity_type: ERPEntityType

    # Version metadata
    version_number: int
    parent_version: Optional[str] = None
    branch_name: str = "main"

    # Change information
    changed_fields: Set[str] = Field(default_factory=set)
    change_summary: str = ""
    change_type: str = "update"  # create, update, delete

    # Author information
    author_id: str
    authored_at: datetime = Field(default_factory=datetime.now)
    committed_at: Optional[datetime] = None

    # Data payload
    data: Dict[str, Any] = Field(default_factory=dict)
    data_hash: str = ""


class ConflictData(BaseModel):
    """Data conflict information."""

    conflict_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_id: str
    entity_type: ERPEntityType

    # Conflicting versions
    base_version: DataVersion
    local_version: DataVersion
    remote_version: DataVersion

    # Conflict analysis
    conflicting_fields: Set[str] = Field(default_factory=set)
    conflict_type: str = (
        "field_conflict"  # field_conflict, schema_conflict, business_rule_conflict
    )
    auto_resolvable: bool = False

    # Resolution
    resolution_strategy: Optional[ConflictResolutionStrategy] = None
    resolved_version: Optional[DataVersion] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None

    # Context
    detected_at: datetime = Field(default_factory=datetime.now)
    priority: int = 1  # 1-5, higher = more critical


class CollaborationWorkspace(BaseModel):
    """Collaborative workspace."""

    workspace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""

    # Workspace configuration
    workspace_type: str = "document"  # document, project, meeting, chat
    entity_type: Optional[ERPEntityType] = None
    entity_id: Optional[str] = None

    # Access control
    owner_id: str
    participants: Set[str] = Field(default_factory=set)
    permissions: Dict[str, Set[str]] = Field(
        default_factory=dict
    )  # user_id -> permissions

    # Collaboration settings
    max_participants: int = 50
    allow_anonymous: bool = False
    require_approval: bool = False
    sync_mode: SynchronizationMode = SynchronizationMode.REALTIME
    conflict_resolution: ConflictResolutionStrategy = (
        ConflictResolutionStrategy.LAST_WRITE_WINS
    )

    # State
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)


class RealtimeMessage(BaseModel):
    """Realtime collaboration message."""

    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message_type: str

    # Routing
    sender_id: str
    recipients: Set[str] = Field(default_factory=set)
    workspace_id: Optional[str] = None
    channel: str = "default"

    # Content
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

    # Delivery
    delivery_required: bool = True
    ttl_seconds: Optional[int] = None
    priority: int = 1


class WebSocketConnection:
    """WebSocket connection wrapper."""

    def __init__(self, websocket, user_id: str, session_id: str) -> dict:
        self.websocket = websocket
        self.user_id = user_id
        self.session_id = session_id
        self.connected_at = datetime.now()
        self.last_ping = datetime.now()
        self.subscriptions: Set[str] = set()
        self.capabilities: Set[str] = set()

    async def send_message(self, message: RealtimeMessage) -> bool:
        """Send message through WebSocket."""
        try:
            message_json = json.dumps(
                {
                    "message_id": message.message_id,
                    "message_type": message.message_type,
                    "sender_id": message.sender_id,
                    "workspace_id": message.workspace_id,
                    "channel": message.channel,
                    "payload": message.payload,
                    "timestamp": message.timestamp.isoformat(),
                }
            )

            await self.websocket.send(message_json)
            return True

        except Exception as e:
            print(f"[WebSocket] Failed to send message: {e}")
            return False

    async def close(self) -> None:
        """Close WebSocket connection."""
        try:
            await self.websocket.close()
        except Exception:
            pass


class RealtimeEventBus:
    """Realtime event distribution system."""

    def __init__(self) -> dict:
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)
        self.workspace_subscribers: Dict[str, Set[str]] = defaultdict(set)
        self.event_handlers: Dict[CollaborationEventType, List[callable]] = defaultdict(
            list
        )

        # Message queue for offline users
        self.offline_messages: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

        # Event history for debugging
        self.event_history: deque = deque(maxlen=1000)

    def register_connection(self, connection: WebSocketConnection) -> None:
        """Register a new WebSocket connection."""
        self.connections[connection.session_id] = connection
        self.user_connections[connection.user_id].add(connection.session_id)

    def unregister_connection(self, session_id: str) -> None:
        """Unregister WebSocket connection."""
        connection = self.connections.get(session_id)
        if connection:
            self.user_connections[connection.user_id].discard(session_id)
            del self.connections[session_id]

    def subscribe_to_workspace(self, session_id: str, workspace_id: str) -> None:
        """Subscribe connection to workspace events."""
        connection = self.connections.get(session_id)
        if connection:
            connection.subscriptions.add(workspace_id)
            self.workspace_subscribers[workspace_id].add(session_id)

    def unsubscribe_from_workspace(self, session_id: str, workspace_id: str) -> None:
        """Unsubscribe connection from workspace events."""
        connection = self.connections.get(session_id)
        if connection:
            connection.subscriptions.discard(workspace_id)
            self.workspace_subscribers[workspace_id].discard(session_id)

    async def publish_event(self, event: CollaborationEvent) -> None:
        """Publish collaboration event to subscribers."""
        # Add to event history
        self.event_history.append(event)

        # Determine recipients
        recipients = set()

        # Add workspace subscribers
        if event.workspace_id:
            recipients.update(self.workspace_subscribers.get(event.workspace_id, set()))

        # Add direct user connections
        if event.user_id in self.user_connections:
            recipients.update(self.user_connections[event.user_id])

        # Create message
        message = RealtimeMessage(
            message_type="collaboration_event",
            sender_id=event.user_id,
            workspace_id=event.workspace_id,
            payload=event.dict(),
        )

        # Send to all recipients
        for session_id in recipients:
            connection = self.connections.get(session_id)
            if connection:
                await connection.send_message(message)

        # Trigger event handlers
        for handler in self.event_handlers[event.event_type]:
            try:
                await handler(event)
            except Exception as e:
                print(f"[Event Bus] Handler error: {e}")

    async def send_direct_message(self, message: RealtimeMessage) -> None:
        """Send direct message to specific recipients."""
        for recipient_id in message.recipients:
            # Get user connections
            session_ids = self.user_connections.get(recipient_id, set())

            if session_ids:
                # Send to all active connections
                for session_id in session_ids:
                    connection = self.connections.get(session_id)
                    if connection:
                        await connection.send_message(message)
            else:
                # Queue for offline user
                if message.delivery_required:
                    self.offline_messages[recipient_id].append(message)

    def register_event_handler(
        self, event_type: CollaborationEventType, handler: callable
    ) -> None:
        """Register event handler."""
        self.event_handlers[event_type].append(handler)

    def get_workspace_participants(self, workspace_id: str) -> List[str]:
        """Get active participants in workspace."""
        session_ids = self.workspace_subscribers.get(workspace_id, set())
        participants = []

        for session_id in session_ids:
            connection = self.connections.get(session_id)
            if connection:
                participants.append(connection.user_id)

        return list(set(participants))  # Remove duplicates


class ConflictResolver:
    """Intelligent conflict resolution system."""

    def __init__(self) -> dict:
        self.resolution_strategies: Dict[ConflictResolutionStrategy, callable] = {
            ConflictResolutionStrategy.LAST_WRITE_WINS: self._resolve_last_write_wins,
            ConflictResolutionStrategy.FIRST_WRITE_WINS: self._resolve_first_write_wins,
            ConflictResolutionStrategy.MERGE_AUTOMATIC: self._resolve_merge_automatic,
            ConflictResolutionStrategy.ROLE_BASED: self._resolve_role_based,
        }

    async def resolve_conflict(
        self, conflict: ConflictData, context: ApplicationContext
    ) -> Optional[DataVersion]:
        """Resolve data conflict."""
        strategy = conflict.resolution_strategy
        if not strategy:
            strategy = ConflictResolutionStrategy.LAST_WRITE_WINS

        resolver = self.resolution_strategies.get(strategy)
        if not resolver:
            return None

        try:
            resolved_version = await resolver(conflict, context)

            if resolved_version:
                conflict.resolved_version = resolved_version
                conflict.resolved_by = context.user_id
                conflict.resolved_at = datetime.now()

            return resolved_version

        except Exception as e:
            print(f"[Conflict Resolver] Error resolving conflict: {e}")
            return None

    async def _resolve_last_write_wins(
        self, conflict: ConflictData, context: ApplicationContext
    ) -> DataVersion:
        """Resolve using last write wins strategy."""
        if conflict.local_version.authored_at > conflict.remote_version.authored_at:
            return conflict.local_version
        else:
            return conflict.remote_version

    async def _resolve_first_write_wins(
        self, conflict: ConflictData, context: ApplicationContext
    ) -> DataVersion:
        """Resolve using first write wins strategy."""
        if conflict.local_version.authored_at < conflict.remote_version.authored_at:
            return conflict.local_version
        else:
            return conflict.remote_version

    async def _resolve_merge_automatic(
        self, conflict: ConflictData, context: ApplicationContext
    ) -> DataVersion:
        """Resolve using automatic merge strategy."""
        # Create merged version
        merged_data = conflict.base_version.data.copy()

        # Merge non-conflicting changes from both versions
        local_changes = self._get_field_changes(
            conflict.base_version.data, conflict.local_version.data
        )
        remote_changes = self._get_field_changes(
            conflict.base_version.data, conflict.remote_version.data
        )

        # Apply non-conflicting changes
        for field, value in local_changes.items():
            if field not in conflict.conflicting_fields:
                merged_data[field] = value

        for field, value in remote_changes.items():
            if field not in conflict.conflicting_fields:
                merged_data[field] = value

        # For conflicting fields, use last write wins as fallback
        for field in conflict.conflicting_fields:
            if conflict.local_version.authored_at > conflict.remote_version.authored_at:
                merged_data[field] = conflict.local_version.data.get(field)
            else:
                merged_data[field] = conflict.remote_version.data.get(field)

        # Create merged version
        merged_version = DataVersion(
            entity_id=conflict.entity_id,
            entity_type=conflict.entity_type,
            version_number=max(
                conflict.local_version.version_number,
                conflict.remote_version.version_number,
            )
            + 1,
            author_id=context.user_id,
            data=merged_data,
            change_summary=f"Auto-merged conflict {conflict.conflict_id}",
            change_type="merge",
        )

        return merged_version

    async def _resolve_role_based(
        self, conflict: ConflictData, context: ApplicationContext
    ) -> DataVersion:
        """Resolve using role-based priority."""
        # Get user roles for both versions
        local_author_roles = self._get_user_roles(
            conflict.local_version.author_id, context
        )
        remote_author_roles = self._get_user_roles(
            conflict.remote_version.author_id, context
        )

        # Define role priority (higher = more priority)
        role_priorities = {
            "system_admin": 100,
            "finance_manager": 90,
            "hr_manager": 85,
            "department_manager": 80,
            "team_lead": 70,
            "senior_user": 60,
            "user": 50,
        }

        local_priority = max(
            [role_priorities.get(role, 0) for role in local_author_roles], default=0
        )
        remote_priority = max(
            [role_priorities.get(role, 0) for role in remote_author_roles], default=0
        )

        if local_priority > remote_priority:
            return conflict.local_version
        elif remote_priority > local_priority:
            return conflict.remote_version
        else:
            # Same priority, fall back to last write wins
            return await self._resolve_last_write_wins(conflict, context)

    def _get_field_changes(
        self, base_data: Dict[str, Any], new_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get changed fields between two data versions."""
        changes = {}

        for field, value in new_data.items():
            if field not in base_data or base_data[field] != value:
                changes[field] = value

        return changes

    def _get_user_roles(self, user_id: str, context: ApplicationContext) -> List[str]:
        """Get user roles (simplified)."""
        # In real implementation, would query user management system
        return context.user_roles if context.user_id == user_id else ["user"]


class VersionedDataStore:
    """Versioned data storage for collaboration."""

    def __init__(self) -> dict:
        self.versions: Dict[str, List[DataVersion]] = defaultdict(list)
        self.latest_versions: Dict[str, DataVersion] = {}
        self.version_tree: Dict[str, Dict[str, List[str]]] = defaultdict(
            lambda: defaultdict(list)
        )

    def store_version(self, version: DataVersion) -> None:
        """Store a new data version."""
        entity_key = f"{version.entity_type}:{version.entity_id}"

        # Add to versions list
        self.versions[entity_key].append(version)

        # Update latest version
        self.latest_versions[entity_key] = version

        # Update version tree
        if version.parent_version:
            self.version_tree[entity_key][version.parent_version].append(
                version.version_id
            )

    def get_version(
        self, entity_type: ERPEntityType, entity_id: str, version_id: str
    ) -> Optional[DataVersion]:
        """Get specific version of entity."""
        entity_key = f"{entity_type}:{entity_id}"
        versions = self.versions.get(entity_key, [])

        for version in versions:
            if version.version_id == version_id:
                return version

        return None

    def get_latest_version(
        self, entity_type: ERPEntityType, entity_id: str
    ) -> Optional[DataVersion]:
        """Get latest version of entity."""
        entity_key = f"{entity_type}:{entity_id}"
        return self.latest_versions.get(entity_key)

    def get_version_history(
        self, entity_type: ERPEntityType, entity_id: str
    ) -> List[DataVersion]:
        """Get version history for entity."""
        entity_key = f"{entity_type}:{entity_id}"
        return self.versions.get(entity_key, [])

    def detect_conflicts(
        self, entity_type: ERPEntityType, entity_id: str, incoming_version: DataVersion
    ) -> Optional[ConflictData]:
        """Detect conflicts with incoming version."""
        current_version = self.get_latest_version(entity_type, entity_id)

        if not current_version:
            return None  # No conflict for new entity

        # Check if versions have same parent (concurrent edits)
        if (
            incoming_version.parent_version
            and current_version.parent_version
            and incoming_version.parent_version != current_version.version_id
            and current_version.parent_version != incoming_version.version_id
        ):
            # Find common ancestor
            base_version = self._find_common_ancestor(
                entity_type,
                entity_id,
                current_version.version_id,
                incoming_version.version_id,
            )

            if base_version:
                # Analyze conflicting fields
                conflicting_fields = self._find_conflicting_fields(
                    base_version.data, current_version.data, incoming_version.data
                )

                if conflicting_fields:
                    return ConflictData(
                        entity_id=entity_id,
                        entity_type=entity_type,
                        base_version=base_version,
                        local_version=current_version,
                        remote_version=incoming_version,
                        conflicting_fields=conflicting_fields,
                        auto_resolvable=len(conflicting_fields) <= 3,  # Heuristic
                    )

        return None

    def _find_common_ancestor(
        self,
        entity_type: ERPEntityType,
        entity_id: str,
        version1_id: str,
        version2_id: str,
    ) -> Optional[DataVersion]:
        """Find common ancestor version."""
        # Simplified implementation - in real system would use proper graph traversal
        entity_key = f"{entity_type}:{entity_id}"
        versions = self.versions.get(entity_key, [])

        # Find versions
        version1 = next((v for v in versions if v.version_id == version1_id), None)
        version2 = next((v for v in versions if v.version_id == version2_id), None)

        if not version1 or not version2:
            return None

        # Simple case: if one is parent of other
        if version1.parent_version == version2.version_id:
            return version2
        if version2.parent_version == version1.version_id:
            return version1

        # Find common parent (simplified)
        if version1.parent_version == version2.parent_version:
            parent_version = next(
                (v for v in versions if v.version_id == version1.parent_version), None
            )
            return parent_version

        return None

    def _find_conflicting_fields(
        self, base_data: Dict[str, Any], data1: Dict[str, Any], data2: Dict[str, Any]
    ) -> Set[str]:
        """Find fields that conflict between two versions."""
        conflicting_fields = set()

        # Get all fields that changed from base
        changed_fields1 = set()
        changed_fields2 = set()

        for field in set(
            list(base_data.keys()) + list(data1.keys()) + list(data2.keys())
        ):
            base_value = base_data.get(field)
            value1 = data1.get(field)
            value2 = data2.get(field)

            if base_value != value1:
                changed_fields1.add(field)
            if base_value != value2:
                changed_fields2.add(field)

        # Find fields changed by both versions with different values
        for field in changed_fields1.intersection(changed_fields2):
            if data1.get(field) != data2.get(field):
                conflicting_fields.add(field)

        return conflicting_fields


class CollaborationManager:
    """Main collaboration management system."""

    def __init__(self, sdk: MobileERPSDK) -> dict:
        self.sdk = sdk
        self.event_bus = RealtimeEventBus()
        self.conflict_resolver = ConflictResolver()
        self.version_store = VersionedDataStore()

        # State management
        self.workspaces: Dict[str, CollaborationWorkspace] = {}
        self.user_presence: Dict[str, UserPresence] = {}
        self.active_conflicts: Dict[str, ConflictData] = {}

        # WebSocket server
        self.websocket_server = None
        self.server_port = 8765

        # Register event handlers
        self._register_event_handlers()

    def _register_event_handlers(self) -> None:
        """Register collaboration event handlers."""
        self.event_bus.register_event_handler(
            CollaborationEventType.DATA_UPDATE, self._handle_data_update
        )
        self.event_bus.register_event_handler(
            CollaborationEventType.DATA_CONFLICT, self._handle_data_conflict
        )
        self.event_bus.register_event_handler(
            CollaborationEventType.USER_JOIN, self._handle_user_join
        )
        self.event_bus.register_event_handler(
            CollaborationEventType.USER_LEAVE, self._handle_user_leave
        )

    async def start_websocket_server(self) -> None:
        """Start WebSocket server for realtime communication."""

        async def handle_client(websocket, path) -> dict:
            await self._handle_websocket_connection(websocket, path)

        self.websocket_server = await websockets.serve(
            handle_client, "localhost", self.server_port
        )

        print(f"[Collaboration] WebSocket server started on port {self.server_port}")

    async def _handle_websocket_connection(self, websocket, path: str) -> None:
        """Handle new WebSocket connection."""
        connection = None

        try:
            # Wait for authentication message
            auth_message = await websocket.recv()
            auth_data = json.loads(auth_message)

            # Validate authentication
            user_id = auth_data.get("user_id")
            session_id = auth_data.get("session_id")

            if not user_id or not session_id:
                await websocket.close(code=4001, reason="Authentication required")
                return

            # Create connection
            connection = WebSocketConnection(websocket, user_id, session_id)
            self.event_bus.register_connection(connection)

            # Send authentication success
            await connection.send_message(
                RealtimeMessage(
                    message_type="auth_success",
                    sender_id="system",
                    recipients={user_id},
                    payload={"session_id": session_id},
                )
            )

            # Handle messages
            async for message in websocket:
                await self._handle_websocket_message(connection, message)

        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"[WebSocket] Connection error: {e}")
        finally:
            if connection:
                self.event_bus.unregister_connection(connection.session_id)

    async def _handle_websocket_message(
        self, connection: WebSocketConnection, message: str
    ) -> None:
        """Handle WebSocket message from client."""
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "ping":
                # Update last ping time
                connection.last_ping = datetime.now()
                await connection.send_message(
                    RealtimeMessage(
                        message_type="pong",
                        sender_id="system",
                        recipients={connection.user_id},
                    )
                )

            elif message_type == "subscribe_workspace":
                workspace_id = data.get("workspace_id")
                if workspace_id:
                    self.event_bus.subscribe_to_workspace(
                        connection.session_id, workspace_id
                    )

            elif message_type == "unsubscribe_workspace":
                workspace_id = data.get("workspace_id")
                if workspace_id:
                    self.event_bus.unsubscribe_from_workspace(
                        connection.session_id, workspace_id
                    )

            elif message_type == "collaboration_event":
                # Create and publish collaboration event
                event = CollaborationEvent(
                    event_type=CollaborationEventType(data.get("event_type")),
                    user_id=connection.user_id,
                    session_id=connection.session_id,
                    device_id=data.get("device_id", "unknown"),
                    resource_type=data.get("resource_type"),
                    resource_id=data.get("resource_id"),
                    workspace_id=data.get("workspace_id"),
                    data=data.get("data", {}),
                    metadata=data.get("metadata", {}),
                )

                await self.event_bus.publish_event(event)

            elif message_type == "update_presence":
                # Update user presence
                presence = UserPresence(
                    user_id=connection.user_id,
                    status=PresenceStatus(data.get("status", "online")),
                    status_message=data.get("status_message"),
                    workspace_id=data.get("workspace_id"),
                    resource_id=data.get("resource_id"),
                    cursor_position=data.get("cursor_position"),
                    device_info=data.get("device_info", {}),
                    capabilities=set(data.get("capabilities", [])),
                )

                self.user_presence[connection.user_id] = presence

                # Broadcast presence update
                await self._broadcast_presence_update(presence)

        except Exception as e:
            print(f"[WebSocket] Message handling error: {e}")

    async def create_workspace(
        self,
        name: str,
        workspace_type: str,
        owner_id: str,
        entity_type: Optional[ERPEntityType] = None,
        entity_id: Optional[str] = None,
        **kwargs,
    ) -> CollaborationWorkspace:
        """Create new collaboration workspace."""
        workspace = CollaborationWorkspace(
            name=name,
            workspace_type=workspace_type,
            owner_id=owner_id,
            entity_type=entity_type,
            entity_id=entity_id,
            **kwargs,
        )

        # Set owner permissions
        workspace.permissions[owner_id] = {"read", "write", "admin", "invite"}
        workspace.participants.add(owner_id)

        self.workspaces[workspace.workspace_id] = workspace

        # Publish workspace creation event
        await self.event_bus.publish_event(
            CollaborationEvent(
                event_type=CollaborationEventType.USER_JOIN,
                user_id=owner_id,
                session_id="system",
                device_id="system",
                resource_type="workspace",
                resource_id=workspace.workspace_id,
                workspace_id=workspace.workspace_id,
                data={"workspace_created": True},
            )
        )

        return workspace

    async def join_workspace(
        self, workspace_id: str, user_id: str, session_id: str
    ) -> bool:
        """Join user to collaboration workspace."""
        workspace = self.workspaces.get(workspace_id)
        if not workspace or not workspace.active:
            return False

        # Check permissions
        if workspace.require_approval and user_id not in workspace.participants:
            # Would normally require approval workflow
            return False

        # Add to participants
        workspace.participants.add(user_id)
        workspace.last_activity = datetime.now()

        # Set default permissions
        if user_id not in workspace.permissions:
            workspace.permissions[user_id] = {"read"}

        # Publish join event
        await self.event_bus.publish_event(
            CollaborationEvent(
                event_type=CollaborationEventType.USER_JOIN,
                user_id=user_id,
                session_id=session_id,
                device_id="unknown",
                resource_type="workspace",
                resource_id=workspace_id,
                workspace_id=workspace_id,
                data={"participant_count": len(workspace.participants)},
            )
        )

        return True

    async def leave_workspace(
        self, workspace_id: str, user_id: str, session_id: str
    ) -> bool:
        """Remove user from collaboration workspace."""
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return False

        workspace.participants.discard(user_id)
        workspace.last_activity = datetime.now()

        # Publish leave event
        await self.event_bus.publish_event(
            CollaborationEvent(
                event_type=CollaborationEventType.USER_LEAVE,
                user_id=user_id,
                session_id=session_id,
                device_id="unknown",
                resource_type="workspace",
                resource_id=workspace_id,
                workspace_id=workspace_id,
                data={"participant_count": len(workspace.participants)},
            )
        )

        return True

    async def sync_data_version(
        self,
        entity_type: ERPEntityType,
        entity_id: str,
        data: Dict[str, Any],
        user_id: str,
        parent_version_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[ConflictData]]:
        """Synchronize data version with conflict detection."""
        # Create new version
        version = DataVersion(
            entity_id=entity_id,
            entity_type=entity_type,
            version_number=1,  # Would be calculated properly
            parent_version=parent_version_id,
            author_id=user_id,
            data=data,
            data_hash=self._calculate_data_hash(data),
        )

        # Check for conflicts
        conflict = self.version_store.detect_conflicts(entity_type, entity_id, version)

        if conflict:
            # Store conflict for resolution
            self.active_conflicts[conflict.conflict_id] = conflict

            # Try automatic resolution
            context = ApplicationContext(
                user_id=user_id,
                organization_id="default",
                session_id="sync_session",
                device_info=None,
                current_state="ready",
            )

            resolved_version = await self.conflict_resolver.resolve_conflict(
                conflict, context
            )

            if resolved_version:
                # Store resolved version
                self.version_store.store_version(resolved_version)

                # Remove from active conflicts
                del self.active_conflicts[conflict.conflict_id]

                return True, None
            else:
                # Manual resolution required
                return False, conflict
        else:
            # No conflict, store version
            self.version_store.store_version(version)
            return True, None

    def _calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """Calculate hash of data for version comparison."""
        import hashlib

        data_json = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_json.encode()).hexdigest()

    async def _handle_data_update(self, event: CollaborationEvent) -> None:
        """Handle data update event."""
        # Extract update information
        entity_type = ERPEntityType(event.data.get("entity_type"))
        entity_id = event.data.get("entity_id")
        updated_data = event.data.get("data", {})

        # Sync data version
        success, conflict = await self.sync_data_version(
            entity_type, entity_id, updated_data, event.user_id
        )

        if conflict:
            # Publish conflict event
            await self.event_bus.publish_event(
                CollaborationEvent(
                    event_type=CollaborationEventType.DATA_CONFLICT,
                    user_id=event.user_id,
                    session_id=event.session_id,
                    device_id=event.device_id,
                    resource_type=event.resource_type,
                    resource_id=event.resource_id,
                    workspace_id=event.workspace_id,
                    data={"conflict_id": conflict.conflict_id},
                )
            )

    async def _handle_data_conflict(self, event: CollaborationEvent) -> None:
        """Handle data conflict event."""
        conflict_id = event.data.get("conflict_id")
        conflict = self.active_conflicts.get(conflict_id)

        if conflict:
            # Notify workspace participants about conflict
            if event.workspace_id:
                participants = self.event_bus.get_workspace_participants(
                    event.workspace_id
                )

                for participant_id in participants:
                    if participant_id != event.user_id:
                        await self.event_bus.send_direct_message(
                            RealtimeMessage(
                                message_type="conflict_notification",
                                sender_id="system",
                                recipients={participant_id},
                                payload={
                                    "conflict_id": conflict_id,
                                    "entity_type": conflict.entity_type,
                                    "entity_id": conflict.entity_id,
                                    "requires_manual_resolution": not conflict.auto_resolvable,
                                },
                            )
                        )

    async def _handle_user_join(self, event: CollaborationEvent) -> None:
        """Handle user join event."""
        # Broadcast to other participants
        if event.workspace_id:
            participants = self.event_bus.get_workspace_participants(event.workspace_id)

            for participant_id in participants:
                if participant_id != event.user_id:
                    await self.event_bus.send_direct_message(
                        RealtimeMessage(
                            message_type="user_joined",
                            sender_id="system",
                            recipients={participant_id},
                            payload={
                                "user_id": event.user_id,
                                "workspace_id": event.workspace_id,
                                "participant_count": event.data.get(
                                    "participant_count", 0
                                ),
                            },
                        )
                    )

    async def _handle_user_leave(self, event: CollaborationEvent) -> None:
        """Handle user leave event."""
        # Clean up user presence
        if event.user_id in self.user_presence:
            del self.user_presence[event.user_id]

        # Broadcast to other participants
        if event.workspace_id:
            participants = self.event_bus.get_workspace_participants(event.workspace_id)

            for participant_id in participants:
                if participant_id != event.user_id:
                    await self.event_bus.send_direct_message(
                        RealtimeMessage(
                            message_type="user_left",
                            sender_id="system",
                            recipients={participant_id},
                            payload={
                                "user_id": event.user_id,
                                "workspace_id": event.workspace_id,
                                "participant_count": event.data.get(
                                    "participant_count", 0
                                ),
                            },
                        )
                    )

    async def _broadcast_presence_update(self, presence: UserPresence) -> None:
        """Broadcast user presence update."""
        # Find relevant workspaces
        workspaces_to_notify = []

        if presence.workspace_id:
            workspaces_to_notify.append(presence.workspace_id)
        else:
            # Notify all workspaces where user is participant
            for workspace in self.workspaces.values():
                if presence.user_id in workspace.participants:
                    workspaces_to_notify.append(workspace.workspace_id)

        # Broadcast to workspace participants
        for workspace_id in workspaces_to_notify:
            participants = self.event_bus.get_workspace_participants(workspace_id)

            for participant_id in participants:
                if participant_id != presence.user_id:
                    await self.event_bus.send_direct_message(
                        RealtimeMessage(
                            message_type="presence_update",
                            sender_id="system",
                            recipients={participant_id},
                            payload={
                                "user_id": presence.user_id,
                                "status": presence.status,
                                "status_message": presence.status_message,
                                "workspace_id": presence.workspace_id,
                                "cursor_position": presence.cursor_position,
                                "last_seen": presence.last_seen.isoformat(),
                            },
                        )
                    )

    def get_workspace_status(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive workspace status."""
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return None

        # Get active participants
        active_participants = self.event_bus.get_workspace_participants(workspace_id)

        # Get presence information
        participant_presence = {}
        for user_id in active_participants:
            presence = self.user_presence.get(user_id)
            if presence:
                participant_presence[user_id] = {
                    "status": presence.status,
                    "status_message": presence.status_message,
                    "last_seen": presence.last_seen.isoformat(),
                    "cursor_position": presence.cursor_position,
                }

        # Get active conflicts
        workspace_conflicts = []
        for conflict in self.active_conflicts.values():
            if (
                conflict.entity_type == workspace.entity_type
                and conflict.entity_id == workspace.entity_id
            ):
                workspace_conflicts.append(
                    {
                        "conflict_id": conflict.conflict_id,
                        "conflicting_fields": list(conflict.conflicting_fields),
                        "auto_resolvable": conflict.auto_resolvable,
                        "detected_at": conflict.detected_at.isoformat(),
                    }
                )

        return {
            "workspace_id": workspace_id,
            "name": workspace.name,
            "workspace_type": workspace.workspace_type,
            "owner_id": workspace.owner_id,
            "total_participants": len(workspace.participants),
            "active_participants": len(active_participants),
            "participant_presence": participant_presence,
            "active_conflicts": workspace_conflicts,
            "last_activity": workspace.last_activity.isoformat(),
            "sync_mode": workspace.sync_mode,
            "conflict_resolution": workspace.conflict_resolution,
        }

    async def stop(self) -> None:
        """Stop collaboration manager and cleanup resources."""
        if self.websocket_server:
            self.websocket_server.close()
            await self.websocket_server.wait_closed()

        # Close all connections
        for connection in self.event_bus.connections.values():
            await connection.close()

        print("[Collaboration] Manager stopped")
