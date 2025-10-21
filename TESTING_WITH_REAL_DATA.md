# Testing TopDeck with Real Data

This guide walks you through testing TopDeck with real cloud infrastructure data using the new automated discovery feature.

## Prerequisites

Before you begin, ensure you have:

1. **Docker and Docker Compose** installed
2. **Python 3.11+** installed
3. **Cloud provider credentials** for at least one provider (Azure, AWS, or GCP)
4. **Permissions** to read cloud resources (Reader/Viewer role)

## Quick Start (5 Minutes)

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/MattVerwey/TopDeck.git
cd TopDeck

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials

Copy the example environment file and add your credentials:

```bash
# Copy example file
cp .env.example .env

# Edit with your favorite editor
nano .env  # or vim, code, etc.
```

**Example for Azure**:
```bash
# Enable Azure discovery
ENABLE_AZURE_DISCOVERY=true

# Azure credentials
AZURE_TENANT_ID=12345678-1234-1234-1234-123456789abc
AZURE_CLIENT_ID=87654321-4321-4321-4321-cba987654321
AZURE_CLIENT_SECRET=your-secret-here
AZURE_SUBSCRIPTION_ID=abcdef01-2345-6789-abcd-ef0123456789

# Neo4j configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=topdeck123

# Discovery settings
DISCOVERY_SCAN_INTERVAL=28800  # 8 hours
DISCOVERY_PARALLEL_WORKERS=5
```

### 3. Start Services

```bash
# Start Neo4j, Redis, and RabbitMQ
docker-compose up -d

# Wait for services to be ready (about 30 seconds)
sleep 30

# Verify services are running
docker-compose ps
```

### 4. Verify Configuration

Run the verification script to ensure everything is configured correctly:

```bash
python scripts/verify_scheduler.py
```

You should see output like:
```
============================================================
TOPDECK AUTOMATED DISCOVERY VERIFICATION
============================================================

============================================================
CREDENTIAL CHECK
============================================================

Azure Discovery: ✓ Configured
  Tenant ID: 12345678...
  Client ID: 87654321...
  Subscription ID: abcdef01...

...

✓ Scheduler is ready!
✓ Discovery enabled for: AZURE
✓ Scans will run every 8 hours
```

### 5. Start TopDeck API

```bash
# Start the API server
make run

# Or alternatively:
python -m topdeck
```

Watch the console output. You should see:
```
🚀 Starting TopDeck API v0.3.0
   Environment: development
   Port: 8000
   Log Level: INFO

INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Connected to Neo4j for scheduled discovery
INFO:     Discovery scheduler started with 8-hour interval
INFO:     Starting automated resource discovery
INFO:     Discovering Azure resources...
```

### 6. Monitor Discovery Progress

In another terminal, watch the discovery progress:

```bash
# Check scheduler status
curl http://localhost:8000/api/v1/discovery/status | jq

# Expected output:
{
  "scheduler_running": true,
  "discovery_in_progress": true,
  "last_discovery_time": null,
  "interval_hours": 8,
  "enabled_providers": {
    "azure": true,
    "aws": false,
    "gcp": false
  }
}
```

Wait for discovery to complete (typically 10-60 seconds depending on your infrastructure size).

### 7. Query Discovered Resources

Once discovery completes, query the topology:

```bash
# Get all resources
curl http://localhost:8000/api/v1/topology | jq

# Count resources
curl http://localhost:8000/api/v1/topology | jq '.nodes | length'

# List resource types
curl http://localhost:8000/api/v1/topology | jq '.nodes | group_by(.resource_type) | map({type: .[0].resource_type, count: length})'
```

### 8. Explore in Neo4j Browser

Open Neo4j Browser in your web browser:

1. Go to http://localhost:7474
2. Login with username `neo4j` and password `topdeck123`
3. Run Cypher queries:

```cypher
// View all resources
MATCH (n) RETURN n LIMIT 50

// Count resources by type
MATCH (n:Resource)
RETURN n.resource_type as Type, count(*) as Count
ORDER BY Count DESC

// View dependencies
MATCH (n)-[r:DEPENDS_ON]->(m)
RETURN n.name, type(r), m.name
LIMIT 20

// Find resources in a specific region
MATCH (n:Resource)
WHERE n.region = 'eastus'
RETURN n.name, n.resource_type

// Find all AKS clusters
MATCH (n:Resource)
WHERE n.resource_type = 'AKS'
RETURN n.name, n.properties
```

## Real-World Testing Scenarios

### Scenario 1: Multi-Cloud Discovery

Test discovery across multiple cloud providers:

**Configure multiple providers in `.env`**:
```bash
# Enable all providers
ENABLE_AZURE_DISCOVERY=true
ENABLE_AWS_DISCOVERY=true
ENABLE_GCP_DISCOVERY=true

# Add credentials for each
# ... Azure credentials ...
# ... AWS credentials ...
# ... GCP credentials ...
```

**Restart the API and verify**:
```bash
# Check status
curl http://localhost:8000/api/v1/discovery/status | jq '.enabled_providers'

# Expected:
{
  "azure": true,
  "aws": true,
  "gcp": true
}
```

### Scenario 2: Manual Discovery Trigger

Test manual discovery triggering:

```bash
# Trigger discovery manually
curl -X POST http://localhost:8000/api/v1/discovery/trigger | jq

# Expected response:
{
  "status": "scheduled",
  "message": "Discovery has been scheduled to run",
  "last_run": "2025-10-21T12:00:00"
}

# Try triggering again while discovery is running
curl -X POST http://localhost:8000/api/v1/discovery/trigger | jq

# Expected response:
{
  "status": "already_running",
  "message": "Discovery is already in progress"
}
```

### Scenario 3: Testing Scheduled Updates

Test that discovery runs automatically every 8 hours:

```bash
# Set a shorter interval for testing (5 minutes)
# Edit .env:
DISCOVERY_SCAN_INTERVAL=300  # 5 minutes

# Restart the API
# Wait 5 minutes and check logs

# You should see:
# INFO: Starting automated resource discovery
# INFO: Discovering Azure resources...
# INFO: Azure discovery completed: X resources
```

### Scenario 4: Resource Updates

Test that existing resources are updated:

1. Make a change to a resource in your cloud provider (e.g., add a tag)
2. Wait for next discovery run or trigger manually
3. Query the resource in Neo4j to verify the update

```bash
# Trigger discovery
curl -X POST http://localhost:8000/api/v1/discovery/trigger

# Wait for completion, then query
curl "http://localhost:8000/api/v1/topology" | jq '.nodes[] | select(.name == "your-resource-name")'
```

### Scenario 5: Large Infrastructure

Test with large infrastructure (500+ resources):

```bash
# Increase parallel workers for better performance
# Edit .env:
DISCOVERY_PARALLEL_WORKERS=10
DISCOVERY_TIMEOUT=600  # 10 minutes

# Restart API and monitor
tail -f logs/topdeck.log | grep "discovery"
```

## Verifying Data Quality

### Check Resource Count Matches Cloud Provider

**Azure**:
```bash
# Using Azure CLI
az resource list --query "length(@)"

# Compare with TopDeck
curl http://localhost:8000/api/v1/topology | jq '.nodes | length'
```

**AWS**:
```bash
# Using AWS CLI (example for EC2 instances)
aws ec2 describe-instances --query "Reservations[].Instances[].InstanceId" | jq 'length'

# Compare with TopDeck
curl http://localhost:8000/api/v1/topology | jq '[.nodes[] | select(.resource_type == "EC2")] | length'
```

### Validate Dependencies

Check that dependencies are correctly detected:

```bash
# Query Neo4j for resources with dependencies
curl http://localhost:8000/api/v1/topology | jq '.edges | length'

# Should be > 0 if you have resources with dependencies
```

### Check Resource Properties

Verify that important properties are captured:

```bash
# Get a sample resource with all properties
curl http://localhost:8000/api/v1/topology | jq '.nodes[0]'

# Should include:
# - id
# - resource_type
# - name
# - cloud_provider
# - region
# - properties (with cloud-specific details)
```

