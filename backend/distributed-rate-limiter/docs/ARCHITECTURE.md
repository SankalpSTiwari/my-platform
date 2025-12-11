# Distributed Rate Limiter – Architecture & Operations

## Overview
- **Goal:** Centralized, horizontally scalable token bucket with sliding-window analytics, exposed over gRPC, backed by Redis (cluster-ready), with Prometheus metrics for Grafana.
- **Key paths:** `src/ratelimiter/logic.py` (token bucket + analytics), `src/ratelimiter/server.py` (gRPC), `src/ratelimiter/metrics.py` (Prometheus), `src/ratelimiter/redis_client.py` (Redis/RedisCluster).

## Core Algorithm (Token Bucket + Sliding Window)
- Each identity/key has two Redis structures:
  - `rl:{key}:bucket` (hash) → `tokens`, `ts` (last refill ms).
  - `rl:{key}:events` (sorted set) → request timestamps for sliding-window counts.
- **Acquire (Lua, atomic):**
  1. Refill tokens based on elapsed time and `refill_rate_per_sec` up to `bucket_capacity`.
  2. If `tokens >= cost`, allow and decrement; else deny.
  3. Update bucket hash + TTL, append event to ZSET, trim old events (`now - window_ms`), set TTL.
  4. Return `(allowed, remaining_tokens, window_count)`.
- **Fallbacks:** If `EVALSHA` unsupported (e.g., some fakes), falls back to `EVAL`; tests can force a pure-Python pipeline path (`use_scripts=False`).
- **GetUsage (read-only):** Trims old events, returns ZSET count and computes up-to-date token refill without consuming tokens; refreshes bucket state + TTL.

## Request Flow
1. Client calls gRPC `Acquire` with `key` and optional `tokens`.
2. `RateLimiterService` delegates to `RateLimiter.acquire`.
3. Lua script runs atomically on Redis (or fallback), returns decision + remaining + window count.
4. Prometheus counters/histogram updated; response returned.
5. `GetUsage` mirrors read path without consuming tokens.

## Data Model & Keys
- Bucket hash: `rl:{key}:bucket` → `tokens`, `ts`
- Events ZSET: `rl:{key}:events` → members: unique request IDs, score: timestamp ms
- TTL: `token_ttl_ms` applied to both to avoid unbounded growth.

## Configuration (env)
- `REDIS_URLS` (comma-separated; multiple → cluster mode)
- `BUCKET_CAPACITY`, `REFILL_RATE_PER_SEC`, `TOKEN_TTL_MS`, `ANALYTICS_WINDOW_MS`
- `GRPC_HOST`, `GRPC_PORT` (default `0.0.0.0:50051`)
- `METRICS_PORT` (default `9090`)
See `src/ratelimiter/config.py` for defaults and parsing.

## Deployment Notes
- **Redis:** Single instance or Redis Cluster; client auto-selects based on `REDIS_URLS`.
- **gRPC server:** ThreadPool executor (32 workers by default); expose via load balancer for horizontal scaling.
- **State locality:** Any instance can serve any key; Redis enforces atomicity. For extreme hotspots, consider key hashing/sharding at the client to reduce cross-node hops in a cluster.
- **Graceful shutdown:** SIGINT/SIGTERM stop with grace period.

## Observability
- Prometheus metrics (`src/ratelimiter/metrics.py`):
  - `rate_limiter_requests_total{result=allowed|throttled}`
  - `rate_limiter_request_latency_seconds` histogram
- Scrape `METRICS_PORT` and build Grafana dashboards for allow/throttle rates, P99 latency.

## Testing & Local Dev
- Install deps: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
- Regenerate stubs after proto changes: `.venv/bin/python -m grpc_tools.protoc -Iproto --python_out=src --grpc_python_out=src proto/rate_limiter.proto`
- Run server: `PYTHONPATH=src REDIS_URLS=redis://localhost:6379 .venv/bin/python -m ratelimiter.server`
- Tests (fakeredis): `PYTHONPATH=src .venv/bin/python -m pytest`
- Make targets: `make proto`, `make test`, `make run` (requires `PYTHONPATH=src` when not installed as a package).

## Failure Modes & Consistency
- **Atomicity:** Lua script guarantees single-key atomic updates per shard; Redis Cluster routes by hash slot (`rl:{key}:...` stable prefix).
- **Partial failure:** If Redis unavailable, RPC will error; clients should retry with backoff.
- **TTL expiry:** Buckets expire to reclaim memory; first request after expiry starts with full `bucket_capacity`.
- **Clock:** Relies on Redis server time (via Lua `now_ms` argument from app). Ensure relatively synchronized clocks across app instances; minor skew only affects refill precision.

## Extensibility Ideas
- Add per-route/policy configs fetched from a control plane.
- Add `Retry-After` hints in responses.
- Add multi-tenant metrics labels (e.g., `tenant`).
- Support priority/burst multipliers per key.

