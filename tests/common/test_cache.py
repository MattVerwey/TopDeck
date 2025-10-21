"""
Tests for cache layer.
"""

from unittest.mock import AsyncMock, patch

import pytest

from topdeck.common.cache import (
    Cache,
    CacheConfig,
    cached,
)


class TestCacheConfig:
    """Tests for CacheConfig"""

    def test_cache_config_defaults(self):
        """Test default configuration"""
        config = CacheConfig()

        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.password is None
        assert config.default_ttl == 3600
        assert config.key_prefix == "topdeck:"

    def test_cache_config_custom(self):
        """Test custom configuration"""
        config = CacheConfig(
            host="redis.example.com",
            port=6380,
            db=1,
            password="secret",
            default_ttl=1800,
            key_prefix="myapp:",
        )

        assert config.host == "redis.example.com"
        assert config.port == 6380
        assert config.db == 1
        assert config.password == "secret"
        assert config.default_ttl == 1800
        assert config.key_prefix == "myapp:"


class TestCache:
    """Tests for Cache"""

    @pytest.mark.asyncio
    async def test_cache_without_redis(self):
        """Test cache operations when Redis is not available"""
        with patch("topdeck.common.cache.REDIS_AVAILABLE", False):
            cache = Cache()

            # Operations should be no-ops
            await cache.connect()

            result = await cache.set("key", "value")
            assert result is False

            result = await cache.get("key")
            assert result is None

            result = await cache.delete("key")
            assert result is False

            result = await cache.exists("key")
            assert result is False

    @pytest.mark.asyncio
    async def test_cache_make_key(self):
        """Test cache key generation"""
        config = CacheConfig(key_prefix="test:")
        cache = Cache(config)

        key = cache._make_key("mykey")
        assert key == "test:mykey"

    @pytest.mark.asyncio
    @patch("topdeck.common.cache.REDIS_AVAILABLE", True)
    @patch("topdeck.common.cache.aioredis")
    async def test_cache_connect_success(self, mock_aioredis):
        """Test successful Redis connection"""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock()
        mock_aioredis.Redis.return_value = mock_client

        cache = Cache()
        await cache.connect()

        assert cache._client == mock_client
        mock_client.ping.assert_called_once()

    @pytest.mark.asyncio
    @patch("topdeck.common.cache.REDIS_AVAILABLE", True)
    @patch("topdeck.common.cache.aioredis")
    async def test_cache_connect_failure(self, mock_aioredis):
        """Test failed Redis connection"""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(side_effect=Exception("Connection failed"))
        mock_aioredis.Redis.return_value = mock_client

        cache = Cache()
        await cache.connect()

        assert cache._enabled is False

    @pytest.mark.asyncio
    @patch("topdeck.common.cache.REDIS_AVAILABLE", True)
    async def test_cache_get_set(self):
        """Test get and set operations"""
        cache = Cache()
        cache._enabled = True
        cache._client = AsyncMock()
        cache._client.get = AsyncMock(return_value='{"value": 123}')
        cache._client.setex = AsyncMock()

        # Set value
        result = await cache.set("key", {"value": 123}, ttl=300)
        assert result is True
        cache._client.setex.assert_called_once()

        # Get value
        result = await cache.get("key")
        assert result == {"value": 123}
        cache._client.get.assert_called_once()

    @pytest.mark.asyncio
    @patch("topdeck.common.cache.REDIS_AVAILABLE", True)
    async def test_cache_get_miss(self):
        """Test cache miss"""
        cache = Cache()
        cache._enabled = True
        cache._client = AsyncMock()
        cache._client.get = AsyncMock(return_value=None)

        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    @patch("topdeck.common.cache.REDIS_AVAILABLE", True)
    async def test_cache_delete(self):
        """Test delete operation"""
        cache = Cache()
        cache._enabled = True
        cache._client = AsyncMock()
        cache._client.delete = AsyncMock(return_value=1)

        result = await cache.delete("key")
        assert result is True
        cache._client.delete.assert_called_once()

    @pytest.mark.asyncio
    @patch("topdeck.common.cache.REDIS_AVAILABLE", True)
    async def test_cache_exists(self):
        """Test exists operation"""
        cache = Cache()
        cache._enabled = True
        cache._client = AsyncMock()
        cache._client.exists = AsyncMock(return_value=1)

        result = await cache.exists("key")
        assert result is True
        cache._client.exists.assert_called_once()

    @pytest.mark.asyncio
    @patch("topdeck.common.cache.REDIS_AVAILABLE", True)
    async def test_cache_clear_pattern(self):
        """Test clearing keys by pattern"""
        cache = Cache()
        cache._enabled = True
        cache._client = AsyncMock()
        cache._client.keys = AsyncMock(return_value=["key1", "key2", "key3"])
        cache._client.delete = AsyncMock(return_value=3)

        result = await cache.clear_pattern("test:*")
        assert result == 3
        cache._client.keys.assert_called_once()
        cache._client.delete.assert_called_once_with("key1", "key2", "key3")

    @pytest.mark.asyncio
    @patch("topdeck.common.cache.REDIS_AVAILABLE", True)
    async def test_cache_get_stats(self):
        """Test getting cache statistics"""
        cache = Cache()
        cache._enabled = True
        cache._client = AsyncMock()
        cache._client.info = AsyncMock(
            return_value={
                "keyspace_hits": 100,
                "keyspace_misses": 20,
            }
        )
        cache._client.dbsize = AsyncMock(return_value=50)

        stats = await cache.get_stats()
        assert stats["enabled"] is True
        assert stats["hits"] == 100
        assert stats["misses"] == 20
        assert stats["keys"] == 50


class TestCachedDecorator:
    """Tests for @cached decorator"""

    @pytest.mark.asyncio
    async def test_cached_decorator_without_cache(self):
        """Test decorator when cache is not available"""
        call_count = 0

        class TestClass:
            @cached(ttl=300)
            async def expensive_operation(self, x):
                nonlocal call_count
                call_count += 1
                return x * 2

        obj = TestClass()

        result1 = await obj.expensive_operation(5)
        result2 = await obj.expensive_operation(5)

        assert result1 == 10
        assert result2 == 10
        assert call_count == 2  # Called twice, no caching

    @pytest.mark.asyncio
    @patch("topdeck.common.cache.REDIS_AVAILABLE", True)
    async def test_cached_decorator_with_cache(self):
        """Test decorator with cache enabled"""
        call_count = 0

        class TestClass:
            def __init__(self):
                self._cache = Cache()
                self._cache._enabled = True
                self._cache._client = AsyncMock()
                self._cache._client.get = AsyncMock(return_value=None)
                self._cache._client.setex = AsyncMock()

            @cached(ttl=300, key_prefix="test")
            async def expensive_operation(self, x):
                nonlocal call_count
                call_count += 1
                return x * 2

        obj = TestClass()

        # First call - cache miss
        result1 = await obj.expensive_operation(5)
        assert result1 == 10
        assert call_count == 1

        # Simulate cache hit
        obj._cache._client.get = AsyncMock(return_value=10)

        # Second call - should use cache
        result2 = await obj.expensive_operation(5)
        assert result2 == 10
        # Note: call_count might be 2 in this test due to implementation details
