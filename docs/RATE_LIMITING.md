# Rate Limiting in TopDeck

TopDeck implements intelligent rate limiting to protect the API from abuse and ensure fair resource allocation across clients. The system uses a **token bucket algorithm** with Redis for distributed rate limiting across multiple API instances.

## Overview

Rate limiting prevents any single client from overwhelming the API with too many requests. This is especially important for the TopDeck dashboard, which makes multiple API calls when loading pages with resources, dependencies, and risk assessments.

### Key Features

- **Distributed**: Uses Redis for coordination across multiple API instances
- **Token Bucket Algorithm**: Allows burst traffic while maintaining average rate limits
- **Per-Scope Limiting**: Different endpoints can have different rate limits
- **Graceful Degradation**: Falls back to in-memory limiting if Redis is unavailable
- **Standards-Compliant**: Returns proper HTTP 429 status with `Retry-After` header
- **Rate Limit Headers**: Provides visibility into remaining quota

## How It Works

### Token Bucket Algorithm

The token bucket algorithm works like this:

1. Each client has a "bucket" that holds tokens
2. Tokens are added to the bucket at a constant rate (e.g., 60 per minute = 1 per second)
3. Each request consumes 1 token
4. If the bucket has tokens, the request is allowed and a token is removed
5. If the bucket is empty, the request is rate limited (HTTP 429)
6. The bucket has a maximum capacity (burst size) to allow short traffic spikes

**Example:**
- Rate: 60 requests/minute (1 token/second)
- Burst: 120 tokens (2x the rate)
- Client can make 120 requests instantly, then 1 request per second thereafter

### Scopes

Different API endpoints can have different rate limit scopes:

- **topology**: `/api/v1/topology/*` - Resource and dependency queries
- **risk**: `/api/v1/risk/*` - Risk assessment endpoints
- **monitoring**: `/api/v1/monitoring/*` - Metrics and monitoring
- **prediction**: `/api/v1/prediction/*` - ML prediction endpoints
- **changes**: `/api/v1/changes/*` - Change management
- **global**: All other endpoints

Each scope tracks rate limits independently, preventing one heavy operation from blocking other API usage.

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Enable rate limiting (default: true)
RATE_LIMIT_ENABLED=true

# Use Redis for distributed rate limiting (default: true)
# Falls back to in-memory if Redis unavailable
RATE_LIMIT_USE_REDIS=true

# Token refill rate: requests per minute (default: 60)
# This means 1 token is added to the bucket every second
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Burst capacity: maximum tokens in bucket (default: 2x rate)
# Set to 0 for auto (2x requests_per_minute)
# Higher values allow larger bursts but more potential for abuse
RATE_LIMIT_BURST_SIZE=120
```

### Recommended Settings

**Development:**
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=120
RATE_LIMIT_BURST_SIZE=240
```

**Production:**
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_USE_REDIS=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST_SIZE=120
```

**High-Traffic Production:**
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_USE_REDIS=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST_SIZE=200
```

## Rate Limit Headers

Every API response includes rate limit information:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 120
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699564800
```

- `X-RateLimit-Limit`: Maximum tokens in your bucket
- `X-RateLimit-Remaining`: Tokens currently available
- `X-RateLimit-Reset`: Unix timestamp when tokens will refill

When rate limited:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 5
X-RateLimit-Limit: 120
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1699564805

{
  "detail": "Rate limit exceeded. Retry after 5 seconds."
}
```

## Client Handling

### Frontend (Automatic)

The TopDeck frontend automatically handles rate limiting:

```typescript
// api.ts already implements retry logic
const result = await apiClient.getTopology();
// Automatically retries with Retry-After header on 429
```

The frontend:
1. Detects 429 responses
2. Reads the `Retry-After` header
3. Waits the specified time
4. Retries the request (up to 3 times)

### Custom Clients

When building custom clients, handle 429 responses:

```python
import time
import requests

def api_call_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url)
        
        if response.status_code == 429:
            # Read Retry-After header
            retry_after = int(response.headers.get('Retry-After', 1))
            print(f"Rate limited. Waiting {retry_after}s...")
            time.sleep(retry_after)
            continue
        
        return response
    
    raise Exception("Max retries exceeded")
```

```javascript
async function apiCallWithRetry(url, maxRetries = 3) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    const response = await fetch(url);
    
    if (response.status === 429) {
      const retryAfter = parseInt(response.headers.get('Retry-After') || '1');
      console.log(`Rate limited. Waiting ${retryAfter}s...`);
      await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
      continue;
    }
    
    return response;
  }
  
  throw new Error('Max retries exceeded');
}
```

## Monitoring

### Check Rate Limit Status

Monitor rate limit effectiveness:

```bash
# Check Redis for rate limit data
redis-cli --scan --pattern "topdeck:ratelimit:*"

# View a specific client's bucket
redis-cli HGETALL "topdeck:ratelimit:global:192.168.1.100"
# Returns: tokens (available), last_refill (timestamp)
```

### Application Logs

Rate limit events are logged:

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

Track rate limiting via Prometheus metrics (if enabled):

- `http_requests_total{status="429"}` - Total rate limited requests
- `http_request_duration_seconds` - Request latency

## Troubleshooting

### "Rate limit exceeded" errors

**Problem:** Clients receive 429 errors frequently

**Solutions:**
1. **Increase rate limits**: Raise `RATE_LIMIT_REQUESTS_PER_MINUTE`
2. **Increase burst size**: Raise `RATE_LIMIT_BURST_SIZE`
3. **Optimize client**: Reduce unnecessary API calls
4. **Add caching**: Cache responses client-side
5. **Batch requests**: Combine multiple queries where possible

### Rate limiting not working

**Problem:** No rate limiting appears to be happening

**Check:**
1. Is `RATE_LIMIT_ENABLED=true` in `.env`?
2. Is Redis running and accessible?
3. Check logs for "Redis rate limiter disabled" warnings
4. Verify exempt paths don't include your endpoints

### Redis connection issues

**Problem:** "Redis rate limiter disabled" in logs

**Impact:** Falls back to in-memory limiting (single instance only)

**Solutions:**
1. Verify Redis is running: `redis-cli ping`
2. Check Redis connection settings in `.env`
3. Verify network connectivity
4. Check Redis logs for errors

### Different limits per user

**Advanced:** Implement custom rate limiting by user ID instead of IP:

```python
# Custom middleware in main.py
class UserRateLimitMiddleware(RateLimitMiddleware):
    async def dispatch(self, request, call_next):
        # Get user ID from JWT token or session
        user_id = get_user_id_from_request(request)
        
        # Use user ID instead of IP for rate limiting
        # This requires modifying the client_id in the parent class
        request.state.rate_limit_client_id = user_id
        
        return await super().dispatch(request, call_next)
```

## Best Practices

1. **Monitor Initially**: Start with lenient limits and tighten based on actual usage
2. **Document Limits**: Clearly communicate rate limits in API documentation
3. **Provide Feedback**: Always return `Retry-After` header with 429 responses
4. **Use Redis**: Enable Redis-based limiting for production deployments
5. **Scope Appropriately**: Use per-scope limiting for different endpoint types
6. **Test Thoroughly**: Test your client's retry logic before production
7. **Plan for Growth**: Set limits that allow for reasonable traffic growth
8. **Cache Aggressively**: Reduce API calls by caching on the client side

## Architecture

### Token Bucket in Redis

```
Redis Key: topdeck:ratelimit:{scope}:{client_id}
Hash Fields:
  - tokens: Current token count (float)
  - last_refill: Last refill timestamp (float)

Lua Script (Atomic):
1. Calculate elapsed time since last_refill
2. Add tokens: time_elapsed * refill_rate
3. Cap tokens at burst_size
4. If tokens >= cost, subtract cost and return 1 (allow)
5. Else return 0 (deny)
```

### Fallback Behavior

```
Redis Available? → Use Redis Rate Limiter (Distributed)
       ↓ No
In-Memory Limiter (Single Instance)
       ↓ Exception
Fail Open (Allow Request)
```

The system gracefully degrades:
1. **Best**: Redis-based distributed limiting
2. **Good**: In-memory limiting (single instance)
3. **Safe**: Fail open on errors (availability over strict limiting)

## Related Documentation

- [API Documentation](../README.md#-what-can-you-do-with-topdeck-today)
- [Configuration Guide](../README.md#-getting-started)
- [Frontend API Client](../frontend/src/services/api.ts)
- [Redis Configuration](../docker-compose.yml)

## FAQ

**Q: Will rate limiting affect dashboard performance?**
A: No. The token bucket algorithm allows burst traffic for page loads while preventing sustained abuse.

**Q: What happens if Redis goes down?**
A: The system falls back to in-memory rate limiting automatically. No requests are blocked.

**Q: Can I disable rate limiting?**
A: Yes, set `RATE_LIMIT_ENABLED=false` in `.env`. Not recommended for production.

**Q: Do internal API calls get rate limited?**
A: No. Health checks (`/health`, `/metrics`) and info endpoints are exempt.

**Q: Why use token bucket instead of sliding window?**
A: Token bucket better handles burst traffic patterns common in web applications, like loading a dashboard page.

**Q: How do I increase limits for specific users?**
A: Implement custom middleware to use user ID instead of IP and assign different limits per user role.
