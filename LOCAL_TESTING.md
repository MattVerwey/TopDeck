# Local Testing with Live Data

This guide helps you test TopDeck locally with your own live cloud infrastructure data. By the end of this guide, you'll have TopDeck running on your machine, discovering and analyzing your real Azure, AWS, or GCP resources.

## 🎯 Quick Start (15 Minutes)

For the impatient, here's the fastest path to testing with live data:

```bash
# 1. Clone and setup
git clone https://github.com/MattVerwey/TopDeck.git
cd TopDeck

# 2. Start infrastructure
docker compose up -d

# 3. Configure credentials (see Configuration section below)
cp .env.example .env
# Edit .env with your cloud credentials

# 4. Install dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 5. Start TopDeck
make run

# 6. Access the UI
# Open http://localhost:8000/api/docs for API documentation
# Open http://localhost:7474 for Neo4j Browser
```

That's it! TopDeck will automatically discover your cloud resources on startup.

## 📋 Prerequisites

Before you begin, ensure you have:

1. **Docker and Docker Compose** (or `docker compose` v2)
   - Docker Desktop for Mac/Windows, or Docker Engine for Linux
   - Verify: `docker --version` and `docker compose version`

2. **Python 3.11 or higher**
   - Verify: `python --version`

3. **Cloud Provider Access** (at least one):
   - **Azure**: Service Principal with Reader role
   - **AWS**: IAM user with ReadOnlyAccess policy  
   - **GCP**: Service account with Viewer role

4. **Cloud Resources to Discover**:
   - At least a few resources deployed in your cloud provider
   - Can be development/test environment

## 🔧 Detailed Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/MattVerwey/TopDeck.git
cd TopDeck
```

### Step 2: Start Infrastructure Services

TopDeck requires Neo4j (graph database), Redis (cache), and RabbitMQ (message queue):

```bash
# Start all infrastructure services
docker compose up -d

# Verify services are running
docker compose ps

# You should see:
# - topdeck-neo4j (healthy)
# - topdeck-redis (healthy)
# - topdeck-rabbitmq (healthy)
```

**Troubleshooting:**
- If `docker compose` doesn't work, try `docker-compose` (older versions)
- If ports are already in use, edit `docker-compose.yml` to use different ports
- View logs: `docker compose logs -f`

### Step 3: Configure Cloud Credentials

Copy the example environment file and add your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your favorite text editor. Here are the key sections:

#### Azure Configuration

To get Azure credentials, you need a Service Principal:

```bash
# Create a service principal (one-time setup)
az ad sp create-for-rbac --name "topdeck-local-testing" \
  --role Reader \
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID

# This outputs:
# - appId (AZURE_CLIENT_ID)
# - password (AZURE_CLIENT_SECRET)
# - tenant (AZURE_TENANT_ID)
```

Add to `.env`:
```bash
# Enable Azure discovery
ENABLE_AZURE_DISCOVERY=true

# Azure credentials
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_SUBSCRIPTION_ID=your-subscription-id
```

#### AWS Configuration

Add to `.env`:
```bash
# Enable AWS discovery
ENABLE_AWS_DISCOVERY=true

# AWS credentials
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=us-east-1  # or your preferred region
```

#### GCP Configuration

Add to `.env`:
```bash
# Enable GCP discovery
ENABLE_GCP_DISCOVERY=true

# GCP credentials
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCP_PROJECT_ID=your-project-id
```

#### Discovery Settings

Configure how often TopDeck scans for resources:

```bash
# Discovery runs every 8 hours by default (28800 seconds)
DISCOVERY_SCAN_INTERVAL=28800

# For local testing, you might want more frequent updates:
# DISCOVERY_SCAN_INTERVAL=1800  # 30 minutes

# Number of parallel workers (increase for large infrastructures)
DISCOVERY_PARALLEL_WORKERS=5

# Discovery timeout
DISCOVERY_TIMEOUT=300  # 5 minutes
```

### Step 4: Install Python Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Verify Configuration

Before starting TopDeck, verify your configuration:

```bash
python scripts/verify_scheduler.py
```

Expected output:
```
============================================================
TOPDECK AUTOMATED DISCOVERY VERIFICATION
============================================================

✓ Azure Discovery: Configured
  Tenant ID: 12345678...
  Client ID: 87654321...
  Subscription ID: abcdef01...

✓ Scheduler is ready!
✓ Discovery enabled for: AZURE
✓ Scans will run every 8 hours
```

### Step 6: Start TopDeck

```bash
# Start the API server
make run

# Or manually:
# PYTHONPATH=src python -m topdeck
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

Discovery will start automatically on first startup!

## 🔍 Exploring Your Data

