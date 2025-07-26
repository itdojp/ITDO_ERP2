"""
CC02 v79.0 Day 24: Enterprise Integrated Data Platform & Analytics
Module 2: Real-time Streaming & Event Processing

Advanced real-time event streaming platform with distributed processing,
complex event pattern detection, and intelligent stream analytics.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from ..core.mobile_erp_sdk import MobileERPSDK


class EventType(Enum):
    """Event type classifications"""

    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"
    BUSINESS_EVENT = "business_event"
    SENSOR_DATA = "sensor_data"
    TRANSACTION = "transaction"
    ALERT = "alert"
    METRIC = "metric"


class StreamFormat(Enum):
    """Stream data formats"""

    JSON = "json"
    AVRO = "avro"
    PROTOBUF = "protobuf"
    CSV = "csv"
    BINARY = "binary"


class ProcessingMode(Enum):
    """Stream processing modes"""

    EXACTLY_ONCE = "exactly_once"
    AT_LEAST_ONCE = "at_least_once"
    AT_MOST_ONCE = "at_most_once"


class WindowType(Enum):
    """Windowing strategies for stream processing"""

    TUMBLING = "tumbling"  # Fixed, non-overlapping windows
    HOPPING = "hopping"  # Fixed, overlapping windows
    SLIDING = "sliding"  # Variable-size, data-driven windows
    SESSION = "session"  # Activity-based windows


@dataclass
class StreamEvent:
    """Stream event data structure"""

    id: str
    type: EventType
    source: str
    payload: Dict[str, Any]
    timestamp: datetime
    version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None


@dataclass
class StreamTopic:
    """Stream topic configuration"""

    name: str
    partitions: int
    replication_factor: int
    retention_ms: int
    format: StreamFormat
    schema: Optional[Dict[str, Any]] = None
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProcessingWindow:
    """Processing window definition"""

    window_type: WindowType
    size_ms: int
    slide_ms: Optional[int] = None  # For hopping windows
    grace_period_ms: int = 5000  # Late arrival tolerance
    key_selector: Optional[str] = None


@dataclass
class EventPattern:
    """Complex event pattern for CEP"""

    id: str
    name: str
    pattern_definition: Dict[str, Any]
    time_window_ms: int
    key_selector: Optional[str] = None
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class StreamProcessor:
    """Stream processor configuration"""

    id: str
    name: str
    input_topics: List[str]
    output_topics: List[str]
    processing_logic: Callable
    window_config: Optional[ProcessingWindow] = None
    parallelism: int = 1
    enabled: bool = True


class EventProducer:
    """High-performance event producer"""

    def __init__(self, bootstrap_servers: str = "localhost:9092") -> dict:
        self.bootstrap_servers = bootstrap_servers
        self.producer: Optional[AIOKafkaProducer] = None
        self.metrics = {
            "events_sent": 0,
            "bytes_sent": 0,
            "errors": 0,
            "last_send_time": None,
        }

    async def start(self) -> dict:
        """Start the event producer"""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=self._serialize_event,
            key_serializer=lambda x: str(x).encode("utf-8") if x else None,
            compression_type="gzip",
            batch_size=16384,
            linger_ms=10,
            acks="all",
        )
        await self.producer.start()
        logging.info("Event producer started")

    async def stop(self) -> dict:
        """Stop the event producer"""
        if self.producer:
            await self.producer.stop()
            logging.info("Event producer stopped")

    def _serialize_event(self, event: StreamEvent) -> bytes:
        """Serialize event to bytes"""
        event_dict = {
            "id": event.id,
            "type": event.type.value,
            "source": event.source,
            "payload": event.payload,
            "timestamp": event.timestamp.isoformat(),
            "version": event.version,
            "metadata": event.metadata,
            "correlation_id": event.correlation_id,
            "causation_id": event.causation_id,
        }
        return json.dumps(event_dict).encode("utf-8")

    async def send_event(
        self, topic: str, event: StreamEvent, partition_key: Optional[str] = None
    ) -> bool:
        """Send event to stream topic"""
        try:
            if not self.producer:
                raise RuntimeError("Producer not started")

            # Send event
            await self.producer.send(topic=topic, value=event, key=partition_key)

            # Update metrics
            self.metrics["events_sent"] += 1
            self.metrics["bytes_sent"] += len(self._serialize_event(event))
            self.metrics["last_send_time"] = datetime.now()

            return True

        except Exception as e:
            logging.error(f"Failed to send event: {e}")
            self.metrics["errors"] += 1
            return False

    async def send_batch(
        self,
        topic: str,
        events: List[StreamEvent],
        partition_key_func: Optional[Callable] = None,
    ) -> int:
        """Send batch of events"""
        sent_count = 0

        for event in events:
            partition_key = None
            if partition_key_func:
                partition_key = partition_key_func(event)

            success = await self.send_event(topic, event, partition_key)
            if success:
                sent_count += 1

        return sent_count

    def get_metrics(self) -> Dict[str, Any]:
        """Get producer metrics"""
        return self.metrics.copy()


class EventConsumer:
    """High-performance event consumer"""

    def __init__(
        self, consumer_group: str, bootstrap_servers: str = "localhost:9092"
    ) -> dict:
        self.consumer_group = consumer_group
        self.bootstrap_servers = bootstrap_servers
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.running = False
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.metrics = {
            "events_received": 0,
            "bytes_received": 0,
            "processing_errors": 0,
            "last_receive_time": None,
        }

    async def start(self, topics: List[str]) -> dict:
        """Start the event consumer"""
        self.consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.consumer_group,
            value_deserializer=self._deserialize_event,
            auto_offset_reset="latest",
            enable_auto_commit=True,
            auto_commit_interval_ms=1000,
        )
        await self.consumer.start()
        self.running = True
        logging.info(f"Event consumer started for topics: {topics}")

    async def stop(self) -> dict:
        """Stop the event consumer"""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
            logging.info("Event consumer stopped")

    def _deserialize_event(self, data: bytes) -> StreamEvent:
        """Deserialize event from bytes"""
        event_dict = json.loads(data.decode("utf-8"))

        return StreamEvent(
            id=event_dict["id"],
            type=EventType(event_dict["type"]),
            source=event_dict["source"],
            payload=event_dict["payload"],
            timestamp=datetime.fromisoformat(event_dict["timestamp"]),
            version=event_dict.get("version", "1.0"),
            metadata=event_dict.get("metadata", {}),
            correlation_id=event_dict.get("correlation_id"),
            causation_id=event_dict.get("causation_id"),
        )

    def add_event_handler(self, event_type: EventType, handler: Callable) -> dict:
        """Add event handler for specific event type"""
        self.event_handlers[event_type.value].append(handler)

    async def consume_events(self) -> dict:
        """Main event consumption loop"""
        try:
            async for message in self.consumer:
                if not self.running:
                    break

                try:
                    event = message.value

                    # Update metrics
                    self.metrics["events_received"] += 1
                    self.metrics["bytes_received"] += len(message.value)
                    self.metrics["last_receive_time"] = datetime.now()

                    # Process event
                    await self._process_event(event)

                except Exception as e:
                    logging.error(f"Event processing error: {e}")
                    self.metrics["processing_errors"] += 1

        except Exception as e:
            logging.error(f"Consumer error: {e}")

    async def _process_event(self, event: StreamEvent) -> dict:
        """Process individual event"""
        handlers = self.event_handlers.get(event.type.value, [])

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logging.error(f"Handler error: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get consumer metrics"""
        return self.metrics.copy()


