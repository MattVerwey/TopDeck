# Observability Architecture

TopDeck integrates with multiple observability platforms to provide comprehensive monitoring, tracing, and logging capabilities.

## Three Pillars of Observability

### 1. Metrics (Prometheus)
**Purpose**: Performance indicators and resource utilization

**What it stores**:
- CPU usage
- Memory consumption
- Request rates
- Error rates
- Latency percentiles (p50, p95, p99)
- Database connections
- Queue depths

**Use cases**:
- Monitor resource health
- Detect performance bottlenecks
- Alert on anomalies
- Track SLA metrics

**Integration**: `PROMETHEUS_URL=http://localhost:9090`

**Endpoints**:
- `GET /api/v1/monitoring/resources/{resource_id}/metrics` - Get metrics for a resource
- `GET /api/v1/monitoring/flows/bottlenecks` - Detect performance bottlenecks

### 2. Traces (Tempo)
**Purpose**: Distributed transaction flows and service interactions

**What it stores**:
- Trace IDs (unique identifiers for requests)
- Spans (individual operations within a trace)
- Service-to-service calls
- Request timing and latency
- Error propagation paths

**Use cases**:
- Trace requests across microservices
- Understand service dependencies
- Debug performance issues
- Analyze error propagation
- Identify slow operations

**Integration**: `TEMPO_URL=http://localhost:3200`

**Endpoints**:
- `GET /api/v1/monitoring/traces/{trace_id}` - Get a specific trace
- `GET /api/v1/monitoring/resources/{resource_id}/traces` - Get traces for a resource

**Important**: Trace IDs are stored in Tempo, NOT Prometheus. Prometheus is for metrics only.

### 3. Logs (Loki / Elasticsearch / Azure Log Analytics)
**Purpose**: Detailed event records and error messages

**What it stores**:
- Application logs
- Error messages and stack traces
- Audit events
- Debug information
- Correlation IDs

**Use cases**:
- Debug application issues
- Search for specific errors
- Correlate logs with traces
- Audit user actions
- Root cause analysis

**Integration**:
- `LOKI_URL=http://localhost:3100` (Kubernetes/container logs)
- `ELASTICSEARCH_URL=https://elasticsearch:9200` (Elastic Stack)
- `AZURE_LOG_ANALYTICS_WORKSPACE_ID=xxx` (Azure-native)

**Endpoints**:
- `GET /api/v1/monitoring/resources/{resource_id}/errors` - Get error analysis
- `GET /api/v1/monitoring/flows/{flow_id}/failures` - Find failure points
- `GET /api/v1/monitoring/flows/trace/{correlation_id}` - Trace transactions via logs

## Architecture Flow

```
Application Request
       |
       v
   [Service A]
       |
       ├──> Metrics → Prometheus (CPU, memory, latency)
       ├──> Traces → Tempo (trace_id, spans)
       └──> Logs → Loki/Elasticsearch (error messages)
       |
       v
   [Service B]
       |
       ├──> Metrics → Prometheus
       ├──> Traces → Tempo (same trace_id, new span)
       └──> Logs → Loki/Elasticsearch
```

## OpenTelemetry Integration

TopDeck uses OpenTelemetry as the instrumentation standard:

- **Metrics**: Exposed in Prometheus format
- **Traces**: Sent to Tempo via OTLP (port 4317 gRPC or 4318 HTTP)
- **Logs**: Structured logs with correlation IDs

## Configuration Example

```bash
# .env file
PROMETHEUS_URL=http://prometheus:9090    # Metrics
TEMPO_URL=http://tempo:3200              # Traces (trace IDs)
LOKI_URL=http://loki:3100                # Logs
```

## Common Patterns

### Pattern 1: Debug Slow Request
1. Check **metrics** in Prometheus → Identify high latency
2. Get **trace** from Tempo → See which service is slow
3. Query **logs** from Loki → Find error details

### Pattern 2: Analyze Service Dependency
1. Get **traces** from Tempo → Build service call graph
2. Check **metrics** from Prometheus → Add performance data
3. Validate with **topology** from Neo4j → Compare actual vs. expected

### Pattern 3: Root Cause Analysis
1. Check **logs** for errors → Find correlation_id or trace_id
2. Get **trace** from Tempo → See full request flow
3. Check **metrics** around that time → Identify resource issues

## External Observability Stack

TopDeck integrates with your existing observability infrastructure:

- **Prometheus**: Your existing Prometheus instance for metrics
- **Tempo**: Your existing Tempo instance for distributed tracing (e.g., from Grafana Cloud)
- **Loki**: Your existing Loki instance for logs

Configure TopDeck to connect to these services via environment variables:

```bash
PROMETHEUS_URL=http://your-prometheus:9090
TEMPO_URL=http://your-tempo:3200
LOKI_URL=http://your-loki:3100
```

## Best Practices

1. **Use the right tool for the job**:
   - Prometheus for "What is the current state?"
   - Tempo for "How did we get here?"
   - Loki for "What exactly happened?"

2. **Correlation**:
   - Use trace_id in logs
   - Add resource_id to traces
   - Link metrics with traces via labels

3. **Retention**:
   - Metrics: 15-30 days (high cardinality)
   - Traces: 7-14 days (high volume)
   - Logs: 30-90 days (detailed information)

4. **Sampling**:
   - Metrics: Always collect (low overhead)
   - Traces: Sample in production (e.g., 10%)
   - Logs: Filter noise, keep errors

## Health Check

Check the status of all observability integrations:

```bash
curl http://localhost:8000/api/v1/monitoring/health
```

Response:
```json
{
  "prometheus": {"status": "healthy", "url": "http://prometheus:9090"},
  "tempo": {"status": "healthy", "url": "http://tempo:3200"},
  "loki": {"status": "healthy", "url": "http://loki:3100"}
}
```

## Further Reading

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Tempo Documentation](https://grafana.com/docs/tempo/)
- [Grafana Loki Documentation](https://grafana.com/docs/loki/)
- [OpenTelemetry Specification](https://opentelemetry.io/docs/)
