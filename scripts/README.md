# TopDeck Scripts

Utility scripts for testing, setup, and management.

> **💡 New to TopDeck?** See **[LOCAL_TESTING.md](../LOCAL_TESTING.md)** for a complete guide to testing TopDeck with your own cloud data.

## Quick Reference

### For Local Testing

```bash
# Verify your setup is ready
python scripts/verify_scheduler.py

# Check API health
python scripts/health_check.py --detailed

# Test discovery
python scripts/test_discovery.py

# Run end-to-end test
./scripts/e2e-test.sh
```

For detailed local testing instructions, see **[LOCAL_TESTING.md](../LOCAL_TESTING.md)**.

## Available Scripts

### Testing Scripts

#### verify_scheduler.py

**Configuration Verification Script** - Verifies your TopDeck configuration is correct before starting.

**What it does**:
1. Checks cloud provider credentials (Azure, AWS, GCP)
2. Verifies database connections (Neo4j, Redis, RabbitMQ)
3. Validates discovery configuration
4. Reports what will be discovered

**Usage**:
```bash
python scripts/verify_scheduler.py
```

**Prerequisites**:
- `.env` file configured
- Virtual environment activated

**Example Output**:
```
============================================================
TOPDECK AUTOMATED DISCOVERY VERIFICATION
============================================================

✓ Azure Discovery: Configured
  Tenant ID: 12345678...
  Client ID: 87654321...
  Subscription ID: abcdef01...

✓ Neo4j: Connected
✓ Redis: Connected
✓ RabbitMQ: Connected

✓ Scheduler is ready!
✓ Discovery enabled for: AZURE
✓ Scans will run every 8 hours
```

#### health_check.py

**Health Check Script** - Tests if TopDeck API is running and all components are healthy.

**What it does**:
1. Checks API server is responding
2. Tests Neo4j connection
3. Tests Redis connection
4. Tests RabbitMQ connection
5. Reports overall health status

**Usage**:
```bash
# Basic health check
python scripts/health_check.py

# Detailed health check
python scripts/health_check.py --detailed
```

**Prerequisites**:
- TopDeck API running (`make run`)

**Example Output**:
```
✓ TopDeck API is healthy!

Components:
  ✓ Neo4j: healthy
  ✓ Redis: healthy
  ✓ RabbitMQ: healthy
```

#### e2e-test.sh

**End-to-End Testing Script** - Performs a complete test of TopDeck from start to finish.

**What it does**:
1. Checks prerequisites (Docker, Python, curl)
2. Starts infrastructure services (Neo4j, Redis, RabbitMQ)
3. Starts the TopDeck API server
4. Tests all API endpoints
5. Runs Azure discovery (if configured)
6. Verifies data in Neo4j
7. Runs integration tests
8. Displays service URLs

**Usage**:
```bash
./scripts/e2e-test.sh
```

**Prerequisites**:
- Docker and Docker Compose installed
- Python 3.11+ installed
- `.env` file configured (optional - only needed for live cloud resource discovery)
- Cloud resources deployed (optional - for testing with live data)

**Output**: Services will remain running. Press Ctrl+C to stop.

**See also**: [LOCAL_TESTING.md](../LOCAL_TESTING.md) for detailed testing scenarios.

#### test_discovery.py

**Azure Discovery Test Script** - Tests Azure resource discovery functionality.

**What it does**:
1. Loads Azure credentials from `.env`
2. Initializes Azure discoverer
3. Discovers resources in test resource group
4. Displays detailed results

**Usage**:
```bash
# Test discovery with configured cloud provider
python scripts/test_discovery.py

# The script will use credentials from .env
```

**Prerequisites**:
- `.env` file configured with cloud credentials (see [LOCAL_TESTING.md](../LOCAL_TESTING.md))
- Cloud test infrastructure deployed (or any existing resources)
- Virtual environment activated
- Neo4j running (`docker compose up -d`)

**Example Output**:
```
🔍 TopDeck Azure Resource Discovery Test
========================================

   Subscription: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   Resource Group: topdeck-test-rg

✅ Resources found: 5
✅ Dependencies found: 3

📦 DISCOVERED RESOURCES
   storage_account (1):
      - topdeck-storage
   virtual_network (1):
      - topdeck-vnet
```

### Demonstration Scripts

The `examples/` directory contains demonstration scripts for testing TopDeck features. See [examples/README.md](../examples/README.md) for details.

Quick demos:
```bash
# Simple discovery demo
python examples/simple_demo.py

# Enhanced topology demo
python examples/enhanced_topology_demo.py --resource-id <id>

# Risk analysis demo
python examples/risk_scoring_demo.py
```

## Local Testing Workflow

For comprehensive local testing with your own cloud data:

### 1. Initial Setup

```bash
# Verify configuration
python scripts/verify_scheduler.py

# Start services
docker compose up -d

# Start TopDeck
make run
```

### 2. Verify Everything Works

```bash
# Check API health
python scripts/health_check.py --detailed

# Test discovery
python scripts/test_discovery.py
```

### 3. Explore Your Data

```bash
# Query topology
curl http://localhost:8000/api/v1/topology | jq

# Check discovery status
curl http://localhost:8000/api/v1/discovery/status | jq
```

