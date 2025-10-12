# TopDeck - Multi-Cloud Integration & Risk Analysis Platform

TopDeck is an intelligent multi-cloud integration platform designed to provide comprehensive visibility into cloud infrastructure, application deployments, and their interdependencies. It helps organizations understand their application topology, data flows, and assess risks associated with changes across multi-cloud environments.

## 🎯 Vision

Build a platform that:
- **Discovers & Maps**: Automatically discovers cloud resources across multiple cloud providers (Azure, AWS, GCP)
- **Analyzes Dependencies**: Links code repositories to infrastructure to understand deployment relationships
- **Visualizes Topology**: Creates network flow diagrams showing how applications communicate
- **Assesses Risk**: Provides impact analysis for changes - "What breaks if this service fails?"
- **Tracks Data Flow**: Monitors error paths and performance bottlenecks (API delays, SQL deadlocks, etc.)

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

## 📁 Project Structure

```
TopDeck/
├── docs/                           # Documentation
│   ├── architecture/               # Architecture diagrams and decisions
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
- **Phase 1 - Issue #1**: Technology Stack Decision ([ADR-001](docs/architecture/adr/001-technology-stack.md))
  - Evaluated Python vs Go through proof-of-concept implementations
  - Selected Python 3.11+ with FastAPI
  - Established project structure and development environment
  - Created initial test suite and API server

### 🚧 In Progress
- **Phase 1 - Issue #2**: Core Data Models (Next)
- **Phase 1 - Issue #3**: Azure Resource Discovery

## 📋 Development Roadmap

### Phase 1: Foundation (Months 1-2)
- [x] **Issue #1**: Technology Stack Decision
- [ ] **Issue #2**: Design core data models for resources and dependencies
- [ ] **Issue #3**: Implement Azure resource discovery
- [ ] Build foundational graph database schema

### Phase 2: Multi-Cloud Architecture (Months 3-4)
- [ ] Architect and implement AWS resource discovery using Terraform
- [ ] Architect and implement GCP resource discovery using Terraform
- [ ] Build unified multi-cloud resource abstraction layer
- [ ] Create infrastructure deployment automation

### Phase 3: Platform Integrations (Months 5-6)
- [ ] Build Azure DevOps pipeline integration
- [ ] Add GitHub Actions and repository integration
- [ ] Implement deployment tracking and linking
- [ ] Create basic topology visualization

### Phase 4: Analysis & Intelligence (Months 7-8)
- [ ] Develop dependency graph builder
- [ ] Implement risk analysis engine
- [ ] Build change impact assessment
- [ ] Integrate performance metrics and monitoring
- [ ] Add error correlation and alerting

### Phase 5: Production Ready (Months 9-10)
- [ ] Security hardening
- [ ] Performance optimization
- [ ] Comprehensive testing
- [ ] Documentation and user guides

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

**Status**: 🚧 In Initial Planning Phase

For current development tasks, see [Issues](https://github.com/MattVerwey/TopDeck/issues)
