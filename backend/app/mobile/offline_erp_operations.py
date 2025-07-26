"""Offline-First ERP Operations System - CC02 v73.0 Day 18."""

from __future__ import annotations

import asyncio
import json
import sqlite3
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from pydantic import BaseModel, Field

from ..sdk.mobile_sdk_core import MobileERPSDK
from ..sdk.mobile_sdk_sync import ConflictResolutionStrategy, SyncEngine
from .enterprise_auth_system import EnterpriseAuthenticationSystem


class OperationType(str, Enum):
    """ERP operation types."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    REJECT = "reject"
    SUBMIT = "submit"
    CANCEL = "cancel"


class EntityType(str, Enum):
    """ERP entity types."""
    INVOICE = "invoice"
    PURCHASE_ORDER = "purchase_order"
    EMPLOYEE = "employee"
    CUSTOMER = "customer"
    VENDOR = "vendor"
    PRODUCT = "product"
    PROJECT = "project"
    TASK = "task"
    EXPENSE = "expense"
    TIMESHEET = "timesheet"
    ASSET = "asset"
    CONTRACT = "contract"


class OperationStatus(str, Enum):
    """Operation execution status."""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SYNCED = "synced"


class PriorityLevel(str, Enum):
    """Operation priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class OfflineOperation(BaseModel):
    """Offline ERP operation."""
    operation_id: str
    entity_type: EntityType
    entity_id: str
    operation_type: OperationType
    
    # Operation data
    data: Dict[str, Any] = Field(default_factory=dict)
    previous_data: Optional[Dict[str, Any]] = None
    
    # Metadata
    user_id: str
    session_id: str
    device_id: str
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    synced_at: Optional[datetime] = None
    
    # Status and priority
    status: OperationStatus = OperationStatus.PENDING
    priority: PriorityLevel = PriorityLevel.NORMAL
    
    # Dependencies
    depends_on: List[str] = Field(default_factory=list)
    blocks: List[str] = Field(default_factory=list)
    
    # Conflict resolution
    conflict_resolution_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.CLIENT_WINS
    
    # Error handling
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    
    # Validation
    validation_rules: List[str] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)


class EntitySchema(BaseModel):
    """Schema definition for ERP entities."""
    entity_type: EntityType
    version: str = "1.0"
    
    # Field definitions
    fields: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    required_fields: Set[str] = Field(default_factory=set)
    
    # Validation rules
    validation_rules: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Business rules
    business_rules: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Relationships
    relationships: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Indexing
    indexed_fields: Set[str] = Field(default_factory=set)
    full_text_fields: Set[str] = Field(default_factory=set)


class OfflineCache(BaseModel):
    """Offline data cache entry."""
    cache_key: str
    entity_type: EntityType
    entity_id: str
    
    # Data
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Cache management
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    accessed_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    # Sync information
    server_version: Optional[str] = None
    last_synced: Optional[datetime] = None
    sync_required: bool = False
    
    # Access patterns
    access_count: int = 0
    access_frequency: float = 0.0  # accesses per hour


class BusinessRule(BaseModel):
    """Business rule definition."""
    rule_id: str
    name: str
    description: str
    entity_type: EntityType
    
    # Rule definition
    condition: Dict[str, Any] = Field(default_factory=dict)
    action: Dict[str, Any] = Field(default_factory=dict)
    
    # Rule metadata
    priority: int = 100
    enabled: bool = True
    
    # Execution context
    execution_context: Set[str] = Field(default_factory=set)  # offline, online, both
    
    # Dependencies
    depends_on_rules: List[str] = Field(default_factory=list)


