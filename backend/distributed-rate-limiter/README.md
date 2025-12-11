# Distributed Rate Limiter (Python + Redis + gRPC)

Cluster-wide token bucket with sliding-window analytics, backed by Redis (cluster-ready) and exposed over gRPC. Metrics are exported via Prometheus for Grafana dashboards.

## Quickstart

1. Install dependencies

```
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

2. Generate gRPC stubs (already generated, rerun if you edit the proto)

```
.venv/bin/python -m grpc_tools.protoc -Iproto --python_out=src --grpc_python_out=src proto/rate_limiter.proto
```

3. Run the server

```
REDIS_URLS=redis://localhost:6379 BUCKET_CAPACITY=100 REFILL_RATE_PER_SEC=50 \
GRPC_PORT=50051 METRICS_PORT=9090 python -m ratelimiter.server
```

The service listens on `GRPC_HOST:GRPC_PORT` (default `0.0.0.0:50051`) and exposes Prometheus metrics on `METRICS_PORT` (default `9090`).

## gRPC Contract

Proto is in `proto/rate_limiter.proto`. Key RPCs:

- `Acquire`: atomically consumes tokens; returns allow/deny, remaining tokens, and sliding-window counts.
- `GetUsage`: returns sliding-window analytics without consuming tokens.

## Configuration (env vars)

- `REDIS_URLS`: comma-separated Redis URLs. Multiple entries enable Redis Cluster.
- `BUCKET_CAPACITY`: max tokens per identity (default 100).
- `REFILL_RATE_PER_SEC`: tokens replenished per second (default 50).
- `TOKEN_TTL_MS`: TTL for bucket state (default 300000).
- `ANALYTICS_WINDOW_MS`: window size for sliding analytics (default 60000).
- `GRPC_HOST` / `GRPC_PORT`: bind host/port for gRPC (default `0.0.0.0:50051`).
- `METRICS_PORT`: Prometheus HTTP port (default 9090).

## Architecture

- **Token bucket**: atomic Lua script maintains bucket tokens & last refill timestamp per key.
- **Sliding window analytics**: request timestamps stored in a sorted set; old entries are trimmed each call.
- **Redis cluster ready**: multiple `REDIS_URLS` triggers `RedisCluster` client with startup nodes.
- **Observability**: Prometheus counters + latency histogram; scrape `METRICS_PORT` and visualize in Grafana.

## Testing

Unit tests use `fakeredis`:

```
.venv/bin/python -m pytest
```

## Development tips

- Edit the proto then run `make proto`.
- Export `PYTHONPATH=src` when running from the repo root.
- Use small `BUCKET_CAPACITY` and `REFILL_RATE_PER_SEC` in dev to see throttling quickly.