### 4. Run Examples

```bash
# Get a resource ID
RESOURCE_ID=$(curl -s http://localhost:8000/api/v1/topology | jq -r '.nodes[0].id')

# Run topology demo
python examples/enhanced_topology_demo.py --resource-id $RESOURCE_ID

# Run risk demo
python examples/risk_scoring_demo.py
```

For detailed instructions, see **[LOCAL_TESTING.md](../LOCAL_TESTING.md)**.

## Project Management Scripts

#### create-github-issues.sh

Creates GitHub issues from the templates in `docs/issues/`.

**Prerequisites**:
- GitHub CLI (`gh`) must be installed
- You must be authenticated with `gh auth login`
- You must have write access to the repository

**Usage**:
```bash
./scripts/create-github-issues.sh
```

This will create all 10 issues from the templates:
- **Phase 1** (Issues #1-3): Foundation
- **Phase 2** (Issues #4, #6, #10): Platform Integrations
- **Phase 3** (Issues #5, #7): Analysis & Intelligence
- **Phase 4** (Issues #8-9): Multi-Cloud Architecture

**Labels Used**:
- `enhancement` - For new features
- `architecture` - For architectural decisions
- `discovery` - For resource discovery features
- `integration` - For CI/CD integrations
- `visualization` - For UI/dashboard features
- `analysis` - For risk analysis features
- `monitoring` - For monitoring integrations
- `ui` - For user interface work
- `cloud: azure` - Azure-specific work
- `cloud: aws` - AWS-specific work
- `cloud: gcp` - GCP-specific work
- `priority: high` - High priority items
- `priority: medium` - Medium priority items
- `phase-1` through `phase-4` - Development phases

**Note**: You may need to create these labels in your repository first if they don't exist.

## Manual Issue Creation

If you prefer to create issues manually:

1. Go to https://github.com/MattVerwey/TopDeck/issues/new
2. Copy the content from the relevant file in `docs/issues/`
3. Use the title from the first line (without the `#`)
4. Add the labels listed on line 3
5. Submit the issue

## Creating Labels

To create all necessary labels at once:

```bash
# Create priority labels
gh label create "priority: high" --color "d73a4a" --description "High priority"
gh label create "priority: medium" --color "fbca04" --description "Medium priority"
gh label create "priority: low" --color "0e8a16" --description "Low priority"

# Create phase labels
gh label create "phase-1" --color "1d76db" --description "Phase 1: Foundation"
gh label create "phase-2" --color "1d76db" --description "Phase 2: Platform Integrations"
gh label create "phase-3" --color "1d76db" --description "Phase 3: Analysis & Intelligence"
gh label create "phase-4" --color "1d76db" --description "Phase 4: Multi-Cloud Architecture"

# Create cloud provider labels
gh label create "cloud: azure" --color "0078d4" --description "Azure-specific"
gh label create "cloud: aws" --color "ff9900" --description "AWS-specific"
gh label create "cloud: gcp" --color "4285f4" --description "GCP-specific"

# Create component labels
gh label create "discovery" --color "bfdadc" --description "Resource discovery"
gh label create "integration" --color "bfdadc" --description "CI/CD integration"
gh label create "analysis" --color "bfdadc" --description "Risk analysis"
gh label create "visualization" --color "bfdadc" --description "Visualization"
gh label create "monitoring" --color "bfdadc" --description "Monitoring"
gh label create "ui" --color "bfdadc" --description "User interface"
gh label create "architecture" --color "bfdadc" --description "Architecture decisions"
```

## Related Documentation

- **[LOCAL_TESTING.md](../LOCAL_TESTING.md)** - ⭐ **Complete local testing guide**
- **[TESTING_WITH_REAL_DATA.md](../TESTING_WITH_REAL_DATA.md)** - Advanced testing scenarios
- **[QUICK_START.md](../QUICK_START.md)** - 5-minute quick start
- **[DEVELOPMENT.md](../DEVELOPMENT.md)** - Development workflow and setup
- **[examples/README.md](../examples/README.md)** - Example scripts documentation

## Quick Start for Local Testing

The fastest way to test TopDeck with your cloud data:

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your cloud credentials

# 2. Verify setup
python scripts/verify_scheduler.py

# 3. Start services
docker compose up -d

# 4. Start TopDeck (in separate terminal)
make run

# 5. Test everything works
python scripts/health_check.py --detailed
python scripts/test_discovery.py
```

For detailed step-by-step instructions, see **[LOCAL_TESTING.md](../LOCAL_TESTING.md)**.

## Troubleshooting

### verify_scheduler.py shows credential errors

- Check your `.env` file has correct credentials
- For Azure: Verify service principal has Reader role
- For AWS: Verify IAM user has ReadOnlyAccess policy
- For GCP: Verify service account has Viewer role

### health_check.py fails

- Ensure TopDeck API is running: `make run`
- Verify services are running: `docker compose ps`
- Check logs: `docker compose logs`

### test_discovery.py finds no resources

- Verify you have resources deployed in your cloud provider
- Check credentials have access to those resources
- Ensure resources are in the configured subscription/project/account

For more troubleshooting help, see [LOCAL_TESTING.md](../LOCAL_TESTING.md#troubleshooting).
