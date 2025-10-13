# Transaction Flow Visualization

## Overview

The Transaction Flow Visualization feature enables users to trace transactions through the network using correlation/transaction IDs found in logs. This powerful feature helps identify:

- The path a transaction took through your infrastructure
- Performance bottlenecks and slow components
- Error sources and failure points
- Service dependencies in action
- Timing information for each hop

## How It Works

### Data Sources

The system integrates with multiple observability platforms to trace transactions:

1. **Loki** - For log aggregation and querying
2. **Azure Log Analytics** - For Azure-native log analytics
3. **Prometheus** - For metrics enrichment

The system automatically:
- Searches logs for correlation/transaction IDs
- Builds a timeline of log entries
- Maps logs to resources in the topology
- Enriches with metrics and performance data
- Visualizes the flow graphically

### Correlation ID Detection

The system looks for correlation IDs in several fields:
- `correlation_id`
- `transaction_id`
- `trace_id`
- Custom fields in log properties

## Using the Feature

### Step 1: Select a Pod

1. Navigate to the **Topology** view
2. Click on a **Pod** resource in the graph
3. The pod details panel will appear at the bottom

### Step 2: Visualize Flow

1. Click the **"Visualize Flow"** button on the pod details panel
2. The Transaction Flow Dialog opens

### Step 3: Select a Transaction

1. The system automatically searches for correlation IDs in the pod's logs (last hour)
2. A list of transaction IDs appears on the left sidebar
3. Click on any transaction ID to visualize its flow

### Step 4: Analyze the Flow

The visualization shows:

**Flow Summary:**
- Transaction ID
- Total duration in milliseconds
- Number of resources touched
- Error and warning counts
- Data source (Loki, Azure Log Analytics, or multi)

**Interactive Graph:**
- Nodes represent resources (pods, services, databases, etc.)
- Edges show the flow direction and timing
- Colors indicate status:
  - 🟢 Green: Success
  - 🟡 Orange: Warning
  - 🔴 Red: Error

**Node Information:**
- Resource name and type
- Timestamp when the resource processed the transaction
- Number of log entries
- Performance metrics (if available)

## Configuration

### Environment Variables

```env
# Loki Configuration
LOKI_URL=http://loki:3100

# Azure Log Analytics Configuration
AZURE_LOG_ANALYTICS_WORKSPACE_ID=your-workspace-id
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# Prometheus Configuration (for metrics enrichment)
PROMETHEUS_URL=http://prometheus:9090
```

### Logging Best Practices

To get the most out of transaction flow visualization:

1. **Always include correlation IDs in logs:**
   ```python
   from topdeck.common import set_correlation_id, get_logger
   
   logger = get_logger(__name__)
   
   def handle_request(correlation_id):
       set_correlation_id(correlation_id)
       logger.info("Processing request")
       # ... your code ...
   ```

2. **Use structured logging:**
   ```python
   logger.info("Database query completed", extra={
       "duration_ms": 50,
       "query_type": "SELECT",
       "rows_returned": 100
   })
   ```

3. **Propagate correlation IDs across services:**
   - Include in HTTP headers: `X-Correlation-ID`
   - Include in message queue headers
   - Pass through database connection tags

## Use Cases

### Performance Investigation

When users report slow response times:
1. Select the frontend pod in topology
2. Click "Visualize Flow"
3. Choose a recent slow transaction ID
4. Identify which service/resource caused the delay

### Error Debugging

When 500 errors appear in logs:
1. Select the affected pod
2. Click "Visualize Flow"
3. Choose a transaction ID with errors
4. See which resource in the chain failed

### Understanding Dependencies

To understand how services interact:
1. Select any pod
2. Visualize multiple transaction flows
3. Observe the common patterns

## API Endpoints

### Get Correlation IDs

```
GET /api/v1/monitoring/resources/{resource_id}/correlation-ids?duration_hours=1&limit=50
```

### Trace Transaction Flow

```
GET /api/v1/monitoring/flows/trace/{correlation_id}?duration_hours=1&source=auto&enrich=true
```

## Related Features

- [Network Flow Diagrams](../architecture/network-flow-diagrams.md) - Static flow patterns
- [Topology Visualization](../../FRONTEND_README.md#network-topology-visualization) - Infrastructure topology
