# TopDeck Examples

This directory contains example scripts and demonstrations for TopDeck features.

> **💡 New to TopDeck?** See **[LOCAL_TESTING.md](../LOCAL_TESTING.md)** for a complete guide to setting up and testing TopDeck with your own cloud data.

## Quick Start with Examples

### Prerequisites

Before running examples:

1. **TopDeck API server running**:
   ```bash
   # From repository root
   docker compose up -d  # Start infrastructure
   make run              # Start API server
   ```

2. **Resources discovered and loaded into Neo4j**:
   ```bash
   # Configure cloud credentials in .env first
   # Discovery runs automatically on startup, or trigger manually:
   curl -X POST http://localhost:8000/api/v1/discovery/trigger
   ```

3. **Install httpx** (if not already installed):
   ```bash
   pip install httpx
   ```

For detailed setup, see **[LOCAL_TESTING.md](../LOCAL_TESTING.md)**.

## Available Examples

### Enhanced Topology Analysis Demo

**Script:** `enhanced_topology_demo.py`

Demonstrates the enhanced topology and dependency analysis features.

**Usage**:
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

### Other Examples

#### Simple Demo
**Script:** `simple_demo.py`

Basic demonstration of TopDeck discovery and query features.

```bash
python examples/simple_demo.py
```

#### Multi-Cloud Discovery
**Script:** `multi_cloud_discovery.py`

Demonstrates discovering resources across multiple cloud providers.

```bash
# Configure all cloud providers in .env first
python examples/multi_cloud_discovery.py
```

#### GitHub Integration
**Script:** `github_integration_example.py`

Shows how to integrate GitHub repositories and workflows.

```bash
# Configure GITHUB_TOKEN in .env first
python examples/github_integration_example.py
```

#### Risk Scoring Demo
**Script:** `risk_scoring_demo.py`

Demonstrates risk analysis capabilities.

```bash
python examples/risk_scoring_demo.py
```

#### Error Replay Demo
**Script:** `error_replay_demo.py`

Shows error capture and replay features.

```bash
python examples/error_replay_demo.py
```

#### Prediction Demo
**Script:** `prediction_example.py`

Demonstrates ML-based prediction features.

```bash
python examples/prediction_example.py
```

## Getting Resource IDs

Many examples require a resource ID. Here's how to get one:

```bash
# Using curl
curl http://localhost:8000/api/v1/topology | jq '.nodes[].id'

# Using Neo4j browser
# Navigate to http://localhost:7474
# Run: MATCH (r:Resource) RETURN r.id, r.name LIMIT 10

# Save to variable
RESOURCE_ID=$(curl -s http://localhost:8000/api/v1/topology | jq -r '.nodes[0].id')
echo "Resource ID: $RESOURCE_ID"
```

## Documentation

For more information about TopDeck features:
- **[LOCAL_TESTING.md](../LOCAL_TESTING.md)** - ⭐ Complete local testing guide
- **[Enhanced Topology Analysis Guide](../docs/features/ENHANCED_TOPOLOGY_ANALYSIS.md)** - Complete topology documentation
- **[Topology Quick Reference](../docs/features/ENHANCED_TOPOLOGY_QUICK_REF.md)** - Quick commands and examples
- **[Enhanced Risk Analysis Guide](../docs/features/risk-analysis/ENHANCED_RISK_ANALYSIS.md)** - Risk analysis documentation
- **[README.md](../README.md)** - Full project overview

## Troubleshooting

**Error: Cannot connect to TopDeck API**
- Ensure TopDeck API is running: `make run`
- Check the API URL is correct (default: http://localhost:8000)
- Verify infrastructure services are running: `docker compose ps`

**Error: Resource not found**
- Verify the resource ID exists
- Run discovery to populate data: `curl -X POST http://localhost:8000/api/v1/discovery/trigger`
- Check Neo4j has data: 
  - Open http://localhost:7474
  - Run: `MATCH (r:Resource) RETURN count(r)`

**Empty results**
- Ensure discovery has completed: `curl http://localhost:8000/api/v1/discovery/status | jq`
- Check relationships exist: 
  - Open http://localhost:7474
  - Run: `MATCH ()-[r]->() RETURN count(r)`
- Verify cloud credentials are correct: `python scripts/verify_scheduler.py`

**Need more help?**
See [LOCAL_TESTING.md](../LOCAL_TESTING.md) for comprehensive troubleshooting.
