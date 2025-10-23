# Azure Service Bus Enhancement for Service Graph and Risk Analysis

## Overview

This enhancement adds comprehensive Azure Service Bus support to TopDeck's discovery, topology visualization, and risk analysis capabilities. Service Bus is Azure's enterprise messaging service that enables asynchronous communication patterns between applications.

## What Was Added

### Backend Discovery

#### 1. Service Bus Resource Types
Four new resource types have been added to the system:
- **`servicebus_namespace`** - The Service Bus namespace (container for topics and queues)
- **`servicebus_topic`** - Publish-subscribe messaging topics
- **`servicebus_queue`** - Point-to-point messaging queues
- **`servicebus_subscription`** - Topic subscriptions for receiving messages

#### 2. Discovery Capabilities
The enhanced discovery system now:
- Discovers all Service Bus namespaces in an Azure subscription
- Discovers all topics and queues within each namespace
- Discovers all subscriptions for each topic
- Extracts detailed properties including:
  - SKU tier (Basic, Standard, Premium)
  - Message size limits
  - Session support
  - Duplicate detection settings
  - Delivery count settings
  - Health status

#### 3. Dependency Detection
The system automatically detects:
- **Namespace → Topic/Queue relationships** (strong, 1.0 strength)
- **Topic → Subscription relationships** (strong, 1.0 strength)
- **Application → Service Bus heuristic relationships** (weak, 0.3 strength)
  - Apps in the same resource group are marked as potential Service Bus users

### Risk Analysis Integration

#### Risk Scoring
Service Bus resources are assigned appropriate criticality factors:
- **Namespace**: 28 (high - messaging backbone)
- **Topics**: 26 (high - critical pub-sub channels)
- **Queues**: 26 (high - critical message routing)
- **Subscriptions**: 18 (medium - individual consumers)

These criticality levels reflect that messaging infrastructure is typically critical to application architecture:
- Namespace failures affect all topics and queues
- Topic/queue failures break async communication patterns
- Subscription failures affect individual consumers but are less critical

#### Risk Assessment Impact
When analyzing risk for Service Bus resources, the system considers:
- Number of publishers and subscribers
- Whether the resource is a single point of failure
- Impact on dependent services
- Blast radius calculations

### Enhanced Dependency Detection (Phase 1) ✨ **NEW**

The system now uses **definitive configuration parsing** instead of just heuristics:

#### App Service Configuration Parsing
- Automatically fetches application settings and connection strings from Azure App Services
- Parses Service Bus connection strings (format: `Endpoint=sb://namespace.servicebus.windows.net/...`)
- Creates **strong dependencies** (0.9 strength) when connections are found
- Discovery method: `app_service_config`

#### Kubernetes ConfigMaps & Secrets
- Queries AKS clusters for ConfigMaps and Secrets across all namespaces
- Parses environment variables for Service Bus connection strings
- Decodes base64-encoded secrets automatically
- Creates **strong dependencies** (0.9 strength) when connections are found
- Discovery method: `kubernetes_config`

#### Fallback to Heuristics
- For apps where configuration parsing fails or isn't accessible
- Uses resource group colocation as a weak signal
- Creates **weak dependencies** (0.3 strength)
- Discovery method: `heuristic_colocation`

This multi-layered approach ensures maximum accuracy while maintaining broad coverage.

### Frontend Visualization

#### Color Scheme
Service Bus resources have distinct purple/violet colors for easy identification:
- **Namespace**: `#8b5cf6` (purple)
- **Topic**: `#a78bfa` (lighter purple)
- **Queue**: `#c4b5fd` (light purple)
- **Subscription**: `#ddd6fe` (pale purple)

#### Relationship Labels
New relationship types for messaging patterns:
- **`contains`** - For namespace→topic/queue and topic→subscription
- **`publishes_to`** - For apps publishing to topics/queues
- **`subscribes_from`** - For apps consuming from subscriptions

#### Mock Data
The demo mode includes a realistic Service Bus topology:
- 1 namespace (`SB-Prod-Namespace`)
- 2 topics (`orders-topic`, `events-topic`)
- 1 subscription (`order-processing-sub`)
- Connections showing pub-sub patterns with API pods and worker pods

