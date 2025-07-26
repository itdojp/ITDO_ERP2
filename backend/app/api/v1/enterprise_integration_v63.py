"""
CC02 v63.0 Day 8: Enterprise Integration Patterns & Message Queues
Advanced ERP system with enterprise integration patterns, message queues, and event-driven architecture
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import redis
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field

from app.core.exceptions import BusinessLogicError, NotFoundError

# Router setup
router = APIRouter(
    prefix="/api/v1/enterprise-integration-v63", tags=["Enterprise Integration v63"]
)

# Redis connection for message queue
redis_client = redis.Redis(host="localhost", port=6379, db=2, decode_responses=True)


# Enums
class MessageType(str, Enum):
    COMMAND = "command"
    EVENT = "event"
    QUERY = "query"
    REPLY = "reply"


class QueueType(str, Enum):
    DIRECT = "direct"
    TOPIC = "topic"
    FANOUT = "fanout"
    HEADERS = "headers"


class MessagePriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"


class IntegrationPattern(str, Enum):
    MESSAGE_CHANNEL = "message_channel"
    MESSAGE_ENDPOINT = "message_endpoint"
    MESSAGE_ROUTER = "message_router"
    MESSAGE_TRANSLATOR = "message_translator"
    MESSAGE_FILTER = "message_filter"
    AGGREGATOR = "aggregator"
    SPLITTER = "splitter"
    RESEQUENCER = "resequencer"
    SCATTER_GATHER = "scatter_gather"
    SAGA_ORCHESTRATOR = "saga_orchestrator"


class SagaStatus(str, Enum):
    STARTED = "started"
    PROCESSING = "processing"
    COMPENSATING = "compensating"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"


# Request/Response Models
class MessageRequest(BaseModel):
    message_id: Optional[UUID] = Field(default_factory=uuid4)
    message_type: MessageType
    queue_name: str = Field(..., min_length=1, max_length=100)
    payload: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    correlation_id: Optional[UUID] = None
    reply_to: Optional[str] = None
    expiration_ms: Optional[int] = Field(None, ge=1000, le=3600000)  # 1s to 1h
    headers: Dict[str, str] = Field(default_factory=dict)
    routing_key: Optional[str] = None


class QueueConfiguration(BaseModel):
    queue_name: str = Field(..., min_length=1, max_length=100)
    queue_type: QueueType
    durable: bool = True
    auto_delete: bool = False
    max_length: Optional[int] = Field(None, ge=1, le=1000000)
    message_ttl_ms: Optional[int] = Field(None, ge=1000, le=86400000)  # 1s to 1d
    dead_letter_queue: Optional[str] = None
    retry_limit: int = Field(3, ge=0, le=10)
    routing_patterns: List[str] = Field(default_factory=list)
    consumer_prefetch: int = Field(10, ge=1, le=1000)


class IntegrationPatternRequest(BaseModel):
    pattern_id: UUID = Field(default_factory=uuid4)
    pattern_type: IntegrationPattern
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    configuration: Dict[str, Any]
    source_endpoints: List[str]
    target_endpoints: List[str]
    transformation_rules: Optional[Dict[str, Any]] = None
    filtering_criteria: Optional[Dict[str, Any]] = None
    enabled: bool = True


class SagaDefinition(BaseModel):
    saga_id: UUID = Field(default_factory=uuid4)
    saga_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    steps: List[Dict[str, Any]]
    compensation_steps: List[Dict[str, Any]]
    timeout_seconds: int = Field(300, ge=30, le=3600)  # 30s to 1h
    retry_policy: Dict[str, Any] = Field(default_factory=dict)
    failure_policy: str = Field("compensate", regex="^(compensate|retry|abort)$")


class MessageResponse(BaseModel):
    message_id: UUID
    status: ProcessingStatus
    queue_name: str
    processed_at: Optional[datetime] = None
    processing_time_ms: Optional[int] = None
    error_details: Optional[str] = None
    retry_count: int = 0
    next_retry_at: Optional[datetime] = None


class QueueMetrics(BaseModel):
    queue_name: str
    total_messages: int
    pending_messages: int
    processing_messages: int
    completed_messages: int
    failed_messages: int
    dead_letter_messages: int
    average_processing_time_ms: float
    throughput_per_second: float
    error_rate_percent: float
    last_activity: Optional[datetime] = None


class IntegrationPatternResponse(BaseModel):
    pattern_id: UUID
    pattern_type: IntegrationPattern
    name: str
    status: str
    messages_processed: int
    average_latency_ms: float
    error_count: int
    last_execution: Optional[datetime] = None
    configuration: Dict[str, Any]


class SagaExecutionResponse(BaseModel):
    saga_id: UUID
    execution_id: UUID
    saga_name: str
    status: SagaStatus
    current_step: int
    total_steps: int
    started_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    compensation_steps_executed: List[int] = Field(default_factory=list)
    error_details: Optional[str] = None
    execution_context: Dict[str, Any] = Field(default_factory=dict)


# Core Components
class MessageQueue:
    """High-performance message queue with Redis backend"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.queues: Dict[str, QueueConfiguration] = {}

    async def create_queue(self, config: QueueConfiguration) -> Dict[str, Any]:
        """Create a new message queue with configuration"""
        try:
            # Store queue configuration
            queue_key = f"queue:config:{config.queue_name}"
            queue_data = config.dict()

            self.redis.hset(
                queue_key,
                mapping={
                    k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                    for k, v in queue_data.items()
                },
            )

            # Initialize queue metrics
            metrics_key = f"queue:metrics:{config.queue_name}"
            self.redis.hset(
                metrics_key,
                mapping={
                    "total_messages": 0,
                    "pending_messages": 0,
                    "processing_messages": 0,
                    "completed_messages": 0,
                    "failed_messages": 0,
                    "dead_letter_messages": 0,
                    "created_at": datetime.utcnow().isoformat(),
                },
            )

            # Set up dead letter queue if specified
            if config.dead_letter_queue:
                dlq_config = QueueConfiguration(
                    queue_name=config.dead_letter_queue,
                    queue_type=QueueType.DIRECT,
                    durable=True,
                    auto_delete=False,
                )
                await self._ensure_dlq_exists(dlq_config)

            self.queues[config.queue_name] = config

            return {
                "queue_name": config.queue_name,
                "status": "created",
                "configuration": queue_data,
            }

        except Exception as e:
            raise BusinessLogicError(f"Failed to create queue: {str(e)}")

    async def send_message(self, request: MessageRequest) -> MessageResponse:
        """Send message to queue with priority and routing"""
        try:
            start_time = datetime.utcnow()

            # Validate queue exists
            if request.queue_name not in self.queues:
                await self._load_queue_config(request.queue_name)

            # Prepare message data
            message_data = {
                "message_id": str(request.message_id),
                "message_type": request.message_type,
                "payload": json.dumps(request.payload),
                "priority": request.priority,
                "correlation_id": str(request.correlation_id)
                if request.correlation_id
                else None,
                "reply_to": request.reply_to,
                "headers": json.dumps(request.headers),
                "routing_key": request.routing_key,
                "created_at": start_time.isoformat(),
                "status": ProcessingStatus.PENDING,
                "retry_count": 0,
            }

            # Set expiration if specified
            if request.expiration_ms:
                expires_at = start_time + timedelta(milliseconds=request.expiration_ms)
                message_data["expires_at"] = expires_at.isoformat()

            # Store message
            message_key = f"message:{request.message_id}"
            self.redis.hset(message_key, mapping=message_data)

            # Add to priority queue
            priority_score = self._get_priority_score(request.priority)
            queue_key = f"queue:pending:{request.queue_name}"
            self.redis.zadd(queue_key, {str(request.message_id): priority_score})

            # Update metrics
            await self._update_queue_metrics(request.queue_name, "message_sent")

            processing_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            return MessageResponse(
                message_id=request.message_id,
                status=ProcessingStatus.PENDING,
                queue_name=request.queue_name,
                processed_at=start_time,
                processing_time_ms=processing_time,
            )

        except Exception as e:
            raise BusinessLogicError(f"Failed to send message: {str(e)}")

    async def receive_message(
        self, queue_name: str, consumer_id: str
    ) -> Optional[MessageResponse]:
        """Receive message from queue for processing"""
        try:
            # Get highest priority pending message
            queue_key = f"queue:pending:{queue_name}"
            message_ids = self.redis.zrevrange(queue_key, 0, 0)

            if not message_ids:
                return None

            message_id = message_ids[0]

            # Move to processing
            self.redis.zrem(queue_key, message_id)
            processing_key = f"queue:processing:{queue_name}"
            self.redis.zadd(processing_key, {message_id: datetime.utcnow().timestamp()})

            # Update message status
            message_key = f"message:{message_id}"
            message_data = self.redis.hgetall(message_key)

            if not message_data:
                return None

            # Update status and consumer
            self.redis.hset(
                message_key,
                mapping={
                    "status": ProcessingStatus.PROCESSING,
                    "consumer_id": consumer_id,
                    "processing_started_at": datetime.utcnow().isoformat(),
                },
            )

            # Update metrics
            await self._update_queue_metrics(queue_name, "message_received")

            return MessageResponse(
                message_id=UUID(message_id),
                status=ProcessingStatus.PROCESSING,
                queue_name=queue_name,
                processed_at=datetime.fromisoformat(message_data["created_at"]),
                retry_count=int(message_data.get("retry_count", 0)),
            )

        except Exception as e:
            raise BusinessLogicError(f"Failed to receive message: {str(e)}")

    async def complete_message(
        self, message_id: UUID, queue_name: str
    ) -> Dict[str, Any]:
        """Mark message as completed"""
        try:
            # Remove from processing queue
            processing_key = f"queue:processing:{queue_name}"
            self.redis.zrem(processing_key, str(message_id))

            # Update message status
            message_key = f"message:{message_id}"
            self.redis.hset(
                message_key,
                mapping={
                    "status": ProcessingStatus.COMPLETED,
                    "completed_at": datetime.utcnow().isoformat(),
                },
            )

            # Update metrics
            await self._update_queue_metrics(queue_name, "message_completed")

            return {"message_id": str(message_id), "status": "completed"}

        except Exception as e:
            raise BusinessLogicError(f"Failed to complete message: {str(e)}")

    async def fail_message(
        self, message_id: UUID, queue_name: str, error: str
    ) -> Dict[str, Any]:
        """Handle message failure with retry logic"""
        try:
            message_key = f"message:{message_id}"
            message_data = self.redis.hgetall(message_key)

            if not message_data:
                raise NotFoundError(f"Message {message_id} not found")

            retry_count = int(message_data.get("retry_count", 0))
            queue_config = self.queues.get(queue_name)
            max_retries = queue_config.retry_limit if queue_config else 3

            # Remove from processing
            processing_key = f"queue:processing:{queue_name}"
            self.redis.zrem(processing_key, str(message_id))

            if retry_count < max_retries:
                # Schedule retry
                retry_count += 1
                next_retry = datetime.utcnow() + timedelta(
                    seconds=min(60 * (2**retry_count), 3600)
                )

                self.redis.hset(
                    message_key,
                    mapping={
                        "status": ProcessingStatus.RETRYING,
                        "retry_count": retry_count,
                        "error_details": error,
                        "next_retry_at": next_retry.isoformat(),
                    },
                )

                # Schedule retry
                retry_key = f"queue:retry:{queue_name}"
                self.redis.zadd(retry_key, {str(message_id): next_retry.timestamp()})

                await self._update_queue_metrics(queue_name, "message_retry")

                return {
                    "message_id": str(message_id),
                    "status": "retrying",
                    "retry_count": retry_count,
                    "next_retry_at": next_retry.isoformat(),
                }
            else:
                # Send to dead letter queue
                self.redis.hset(
                    message_key,
                    mapping={
                        "status": ProcessingStatus.DEAD_LETTER,
                        "error_details": error,
                        "dead_letter_at": datetime.utcnow().isoformat(),
                    },
                )

                if queue_config and queue_config.dead_letter_queue:
                    dlq_key = f"queue:pending:{queue_config.dead_letter_queue}"
                    self.redis.zadd(
                        dlq_key, {str(message_id): datetime.utcnow().timestamp()}
                    )

                await self._update_queue_metrics(queue_name, "message_dead_letter")

                return {
                    "message_id": str(message_id),
                    "status": "dead_letter",
                    "error": error,
                }

        except Exception as e:
            raise BusinessLogicError(f"Failed to handle message failure: {str(e)}")

    async def get_queue_metrics(self, queue_name: str) -> QueueMetrics:
        """Get comprehensive queue metrics"""
        try:
            metrics_key = f"queue:metrics:{queue_name}"
            metrics_data = self.redis.hgetall(metrics_key)

            if not metrics_data:
                raise NotFoundError(f"Queue {queue_name} not found")

            # Get current queue lengths
            pending_count = self.redis.zcard(f"queue:pending:{queue_name}")
            processing_count = self.redis.zcard(f"queue:processing:{queue_name}")
            retry_count = self.redis.zcard(f"queue:retry:{queue_name}")

            # Calculate rates
            total_messages = int(metrics_data.get("total_messages", 0))
            completed_messages = int(metrics_data.get("completed_messages", 0))
            failed_messages = int(metrics_data.get("failed_messages", 0))

            error_rate = (failed_messages / max(total_messages, 1)) * 100

            return QueueMetrics(
                queue_name=queue_name,
                total_messages=total_messages,
                pending_messages=pending_count,
                processing_messages=processing_count,
                completed_messages=completed_messages,
                failed_messages=failed_messages,
                dead_letter_messages=int(metrics_data.get("dead_letter_messages", 0)),
                average_processing_time_ms=float(
                    metrics_data.get("avg_processing_time_ms", 0)
                ),
                throughput_per_second=float(
                    metrics_data.get("throughput_per_second", 0)
                ),
                error_rate_percent=error_rate,
                last_activity=datetime.fromisoformat(metrics_data["created_at"])
                if "created_at" in metrics_data
                else None,
            )

        except Exception as e:
            raise BusinessLogicError(f"Failed to get queue metrics: {str(e)}")

    def _get_priority_score(self, priority: MessagePriority) -> float:
        """Convert priority to numeric score for ordering"""
        priority_scores = {
            MessagePriority.LOW: 1.0,
            MessagePriority.NORMAL: 2.0,
            MessagePriority.HIGH: 3.0,
            MessagePriority.CRITICAL: 4.0,
        }
        return priority_scores.get(priority, 2.0)

    async def _load_queue_config(self, queue_name: str) -> None:
        """Load queue configuration from Redis"""
        queue_key = f"queue:config:{queue_name}"
        config_data = self.redis.hgetall(queue_key)

        if not config_data:
            raise NotFoundError(f"Queue {queue_name} not found")

        # Parse configuration
        config_dict = {}
        for key, value in config_data.items():
            try:
                config_dict[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                config_dict[key] = value

        self.queues[queue_name] = QueueConfiguration(**config_dict)

    async def _ensure_dlq_exists(self, dlq_config: QueueConfiguration) -> None:
        """Ensure dead letter queue exists"""
        if dlq_config.queue_name not in self.queues:
            await self.create_queue(dlq_config)

    async def _update_queue_metrics(self, queue_name: str, metric_type: str) -> None:
        """Update queue metrics"""
        metrics_key = f"queue:metrics:{queue_name}"

        # Increment appropriate counter
        if metric_type == "message_sent":
            self.redis.hincrby(metrics_key, "total_messages", 1)
            self.redis.hincrby(metrics_key, "pending_messages", 1)
        elif metric_type == "message_received":
            self.redis.hincrby(metrics_key, "pending_messages", -1)
            self.redis.hincrby(metrics_key, "processing_messages", 1)
        elif metric_type == "message_completed":
            self.redis.hincrby(metrics_key, "processing_messages", -1)
            self.redis.hincrby(metrics_key, "completed_messages", 1)
        elif metric_type == "message_retry":
            self.redis.hincrby(metrics_key, "processing_messages", -1)
        elif metric_type == "message_dead_letter":
            self.redis.hincrby(metrics_key, "dead_letter_messages", 1)
            self.redis.hincrby(metrics_key, "failed_messages", 1)


class IntegrationPatternEngine:
    """Enterprise Integration Patterns implementation"""

    def __init__(self, message_queue: MessageQueue):
        self.message_queue = message_queue
        self.patterns: Dict[UUID, IntegrationPatternRequest] = {}
        self.active_processors: Dict[UUID, asyncio.Task] = {}

    async def create_pattern(
        self, request: IntegrationPatternRequest
    ) -> IntegrationPatternResponse:
        """Create and activate integration pattern"""
        try:
            # Store pattern configuration
            pattern_key = f"pattern:config:{request.pattern_id}"
            pattern_data = request.dict()

            redis_client.hset(
                pattern_key,
                mapping={
                    k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                    for k, v in pattern_data.items()
                },
            )

            # Initialize pattern metrics
            metrics_key = f"pattern:metrics:{request.pattern_id}"
            redis_client.hset(
                metrics_key,
                mapping={
                    "messages_processed": 0,
                    "error_count": 0,
                    "total_latency_ms": 0,
                    "created_at": datetime.utcnow().isoformat(),
                    "last_execution": datetime.utcnow().isoformat(),
                },
            )

            self.patterns[request.pattern_id] = request

            # Start pattern processor if enabled
            if request.enabled:
                await self._start_pattern_processor(request.pattern_id)

            return IntegrationPatternResponse(
                pattern_id=request.pattern_id,
                pattern_type=request.pattern_type,
                name=request.name,
                status="active" if request.enabled else "inactive",
                messages_processed=0,
                average_latency_ms=0.0,
                error_count=0,
                last_execution=datetime.utcnow(),
                configuration=request.configuration,
            )

        except Exception as e:
            raise BusinessLogicError(f"Failed to create integration pattern: {str(e)}")

    async def process_message_with_pattern(
        self, pattern_id: UUID, message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process message through integration pattern"""
        try:
            pattern = self.patterns.get(pattern_id)
            if not pattern:
                await self._load_pattern_config(pattern_id)
                pattern = self.patterns[pattern_id]

            start_time = datetime.utcnow()

            # Apply pattern-specific processing
            result = await self._apply_pattern_logic(pattern, message)

            # Update metrics
            processing_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )
            await self._update_pattern_metrics(
                pattern_id, processing_time, success=True
            )

            return result

        except Exception as e:
            await self._update_pattern_metrics(pattern_id, 0, success=False)
            raise BusinessLogicError(f"Pattern processing failed: {str(e)}")

    async def _apply_pattern_logic(
        self, pattern: IntegrationPatternRequest, message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply specific integration pattern logic"""

        if pattern.pattern_type == IntegrationPattern.MESSAGE_FILTER:
            return await self._apply_message_filter(pattern, message)
        elif pattern.pattern_type == IntegrationPattern.MESSAGE_TRANSLATOR:
            return await self._apply_message_translator(pattern, message)
        elif pattern.pattern_type == IntegrationPattern.MESSAGE_ROUTER:
            return await self._apply_message_router(pattern, message)
        elif pattern.pattern_type == IntegrationPattern.SPLITTER:
            return await self._apply_splitter(pattern, message)
        elif pattern.pattern_type == IntegrationPattern.AGGREGATOR:
            return await self._apply_aggregator(pattern, message)
        elif pattern.pattern_type == IntegrationPattern.SCATTER_GATHER:
            return await self._apply_scatter_gather(pattern, message)
        else:
            # Default passthrough
            return {"processed": True, "message": message}

    async def _apply_message_filter(
        self, pattern: IntegrationPatternRequest, message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply message filtering logic"""
        criteria = pattern.filtering_criteria or {}

        # Simple filtering logic
        for field, expected_value in criteria.items():
            if field in message and message[field] != expected_value:
                return {
                    "filtered": True,
                    "reason": f"Field {field} does not match criteria",
                }

        return {"filtered": False, "message": message}

    async def _apply_message_translator(
        self, pattern: IntegrationPatternRequest, message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply message transformation logic"""
        transformation_rules = pattern.transformation_rules or {}
        translated_message = message.copy()

        # Apply field mappings
        field_mappings = transformation_rules.get("field_mappings", {})
        for source_field, target_field in field_mappings.items():
            if source_field in translated_message:
                translated_message[target_field] = translated_message.pop(source_field)

        # Apply value transformations
        value_transformations = transformation_rules.get("value_transformations", {})
        for field, transformation in value_transformations.items():
            if field in translated_message:
                if transformation["type"] == "multiply":
                    translated_message[field] = (
                        float(translated_message[field]) * transformation["factor"]
                    )
                elif transformation["type"] == "format":
                    translated_message[field] = transformation["format"].format(
                        translated_message[field]
                    )

        return {"translated": True, "message": translated_message}

    async def _apply_message_router(
        self, pattern: IntegrationPatternRequest, message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply message routing logic"""
        routing_rules = pattern.configuration.get("routing_rules", [])

        for rule in routing_rules:
            condition_field = rule.get("condition_field")
            condition_value = rule.get("condition_value")
            target_endpoint = rule.get("target_endpoint")

            if (
                condition_field in message
                and message[condition_field] == condition_value
            ):
                # Route to specific endpoint
                return {
                    "routed": True,
                    "target_endpoint": target_endpoint,
                    "message": message,
                }

        # Default routing
        default_endpoint = pattern.configuration.get("default_endpoint")
        return {
            "routed": True,
            "target_endpoint": default_endpoint or pattern.target_endpoints[0],
            "message": message,
        }

    async def _apply_splitter(
        self, pattern: IntegrationPatternRequest, message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply message splitting logic"""
        split_config = pattern.configuration.get("split_config", {})
        split_field = split_config.get("field")

        if split_field and split_field in message:
            items = message[split_field]
            if isinstance(items, list):
                split_messages = []
                for i, item in enumerate(items):
                    split_message = message.copy()
                    split_message[split_field] = item
                    split_message["_split_index"] = i
                    split_message["_split_total"] = len(items)
                    split_messages.append(split_message)

                return {"split": True, "messages": split_messages}

        return {"split": False, "message": message}

    async def _apply_aggregator(
        self, pattern: IntegrationPatternRequest, message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply message aggregation logic"""
        aggregation_key = f"aggregator:{pattern.pattern_id}"
        correlation_field = pattern.configuration.get(
            "correlation_field", "correlation_id"
        )

        if correlation_field in message:
            correlation_id = message[correlation_field]
            group_key = f"{aggregation_key}:{correlation_id}"

            # Add message to aggregation group
            redis_client.lpush(group_key, json.dumps(message))
            redis_client.expire(group_key, 300)  # 5 minute timeout

            # Check if aggregation is complete
            expected_count = pattern.configuration.get("expected_count", 1)
            current_count = redis_client.llen(group_key)

            if current_count >= expected_count:
                # Retrieve all messages and aggregate
                raw_messages = redis_client.lrange(group_key, 0, -1)
                messages = [json.loads(msg) for msg in raw_messages]

                # Simple aggregation - combine payloads
                aggregated_payload = {}
                for msg in messages:
                    if "payload" in msg:
                        aggregated_payload.update(msg["payload"])

                # Clean up
                redis_client.delete(group_key)

                return {
                    "aggregated": True,
                    "message_count": len(messages),
                    "payload": aggregated_payload,
                }

        return {"aggregated": False, "waiting": True}

    async def _apply_scatter_gather(
        self, pattern: IntegrationPatternRequest, message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply scatter-gather pattern"""
        scatter_endpoints = pattern.target_endpoints
        gather_timeout = pattern.configuration.get("gather_timeout_seconds", 30)

        # Scatter - send to all endpoints
        scatter_id = str(uuid4())
        scatter_key = f"scatter:{pattern.pattern_id}:{scatter_id}"

        responses = {}
        for endpoint in scatter_endpoints:
            # Simulate sending to endpoint
            response = await self._simulate_endpoint_call(endpoint, message)
            responses[endpoint] = response

        # Gather - collect responses
        return {
            "scattered": True,
            "gathered": True,
            "scatter_id": scatter_id,
            "responses": responses,
            "endpoint_count": len(scatter_endpoints),
        }

    async def _simulate_endpoint_call(
        self, endpoint: str, message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate calling an endpoint"""
        # In real implementation, this would make HTTP calls
        return {
            "endpoint": endpoint,
            "status": "success",
            "response_time_ms": 50,
            "data": {"processed": True},
        }

    async def _start_pattern_processor(self, pattern_id: UUID) -> None:
        """Start background processor for pattern"""
        if pattern_id not in self.active_processors:
            task = asyncio.create_task(self._pattern_processor_loop(pattern_id))
            self.active_processors[pattern_id] = task

    async def _pattern_processor_loop(self, pattern_id: UUID) -> None:
        """Background processing loop for pattern"""
        try:
            while True:
                pattern = self.patterns.get(pattern_id)
                if not pattern or not pattern.enabled:
                    break

                # Process messages from source endpoints
                for endpoint in pattern.source_endpoints:
                    # In real implementation, this would consume from actual endpoints
                    await asyncio.sleep(1)  # Prevent tight loop

                await asyncio.sleep(5)  # Processing interval

        except asyncio.CancelledError:
            pass
        finally:
            if pattern_id in self.active_processors:
                del self.active_processors[pattern_id]

    async def _load_pattern_config(self, pattern_id: UUID) -> None:
        """Load pattern configuration from Redis"""
        pattern_key = f"pattern:config:{pattern_id}"
        config_data = redis_client.hgetall(pattern_key)

        if not config_data:
            raise NotFoundError(f"Pattern {pattern_id} not found")

        # Parse configuration
        config_dict = {}
        for key, value in config_data.items():
            try:
                config_dict[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                config_dict[key] = value

        self.patterns[pattern_id] = IntegrationPatternRequest(**config_dict)

    async def _update_pattern_metrics(
        self, pattern_id: UUID, processing_time_ms: int, success: bool
    ) -> None:
        """Update pattern execution metrics"""
        metrics_key = f"pattern:metrics:{pattern_id}"

        if success:
            redis_client.hincrby(metrics_key, "messages_processed", 1)
            redis_client.hincrby(metrics_key, "total_latency_ms", processing_time_ms)
        else:
            redis_client.hincrby(metrics_key, "error_count", 1)

        redis_client.hset(metrics_key, "last_execution", datetime.utcnow().isoformat())


class SagaOrchestrator:
    """SAGA pattern implementation for distributed transactions"""

    def __init__(self, message_queue: MessageQueue):
        self.message_queue = message_queue
        self.sagas: Dict[UUID, SagaDefinition] = {}
        self.executions: Dict[UUID, Dict[str, Any]] = {}

    async def define_saga(self, definition: SagaDefinition) -> Dict[str, Any]:
        """Define a new SAGA workflow"""
        try:
            # Store saga definition
            saga_key = f"saga:definition:{definition.saga_id}"
            saga_data = definition.dict()

            redis_client.hset(
                saga_key,
                mapping={
                    k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                    for k, v in saga_data.items()
                },
            )

            self.sagas[definition.saga_id] = definition

            return {
                "saga_id": str(definition.saga_id),
                "saga_name": definition.saga_name,
                "step_count": len(definition.steps),
                "compensation_step_count": len(definition.compensation_steps),
                "status": "defined",
            }

        except Exception as e:
            raise BusinessLogicError(f"Failed to define saga: {str(e)}")

    async def execute_saga(
        self, saga_id: UUID, initial_context: Dict[str, Any]
    ) -> SagaExecutionResponse:
        """Start saga execution"""
        try:
            saga = self.sagas.get(saga_id)
            if not saga:
                await self._load_saga_definition(saga_id)
                saga = self.sagas[saga_id]

            execution_id = uuid4()
            execution_context = {
                "saga_id": str(saga_id),
                "execution_id": str(execution_id),
                "saga_name": saga.saga_name,
                "status": SagaStatus.STARTED,
                "current_step": 0,
                "total_steps": len(saga.steps),
                "started_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "execution_context": initial_context,
                "completed_steps": [],
                "compensation_steps_executed": [],
            }

            # Store execution state
            execution_key = f"saga:execution:{execution_id}"
            redis_client.hset(
                execution_key,
                mapping={
                    k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                    for k, v in execution_context.items()
                },
            )

            self.executions[execution_id] = execution_context

            # Start execution
            await self._execute_saga_step(execution_id, 0)

            return SagaExecutionResponse(
                saga_id=saga_id,
                execution_id=execution_id,
                saga_name=saga.saga_name,
                status=SagaStatus.STARTED,
                current_step=0,
                total_steps=len(saga.steps),
                started_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                execution_context=initial_context,
            )

        except Exception as e:
            raise BusinessLogicError(f"Failed to execute saga: {str(e)}")

    async def _execute_saga_step(self, execution_id: UUID, step_index: int) -> None:
        """Execute a single saga step"""
        try:
            execution = self.executions.get(execution_id)
            if not execution:
                await self._load_saga_execution(execution_id)
                execution = self.executions[execution_id]

            saga_id = UUID(execution["saga_id"])
            saga = self.sagas[saga_id]

            if step_index >= len(saga.steps):
                # All steps completed
                await self._complete_saga(execution_id)
                return

            step = saga.steps[step_index]

            # Update execution status
            await self._update_execution_status(
                execution_id,
                {
                    "status": SagaStatus.PROCESSING,
                    "current_step": step_index,
                    "updated_at": datetime.utcnow().isoformat(),
                },
            )

            # Execute step
            try:
                step_result = await self._execute_step_action(
                    step, execution["execution_context"]
                )

                # Step succeeded, move to next
                execution["completed_steps"].append(step_index)
                execution["execution_context"].update(
                    step_result.get("context_updates", {})
                )

                await self._update_execution_context(
                    execution_id, execution["execution_context"]
                )
                await self._execute_saga_step(execution_id, step_index + 1)

            except Exception as step_error:
                # Step failed, start compensation
                await self._start_compensation(
                    execution_id, step_index, str(step_error)
                )

        except Exception as e:
            await self._fail_saga(execution_id, str(e))

    async def _execute_step_action(
        self, step: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute individual step action"""
        action_type = step.get("action_type")

        if action_type == "http_call":
            return await self._execute_http_call_step(step, context)
        elif action_type == "database_operation":
            return await self._execute_database_step(step, context)
        elif action_type == "message_send":
            return await self._execute_message_step(step, context)
        else:
            # Default simulation
            return {"success": True, "context_updates": {"step_completed": True}}

    async def _execute_http_call_step(
        self, step: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute HTTP call step"""
        # Simulate HTTP call
        endpoint = step.get("endpoint", "http://localhost/api")
        method = step.get("method", "POST")

        # In real implementation, would make actual HTTP call
        return {
            "success": True,
            "response_status": 200,
            "context_updates": {
                f"step_{step.get('name', 'unknown')}_completed": True,
                "http_response": {"status": "success"},
            },
        }

    async def _execute_database_step(
        self, step: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute database operation step"""
        operation = step.get("operation", "insert")
        table = step.get("table", "default")

        # Simulate database operation
        return {
            "success": True,
            "context_updates": {f"db_{operation}_completed": True, "affected_rows": 1},
        }

    async def _execute_message_step(
        self, step: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute message sending step"""
        queue_name = step.get("queue_name", "default")
        message_payload = step.get("payload", {})

        # Send message through message queue
        message_request = MessageRequest(
            message_type=MessageType.COMMAND,
            queue_name=queue_name,
            payload=message_payload,
            priority=MessagePriority.HIGH,
        )

        response = await self.message_queue.send_message(message_request)

        return {
            "success": True,
            "context_updates": {
                "message_sent": True,
                "message_id": str(response.message_id),
            },
        }

    async def _start_compensation(
        self, execution_id: UUID, failed_step_index: int, error: str
    ) -> None:
        """Start saga compensation"""
        try:
            execution = self.executions[execution_id]
            saga_id = UUID(execution["saga_id"])
            saga = self.sagas[saga_id]

            await self._update_execution_status(
                execution_id,
                {
                    "status": SagaStatus.COMPENSATING,
                    "error_details": error,
                    "updated_at": datetime.utcnow().isoformat(),
                },
            )

            # Execute compensation steps in reverse order
            completed_steps = execution.get("completed_steps", [])
            for step_index in reversed(completed_steps):
                if step_index < len(saga.compensation_steps):
                    compensation_step = saga.compensation_steps[step_index]
                    await self._execute_compensation_step(
                        execution_id, step_index, compensation_step
                    )

            await self._complete_compensation(execution_id)

        except Exception as e:
            await self._fail_saga(execution_id, f"Compensation failed: {str(e)}")

    async def _execute_compensation_step(
        self, execution_id: UUID, step_index: int, compensation_step: Dict[str, Any]
    ) -> None:
        """Execute compensation step"""
        try:
            execution = self.executions[execution_id]

            # Execute compensation action
            result = await self._execute_step_action(
                compensation_step, execution["execution_context"]
            )

            # Track compensation
            if "compensation_steps_executed" not in execution:
                execution["compensation_steps_executed"] = []
            execution["compensation_steps_executed"].append(step_index)

            await self._update_execution_context(
                execution_id, execution["execution_context"]
            )

        except Exception:
            # Log compensation failure but continue
            pass

    async def _complete_saga(self, execution_id: UUID) -> None:
        """Complete saga execution successfully"""
        await self._update_execution_status(
            execution_id,
            {
                "status": SagaStatus.COMPLETED,
                "completed_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            },
        )

    async def _complete_compensation(self, execution_id: UUID) -> None:
        """Complete saga compensation"""
        await self._update_execution_status(
            execution_id,
            {
                "status": SagaStatus.COMPENSATED,
                "completed_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            },
        )

    async def _fail_saga(self, execution_id: UUID, error: str) -> None:
        """Mark saga as failed"""
        await self._update_execution_status(
            execution_id,
            {
                "status": SagaStatus.FAILED,
                "error_details": error,
                "completed_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            },
        )

    async def _update_execution_status(
        self, execution_id: UUID, updates: Dict[str, Any]
    ) -> None:
        """Update saga execution status"""
        execution_key = f"saga:execution:{execution_id}"

        redis_client.hset(
            execution_key,
            mapping={
                k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                for k, v in updates.items()
            },
        )

        if execution_id in self.executions:
            self.executions[execution_id].update(updates)

    async def _update_execution_context(
        self, execution_id: UUID, context: Dict[str, Any]
    ) -> None:
        """Update saga execution context"""
        execution_key = f"saga:execution:{execution_id}"
        redis_client.hset(execution_key, "execution_context", json.dumps(context))

        if execution_id in self.executions:
            self.executions[execution_id]["execution_context"] = context

    async def _load_saga_definition(self, saga_id: UUID) -> None:
        """Load saga definition from Redis"""
        saga_key = f"saga:definition:{saga_id}"
        saga_data = redis_client.hgetall(saga_key)

        if not saga_data:
            raise NotFoundError(f"Saga {saga_id} not found")

        # Parse configuration
        config_dict = {}
        for key, value in saga_data.items():
            try:
                config_dict[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                config_dict[key] = value

        self.sagas[saga_id] = SagaDefinition(**config_dict)

    async def _load_saga_execution(self, execution_id: UUID) -> None:
        """Load saga execution from Redis"""
        execution_key = f"saga:execution:{execution_id}"
        execution_data = redis_client.hgetall(execution_key)

        if not execution_data:
            raise NotFoundError(f"Saga execution {execution_id} not found")

        # Parse execution data
        execution_dict = {}
        for key, value in execution_data.items():
            try:
                execution_dict[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                execution_dict[key] = value

        self.executions[execution_id] = execution_dict


# Global instances
message_queue = MessageQueue(redis_client)
integration_engine = IntegrationPatternEngine(message_queue)
saga_orchestrator = SagaOrchestrator(message_queue)


# API Endpoints
@router.post("/message-queue/create", response_model=Dict[str, Any])
async def create_message_queue(
    config: QueueConfiguration, background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Create a new message queue with configuration"""
    return await message_queue.create_queue(config)


@router.post("/message-queue/send", response_model=MessageResponse)
async def send_message_to_queue(
    request: MessageRequest, background_tasks: BackgroundTasks
) -> MessageResponse:
    """Send message to queue"""
    return await message_queue.send_message(request)


@router.get(
    "/message-queue/{queue_name}/receive", response_model=Optional[MessageResponse]
)
async def receive_message_from_queue(
    queue_name: str, consumer_id: str = "default_consumer"
) -> Optional[MessageResponse]:
    """Receive message from queue"""
    return await message_queue.receive_message(queue_name, consumer_id)


@router.post("/message-queue/{queue_name}/complete/{message_id}")
async def complete_message_processing(
    queue_name: str, message_id: UUID
) -> Dict[str, Any]:
    """Mark message as completed"""
    return await message_queue.complete_message(message_id, queue_name)


@router.post("/message-queue/{queue_name}/fail/{message_id}")
async def fail_message_processing(
    queue_name: str, message_id: UUID, error: str
) -> Dict[str, Any]:
    """Handle message processing failure"""
    return await message_queue.fail_message(message_id, queue_name, error)


@router.get("/message-queue/{queue_name}/metrics", response_model=QueueMetrics)
async def get_queue_metrics(queue_name: str) -> QueueMetrics:
    """Get comprehensive queue metrics"""
    return await message_queue.get_queue_metrics(queue_name)


@router.post("/integration-patterns/create", response_model=IntegrationPatternResponse)
async def create_integration_pattern(
    request: IntegrationPatternRequest, background_tasks: BackgroundTasks
) -> IntegrationPatternResponse:
    """Create and activate integration pattern"""
    return await integration_engine.create_pattern(request)


@router.post("/integration-patterns/{pattern_id}/process")
async def process_message_with_integration_pattern(
    pattern_id: UUID, message: Dict[str, Any]
) -> Dict[str, Any]:
    """Process message through integration pattern"""
    return await integration_engine.process_message_with_pattern(pattern_id, message)


@router.post("/saga/define", response_model=Dict[str, Any])
async def define_saga_workflow(
    definition: SagaDefinition, background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Define a new SAGA workflow"""
    return await saga_orchestrator.define_saga(definition)


@router.post("/saga/{saga_id}/execute", response_model=SagaExecutionResponse)
async def execute_saga_workflow(
    saga_id: UUID, initial_context: Dict[str, Any], background_tasks: BackgroundTasks
) -> SagaExecutionResponse:
    """Start saga execution"""
    return await saga_orchestrator.execute_saga(saga_id, initial_context)


@router.get("/saga/execution/{execution_id}", response_model=SagaExecutionResponse)
async def get_saga_execution_status(execution_id: UUID) -> SagaExecutionResponse:
    """Get saga execution status"""
    execution_key = f"saga:execution:{execution_id}"
    execution_data = redis_client.hgetall(execution_key)

    if not execution_data:
        raise HTTPException(status_code=404, detail="Saga execution not found")

    # Parse execution data
    execution_dict = {}
    for key, value in execution_data.items():
        try:
            execution_dict[key] = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            execution_dict[key] = value

    return SagaExecutionResponse(
        saga_id=UUID(execution_dict["saga_id"]),
        execution_id=execution_id,
        saga_name=execution_dict["saga_name"],
        status=SagaStatus(execution_dict["status"]),
        current_step=int(execution_dict["current_step"]),
        total_steps=int(execution_dict["total_steps"]),
        started_at=datetime.fromisoformat(execution_dict["started_at"]),
        updated_at=datetime.fromisoformat(execution_dict["updated_at"]),
        completed_at=datetime.fromisoformat(execution_dict["completed_at"])
        if execution_dict.get("completed_at")
        else None,
        compensation_steps_executed=execution_dict.get(
            "compensation_steps_executed", []
        ),
        error_details=execution_dict.get("error_details"),
        execution_context=execution_dict.get("execution_context", {}),
    )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    try:
        # Test Redis connection
        redis_client.ping()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "message_queue": "operational",
                "integration_patterns": "operational",
                "saga_orchestrator": "operational",
                "redis": "connected",
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}",
        )