class OfflineStorageEngine:
    """Local storage engine for offline operations."""
    
    def __init__(self, storage_path: str = "offline_erp.db"):
        self.storage_path = storage_path
        self.connection: Optional[sqlite3.Connection] = None
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Initialize SQLite database for offline storage."""
        self.connection = sqlite3.connect(self.storage_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        
        # Create tables
        self._create_tables()
        self._create_indexes()
    
    def _create_tables(self) -> None:
        """Create database tables."""
        cursor = self.connection.cursor()
        
        # Operations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operations (
                operation_id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                data TEXT NOT NULL,
                previous_data TEXT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                device_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                executed_at TEXT,
                synced_at TEXT,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                depends_on TEXT,
                blocks TEXT,
                conflict_resolution_strategy TEXT NOT NULL,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                error_message TEXT,
                validation_rules TEXT,
                validation_errors TEXT
            )
        """)
        
        # Cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                cache_key TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                data TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                accessed_at TEXT NOT NULL,
                expires_at TEXT,
                server_version TEXT,
                last_synced TEXT,
                sync_required INTEGER DEFAULT 0,
                access_count INTEGER DEFAULT 0,
                access_frequency REAL DEFAULT 0.0
            )
        """)
        
        # Schemas table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entity_schemas (
                entity_type TEXT PRIMARY KEY,
                version TEXT NOT NULL,
                schema_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Business rules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS business_rules (
                rule_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                entity_type TEXT NOT NULL,
                rule_data TEXT NOT NULL,
                priority INTEGER DEFAULT 100,
                enabled INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        self.connection.commit()
    
    def _create_indexes(self) -> None:
        """Create database indexes for performance."""
        cursor = self.connection.cursor()
        
        # Operations indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_operations_entity ON operations(entity_type, entity_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_operations_user ON operations(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_operations_status ON operations(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_operations_created ON operations(created_at)")
        
        # Cache indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_entity ON cache(entity_type, entity_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_accessed ON cache(accessed_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_sync ON cache(sync_required)")
        
        # Business rules indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rules_entity ON business_rules(entity_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rules_enabled ON business_rules(enabled)")
        
        self.connection.commit()
    
    async def store_operation(self, operation: OfflineOperation) -> None:
        """Store offline operation."""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO operations (
                operation_id, entity_type, entity_id, operation_type,
                data, previous_data, user_id, session_id, device_id,
                created_at, executed_at, synced_at, status, priority,
                depends_on, blocks, conflict_resolution_strategy,
                retry_count, max_retries, error_message,
                validation_rules, validation_errors
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            operation.operation_id,
            operation.entity_type,
            operation.entity_id,
            operation.operation_type,
            json.dumps(operation.data),
            json.dumps(operation.previous_data) if operation.previous_data else None,
            operation.user_id,
            operation.session_id,
            operation.device_id,
            operation.created_at.isoformat(),
            operation.executed_at.isoformat() if operation.executed_at else None,
            operation.synced_at.isoformat() if operation.synced_at else None,
            operation.status,
            operation.priority,
            json.dumps(operation.depends_on),
            json.dumps(operation.blocks),
            operation.conflict_resolution_strategy,
            operation.retry_count,
            operation.max_retries,
            operation.error_message,
            json.dumps(operation.validation_rules),
            json.dumps(operation.validation_errors)
        ))
        
        self.connection.commit()
    
    async def get_operation(self, operation_id: str) -> Optional[OfflineOperation]:
        """Get operation by ID."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM operations WHERE operation_id = ?", (operation_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return OfflineOperation(
            operation_id=row["operation_id"],
            entity_type=EntityType(row["entity_type"]),
            entity_id=row["entity_id"],
            operation_type=OperationType(row["operation_type"]),
            data=json.loads(row["data"]),
            previous_data=json.loads(row["previous_data"]) if row["previous_data"] else None,
            user_id=row["user_id"],
            session_id=row["session_id"],
            device_id=row["device_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            executed_at=datetime.fromisoformat(row["executed_at"]) if row["executed_at"] else None,
            synced_at=datetime.fromisoformat(row["synced_at"]) if row["synced_at"] else None,
            status=OperationStatus(row["status"]),
            priority=PriorityLevel(row["priority"]),
            depends_on=json.loads(row["depends_on"]),
            blocks=json.loads(row["blocks"]),
            conflict_resolution_strategy=ConflictResolutionStrategy(row["conflict_resolution_strategy"]),
            retry_count=row["retry_count"],
            max_retries=row["max_retries"],
            error_message=row["error_message"],
            validation_rules=json.loads(row["validation_rules"]),
            validation_errors=json.loads(row["validation_errors"])
        )
    
    async def get_pending_operations(
        self,
        entity_type: Optional[EntityType] = None,
        user_id: Optional[str] = None
    ) -> List[OfflineOperation]:
        """Get pending operations."""
        cursor = self.connection.cursor()
        
        query = "SELECT * FROM operations WHERE status = 'pending'"
        params = []
        
        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        query += " ORDER BY priority DESC, created_at ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        operations = []
        for row in rows:
            operation = await self.get_operation(row["operation_id"])
            if operation:
                operations.append(operation)
        
        return operations
    
    async def store_cache_entry(self, cache_entry: OfflineCache) -> None:
        """Store cache entry."""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO cache (
                cache_key, entity_type, entity_id, data, metadata,
                created_at, updated_at, accessed_at, expires_at,
                server_version, last_synced, sync_required,
                access_count, access_frequency
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cache_entry.cache_key,
            cache_entry.entity_type,
            cache_entry.entity_id,
            json.dumps(cache_entry.data),
            json.dumps(cache_entry.metadata),
            cache_entry.created_at.isoformat(),
            cache_entry.updated_at.isoformat(),
            cache_entry.accessed_at.isoformat(),
            cache_entry.expires_at.isoformat() if cache_entry.expires_at else None,
            cache_entry.server_version,
            cache_entry.last_synced.isoformat() if cache_entry.last_synced else None,
            1 if cache_entry.sync_required else 0,
            cache_entry.access_count,
            cache_entry.access_frequency
        ))
        
        self.connection.commit()
    
    async def get_cache_entry(self, cache_key: str) -> Optional[OfflineCache]:
        """Get cache entry by key."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM cache WHERE cache_key = ?", (cache_key,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        # Update access information
        access_count = row["access_count"] + 1
        access_frequency = self._calculate_access_frequency(
            access_count,
            datetime.fromisoformat(row["created_at"])
        )
        
        cursor.execute("""
            UPDATE cache SET accessed_at = ?, access_count = ?, access_frequency = ?
            WHERE cache_key = ?
        """, (datetime.now().isoformat(), access_count, access_frequency, cache_key))
        
        self.connection.commit()
        
        return OfflineCache(
            cache_key=row["cache_key"],
            entity_type=EntityType(row["entity_type"]),
            entity_id=row["entity_id"],
            data=json.loads(row["data"]),
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            accessed_at=datetime.now(),
            expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
            server_version=row["server_version"],
            last_synced=datetime.fromisoformat(row["last_synced"]) if row["last_synced"] else None,
            sync_required=bool(row["sync_required"]),
            access_count=access_count,
            access_frequency=access_frequency
        )
    
    def _calculate_access_frequency(self, access_count: int, created_at: datetime) -> float:
        """Calculate access frequency (accesses per hour)."""
        hours_since_creation = (datetime.now() - created_at).total_seconds() / 3600
        if hours_since_creation < 1:
            hours_since_creation = 1
        
        return access_count / hours_since_creation
    
    async def cleanup_expired_cache(self) -> int:
        """Clean up expired cache entries."""
        cursor = self.connection.cursor()
        
        # Delete expired entries
        cursor.execute("""
            DELETE FROM cache 
            WHERE expires_at IS NOT NULL AND expires_at < ?
        """, (datetime.now().isoformat(),))
        
        deleted_count = cursor.rowcount
        self.connection.commit()
        
        return deleted_count


class BusinessRuleEngine:
    """Business rule evaluation engine."""
    
    def __init__(self, storage_engine: OfflineStorageEngine):
        self.storage_engine = storage_engine
        self.rules: Dict[EntityType, List[BusinessRule]] = {}
        self._load_rules()
    
    def _load_rules(self) -> None:
        """Load business rules from storage."""
        # Setup default rules
        self._setup_default_rules()
    
    def _setup_default_rules(self) -> None:
        """Setup default business rules."""
        # Invoice validation rules
        invoice_rules = [
            BusinessRule(
                rule_id="invoice_amount_required",
                name="Invoice Amount Required",
                description="Invoice must have a valid amount greater than zero",
                entity_type=EntityType.INVOICE,
                condition={"field": "amount", "operator": "greater_than", "value": 0},
                action={"type": "validation_error", "message": "Invoice amount must be greater than zero"},
                execution_context={"offline", "online"}
            ),
            BusinessRule(
                rule_id="invoice_customer_required",
                name="Invoice Customer Required",
                description="Invoice must have a valid customer",
                entity_type=EntityType.INVOICE,
                condition={"field": "customer_id", "operator": "not_empty"},
                action={"type": "validation_error", "message": "Customer is required for invoice"},
                execution_context={"offline", "online"}
            )
        ]
        
        self.rules[EntityType.INVOICE] = invoice_rules
        
        # Purchase Order rules
        po_rules = [
            BusinessRule(
                rule_id="po_approval_threshold",
                name="PO Approval Threshold",
                description="Purchase orders over $10,000 require approval",
                entity_type=EntityType.PURCHASE_ORDER,
                condition={"field": "total_amount", "operator": "greater_than", "value": 10000},
                action={"type": "require_approval", "approval_level": "manager"},
                execution_context={"offline", "online"}
            )
        ]
        
        self.rules[EntityType.PURCHASE_ORDER] = po_rules
    
    async def evaluate_rules(
        self,
        entity_type: EntityType,
        entity_data: Dict[str, Any],
        operation_type: OperationType
    ) -> Tuple[bool, List[str]]:
        """Evaluate business rules for entity."""
        if entity_type not in self.rules:
            return True, []
        
        errors = []
        
        for rule in self.rules[entity_type]:
            if not rule.enabled:
                continue
            
            # Check execution context
            if "offline" not in rule.execution_context:
                continue
            
            # Evaluate condition
            condition_met = self._evaluate_condition(rule.condition, entity_data)
            
            if condition_met:
                # Execute action
                action_result = await self._execute_action(rule.action, entity_data, operation_type)
                if not action_result["success"]:
                    errors.append(action_result["message"])
        
        return len(errors) == 0, errors
    
    def _evaluate_condition(self, condition: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Evaluate rule condition."""
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")
        
        if not field or not operator:
            return False
        
        field_value = data.get(field)
        
        if operator == "equals":
            return field_value == value
        elif operator == "not_equals":
            return field_value != value
        elif operator == "greater_than":
            return isinstance(field_value, (int, float)) and field_value > value
        elif operator == "less_than":
            return isinstance(field_value, (int, float)) and field_value < value
        elif operator == "not_empty":
            return field_value is not None and str(field_value).strip() != ""
        elif operator == "empty":
            return field_value is None or str(field_value).strip() == ""
        elif operator == "in":
            return field_value in (value if isinstance(value, list) else [value])
        elif operator == "not_in":
            return field_value not in (value if isinstance(value, list) else [value])
        else:
            return False
    
    async def _execute_action(
        self,
        action: Dict[str, Any],
        data: Dict[str, Any],
        operation_type: OperationType
    ) -> Dict[str, Any]:
        """Execute rule action."""
        action_type = action.get("type")
        
        if action_type == "validation_error":
            return {
                "success": False,
                "message": action.get("message", "Validation failed")
            }
        elif action_type == "require_approval":
            # For offline operations, we can't get real-time approval
            # So we mark it as requiring sync before execution
            return {
                "success": True,
                "message": "Approval required - will be processed during sync",
                "requires_sync": True
            }
        elif action_type == "set_field":
            field = action.get("field")
            value = action.get("value")
            if field:
                data[field] = value
            return {"success": True, "message": "Field updated"}
        else:
            return {"success": True, "message": "No action required"}


class OfflineERPOperationManager:
    """Main offline ERP operations manager."""
    
    def __init__(
        self,
        sdk: MobileERPSDK,
        auth_system: EnterpriseAuthenticationSystem,
        storage_path: str = "offline_erp.db"
    ):
        self.sdk = sdk
        self.auth_system = auth_system
        
        # Core components
        self.storage_engine = OfflineStorageEngine(storage_path)
        self.business_rule_engine = BusinessRuleEngine(self.storage_engine)
        
        # Entity schemas
        self.entity_schemas: Dict[EntityType, EntitySchema] = {}
        self._setup_entity_schemas()
        
        # Operation queue
        self.operation_queue: List[OfflineOperation] = []
        self.processing_operations: Set[str] = set()
        
        # Sync integration
        self.sync_engine: Optional[SyncEngine] = None
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._start_background_tasks()
    
    def _setup_entity_schemas(self) -> None:
        """Setup entity schemas."""
        # Invoice schema
        invoice_schema = EntitySchema(
            entity_type=EntityType.INVOICE,
            fields={
                "invoice_id": {"type": "string", "required": True},
                "customer_id": {"type": "string", "required": True},
                "invoice_number": {"type": "string", "required": True},
                "invoice_date": {"type": "date", "required": True},
                "due_date": {"type": "date", "required": True},
                "amount": {"type": "decimal", "required": True, "min": 0},
                "tax_amount": {"type": "decimal", "required": False, "min": 0},
                "total_amount": {"type": "decimal", "required": True, "min": 0},
                "status": {"type": "string", "enum": ["draft", "sent", "paid", "overdue"]},
                "line_items": {"type": "array", "required": False}
            },
            required_fields={"invoice_id", "customer_id", "invoice_number", "amount"},
            indexed_fields={"invoice_id", "customer_id", "invoice_number", "status"},
            full_text_fields={"description", "notes"}
        )
        
        self.entity_schemas[EntityType.INVOICE] = invoice_schema
        
        # Purchase Order schema
        po_schema = EntitySchema(
            entity_type=EntityType.PURCHASE_ORDER,
            fields={
                "po_id": {"type": "string", "required": True},
                "vendor_id": {"type": "string", "required": True},
                "po_number": {"type": "string", "required": True},
                "po_date": {"type": "date", "required": True},
                "total_amount": {"type": "decimal", "required": True, "min": 0},
                "status": {"type": "string", "enum": ["draft", "approved", "sent", "received"]},
                "approval_required": {"type": "boolean", "default": False}
            },
            required_fields={"po_id", "vendor_id", "po_number", "total_amount"},
            indexed_fields={"po_id", "vendor_id", "po_number", "status"}
        )
        
        self.entity_schemas[EntityType.PURCHASE_ORDER] = po_schema
        
        # Employee schema
        employee_schema = EntitySchema(
            entity_type=EntityType.EMPLOYEE,
            fields={
                "employee_id": {"type": "string", "required": True},
                "first_name": {"type": "string", "required": True},
                "last_name": {"type": "string", "required": True},
                "email": {"type": "email", "required": True},
                "department": {"type": "string", "required": False},
                "position": {"type": "string", "required": False},
                "hire_date": {"type": "date", "required": True},
                "salary": {"type": "decimal", "required": False, "min": 0},
                "active": {"type": "boolean", "default": True}
            },
            required_fields={"employee_id", "first_name", "last_name", "email"},
            indexed_fields={"employee_id", "email", "department"},
            full_text_fields={"first_name", "last_name", "department", "position"}
        )
        
        self.entity_schemas[EntityType.EMPLOYEE] = employee_schema
    
    def _start_background_tasks(self) -> None:
        """Start background processing tasks."""
        # Operation processor
        task = asyncio.create_task(self._process_operations_loop())
        self._background_tasks.append(task)
        
        # Cache cleanup
        task = asyncio.create_task(self._cache_cleanup_loop())
        self._background_tasks.append(task)
        
        # Sync coordinator
        task = asyncio.create_task(self._sync_coordinator_loop())
        self._background_tasks.append(task)
    
    async def _process_operations_loop(self) -> None:
        """Background loop for processing operations."""
        while True:
            try:
                await self._process_pending_operations()
                await asyncio.sleep(1)  # Process every second
            except Exception as e:
                print(f"Error in operation processing loop: {e}")
                await asyncio.sleep(5)
    
    async def _cache_cleanup_loop(self) -> None:
        """Background loop for cache cleanup."""
        while True:
            try:
                deleted_count = await self.storage_engine.cleanup_expired_cache()
                if deleted_count > 0:
                    print(f"Cleaned up {deleted_count} expired cache entries")
                await asyncio.sleep(300)  # Cleanup every 5 minutes
            except Exception as e:
                print(f"Error in cache cleanup loop: {e}")
                await asyncio.sleep(300)
    
    async def _sync_coordinator_loop(self) -> None:
        """Background loop for sync coordination."""
        while True:
            try:
                if self.sync_engine:
                    # Check for operations that need syncing
                    sync_operations = await self._get_operations_needing_sync()
                    if sync_operations:
                        await self._coordinate_sync(sync_operations)
                
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                print(f"Error in sync coordination loop: {e}")
                await asyncio.sleep(60)
    
    async def create_operation(
        self,
        entity_type: EntityType,
        entity_id: str,
        operation_type: OperationType,
        data: Dict[str, Any],
        user_id: str,
        session_id: str,
        device_id: str,
        priority: PriorityLevel = PriorityLevel.NORMAL
    ) -> OfflineOperation:
        """Create new offline operation."""
        # Validate entity data
        validation_result = await self._validate_entity_data(entity_type, data, operation_type)
        
        # Create operation
        operation = OfflineOperation(
            operation_id=str(uuid.uuid4()),
            entity_type=entity_type,
            entity_id=entity_id,
            operation_type=operation_type,
            data=data,
            user_id=user_id,
            session_id=session_id,
            device_id=device_id,
            priority=priority,
            validation_errors=validation_result["errors"] if not validation_result["valid"] else []
        )
        
        # Store operation
        await self.storage_engine.store_operation(operation)
        
        # Add to processing queue
        self.operation_queue.append(operation)
        
        return operation
    
    async def _validate_entity_data(
        self,
        entity_type: EntityType,
        data: Dict[str, Any],
        operation_type: OperationType
    ) -> Dict[str, Any]:
        """Validate entity data against schema and business rules."""
        errors = []
        
        # Schema validation
        if entity_type in self.entity_schemas:
            schema = self.entity_schemas[entity_type]
            
            # Check required fields
            for field in schema.required_fields:
                if field not in data or data[field] is None:
                    errors.append(f"Required field '{field}' is missing")
            
            # Validate field types and constraints
            for field, field_config in schema.fields.items():
                if field in data:
                    field_errors = self._validate_field(field, data[field], field_config)
                    errors.extend(field_errors)
        
        # Business rule validation
        rules_valid, rule_errors = await self.business_rule_engine.evaluate_rules(
            entity_type, data, operation_type
        )
        errors.extend(rule_errors)
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    def _validate_field(self, field_name: str, value: Any, config: Dict[str, Any]) -> List[str]:
        """Validate individual field."""
        errors = []
        field_type = config.get("type")
        
        if field_type == "string":
            if not isinstance(value, str):
                errors.append(f"Field '{field_name}' must be a string")
            elif "min_length" in config and len(value) < config["min_length"]:
                errors.append(f"Field '{field_name}' must be at least {config['min_length']} characters")
            elif "max_length" in config and len(value) > config["max_length"]:
                errors.append(f"Field '{field_name}' must be at most {config['max_length']} characters")
        
        elif field_type == "decimal":
            if not isinstance(value, (int, float)):
                errors.append(f"Field '{field_name}' must be a number")
            elif "min" in config and value < config["min"]:
                errors.append(f"Field '{field_name}' must be at least {config['min']}")
            elif "max" in config and value > config["max"]:
                errors.append(f"Field '{field_name}' must be at most {config['max']}")
        
        elif field_type == "email":
            if not isinstance(value, str) or "@" not in value:
                errors.append(f"Field '{field_name}' must be a valid email address")
        
        elif field_type == "date":
            try:
                if isinstance(value, str):
                    datetime.fromisoformat(value.replace("Z", "+00:00"))
                elif not isinstance(value, datetime):
                    errors.append(f"Field '{field_name}' must be a valid date")
            except ValueError:
                errors.append(f"Field '{field_name}' must be a valid date format")
        
        elif field_type == "boolean":
            if not isinstance(value, bool):
                errors.append(f"Field '{field_name}' must be a boolean")
        
        # Enum validation
        if "enum" in config and value not in config["enum"]:
            errors.append(f"Field '{field_name}' must be one of: {', '.join(config['enum'])}")
        
        return errors
    
    async def _process_pending_operations(self) -> None:
        """Process pending operations in queue."""
        if not self.operation_queue:
            return
        
        # Get operations that can be processed (dependencies resolved)
        processable_operations = []
        for operation in self.operation_queue[:10]:  # Process up to 10 at a time
            if operation.operation_id not in self.processing_operations:
                if await self._can_process_operation(operation):
                    processable_operations.append(operation)
        
        # Process operations
        for operation in processable_operations:
            await self._process_operation(operation)
    
    async def _can_process_operation(self, operation: OfflineOperation) -> bool:
        """Check if operation can be processed (dependencies resolved)."""
        if not operation.depends_on:
            return True
        
        # Check if all dependencies are completed
        for dep_id in operation.depends_on:
            dep_operation = await self.storage_engine.get_operation(dep_id)
            if not dep_operation or dep_operation.status != OperationStatus.COMPLETED:
                return False
        
        return True
    
    async def _process_operation(self, operation: OfflineOperation) -> None:
        """Process individual operation."""
        self.processing_operations.add(operation.operation_id)
        
        try:
            # Update status
            operation.status = OperationStatus.EXECUTING
            operation.executed_at = datetime.now()
            await self.storage_engine.store_operation(operation)
            
            # Execute operation based on type
            success = await self._execute_operation(operation)
            
            if success:
                operation.status = OperationStatus.COMPLETED
                
                # Update cache if needed
                await self._update_cache_after_operation(operation)
                
                # Remove from queue
                if operation in self.operation_queue:
                    self.operation_queue.remove(operation)
            else:
                # Handle failure
                operation.retry_count += 1
                if operation.retry_count >= operation.max_retries:
                    operation.status = OperationStatus.FAILED
                    if operation in self.operation_queue:
                        self.operation_queue.remove(operation)
                else:
                    operation.status = OperationStatus.PENDING
            
            await self.storage_engine.store_operation(operation)
            
        except Exception as e:
            operation.status = OperationStatus.FAILED
            operation.error_message = str(e)
            await self.storage_engine.store_operation(operation)
            
            if operation in self.operation_queue:
                self.operation_queue.remove(operation)
        
        finally:
            self.processing_operations.discard(operation.operation_id)
    
    async def _execute_operation(self, operation: OfflineOperation) -> bool:
        """Execute the actual operation."""
        try:
            if operation.operation_type == OperationType.CREATE:
                return await self._execute_create_operation(operation)
            elif operation.operation_type == OperationType.UPDATE:
                return await self._execute_update_operation(operation)
            elif operation.operation_type == OperationType.DELETE:
                return await self._execute_delete_operation(operation)
            elif operation.operation_type in [OperationType.APPROVE, OperationType.REJECT]:
                return await self._execute_approval_operation(operation)
            else:
                # For other operations, just mark as successful for offline
                return True
        except Exception as e:
            operation.error_message = str(e)
            return False
    
    async def _execute_create_operation(self, operation: OfflineOperation) -> bool:
        """Execute create operation."""
        # For offline mode, we store in local cache
        cache_key = f"{operation.entity_type}_{operation.entity_id}"
        
        cache_entry = OfflineCache(
            cache_key=cache_key,
            entity_type=operation.entity_type,
            entity_id=operation.entity_id,
            data=operation.data,
            sync_required=True
        )
        
        await self.storage_engine.store_cache_entry(cache_entry)
        return True
    
    async def _execute_update_operation(self, operation: OfflineOperation) -> bool:
        """Execute update operation."""
        # Get existing data from cache
        cache_key = f"{operation.entity_type}_{operation.entity_id}"
        existing = await self.storage_engine.get_cache_entry(cache_key)
        
        if existing:
            # Store previous data for conflict resolution
            operation.previous_data = existing.data
            
            # Update with new data
            updated_data = {**existing.data, **operation.data}
            
            existing.data = updated_data
            existing.updated_at = datetime.now()
            existing.sync_required = True
            
            await self.storage_engine.store_cache_entry(existing)
        else:
            # Create new cache entry
            cache_entry = OfflineCache(
                cache_key=cache_key,
                entity_type=operation.entity_type,
                entity_id=operation.entity_id,
                data=operation.data,
                sync_required=True
            )
            
            await self.storage_engine.store_cache_entry(cache_entry)
        
        return True
    
    async def _execute_delete_operation(self, operation: OfflineOperation) -> bool:
        """Execute delete operation."""
        # Mark as deleted in cache (soft delete for sync)
        cache_key = f"{operation.entity_type}_{operation.entity_id}"
        existing = await self.storage_engine.get_cache_entry(cache_key)
        
        if existing:
            existing.data["_deleted"] = True
            existing.updated_at = datetime.now()
            existing.sync_required = True
            
            await self.storage_engine.store_cache_entry(existing)
        
        return True
    
    async def _execute_approval_operation(self, operation: OfflineOperation) -> bool:
        """Execute approval operation."""
        # For offline operations, we can only queue approval for sync
        # Update the entity status locally
        cache_key = f"{operation.entity_type}_{operation.entity_id}"
        existing = await self.storage_engine.get_cache_entry(cache_key)
        
        if existing:
            if operation.operation_type == OperationType.APPROVE:
                existing.data["status"] = "approved"
                existing.data["approved_by"] = operation.user_id
                existing.data["approved_at"] = datetime.now().isoformat()
            else:  # REJECT
                existing.data["status"] = "rejected"
                existing.data["rejected_by"] = operation.user_id
                existing.data["rejected_at"] = datetime.now().isoformat()
            
            existing.updated_at = datetime.now()
            existing.sync_required = True
            
            await self.storage_engine.store_cache_entry(existing)
        
        return True
    
    async def _update_cache_after_operation(self, operation: OfflineOperation) -> None:
        """Update cache after successful operation."""
        # Update access patterns and metadata
        cache_key = f"{operation.entity_type}_{operation.entity_id}"
        cache_entry = await self.storage_engine.get_cache_entry(cache_key)
        
        if cache_entry:
            # Update metadata
            cache_entry.metadata["last_operation"] = {
                "operation_id": operation.operation_id,
                "operation_type": operation.operation_type,
                "executed_at": operation.executed_at.isoformat() if operation.executed_at else None
            }
            
            await self.storage_engine.store_cache_entry(cache_entry)
    
    async def _get_operations_needing_sync(self) -> List[OfflineOperation]:
        """Get operations that need to be synced to server."""
        # Get completed operations that haven't been synced
        cursor = self.storage_engine.connection.cursor()
        cursor.execute("""
            SELECT operation_id FROM operations 
            WHERE status = 'completed' AND synced_at IS NULL
            ORDER BY priority DESC, created_at ASC
            LIMIT 50
        """)
        
        rows = cursor.fetchall()
        operations = []
        
        for row in rows:
            operation = await self.storage_engine.get_operation(row["operation_id"])
            if operation:
                operations.append(operation)
        
        return operations
    
    async def _coordinate_sync(self, operations: List[OfflineOperation]) -> None:
        """Coordinate synchronization of operations."""
        if not self.sync_engine:
            return
        
        # Group operations by entity type for efficient syncing
        grouped_operations = {}
        for operation in operations:
            entity_type = operation.entity_type
            if entity_type not in grouped_operations:
                grouped_operations[entity_type] = []
            grouped_operations[entity_type].append(operation)
        
        # Sync each group
        for entity_type, entity_operations in grouped_operations.items():
            try:
                await self._sync_entity_operations(entity_type, entity_operations)
            except Exception as e:
                print(f"Error syncing {entity_type} operations: {e}")
    
    async def _sync_entity_operations(
        self,
        entity_type: EntityType,
        operations: List[OfflineOperation]
    ) -> None:
        """Sync operations for specific entity type."""
        # This would integrate with the actual sync engine
        # For now, we'll mark operations as synced
        
        for operation in operations:
            try:
                # Mock sync success
                operation.status = OperationStatus.SYNCED
                operation.synced_at = datetime.now()
                
                await self.storage_engine.store_operation(operation)
                
                # Update cache sync status
                cache_key = f"{operation.entity_type}_{operation.entity_id}"
                cache_entry = await self.storage_engine.get_cache_entry(cache_key)
                if cache_entry:
                    cache_entry.sync_required = False
                    cache_entry.last_synced = datetime.now()
                    await self.storage_engine.store_cache_entry(cache_entry)
                
            except Exception as e:
                print(f"Error syncing operation {operation.operation_id}: {e}")
    
    async def get_entity(self, entity_type: EntityType, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity data from offline cache."""
        cache_key = f"{entity_type}_{entity_id}"
        cache_entry = await self.storage_engine.get_cache_entry(cache_key)
        
        if not cache_entry:
            return None
        
        # Check if deleted
        if cache_entry.data.get("_deleted"):
            return None
        
        return cache_entry.data
    
    async def search_entities(
        self,
        entity_type: EntityType,
        filters: Dict[str, Any] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search entities in offline cache."""
        cursor = self.storage_engine.connection.cursor()
        
        query = "SELECT * FROM cache WHERE entity_type = ?"
        params = [entity_type]
        
        if filters:
            # Simple filtering (in real implementation, would be more sophisticated)
            for field, value in filters.items():
                query += f" AND json_extract(data, '$.{field}') = ?"
                params.append(value)
        
        query += f" LIMIT {limit}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        entities = []
        for row in rows:
            data = json.loads(row["data"])
            if not data.get("_deleted"):
                entities.append(data)
        
        return entities
    
    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get operation status."""
        # This would be implemented with proper async handling
        # For now, return a mock status
        return {
            "operation_id": operation_id,
            "status": "completed",
            "created_at": datetime.now().isoformat(),
            "executed_at": datetime.now().isoformat()
        }
    
    def get_offline_statistics(self) -> Dict[str, Any]:
        """Get offline operation statistics."""
        cursor = self.storage_engine.connection.cursor()
        
        # Get operation counts by status
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM operations 
            GROUP BY status
        """)
        status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}
        
        # Get cache statistics
        cursor.execute("SELECT COUNT(*) as count FROM cache")
        cache_count = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM cache WHERE sync_required = 1")
        pending_sync_count = cursor.fetchone()["count"]
        
        return {
            "operations": {
                "total": sum(status_counts.values()),
                "by_status": status_counts,
                "pending": status_counts.get("pending", 0),
                "completed": status_counts.get("completed", 0),
                "failed": status_counts.get("failed", 0)
            },
            "cache": {
                "total_entries": cache_count,
                "pending_sync": pending_sync_count,
                "sync_progress": round(
                    (cache_count - pending_sync_count) / cache_count * 100, 1
                ) if cache_count > 0 else 100
            },
            "queue_size": len(self.operation_queue),
            "processing_count": len(self.processing_operations)
        }