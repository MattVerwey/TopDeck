# Phase 3: Production Ready - Quick Start Guide

Get started with Phase 3 production-ready features in 5 minutes.

---

## Quick Install

```bash
# Install dependencies
pip install redis httpx structlog pytest pytest-asyncio

# Optional: Start Redis for caching
docker run -d -p 6379:6379 redis:latest
```

---

## Worker Pool - Parallel Execution

### Basic Usage

```python
from topdeck.common.worker_pool import parallel_map

async def process_item(item):
    # Your async processing logic
    return item * 2

# Process items in parallel (5 workers by default)
results = await parallel_map(process_item, [1, 2, 3, 4, 5])
# Returns: [2, 4, 6, 8, 10]
```

### Advanced Configuration

```python
from topdeck.common.worker_pool import WorkerPool, WorkerPoolConfig

# Configure worker pool
config = WorkerPoolConfig(
    max_workers=10,        # Concurrent workers
    timeout=30.0,          # Timeout per task (seconds)
    continue_on_error=True # Continue on partial failures
)

pool = WorkerPool(config)

# Execute tasks
results = await pool.map(process_item, items)

# Get execution summary
summary = pool.get_summary()
print(f"Success: {summary['success']}, Failed: {summary['failure']}")
```

### Performance Example

```python
# Sequential (slow)
results = []
for item in items:  # 10 items × 0.5s = 5s
    result = await process_item(item)
    results.append(result)

# Parallel (fast)
results = await parallel_map(process_item, items, max_workers=5)
# 10 items / 5 workers × 0.5s = 1s
# Speedup: 5x faster! ⚡
```

---

## Redis Cache - Distributed Caching

### Basic Usage

```python
from topdeck.common.cache import Cache, CacheConfig

# Initialize cache
cache = Cache(CacheConfig(
    host="localhost",
    port=6379,
    default_ttl=300,  # 5 minutes
))

await cache.connect()

# Set value
await cache.set("user:123", {"name": "Alice", "role": "admin"})

# Get value
user = await cache.get("user:123")
print(user)  # {'name': 'Alice', 'role': 'admin'}

# Delete
await cache.delete("user:123")

# Cleanup
await cache.close()
```

### Decorator Usage

```python
from topdeck.common.cache import cached

class DataService:
    def __init__(self):
        self._cache = cache  # Use shared cache instance
    
    @cached(ttl=300, key_prefix="data")
    async def get_data(self, id: str):
        # This expensive operation is cached
        # First call: executes function
        # Subsequent calls: returns cached result
        data = await expensive_database_query(id)
        return data

# Usage
service = DataService()
data = await service.get_data("123")  # Slow: 2s
data = await service.get_data("123")  # Fast: 2ms ⚡
# Speedup: 1000x faster!
```

### Pattern Operations

```python
# Set multiple values
await cache.set("resource:vm-1", {"type": "vm", "size": "large"})
await cache.set("resource:vm-2", {"type": "vm", "size": "small"})
await cache.set("resource:db-1", {"type": "db", "size": "xlarge"})

# Clear pattern
deleted = await cache.clear_pattern("resource:vm-*")
print(f"Deleted {deleted} keys")  # Deleted 2 keys

# Get statistics
stats = await cache.get_stats()
print(stats)
# {'enabled': True, 'hits': 100, 'misses': 20, 'keys': 50}
```

---

## Parallel Discovery - Azure Resources

### Enable Parallel Discovery

```python
from topdeck.discovery.azure.discoverer import AzureDiscoverer

# Create discoverer with parallel support
discoverer = AzureDiscoverer(
    subscription_id="your-subscription-id",
    enable_parallel=True,   # Enable parallel discovery
    max_workers=5,          # Concurrent workers
)

# Use parallel discovery (3-4x faster!)
result = await discoverer.discover_specialized_resources_parallel()

print(f"Discovered {len(result.resources)} resources")
# Sequential: ~15s
# Parallel: ~5s
# Speedup: 3x faster! ⚡
```

### With Caching

```python
from topdeck.common.cache import CacheConfig

# Enable both parallel + caching
discoverer = AzureDiscoverer(
    subscription_id="your-subscription-id",
    enable_parallel=True,
    max_workers=5,
    enable_cache=True,      # Enable caching
    cache_config=CacheConfig(host="localhost"),
)

# Connect to cache
await discoverer.connect_cache()

# First discovery (slow but cached)
result = await discoverer.discover_specialized_resources_parallel()
# Takes: ~5s

# Second discovery (cached, super fast!)
result = await discoverer.discover_specialized_resources_parallel()
# Takes: ~50ms
# Speedup: 100x faster! ⚡

# Cleanup
await discoverer.close()
```

---

## Complete Example

