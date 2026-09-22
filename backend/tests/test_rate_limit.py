import pytest

from app.security.rate_limit import InMemoryRateLimiter, RateLimitExceededError


def test_rate_limiter_allows_up_to_max_requests():
    limiter = InMemoryRateLimiter(max_requests=3, window_seconds=60)
    for _ in range(3):
        limiter.check("key-a")  # não deve levantar


def test_rate_limiter_blocks_after_max_requests():
    limiter = InMemoryRateLimiter(max_requests=3, window_seconds=60)
    for _ in range(3):
        limiter.check("key-a")
    with pytest.raises(RateLimitExceededError):
        limiter.check("key-a")


def test_rate_limiter_keys_are_independent():
    limiter = InMemoryRateLimiter(max_requests=1, window_seconds=60)
    limiter.check("key-a")
    limiter.check("key-b")  # chave diferente, não deve ser bloqueada
