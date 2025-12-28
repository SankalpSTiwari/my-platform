"""Tests for Read Service."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, MagicMock

from urlshortener.shared.models.database import Base, URLMapping
from urlshortener.shared.utils.redis_client import RedisClient
from urlshortener.shared.config import Config
from urlshortener.read_service.service import ReadService


@pytest.fixture
def db_session():
    """Create in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Add test data
    mapping = URLMapping(
        short_code="test123",
        original_url="https://example.com",
        created_at=datetime.utcnow()
    )
    session.add(mapping)
    session.commit()
    
    yield session
    session.close()


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    redis_client = Mock(spec=RedisClient)
    redis_client.get_cached_url = MagicMock(return_value=None)
    redis_client.cache_url = MagicMock()
    redis_client.delete_cache = MagicMock()
    redis_client.is_available = MagicMock(return_value=True)
    return redis_client


@pytest.fixture
def config():
    """Create test configuration."""
    return Config(cache_ttl_seconds=3600)


@pytest.fixture
def read_service(db_session, mock_redis, config):
    """Create Read Service instance."""
    return ReadService(db_session, mock_redis, config)


def test_get_original_url_exists(read_service):
    """Test getting original URL that exists."""
    original_url, is_expired = read_service.get_original_url("test123")
    
    assert original_url == "https://example.com"
    assert is_expired is False


def test_get_original_url_not_found(read_service):
    """Test getting original URL that doesn't exist."""
    original_url, is_expired = read_service.get_original_url("nonexistent")
    
    assert original_url is None
    assert is_expired is False


def test_get_original_url_from_cache(read_service, mock_redis):
    """Test getting original URL from cache."""
    mock_redis.get_cached_url.return_value = {
        'original_url': 'https://cached.com',
        'expiration_time': None
    }
    
    original_url, is_expired = read_service.get_original_url("test123")
    
    assert original_url == "https://cached.com"
    assert is_expired is False
    # Should not query database
    assert read_service.db.query(URLMapping).count() == 1


def test_get_original_url_expired(read_service, db_session):
    """Test getting expired URL."""
    expired_mapping = URLMapping(
        short_code="expired",
        original_url="https://expired.com",
        expiration_time=datetime.utcnow() - timedelta(days=1)
    )
    db_session.add(expired_mapping)
    db_session.commit()
    
    original_url, is_expired = read_service.get_original_url("expired")
    
    assert original_url is None
    assert is_expired is True


def test_cache_url_on_miss(read_service, mock_redis):
    """Test that URL is cached after database lookup."""
    read_service.get_original_url("test123")
    
    # Should cache the result
    assert mock_redis.cache_url.called


def test_redis_unavailable_fallback(read_service, mock_redis):
    """Test fallback to database when Redis is unavailable."""
    mock_redis.get_cached_url.return_value = None
    mock_redis.is_available.return_value = False
    
    # Should still work, just without caching
    original_url, is_expired = read_service.get_original_url("test123")
    
    assert original_url == "https://example.com"
    assert is_expired is False

