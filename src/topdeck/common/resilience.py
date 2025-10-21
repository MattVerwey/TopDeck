"""
Resilience utilities for error handling, retry logic, and rate limiting.

Provides decorators and utilities for making API calls more resilient.
"""

import asyncio
import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for API calls.

    Ensures API calls don't exceed rate limits.
    """

    def __init__(self, max_calls: int, time_window: float):
        """
        Initialize rate limiter.

        Args:
            max_calls: Maximum number of calls allowed in time window
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Wait until a call can be made without exceeding rate limit."""
        async with self._lock:
            now = time.time()

            # Remove calls outside the time window
            self.calls = [
                call_time for call_time in self.calls if now - call_time < self.time_window
            ]

            # If at max capacity, wait
            if len(self.calls) >= self.max_calls:
                oldest_call = self.calls[0]
                wait_time = self.time_window - (now - oldest_call)
                if wait_time > 0:
                    logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                    # Re-check after waiting
                    now = time.time()
                    self.calls = [
                        call_time for call_time in self.calls if now - call_time < self.time_window
                    ]

            # Record this call
            self.calls.append(now)


class RetryConfig:
    """Configuration for retry logic."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        """
        Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter to delays
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


def retry_with_backoff(
    config: RetryConfig | None = None,
    exceptions: tuple[type[Exception], ...] = (Exception,),
):
    """
    Decorator to retry async functions with exponential backoff.

    Args:
        config: Retry configuration (uses defaults if None)
        exceptions: Tuple of exception types to retry on

    Returns:
        Decorated function
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == config.max_attempts - 1:
                        # Last attempt, raise the exception
                        logger.error(
                            f"Function {func.__name__} failed after {config.max_attempts} attempts: {e}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(
                        config.initial_delay * (config.exponential_base**attempt),
                        config.max_delay,
                    )

                    # Add jitter if enabled
                    if config.jitter:
                        import random

                        delay = delay * (0.5 + random.random())

                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{config.max_attempts}), "
                        f"retrying in {delay:.2f}s: {e}"
                    )

                    await asyncio.sleep(delay)

            # Should not reach here, but just in case
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


async def with_rate_limit(rate_limiter: RateLimiter, func: Callable, *args, **kwargs) -> Any:
    """
    Execute a function with rate limiting.

    Args:
        rate_limiter: RateLimiter instance
        func: Function to execute
        *args: Positional arguments for function
        **kwargs: Keyword arguments for function

    Returns:
        Result of function call
    """
    await rate_limiter.acquire()
    if asyncio.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    else:
        return func(*args, **kwargs)


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Prevents repeated calls to a failing service by "opening" the circuit
    after a threshold of failures.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type[Exception] = Exception,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time in seconds before attempting to close circuit
            expected_exception: Exception type to count as failure
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = "closed"  # closed, open, half_open
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call function through circuit breaker.

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result of function call

        Raises:
            Exception: If circuit is open or function fails
        """
        async with self._lock:
            # Check if circuit should be half-open
            if self.state == "open":
                if (
                    self.last_failure_time
                    and time.time() - self.last_failure_time >= self.recovery_timeout
                ):
                    self.state = "half_open"
                    logger.info("Circuit breaker entering half-open state")
                else:
                    raise Exception("Circuit breaker is open")

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Success - reset failure count and close circuit
            async with self._lock:
                if self.state == "half_open":
                    logger.info("Circuit breaker closing after successful call")
                self.failure_count = 0
                self.state = "closed"

            return result

        except self.expected_exception:
            async with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.state = "open"
                    logger.error(f"Circuit breaker opened after {self.failure_count} failures")

            raise


class ErrorTracker:
    """
    Track errors during batch operations.

    Allows operations to continue despite partial failures.
    """

    def __init__(self):
        """Initialize error tracker."""
        self.errors: list[dict[str, Any]] = []
        self.success_count = 0
        self.failure_count = 0

    def record_success(self, item_id: str):
        """Record a successful operation."""
        self.success_count += 1

    def record_error(self, item_id: str, error: Exception, context: dict | None = None):
        """
        Record an error.

        Args:
            item_id: Identifier for the item that failed
            error: Exception that occurred
            context: Optional context information
        """
        self.failure_count += 1
        error_record = {
            "item_id": item_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
        }
        self.errors.append(error_record)
        logger.error(f"Error processing {item_id}: {error}")

    def get_summary(self) -> dict[str, Any]:
        """
        Get summary of tracked operations.

        Returns:
            Dictionary with summary statistics
        """
        return {
            "total": self.success_count + self.failure_count,
            "success": self.success_count,
            "failure": self.failure_count,
            "error_rate": self.failure_count / max(1, self.success_count + self.failure_count),
            "errors": self.errors,
        }

    def has_errors(self) -> bool:
        """Check if any errors were recorded."""
        return len(self.errors) > 0

    def raise_if_all_failed(self):
        """Raise exception if all operations failed."""
        if self.failure_count > 0 and self.success_count == 0:
            raise Exception(f"All operations failed: {len(self.errors)} errors")