### Access Points

Once TopDeck is running, you can access:

1. **API Documentation**: http://localhost:8000/api/docs
   - Interactive API explorer (Swagger UI)
   - Test all endpoints directly in browser

2. **Neo4j Browser**: http://localhost:7474
   - Username: `neo4j`
   - Password: `topdeck123`
   - Visualize your resource graph

3. **RabbitMQ Management**: http://localhost:15672
   - Username: `topdeck`
   - Password: `topdeck123`
   - Monitor background jobs

### Query Your Resources

#### Using the API

```bash
# Get all discovered resources
curl http://localhost:8000/api/v1/topology | jq

# Count resources
curl http://localhost:8000/api/v1/topology | jq '.nodes | length'

# List resource types
curl http://localhost:8000/api/v1/topology | \
  jq '.nodes | group_by(.resource_type) | map({type: .[0].resource_type, count: length})'

# Get discovery status
curl http://localhost:8000/api/v1/discovery/status | jq

# Manually trigger discovery
curl -X POST http://localhost:8000/api/v1/discovery/trigger
```

#### Using Neo4j Browser

Navigate to http://localhost:7474 and run these Cypher queries:

```cypher
// View all resources
MATCH (n:Resource) RETURN n LIMIT 50

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

### Run Example Scripts

TopDeck includes several example scripts for testing features:

```bash
# Basic discovery demo
python examples/simple_demo.py

# Enhanced topology analysis
python examples/enhanced_topology_demo.py --resource-id <your-resource-id>

# Multi-cloud discovery
python examples/multi_cloud_discovery.py

# Risk analysis demo
python examples/risk_scoring_demo.py

# Error replay demo
python examples/error_replay_demo.py

# Prediction demo
python examples/prediction_example.py
```

**Note**: Replace `<your-resource-id>` with an actual resource ID from your Neo4j database.

To get resource IDs:
```bash
curl http://localhost:8000/api/v1/topology | jq '.nodes[].id'
```

## 🧪 Testing Scenarios

### Scenario 1: Basic Resource Discovery

Test that TopDeck can discover your resources:

```bash
# 1. Trigger discovery manually
curl -X POST http://localhost:8000/api/v1/discovery/trigger

# 2. Check status
curl http://localhost:8000/api/v1/discovery/status | jq

# 3. Wait for completion (watch the API logs)

# 4. Query resources
curl http://localhost:8000/api/v1/topology | jq '.nodes | length'

# 5. Compare with cloud provider
# Azure:
az resource list --query "length(@)"

