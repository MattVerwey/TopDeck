# Log Platform Support

## Overview

TopDeck provides **flexible log platform support**, allowing you to use your existing observability stack without requiring specific tools like Prometheus or Grafana. The platform can determine dependencies and change impact from logs across multiple log analytics platforms.

## Supported Platforms

### ✅ Elasticsearch

**Use Case**: Teams using the Elastic Stack (Elasticsearch, Logstash, Kibana)

**What TopDeck Can Do**:
- Trace transactions across services using correlation IDs
- Discover service-to-service dependencies from log patterns
- Identify change impact by correlating deployments with error spikes
- Track resource-level errors and performance issues

**Configuration**:
```bash
# .env file
ELASTICSEARCH_URL=https://elasticsearch.example.com:9200
ELASTICSEARCH_INDEX_PATTERN=logs-*

# Option 1: API Key (recommended)
ELASTICSEARCH_API_KEY=your-api-key

# Option 2: Basic Authentication
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=your-password
```

**Example Usage**:
```bash
# Trace a transaction through your system
curl "http://localhost:8000/api/v1/monitoring/transactions/trace?transaction_id=txn-123&source=elasticsearch"

# Get errors for a resource
curl "http://localhost:8000/api/v1/monitoring/resources/my-service/errors"

# Check health
curl "http://localhost:8000/api/v1/monitoring/health"
```

### ✅ Azure Log Analytics

**Use Case**: Teams using Azure Monitor and Application Insights

**What TopDeck Can Do**:
- Query logs using KQL (Kusto Query Language)
- Trace distributed transactions via correlation IDs
- Discover dependencies from Application Insights telemetry
- Correlate changes with performance degradation

**Configuration**:
```bash
# .env file
AZURE_LOG_ANALYTICS_WORKSPACE_ID=your-workspace-id

# Azure credentials (uses DefaultAzureCredential)
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
```

**Example Usage**:
```bash
# Trace a transaction
curl "http://localhost:8000/api/v1/monitoring/transactions/trace?transaction_id=abc-123&source=azure_log_analytics"

# Discover dependencies from logs
python -m topdeck.discovery.monitoring_dependency_discovery \
  --platform azure_log_analytics \
  --duration-hours 24
```

### ✅ Prometheus + Grafana

**Use Case**: Teams using Prometheus for metrics and Grafana for visualization

**What TopDeck Can Do**:
- Collect performance metrics (CPU, memory, latency, error rates)
- Detect performance bottlenecks in request flows
- Identify anomalies in resource behavior
- Compare metrics across resources

**Configuration**:
```bash
# .env file
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000
```

**Example Usage**:
```bash
# Get metrics for a resource
curl "http://localhost:8000/api/v1/monitoring/resources/my-pod/metrics?resource_type=pod&duration_hours=2"

# Detect bottlenecks in a flow
curl "http://localhost:8000/api/v1/monitoring/flows/bottlenecks?flow_path=lb&flow_path=api&flow_path=db"
```

### ✅ Loki

**Use Case**: Teams using Loki for log aggregation in Kubernetes

**What TopDeck Can Do**:
- Query logs using LogQL
- Trace logs across pods and services
- Identify error patterns and spikes
- Correlate logs with resource topology

**Configuration**:
```bash
# .env file
LOKI_URL=http://loki:3100
```

**Example Usage**:
```bash
# Get resource errors
curl "http://localhost:8000/api/v1/monitoring/resources/my-pod/errors?duration_hours=1"

# Find failure point in a flow
curl "http://localhost:8000/api/v1/monitoring/flows/failures?flow_path=frontend&flow_path=api&flow_path=db"
```

## Multi-Platform Support

**You can use multiple platforms simultaneously!** TopDeck will aggregate data from all configured sources to provide a complete picture.

### Example: Elasticsearch + Prometheus

```bash
# .env file
ELASTICSEARCH_URL=https://elasticsearch.example.com:9200
ELASTICSEARCH_API_KEY=your-api-key
PROMETHEUS_URL=http://prometheus:9090
```

TopDeck will:
1. Use Elasticsearch for log-based dependency discovery
2. Use Prometheus for metrics-based dependency discovery
3. Combine evidence from both sources with confidence scoring
4. Provide unified dependency graph and change impact analysis

### Example: Azure Log Analytics Only

```bash
# .env file
AZURE_LOG_ANALYTICS_WORKSPACE_ID=your-workspace-id
# Leave other monitoring platforms unconfigured
```

TopDeck will:
1. Use only Azure Log Analytics for all analysis
2. Work perfectly without Prometheus or Grafana
3. Provide full dependency discovery and change impact analysis

## How It Works

### Dependency Discovery from Logs

TopDeck analyzes log messages to identify service communication patterns:

1. **HTTP/HTTPS Requests**: Extracts target URLs from log messages
   ```
   "Making GET request to https://api.service-b.com/users"
   → Dependency: current-service → api.service-b.com
   ```

