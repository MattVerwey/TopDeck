# Error Replay Guide

## Overview

The Error Replay feature in TopDeck acts as a **"DVR for cloud errors"** - it captures, stores, and replays errors with full context to help you understand what went wrong and why.

When an error occurs, Error Replay automatically:
- 📸 **Captures a snapshot** of the error with full context
- 🔍 **Collects surrounding logs** from Loki/Elasticsearch/Azure Log Analytics
- 📊 **Gathers metrics** at the time of error from Prometheus
- 🔗 **Retrieves distributed traces** from Tempo
- 🗺️ **Records topology state** from Neo4j
- 🚀 **Tracks recent deployments** and changes
- 🔗 **Identifies related errors** and affected resources

This allows you to "replay" any error to debug what happened, understand the root cause, and prevent future occurrences.

## Key Features

### 1. Automatic Context Collection
Error Replay automatically collects rich context when an error occurs:
- **Logs**: 5-minute window of logs before and after the error
- **Metrics**: Resource metrics (CPU, memory, latency) at error time
- **Traces**: Distributed traces showing request flow
- **Topology**: Network topology and resource dependencies
- **Deployments**: Recent deployment history
- **Related Errors**: Other errors in the same time window

### 2. Time-Travel Debugging
Replay any past error to see:
- Timeline of events leading to the error
- System state at the time of error
- What changed before the error
- How the error propagated through dependencies

### 3. Root Cause Analysis
Automated analysis identifies:
- Primary cause of the error
- Contributing factors
- Confidence level
- Related topology changes

### 4. Actionable Recommendations
Get specific recommendations to fix the issue:
- Deployment rollback suggestions
- Configuration changes
- Escalation procedures
- Circuit breaker activation

## Quick Start

### Prerequisites
- TopDeck API running (`make run`)
- At least one observability platform configured (Prometheus, Loki, Tempo, etc.)
- Neo4j running (`make docker-up`)

### Basic Usage

#### 1. Capture an Error

```bash
curl -X POST http://localhost:8000/error-replay/capture \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Database connection timeout",
    "severity": "high",
    "source": "application",
    "resource_id": "sql-db-prod-001",
    "resource_type": "database",
    "error_type": "connection_timeout",
    "correlation_id": "abc-123-def",
    "tags": {
      "environment": "production",
      "region": "us-west-2"
    }
  }'
```

Response:
```json
{
  "error_id": "e8f7a3b9c2d1f456",
  "timestamp": "2024-11-01T14:30:00Z",
  "severity": "high",
  "source": "application",
  "resource_id": "sql-db-prod-001",
  "message": "Database connection timeout",
  "logs": [...],
  "metrics": {...},
  "topology_snapshot": {...},
  "related_errors": ["e8f7a3b9c2d1f455"],
  "affected_resources": ["api-prod-001", "api-prod-002"]
}
```

#### 2. Replay an Error

```bash
curl http://localhost:8000/error-replay/replay/e8f7a3b9c2d1f456
```

Response:
```json
{
  "error_id": "e8f7a3b9c2d1f456",
  "original_timestamp": "2024-11-01T14:30:00Z",
  "error_snapshot": {...},
  "timeline": [
    {
      "timestamp": "2024-11-01T14:25:00Z",
      "type": "deployment",
      "message": "Deployment v2.1.0"
    },
    {
      "timestamp": "2024-11-01T14:29:55Z",
      "type": "log",
      "message": "Connection pool exhausted",
      "level": "WARN"
    },
    {
      "timestamp": "2024-11-01T14:30:00Z",
      "type": "error",
      "message": "Database connection timeout",
      "severity": "high"
    }
  ],
  "root_cause_analysis": {
    "primary_cause": "Recent deployment",
    "contributing_factors": [
      "Deployment occurred 1 time(s) in last 24h",
      "Detected 2 metric anomalies"
    ],
    "confidence": 0.7
  },
  "recommendations": [
    "Consider rolling back the recent deployment",
    "Review deployment logs and changes",
    "Check resource health and dependencies"
  ],
  "related_changes": [...]
}
```

#### 3. Search for Errors

```bash
# By severity
curl -X POST http://localhost:8000/error-replay/search \
  -H "Content-Type: application/json" \
  -d '{"severity": "critical", "limit": 10}'

# By resource
curl http://localhost:8000/error-replay/by-resource/sql-db-prod-001?limit=20

# By time range
curl -X POST http://localhost:8000/error-replay/search \
  -H "Content-Type: application/json" \
  -d '{
    "start_time": "2024-11-01T00:00:00Z",
    "end_time": "2024-11-01T23:59:59Z",
    "limit": 50
  }'

# By correlation ID (trace related errors)
curl http://localhost:8000/error-replay/by-correlation/abc-123-def?limit=50
```

#### 4. Get Error Statistics

