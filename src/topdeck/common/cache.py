"""
Caching layer with Redis backend.

Provides distributed caching for resource discovery results,
API responses, and other frequently accessed data.
"""

import json
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

try:
    import redis.asyncio as aioredis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None

logger = logging.getLogger(__name__)


class CacheConfig:
    """Configuration for cache."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        default_ttl: int = 3600,  # 1 hour
        key_prefix: str = "topdeck:",
        ssl: bool = False,
        ssl_cert_reqs: str = "required",
    ):
        """
        Initialize cache configuration.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Optional Redis password
            default_ttl: Default TTL in seconds
            key_prefix: Prefix for all cache keys
            ssl: Enable SSL/TLS encryption for Redis connection
            ssl_cert_reqs: SSL certificate requirements ('none', 'optional', 'required')
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self.ssl = ssl
        self.ssl_cert_reqs = ssl_cert_reqs


class Cache:
    """
    Distributed cache using Redis.

    Provides get/set operations with TTL support and JSON serialization.
    """

    def __init__(self, config: CacheConfig | None = None):
        """
        Initialize cache.

        Args:
            config: Cache configuration (uses defaults if None)
        """
        self.config = config or CacheConfig()
        self._client: Any | None = None
        self._enabled = REDIS_AVAILABLE

        if not REDIS_AVAILABLE:
            logger.warning(
                "Redis client not available. Cache operations will be no-ops. "
                "Install redis package to enable caching."
            )

    async def connect(self) -> None:
        """Connect to Redis server with optional SSL/TLS encryption."""
        if not self._enabled:
            return

        try:
            connection_params = {
                "host": self.config.host,
                "port": self.config.port,
                "db": self.config.db,
                "password": self.config.password,
                "decode_responses": True,
            }

            # Add SSL parameters if encryption is enabled
            if self.config.ssl:
                import ssl
                if self.config.ssl_cert_reqs == "none":
                    connection_params["ssl_cert_reqs"] = ssl.CERT_NONE
                elif self.config.ssl_cert_reqs == "optional":
                    connection_params["ssl_cert_reqs"] = ssl.CERT_OPTIONAL
                elif self.config.ssl_cert_reqs == "required":
                    connection_params["ssl_cert_reqs"] = ssl.CERT_REQUIRED

                logger.info(
                    f"Connecting to Redis with SSL/TLS encryption at {self.config.host}:{self.config.port}"
                )

            self._client = aioredis.Redis(**connection_params)
            # Test connection
            await self._client.ping()
            logger.info(f"Connected to Redis at {self.config.host}:{self.config.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._enabled = False

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            logger.info("Closed Redis connection")

    def _make_key(self, key: str) -> str:
        """Create full cache key with prefix."""
        return f"{self.config.key_prefix}{key}"

    async def get(self, key: str) -> Any | None:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self._enabled or not self._client:
            return None

        try:
            full_key = self._make_key(key)
            value = await self._client.get(full_key)

            if value is not None:
                logger.debug(f"Cache hit: {key}")
                return json.loads(value)

            logger.debug(f"Cache miss: {key}")
            return None

        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds (uses default if None)

        Returns:
            True if successful, False otherwise
        """
        if not self._enabled or not self._client:
            return False

        try:
            full_key = self._make_key(key)
            ttl = ttl or self.config.default_ttl

            serialized = json.dumps(value)
            await self._client.setex(full_key, ttl, serialized)

            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False otherwise
        """
        if not self._enabled or not self._client:
            return False

        try:
            full_key = self._make_key(key)
            result = await self._client.delete(full_key)

            logger.debug(f"Cache delete: {key}")
            return result > 0

        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        if not self._enabled or not self._client:
            return False

        try:
            full_key = self._make_key(key)
            result = await self._client.exists(full_key)
            return result > 0

        except Exception as e:
            logger.error(f"Error checking cache existence: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern.

        Args:
            pattern: Key pattern (e.g., "resources:*")

        Returns:
            Number of keys deleted
        """
        if not self._enabled or not self._client:
            return 0

        try:
            full_pattern = self._make_key(pattern)
            keys = await self._client.keys(full_pattern)

            if keys:
                deleted = await self._client.delete(*keys)
                logger.info(f"Cleared {deleted} keys matching pattern: {pattern}")
                return deleted

            return 0

        except Exception as e:
            logger.error(f"Error clearing cache pattern: {e}")
            return 0

    async def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        if not self._enabled or not self._client:
            return {"enabled": False}

        try:
            info = await self._client.info("stats")
            return {
                "enabled": True,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "keys": await self._client.dbsize(),
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"enabled": True, "error": str(e)}


def cached(
    ttl: int | None = None,
    key_prefix: str | None = None,
):
    """
    Decorator for caching async function results.

    Args:
        ttl: Time to live in seconds (uses cache default if None)
        key_prefix: Optional prefix for cache key

    Example:
        >>> cache = Cache()
        >>> await cache.connect()
        >>>
        >>> @cached(ttl=300, key_prefix="discover")
        >>> async def discover_resources(subscription_id: str):
        ...     # Expensive operation
        ...     return resources
        >>>
        >>> # First call: executes function and caches result
        >>> result = await discover_resources("sub-123")
        >>>
        >>> # Second call: returns cached result
        >>> result = await discover_resources("sub-123")
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args, **kwargs) -> Any:
            # Get cache instance from self if available
            cache_instance = getattr(self, "_cache", None)

            if not cache_instance or not cache_instance._enabled:
                # No cache available, execute function directly
                return await func(self, *args, **kwargs)

            # Build cache key from function name and arguments
            func_name = func.__name__

            # Simple key generation (can be improved)
            key_parts = [key_prefix or func_name]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_result = await cache_instance.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Returning cached result for {func_name}")
                return cached_result

            # Execute function and cache result
            result = await func(self, *args, **kwargs)
            await cache_instance.set(cache_key, result, ttl=ttl)

            return result

        return wrapper

    return decorator
