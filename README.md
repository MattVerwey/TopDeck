# TopDeck - Multi-Cloud Integration & Risk Analysis Platform

TopDeck is an intelligent multi-cloud integration platform designed to provide comprehensive visibility into cloud infrastructure, application deployments, and their interdependencies. It helps organizations understand their application topology, data flows, and assess risks associated with changes across multi-cloud environments.

## 🎯 Vision & Purpose

**TopDeck is "Air Traffic Control" for your cloud deployments.**

### The Core Problem We Solve

Modern cloud applications are complex webs of services, databases, and infrastructure. When you need to:
- Deploy an update to a service
- Take down infrastructure for maintenance  
- Investigate why something broke

You need to answer: **"What will this affect?"** and **"What depends on this?"**

TopDeck provides that answer by:
1. **Discovering** your cloud resources and application deployments
2. **Mapping** the dependencies between services, databases, and infrastructure
3. **Analyzing** the risk and blast radius of changes
4. **Visualizing** the complete topology so you can see what's connected

### Real-World Use Case

**Before TopDeck:**
- "Can I restart this database?" → Hope for the best or spend hours tracing dependencies
- "What broke after that deployment?" → Manual log diving across multiple services
- "Is this API endpoint critical?" → Guesswork based on tribal knowledge

**With TopDeck:**
- See immediately that 5 services depend on that database
- Visualize the entire dependency chain in one view
- Get a risk score showing this is a critical component
- Understand the blast radius before making changes

## 📚 Documentation Quick Links

### Getting Started
- **[Quick Start Guide](QUICK_START.md)** - Get started in 5 minutes
- **[Deploy to Test Environment](DEPLOY_TO_TEST.md)** - 15-minute test deployment guide
- **[Testing Quick Start](docs/TESTING_QUICKSTART.md)** - Test TopDeck in 5 minutes
- **[Development Guide](DEVELOPMENT.md)** - Development workflow and guidelines
- **[Automated Discovery](docs/AUTOMATED_DISCOVERY.md)** - ✨ NEW! Automatic 8-hour resource discovery
- **[App & Check Enhancements](docs/APP_CHECK_ENHANCEMENTS.md)** - ✨ NEW! CLI arguments, health checks, and security scanning

### Topology & Dependencies (NEW!)
- **[Enhanced Topology Analysis Guide](docs/ENHANCED_TOPOLOGY_ANALYSIS.md)** - Complete in-depth topology and dependency analysis
- **[Topology Analysis Quick Reference](docs/ENHANCED_TOPOLOGY_QUICK_REF.md)** - Quick commands and examples

### Risk Analysis
- **[Enhanced Risk Analysis Guide](docs/ENHANCED_RISK_ANALYSIS.md)** - Complete in-depth risk analysis documentation
- **[Enhanced Dependency Analysis Guide](docs/ENHANCED_DEPENDENCY_ANALYSIS.md)** - ✨ NEW! Circular dependencies, health scoring, and cascading failures
- **[Risk Analysis Quick Reference](docs/ENHANCED_RISK_ANALYSIS_QUICK_REF.md)** - Quick commands and examples
- **[Phase 3 Completion Summary](PHASE_3_RISK_ANALYSIS_COMPLETION.md)** - Original risk analysis implementation

### Deployment & Readiness
- **[Executive Summary](docs/archive/DEPLOYMENT_STATUS_SUMMARY.md)** - Quick status overview (2 min read)
- **[Deployment Answer](docs/archive/DEPLOYMENT_ANSWER.md)** - Direct answer to "Is it ready?" (5 min read)
- **[Deploy to Test Environment](DEPLOY_TO_TEST.md)** - 15-minute deployment guide ⚡
- **[Deployment Readiness Assessment](DEPLOYMENT_READINESS.md)** - Complete readiness evaluation
- **[Deployment Decision Flowchart](docs/DEPLOYMENT_DECISION_FLOWCHART.md)** - Decision support tool
- **[Hosting and Testing Guide](docs/HOSTING_AND_TESTING_GUIDE.md)** - Complete guide for hosting and testing
- **[Azure Testing Guide](docs/AZURE_TESTING_GUIDE.md)** - Azure test infrastructure setup
- **[Scripts Documentation](scripts/README.md)** - Available testing and management scripts

