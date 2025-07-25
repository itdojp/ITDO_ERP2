"""
CC02 v55.0 Event Streaming Engine
Real-time Event Processing and Message Queue Management
Day 5 of 7-day intensive backend development
"""

from typing import List, Dict, Any, Optional, Union, Set, Callable, AsyncGenerator
from uuid import UUID, uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import json
import asyncio
import aioredis
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, text
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import EventProcessingError, ValidationError
from app.models.events import EventStream, EventSubscription, EventHandler, ProcessedEvent
from app.services.audit_service import AuditService

class EventType(str, Enum):
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    ORDER_CREATED = "order.created"
    ORDER_UPDATED = "order.updated"
    ORDER_CANCELLED = "order.cancelled"
    ORDER_SHIPPED = "order.shipped"
    INVENTORY_UPDATED = "inventory.updated"
    INVENTORY_LOW_STOCK = "inventory.low_stock"
    PAYMENT_PROCESSED = "payment.processed"
    PAYMENT_FAILED = "payment.failed"
    NOTIFICATION_SENT = "notification.sent"
    DATA_SYNC_COMPLETED = "data.sync.completed"
    SYSTEM_ALERT = "system.alert"
    CUSTOM = "custom"

class EventPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"

class DeliveryMode(str, Enum):
    AT_LEAST_ONCE = "at_least_once"
    AT_MOST_ONCE = "at_most_once"
    EXACTLY_ONCE = "exactly_once"

@dataclass
class Event:
    """Event data structure"""
    id: UUID
    type: EventType
    source: str
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: Optional[UUID] = None
    causation_id: Optional[UUID] = None
    version: int = 1

@dataclass
class EventSubscription:
    """Event subscription configuration"""
    id: UUID
    subscriber_id: str
    event_types: List[EventType]
    filters: Dict[str, Any] = field(default_factory=dict)
    delivery_mode: DeliveryMode = DeliveryMode.AT_LEAST_ONCE
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    dead_letter_queue: Optional[str] = None
    is_active: bool = True

@dataclass
class ProcessingResult:
    """Event processing result"""
    event_id: UUID
    status: ProcessingStatus
    processing_time: float
    error_message: Optional[str] = None
    retry_count: int = 0
    next_retry: Optional[datetime] = None

class BaseEventHandler(ABC):
    """Base class for event handlers"""
    
    def __init__(self, handler_id: str, event_types: List[EventType]):
        self.handler_id = handler_id
        self.event_types = event_types
    
    @abstractmethod
    async def handle(self, event: Event) -> ProcessingResult:
        """Handle the event"""
        pass
    
    def can_handle(self, event: Event) -> bool:
        """Check if handler can process the event"""
        return event.type in self.event_types

class EmailNotificationHandler(BaseEventHandler):
    """Email notification event handler"""
    
    def __init__(self):
        super().__init__(
            "email_notification",
            [EventType.USER_CREATED, EventType.ORDER_CREATED, EventType.PAYMENT_PROCESSED]
        )
    
    async def handle(self, event: Event) -> ProcessingResult:
        """Handle email notification events"""
        start_time = datetime.utcnow()
        
        try:
            # Simulate email sending
            await asyncio.sleep(0.1)  # Simulate network delay
            
            if event.type == EventType.USER_CREATED:
                await self._send_welcome_email(event.data)
            elif event.type == EventType.ORDER_CREATED:
                await self._send_order_confirmation(event.data)
            elif event.type == EventType.PAYMENT_PROCESSED:
                await self._send_payment_receipt(event.data)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ProcessingResult(
                event_id=event.id,
                status=ProcessingStatus.SUCCESS,
                processing_time=processing_time
            )
        
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ProcessingResult(
                event_id=event.id,
                status=ProcessingStatus.FAILED,
                processing_time=processing_time,
                error_message=str(e)
            )
    
    async def _send_welcome_email(self, data: Dict[str, Any]):
        """Send welcome email"""
        user_email = data.get('email')
        if not user_email:
            raise ValueError("User email not provided")
        
        # Simulate email sending logic
        logging.info(f"Sending welcome email to {user_email}")
    
    async def _send_order_confirmation(self, data: Dict[str, Any]):
        """Send order confirmation email"""
        order_id = data.get('order_id')
        customer_email = data.get('customer_email')
        
        if not customer_email:
            raise ValueError("Customer email not provided")
        
        logging.info(f"Sending order confirmation for {order_id} to {customer_email}")
    
    async def _send_payment_receipt(self, data: Dict[str, Any]):
        """Send payment receipt email"""
        payment_id = data.get('payment_id')
        customer_email = data.get('customer_email')
        
        if not customer_email:
            raise ValueError("Customer email not provided")
        
        logging.info(f"Sending payment receipt for {payment_id} to {customer_email}")

