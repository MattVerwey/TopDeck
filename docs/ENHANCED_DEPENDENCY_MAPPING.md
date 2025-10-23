# Enhanced Resource Dependency Mapping

## Overview

TopDeck now supports advanced dependency mapping that goes beyond simple resource group matching. The enhanced dependency discovery uses multiple data sources to create accurate, high-confidence dependency relationships.

## Discovery Methods

### 1. Connection String Analysis

**What it does:**
- Parses connection strings from resource configurations
- Extracts database connections, storage endpoints, cache connections, and API endpoints
- Creates dependencies with 90% confidence (very reliable)

**Supported Connection Types:**
- **Azure SQL Server**: `Server=tcp:myserver.database.windows.net,1433;Database=mydb;`
- **PostgreSQL**: `postgresql://user:pass@host:5432/database`
- **MySQL**: `mysql://user:pass@host:3306/database`
- **Redis**: `redis://host:6379/0`
- **Azure Storage**: `DefaultEndpointsProtocol=https;AccountName=storage;AccountKey=...`
- **AWS S3**: `https://bucket.s3.region.amazonaws.com`
- **Generic Endpoints**: `https://api.example.com`

**Where it looks:**
- Azure App Services: App settings and connection strings
- AWS Lambda/ECS: Environment variables
- GCP Cloud Functions/Run: Environment variables
- VM/Instance: User data and custom metadata
- Kubernetes: ConfigMaps and environment variables

### 2. Loki Log Analysis

**What it does:**
- Analyzes application logs for communication patterns
- Extracts HTTP requests, database queries, and service calls
- Creates dependencies with confidence based on log frequency

**Patterns detected:**
- HTTP/HTTPS requests: `GET https://api.example.com/endpoint`
- Database connections: `Connecting to postgres://db.example.com:5432`
- Service calls: `Calling order-service`

**Confidence levels:**
- HTTP URLs: 80%
- Database connections: 85%
- Service names: 60%

### 3. Prometheus Metrics Analysis

**What it does:**
- Analyzes metrics for traffic patterns
- Identifies service-to-service communication
- Measures connection volumes and health

**Metrics analyzed:**
- `request_rate`: HTTP requests between services
- `connections`: Database/cache connection counts
- `latency_p95`: Service response times
- `error_rate`: Failed connections

**Confidence levels:**
- Direct metrics: 80-85%
- Combined with logs: 95%+

## Resource Types Enhanced

### Azure

| Resource Type | Connection Sources | Example Dependencies |
|--------------|-------------------|---------------------|
| App Service | App settings, connection strings | → SQL Database, Redis Cache, Storage Account |
| Virtual Machine | Extensions, custom data | → SQL Database, Storage Account |
| AKS | Add-on configs, pod specs | → Container Registry, Key Vault, Storage |
| Function App | App settings, bindings | → Storage Account, Event Hub, Service Bus |

### AWS

| Resource Type | Connection Sources | Example Dependencies |
|--------------|-------------------|---------------------|
| Lambda | Environment variables | → RDS, DynamoDB, S3, SQS |
| ECS Service | Task definition | → RDS, ElastiCache, S3 |
| EC2 Instance | User data | → RDS, ElastiCache, S3 |
| EKS | Pod specifications | → ECR, RDS, S3 |

### GCP

| Resource Type | Connection Sources | Example Dependencies |
|--------------|-------------------|---------------------|
| Cloud Function | Environment variables | → Cloud SQL, Cloud Storage, Firestore |
| Cloud Run | Container environment | → Cloud SQL, Cloud Storage, Memorystore |
| Compute Instance | Metadata | → Cloud SQL, Cloud Storage |
| GKE | Pod specifications | → Container Registry, Cloud SQL, Cloud Storage |

## Usage Examples

### Python API

