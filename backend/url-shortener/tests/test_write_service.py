"""Tests for Write Service."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, MagicMock

from urlshortener.shared.models.database import Base, URLMapping
from urlshortener.shared.utils.redis_client import RedisClient
from urlshortener.shared.config import Config
from urlshortener.write_service.service import WriteService


@pytest.fixture
def db_session():
    """Create in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    redis_client = Mock(spec=RedisClient)
    redis_client.get_next_counter = MagicMock(return_value=1)
    redis_client.cache_url = MagicMock()
    redis_client.is_available = MagicMock(return_value=True)
    return redis_client


@pytest.fixture
def config():
    """Create test configuration."""
    return Config(
        base_url="https://short.ly",
        min_short_code_length=6,
        use_obfuscation=False,  # Disable for predictable tests
    )


@pytest.fixture
def write_service(db_session, mock_redis, config):
    """Create Write Service instance."""
    return WriteService(db_session, mock_redis, config)


def test_create_short_url_basic(write_service):
    """Test creating a basic short URL."""
    short_url = write_service.create_short_url("https://example.com")
    
    assert short_url.startswith("https://short.ly/")
    assert len(short_url.split("/")[-1]) >= 6


def test_create_short_url_with_custom_alias(write_service):
    """Test creating short URL with custom alias."""
    short_url = write_service.create_short_url(
        "https://example.com",
        custom_alias="test-link"
    )
    
    assert short_url == "https://short.ly/test-link"
    
    # Verify it's in database
    mapping = write_service.db.query(URLMapping).filter_by(short_code="test-link").first()
    assert mapping is not None
    assert mapping.original_url == "https://example.com"


def test_create_short_url_duplicate_custom_alias(write_service):
    """Test that duplicate custom alias raises error."""
    write_service.create_short_url(
        "https://example.com",
        custom_alias="duplicate"
    )
    
    with pytest.raises(ValueError, match="already exists"):
        write_service.create_short_url(
            "https://another.com",
            custom_alias="duplicate"
        )


def test_create_short_url_with_expiration(write_service):
    """Test creating short URL with expiration."""
    expiration = datetime.utcnow() + timedelta(days=30)
    short_url = write_service.create_short_url(
        "https://example.com",
        expiration_time=expiration
    )
    
    mapping = write_service.db.query(URLMapping).first()
    assert mapping.expiration_time is not None
    assert mapping.expiration_time == expiration


def test_create_short_url_invalid_url(write_service):
    """Test that invalid URL raises error."""
    with pytest.raises(ValueError, match="Invalid URL format"):
        write_service.create_short_url("not-a-url")
    
    with pytest.raises(ValueError, match="Invalid URL format"):
        write_service.create_short_url("ftp://example.com")


def test_create_short_url_invalid_custom_alias(write_service):
    """Test that invalid custom alias raises error."""
    with pytest.raises(ValueError, match="invalid characters"):
        write_service.create_short_url(
            "https://example.com",
            custom_alias="invalid@alias"
        )


def test_redis_counter_used(write_service, mock_redis):
    """Test that Redis counter is used for generation."""
    write_service.create_short_url("https://example.com")
    mock_redis.get_next_counter.assert_called_once()


def test_url_cached_in_redis(write_service, mock_redis):
    """Test that URL is cached in Redis after creation."""
    write_service.create_short_url("https://example.com")
    assert mock_redis.cache_url.called

