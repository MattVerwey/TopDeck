# TopDeck - Multi-Cloud Integration & Risk Analysis Platform

TopDeck is an intelligent multi-cloud integration platform designed to provide comprehensive visibility into cloud infrastructure, application deployments, and their interdependencies. It helps organizations understand their application topology, data flows, and assess risks associated with changes across multi-cloud environments.

## 🎯 Vision

Build a platform that:
- **Discovers & Maps**: Automatically discovers cloud resources across multiple cloud providers (Azure, AWS, GCP)
- **Analyzes Dependencies**: Links code repositories to infrastructure to understand deployment relationships
- **Visualizes Topology**: Creates network flow diagrams showing how applications communicate
- **Assesses Risk**: Provides impact analysis for changes - "What breaks if this service fails?"
- **Tracks Data Flow**: Monitors error paths and performance bottlenecks (API delays, SQL deadlocks, etc.)

## 📚 Documentation Quick Links

- **[Progress Tracking](PROGRESS.md)** - Detailed status of all phases and issues
- **[Quick Reference](QUICK_REFERENCE.md)** - Quick start guide and common tasks
- **[Quick Start Guide](QUICK_START.md)** - Get started in 5 minutes
- **[Development Guide](DEVELOPMENT.md)** - Development workflow and guidelines
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
   - API latency tracking
   - Database deadlock detection
   - Error correlation analysis
   - Root cause identification

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

**Rationale**: After evaluating both Python and Go through proof-of-concept implementations, Python was selected for its superior cloud SDK support, faster development velocity, and rich ecosystem. See the [ADR](docs/architecture/adr/001-technology-stack.md) for complete analysis.

## 🚦 Getting Started

### Prerequisites
- Python 3.11 or higher
- Docker & Docker Compose
- Cloud credentials (Azure, AWS, GCP)

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

## 📊 Current Status

### ✅ Completed

#### Phase 1: Foundation
- **Issue #1**: Technology Stack Decision ([ADR-001](docs/architecture/adr/001-technology-stack.md))
  - Evaluated Python vs Go through proof-of-concept implementations
  - Selected Python 3.11+ with FastAPI
  - Established project structure and development environment
  - Created initial test suite and API server

- **Issue #2**: Core Data Models ([Completion Report](docs/issues/ISSUE-002-COMPLETION.md))
  - Designed and implemented cloud-agnostic data models
  - Created Neo4j schema with 6 node types and 13 relationship types
  - Implemented Python data models (Application, Repository, Deployment, Resource)
  - Built comprehensive Neo4j client with CRUD operations
  - Added 500+ lines of tests with full coverage

- **Issue #3**: Azure Resource Discovery ([Progress Report](docs/issues/ISSUE-003-PROGRESS.md))
  - **Phase 1**: Foundation Complete
    - Azure SDK integration with multiple auth methods
    - Resource mapper supporting 14+ Azure resource types
    - Basic dependency detection
    - Neo4j storage integration
  - **Phase 2 & 3**: Enhanced Discovery & Production Ready ([Summary](PHASE_2_3_SUMMARY.md))
    - Azure DevOps API integration (repositories, pipelines, deployments)
    - Specialized resource discovery (compute, networking, data resources)
    - Production resilience patterns (rate limiting, retry, circuit breaker)
    - Structured logging with correlation IDs
    - Comprehensive error handling

#### Phase 4: Multi-Cloud Architecture
- **AWS & GCP Discovery Modules** ([Phase 4 Summary](docs/PHASE_4_SUMMARY.md))
  - AWS resource mapper supporting 18+ resource types
  - GCP resource mapper supporting 17+ resource types
  - Consistent Neo4j schema across all cloud providers
  - Tag/label normalization for unified queries
  - Terraform templates for multi-cloud deployment
  - 46 passing tests (21 AWS + 25 GCP)

### 🚧 In Progress
- **Phase 2**: Platform Integrations
  - GitHub Actions and repository integration (planned)
  - Basic topology visualization (planned)
  
- **Phase 3**: Analysis & Intelligence
  - Dependency graph builder (framework in place)
  - Risk analysis engine (planned)
  
