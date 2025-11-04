# TopDeck Documentation

Welcome to the TopDeck documentation! This directory contains comprehensive guides, API references, and operational documentation.

## 📚 Documentation Structure

### Features Documentation (`features/`)
Feature-specific guides and references for TopDeck's core capabilities:

- **`code-scanning/`** - Azure DevOps repository scanning for dependency discovery
  - AKS and App Service support
  - Service Bus dependency mapping
  - Multi-project scanning
  
- **`risk-analysis/`** - Risk assessment and analysis
  - Enhanced risk scoring
  - Frontend integration
  - Quick reference guides

- **`dependency-mapping/`** - Resource dependency discovery and visualization
  - Enhanced dependency analysis
  - Service Bus topology
  - Dependency verification

- **`change-management/`** - Change tracking and impact analysis
  - Change management workflows
  - Impact assessment

- **`accuracy-tracking/`** - Prediction accuracy monitoring
  - Accuracy tracking system
  - Metrics and reporting

- **`reporting/`** - Report generation and export
  - PDF export capabilities
  - Report customization
  - Future improvements

### Setup & Configuration (`setup/`)
Getting started guides and configuration documentation:

- Azure setup and testing
- Multi-cloud configuration
- Project setup
- Quick start guides

### Deployment (`deployment/`)
Production deployment and hosting guides:

- Production deployment procedures
- Security checklists
- Decision flowcharts
- Hosting guides

### API Documentation (`api/`)
RESTful API references and examples

### Architecture Documentation (`architecture/`)
System architecture diagrams and design decisions

### User Guides (`user-guide/`)
End-user documentation and tutorials

### Archived Documentation (`archive/`)
Historical documentation and completed implementation summaries

## 🚀 Quick Links

### Getting Started
1. [Quick Start Guide](../QUICK_START.md) - Get TopDeck running locally
2. [Development Guide](../DEVELOPMENT.md) - Set up development environment
3. [Docker Setup](../DOCKER_SETUP.md) - Container-based deployment

### Core Features
- [Code Repository Scanner](features/code-scanning/CODE_REPOSITORY_SCANNER.md)
- [AKS Support](features/code-scanning/AKS_CODE_SCANNING.md)
- [Risk Analysis](features/risk-analysis/ENHANCED_RISK_ANALYSIS.md)
- [Dependency Mapping](features/dependency-mapping/ENHANCED_DEPENDENCY_MAPPING.md)

### Operations
- [Operations Runbook](OPERATIONS_RUNBOOK.md)
- [Observability](OBSERVABILITY.md)
- [Rate Limiting](RATE_LIMITING.md)
- [Security & Encryption](SECURITY_ENCRYPTION.md)

### API
- [Quick API Guide](QUICK_API_GUIDE.md)
- API docs available at: `http://localhost:8000/api/docs`

## 📖 Documentation Index

### By Use Case

#### "I want to discover dependencies from my code repositories"
→ Start with [Code Repository Scanner](features/code-scanning/CODE_REPOSITORY_SCANNER.md)
→ For AKS deployments: [AKS Support Guide](features/code-scanning/AKS_CODE_SCANNING.md)

#### "I need to assess risks in my infrastructure"
→ Start with [Enhanced Risk Analysis](features/risk-analysis/ENHANCED_RISK_ANALYSIS.md)

#### "I want to visualize my service dependencies"
→ Start with [Dependency Mapping](features/dependency-mapping/ENHANCED_DEPENDENCY_MAPPING.md)

#### "I need to track changes and their impact"
→ Start with [Change Management Guide](features/change-management/CHANGE_MANAGEMENT_GUIDE.md)

#### "I'm deploying to production"
→ Start with [Production Deployment Guide](deployment/PRODUCTION_DEPLOYMENT_GUIDE.md)

## 🔧 Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on contributing to documentation.

### Documentation Standards
- Use clear, descriptive headings
- Include code examples where applicable
- Add diagrams for complex workflows
- Keep quick reference guides concise
- Update this README when adding new docs

## 📝 Recent Updates

- **Nov 2025**: Added AKS code scanning support
- **Nov 2025**: Reorganized documentation into feature-based structure
- **Oct 2025**: Added enhanced risk analysis features
- **Oct 2025**: Improved dependency mapping capabilities

## 🆘 Need Help?

- Check [FAQ](../README.md#faq) in main README
- Review [Troubleshooting sections](OPERATIONS_RUNBOOK.md) in operational docs
- Open an issue on GitHub
