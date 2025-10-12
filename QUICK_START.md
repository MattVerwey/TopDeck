# TopDeck Quick Start Guide

Get TopDeck running in 5 minutes! ⚡

## 1️⃣ Prerequisites

Install these first:
- Docker Desktop
- Git
- A code editor (VS Code recommended)

## 2️⃣ Clone & Setup

```bash
# Clone the repository
git clone https://github.com/MattVerwey/TopDeck.git
cd TopDeck

# Copy environment template
cp .env.example .env

# Start infrastructure services
docker-compose up -d
```

## 3️⃣ Verify Services

Check that services are running:

```bash
# Check Docker containers
docker ps

# Test Neo4j (should return PONG)
docker exec -it topdeck-neo4j cypher-shell -u neo4j -p topdeck123 "RETURN 'PONG' as result;"

# Test Redis (should return PONG)
docker exec -it topdeck-redis redis-cli -a topdeck123 ping
```

## 4️⃣ Access Services

Open these URLs in your browser:

- **Neo4j Browser**: http://localhost:7474
  - Username: `neo4j`
  - Password: `topdeck123`

- **RabbitMQ Management**: http://localhost:15672
  - Username: `topdeck`
  - Password: `topdeck123`

## 5️⃣ Next Steps

### For Developers

1. **Review Documentation**
   ```bash
   # Read the getting started guide
   cat docs/user-guide/getting-started.md
   
   # Review architecture
   cat docs/architecture/system-architecture.md
   ```

2. **Pick an Issue**
   - Check `docs/issues/` for development tasks
   - Start with Issue #1 (Technology Stack Decision)

3. **Set up your environment**
   - Install Python 3.11+ or Go 1.21+
   - Install Node.js 18+ (for frontend)
   - Configure your IDE

### For Contributors

1. Read `CONTRIBUTING.md`
2. Check [open issues](https://github.com/MattVerwey/TopDeck/issues)
3. Join [discussions](https://github.com/MattVerwey/TopDeck/discussions)

## 🆘 Troubleshooting

**Services won't start?**
```bash
# Check Docker logs
docker-compose logs

# Restart services
docker-compose restart

# Clean start (removes data!)
docker-compose down -v
docker-compose up -d
```

**Port conflicts?**
Edit `docker-compose.yml` to use different ports.

**Need help?**
Create an issue or start a discussion on GitHub.

## 📚 Key Documents

- `README.md` - Full project overview
- `docs/PROJECT_SETUP_SUMMARY.md` - What's been created
- `docs/user-guide/getting-started.md` - Detailed setup guide
- `CONTRIBUTING.md` - How to contribute

## 🎯 Development Phases

We're currently in **Phase 0: Planning**

**Phase 1** (Weeks 1-2): Foundation
- Decide tech stack
- Design data models
- Set up project structure

**Phase 2** (Weeks 2-4): Discovery
- Azure resource discovery
- Azure DevOps integration

**Phase 3** (Weeks 5-8): Analysis
- Risk analysis engine
- Topology visualization

**Phase 4** (Weeks 7-10): Monitoring
- Performance monitoring
- Error correlation

## 🚀 Quick Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Check status
docker-compose ps

# Access Neo4j shell
docker exec -it topdeck-neo4j cypher-shell -u neo4j -p topdeck123

# Access Redis CLI
docker exec -it topdeck-redis redis-cli -a topdeck123
```

---

**Ready to build something amazing? Let's go! 🚀**
