"""Enhanced monitoring and observability for ITDO ERP System."""

import asyncio
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Awaitable, Callable, Dict, Generator, Optional, TypeVar

import structlog
from fastapi import Request, Response
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer()
        if __debug__
        else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(30),  # INFO level
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

# Get structured logger
logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

ACTIVE_CONNECTIONS = Gauge("active_connections", "Number of active connections")

DATABASE_QUERY_COUNT = Counter(
    "database_queries_total", "Total database queries", ["operation", "table"]
)

DATABASE_QUERY_DURATION = Histogram(
    "database_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
)

API_RESPONSE_SIZE = Histogram(
    "api_response_size_bytes", "API response size in bytes", ["endpoint"]
)

ERROR_COUNT = Counter("errors_total", "Total errors", ["error_type", "endpoint"])

BUSINESS_METRICS = {
    "organizations_created": Counter(
        "organizations_created_total", "Total organizations created"
    ),
    "departments_created": Counter(
        "departments_created_total", "Total departments created"
    ),
    "roles_created": Counter("roles_created_total", "Total roles created"),
    "users_active": Gauge("users_active", "Number of active users"),
    "login_attempts": Counter(
        "login_attempts_total", "Total login attempts", ["status"]
    ),
}


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting metrics and logging."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request and collect metrics."""
        start_time = time.time()

        # Extract request info
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"

        # Increment active connections
        ACTIVE_CONNECTIONS.inc()

        # Add request context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=id(request),
            method=method,
            path=path,
            client_ip=client_ip,
            user_agent=request.headers.get("user-agent", "unknown"),
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate metrics
            duration = time.time() - start_time
            status_code = response.status_code

            # Update metrics
            REQUEST_COUNT.labels(
                method=method, endpoint=path, status_code=status_code
            ).inc()

            REQUEST_DURATION.labels(method=method, endpoint=path).observe(duration)

            # Log response size if available
            if hasattr(response, "body"):
                body_size = len(response.body) if response.body else 0
                API_RESPONSE_SIZE.labels(endpoint=path).observe(body_size)

            # Log request completion
            logger.info(
                "Request completed",
                status_code=status_code,
                duration=duration,
                response_size=getattr(response, "content_length", 0),
            )

            return response

        except Exception as e:
            # Handle errors
            duration = time.time() - start_time
            error_type = type(e).__name__

            ERROR_COUNT.labels(error_type=error_type, endpoint=path).inc()

            logger.error(
                "Request failed",
                error_type=error_type,
                error_message=str(e),
                duration=duration,
                exc_info=True,
            )

            raise

        finally:
            # Decrement active connections
            ACTIVE_CONNECTIONS.dec()


def setup_tracing(service_name: str = "itdo-erp-backend") -> None:
    """Setup OpenTelemetry tracing."""
    # Configure tracer provider
    trace.set_tracer_provider(TracerProvider())

    # Configure Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name="localhost",
        agent_port=6831,
    )

    # Add span processor
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

    # Instrument frameworks
    FastAPIInstrumentor.instrument()
    SQLAlchemyInstrumentor.instrument()
    RedisInstrumentor.instrument()


F = TypeVar("F", bound=Callable[..., Any])


