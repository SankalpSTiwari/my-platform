from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Callable

from redis.exceptions import ResponseError


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    remaining_tokens: float
    window_count: int
    window_ms: int


LUA_ACQUIRE_SCRIPT = """
local bucket_key = KEYS[1]
local events_key = KEYS[2]

local now_ms = tonumber(ARGV[1])
local capacity = tonumber(ARGV[2])
local refill_rate_per_sec = tonumber(ARGV[3])
local cost = tonumber(ARGV[4])
local ttl_ms = tonumber(ARGV[5])
local window_ms = tonumber(ARGV[6])
local request_id = ARGV[7]

local tokens = tonumber(redis.call('HGET', bucket_key, 'tokens'))
local last_refill = tonumber(redis.call('HGET', bucket_key, 'ts'))

if tokens == nil then
  tokens = capacity
  last_refill = now_ms
end

local elapsed = math.max(0, now_ms - last_refill)
local refill = (elapsed / 1000.0) * refill_rate_per_sec
tokens = math.min(capacity, tokens + refill)

local allowed = 0
if tokens >= cost then
  allowed = 1
  tokens = tokens - cost
end

redis.call('HSET', bucket_key, 'tokens', tokens, 'ts', now_ms)
redis.call('PEXPIRE', bucket_key, ttl_ms)

-- Sliding window analytics
redis.call('ZADD', events_key, now_ms, request_id)
redis.call('ZREMRANGEBYSCORE', events_key, 0, now_ms - window_ms)
redis.call('PEXPIRE', events_key, ttl_ms)
local window_count = redis.call('ZCARD', events_key)

return {allowed, tokens, window_count}
"""


class RateLimiter:
    def __init__(
        self,
        redis_client,
        *,
        bucket_capacity: int,
        refill_rate_per_sec: float,
        token_ttl_ms: int,
        window_ms: int,
        time_fn: Callable[[], int] | None = None,
        use_scripts: bool = True,
    ) -> None:
        self.redis = redis_client
        self.bucket_capacity = bucket_capacity
        self.refill_rate_per_sec = refill_rate_per_sec
        self.token_ttl_ms = token_ttl_ms
        self.window_ms = window_ms
        self._time_fn = time_fn or (lambda: int(time.time() * 1000))
        self._use_scripts = use_scripts
        self._acquire_script = (
            self.redis.register_script(LUA_ACQUIRE_SCRIPT) if use_scripts else None
        )

    def _bucket_key(self, key: str) -> str:
        return f"rl:{key}:bucket"

    def _events_key(self, key: str) -> str:
        return f"rl:{key}:events"

    def acquire(self, key: str, tokens: float = 1.0) -> RateLimitResult:
        cost = tokens if tokens > 0 else 1.0
        now_ms = self._time_fn()
        req_id = f"{now_ms}-{uuid.uuid4().hex}"

        if self._use_scripts:
            try:
                allowed, remaining, window_count = self._acquire_script(
                    keys=[self._bucket_key(key), self._events_key(key)],
                    args=[
                        now_ms,
                        self.bucket_capacity,
                        self.refill_rate_per_sec,
                        cost,
                        self.token_ttl_ms,
                        self.window_ms,
                        req_id,
                    ],
                )
            except ResponseError as exc:
                # Some test doubles (e.g., fakeredis) may not support evalsha; fall back.
                if "evalsha" not in str(exc).lower():
                    raise
                allowed, remaining, window_count = self._acquire_via_eval(
                    key, req_id, now_ms, cost
                )
        else:
            allowed, remaining, window_count = self._acquire_python(
                key, req_id, now_ms, cost
            )

        return RateLimitResult(
            allowed=bool(allowed),
            remaining_tokens=float(remaining),
            window_count=int(window_count),
            window_ms=self.window_ms,
        )

    def get_usage(self, key: str) -> RateLimitResult:
        """
        Return current sliding-window usage without consuming tokens.
        """
        now_ms = self._time_fn()
        events_key = self._events_key(key)
        # Trim first to avoid stale data skewing metrics.
        self.redis.zremrangebyscore(events_key, 0, now_ms - self.window_ms)
        count = self.redis.zcard(events_key)
        self.redis.pexpire(events_key, self.token_ttl_ms)
        bucket_key = self._bucket_key(key)
        tokens = self.redis.hget(bucket_key, "tokens")
        last_refill = self.redis.hget(bucket_key, "ts")
        tokens_val = float(tokens) if tokens is not None else float(self.bucket_capacity)
        last_refill_val = int(last_refill) if last_refill is not None else now_ms

        elapsed = max(0, now_ms - last_refill_val)
        refill = (elapsed / 1000.0) * self.refill_rate_per_sec
        tokens_val = min(self.bucket_capacity, tokens_val + refill)

        # Refresh stored values so future callers see the up-to-date state.
        self.redis.hset(bucket_key, mapping={"tokens": tokens_val, "ts": now_ms})
        self.redis.pexpire(bucket_key, self.token_ttl_ms)

        return RateLimitResult(
            allowed=True,
            remaining_tokens=tokens_val,
            window_count=int(count),
            window_ms=self.window_ms,
        )

    def _acquire_via_eval(
        self, key: str, request_id: str, now_ms: int, cost: float
    ) -> tuple:
        allowed, remaining, window_count = self.redis.eval(
            LUA_ACQUIRE_SCRIPT,
            2,
            self._bucket_key(key),
            self._events_key(key),
            now_ms,
            self.bucket_capacity,
            self.refill_rate_per_sec,
            cost,
            self.token_ttl_ms,
            self.window_ms,
            request_id,
        )
        return allowed, remaining, window_count

    def _acquire_python(
        self, key: str, request_id: str, now_ms: int, cost: float
    ) -> tuple:
        bucket_key = self._bucket_key(key)
        events_key = self._events_key(key)

        tokens = self.redis.hget(bucket_key, "tokens")
        last_refill = self.redis.hget(bucket_key, "ts")
        tokens_val = float(tokens) if tokens is not None else float(self.bucket_capacity)
        last_refill_val = int(last_refill) if last_refill is not None else now_ms

        elapsed = max(0, now_ms - last_refill_val)
        refill = (elapsed / 1000.0) * self.refill_rate_per_sec
        tokens_val = min(self.bucket_capacity, tokens_val + refill)

        allowed = 0
        if tokens_val >= cost:
            allowed = 1
            tokens_val -= cost

        pipe = self.redis.pipeline()
        pipe.hset(bucket_key, mapping={"tokens": tokens_val, "ts": now_ms})
        pipe.pexpire(bucket_key, self.token_ttl_ms)
        pipe.zadd(events_key, {request_id: now_ms})
        pipe.zremrangebyscore(events_key, 0, now_ms - self.window_ms)
        pipe.pexpire(events_key, self.token_ttl_ms)
        pipe.zcard(events_key)
        _, _, _, _, _, window_count = pipe.execute()

        return allowed, tokens_val, window_count