2. **Database Connections**: Identifies database dependencies
   ```
   "Connected to postgres://db.example.com:5432/mydb"
   → Dependency: current-service → db.example.com
   ```

3. **Service Calls**: Recognizes service name patterns
   ```
   "Calling order-service for processing"
   → Dependency: current-service → order-service
   ```

### Transaction Tracing

TopDeck traces transactions across services using correlation IDs:

```
Resource A: [correlation_id: txn-123] Request received
Resource B: [correlation_id: txn-123] Processing order
Resource C: [correlation_id: txn-123] Database query
Resource B: [correlation_id: txn-123] Response sent
Resource A: [correlation_id: txn-123] Request complete

→ Flow: Resource A → Resource B → Resource C
```

### Change Impact Analysis

TopDeck correlates changes with log patterns:

1. **Before Deployment**: Baseline error rate 2%
2. **Deployment Event**: Service updated at 10:30 AM
3. **After Deployment**: Error rate jumps to 15%
4. **Analysis**: TopDeck identifies deployment as likely cause

## Field Mapping

TopDeck looks for these fields in your logs (platform-agnostic):

| Field Purpose | Elasticsearch | Azure Log Analytics | Generic |
|--------------|---------------|---------------------|---------|
| Timestamp | `@timestamp` | `TimeGenerated` | `timestamp` |
| Message | `message` | `Message` | `message` |
| Log Level | `level`, `severity` | `SeverityLevel` | `level` |
| Correlation ID | `correlation_id`, `trace_id` | `CorrelationId` | `correlation_id` |
| Resource ID | `resource_id`, `kubernetes.pod.name` | `ResourceId` | `resource_id` |
| Operation | `operation_name` | `OperationName` | `operation` |

## FAQ

### Q: Do I need Prometheus AND Grafana?

**A: No!** You can use:
- Just Elasticsearch
- Just Azure Log Analytics
- Just Loki
- Any combination that fits your needs

TopDeck adapts to your existing infrastructure.

### Q: Can I use Datadog or New Relic?

**A: Coming soon!** The architecture is designed to support any log platform. Elasticsearch and Azure Log Analytics support cover most use cases today.

### Q: What if I don't have any monitoring platform?

**A: You need at least one log source.** TopDeck analyzes logs to discover dependencies. Without logs, it can still:
- Discover resources from cloud APIs
- Map infrastructure topology
- But cannot trace transactions or discover runtime dependencies

### Q: How accurate is log-based dependency discovery?

**A: Very accurate** when logs contain service communication information. TopDeck uses:
- Pattern matching with confidence scoring (0.0-1.0)
- Evidence aggregation from multiple sources
- Correlation ID tracing for high accuracy

Lower confidence dependencies can be filtered out.

### Q: Can I combine cloud-native and third-party tools?

**A: Yes!** For example:
- Azure Log Analytics for Azure resources
- Elasticsearch for on-premise resources
- Prometheus for Kubernetes metrics

TopDeck aggregates all sources into a unified view.

## Getting Started

### Step 1: Check Your Current Setup

Identify what observability tools you're already using:
```bash
# Do you have Elasticsearch?
curl http://localhost:9200/_cluster/health

# Do you have Azure Log Analytics?
az monitor log-analytics workspace show --ids /subscriptions/...

# Do you have Prometheus?
curl http://localhost:9090/api/v1/status/config
```

### Step 2: Configure TopDeck

Add your platform URLs to `.env`:
```bash
cp .env.example .env
# Edit .env with your platform URLs
```

### Step 3: Test Connection

```bash
# Start TopDeck
make run

# Check monitoring health
curl http://localhost:8000/api/v1/monitoring/health
```

Expected response:
```json
{
  "elasticsearch": {
    "status": "healthy",
    "url": "https://elasticsearch.example.com:9200"
  },
  "azure_log_analytics": {
    "status": "not_configured",
    "workspace_id": null
  },
  "prometheus": {
    "status": "not_configured",
    "url": null
  },
  "loki": {
    "status": "not_configured",
    "url": null
  }
}
```

### Step 4: Discover Dependencies

```bash
# Run dependency discovery
python -m topdeck.discovery.monitoring_dependency_discovery \
  --duration-hours 24

# View results
curl http://localhost:8000/api/v1/topology
```

## Best Practices

1. **Use Correlation IDs**: Ensure your logs include correlation/trace IDs for transaction tracing
2. **Structured Logging**: Use JSON or structured log formats for easier parsing
3. **Include Context**: Log service names, URLs, and connection details
4. **Consistent Fields**: Use consistent field names across services
5. **Appropriate Log Levels**: Use proper log levels (error, warn, info) for filtering

## Support

For questions or issues:
- Check the [Monitoring API Documentation](api/MONITORING_API.md)
- Review [Enhanced Dependency Analysis Guide](ENHANCED_DEPENDENCY_ANALYSIS.md)
- Create an [Issue](https://github.com/MattVerwey/TopDeck/issues)