def trace_function(operation_name: Optional[str] = None) -> Callable[[F], F]:
    """Decorator to trace function execution."""

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = trace.get_tracer(__name__)
            span_name = operation_name or f"{func.__module__}.{func.__name__}"

            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("function.result", "success")
                    return result
                except Exception as e:
                    span.set_attribute("function.result", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    raise

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = trace.get_tracer(__name__)
            span_name = operation_name or f"{func.__module__}.{func.__name__}"

            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("function.result", "success")
                    return result
                except Exception as e:
                    span.set_attribute("function.result", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    raise

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore[return-value]
        else:
            return sync_wrapper  # type: ignore[return-value]

    return decorator


@contextmanager
def database_query_timer(operation: str, table: str) -> Generator[None, None, None]:
    """Context manager for timing database queries."""
    start_time = time.time()

    try:
        yield
    finally:
        duration = time.time() - start_time

        DATABASE_QUERY_COUNT.labels(operation=operation, table=table).inc()

        DATABASE_QUERY_DURATION.labels(operation=operation, table=table).observe(
            duration
        )

        logger.debug(
            "Database query executed",
            operation=operation,
            table=table,
            duration=duration,
        )


def log_business_event(event_type: str, details: Dict[str, Any]) -> None:
    """Log business events for analytics."""
    logger.info("Business event", event_type=event_type, **details)

    # Update business metrics
    if event_type == "organization_created":
        BUSINESS_METRICS["organizations_created"].inc()
    elif event_type == "department_created":
        BUSINESS_METRICS["departments_created"].inc()
    elif event_type == "role_created":
        BUSINESS_METRICS["roles_created"].inc()
    elif event_type == "user_login":
        BUSINESS_METRICS["login_attempts"].labels(status="success").inc()
    elif event_type == "user_login_failed":
        BUSINESS_METRICS["login_attempts"].labels(status="failed").inc()


class HealthChecker:
    """Health check implementation."""

    def __init__(self) -> None:
        self.checks: Dict[str, Callable[[], bool]] = {}
        self.last_check_time: Dict[str, datetime] = {}
        self.check_interval = timedelta(seconds=30)

    def register_check(self, name: str, check_func: Callable[[], bool]) -> None:
        """Register a health check function."""
        self.checks[name] = check_func

    async def run_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        results = {}
        overall_healthy = True

        for name, check_func in self.checks.items():
            try:
                # Skip if checked recently
                if (
                    name in self.last_check_time
                    and datetime.now() - self.last_check_time[name]
                    < self.check_interval
                ):
                    continue

                start_time = time.time()
                healthy = (
                    await check_func()
                    if asyncio.iscoroutinefunction(check_func)
                    else check_func()
                )
                duration = time.time() - start_time

                results[name] = {
                    "healthy": healthy,
                    "duration": duration,
                    "timestamp": datetime.now().isoformat(),
                }

                if not healthy:
                    overall_healthy = False

                self.last_check_time[name] = datetime.now()

            except Exception as e:
                results[name] = {
                    "healthy": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
                overall_healthy = False

        return {
            "healthy": overall_healthy,
            "checks": results,
            "timestamp": datetime.now().isoformat(),
        }


# Global health checker instance
health_checker = HealthChecker()


def setup_health_checks(
    app: Any, db_session_factory: Any, redis_client: Any = None
) -> None:
    """Setup standard health checks."""

    def check_database() -> bool:
        """Check database connectivity."""
        try:
            from sqlalchemy import text

            with db_session_factory() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False

    def check_redis() -> bool:
        """Check Redis connectivity."""
        if not redis_client:
            return True

        try:
            redis_client.ping()
            return True
        except Exception as e:
            logger.error("Redis health check failed", error=str(e))
            return False

    def check_disk_space() -> bool:
        """Check available disk space."""
        try:
            import shutil

            total, used, free = shutil.disk_usage("/")
            free_percent = (free / total) * 100
            return free_percent > 10  # At least 10% free
        except Exception as e:
            logger.error("Disk space check failed", error=str(e))
            return False

    def check_memory() -> bool:
        """Check available memory."""
        try:
            import psutil

            memory = psutil.virtual_memory()
            return memory.percent < 90  # Less than 90% used
        except Exception as e:
            logger.error("Memory check failed", error=str(e))
            return False

    # Register health checks
    health_checker.register_check("database", check_database)
    health_checker.register_check("redis", check_redis)
    health_checker.register_check("disk_space", check_disk_space)
    health_checker.register_check("memory", check_memory)


def get_metrics() -> str:
    """Get Prometheus metrics."""
    return generate_latest()  # type: ignore[no-any-return]


# Performance monitoring decorator
def monitor_performance(metric_name: Optional[str] = None) -> Callable[[F], F]:
    """Decorator to monitor function performance."""

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            function_name = metric_name or f"{func.__module__}.{func.__name__}"

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                logger.debug(
                    "Function performance",
                    function=function_name,
                    duration=duration,
                    status="success",
                )

                return result
            except Exception as e:
                duration = time.time() - start_time

                logger.warning(
                    "Function performance",
                    function=function_name,
                    duration=duration,
                    status="error",
                    error=str(e),
                )

                raise

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            function_name = metric_name or f"{func.__module__}.{func.__name__}"

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                logger.debug(
                    "Function performance",
                    function=function_name,
                    duration=duration,
                    status="success",
                )

                return result
            except Exception as e:
                duration = time.time() - start_time

                logger.warning(
                    "Function performance",
                    function=function_name,
                    duration=duration,
                    status="error",
                    error=str(e),
                )

                raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore[return-value]
        else:
            return sync_wrapper  # type: ignore[return-value]

    return decorator
