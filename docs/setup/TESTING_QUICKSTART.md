# TopDeck Testing Quick Start

**Last Updated**: 2025-10-13  
**Audience**: Developers and QA

---

## 🚀 Quick Start (5 Minutes)

Get TopDeck running and tested in 5 minutes:

```bash
# 1. Clone and setup
git clone https://github.com/MattVerwey/TopDeck.git
cd TopDeck
cp .env.example .env

# 2. Install Python dependencies
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
pip install pytest pytest-asyncio pytest-cov pytest-mock httpx

# 3. Run end-to-end test
./scripts/e2e-test.sh
```

That's it! The script will:
- ✅ Start all infrastructure services
- ✅ Start the TopDeck API
- ✅ Test all endpoints
- ✅ Display service URLs

---

## 📋 Testing Options

### Option 1: End-to-End Test (Recommended)

**Full automated test of entire system**

```bash
./scripts/e2e-test.sh
```

**What it tests**:
- Infrastructure services (Neo4j, Redis, RabbitMQ)
- API server startup and health
- All API endpoints
- Azure discovery (if configured)
- Data storage in Neo4j
- Integration tests

**Duration**: ~2-3 minutes  
**Prerequisites**: Docker, Python 3.11+  
**Azure Required**: No (but optional for discovery)

### Option 2: Azure Discovery Test

**Test Azure resource discovery only**

```bash
# Configure Azure credentials in .env first
python scripts/test_discovery.py
```

**What it tests**:
- Azure authentication
- Resource discovery
- Dependency detection
- Data parsing

**Duration**: ~30 seconds  
**Prerequisites**: Azure credentials in `.env`  
**Azure Required**: Yes

### Option 3: Unit Tests

**Fast tests without external dependencies**

```bash
# Run all unit tests
pytest tests/unit/ tests/discovery/ tests/analysis/ -v

# Run with coverage
pytest tests/unit/ --cov=topdeck --cov-report=term-missing

# Run specific module
pytest tests/discovery/test_models.py -v
```

**What it tests**:
- Data models
- Business logic
- Utilities
- Parsers

**Duration**: ~10-30 seconds  
**Prerequisites**: Python dependencies only  
**Azure Required**: No

### Option 4: Integration Tests

**Tests requiring live services**

```bash
# Start services first
docker-compose up -d

# Run integration tests
pytest tests/integration/ -v

# Run Azure integration tests (requires credentials)
pytest tests/integration/azure/ -v
```

**What it tests**:
- Neo4j operations
- Redis caching
- Azure SDK calls
- API endpoints

**Duration**: ~1-2 minutes  
**Prerequisites**: Docker + services running  
**Azure Required**: Only for Azure tests

### Option 5: Manual Testing

**Test the API interactively**

```bash
# Start services
docker-compose up -d

# Start API
python -m topdeck

# In another terminal, test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/info
curl http://localhost:8000/api/v1/topology

# Or open browser to:
# http://localhost:8000/api/docs
```

---

## 🧪 Test Scenarios

### Scenario 1: New Developer Setup

```bash
# Clone and install
git clone https://github.com/MattVerwey/TopDeck.git
cd TopDeck
python -m venv venv
source venv/bin/activate
pip install -e .
pip install pytest pytest-asyncio pytest-cov pytest-mock httpx

# Run unit tests to verify setup
pytest tests/unit/ -v

# Start services and API
docker-compose up -d
python -m topdeck

# Test API
curl http://localhost:8000/health
```

**Success**: Health check returns `{"status": "healthy"}`

### Scenario 2: Azure Integration Testing

```bash
# Prerequisites: Azure test infrastructure deployed
# See: docs/AZURE_TESTING_GUIDE.md

# Configure credentials
cp .env.example .env
# Edit .env with Azure credentials

# Test discovery
python scripts/test_discovery.py

# Expected: Shows discovered resources
```

**Success**: Discovers resources in test resource group

### Scenario 3: Full System Test

```bash
# One command to test everything
./scripts/e2e-test.sh

# Or step by step:
docker-compose up -d
python -m topdeck &
sleep 5
curl http://localhost:8000/health
python scripts/test_discovery.py
pytest tests/integration/ -v
```

**Success**: All services running, API responding, tests passing

### Scenario 4: CI/CD Pipeline Test

