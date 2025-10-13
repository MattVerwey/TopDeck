# TopDeck Quick Reference Guide

**Last Updated**: 2025-10-13

## 📊 Current Status at a Glance

| Phase | Status | Completion | Key Deliverables |
|-------|--------|-----------|------------------|
| **Phase 1: Foundation** | ✅ Complete | 100% | Azure discovery, data models, Neo4j schema |
| **Phase 2: Platform Integrations** | 🚧 In Progress | 50% | Azure DevOps ✅, GitHub pending |
| **Phase 3: Analysis & Intelligence** | 🎯 Next | 20% | Framework in place, features planned |
| **Phase 4: Multi-Cloud** | ✅ Foundation | 70% | AWS & GCP mappers ✅, orchestrators pending |
| **Phase 5: Production Ready** | 🔜 Planned | 40% | Partial - resilience, docs complete |

**Overall Progress**: ~50% Complete

---

## 🎯 What's Working Right Now

### Fully Operational Features ✅

1. **Azure Resource Discovery**
   - Discovers 14+ Azure resource types
   - Full SDK integration with multiple auth methods
   - Production-ready with resilience patterns
   - Rate limiting, retry logic, circuit breaker
   - Structured logging with correlation IDs

2. **Azure DevOps Integration**
   - Repository discovery with commit history
   - Build/deployment tracking from pipelines
   - Application inference from repositories
   - Rate limiting and error handling

3. **Multi-Cloud Support (Foundation)**
   - AWS mapper: 18+ resource types
   - GCP mapper: 17+ resource types
   - Unified Neo4j schema across clouds
   - Tag/label normalization

4. **Data Models & Storage**
   - Cloud-agnostic data models
   - Neo4j schema with 6 node types, 13 relationships
   - Complete CRUD operations
   - 34 indexes for performance

5. **Production Patterns**
   - Rate limiting (token bucket algorithm)
   - Retry with exponential backoff
   - Circuit breaker pattern
   - Error tracking for batch operations
   - Structured JSON logging

---

## 🚧 What's Coming Next

### High Priority (Next 2-4 weeks)