## Usage

### Discovery

To discover Service Bus resources in your Azure subscription:

```python
from topdeck.discovery.azure.discoverer import AzureDiscoverer

discoverer = AzureDiscoverer(
    subscription_id="your-subscription-id",
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret"
)

result = await discoverer.discover_all_resources()

# Filter Service Bus resources
sb_namespaces = [r for r in result.resources if r.resource_type == "servicebus_namespace"]
sb_topics = [r for r in result.resources if r.resource_type == "servicebus_topic"]
sb_queues = [r for r in result.resources if r.resource_type == "servicebus_queue"]
sb_subscriptions = [r for r in result.resources if r.resource_type == "servicebus_subscription"]
```

### Risk Analysis

To analyze risk for a Service Bus namespace:

```bash
# Get comprehensive risk assessment
curl "http://localhost:8000/api/v1/risk/resources/{namespace-id}"

# Check if it's a single point of failure
curl "http://localhost:8000/api/v1/risk/spof"
```

The risk analysis will show:
- **Risk Score**: 0-100 score based on criticality and dependencies
- **Risk Level**: Critical/High/Medium/Low
- **Blast Radius**: Number of services affected if it fails
- **Dependencies**: What services publish or subscribe
- **Impact**: Detailed impact assessment

### Topology Visualization

The Service Bus resources appear in the service dependency graph:

1. Navigate to **Topology** → **Dependency View**
2. Enable **Demo Mode** to see the example Service Bus topology
3. Service Bus resources are shown in purple/violet colors
4. Click nodes to see details including namespace, configuration, and health status
5. Follow the arrows to see message flow:
   - Apps → Topics (publishers)
   - Subscriptions → Apps (subscribers)

## Architecture Patterns

### Pub-Sub Pattern
```
API Service → Topic → Subscription → Worker Service
```
- API services publish events to topics
- Multiple subscriptions can receive from one topic
- Worker services process events asynchronously

### Queue Pattern
```
API Service → Queue → Worker Service
```
- Direct point-to-point messaging
- Guarantees single processing per message
- Good for task distribution

### Event-Driven Architecture
```
Order Service → Orders Topic → [Order Processor, Inventory Service, Notification Service]
```
- One event triggers multiple independent handlers
- Loose coupling between services
- Each subscription can filter messages

## Benefits for Operations

### 1. Visibility
- See all messaging infrastructure in one place
- Understand which apps publish and subscribe
- Identify message flow patterns

### 2. Risk Assessment
- Identify critical messaging paths
- Assess blast radius of Service Bus failures
- Find single points of failure in async communication

### 3. Impact Analysis
- "What happens if this topic fails?"
- "Which services depend on this namespace?"
- "What's the impact of changing this subscription?"

### 4. Change Planning
- Visualize dependencies before changes
- Plan maintenance windows
- Identify redundancy gaps

## Technical Details

### Files Modified

**Backend:**
- `requirements.txt` - Added `azure-mgmt-servicebus==8.2.0`
- `src/topdeck/discovery/azure/mapper.py` - Added resource type mappings
- `src/topdeck/discovery/azure/resources.py` - Added discovery and dependency detection
- `src/topdeck/discovery/azure/discoverer.py` - Integrated messaging discovery
- `src/topdeck/analysis/risk/scoring.py` - Added criticality factors

**Frontend:**
- `frontend/src/components/topology/ServiceDependencyGraph.tsx` - Added colors and labels
- `frontend/src/utils/mockTopologyData.ts` - Added Service Bus demo data

**Tests:**
- `tests/discovery/azure/test_servicebus.py` - Comprehensive test suite (9 tests)

### Dependencies

The enhancement requires:
- Azure SDK for Python: `azure-mgmt-servicebus>=8.2.0`
- Appropriate Azure credentials with Service Bus read permissions

### Permissions Required

#### Basic Service Bus Discovery
To discover Service Bus resources, the service principal needs:
- `Microsoft.ServiceBus/namespaces/read`
- `Microsoft.ServiceBus/namespaces/topics/read`
- `Microsoft.ServiceBus/namespaces/queues/read`
- `Microsoft.ServiceBus/namespaces/topics/subscriptions/read`

