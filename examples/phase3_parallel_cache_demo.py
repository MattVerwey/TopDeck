"""
Demonstration of Phase 3 Production Ready features:
- Parallel discovery with worker pools
- Redis caching layer
- Performance optimizations

This example shows how to use the new parallel discovery and caching
features to significantly improve performance.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from topdeck.common.worker_pool import WorkerPool, WorkerPoolConfig, parallel_map
from topdeck.common.cache import Cache, CacheConfig
from topdeck.common.logging_config import setup_logging, get_logger

# Setup logging
setup_logging(level="INFO")
logger = get_logger(__name__)


async def demo_worker_pool():
    """Demonstrate parallel task execution with worker pool."""
    print("\n" + "=" * 70)
    print("WORKER POOL DEMONSTRATION")
    print("=" * 70)
    
    print("\nProcessing 10 items with max 3 concurrent workers...")
    
    async def process_item(item_id: int) -> dict:
        """Simulate resource discovery for an item."""
        await asyncio.sleep(0.5)  # Simulate API call
        return {
            "id": item_id,
            "status": "discovered",
            "timestamp": datetime.now().isoformat(),
        }
    
    # Method 1: Using WorkerPool directly
    print("\nMethod 1: Using WorkerPool directly")
    config = WorkerPoolConfig(max_workers=3)
    pool = WorkerPool(config)
    
    items = list(range(10))
    start_time = datetime.now()
    
    results = await pool.map(process_item, items)
    
    duration = (datetime.now() - start_time).total_seconds()
    
    print(f"✓ Processed {len(results)} items in {duration:.2f}s")
    print(f"  Average: {duration/len(results):.2f}s per item")
    print(f"  Sequential would take: ~{len(results) * 0.5:.1f}s")
    print(f"  Speedup: {(len(results) * 0.5) / duration:.1f}x")
    
    # Get execution summary
    summary = pool.get_summary()
    print(f"\nExecution Summary:")
    print(f"  Total: {summary['total']}")
    print(f"  Success: {summary['success']}")
    print(f"  Failed: {summary['failure']}")
    print(f"  Error Rate: {summary['error_rate']:.2%}")
    
    # Method 2: Using parallel_map convenience function
    print("\n\nMethod 2: Using parallel_map convenience function")
    
    start_time = datetime.now()
    results = await parallel_map(process_item, items, max_workers=3)
    duration = (datetime.now() - start_time).total_seconds()
    
    print(f"✓ Processed {len(results)} items in {duration:.2f}s")


async def demo_worker_pool_error_handling():
    """Demonstrate error handling in worker pool."""
    print("\n" + "=" * 70)
    print("WORKER POOL ERROR HANDLING")
    print("=" * 70)
    
    print("\nProcessing items where some will fail...")
    
    async def process_with_errors(item_id: int) -> dict:
        """Simulate processing where some items fail."""
        await asyncio.sleep(0.1)
        
        if item_id % 3 == 0:
            raise ValueError(f"Item {item_id} processing failed")
        
        return {"id": item_id, "status": "success"}
    
    config = WorkerPoolConfig(max_workers=5, continue_on_error=True)
    pool = WorkerPool(config)
    
    items = list(range(10))
    results = await pool.map(process_with_errors, items)
    
    print(f"\n✓ Completed with partial failures")
    print(f"  Successful: {len(results)} items")
    print(f"  Expected failures: {len([i for i in items if i % 3 == 0])}")
    
    summary = pool.get_summary()
    print(f"\nExecution Summary:")
    print(f"  Total: {summary['total']}")
    print(f"  Success: {summary['success']}")
    print(f"  Failed: {summary['failure']}")
    print(f"  Error Rate: {summary['error_rate']:.2%}")


async def demo_cache_operations():
    """Demonstrate caching operations."""
    print("\n" + "=" * 70)
    print("CACHE OPERATIONS DEMONSTRATION")
    print("=" * 70)
    
    # Initialize cache
    config = CacheConfig(
        host="localhost",
        port=6379,
        default_ttl=300,  # 5 minutes
        key_prefix="demo:",
    )
    cache = Cache(config)
    
    # Try to connect (will gracefully degrade if Redis not available)
    await cache.connect()
    
    if not cache._enabled:
        print("\n⚠️  Redis not available, cache operations will be no-ops")
        print("   Install and run Redis to see caching in action:")
        print("   $ docker run -d -p 6379:6379 redis:latest")
        return
    
    print("\n✓ Connected to Redis")
    
    # Basic operations
    print("\nBasic cache operations:")
    
    # Set values
    await cache.set("user:123", {"name": "Alice", "role": "admin"})
    await cache.set("user:456", {"name": "Bob", "role": "user"}, ttl=60)
    print("  ✓ Set user:123 and user:456")
    
    # Get values
    user = await cache.get("user:123")
    print(f"  ✓ Retrieved user:123: {user}")
    
    # Check existence
    exists = await cache.exists("user:123")
    print(f"  ✓ user:123 exists: {exists}")
    
    # Simulate caching expensive operation
    print("\nCaching expensive operation:")
    
    async def expensive_query(query_id: str):
        """Simulate expensive database query."""
        logger.info(f"Executing expensive query: {query_id}")
        await asyncio.sleep(1.0)
        return {"query_id": query_id, "results": [1, 2, 3, 4, 5]}
    
    query_id = "complex_query_1"
    cache_key = f"query:{query_id}"
    
    # First call - cache miss
    print(f"  First call (cache miss)...")
    start_time = datetime.now()
    cached_result = await cache.get(cache_key)
    
    if cached_result is None:
        result = await expensive_query(query_id)
        await cache.set(cache_key, result, ttl=300)
        print(f"    Executed query and cached result")
    else:
        result = cached_result
        print(f"    Used cached result")
    
    duration1 = (datetime.now() - start_time).total_seconds()
    print(f"    Duration: {duration1:.2f}s")
    
    # Second call - cache hit
    print(f"\n  Second call (cache hit)...")
    start_time = datetime.now()
    cached_result = await cache.get(cache_key)
    
    if cached_result is None:
        result = await expensive_query(query_id)
        await cache.set(cache_key, result, ttl=300)
    else:
        result = cached_result
        print(f"    Used cached result")
    
    duration2 = (datetime.now() - start_time).total_seconds()
    print(f"    Duration: {duration2:.2f}s")
    print(f"    Speedup: {duration1/duration2:.1f}x faster")
    
    # Get cache stats
    print("\nCache statistics:")
    stats = await cache.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Cleanup
    await cache.delete(cache_key)
    await cache.clear_pattern("user:*")
    await cache.close()
    print("\n✓ Cache cleaned up and closed")


async def demo_parallel_discovery_simulation():
    """Simulate parallel resource discovery."""
    print("\n" + "=" * 70)
    print("PARALLEL RESOURCE DISCOVERY SIMULATION")
    print("=" * 70)
    
    print("\nSimulating discovery of 4 resource types in parallel...")
    
    async def discover_compute_resources():
        """Simulate compute resource discovery."""
        logger.info("Discovering compute resources...")
        await asyncio.sleep(2.0)  # Simulate API calls
        return ["vm-1", "vm-2", "aks-1", "app-service-1"]
    
    async def discover_networking_resources():
        """Simulate networking resource discovery."""
        logger.info("Discovering networking resources...")
        await asyncio.sleep(1.5)
        return ["vnet-1", "lb-1", "nsg-1"]
    
    async def discover_data_resources():
        """Simulate data resource discovery."""
        logger.info("Discovering data resources...")
        await asyncio.sleep(2.5)
        return ["sql-1", "storage-1", "cosmos-1"]
    
    async def discover_config_resources():
        """Simulate config resource discovery."""
        logger.info("Discovering config resources...")
        await asyncio.sleep(1.0)
        return ["keyvault-1"]
    
    # Sequential discovery (for comparison)
    print("\nSequential discovery:")
    start_time = datetime.now()
    
    compute = await discover_compute_resources()
    networking = await discover_networking_resources()
    data = await discover_data_resources()
    config = await discover_config_resources()
    
    sequential_duration = (datetime.now() - start_time).total_seconds()
    total_resources = len(compute) + len(networking) + len(data) + len(config)
    
    print(f"  ✓ Discovered {total_resources} resources")
    print(f"  Duration: {sequential_duration:.2f}s")
    
    # Parallel discovery
    print("\nParallel discovery (max 4 workers):")
    start_time = datetime.now()
    
    tasks = [
        discover_compute_resources(),
        discover_networking_resources(),
        discover_data_resources(),
        discover_config_resources(),
    ]
    
    results = await asyncio.gather(*tasks)
    
    parallel_duration = (datetime.now() - start_time).total_seconds()
    total_resources = sum(len(r) for r in results)
    
    print(f"  ✓ Discovered {total_resources} resources")
    print(f"  Duration: {parallel_duration:.2f}s")
    print(f"  Speedup: {sequential_duration/parallel_duration:.1f}x faster")
    
    # Using WorkerPool
    print("\nUsing WorkerPool (max 4 workers):")
    start_time = datetime.now()
    
    config = WorkerPoolConfig(max_workers=4)
    pool = WorkerPool(config)
    
    tasks = [
        discover_compute_resources,
        discover_networking_resources,
        discover_data_resources,
        discover_config_resources,
    ]
    
    results = await pool.execute(tasks, [() for _ in tasks], [{} for _ in tasks])
    
    pool_duration = (datetime.now() - start_time).total_seconds()
    total_resources = sum(len(r) for r in results)
    
    print(f"  ✓ Discovered {total_resources} resources")
    print(f"  Duration: {pool_duration:.2f}s")
    print(f"  Speedup: {sequential_duration/pool_duration:.1f}x faster")


async def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print(" PHASE 3: PRODUCTION READY FEATURES")
    print("=" * 70)
    print("\nDemonstrating parallel discovery and caching capabilities")
    print("added in Phase 3 (Production Ready)")
    
    try:
        await demo_worker_pool()
        await demo_worker_pool_error_handling()
        await demo_cache_operations()
        await demo_parallel_discovery_simulation()
        
        print("\n" + "=" * 70)
        print(" ALL DEMONSTRATIONS COMPLETED")
        print("=" * 70)
        print("\nKey Benefits:")
        print("  • Parallel discovery: 2-4x faster resource discovery")
        print("  • Worker pools: Controlled concurrency with error handling")
        print("  • Caching: 10-100x faster for repeated queries")
        print("  • Production ready: Resilient and performant")
        print("\nSee docs/PHASE_2_3_IMPLEMENTATION.md for more details.")
        print("=" * 70 + "\n")
    
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