class InventoryHandler(BaseEventHandler):
    """Inventory management event handler"""
    
    def __init__(self):
        super().__init__(
            "inventory_handler",
            [EventType.ORDER_CREATED, EventType.ORDER_CANCELLED, EventType.INVENTORY_UPDATED]
        )
    
    async def handle(self, event: Event) -> ProcessingResult:
        """Handle inventory events"""
        start_time = datetime.utcnow()
        
        try:
            if event.type == EventType.ORDER_CREATED:
                await self._reserve_inventory(event.data)
            elif event.type == EventType.ORDER_CANCELLED:
                await self._release_inventory(event.data)
            elif event.type == EventType.INVENTORY_UPDATED:
                await self._check_stock_levels(event.data)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ProcessingResult(
                event_id=event.id,
                status=ProcessingStatus.SUCCESS,
                processing_time=processing_time
            )
        
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ProcessingResult(
                event_id=event.id,
                status=ProcessingStatus.FAILED,
                processing_time=processing_time,
                error_message=str(e)
            )
    
    async def _reserve_inventory(self, data: Dict[str, Any]):
        """Reserve inventory for order"""
        order_items = data.get('items', [])
        
        for item in order_items:
            product_id = item.get('product_id')
            quantity = item.get('quantity')
            
            if not product_id or not quantity:
                continue
            
            # Simulate inventory reservation
            logging.info(f"Reserving {quantity} units of product {product_id}")
    
    async def _release_inventory(self, data: Dict[str, Any]):
        """Release reserved inventory"""
        order_items = data.get('items', [])
        
        for item in order_items:
            product_id = item.get('product_id')
            quantity = item.get('quantity')
            
            if not product_id or not quantity:
                continue
            
            # Simulate inventory release
            logging.info(f"Releasing {quantity} units of product {product_id}")
    
    async def _check_stock_levels(self, data: Dict[str, Any]):
        """Check stock levels and trigger alerts"""
        product_id = data.get('product_id')
        current_stock = data.get('current_stock')
        minimum_stock = data.get('minimum_stock', 10)
        
        if current_stock < minimum_stock:
            # Trigger low stock alert
            logging.warning(f"Low stock alert for product {product_id}: {current_stock} < {minimum_stock}")

