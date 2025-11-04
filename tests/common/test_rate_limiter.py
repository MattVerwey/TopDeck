"""
Tests for rate limiting functionality.
"""

import time
from unittest.mock import AsyncMock

import pytest

from topdeck.common.rate_limiter import RateLimiter, RedisRateLimiter


def test_rate_limiter_allows_requests_within_limit():
    """Test that rate limiter allows requests within the limit."""
    limiter = RateLimiter(requests_per_minute=5)
    client_id = "test-client"

    # Should allow 5 requests
    for _ in range(5):
        assert limiter.is_allowed(client_id) is True


def test_rate_limiter_blocks_requests_over_limit():
    """Test that rate limiter blocks requests over the limit."""
    limiter = RateLimiter(requests_per_minute=3)
    client_id = "test-client"

    # Use up the limit
    for _ in range(3):
        assert limiter.is_allowed(client_id) is True

    # Next request should be blocked
    assert limiter.is_allowed(client_id) is False


def test_rate_limiter_resets_after_window():
    """Test that rate limiter resets after the time window."""
    limiter = RateLimiter(requests_per_minute=2)
    client_id = "test-client"

    # Use up the limit
    assert limiter.is_allowed(client_id) is True
    assert limiter.is_allowed(client_id) is True
    assert limiter.is_allowed(client_id) is False

    # Wait for window to pass (simulate with small window for testing)
    limiter.window_seconds = 1
    time.sleep(1.1)

    # Should be allowed again
    assert limiter.is_allowed(client_id) is True


def test_rate_limiter_separate_clients():
    """Test that rate limiter tracks clients separately."""
    limiter = RateLimiter(requests_per_minute=2)

    # Client 1 uses up their limit
    assert limiter.is_allowed("client-1") is True
    assert limiter.is_allowed("client-1") is True
    assert limiter.is_allowed("client-1") is False

    # Client 2 should still be allowed
    assert limiter.is_allowed("client-2") is True
    assert limiter.is_allowed("client-2") is True


def test_get_retry_after():
    """Test getting retry after time."""
    limiter = RateLimiter(requests_per_minute=1)
    client_id = "test-client"

    # Use up limit
    limiter.is_allowed(client_id)
    limiter.is_allowed(client_id)

    # Check retry after
    retry_after = limiter.get_retry_after(client_id)
    assert retry_after > 0
    assert retry_after <= 60


# Redis Rate Limiter Tests


@pytest.mark.asyncio
async def test_redis_rate_limiter_check_rate_limit():
    """Test that check_rate_limit returns all info in single call."""
    redis_client = AsyncMock()
    
    # Mock eval to return [allowed, remaining, retry_after]
    redis_client.eval = AsyncMock(return_value=[1, 95, 0])
    
    limiter = RedisRateLimiter(
        redis_client=redis_client,
        requests_per_minute=60,
        burst_size=120,
    )
    
    client_id = "test-client"
    
    # Should return all info
    is_allowed, remaining, retry_after, reset_timestamp = await limiter.check_rate_limit(client_id)
    assert is_allowed is True
    assert remaining == 95
    assert retry_after == 0
    assert reset_timestamp > 0
    
    # Verify only one Redis eval call
    assert redis_client.eval.call_count == 1


@pytest.mark.asyncio
async def test_redis_rate_limiter_allows_requests_within_burst():
    """Test that Redis rate limiter allows requests within burst size."""
    # Mock Redis client
    redis_client = AsyncMock()
    
    # Mock eval to return [allowed, remaining, retry_after]
    redis_client.eval = AsyncMock(return_value=[1, 9, 0])
    
    limiter = RedisRateLimiter(
        redis_client=redis_client,
        requests_per_minute=60,
        burst_size=10,
    )
    
    client_id = "test-client"
    
    # Should allow requests
    result = await limiter.is_allowed(client_id)
    assert result is True
    
    # Verify Redis eval was called
    assert redis_client.eval.called


