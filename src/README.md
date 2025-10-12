# TopDeck Source Code

This directory contains the core source code for the TopDeck platform.

## Structure

### `/discovery`
Cloud resource discovery engines for different cloud providers.
- `azure/` - Azure resource discovery (AKS, App Service, SQL DB, etc.)
- `aws/` - AWS resource discovery (EKS, EC2, RDS, etc.)
- `gcp/` - GCP resource discovery (GKE, Compute Engine, Cloud SQL, etc.)
- `common/` - Shared discovery interfaces and utilities

### `/integration`
Code repository and CI/CD platform integrations.
- `azure-devops/` - Azure DevOps pipeline and repository integration
- `github/` - GitHub Actions and repository integration
- `common/` - Shared integration interfaces

### `/analysis`
Core analysis engines for topology mapping and risk assessment.
- `topology/` - Network topology mapping and visualization
- `risk/` - Risk analysis and impact assessment
- `dependencies/` - Dependency graph builder

### `/monitoring`
Performance monitoring and observability integration.
- `metrics/` - Metrics collection and aggregation
- `alerts/` - Alert correlation and analysis

### `/api`
REST API layer for platform access.
- `controllers/` - API endpoint controllers
- `models/` - Data transfer objects and API models

### `/ui`
Web-based dashboard and visualization.
- `components/` - Reusable React components
- `pages/` - Page-level components

### `/storage`
Data persistence layers.
- `graph/` - Neo4j graph database interface
- `cache/` - Redis caching layer

## Development Guidelines

- Each module should be independently testable
- Use dependency injection for loose coupling
- Follow the interfaces defined in `common/` directories
- Write comprehensive unit tests
- Document public APIs

## Getting Started

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development setup instructions.