class EventBus:
    """Event bus for publishing and subscribing to events"""
    
    def __init__(self):
        self.handlers: Dict[str, BaseEventHandler] = {}
        self.subscriptions: Dict[str, EventSubscription] = {}
        self.redis_client: Optional[aioredis.Redis] = None
        self.processing_queue = asyncio.Queue()
        self.dead_letter_queue = asyncio.Queue()
        self.is_running = False
    
    async def initialize(self, redis_url: str = "redis://localhost:6379"):
        """Initialize event bus"""
        self.redis_client = await aioredis.from_url(redis_url)
        
        # Register default handlers
        self.register_handler(EmailNotificationHandler())
        self.register_handler(InventoryHandler())
    
    async def shutdown(self):
        """Shutdown event bus"""
        self.is_running = False
        if self.redis_client:
            await self.redis_client.close()
    
    def register_handler(self, handler: BaseEventHandler):
        """Register event handler"""
        self.handlers[handler.handler_id] = handler
    
    def unregister_handler(self, handler_id: str):
        """Unregister event handler"""
        if handler_id in self.handlers:
            del self.handlers[handler_id]
    
    async def subscribe(
        self,
        subscriber_id: str,
        event_types: List[EventType],
        filters: Dict[str, Any] = None,
        delivery_mode: DeliveryMode = DeliveryMode.AT_LEAST_ONCE
    ) -> str:
        """Subscribe to events"""
        subscription_id = str(uuid4())
        
        subscription = EventSubscription(
            id=UUID(subscription_id),
            subscriber_id=subscriber_id,
            event_types=event_types,
            filters=filters or {},
            delivery_mode=delivery_mode,
            retry_policy={
                'max_retries': 3,
                'retry_delay': 5,
                'backoff_multiplier': 2
            }
        )
        
        self.subscriptions[subscription_id] = subscription
        return subscription_id
    
    async def unsubscribe(self, subscription_id: str):
        """Unsubscribe from events"""
        if subscription_id in self.subscriptions:
            self.subscriptions[subscription_id].is_active = False
    
    async def publish(self, event: Event):
        """Publish event to the bus"""
        # Store event in Redis stream
        if self.redis_client:
            event_data = {
                'id': str(event.id),
                'type': event.type.value,
                'source': event.source,
                'timestamp': event.timestamp.isoformat(),
                'data': json.dumps(event.data),
                'metadata': json.dumps(event.metadata),
                'priority': event.priority.value,
                'correlation_id': str(event.correlation_id) if event.correlation_id else None,
                'causation_id': str(event.causation_id) if event.causation_id else None,
                'version': event.version
            }
            
            stream_key = f"events:{event.type.value}"
            await self.redis_client.xadd(stream_key, event_data)
        
        # Add to processing queue
        await self.processing_queue.put(event)
    
    async def start_processing(self):
        """Start event processing loop"""
        self.is_running = True
        
        # Start processing workers
        workers = [
            asyncio.create_task(self._process_events()),
            asyncio.create_task(self._process_dead_letter_queue()),
            asyncio.create_task(self._process_retries())
        ]
        
        await asyncio.gather(*workers)
    
    async def _process_events(self):
        """Process events from the queue"""
        while self.is_running:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(
                    self.processing_queue.get(),
                    timeout=1.0
                )
                
                # Find matching handlers
                matching_handlers = [
                    handler for handler in self.handlers.values()
                    if handler.can_handle(event)
                ]
                
                # Process event with each handler
                for handler in matching_handlers:
                    asyncio.create_task(self._handle_event(handler, event))
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logging.error(f"Error processing events: {e}")
    
    async def _handle_event(self, handler: BaseEventHandler, event: Event):
        """Handle event with specific handler"""
        try:
            result = await handler.handle(event)
            
            if result.status == ProcessingStatus.FAILED:
                # Check if we should retry
                retry_policy = self.subscriptions.get(handler.handler_id, {}).retry_policy or {}
                max_retries = retry_policy.get('max_retries', 3)
                
                if result.retry_count < max_retries:
                    # Schedule retry
                    retry_delay = retry_policy.get('retry_delay', 5)
                    backoff_multiplier = retry_policy.get('backoff_multiplier', 2)
                    delay = retry_delay * (backoff_multiplier ** result.retry_count)
                    
                    result.next_retry = datetime.utcnow() + timedelta(seconds=delay)
                    result.retry_count += 1
                    result.status = ProcessingStatus.RETRYING
                    
                    # Schedule retry
                    asyncio.create_task(self._schedule_retry(handler, event, result))
                else:
                    # Move to dead letter queue
                    result.status = ProcessingStatus.DEAD_LETTER
                    await self.dead_letter_queue.put((event, result))
            
            # Log processing result
            await self._log_processing_result(event, handler, result)
            
        except Exception as e:
            logging.error(f"Handler {handler.handler_id} failed to process event {event.id}: {e}")
    
    async def _schedule_retry(self, handler: BaseEventHandler, event: Event, result: ProcessingResult):
        """Schedule event retry"""
        if result.next_retry:
            delay = (result.next_retry - datetime.utcnow()).total_seconds()
            if delay > 0:
                await asyncio.sleep(delay)
            
            await self._handle_event(handler, event)
    
    async def _process_dead_letter_queue(self):
        """Process dead letter queue"""
        while self.is_running:
            try:
                # Get item from dead letter queue with timeout
                item = await asyncio.wait_for(
                    self.dead_letter_queue.get(),
                    timeout=1.0
                )
                
                event, result = item
                
                # Log dead letter event
                logging.error(f"Event {event.id} moved to dead letter queue: {result.error_message}")
                
                # Store in dead letter storage (Redis or database)
                if self.redis_client:
                    dead_letter_data = {
                        'event_id': str(event.id),
                        'event_type': event.type.value,
                        'error_message': result.error_message,
                        'retry_count': result.retry_count,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                    await self.redis_client.lpush(
                        "dead_letter_queue",
                        json.dumps(dead_letter_data)
                    )
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logging.error(f"Error processing dead letter queue: {e}")
    
    async def _process_retries(self):
        """Process retry queue"""
        while self.is_running:
            try:
                # Check for events that need retry
                if self.redis_client:
                    # Get events from retry queue
                    retry_events = await self.redis_client.zrangebyscore(
                        "retry_queue",
                        0,
                        datetime.utcnow().timestamp(),
                        withscores=True
                    )
                    
                    for event_data, score in retry_events:
                        # Remove from retry queue
                        await self.redis_client.zrem("retry_queue", event_data)
                        
                        # Parse and reprocess event
                        event_info = json.loads(event_data)
                        # Reconstruct and reprocess event
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logging.error(f"Error processing retries: {e}")
    
    async def _log_processing_result(
        self,
        event: Event,
        handler: BaseEventHandler,
        result: ProcessingResult
    ):
        """Log processing result"""
        log_data = {
            'event_id': str(event.id),
            'event_type': event.type.value,
            'handler_id': handler.handler_id,
            'status': result.status.value,
            'processing_time': result.processing_time,
            'error_message': result.error_message,
            'retry_count': result.retry_count,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if self.redis_client:
            await self.redis_client.lpush(
                "event_processing_log",
                json.dumps(log_data)
            )
    
    async def get_event_stream(
        self,
        event_type: EventType,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> AsyncGenerator[Event, None]:
        """Get event stream"""
        if not self.redis_client:
            return
        
        stream_key = f"events:{event_type.value}"
        
        # Read from Redis stream
        start_id = "0" if not start_time else f"{int(start_time.timestamp() * 1000)}-0"
        end_id = "+" if not end_time else f"{int(end_time.timestamp() * 1000)}-0"
        
        events = await self.redis_client.xrange(stream_key, min=start_id, max=end_id)
        
        for event_id, fields in events:
            event_data = {k.decode(): v.decode() for k, v in fields.items()}
            
            event = Event(
                id=UUID(event_data['id']),
                type=EventType(event_data['type']),
                source=event_data['source'],
                timestamp=datetime.fromisoformat(event_data['timestamp']),
                data=json.loads(event_data['data']),
                metadata=json.loads(event_data['metadata']),
                priority=EventPriority(event_data['priority']),
                correlation_id=UUID(event_data['correlation_id']) if event_data.get('correlation_id') else None,
                causation_id=UUID(event_data['causation_id']) if event_data.get('causation_id') else None,
                version=int(event_data['version'])
            )
            
            yield event

class EventStreamingEngine:
    """Main event streaming engine"""
    
    def __init__(self):
        self.event_bus = EventBus()
        self.audit_service = AuditService()
        self.metrics = {
            'events_published': 0,
            'events_processed': 0,
            'events_failed': 0,
            'processing_time_total': 0.0,
            'handlers_registered': 0
        }
    
    async def initialize(self, redis_url: str = "redis://localhost:6379"):
        """Initialize streaming engine"""
        await self.event_bus.initialize(redis_url)
    
    async def shutdown(self):
        """Shutdown streaming engine"""
        await self.event_bus.shutdown()
    
    async def publish_event(
        self,
        event_type: EventType,
        source: str,
        data: Dict[str, Any],
        metadata: Dict[str, Any] = None,
        priority: EventPriority = EventPriority.NORMAL,
        correlation_id: Optional[UUID] = None,
        causation_id: Optional[UUID] = None
    ) -> UUID:
        """Publish event to the stream"""
        
        event = Event(
            id=uuid4(),
            type=event_type,
            source=source,
            timestamp=datetime.utcnow(),
            data=data,
            metadata=metadata or {},
            priority=priority,
            correlation_id=correlation_id,
            causation_id=causation_id
        )
        
        await self.event_bus.publish(event)
        
        # Update metrics
        self.metrics['events_published'] += 1
        
        # Audit log
        await self.audit_service.log_event(
            event_type="event_published",
            entity_type="event_stream",
            entity_id=event.id,
            details={
                'event_type': event_type.value,
                'source': source,
                'priority': priority.value,
                'data_size': len(json.dumps(data))
            }
        )
        
        return event.id
    
    async def subscribe_to_events(
        self,
        subscriber_id: str,
        event_types: List[EventType],
        handler: Optional[BaseEventHandler] = None,
        filters: Dict[str, Any] = None
    ) -> str:
        """Subscribe to events"""
        
        subscription_id = await self.event_bus.subscribe(
            subscriber_id, event_types, filters
        )
        
        if handler:
            self.event_bus.register_handler(handler)
            self.metrics['handlers_registered'] += 1
        
        return subscription_id
    
    async def start_processing(self):
        """Start event processing"""
        await self.event_bus.start_processing()
    
    async def get_event_history(
        self,
        event_type: EventType,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Event]:
        """Get event history"""
        
        events = []
        count = 0
        
        async for event in self.event_bus.get_event_stream(event_type, start_time, end_time):
            events.append(event)
            count += 1
            if count >= limit:
                break
        
        return events
    
    async def get_processing_metrics(self) -> Dict[str, Any]:
        """Get processing metrics"""
        
        # Get additional metrics from Redis
        if self.event_bus.redis_client:
            # Get dead letter queue size
            dead_letter_size = await self.event_bus.redis_client.llen("dead_letter_queue")
            
            # Get retry queue size
            retry_queue_size = await self.event_bus.redis_client.zcard("retry_queue")
            
            # Get recent processing stats
            recent_logs = await self.event_bus.redis_client.lrange(
                "event_processing_log", 0, 999
            )
            
            successful_events = 0
            failed_events = 0
            total_processing_time = 0.0
            
            for log_entry in recent_logs:
                log_data = json.loads(log_entry)
                if log_data['status'] == ProcessingStatus.SUCCESS.value:
                    successful_events += 1
                elif log_data['status'] == ProcessingStatus.FAILED.value:
                    failed_events += 1
                
                total_processing_time += log_data.get('processing_time', 0)
            
            avg_processing_time = (
                total_processing_time / len(recent_logs)
                if recent_logs else 0
            )
            
            return {
                **self.metrics,
                'dead_letter_queue_size': dead_letter_size,
                'retry_queue_size': retry_queue_size,
                'recent_successful_events': successful_events,
                'recent_failed_events': failed_events,
                'average_processing_time': avg_processing_time,
                'success_rate': (
                    successful_events / (successful_events + failed_events) * 100
                    if (successful_events + failed_events) > 0 else 0
                ),
                'generated_at': datetime.utcnow().isoformat()
            }
        
        return self.metrics
    
    async def replay_events(
        self,
        event_type: EventType,
        start_time: datetime,
        end_time: datetime,
        target_handlers: List[str] = None
    ) -> Dict[str, Any]:
        """Replay events for reprocessing"""
        
        replayed_count = 0
        
        async for event in self.event_bus.get_event_stream(event_type, start_time, end_time):
            if target_handlers:
                # Only replay for specific handlers
                matching_handlers = [
                    handler for handler_id, handler in self.event_bus.handlers.items()
                    if handler_id in target_handlers and handler.can_handle(event)
                ]
                
                for handler in matching_handlers:
                    asyncio.create_task(self.event_bus._handle_event(handler, event))
            else:
                # Replay for all handlers
                await self.event_bus.publish(event)
            
            replayed_count += 1
        
        return {
            'replayed_count': replayed_count,
            'event_type': event_type.value,
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'target_handlers': target_handlers,
            'replayed_at': datetime.utcnow().isoformat()
        }

# Singleton instance
streaming_engine = EventStreamingEngine()

# Helper functions
async def publish_event(
    event_type: EventType,
    source: str,
    data: Dict[str, Any],
    metadata: Dict[str, Any] = None,
    priority: EventPriority = EventPriority.NORMAL
) -> UUID:
    """Publish event to stream"""
    return await streaming_engine.publish_event(
        event_type, source, data, metadata, priority
    )

async def subscribe_to_events(
    subscriber_id: str,
    event_types: List[EventType],
    handler: Optional[BaseEventHandler] = None
) -> str:
    """Subscribe to events"""
    return await streaming_engine.subscribe_to_events(
        subscriber_id, event_types, handler
    )

async def get_event_metrics() -> Dict[str, Any]:
    """Get event processing metrics"""
    return await streaming_engine.get_processing_metrics()