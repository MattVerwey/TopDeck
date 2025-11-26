# TopDeck Quick Start Guide

Get TopDeck running in 5 minutes! ⚡

> **💡 For Local Testing with Live Data**: See **[LOCAL_TESTING.md](LOCAL_TESTING.md)** for a comprehensive guide to testing TopDeck with your own cloud resources.

## 1️⃣ Prerequisites

Install these first:
- **Docker Desktop** (or Docker Engine + Docker Compose)
- **Python 3.11+**
- **Git**
- **Cloud credentials** (optional, for live data discovery)

## 2️⃣ Clone & Setup

```bash
# Clone the repository
git clone https://github.com/MattVerwey/TopDeck.git
cd TopDeck

# Copy environment template
cp .env.example .env
# Edit .env with your cloud credentials (optional for now)

# Start infrastructure services (Neo4j, Redis, RabbitMQ)
docker compose up -d
# Note: Use 'docker-compose' if 'docker compose' doesn't work
```

## 3️⃣ Install Python Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 4️⃣ Verify Services

Check that infrastructure services are running:

```bash
# Check Docker containers
docker compose ps

# You should see:
# - topdeck-neo4j (healthy)
# - topdeck-redis (healthy)
# - topdeck-rabbitmq (healthy)
```

Optional verification:
```bash
# Test Neo4j (should return PONG)
docker exec -it topdeck-neo4j cypher-shell -u neo4j -p topdeck123 "RETURN 'PONG' as result;"

# Test Redis (should return PONG)
docker exec -it topdeck-redis redis-cli -a topdeck123 ping
```

## 5️⃣ Start TopDeck

```bash
# Start the API server
make run

# Or manually:
# PYTHONPATH=src python -m topdeck
```

TopDeck will start and automatically discover resources if you configured cloud credentials.

## 6️⃣ Access TopDeck

Open these URLs in your browser:

- **API Documentation**: http://localhost:8000/api/docs
  - Interactive API explorer (Swagger UI)
  
- **Neo4j Browser**: http://localhost:7474
  - Username: `neo4j`
  - Password: `topdeck123`
  - Visualize your resource graph

- **RabbitMQ Management**: http://localhost:15672
  - Username: `topdeck`
  - Password: `topdeck123`

## 7️⃣ Test with Sample Data

If you haven't configured cloud credentials yet, you can still test TopDeck:

```bash
# Run example scripts
python examples/simple_demo.py

# Or run the end-to-end test
./scripts/e2e-test.sh
```

## 8️⃣ Next Steps

### Test with Your Live Cloud Data

**See [LOCAL_TESTING.md](LOCAL_TESTING.md) for the complete guide!**

Quick steps:
1. Configure cloud credentials in `.env`
2. Restart TopDeck: `make run`
3. TopDeck will automatically discover your resources
4. Query your data: `curl http://localhost:8000/api/v1/topology | jq`

### Explore the Features

```bash
# Get all resources
curl http://localhost:8000/api/v1/topology | jq

# Check discovery status
curl http://localhost:8000/api/v1/discovery/status | jq

# Trigger manual discovery
curl -X POST http://localhost:8000/api/v1/discovery/trigger

# Get a resource and analyze it
RESOURCE_ID=$(curl -s http://localhost:8000/api/v1/topology | jq -r '.nodes[0].id')
curl "http://localhost:8000/api/v1/risk/resources/$RESOURCE_ID/comprehensive" | jq
```

### For Developers

1. **Read the documentation**:
   - [LOCAL_TESTING.md](LOCAL_TESTING.md) - Local testing guide
   - [DEVELOPMENT.md](DEVELOPMENT.md) - Development workflow
   - [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines

2. **Pick an issue**:
   - Check [open issues](https://github.com/MattVerwey/TopDeck/issues)

3. **Set up development environment**:
   - Install development dependencies: `make install-dev`
   - Run tests: `make test`
   - Run linters: `make lint`

## 🆘 Troubleshooting

**Services won't start?**
```bash
# Check Docker logs
docker compose logs

# Restart services
docker compose restart

# Clean start (removes data!)
docker compose down -v
docker compose up -d
```

**Port conflicts?**
- Edit `docker-compose.yml` to use different ports
- Common conflicts: 8000 (API), 7474/7687 (Neo4j), 6379 (Redis), 5672/15672 (RabbitMQ)

**Python import errors?**
```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Install dependencies again
pip install -r requirements.txt
```

**Need help?**
- Check [LOCAL_TESTING.md](LOCAL_TESTING.md) for detailed troubleshooting
- Create an issue on [GitHub](https://github.com/MattVerwey/TopDeck/issues)
- Check existing [discussions](https://github.com/MattVerwey/TopDeck/discussions)

## 📚 Key Documentation

- **[LOCAL_TESTING.md](LOCAL_TESTING.md)** - ⭐ Complete local testing guide
- **[README.md](README.md)** - Full project overview
- **[TESTING_WITH_REAL_DATA.md](TESTING_WITH_REAL_DATA.md)** - Real data testing guide
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Development workflow
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute
- **[docs/](docs/)** - Detailed feature documentation

## 🎯 Development Phases

We're currently in **Phase 0: Planning**

**Phase 1** (Weeks 1-2): Foundation
- Decide tech stack
- Design data models
- Set up project structure
- Azure resource discovery

**Phase 2** (Weeks 3-4): Platform Integrations
- Azure DevOps integration
- GitHub integration
- Deployment tracking

**Phase 3** (Weeks 5-6): Analysis & Intelligence
- Risk analysis engine
- Topology visualization
- Performance monitoring

**Phase 4** (Weeks 7-10): Multi-Cloud Architecture
- AWS resource discovery
- GCP resource discovery
- Multi-cloud abstraction

## 🚀 Quick Commands

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Check service status
docker compose ps

# Start TopDeck API
make run

# Run tests
make test

# Access Neo4j shell
docker exec -it topdeck-neo4j cypher-shell -u neo4j -p topdeck123

# Access Redis CLI
docker exec -it topdeck-redis redis-cli -a topdeck123

# Query TopDeck API
curl http://localhost:8000/api/v1/topology | jq
curl http://localhost:8000/api/v1/discovery/status | jq
```

---

**Ready to test with your live data? See [LOCAL_TESTING.md](LOCAL_TESTING.md)! 🚀**