```python
import asyncio
from topdeck.discovery.azure.discoverer import AzureDiscoverer
from topdeck.common.cache import Cache, CacheConfig
from topdeck.common.worker_pool import parallel_map

async def main():
    # 1. Setup cache
    cache = Cache(CacheConfig(host="localhost"))
    await cache.connect()
    
    # 2. Setup discoverer with parallel + cache
    discoverer = AzureDiscoverer(
        subscription_id="your-sub-id",
        enable_parallel=True,
        max_workers=5,
        enable_cache=True,
        cache_config=CacheConfig(host="localhost"),
    )
    await discoverer.connect_cache()
    
    # 3. Discover resources (parallel + cached)
    result = await discoverer.discover_specialized_resources_parallel()
    
    print(f"✅ Discovered {len(result.resources)} resources")
    print(f"   Applications: {len(result.applications)}")
    print(f"   Dependencies: {len(result.dependencies)}")
    
    # 4. Process resources in parallel
    async def enrich_resource(resource):
        # Your enrichment logic
        return resource
    
    enriched = await parallel_map(
        enrich_resource,
        result.resources,
        max_workers=10
    )
    
    print(f"✅ Enriched {len(enriched)} resources")
    
    # 5. Cleanup
    await discoverer.close()
    await cache.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Run the Demo

```bash
# Run comprehensive demo
python examples/phase3_parallel_cache_demo.py

# Expected output:
# WORKER POOL DEMONSTRATION
# ✓ Processed 10 items in 2.00s
# Sequential would take: ~5.0s
# Speedup: 2.5x
#
# PARALLEL RESOURCE DISCOVERY SIMULATION
# Sequential discovery: 7.01s
# Parallel discovery: 2.50s
# Speedup: 2.8x faster
```

---

## Performance Tips

### 1. Choose Right Number of Workers

```python
# Too few: underutilized
max_workers=2  # Only 2x speedup

# Good: optimal for most cases
max_workers=5  # 3-5x speedup

# Too many: overhead increases
max_workers=50  # Diminishing returns
```

### 2. Set Appropriate Timeouts

```python
# Short timeout for quick operations
WorkerPoolConfig(timeout=5.0)

# Longer timeout for API calls
WorkerPoolConfig(timeout=30.0)
```

### 3. Use Caching Strategically

```python
# Cache expensive queries
@cached(ttl=300)  # 5 minutes
async def expensive_query():
    pass

# Short TTL for frequently changing data
@cached(ttl=60)  # 1 minute
async def dynamic_data():
    pass

# Long TTL for static data
@cached(ttl=3600)  # 1 hour
async def static_data():
    pass
```

### 4. Monitor Performance

```python
# Get worker pool summary
summary = pool.get_summary()
if summary['error_rate'] > 0.1:  # > 10% errors
    print(f"⚠️  High error rate: {summary['error_rate']:.2%}")

# Get cache statistics
stats = await cache.get_stats()
hit_rate = stats['hits'] / (stats['hits'] + stats['misses'])
if hit_rate < 0.5:  # < 50% hit rate
    print(f"⚠️  Low cache hit rate: {hit_rate:.2%}")
```

---

## Troubleshooting

### Worker Pool Issues

**Q: Tasks are timing out**
```python
# Increase timeout
config = WorkerPoolConfig(timeout=60.0)  # 1 minute
```

**Q: Too many errors**
```python
# Check error details
summary = pool.get_summary()
for error in summary['errors']:
    print(error)
```

### Cache Issues

**Q: Cache not working**
```python
# Check if Redis is running
docker ps | grep redis

# Check connection
try:
    await cache.connect()
    print("✅ Connected to Redis")
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
```

**Q: Cache returning stale data**
```python
# Clear specific pattern
await cache.clear_pattern("stale:*")

# Or reduce TTL
await cache.set("key", value, ttl=60)  # 1 minute
```

---

## Next Steps

1. **Try the Demo**
   ```bash
   python examples/phase3_parallel_cache_demo.py
   ```

2. **Read Full Documentation**
   - [PHASE_2_3_IMPLEMENTATION.md](docs/PHASE_2_3_IMPLEMENTATION.md)
   - [PHASE_3_COMPLETION_SUMMARY.md](PHASE_3_COMPLETION_SUMMARY.md)

3. **Run Tests**
   ```bash
   pytest tests/common/test_worker_pool.py -v
   pytest tests/common/test_cache.py -v
   ```

4. **Integrate into Your Code**
   - Start with `parallel_map` for simple cases
   - Add caching for expensive operations
   - Enable parallel discovery for Azure resources

---

## Support

- **Documentation**: See [docs/](docs/)
- **Examples**: See [examples/](examples/)
- **Issues**: See [GitHub Issues](https://github.com/MattVerwey/TopDeck/issues)
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Happy coding! 🚀**
