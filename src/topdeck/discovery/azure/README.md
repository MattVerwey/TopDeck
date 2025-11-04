# Azure Resource Discovery

This module implements Azure resource discovery for TopDeck.

## Features

- ✅ Azure SDK integration (ResourceManagementClient)
- ✅ Resource type mapping (Azure types → TopDeck types)
- ✅ Property extraction (resource group, subscription, tags)
- ✅ Environment detection from tags
- ✅ Status mapping (provisioning state → TopDeck status)
- ✅ Basic dependency detection (heuristic-based)

## Components

### AzureDiscoverer (`discoverer.py`)

Main orchestrator for Azure resource discovery.

**Usage**:
```python
from topdeck.discovery.azure import AzureDiscoverer

# Initialize with subscription ID
discoverer = AzureDiscoverer(subscription_id="your-subscription-id")

# Discover all resources
result = await discoverer.discover_all_resources()

# Discover specific resource group
result = await discoverer.discover_resource_group("rg-prod")

# Access results
print(f"Found {result.resource_count} resources")
print(f"Found {result.dependency_count} dependencies")
```

**Authentication**:
- Default: Uses `DefaultAzureCredential` (supports Azure CLI, Managed Identity, etc.)
- Service Principal: Provide `tenant_id`, `client_id`, `client_secret`
- Custom: Pass your own credential object

### AzureResourceMapper (`mapper.py`)

Maps Azure resources to TopDeck's normalized model.

**Supported Resource Types** (130 mappings covering 56 resource providers):

*For a complete list, see [Azure Resource Mapping Documentation](../../../../docs/AZURE_RESOURCE_MAPPING.md)*

**Key Resource Categories**:
- ✅ **Compute** (8 types): VMs, VM Scale Sets, Container Instances, AKS, Disks, etc.
- ✅ **Web & App Services** (6 types): App Services, App Service Plans, Static Web Apps, etc.
- ✅ **Databases** (14 types): SQL, PostgreSQL, MySQL, MariaDB, Cosmos DB, Redis, etc.
- ✅ **Networking** (30 types): VNets, Load Balancers, Application Gateway, Front Door, Firewall, VPN, etc.
- ✅ **Storage** (7 types): Storage Accounts, Blob/File/Queue/Table Services, Data Lake, etc.
- ✅ **Messaging** (10 types): Service Bus, Event Hub, Event Grid, Notification Hubs, etc.
- ✅ **Integration** (6 types): Logic Apps, API Management, Data Factory, etc.
- ✅ **Analytics** (7 types): Synapse, Databricks, Stream Analytics, HDInsight, etc.
- ✅ **AI/ML** (3 types): Cognitive Services, Machine Learning, Bot Service
- ✅ **IoT** (4 types): IoT Hub, IoT Central, Device Provisioning Service, etc.
- ✅ **Monitoring** (9 types): Application Insights, Log Analytics, Automation, etc.
- ✅ And many more categories including Identity, Security, DevOps, etc.

**Mapping Features**:
- Resource ID parsing (subscription, resource group extraction)
- Provisioning state → status mapping
- Environment detection from tags
- Tag normalization

### Resource Discovery Functions (`resources.py`)

Specialized discovery functions for different resource categories.

**Planned Functions**:
- `discover_compute_resources()` - VMs, App Services, AKS
- `discover_networking_resources()` - VNets, Load Balancers, NSGs
- `discover_data_resources()` - SQL, Cosmos DB, Storage
- `discover_config_resources()` - Key Vault, App Configuration

## Data Models

### DiscoveredResource

Represents a discovered cloud resource in normalized format.

**Properties**:
- `id`: Cloud resource ID (Azure ARM ID)
- `name`: Resource name
- `resource_type`: TopDeck normalized type
- `cloud_provider`: "azure"
- `region`: Azure location
- `resource_group`: Resource group name
- `subscription_id`: Azure subscription ID
- `status`: Resource status (running, stopped, error, etc.)
- `environment`: Environment tag (prod, staging, dev)
- `tags`: Resource tags
- `properties`: Cloud-specific properties (as JSON)
- `discovered_at`: Discovery timestamp
- `last_seen`: Last seen timestamp

### ResourceDependency

Represents a dependency between two resources.

**Properties**:
- `source_id`: Resource that depends on target
- `target_id`: Resource that is depended upon
- `category`: network, data, configuration, compute
- `dependency_type`: required, optional, strong, weak
- `strength`: 0.0 (weak) to 1.0 (critical)
- `discovered_method`: How dependency was discovered
- `description`: Human-readable description

### DiscoveryResult

Results from a discovery operation.

**Properties**:
- `resources`: List of discovered resources
- `dependencies`: List of discovered dependencies
- `errors`: List of error messages
- `subscription_id`: Subscription that was scanned
- `discovery_started_at`: Start timestamp
- `discovery_completed_at`: Completion timestamp

## Examples

### Basic Discovery

