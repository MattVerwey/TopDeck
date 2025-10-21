"""
Tests for resilience utilities.
"""

import asyncio
import time

import pytest

from topdeck.common.resilience import (
    CircuitBreaker,
    ErrorTracker,
    RateLimiter,
    RetryConfig,
    retry_with_backoff,
)


class TestRateLimiter:
    """Tests for RateLimiter"""

    @pytest.mark.asyncio
    async def test_rate_limiter_basic(self):
        """Test basic rate limiting"""
        limiter = RateLimiter(max_calls=5, time_window=1.0)

        # First 5 calls should be immediate
        start = time.time()
        for _ in range(5):
            await limiter.acquire()
        elapsed = time.time() - start

        assert elapsed < 0.1  # Should be nearly instant

    @pytest.mark.asyncio
    async def test_rate_limiter_enforces_limit(self):
        """Test that rate limiter enforces the limit"""
        limiter = RateLimiter(max_calls=3, time_window=1.0)

        # First 3 calls are immediate
        for _ in range(3):
            await limiter.acquire()

        # 4th call should wait
        start = time.time()
        await limiter.acquire()
        elapsed = time.time() - start

        # Should have waited close to 1 second
        assert elapsed >= 0.9


class TestRetryConfig:
    """Tests for RetryConfig"""

    def test_retry_config_defaults(self):
        """Test default retry configuration"""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_retry_config_custom(self):
        """Test custom retry configuration"""
        config = RetryConfig(
            max_attempts=5,
            initial_delay=0.5,
            max_delay=30.0,
            exponential_base=3.0,
            jitter=False,
        )

        assert config.max_attempts == 5
        assert config.initial_delay == 0.5
        assert config.max_delay == 30.0
        assert config.exponential_base == 3.0
        assert config.jitter is False


class TestRetryWithBackoff:
    """Tests for retry_with_backoff decorator"""

    @pytest.mark.asyncio
    async def test_retry_succeeds_first_try(self):
        """Test that successful function doesn't retry"""
        call_count = 0

        @retry_with_backoff(config=RetryConfig(max_attempts=3, initial_delay=0.1))
        async def succeeds():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await succeeds()

        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_succeeds_second_try(self):
        """Test that failing function retries and succeeds"""
        call_count = 0

        @retry_with_backoff(config=RetryConfig(max_attempts=3, initial_delay=0.1))
        async def fails_once():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First try fails")
            return "success"

        result = await fails_once()

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_exhausts_attempts(self):
        """Test that retry gives up after max attempts"""
        call_count = 0

        @retry_with_backoff(config=RetryConfig(max_attempts=3, initial_delay=0.1))
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(ValueError):
            await always_fails()

        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_specific_exceptions(self):
        """Test that retry only handles specific exceptions"""
        call_count = 0

        @retry_with_backoff(
            config=RetryConfig(max_attempts=3, initial_delay=0.1), exceptions=(ValueError,)
        )
        async def raises_different_error():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise KeyError("Different error")
            return "success"

        # Should raise immediately without retry
        with pytest.raises(KeyError):
            await raises_different_error()

        assert call_count == 1


class TestErrorTracker:
    """Tests for ErrorTracker"""

    def test_error_tracker_init(self):
        """Test initializing error tracker"""
        tracker = ErrorTracker()

        assert tracker.success_count == 0
        assert tracker.failure_count == 0
        assert len(tracker.errors) == 0

    def test_error_tracker_record_success(self):
        """Test recording successes"""
        tracker = ErrorTracker()

        tracker.record_success("item1")
        tracker.record_success("item2")

        assert tracker.success_count == 2
        assert tracker.failure_count == 0

    def test_error_tracker_record_error(self):
        """Test recording errors"""
        tracker = ErrorTracker()

        tracker.record_error("item1", ValueError("Error 1"))
        tracker.record_error("item2", KeyError("Error 2"), {"context": "extra"})

        assert tracker.success_count == 0
        assert tracker.failure_count == 2
        assert len(tracker.errors) == 2

        # Check first error
        assert tracker.errors[0]["item_id"] == "item1"
        assert tracker.errors[0]["error_type"] == "ValueError"
        assert tracker.errors[0]["error_message"] == "Error 1"

        # Check second error with context
        assert tracker.errors[1]["item_id"] == "item2"
        assert tracker.errors[1]["context"]["context"] == "extra"

    def test_error_tracker_summary(self):
        """Test getting summary"""
        tracker = ErrorTracker()

        tracker.record_success("item1")
        tracker.record_success("item2")
        tracker.record_error("item3", ValueError("Error"))

        summary = tracker.get_summary()

        assert summary["total"] == 3
        assert summary["success"] == 2
        assert summary["failure"] == 1
        assert summary["error_rate"] == pytest.approx(1 / 3)
        assert len(summary["errors"]) == 1

    def test_error_tracker_has_errors(self):
        """Test has_errors method"""
        tracker = ErrorTracker()

        assert not tracker.has_errors()

        tracker.record_success("item1")
        assert not tracker.has_errors()

        tracker.record_error("item2", ValueError("Error"))
        assert tracker.has_errors()

    def test_error_tracker_raise_if_all_failed(self):
        """Test raise_if_all_failed method"""
        tracker = ErrorTracker()

        # No operations - should not raise
        tracker.raise_if_all_failed()

        # All successes - should not raise
        tracker.record_success("item1")
        tracker.raise_if_all_failed()

        # Mixed - should not raise
        tracker.record_error("item2", ValueError("Error"))
        tracker.raise_if_all_failed()

        # All failures - should raise
        tracker2 = ErrorTracker()
        tracker2.record_error("item1", ValueError("Error 1"))
        tracker2.record_error("item2", ValueError("Error 2"))

        with pytest.raises(Exception, match="All operations failed"):
            tracker2.raise_if_all_failed()


class TestCircuitBreaker:
    """Tests for CircuitBreaker"""

    @pytest.mark.asyncio
    async def test_circuit_breaker_success(self):
        """Test circuit breaker with successful calls"""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)

        async def succeeds():
            return "success"

        result = await breaker.call(succeeds)
        assert result == "success"
        assert breaker.state == "closed"

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self):
        """Test that circuit opens after threshold failures"""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)

        async def fails():
            raise ValueError("Failed")

        # First 3 failures should open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(fails)

        assert breaker.state == "open"

        # 4th call should fail immediately with circuit open
        with pytest.raises(Exception, match="Circuit breaker is open"):
            await breaker.call(fails)

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovers(self):
        """Test that circuit breaker recovers after timeout"""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.5)

        call_count = 0

        async def sometimes_fails():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ValueError("Failed")
            return "success"

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(sometimes_fails)

        assert breaker.state == "open"

        # Wait for recovery timeout
        await asyncio.sleep(0.6)

        # Should enter half-open and succeed
        result = await breaker.call(sometimes_fails)
        assert result == "success"
        assert breaker.state == "closed"
