# API Enhancements Documentation

This document describes the enhancements made to the TopDeck API for improved observability, reliability, and maintainability.

## Overview

The following enhancements have been added to improve the production readiness of the TopDeck API:

1. **Request Logging & Tracing**
2. **Rate Limiting**
3. **Health Checks**
4. **Metrics & Monitoring**
5. **Input Validation**
6. **Error Handling**
7. **API Versioning**

## 1. Request Logging & Tracing

### Features

- **Request ID Generation**: Every request gets a unique correlation ID
- **Timing Metrics**: Request duration is tracked and logged
- **Structured Logging**: All logs include request context
- **Response Headers**: Request ID and process time added to responses

### Usage

Request IDs are automatically added to all responses:

```bash
curl -i http://localhost:8000/api/v1/topology
```

Response headers:
```
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
X-Process-Time: 45.23
```

### Implementation

Located in `src/topdeck/common/middleware.py`:
- `RequestLoggingMiddleware`: Logs all requests/responses
- `RequestIDMiddleware`: Adds correlation IDs

## 2. Rate Limiting

### Features

- **Per-Client Rate Limiting**: Limits requests per IP address
- **Configurable Limits**: Adjustable via environment variables
- **Sliding Window**: Fair rate limiting using sliding window algorithm
- **Exempt Paths**: Health checks and metrics are exempt

### Configuration

In `.env`:
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

### Response

When rate limit is exceeded:
```json
{
  "detail": "Rate limit exceeded. Retry after 30 seconds."
}
```

Headers include:
```
Retry-After: 30
```

### Implementation

Located in `src/topdeck/common/rate_limiter.py`:
- `RateLimiter`: Core rate limiting logic
- `RateLimitMiddleware`: FastAPI middleware

## 3. Health Checks

### Endpoints

#### Basic Health Check
```bash
GET /health
```

Response:
```json
{
  "status": "healthy"
}
```

#### Detailed Health Check
```bash
GET /health/detailed
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-21T11:13:58.945Z",
  "components": {
    "neo4j": {
      "status": "healthy",
      "message": "Neo4j is connected and responsive",
      "response_time_ms": 12.34,
      "details": {
        "connected": true
      }
    },
    "redis": {
      "status": "healthy",
      "message": "Redis is connected and responsive",
      "response_time_ms": 5.67,
      "details": {
        "redis_version": "7.0.0",
        "uptime_seconds": 12345
      }
    },
    "rabbitmq": {
      "status": "healthy",
      "message": "RabbitMQ is connected and responsive",
      "response_time_ms": 8.90,
      "details": {
        "connected": true
      }
    }
  }
}
```

### Status Values

- `healthy`: All systems operational
- `degraded`: Some systems have issues
- `unhealthy`: Critical systems are down

### Implementation

Located in `src/topdeck/common/health.py`:
- `check_neo4j_health()`: Neo4j health check
- `check_redis_health()`: Redis health check
- `check_rabbitmq_health()`: RabbitMQ health check

## 4. Metrics & Monitoring

### Prometheus Endpoint

```bash
GET /metrics
```

Returns Prometheus-formatted metrics for scraping.

### Available Metrics

#### HTTP Metrics
- `topdeck_http_requests_total`: Total HTTP requests by method, endpoint, status
- `topdeck_http_request_duration_seconds`: Request duration histogram

#### Discovery Metrics
- `topdeck_discovery_runs_total`: Total discovery runs by cloud provider
- `topdeck_discovery_resources_found`: Resources found by type and provider
- `topdeck_discovery_duration_seconds`: Discovery run duration

#### Risk Analysis Metrics
- `topdeck_risk_assessments_total`: Total risk assessments performed
- `topdeck_risk_score_distribution`: Distribution of risk scores
- `topdeck_single_points_of_failure`: Number of SPOFs detected

#### Database Metrics
- `topdeck_neo4j_query_duration_seconds`: Neo4j query duration
- `topdeck_neo4j_queries_total`: Total Neo4j queries
- `topdeck_redis_operations_total`: Total Redis operations
- `topdeck_cache_hits_total`: Cache hit count
- `topdeck_cache_misses_total`: Cache miss count

### Example Prometheus Configuration

```yaml
scrape_configs:
  - job_name: 'topdeck'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
```

### Implementation

Located in `src/topdeck/common/metrics.py`

## 5. Input Validation

### Features

- **Reusable Validators**: Common validation functions
- **Consistent Error Format**: Standardized validation errors
- **Type Safety**: Strong typing for validated inputs

### Available Validators

```python
from topdeck.common.validators import (
    validate_resource_id,
    validate_cloud_provider,
    validate_resource_type,
    validate_subscription_id,
    validate_pagination,
    validate_risk_score,
    sanitize_string,
)
```

### Example Usage

