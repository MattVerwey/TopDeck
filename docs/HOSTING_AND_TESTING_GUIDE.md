# TopDeck Hosting and Testing Guide

**Last Updated**: 2025-10-13  
**Status**: Ready for Testing  
**Phase**: 2-3 Integration Testing

---

## Overview

This guide walks you through hosting the TopDeck application and testing it with the Azure test infrastructure. By following this guide, you'll have a fully operational TopDeck instance discovering and analyzing Azure resources.

**What You'll Accomplish**:
- ✅ Host the TopDeck API server locally
- ✅ Connect to Azure test infrastructure
- ✅ Discover Azure resources automatically
- ✅ Visualize infrastructure topology
- ✅ Test all integrated features end-to-end

---

## Prerequisites

### Required Software

1. **Docker Desktop** - For running infrastructure services
2. **Python 3.11+** - For running TopDeck application
3. **Git** - For cloning the repository
4. **Azure CLI** - For Azure authentication

### Azure Test Infrastructure

Before starting, ensure you have:
- ✅ Deployed Azure test infrastructure (see [AZURE_TESTING_GUIDE.md](AZURE_TESTING_GUIDE.md))
- ✅ Azure service principal credentials
- ✅ Test resource group deployed

If not, run:
```bash
cd scripts/azure-testing
./setup-azure-trial.sh
./deploy-test-infrastructure.sh
```

---

## Step 1: Environment Setup

### 1.1 Clone and Navigate

```bash
git clone https://github.com/MattVerwey/TopDeck.git
cd TopDeck
```

### 1.2 Create Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### 1.3 Install Dependencies

```bash
# Install the application
pip install -e .

# Install development dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock httpx
```

---

## Step 2: Infrastructure Services

### 2.1 Start Required Services

TopDeck requires Neo4j (graph database) and Redis (cache):

```bash
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# Check service health
docker-compose logs neo4j redis
```

**Expected Output**:
```
NAME                  STATUS              PORTS
topdeck-neo4j         Up (healthy)        7474/tcp, 7687/tcp
topdeck-redis         Up (healthy)        6379/tcp
topdeck-rabbitmq      Up (healthy)        5672/tcp, 15672/tcp
```

### 2.2 Verify Services

```bash
# Test Neo4j connection
docker exec -it topdeck-neo4j cypher-shell -u neo4j -p topdeck123 "RETURN 'OK' as status;"

# Test Redis connection
docker exec -it topdeck-redis redis-cli -a topdeck123 ping
```

Both should respond successfully.

---

## Step 3: Configure Azure Integration

### 3.1 Create Environment Configuration

Create a `.env` file with your Azure credentials:

```bash
# Copy the example
cp .env.example .env

# Edit with your credentials
nano .env  # or use your preferred editor
```

### 3.2 Required Azure Configuration

Add these values to your `.env` file:

```bash
# ============================================
# Azure Configuration (REQUIRED)
# ============================================
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_SUBSCRIPTION_ID=your-subscription-id

# ============================================
# Test Resource Group (from Azure setup)
# ============================================
TEST_RESOURCE_GROUP=topdeck-test-rg

# ============================================
# Neo4j Configuration (matches docker-compose)
# ============================================
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=topdeck123

# ============================================
# Redis Configuration (matches docker-compose)
# ============================================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=topdeck123
REDIS_DB=0

# ============================================
# Application Configuration
# ============================================
APP_ENV=development
APP_PORT=8000
LOG_LEVEL=INFO

# ============================================
# Feature Flags (enable what you want to test)
# ============================================
ENABLE_AZURE_DISCOVERY=true
ENABLE_AWS_DISCOVERY=false
ENABLE_GCP_DISCOVERY=false
ENABLE_GITHUB_INTEGRATION=false
ENABLE_AZURE_DEVOPS_INTEGRATION=false
ENABLE_RISK_ANALYSIS=true
ENABLE_MONITORING=true
```