### Project Status
- **[Progress Tracking](PROGRESS.md)** - Detailed status of all phases and issues
- **[Quick Reference](QUICK_REFERENCE.md)** - Quick reference for common tasks
- **[Roadmap Changes](docs/ROADMAP_CHANGES.md)** - Roadmap evolution and rationale
- **[Contributing](CONTRIBUTING.md)** - How to contribute to TopDeck

## 🏗️ Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    TopDeck Platform                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  Discovery  │  │  Integration │  │  Risk Analysis   │   │
│  │   Engine    │  │    Layer     │  │     Engine       │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
│         │                 │                   │              │
│         └─────────────────┴───────────────────┘              │
│                          │                                   │
│  ┌───────────────────────┴────────────────────────────┐     │
│  │          Dependency Graph & Topology Store         │     │
│  └────────────────────────────────────────────────────┘     │
│                          │                                   │
│  ┌───────────────────────┴────────────────────────────┐     │
│  │     Visualization & Reporting Dashboard            │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
         │                  │                  │
         ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Azure        │  │ AWS          │  │ Code Repos   │
│ - AKS        │  │ - EKS        │  │ - GitHub     │
│ - App Svc    │  │ - EC2        │  │ - Azure      │
│ - SQL DB     │  │ - RDS        │  │   DevOps     │
│ - App Gw     │  │ - ALB        │  │ - GitLab     │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Key Features

1. **Cloud Resource Discovery**
   - Scan Azure, AWS, GCP resources
   - Identify compute (AKS, App Service, VMs, EC2, GKE)
   - Map networking (Load Balancers, Application Gateways, VPCs)
   - Track data stores (SQL DB, Cosmos DB, RDS, DynamoDB)

2. **Code-to-Infrastructure Mapping**
   - Parse CI/CD pipelines (Azure DevOps, GitHub Actions)
   - Analyze application code for dependencies
   - Extract connection strings and JVM options
   - Link deployments to infrastructure

3. **Network Topology Mapping**
   - Build complete network flow diagrams
   - Identify service-to-service communication
   - Map data flow paths
   - Track external dependencies

4. **Risk Analysis Engine**
   - Impact assessment: "What depends on this?"
   - Change risk scoring
   - Blast radius calculation
   - Failure scenario simulation

5. **Performance Monitoring Integration**
   - Multiple log platforms supported: Prometheus/Grafana, Elasticsearch, Azure Log Analytics, Loki
   - API latency tracking
   - Database deadlock detection
   - Error correlation analysis
   - Root cause identification
   - Transaction tracing across services

## 🚀 Example Use Case

**Scenario**: Application deployed from Azure DevOps to AKS

```
[Azure DevOps Pipeline]
         ↓
    [AKS Cluster]
         ↓
[Load Balancer] → [Application Gateway]
         ↓
  [Application Pods]
         ↓
   [SQL Database]
```

**TopDeck Analysis**:
- Maps entire deployment flow
- Identifies that Application Gateway is a single point of failure
- Shows SQL Database is shared with 3 other services
- Calculates that updating the app affects 5 dependent services
- Highlights that recent SQL deadlocks occurred during peak traffic

## 📊 Network Flow Diagrams

TopDeck provides comprehensive network flow diagrams showing how data flows through cloud infrastructure. See **[Network Flow Diagrams](docs/architecture/network-flow-diagrams.md)** for detailed patterns including:

- **Pod → Load Balancer → Gateway → Storage** data flows
- Azure patterns (Application Gateway, AKS, hub-spoke topology)
- AWS patterns (ALB + EKS, Lambda serverless)
- GCP patterns (Global Load Balancing, Cloud Run)
- Multi-cloud flows and security patterns