```python
import asyncio
from topdeck.discovery.azure import AzureDiscoverer

async def main():
    # Create discoverer
    discoverer = AzureDiscoverer(
        subscription_id="12345678-1234-1234-1234-123456789abc"
    )
    
    # Discover all resources
    result = await discoverer.discover_all_resources()
    
    # Print summary
    print(result.summary())
    
    # Access resources
    for resource in result.resources:
        print(f"- {resource.name} ({resource.resource_type})")

if __name__ == "__main__":
    asyncio.run(main())
```

### Service Principal Authentication

```python
discoverer = AzureDiscoverer(
    subscription_id="your-subscription-id",
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret",
)

result = await discoverer.discover_all_resources()
```

### Filter by Resource Group

```python
# Discover only production resources
result = await discoverer.discover_resource_group("rg-prod")
```

### Store in Neo4j

```python
from topdeck.storage.neo4j_client import Neo4jClient

# Discover resources
result = await discoverer.discover_all_resources()

# Connect to Neo4j
client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
client.connect()

# Store resources
for resource in result.resources:
    properties = resource.to_neo4j_properties()
    client.upsert_resource(properties)

# Store dependencies
for dependency in result.dependencies:
    properties = dependency.to_neo4j_properties()
    client.create_dependency(
        dependency.source_id,
        dependency.target_id,
        properties,
    )

client.close()
```

## Analyzing Unmapped Resources

To identify which resource types in your Azure subscription are not yet mapped:

```bash
python scripts/analyze_unmapped_resources.py \
    --subscription-id "your-subscription-id" \
    --tenant-id "your-tenant-id" \
    --client-id "your-client-id" \
    --client-secret "your-client-secret"
```

This will:
- Discover all resources in your subscription
- Report which resource types are unmapped (showing as "unknown")
- Show mapping coverage percentage
- Provide recommendations for adding missing mappings

## Testing

Tests are located in `tests/discovery/azure/`.

**Run tests**:
```bash
# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Run all Azure discovery tests
pytest tests/discovery/azure/ -v

# Run specific test file
pytest tests/discovery/azure/test_mapper.py -v
```

**Test Coverage**:
- ✅ Resource type mapping (130+ resource types)
- ✅ Resource ID parsing
- ✅ Status mapping
- ✅ Environment extraction
- ✅ Complete resource mapping
- ✅ New resource types (VM Scale Sets, Container Registry, Event Hub, etc.)

## Future Enhancements

### Planned Features

1. **Detailed Resource Discovery**
   - Implement specialized discovery functions per resource type
   - Extract detailed configurations and properties
   - Get network configurations and connections

2. **Advanced Dependency Detection**
   - Parse App Service connection strings
   - Analyze network traffic patterns
   - Parse Kubernetes deployments for service dependencies
   - Use Azure Resource Graph for relationship queries

3. **Incremental Discovery**
   - Delta sync (only update changed resources)
   - Track resource changes over time
   - Detect drift from baseline

4. **Multi-Subscription Support**
   - Discover across multiple subscriptions
   - Aggregate cross-subscription dependencies
   - Handle different credentials per subscription

5. **Rate Limiting & Performance**
   - Respect Azure API rate limits
   - Implement exponential backoff
   - Parallel discovery with worker pools
   - Caching for frequently accessed resources

6. **Kubernetes Integration**
   - Connect to AKS clusters
   - Discover pods, services, deployments
   - Map Kubernetes resources to Neo4j

## Architecture Decisions

### Why Heuristic-Based Dependencies?

The current implementation uses simple heuristics for dependency detection:
- App Services → SQL Databases in same resource group
- AKS → Storage Accounts in same resource group

**Rationale**:
- Provides immediate value for common patterns
- Doesn't require complex configuration parsing
- Low risk of false positives with conservative heuristics

**Future**: Will be replaced with:
- Configuration parsing (connection strings, environment variables)
- Azure Resource Graph queries (built-in relationships)
- Network traffic analysis (actual connections)

### Why Single-Pass Discovery?

Resources are discovered in a single pass through the Azure API.

**Benefits**:
- Simple implementation
- Predictable performance
- Easy to understand and debug

**Limitations**:
- Can't optimize for specific resource types
- All resources discovered even if not needed

**Future**: Will support:
- Selective discovery (only specified resource types)
- Two-pass discovery (resources first, then detailed configs)

## Dependencies

### Required

- `azure-identity` - Azure authentication
- `azure-mgmt-resource` - Resource management API
- `neo4j` - Graph database client

### Optional

- `azure-mgmt-compute` - Detailed VM/VMSS information
- `azure-mgmt-network` - Detailed networking information
- `azure-mgmt-containerservice` - Detailed AKS information
- `kubernetes` - Kubernetes cluster introspection

## Contributing

When adding new resource types:

1. Add mapping to `AzureResourceMapper.RESOURCE_TYPE_MAP`
2. Add specialized discovery function to `resources.py` (optional)
3. Add tests to `tests/discovery/azure/test_mapper.py`
4. Update this README with the new resource type

## References

- [Azure Resource Manager API](https://docs.microsoft.com/en-us/rest/api/resources/)
- [Azure SDK for Python](https://docs.microsoft.com/en-us/azure/developer/python/)
- [Azure Resource Graph](https://docs.microsoft.com/en-us/azure/governance/resource-graph/)
