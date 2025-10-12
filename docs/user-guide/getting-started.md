# Getting Started with TopDeck

This guide will help you get TopDeck up and running for development.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker Desktop** (version 20.10+)
- **Docker Compose** (version 2.0+)
- **Git**
- **Python 3.11+** or **Go 1.21+** (depending on final tech stack decision)
- **Node.js 18+** (for frontend development)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/MattVerwey/TopDeck.git
cd TopDeck
```

### 2. Start Infrastructure Services

Start Neo4j, Redis, and RabbitMQ using Docker Compose:

```bash
docker-compose up -d
```

This will start:
- Neo4j at `http://localhost:7474` (Bolt: `bolt://localhost:7687`)
- Redis at `localhost:6379`
- RabbitMQ at `http://localhost:15672` (Management UI)

**Default Credentials**:
- Neo4j: `neo4j` / `topdeck123`
- Redis: password is `topdeck123`
- RabbitMQ: `topdeck` / `topdeck123`

### 3. Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your cloud credentials:

```bash
# Azure
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_SUBSCRIPTION_ID=your-subscription-id

# Neo4j (already configured for local dev)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=topdeck123

# Redis (already configured for local dev)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=topdeck123
```

### 4. Install Dependencies

#### For Python Backend (if using Python)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### For Go Backend (if using Go)

```bash
# Install dependencies
go mod download
```

#### For Frontend

```bash
cd src/ui
npm install
```

### 5. Initialize Database

Run the database initialization script to create indexes and constraints:

```bash
# TBD: Will be added once implementation begins
python scripts/setup/init_database.py
```

### 6. Start the Application

#### Backend

```bash
# Python
python -m src.api.main

# Or Go
go run ./src/api/main.go
```

The API will be available at `http://localhost:8000`

#### Frontend

```bash
cd src/ui
npm run dev
```

The UI will be available at `http://localhost:3000`

## Verify Installation

### 1. Check Neo4j

Open Neo4j Browser at `http://localhost:7474`

Login with `neo4j` / `topdeck123`

Run a test query:
```cypher
MATCH (n) RETURN count(n);
```

### 2. Check Redis

```bash
redis-cli -a topdeck123 ping
# Should return: PONG
```

### 3. Check RabbitMQ

Open management UI at `http://localhost:15672`

Login with `topdeck` / `topdeck123`

### 4. Check API

```bash
curl http://localhost:8000/api/v1/health
```

Should return:
```json
{
  "status": "healthy",
  "services": {
    "neo4j": "connected",
    "redis": "connected",
    "rabbitmq": "connected"
  }
}
```

## Running Your First Discovery Scan

### 1. Configure Azure Access

Ensure your `.env` file has valid Azure credentials with at least Reader permissions.

### 2. Trigger a Discovery Scan

```bash
curl -X POST http://localhost:8000/api/v1/discovery/scan \
  -H "Content-Type: application/json" \
  -d '{
    "cloud_provider": "azure",
    "subscription_id": "your-subscription-id",
    "resource_types": ["aks", "app_service", "sql_database"]
  }'
```

### 3. Check Progress

```bash
curl http://localhost:8000/api/v1/discovery/status/SCAN_ID
```

### 4. View Results

Open the UI at `http://localhost:3000` and navigate to the Topology view.

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Edit code, add tests, and ensure everything works locally.

### 3. Run Tests

```bash
# Python
pytest tests/

# Go
go test ./...

# Frontend
cd src/ui && npm test
```

### 4. Run Linters

```bash
# Python
black src/
pylint src/

# Go
gofmt -w .
golint ./...

# Frontend
cd src/ui && npm run lint
```

### 5. Commit and Push

```bash
git add .
git commit -m "feat: your feature description"
git push origin feature/your-feature-name
```

### 6. Create Pull Request

Open a PR on GitHub and wait for review.

## Common Issues

### Neo4j Won't Start

**Issue**: Neo4j container fails to start

**Solution**: 
- Ensure port 7474 and 7687 are not in use
- Check Docker logs: `docker logs topdeck-neo4j`
- Increase memory allocation in Docker Desktop

### Cannot Connect to Redis

**Issue**: Connection refused to Redis

**Solution**:
- Ensure Redis container is running: `docker ps`
- Check if port 6379 is available
- Verify password in `.env` matches Docker Compose

### Discovery Scan Fails

**Issue**: Discovery scan returns errors

**Solution**:
- Verify Azure credentials are correct
- Ensure service principal has Reader role
- Check API logs for specific error messages
- Verify network connectivity to Azure

### Frontend Won't Load

**Issue**: UI shows blank page

**Solution**:
- Check browser console for errors
- Verify backend API is running
- Check CORS configuration
- Clear browser cache

## Next Steps

1. Read the [Architecture Documentation](../architecture/README.md)
2. Review [Contributing Guidelines](../../CONTRIBUTING.md)
3. Check [Open Issues](https://github.com/MattVerwey/TopDeck/issues)
4. Join our [Discussions](https://github.com/MattVerwey/TopDeck/discussions)

## Getting Help

- **Documentation**: Check the `/docs` directory
- **Issues**: Create an issue on GitHub
- **Discussions**: Ask questions in GitHub Discussions
- **Email**: Contact the maintainers

## Development Tools

### Recommended VS Code Extensions

- Python: `ms-python.python`
- Go: `golang.go`
- TypeScript: `ms-vscode.vscode-typescript-next`
- Docker: `ms-azuretools.vscode-docker`
- Neo4j: `neo4j.vscode-cypher`

### Useful Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop all services
docker-compose down

# Remove all data (careful!)
docker-compose down -v

# Run Neo4j shell
docker exec -it topdeck-neo4j cypher-shell -u neo4j -p topdeck123

# Run Redis CLI
docker exec -it topdeck-redis redis-cli -a topdeck123
```

## Performance Tips

1. **Use local cache**: Enable Redis caching for API responses
2. **Limit discovery scope**: Start with specific resource types
3. **Incremental updates**: Use delta sync for large subscriptions
4. **Parallel processing**: Configure worker count appropriately

## Security Notes

⚠️ **Important Security Reminders**:

1. Never commit `.env` file to Git
2. Rotate credentials regularly
3. Use least privilege for service principals
4. Enable audit logging
5. Review access logs regularly

---

**Happy Coding! 🚀**