These diagrams provide the foundation for TopDeck's interactive topology visualization.

## 📁 Project Structure

```
TopDeck/
├── docs/                           # Documentation
│   ├── architecture/               # Architecture diagrams and decisions
│   │   ├── network-flow-diagrams.md # Complete network flow patterns
│   │   └── topology-examples.md    # Real-world topology examples
│   ├── api/                        # API documentation
│   └── user-guide/                 # User guides and tutorials
├── src/
│   ├── discovery/                  # Cloud resource discovery
│   │   ├── azure/                  # Azure-specific discovery
│   │   ├── aws/                    # AWS-specific discovery
│   │   ├── gcp/                    # GCP-specific discovery
│   │   └── common/                 # Common discovery interfaces
│   ├── integration/                # Code repository integration
│   │   ├── azure-devops/           # Azure DevOps integration
│   │   ├── github/                 # GitHub integration
│   │   └── common/                 # Common integration interfaces
│   ├── analysis/                   # Risk analysis and topology
│   │   ├── topology/               # Topology mapping
│   │   ├── risk/                   # Risk assessment engine
│   │   └── dependencies/           # Dependency graph builder
│   ├── monitoring/                 # Performance monitoring integration
│   │   ├── metrics/                # Metrics collection
│   │   └── alerts/                 # Alert correlation
│   ├── api/                        # REST API
│   │   ├── controllers/            # API controllers
│   │   └── models/                 # Data models
│   ├── ui/                         # Web dashboard
│   │   ├── components/             # React components
│   │   └── pages/                  # Page components
│   └── storage/                    # Data persistence
│       ├── graph/                  # Graph database layer
│       └── cache/                  # Caching layer
├── tests/
│   ├── unit/                       # Unit tests
│   ├── integration/                # Integration tests
│   └── e2e/                        # End-to-end tests
├── infrastructure/                 # Infrastructure as Code
│   ├── terraform/                  # Terraform configurations
│   └── kubernetes/                 # Kubernetes manifests
├── scripts/                        # Utility scripts
│   ├── setup/                      # Setup scripts
│   └── migrations/                 # Database migrations
├── .github/
│   ├── workflows/                  # GitHub Actions workflows
│   └── ISSUE_TEMPLATE/             # Issue templates
├── README.md                       # This file
├── CONTRIBUTING.md                 # Contribution guidelines
├── LICENSE                         # License information
└── .gitignore                      # Git ignore rules
```

## 🛠️ Technology Stack

**Status**: Decision made in [ADR-001: Technology Stack Selection](docs/architecture/adr/001-technology-stack.md)

### Backend
- **Language**: Python 3.11+
- **API Framework**: FastAPI with Pydantic
- **Graph Database**: Neo4j 5.x for topology and dependency graphs
- **Cache**: Redis 7.x for performance
- **Message Queue**: RabbitMQ 3.x for async processing

### Frontend
- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite
- **Visualization**: D3.js and Cytoscape.js for network diagrams
- **UI Library**: Tailwind CSS with shadcn/ui

### Cloud SDKs
- **Azure**: Azure SDK for Python
- **AWS**: Boto3
- **GCP**: Google Cloud SDK

### CI/CD Integration
- Azure DevOps REST API
- GitHub REST API & GraphQL
- GitLab API (future)

### Monitoring & Observability
- **Prometheus** - Metrics collection and monitoring
- **Grafana** - Visualization and dashboards
- **Elasticsearch** - Log aggregation and search (supports Elastic Stack)
- **Azure Log Analytics** - Azure-native log analytics
- **Loki** - Log aggregation for Kubernetes

**Flexible Log Platform Support**: TopDeck works with your existing observability stack. You don't need Prometheus or Grafana - use Elasticsearch, Azure Log Analytics, or any combination that fits your infrastructure.