1. **GitHub Integration** (Issue #10)
   - Repository and workflow discovery
   - Deployment tracking
   - Cross-platform code-to-infrastructure mapping

2. **Topology Visualization** (Issue #6)
   - D3.js/Cytoscape.js interactive diagrams
   - Multi-cloud resource views
   - Relationship visualization

3. **Complete AWS/GCP Orchestrators**
   - Full SDK integration
   - Multi-region/project support
   - Integration tests

### Medium Priority (4-8 weeks)

4. **Risk Analysis Engine** (Issue #5)
   - Impact assessment
   - Change risk scoring
   - Blast radius calculation

5. **Monitoring Integration** (Issue #7)
   - API latency tracking
   - Performance metrics
   - Error correlation

---

## 📁 Key Files & Locations

### Getting Started
- `README.md` - Main project documentation
- `PROGRESS.md` - Detailed progress tracking
- `QUICK_START.md` - Quick setup guide
- `DEVELOPMENT.md` - Development guidelines

### Documentation
- `docs/PHASE_4_SUMMARY.md` - Multi-cloud implementation
- `docs/PHASE_2_3_SUMMARY.md` - Azure DevOps & resilience
- `docs/TASK_COMPLETION_SUMMARY.md` - Schema validation
- `docs/ROADMAP_CHANGES.md` - Roadmap evolution
- `docs/MULTI_CLOUD_CONFIGURATION.md` - Multi-cloud setup

### Architecture
- `docs/architecture/adr/001-technology-stack.md` - Tech stack decision
- `docs/architecture/data-models.md` - Complete data model reference
- `docs/architecture/neo4j-schema.cypher` - Neo4j schema

### Issue Reports
- `docs/issues/ISSUE-002-COMPLETION.md` - Data models complete
- `docs/issues/ISSUE-003-PROGRESS.md` - Azure discovery progress

### Source Code
- `src/topdeck/discovery/azure/` - Azure discovery module
- `src/topdeck/discovery/aws/` - AWS discovery module
- `src/topdeck/discovery/gcp/` - GCP discovery module
- `src/topdeck/discovery/models.py` - Core data models
- `src/topdeck/storage/neo4j_client.py` - Neo4j client
- `src/topdeck/common/resilience.py` - Resilience patterns
- `src/topdeck/common/logging_config.py` - Structured logging

### Tests
- `tests/discovery/azure/` - Azure discovery tests (20+ tests)
- `tests/discovery/aws/` - AWS mapper tests (21 tests)
- `tests/discovery/gcp/` - GCP mapper tests (25 tests)
- `tests/discovery/test_models.py` - Data model tests (240 lines)
- `tests/common/test_resilience.py` - Resilience pattern tests

---

## 🔧 Common Tasks

### Run Tests
```bash
# All tests
pytest

# Specific module
pytest tests/discovery/azure/
pytest tests/discovery/aws/
pytest tests/discovery/gcp/

# With coverage
pytest --cov=src/topdeck
```

### Azure Discovery Example
```python
from topdeck.discovery.azure import AzureDiscoverer
from topdeck.storage.neo4j_client import Neo4jClient

# Initialize
discoverer = AzureDiscoverer(subscription_id="...")
neo4j = Neo4jClient("bolt://localhost:7687", "neo4j", "password")

# Discover
result = await discoverer.discover_all_resources()

# Store in Neo4j
neo4j.connect()
for resource in result.resources:
    neo4j.upsert_resource(resource.to_neo4j_properties())
```

### Multi-Cloud Discovery Example
```python
from topdeck.discovery.azure import AzureDiscoverer
from topdeck.discovery.aws import AWSDiscoverer
from topdeck.discovery.gcp import GCPDiscoverer

# Initialize all
azure = AzureDiscoverer(subscription_id="...")
aws = AWSDiscoverer(access_key_id="...")
gcp = GCPDiscoverer(project_id="...")

# Discover in parallel
results = await asyncio.gather(
    azure.discover_all_resources(),
    aws.discover_all_resources(),
    gcp.discover_all_resources()
)
```

### Azure DevOps Integration Example
```python
from topdeck.discovery.azure.devops import AzureDevOpsDiscoverer

# Initialize
devops = AzureDevOpsDiscoverer(
    organization="myorg",
    pat="personal-access-token"
)

# Discover repositories
repos = await devops.discover_repositories(project="myproject")

# Discover deployments
deployments = await devops.discover_deployments(project="myproject")
```

---

## 📊 Supported Resources

### Azure (14+ types) ✅ Complete
- **Compute**: VMs, AKS, App Service
- **Databases**: SQL, PostgreSQL, MySQL, Cosmos DB
- **Storage**: Storage Accounts
- **Networking**: VNet, Load Balancers, NSG, App Gateway
- **Config**: Key Vault, Redis Cache

### AWS (18+ types) ✅ Mapper Complete
- **Compute**: EKS, EC2, Lambda, ECS
- **Databases**: RDS, DynamoDB, ElastiCache
- **Storage**: S3
- **Networking**: VPC, Subnets, Security Groups, Load Balancers
- **Config**: Secrets Manager, Parameter Store

### GCP (17+ types) ✅ Mapper Complete
- **Compute**: GKE, Compute Engine, Cloud Run, Cloud Functions, App Engine
- **Databases**: Cloud SQL, Spanner, Firestore, Memorystore
- **Storage**: Cloud Storage, BigQuery
- **Networking**: VPC, Subnets, Firewall, Load Balancers
- **Config**: Secret Manager, KMS

**Total**: 49+ resource types across all clouds

---

## 🎓 Learning Resources

### Getting Started
1. Read `README.md` for overview
2. Review `QUICK_START.md` for setup
3. Check `DEVELOPMENT.md` for dev workflow
4. Study `docs/architecture/adr/001-technology-stack.md` for tech choices

### Understanding the Code
1. `docs/architecture/data-models.md` - Data model reference
2. `src/topdeck/discovery/README.md` - Discovery module overview
3. `src/topdeck/discovery/azure/README.md` - Azure discovery guide
4. Module README files in each discovery folder

### Implementation Patterns
1. `docs/PHASE_2_3_SUMMARY.md` - Resilience patterns
2. `src/topdeck/common/resilience.py` - Code examples
3. Test files for usage examples
4. `examples/` directory for full scenarios

---

## 🔍 Quick Stats

### Code Metrics
- **Total Code**: 10,000+ lines
- **Tests**: 100+ tests, 2,000+ lines
- **Documentation**: 5,000+ lines
- **Test Coverage**: High across all modules

### Feature Breakdown
- ✅ **Complete**: Azure discovery, data models, Azure DevOps, multi-cloud mappers
- 🚧 **In Progress**: GitHub integration, topology visualization
- 🎯 **Next**: Risk analysis, monitoring integration
- 🔜 **Planned**: Advanced analytics, production hardening

### Resource Discovery
- **Azure**: 14+ types, fully operational
- **AWS**: 18+ types, mapper complete
- **GCP**: 17+ types, mapper complete
- **Total**: 49+ types across 3 clouds

---

## 💡 Tips & Best Practices

### Development
- Use virtual environment: `python -m venv venv`
- Install dev dependencies: `pip install -r requirements-dev.txt`
- Run pre-commit hooks: `pre-commit install`
- Use Makefile targets: `make test`, `make lint`, `make format`

### Testing
- Write tests for new features
- Follow existing test patterns
- Use fixtures from `tests/conftest.py`
- Aim for high coverage (>80%)

### Documentation
- Update README.md for major features
- Add module-level README files
- Document complex algorithms
- Keep PROGRESS.md updated

### Git Workflow
- Create feature branches: `feature/your-feature`
- Use conventional commits
- Keep commits focused and small
- Reference issues in commits

---

## 🆘 Getting Help

### Documentation
- Check `docs/` directory first
- Review module README files
- Read issue completion reports
- Check examples in `examples/`

### Issues & Questions
- Open an issue on GitHub
- Check existing issues first
- Tag with appropriate labels
- Provide context and examples

### Contact
- GitHub Issues: [MattVerwey/TopDeck/issues](https://github.com/MattVerwey/TopDeck/issues)
- GitHub Discussions: For questions and ideas

---

**Quick Links**:
- [Full Documentation](README.md)
- [Progress Tracking](PROGRESS.md)
- [Roadmap](docs/ROADMAP_CHANGES.md)
- [Contributing](CONTRIBUTING.md)

**Status**: 🚀 Active Development - ~50% Complete