@pytest.mark.asyncio
async def test_redis_rate_limiter_blocks_over_limit():
    """Test that Redis rate limiter blocks requests over limit."""
    redis_client = AsyncMock()
    
    # Mock eval to return [blocked, remaining, retry_after]
    redis_client.eval = AsyncMock(return_value=[0, 0, 5])
    
    limiter = RedisRateLimiter(
        redis_client=redis_client,
        requests_per_minute=60,
        burst_size=10,
    )
    
    client_id = "test-client"
    
    # Should block request
    result = await limiter.is_allowed(client_id)
    assert result is False


@pytest.mark.asyncio
async def test_redis_rate_limiter_scopes():
    """Test that Redis rate limiter supports different scopes."""
    redis_client = AsyncMock()
    redis_client.eval = AsyncMock(return_value=1)
    
    limiter = RedisRateLimiter(
        redis_client=redis_client,
        requests_per_minute=60,
    )
    
    client_id = "test-client"
    
    # Test different scopes
    await limiter.is_allowed(client_id, scope="topology")
    await limiter.is_allowed(client_id, scope="risk")
    
    # Verify different Redis keys were used
    assert redis_client.eval.call_count == 2
    calls = redis_client.eval.call_args_list
    
    # Extract keys from call arguments (third positional argument in eval)
    # Call signature: eval(script, num_keys, key, ...)
    EVAL_KEY_INDEX = 2
    key1 = calls[0].args[EVAL_KEY_INDEX]
    key2 = calls[1].args[EVAL_KEY_INDEX]
    
    # Keys should be different for different scopes
    assert key1 != key2
    assert "topology" in key1
    assert "risk" in key2


@pytest.mark.asyncio
async def test_redis_rate_limiter_get_remaining():
    """Test getting remaining tokens."""
    redis_client = AsyncMock()
    
    # Mock hmget to return bucket state: 5 tokens, current time
    redis_client.hmget = AsyncMock(return_value=[b"5.0", str(time.time()).encode()])
    
    limiter = RedisRateLimiter(
        redis_client=redis_client,
        requests_per_minute=60,
        burst_size=10,
    )
    
    client_id = "test-client"
    
    remaining = await limiter.get_remaining(client_id)
    assert remaining == 5


@pytest.mark.asyncio
async def test_redis_rate_limiter_get_retry_after():
    """Test getting retry after time."""
    redis_client = AsyncMock()
    
    # Mock hmget to return bucket state: 0.5 tokens, current time
    current_time = time.time()
    redis_client.hmget = AsyncMock(return_value=[b"0.5", str(current_time).encode()])
    
    limiter = RedisRateLimiter(
        redis_client=redis_client,
        requests_per_minute=60,  # 1 token per second
        burst_size=10,
    )
    
    client_id = "test-client"
    
    retry_after = await limiter.get_retry_after(client_id)
    # Should be around 0.5 seconds to get 1 token (0.5 + 0.5 = 1)
    assert retry_after >= 0
    assert retry_after <= 2


@pytest.mark.asyncio
async def test_redis_rate_limiter_fails_open_on_error():
    """Test that Redis rate limiter fails open (allows) on Redis error."""
    redis_client = AsyncMock()
    
    # Mock eval to raise an exception
    redis_client.eval = AsyncMock(side_effect=Exception("Redis error"))
    
    limiter = RedisRateLimiter(
        redis_client=redis_client,
        requests_per_minute=60,
    )
    
    client_id = "test-client"
    
    # Should allow request even on error (fail open)
    result = await limiter.is_allowed(client_id)
    assert result is True


@pytest.mark.asyncio
async def test_redis_rate_limiter_without_redis():
    """Test that Redis rate limiter handles missing Redis client gracefully."""
    limiter = RedisRateLimiter(
        redis_client=None,
        requests_per_minute=60,
    )
    
    client_id = "test-client"
    
    # Should always allow when Redis is not available
    result = await limiter.is_allowed(client_id)
    assert result is True
    
    remaining = await limiter.get_remaining(client_id)
    assert remaining > 0
    
    retry_after = await limiter.get_retry_after(client_id)
    assert retry_after == 0
