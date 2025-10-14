# Quick Deploy to Test Environment

**Goal**: Get TopDeck running in a test environment with Azure integration in 15 minutes.

---

## Prerequisites Checklist

- [ ] Docker Desktop installed and running
- [ ] Python 3.11+ installed
- [ ] Git installed
- [ ] Azure credentials available (tenant ID, client ID, client secret, subscription ID)

---

## Quick Start (15 minutes)

### 1. Clone and Setup (2 minutes)
```bash
git clone https://github.com/MattVerwey/TopDeck.git
cd TopDeck

# Create environment file
cp .env.example .env
```

### 2. Configure Credentials (3 minutes)
Edit `.env` file:
```bash
# Minimum required for Azure
AZURE_TENANT_ID=your-tenant-id-here
AZURE_CLIENT_ID=your-client-id-here
AZURE_CLIENT_SECRET=your-client-secret-here
AZURE_SUBSCRIPTION_ID=your-subscription-id-here

# Neo4j (default from docker-compose)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=topdeck123

# Feature flags
ENABLE_AZURE_DISCOVERY=true
ENABLE_RISK_ANALYSIS=true
ENABLE_GITHUB_INTEGRATION=false
ENABLE_AZURE_DEVOPS_INTEGRATION=false
```

### 3. Start Infrastructure (5 minutes)
```bash
# Start Neo4j, Redis, RabbitMQ
docker-compose up -d

# Wait for Neo4j to initialize (30-40 seconds)
echo "Waiting for Neo4j to start..."
sleep 40

# Verify services are running
docker-compose ps
```

Expected output:
```
NAME                  STATUS              PORTS
topdeck-neo4j         running (healthy)   0.0.0.0:7474->7474/tcp, 0.0.0.0:7687->7687/tcp
topdeck-redis         running (healthy)   0.0.0.0:6379->6379/tcp
topdeck-rabbitmq      running (healthy)   0.0.0.0:5672->5672/tcp, 0.0.0.0:15672->15672/tcp
```

### 4. Install and Run (3 minutes)
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install TopDeck
pip install -e .

# Start the API server
python -m topdeck
```

Expected output:
```
🚀 Starting TopDeck API v0.3.0
   Environment: development
   Port: 8000
   Log Level: INFO

INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 5. Test Discovery (2 minutes)
Open a new terminal:
```bash
# Activate virtual environment
cd TopDeck
source venv/bin/activate

# Run discovery
python scripts/test_discovery.py

# Expected: Discovers Azure resources and stores in Neo4j
```

---

## Verify Deployment

### Check API is Running
```bash
# Health check
curl http://localhost:8000/api/health

# Expected: {"status": "healthy"}
```

### Check API Documentation
Open browser: http://localhost:8000/api/docs

You should see:
- Swagger UI with all API endpoints
- Routes for topology, risk, monitoring, integrations

### Check Neo4j Browser
Open browser: http://localhost:7474

Login with:
- Username: `neo4j`
- Password: `topdeck123`

Run query:
```cypher
MATCH (r:Resource) RETURN r LIMIT 25;
```

Should see discovered Azure resources.

### Check Discovered Resources
```bash
# Query topology API
curl http://localhost:8000/api/v1/topology | jq

# Should return JSON with discovered resources
```

---

## Test Risk Analysis

### 1. Get a Resource ID
```bash
# List all resources
curl http://localhost:8000/api/v1/topology | jq '.[] | .id' | head -1

# Copy a resource ID
```

### 2. Analyze Risk
```bash
# Replace {resource_id} with actual ID
curl http://localhost:8000/api/v1/risk/resources/{resource_id} | jq

# Expected: Risk assessment with score, dependencies, recommendations
```

### 3. Check Single Points of Failure
```bash
curl http://localhost:8000/api/v1/risk/single-points-of-failure | jq

# Expected: List of resources with no redundancy
```

---

## Optional: Start Frontend

```bash
# In new terminal
cd TopDeck/frontend

# Install dependencies (first time only)
npm install

# Create frontend .env
echo "VITE_API_URL=http://localhost:8000" > .env

# Start development server
npm run dev

# Access at http://localhost:3000
```

---

## Troubleshooting

### Neo4j won't start
```bash
# Check logs
docker logs topdeck-neo4j

# Restart
docker-compose restart neo4j

# Wait 40 seconds then retry
```