# AWS:
aws ec2 describe-instances --query "Reservations[].Instances[].InstanceId" | jq 'length'
```

### Scenario 2: Dependency Analysis

Test dependency detection:

```bash
# Get a resource ID
RESOURCE_ID=$(curl -s http://localhost:8000/api/v1/topology | jq -r '.nodes[0].id')

# Get dependencies
curl "http://localhost:8000/api/v1/topology/resources/$RESOURCE_ID/dependencies" | jq

# Get dependency chains
curl "http://localhost:8000/api/v1/topology/resources/$RESOURCE_ID/chains" | jq

# Get comprehensive analysis
curl "http://localhost:8000/api/v1/topology/resources/$RESOURCE_ID/analysis" | jq
```

### Scenario 3: Risk Analysis

Test risk assessment:

```bash
# Get a resource ID
RESOURCE_ID=$(curl -s http://localhost:8000/api/v1/topology | jq -r '.nodes[0].id')

# Comprehensive risk analysis
curl "http://localhost:8000/api/v1/risk/resources/$RESOURCE_ID/comprehensive" | jq

# Check for single points of failure
curl "http://localhost:8000/api/v1/risk/spof" | jq

# Detect circular dependencies
curl "http://localhost:8000/api/v1/risk/dependencies/circular" | jq
```

### Scenario 4: Scheduled Discovery

Test automatic discovery:

```bash
# Set shorter interval for testing (5 minutes)
# Edit .env:
# DISCOVERY_SCAN_INTERVAL=300

# Restart TopDeck
# Ctrl+C to stop, then: make run

# Wait 5 minutes and check logs
# You should see discovery running automatically
```

### Scenario 5: Multi-Cloud Discovery

Test discovering from multiple cloud providers:

```bash
# Configure credentials for all providers in .env
# Enable all:
# ENABLE_AZURE_DISCOVERY=true
# ENABLE_AWS_DISCOVERY=true
# ENABLE_GCP_DISCOVERY=true

# Restart TopDeck
make run

# Check status
curl http://localhost:8000/api/v1/discovery/status | jq '.enabled_providers'

# Query multi-cloud topology
curl http://localhost:8000/api/v1/topology | \
  jq '.nodes | group_by(.cloud_provider) | map({provider: .[0].cloud_provider, count: length})'
```

## 📊 Monitoring and Debugging

### Check Service Health

```bash
# Simple health check
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8000/health/detailed | jq

# Or use the script
python scripts/health_check.py --detailed
```

### View Logs

```bash
# API logs (in terminal where you ran 'make run')
# Or redirect to file:
make run > topdeck.log 2>&1

# Docker service logs
docker compose logs -f neo4j
docker compose logs -f redis
docker compose logs -f rabbitmq
```

### Common Issues

#### Discovery Not Finding Resources

1. **Check credentials**:
   ```bash
   python scripts/verify_scheduler.py
   ```

2. **Verify permissions**:
   - Azure: Service principal needs `Reader` role
   - AWS: IAM user needs `ReadOnlyAccess` policy
   - GCP: Service account needs `Viewer` role

3. **Test cloud provider connectivity**:
   ```bash
   # Azure
   az account show
   
   # AWS
   aws sts get-caller-identity
   
   # GCP
   gcloud auth list
   ```

#### Resources Not Appearing in Neo4j

1. **Check Neo4j connection**:
   ```bash
   curl http://localhost:8000/health/detailed | jq '.components.neo4j'
   ```

2. **Verify Neo4j is running**:
   ```bash
   docker compose ps neo4j
   ```

3. **Check Neo4j directly**:
   - Open http://localhost:7474
   - Run: `MATCH (n) RETURN count(n)`

#### Discovery Taking Too Long

For large infrastructures (500+ resources):

```bash
# Edit .env:
DISCOVERY_TIMEOUT=600  # 10 minutes
DISCOVERY_PARALLEL_WORKERS=10

# Restart TopDeck
```

#### Port Conflicts

If ports 8000, 7474, 7687, 6379, 5672, or 15672 are already in use:

1. Edit `docker-compose.yml` to use different ports
2. Update `.env` with new port numbers
3. Restart: `docker compose down && docker compose up -d`

## 🚀 Next Steps

Once you have TopDeck running with your live data:

1. **Explore the Web UI**:
   ```bash
   cd frontend
   npm install
   npm run dev
   # Access at http://localhost:3000
   ```

2. **Try Advanced Features**:
   - Error replay and debugging
   - ML-based predictions
   - Change management
   - Reporting

3. **Integrate with CI/CD**:
   - Set up Azure DevOps integration
   - Connect GitHub repositories
   - Track deployments

4. **Customize for Your Needs**:
   - Create custom Cypher queries
   - Build custom dashboards
   - Integrate with your monitoring tools

## 📚 Additional Resources

- **[README.md](README.md)** - Full project overview
- **[QUICK_START.md](QUICK_START.md)** - 5-minute quick start
- **[TESTING_WITH_REAL_DATA.md](TESTING_WITH_REAL_DATA.md)** - Detailed testing guide
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Development workflow
- **[docs/AUTOMATED_DISCOVERY.md](docs/AUTOMATED_DISCOVERY.md)** - Discovery documentation
- **[docs/features/ENHANCED_TOPOLOGY_ANALYSIS.md](docs/features/ENHANCED_TOPOLOGY_ANALYSIS.md)** - Topology features
- **[docs/features/risk-analysis/ENHANCED_RISK_ANALYSIS.md](docs/features/risk-analysis/ENHANCED_RISK_ANALYSIS.md)** - Risk analysis features
- **[examples/README.md](examples/README.md)** - Example scripts

## 💡 Tips for Local Testing

1. **Start Small**: Begin with a single cloud provider and a small number of resources
2. **Use Frequent Scans**: Set `DISCOVERY_SCAN_INTERVAL=1800` (30 minutes) for faster iteration
3. **Monitor Logs**: Keep an eye on the API logs to catch issues early
4. **Test Incrementally**: Test each feature separately before combining
5. **Save Neo4j Snapshots**: Use Neo4j's export features to save your graph for testing
6. **Use Test Resources**: Create dedicated test resources in your cloud provider for safe experimentation

## 🆘 Getting Help

If you encounter issues:

1. **Check the documentation** in the `docs/` folder
2. **Run verification scripts**:
   - `python scripts/verify_scheduler.py`
   - `python scripts/health_check.py --detailed`
3. **Search existing issues**: https://github.com/MattVerwey/TopDeck/issues
4. **Open a new issue** with:
   - Error messages from logs
   - Output from verification scripts
   - Your cloud provider and resource count
   - Configuration settings (without credentials!)

---

**Happy Testing! 🎉**

For questions or feedback, open an issue on GitHub.