```bash
# Same tests that run in GitHub Actions

# Unit tests
pytest tests/unit/ tests/discovery/ tests/analysis/ \
  --cov=topdeck --cov-report=xml

# Integration tests (with services)
docker-compose up -d
pytest tests/integration/ -v

# Cleanup
docker-compose down -v
```

**Success**: All tests pass, coverage report generated

---

## 🎯 Test Checklist

Use this checklist to verify TopDeck is working:

### Basic Functionality
- [ ] Repository cloned and dependencies installed
- [ ] Docker Compose services start successfully
- [ ] Neo4j accessible at http://localhost:7474
- [ ] Redis responding to ping
- [ ] API server starts without errors
- [ ] Health endpoint returns healthy status
- [ ] API documentation accessible at /api/docs

### Unit Tests
- [ ] Model tests pass
- [ ] Discovery tests pass
- [ ] Analysis tests pass
- [ ] Common utility tests pass

### Integration Tests
- [ ] Neo4j client tests pass
- [ ] Redis cache tests pass
- [ ] API route tests pass

### Azure Integration (if configured)
- [ ] Azure credentials configured in .env
- [ ] Azure authentication works
- [ ] Resources discovered successfully
- [ ] Data stored in Neo4j
- [ ] Dependencies detected

### API Endpoints
- [ ] GET /health returns 200
- [ ] GET /api/info returns version
- [ ] GET /api/v1/topology returns data
- [ ] Swagger UI loads at /api/docs

---

## 📊 Test Coverage

Current test coverage (as of 2025-10-13):

- **Unit Tests**: 120+ tests
- **Integration Tests**: 15+ tests
- **Total LOC Tested**: ~8,000 lines
- **Coverage**: ~70-80% (varies by module)

Key tested modules:
- ✅ Discovery (Azure, AWS, GCP mappers)
- ✅ Data models
- ✅ API routes
- ✅ Common utilities (resilience, logging, caching)
- ✅ Analysis (topology, flow detection)
- ✅ Monitoring (Prometheus, Loki collectors)

---

## 🐛 Troubleshooting Tests

### Tests Fail with Import Errors

```bash
# Reinstall package
pip install -e .

# Verify installation
python -c "import topdeck; print(topdeck.__version__)"
```

### Docker Services Won't Start

```bash
# Check Docker is running
docker ps

# Check logs
docker-compose logs

# Clean restart
docker-compose down -v
docker-compose up -d
```

### Azure Tests Fail

```bash
# Verify credentials
az login
az account show

# Test authentication
python -c "
from azure.identity import ClientSecretCredential
from dotenv import load_dotenv
import os
load_dotenv()
cred = ClientSecretCredential(
    os.getenv('AZURE_TENANT_ID'),
    os.getenv('AZURE_CLIENT_ID'),
    os.getenv('AZURE_CLIENT_SECRET')
)
print('✅ Auth works')
"
```

### API Tests Timeout

```bash
# Check API is running
curl http://localhost:8000/health

# Check API logs
# If started with python -m topdeck, check console output

# Increase timeout in test
pytest tests/api/ -v --timeout=60
```

---

## 📚 Related Documentation

- **[HOSTING_AND_TESTING_GUIDE.md](HOSTING_AND_TESTING_GUIDE.md)** - Comprehensive hosting guide
- **[AZURE_TESTING_GUIDE.md](AZURE_TESTING_GUIDE.md)** - Azure infrastructure setup
- **[DEVELOPMENT.md](../DEVELOPMENT.md)** - Development workflow
- **[scripts/README.md](../scripts/README.md)** - Available scripts

---

## 🎓 Learning Path

### Day 1: Setup and Unit Tests
1. Clone repository
2. Install dependencies
3. Run unit tests
4. Explore code structure

### Day 2: Integration Testing
1. Start Docker services
2. Run integration tests
3. Explore Neo4j browser
4. Test API endpoints

### Day 3: Azure Integration
1. Set up Azure trial
2. Deploy test infrastructure
3. Configure credentials
4. Run discovery tests

### Day 4: End-to-End Testing
1. Run full e2e test
2. Monitor services
3. Query Neo4j data
4. Test API workflows

---

**Need Help?**
- Check [Troubleshooting](#troubleshooting-tests) section
- Review [HOSTING_AND_TESTING_GUIDE.md](HOSTING_AND_TESTING_GUIDE.md)
- Open an issue on GitHub
- Join discussions

---

**Status**: ✅ Ready for Testing  
**Last Updated**: 2025-10-13
