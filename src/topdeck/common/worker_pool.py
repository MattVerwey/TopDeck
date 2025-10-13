"""
Worker pool for parallel/concurrent task execution.

Provides a thread-safe worker pool for executing async tasks in parallel
with configurable concurrency limits and error handling.
"""

import asyncio
import logging
from typing import Any, Callable, List, Optional, TypeVar
from dataclasses import dataclass

from .resilience import ErrorTracker

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class WorkerPoolConfig:
    """Configuration for worker pool."""
    
    max_workers: int = 5
    """Maximum number of concurrent workers"""
    
    timeout: Optional[float] = None
    """Optional timeout for each task in seconds"""
    
    continue_on_error: bool = True
    """Whether to continue processing if a task fails"""


class WorkerPool:
    """
    Worker pool for parallel async task execution.
    
    Manages concurrent execution of async tasks with configurable
    concurrency limits, error handling, and progress tracking.
    """
    
    def __init__(self, config: Optional[WorkerPoolConfig] = None):
        """
        Initialize worker pool.
        
        Args:
            config: Worker pool configuration (uses defaults if None)
        """
        self.config = config or WorkerPoolConfig()
        self._semaphore = asyncio.Semaphore(self.config.max_workers)
        self._error_tracker = ErrorTracker()
    
    async def execute(
        self,
        tasks: List[Callable],
        task_args: Optional[List[tuple]] = None,
        task_kwargs: Optional[List[dict]] = None,
    ) -> List[Any]:
        """
        Execute multiple async tasks in parallel.
        
        Args:
            tasks: List of async callables to execute
            task_args: Optional list of positional arguments for each task
            task_kwargs: Optional list of keyword arguments for each task
            
        Returns:
            List of results from successful tasks
            
        Raises:
            RuntimeError: If all tasks fail and continue_on_error is False
        """
        if task_args is None:
            task_args = [() for _ in tasks]
        if task_kwargs is None:
            task_kwargs = [{} for _ in tasks]
        
        if len(tasks) != len(task_args) or len(tasks) != len(task_kwargs):
            raise ValueError("tasks, task_args, and task_kwargs must have same length")
        
        # Create worker tasks
        worker_tasks = [
            self._execute_task(i, task, args, kwargs)
            for i, (task, args, kwargs) in enumerate(zip(tasks, task_args, task_kwargs))
        ]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*worker_tasks, return_exceptions=True)
        
        # Separate successful results from errors
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task {i} failed: {result}")
                self._error_tracker.record_error(str(i), result)
            else:
                successful_results.append(result)
                self._error_tracker.record_success(str(i))
        
        # Log summary
        summary = self._error_tracker.get_summary()
        logger.info(
            f"Worker pool completed: {summary['success']} succeeded, "
            f"{summary['failure']} failed out of {summary['total']}"
        )
        
        # Raise if all tasks failed and not configured to continue
        if not self.config.continue_on_error:
            if summary['failure'] == summary['total']:
                raise RuntimeError(
                    f"All {summary['total']} tasks failed. "
                    f"Error rate: {summary['error_rate']:.2%}"
                )
        
        return successful_results
    
    async def map(
        self,
        func: Callable,
        items: List[Any],
    ) -> List[Any]:
        """
        Map an async function over a list of items in parallel.
        
        Similar to asyncio.gather but with concurrency limits.
        
        Args:
            func: Async callable to apply to each item
            items: List of items to process
            
        Returns:
            List of results from successful function calls
        """
        tasks = [func for _ in items]
        task_args = [(item,) for item in items]
        
        return await self.execute(tasks, task_args)
    
    async def _execute_task(
        self,
        task_id: int,
        task: Callable,
        args: tuple,
        kwargs: dict,
    ) -> Any:
        """
        Execute a single task with semaphore control.
        
        Args:
            task_id: Unique task identifier
            task: Async callable to execute
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            Task result
            
        Raises:
            Exception: If task fails
        """
        async with self._semaphore:
            logger.debug(f"Starting task {task_id}")
            
            try:
                if self.config.timeout:
                    result = await asyncio.wait_for(
                        task(*args, **kwargs),
                        timeout=self.config.timeout
                    )
                else:
                    result = await task(*args, **kwargs)
                
                logger.debug(f"Task {task_id} completed successfully")
                return result
                
            except asyncio.TimeoutError:
                logger.error(f"Task {task_id} timed out after {self.config.timeout}s")
                raise
            except Exception as e:
                logger.error(f"Task {task_id} failed: {e}")
                raise
    
    def get_summary(self) -> dict:
        """
        Get execution summary.
        
        Returns:
            Dictionary with execution statistics
        """
        return self._error_tracker.get_summary()
    
    def has_errors(self) -> bool:
        """Check if any tasks failed."""
        return self._error_tracker.has_errors()


async def parallel_map(
    func: Callable,
    items: List[Any],
    max_workers: int = 5,
    timeout: Optional[float] = None,
) -> List[Any]:
    """
    Convenience function for parallel mapping.
    
    Args:
        func: Async callable to apply to each item
        items: List of items to process
        max_workers: Maximum concurrent workers
        timeout: Optional timeout per task in seconds
        
    Returns:
        List of results from successful function calls
        
    Example:
        >>> async def process_item(item):
        ...     await asyncio.sleep(1)
        ...     return item * 2
        >>> 
        >>> items = [1, 2, 3, 4, 5]
        >>> results = await parallel_map(process_item, items, max_workers=3)
        >>> print(results)
        [2, 4, 6, 8, 10]
    """
    config = WorkerPoolConfig(max_workers=max_workers, timeout=timeout)
    pool = WorkerPool(config)
    return await pool.map(func, items)
