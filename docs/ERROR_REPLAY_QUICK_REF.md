# Error Replay Quick Reference

Quick reference for TopDeck's Error Replay feature - the "DVR for cloud errors".

## Quick Start

```bash
# Start TopDeck API
make run

# Capture an error
curl -X POST http://localhost:8000/error-replay/capture \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Database timeout",
    "severity": "high",
    "source": "application",
    "resource_id": "db-001"
  }'

# Replay the error
curl http://localhost:8000/error-replay/replay/{error-id}
```

## Common Commands

### Capture Errors

```bash
# Basic error
curl -X POST http://localhost:8000/error-replay/capture \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Connection failed",
    "severity": "high",
    "source": "application"
  }'

# With full context
curl -X POST http://localhost:8000/error-replay/capture \
  -H "Content-Type: application/json" \
  -d '{
    "message": "API timeout",
    "severity": "critical",
    "source": "prometheus",
    "resource_id": "api-001",
    "resource_type": "api",
    "error_type": "timeout",
    "correlation_id": "req-123",
    "trace_id": "trace-456",
    "tags": {"env": "prod"}
  }'
```

### Search Errors

```bash
# By severity
curl -X POST http://localhost:8000/error-replay/search \
  -d '{"severity": "critical"}'

# By time range
curl -X POST http://localhost:8000/error-replay/search \
  -d '{
    "start_time": "2024-11-01T00:00:00Z",
    "end_time": "2024-11-01T23:59:59Z"
  }'

# By resource
curl -X POST http://localhost:8000/error-replay/search \
  -d '{"resource_id": "db-001"}'

# Multiple filters
curl -X POST http://localhost:8000/error-replay/search \
  -d '{
    "severity": "high",
    "resource_type": "database",
    "error_type": "timeout",
    "limit": 20
  }'
```

### Get Recent Errors

```bash
# Last 20 errors
curl http://localhost:8000/error-replay/recent

# Last 10 critical errors
curl http://localhost:8000/error-replay/recent?severity=critical&limit=10
```

### Get Errors by Resource

```bash
curl http://localhost:8000/error-replay/by-resource/db-001?limit=50
```

### Trace Cascading Failures

```bash
# Get all errors with same correlation ID
curl http://localhost:8000/error-replay/by-correlation/req-123
```

### Error Statistics

```bash
curl "http://localhost:8000/error-replay/statistics?start_time=2024-11-01T00:00:00Z&end_time=2024-11-02T00:00:00Z"
```

## Severity Levels

- **critical**: System down, data loss, security breach
- **high**: Major feature broken, significant degradation
- **medium**: Minor feature issue, acceptable impact
- **low**: Cosmetic issues, logging errors
- **info**: Informational events

## Error Sources

- **application**: Application code errors
- **prometheus**: Metrics-based errors
- **loki**: Log-based errors
- **tempo**: Trace-based errors
- **elasticsearch**: Elasticsearch log errors
- **azure_log_analytics**: Azure log errors
- **manual**: Manually reported errors

## Python SDK Usage

```python
from topdeck.monitoring.error_replay import (
    ErrorReplayService,
    ErrorSeverity,
    ErrorSource,
)
from topdeck.storage.neo4j_client import Neo4jClient

# Initialize service
neo4j_client = Neo4jClient(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="password"
)

service = ErrorReplayService(
    neo4j_client=neo4j_client,
    prometheus_url="http://prometheus:9090",
    loki_url="http://loki:3100"
)

# Capture error
error = await service.capture_error(
    message="Database timeout",
    severity=ErrorSeverity.HIGH,
    source=ErrorSource.APPLICATION,
    resource_id="db-001",
    correlation_id="req-123"
)

# Replay error
result = await service.replay_error(error.error_id)

# Search errors
from topdeck.monitoring.error_replay import ErrorSearchFilter

filter = ErrorSearchFilter(
    severity=ErrorSeverity.CRITICAL,
    resource_type="database",
    limit=20
)
errors = await service.search_errors(filter)
```

## Integration with Application Code

### Python

```python
# Add to error handling
try:
    dangerous_operation()
except Exception as e:
    await error_replay_service.capture_error(
        message=str(e),
        severity=ErrorSeverity.HIGH,
        source=ErrorSource.APPLICATION,
        resource_id=resource_id,
        stack_trace=traceback.format_exc(),
        correlation_id=context.correlation_id
    )
    raise
```

### JavaScript/Node.js

```javascript
// Global error handler
process.on('uncaughtException', async (error) => {
  await fetch('http://topdeck:8000/error-replay/capture', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: error.message,
      severity: 'high',
      source: 'application',
      stack_trace: error.stack,
      correlation_id: getCorrelationId()
    })
  });
});
```

## Response Examples

### Capture Response

```json
{
  "error_id": "e8f7a3b9c2d1f456",
  "timestamp": "2024-11-01T14:30:00Z",
  "severity": "high",
  "source": "application",
  "resource_id": "db-001",
  "message": "Database timeout",
  "logs": [...],
  "metrics": {...},
  "topology_snapshot": {...},
  "related_errors": ["error-123"],
  "affected_resources": ["api-001"]
}
```

### Replay Response

```json
{
  "error_id": "e8f7a3b9c2d1f456",
  "timeline": [
    {
      "timestamp": "2024-11-01T14:25:00Z",
      "type": "deployment",
      "message": "Deployment v2.1.0"
    },
    {
      "timestamp": "2024-11-01T14:30:00Z",
      "type": "error",
      "message": "Database timeout"
    }
  ],
  "root_cause_analysis": {
    "primary_cause": "Recent deployment",
    "confidence": 0.7
  },
  "recommendations": [
    "Consider rolling back the recent deployment",
    "Check resource health"
  ]
}
```

### Statistics Response

```json
{
  "total_errors": 342,
  "severities": ["critical", "high", "medium"],
  "sources": ["application", "prometheus"],
  "resource_types": ["database", "api"],
  "error_types": ["timeout", "connection_error"]
}
```

## Best Practices

1. **Always use correlation IDs** for tracing across services
2. **Include resource context** (resource_id, resource_type)
3. **Use appropriate severity levels** based on impact
4. **Add custom tags** for better filtering
5. **Integrate with error handlers** to capture automatically
6. **Review replays regularly** to identify patterns
7. **Follow recommendations** to prevent recurrence

## Troubleshooting

### No logs in snapshot
- Check observability platform URLs in config
- Verify resource labels match
- Ensure time sync between services

### Root cause shows "Unknown"
- Add more observability platforms
- Track deployments in Neo4j
- Increase log retention

### Search returns no results
- Use UTC timestamps
- Check filter criteria (exact matches)
- Verify errors were captured

## Configuration

Add to `.env`:

```bash
# Observability platforms
PROMETHEUS_URL=http://prometheus:9090
LOKI_URL=http://loki:3100
TEMPO_URL=http://tempo:3200
ELASTICSEARCH_URL=https://elasticsearch:9200
ELASTICSEARCH_API_KEY=your-key
AZURE_LOG_ANALYTICS_WORKSPACE_ID=workspace-id
```

## Related Documentation

- **[Complete Guide](ERROR_REPLAY_GUIDE.md)** - Full documentation
- **[Monitoring Integration](MONITORING_INTEGRATION.md)** - Setup observability
- **[Risk Analysis](ENHANCED_RISK_ANALYSIS.md)** - Correlate with risk
- **[API Reference](../README.md)** - Complete API docs

## Support

- Issues: https://github.com/MattVerwey/TopDeck/issues
- Discussions: https://github.com/MattVerwey/TopDeck/discussions
- Demo: `python examples/error_replay_demo.py`
