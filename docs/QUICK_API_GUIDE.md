# Quick API Guide - Topology & Monitoring

Quick reference for using TopDeck's topology visualization and monitoring APIs.

## Starting the API Server

```bash
# Start the API server
python -m topdeck

# Server runs at http://localhost:8000
# API docs at http://localhost:8000/api/docs
```

## Topology API

### Get Full Topology

```bash
# All resources
curl http://localhost:8000/api/v1/topology

# Filter by cloud provider
curl "http://localhost:8000/api/v1/topology?cloud_provider=azure"

# Filter by region
curl "http://localhost:8000/api/v1/topology?cloud_provider=azure&region=eastus"

# Filter by resource type
curl "http://localhost:8000/api/v1/topology?resource_type=pod"
```

### Get Resource Dependencies

```bash
# Both upstream and downstream (default)
curl http://localhost:8000/api/v1/topology/resources/my-pod/dependencies

# Only upstream (what this depends on)
curl "http://localhost:8000/api/v1/topology/resources/my-pod/dependencies?direction=upstream"

# Only downstream (what depends on this)
curl "http://localhost:8000/api/v1/topology/resources/my-pod/dependencies?direction=downstream"

# Deeper traversal (up to 10 levels)
curl "http://localhost:8000/api/v1/topology/resources/my-pod/dependencies?depth=5"
```

### Get Data Flows

```bash
# All flows
curl http://localhost:8000/api/v1/topology/flows

# HTTPS flows
curl "http://localhost:8000/api/v1/topology/flows?flow_type=https"

# Database flows
curl "http://localhost:8000/api/v1/topology/flows?flow_type=database"

# Flows starting from load balancers
curl "http://localhost:8000/api/v1/topology/flows?start_resource_type=load_balancer"

# HTTPS flows from load balancers
curl "http://localhost:8000/api/v1/topology/flows?flow_type=https&start_resource_type=load_balancer"
```

## Monitoring API

### Get Resource Metrics

```bash
# Get metrics for a pod (last 1 hour)
curl "http://localhost:8000/api/v1/monitoring/resources/my-pod/metrics?resource_type=pod"

# Get metrics for last 6 hours
curl "http://localhost:8000/api/v1/monitoring/resources/my-pod/metrics?resource_type=pod&duration_hours=6"

# Get database metrics
curl "http://localhost:8000/api/v1/monitoring/resources/my-db/metrics?resource_type=database&duration_hours=2"

# Get load balancer metrics
curl "http://localhost:8000/api/v1/monitoring/resources/my-lb/metrics?resource_type=load_balancer"
```

### Detect Bottlenecks

```bash
# Check bottlenecks in a request flow
curl "http://localhost:8000/api/v1/monitoring/flows/request/bottlenecks?flow_path=load-balancer&flow_path=gateway&flow_path=api-pod&flow_path=database"

# Simpler flow
curl "http://localhost:8000/api/v1/monitoring/flows/simple/bottlenecks?flow_path=frontend&flow_path=backend&flow_path=db"
```

### Analyze Errors

```bash
# Get errors for a resource (last 1 hour)
curl http://localhost:8000/api/v1/monitoring/resources/my-pod/errors

# Get errors for last 6 hours
curl "http://localhost:8000/api/v1/monitoring/resources/my-pod/errors?duration_hours=6"
```

### Find Failure Points

```bash
# Find failure point in microservices (last 30 minutes)
curl "http://localhost:8000/api/v1/monitoring/flows/user-flow/failures?flow_path=frontend&flow_path=api&flow_path=auth&flow_path=database"

# Analyze last hour
curl "http://localhost:8000/api/v1/monitoring/flows/payment/failures?flow_path=gateway&flow_path=payment-service&flow_path=payment-db&duration_minutes=60"
```

### Check Monitoring Health

```bash
# Check Prometheus and Loki connectivity
curl http://localhost:8000/api/v1/monitoring/health
```

## Common Use Cases

### Scenario 1: New Deployment - Visualize Infrastructure

```bash
# 1. Get complete topology
curl "http://localhost:8000/api/v1/topology?cloud_provider=azure" > topology.json

# 2. Visualize with frontend or process with jq
cat topology.json | jq '.nodes | length'  # Count resources
cat topology.json | jq '.edges | length'  # Count relationships
```

### Scenario 2: Performance Issue - Find Bottleneck

```bash
# 1. Get data flows
curl "http://localhost:8000/api/v1/topology/flows?flow_type=https" > flows.json

# 2. Check bottlenecks in the main request flow
curl "http://localhost:8000/api/v1/monitoring/flows/main/bottlenecks?flow_path=lb&flow_path=api&flow_path=db" | jq

# 3. Get detailed metrics for problematic resource
curl "http://localhost:8000/api/v1/monitoring/resources/api-pod/metrics?resource_type=pod&duration_hours=1" | jq '.health_score'
```

### Scenario 3: Incident - Find Root Cause

