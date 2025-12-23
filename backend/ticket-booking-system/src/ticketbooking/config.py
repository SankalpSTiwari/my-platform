"""Configuration settings for the ticket booking system."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Application configuration."""

    # Database (defaults to SQLite for local development)
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./ticketbooking.db")

    # API
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "5000"))

    # Redis (for distributed locking)
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "0"))

    # Booking
    booking_lock_ttl_seconds: int = int(os.getenv("BOOKING_LOCK_TTL_SECONDS", "600"))  # 10 minutes
    booking_timeout_seconds: int = int(os.getenv("BOOKING_TIMEOUT_SECONDS", "600"))

    # Caching
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "300"))  # 5 minutes

    # Search
    search_page_size: int = int(os.getenv("SEARCH_PAGE_SIZE", "20"))
    max_search_results: int = int(os.getenv("MAX_SEARCH_RESULTS", "1000"))

    # Elasticsearch (if using for search)
    elasticsearch_host: str = os.getenv("ELASTICSEARCH_HOST", "localhost")
    elasticsearch_port: int = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
    elasticsearch_index: str = os.getenv("ELASTICSEARCH_INDEX", "events")

    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        return cls()

