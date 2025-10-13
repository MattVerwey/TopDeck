"""
Tests for worker pool.
"""

import pytest
import asyncio

from topdeck.common.worker_pool import (
    WorkerPool,
    WorkerPoolConfig,
    parallel_map,
)


class TestWorkerPoolConfig:
    """Tests for WorkerPoolConfig"""
    
    def test_worker_pool_config_defaults(self):
        """Test default configuration"""
        config = WorkerPoolConfig()
        
        assert config.max_workers == 5
        assert config.timeout is None
        assert config.continue_on_error is True
    
    def test_worker_pool_config_custom(self):
        """Test custom configuration"""
        config = WorkerPoolConfig(
            max_workers=10,
            timeout=30.0,
            continue_on_error=False,
        )
        
        assert config.max_workers == 10
        assert config.timeout == 30.0
        assert config.continue_on_error is False


class TestWorkerPool:
    """Tests for WorkerPool"""
    
    @pytest.mark.asyncio
    async def test_worker_pool_execute_success(self):
        """Test executing tasks successfully"""
        pool = WorkerPool()
        
        async def task(x):
            await asyncio.sleep(0.01)
            return x * 2
        
        tasks = [task for _ in range(5)]
        task_args = [(i,) for i in range(5)]
        
        results = await pool.execute(tasks, task_args)
        
        assert len(results) == 5
        assert results == [0, 2, 4, 6, 8]
        assert not pool.has_errors()
    
    @pytest.mark.asyncio
    async def test_worker_pool_map(self):
        """Test mapping function over items"""
        pool = WorkerPool()
        
        async def double(x):
            await asyncio.sleep(0.01)
            return x * 2
        
        items = [1, 2, 3, 4, 5]
        results = await pool.map(double, items)
        
        assert len(results) == 5
        assert results == [2, 4, 6, 8, 10]
    
    @pytest.mark.asyncio
    async def test_worker_pool_partial_failure(self):
        """Test handling partial failures"""
        config = WorkerPoolConfig(continue_on_error=True)
        pool = WorkerPool(config)
        
        async def task(x):
            await asyncio.sleep(0.01)
            if x == 2:
                raise ValueError(f"Task {x} failed")
            return x * 2
        
        tasks = [task for _ in range(5)]
        task_args = [(i,) for i in range(5)]
        
        results = await pool.execute(tasks, task_args)
        
        # Should return results from successful tasks
        assert len(results) == 4
        assert 4 not in results  # Task 2 failed
        assert pool.has_errors()
        
        summary = pool.get_summary()
        assert summary['success'] == 4
        assert summary['failure'] == 1
        assert summary['total'] == 5
    
    @pytest.mark.asyncio
    async def test_worker_pool_timeout(self):
        """Test task timeout"""
        config = WorkerPoolConfig(timeout=0.1, continue_on_error=True)
        pool = WorkerPool(config)
        
        async def slow_task(x):
            await asyncio.sleep(1.0)  # Longer than timeout
            return x
        
        async def fast_task(x):
            await asyncio.sleep(0.01)
            return x
        
        tasks = [slow_task, fast_task, slow_task]
        task_args = [(1,), (2,), (3,)]
        
        results = await pool.execute(tasks, task_args)
        
        # Only fast task should succeed
        assert len(results) == 1
        assert results[0] == 2
        
        summary = pool.get_summary()
        assert summary['success'] == 1
        assert summary['failure'] == 2
    
    @pytest.mark.asyncio
    async def test_worker_pool_concurrency_limit(self):
        """Test concurrency limiting"""
        config = WorkerPoolConfig(max_workers=2)
        pool = WorkerPool(config)
        
        concurrent_count = 0
        max_concurrent = 0
        lock = asyncio.Lock()
        
        async def task(x):
            nonlocal concurrent_count, max_concurrent
            
            async with lock:
                concurrent_count += 1
                max_concurrent = max(max_concurrent, concurrent_count)
            
            await asyncio.sleep(0.05)
            
            async with lock:
                concurrent_count -= 1
            
            return x
        
        tasks = [task for _ in range(10)]
        task_args = [(i,) for i in range(10)]
        
        results = await pool.execute(tasks, task_args)
        
        assert len(results) == 10
        assert max_concurrent <= 2  # Should not exceed max_workers
    
    @pytest.mark.asyncio
    async def test_worker_pool_all_failures(self):
        """Test handling when all tasks fail"""
        config = WorkerPoolConfig(continue_on_error=False)
        pool = WorkerPool(config)
        
        async def failing_task(x):
            raise ValueError(f"Task {x} failed")
        
        tasks = [failing_task for _ in range(3)]
        task_args = [(i,) for i in range(3)]
        
        with pytest.raises(RuntimeError, match="All 3 tasks failed"):
            await pool.execute(tasks, task_args)


class TestParallelMap:
    """Tests for parallel_map convenience function"""
    
    @pytest.mark.asyncio
    async def test_parallel_map_success(self):
        """Test parallel mapping"""
        async def triple(x):
            await asyncio.sleep(0.01)
            return x * 3
        
        items = [1, 2, 3, 4, 5]
        results = await parallel_map(triple, items, max_workers=3)
        
        assert results == [3, 6, 9, 12, 15]
    
    @pytest.mark.asyncio
    async def test_parallel_map_with_timeout(self):
        """Test parallel mapping with timeout"""
        async def slow_double(x):
            if x == 2:
                await asyncio.sleep(1.0)  # Will timeout
            else:
                await asyncio.sleep(0.01)
            return x * 2
        
        items = [1, 2, 3]
        results = await parallel_map(
            slow_double,
            items,
            max_workers=2,
            timeout=0.1
        )
        
        # Only items 1 and 3 should succeed
        assert len(results) == 2
        assert 2 in results  # item 1
        assert 6 in results  # item 3
        assert 4 not in results  # item 2 timed out
    
    @pytest.mark.asyncio
    async def test_parallel_map_empty_list(self):
        """Test parallel mapping with empty list"""
        async def process(x):
            return x
        
        results = await parallel_map(process, [])
        
        assert results == []