### Azure authentication fails
```bash
# Verify credentials with Azure CLI
az login --service-principal \
  -u $AZURE_CLIENT_ID \
  -p $AZURE_CLIENT_SECRET \
  --tenant $AZURE_TENANT_ID

# Check subscription access
az account show
```

### No resources discovered
```bash
# Check Azure permissions
# Service principal needs "Reader" role on subscription

az role assignment list --assignee $AZURE_CLIENT_ID
```

### API won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill process or use different port
export APP_PORT=8001
python -m topdeck
```

---

## Integration Testing

### Test GitHub Integration
Add to `.env`:
```bash
GITHUB_TOKEN=your-personal-access-token
GITHUB_ORGANIZATION=your-org-name
ENABLE_GITHUB_INTEGRATION=true
```

Run integration:
```bash
python examples/github_integration.py
```

### Test Azure DevOps Integration
Add to `.env`:
```bash
AZURE_DEVOPS_ORGANIZATION=your-org
AZURE_DEVOPS_PAT=your-pat-token
ENABLE_AZURE_DEVOPS_INTEGRATION=true
```

Run integration:
```bash
python examples/azure_devops_integration.py
```

---

## Run E2E Test

```bash
# Automated end-to-end test
./scripts/e2e-test.sh

# This will:
# - Start services
# - Run discovery
# - Test API endpoints
# - Verify Neo4j data
# - Run integration tests
```

---

## Deployment Validation Checklist

- [ ] Docker services running (Neo4j, Redis, RabbitMQ)
- [ ] API server started on port 8000
- [ ] API health check returns healthy
- [ ] Swagger docs accessible
- [ ] Azure resources discovered
- [ ] Neo4j contains resource nodes
- [ ] Risk analysis API returns results
- [ ] Frontend accessible (if deployed)
- [ ] Integration tests pass (if configured)

---

## What to Test in Test Environment

### 1. Resource Discovery
- [ ] Discover Azure resources in your subscription
- [ ] Verify all resource types are discovered
- [ ] Check relationships are created correctly
- [ ] Validate metadata is captured

### 2. Risk Analysis
- [ ] Get risk assessment for critical resources
- [ ] Identify single points of failure
- [ ] Calculate blast radius for key resources
- [ ] Simulate failure scenarios
- [ ] Review recommendations

### 3. Integration
- [ ] Link GitHub repos to resources (if using GitHub)
- [ ] Link Azure DevOps pipelines (if using Azure DevOps)
- [ ] Track deployments
- [ ] Verify code-to-infrastructure mapping

### 4. API Testing
- [ ] Test all topology endpoints
- [ ] Test all risk analysis endpoints
- [ ] Test monitoring endpoints
- [ ] Verify response times
- [ ] Check error handling

### 5. Frontend Testing (if deployed)
- [ ] Navigate all pages
- [ ] Interact with topology graph
- [ ] View risk analysis charts
- [ ] Test filters and search
- [ ] Verify responsive design

---

## Next Steps After Deployment

1. **Monitor Performance**
   - Check API response times
   - Monitor Neo4j memory usage
   - Track discovery completion times

2. **Gather Feedback**
   - Test with real infrastructure
   - Validate risk scores accuracy
   - Identify missing features

3. **Iterate**
   - Adjust risk scoring weights if needed
   - Add missing resource types
   - Improve UI based on feedback

---

## Quick Reference

### Start Everything
```bash
docker-compose up -d && sleep 40
source venv/bin/activate
python -m topdeck
```

### Stop Everything
```bash
# Stop API (Ctrl+C in API terminal)
docker-compose down
```

### Reset Database
```bash
docker-compose down -v
docker-compose up -d
sleep 40
```

### View Logs
```bash
# API logs (in API terminal)

# Infrastructure logs
docker-compose logs -f neo4j
docker-compose logs -f redis
```

---

## Support

- **Full Guide**: [docs/HOSTING_AND_TESTING_GUIDE.md](docs/HOSTING_AND_TESTING_GUIDE.md)
- **Deployment Readiness**: [DEPLOYMENT_READINESS.md](DEPLOYMENT_READINESS.md)
- **Azure Setup**: [docs/AZURE_TESTING_GUIDE.md](docs/AZURE_TESTING_GUIDE.md)
- **API Docs**: http://localhost:8000/api/docs

---

**Time to Deploy**: ~15 minutes  
**Status**: ✅ Ready for test environment  
**Confidence**: High - All components tested and documented