```bash
curl "http://localhost:8000/error-replay/statistics?start_time=2024-11-01T00:00:00Z&end_time=2024-11-01T23:59:59Z"
```

Response:
```json
{
  "total_errors": 342,
  "severities": ["critical", "high", "medium", "low"],
  "sources": ["application", "prometheus", "loki"],
  "resource_types": ["database", "api", "cache"],
  "error_types": ["connection_timeout", "high_latency", "out_of_memory"],
  "time_range": {
    "start": "2024-11-01T00:00:00Z",
    "end": "2024-11-01T23:59:59Z"
  }
}
```

#### 5. Get Recent Errors

```bash
# Last 20 errors
curl http://localhost:8000/error-replay/recent?limit=20

# Recent critical errors only
curl http://localhost:8000/error-replay/recent?severity=critical&limit=10
```

## API Reference

### POST /error-replay/capture
Capture an error with full context.

**Request Body:**
```typescript
{
  message: string;              // Required: Error message
  severity: "critical" | "high" | "medium" | "low" | "info";  // Required
  source: "prometheus" | "loki" | "tempo" | "elasticsearch" | "azure_log_analytics" | "application" | "manual";  // Required
  resource_id?: string;         // Optional: Affected resource ID
  resource_type?: string;       // Optional: Resource type
  error_type?: string;          // Optional: Error category
  stack_trace?: string;         // Optional: Stack trace
  correlation_id?: string;      // Optional: Correlation ID
  trace_id?: string;            // Optional: Distributed trace ID
  span_id?: string;             // Optional: Span ID
  tags?: { [key: string]: string };  // Optional: Custom tags
  metadata?: { [key: string]: any }; // Optional: Additional metadata
}
```

**Response:** `ErrorSnapshot` (201 Created)

### GET /error-replay/replay/{error_id}
Replay an error to understand what happened.

**Path Parameters:**
- `error_id`: Error ID to replay

**Response:** `ErrorReplayResult` (200 OK)

### POST /error-replay/search
Search for errors matching criteria.

**Request Body:**
```typescript
{
  start_time?: string;          // ISO 8601 timestamp
  end_time?: string;            // ISO 8601 timestamp
  severity?: "critical" | "high" | "medium" | "low" | "info";
  source?: string;              // Error source
  resource_id?: string;         // Resource ID
  resource_type?: string;       // Resource type
  error_type?: string;          // Error type
  correlation_id?: string;      // Correlation ID
  trace_id?: string;            // Trace ID
  tags?: { [key: string]: string };
  limit?: number;               // Default: 100, Max: 1000
}
```

**Response:** `ErrorSnapshot[]` (200 OK)

### GET /error-replay/statistics
Get error statistics for a time range.

**Query Parameters:**
- `start_time`: Start time (ISO 8601, required)
- `end_time`: End time (ISO 8601, required)

**Response:** `ErrorStatistics` (200 OK)

### GET /error-replay/recent
Get recent errors (last 24 hours).

**Query Parameters:**
- `limit`: Number of errors (default: 20, max: 100)
- `severity`: Filter by severity (optional)

**Response:** `ErrorSnapshot[]` (200 OK)

### GET /error-replay/by-resource/{resource_id}
Get errors for a specific resource.

**Path Parameters:**
- `resource_id`: Resource ID

**Query Parameters:**
- `limit`: Number of errors (default: 50, max: 500)

**Response:** `ErrorSnapshot[]` (200 OK)

### GET /error-replay/by-correlation/{correlation_id}
Get errors for a correlation ID.

**Path Parameters:**
- `correlation_id`: Correlation ID

**Query Parameters:**
- `limit`: Number of errors (default: 50, max: 500)

**Response:** `ErrorSnapshot[]` (200 OK)

## Integration with Observability Platforms

### Prometheus
Error Replay collects metrics at the time of error:
- CPU usage
- Memory usage
- Request latency (p50, p95, p99)
- Error rates
- Request rates

**Configuration:**
```bash
# .env
PROMETHEUS_URL=http://prometheus:9090
```

### Loki
Collects logs in a 5-minute window around the error:
- Application logs
- Error messages
- Warning signs

**Configuration:**
```bash
# .env
LOKI_URL=http://loki:3100
```

### Tempo
Retrieves distributed traces for request flow:
- Service interactions
- Request path
- Span timings

**Configuration:**
```bash
# .env
TEMPO_URL=http://tempo:3200
```

### Elasticsearch
Alternative log aggregation platform:
- Application logs
- Infrastructure logs
- Security logs

**Configuration:**
```bash
# .env
ELASTICSEARCH_URL=https://elasticsearch.example.com:9200
ELASTICSEARCH_API_KEY=your-api-key
ELASTICSEARCH_INDEX_PATTERN=logs-*
```

### Azure Log Analytics
Azure-native log platform:
- Application Insights logs
- Resource logs
- Activity logs

