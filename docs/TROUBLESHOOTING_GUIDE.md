# Troubleshooting Features Guide

**Date**: November 25, 2024  
**Status**: Implemented - Ready for Use

## Overview

TopDeck's troubleshooting module provides advanced features designed to address critical market gaps in SRE tooling. Based on extensive market research, we've identified and implemented solutions for the most requested SRE capabilities.

### Features Implemented

1. **Log Correlation Engine** (Gap 1) - Most requested by SREs
2. **Error Context Aggregation** (Gap 2) - Reduces MTTR significantly
3. **Dependency Health Dashboard** (Gap 5) - Essential for incident triage

---

## 1. Log Correlation Engine

**Addresses Market Gap #1: Log Correlation Across Distributed Systems**

### Problem
- SREs spend 60% of troubleshooting time correlating logs across services
- No unified view of logs for a specific transaction
- Correlation IDs often missing or inconsistent

### Solution
- Automatic correlation ID detection and propagation tracking
- Cross-service log aggregation by transaction
- Timeline view showing logs from all affected services
- Integration with Loki, Elasticsearch, Azure Log Analytics

### API Endpoints

#### Correlate Logs by Correlation ID
```bash
curl "http://localhost:8000/api/v1/troubleshooting/logs/correlate/{correlation_id}?time_window_minutes=30"
```

**Response:**
```json
{
  "correlation_id": "req-abc-123",
  "start_time": "2024-11-25T10:00:00Z",
  "end_time": "2024-11-25T10:00:05Z",
  "entries": [
    {
      "timestamp": "2024-11-25T10:00:00Z",
      "message": "Request received",
      "level": "info",
      "service_id": "api-gateway",
      "service_name": "API Gateway",
      "correlation_id": "req-abc-123"
    },
    {
      "timestamp": "2024-11-25T10:00:01Z",
      "message": "Processing payment",
      "level": "info",
      "service_id": "payment-service",
      "service_name": "Payment Service",
      "correlation_id": "req-abc-123"
    }
  ],
  "services_involved": ["api-gateway", "payment-service", "db-service"],
  "error_count": 1,
  "warning_count": 2,
  "duration_ms": 5000
}
```

#### Trace Error Propagation
```bash
curl "http://localhost:8000/api/v1/troubleshooting/logs/error-chain/{error_id}?depth=5"
```

**Response:**
```json
{
  "error_id": "err-456",
  "root_cause_service": "db-service",
  "root_cause_error": "Connection timeout to database",
  "affected_services": ["db-service", "payment-service", "api-gateway"],
  "propagation_path": [
    {
      "service_id": "db-service",
      "error_message": "Connection timeout",
      "timestamp": "2024-11-25T10:00:00Z",
      "is_root_cause": true
    },
    {
      "service_id": "payment-service",
      "error_message": "Failed to process payment: database unavailable",
      "timestamp": "2024-11-25T10:00:00.500Z",
      "is_root_cause": false
    }
  ],
  "total_duration_ms": 500,
  "confidence_score": 0.85
}
```

#### Get Transaction Timeline
```bash
curl "http://localhost:8000/api/v1/troubleshooting/logs/transaction-timeline/{tx_id}"
```

**Response:**
```json
{
  "transaction_id": "tx-789",
  "start_time": "2024-11-25T10:00:00Z",
  "end_time": "2024-11-25T10:00:02Z",
  "total_duration_ms": 2000,
  "events": [
    {
      "timestamp": "2024-11-25T10:00:00Z",
      "service_id": "api-gateway",
      "event_type": "request",
      "message": "Incoming request from client"
    },
    {
      "timestamp": "2024-11-25T10:00:01Z",
      "service_id": "payment-service",
      "event_type": "log",
      "message": "Validating payment details"
    },
    {
      "timestamp": "2024-11-25T10:00:02Z",
      "service_id": "api-gateway",
      "event_type": "response",
      "message": "Request completed successfully"
    }
  ],
  "services_path": ["api-gateway", "payment-service", "api-gateway"],
  "success": true
}
```

---

## 2. Error Context Aggregation

**Addresses Market Gap #2: Error Context Aggregation**

### Problem
- When an error occurs, SREs must manually gather context
- Metrics, logs, traces, and configuration are in different tools
- Time-sensitive: context disappears after rotation/retention

### Solution
- Automatic context capture on error detection
- Aggregates: logs (±5 min), metrics (±15 min), traces, config state
- Topology snapshot at error time
- One-click access to all related data

### API Endpoints

#### Capture Error Context
```bash
curl -X POST "http://localhost:8000/api/v1/troubleshooting/context/capture" \
  -H "Content-Type: application/json" \
  -d '{
    "resource_id": "api-service-prod",
    "error_message": "Connection timeout to database",
    "error_type": "timeout",
    "severity": "error",
    "context_window_minutes": 5
  }'
```

