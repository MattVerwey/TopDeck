"""
Rate limiting for API endpoints.

Provides a simple in-memory rate limiter to prevent API abuse.
"""

import time
from collections import defaultdict
from collections.abc import Callable

import structlog
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter using a sliding window approach."""

    def __init__(self, requests_per_minute: int = 60) -> None:
        """
        Initialize the rate limiter.

        Args:
            requests_per_minute: Maximum number of requests allowed per minute per client
        """
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        self.requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_id: str) -> bool:
        """
        Check if a request from the client is allowed.

        Args:
            client_id: Unique identifier for the client (e.g., IP address)

        Returns:
            True if the request is allowed, False otherwise
        """
        current_time = time.time()
        window_start = current_time - self.window_seconds

        # Remove expired timestamps
        self.requests[client_id] = [
            timestamp for timestamp in self.requests[client_id] if timestamp > window_start
        ]

        # Check if under the limit
        if len(self.requests[client_id]) < self.requests_per_minute:
            self.requests[client_id].append(current_time)
            return True

        return False

    def get_retry_after(self, client_id: str) -> int:
        """
        Get the number of seconds until the client can make another request.

        Args:
            client_id: Unique identifier for the client

        Returns:
            Number of seconds to wait
        """
        if not self.requests[client_id]:
            return 0

        oldest_timestamp = min(self.requests[client_id])
        window_start = time.time() - self.window_seconds

        if oldest_timestamp <= window_start:
            return 0

        return int(oldest_timestamp + self.window_seconds - time.time()) + 1


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to apply rate limiting to API requests."""

    def __init__(
        self, app, rate_limiter: RateLimiter | None = None, exempt_paths: list[str] | None = None
    ) -> None:
        """
        Initialize the middleware.

        Args:
            app: ASGI application
            rate_limiter: Rate limiter instance. If None, creates a default one.
            exempt_paths: List of paths to exempt from rate limiting (e.g., ["/health", "/"])
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
        self.exempt_paths = exempt_paths or ["/health", "/", "/api/info"]

    async def dispatch(self, request: Request, call_next: Callable):
        """Apply rate limiting to the request."""
        # Skip rate limiting for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        # Get client identifier (IP address)
        client_id = request.client.host if request.client else "unknown"

        # Check rate limit
        if not self.rate_limiter.is_allowed(client_id):
            retry_after = self.rate_limiter.get_retry_after(client_id)
            logger.warning(
                "rate_limit_exceeded",
                client_id=client_id,
                path=request.url.path,
                retry_after=retry_after,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