**Rationale**: After evaluating both Python and Go through proof-of-concept implementations, Python was selected for its superior cloud SDK support, faster development velocity, and rich ecosystem. See the [ADR](docs/architecture/adr/001-technology-stack.md) for complete analysis.

## 🚀 Deployment Status

**✅ READY FOR TEST ENVIRONMENT DEPLOYMENT**

TopDeck has reached a significant milestone and is **ready to be deployed to a test environment** with full integration capabilities:

- ✅ **Azure Discovery**: Fully functional (14+ resource types)
- ✅ **Risk Analysis**: Complete engine with scoring and recommendations
- ✅ **CI/CD Integration**: GitHub and Azure DevOps working
- ✅ **Interactive UI**: React dashboard with 5 main views
- ✅ **API Server**: FastAPI with comprehensive endpoints
- ✅ **Documentation**: Complete deployment and testing guides

**See [DEPLOYMENT_READINESS.md](DEPLOYMENT_READINESS.md) for complete assessment** or **[DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md) for 15-minute deployment guide**.

---

## 💡 What Can You Do With TopDeck Today?

### Current Capabilities (v0.3)

**1. Discover Azure Resources**
```bash
# Scan your Azure subscription
python -m topdeck.discovery.azure.discoverer --subscription-id <id>

# Results stored in Neo4j graph database
# 14+ resource types: AKS, App Services, SQL DB, Storage, VNets, etc.
```

**2. Link Code to Infrastructure**
```bash
# Connect Azure DevOps pipelines to resources
python examples/azure_devops_integration.py

# Track GitHub deployments
python examples/github_integration.py

# See which repo deployed to which resource
```

**3. Query Topology and Dependencies - NEW Enhanced Capabilities! 🎯**
```bash
# Start the API server
make run

# Get complete topology graph
curl http://localhost:8000/api/v1/topology

# Get detailed resource attachments (NEW!)
curl http://localhost:8000/api/v1/topology/resources/{id}/attachments

# Get dependency chains (NEW!)
curl http://localhost:8000/api/v1/topology/resources/{id}/chains

# Get comprehensive attachment analysis (NEW!)
curl http://localhost:8000/api/v1/topology/resources/{id}/analysis

# Enhanced dependencies with attachment details
curl http://localhost:8000/api/v1/topology/resources/{id}/dependencies
```

**New Topology & Dependency Features:**
- ✅ **Resource Attachments**: See which resources are attached to which with detailed connection info
- ✅ **Relationship Details**: View ports, protocols, connection strings, and endpoint details
- ✅ **Dependency Chains**: Trace complete paths showing how dependencies cascade
- ✅ **Attachment Analysis**: Get bigger picture with metrics, strength scores, and impact radius
- ✅ **Critical Identification**: Automatically identify critical attachments and connections
- ✅ **Relationship Categorization**: Organize by dependency, connectivity, deployment, security

See **[Enhanced Topology Analysis Guide](docs/ENHANCED_TOPOLOGY_ANALYSIS.md)** for complete documentation.

**4. Explore with Web UI**
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Access at http://localhost:3000
```

The web interface provides:
- **Dashboard**: Overview with key metrics and status
- **Topology View**: Interactive network graph with Cytoscape.js
- **Risk Analysis**: Visual risk distribution and SPOF detection
- **Change Impact**: Analyze impacts of changes with real-time assessment ✨ **ENHANCED**
- **Integrations**: Manage data source plugins and configurations

See [FRONTEND_README.md](FRONTEND_README.md) for complete UI documentation.

**5. Analyze Risk - NEW Enhanced Capabilities! 🎯**
```bash
# Note: Replace {resource-id} with actual resource ID from your Neo4j database

# Comprehensive risk analysis (combines all scenarios)
curl "http://localhost:8000/api/v1/risk/resources/{resource-id}/comprehensive?project_path=/app"

# Degraded performance scenario (realistic production issues)
curl "http://localhost:8000/api/v1/risk/resources/{resource-id}/degraded-performance?current_load=0.8"

