from __future__ import annotations

import logging
import signal
import time
from concurrent import futures

import grpc

from ratelimiter.config import Settings
from ratelimiter.logic import RateLimiter
from ratelimiter.metrics import record_decision, record_latency, start_metrics_server
from ratelimiter.redis_client import create_redis_client

import rate_limiter_pb2
import rate_limiter_pb2_grpc

logger = logging.getLogger(__name__)


class RateLimiterService(rate_limiter_pb2_grpc.RateLimiterServicer):
    def __init__(self, limiter: RateLimiter) -> None:
        self.limiter = limiter

    def Acquire(self, request, context):
        start = time.perf_counter()
        result = self.limiter.acquire(request.key, tokens=request.tokens or 1.0)
        record_decision(result.allowed)
        record_latency(time.perf_counter() - start)

        return rate_limiter_pb2.RateLimitResponse(
            allowed=result.allowed,
            remaining_tokens=result.remaining_tokens,
            window_count=result.window_count,
            window_ms=result.window_ms,
        )

    def GetUsage(self, request, context):
        result = self.limiter.get_usage(request.key)
        return rate_limiter_pb2.UsageResponse(
            window_count=result.window_count,
            window_ms=result.window_ms,
        )


def serve(settings: Settings | None = None) -> None:
    settings = settings or Settings.from_env()
    redis_client = create_redis_client(settings)
    limiter = RateLimiter(
        redis_client,
        bucket_capacity=settings.bucket_capacity,
        refill_rate_per_sec=settings.refill_rate_per_sec,
        token_ttl_ms=settings.token_ttl_ms,
        window_ms=settings.window_ms,
    )

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=32))
    rate_limiter_pb2_grpc.add_RateLimiterServicer_to_server(
        RateLimiterService(limiter), server
    )
    server.add_insecure_port(f"{settings.grpc_host}:{settings.grpc_port}")

    start_metrics_server(settings.metrics_port)
    server.start()

    logger.info(
        "Rate limiter started on %s:%s (metrics=%s)",
        settings.grpc_host,
        settings.grpc_port,
        settings.metrics_port,
    )

    # Handle graceful shutdown signals.
    stop_event = server.stop

    def _handle_signal(signum, frame):  # pragma: no cover - signal path
        logger.info("Received signal %s, shutting down...", signum)
        stop_event(grace=5)

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    server.wait_for_termination()


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    serve()

