"""アプリケーションメトリクス"""

import time
from functools import wraps

from prometheus_client import Counter, Gauge, Histogram

# メトリクス定義
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)

http_request_duration = Histogram(
    "http_request_duration_seconds", "HTTP request duration", ["method", "endpoint"]
)

active_users = Gauge("active_users", "Number of active users")

db_connections = Gauge("db_connections_active", "Active database connections")

test_failures = Counter(
    "test_failures_total", "Total test failures", ["test_type", "test_file"]
)

ci_build_duration = Histogram(
    "ci_build_duration_seconds", "CI build duration", ["build_type"]
)

code_coverage = Gauge(
    "code_coverage_percentage", "Code coverage percentage", ["component"]
)


def track_request(func) -> dict:
    """リクエストトラッキングデコレータ"""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> dict:
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


def track_test_result(test_type: str, test_file: str, success: bool) -> dict:
    """テスト結果トラッキング"""
    if not success:
        test_failures.labels(test_type=test_type, test_file=test_file).inc()


def update_coverage(component: str, percentage: float) -> dict:
    """カバレッジ更新"""
    code_coverage.labels(component=component).set(percentage)


def track_ci_build(build_type: str, duration: float) -> dict:
    """CIビルド時間トラッキング"""
    ci_build_duration.labels(build_type=build_type).observe(duration)
