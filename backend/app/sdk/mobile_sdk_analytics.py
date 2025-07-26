"""Mobile SDK Analytics & Metrics Module - CC02 v72.0 Day 17."""

from __future__ import annotations

import asyncio
import statistics
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import psutil
from pydantic import BaseModel, Field

from .mobile_sdk_core import MobileERPSDK


class EventType(str, Enum):
    """Analytics event types."""

    SCREEN_VIEW = "screen_view"
    USER_ACTION = "user_action"
    API_CALL = "api_call"
    ERROR = "error"
    PERFORMANCE = "performance"
    CUSTOM = "custom"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    APP_LAUNCH = "app_launch"
    APP_BACKGROUND = "app_background"
    APP_FOREGROUND = "app_foreground"
    FEATURE_USAGE = "feature_usage"
    CRASH = "crash"


class MetricType(str, Enum):
    """Performance metric types."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"


class AnalyticsEvent(BaseModel):
    """Analytics event model."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    event_name: str
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    device_id: Optional[str] = None

    # Event properties
    properties: Dict[str, Any] = Field(default_factory=dict)
    user_properties: Dict[str, Any] = Field(default_factory=dict)

    # Context information
    screen_name: Optional[str] = None
    app_version: Optional[str] = None
    platform: Optional[str] = None
    os_version: Optional[str] = None
    device_model: Optional[str] = None
    network_type: Optional[str] = None

    # Performance metrics
    duration_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None

    # Location
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None

    # Custom dimensions
    custom_dimensions: Dict[str, str] = Field(default_factory=dict)
    custom_metrics: Dict[str, float] = Field(default_factory=dict)


class PerformanceMetric(BaseModel):
    """Performance metric model."""

    metric_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metric_type: MetricType
    metric_name: str
    value: Union[int, float]
    timestamp: datetime = Field(default_factory=datetime.now)
    tags: Dict[str, str] = Field(default_factory=dict)
    unit: Optional[str] = None

    # Histogram specific
    buckets: Optional[Dict[str, int]] = None

    # Rate specific
    rate_per_second: Optional[float] = None

    # Context
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    device_id: Optional[str] = None


class SessionInfo(BaseModel):
    """User session information."""

    session_id: str
    user_id: Optional[str]
    device_id: Optional[str]
    started_at: datetime
    last_activity: datetime
    screen_views: int = 0
    user_actions: int = 0
    api_calls: int = 0
    errors: int = 0
    crashes: int = 0
    total_duration_ms: float = 0
    is_active: bool = True

    # Performance aggregates
    avg_response_time_ms: float = 0
    memory_peak_mb: float = 0
    cpu_peak_percent: float = 0

    # User engagement metrics
    feature_usage: Dict[str, int] = Field(default_factory=dict)
    screen_time: Dict[str, float] = Field(default_factory=dict)


class UserCohort(BaseModel):
    """User cohort definition."""

    cohort_id: str
    name: str
    description: str
    criteria: Dict[str, Any]
    created_at: datetime
    users_count: int = 0
    retention_rates: Dict[str, float] = Field(default_factory=dict)


class FunnelStep(BaseModel):
    """Funnel analysis step."""

    step_name: str
    event_criteria: Dict[str, Any]
    users_entered: int = 0
    users_completed: int = 0
    conversion_rate: float = 0.0
    avg_time_to_complete_ms: float = 0.0


class AnalyticsFunnel(BaseModel):
    """Analytics funnel for conversion tracking."""

    funnel_id: str
    name: str
    description: str
    steps: List[FunnelStep]
    time_window_hours: int = 24
    created_at: datetime
    last_calculated: Optional[datetime] = None


