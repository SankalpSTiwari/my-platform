"""Redis client utilities for counter and caching."""

import redis
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper for URL Shortener."""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        """
        Initialize Redis client.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
        """
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.client.ping()
            logger.info(f"Connected to Redis at {host}:{port}")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Some features may be unavailable.")
            self.client = None

    def get_next_counter(self, key: str = "url_shortener:counter") -> Optional[int]:
        """
        Get next counter value from Redis.
        
        Args:
            key: Redis key for counter
            
        Returns:
            Next counter value or None if Redis unavailable
        """
        if not self.client:
            return None
        
        try:
            return self.client.incr(key)
        except Exception as e:
            logger.error(f"Error getting counter from Redis: {e}")
            return None

    def get_cached_url(self, short_code: str) -> Optional[dict]:
        """
        Get cached URL mapping from Redis.
        
        Args:
            short_code: Short code to look up
            
        Returns:
            Dictionary with 'original_url' and 'expiration_time' or None
        """
        if not self.client:
            return None
        
        try:
            key = f"url:{short_code}"
            data = self.client.hgetall(key)
            if data and data.get('original_url'):
                return {
                    'original_url': data['original_url'],
                    'expiration_time': data.get('expiration_time'),
                }
            return None
        except Exception as e:
            logger.error(f"Error getting cached URL from Redis: {e}")
            return None

    def cache_url(self, short_code: str, original_url: str, expiration_time: Optional[str] = None, ttl: int = 3600):
        """
        Cache URL mapping in Redis.
        
        Args:
            short_code: Short code
            original_url: Original URL
            expiration_time: Expiration timestamp (ISO string)
            ttl: Time to live in seconds (default: 1 hour)
        """
        if not self.client:
            return
        
        try:
            key = f"url:{short_code}"
            data = {
                'original_url': original_url,
            }
            if expiration_time:
                data['expiration_time'] = expiration_time
            
            self.client.hset(key, mapping=data)
            self.client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Error caching URL in Redis: {e}")

    def delete_cache(self, short_code: str):
        """
        Delete cached URL from Redis.
        
        Args:
            short_code: Short code to delete
        """
        if not self.client:
            return
        
        try:
            key = f"url:{short_code}"
            self.client.delete(key)
        except Exception as e:
            logger.error(f"Error deleting cache from Redis: {e}")

    def is_available(self) -> bool:
        """Check if Redis is available."""
        if not self.client:
            return False
        try:
            self.client.ping()
            return True
        except:
            return False

