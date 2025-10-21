"""Common utilities and shared components."""

# Don't import Settings by default to avoid pydantic dependency in imports
# Users can: from topdeck.common.config import Settings

from topdeck.common.cache import (
    Cache,
    CacheConfig,
    cached,
)
from topdeck.common.logging_config import (
    LoggingContext,
    get_correlation_id,
    get_logger,
    log_operation_metrics,
    set_correlation_id,
    setup_logging,
)
from topdeck.common.resilience import (
    CircuitBreaker,
    ErrorTracker,
    RateLimiter,
    RetryConfig,
    retry_with_backoff,
    with_rate_limit,
)
from topdeck.common.worker_pool import (
    WorkerPool,
    WorkerPoolConfig,
    parallel_map,
)

__all__ = [
    # Resilience
    "RateLimiter",
    "RetryConfig",
    "retry_with_backoff",
    "ErrorTracker",
    "CircuitBreaker",
    "with_rate_limit",
    # Logging
    "setup_logging",
    "get_logger",
    "set_correlation_id",
    "get_correlation_id",
    "LoggingContext",
    "log_operation_metrics",
    # Worker Pool
    "WorkerPool",
    "WorkerPoolConfig",
    "parallel_map",
    # Cache
    "Cache",
    "CacheConfig",
    "cached",
]
