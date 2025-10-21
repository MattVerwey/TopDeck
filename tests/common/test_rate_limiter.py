"""
Tests for rate limiting functionality.
"""

import pytest
import time
from topdeck.common.rate_limiter import RateLimiter


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
