import pytest

import fakeredis

from ratelimiter.logic import RateLimiter


class FakeClock:
    def __init__(self, start_ms: int = 0) -> None:
        self._now = start_ms

    def now(self) -> int:
        return self._now

    def advance(self, ms: int) -> None:
        self._now += ms


def make_limiter(clock: FakeClock, **overrides) -> RateLimiter:
    redis_client = fakeredis.FakeRedis()
    defaults = dict(
        bucket_capacity=3,
        refill_rate_per_sec=1.0,
        token_ttl_ms=60_000,
        window_ms=1_000,
        time_fn=clock.now,
        use_scripts=False,  # fakeredis does not support evalsha; use Python path
    )
    defaults.update(overrides)
    return RateLimiter(redis_client, **defaults)


def test_allows_until_capacity_then_blocks() -> None:
    clock = FakeClock()
    limiter = make_limiter(clock, bucket_capacity=2, refill_rate_per_sec=0.0)

    first = limiter.acquire("user-1")
    second = limiter.acquire("user-1")
    blocked = limiter.acquire("user-1")

    assert first.allowed is True
    assert second.allowed is True
    assert blocked.allowed is False
    assert blocked.remaining_tokens == pytest.approx(0.0)
    assert blocked.window_count == 3  # analytics still count the request


def test_refill_allows_after_time_passes() -> None:
    clock = FakeClock()
    limiter = make_limiter(clock, bucket_capacity=2, refill_rate_per_sec=1.0)

    limiter.acquire("user-2")
    limiter.acquire("user-2")
    blocked = limiter.acquire("user-2")
    assert blocked.allowed is False

    clock.advance(1500)  # 1.5s -> ~1.5 tokens refilled
    allowed_again = limiter.acquire("user-2")
    assert allowed_again.allowed is True
    assert allowed_again.remaining_tokens == pytest.approx(0.5, rel=1e-2)


def test_sliding_window_usage_trimmed() -> None:
    clock = FakeClock()
    limiter = make_limiter(clock, window_ms=1_000)

    limiter.acquire("user-3")
    clock.advance(200)
    limiter.acquire("user-3")
    clock.advance(900)  # now at 1100ms

    usage = limiter.get_usage("user-3")
    assert usage.window_count == 1  # the first call aged out of the 1s window
    assert usage.remaining_tokens == pytest.approx(2.1, rel=1e-2)

