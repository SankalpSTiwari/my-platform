"""Redis client utility for distributed locking."""

import logging
from typing import Optional

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available. Distributed locking will be disabled.")

from ticketbooking.config import Config

logger = logging.getLogger(__name__)


def create_redis_client(config: Config) -> Optional["redis.Redis"]:
    """Create Redis client if available."""
    if not REDIS_AVAILABLE:
        logger.warning("Redis package not installed. Distributed locking disabled.")
        return None

    try:
        client = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            db=config.redis_db,
            decode_responses=True,
        )
        # Test connection
        client.ping()
        logger.info("Redis connection established")
        return client
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}. Distributed locking disabled.")
        return None




