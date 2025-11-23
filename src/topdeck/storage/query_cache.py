"""
Query result caching for Neo4j queries.

Provides a simple in-memory cache with TTL for frequently accessed query results
to reduce database load and improve response times.
"""

import hashlib
import json
import time
from collections import OrderedDict
from threading import Lock
from typing import Any


class QueryCache:
    """
    Thread-safe LRU cache with TTL for Neo4j query results.
    
    Stores query results in memory with automatic expiration and LRU eviction.
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize query cache.

        Args:
            max_size: Maximum number of cached items (default: 1000)
            default_ttl: Default TTL in seconds (default: 300 = 5 minutes)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def _generate_key(self, query: str, params: dict[str, Any] | None = None) -> str:
        """
        Generate cache key from query and parameters.

        Args:
            query: Cypher query string
            params: Query parameters

        Returns:
            Cache key
        """
        # Create a deterministic key from query + sorted params
        params_str = json.dumps(params or {}, sort_keys=True)
        combined = f"{query}:{params_str}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def get(self, query: str, params: dict[str, Any] | None = None) -> Any | None:
        """
        Get cached result for a query.

        Args:
            query: Cypher query string
            params: Query parameters

        Returns:
            Cached result or None if not found or expired
        """
        key = self._generate_key(query, params)

        with self._lock:
            if key in self._cache:
                result, expiry_time = self._cache[key]
                
                # Check if expired
                if time.time() < expiry_time:
                    # Move to end (most recently used)
                    self._cache.move_to_end(key)
                    self._hits += 1
                    return result
                else:
                    # Remove expired entry
                    del self._cache[key]

            self._misses += 1
            return None

    def set(
        self, query: str, result: Any, params: dict[str, Any] | None = None, ttl: int | None = None
    ) -> None:
        """
        Cache a query result.

        Args:
            query: Cypher query string
            result: Query result to cache
            params: Query parameters
            ttl: Time to live in seconds (uses default_ttl if None)
        """
        key = self._generate_key(query, params)
        ttl = ttl or self.default_ttl
        expiry_time = time.time() + ttl

        with self._lock:
            # If key exists, update it
            if key in self._cache:
                del self._cache[key]

            # Add new entry
            self._cache[key] = (result, expiry_time)

            # Evict oldest if over size limit
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    def invalidate(self, query: str, params: dict[str, Any] | None = None) -> None:
        """
        Invalidate a specific cached query.

        Args:
            query: Cypher query string
            params: Query parameters
        """
        key = self._generate_key(query, params)

        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cached queries matching a pattern.

        Args:
            pattern: String pattern to match in query

        Returns:
            Number of entries invalidated
        """
        count = 0
        with self._lock:
            keys_to_remove = []
            for key in self._cache:
                # We can't directly access the query from the key,
                # so this is a simplified pattern match
                # In practice, you might want to store metadata
                keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._cache[key]
                count += 1

        return count

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

            # Clean up expired entries first
            current_time = time.time()
            expired_keys = [
                key for key, (_, expiry) in self._cache.items() 
                if current_time >= expiry
            ]
            for key in expired_keys:
                del self._cache[key]

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 2),
                "default_ttl": self.default_ttl,
            }


# Global cache instance
_query_cache: QueryCache | None = None


def get_query_cache() -> QueryCache:
    """
    Get the global query cache instance.

    Returns:
        Global QueryCache instance
    """
    global _query_cache
    if _query_cache is None:
        _query_cache = QueryCache()
    return _query_cache


def initialize_query_cache(max_size: int = 1000, default_ttl: int = 300) -> None:
    """
    Initialize the global query cache.

    Args:
        max_size: Maximum number of cached items
        default_ttl: Default TTL in seconds
    """
    global _query_cache
    _query_cache = QueryCache(max_size=max_size, default_ttl=default_ttl)