**Response:**
```json
{
  "context_id": "ctx-abc-123",
  "error_time": "2024-11-25T10:30:00Z",
  "resource_id": "api-service-prod",
  "resource_name": "API Service",
  "error_message": "Connection timeout to database",
  "error_type": "timeout",
  "severity": "error",
  "snapshots": {
    "logs": {
      "context_type": "logs",
      "data": {
        "entries": [...],
        "error_count": 5,
        "warning_count": 12
      }
    },
    "metrics": {
      "context_type": "metrics",
      "data": [
        {"name": "cpu_usage", "value": 85.5},
        {"name": "memory_usage", "value": 78.2},
        {"name": "error_rate", "value": 5.5}
      ]
    },
    "topology": {
      "context_type": "topology",
      "data": {
        "upstream_dependencies": ["db-prod", "cache-prod"],
        "downstream_dependencies": ["web-app", "mobile-api"],
        "blast_radius_count": 15
      }
    },
    "dependencies": {
      "context_type": "dependencies",
      "data": [
        {
          "dependency_id": "db-prod",
          "status": "unhealthy",
          "latency_ms": 1500,
          "error_rate": 0.15
        }
      ]
    },
    "deployments": {
      "context_type": "deployments",
      "data": [
        {
          "deployment_id": "dep-456",
          "version": "v2.1.0",
          "deployed_at": "2024-11-25T09:00:00Z",
          "is_recent": true
        }
      ]
    }
  },
  "recommendations": [
    "Recent deployment detected (1 in last hour). Consider rollback if this is a new issue.",
    "Dependencies with issues: Production Database. Check dependency health before investigating service code.",
    "High blast radius (15 affected services). Prioritize resolution and consider notifying stakeholders."
  ],
  "created_at": "2024-11-25T10:30:05Z",
  "expires_at": "2024-11-28T10:30:05Z"
}
```

#### Retrieve Captured Context
```bash
curl "http://localhost:8000/api/v1/troubleshooting/context/{context_id}"
```

#### Get Contexts by Resource
```bash
curl "http://localhost:8000/api/v1/troubleshooting/context/by-resource/{resource_id}?limit=10"
```

---

## 3. Dependency Health Dashboard

**Addresses Market Gap #5: Service Dependency Health Dashboard**

### Problem
- During incidents, SREs need to quickly see which dependencies are healthy
- Current dashboards show individual service health, not dependency health
- No quick view of "is my database healthy? is my cache healthy?"

### Solution
- Real-time health status of all dependencies
- Latency/error rate to each dependency
- Connection pool status
- Historical dependency health trends

### API Endpoints

#### Get Dependency Health
```bash
curl "http://localhost:8000/api/v1/troubleshooting/dependencies/{resource_id}/health"
```

**Response:**
```json
{
  "resource_id": "api-service-prod",
  "resource_name": "API Service",
  "overall_health": "degraded",
  "overall_health_score": 72.5,
  "dependencies": [
    {
      "dependency_id": "db-prod",
      "dependency_name": "Production Database",
      "dependency_type": "database",
      "status": "healthy",
      "health_score": 95.0,
      "metrics": {
        "latency_p50_ms": 25.0,
        "latency_p95_ms": 75.0,
        "error_rate_percent": 0.1,
        "request_rate_per_sec": 500.0
      },
      "connection_pool": {
        "total_connections": 20,
        "active_connections": 8,
        "idle_connections": 12,
        "max_connections": 50,
        "utilization_percent": 40.0
      },
      "circuit_breaker_status": "closed",
      "anomalies": []
    },
    {
      "dependency_id": "cache-prod",
      "dependency_name": "Production Cache",
      "dependency_type": "cache",
      "status": "degraded",
      "health_score": 65.0,
      "metrics": {
        "latency_p95_ms": 250.0,
        "error_rate_percent": 2.5
      },
      "anomalies": [
        "Latency spike: 250ms (threshold: 200ms)",
        "Elevated error rate: 2.5% (threshold: 1%)"
      ]
    }
  ],
  "critical_issues": [
    "Production Cache: High latency (250ms)"
  ],
  "recommendations": [
    "Monitor Production Cache latency - consider caching or query optimization"
  ],
  "generated_at": "2024-11-25T10:35:00Z"
}
```

#### Get Dependency Timeline
```bash
curl "http://localhost:8000/api/v1/troubleshooting/dependencies/{resource_id}/timeline/{dependency_id}?hours=24"
```

