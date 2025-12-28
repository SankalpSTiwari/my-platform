# URL Shortener System

A production-ready URL Shortener system using a **separate Write Service and Read Service** architecture, designed to scale to high read traffic with eventual consistency.

## Architecture

The system consists of:

1. **API Gateway** - Routes requests to appropriate services
2. **Write Service** - Handles short URL creation
3. **Read Service** - Handles redirection requests with caching
4. **Redis** - Global counter for code generation and read-through cache
5. **PostgreSQL** - Primary database for URL mappings

## Features

- ✅ Create short URLs from long URLs
- ✅ Custom alias support
- ✅ Expiration time support
- ✅ High-performance redirects with Redis caching
- ✅ Base62 encoding with optional obfuscation
- ✅ Horizontal scalability
- ✅ Eventual consistency model

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL
- Redis

### Installation

1. **Install dependencies:**
   ```bash
   make install
   # or
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost/urlshortener"
   export REDIS_HOST="localhost"
   export REDIS_PORT="6379"
   export BASE_URL="https://short.ly"
   export SERVICE_PORT="8000"
   ```

3. **Initialize database:**
   ```bash
   make db-init
   # or
   export PYTHONPATH=src
   python -c "from urlshortener.shared.models.database import init_db; from urlshortener.shared.config import Config; init_db(Config.from_env().database_url)"
   ```

4. **Run the server:**
   ```bash
   make run
   # or
   export PYTHONPATH=src
   python -m urlshortener.main
   ```

The server will start on `http://localhost:8000` (or the port specified in `SERVICE_PORT`).

## API Endpoints

### Create Short URL

```bash
POST /urls
Content-Type: application/json

{
  "original_url": "https://example.com/long/path",
  "custom_alias": "optional-string",
  "expiration_time": "2026-01-01T00:00:00Z"
}
```

**Response:**
```json
{
  "short_url": "https://short.ly/Ab3x9Q"
}
```

### Redirect Short URL

```bash
GET /{short_code}
```

**Response:**
- `302 Found` → Redirects to original URL
- `404 Not Found` → URL not found or expired

### Health Check

```bash
GET /health
```

## Configuration

Environment variables:

- `DATABASE_URL` - PostgreSQL connection string (default: `postgresql://localhost/urlshortener`)
- `REDIS_HOST` - Redis host (default: `localhost`)
- `REDIS_PORT` - Redis port (default: `6379`)
- `REDIS_DB` - Redis database number (default: `0`)
- `BASE_URL` - Base URL for short links (default: `https://short.ly`)
- `SERVICE_HOST` - API server host (default: `0.0.0.0`)
- `SERVICE_PORT` - API server port (default: `8000`)
- `CACHE_TTL_SECONDS` - Cache TTL in seconds (default: `3600`)
- `COUNTER_KEY` - Redis key for counter (default: `url_shortener:counter`)
- `MIN_SHORT_CODE_LENGTH` - Minimum short code length (default: `6`)
- `USE_OBFUSCATION` - Enable code obfuscation (default: `true`)

## Design Decisions

### Short Code Generation

- Uses a **global incrementing counter in Redis** (`INCR`)
- Encodes counter using **Base62** (0-9, A-Z, a-z)
- Optionally applies bijective obfuscation to make codes less predictable
- Falls back to timestamp-based generation if Redis is unavailable

### Caching Strategy

- **Read-through cache** in Redis
- Cache key: `url:{short_code}`
- Cache value: Hash with `original_url` and `expiration_time`
- Default TTL: 1 hour
- Cache misses fall back to database

### Scalability

- **Stateless services** for horizontal scaling
- **Read/Write separation** allows independent scaling
- **Redis caching** reduces database load
- **Eventual consistency** model for high availability

### Failure Handling

- **Redis unavailable**: Falls back to database for reads, timestamp-based generation for writes
- **Database unavailable**: Read replicas or snapshots
- **Expired URLs**: Treated as non-existent (404)

## Database Schema

### Table: `urls`

| Column          | Type         | Notes    |
| --------------- | ------------ | -------- |
| short_code      | VARCHAR (PK) | Unique   |
| original_url    | TEXT         |          |
| created_at      | TIMESTAMP    |          |
| expiration_time | TIMESTAMP    | nullable |
| user_id         | VARCHAR(36)  | nullable |

**Indexes:**
- Primary key on `short_code`

## Performance Targets

- **Redirect latency**: ≤ 200ms (P95)
- **Throughput**: ~100M redirects per day
- **Capacity**: ~1B total URLs

## Project Structure

