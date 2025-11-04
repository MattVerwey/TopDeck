# Rate Limiting Implementation Summary

## Problem Statement
When clicking through the TopDeck dashboard, users were hitting rate limits due to the many API calls needed to load resources, dependencies, and risk assessments. This caused errors in the frontend and degraded the user experience.

## Solution
Implemented a comprehensive Redis-based distributed rate limiting system using the token bucket algorithm to intelligently manage API rate limits while allowing for normal dashboard usage patterns.

## Key Features

### 1. Token Bucket Algorithm
- **Burst Capacity**: Allows 120 instant requests (2x the rate) when loading a dashboard page
- **Sustained Rate**: Refills at 1 token per second (60/minute) for ongoing usage
- **Fair Distribution**: Each client gets their own bucket tracked independently

### 2. Distributed Architecture
- **Redis-Backed**: Rate limits work across multiple API instances
- **Atomic Operations**: Lua scripts ensure consistency in concurrent scenarios
- **Graceful Degradation**: Falls back to in-memory limiting if Redis unavailable

### 3. Per-Scope Limiting
Different endpoint types tracked separately:
- `topology`: Resource and dependency queries
- `risk`: Risk assessment endpoints
- `monitoring`: Metrics and monitoring
- `prediction`: ML prediction endpoints
- `changes`: Change management
- `global`: All other endpoints

This prevents heavy operations on one endpoint from blocking access to others.

### 4. HTTP Standards Compliance
Proper headers on all responses:
```http
X-RateLimit-Limit: 120
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699564800
Retry-After: 5  # On 429 responses
```

### 5. Intelligent Frontend Retry
- Detects 429 responses automatically
- Respects `Retry-After` header for exact wait time
- Falls back to exponential backoff for other retryable errors
- Transparent to application code (already integrated in api.ts)

## Implementation Details

### Backend Components

#### Rate Limiter (`src/topdeck/common/rate_limiter.py`)
```python
class RedisRateLimiter:
    """Token bucket rate limiter using Redis."""
    
    def __init__(
        self,
        redis_client: Optional[aioredis.Redis],
        requests_per_minute: int = 60,
        burst_size: Optional[int] = None,  # Defaults to 2x rate
    ):
        self.refill_rate = requests_per_minute / 60.0  # tokens per second
        self.burst_size = burst_size or (requests_per_minute * 2)
        # ... initialization
    
    async def is_allowed(
        self,
        client_id: str,
        scope: str = "global",
        cost: int = 1
    ) -> bool:
        """Check if request is allowed using atomic Lua script."""
        # Lua script atomically:
        # 1. Calculate elapsed time
        # 2. Add refilled tokens
        # 3. Check if sufficient tokens
        # 4. Deduct tokens if allowed
        # 5. Return allow/deny
```

#### Middleware (`src/topdeck/api/main.py`)
```python
class LazyRateLimiterMiddleware(RateLimitMiddleware):
    """Initializes Redis rate limiter on first request."""
    
    async def dispatch(self, request, call_next):
        # Initialize Redis limiter if available
        if not self._initialized and hasattr(request.app.state, "redis_client"):
            redis_client = request.app.state.redis_client
            if redis_client:
                self._redis_limiter = RedisRateLimiter(
                    redis_client=redis_client,
                    requests_per_minute=settings.rate_limit_requests_per_minute,
                    burst_size=settings.rate_limit_burst_size or None,
                )
        
        # Apply rate limiting with proper headers
        return await super().dispatch(request, call_next)
```

### Configuration (`src/topdeck/common/config.py`)
```python
class Settings(BaseSettings):
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_use_redis: bool = Field(default=True)
    rate_limit_requests_per_minute: int = Field(default=60)
    rate_limit_burst_size: int = Field(default=0)  # 0 = auto (2x rate)
```

### Frontend Enhancement (`frontend/src/services/api.ts`)
```typescript
private async requestWithRetry<T>(
  requestFn: () => Promise<T>,
  retries = 0,
): Promise<T> {
  try {
    return await requestFn();
  } catch (error) {
    if (error instanceof ApiError && error.statusCode === 429) {
      // Respect Retry-After header
      const retryAfter = getRetryAfterHeader(error);
      const delay = retryAfter * 1000 + 100;  // Add small buffer
      
      await sleep(delay);
      return this.requestWithRetry(requestFn, retries + 1);
    }
    // ... handle other retryable errors
  }
}
```

## Configuration Examples

### Development
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_USE_REDIS=true
RATE_LIMIT_REQUESTS_PER_MINUTE=120
RATE_LIMIT_BURST_SIZE=240
```
Allows: 240 instant requests, then 2 per second

### Production
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_USE_REDIS=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST_SIZE=120
```
Allows: 120 instant requests, then 1 per second