```python
from fastapi import APIRouter
from topdeck.common.validators import validate_resource_id, validate_cloud_provider

router = APIRouter()

@router.get("/resources/{resource_id}")
async def get_resource(resource_id: str, provider: str):
    # Validate inputs
    resource_id = validate_resource_id(resource_id)
    provider = validate_cloud_provider(provider)
    
    # ... rest of endpoint logic
```

### Error Response

```json
{
  "field": "provider",
  "message": "Invalid cloud provider. Must be one of: azure, aws, gcp"
}
```

### Implementation

Located in `src/topdeck/common/validators.py`

## 6. Error Handling

### Features

- **Correlation IDs**: All errors include request ID
- **Structured Errors**: Consistent error format
- **Custom Exceptions**: Domain-specific error types
- **Error Logging**: Automatic error logging with context

### Error Response Format

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Resource with ID 'abc-123' not found",
    "field": null,
    "details": {
      "resource_type": "compute",
      "resource_id": "abc-123"
    }
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-10-21T11:13:58.945Z",
  "path": "/api/v1/resources/abc-123"
}
```

### Custom Exceptions

```python
from topdeck.common.errors import (
    ResourceNotFoundException,
    InvalidInputException,
    ServiceUnavailableException,
    RateLimitExceededException,
)

# Example usage
if not resource:
    raise ResourceNotFoundException("compute", resource_id)
```

### Implementation

Located in `src/topdeck/common/errors.py`:
- `TopDeckException`: Base exception class
- `ResourceNotFoundException`: 404 errors
- `InvalidInputException`: 422 errors
- `ServiceUnavailableException`: 503 errors
- `RateLimitExceededException`: 429 errors

## 7. API Versioning

### Features

- **URL-based Versioning**: Version in URL path
- **Backward Compatibility**: Support multiple versions
- **Version Headers**: Version info in response headers

### Usage

All API routes are versioned:

```bash
# Version 1 (current)
GET /api/v1/topology

# Future: Version 2
GET /api/v2/topology
```

### Response Headers

```
X-API-Version: v1
```

### Implementation

Located in `src/topdeck/common/versioning.py`:
- `APIVersion`: Version definitions
- `APIVersionMiddleware`: Version extraction and validation
- `VersionedAPIRoute`: Helper for versioned routes

### Example: Version-Specific Endpoint

```python
from topdeck.common.versioning import APIVersion, require_version

@router.get("/resource")
@require_version(APIVersion.V1)
async def get_resource_v1(request: Request):
    # V1-specific implementation
    pass
```

## Configuration

### Environment Variables

All enhancements can be configured via environment variables:

```bash
# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Request Configuration
REQUEST_TIMEOUT_SECONDS=30
MAX_REQUEST_SIZE_MB=10

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Testing

### Unit Tests

Tests are provided for all new utilities:

```bash
# Run tests for enhancements
pytest tests/common/test_middleware.py
pytest tests/common/test_rate_limiter.py
pytest tests/common/test_validators.py
```

### Integration Testing

Test the API with health checks and metrics:

```bash
# Health check
curl http://localhost:8000/health/detailed

# Metrics
curl http://localhost:8000/metrics

# Test rate limiting (run multiple times quickly)
for i in {1..70}; do curl http://localhost:8000/api/v1/topology; done
```

## Production Deployment

### Recommended Setup

1. **Enable rate limiting** to protect against abuse
2. **Configure Prometheus** to scrape `/metrics`
3. **Set up monitoring alerts** for health check failures
4. **Use request IDs** in support tickets for debugging
5. **Review logs regularly** for error patterns

### Prometheus Alerts Example

```yaml
groups:
  - name: topdeck
    rules:
      - alert: HighErrorRate
        expr: rate(topdeck_http_requests_total{status_code=~"5.."}[5m]) > 0.1
        annotations:
          summary: "High error rate detected"
      
      - alert: ServiceUnhealthy
        expr: up{job="topdeck"} == 0
        annotations:
          summary: "TopDeck API is down"
```

## Benefits

1. **Observability**: Full request tracing and logging
2. **Reliability**: Rate limiting and health checks
3. **Monitoring**: Comprehensive Prometheus metrics
4. **Debugging**: Correlation IDs and detailed error messages
5. **Maintainability**: Reusable validators and consistent patterns
6. **Production Ready**: All features needed for production deployment

## Migration Notes

### Backward Compatibility

All enhancements are backward compatible:
- Existing API routes still work
- No breaking changes to response formats
- Optional features can be disabled via configuration

### Gradual Adoption

Features can be adopted gradually:
1. Start with basic health checks and metrics
2. Enable rate limiting for public endpoints
3. Integrate Prometheus for monitoring
4. Use validators in new endpoints
5. Adopt versioning for new API features
