# Log Search Engine

A full-text search engine optimized for logs with inverted index, time-based partitioning, query language, and visualization dashboard.

## Features

- **Inverted Index**: Fast full-text search using term-to-document mapping
- **Time-Based Partitioning**: Efficient storage and retrieval with automatic cleanup
- **Query Language**: Support for field filters, boolean operators, and aggregations
- **Fuzzy Search**: Typo-tolerant search using RapidFuzz
- **Visualization Dashboard**: React-based UI for search and analytics
- **REST API**: HTTP API for log ingestion and search

## Architecture

### Components

1. **Inverted Index** (`index/inverted_index.py`)
   - Maps terms to posting lists (document IDs + positions)
   - TF-IDF scoring for relevance ranking
   - Fuzzy matching support

2. **Time Partitioning** (`partition/time_partition.py`)
   - Partitions logs by time windows (default: 1 hour)
   - Automatic cleanup of old partitions
   - Efficient time-range queries

3. **Query Engine** (`query/query_engine.py`)
   - Parses query language
   - Executes searches across partitions
   - Computes aggregations

4. **API Server** (`api/server.py`)
   - REST endpoints for ingestion and search
   - CORS-enabled for frontend access

5. **Frontend Dashboard** (`frontend/`)
   - React-based search interface
   - Real-time visualization with Recharts
   - Log ingestion form

## Quickstart

### Backend Setup

1. Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. Run the server:

```bash
export PYTHONPATH=src
python -m logsearch.main
```

Or using environment variables:

```bash
API_PORT=5000 PARTITION_DURATION_MS=3600000 python -m logsearch.main
```

### Frontend Setup

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Start the development server:

```bash
npm start
```

The frontend will be available at `http://localhost:3000` and will proxy API requests to `http://localhost:5000`.

## API Usage

### Ingest Logs

```bash
curl -X POST http://localhost:5000/api/logs \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Error occurred in payment processing",
    "level": "ERROR",
    "source": "payment-service",
    "timestamp": "2024-01-15T10:30:00Z"
  }'
```

### Batch Ingest

```bash
curl -X POST http://localhost:5000/api/logs/batch \
  -H "Content-Type: application/json" \
  -d '{
    "logs": [
      {"message": "User logged in", "level": "INFO"},
      {"message": "Database connection failed", "level": "ERROR"}
    ]
  }'
```

### Search

```bash
# Simple text search
curl "http://localhost:5000/api/search?q=error"

# With field filters
curl "http://localhost:5000/api/search?q=level:ERROR"

# With time range
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "error",
    "start_time": 1705315800000,
    "end_time": 1705319400000
  }'
```

### Aggregations

```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "error | group by level"
  }'
```

## Query Language

### Simple Text Search

```
error
timeout
database connection
```

### Field Filters

```
level:ERROR
source:payment-service
level:ERROR AND source:api
level:ERROR OR level:WARN
level:ERROR AND NOT source:test
```

### Aggregations

```
error | group by level
level:ERROR | group by source
error | group by level, source | count
```

## Configuration

Environment variables:

- `PARTITION_DURATION_MS`: Duration of each partition in milliseconds (default: 3600000 = 1 hour)
- `MAX_PARTITIONS`: Maximum number of partitions to keep (default: 168 = 7 days)
- `API_HOST`: API server host (default: 0.0.0.0)
- `API_PORT`: API server port (default: 5000)
- `DEFAULT_LIMIT`: Default search result limit (default: 100)
- `FUZZY_THRESHOLD`: Fuzzy matching threshold 0-100 (default: 80)

## Testing

Run tests:

```bash
export PYTHONPATH=src
pytest tests/
```

With coverage:

```bash
pytest tests/ --cov=logsearch --cov-report=html
```

## Project Structure

```
log-search-engine/
├── src/
│   └── logsearch/
│       ├── index/          # Inverted index implementation
│       ├── partition/      # Time-based partitioning
│       ├── query/          # Query engine and parser
│       ├── api/            # REST API server
│       ├── config.py       # Configuration
│       └── main.py         # Entry point
├── frontend/               # React dashboard
│   ├── src/
│   │   ├── components/     # React components
│   │   └── App.js          # Main app
│   └── package.json
├── tests/                  # Unit tests
├── docs/                   # Documentation
├── requirements.txt        # Python dependencies
└── README.md
```

## Resume Bullet

**Developed a log search platform with a custom inverted index, time-based partitioning, and a query engine supporting fuzzy search and aggregations.**

## License

MIT

