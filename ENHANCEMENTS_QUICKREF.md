# TopDeck Enhancements - Quick Reference

## New API Endpoints

```bash
# Basic health check
GET /health

# Detailed health with dependency status
GET /health/detailed

# Prometheus metrics
GET /metrics
```

## Response Headers

All API responses now include:

```
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
X-Process-Time: 45.23
X-API-Version: v1
```

When rate limited:
```
Retry-After: 30
```

## Configuration

Add to `.env`:

```bash
# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Request Settings
REQUEST_TIMEOUT_SECONDS=30
MAX_REQUEST_SIZE_MB=10
```

## Quick Test Commands

```bash
# Test health check
curl http://localhost:8000/health/detailed

# View metrics
curl http://localhost:8000/metrics | head -20

# Test rate limiting (send many requests)
for i in {1..70}; do curl http://localhost:8000/api/v1/topology; done

# Get request ID
curl -i http://localhost:8000/api/v1/topology | grep X-Request-ID
```

## Using New Features

### Backend: Input Validation

```python
from topdeck.common.validators import validate_resource_id, validate_cloud_provider

@router.get("/resources/{resource_id}")
async def get_resource(resource_id: str, provider: str):
    resource_id = validate_resource_id(resource_id)
    provider = validate_cloud_provider(provider)
    # ... rest of endpoint
```

### Backend: Custom Errors

```python
from topdeck.common.errors import ResourceNotFoundException

if not resource:
    raise ResourceNotFoundException("compute", resource_id)
```

### Frontend: Error Boundary

```tsx
import ErrorBoundary from './components/common/ErrorBoundary';

<ErrorBoundary>
  <YourComponent />
</ErrorBoundary>
```

### Frontend: Error Display

```tsx
import ErrorDisplay from './components/common/ErrorDisplay';

{error && (
  <ErrorDisplay 
    error={error} 
    onRetry={handleRetry}
    title="Failed to load data"
  />
)}
```

## Metrics Available

```
# HTTP Metrics
topdeck_http_requests_total
topdeck_http_request_duration_seconds

# Discovery Metrics
topdeck_discovery_runs_total
topdeck_discovery_resources_found
topdeck_discovery_duration_seconds

# Risk Metrics
topdeck_risk_assessments_total
topdeck_risk_score_distribution
topdeck_single_points_of_failure

# Database Metrics
topdeck_neo4j_query_duration_seconds
topdeck_redis_operations_total
topdeck_cache_hits_total
```

## Prometheus Setup

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'topdeck'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
```

## Sample Alerts

```yaml
groups:
  - name: topdeck
    rules:
      - alert: HighErrorRate
        expr: rate(topdeck_http_requests_total{status_code=~"5.."}[5m]) > 0.1
        
      - alert: ServiceUnhealthy
        expr: up{job="topdeck"} == 0
        
      - alert: HighLatency
        expr: histogram_quantile(0.95, topdeck_http_request_duration_seconds) > 2
```

## Running Tests

```bash
# Backend tests
pytest tests/common/test_middleware.py -v
pytest tests/common/test_rate_limiter.py -v
pytest tests/common/test_validators.py -v

# All tests
pytest tests/ -v
```

## What Changed

**18 Files Modified/Added**:
- 7 new backend utility modules
- 3 new test files
- 3 new frontend components
- 2 documentation files
- 3 updated files

**Key Improvements**:
- ✅ Request logging & tracing
- ✅ Rate limiting
- ✅ Health checks
- ✅ Prometheus metrics
- ✅ Input validation
- ✅ Error handling
- ✅ API versioning
- ✅ Frontend retry logic
- ✅ Error boundaries

## Documentation

- **Full Guide**: `docs/API_ENHANCEMENTS.md`
- **Summary**: `ENHANCEMENTS_SUMMARY.md`
- **This Card**: `ENHANCEMENTS_QUICKREF.md`

## Status

🎯 **All Enhancements Complete**  
✅ **Production Ready**  
📚 **Fully Documented**  
🧪 **Tested**  
♻️ **Backward Compatible**

---

For detailed information, see `docs/API_ENHANCEMENTS.md`
