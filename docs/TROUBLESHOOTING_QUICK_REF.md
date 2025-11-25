# Troubleshooting Quick Reference

## Log Correlation

### Correlate logs by correlation ID
```bash
curl "http://localhost:8000/api/v1/troubleshooting/logs/correlate/{correlation_id}"
```

### Trace error propagation chain
```bash
curl "http://localhost:8000/api/v1/troubleshooting/logs/error-chain/{error_id}"
```

### Get transaction timeline
```bash
curl "http://localhost:8000/api/v1/troubleshooting/logs/transaction-timeline/{tx_id}"
```

### Find correlation IDs for errors
```bash
curl "http://localhost:8000/api/v1/troubleshooting/logs/find-correlation-ids/{resource_id}?error_pattern=timeout"
```

## Error Context

### Capture error context
```bash
curl -X POST "http://localhost:8000/api/v1/troubleshooting/context/capture" \
  -H "Content-Type: application/json" \
  -d '{
    "resource_id": "api-service",
    "error_message": "Connection timeout",
    "error_type": "timeout",
    "severity": "error"
  }'
```

### Get captured context
```bash
curl "http://localhost:8000/api/v1/troubleshooting/context/{context_id}"
```

### Get contexts by resource
```bash
curl "http://localhost:8000/api/v1/troubleshooting/context/by-resource/{resource_id}"
```

## Dependency Health

### Get dependency health for a service
```bash
curl "http://localhost:8000/api/v1/troubleshooting/dependencies/{resource_id}/health"
```

### Get dependency timeline (last 24h)
```bash
curl "http://localhost:8000/api/v1/troubleshooting/dependencies/{resource_id}/timeline/{dependency_id}?hours=24"
```

### Get dashboard summary
```bash
curl "http://localhost:8000/api/v1/troubleshooting/dependencies/dashboard"
```

## Incident Response Workflow

1. Check dependency health: `GET /troubleshooting/dependencies/{id}/health`
2. Capture error context: `POST /troubleshooting/context/capture`
3. Find correlation IDs: `GET /troubleshooting/logs/find-correlation-ids/{id}`
4. Trace error chain: `GET /troubleshooting/logs/error-chain/{id}`
5. Get transaction timeline: `GET /troubleshooting/logs/transaction-timeline/{id}`

## Health Status Meanings

| Status | Score | Description |
|--------|-------|-------------|
| `healthy` | ≥80 | All metrics within normal range |
| `degraded` | 50-79 | Some metrics elevated, needs monitoring |
| `unhealthy` | <50 | Critical issues, requires attention |

## Common Anomalies

- **Latency spike**: P95 > 500ms
- **High error rate**: Error rate > 5%
- **Pool exhaustion**: Utilization > 90% or waiting requests
- **Circuit breaker open**: Service is being protected
