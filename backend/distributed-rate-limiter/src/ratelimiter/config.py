from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List


def _get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def _get_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    return float(raw) if raw is not None else default


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return int(raw) if raw is not None else default


@dataclass(frozen=True)
class Settings:
    redis_urls: List[str]
    bucket_capacity: int
    refill_rate_per_sec: float
    token_ttl_ms: int
    window_ms: int
    grpc_host: str
    grpc_port: int
    metrics_port: int

    @classmethod
    def from_env(cls) -> "Settings":
        redis_urls_raw = _get_env("REDIS_URLS", "redis://localhost:6379")
        redis_urls = [url.strip() for url in redis_urls_raw.split(",") if url.strip()]
        if not redis_urls:
            raise RuntimeError("REDIS_URLS must include at least one url")

        return cls(
            redis_urls=redis_urls,
            bucket_capacity=_get_int("BUCKET_CAPACITY", 100),
            refill_rate_per_sec=_get_float("REFILL_RATE_PER_SEC", 50.0),
            token_ttl_ms=_get_int("TOKEN_TTL_MS", 300_000),
            window_ms=_get_int("ANALYTICS_WINDOW_MS", 60_000),
            grpc_host=os.getenv("GRPC_HOST", "0.0.0.0"),
            grpc_port=_get_int("GRPC_PORT", 50051),
            metrics_port=_get_int("METRICS_PORT", 9090),
        )