```python
from topdeck.discovery.enhanced_dependency_enrichment import EnhancedDependencyEnrichment
from topdeck.discovery.models import DiscoveredResource

# Initialize enrichment service
enrichment = EnhancedDependencyEnrichment(
    loki_url="http://loki:3100",
    prometheus_url="http://prometheus:9090"
)

# Enrich dependencies for resources
resources = [...]  # List of DiscoveredResource objects
result = await enrichment.enrich_resource_dependencies(
    resources=resources,
    analyze_monitoring=True,
    monitoring_duration=timedelta(hours=24)
)

print(f"Found {result.total_new_dependencies} new dependencies")
print(f"Connection strings: {result.enrichment_summary['connection_string_count']}")
print(f"Monitoring: {result.enrichment_summary['monitoring_count']}")

# Close collectors
await enrichment.close()
```

### Using with Mappers

```python
from topdeck.discovery.azure.mapper import AzureResourceMapper

# Extract connection string dependencies from Azure App Service
resource_id = "/subscriptions/.../providers/Microsoft.Web/sites/myapp"
properties = {
    "siteConfig": {
        "appSettings": [
            {"name": "DB_CONNECTION", "value": "Server=tcp:mydb.database.windows.net,1433;Database=prod;"}
        ]
    }
}

dependencies = AzureResourceMapper.extract_connection_strings_from_properties(
    resource_id=resource_id,
    resource_type="Microsoft.Web/sites",
    properties=properties
)

for dep in dependencies:
    print(f"{dep.source_id} -> {dep.target_id}")
    print(f"  Category: {dep.category}, Type: {dep.dependency_type}")
    print(f"  Confidence: {dep.strength}")
```

### Analyzing Traffic Patterns

```python
from topdeck.discovery.monitoring_dependency_discovery import MonitoringDependencyDiscovery
from topdeck.monitoring.collectors.loki import LokiCollector
from topdeck.monitoring.collectors.prometheus import PrometheusCollector

# Initialize collectors
loki = LokiCollector("http://loki:3100")
prometheus = PrometheusCollector("http://prometheus:9090")

# Create discovery service
discovery = MonitoringDependencyDiscovery(
    loki_collector=loki,
    prometheus_collector=prometheus
)

# Analyze traffic patterns
resource_ids = ["service-a", "service-b", "database-1"]
patterns = await discovery.analyze_traffic_patterns(
    resource_ids=resource_ids,
    duration=timedelta(hours=24)
)

# Convert to dependencies
dependencies = discovery.create_dependencies_from_traffic_patterns(
    patterns=patterns,
    min_confidence=0.5
)

print(f"Found {len(dependencies)} traffic-based dependencies")
```

## Dependency Categories

| Category | Description | Examples |
|----------|-------------|----------|
| DATA | Data storage and persistence | Databases, caches, storage accounts |
| NETWORK | Network communication | HTTP APIs, load balancers, gateways |
| CONFIGURATION | Configuration dependencies | Key vaults, secret stores, config services |
| COMPUTE | Compute dependencies | VM dependencies, container orchestration |

## Dependency Types

| Type | Strength | Description |
|------|----------|-------------|
| REQUIRED | 0.9 | Critical dependency, failure causes immediate impact |
| STRONG | 0.7 | Important dependency, failure causes significant impact |
| OPTIONAL | 0.5 | Nice-to-have dependency, failure has limited impact |
| WEAK | 0.3 | Minor dependency, failure has minimal impact |

## Discovery Methods

| Method | Typical Strength | When to Use |
|--------|------------------|-------------|
| connection_string | 0.9 | Always - very reliable |
| traffic_analysis | 0.5-0.9 | When monitoring data available |
| configuration | 0.7 | For explicit config references |
| resource_group | 0.3 | As fallback only |

## Best Practices

### 1. Use Connection Strings When Possible
Connection strings provide the most reliable dependencies:
```python
# Good: Store connection strings in app settings
"DB_CONNECTION": "Server=tcp:mydb.database.windows.net,1433;Database=prod;"

# Bad: Hard-coded or scattered across multiple configs
```