**Configuration:**
```bash
# .env
AZURE_LOG_ANALYTICS_WORKSPACE_ID=your-workspace-id
```

## Use Cases

### 1. Debug Production Errors
When an error occurs in production:
1. Error is automatically captured with full context
2. Replay the error to see the timeline of events
3. Review root cause analysis
4. Follow recommendations to fix

### 2. Investigate Cascading Failures
When multiple services fail:
1. Search for errors by correlation ID
2. See how errors propagated through dependencies
3. Identify the initial failure point
4. Understand the blast radius

### 3. Post-Mortem Analysis
After an incident:
1. Search for errors in the incident time range
2. Replay key errors to understand the sequence
3. Generate timeline for post-mortem document
4. Identify systemic issues

### 4. Performance Degradation
When performance degrades:
1. Capture performance-related errors
2. Review metrics at time of degradation
3. Correlate with recent deployments
4. Identify bottlenecks

### 5. Deployment Validation
After a deployment:
1. Monitor for new errors
2. Compare error rates before/after
3. Quick rollback if errors spike
4. Validate deployment success

## Best Practices

### 1. Use Correlation IDs
Always include correlation IDs to trace errors across services:
```javascript
// Application code
const correlationId = generateCorrelationId();
logContext.correlationId = correlationId;

// When capturing error
await captureError({
  message: "Error occurred",
  correlation_id: correlationId,
  ...
});
```

### 2. Include Resource Context
Always specify resource_id and resource_type:
```javascript
await captureError({
  message: "Database timeout",
  resource_id: "sql-db-prod-001",
  resource_type: "database",
  ...
});
```

### 3. Use Appropriate Severity
- **Critical**: System down, data loss, security breach
- **High**: Major feature broken, significant performance degradation
- **Medium**: Minor feature issue, acceptable performance impact
- **Low**: Cosmetic issues, logging errors
- **Info**: Informational events

### 4. Add Custom Tags
Use tags for filtering and grouping:
```javascript
await captureError({
  message: "Error occurred",
  tags: {
    environment: "production",
    region: "us-west-2",
    team: "platform",
    service: "api-gateway"
  },
  ...
});
```

### 5. Automate Error Capture
Integrate with your application's error handling:
```python
# Python example
try:
    dangerous_operation()
except Exception as e:
    await error_replay_service.capture_error(
        message=str(e),
        severity=ErrorSeverity.HIGH,
        source=ErrorSource.APPLICATION,
        resource_id=resource_id,
        stack_trace=traceback.format_exc(),
        correlation_id=context.correlation_id,
    )
    raise
```

```javascript
// Node.js example
process.on('uncaughtException', async (error) => {
  await fetch('http://topdeck/error-replay/capture', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: error.message,
      severity: 'high',
      source: 'application',
      stack_trace: error.stack,
      correlation_id: context.correlationId
    })
  });
});
```

## Troubleshooting

### Error snapshots have no logs
- Verify observability platform URLs are configured
- Check that resources have proper labels/tags for matching
- Ensure time synchronization between services

### Root cause analysis shows "Unknown"
- This is normal when there's insufficient context
- Ensure recent deployments are tracked in Neo4j
- Add more observability platforms for better context

### Search returns no results
- Verify time ranges (use UTC timestamps)
- Check filter criteria (exact matches required)
- Ensure errors were captured (check Neo4j)

### Performance concerns
- Error Replay uses Neo4j for storage
- Old errors can be archived/deleted using Cypher queries
- Consider data retention policies (e.g., 90 days)

## Advanced Usage

### Custom Error Sources
You can create custom error sources by extending the `ErrorSource` enum and integrating with your own monitoring tools.

### Error Enrichment
Errors are automatically enriched with context, but you can add custom enrichment by extending the `ErrorReplayService` class.

### Webhook Integration
Integrate with alerting systems to automatically capture errors:
```python
# Example webhook handler
@app.post("/webhook/errors")
async def error_webhook(alert: dict):
    await error_replay_service.capture_error(
        message=alert["message"],
        severity=map_severity(alert["severity"]),
        source=ErrorSource.PROMETHEUS,
        resource_id=alert["labels"]["resource"],
        tags=alert["labels"]
    )
```

## Monitoring Error Replay

Monitor the Error Replay feature itself:
- Error capture rate
- Storage usage in Neo4j
- Query performance
- Context collection success rate

## Next Steps

- **[Monitoring Integration Guide](docs/MONITORING_INTEGRATION.md)** - Setup observability platforms
- **[Risk Analysis Guide](docs/ENHANCED_RISK_ANALYSIS.md)** - Correlate errors with risk
- **[Topology Analysis Guide](docs/ENHANCED_TOPOLOGY_ANALYSIS.md)** - Understand error propagation

## Support

For issues or questions:
- Create an issue: https://github.com/MattVerwey/TopDeck/issues
- Discussions: https://github.com/MattVerwey/TopDeck/discussions
