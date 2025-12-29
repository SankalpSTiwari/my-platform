"""Write Service for creating short URLs."""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from urlshortener.shared.models.database import URLMapping
from urlshortener.shared.utils.base62 import encode, obfuscate
from urlshortener.shared.utils.redis_client import RedisClient
from urlshortener.shared.config import Config
import logging

logger = logging.getLogger(__name__)


class WriteService:
    """Service for creating short URLs."""

    def __init__(self, db: Session, redis_client: RedisClient, config: Config):
        """
        Initialize Write Service.
        
        Args:
            db: Database session
            redis_client: Redis client for counter
            config: Application configuration
        """
        self.db = db
        self.redis_client = redis_client
        self.config = config

    def create_short_url(
        self,
        original_url: str,
        custom_alias: Optional[str] = None,
        expiration_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Create a short URL from a long URL.
        
        Args:
            original_url: Original long URL
            custom_alias: Optional custom alias for the short code
            expiration_time: Optional expiration timestamp
            user_id: Optional user ID
            
        Returns:
            Short URL (full URL with domain)
            
        Raises:
            ValueError: If custom alias already exists or URL is invalid
        """
        # Validate URL format (basic validation)
        if not original_url or not original_url.startswith(("http://", "https://")):
            raise ValueError("Invalid URL format. Must start with http:// or https://")

        # Check if custom alias is provided
        if custom_alias:
            # Validate custom alias format
            if not self._is_valid_short_code(custom_alias):
                raise ValueError("Custom alias contains invalid characters")
            
            # Check if custom alias already exists
            existing = (
                self.db.query(URLMapping)
                .filter(URLMapping.short_code == custom_alias)
                .first()
            )
            if existing:
                raise ValueError(f"Custom alias '{custom_alias}' already exists")
            
            short_code = custom_alias
        else:
            # Generate short code from counter
            short_code = self._generate_short_code()

        # Create URL mapping
        url_mapping = URLMapping(
            short_code=short_code,
            original_url=original_url,
            expiration_time=expiration_time,
            user_id=user_id,
        )

        try:
            self.db.add(url_mapping)
            self.db.commit()
            
            # Cache the new URL in Redis
            expiration_str = expiration_time.isoformat() if expiration_time else None
            self.redis_client.cache_url(
                short_code,
                original_url,
                expiration_str)
            
            logger.info(f"Created short URL: {short_code} -> {original_url}")
            return f"{self.config.base_url}/{short_code}"
            
        except IntegrityError:
            self.db.rollback()
            # If we get here with a generated code, retry once
            if not custom_alias:
                short_code = self._generate_short_code()
                url_mapping.short_code = short_code
                self.db.add(url_mapping)
                self.db.commit()
                return f"{self.config.base_url}/{short_code}"
            raise ValueError(f"Short code '{short_code}' already exists")

    def _generate_short_code(self) -> str:
        """
        Generate a unique short code using Redis counter.
        
        Returns:
            Generated short code
        """
        # Get next counter value from Redis
        counter = self.redis_client.get_next_counter(self.config.counter_key)
        
        if counter is None:
            # Fallback: use timestamp-based generation if Redis unavailable
            logger.warning("Redis unavailable, using timestamp-based generation")
            counter = int(datetime.utcnow().timestamp() * 1000000)
        
        # Encode to Base62
        encoded = encode(counter)
        
        # Pad to minimum length if needed
        if len(encoded) < self.config.min_short_code_length:
            encoded = encoded.ljust(self.config.min_short_code_length, "0")
        
        # Apply obfuscation if enabled
        if self.config.use_obfuscation:
            encoded = obfuscate(encoded)
        
        return encoded

    def _is_valid_short_code(self, code: str) -> bool:
        """
        Validate short code format.
        
        Args:
            code: Short code to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not code or len(code) < 1:
            return False
        
        # Allow alphanumeric characters and some safe special chars
        valid_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
        return all(c in valid_chars for c in code)