### 2. Enable Monitoring Analysis
Combine all three methods for highest accuracy:
```python
result = await enrichment.enrich_resource_dependencies(
    resources=resources,
    analyze_monitoring=True,  # Enable for best results
    monitoring_duration=timedelta(hours=24)
)
```

### 3. Filter by Confidence
Set appropriate confidence thresholds:
```python
# For critical systems, use high confidence
dependencies = discovery.create_dependencies_from_traffic_patterns(
    patterns=patterns,
    min_confidence=0.7  # Only high-confidence dependencies
)

# For discovery/exploration, use lower threshold
dependencies = discovery.create_dependencies_from_traffic_patterns(
    patterns=patterns,
    min_confidence=0.5  # Include more potential dependencies
)
```

### 4. Use Proper Logging
Ensure applications log service calls:
```python
# Good: Explicit service call logging
logger.info(f"Calling order-service at {order_service_url}")

# Bad: Silent failures
try:
    response = requests.get(order_service_url)
except:
    pass  # No logging
```

### 5. Tag Metrics Properly
Use consistent labels in metrics:
```python
# Good: Clear target identification
http_requests_total{
    source_service="frontend",
    target_service="backend",
    method="GET"
}

# Bad: No service identification
http_requests_total{method="GET"}
```

## Configuration

### Environment Variables

```bash
# Loki configuration
LOKI_URL=http://loki:3100

# Prometheus configuration
PROMETHEUS_URL=http://prometheus:9090

# Enrichment settings
DEPENDENCY_MIN_CONFIDENCE=0.5
DEPENDENCY_MONITORING_HOURS=24
```

### Neo4j Storage

Enhanced dependencies are stored with additional metadata:

```cypher
// Create dependency with enrichment metadata
CREATE (source)-[dep:DEPENDS_ON {
    category: 'data',
    dependency_type: 'required',
    strength: 0.9,
    discovered_method: 'connection_string',
    discovered_at: datetime(),
    description: 'Database connection from app settings'
}]->(target)
```

## Performance Considerations

### Connection String Parsing
- **Speed**: Very fast (milliseconds per resource)
- **Cost**: Minimal CPU and memory
- **Recommendation**: Always enable

### Log Analysis
- **Speed**: Moderate (seconds per resource, depends on log volume)
- **Cost**: Network I/O to Loki
- **Recommendation**: Use for critical resources or scheduled enrichment

### Metrics Analysis
- **Speed**: Moderate (seconds per resource, depends on time range)
- **Cost**: Network I/O to Prometheus
- **Recommendation**: Use for critical resources or scheduled enrichment

### Combined Analysis
- **Speed**: 5-30 seconds per resource group
- **Cost**: Combined network I/O
- **Recommendation**: Run periodically (e.g., every 6-12 hours)

## Troubleshooting

### No Dependencies Found

**Check connection strings:**
```python
# Verify properties contain connection strings
print(resource.properties)

# Test parser directly
conn_info = ConnectionStringParser.parse_connection_string(connection_string)
print(f"Parsed: {conn_info}")
```

**Check monitoring availability:**
```python
# Verify enrichment capabilities
capabilities = enrichment.get_enrichment_capabilities()
print(f"Loki available: {capabilities['loki_log_analysis']}")
print(f"Prometheus available: {capabilities['prometheus_metrics_analysis']}")
```

### Low Confidence Dependencies

**Increase monitoring duration:**
```python
# Look at longer time period
result = await enrichment.enrich_resource_dependencies(
    resources=resources,
    monitoring_duration=timedelta(hours=72)  # 3 days instead of 1
)
```

**Check log patterns:**
```python
# Verify logs contain parseable patterns
streams = await loki.get_resource_logs(resource_id)
for stream in streams:
    for entry in stream.entries:
        print(entry.message)  # Should contain URLs, service names, etc.
```

## Future Enhancements

- Support for Kubernetes ConfigMaps and Secrets
- Azure Key Vault reference detection
- AWS Systems Manager Parameter Store integration
- GCP Secret Manager integration
- OpenTelemetry trace analysis
- Service mesh integration (Istio, Linkerd)
