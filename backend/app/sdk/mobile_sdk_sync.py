"""Mobile SDK Data Synchronization & Offline Module - CC02 v72.0 Day 17."""

from __future__ import annotations

import asyncio
import gzip
import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from pydantic import BaseModel, Field

from .mobile_sdk_core import MobileERPSDK, NetworkError, SDKError


class SyncStatus(str, Enum):
    """Synchronization status."""

    IDLE = "idle"
    PREPARING = "preparing"
    UPLOADING = "uploading"
    DOWNLOADING = "downloading"
    APPLYING = "applying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConflictResolution(str, Enum):
    """Conflict resolution strategies."""

    CLIENT_WINS = "client_wins"
    SERVER_WINS = "server_wins"
    MERGE = "merge"
    MANUAL = "manual"
    LAST_MODIFIED = "last_modified"


class SyncPriority(str, Enum):
    """Synchronization priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class SyncDirection(str, Enum):
    """Synchronization direction."""

    UPLOAD = "upload"
    DOWNLOAD = "download"
    BIDIRECTIONAL = "bidirectional"


class EntitySyncConfig(BaseModel):
    """Entity synchronization configuration."""

    entity_type: str
    sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    conflict_resolution: ConflictResolution = ConflictResolution.SERVER_WINS
    priority: SyncPriority = SyncPriority.NORMAL
    batch_size: int = Field(default=100, ge=1, le=1000)
    enable_compression: bool = True
    enable_encryption: bool = True
    sync_frequency_minutes: int = Field(default=15, ge=1)
    offline_retention_days: int = Field(default=30, ge=1, le=365)
    dependencies: List[str] = Field(default_factory=list)
    filters: Dict[str, Any] = Field(default_factory=dict)


class SyncOperation(BaseModel):
    """Individual sync operation."""

    operation_id: str
    entity_type: str
    entity_id: str
    operation_type: str  # create, update, delete
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime
    client_version: int
    server_version: Optional[int] = None
    conflict_data: Optional[Dict[str, Any]] = None
    resolved: bool = False


class SyncBatch(BaseModel):
    """Batch of sync operations."""

    batch_id: str
    entity_type: str
    operations: List[SyncOperation]
    batch_size: int
    created_at: datetime
    status: SyncStatus = SyncStatus.PREPARING
    progress_percentage: float = 0.0
    error_message: Optional[str] = None
    compressed_size: Optional[int] = None
    uncompressed_size: Optional[int] = None


class SyncSession(BaseModel):
    """Synchronization session."""

    session_id: str
    device_id: str
    user_id: str
    organization_id: str
    started_at: datetime
    last_activity: datetime
    status: SyncStatus
    entity_configs: List[EntitySyncConfig]
    batches: List[SyncBatch] = Field(default_factory=list)
    total_operations: int = 0
    completed_operations: int = 0
    failed_operations: int = 0
    conflicts_detected: int = 0
    data_transferred_mb: float = 0.0
    compression_ratio: float = 0.0
    estimated_completion: Optional[datetime] = None


T = TypeVar("T")


class OfflineStorage:
    """SQLite-based offline storage."""

    def __init__(self, storage_path: str) -> dict:
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: Optional[sqlite3.Connection] = None
        self._lock = threading.RLock()
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            # Entity data table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entity_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    data TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    synced_at TIMESTAMP,
                    deleted BOOLEAN DEFAULT FALSE,
                    conflict_data TEXT,
                    UNIQUE(entity_type, entity_id)
                )
            """)

            # Sync operations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id TEXT UNIQUE NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    client_version INTEGER NOT NULL,
                    server_version INTEGER,
                    status TEXT DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Sync metadata table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_entity_data_type_id ON entity_data(entity_type, entity_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_entity_data_updated ON entity_data(updated_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sync_ops_type ON sync_operations(entity_type)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sync_ops_status ON sync_operations(status)"
            )

            conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(
                str(self.storage_path), check_same_thread=False, timeout=30.0
            )
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._connection.execute("PRAGMA journal_mode = WAL")
        return self._connection

    def store_entity(
        self, entity_type: str, entity_id: str, data: Dict[str, Any], version: int = 1
    ) -> None:
        """Store entity data."""
        with self._lock:
            conn = self._get_connection()
            data_json = json.dumps(data, default=str)

            conn.execute(
                """
                INSERT OR REPLACE INTO entity_data
                (entity_type, entity_id, data, version, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (entity_type, entity_id, data_json, version),
            )
            conn.commit()

    def get_entity(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity data."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.execute(
                """
                SELECT data, version, updated_at, synced_at, deleted
                FROM entity_data
                WHERE entity_type = ? AND entity_id = ? AND deleted = FALSE
            """,
                (entity_type, entity_id),
            )

            row = cursor.fetchone()
            if row:
                return {
                    "data": json.loads(row["data"]),
                    "version": row["version"],
                    "updated_at": row["updated_at"],
                    "synced_at": row["synced_at"],
                    "deleted": bool(row["deleted"]),
                }
            return None

    def list_entities(
        self,
        entity_type: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List entities with filtering."""
        with self._lock:
            conn = self._get_connection()

            query = """
                SELECT entity_id, data, version, updated_at, synced_at
                FROM entity_data
                WHERE entity_type = ? AND deleted = FALSE
            """
            params = [entity_type]

            # Add filters (simplified implementation)
            if filters:
                for key, value in filters.items():
                    query += f" AND json_extract(data, '$.{key}') = ?"
                    params.append(value)

            query += " ORDER BY updated_at DESC"

            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])

            cursor = conn.execute(query, params)

            entities = []
            for row in cursor.fetchall():
                entities.append(
                    {
                        "entity_id": row["entity_id"],
                        "data": json.loads(row["data"]),
                        "version": row["version"],
                        "updated_at": row["updated_at"],
                        "synced_at": row["synced_at"],
                    }
                )

            return entities

    def delete_entity(self, entity_type: str, entity_id: str) -> None:
        """Mark entity as deleted."""
        with self._lock:
            conn = self._get_connection()
            conn.execute(
                """
                UPDATE entity_data
                SET deleted = TRUE, updated_at = CURRENT_TIMESTAMP
                WHERE entity_type = ? AND entity_id = ?
            """,
                (entity_type, entity_id),
            )
            conn.commit()

    def store_sync_operation(self, operation: SyncOperation) -> None:
        """Store sync operation."""
        with self._lock:
            conn = self._get_connection()
            data_json = json.dumps(operation.data, default=str)

            conn.execute(
                """
                INSERT OR REPLACE INTO sync_operations
                (operation_id, entity_type, entity_id, operation_type, data,
                 timestamp, client_version, server_version, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    operation.operation_id,
                    operation.entity_type,
                    operation.entity_id,
                    operation.operation_type,
                    data_json,
                    operation.timestamp.isoformat(),
                    operation.client_version,
                    operation.server_version,
                    "pending",
                ),
            )
            conn.commit()

    def get_pending_operations(
        self, entity_type: Optional[str] = None, limit: Optional[int] = None
    ) -> List[SyncOperation]:
        """Get pending sync operations."""
        with self._lock:
            conn = self._get_connection()

            query = """
                SELECT operation_id, entity_type, entity_id, operation_type, data,
                       timestamp, client_version, server_version
                FROM sync_operations
                WHERE status = 'pending'
            """
            params = []

            if entity_type:
                query += " AND entity_type = ?"
                params.append(entity_type)

            query += " ORDER BY timestamp ASC"

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            cursor = conn.execute(query, params)

            operations = []
            for row in cursor.fetchall():
                operations.append(
                    SyncOperation(
                        operation_id=row["operation_id"],
                        entity_type=row["entity_type"],
                        entity_id=row["entity_id"],
                        operation_type=row["operation_type"],
                        data=json.loads(row["data"]),
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        client_version=row["client_version"],
                        server_version=row["server_version"],
                    )
                )

            return operations

    def update_operation_status(
        self, operation_id: str, status: str, error_message: Optional[str] = None
    ) -> None:
        """Update sync operation status."""
        with self._lock:
            conn = self._get_connection()
            conn.execute(
                """
                UPDATE sync_operations
                SET status = ?, error_message = ?, retry_count = retry_count + 1
                WHERE operation_id = ?
            """,
                (status, error_message, operation_id),
            )
            conn.commit()

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value."""
        with self._lock:
            conn = self._get_connection()
            value_json = json.dumps(value, default=str)
            conn.execute(
                """
                INSERT OR REPLACE INTO sync_metadata (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
                (key, value_json),
            )
            conn.commit()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.execute(
                """
                SELECT value FROM sync_metadata WHERE key = ?
            """,
                (key,),
            )

            row = cursor.fetchone()
            if row:
                return json.loads(row["value"])
            return default

    def cleanup_old_data(self, retention_days: int = 30) -> int:
        """Clean up old data beyond retention period."""
        with self._lock:
            conn = self._get_connection()
            cutoff_date = datetime.now() - timedelta(days=retention_days)

            # Clean up old deleted entities
            cursor = conn.execute(
                """
                DELETE FROM entity_data
                WHERE deleted = TRUE AND updated_at < ?
            """,
                (cutoff_date.isoformat(),),
            )

            deleted_count = cursor.rowcount

            # Clean up completed sync operations
            conn.execute(
                """
                DELETE FROM sync_operations
                WHERE status IN ('completed', 'failed') AND created_at < ?
            """,
                (cutoff_date.isoformat(),),
            )

            conn.commit()
            return deleted_count

    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage information."""
        with self._lock:
            conn = self._get_connection()

            # Get table sizes
            cursor = conn.execute("""
                SELECT
                    (SELECT COUNT(*) FROM entity_data WHERE deleted = FALSE) as entities,
                    (SELECT COUNT(*) FROM sync_operations WHERE status = 'pending') as pending_ops,
                    (SELECT COUNT(*) FROM sync_metadata) as metadata_entries
            """)
            row = cursor.fetchone()

            # Get file size
            file_size = (
                self.storage_path.stat().st_size if self.storage_path.exists() else 0
            )

            return {
                "file_path": str(self.storage_path),
                "file_size_bytes": file_size,
                "entity_count": row["entities"],
                "pending_operations": row["pending_ops"],
                "metadata_entries": row["metadata_entries"],
            }

    def close(self) -> None:
        """Close database connection."""
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None


class ConflictResolver:
    """Handles data conflicts during synchronization."""

    def __init__(
        self, default_strategy: ConflictResolution = ConflictResolution.SERVER_WINS
    ):
        self.default_strategy = default_strategy
        self._custom_resolvers: Dict[str, Callable] = {}

    def register_resolver(
        self,
        entity_type: str,
        resolver_func: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]],
    ) -> None:
        """Register custom conflict resolver for entity type."""
        self._custom_resolvers[entity_type] = resolver_func

    def resolve_conflict(
        self,
        entity_type: str,
        client_data: Dict[str, Any],
        server_data: Dict[str, Any],
        strategy: Optional[ConflictResolution] = None,
    ) -> Dict[str, Any]:
        """Resolve data conflict."""
        resolution_strategy = strategy or self.default_strategy

        # Use custom resolver if available
        if entity_type in self._custom_resolvers:
            try:
                return self._custom_resolvers[entity_type](client_data, server_data)
            except Exception as e:
                print(f"[SDK] Custom resolver failed: {e}, falling back to default")

        # Apply resolution strategy
        if resolution_strategy == ConflictResolution.CLIENT_WINS:
            return client_data
        elif resolution_strategy == ConflictResolution.SERVER_WINS:
            return server_data
        elif resolution_strategy == ConflictResolution.LAST_MODIFIED:
            client_modified = client_data.get("updated_at", "1970-01-01T00:00:00")
            server_modified = server_data.get("updated_at", "1970-01-01T00:00:00")
            return client_data if client_modified > server_modified else server_data
        elif resolution_strategy == ConflictResolution.MERGE:
            return self._merge_data(client_data, server_data)
        else:  # MANUAL
            # Return both for manual resolution
            return {
                "conflict": True,
                "client_data": client_data,
                "server_data": server_data,
                "resolution_required": True,
            }

    def _merge_data(
        self, client_data: Dict[str, Any], server_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge client and server data."""
        merged = server_data.copy()

        for key, value in client_data.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(value, dict) and isinstance(merged[key], dict):
                merged[key] = self._merge_data(value, merged[key])
            elif isinstance(value, list) and isinstance(merged[key], list):
                # Merge lists by extending (simple approach)
                merged[key] = list(set(merged[key] + value))
            else:
                # Keep server value for conflicting fields
                pass

        return merged


class DataCompressor:
    """Data compression utilities."""

    @staticmethod
    def compress_data(data: Union[str, bytes]) -> bytes:
        """Compress data using gzip."""
        if isinstance(data, str):
            data = data.encode("utf-8")
        return gzip.compress(data, compresslevel=6)

    @staticmethod
    def decompress_data(compressed_data: bytes) -> bytes:
        """Decompress gzip data."""
        return gzip.decompress(compressed_data)

    @staticmethod
    def compress_json(data: Dict[str, Any]) -> bytes:
        """Compress JSON data."""
        json_str = json.dumps(data, separators=(",", ":"), default=str)
        return DataCompressor.compress_data(json_str)

    @staticmethod
    def decompress_json(compressed_data: bytes) -> Dict[str, Any]:
        """Decompress JSON data."""
        json_str = DataCompressor.decompress_data(compressed_data).decode("utf-8")
        return json.loads(json_str)

    @staticmethod
    def calculate_compression_ratio(original_size: int, compressed_size: int) -> float:
        """Calculate compression ratio."""
        if original_size == 0:
            return 0.0
        return 1.0 - (compressed_size / original_size)


class SyncProgressTracker:
    """Tracks synchronization progress."""

    def __init__(self) -> dict:
        self._listeners: List[Callable[[Dict[str, Any]], None]] = []
        self._current_session: Optional[SyncSession] = None

    def add_listener(self, listener: Callable[[Dict[str, Any]], None]) -> None:
        """Add progress listener."""
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[Dict[str, Any]], None]) -> None:
        """Remove progress listener."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def start_session(self, session: SyncSession) -> None:
        """Start tracking session."""
        self._current_session = session
        self._notify_listeners(
            "session_started",
            {
                "session_id": session.session_id,
                "total_operations": session.total_operations,
            },
        )

    def update_progress(
        self,
        completed_operations: int,
        failed_operations: int = 0,
        data_transferred_mb: float = 0.0,
    ) -> None:
        """Update progress."""
        if not self._current_session:
            return

        self._current_session.completed_operations = completed_operations
        self._current_session.failed_operations = failed_operations
        self._current_session.data_transferred_mb += data_transferred_mb
        self._current_session.last_activity = datetime.now()

        # Calculate progress percentage
        if self._current_session.total_operations > 0:
            progress = (
                completed_operations / self._current_session.total_operations
            ) * 100
        else:
            progress = 0.0

        # Estimate completion time
        if progress > 0 and self._current_session.started_at:
            elapsed = datetime.now() - self._current_session.started_at
            estimated_total = elapsed / (progress / 100)
            self._current_session.estimated_completion = (
                self._current_session.started_at + estimated_total
            )

        self._notify_listeners(
            "progress_updated",
            {
                "session_id": self._current_session.session_id,
                "progress_percentage": progress,
                "completed_operations": completed_operations,
                "failed_operations": failed_operations,
                "data_transferred_mb": self._current_session.data_transferred_mb,
                "estimated_completion": self._current_session.estimated_completion,
            },
        )

    def complete_session(
        self, status: SyncStatus, error_message: Optional[str] = None
    ) -> None:
        """Complete session tracking."""
        if not self._current_session:
            return

        self._current_session.status = status

        self._notify_listeners(
            "session_completed",
            {
                "session_id": self._current_session.session_id,
                "status": status.value,
                "completed_operations": self._current_session.completed_operations,
                "failed_operations": self._current_session.failed_operations,
                "data_transferred_mb": self._current_session.data_transferred_mb,
                "duration_seconds": (
                    datetime.now() - self._current_session.started_at
                ).total_seconds(),
                "error_message": error_message,
            },
        )

        self._current_session = None

    def _notify_listeners(self, event_type: str, data: Dict[str, Any]) -> None:
        """Notify all listeners."""
        event_data = {"event_type": event_type, **data}
        for listener in self._listeners:
            try:
                listener(event_data)
            except Exception as e:
                print(f"[SDK] Progress listener error: {e}")


class SyncEngine:
    """Core synchronization engine."""

    def __init__(self, sdk: MobileERPSDK, storage: OfflineStorage) -> dict:
        self.sdk = sdk
        self.storage = storage
        self.conflict_resolver = ConflictResolver()
        self.progress_tracker = SyncProgressTracker()

        self._entity_configs: Dict[str, EntitySyncConfig] = {}
        self._sync_lock = asyncio.Lock()
        self._background_sync_task: Optional[asyncio.Task] = None
        self._sync_active = False

    def register_entity_config(self, config: EntitySyncConfig) -> None:
        """Register entity synchronization configuration."""
        self._entity_configs[config.entity_type] = config

    def get_entity_config(self, entity_type: str) -> Optional[EntitySyncConfig]:
        """Get entity synchronization configuration."""
        return self._entity_configs.get(entity_type)

    async def start_background_sync(self) -> None:
        """Start background synchronization."""
        if self._background_sync_task and not self._background_sync_task.done():
            return

        self._background_sync_task = asyncio.create_task(self._background_sync_loop())

    async def stop_background_sync(self) -> None:
        """Stop background synchronization."""
        if self._background_sync_task:
            self._background_sync_task.cancel()
            try:
                await self._background_sync_task
            except asyncio.CancelledError:
                pass

    async def sync_now(
        self, entity_types: Optional[List[str]] = None, force_full_sync: bool = False
    ) -> SyncSession:
        """Trigger immediate synchronization."""
        async with self._sync_lock:
            if self._sync_active:
                raise SDKError("Synchronization already in progress")

            self._sync_active = True

            try:
                # Determine entity types to sync
                if entity_types is None:
                    entity_types = list(self._entity_configs.keys())

                # Create sync session
                session = SyncSession(
                    session_id=f"sync_{int(time.time() * 1000)}",
                    device_id=self.sdk.auth_manager.device_info.device_id
                    if self.sdk.auth_manager.device_info
                    else "unknown",
                    user_id="current_user",  # Get from auth manager
                    organization_id=self.sdk.config.organization_id,
                    started_at=datetime.now(),
                    last_activity=datetime.now(),
                    status=SyncStatus.PREPARING,
                    entity_configs=[
                        self._entity_configs[et]
                        for et in entity_types
                        if et in self._entity_configs
                    ],
                )

                # Start progress tracking
                self.progress_tracker.start_session(session)

                # Execute sync for each entity type
                for entity_type in entity_types:
                    if entity_type not in self._entity_configs:
                        continue

                    config = self._entity_configs[entity_type]

                    try:
                        await self._sync_entity_type(session, config, force_full_sync)
                    except Exception as e:
                        print(f"[SDK] Sync failed for {entity_type}: {e}")
                        session.failed_operations += 1

                # Complete session
                session.status = (
                    SyncStatus.COMPLETED
                    if session.failed_operations == 0
                    else SyncStatus.FAILED
                )
                self.progress_tracker.complete_session(session.status)

                return session

            finally:
                self._sync_active = False

    async def _sync_entity_type(
        self, session: SyncSession, config: EntitySyncConfig, force_full_sync: bool
    ) -> None:
        """Synchronize specific entity type."""
        # Phase 1: Upload local changes
        if config.sync_direction in [SyncDirection.UPLOAD, SyncDirection.BIDIRECTIONAL]:
            await self._upload_changes(session, config)

        # Phase 2: Download server changes
        if config.sync_direction in [
            SyncDirection.DOWNLOAD,
            SyncDirection.BIDIRECTIONAL,
        ]:
            await self._download_changes(session, config, force_full_sync)

    async def _upload_changes(
        self, session: SyncSession, config: EntitySyncConfig
    ) -> None:
        """Upload local changes to server."""
        session.status = SyncStatus.UPLOADING

        # Get pending operations
        pending_ops = self.storage.get_pending_operations(
            entity_type=config.entity_type, limit=config.batch_size
        )

        if not pending_ops:
            return

        # Create batch
        batch = SyncBatch(
            batch_id=f"upload_{config.entity_type}_{int(time.time() * 1000)}",
            entity_type=config.entity_type,
            operations=pending_ops,
            batch_size=len(pending_ops),
            created_at=datetime.now(),
        )

        session.batches.append(batch)
        session.total_operations += len(pending_ops)

        try:
            # Prepare batch data
            batch_data = {
                "batch_id": batch.batch_id,
                "entity_type": config.entity_type,
                "operations": [op.dict() for op in pending_ops],
                "sync_options": {
                    "conflict_resolution": config.conflict_resolution.value,
                    "enable_compression": config.enable_compression,
                },
            }

            # Compress if enabled
            if config.enable_compression:
                original_size = len(json.dumps(batch_data))
                compressed_data = DataCompressor.compress_json(batch_data)
                batch.compressed_size = len(compressed_data)
                batch.uncompressed_size = original_size
                batch.compression_ratio = DataCompressor.calculate_compression_ratio(
                    original_size, batch.compressed_size
                )

            # Upload to server
            response = await self.sdk.http_client.post(
                "mobile-erp/sync/upload",
                batch_data,
                params={"organization_id": self.sdk.config.organization_id},
            )

            if response["status"] != 200:
                raise NetworkError(
                    f"Upload failed: {response.get('data', {}).get('message', 'Unknown error')}"
                )

            # Process upload results
            upload_results = response["data"]
            for i, result in enumerate(upload_results.get("results", [])):
                operation = pending_ops[i]

                if result.get("success"):
                    self.storage.update_operation_status(
                        operation.operation_id, "completed"
                    )
                    session.completed_operations += 1
                else:
                    error_msg = result.get("error", "Upload failed")
                    self.storage.update_operation_status(
                        operation.operation_id, "failed", error_msg
                    )
                    session.failed_operations += 1

            batch.status = SyncStatus.COMPLETED

        except Exception as e:
            batch.status = SyncStatus.FAILED
            batch.error_message = str(e)
            raise

    async def _download_changes(
        self, session: SyncSession, config: EntitySyncConfig, force_full_sync: bool
    ) -> None:
        """Download changes from server."""
        session.status = SyncStatus.DOWNLOADING

        # Get last sync timestamp
        last_sync_key = f"last_sync_{config.entity_type}"
        last_sync = (
            self.storage.get_metadata(last_sync_key) if not force_full_sync else None
        )

        try:
            # Request changes from server
            download_params = {
                "entity_type": config.entity_type,
                "since": last_sync,
                "limit": config.batch_size,
                "filters": json.dumps(config.filters) if config.filters else None,
            }

            response = await self.sdk.http_client.get(
                "mobile-erp/sync/download",
                params={
                    **download_params,
                    "organization_id": self.sdk.config.organization_id,
                },
            )

            if response["status"] != 200:
                raise NetworkError(
                    f"Download failed: {response.get('data', {}).get('message', 'Unknown error')}"
                )

            # Process downloaded data
            download_data = response["data"]
            changes = download_data.get("changes", [])

            if not changes:
                return

            session.status = SyncStatus.APPLYING

            # Apply changes
            conflicts_detected = 0
            for change in changes:
                try:
                    await self._apply_server_change(change, config)
                    session.completed_operations += 1
                except ConflictError as e:
                    conflicts_detected += 1
                    # Handle conflict based on strategy
                    if config.conflict_resolution == ConflictResolution.MANUAL:
                        # Store conflict for manual resolution
                        self.storage.set_metadata(
                            f"conflict_{config.entity_type}_{change['entity_id']}",
                            e.conflict_data,
                        )
                    else:
                        # Auto-resolve conflict
                        resolved_data = self.conflict_resolver.resolve_conflict(
                            config.entity_type,
                            e.conflict_data["client_data"],
                            e.conflict_data["server_data"],
                            config.conflict_resolution,
                        )

                        self.storage.store_entity(
                            config.entity_type,
                            change["entity_id"],
                            resolved_data,
                            change.get("version", 1),
                        )
                        session.completed_operations += 1

                except Exception as e:
                    print(f"[SDK] Failed to apply change: {e}")
                    session.failed_operations += 1

            session.conflicts_detected += conflicts_detected

            # Update last sync timestamp
            if download_data.get("sync_timestamp"):
                self.storage.set_metadata(
                    last_sync_key, download_data["sync_timestamp"]
                )

        except Exception as e:
            raise NetworkError(f"Download failed: {str(e)}")

    async def _apply_server_change(
        self, change: Dict[str, Any], config: EntitySyncConfig
    ) -> None:
        """Apply server change to local storage."""
        entity_type = change["entity_type"]
        entity_id = change["entity_id"]
        operation_type = change["operation_type"]
        server_data = change["data"]
        server_version = change.get("version", 1)

        if operation_type == "delete":
            self.storage.delete_entity(entity_type, entity_id)
            return

        # Check for existing local data
        existing_entity = self.storage.get_entity(entity_type, entity_id)

        if existing_entity and not change.get("force_overwrite", False):
            # Check for conflicts
            if existing_entity["version"] != server_version:
                # Version conflict detected
                raise ConflictError(
                    {
                        "entity_type": entity_type,
                        "entity_id": entity_id,
                        "client_data": existing_entity["data"],
                        "server_data": server_data,
                        "client_version": existing_entity["version"],
                        "server_version": server_version,
                    }
                )

        # Apply change
        self.storage.store_entity(entity_type, entity_id, server_data, server_version)

    async def _background_sync_loop(self) -> None:
        """Background synchronization loop."""
        while True:
            try:
                # Wait for next sync interval
                min_interval = (
                    min(
                        config.sync_frequency_minutes
                        for config in self._entity_configs.values()
                    )
                    if self._entity_configs
                    else 15
                )

                await asyncio.sleep(min_interval * 60)

                # Check if we should sync
                if self.sdk.is_authenticated() and not self._sync_active:
                    try:
                        await self.sync_now()
                    except Exception as e:
                        print(f"[SDK] Background sync failed: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[SDK] Background sync loop error: {e}")
                await asyncio.sleep(60)  # Wait before retrying


class ConflictError(Exception):
    """Exception raised when data conflicts are detected."""

    def __init__(self, conflict_data: Dict[str, Any]) -> dict:
        self.conflict_data = conflict_data
        super().__init__(
            f"Data conflict for {conflict_data['entity_type']}:{conflict_data['entity_id']}"
        )


class DataSyncModule:
    """Main data synchronization module for SDK."""

    def __init__(self, sdk: MobileERPSDK, storage_path: str = "offline_storage.db") -> dict:
        self.sdk = sdk
        self.storage = OfflineStorage(storage_path)
        self.sync_engine = SyncEngine(sdk, self.storage)

        # Register default entity configurations
        self._register_default_configs()

    def _register_default_configs(self) -> None:
        """Register default synchronization configurations."""
        default_configs = [
            EntitySyncConfig(
                entity_type="tasks",
                sync_direction=SyncDirection.BIDIRECTIONAL,
                conflict_resolution=ConflictResolution.LAST_MODIFIED,
                priority=SyncPriority.HIGH,
                sync_frequency_minutes=5,
            ),
            EntitySyncConfig(
                entity_type="documents",
                sync_direction=SyncDirection.BIDIRECTIONAL,
                conflict_resolution=ConflictResolution.SERVER_WINS,
                priority=SyncPriority.NORMAL,
                sync_frequency_minutes=15,
            ),
            EntitySyncConfig(
                entity_type="notifications",
                sync_direction=SyncDirection.DOWNLOAD,
                conflict_resolution=ConflictResolution.SERVER_WINS,
                priority=SyncPriority.HIGH,
                sync_frequency_minutes=1,
            ),
        ]

        for config in default_configs:
            self.sync_engine.register_entity_config(config)

    async def initialize(self) -> None:
        """Initialize synchronization module."""
        # Start background sync
        await self.sync_engine.start_background_sync()

        # Register event handlers
        self.sdk.events.on("network.connected", self._on_network_connected)
        self.sdk.events.on("auth.success", self._on_auth_success)

    async def _on_network_connected(self) -> None:
        """Handle network connected event."""
        if self.sdk.is_authenticated():
            try:
                await self.sync_engine.sync_now()
            except Exception as e:
                print(f"[SDK] Auto-sync on network connect failed: {e}")

    async def _on_auth_success(self, token: Any) -> None:
        """Handle successful authentication event."""
        try:
            await self.sync_engine.sync_now()
        except Exception as e:
            print(f"[SDK] Auto-sync on auth success failed: {e}")

    def configure_entity_sync(self, config: EntitySyncConfig) -> None:
        """Configure entity synchronization."""
        self.sync_engine.register_entity_config(config)

    async def sync_now(
        self, entity_types: Optional[List[str]] = None, force_full_sync: bool = False
    ) -> SyncSession:
        """Trigger immediate synchronization."""
        return await self.sync_engine.sync_now(entity_types, force_full_sync)

    def add_progress_listener(self, listener: Callable[[Dict[str, Any]], None]) -> None:
        """Add synchronization progress listener."""
        self.sync_engine.progress_tracker.add_listener(listener)

    def get_offline_data(
        self,
        entity_type: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get offline data."""
        return self.storage.list_entities(entity_type, filters, limit, offset)

    def store_offline_data(
        self, entity_type: str, entity_id: str, data: Dict[str, Any]
    ) -> None:
        """Store data for offline use."""
        # Create sync operation for later upload
        operation = SyncOperation(
            operation_id=f"offline_{entity_type}_{entity_id}_{int(time.time() * 1000)}",
            entity_type=entity_type,
            entity_id=entity_id,
            operation_type="update",
            data=data,
            timestamp=datetime.now(),
            client_version=1,
        )

        # Store data locally
        self.storage.store_entity(entity_type, entity_id, data)

        # Queue for sync
        self.storage.store_sync_operation(operation)

    def delete_offline_data(self, entity_type: str, entity_id: str) -> None:
        """Delete offline data."""
        # Create delete operation for later sync
        operation = SyncOperation(
            operation_id=f"delete_{entity_type}_{entity_id}_{int(time.time() * 1000)}",
            entity_type=entity_type,
            entity_id=entity_id,
            operation_type="delete",
            data={},
            timestamp=datetime.now(),
            client_version=1,
        )

        # Mark as deleted locally
        self.storage.delete_entity(entity_type, entity_id)

        # Queue for sync
        self.storage.store_sync_operation(operation)

    def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status."""
        storage_info = self.storage.get_storage_info()

        return {
            "sync_active": self.sync_engine._sync_active,
            "last_sync": self.storage.get_metadata("last_sync_timestamp"),
            "storage_info": storage_info,
            "pending_operations": storage_info["pending_operations"],
            "offline_entities": storage_info["entity_count"],
        }

    def cleanup_storage(self, retention_days: int = 30) -> Dict[str, Any]:
        """Clean up old offline data."""
        deleted_count = self.storage.cleanup_old_data(retention_days)

        return {
            "deleted_entities": deleted_count,
            "retention_days": retention_days,
            "cleanup_completed_at": datetime.now().isoformat(),
        }

    async def close(self) -> None:
        """Close synchronization module."""
        await self.sync_engine.stop_background_sync()
        self.storage.close()
