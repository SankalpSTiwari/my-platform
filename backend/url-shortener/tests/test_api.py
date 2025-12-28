"""Integration tests for API endpoints."""

import pytest
from datetime import datetime, timedelta
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from urlshortener.shared.models.database import Base, init_db, get_session_factory
from urlshortener.shared.utils.redis_client import RedisClient
from urlshortener.shared.config import Config
from urlshortener.api.gateway import app


@pytest.fixture
def test_app():
    """Create test Flask app."""
    # Use in-memory SQLite for testing
    test_config = Config(
        database_url="sqlite:///:memory:",
        base_url="https://short.ly",
        redis_host="localhost",
        redis_port=6379
    )
    
    # Initialize database
    engine = create_engine(test_config.database_url)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    
    # Mock Redis
    from unittest.mock import Mock, MagicMock
    redis_client = Mock(spec=RedisClient)
    redis_client.get_next_counter = MagicMock(return_value=1)
    redis_client.cache_url = MagicMock()
    redis_client.get_cached_url = MagicMock(return_value=None)
    redis_client.delete_cache = MagicMock()
    redis_client.is_available = MagicMock(return_value=True)
    
    # Store in module-level variables that gateway.py uses
    import urlshortener.api.gateway as gateway_module
    gateway_module.config = test_config
    gateway_module.redis_client = redis_client
    gateway_module.SessionLocal = SessionLocal
    
    # Override get_db function
    def get_test_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    gateway_module.get_db = get_test_db
    
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client


def test_health_endpoint(test_app):
    """Test health check endpoint."""
    response = test_app.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'


def test_create_short_url(test_app):
    """Test creating a short URL."""
    response = test_app.post(
        '/urls',
        json={'original_url': 'https://example.com'},
        content_type='application/json'
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert 'short_url' in data
    assert data['short_url'].startswith('https://short.ly/')


def test_create_short_url_missing_url(test_app):
    """Test creating short URL without URL."""
    response = test_app.post(
        '/urls',
        json={},
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_create_short_url_with_custom_alias(test_app):
    """Test creating short URL with custom alias."""
    response = test_app.post(
        '/urls',
        json={
            'original_url': 'https://example.com',
            'custom_alias': 'my-link'
        },
        content_type='application/json'
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['short_url'] == 'https://short.ly/my-link'


def test_create_short_url_duplicate_alias(test_app):
    """Test creating short URL with duplicate alias."""
    # Create first
    test_app.post(
        '/urls',
        json={
            'original_url': 'https://example.com',
            'custom_alias': 'duplicate'
        },
        content_type='application/json'
    )
    
    # Try to create duplicate
    response = test_app.post(
        '/urls',
        json={
            'original_url': 'https://another.com',
            'custom_alias': 'duplicate'
        },
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_redirect_short_url(test_app):
    """Test redirecting a short URL."""
    # Create a short URL first
    create_response = test_app.post(
        '/urls',
        json={
            'original_url': 'https://example.com',
            'custom_alias': 'redirect-test'
        },
        content_type='application/json'
    )
    
    # Redirect
    response = test_app.get('/redirect-test', follow_redirects=False)
    
    assert response.status_code == 302
    assert response.location == 'https://example.com'


def test_redirect_nonexistent_url(test_app):
    """Test redirecting a non-existent URL."""
    response = test_app.get('/nonexistent')
    
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data


def test_create_short_url_with_expiration(test_app):
    """Test creating short URL with expiration."""
    expiration = (datetime.utcnow() + timedelta(days=30)).isoformat() + 'Z'
    response = test_app.post(
        '/urls',
        json={
            'original_url': 'https://example.com',
            'expiration_time': expiration
        },
        content_type='application/json'
    )
    
    assert response.status_code == 201