```bash
# 1. Find failure point
curl "http://localhost:8000/api/v1/monitoring/flows/incident/failures?flow_path=lb&flow_path=api&flow_path=db" > failure.json

# 2. Check errors for failing resource
cat failure.json | jq -r '.resource_id'  # Get failing resource ID
FAILING_RESOURCE=$(cat failure.json | jq -r '.resource_id')

# 3. Get detailed error analysis
curl "http://localhost:8000/api/v1/monitoring/resources/$FAILING_RESOURCE/errors?duration_hours=1" | jq '.error_types'
```

### Scenario 4: Change Impact - Analyze Dependencies

```bash
# 1. Before making a change, check what depends on the resource
curl "http://localhost:8000/api/v1/topology/resources/database-server/dependencies?direction=downstream&depth=5" > dependents.json

# 2. Count affected services
cat dependents.json | jq '.downstream | length'

# 3. List affected services
cat dependents.json | jq -r '.downstream[].name'
```

## Response Examples

### Topology Node

```json
{
  "id": "aks-cluster-1",
  "resource_type": "kubernetes_cluster",
  "name": "production-aks",
  "cloud_provider": "azure",
  "region": "eastus",
  "properties": {
    "kubernetes_version": "1.27",
    "node_count": 3
  },
  "metadata": {}
}
```

### Resource Metrics

```json
{
  "resource_id": "api-pod",
  "resource_type": "pod",
  "metrics": {
    "cpu_usage": {...},
    "latency_p95": {...}
  },
  "anomalies": ["High latency detected: 1500ms"],
  "health_score": 75.5
}
```

### Bottleneck

```json
{
  "resource_id": "database-server",
  "type": "cpu_saturation",
  "severity": "high",
  "details": "CPU usage: 95.00%"
}
```

### Failure Point

```json
{
  "resource_id": "auth-service",
  "error_rate": 12.5,
  "error_count": 375,
  "error_types": {
    "TimeoutError": 200,
    "DatabaseError": 175
  },
  "recent_errors": [...]
}
```

## Using with jq (JSON Processing)

```bash
# Get all pod names
curl "http://localhost:8000/api/v1/topology?resource_type=pod" | jq -r '.nodes[].name'

# Count resources by cloud provider
curl http://localhost:8000/api/v1/topology | jq '[.nodes[].cloud_provider] | group_by(.) | map({provider: .[0], count: length})'

# Find resources with anomalies
curl "http://localhost:8000/api/v1/monitoring/resources/pod-1/metrics?resource_type=pod" | jq 'select(.anomalies | length > 0)'

# Get error types sorted by frequency
curl "http://localhost:8000/api/v1/monitoring/resources/api/errors" | jq '.error_types | to_entries | sort_by(.value) | reverse'
```

## Python Example

```python
import httpx
import asyncio

async def get_topology():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/topology",
            params={"cloud_provider": "azure"}
        )
        return response.json()

async def detect_bottlenecks(flow_path):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/monitoring/flows/main/bottlenecks",
            params={"flow_path": flow_path}
        )
        return response.json()

# Run
topology = asyncio.run(get_topology())
print(f"Found {len(topology['nodes'])} resources")

bottlenecks = asyncio.run(detect_bottlenecks(["lb", "api", "db"]))
for b in bottlenecks:
    print(f"Bottleneck in {b['resource_id']}: {b['details']}")
```

## JavaScript/TypeScript Example

```typescript
// Fetch topology
const topology = await fetch('http://localhost:8000/api/v1/topology?cloud_provider=azure')
  .then(res => res.json());

console.log(`Found ${topology.nodes.length} resources`);

// Get dependencies
const deps = await fetch('http://localhost:8000/api/v1/topology/resources/my-pod/dependencies?depth=3')
  .then(res => res.json());

console.log(`Upstream dependencies: ${deps.upstream.length}`);
console.log(`Downstream dependencies: ${deps.downstream.length}`);

// Detect bottlenecks
const params = new URLSearchParams();
['lb', 'api', 'db'].forEach(id => params.append('flow_path', id));

const bottlenecks = await fetch(`http://localhost:8000/api/v1/monitoring/flows/main/bottlenecks?${params}`)
  .then(res => res.json());

bottlenecks.forEach(b => {
  console.log(`⚠️ ${b.type} in ${b.resource_id}: ${b.details}`);
});
```

## Interactive API Documentation

Visit **http://localhost:8000/api/docs** for:
- Interactive Swagger UI
- Try out API endpoints
- See request/response schemas
- Auto-generated code examples

## Configuration

Set environment variables for monitoring platforms:

```bash
export PROMETHEUS_URL=http://prometheus:9090
export LOKI_URL=http://loki:3100
export GRAFANA_URL=http://grafana:3000
```

## Next Steps

1. **Explore API Docs**: http://localhost:8000/api/docs
2. **Build Frontend**: Use data to create visualizations
3. **Set up Monitoring**: Connect Prometheus and Loki
4. **Create Dashboards**: Build Grafana dashboards

## More Information

- [Topology API Documentation](api/TOPOLOGY_API.md)
- [Monitoring API Documentation](api/MONITORING_API.md)
- [Phase 2 Implementation Guide](PHASE_2_IMPLEMENTATION.md)