class PerformanceMonitor:
    """System performance monitoring."""

    def __init__(self) -> dict:
        self._monitoring = False
        self._metrics_buffer: deque = deque(maxlen=1000)
        self._monitor_task: Optional[asyncio.Task] = None
        self._callbacks: List[Callable[[Dict[str, Any]], None]] = []

    def add_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Add performance callback."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Remove performance callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def start_monitoring(self, interval_seconds: float = 10.0) -> None:
        """Start performance monitoring."""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval_seconds))

    async def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    async def _monitor_loop(self, interval_seconds: float) -> None:
        """Performance monitoring loop."""
        while self._monitoring:
            try:
                metrics = await self._collect_metrics()
                self._metrics_buffer.append(metrics)

                # Notify callbacks
                for callback in self._callbacks:
                    try:
                        callback(metrics)
                    except Exception as e:
                        print(f"[SDK] Performance callback error: {e}")

                await asyncio.sleep(interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[SDK] Performance monitoring error: {e}")
                await asyncio.sleep(interval_seconds)

    async def _collect_metrics(self) -> Dict[str, Any]:
        """Collect current performance metrics."""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()

        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / 1024 / 1024
        memory_available_mb = memory.available / 1024 / 1024

        # Disk metrics
        disk = psutil.disk_usage("/")
        disk_percent = (disk.used / disk.total) * 100
        disk_free_gb = disk.free / 1024 / 1024 / 1024

        # Network metrics (simplified)
        network = psutil.net_io_counters()
        network_sent_mb = network.bytes_sent / 1024 / 1024
        network_recv_mb = network.bytes_recv / 1024 / 1024

        return {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
            },
            "memory": {
                "percent": memory_percent,
                "used_mb": memory_used_mb,
                "available_mb": memory_available_mb,
                "total_mb": memory.total / 1024 / 1024,
            },
            "disk": {
                "percent": disk_percent,
                "free_gb": disk_free_gb,
                "total_gb": disk.total / 1024 / 1024 / 1024,
            },
            "network": {
                "sent_mb": network_sent_mb,
                "recv_mb": network_recv_mb,
            },
        }

    def get_recent_metrics(self, minutes: int = 10) -> List[Dict[str, Any]]:
        """Get recent performance metrics."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)

        recent_metrics = []
        for metrics in self._metrics_buffer:
            if datetime.fromisoformat(metrics["timestamp"]) >= cutoff_time:
                recent_metrics.append(metrics)

        return recent_metrics

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        if not self._metrics_buffer:
            return {}

        # Extract metrics for analysis
        cpu_values = [m["cpu"]["percent"] for m in self._metrics_buffer]
        memory_values = [m["memory"]["percent"] for m in self._metrics_buffer]

        summary = {
            "measurement_period_minutes": len(self._metrics_buffer)
            / 6,  # Assuming 10s intervals
            "cpu": {
                "avg_percent": statistics.mean(cpu_values) if cpu_values else 0,
                "max_percent": max(cpu_values) if cpu_values else 0,
                "min_percent": min(cpu_values) if cpu_values else 0,
            },
            "memory": {
                "avg_percent": statistics.mean(memory_values) if memory_values else 0,
                "max_percent": max(memory_values) if memory_values else 0,
                "min_percent": min(memory_values) if memory_values else 0,
            },
            "sample_count": len(self._metrics_buffer),
        }

        return summary


class ErrorTracker:
    """Error and crash tracking."""

    def __init__(self, sdk: MobileERPSDK) -> dict:
        self.sdk = sdk
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._recent_errors: deque = deque(maxlen=100)
        self._error_callbacks: List[Callable[[Dict[str, Any]], None]] = []

    def add_error_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Add error callback."""
        self._error_callbacks.append(callback)

    def remove_error_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Remove error callback."""
        if callback in self._error_callbacks:
            self._error_callbacks.remove(callback)

    def track_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: str = "error",
    ) -> str:
        """Track error occurrence."""
        error_id = str(uuid.uuid4())
        error_type = type(error).__name__
        error_message = str(error)

        error_data = {
            "error_id": error_id,
            "error_type": error_type,
            "error_message": error_message,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
            "context": context or {},
            "stack_trace": self._get_stack_trace(error),
        }

        # Update counters
        self._error_counts[error_type] += 1
        self._recent_errors.append(error_data)

        # Notify callbacks
        for callback in self._error_callbacks:
            try:
                callback(error_data)
            except Exception as e:
                print(f"[SDK] Error callback failed: {e}")

        # Send to analytics
        asyncio.create_task(self._send_error_event(error_data))

        return error_id

    def track_crash(
        self, crash_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Track application crash."""
        crash_id = str(uuid.uuid4())

        crash_event = {
            "crash_id": crash_id,
            "timestamp": datetime.now().isoformat(),
            "crash_data": crash_data,
            "context": context or {},
        }

        # Update counters
        self._error_counts["crash"] += 1
        self._recent_errors.append(crash_event)

        # Send crash event
        asyncio.create_task(self._send_crash_event(crash_event))

        return crash_id

    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary statistics."""
        total_errors = sum(self._error_counts.values())

        # Calculate error rates
        recent_errors = [
            e
            for e in self._recent_errors
            if datetime.fromisoformat(e["timestamp"])
            >= datetime.now() - timedelta(hours=1)
        ]

        return {
            "total_errors": total_errors,
            "error_types": dict(self._error_counts),
            "recent_errors_count": len(recent_errors),
            "error_rate_per_hour": len(recent_errors),
            "most_common_errors": sorted(
                self._error_counts.items(), key=lambda x: x[1], reverse=True
            )[:5],
        }

    def _get_stack_trace(self, error: Exception) -> Optional[str]:
        """Get stack trace from exception."""
        import traceback

        try:
            return "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )
        except Exception:
            return None

    async def _send_error_event(self, error_data: Dict[str, Any]) -> None:
        """Send error event to analytics."""
        try:
            await self.sdk.http_client.post(
                "mobile-erp/analytics/events",
                {
                    "event_type": "error",
                    "event_name": "application_error",
                    "properties": error_data,
                },
                params={
                    "organization_id": self.sdk.config.organization_id,
                    "user_id": "current_user",
                    "device_id": self.sdk.auth_manager.device_info.device_id
                    if self.sdk.auth_manager.device_info
                    else "unknown",
                },
            )
        except Exception as e:
            print(f"[SDK] Failed to send error event: {e}")

    async def _send_crash_event(self, crash_data: Dict[str, Any]) -> None:
        """Send crash event to analytics."""
        try:
            await self.sdk.http_client.post(
                "mobile-erp/analytics/events",
                {
                    "event_type": "crash",
                    "event_name": "application_crash",
                    "properties": crash_data,
                },
                params={
                    "organization_id": self.sdk.config.organization_id,
                    "user_id": "current_user",
                    "device_id": self.sdk.auth_manager.device_info.device_id
                    if self.sdk.auth_manager.device_info
                    else "unknown",
                },
            )
        except Exception as e:
            print(f"[SDK] Failed to send crash event: {e}")


class UserBehaviorAnalyzer:
    """Analyzes user behavior patterns."""

    def __init__(self) -> dict:
        self._user_sessions: Dict[str, SessionInfo] = {}
        self._user_journeys: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._feature_usage: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self._screen_flows: Dict[Tuple[str, str], int] = defaultdict(int)

    def start_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> SessionInfo:
        """Start user session tracking."""
        session = SessionInfo(
            session_id=session_id,
            user_id=user_id,
            device_id=device_id,
            started_at=datetime.now(),
            last_activity=datetime.now(),
        )

        self._user_sessions[session_id] = session
        return session

    def end_session(self, session_id: str) -> Optional[SessionInfo]:
        """End user session tracking."""
        session = self._user_sessions.get(session_id)
        if session:
            session.is_active = False
            session.total_duration_ms = (
                datetime.now() - session.started_at
            ).total_seconds() * 1000

            # Calculate averages
            if session.api_calls > 0:
                session.avg_response_time_ms = (
                    session.total_duration_ms / session.api_calls
                )

        return session

    def track_screen_view(
        self,
        session_id: str,
        screen_name: str,
        duration_ms: Optional[float] = None,
        previous_screen: Optional[str] = None,
    ) -> None:
        """Track screen view event."""
        session = self._user_sessions.get(session_id)
        if session:
            session.screen_views += 1
            session.last_activity = datetime.now()

            if duration_ms:
                session.screen_time[screen_name] = (
                    session.screen_time.get(screen_name, 0) + duration_ms
                )

            # Track screen flow
            if previous_screen:
                flow_key = (previous_screen, screen_name)
                self._screen_flows[flow_key] += 1

            # Add to user journey
            if session.user_id:
                self._user_journeys[session.user_id].append(
                    {
                        "type": "screen_view",
                        "screen_name": screen_name,
                        "timestamp": datetime.now().isoformat(),
                        "duration_ms": duration_ms,
                    }
                )

    def track_user_action(
        self,
        session_id: str,
        action_name: str,
        feature_name: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track user action event."""
        session = self._user_sessions.get(session_id)
        if session:
            session.user_actions += 1
            session.last_activity = datetime.now()

            # Track feature usage
            if feature_name:
                session.feature_usage[feature_name] = (
                    session.feature_usage.get(feature_name, 0) + 1
                )

                if session.user_id:
                    self._feature_usage[session.user_id][feature_name] += 1

            # Add to user journey
            if session.user_id:
                self._user_journeys[session.user_id].append(
                    {
                        "type": "user_action",
                        "action_name": action_name,
                        "feature_name": feature_name,
                        "timestamp": datetime.now().isoformat(),
                        "properties": properties or {},
                    }
                )

    def track_api_call(
        self,
        session_id: str,
        endpoint: str,
        method: str,
        response_time_ms: float,
        status_code: int,
    ) -> None:
        """Track API call performance."""
        session = self._user_sessions.get(session_id)
        if session:
            session.api_calls += 1
            session.last_activity = datetime.now()

            # Update response time average
            current_avg = session.avg_response_time_ms
            session.avg_response_time_ms = (
                current_avg * (session.api_calls - 1) + response_time_ms
            ) / session.api_calls

            # Track errors
            if status_code >= 400:
                session.errors += 1

    def update_performance_metrics(
        self, session_id: str, memory_usage_mb: float, cpu_usage_percent: float
    ) -> None:
        """Update session performance metrics."""
        session = self._user_sessions.get(session_id)
        if session:
            session.memory_peak_mb = max(session.memory_peak_mb, memory_usage_mb)
            session.cpu_peak_percent = max(session.cpu_peak_percent, cpu_usage_percent)

    def get_user_behavior_summary(self, user_id: str) -> Dict[str, Any]:
        """Get user behavior summary."""
        user_sessions = [
            s for s in self._user_sessions.values() if s.user_id == user_id
        ]

        if not user_sessions:
            return {}

        # Calculate aggregates
        total_sessions = len(user_sessions)
        total_duration_hours = (
            sum(s.total_duration_ms for s in user_sessions) / 1000 / 3600
        )
        total_screen_views = sum(s.screen_views for s in user_sessions)
        total_actions = sum(s.user_actions for s in user_sessions)

        # Feature usage
        feature_usage = self._feature_usage.get(user_id, {})
        most_used_features = sorted(
            feature_usage.items(), key=lambda x: x[1], reverse=True
        )[:5]

        # User journey
        journey = self._user_journeys.get(user_id, [])

        return {
            "user_id": user_id,
            "total_sessions": total_sessions,
            "total_duration_hours": total_duration_hours,
            "avg_session_duration_minutes": (total_duration_hours * 60) / total_sessions
            if total_sessions > 0
            else 0,
            "total_screen_views": total_screen_views,
            "total_actions": total_actions,
            "feature_usage": dict(feature_usage),
            "most_used_features": most_used_features,
            "journey_events": len(journey),
            "last_activity": max(s.last_activity for s in user_sessions)
            if user_sessions
            else None,
        }

    def get_screen_flow_analysis(self) -> Dict[str, Any]:
        """Get screen flow analysis."""
        # Most common flows
        most_common_flows = sorted(
            self._screen_flows.items(), key=lambda x: x[1], reverse=True
        )[:10]

        # Screen popularity
        screen_visits = defaultdict(int)
        for (from_screen, to_screen), count in self._screen_flows.items():
            screen_visits[to_screen] += count

        popular_screens = sorted(
            screen_visits.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return {
            "most_common_flows": [
                {"from": flow[0][0], "to": flow[0][1], "count": flow[1]}
                for flow in most_common_flows
            ],
            "popular_screens": [
                {"screen": screen[0], "visits": screen[1]} for screen in popular_screens
            ],
            "total_flows": len(self._screen_flows),
            "unique_screens": len(
                set(screen for flow in self._screen_flows.keys() for screen in flow)
            ),
        }


class FunnelAnalyzer:
    """Analyzes user conversion funnels."""

    def __init__(self) -> dict:
        self._funnels: Dict[str, AnalyticsFunnel] = {}
        self._user_events: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def create_funnel(
        self,
        funnel_id: str,
        name: str,
        description: str,
        steps: List[Dict[str, Any]],
        time_window_hours: int = 24,
    ) -> AnalyticsFunnel:
        """Create conversion funnel."""
        funnel_steps = [
            FunnelStep(step_name=step["name"], event_criteria=step["criteria"])
            for step in steps
        ]

        funnel = AnalyticsFunnel(
            funnel_id=funnel_id,
            name=name,
            description=description,
            steps=funnel_steps,
            time_window_hours=time_window_hours,
            created_at=datetime.now(),
        )

        self._funnels[funnel_id] = funnel
        return funnel

    def track_event(
        self,
        user_id: str,
        event_name: str,
        properties: Dict[str, Any],
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Track event for funnel analysis."""
        event = {
            "event_name": event_name,
            "properties": properties,
            "timestamp": timestamp or datetime.now(),
        }

        self._user_events[user_id].append(event)

    def calculate_funnel(self, funnel_id: str) -> Optional[AnalyticsFunnel]:
        """Calculate funnel conversion rates."""
        funnel = self._funnels.get(funnel_id)
        if not funnel:
            return None

        time_window = timedelta(hours=funnel.time_window_hours)
        now = datetime.now()

        # Track users through funnel steps
        step_completions: Dict[int, Set[str]] = defaultdict(set)
        step_timings: Dict[int, List[float]] = defaultdict(list)

        for user_id, events in self._user_events.items():
            # Filter events within time window
            recent_events = [e for e in events if now - e["timestamp"] <= time_window]

            # Track user through funnel
            user_step_times: Dict[int, datetime] = {}

            for step_idx, step in enumerate(funnel.steps):
                step_completed = False

                for event in recent_events:
                    if self._event_matches_criteria(event, step.event_criteria):
                        step_completions[step_idx].add(user_id)
                        user_step_times[step_idx] = event["timestamp"]
                        step_completed = True
                        break

                # If user didn't complete this step, they can't complete later steps
                if not step_completed:
                    break

            # Calculate step completion times
            for step_idx in range(1, len(funnel.steps)):
                if step_idx in user_step_times and (step_idx - 1) in user_step_times:
                    duration = (
                        user_step_times[step_idx] - user_step_times[step_idx - 1]
                    ).total_seconds() * 1000
                    step_timings[step_idx].append(duration)

        # Update funnel statistics
        for step_idx, step in enumerate(funnel.steps):
            step.users_completed = len(step_completions[step_idx])

            if step_idx == 0:
                step.users_entered = step.users_completed
                step.conversion_rate = 100.0  # First step is always 100%
            else:
                prev_step_users = len(step_completions[step_idx - 1])
                step.users_entered = prev_step_users
                step.conversion_rate = (
                    (step.users_completed / prev_step_users * 100)
                    if prev_step_users > 0
                    else 0
                )

            # Average completion time
            if step_idx in step_timings and step_timings[step_idx]:
                step.avg_time_to_complete_ms = statistics.mean(step_timings[step_idx])

        funnel.last_calculated = now
        return funnel

    def _event_matches_criteria(
        self, event: Dict[str, Any], criteria: Dict[str, Any]
    ) -> bool:
        """Check if event matches funnel step criteria."""
        # Simple criteria matching
        if "event_name" in criteria:
            if event["event_name"] != criteria["event_name"]:
                return False

        if "properties" in criteria:
            for key, value in criteria["properties"].items():
                if event["properties"].get(key) != value:
                    return False

        return True

    def get_funnel_report(self, funnel_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive funnel report."""
        funnel = self.calculate_funnel(funnel_id)
        if not funnel:
            return None

        # Calculate overall conversion rate
        if funnel.steps:
            first_step_users = funnel.steps[0].users_entered
            last_step_users = funnel.steps[-1].users_completed
            overall_conversion = (
                (last_step_users / first_step_users * 100)
                if first_step_users > 0
                else 0
            )
        else:
            overall_conversion = 0

        # Identify drop-off points
        drop_offs = []
        for i in range(1, len(funnel.steps)):
            current_step = funnel.steps[i]
            prev_step = funnel.steps[i - 1]
            drop_off_rate = 100 - current_step.conversion_rate

            if drop_off_rate > 20:  # Significant drop-off
                drop_offs.append(
                    {
                        "from_step": prev_step.step_name,
                        "to_step": current_step.step_name,
                        "drop_off_rate": drop_off_rate,
                        "users_lost": prev_step.users_completed
                        - current_step.users_completed,
                    }
                )

        return {
            "funnel_id": funnel.funnel_id,
            "name": funnel.name,
            "overall_conversion_rate": overall_conversion,
            "total_users_entered": funnel.steps[0].users_entered if funnel.steps else 0,
            "total_users_converted": funnel.steps[-1].users_completed
            if funnel.steps
            else 0,
            "steps": [
                {
                    "step_name": step.step_name,
                    "users_entered": step.users_entered,
                    "users_completed": step.users_completed,
                    "conversion_rate": step.conversion_rate,
                    "avg_time_to_complete_ms": step.avg_time_to_complete_ms,
                }
                for step in funnel.steps
            ],
            "drop_off_points": drop_offs,
            "last_calculated": funnel.last_calculated.isoformat()
            if funnel.last_calculated
            else None,
        }


class AnalyticsCollector:
    """Main analytics data collector."""

    def __init__(self, sdk: MobileERPSDK) -> dict:
        self.sdk = sdk
        self._event_buffer: deque = deque(maxlen=1000)
        self._metric_buffer: deque = deque(maxlen=1000)
        self._flush_interval = 30  # seconds
        self._flush_task: Optional[asyncio.Task] = None
        self._collecting = False

        # Components
        self.performance_monitor = PerformanceMonitor()
        self.error_tracker = ErrorTracker(sdk)
        self.behavior_analyzer = UserBehaviorAnalyzer()
        self.funnel_analyzer = FunnelAnalyzer()

        # Current session
        self._current_session_id: Optional[str] = None
        self._current_screen: Optional[str] = None
        self._screen_start_time: Optional[datetime] = None

    async def initialize(self) -> None:
        """Initialize analytics collector."""
        self._collecting = True

        # Start periodic flushing
        self._flush_task = asyncio.create_task(self._flush_loop())

        # Start performance monitoring
        await self.performance_monitor.start_monitoring()

        # Add performance callback
        self.performance_monitor.add_callback(self._on_performance_data)

        # Add error callback
        self.error_tracker.add_error_callback(self._on_error_data)

        # Register SDK event handlers
        self.sdk.events.on("auth.success", self._on_auth_success)
        self.sdk.events.on("sdk.closed", self._on_sdk_closed)

    async def close(self) -> None:
        """Close analytics collector."""
        self._collecting = False

        # Stop components
        await self.performance_monitor.stop_monitoring()

        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Final flush
        await self._flush_events()
        await self._flush_metrics()

    def start_session(self, user_id: Optional[str] = None) -> str:
        """Start analytics session."""
        session_id = str(uuid.uuid4())
        self._current_session_id = session_id

        device_id = (
            self.sdk.auth_manager.device_info.device_id
            if self.sdk.auth_manager.device_info
            else None
        )

        # Start behavior tracking
        self.behavior_analyzer.start_session(session_id, user_id, device_id)

        # Track session start event
        self.track_event(
            EventType.SESSION_START,
            "session_started",
            properties={"session_id": session_id},
        )

        return session_id

    def end_session(self) -> None:
        """End current analytics session."""
        if not self._current_session_id:
            return

        # End screen view if active
        if self._current_screen:
            self._end_screen_view()

        # End behavior tracking
        self.behavior_analyzer.end_session(self._current_session_id)

        # Track session end event
        self.track_event(
            EventType.SESSION_END,
            "session_ended",
            properties={"session_id": self._current_session_id},
        )

        self._current_session_id = None

    def track_event(
        self,
        event_type: EventType,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None,
        user_properties: Optional[Dict[str, Any]] = None,
        custom_dimensions: Optional[Dict[str, str]] = None,
        custom_metrics: Optional[Dict[str, float]] = None,
    ) -> str:
        """Track analytics event."""
        device_info = self.sdk.auth_manager.device_info

        event = AnalyticsEvent(
            event_type=event_type,
            event_name=event_name,
            session_id=self._current_session_id,
            properties=properties or {},
            user_properties=user_properties or {},
            custom_dimensions=custom_dimensions or {},
            custom_metrics=custom_metrics or {},
            screen_name=self._current_screen,
            app_version=device_info.app_version if device_info else None,
            platform=device_info.platform if device_info else None,
            os_version=device_info.os_version if device_info else None,
            device_model=device_info.device_model if device_info else None,
            device_id=device_info.device_id if device_info else None,
        )

        self._event_buffer.append(event)

        # Update behavior analyzer
        if event_type == EventType.SCREEN_VIEW and self._current_session_id:
            self.behavior_analyzer.track_screen_view(
                self._current_session_id,
                event_name,
                properties.get("duration_ms") if properties else None,
                properties.get("previous_screen") if properties else None,
            )
        elif event_type == EventType.USER_ACTION and self._current_session_id:
            self.behavior_analyzer.track_user_action(
                self._current_session_id,
                event_name,
                properties.get("feature_name") if properties else None,
                properties,
            )

        # Update funnel analyzer
        if self._current_session_id:
            # Assuming we have a user_id from session
            user_id = "current_user"  # This should come from auth manager
            self.funnel_analyzer.track_event(user_id, event_name, properties or {})

        return event.event_id

    def track_screen_view(
        self, screen_name: str, properties: Optional[Dict[str, Any]] = None
    ) -> str:
        """Track screen view event."""
        # End previous screen view
        if self._current_screen:
            self._end_screen_view()

        # Start new screen view
        self._current_screen = screen_name
        self._screen_start_time = datetime.now()

        return self.track_event(
            EventType.SCREEN_VIEW, screen_name, properties=properties
        )

    def track_user_action(
        self,
        action_name: str,
        feature_name: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Track user action event."""
        action_properties = properties or {}
        if feature_name:
            action_properties["feature_name"] = feature_name

        return self.track_event(
            EventType.USER_ACTION, action_name, properties=action_properties
        )

    def track_api_call(
        self,
        endpoint: str,
        method: str,
        response_time_ms: float,
        status_code: int,
        request_size_bytes: Optional[int] = None,
        response_size_bytes: Optional[int] = None,
    ) -> str:
        """Track API call performance."""
        properties = {
            "endpoint": endpoint,
            "method": method,
            "response_time_ms": response_time_ms,
            "status_code": status_code,
        }

        if request_size_bytes:
            properties["request_size_bytes"] = request_size_bytes
        if response_size_bytes:
            properties["response_size_bytes"] = response_size_bytes

        # Update behavior analyzer
        if self._current_session_id:
            self.behavior_analyzer.track_api_call(
                self._current_session_id,
                endpoint,
                method,
                response_time_ms,
                status_code,
            )

        return self.track_event(
            EventType.API_CALL, f"{method}_{endpoint}", properties=properties
        )

    def track_performance_metric(
        self,
        metric_type: MetricType,
        metric_name: str,
        value: Union[int, float],
        tags: Optional[Dict[str, str]] = None,
        unit: Optional[str] = None,
    ) -> str:
        """Track performance metric."""
        metric = PerformanceMetric(
            metric_type=metric_type,
            metric_name=metric_name,
            value=value,
            tags=tags or {},
            unit=unit,
            session_id=self._current_session_id,
            device_id=(
                self.sdk.auth_manager.device_info.device_id
                if self.sdk.auth_manager.device_info
                else None
            ),
        )

        self._metric_buffer.append(metric)
        return metric.metric_id

    def track_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: str = "error",
    ) -> str:
        """Track error occurrence."""
        error_id = self.error_tracker.track_error(error, context, severity)

        # Also create analytics event
        self.track_event(
            EventType.ERROR,
            "application_error",
            properties={
                "error_id": error_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "severity": severity,
                "context": context or {},
            },
        )

        return error_id

    def track_crash(
        self, crash_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Track application crash."""
        crash_id = self.error_tracker.track_crash(crash_data, context)

        # Also create analytics event
        self.track_event(
            EventType.CRASH,
            "application_crash",
            properties={
                "crash_id": crash_id,
                "crash_data": crash_data,
                "context": context or {},
            },
        )

        return crash_id

    def _end_screen_view(self) -> None:
        """End current screen view and record duration."""
        if self._current_screen and self._screen_start_time:
            duration_ms = (
                datetime.now() - self._screen_start_time
            ).total_seconds() * 1000

            # Update behavior analyzer
            if self._current_session_id:
                self.behavior_analyzer.track_screen_view(
                    self._current_session_id, self._current_screen, duration_ms
                )

    def _on_performance_data(self, metrics: Dict[str, Any]) -> None:
        """Handle performance monitoring data."""
        # Track key performance metrics
        self.track_performance_metric(
            MetricType.GAUGE,
            "cpu_usage_percent",
            metrics["cpu"]["percent"],
            unit="percent",
        )

        self.track_performance_metric(
            MetricType.GAUGE,
            "memory_usage_percent",
            metrics["memory"]["percent"],
            unit="percent",
        )

        # Update session performance
        if self._current_session_id:
            self.behavior_analyzer.update_performance_metrics(
                self._current_session_id,
                metrics["memory"]["used_mb"],
                metrics["cpu"]["percent"],
            )

    def _on_error_data(self, error_data: Dict[str, Any]) -> None:
        """Handle error tracking data."""
        # Error data is already tracked by error tracker
        pass

    async def _on_auth_success(self, token: Any) -> None:
        """Handle authentication success."""
        # Start new session on auth
        self.start_session("current_user")  # Should get real user ID

    async def _on_sdk_closed(self) -> None:
        """Handle SDK closed event."""
        self.end_session()

    async def _flush_loop(self) -> None:
        """Periodic flush loop."""
        while self._collecting:
            try:
                await asyncio.sleep(self._flush_interval)
                await self._flush_events()
                await self._flush_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[SDK] Analytics flush error: {e}")

    async def _flush_events(self) -> None:
        """Flush events to server."""
        if not self._event_buffer:
            return

        events_to_send = list(self._event_buffer)
        self._event_buffer.clear()

        try:
            # Send events in batches
            batch_size = 50
            for i in range(0, len(events_to_send), batch_size):
                batch = events_to_send[i : i + batch_size]

                batch_data = {
                    "events": [event.dict() for event in batch],
                    "batch_timestamp": datetime.now().isoformat(),
                }

                await self.sdk.http_client.post(
                    "mobile-erp/analytics/events/batch",
                    batch_data,
                    params={"organization_id": self.sdk.config.organization_id},
                )

        except Exception as e:
            print(f"[SDK] Failed to flush analytics events: {e}")
            # Re-add events to buffer for retry (up to limit)
            self._event_buffer.extendleft(reversed(events_to_send[-100:]))

    async def _flush_metrics(self) -> None:
        """Flush metrics to server."""
        if not self._metric_buffer:
            return

        metrics_to_send = list(self._metric_buffer)
        self._metric_buffer.clear()

        try:
            # Send metrics in batches
            batch_size = 50
            for i in range(0, len(metrics_to_send), batch_size):
                batch = metrics_to_send[i : i + batch_size]

                batch_data = {
                    "metrics": [metric.dict() for metric in batch],
                    "batch_timestamp": datetime.now().isoformat(),
                }

                await self.sdk.http_client.post(
                    "mobile-erp/analytics/performance/batch",
                    batch_data,
                    params={"organization_id": self.sdk.config.organization_id},
                )

        except Exception as e:
            print(f"[SDK] Failed to flush performance metrics: {e}")
            # Re-add metrics to buffer for retry (up to limit)
            self._metric_buffer.extendleft(reversed(metrics_to_send[-100:]))

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary."""
        return {
            "current_session_id": self._current_session_id,
            "current_screen": self._current_screen,
            "events_in_buffer": len(self._event_buffer),
            "metrics_in_buffer": len(self._metric_buffer),
            "performance_summary": self.performance_monitor.get_performance_summary(),
            "error_summary": self.error_tracker.get_error_summary(),
            "screen_flow_analysis": self.behavior_analyzer.get_screen_flow_analysis(),
        }


class AnalyticsModule:
    """Main analytics module for SDK."""

    def __init__(self, sdk: MobileERPSDK) -> dict:
        self.sdk = sdk
        self.collector = AnalyticsCollector(sdk)

    async def initialize(self) -> None:
        """Initialize analytics module."""
        await self.collector.initialize()

        # Register module with SDK
        self.sdk.register_module("analytics", self)

    async def close(self) -> None:
        """Close analytics module."""
        await self.collector.close()

    # Expose collector methods
    def start_session(self, user_id: Optional[str] = None) -> str:
        """Start analytics session."""
        return self.collector.start_session(user_id)

    def end_session(self) -> None:
        """End analytics session."""
        self.collector.end_session()

    def track_event(
        self,
        event_type: EventType,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> str:
        """Track analytics event."""
        return self.collector.track_event(event_type, event_name, properties, **kwargs)

    def track_screen_view(
        self, screen_name: str, properties: Optional[Dict[str, Any]] = None
    ) -> str:
        """Track screen view."""
        return self.collector.track_screen_view(screen_name, properties)

    def track_user_action(
        self,
        action_name: str,
        feature_name: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Track user action."""
        return self.collector.track_user_action(action_name, feature_name, properties)

    def track_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: str = "error",
    ) -> str:
        """Track error."""
        return self.collector.track_error(error, context, severity)

    def create_funnel(
        self,
        funnel_id: str,
        name: str,
        description: str,
        steps: List[Dict[str, Any]],
        time_window_hours: int = 24,
    ) -> AnalyticsFunnel:
        """Create conversion funnel."""
        return self.collector.funnel_analyzer.create_funnel(
            funnel_id, name, description, steps, time_window_hours
        )

    def get_funnel_report(self, funnel_id: str) -> Optional[Dict[str, Any]]:
        """Get funnel report."""
        return self.collector.funnel_analyzer.get_funnel_report(funnel_id)

    def get_user_behavior_summary(self, user_id: str) -> Dict[str, Any]:
        """Get user behavior summary."""
        return self.collector.behavior_analyzer.get_user_behavior_summary(user_id)

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary."""
        return self.collector.get_analytics_summary()