### 📝 Next Steps
1. Complete GitHub integration (Issue #10)
2. Build topology visualization (Issue #6)
3. Implement risk analysis engine (Issue #5)
4. Add monitoring integration (Issue #7)

## 📋 Development Roadmap

### Phase 1: Foundation (Months 1-2) ✅ COMPLETE
- [x] **Issue #1**: Technology Stack Decision
- [x] **Issue #2**: Design core data models for resources and dependencies
- [x] **Issue #3**: Implement Azure resource discovery
  - [x] Foundation: Azure SDK integration, resource mapper, Neo4j client
  - [x] Phase 2: Azure DevOps API integration, specialized resource discovery
  - [x] Phase 3: Production resilience patterns, structured logging
- [x] Build foundational graph database schema (Neo4j with 6 node types, 13 relationships)

### Phase 2: Platform Integrations (Months 3-4) 🚧 IN PROGRESS
- [x] Build Azure DevOps pipeline integration
  - [x] Repository discovery with commit history
  - [x] Build/deployment tracking
  - [x] Application inference from repositories
- [ ] Add GitHub Actions and repository integration (Issue #10)
- [x] Implement deployment tracking and linking
- [ ] Create basic topology visualization (Issue #6)

### Phase 3: Analysis & Intelligence (Months 5-6) 🎯 NEXT
- [x] Develop dependency graph builder (framework)
  - [x] Basic dependency detection
  - [x] Network relationship analysis
  - [ ] Advanced dependency inference
- [ ] Implement risk analysis engine (Issue #5)
- [ ] Build change impact assessment
- [ ] Integrate performance metrics and monitoring (Issue #7)
- [ ] Add error correlation and alerting

### Phase 4: Multi-Cloud Architecture (Months 7-8) ✅ FOUNDATION COMPLETE
- [x] Architect and implement AWS resource discovery (Issue #8)
  - [x] AWS resource mapper (18+ resource types)
  - [x] Consistent Neo4j schema
  - [x] 21 passing tests
- [x] Architect and implement GCP resource discovery (Issue #9)
  - [x] GCP resource mapper (17+ resource types)
  - [x] Tag/label normalization
  - [x] 25 passing tests
- [x] Build unified multi-cloud resource abstraction layer
  - [x] Cloud-agnostic data models
  - [x] Consistent Neo4j storage format
  - [x] Multi-cloud discovery orchestration
- [x] Create infrastructure deployment automation (Issue #12)
  - [x] Terraform templates for Azure, AWS, GCP
  - [x] Separate state backends per cloud
  - [ ] Full discovery implementation (mappers ready, orchestrators need enhancement)

### Phase 5: Production Ready (Months 9-10) 🔜 PLANNED
- [x] Security hardening (credentials management, read-only access)
- [x] Performance optimization (rate limiting, retry logic, circuit breaker)
- [x] Comprehensive testing (100+ tests across all modules)
- [x] Documentation and user guides (comprehensive docs for all modules)
- [ ] End-to-end integration tests
- [ ] Production deployment guides
- [ ] Monitoring and observability setup

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on:
- Code of conduct
- Development setup
- Pull request process
- Coding standards

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔒 Security

- All cloud credentials are stored securely using industry-standard encryption
- Read-only access is enforced for cloud resource scanning
- Sensitive data is masked in logs and UI
- Role-based access control (RBAC) for platform users

## 📞 Support

- Create an [Issue](https://github.com/MattVerwey/TopDeck/issues) for bug reports
- Start a [Discussion](https://github.com/MattVerwey/TopDeck/discussions) for questions
- Check [Documentation](./docs/) for guides

## 🌟 Vision Statement

TopDeck aims to be the **"air traffic control"** for multi-cloud environments - providing real-time visibility, predictive insights, and proactive risk management for modern cloud-native applications.

---

**Status**: 🚀 Active Development - Phase 1 Complete, Phase 4 Foundation Complete

**Latest Milestones**:
- ✅ Phase 1 Complete: Foundation with Azure discovery
- ✅ Phase 4 Foundation: Multi-cloud support (AWS & GCP) 
- 🚧 Phase 2 In Progress: Platform integrations
- 🎯 Next: Complete Phase 2 & 3 features

For current development tasks, see [Issues](https://github.com/MattVerwey/TopDeck/issues)