# Intermittent failure analysis (service blips)
curl "http://localhost:8000/api/v1/risk/resources/{resource-id}/intermittent-failure?failure_frequency=0.05"

# Partial outage analysis (multi-zone failures)
curl "http://localhost:8000/api/v1/risk/resources/{resource-id}/partial-outage?affected_zones=zone-a"

# Standard risk assessment
curl "http://localhost:8000/api/v1/risk/resources/{resource-id}"

# Find all single points of failure
curl "http://localhost:8000/api/v1/risk/spof"

# Detect circular dependencies (NEW!)
curl "http://localhost:8000/api/v1/risk/dependencies/circular"

# Check dependency health (NEW!)
curl "http://localhost:8000/api/v1/risk/dependencies/{resource-id}/health"

# Compare risk across resources (NEW!)
curl "http://localhost:8000/api/v1/risk/compare?resource_ids=id1,id2,id3"

# Analyze cascading failure probability (NEW!)
curl "http://localhost:8000/api/v1/risk/cascading-failure/{resource-id}"
```

**Risk Analysis Features:**
- ✅ **Degraded Performance**: Analyzes realistic degradation (slow responses, timeouts, blips)
- ✅ **Intermittent Failures**: Models occasional errors and service blips
- ✅ **Partial Outages**: Multi-zone failure scenarios
- ✅ **Dependency Vulnerabilities**: Scans npm/pip packages for CVEs
- ✅ **Multiple Outcomes**: Probability-weighted scenarios with user impact
- ✅ **Enhanced Dependency Search**: All relationship types in graph
- ✅ **Combined Risk Score**: Weighted average across all scenarios

**NEW Advanced Dependency Analysis Features:** ✨
- ✅ **Circular Dependency Detection**: Find cycles in dependency graph that can cause deadlocks
- ✅ **Dependency Health Scoring**: Comprehensive health score (0-100) considering coupling, SPOFs, and depth
- ✅ **Risk Comparison**: Compare risk scores across multiple resources for prioritization
- ✅ **Cascading Failure Probability**: Model how failures propagate through dependencies

See **[Enhanced Risk Analysis Guide](docs/ENHANCED_RISK_ANALYSIS.md)** and **[Enhanced Dependency Analysis Guide](docs/ENHANCED_DEPENDENCY_ANALYSIS.md)** for complete documentation.

**6. ML-Based Predictions** ✨ **NEW**
```bash
# Predict resource failure probability
curl "http://localhost:8000/api/v1/prediction/resources/{resource-id}/failure-risk"

# Forecast performance degradation
curl "http://localhost:8000/api/v1/prediction/resources/{resource-id}/performance?metric_name=latency_p95&horizon_hours=24"

# Detect anomalies in resource behavior
curl "http://localhost:8000/api/v1/prediction/resources/{resource-id}/anomalies"

# Check prediction service health
curl "http://localhost:8000/api/v1/prediction/health"
```

**ML Prediction Features:**
- ✅ **Failure Prediction**: Predict resource failures 24-72 hours in advance using ML
- ✅ **Performance Forecasting**: Forecast latency, throughput, and error rates using time-series models
- ✅ **Anomaly Detection**: Detect unusual patterns using unsupervised learning
- ✅ **Contributing Factors**: Identify what's causing predicted issues
- ✅ **Actionable Recommendations**: Get specific steps to prevent failures
- ✅ **Traditional ML**: Uses scikit-learn, Prophet, statsmodels (no LLM needed)
- ✅ **Fast Inference**: <100ms prediction time
- ✅ **Privacy-First**: All predictions run locally, no external APIs

**Why Not LLM?** We use traditional ML libraries (scikit-learn, Prophet) instead of LLMs because:
- **Purpose-built** for time-series and numerical prediction
- **10-100x faster** inference (10-50ms vs 1-5 seconds)
- **No API costs** - runs locally
- **More accurate** for numerical/time-series data
- **Explainable** - can show why predictions were made

See **[ML Prediction Research](docs/ML_PREDICTION_RESEARCH.md)** for technical analysis and **[ML Prediction Guide](docs/ML_PREDICTION_GUIDE.md)** for usage examples.

**7. Change Management** ✨ **NEW**
```bash
# Create a change request
curl -X POST http://localhost:8000/api/v1/changes \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Deploy API v2.1.0",
    "description": "Production deployment",
    "change_type": "deployment",
    "affected_resources": ["resource-id"],
    "scheduled_start": "2024-11-15T02:00:00Z"
  }'

