# Common Utilities

This module contains shared utilities and infrastructure code used across TopDeck.

## Modules

### resilience.py

Production-ready resilience patterns for making API calls more reliable.

**Features**:
- `RateLimiter`: Token bucket rate limiting for API throttling
- `RetryConfig`: Configuration for exponential backoff retry logic
- `retry_with_backoff`: Decorator for async functions with automatic retry
- `CircuitBreaker`: Prevent cascading failures
- `ErrorTracker`: Track outcomes of batch operations

**Usage**:
```python
from topdeck.common.resilience import (
    RateLimiter,
    retry_with_backoff,
    RetryConfig,
)

# Rate limiting
limiter = RateLimiter(max_calls=200, time_window=60.0)
await limiter.acquire()
# Make API call

# Retry with backoff
@retry_with_backoff(config=RetryConfig(max_attempts=3))
async def risky_api_call():
    # Your code here
    pass
```

### logging_config.py

Structured logging infrastructure with JSON formatting and correlation IDs.

**Features**:
- `StructuredFormatter`: JSON-formatted logs for log aggregation
- `ContextLogger`: Logger with correlation ID support
- `LoggingContext`: Context manager for temporary logging context
- `log_operation_metrics`: Log operation performance metrics

**Usage**:
```python
from topdeck.common.logging_config import (
    setup_logging,
    get_logger,
    set_correlation_id,
)

# Set up logging
setup_logging(level="INFO", json_format=True)

# Get logger
logger = get_logger(__name__)

# Set correlation ID
set_correlation_id("request-123")

# Log
logger.info("Processing request")
```

## Design Patterns

### Rate Limiting

Uses the **token bucket algorithm** to enforce rate limits:
- Tokens are added at a constant rate
- Each request consumes a token
- When bucket is empty, requests wait

### Retry Logic

Uses **exponential backoff with jitter**:
- Initial delay doubles on each retry (exponential)
- Random jitter prevents thundering herd
- Maximum delay caps the wait time

### Circuit Breaker

Implements the **circuit breaker pattern**:
- **Closed**: Normal operation
- **Open**: Failures exceeded threshold, reject immediately
- **Half-Open**: After timeout, test with single request

### Error Tracking

Uses **accumulator pattern** for batch operations:
- Continue processing despite failures
- Track all errors with context
- Provide summary statistics

## Integration

These utilities are integrated throughout TopDeck:

- **Azure DevOps integration** uses rate limiting and retry logic
- **Resource discovery** uses error tracking for batch operations
- **API handlers** use structured logging with correlation IDs
- **External API calls** use circuit breakers for resilience

## Testing

Run tests:
```bash
pytest tests/common/test_resilience.py -v
```

## Performance

**Rate Limiter**: O(n) where n = number of calls in time window  
**Retry Logic**: Minimal overhead (~1ms per retry decision)  
**Circuit Breaker**: O(1) state checks  
**Error Tracker**: O(1) record operations

## Future Enhancements

- [ ] Distributed rate limiting with Redis
- [ ] Metrics export to Prometheus
- [ ] Distributed tracing with OpenTelemetry
- [ ] Advanced circuit breaker with health checks
