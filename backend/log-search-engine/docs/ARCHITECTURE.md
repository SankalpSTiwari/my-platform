# Log Search Engine Architecture

## Overview

The Log Search Engine is designed for efficient full-text search over log data with support for time-based queries, aggregations, and fuzzy matching.

## Core Components

### 1. Inverted Index

The inverted index maps terms to posting lists containing:
- Document IDs
- Term positions within documents
- Relevance scores (TF-IDF)

**Key Features:**
- Tokenization: Splits text into terms (alphanumeric, min 2 chars)
- TF-IDF Scoring: Term frequency × Inverse document frequency
- Fuzzy Matching: Uses RapidFuzz for typo tolerance
- Position Tracking: Enables phrase matching (future enhancement)

**Data Structure:**
```
index: {
  "error": [Posting(doc_id="1", positions=[0, 45], score=2.5), ...],
  "timeout": [Posting(doc_id="2", positions=[12], score=1.8), ...]
}
```

### 2. Time-Based Partitioning

Logs are partitioned by time windows (default: 1 hour) for:
- Efficient time-range queries (only search relevant partitions)
- Automatic cleanup of old data
- Memory management (bounded partition count)

**Partition Structure:**
```
Partition {
  start_time: 1705315800000
  end_time: 1705319400000
  index: InvertedIndex
  doc_count: 1500
}
```

**Partition Manager:**
- Maintains multiple partitions
- Routes documents to correct partition based on timestamp
- Cleans up partitions exceeding `max_partitions` limit
- Searches across partitions within time range

### 3. Query Engine

The query engine parses and executes queries with:

**Query Parser:**
- Extracts field filters (`level:ERROR`)
- Parses boolean operators (`AND`, `OR`, `NOT`)
- Identifies aggregation clauses (`| group by level`)

**Execution Flow:**
1. Parse query string
2. Build text search query from terms
3. Search partitions within time range
4. Apply field filters
5. Compute aggregations
6. Return ranked results

**Query Examples:**
```
"error"                                    # Simple text
"level:ERROR AND message:timeout"          # Field filters
"error | group by level"                   # With aggregation
"level:ERROR AND NOT source:test"          # Boolean logic
```

### 4. API Server

REST API endpoints:

- `POST /api/logs` - Ingest single log
- `POST /api/logs/batch` - Ingest multiple logs
- `GET/POST /api/search` - Search logs
- `GET /api/stats` - Engine statistics
- `GET /health` - Health check

**Request/Response Format:**
```json
// Ingest
POST /api/logs
{
  "message": "Error occurred",
  "level": "ERROR",
  "source": "api-service",
  "timestamp": "2024-01-15T10:30:00Z"
}

// Search
POST /api/search
{
  "query": "error | group by level",
  "start_time": 1705315800000,
  "end_time": 1705319400000,
  "limit": 100
}

// Response
{
  "query": "error",
  "total_count": 45,
  "returned_count": 45,
  "execution_time_ms": 12.5,
  "results": [...],
  "aggregations": {
    "groups": {
      "level=ERROR": 30,
      "level=WARN": 15
    }
  }
}
```

### 5. Frontend Dashboard

React-based visualization with:
- Search interface with query examples
- Time range filters
- Results display with syntax highlighting
- Aggregation charts (bar charts via Recharts)
- Log ingestion form

## Data Flow

### Ingestion Flow

```
Log Entry → API Server → TimePartitionManager → TimePartition → InvertedIndex
```

1. API receives log entry
2. Creates Document object with timestamp
3. PartitionManager routes to appropriate time partition
4. Partition adds document to its InvertedIndex
5. Index tokenizes and updates posting lists

### Search Flow

```
Query → QueryEngine → QueryParser → PartitionManager → InvertedIndex → Results
```

1. QueryEngine receives query string
2. QueryParser extracts terms, filters, aggregations
3. PartitionManager searches relevant partitions
4. Each partition's InvertedIndex performs search
5. Results merged and ranked by score
6. Field filters applied
7. Aggregations computed
8. Results returned to client

## Performance Considerations

### Indexing
- **Time Complexity**: O(n) where n = document length
- **Space Complexity**: O(m) where m = total unique terms

### Searching
- **Time Complexity**: O(k × log(d)) where k = query terms, d = documents
- **Partitioning**: Reduces search space by time range
- **Fuzzy Matching**: O(t) where t = indexed terms (can be optimized with indexing)

### Memory Management
- Partitions automatically cleaned up when exceeding limit
- Oldest partitions removed first (FIFO)
- Configurable via `MAX_PARTITIONS`

## Scalability

### Current Limitations
- In-memory storage (not persistent)
- Single-node (no distributed search)
- No sharding across multiple machines

### Future Enhancements
- Persistent storage (Redis, Elasticsearch backend)
- Distributed search across nodes
- Sharding by time or hash
- Caching layer for frequent queries
- Index compression

## Security Considerations

- No authentication/authorization (add for production)
- CORS enabled for frontend (restrict origins in production)
- Input validation on query strings
- Rate limiting recommended for API

## Monitoring

- Execution time tracking per query
- Partition statistics (count, document counts)
- Search result counts
- Error logging

Metrics can be exported to Prometheus (future enhancement).