### 3.3 Get Azure Credentials

If you need to get your service principal credentials:

```bash
# Source the configuration from Azure setup
source scripts/azure-testing/azure-setup.env

# Or manually retrieve from Azure
az ad sp list --display-name "TopDeck-ServicePrincipal" --query "[0].{appId:appId}"
```

---

## Step 4: Start the Application

### 4.1 Start TopDeck API Server

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Start the server
python -m topdeck
```

**Expected Output**:
```
🚀 Starting TopDeck API v0.1.0
   Environment: development
   Port: 8000
   Log Level: INFO

INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 4.2 Verify Application is Running

Open another terminal and test:

```bash
# Health check
curl http://localhost:8000/health

# API info
curl http://localhost:8000/api/info

# View API documentation
open http://localhost:8000/api/docs  # or visit in browser
```

---

## Step 5: Test Azure Resource Discovery

### 5.1 Run Simple Discovery Test

Create a test script `test_discovery.py`:

```python
#!/usr/bin/env python3
"""Test Azure resource discovery."""

import asyncio
import os
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
from topdeck.discovery.azure.discoverer import AzureDiscoverer

async def main():
    # Load environment
    load_dotenv()
    
    # Get credentials
    credential = ClientSecretCredential(
        tenant_id=os.getenv("AZURE_TENANT_ID"),
        client_id=os.getenv("AZURE_CLIENT_ID"),
        client_secret=os.getenv("AZURE_CLIENT_SECRET"),
    )
    
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    resource_group = os.getenv("TEST_RESOURCE_GROUP", "topdeck-test-rg")
    
    print("🔍 Starting Azure resource discovery...")
    print(f"   Subscription: {subscription_id}")
    print(f"   Resource Group: {resource_group}")
    print()
    
    # Create discoverer
    discoverer = AzureDiscoverer(credential, subscription_id)
    
    # Discover resources
    result = await discoverer.discover_resources(resource_group_filter=resource_group)
    
    # Display results
    print(f"✅ Discovery complete!")
    print(f"   Resources found: {result.resource_count}")
    print(f"   Dependencies found: {result.dependency_count}")
    print()
    
    if result.resources:
        print("📦 Discovered resources:")
        for resource in result.resources[:10]:  # Show first 10
            print(f"   - {resource.name} ({resource.resource_type})")
        if len(result.resources) > 10:
            print(f"   ... and {len(result.resources) - 10} more")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
python test_discovery.py
```

### 5.2 Expected Output

```
🔍 Starting Azure resource discovery...
   Subscription: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   Resource Group: topdeck-test-rg

✅ Discovery complete!
   Resources found: 5
   Dependencies found: 3

📦 Discovered resources:
   - topdeck-storage (storage_account)
   - topdeck-vnet (virtual_network)
   - topdeck-subnet (subnet)
   - topdeck-nsg (network_security_group)
   - topdeck-test-rg (resource_group)
```

---

## Step 6: Test API Endpoints

### 6.1 Test Topology Endpoints

```bash
# Get all topology
curl http://localhost:8000/api/v1/topology

# Get Azure resources
curl "http://localhost:8000/api/v1/topology?cloud_provider=azure"

# Get specific resource type
curl "http://localhost:8000/api/v1/topology/resources?resource_type=storage_account"
```

### 6.2 Test Monitoring Endpoints

```bash
# Check monitoring health
curl http://localhost:8000/api/v1/monitoring/health

# Get Prometheus metrics (if configured)
curl http://localhost:8000/api/v1/monitoring/prometheus/metrics
```

### 6.3 Interactive API Testing

1. Open browser to http://localhost:8000/api/docs
2. Try the interactive Swagger UI
3. Execute API calls directly from the browser
4. View request/response schemas

---

## Step 7: Run Integration Tests

### 7.1 Run Azure Integration Tests

