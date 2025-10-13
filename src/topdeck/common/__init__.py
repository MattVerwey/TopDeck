"""Common utilities and shared components."""

# Don't import Settings by default to avoid pydantic dependency in imports
# Users can: from topdeck.common.config import Settings

from topdeck.common.resilience import (
    RateLimiter,
    RetryConfig,
    retry_with_backoff,
    ErrorTracker,
    CircuitBreaker,
    with_rate_limit,
)
from topdeck.common.logging_config import (
    setup_logging,
    get_logger,
    set_correlation_id,
    get_correlation_id,
    LoggingContext,
    log_operation_metrics,
)
from topdeck.common.worker_pool import (
    WorkerPool,
    WorkerPoolConfig,
    parallel_map,
)
from topdeck.common.cache import (
    Cache,
    CacheConfig,
    cached,
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
