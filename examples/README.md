# TopDeck Examples

This directory contains example scripts and demonstrations for TopDeck features.

## Enhanced Topology Analysis Demo

**Script:** `enhanced_topology_demo.py`

Demonstrates the new enhanced topology and dependency analysis features, showing which resources are attached to which and providing in-depth analysis.

### Prerequisites

1. TopDeck API server running:
   ```bash
   # From repository root
   docker-compose up -d  # Start Neo4j
   make run              # Start API server
   ```

2. Resources discovered and loaded into Neo4j:
   ```bash
   # Run discovery for your cloud provider
   python -m topdeck.discovery.azure.discoverer --subscription-id <id>
   ```

3. Install httpx (if not already installed):
   ```bash
   pip install httpx
   ```

### Usage

Basic usage:
```bash
python examples/enhanced_topology_demo.py --resource-id <resource-id>
```

Show specific feature only:
```bash
# Show only comprehensive analysis
python examples/enhanced_topology_demo.py --resource-id <resource-id> --feature analysis

# Show only attachments
python examples/enhanced_topology_demo.py --resource-id <resource-id> --feature attachments

# Show only dependency chains
python examples/enhanced_topology_demo.py --resource-id <resource-id> --feature chains

# Show enhanced dependencies endpoint
python examples/enhanced_topology_demo.py --resource-id <resource-id> --feature dependencies
```

Custom API URL:
```bash
python examples/enhanced_topology_demo.py \
  --resource-id <resource-id> \
  --api-url http://your-server:8000
```

### Features Demonstrated

1. **Comprehensive Attachment Analysis**
   - Total attachments and breakdown by type
   - Critical attachments identification
   - Attachment strength scores
   - Impact radius
   - Dependency chains

2. **Resource Attachments**
   - Detailed connection information
   - Relationship types and properties
   - Ports, protocols, endpoints
   - Criticality indicators
   - Relationship categorization

3. **Dependency Chains**
   - Upstream chains (what this depends on)
   - Downstream chains (what depends on this)
   - Multi-hop dependency paths
   - Relationship types at each hop

4. **Enhanced Dependencies**
   - Traditional dependency view
   - Now includes attachment details
   - Backward compatible with existing code

### Example Output

```
================================================================================
 Enhanced Topology and Dependency Analysis Demo
================================================================================

Analyzing resource: my-app-service
API URL: http://localhost:8000

================================================================================
 Comprehensive Attachment Analysis
================================================================================

Resource: MyAppService (app_service)
Resource ID: my-app-service

📊 SUMMARY
  Total Attachments: 5
  Critical Attachments: 3
  Impact Radius: 12 resources
  Unique Relationship Types: 3
  Max Chain Length: 4

📈 ATTACHMENT BREAKDOWN BY TYPE
  DEPENDS_ON                Count:   2  Strength: 1.00
  CONNECTS_TO               Count:   1  Strength: 1.00
  ROUTES_TO                 Count:   2  Strength: 1.00

⚠️  CRITICAL ATTACHMENTS
  • MyAppService → MySQLDatabase
    Type: DEPENDS_ON
    Category: dependency
  • MyAppService → RedisCache
    Type: CONNECTS_TO
    Category: connectivity
  • LoadBalancer → MyAppService
    Type: ROUTES_TO
    Category: connectivity

🔗 DEPENDENCY CHAINS (showing first 3 of 5)
  1. MyAppService → MySQLDatabase → BackupJob → StorageAccount
  2. MyAppService → RedisCache
  3. LoadBalancer → MyAppService → MySQLDatabase
```

## Other Examples

### Simple Demo
**Script:** `simple_demo.py`

Basic demonstration of TopDeck discovery and query features.

### Multi-Cloud Discovery
**Script:** `multi_cloud_discovery.py`

Demonstrates discovering resources across multiple cloud providers.

### GitHub Integration
**Script:** `github_integration_example.py`

Shows how to integrate GitHub repositories and workflows.

### Phase 2/3 Examples
**Script:** `phase2_3_examples.py`

Examples from Phase 2 and Phase 3 development.

## Documentation

For more information about enhanced topology features:
- **[Enhanced Topology Analysis Guide](../docs/ENHANCED_TOPOLOGY_ANALYSIS.md)** - Complete documentation
- **[Topology Quick Reference](../docs/ENHANCED_TOPOLOGY_QUICK_REF.md)** - Quick commands and examples

## Getting Resource IDs

To find resource IDs for testing:

```bash
# Using curl
curl http://localhost:8000/api/v1/topology | jq '.nodes[].id'

# Using the Neo4j browser
# Navigate to http://localhost:7474
# Run: MATCH (r:Resource) RETURN r.id, r.name LIMIT 10
```

## Troubleshooting

**Error: Cannot connect to TopDeck API**
- Ensure TopDeck API is running: `make run`
- Check the API URL is correct
- Verify Neo4j is running: `docker-compose ps`

**Error: Resource not found**
- Verify the resource ID exists
- Run discovery to populate data
- Check Neo4j has data: `MATCH (r:Resource) RETURN count(r)`

**Empty results**
- Ensure relationships have been created between resources
- Run discovery and integration scripts
- Check Neo4j for relationships: `MATCH ()-[r]->() RETURN count(r)`
