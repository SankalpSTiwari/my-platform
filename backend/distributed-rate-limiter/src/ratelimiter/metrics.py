from __future__ import annotations

from prometheus_client import Counter, Histogram, start_http_server

# Request counts split by decision.
requests_total = Counter(
    "rate_limiter_requests_total",
    "Total Acquire calls processed",
    labelnames=("result",),
)

# Latency for Acquire handler end-to-end.
request_latency_seconds = Histogram(
    "rate_limiter_request_latency_seconds",
    "Acquire handler latency distribution",
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0),
)


def record_decision(allowed: bool) -> None:
    requests_total.labels(result="allowed" if allowed else "throttled").inc()


def record_latency(seconds: float) -> None:
    request_latency_seconds.observe(seconds)


def start_metrics_server(port: int) -> None:
    start_http_server(port)