## Troubleshooting

### Discovery Not Finding Resources

1. **Check credentials**:
   ```bash
   python scripts/verify_scheduler.py
   ```

2. **Verify permissions**:
   - Azure: Service principal needs Reader role
   - AWS: IAM user needs ReadOnlyAccess policy
   - GCP: Service account needs Viewer role

3. **Check cloud provider console**:
   - Verify resources exist in the subscription/account
   - Check if resources are in expected regions

### Discovery Taking Too Long

1. **Increase timeout**:
   ```bash
   # In .env
   DISCOVERY_TIMEOUT=600  # 10 minutes
   ```

2. **Increase parallel workers**:
   ```bash
   # In .env
   DISCOVERY_PARALLEL_WORKERS=10
   ```

3. **Check network connectivity**:
   ```bash
   # Test connectivity to cloud provider APIs
   curl -I https://management.azure.com/  # Azure
   curl -I https://ec2.amazonaws.com/      # AWS
   ```

### Resources Not Appearing in Neo4j

1. **Check Neo4j connection**:
   ```bash
   curl http://localhost:8000/health/detailed | jq '.components.neo4j'
   ```

2. **Check Neo4j logs**:
   ```bash
   docker-compose logs neo4j
   ```

3. **Verify Neo4j is accessible**:
   ```bash
   # Connect with Neo4j Browser
   # http://localhost:7474
   
   # Or use cypher-shell
   docker exec -it topdeck-neo4j cypher-shell -u neo4j -p topdeck123
   ```

### Discovery Errors in Logs

Check the logs for specific error messages:

```bash
# View API logs
tail -f logs/topdeck.log

# Look for error patterns:
# - Authentication failed → Check credentials
# - Timeout → Increase DISCOVERY_TIMEOUT
# - Rate limit → Cloud provider API rate limiting
# - Network error → Check internet connectivity
```

## Performance Benchmarks

Expected performance for different infrastructure sizes:

| Infrastructure Size | Resources | Discovery Time | Notes |
|-------------------|-----------|----------------|-------|
| Small | 10-50 | 5-15 seconds | Single region, basic services |
| Medium | 50-200 | 15-45 seconds | Multi-region, diverse services |
| Large | 200-500 | 45-120 seconds | Complex topology, many dependencies |
| Extra Large | 500+ | 2-5 minutes | Enterprise scale, increase workers |

## Best Practices

### 1. Use Appropriate Scan Intervals

- **Development**: 5-15 minutes for rapid iteration
- **Staging**: 1-4 hours for regular updates
- **Production**: 8-12 hours to balance freshness with API load

### 2. Monitor Discovery Health

Set up monitoring to track:
- Discovery success rate
- Discovery duration
- Resource count trends
- Error rates

### 3. Optimize for Scale

For large infrastructures (500+ resources):
- Increase `DISCOVERY_PARALLEL_WORKERS` to 10-20
- Increase `DISCOVERY_TIMEOUT` to 600-900 seconds
- Consider running discovery off-hours to reduce API load

### 4. Review Logs Regularly

- Check for authentication errors
- Monitor for rate limiting
- Watch for timeout issues
- Review resource counts for unexpected changes

## Next Steps

Once you've verified that discovery works with real data:

1. **Explore the topology**: Use the API to query resources and dependencies
2. **Test risk analysis**: Try the risk analysis endpoints with real resources
3. **Build custom queries**: Create Cypher queries for your specific use cases
4. **Integrate with CI/CD**: Use discovery data in your deployment pipelines
5. **Set up monitoring**: Track discovery metrics and resource changes

## Support

If you encounter issues:

1. Check the [documentation](docs/AUTOMATED_DISCOVERY.md)
2. Run the [verification script](scripts/verify_scheduler.py)
3. Review [troubleshooting guide](#troubleshooting)
4. Open an [issue](https://github.com/MattVerwey/TopDeck/issues) with:
   - Error messages from logs
   - Output from verification script
   - Cloud provider and resource count
   - Discovery configuration settings
