from __future__ import annotations

from typing import Sequence
from urllib.parse import urlparse

try:
    import redis
except ImportError as exc:  # pragma: no cover - import failure surfaced at runtime
    raise RuntimeError(
        "redis package is required. Install with `pip install redis`."
    ) from exc

from .config import Settings


def _parse_node(url: str) -> dict:
    parsed = urlparse(url)
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 6379,
        "username": parsed.username,
        "password": parsed.password,
        "scheme": parsed.scheme,
    }


def create_redis_client(settings: Settings, existing: "redis.Redis | None" = None):
    """
    Create a Redis or RedisCluster client based on the provided settings.

    When multiple URLs are supplied, cluster mode is used with startup nodes.
    """
    if existing is not None:
        return existing

    if len(settings.redis_urls) == 1:
        return redis.Redis.from_url(settings.redis_urls[0])

    nodes = [_parse_node(url) for url in settings.redis_urls]
    startup_nodes = [{"host": n["host"], "port": n["port"]} for n in nodes]
    # Credentials are pulled from the first URL if present.
    first = nodes[0]
    return redis.RedisCluster(
        startup_nodes=startup_nodes,
        username=first.get("username"),
        password=first.get("password"),
        ssl=first.get("scheme") == "rediss",
    )