# Assess change impact
curl -X POST "http://localhost:8000/api/v1/changes/{change-id}/assess?resource_id=resource-123"

# View change calendar
curl "http://localhost:8000/api/v1/changes/calendar?start_date=2024-11-01T00:00:00Z"

# Receive webhooks from ServiceNow/Jira
# POST /api/v1/webhooks/servicenow
# POST /api/v1/webhooks/jira
```

**Change Management Features:**
- ✅ **Change Request Tracking**: Create and track change requests through their lifecycle
- ✅ **Impact Assessment**: Automated analysis of change blast radius and risk
- ✅ **Change Calendar**: Visualize upcoming changes and detect conflicts
- ✅ **ServiceNow Integration**: Webhook receiver for ServiceNow change requests
- ✅ **Jira Integration**: Webhook receiver for Jira change tickets
- ✅ **Risk-Based Recommendations**: Automatic approval routing and scheduling guidance
- ✅ **Rollback Planning**: Identifies when rollback plans are required

See **[Change Management Guide](docs/CHANGE_MANAGEMENT_GUIDE.md)** for complete documentation.

### What's Next 🚀

Recent additions:
- **Change Management** ✨ NEW: Full change request tracking with ServiceNow/Jira integration
- **ML-Based Predictions** ✨ NEW: Predict failures, performance degradation, and detect anomalies using traditional ML (scikit-learn, Prophet)

Areas for future enhancement:
- **Multi-Cloud Support**: Complete AWS/GCP discovery (Azure is fully implemented)
- **Cost Impact Analysis**: Estimate financial impact of failures
- **Automated Change Workflows**: Approval automation and change templates
- **Automated Remediation**: Suggest and apply infrastructure changes

---

## 🚦 Getting Started

### Prerequisites
- Python 3.11 or higher
- Docker & Docker Compose
- Azure credentials (AWS/GCP support planned)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/MattVerwey/TopDeck.git
cd TopDeck

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
make install-dev

# Configure environment
cp .env.example .env
# Edit .env with your cloud credentials

# Start infrastructure services (Neo4j, Redis, RabbitMQ)
make docker-up

# Run the API server
make run

# In another terminal, run tests
make test
```

The API will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **Neo4j Browser**: http://localhost:7474
- **RabbitMQ Management**: http://localhost:15672

For detailed development information, see [DEVELOPMENT.md](DEVELOPMENT.md).

### Testing the Application

TopDeck includes comprehensive testing infrastructure for local development and CI/CD:

**Quick Test (5 minutes)**:
```bash
# Run automated end-to-end test
./scripts/e2e-test.sh
```

**Test Azure Discovery**:
```bash
# Configure Azure credentials in .env first
python scripts/test_discovery.py
```

**Run Unit Tests**:
```bash
# Fast tests without external dependencies
pytest tests/unit/ tests/discovery/ tests/analysis/ -v
```

**Documentation**:
- **[Testing Quick Start](docs/TESTING_QUICKSTART.md)** - 5-minute testing guide
- **[Hosting and Testing Guide](docs/HOSTING_AND_TESTING_GUIDE.md)** - Complete testing guide
- **[Azure Testing Guide](docs/AZURE_TESTING_GUIDE.md)** - Azure infrastructure setup

## 📊 Where We Are Today

### ✅ What You Can Use Now