```bash
# Run all integration tests
pytest tests/integration/azure/ -v

# Run specific test
pytest tests/integration/azure/test_infrastructure.py::test_resource_group_exists -v

# Run with detailed output
pytest tests/integration/azure/ -v -s
```

### 7.2 Run Full Test Suite

```bash
# Run all tests with coverage
pytest tests/ -v --cov=topdeck --cov-report=term-missing

# Run only unit tests (fast)
pytest tests/unit/ tests/discovery/ tests/analysis/ -v

# Run only integration tests (requires Azure)
pytest tests/integration/ -v -m integration
```

---

## Step 8: Access Web Interfaces

### 8.1 Neo4j Browser

1. Open http://localhost:7474
2. Login with:
   - Username: `neo4j`
   - Password: `topdeck123`
3. Run queries:

```cypher
// Count all resources
MATCH (r:Resource) RETURN count(r) as total_resources;

// Show all Azure resources
MATCH (r:Resource {cloud_provider: 'azure'})
RETURN r.name, r.resource_type, r.region
LIMIT 10;

// Show resource dependencies
MATCH (r1:Resource)-[rel:DEPENDS_ON]->(r2:Resource)
RETURN r1.name, type(rel), r2.name
LIMIT 20;

// Visualize topology
MATCH (r:Resource)
WHERE r.resource_group = 'topdeck-test-rg'
MATCH path = (r)-[*0..2]-(related)
RETURN path
LIMIT 50;
```

### 8.2 RabbitMQ Management

1. Open http://localhost:15672
2. Login with:
   - Username: `topdeck`
   - Password: `topdeck123`
3. Monitor queues and messages

### 8.3 TopDeck API Documentation

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- OpenAPI Spec: http://localhost:8000/api/openapi.json

---

## Step 9: End-to-End Testing Workflow

### Complete Test Scenario

```bash
# 1. Start infrastructure
docker-compose up -d

# 2. Start application
python -m topdeck &
sleep 5  # Wait for startup

# 3. Run discovery
python test_discovery.py

# 4. Query discovered resources
curl http://localhost:8000/api/v1/topology | jq

# 5. Check Neo4j
docker exec -it topdeck-neo4j cypher-shell -u neo4j -p topdeck123 \
  "MATCH (r:Resource) RETURN count(r) as total;"

# 6. Run integration tests
pytest tests/integration/azure/ -v

# 7. Stop application
pkill -f "python -m topdeck"

# 8. Review logs
docker-compose logs topdeck-neo4j
```

---

## Troubleshooting

### Application Won't Start

**Problem**: `ModuleNotFoundError` or import errors

**Solution**:
```bash
# Reinstall dependencies
pip install -e .
pip install -r requirements-dev.txt

# Verify installation
python -c "import topdeck; print(topdeck.__version__)"
```

### Can't Connect to Azure

**Problem**: Authentication errors

**Solution**:
```bash
# Test Azure credentials
az login
az account show

# Verify service principal
az ad sp show --id $AZURE_CLIENT_ID

# Test credentials directly
python -c "
from azure.identity import ClientSecretCredential
import os
from dotenv import load_dotenv
load_dotenv()
cred = ClientSecretCredential(
    os.getenv('AZURE_TENANT_ID'),
    os.getenv('AZURE_CLIENT_ID'),
    os.getenv('AZURE_CLIENT_SECRET')
)
token = cred.get_token('https://management.azure.com/.default')
print('✅ Authentication successful!')
"
```

### Neo4j Connection Failed

**Problem**: Can't connect to database

**Solution**:
```bash
# Check Neo4j is running
docker-compose ps neo4j

# Check Neo4j logs
docker-compose logs neo4j

# Restart Neo4j
docker-compose restart neo4j

# Test connection
docker exec -it topdeck-neo4j cypher-shell -u neo4j -p topdeck123 "RETURN 1;"
```

### No Resources Discovered

**Problem**: Discovery returns 0 resources

