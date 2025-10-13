# Monitoring API Documentation

## Overview

The Monitoring API provides endpoints for retrieving metrics and logs from observability platforms (Prometheus, Loki, Grafana). These endpoints enable performance monitoring, bottleneck detection, and failure analysis in microservice architectures.

## Base URL

```
/api/v1/monitoring
```

## Endpoints

### GET /api/v1/monitoring/resources/{resource_id}/metrics

Get performance metrics for a specific resource from Prometheus.

**Path Parameters:**
- `resource_id` (required, string): Resource identifier

**Query Parameters:**
- `resource_type` (required, string): Type of resource (`pod`, `service`, `database`, `load_balancer`, etc.)
- `duration_hours` (optional, integer, 1-24, default=1): Duration in hours to query

**Response:**
```json
{
  "resource_id": "web-app-pod",
  "resource_type": "pod",
  "metrics": {
    "cpu_usage": {
      "metric_name": "cpu_usage",
      "labels": {"pod": "web-app-pod"},
      "values": [
        {
          "timestamp": "2025-10-13T10:00:00Z",
          "value": 0.45,
          "labels": {"pod": "web-app-pod"}
        }
      ]
    },
    "latency_p95": {
      "metric_name": "latency_p95",
      "labels": {"pod": "web-app-pod"},
      "values": [
        {
          "timestamp": "2025-10-13T10:00:00Z",
          "value": 0.250,
          "labels": {"pod": "web-app-pod"}
        }
      ]
    }
  },
  "anomalies": ["High latency detected: 1500ms"],
  "health_score": 85.5
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/monitoring/resources/web-app-pod/metrics?resource_type=pod&duration_hours=2"
```

---

### GET /api/v1/monitoring/flows/{flow_id}/bottlenecks

Detect performance bottlenecks in a data flow.

**Path Parameters:**
- `flow_id` (required, string): Flow identifier

**Query Parameters:**
- `flow_path` (required, array of strings): List of resource IDs in the flow path

**Response:**
```json
[
  {
    "resource_id": "api-service-pod",
    "type": "high_latency",
    "severity": "high",
    "details": "P95 latency: 1500.00ms"
  },
  {
    "resource_id": "database-server",
    "type": "cpu_saturation",
    "severity": "high",
    "details": "CPU usage: 95.00%"
  }
]
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/monitoring/flows/flow-123/bottlenecks?flow_path=lb-1&flow_path=api-1&flow_path=db-1"
```

---

### GET /api/v1/monitoring/resources/{resource_id}/errors

Get error analysis for a specific resource from Loki logs.

**Path Parameters:**
- `resource_id` (required, string): Resource identifier

**Query Parameters:**
- `duration_hours` (optional, integer, 1-24, default=1): Duration in hours to analyze

**Response:**
```json
{
  "resource_id": "api-service-pod",
  "error_count": 245,
  "error_types": {
    "TimeoutError": 120,
    "DatabaseError": 75,
    "ConnectionError": 50
  },
  "recent_errors": [
    {
      "timestamp": "2025-10-13T10:45:00Z",
      "message": "ERROR: Database connection timeout after 30s",
      "labels": {"resource_id": "api-service-pod", "level": "error"},
      "level": "error"
    }
  ],
  "error_rate": 4.08
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/monitoring/resources/api-service-pod/errors?duration_hours=2"
```

---

### GET /api/v1/monitoring/flows/{flow_id}/failures

Find the failure point in a data flow.

**Path Parameters:**
- `flow_id` (required, string): Flow identifier

**Query Parameters:**
- `flow_path` (required, array of strings): List of resource IDs in the flow path
- `duration_minutes` (optional, integer, 5-120, default=30): Duration in minutes to analyze

**Response:**
```json
{
  "resource_id": "database-server",
  "error_rate": 8.5,
  "error_count": 255,
  "error_types": {
    "DatabaseError": 180,
    "TimeoutError": 75
  },
  "recent_errors": [
    {
      "timestamp": "2025-10-13T10:45:00Z",
      "message": "CRITICAL: Deadlock detected on Orders table",
      "level": "fatal"
    }
  ]
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/monitoring/flows/flow-123/failures?flow_path=lb-1&flow_path=api-1&flow_path=db-1&duration_minutes=60"
```

---

### GET /api/v1/monitoring/health

Get health status of monitoring integrations.

**Response:**
```json
{
  "prometheus": {
    "status": "healthy",
    "url": "http://prometheus:9090"
  },
  "loki": {
    "status": "healthy",
    "url": "http://loki:3100"
  }
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/monitoring/health"
```

---

## Integration with Observability Platforms

### Prometheus

TopDeck integrates with Prometheus to collect performance metrics:

- **CPU Usage**: Container CPU utilization
- **Memory Usage**: Container memory consumption
- **Request Rate**: HTTP requests per second
- **Error Rate**: Percentage of failed requests
- **Latency**: P95/P99 response times
- **Database Metrics**: Query duration, connections, deadlocks

### Loki

TopDeck integrates with Loki to collect and analyze logs:

- **Error Logs**: Errors, exceptions, fatal errors
- **Log Levels**: Fatal, error, warn, info, debug
- **Error Types**: Timeout, connection, database, authentication, etc.
- **Error Correlation**: Trace errors across resources in a flow

### Grafana

While not directly queried by the API, Grafana can be used to:

- Visualize metrics from Prometheus
- Display logs from Loki
- Create dashboards for topology and performance
- Set up alerts based on thresholds

---

## Use Cases

### Monitor Resource Performance

Get metrics for a specific pod:

```bash
curl "http://localhost:8000/api/v1/monitoring/resources/my-app-pod/metrics?resource_type=pod&duration_hours=1"
```

### Detect Bottlenecks in Request Flow

Find performance bottlenecks in a request path:

```bash
curl "http://localhost:8000/api/v1/monitoring/flows/request-flow/bottlenecks?flow_path=lb&flow_path=gateway&flow_path=api&flow_path=database"
```

### Pinpoint Failure in Microservices

Identify which service is failing:

```bash
curl "http://localhost:8000/api/v1/monitoring/flows/user-flow/failures?flow_path=frontend&flow_path=api&flow_path=auth&flow_path=database"
```

### Analyze Error Patterns

Get error statistics for troubleshooting:

```bash
curl "http://localhost:8000/api/v1/monitoring/resources/payment-service/errors?duration_hours=6"
```

---

## Configuration

Set the following environment variables to configure monitoring integrations:

```bash
PROMETHEUS_URL=http://prometheus:9090
LOKI_URL=http://loki:3100
GRAFANA_URL=http://grafana:3000
```

---

## Next Steps

1. Add real-time streaming with WebSockets
2. Implement alert correlation
3. Add predictive analysis using historical data
4. Support for additional platforms (Datadog, New Relic, etc.)
