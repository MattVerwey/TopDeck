# Rate Limiting Quick Reference

## TL;DR

TopDeck uses Redis-based token bucket rate limiting to protect the API. The frontend automatically handles rate limits with retry logic.

## Quick Configuration

```bash
# .env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_USE_REDIS=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60    # 1 token/second
RATE_LIMIT_BURST_SIZE=120             # Allow bursts up to 120 requests
```

## Rate Limit Headers

Every response includes:
```
X-RateLimit-Limit: 120        # Max tokens
X-RateLimit-Remaining: 95     # Available tokens
X-RateLimit-Reset: 1699564800 # Unix timestamp
```

When rate limited (HTTP 429):
```
Retry-After: 5                # Wait 5 seconds
```

## Default Limits

| Endpoint Type | Scope | Example Path |
|--------------|-------|--------------|
| Topology | `topology` | `/api/v1/topology/*` |
| Risk Analysis | `risk` | `/api/v1/risk/*` |
| Monitoring | `monitoring` | `/api/v1/monitoring/*` |
| Predictions | `prediction` | `/api/v1/prediction/*` |
| Changes | `changes` | `/api/v1/changes/*` |
| Other | `global` | All other endpoints |

Each scope is tracked independently.

## Common Settings

### Development
```bash
RATE_LIMIT_REQUESTS_PER_MINUTE=120
RATE_LIMIT_BURST_SIZE=240
```

### Production
```bash
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST_SIZE=120
```

### High-Traffic
```bash
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST_SIZE=200
```

## Client Retry Pattern

The frontend already handles this automatically.

For custom clients:

```python
# Python
import time
import requests

response = requests.get(url)
if response.status_code == 429:
    retry_after = int(response.headers.get('Retry-After', 1))
    time.sleep(retry_after)
    response = requests.get(url)  # Retry
```

```javascript
// JavaScript
const response = await fetch(url);
if (response.status === 429) {
  const retryAfter = parseInt(response.headers.get('Retry-After') || '1');
  await new Promise(r => setTimeout(r, retryAfter * 1000));
  return fetch(url);  // Retry
}
```

## Troubleshooting

### Too Many 429 Errors

1. Increase `RATE_LIMIT_REQUESTS_PER_MINUTE`
2. Increase `RATE_LIMIT_BURST_SIZE`
3. Optimize client code to reduce API calls
4. Add client-side caching

### Rate Limiting Not Working

1. Check `RATE_LIMIT_ENABLED=true`
2. Verify Redis is running: `redis-cli ping`
3. Check logs for errors

### Check Current Limits

```bash
# View Redis rate limit keys
redis-cli --scan --pattern "topdeck:ratelimit:*"

# Check specific client
redis-cli HGETALL "topdeck:ratelimit:global:192.168.1.100"
```

## How Token Bucket Works

```
Bucket Capacity: 120 tokens (burst size)
Refill Rate: 1 token/second (60/minute)

[████████████████████] 120 tokens (full bucket)
  ↓ Make 120 requests instantly
[                    ] 0 tokens (empty)
  ↓ Wait 1 second
[█                   ] 1 token (refilled)
  ↓ Wait 1 second  
[██                  ] 2 tokens (refilled)
```

This allows:
- **Burst**: 120 requests instantly
- **Sustained**: 1 request/second after burst

## Monitoring

### Logs
```json
{
  "event": "rate_limit_exceeded",
  "client_id": "192.168.1.100",
  "path": "/api/v1/topology",
  "retry_after": 5
}
```

### Prometheus Metrics
```
http_requests_total{status="429"}
```

## Exempt Endpoints

These endpoints are NOT rate limited:
- `/health`
- `/health/detailed`
- `/metrics`
- `/`
- `/api/info`

## Architecture

```
Request → Middleware → Check Redis Token Bucket
                    ↓
              Have tokens? → Yes → Allow (200)
                    ↓ No
              Rate Limited → Block (429 + Retry-After)
```

**Fallback**: Redis unavailable → In-memory limiter → Fail open (allow)

## Full Documentation

See [docs/RATE_LIMITING.md](RATE_LIMITING.md) for complete details.