class StreamProcessor:
    """Stream processing engine"""

    def __init__(self, processor_id: str) -> dict:
        self.processor_id = processor_id
        self.windowed_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.state_store: Dict[str, Any] = {}
        self.watermarks: Dict[str, datetime] = {}
        self.running = False

    async def process_stream(
        self,
        input_consumer: EventConsumer,
        output_producer: EventProducer,
        processing_function: Callable,
        window_config: Optional[ProcessingWindow] = None,
    ):
        """Main stream processing loop"""
        self.running = True

        async for message in input_consumer.consumer:
            if not self.running:
                break

            try:
                event = message.value

                if window_config:
                    # Windowed processing
                    await self._process_windowed_event(
                        event, processing_function, window_config, output_producer
                    )
                else:
                    # Direct processing
                    result = await self._execute_processing_function(
                        processing_function, event
                    )

                    if result:
                        await output_producer.send_event("processed_events", result)

            except Exception as e:
                logging.error(f"Stream processing error: {e}")

    async def _process_windowed_event(
        self,
        event: StreamEvent,
        processing_function: Callable,
        window_config: ProcessingWindow,
        output_producer: EventProducer,
    ):
        """Process event with windowing"""
        window_key = self._get_window_key(event, window_config)

        # Add event to window
        self.windowed_data[window_key].append(event)

        # Update watermark
        self.watermarks[window_key] = max(
            self.watermarks.get(window_key, event.timestamp), event.timestamp
        )

        # Check if window should be processed
        if self._should_process_window(window_key, window_config):
            window_events = list(self.windowed_data[window_key])

            # Process window
            result = await self._execute_processing_function(
                processing_function, window_events
            )

            if result:
                await output_producer.send_event("windowed_results", result)

            # Clear processed window
            self.windowed_data[window_key].clear()

    def _get_window_key(
        self, event: StreamEvent, window_config: ProcessingWindow
    ) -> str:
        """Generate window key for event"""
        if window_config.key_selector:
            key_value = event.payload.get(window_config.key_selector, "default")
        else:
            key_value = "global"

        if window_config.window_type == WindowType.TUMBLING:
            window_start = (
                event.timestamp.timestamp() // (window_config.size_ms / 1000)
            ) * (window_config.size_ms / 1000)
            return f"{key_value}_{int(window_start)}"
        elif window_config.window_type == WindowType.HOPPING:
            window_start = (
                event.timestamp.timestamp() // (window_config.slide_ms / 1000)
            ) * (window_config.slide_ms / 1000)
            return f"{key_value}_{int(window_start)}"
        else:
            # Session windows or sliding windows would need more complex logic
            return f"{key_value}_{int(event.timestamp.timestamp())}"

    def _should_process_window(
        self, window_key: str, window_config: ProcessingWindow
    ) -> bool:
        """Determine if window should be processed"""
        if not self.windowed_data[window_key]:
            return False

        latest_timestamp = max(
            event.timestamp for event in self.windowed_data[window_key]
        )
        current_time = datetime.now()

        # Process if window is beyond grace period
        grace_period = timedelta(milliseconds=window_config.grace_period_ms)
        return current_time > latest_timestamp + grace_period

    async def _execute_processing_function(
        self, function: Callable, data: Any
    ) -> Optional[StreamEvent]:
        """Execute processing function safely"""
        try:
            if asyncio.iscoroutinefunction(function):
                return await function(data)
            else:
                return function(data)
        except Exception as e:
            logging.error(f"Processing function error: {e}")
            return None

    def stop(self) -> dict:
        """Stop stream processor"""
        self.running = False


