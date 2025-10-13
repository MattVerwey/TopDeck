# TopDeck Scripts

Utility scripts for project setup, management, and testing.

## Available Scripts

### Testing Scripts

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
- `.env` file configured with Azure credentials
- Azure test infrastructure deployed (optional, for discovery)

**Output**: Services will remain running. Press Ctrl+C to stop.

#### test_discovery.py

**Azure Discovery Test Script** - Tests Azure resource discovery functionality.

**What it does**:
1. Loads Azure credentials from `.env`
2. Initializes Azure discoverer
3. Discovers resources in test resource group
4. Displays detailed results

**Usage**:
```bash
python scripts/test_discovery.py
```

**Prerequisites**:
- `.env` file configured with Azure credentials
- Azure test infrastructure deployed
- Virtual environment activated

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

### Project Management Scripts

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

- **[HOSTING_AND_TESTING_GUIDE.md](../docs/HOSTING_AND_TESTING_GUIDE.md)** - Complete guide for hosting and testing TopDeck
- **[AZURE_TESTING_GUIDE.md](../docs/AZURE_TESTING_GUIDE.md)** - Azure test infrastructure setup
- **[DEVELOPMENT.md](../DEVELOPMENT.md)** - Development workflow and setup

## Quick Start for Testing

```bash
# 1. Set up Azure test infrastructure (first time only)
cd scripts/azure-testing
./setup-azure-trial.sh
./deploy-test-infrastructure.sh
cd ../..

# 2. Configure environment
cp .env.example .env
# Edit .env with your Azure credentials

# 3. Run end-to-end test
./scripts/e2e-test.sh

# 4. Or test discovery only
python scripts/test_discovery.py
```

For detailed instructions, see [HOSTING_AND_TESTING_GUIDE.md](../docs/HOSTING_AND_TESTING_GUIDE.md).