**Solution**:
```bash
# Verify Azure resources exist
az resource list --resource-group topdeck-test-rg --output table

# Check if resources were deployed
cd scripts/azure-testing
./validate-deployment.sh

# Verify permissions
az role assignment list --assignee $AZURE_CLIENT_ID --output table
```

### Port Already in Use

**Problem**: Port 8000 already in use

**Solution**:
```bash
# Use different port
export APP_PORT=8001
python -m topdeck

# Or find and kill the process using port
lsof -ti:8000 | xargs kill -9
```

---

## Performance Testing

### Load Testing Discovery

```python
#!/usr/bin/env python3
"""Load test discovery performance."""

import asyncio
import time
from topdeck.discovery.azure.discoverer import AzureDiscoverer
from azure.identity import ClientSecretCredential
import os
from dotenv import load_dotenv

async def benchmark_discovery():
    load_dotenv()
    
    credential = ClientSecretCredential(
        os.getenv("AZURE_TENANT_ID"),
        os.getenv("AZURE_CLIENT_ID"),
        os.getenv("AZURE_CLIENT_SECRET"),
    )
    
    discoverer = AzureDiscoverer(credential, os.getenv("AZURE_SUBSCRIPTION_ID"))
    
    print("🔄 Running 5 discovery iterations...")
    times = []
    
    for i in range(5):
        start = time.time()
        result = await discoverer.discover_resources(
            resource_group_filter=os.getenv("TEST_RESOURCE_GROUP", "topdeck-test-rg")
        )
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"   Iteration {i+1}: {elapsed:.2f}s ({result.resource_count} resources)")
    
    avg_time = sum(times) / len(times)
    print(f"\n📊 Average time: {avg_time:.2f}s")
    print(f"   Min: {min(times):.2f}s")
    print(f"   Max: {max(times):.2f}s")

if __name__ == "__main__":
    asyncio.run(benchmark_discovery())
```

---

## Next Steps

### Phase Completion

Now that you can host and test the application:

1. **Complete Phase 2**:
   - ✅ Azure DevOps integration working
   - ✅ GitHub integration working
   - ✅ Basic topology visualization API
   - 🔜 Frontend visualization (React + Cytoscape.js)

2. **Complete Phase 3**:
   - ✅ Monitoring integration
   - ✅ Performance optimization
   - 🔜 Risk analysis engine (Issue #5)
   - 🔜 Error correlation

3. **Move to Phase 4**:
   - AWS resource discovery
   - GCP resource discovery
   - Multi-cloud abstraction

### Production Deployment

For production deployment:

1. Review [AZURE_TESTING_GUIDE.md](AZURE_TESTING_GUIDE.md) for infrastructure
2. Set up proper secrets management (Azure Key Vault)
3. Configure monitoring (Application Insights)
4. Set up CI/CD pipelines
5. Review security best practices in [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## Related Documentation

- [AZURE_TESTING_GUIDE.md](AZURE_TESTING_GUIDE.md) - Azure infrastructure setup
- [DEVELOPMENT.md](../DEVELOPMENT.md) - Development workflow
- [QUICK_START.md](../QUICK_START.md) - Quick start guide
- [PHASE_2_IMPLEMENTATION.md](PHASE_2_IMPLEMENTATION.md) - Phase 2 features
- [PHASE_3_COMPLETION_SUMMARY.md](../PHASE_3_COMPLETION_SUMMARY.md) - Phase 3 features

---

## Support

**Issues?** 
- Check troubleshooting section above
- Review logs: `docker-compose logs`
- Check GitHub issues: https://github.com/MattVerwey/TopDeck/issues

**Questions?**
- Open a discussion: https://github.com/MattVerwey/TopDeck/discussions
- Read the docs: `/docs` directory

---

**Status**: ✅ Ready for Integration Testing  
**Last Updated**: 2025-10-13  
**Phase**: 2-3 (75-85% Complete)
