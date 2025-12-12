"""Configuration for log search engine."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Configuration settings."""

    # Partition settings
    partition_duration_ms: int = 3600 * 1000  # 1 hour
    max_partitions: int = 24 * 7  # 7 days

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 5000

    # Search settings
    default_limit: int = 100
    default_fuzzy_threshold: int = 80

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            partition_duration_ms=int(
                os.getenv("PARTITION_DURATION_MS", 3600 * 1000)
            ),
            max_partitions=int(os.getenv("MAX_PARTITIONS", 24 * 7)),
            api_host=os.getenv("API_HOST", "0.0.0.0"),
            api_port=int(os.getenv("API_PORT", 5000)),
            default_limit=int(os.getenv("DEFAULT_LIMIT", 100)),
            default_fuzzy_threshold=int(os.getenv("FUZZY_THRESHOLD", 80)),
        )

