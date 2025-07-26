"""
Tests for CC02 v63.0 Enterprise Integration Patterns & Message Queues
Comprehensive test suite covering message queues, integration patterns, and SAGA orchestration
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.api.v1.enterprise_integration_v63 import (
    IntegrationPattern,
    IntegrationPatternEngine,
    IntegrationPatternRequest,
    IntegrationPatternResponse,
    MessagePriority,
    MessageQueue,
    MessageRequest,
    MessageResponse,
    MessageType,
    ProcessingStatus,
    QueueConfiguration,
    QueueMetrics,
    QueueType,
    SagaDefinition,
    SagaExecutionResponse,
    SagaOrchestrator,
    SagaStatus,
)
from app.core.exceptions import BusinessLogicError, NotFoundError


# Test Fixtures
@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis_mock = MagicMock()
    redis_mock.ping.return_value = True
    redis_mock.hset.return_value = True
    redis_mock.hget.return_value = None
    redis_mock.hgetall.return_value = {}
    redis_mock.zadd.return_value = True
    redis_mock.zrevrange.return_value = []
    redis_mock.zrem.return_value = True
    redis_mock.zcard.return_value = 0
    redis_mock.hincrby.return_value = 1
    redis_mock.lpush.return_value = 1
    redis_mock.llen.return_value = 0
    redis_mock.lrange.return_value = []
    redis_mock.delete.return_value = True
    redis_mock.expire.return_value = True
    return redis_mock


@pytest.fixture
def message_queue_instance(mock_redis):
    """Create message queue instance with mocked Redis"""
    return MessageQueue(mock_redis)


@pytest.fixture
def integration_engine_instance(message_queue_instance):
    """Create integration engine instance"""
    return IntegrationPatternEngine(message_queue_instance)


@pytest.fixture
def saga_orchestrator_instance(message_queue_instance):
    """Create saga orchestrator instance"""
    return SagaOrchestrator(message_queue_instance)


@pytest.fixture
def sample_queue_config():
    """Sample queue configuration"""
    return QueueConfiguration(
        queue_name="test-queue",
        queue_type=QueueType.DIRECT,
        durable=True,
        auto_delete=False,
        max_length=1000,
        message_ttl_ms=3600000,
        dead_letter_queue="test-dlq",
        retry_limit=3,
        routing_patterns=["order.*", "payment.*"],
        consumer_prefetch=10,
    )


@pytest.fixture
def sample_message_request():
    """Sample message request"""
    return MessageRequest(
        message_type=MessageType.COMMAND,
        queue_name="test-queue",
        payload={"order_id": str(uuid4()), "action": "process_payment"},
        priority=MessagePriority.HIGH,
        correlation_id=uuid4(),
        reply_to="response-queue",
        expiration_ms=60000,
        headers={"source": "order-service", "version": "1.0"},
        routing_key="order.payment.process",
    )


@pytest.fixture
def sample_integration_pattern():
    """Sample integration pattern request"""
    return IntegrationPatternRequest(
        pattern_type=IntegrationPattern.MESSAGE_ROUTER,
        name="Order Router",
        description="Routes orders based on customer type",
        configuration={
            "routing_rules": [
                {
                    "condition_field": "customer_type",
                    "condition_value": "premium",
                    "target_endpoint": "premium-queue",
                },
                {
                    "condition_field": "customer_type",
                    "condition_value": "standard",
                    "target_endpoint": "standard-queue",
                },
            ],
            "default_endpoint": "default-queue",
        },
        source_endpoints=["incoming-orders"],
        target_endpoints=["premium-queue", "standard-queue", "default-queue"],
        enabled=True,
    )


@pytest.fixture
def sample_saga_definition():
    """Sample SAGA definition"""
    return SagaDefinition(
        saga_name="Order Processing Saga",
        description="Complete order processing workflow",
        steps=[
            {
                "name": "reserve_inventory",
                "action_type": "http_call",
                "endpoint": "http://inventory-service/reserve",
                "method": "POST",
            },
            {
                "name": "process_payment",
                "action_type": "http_call",
                "endpoint": "http://payment-service/charge",
                "method": "POST",
            },
            {
                "name": "create_shipment",
                "action_type": "message_send",
                "queue_name": "shipment-queue",
                "payload": {"action": "create_shipment"},
            },
        ],
        compensation_steps=[
            {
                "name": "cancel_shipment",
                "action_type": "message_send",
                "queue_name": "shipment-queue",
                "payload": {"action": "cancel_shipment"},
            },
            {
                "name": "refund_payment",
                "action_type": "http_call",
                "endpoint": "http://payment-service/refund",
                "method": "POST",
            },
            {
                "name": "release_inventory",
                "action_type": "http_call",
                "endpoint": "http://inventory-service/release",
                "method": "POST",
            },
        ],
        timeout_seconds=300,
        retry_policy={"max_retries": 3, "backoff_factor": 2},
        failure_policy="compensate",
    )


# Unit Tests for MessageQueue
class TestMessageQueue:
    @pytest.mark.asyncio
    async def test_create_queue_success(
        self, message_queue_instance, sample_queue_config, mock_redis
    ):
        """Test successful queue creation"""

        result = await message_queue_instance.create_queue(sample_queue_config)

        assert result["queue_name"] == "test-queue"
        assert result["status"] == "created"
        assert "configuration" in result

        # Verify Redis calls
        mock_redis.hset.assert_called()

        # Verify queue is stored in memory
        assert "test-queue" in message_queue_instance.queues

    @pytest.mark.asyncio
    async def test_create_queue_with_dlq(self, message_queue_instance, mock_redis):
        """Test queue creation with dead letter queue"""

        config = QueueConfiguration(
            queue_name="main-queue",
            queue_type=QueueType.DIRECT,
            dead_letter_queue="dlq-queue",
        )

        result = await message_queue_instance.create_queue(config)

        assert result["status"] == "created"
        mock_redis.hset.assert_called()

    @pytest.mark.asyncio
    async def test_send_message_success(
        self, message_queue_instance, sample_message_request, mock_redis
    ):
        """Test successful message sending"""

        # Setup queue
        config = QueueConfiguration(
            queue_name="test-queue", queue_type=QueueType.DIRECT
        )
        message_queue_instance.queues["test-queue"] = config

        result = await message_queue_instance.send_message(sample_message_request)

        assert isinstance(result, MessageResponse)
        assert result.message_id == sample_message_request.message_id
        assert result.status == ProcessingStatus.PENDING
        assert result.queue_name == "test-queue"
        assert result.processing_time_ms is not None

        # Verify Redis calls
        mock_redis.hset.assert_called()
        mock_redis.zadd.assert_called()

    @pytest.mark.asyncio
    async def test_send_message_with_expiration(
        self, message_queue_instance, mock_redis
    ):
        """Test message sending with expiration"""

        config = QueueConfiguration(
            queue_name="test-queue", queue_type=QueueType.DIRECT
        )
        message_queue_instance.queues["test-queue"] = config

        request = MessageRequest(
            message_type=MessageType.EVENT,
            queue_name="test-queue",
            payload={"test": "data"},
            expiration_ms=30000,
        )

        result = await message_queue_instance.send_message(request)

        assert result.status == ProcessingStatus.PENDING
        mock_redis.hset.assert_called()

    @pytest.mark.asyncio
    async def test_receive_message_success(self, message_queue_instance, mock_redis):
        """Test successful message receiving"""

        # Mock Redis to return a message
        message_id = str(uuid4())
        mock_redis.zrevrange.return_value = [message_id]
        mock_redis.hgetall.return_value = {
            "message_id": message_id,
            "message_type": "command",
            "payload": '{"test": "data"}',
            "created_at": datetime.utcnow().isoformat(),
            "retry_count": "0",
        }

        result = await message_queue_instance.receive_message(
            "test-queue", "consumer-1"
        )

        assert isinstance(result, MessageResponse)
        assert result.message_id == UUID(message_id)
        assert result.status == ProcessingStatus.PROCESSING
        assert result.retry_count == 0

        # Verify Redis operations
        mock_redis.zrem.assert_called()
        mock_redis.zadd.assert_called()
        mock_redis.hset.assert_called()

    @pytest.mark.asyncio
    async def test_receive_message_empty_queue(
        self, message_queue_instance, mock_redis
    ):
        """Test receiving from empty queue"""

        mock_redis.zrevrange.return_value = []

        result = await message_queue_instance.receive_message(
            "test-queue", "consumer-1"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_complete_message_success(self, message_queue_instance, mock_redis):
        """Test successful message completion"""

        message_id = uuid4()

        result = await message_queue_instance.complete_message(message_id, "test-queue")

        assert result["message_id"] == str(message_id)
        assert result["status"] == "completed"

        # Verify Redis operations
        mock_redis.zrem.assert_called()
        mock_redis.hset.assert_called()

    @pytest.mark.asyncio
    async def test_fail_message_with_retry(self, message_queue_instance, mock_redis):
        """Test message failure with retry"""

        message_id = uuid4()
        config = QueueConfiguration(
            queue_name="test-queue", queue_type=QueueType.DIRECT, retry_limit=3
        )
        message_queue_instance.queues["test-queue"] = config

        # Mock message data
        mock_redis.hgetall.return_value = {
            "message_id": str(message_id),
            "retry_count": "1",
        }

        result = await message_queue_instance.fail_message(
            message_id, "test-queue", "Processing error"
        )

        assert result["message_id"] == str(message_id)
        assert result["status"] == "retrying"
        assert result["retry_count"] == 2
        assert "next_retry_at" in result

        # Verify Redis operations
        mock_redis.hset.assert_called()
        mock_redis.zadd.assert_called()

    @pytest.mark.asyncio
    async def test_fail_message_to_dead_letter(
        self, message_queue_instance, mock_redis
    ):
        """Test message failure to dead letter queue"""

        message_id = uuid4()
        config = QueueConfiguration(
            queue_name="test-queue",
            queue_type=QueueType.DIRECT,
            retry_limit=3,
            dead_letter_queue="test-dlq",
        )
        message_queue_instance.queues["test-queue"] = config

        # Mock message with max retries exceeded
        mock_redis.hgetall.return_value = {
            "message_id": str(message_id),
            "retry_count": "3",
        }

        result = await message_queue_instance.fail_message(
            message_id, "test-queue", "Max retries exceeded"
        )

        assert result["message_id"] == str(message_id)
        assert result["status"] == "dead_letter"
        assert "error" in result

        # Verify dead letter queue operations
        mock_redis.hset.assert_called()

    @pytest.mark.asyncio
    async def test_get_queue_metrics(self, message_queue_instance, mock_redis):
        """Test getting queue metrics"""

        # Mock metrics data
        mock_redis.hgetall.return_value = {
            "total_messages": "100",
            "completed_messages": "80",
            "failed_messages": "5",
            "dead_letter_messages": "2",
            "avg_processing_time_ms": "150.5",
            "throughput_per_second": "10.2",
            "created_at": datetime.utcnow().isoformat(),
        }

        # Mock queue counts
        mock_redis.zcard.return_value = 10

        result = await message_queue_instance.get_queue_metrics("test-queue")

        assert isinstance(result, QueueMetrics)
        assert result.queue_name == "test-queue"
        assert result.total_messages == 100
        assert result.pending_messages == 10
        assert result.completed_messages == 80
        assert result.error_rate_percent == 5.0

    @pytest.mark.asyncio
    async def test_get_queue_metrics_not_found(
        self, message_queue_instance, mock_redis
    ):
        """Test getting metrics for non-existent queue"""

        mock_redis.hgetall.return_value = {}

        with pytest.raises(NotFoundError, match="Queue .* not found"):
            await message_queue_instance.get_queue_metrics("nonexistent-queue")

    def test_get_priority_score(self, message_queue_instance):
        """Test priority score calculation"""

        assert message_queue_instance._get_priority_score(MessagePriority.LOW) == 1.0
        assert message_queue_instance._get_priority_score(MessagePriority.NORMAL) == 2.0
        assert message_queue_instance._get_priority_score(MessagePriority.HIGH) == 3.0
        assert (
            message_queue_instance._get_priority_score(MessagePriority.CRITICAL) == 4.0
        )


# Unit Tests for IntegrationPatternEngine
class TestIntegrationPatternEngine:
    @pytest.mark.asyncio
    async def test_create_pattern_success(
        self, integration_engine_instance, sample_integration_pattern
    ):
        """Test successful integration pattern creation"""

        with patch("app.api.v1.enterprise_integration_v63.redis_client") as mock_redis:
            mock_redis.hset.return_value = True

            result = await integration_engine_instance.create_pattern(
                sample_integration_pattern
            )

            assert isinstance(result, IntegrationPatternResponse)
            assert result.pattern_id == sample_integration_pattern.pattern_id
            assert result.pattern_type == IntegrationPattern.MESSAGE_ROUTER
            assert result.name == "Order Router"
            assert result.status == "active"

            # Verify pattern is stored
            assert (
                sample_integration_pattern.pattern_id
                in integration_engine_instance.patterns
            )

    @pytest.mark.asyncio
    async def test_create_pattern_disabled(self, integration_engine_instance):
        """Test creating disabled integration pattern"""

        pattern = IntegrationPatternRequest(
            pattern_type=IntegrationPattern.MESSAGE_FILTER,
            name="Test Filter",
            configuration={"filter_field": "status"},
            source_endpoints=["input"],
            target_endpoints=["output"],
            enabled=False,
        )

        with patch("app.api.v1.enterprise_integration_v63.redis_client") as mock_redis:
            mock_redis.hset.return_value = True

            result = await integration_engine_instance.create_pattern(pattern)

            assert result.status == "inactive"

    @pytest.mark.asyncio
    async def test_process_message_with_filter_pattern(
        self, integration_engine_instance
    ):
        """Test message processing with filter pattern"""

        pattern = IntegrationPatternRequest(
            pattern_type=IntegrationPattern.MESSAGE_FILTER,
            name="Status Filter",
            configuration={},
            source_endpoints=["input"],
            target_endpoints=["output"],
            filtering_criteria={"status": "active"},
        )

        integration_engine_instance.patterns[pattern.pattern_id] = pattern

        # Test message that passes filter
        message = {"status": "active", "data": "test"}

        with patch.object(
            integration_engine_instance, "_update_pattern_metrics"
        ) as mock_metrics:
            result = await integration_engine_instance.process_message_with_pattern(
                pattern.pattern_id, message
            )

            assert result["filtered"] == False
            assert result["message"] == message
            mock_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_with_translator_pattern(
        self, integration_engine_instance
    ):
        """Test message processing with translator pattern"""

        pattern = IntegrationPatternRequest(
            pattern_type=IntegrationPattern.MESSAGE_TRANSLATOR,
            name="Field Mapper",
            configuration={},
            source_endpoints=["input"],
            target_endpoints=["output"],
            transformation_rules={
                "field_mappings": {"old_field": "new_field"},
                "value_transformations": {
                    "amount": {"type": "multiply", "factor": 1.1},
                    "name": {"type": "format", "format": "Mr. {}"},
                },
            },
        )

        integration_engine_instance.patterns[pattern.pattern_id] = pattern

        message = {"old_field": "value", "amount": 100, "name": "John"}

        with patch.object(integration_engine_instance, "_update_pattern_metrics"):
            result = await integration_engine_instance.process_message_with_pattern(
                pattern.pattern_id, message
            )

            assert result["translated"] == True
            translated_message = result["message"]
            assert "new_field" in translated_message
            assert "old_field" not in translated_message
            assert translated_message["amount"] == 110.0
            assert translated_message["name"] == "Mr. John"

    @pytest.mark.asyncio
    async def test_process_message_with_router_pattern(
        self, integration_engine_instance, sample_integration_pattern
    ):
        """Test message processing with router pattern"""

        integration_engine_instance.patterns[sample_integration_pattern.pattern_id] = (
            sample_integration_pattern
        )

        # Test premium customer routing
        message = {"customer_type": "premium", "order_id": "12345"}

        with patch.object(integration_engine_instance, "_update_pattern_metrics"):
            result = await integration_engine_instance.process_message_with_pattern(
                sample_integration_pattern.pattern_id, message
            )

            assert result["routed"] == True
            assert result["target_endpoint"] == "premium-queue"
            assert result["message"] == message

    @pytest.mark.asyncio
    async def test_process_message_with_splitter_pattern(
        self, integration_engine_instance
    ):
        """Test message processing with splitter pattern"""

        pattern = IntegrationPatternRequest(
            pattern_type=IntegrationPattern.SPLITTER,
            name="Order Items Splitter",
            configuration={"split_config": {"field": "items"}},
            source_endpoints=["input"],
            target_endpoints=["output"],
        )

        integration_engine_instance.patterns[pattern.pattern_id] = pattern

        message = {
            "order_id": "12345",
            "items": [{"id": 1, "name": "Item1"}, {"id": 2, "name": "Item2"}],
        }

        with patch.object(integration_engine_instance, "_update_pattern_metrics"):
            result = await integration_engine_instance.process_message_with_pattern(
                pattern.pattern_id, message
            )

            assert result["split"] == True
            assert len(result["messages"]) == 2
            assert result["messages"][0]["_split_index"] == 0
            assert result["messages"][1]["_split_index"] == 1

    @pytest.mark.asyncio
    async def test_process_message_with_aggregator_pattern(
        self, integration_engine_instance
    ):
        """Test message processing with aggregator pattern"""

        pattern = IntegrationPatternRequest(
            pattern_type=IntegrationPattern.AGGREGATOR,
            name="Payment Aggregator",
            configuration={"correlation_field": "transaction_id", "expected_count": 2},
            source_endpoints=["input"],
            target_endpoints=["output"],
        )

        integration_engine_instance.patterns[pattern.pattern_id] = pattern

        message = {"transaction_id": "tx123", "payload": {"payment": 100}}

        with patch("app.api.v1.enterprise_integration_v63.redis_client") as mock_redis:
            # Mock Redis list operations
            mock_redis.lpush.return_value = 1
            mock_redis.expire.return_value = True
            mock_redis.llen.return_value = 2  # Aggregation complete
            mock_redis.lrange.return_value = [
                json.dumps({"transaction_id": "tx123", "payload": {"payment": 100}}),
                json.dumps({"transaction_id": "tx123", "payload": {"fee": 5}}),
            ]
            mock_redis.delete.return_value = True

            with patch.object(integration_engine_instance, "_update_pattern_metrics"):
                result = await integration_engine_instance.process_message_with_pattern(
                    pattern.pattern_id, message
                )

                assert result["aggregated"] == True
                assert result["message_count"] == 2
                assert "payload" in result

    @pytest.mark.asyncio
    async def test_process_message_with_scatter_gather_pattern(
        self, integration_engine_instance
    ):
        """Test message processing with scatter-gather pattern"""

        pattern = IntegrationPatternRequest(
            pattern_type=IntegrationPattern.SCATTER_GATHER,
            name="Price Checker",
            configuration={"gather_timeout_seconds": 30},
            source_endpoints=["input"],
            target_endpoints=["service1", "service2", "service3"],
        )

        integration_engine_instance.patterns[pattern.pattern_id] = pattern

        message = {"product_id": "prod123"}

        with patch.object(integration_engine_instance, "_update_pattern_metrics"):
            with patch.object(
                integration_engine_instance, "_simulate_endpoint_call"
            ) as mock_call:
                mock_call.return_value = {"status": "success", "data": {"price": 100}}

                result = await integration_engine_instance.process_message_with_pattern(
                    pattern.pattern_id, message
                )

                assert result["scattered"] == True
                assert result["gathered"] == True
                assert result["endpoint_count"] == 3
                assert "responses" in result

    @pytest.mark.asyncio
    async def test_process_message_pattern_not_found(self, integration_engine_instance):
        """Test processing message with non-existent pattern"""

        with patch.object(
            integration_engine_instance, "_load_pattern_config"
        ) as mock_load:
            mock_load.side_effect = NotFoundError("Pattern not found")

            with pytest.raises(NotFoundError):
                await integration_engine_instance.process_message_with_pattern(
                    uuid4(), {"test": "data"}
                )

    @pytest.mark.asyncio
    async def test_process_message_with_error(
        self, integration_engine_instance, sample_integration_pattern
    ):
        """Test message processing with error"""

        integration_engine_instance.patterns[sample_integration_pattern.pattern_id] = (
            sample_integration_pattern
        )

        with patch.object(
            integration_engine_instance, "_apply_pattern_logic"
        ) as mock_apply:
            mock_apply.side_effect = Exception("Processing error")

            with patch.object(
                integration_engine_instance, "_update_pattern_metrics"
            ) as mock_metrics:
                with pytest.raises(
                    BusinessLogicError, match="Pattern processing failed"
                ):
                    await integration_engine_instance.process_message_with_pattern(
                        sample_integration_pattern.pattern_id, {"test": "data"}
                    )

                # Verify error metrics update
                mock_metrics.assert_called_with(
                    sample_integration_pattern.pattern_id, 0, success=False
                )


# Unit Tests for SagaOrchestrator
class TestSagaOrchestrator:
    @pytest.mark.asyncio
    async def test_define_saga_success(
        self, saga_orchestrator_instance, sample_saga_definition
    ):
        """Test successful SAGA definition"""

        with patch("app.api.v1.enterprise_integration_v63.redis_client") as mock_redis:
            mock_redis.hset.return_value = True

            result = await saga_orchestrator_instance.define_saga(
                sample_saga_definition
            )

            assert result["saga_id"] == str(sample_saga_definition.saga_id)
            assert result["saga_name"] == "Order Processing Saga"
            assert result["step_count"] == 3
            assert result["compensation_step_count"] == 3
            assert result["status"] == "defined"

            # Verify saga is stored
            assert sample_saga_definition.saga_id in saga_orchestrator_instance.sagas

    @pytest.mark.asyncio
    async def test_execute_saga_success(
        self, saga_orchestrator_instance, sample_saga_definition
    ):
        """Test successful SAGA execution start"""

        saga_orchestrator_instance.sagas[sample_saga_definition.saga_id] = (
            sample_saga_definition
        )

        initial_context = {"order_id": "12345", "customer_id": "cust456"}

        with patch("app.api.v1.enterprise_integration_v63.redis_client") as mock_redis:
            mock_redis.hset.return_value = True

            with patch.object(
                saga_orchestrator_instance, "_execute_saga_step"
            ) as mock_step:
                result = await saga_orchestrator_instance.execute_saga(
                    sample_saga_definition.saga_id, initial_context
                )

                assert isinstance(result, SagaExecutionResponse)
                assert result.saga_id == sample_saga_definition.saga_id
                assert result.saga_name == "Order Processing Saga"
                assert result.status == SagaStatus.STARTED
                assert result.current_step == 0
                assert result.total_steps == 3
                assert result.execution_context == initial_context

                # Verify step execution started
                mock_step.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_saga_not_found(self, saga_orchestrator_instance):
        """Test executing non-existent SAGA"""

        with patch.object(
            saga_orchestrator_instance, "_load_saga_definition"
        ) as mock_load:
            mock_load.side_effect = NotFoundError("Saga not found")

            with pytest.raises(NotFoundError):
                await saga_orchestrator_instance.execute_saga(uuid4(), {})

    @pytest.mark.asyncio
    async def test_execute_saga_step_success(
        self, saga_orchestrator_instance, sample_saga_definition
    ):
        """Test successful SAGA step execution"""

        execution_id = uuid4()
        execution_context = {
            "saga_id": str(sample_saga_definition.saga_id),
            "execution_id": str(execution_id),
            "saga_name": sample_saga_definition.saga_name,
            "status": SagaStatus.STARTED,
            "current_step": 0,
            "total_steps": 3,
            "execution_context": {"order_id": "12345"},
            "completed_steps": [],
        }

        saga_orchestrator_instance.sagas[sample_saga_definition.saga_id] = (
            sample_saga_definition
        )
        saga_orchestrator_instance.executions[execution_id] = execution_context

        with patch.object(
            saga_orchestrator_instance, "_execute_step_action"
        ) as mock_action:
            mock_action.return_value = {
                "success": True,
                "context_updates": {"inventory_reserved": True},
            }

            with patch.object(
                saga_orchestrator_instance, "_update_execution_status"
            ) as mock_status:
                with patch.object(
                    saga_orchestrator_instance, "_update_execution_context"
                ) as mock_context:
                    with patch.object(
                        saga_orchestrator_instance, "_execute_saga_step"
                    ) as mock_next_step:
                        await saga_orchestrator_instance._execute_saga_step(
                            execution_id, 0
                        )

                        # Verify step execution
                        mock_action.assert_called_once()
                        mock_status.assert_called()
                        mock_context.assert_called()
                        mock_next_step.assert_called_with(execution_id, 1)

    @pytest.mark.asyncio
    async def test_execute_saga_step_failure_with_compensation(
        self, saga_orchestrator_instance, sample_saga_definition
    ):
        """Test SAGA step failure triggering compensation"""

        execution_id = uuid4()
        execution_context = {
            "saga_id": str(sample_saga_definition.saga_id),
            "execution_id": str(execution_id),
            "saga_name": sample_saga_definition.saga_name,
            "status": SagaStatus.PROCESSING,
            "current_step": 1,
            "total_steps": 3,
            "execution_context": {"order_id": "12345"},
            "completed_steps": [0],
        }

        saga_orchestrator_instance.sagas[sample_saga_definition.saga_id] = (
            sample_saga_definition
        )
        saga_orchestrator_instance.executions[execution_id] = execution_context

        with patch.object(
            saga_orchestrator_instance, "_execute_step_action"
        ) as mock_action:
            mock_action.side_effect = Exception("Payment failed")

            with patch.object(
                saga_orchestrator_instance, "_start_compensation"
            ) as mock_compensation:
                await saga_orchestrator_instance._execute_saga_step(execution_id, 1)

                # Verify compensation started
                mock_compensation.assert_called_once_with(
                    execution_id, 1, "Payment failed"
                )

    @pytest.mark.asyncio
    async def test_execute_saga_step_completion(
        self, saga_orchestrator_instance, sample_saga_definition
    ):
        """Test SAGA completion when all steps done"""

        execution_id = uuid4()
        execution_context = {
            "saga_id": str(sample_saga_definition.saga_id),
            "execution_id": str(execution_id),
            "saga_name": sample_saga_definition.saga_name,
            "status": SagaStatus.PROCESSING,
            "current_step": 2,
            "total_steps": 3,
            "execution_context": {"order_id": "12345"},
            "completed_steps": [0, 1, 2],
        }

        saga_orchestrator_instance.sagas[sample_saga_definition.saga_id] = (
            sample_saga_definition
        )
        saga_orchestrator_instance.executions[execution_id] = execution_context

        with patch.object(
            saga_orchestrator_instance, "_complete_saga"
        ) as mock_complete:
            await saga_orchestrator_instance._execute_saga_step(execution_id, 3)

            # Verify saga completion
            mock_complete.assert_called_once_with(execution_id)

    @pytest.mark.asyncio
    async def test_execute_http_call_step(self, saga_orchestrator_instance):
        """Test HTTP call step execution"""

        step = {
            "name": "reserve_inventory",
            "action_type": "http_call",
            "endpoint": "http://inventory-service/reserve",
            "method": "POST",
        }

        context = {"order_id": "12345"}

        result = await saga_orchestrator_instance._execute_http_call_step(step, context)

        assert result["success"] == True
        assert result["response_status"] == 200
        assert "context_updates" in result
        assert result["context_updates"]["step_reserve_inventory_completed"] == True

    @pytest.mark.asyncio
    async def test_execute_database_step(self, saga_orchestrator_instance):
        """Test database operation step execution"""

        step = {
            "name": "update_order",
            "action_type": "database_operation",
            "operation": "update",
            "table": "orders",
        }

        context = {"order_id": "12345"}

        result = await saga_orchestrator_instance._execute_database_step(step, context)

        assert result["success"] == True
        assert "context_updates" in result
        assert result["context_updates"]["db_update_completed"] == True

    @pytest.mark.asyncio
    async def test_execute_message_step(self, saga_orchestrator_instance):
        """Test message sending step execution"""

        step = {
            "name": "notify_shipment",
            "action_type": "message_send",
            "queue_name": "shipment-queue",
            "payload": {"action": "create_shipment"},
        }

        context = {"order_id": "12345"}

        with patch.object(
            saga_orchestrator_instance.message_queue, "send_message"
        ) as mock_send:
            mock_send.return_value = MessageResponse(
                message_id=uuid4(),
                status=ProcessingStatus.PENDING,
                queue_name="shipment-queue",
            )

            result = await saga_orchestrator_instance._execute_message_step(
                step, context
            )

            assert result["success"] == True
            assert "context_updates" in result
            assert result["context_updates"]["message_sent"] == True
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_compensation(
        self, saga_orchestrator_instance, sample_saga_definition
    ):
        """Test compensation process start"""

        execution_id = uuid4()
        execution_context = {
            "saga_id": str(sample_saga_definition.saga_id),
            "execution_id": str(execution_id),
            "saga_name": sample_saga_definition.saga_name,
            "status": SagaStatus.PROCESSING,
            "current_step": 2,
            "total_steps": 3,
            "execution_context": {"order_id": "12345"},
            "completed_steps": [0, 1],
        }

        saga_orchestrator_instance.sagas[sample_saga_definition.saga_id] = (
            sample_saga_definition
        )
        saga_orchestrator_instance.executions[execution_id] = execution_context

        with patch.object(
            saga_orchestrator_instance, "_update_execution_status"
        ) as mock_status:
            with patch.object(
                saga_orchestrator_instance, "_execute_compensation_step"
            ) as mock_comp_step:
                with patch.object(
                    saga_orchestrator_instance, "_complete_compensation"
                ) as mock_complete:
                    await saga_orchestrator_instance._start_compensation(
                        execution_id, 2, "Step failed"
                    )

                    # Verify compensation status update
                    mock_status.assert_called()

                    # Verify compensation steps executed in reverse order
                    assert mock_comp_step.call_count == 2  # For steps 0 and 1

                    # Verify compensation completion
                    mock_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_compensation_step(
        self, saga_orchestrator_instance, sample_saga_definition
    ):
        """Test individual compensation step execution"""

        execution_id = uuid4()
        execution_context = {
            "saga_id": str(sample_saga_definition.saga_id),
            "execution_context": {"order_id": "12345"},
            "compensation_steps_executed": [],
        }

        saga_orchestrator_instance.sagas[sample_saga_definition.saga_id] = (
            sample_saga_definition
        )
        saga_orchestrator_instance.executions[execution_id] = execution_context

        compensation_step = {
            "name": "release_inventory",
            "action_type": "http_call",
            "endpoint": "http://inventory-service/release",
            "method": "POST",
        }

        with patch.object(
            saga_orchestrator_instance, "_execute_step_action"
        ) as mock_action:
            mock_action.return_value = {"success": True}

            with patch.object(
                saga_orchestrator_instance, "_update_execution_context"
            ) as mock_context:
                await saga_orchestrator_instance._execute_compensation_step(
                    execution_id, 0, compensation_step
                )

                # Verify compensation tracking
                assert 0 in execution_context["compensation_steps_executed"]
                mock_action.assert_called_once()
                mock_context.assert_called_once()


# Integration Tests
class TestIntegrationWorkflows:
    @pytest.mark.asyncio
    async def test_complete_message_queue_workflow(
        self, message_queue_instance, mock_redis
    ):
        """Test complete message queue workflow"""

        # 1. Create queue
        config = QueueConfiguration(
            queue_name="integration-test-queue",
            queue_type=QueueType.DIRECT,
            retry_limit=2,
        )

        await message_queue_instance.create_queue(config)

        # 2. Send message
        request = MessageRequest(
            message_type=MessageType.COMMAND,
            queue_name="integration-test-queue",
            payload={"test": "integration"},
            priority=MessagePriority.HIGH,
        )

        send_result = await message_queue_instance.send_message(request)
        assert send_result.status == ProcessingStatus.PENDING

        # 3. Receive message
        message_id = str(uuid4())
        mock_redis.zrevrange.return_value = [message_id]
        mock_redis.hgetall.return_value = {
            "message_id": message_id,
            "created_at": datetime.utcnow().isoformat(),
            "retry_count": "0",
        }

        receive_result = await message_queue_instance.receive_message(
            "integration-test-queue", "test-consumer"
        )
        assert receive_result.status == ProcessingStatus.PROCESSING

        # 4. Complete message
        complete_result = await message_queue_instance.complete_message(
            UUID(message_id), "integration-test-queue"
        )
        assert complete_result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_integration_pattern_with_message_queue(
        self, integration_engine_instance, message_queue_instance
    ):
        """Test integration pattern processing with message queue"""

        # Create router pattern
        pattern = IntegrationPatternRequest(
            pattern_type=IntegrationPattern.MESSAGE_ROUTER,
            name="Test Router",
            configuration={
                "routing_rules": [
                    {
                        "condition_field": "priority",
                        "condition_value": "high",
                        "target_endpoint": "high-priority-queue",
                    }
                ],
                "default_endpoint": "default-queue",
            },
            source_endpoints=["input-queue"],
            target_endpoints=["high-priority-queue", "default-queue"],
        )

        with patch("app.api.v1.enterprise_integration_v63.redis_client") as mock_redis:
            mock_redis.hset.return_value = True

            pattern_result = await integration_engine_instance.create_pattern(pattern)
            assert pattern_result.status == "active"

        # Process message through pattern
        message = {"priority": "high", "data": "important"}

        with patch.object(integration_engine_instance, "_update_pattern_metrics"):
            process_result = (
                await integration_engine_instance.process_message_with_pattern(
                    pattern.pattern_id, message
                )
            )

            assert process_result["routed"] == True
            assert process_result["target_endpoint"] == "high-priority-queue"

    @pytest.mark.asyncio
    async def test_saga_with_integration_patterns(
        self, saga_orchestrator_instance, integration_engine_instance
    ):
        """Test SAGA orchestration with integration patterns"""

        # Define SAGA
        saga = SagaDefinition(
            saga_name="Integration Test Saga",
            steps=[
                {
                    "name": "send_message",
                    "action_type": "message_send",
                    "queue_name": "test-queue",
                    "payload": {"action": "process"},
                }
            ],
            compensation_steps=[
                {
                    "name": "cancel_message",
                    "action_type": "message_send",
                    "queue_name": "cancel-queue",
                    "payload": {"action": "cancel"},
                }
            ],
        )

        with patch("app.api.v1.enterprise_integration_v63.redis_client") as mock_redis:
            mock_redis.hset.return_value = True

            define_result = await saga_orchestrator_instance.define_saga(saga)
            assert define_result["status"] == "defined"

        # Execute SAGA
        with patch.object(
            saga_orchestrator_instance, "_execute_saga_step"
        ) as mock_step:
            execute_result = await saga_orchestrator_instance.execute_saga(
                saga.saga_id, {"test": "data"}
            )
            assert execute_result.status == SagaStatus.STARTED


# Performance Tests
class TestPerformance:
    @pytest.mark.asyncio
    async def test_high_throughput_message_processing(
        self, message_queue_instance, mock_redis
    ):
        """Test high throughput message processing"""

        # Setup queue
        config = QueueConfiguration(
            queue_name="perf-test-queue", queue_type=QueueType.DIRECT
        )
        await message_queue_instance.create_queue(config)

        # Send multiple messages concurrently
        messages = []
        for i in range(100):
            request = MessageRequest(
                message_type=MessageType.EVENT,
                queue_name="perf-test-queue",
                payload={"batch_id": i},
                priority=MessagePriority.NORMAL,
            )
            messages.append(message_queue_instance.send_message(request))

        # Execute all sends concurrently
        results = await asyncio.gather(*messages)

        # Verify all messages sent successfully
        assert len(results) == 100
        for result in results:
            assert result.status == ProcessingStatus.PENDING

    @pytest.mark.asyncio
    async def test_concurrent_pattern_processing(self, integration_engine_instance):
        """Test concurrent integration pattern processing"""

        # Create multiple patterns
        patterns = []
        for i in range(10):
            pattern = IntegrationPatternRequest(
                pattern_type=IntegrationPattern.MESSAGE_FILTER,
                name=f"Filter {i}",
                configuration={},
                source_endpoints=[f"input-{i}"],
                target_endpoints=[f"output-{i}"],
                filtering_criteria={"id": i},
            )
            patterns.append(pattern)

        # Create patterns concurrently
        with patch("app.api.v1.enterprise_integration_v63.redis_client") as mock_redis:
            mock_redis.hset.return_value = True

            create_tasks = [
                integration_engine_instance.create_pattern(p) for p in patterns
            ]
            create_results = await asyncio.gather(*create_tasks)

            assert len(create_results) == 10
            for result in create_results:
                assert result.status == "active"

        # Process messages concurrently
        process_tasks = []
        for i, pattern in enumerate(patterns):
            message = {"id": i, "data": f"test_{i}"}
            task = integration_engine_instance.process_message_with_pattern(
                pattern.pattern_id, message
            )
            process_tasks.append(task)

        with patch.object(integration_engine_instance, "_update_pattern_metrics"):
            process_results = await asyncio.gather(*process_tasks)

            # Verify all processing succeeded
            for i, result in enumerate(process_results):
                assert result["filtered"] == False  # All should pass filter


# Error Handling and Edge Cases
class TestErrorHandlingEdgeCases:
    @pytest.mark.asyncio
    async def test_message_queue_redis_connection_failure(self, mock_redis):
        """Test message queue behavior when Redis connection fails"""

        mock_redis.ping.side_effect = Exception("Connection failed")
        mock_redis.hset.side_effect = Exception("Connection failed")

        queue = MessageQueue(mock_redis)
        config = QueueConfiguration(queue_name="test", queue_type=QueueType.DIRECT)

        with pytest.raises(BusinessLogicError, match="Failed to create queue"):
            await queue.create_queue(config)

    @pytest.mark.asyncio
    async def test_integration_pattern_invalid_configuration(
        self, integration_engine_instance
    ):
        """Test integration pattern with invalid configuration"""

        pattern = IntegrationPatternRequest(
            pattern_type=IntegrationPattern.MESSAGE_ROUTER,
            name="Invalid Router",
            configuration={},  # Missing routing rules
            source_endpoints=["input"],
            target_endpoints=["output"],
        )

        integration_engine_instance.patterns[pattern.pattern_id] = pattern

        message = {"data": "test"}

        with patch.object(integration_engine_instance, "_update_pattern_metrics"):
            result = await integration_engine_instance.process_message_with_pattern(
                pattern.pattern_id, message
            )

            # Should use default routing
            assert result["routed"] == True
            assert result["target_endpoint"] == "output"

    @pytest.mark.asyncio
    async def test_saga_step_timeout_handling(self, saga_orchestrator_instance):
        """Test SAGA step timeout handling"""

        saga = SagaDefinition(
            saga_name="Timeout Test",
            steps=[
                {
                    "name": "slow_step",
                    "action_type": "http_call",
                    "endpoint": "http://slow-service/api",
                }
            ],
            compensation_steps=[],
            timeout_seconds=1,  # Very short timeout
        )

        saga_orchestrator_instance.sagas[saga.saga_id] = saga

        execution_id = uuid4()
        execution_context = {
            "saga_id": str(saga.saga_id),
            "execution_context": {},
            "completed_steps": [],
        }
        saga_orchestrator_instance.executions[execution_id] = execution_context

        # Mock slow step execution
        with patch.object(
            saga_orchestrator_instance, "_execute_step_action"
        ) as mock_action:
            mock_action.side_effect = asyncio.TimeoutError("Step timed out")

            with patch.object(
                saga_orchestrator_instance, "_start_compensation"
            ) as mock_compensation:
                await saga_orchestrator_instance._execute_saga_step(execution_id, 0)

                # Should trigger compensation due to timeout
                mock_compensation.assert_called_once()

    def test_message_priority_edge_cases(self, message_queue_instance):
        """Test message priority edge cases"""

        # Test unknown priority defaults to normal
        score = message_queue_instance._get_priority_score("unknown")
        assert score == 2.0  # Default NORMAL priority

        # Test None priority
        score = message_queue_instance._get_priority_score(None)
        assert score == 2.0

    @pytest.mark.asyncio
    async def test_queue_metrics_calculation_edge_cases(
        self, message_queue_instance, mock_redis
    ):
        """Test queue metrics calculation with edge cases"""

        # Test with zero total messages
        mock_redis.hgetall.return_value = {
            "total_messages": "0",
            "completed_messages": "0",
            "failed_messages": "0",
            "created_at": datetime.utcnow().isoformat(),
        }
        mock_redis.zcard.return_value = 0

        result = await message_queue_instance.get_queue_metrics("test-queue")

        # Should handle division by zero gracefully
        assert result.error_rate_percent == 0.0
        assert result.total_messages == 0


if __name__ == "__main__":
    pytest.main([__file__])
