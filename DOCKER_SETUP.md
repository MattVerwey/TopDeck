# TopDeck - Complete Docker Setup Guide

## 🎯 Overview

TopDeck is now fully dockerized with all services running in containers:

### Services

| Service | Container Name | Port | Description |
|---------|---------------|------|-------------|
| **Frontend** | `topdeck-frontend` | 3000 | React UI with Material-UI |
| **API** | `topdeck-api` | 8000 | Python FastAPI backend |
| **Neo4j** | `topdeck-neo4j` | 7474, 7687 | Graph database |
| **Redis** | `topdeck-redis` | 6379 | Cache |
| **RabbitMQ** | `topdeck-rabbitmq` | 5672, 15672 | Message queue |

## 🚀 Quick Start

### 1. Configure Environment

Edit `.env` file with your Azure credentials:

```bash
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_SUBSCRIPTION_ID=your-subscription-id

# Discovery enabled
ENABLE_AZURE_DISCOVERY=true
ENABLE_RISK_ANALYSIS=true
ENABLE_MONITORING=true
```

### 2. Start All Services

```powershell
# Build and start everything
docker-compose up -d --build

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **Neo4j Browser**: http://localhost:7474 (neo4j / topdeck123)
- **RabbitMQ Management**: http://localhost:15672 (topdeck / topdeck123)

## 📋 Common Commands

```powershell
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f api
docker-compose logs -f frontend

# Restart a service
docker-compose restart api

# Check service health
docker-compose ps
```

## 🔍 Health Checks

All services have health checks configured:

```powershell
# Check API health
curl http://localhost:8000/health

# Check detailed health (includes Neo4j, Redis, RabbitMQ)
curl http://localhost:8000/health/detailed

# Check API info and features
curl http://localhost:8000/api/info
```

## 🐛 Troubleshooting

### View Service Logs

```powershell
# API logs
docker-compose logs api

# Frontend logs
docker-compose logs frontend

# All logs
docker-compose logs
```

### Restart Services

```powershell
# Restart everything
docker-compose restart

# Restart specific service
docker-compose restart api
```

### Clean Restart

```powershell
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Rebuild and start fresh
docker-compose up -d --build
```

## 🔧 Development

### Code Changes

After making code changes:

```powershell
# Rebuild affected service
docker-compose up -d --build api
# or
docker-compose up -d --build frontend
```

### View Container Shell

```powershell
# Access API container
docker exec -it topdeck-api /bin/bash

# Access frontend container
docker exec -it topdeck-frontend /bin/sh

# Access Neo4j shell
docker exec -it topdeck-neo4j cypher-shell -u neo4j -p topdeck123
```

## 📊 Monitoring

### Check Resource Usage

```powershell
# View resource usage
docker stats

# View specific containers
docker stats topdeck-api topdeck-frontend
```

### Check Disk Usage

```powershell
# View Docker disk usage
docker system df

# View image sizes
docker images
```

## 🔒 Security Notes

1. **Change default passwords** before deploying to production
2. **Update `.env`** with secure credentials
3. **Enable SSL/TLS** for production deployments
4. **Configure CORS** appropriately in production
5. **Use secrets management** for sensitive data

## 📝 Configuration

### Environment Variables

All configuration is in `.env`:

- **Azure Credentials**: AZURE_TENANT_ID, AZURE_CLIENT_ID, etc.
- **Feature Flags**: ENABLE_AZURE_DISCOVERY, etc.
- **Service Credentials**: NEO4J_PASSWORD, REDIS_PASSWORD, etc.

### Docker Compose Override

Create `docker-compose.override.yml` for local customizations:

```yaml
services:
  api:
    environment:
      - LOG_LEVEL=DEBUG
    ports:
      - "8001:8000"  # Use different port
```

## 🎉 Success Indicators

When everything is working:

- ✅ All containers show "healthy" status
- ✅ Frontend accessible at http://localhost:3000
- ✅ API responds at http://localhost:8000/health
- ✅ Neo4j Browser works at http://localhost:7474
- ✅ Azure discovery runs every 8 hours (configurable)

## 📖 Next Steps

1. **Explore the UI**: Visit http://localhost:3000
2. **Check API Docs**: http://localhost:8000/api/docs
3. **View Topology**: Navigate to Topology view in the UI
4. **Trigger Discovery**: Use the API or wait for automatic discovery
5. **Analyze Risks**: Check the Risk Analysis page

---

## 🆘 Need Help?

- Check logs: `docker-compose logs -f`
- Check health: `docker-compose ps`
- Restart: `docker-compose restart`
- Clean slate: `docker-compose down && docker-compose up -d --build`