**Response:**
```json
{
  "dependency_id": "db-prod",
  "dependency_name": "Production Database",
  "time_range_start": "2024-11-24T10:35:00Z",
  "time_range_end": "2024-11-25T10:35:00Z",
  "data_points": [
    {
      "timestamp": "2024-11-24T12:00:00Z",
      "health_score": 95.0,
      "latency_p95_ms": 50.0,
      "error_rate_percent": 0.1
    },
    {
      "timestamp": "2024-11-24T18:00:00Z",
      "health_score": 60.0,
      "latency_p95_ms": 500.0,
      "error_rate_percent": 5.0
    }
  ],
  "average_health_score": 85.0,
  "degraded_periods": [
    {
      "start": "2024-11-24T17:30:00Z",
      "end": "2024-11-24T19:00:00Z"
    }
  ]
}
```

#### Get Dashboard Summary
```bash
curl "http://localhost:8000/api/v1/troubleshooting/dependencies/dashboard"
```

**Response:**
```json
{
  "total_services": 25,
  "healthy_services": 20,
  "degraded_services": 4,
  "unhealthy_services": 1,
  "total_dependencies": 75,
  "healthy_dependencies": 68,
  "critical_alerts": [
    "payment-service is unhealthy: Database connection pool exhausted"
  ],
  "top_issues": [
    {
      "service": "payment-service",
      "issue": "Database connection pool exhausted (10 requests waiting)",
      "severity": "critical"
    },
    {
      "service": "api-gateway",
      "issue": "High latency to auth-service (450ms)",
      "severity": "warning"
    }
  ],
  "generated_at": "2024-11-25T10:40:00Z"
}
```

---

## Usage Examples

### Incident Response Workflow

1. **Alert triggers** - Service is experiencing errors

2. **Quick health check**:
```bash
# Check all dependencies immediately
curl "http://localhost:8000/api/v1/troubleshooting/dependencies/api-service/health"
```

3. **Capture context** (if needed for later analysis):
```bash
curl -X POST "http://localhost:8000/api/v1/troubleshooting/context/capture" \
  -d '{"resource_id": "api-service", "error_type": "timeout"}'
```

4. **Find correlation IDs** for specific errors:
```bash
curl "http://localhost:8000/api/v1/troubleshooting/logs/find-correlation-ids/api-service?error_pattern=timeout"
```

5. **Trace the error chain**:
```bash
curl "http://localhost:8000/api/v1/troubleshooting/logs/error-chain/{correlation_id}"
```

6. **Get full transaction timeline**:
```bash
curl "http://localhost:8000/api/v1/troubleshooting/logs/transaction-timeline/{correlation_id}"
```

### Post-Incident Analysis

1. **Review captured contexts**:
```bash
curl "http://localhost:8000/api/v1/troubleshooting/context/by-resource/api-service"
```

2. **Check historical dependency health**:
```bash
curl "http://localhost:8000/api/v1/troubleshooting/dependencies/api-service/timeline/db-prod?hours=72"
```

---

## Integration with Observability Stack

### Supported Log Platforms
- **Loki** - Primary log aggregation
- **Elasticsearch** - Full-text log search
- **Azure Log Analytics** - Azure-native logging

### Supported Metrics Platforms
- **Prometheus** - Metrics collection and querying

### Supported Trace Platforms
- **Tempo** - Distributed tracing (planned)

### Configuration

Set these environment variables to enable integrations:

```bash
# Loki
LOKI_URL=http://loki:3100

# Prometheus
PROMETHEUS_URL=http://prometheus:9090

# Elasticsearch
ELASTICSEARCH_URL=http://elasticsearch:9200
ELASTICSEARCH_INDEX_PATTERN=logs-*

# Neo4j (for topology)
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

---

## Benefits

### For SREs
1. **Faster Troubleshooting**: Reduce log correlation time from 15-30 min to < 2 min
2. **Complete Context**: All error context in one API call
3. **Dependency Visibility**: Instantly see which dependencies are affected
4. **Root Cause Identification**: Error chain analysis with confidence scoring

### For Operations
1. **Reduced MTTR**: Faster incident resolution
2. **Better Communication**: Clear dependency health for stakeholder updates
3. **Historical Analysis**: Context preserved for post-incident reviews

### For the Platform
1. **Market Differentiation**: Addresses gaps competitors don't
2. **SRE-Focused**: Built for real troubleshooting workflows
3. **Extensible**: Supports multiple observability platforms

---

## Related Documentation

- [ML-Based SRE Improvements](../ML_SRE_IMPROVEMENTS_SUMMARY.md) - Future ML enhancements
- [SRE Next Phase & Troubleshooting Gaps](SRE_NEXT_PHASE_AND_TROUBLESHOOTING_GAPS.md) - Complete roadmap
- [Live Diagnostics Guide](LIVE_DIAGNOSTICS_GUIDE.md) - Real-time monitoring
- [Error Replay Guide](ERROR_REPLAY_GUIDE.md) - "DVR for cloud errors"

---

**Document Version**: 1.0  
**Last Updated**: November 25, 2024  
**Author**: TopDeck Development Team
