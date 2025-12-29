"""Configuration settings for URL Shortener."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Application configuration."""

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://localhost/urlshortener"
    )

    # Redis
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "0"))

    # Service configuration
    base_url: str = os.getenv("BASE_URL", "https://short.ly")
    service_port: int = int(os.getenv("SERVICE_PORT", "8000"))
    service_host: str = os.getenv("SERVICE_HOST", "0.0.0.0")

    # Cache settings
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))  # 1 hour

    # Counter settings
    counter_key: str = os.getenv("COUNTER_KEY", "url_shortener:counter")

    # Short code settings
    min_short_code_length: int = int(os.getenv("MIN_SHORT_CODE_LENGTH", "6"))
    use_obfuscation: bool = os.getenv("USE_OBFUSCATION", "true").lower() == "true"

    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        return cls()



