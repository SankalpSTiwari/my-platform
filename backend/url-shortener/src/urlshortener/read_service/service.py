"""Read Service for redirecting short URLs."""

from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from urlshortener.shared.models.database import URLMapping
from urlshortener.shared.utils.redis_client import RedisClient
from urlshortener.shared.config import Config
import logging

logger = logging.getLogger(__name__)


class ReadService:
    """Service for reading and redirecting short URLs."""

    def __init__(self, db: Session, redis_client: RedisClient, config: Config):
        """
        Initialize Read Service.
        
        Args:
            db: Database session
            redis_client: Redis client for caching
            config: Application configuration
        """
        self.db = db
        self.redis_client = redis_client
        self.config = config

    def get_original_url(self, short_code: str) -> Tuple[Optional[str], bool]:
        """
        Get original URL for a short code with caching.
        
        Args:
            short_code: Short code to look up
            
        Returns:
            Tuple of (original_url, is_expired)
            - original_url: The original URL if found and not expired, None otherwise
            - is_expired: True if URL exists but is expired, False otherwise
        """
        # Try Redis cache first
        cached = self.redis_client.get_cached_url(short_code)
        if cached:
            original_url = cached['original_url']
            expiration_str = cached.get('expiration_time')
            
            # Check expiration
            if expiration_str:
                try:
                    expiration = datetime.fromisoformat(expiration_str.replace('Z', '+00:00'))
                    if datetime.utcnow() > expiration:
                        # Expired, remove from cache
                        self.redis_client.delete_cache(short_code)
                        return None, True
                except Exception as e:
                    logger.warning(f"Error parsing expiration time: {e}")
            
            logger.debug(f"Cache hit for short code: {short_code}")
            return original_url, False
        
        # Cache miss - query database
        url_mapping = (
            self.db.query(URLMapping)
            .filter(URLMapping.short_code == short_code)
            .first()
        )
        
        if not url_mapping:
            logger.debug(f"Short code not found: {short_code}")
            return None, False
        
        # Check if expired
        if url_mapping.is_expired():
            logger.debug(f"Short code expired: {short_code}")
            # Don't cache expired URLs
            return None, True
        
        # Cache the result
        expiration_str = (
            url_mapping.expiration_time.isoformat()
            if url_mapping.expiration_time
            else None
        )
        self.redis_client.cache_url(
            short_code,
            url_mapping.original_url,
            expiration_str,
            self.config.cache_ttl_seconds
        )
        
        logger.info(f"Redirect: {short_code} -> {url_mapping.original_url}")
        return url_mapping.original_url, False