**Phase 1: Foundation** ✅ **COMPLETE**
- Azure resource discovery (AKS, App Services, SQL DB, Storage, Networking)
- Neo4j graph database for storing topology
- REST API backend with FastAPI
- Basic dependency detection between resources

**Phase 2: Platform Integrations** ✅ **COMPLETE**
- Azure DevOps integration (repos, pipelines, deployments)
- GitHub integration (repos, workflows, deployments)
- Code-to-infrastructure linking
- Basic topology API endpoints

**Phase 3: Interactive Visualization** ✅ **COMPLETE**
- Modern React 18 + TypeScript frontend with Vite
- Five main views: Dashboard, Topology, Risk Analysis, Change Impact, Integrations
- Interactive topology visualization with Cytoscape.js
- Risk analysis charts with Recharts
- Material-UI v7 with professional dark theme
- Responsive layout with collapsible navigation
- Comprehensive error handling and loading states

**Multi-Cloud Foundation** ✅ **MAPPERS READY**
- AWS resource mappers (18+ types: EKS, EC2, RDS, Lambda, etc.)
- GCP resource mappers (17+ types: GKE, Compute Engine, Cloud SQL, etc.)
- Unified data model across clouds
- Ready for orchestrator implementation

### 🎯 What's Next: Core Value Delivery

**Phase 3: Risk Analysis & Intelligence** 🚧 **TOP PRIORITY**

This is where TopDeck delivers its core value. Currently missing:

1. **Risk Analysis Engine** (Issue #5) - **THE CRITICAL PIECE**
   - "What depends on this service?" - Dependency impact analysis
   - "What breaks if this fails?" - Blast radius calculation
   - "How risky is this change?" - Risk scoring algorithm
   - "What are my single points of failure?" - Critical component identification
   
2. **Monitoring Integration** (Issue #7)
   - Correlate failures with dependency chains
   - Track error propagation through services
   - Performance bottleneck detection

### 🔜 Future Phases

**Phase 4: Multi-Cloud Orchestration** (After Phase 3)
- Complete AWS/GCP discovery orchestrators
- Multi-cloud topology unification
- Cross-cloud dependency tracking

**Phase 5: Production Hardening** (After Phase 4)
- Production deployment guides
- Advanced caching and performance
- Security hardening
- End-to-end testing

## 📋 Development Roadmap (Refocused)

### ✅ Phase 1: Foundation (Complete)
Build the infrastructure to discover and store cloud resources.

**Deliverables:**
- [x] Python/FastAPI backend with Neo4j graph database
- [x] Azure resource discovery (14+ resource types)
- [x] Cloud-agnostic data models
- [x] Basic dependency detection

**Status:** ✅ Ready to use for Azure environments

---

### ✅ Phase 2: Platform Integrations (Complete)
Connect to CI/CD platforms to link code with infrastructure.

**Deliverables:**
- [x] Azure DevOps integration (repos, pipelines, deployments)
- [x] GitHub integration (repos, workflows, deployments)
- [x] Code-to-infrastructure mapping
- [x] Topology API endpoints

**Status:** ✅ Can track deployments from Azure DevOps and GitHub

---

### 🎯 Phase 3: Core Value Delivery (IN PROGRESS - FOCUS HERE)
**THIS IS THE CRITICAL PHASE** - Deliver TopDeck's core value proposition.

**Priority 1: Risk Analysis Engine** (Issue #5) ⚠️ **MOST IMPORTANT**
- [ ] Dependency impact analysis - "What depends on this?"
- [ ] Blast radius calculation - "What breaks if this fails?"
- [ ] Risk scoring - "How critical is this component?"
- [ ] Single point of failure detection
- [ ] Change impact assessment

**Priority 2: Interactive Visualization** (Issue #6) ✅ **COMPLETE**
- [x] React frontend with Cytoscape.js
- [x] Interactive dependency graph
- [x] Visual risk indicators
- [x] Drill-down into component details
- [x] Five main views: Dashboard, Topology, Risk Analysis, Change Impact, Integrations
- [x] Responsive layout with collapsible navigation
- [x] Dark theme with consistent styling
- [x] Error handling and loading states

**Priority 3: Monitoring Integration** (Issue #7)
- [x] Prometheus metrics collection (backend ready)
- [x] Loki log aggregation (backend ready)
- [ ] Error correlation with topology
- [ ] Performance bottleneck identification

**Why This Matters:** Without the risk analysis engine, TopDeck can discover and map resources but can't answer the critical questions: "What will break?" and "How risky is this change?" This is the core value users need.

**Status:** 🚧 Framework exists, core algorithms needed

---

### 🔜 Phase 4: Multi-Cloud Expansion (After Phase 3)
Expand proven features to AWS and GCP.

**Deliverables:**
- [x] AWS resource mappers (ready)
- [x] GCP resource mappers (ready)
- [ ] AWS/GCP discovery orchestrators
- [ ] Multi-cloud topology unification
- [ ] Cross-cloud risk analysis

**Status:** 🔜 Mappers ready, waiting for Phase 3 completion

---

### 🔜 Phase 5: Production Ready (After Phase 4)
Harden for production use.

**Deliverables:**
- [ ] Production deployment guides
- [ ] Advanced performance optimization
- [ ] End-to-end integration tests
- [ ] Security hardening

**Status:** 🔜 Planned after core features complete

---

### 📅 Updated Timeline

**Immediate Focus (Next 4-6 weeks):**
1. Implement risk analysis engine (Issue #5) - 3 weeks
2. Build interactive visualization (Issue #6) - 2 weeks  
3. Complete monitoring integration (Issue #7) - 1 week

**After Core Value Delivery:**
4. Multi-cloud orchestration (Phase 4) - 3-4 weeks
5. Production hardening (Phase 5) - 2-3 weeks

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on:
- Code of conduct
- Development setup
- Pull request process
- Coding standards

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔒 Security

TopDeck provides comprehensive security features:

- **Encryption in Transit**: TLS/SSL support for API server, Neo4j, Redis, and RabbitMQ
- **Encryption at Rest**: Database encryption support with Neo4j Enterprise and filesystem encryption
- **Credential Protection**: Secure handling of cloud credentials and API keys via environment variables
- **Read-Only Access**: Cloud resource scanning uses read-only permissions
- **Data Masking**: Sensitive data is masked in logs and UI
- **RBAC**: Role-based access control for platform users
- **Audit Logging**: Security event tracking and audit trails

For detailed encryption configuration, see **[Security & Encryption Guide](docs/SECURITY_ENCRYPTION.md)**.

## 📞 Support

- Create an [Issue](https://github.com/MattVerwey/TopDeck/issues) for bug reports
- Start a [Discussion](https://github.com/MattVerwey/TopDeck/discussions) for questions
- Check [Documentation](./docs/) for guides

## 🌟 Vision Statement

TopDeck aims to be the **"air traffic control"** for cloud deployments - providing clear visibility into what depends on what, enabling confident decision-making about changes, and preventing cascading failures through proactive risk assessment.

We believe operations teams should **know** rather than **guess** what will be affected by their changes.

---

**Current Status**: 🎯 Focused on Core Value Delivery (Phase 3)

**What Works Today**:
- ✅ Azure resource discovery and dependency mapping
- ✅ CI/CD integration (Azure DevOps, GitHub)
- ✅ REST API for topology queries
- ✅ Interactive web UI with 5 main views (Dashboard, Topology, Risk Analysis, Change Impact, Integrations)
- ✅ Professional dark theme with responsive design

**Critical Next Step**:
- 🚧 **Risk Analysis Engine** - The core feature that delivers TopDeck's value

**Why This Matters**: We have great infrastructure for discovering and mapping resources, but the **critical missing piece** is the risk analysis that answers "What breaks if I change this?" - that's what users actually need.

For current development tasks, see [Issues](https://github.com/MattVerwey/TopDeck/issues)
