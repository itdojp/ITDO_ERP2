"""アプリケーションメトリクス"""

import time
from functools import wraps
from typing import Any, Callable

from prometheus_client import REGISTRY, Counter, Gauge, Histogram

# Clear existing metrics to prevent duplicates
try:
    REGISTRY.unregister(REGISTRY._collector_to_names.copy())  # type: ignore[arg-type]
except Exception:
    pass

# メトリクス定義
http_requests_total = Counter(
    "itdo_http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)

http_request_duration = Histogram(
    "itdo_http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
)

active_users = Gauge("itdo_active_users", "Number of active users")

db_connections = Gauge("itdo_db_connections_active", "Active database connections")

test_failures = Counter(
    "itdo_test_failures_total", "Total test failures", ["test_type", "test_file"]
)

ci_build_duration = Histogram(
    "itdo_ci_build_duration_seconds", "CI build duration", ["build_type"]
)

code_coverage = Gauge(
    "itdo_code_coverage_percentage", "Code coverage percentage", ["component"]
)


def track_request(func: Callable[..., Any]) -> Callable[..., Any]:
    """リクエストトラッキングデコレータ"""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.time()
        method = kwargs.get("method", "GET")
        endpoint = kwargs.get("endpoint", "unknown")

        try:
            result = await func(*args, **kwargs)
            status = "2xx"
            return result
        except Exception:
            status = "5xx"
            raise
        finally:
            duration = time.time() - start

            http_requests_total.labels(
                method=method, endpoint=endpoint, status=status
            ).inc()

            http_request_duration.labels(method=method, endpoint=endpoint).observe(
                duration
            )

    return wrapper


def track_test_result(test_type: str, test_file: str, success: bool) -> None:
    """テスト結果トラッキング"""
    if not success:
        test_failures.labels(test_type=test_type, test_file=test_file).inc()


def update_coverage(component: str, percentage: float) -> None:
    """カバレッジ更新"""
    code_coverage.labels(component=component).set(percentage)


def track_ci_build(build_type: str, duration: float) -> None:
    """CIビルド時間トラッキング"""
    ci_build_duration.labels(build_type=build_type).observe(duration)
