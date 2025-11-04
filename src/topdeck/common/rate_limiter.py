"""
Rate limiting for API endpoints.

Provides both in-memory and Redis-based distributed rate limiting to prevent API abuse.
Uses token bucket algorithm for better burst handling.
"""

import time
from collections import defaultdict
from collections.abc import Callable
from typing import Optional

import structlog
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None


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


class RedisRateLimiter:
    """
    Distributed rate limiter using Redis with token bucket algorithm.
    
    Provides better burst handling and works across multiple API instances.
    """

    def __init__(
        self,
        redis_client: Optional["aioredis.Redis"] = None,
        requests_per_minute: int = 60,
        burst_size: Optional[int] = None,
        key_prefix: str = "topdeck:ratelimit:",
    ) -> None:
        """
        Initialize the Redis rate limiter.

        Args:
            redis_client: Redis async client instance
            requests_per_minute: Token refill rate (tokens per minute)
            burst_size: Maximum tokens in bucket (allows bursts). Defaults to 2x requests_per_minute
            key_prefix: Redis key prefix for rate limit data
        """
        self.redis_client = redis_client
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size or (requests_per_minute * 2)
        self.key_prefix = key_prefix
        self.refill_rate = requests_per_minute / 60.0  # tokens per second
        self._enabled = redis_client is not None and REDIS_AVAILABLE

        if not self._enabled:
            logger.warning(
                "Redis rate limiter disabled - Redis client not available. "
                "Falling back to in-memory rate limiting."
            )

    def _make_key(self, client_id: str, scope: str = "global") -> str:
        """Create Redis key for rate limit data."""
        return f"{self.key_prefix}{scope}:{client_id}"

    async def is_allowed(self, client_id: str, scope: str = "global", cost: int = 1) -> bool:
        """
        Check if a request from the client is allowed using token bucket algorithm.

        Args:
            client_id: Unique identifier for the client (e.g., IP address)
            scope: Rate limit scope (e.g., "global", "topology", "risk")
            cost: Number of tokens to consume (default: 1)

        Returns:
            True if the request is allowed, False otherwise
        """
        if not self._enabled:
            return True

        try:
            key = self._make_key(client_id, scope)
            current_time = time.time()

            # Use Lua script for atomic token bucket operation
            lua_script = """
            local key = KEYS[1]
            local now = tonumber(ARGV[1])
            local refill_rate = tonumber(ARGV[2])
            local burst_size = tonumber(ARGV[3])
            local cost = tonumber(ARGV[4])
            local ttl = tonumber(ARGV[5])
            
            -- Get current bucket state
            local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
            local tokens = tonumber(bucket[1]) or burst_size
            local last_refill = tonumber(bucket[2]) or now
            
            -- Calculate tokens to add based on time elapsed
            local time_elapsed = now - last_refill
            local tokens_to_add = time_elapsed * refill_rate
            tokens = math.min(burst_size, tokens + tokens_to_add)
            
            -- Check if we have enough tokens
            if tokens >= cost then
                tokens = tokens - cost
                redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
                redis.call('EXPIRE', key, ttl)
                return 1
            else
                redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
                redis.call('EXPIRE', key, ttl)
                return 0
            end
            """

            result = await self.redis_client.eval(
                lua_script,
                1,  # number of keys
                key,
                current_time,
                self.refill_rate,
                self.burst_size,
                cost,
                120,  # TTL in seconds
            )

            return bool(result)

        except Exception as e:
            logger.error("redis_rate_limit_error", error=str(e), client_id=client_id)
            # Fail open - allow request if Redis is unavailable
            return True

    async def get_retry_after(self, client_id: str, scope: str = "global") -> int:
        """
        Get the number of seconds until the client can make another request.

        Args:
            client_id: Unique identifier for the client
            scope: Rate limit scope

        Returns:
            Number of seconds to wait
        """
        if not self._enabled:
            return 0

        try:
            key = self._make_key(client_id, scope)
            current_time = time.time()

            # Get current bucket state
            bucket = await self.redis_client.hmget(key, "tokens", "last_refill")
            tokens = float(bucket[0]) if bucket[0] else self.burst_size
            last_refill = float(bucket[1]) if bucket[1] else current_time

            # Calculate tokens after refill
            time_elapsed = current_time - last_refill
            tokens_to_add = time_elapsed * self.refill_rate
            tokens = min(self.burst_size, tokens + tokens_to_add)

            # If we have tokens, no wait needed
            if tokens >= 1:
                return 0

            # Calculate time needed to accumulate 1 token
            tokens_needed = 1 - tokens
            seconds_to_wait = tokens_needed / self.refill_rate
            return int(seconds_to_wait) + 1

        except Exception as e:
            logger.error("redis_retry_after_error", error=str(e), client_id=client_id)
            return 0

    async def get_remaining(self, client_id: str, scope: str = "global") -> int:
        """
        Get the number of remaining requests for the client.

        Args:
            client_id: Unique identifier for the client
            scope: Rate limit scope

        Returns:
            Number of remaining tokens/requests
        """
        if not self._enabled:
            return self.burst_size

        try:
            key = self._make_key(client_id, scope)
            current_time = time.time()

            bucket = await self.redis_client.hmget(key, "tokens", "last_refill")
            tokens = float(bucket[0]) if bucket[0] else self.burst_size
            last_refill = float(bucket[1]) if bucket[1] else current_time

            # Calculate current tokens after refill
            time_elapsed = current_time - last_refill
            tokens_to_add = time_elapsed * self.refill_rate
            tokens = min(self.burst_size, tokens + tokens_to_add)

            return int(tokens)

        except Exception as e:
            logger.error("redis_remaining_error", error=str(e), client_id=client_id)
            return self.burst_size


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to apply rate limiting to API requests.
    
    Supports both in-memory and Redis-based rate limiting with proper rate limit headers.
    """

    def __init__(
        self,
        app,
        rate_limiter: RateLimiter | RedisRateLimiter | None = None,
        exempt_paths: list[str] | None = None,
        scope_mapping: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Initialize the middleware.

        Args:
            app: ASGI application
            rate_limiter: Rate limiter instance (RateLimiter or RedisRateLimiter). 
                         If None, creates a default in-memory limiter.
            exempt_paths: List of paths to exempt from rate limiting (e.g., ["/health", "/"])
            scope_mapping: Optional mapping of path patterns to rate limit scopes
                          e.g., {"/api/v1/topology": "topology", "/api/v1/risk": "risk"}
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
        self.exempt_paths = exempt_paths or ["/health", "/", "/api/info"]
        self.scope_mapping = scope_mapping or {}
        self.is_redis_limiter = isinstance(rate_limiter, RedisRateLimiter)

    def _get_scope(self, path: str) -> str:
        """Determine rate limit scope based on request path."""
        for pattern, scope in self.scope_mapping.items():
            if path.startswith(pattern):
                return scope
        return "global"

    async def dispatch(self, request: Request, call_next: Callable):
        """Apply rate limiting to the request with proper headers."""
        # Skip rate limiting for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        # Get client identifier (IP address)
        client_id = request.client.host if request.client else "unknown"
        scope = self._get_scope(request.url.path)

        # Check rate limit based on limiter type
        if self.is_redis_limiter:
            is_allowed = await self.rate_limiter.is_allowed(client_id, scope=scope)
            retry_after = await self.rate_limiter.get_retry_after(client_id, scope=scope)
            remaining = await self.rate_limiter.get_remaining(client_id, scope=scope)
            limit = self.rate_limiter.burst_size
        else:
            # In-memory limiter (synchronous)
            is_allowed = self.rate_limiter.is_allowed(client_id)
            retry_after = self.rate_limiter.get_retry_after(client_id)
            remaining = self.rate_limiter.requests_per_minute - len(
                [ts for ts in self.rate_limiter.requests.get(client_id, []) 
                 if ts > time.time() - self.rate_limiter.window_seconds]
            )
            limit = self.rate_limiter.requests_per_minute

        if not is_allowed:
            logger.warning(
                "rate_limit_exceeded",
                client_id=client_id,
                path=request.url.path,
                scope=scope,
                retry_after=retry_after,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + retry_after)),
                },
            )

        # Process request and add rate limit headers to response
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
        
        return response