class ComplexEventProcessor:
    """Complex Event Processing (CEP) engine"""

    def __init__(self) -> dict:
        self.patterns: Dict[str, EventPattern] = {}
        self.event_buffers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.pattern_matches: List[Dict[str, Any]] = []
        self.running = False

    def add_pattern(self, pattern: EventPattern) -> dict:
        """Add event pattern for detection"""
        self.patterns[pattern.id] = pattern
        logging.info(f"Added CEP pattern: {pattern.name}")

    def remove_pattern(self, pattern_id: str) -> dict:
        """Remove event pattern"""
        if pattern_id in self.patterns:
            del self.patterns[pattern_id]
            logging.info(f"Removed CEP pattern: {pattern_id}")

    async def process_event(self, event: StreamEvent) -> dict:
        """Process event against all patterns"""
        if not self.running:
            return

        # Add event to buffers
        for pattern_id, pattern in self.patterns.items():
            if not pattern.enabled:
                continue

            buffer_key = self._get_buffer_key(pattern, event)
            self.event_buffers[buffer_key].append(event)

            # Check for pattern matches
            matches = await self._check_pattern_match(pattern, buffer_key)

            for match in matches:
                self.pattern_matches.append(
                    {
                        "pattern_id": pattern_id,
                        "pattern_name": pattern.name,
                        "matched_events": match,
                        "match_timestamp": datetime.now(),
                    }
                )

                # Trigger pattern match handler
                await self._handle_pattern_match(pattern, match)

    def _get_buffer_key(self, pattern: EventPattern, event: StreamEvent) -> str:
        """Get buffer key for pattern and event"""
        if pattern.key_selector:
            key_value = event.payload.get(pattern.key_selector, "default")
            return f"{pattern.id}_{key_value}"
        else:
            return pattern.id

    async def _check_pattern_match(
        self, pattern: EventPattern, buffer_key: str
    ) -> List[List[StreamEvent]]:
        """Check if pattern matches in event buffer"""
        buffer = self.event_buffers[buffer_key]
        matches = []

        # Filter events within time window
        cutoff_time = datetime.now() - timedelta(milliseconds=pattern.time_window_ms)
        recent_events = [e for e in buffer if e.timestamp >= cutoff_time]

        if len(recent_events) < 2:
            return matches

        # Pattern matching logic based on pattern definition
        pattern_def = pattern.pattern_definition

        if pattern_def.get("type") == "sequence":
            matches.extend(self._find_sequence_matches(recent_events, pattern_def))
        elif pattern_def.get("type") == "conjunction":
            matches.extend(self._find_conjunction_matches(recent_events, pattern_def))
        elif pattern_def.get("type") == "disjunction":
            matches.extend(self._find_disjunction_matches(recent_events, pattern_def))
        elif pattern_def.get("type") == "negation":
            matches.extend(self._find_negation_matches(recent_events, pattern_def))

        return matches

    def _find_sequence_matches(
        self, events: List[StreamEvent], pattern_def: Dict[str, Any]
    ) -> List[List[StreamEvent]]:
        """Find sequence pattern matches"""
        matches = []
        sequence_rules = pattern_def.get("sequence", [])

        if not sequence_rules:
            return matches

        # Use dynamic programming to find sequences
        for start_idx in range(len(events)):
            match_sequence = self._match_sequence_from_index(
                events, start_idx, sequence_rules
            )
            if match_sequence:
                matches.append(match_sequence)

        return matches

    def _match_sequence_from_index(
        self,
        events: List[StreamEvent],
        start_idx: int,
        sequence_rules: List[Dict[str, Any]],
    ) -> Optional[List[StreamEvent]]:
        """Match sequence starting from specific index"""
        if not sequence_rules:
            return []

        current_rule = sequence_rules[0]
        remaining_rules = sequence_rules[1:]

        # Find event matching current rule
        for idx in range(start_idx, len(events)):
            event = events[idx]

            if self._event_matches_rule(event, current_rule):
                if not remaining_rules:
                    # Last rule matched
                    return [event]
                else:
                    # Recursively match remaining rules
                    remaining_match = self._match_sequence_from_index(
                        events, idx + 1, remaining_rules
                    )
                    if remaining_match is not None:
                        return [event] + remaining_match

        return None

    def _find_conjunction_matches(
        self, events: List[StreamEvent], pattern_def: Dict[str, Any]
    ) -> List[List[StreamEvent]]:
        """Find conjunction (AND) pattern matches"""
        rules = pattern_def.get("rules", [])
        if not rules:
            return []

        # Find events matching all rules
        matching_events = []
        for rule in rules:
            rule_matches = [e for e in events if self._event_matches_rule(e, rule)]
            if not rule_matches:
                return []  # Conjunction requires all rules to match
            matching_events.extend(rule_matches)

        if matching_events:
            return [matching_events]
        else:
            return []

    def _find_disjunction_matches(
        self, events: List[StreamEvent], pattern_def: Dict[str, Any]
    ) -> List[List[StreamEvent]]:
        """Find disjunction (OR) pattern matches"""
        rules = pattern_def.get("rules", [])
        if not rules:
            return []

        # Find events matching any rule
        matching_events = []
        for rule in rules:
            rule_matches = [e for e in events if self._event_matches_rule(e, rule)]
            matching_events.extend(rule_matches)

        if matching_events:
            return [matching_events]
        else:
            return []

    def _find_negation_matches(
        self, events: List[StreamEvent], pattern_def: Dict[str, Any]
    ) -> List[List[StreamEvent]]:
        """Find negation (NOT) pattern matches"""
        positive_rule = pattern_def.get("positive_rule", {})
        negative_rule = pattern_def.get("negative_rule", {})

        # Find events matching positive rule but not negative rule
        matching_events = []
        for event in events:
            if self._event_matches_rule(
                event, positive_rule
            ) and not self._event_matches_rule(event, negative_rule):
                matching_events.append(event)

        if matching_events:
            return [matching_events]
        else:
            return []

    def _event_matches_rule(self, event: StreamEvent, rule: Dict[str, Any]) -> bool:
        """Check if event matches rule"""
        # Event type filter
        if "event_types" in rule:
            if event.type.value not in rule["event_types"]:
                return False

        # Source filter
        if "sources" in rule:
            if event.source not in rule["sources"]:
                return False

        # Payload conditions
        if "conditions" in rule:
            for condition in rule["conditions"]:
                field = condition.get("field")
                operator = condition.get("operator")
                value = condition.get("value")

                if not self._evaluate_condition(event.payload, field, operator, value):
                    return False

        return True

    def _evaluate_condition(
        self, payload: Dict[str, Any], field: str, operator: str, value: Any
    ) -> bool:
        """Evaluate condition against payload"""
        field_value = payload.get(field)

        if field_value is None:
            return False

        if operator == "equals":
            return field_value == value
        elif operator == "not_equals":
            return field_value != value
        elif operator == "greater_than":
            return field_value > value
        elif operator == "less_than":
            return field_value < value
        elif operator == "contains":
            return value in str(field_value)
        elif operator == "regex":
            return bool(re.match(value, str(field_value)))
        else:
            return False

    async def _handle_pattern_match(
        self, pattern: EventPattern, matched_events: List[StreamEvent]
    ):
        """Handle pattern match detection"""
        logging.info(
            f"Pattern match detected: {pattern.name} with {len(matched_events)} events"
        )

        # Create pattern match event
        StreamEvent(
            id=str(uuid.uuid4()),
            type=EventType.ALERT,
            source="cep_engine",
            payload={
                "pattern_id": pattern.id,
                "pattern_name": pattern.name,
                "matched_event_count": len(matched_events),
                "first_event_timestamp": matched_events[0].timestamp.isoformat(),
                "last_event_timestamp": matched_events[-1].timestamp.isoformat(),
                "matched_event_ids": [e.id for e in matched_events],
            },
            timestamp=datetime.now(),
            correlation_id=f"cep_match_{pattern.id}",
        )

        # Trigger match handlers (could send to alert system, etc.)
        # This would integrate with alerting/notification systems

    def start(self) -> dict:
        """Start CEP engine"""
        self.running = True
        logging.info("Complex Event Processor started")

    def stop(self) -> dict:
        """Stop CEP engine"""
        self.running = False
        logging.info("Complex Event Processor stopped")

    def get_pattern_matches(
        self, pattern_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get pattern matches"""
        if pattern_id:
            return [m for m in self.pattern_matches if m["pattern_id"] == pattern_id]
        else:
            return self.pattern_matches.copy()


class StreamAnalytics:
    """Real-time stream analytics engine"""

    def __init__(self) -> dict:
        self.metrics: Dict[str, Any] = defaultdict(lambda: defaultdict(float))
        self.aggregations: Dict[str, Dict[str, Any]] = {}
        self.time_windows = [60, 300, 900, 3600]  # 1min, 5min, 15min, 1hour
        self.running = False

    async def process_event_for_analytics(self, event: StreamEvent) -> dict:
        """Process event for real-time analytics"""
        if not self.running:
            return

        current_time = datetime.now()

        # Update basic metrics
        await self._update_event_metrics(event, current_time)

        # Update windowed aggregations
        await self._update_windowed_aggregations(event, current_time)

        # Detect anomalies
        await self._detect_anomalies(event, current_time)

    async def _update_event_metrics(
        self, event: StreamEvent, current_time: datetime
    ) -> dict:
        """Update basic event metrics"""
        # Event counts by type
        self.metrics["event_counts"][event.type.value] += 1

        # Event counts by source
        self.metrics["source_counts"][event.source] += 1

        # Throughput metrics
        minute_key = current_time.strftime("%Y-%m-%d %H:%M")
        self.metrics["throughput"][minute_key] += 1

        # Payload size metrics
        payload_size = len(json.dumps(event.payload))
        self.metrics["payload_sizes"]["total"] += payload_size
        self.metrics["payload_sizes"]["count"] += 1
        self.metrics["payload_sizes"]["average"] = (
            self.metrics["payload_sizes"]["total"]
            / self.metrics["payload_sizes"]["count"]
        )

    async def _update_windowed_aggregations(
        self, event: StreamEvent, current_time: datetime
    ):
        """Update windowed aggregations"""
        for window_seconds in self.time_windows:
            window_key = self._get_window_key(current_time, window_seconds)

            if window_key not in self.aggregations:
                self.aggregations[window_key] = {
                    "window_seconds": window_seconds,
                    "start_time": current_time,
                    "event_count": 0,
                    "event_types": defaultdict(int),
                    "sources": defaultdict(int),
                    "numeric_aggregations": defaultdict(
                        lambda: {
                            "sum": 0,
                            "count": 0,
                            "min": float("inf"),
                            "max": float("-inf"),
                        }
                    ),
                }

            agg = self.aggregations[window_key]
            agg["event_count"] += 1
            agg["event_types"][event.type.value] += 1
            agg["sources"][event.source] += 1

            # Aggregate numeric fields
            for field, value in event.payload.items():
                if isinstance(value, (int, float)):
                    num_agg = agg["numeric_aggregations"][field]
                    num_agg["sum"] += value
                    num_agg["count"] += 1
                    num_agg["min"] = min(num_agg["min"], value)
                    num_agg["max"] = max(num_agg["max"], value)
                    num_agg["avg"] = num_agg["sum"] / num_agg["count"]

    def _get_window_key(self, current_time: datetime, window_seconds: int) -> str:
        """Generate window key for time-based aggregations"""
        window_start = int(current_time.timestamp() // window_seconds) * window_seconds
        return f"window_{window_seconds}_{window_start}"

    async def _detect_anomalies(
        self, event: StreamEvent, current_time: datetime
    ) -> dict:
        """Detect anomalies in stream data"""
        # Simple anomaly detection based on historical patterns

        # Check throughput anomalies
        recent_throughput = self._get_recent_throughput(current_time)
        if recent_throughput > self._get_throughput_threshold():
            await self._trigger_anomaly_alert(
                "high_throughput",
                {
                    "current_rate": recent_throughput,
                    "threshold": self._get_throughput_threshold(),
                },
            )

        # Check payload size anomalies
        payload_size = len(json.dumps(event.payload))
        avg_payload_size = self.metrics["payload_sizes"].get("average", 0)

        if avg_payload_size > 0 and payload_size > avg_payload_size * 10:
            await self._trigger_anomaly_alert(
                "large_payload",
                {"current_size": payload_size, "average_size": avg_payload_size},
            )

    def _get_recent_throughput(self, current_time: datetime) -> float:
        """Calculate recent throughput"""
        minute_key = current_time.strftime("%Y-%m-%d %H:%M")
        return self.metrics["throughput"].get(minute_key, 0)

    def _get_throughput_threshold(self) -> float:
        """Get throughput anomaly threshold"""
        # Calculate threshold based on historical data
        throughput_values = list(self.metrics["throughput"].values())
        if len(throughput_values) < 10:
            return 1000  # Default threshold

        avg_throughput = sum(throughput_values) / len(throughput_values)
        return avg_throughput * 3  # 3x average as threshold

    async def _trigger_anomaly_alert(
        self, anomaly_type: str, details: Dict[str, Any]
    ) -> dict:
        """Trigger anomaly alert"""
        logging.warning(f"Anomaly detected: {anomaly_type} - {details}")

        # Create anomaly event
        StreamEvent(
            id=str(uuid.uuid4()),
            type=EventType.ALERT,
            source="stream_analytics",
            payload={
                "anomaly_type": anomaly_type,
                "details": details,
                "detection_timestamp": datetime.now().isoformat(),
            },
            timestamp=datetime.now(),
        )

        # Send to alerting system (would integrate with actual alerting)

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary"""
        return {
            "total_events": sum(self.metrics["event_counts"].values()),
            "event_types": dict(self.metrics["event_counts"]),
            "sources": dict(self.metrics["source_counts"]),
            "average_payload_size": self.metrics["payload_sizes"].get("average", 0),
            "active_windows": len(self.aggregations),
            "last_updated": datetime.now(),
        }

    def start(self) -> dict:
        """Start analytics engine"""
        self.running = True
        logging.info("Stream Analytics engine started")

    def stop(self) -> dict:
        """Stop analytics engine"""
        self.running = False
        logging.info("Stream Analytics engine stopped")


class RealtimeStreamingSystem:
    """Main real-time streaming and event processing system"""

    def __init__(
        self, sdk: MobileERPSDK, kafka_servers: str = "localhost:9092"
    ) -> dict:
        self.sdk = sdk
        self.kafka_servers = kafka_servers
        self.producer = EventProducer(kafka_servers)
        self.consumers: Dict[str, EventConsumer] = {}
        self.processors: Dict[str, StreamProcessor] = {}
        self.cep_engine = ComplexEventProcessor()
        self.analytics_engine = StreamAnalytics()
        self.topics: Dict[str, StreamTopic] = {}

        # System configuration
        self.streaming_enabled = True
        self.cep_enabled = True
        self.analytics_enabled = True

        # Initialize default setup
        self._initialize_default_setup()

        logging.info("Real-time Streaming System initialized")

    def _initialize_default_setup(self) -> dict:
        """Initialize default topics and patterns"""

        # Create default topics
        default_topics = [
            StreamTopic(
                name="user_events",
                partitions=6,
                replication_factor=2,
                retention_ms=7 * 24 * 60 * 60 * 1000,  # 7 days
                format=StreamFormat.JSON,
                tags={"domain": "user_activity"},
            ),
            StreamTopic(
                name="business_events",
                partitions=12,
                replication_factor=3,
                retention_ms=30 * 24 * 60 * 60 * 1000,  # 30 days
                format=StreamFormat.JSON,
                tags={"domain": "business", "criticality": "high"},
            ),
            StreamTopic(
                name="system_metrics",
                partitions=3,
                replication_factor=2,
                retention_ms=24 * 60 * 60 * 1000,  # 24 hours
                format=StreamFormat.JSON,
                tags={"domain": "monitoring"},
            ),
        ]

        for topic in default_topics:
            self.topics[topic.name] = topic

        # Create default CEP patterns

        # Pattern 1: Failed login attempts
        failed_login_pattern = EventPattern(
            id="failed_login_sequence",
            name="Multiple Failed Login Attempts",
            pattern_definition={
                "type": "sequence",
                "sequence": [
                    {
                        "event_types": ["user_action"],
                        "conditions": [
                            {"field": "action", "operator": "equals", "value": "login"},
                            {
                                "field": "status",
                                "operator": "equals",
                                "value": "failed",
                            },
                        ],
                    },
                    {
                        "event_types": ["user_action"],
                        "conditions": [
                            {"field": "action", "operator": "equals", "value": "login"},
                            {
                                "field": "status",
                                "operator": "equals",
                                "value": "failed",
                            },
                        ],
                    },
                    {
                        "event_types": ["user_action"],
                        "conditions": [
                            {"field": "action", "operator": "equals", "value": "login"},
                            {
                                "field": "status",
                                "operator": "equals",
                                "value": "failed",
                            },
                        ],
                    },
                ],
            },
            time_window_ms=300000,  # 5 minutes
            key_selector="user_id",
        )
        self.cep_engine.add_pattern(failed_login_pattern)

        # Pattern 2: High value transaction followed by account change
        suspicious_activity_pattern = EventPattern(
            id="suspicious_transaction_pattern",
            name="Suspicious Transaction Activity",
            pattern_definition={
                "type": "sequence",
                "sequence": [
                    {
                        "event_types": ["transaction"],
                        "conditions": [
                            {
                                "field": "amount",
                                "operator": "greater_than",
                                "value": 10000,
                            }
                        ],
                    },
                    {
                        "event_types": ["user_action"],
                        "conditions": [
                            {
                                "field": "action",
                                "operator": "equals",
                                "value": "account_change",
                            }
                        ],
                    },
                ],
            },
            time_window_ms=1800000,  # 30 minutes
            key_selector="user_id",
        )
        self.cep_engine.add_pattern(suspicious_activity_pattern)

    async def start_streaming(self) -> dict:
        """Start the streaming system"""
        if not self.streaming_enabled:
            logging.info("Streaming is disabled")
            return

        logging.info("Starting real-time streaming system")

        # Start producer
        await self.producer.start()

        # Start CEP engine
        if self.cep_enabled:
            self.cep_engine.start()

        # Start analytics engine
        if self.analytics_enabled:
            self.analytics_engine.start()

        logging.info("Real-time streaming system started")

    async def create_consumer(self, consumer_group: str, topics: List[str]) -> str:
        """Create and start event consumer"""
        consumer_id = f"{consumer_group}_{int(datetime.now().timestamp())}"
        consumer = EventConsumer(consumer_group, self.kafka_servers)

        # Add default event handlers
        consumer.add_event_handler(EventType.USER_ACTION, self._handle_user_event)
        consumer.add_event_handler(
            EventType.BUSINESS_EVENT, self._handle_business_event
        )
        consumer.add_event_handler(EventType.SYSTEM_EVENT, self._handle_system_event)
        consumer.add_event_handler(
            EventType.TRANSACTION, self._handle_transaction_event
        )

        await consumer.start(topics)
        self.consumers[consumer_id] = consumer

        # Start consumption loop
        asyncio.create_task(consumer.consume_events())

        logging.info(f"Consumer created: {consumer_id} for topics: {topics}")
        return consumer_id

    async def _handle_user_event(self, event: StreamEvent) -> dict:
        """Handle user events"""
        # Process through CEP engine
        if self.cep_enabled:
            await self.cep_engine.process_event(event)

        # Process through analytics
        if self.analytics_enabled:
            await self.analytics_engine.process_event_for_analytics(event)

    async def _handle_business_event(self, event: StreamEvent) -> dict:
        """Handle business events"""
        # Process through CEP engine
        if self.cep_enabled:
            await self.cep_engine.process_event(event)

        # Process through analytics
        if self.analytics_enabled:
            await self.analytics_engine.process_event_for_analytics(event)

        # Additional business event processing
        if event.payload.get("event_type") == "order_created":
            await self._process_order_event(event)
        elif event.payload.get("event_type") == "payment_processed":
            await self._process_payment_event(event)

    async def _handle_system_event(self, event: StreamEvent) -> dict:
        """Handle system events"""
        # Process through analytics only (system events are usually metrics)
        if self.analytics_enabled:
            await self.analytics_engine.process_event_for_analytics(event)

    async def _handle_transaction_event(self, event: StreamEvent) -> dict:
        """Handle transaction events"""
        # Process through CEP engine for fraud detection
        if self.cep_enabled:
            await self.cep_engine.process_event(event)

        # Process through analytics
        if self.analytics_enabled:
            await self.analytics_engine.process_event_for_analytics(event)

    async def _process_order_event(self, event: StreamEvent) -> dict:
        """Process order creation event"""
        order_data = event.payload

        # Generate derived events
        inventory_event = StreamEvent(
            id=str(uuid.uuid4()),
            type=EventType.BUSINESS_EVENT,
            source="order_processor",
            payload={
                "event_type": "inventory_check_required",
                "order_id": order_data.get("order_id"),
                "products": order_data.get("products", []),
            },
            timestamp=datetime.now(),
            correlation_id=event.correlation_id,
            causation_id=event.id,
        )

        await self.producer.send_event("business_events", inventory_event)

    async def _process_payment_event(self, event: StreamEvent) -> dict:
        """Process payment event"""
        payment_data = event.payload

        # Generate fulfillment event
        fulfillment_event = StreamEvent(
            id=str(uuid.uuid4()),
            type=EventType.BUSINESS_EVENT,
            source="payment_processor",
            payload={
                "event_type": "fulfillment_required",
                "order_id": payment_data.get("order_id"),
                "payment_amount": payment_data.get("amount"),
            },
            timestamp=datetime.now(),
            correlation_id=event.correlation_id,
            causation_id=event.id,
        )

        await self.producer.send_event("business_events", fulfillment_event)

    async def publish_event(self, topic: str, event: StreamEvent) -> bool:
        """Publish event to stream"""
        return await self.producer.send_event(topic, event)

    async def publish_events_batch(self, topic: str, events: List[StreamEvent]) -> int:
        """Publish batch of events"""
        return await self.producer.send_batch(topic, events)

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        producer_metrics = self.producer.get_metrics()

        consumer_metrics = {}
        for consumer_id, consumer in self.consumers.items():
            consumer_metrics[consumer_id] = consumer.get_metrics()

        cep_matches = (
            len(self.cep_engine.get_pattern_matches()) if self.cep_enabled else 0
        )
        analytics_summary = (
            self.analytics_engine.get_analytics_summary()
            if self.analytics_enabled
            else {}
        )

        return {
            "timestamp": datetime.now(),
            "streaming_enabled": self.streaming_enabled,
            "cep_enabled": self.cep_enabled,
            "analytics_enabled": self.analytics_enabled,
            "topics": len(self.topics),
            "consumers": len(self.consumers),
            "processors": len(self.processors),
            "producer_metrics": producer_metrics,
            "consumer_metrics": consumer_metrics,
            "cep_pattern_matches": cep_matches,
            "analytics_summary": analytics_summary,
        }

    async def stop_streaming(self) -> dict:
        """Stop the streaming system"""
        logging.info("Stopping real-time streaming system")

        # Stop consumers
        for consumer in self.consumers.values():
            await consumer.stop()

        # Stop processors
        for processor in self.processors.values():
            processor.stop()

        # Stop engines
        self.cep_engine.stop()
        self.analytics_engine.stop()

        # Stop producer
        await self.producer.stop()

        logging.info("Real-time streaming system stopped")


# Example usage and testing
async def main() -> None:
    """Example usage of the Real-time Streaming & Event Processing system"""

    # Initialize SDK (mock)
    class MockMobileERPSDK:
        pass

    sdk = MockMobileERPSDK()

    # Create streaming system
    streaming_system = RealtimeStreamingSystem(sdk)

    # Start streaming
    print("Starting real-time streaming system...")
    await streaming_system.start_streaming()

    # Create consumer
    await streaming_system.create_consumer(
        "test_consumer_group", ["user_events", "business_events", "system_metrics"]
    )

    # Generate and publish sample events
    print("Publishing sample events...")

    # User events
    user_events = [
        StreamEvent(
            id=str(uuid.uuid4()),
            type=EventType.USER_ACTION,
            source="web_app",
            payload={
                "user_id": "user_123",
                "action": "login",
                "status": "failed",
                "ip_address": "192.168.1.100",
            },
            timestamp=datetime.now(),
        ),
        StreamEvent(
            id=str(uuid.uuid4()),
            type=EventType.USER_ACTION,
            source="web_app",
            payload={
                "user_id": "user_123",
                "action": "login",
                "status": "failed",
                "ip_address": "192.168.1.100",
            },
            timestamp=datetime.now(),
        ),
        StreamEvent(
            id=str(uuid.uuid4()),
            type=EventType.USER_ACTION,
            source="web_app",
            payload={
                "user_id": "user_123",
                "action": "login",
                "status": "failed",
                "ip_address": "192.168.1.100",
            },
            timestamp=datetime.now(),
        ),
    ]

    # Publish user events (should trigger CEP pattern)
    for event in user_events:
        await streaming_system.publish_event("user_events", event)
        await asyncio.sleep(0.1)  # Small delay

    # Transaction events
    transaction_event = StreamEvent(
        id=str(uuid.uuid4()),
        type=EventType.TRANSACTION,
        source="payment_system",
        payload={
            "user_id": "user_456",
            "transaction_id": "txn_789",
            "amount": 15000.0,
            "currency": "USD",
            "status": "completed",
        },
        timestamp=datetime.now(),
    )

    await streaming_system.publish_event("business_events", transaction_event)

    # Account change event (should trigger CEP pattern with transaction)
    account_change_event = StreamEvent(
        id=str(uuid.uuid4()),
        type=EventType.USER_ACTION,
        source="account_service",
        payload={
            "user_id": "user_456",
            "action": "account_change",
            "field": "email",
            "old_value": "old@example.com",
            "new_value": "new@example.com",
        },
        timestamp=datetime.now(),
    )

    await streaming_system.publish_event("user_events", account_change_event)

    # Wait for processing
    print("Waiting for event processing...")
    await asyncio.sleep(5)

    # Get system status
    status = streaming_system.get_system_status()
    print(f"Streaming System Status: {json.dumps(status, indent=2, default=str)}")

    # Check CEP pattern matches
    pattern_matches = streaming_system.cep_engine.get_pattern_matches()
    print(f"CEP Pattern Matches: {len(pattern_matches)}")
    for match in pattern_matches:
        print(
            f"  - Pattern: {match['pattern_name']}, Events: {len(match['matched_events'])}"
        )

    # Stop streaming
    await streaming_system.stop_streaming()

    print("Real-time streaming demonstration completed")


if __name__ == "__main__":
    asyncio.run(main())