### High-Traffic Production
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_USE_REDIS=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST_SIZE=200
```
Allows: 200 instant requests, then 1.67 per second

## Redis Data Structure

```
Key: topdeck:ratelimit:{scope}:{client_id}
Type: Hash
Fields:
  - tokens: float (current token count)
  - last_refill: float (unix timestamp of last refill)
TTL: 120 seconds
```

Example:
```bash
redis-cli HGETALL "topdeck:ratelimit:topology:192.168.1.100"
1) "tokens"
2) "85.3"
3) "last_refill"
4) "1699564725.123"
```

## Testing

### Unit Tests (`tests/common/test_rate_limiter.py`)
- In-memory rate limiter tests (synchronous)
- Redis rate limiter tests (async)
- Token bucket behavior verification
- Scope isolation tests
- Edge cases (Redis unavailable, errors, etc.)

### Manual Testing
```bash
# Check if rate limiting is working
for i in {1..150}; do
  curl -w "%{http_code}\n" -s http://localhost:8000/api/v1/topology > /dev/null
done

# First 120 should succeed (200)
# Next 30 should fail (429)
# After 30 seconds, tokens refill (200 again)
```

## Monitoring

### Logs
```json
{
  "event": "rate_limit_exceeded",
  "client_id": "192.168.1.100",
  "path": "/api/v1/topology",
  "scope": "topology",
  "retry_after": 5,
  "level": "warning"
}
```

### Metrics
- `http_requests_total{status="429"}` - Rate limited requests
- `http_request_duration_seconds` - Request latency
- Check Redis: `redis-cli INFO stats`

### Health Check
```bash
# Check detailed health including Redis
curl http://localhost:8000/health/detailed

# Response includes Redis status
{
  "status": "healthy",
  "components": {
    "redis": {
      "status": "healthy",
      "response_time_ms": 2.5,
      "details": {
        "redis_version": "7.0.0",
        "uptime_seconds": 86400
      }
    }
  }
}
```

## Benefits

1. **Dashboard Performance**: Token bucket allows burst traffic for page loads
2. **Fair Resource Allocation**: Each client gets equal share
3. **Distributed**: Works across multiple API instances
4. **Transparent**: Frontend handles rate limits automatically
5. **Configurable**: Easy to adjust limits for different environments
6. **Observable**: Full monitoring and logging support
7. **Reliable**: Fails open if Redis unavailable
8. **Flexible**: Per-scope limiting for different use cases

## Migration Path

### Existing Deployments
1. Deploy with `RATE_LIMIT_USE_REDIS=false` (uses existing in-memory limiter)
2. Monitor for issues
3. Enable Redis: `RATE_LIMIT_USE_REDIS=true`
4. Monitor rate limit headers and logs
5. Adjust limits as needed

### New Deployments
Start with recommended production settings:
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_USE_REDIS=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST_SIZE=120
```

## Files Changed

### Backend
- `src/topdeck/common/rate_limiter.py` - Core rate limiting implementation
- `src/topdeck/api/main.py` - API integration and middleware
- `src/topdeck/common/config.py` - Configuration settings
- `tests/common/test_rate_limiter.py` - Test coverage

### Frontend
- `frontend/src/services/api.ts` - Retry logic enhancement

### Configuration
- `.env.example` - Configuration documentation

### Documentation
- `docs/RATE_LIMITING.md` - Comprehensive guide
- `docs/RATE_LIMITING_QUICK_REF.md` - Quick reference
- `README.md` - Documentation links

## Future Enhancements

Possible future improvements:
1. **Per-User Rate Limits**: Different limits based on user role/tier
2. **Dynamic Rate Limits**: Adjust based on system load
3. **Rate Limit Quotas**: Daily/monthly quotas in addition to per-minute
4. **Priority Queues**: Higher priority for certain endpoints
5. **Cost-Based Limiting**: Different token costs for expensive operations
6. **Grafana Dashboard**: Visual monitoring of rate limit metrics

## Conclusion

This implementation provides production-ready rate limiting that:
- ✅ Solves the dashboard rate limit problem
- ✅ Works across distributed deployments
- ✅ Provides clear visibility into rate limit status
- ✅ Handles failures gracefully
- ✅ Integrates transparently with existing code
- ✅ Is fully configurable and monitorable

The token bucket algorithm is specifically chosen to handle the dashboard's burst traffic pattern (many simultaneous API calls when loading a page) while still protecting the API from sustained abuse.

For more details, see:
- [Rate Limiting Guide](docs/RATE_LIMITING.md)
- [Quick Reference](docs/RATE_LIMITING_QUICK_REF.md)
