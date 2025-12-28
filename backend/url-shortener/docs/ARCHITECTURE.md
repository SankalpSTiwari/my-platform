# URL Shortener Architecture

## Overview

This document describes the architecture of the URL Shortener system, which uses a **separate Read/Write Service** pattern to achieve high scalability and availability.

## System Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│   API Gateway   │  (Routes requests)
└──────┬──────────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌─────────────┐   ┌─────────────┐
│Write Service│   │Read Service │
└──────┬──────┘   └──────┬───────┘
       │                 │
       ├─────────┐       ├─────────┐
       │         │       │         │
       ▼         ▼       ▼         ▼
┌─────────┐ ┌──────┐ ┌─────────┐ ┌──────┐
│PostgreSQL│ │Redis │ │PostgreSQL│ │Redis │
│(Primary) │ │(Counter)│ │(Read) │ │(Cache)│
└─────────┘ └──────┘ └─────────┘ └──────┘
```

## Components

### 1. API Gateway

**Location:** `src/urlshortener/api/gateway.py`

Routes incoming requests:
- `POST /urls` → Write Service
- `GET /{short_code}` → Read Service
- `GET /health` → Health check

### 2. Write Service

**Location:** `src/urlshortener/write_service/service.py`

**Responsibilities:**
- Generate unique short codes
- Validate custom aliases
- Store URL mappings in database
- Cache new URLs in Redis

**Short Code Generation:**
1. Get next counter from Redis (`INCR url_shortener:counter`)
2. Encode counter to Base62
3. Optionally apply obfuscation
4. Store mapping in PostgreSQL

**Failure Handling:**
- Redis unavailable → Fallback to timestamp-based generation
- Duplicate custom alias → Return error
- Database error → Rollback transaction

### 3. Read Service

**Location:** `src/urlshortener/read_service/service.py`

**Responsibilities:**
- Retrieve original URLs with caching
- Handle redirects
- Check expiration times

**Caching Strategy:**
1. Check Redis cache first
2. Cache hit → Return immediately
3. Cache miss → Query database
4. Store result in Redis
5. Return original URL

**Performance:**
- Target: ≤ 200ms P95 latency
- Cache hit rate: ~90%+ expected

### 4. Redis

**Uses:**
1. **Global Counter** (`url_shortener:counter`)
   - Atomic increment for unique ID generation
   - Key: `url_shortener:counter`
   - Type: Integer

2. **Read-Through Cache** (`url:{short_code}`)
   - Stores URL mappings
   - Key: `url:{short_code}`
   - Type: Hash
   - Fields: `original_url`, `expiration_time`
   - TTL: 1 hour (configurable)

### 5. PostgreSQL

**Schema:**
- Table: `urls`
- Primary Key: `short_code`
- Indexes: Primary key index on `short_code`

**Data:**
- `short_code`: VARCHAR(255) - Unique identifier
- `original_url`: TEXT - Original long URL
- `created_at`: TIMESTAMP - Creation time
- `expiration_time`: TIMESTAMP - Optional expiration
- `user_id`: VARCHAR(36) - Optional user identifier

## Data Flow

### Creating a Short URL

```
1. Client → API Gateway: POST /urls
2. API Gateway → Write Service: create_short_url()
3. Write Service → Redis: INCR counter
4. Write Service: Encode counter to Base62
5. Write Service → PostgreSQL: INSERT url mapping
6. Write Service → Redis: Cache URL
7. Write Service → API Gateway: Return short_url
8. API Gateway → Client: 201 Created
```

### Redirecting a Short URL

```
1. Client → API Gateway: GET /{short_code}
2. API Gateway → Read Service: get_original_url()
3. Read Service → Redis: Check cache
4a. Cache Hit → Read Service: Return original_url
4b. Cache Miss → Read Service → PostgreSQL: Query database
5. Read Service → Redis: Cache result
6. Read Service → API Gateway: Return original_url
7. API Gateway → Client: 302 Redirect
```

## Scalability Design

### Horizontal Scaling

- **Stateless Services**: Both services are stateless and can scale horizontally
- **Load Balancing**: API Gateway can be load balanced
- **Database Read Replicas**: Read Service can use read replicas
- **Redis Cluster**: Redis can be clustered for high availability

### Read/Write Separation

- **Independent Scaling**: Read and Write services scale independently
- **Different Patterns**: Read service optimized for caching, Write service for consistency
- **Traffic Distribution**: ~100:1 read/write ratio expected

### Caching Strategy

- **Read-Through Cache**: Reduces database load
- **Cache TTL**: 1 hour default (configurable)
- **Cache Invalidation**: Automatic on expiration
- **Fallback**: Database query if cache miss

## Failure Handling

### Redis Failure

**Write Service:**
- Counter unavailable → Fallback to timestamp-based generation
- Cache write failure → Log warning, continue

**Read Service:**
- Cache unavailable → Direct database query
- No impact on functionality, only performance

### Database Failure

**Write Service:**
- Transaction rollback
- Return error to client

**Read Service:**
- Use read replicas if available
- Return 500 error if no replicas

### Expired URLs

- Checked in both cache and database
- Treated as non-existent (404)
- Not cached if expired

## Performance Characteristics

### Write Service

- **Latency**: ~50-100ms (database write + Redis operations)
- **Throughput**: Limited by database write capacity
- **Consistency**: Strong consistency (ACID transactions)

### Read Service

- **Latency**: 
  - Cache hit: ~1-5ms
  - Cache miss: ~50-100ms (database query)
- **Throughput**: High (caching reduces database load)
- **Consistency**: Eventual (cache may be slightly stale)

## Security Considerations

- **URL Validation**: Basic format validation
- **Custom Alias**: Character validation
- **Rate Limiting**: Can be added at API Gateway
- **Input Sanitization**: SQL injection prevention via SQLAlchemy

## Future Enhancements

- [ ] Separate Write and Read services into different processes
- [ ] Add analytics and click tracking
- [ ] Implement rate limiting
- [ ] Add authentication and user management
- [ ] Support custom domains
- [ ] Add webhook notifications
- [ ] Implement URL preview/metadata