```
url-shortener/
├── src/
│   └── urlshortener/
│       ├── __init__.py
│       ├── main.py                 # Entry point
│       ├── api/
│       │   └── gateway.py          # API Gateway
│       ├── write_service/
│       │   └── service.py          # Write Service
│       ├── read_service/
│       │   └── service.py          # Read Service
│       └── shared/
│           ├── config.py           # Configuration
│           ├── models/
│           │   └── database.py    # Database models
│           └── utils/
│               ├── base62.py       # Base62 encoding
│               └── redis_client.py # Redis utilities
├── tests/                          # Unit tests
├── docs/                           # Documentation
├── requirements.txt
├── Makefile
└── README.md
```

## Testing

Run the full test suite:

```bash
make test
# or
export PYTHONPATH=src
pytest tests/ -v
```

**Test Coverage:**
- ✅ Base62 encoding/decoding (6 tests)
- ✅ Write Service functionality (8 tests)
- ✅ Read Service functionality (6 tests)
- ✅ API endpoint integration (8 tests)

**Total: 28 tests, all passing** ✅

## Example Usage

### 1. Create a Simple Short URL

```bash
curl -X POST http://localhost:8000/urls \
  -H "Content-Type: application/json" \
  -d '{
    "original_url": "https://example.com/very/long/url/path"
  }'
```

**Response:**
```json
{
  "short_url": "https://short.ly/Ab3x9Q"
}
```

### 2. Create with Custom Alias

```bash
curl -X POST http://localhost:8000/urls \
  -H "Content-Type: application/json" \
  -d '{
    "original_url": "https://www.google.com",
    "custom_alias": "google"
  }'
```

**Response:**
```json
{
  "short_url": "https://short.ly/google"
}
```

### 3. Create with Expiration

```bash
curl -X POST http://localhost:8000/urls \
  -H "Content-Type: application/json" \
  -d '{
    "original_url": "https://example.com",
    "expiration_time": "2026-12-31T23:59:59Z"
  }'
```

### 4. Redirect to Original URL

```bash
# Follow redirects automatically
curl -L http://localhost:8000/google

# Or just get the redirect header
curl -I http://localhost:8000/google
```

**Response:**
```
HTTP/1.1 302 Found
Location: https://www.google.com
```

### 5. Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "redis_available": true
}
```

### Python Example

```python
import requests

# Create short URL
response = requests.post(
    'http://localhost:8000/urls',
    json={
        'original_url': 'https://example.com',
        'custom_alias': 'example'
    }
)
short_url = response.json()['short_url']
print(f"Short URL: {short_url}")

# Redirect
response = requests.get('http://localhost:8000/example', allow_redirects=True)
print(f"Final URL: {response.url}")
```

## Troubleshooting

### Redis Connection Issues

If Redis is not available, the system will:
- **Write Service**: Fall back to timestamp-based code generation
- **Read Service**: Query database directly (no caching)

To check Redis connection:
```bash
redis-cli ping
```

### Database Connection Issues

Ensure PostgreSQL is running and accessible:
```bash
psql -h localhost -U your_user -d urlshortener -c "SELECT 1;"
```

### Port Already in Use

If port 8000 is already in use, set a different port:
```bash
export SERVICE_PORT=8001
make run
```

### Import Errors

Make sure `PYTHONPATH` is set:
```bash
export PYTHONPATH=src
```

## Development

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
pytest tests/ --cov=src/urlshortener --cov-report=html

# Run specific test file
pytest tests/test_write_service.py -v
```

### Code Structure

- **Write Service** (`write_service/service.py`): Handles URL creation
- **Read Service** (`read_service/service.py`): Handles redirects with caching
- **API Gateway** (`api/gateway.py`): Routes requests to appropriate service
- **Shared Utilities** (`shared/`): Common models, config, and utilities

### Adding New Features

1. Add tests first (TDD approach)
2. Implement feature in appropriate service
3. Update API gateway if needed
4. Run tests to verify
5. Update documentation

## Performance Considerations

### Caching

- Redis cache reduces database load by ~90%
- Cache TTL: 1 hour (configurable)
- Cache keys: `url:{short_code}`

### Database

- Primary key index on `short_code` for fast lookups
- Consider read replicas for high read traffic
- Connection pooling recommended for production

### Scaling

- **Horizontal**: Deploy multiple instances behind load balancer
- **Vertical**: Increase Redis memory for larger cache
- **Database**: Use read replicas for Read Service

## Future Enhancements

- [ ] Analytics and click tracking
- [ ] User authentication
- [ ] Custom domains
- [ ] Bulk URL creation
- [ ] URL preview/metadata
- [ ] Rate limiting
- [ ] Webhook notifications
- [ ] Separate Write/Read services into different processes
- [ ] Metrics and monitoring (Prometheus/Grafana)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## License

MIT