These are typically included in the `Reader` role.

#### Enhanced Dependency Detection (Phase 1)
For configuration parsing, additional permissions are required:

**App Service Configuration:**
- `Microsoft.Web/sites/config/list/action` - Read app settings and connection strings
- Typically included in `Website Contributor` or `Contributor` role

**AKS Cluster Configuration:**
- `Microsoft.ContainerService/managedClusters/listClusterAdminCredential/action` - Get cluster credentials
- `Microsoft.ContainerService/managedClusters/read` - Read cluster details
- Kubernetes RBAC permissions to read ConfigMaps and Secrets in all namespaces
- Typically requires `Azure Kubernetes Service Cluster Admin Role` or custom role

**Note**: The system gracefully degrades if these permissions aren't available. It will log debug messages and fall back to heuristic detection. Core Service Bus discovery still works without these enhanced permissions.

## Future Enhancements

### Phase 2: Enhanced Dependency Detection
- Parse application code to find Service Bus client usage
- Extract connection strings from app configurations
- Detect actual publisher/subscriber relationships

### Phase 3: Message Flow Analysis
- Track message volumes and throughput
- Identify message processing delays
- Detect dead letter queue issues

### Phase 4: Performance Metrics
- Integrate with Azure Monitor
- Show message rates and latencies
- Alert on subscription backlogs

### Phase 5: Advanced Risk Scenarios
- Model message queue overflow scenarios
- Assess impact of subscription failures
- Simulate namespace outages

## Testing

### Unit Tests
All Service Bus functionality is covered by unit tests:
```bash
pytest tests/discovery/azure/test_servicebus.py -v
```

Tests cover:
- Resource type mapping (4 tests)
- Namespace, topic, queue, and subscription discovery
- Dependency detection (all relationship types)
- Complete topology scenarios
- **Connection string parsing** (6 tests - NEW)
- **Configuration-based dependency detection** (tested via integration)

### Integration Testing
To test with real Azure resources:
1. Set up Azure credentials with appropriate permissions (see below)
2. Create test Service Bus namespace with topics/queues
3. Create test App Service or AKS cluster with Service Bus connection strings
4. Run discovery: `python scripts/test_discovery.py`
5. Verify resources and dependencies appear in Neo4j
6. Check topology visualization in web UI

## Troubleshooting

### Service Bus Resources Not Appearing

**Check credentials:**
```bash
# Verify Azure credentials work
az login
az servicebus namespace list
```

**Check permissions:**
Ensure the service principal has Reader role on the subscription or resource group.

**Check logs:**
```bash
# Look for Service Bus discovery logs
python -m topdeck.discovery.azure.discoverer --subscription-id <id> --debug
```

### Missing Dependencies

**No connection string detected:**
This is expected. The current implementation uses heuristics (same resource group) to suggest potential connections. Future enhancements will parse app configurations to find actual connections.

**Subscriptions not showing:**
Ensure topics have subscriptions created. The discovery only finds existing subscriptions.

### Frontend Visualization Issues

**Service Bus nodes not colored correctly:**
Refresh the page to ensure the latest code is loaded.

**Demo mode not showing Service Bus:**
Ensure you're in Dependency View (not Standard View) and Demo Mode is enabled.

## Related Documentation

- [Enhanced Service Dependency Graph](SERVICE_DEPENDENCY_GRAPH.md)
- [Risk Analysis Guide](ENHANCED_RISK_ANALYSIS.md)
- [Azure Discovery Documentation](azure/DISCOVERY.md)
- [Topology API Documentation](api/TOPOLOGY_API.md)

## References

- [Azure Service Bus Documentation](https://docs.microsoft.com/en-us/azure/service-bus-messaging/)
- [Azure Service Bus Python SDK](https://docs.microsoft.com/en-us/python/api/overview/azure/servicebus)
- [TopDeck Issue #63](https://github.com/MattVerwey/TopDeck/issues/63)
- [TopDeck PR #62 - Service Dependency Graph](https://github.com/MattVerwey/TopDeck/pull/62)
