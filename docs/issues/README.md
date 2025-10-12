# TopDeck Development Issues

This directory contains detailed issue templates for building TopDeck. These can be used to create GitHub issues to track development progress.

## Issue List

### Phase 1: Foundation (Weeks 1-2)

1. **[Technology Stack Decision](issue-001-technology-stack-decision.md)**
   - Priority: High
   - Decide on core technologies (Python vs Go, frameworks, etc.)
   - Create ADR document

2. **[Core Data Models](issue-002-core-data-models.md)**
   - Priority: High
   - Design Neo4j schema
   - Define resource and relationship models

### Phase 2: Discovery & Integration (Weeks 2-4)

3. **[Azure Resource Discovery](issue-003-azure-resource-discovery.md)**
   - Priority: High
   - Implement Azure cloud resource discovery
   - Support AKS, App Service, VMs, networking, databases

4. **[Azure DevOps Integration](issue-004-azure-devops-integration.md)**
   - Priority: High
   - Integrate with Azure DevOps pipelines
   - Link deployments to infrastructure

### Phase 3: Analysis & Visualization (Weeks 5-8)

5. **[Risk Analysis Engine](issue-005-risk-analysis-engine.md)**
   - Priority: High
   - Implement risk scoring algorithms
   - Build impact assessment and blast radius calculation

6. **[Topology Visualization Dashboard](issue-006-topology-visualization.md)**
   - Priority: High
   - Build React-based web dashboard
   - Create interactive topology visualizations

### Phase 4: Monitoring & Intelligence (Weeks 7-8)

7. **[Performance Monitoring Integration](issue-007-performance-monitoring-integration.md)**
   - Priority: Medium
   - Integrate with Application Insights, CloudWatch
   - Implement error correlation and anomaly detection

## Additional Issues to Create

### AWS Support
- **AWS Resource Discovery**: Similar to Issue #3 but for AWS (EC2, EKS, RDS, etc.)
- **AWS CodePipeline Integration**: Similar to Issue #4 but for AWS

### GCP Support
- **GCP Resource Discovery**: Similar to Issue #3 but for GCP
- **Cloud Build Integration**: GCP CI/CD integration

### GitHub Integration
- **GitHub Actions Integration**: Similar to Issue #4 but for GitHub

### Security & Authentication
- **Authentication & Authorization**: Implement user authentication and RBAC
- **Credential Management**: Secure storage of cloud credentials
- **Audit Logging**: Track all platform access and changes

### API & Infrastructure
- **REST API Implementation**: Build the backend REST API
- **Neo4j Setup & Configuration**: Production-ready Neo4j deployment
- **Docker & Kubernetes**: Containerize application and create K8s manifests

### Testing & Quality
- **Test Infrastructure**: Set up testing frameworks and CI/CD
- **Performance Testing**: Load testing and optimization
- **Security Scanning**: Implement CodeQL and dependency scanning

### Documentation
- **API Documentation**: OpenAPI/Swagger documentation
- **User Guide**: Complete user documentation
- **Architecture Documentation**: Detailed architecture docs

## How to Use These Issues

### Creating GitHub Issues

For each issue template:

1. Copy the content from the markdown file
2. Create a new issue in GitHub
3. Use the title from the markdown (e.g., "Implement Azure Resource Discovery")
4. Add the specified labels
5. Assign to appropriate team members
6. Add to project board/milestone

### Labels to Create

```
Priority:
- priority: high
- priority: medium
- priority: low

Phase:
- phase-1
- phase-2
- phase-3
- phase-4

Type:
- enhancement
- bug
- documentation
- architecture
- discussion

Cloud:
- cloud: azure
- cloud: aws
- cloud: gcp

Component:
- discovery
- integration
- analysis
- visualization
- monitoring
- ui
- api
```

### Issue Dependencies

Many issues depend on earlier issues. The dependency graph:

```
Issue #1 (Tech Stack)
    ├─→ Issue #2 (Data Models)
    │       ├─→ Issue #3 (Azure Discovery)
    │       ├─→ Issue #4 (Azure DevOps)
    │       ├─→ Issue #5 (Risk Analysis)
    │       └─→ Issue #7 (Monitoring)
    └─→ Issue #6 (Visualization)
            └─→ (depends on API from Issues #3, #4, #5)
```

## Development Process

1. **Week 1**: Issues #1-2 (Foundation)
2. **Weeks 2-4**: Issues #3-4 (Discovery & Integration)
3. **Weeks 5-6**: Issue #5 (Risk Analysis)
4. **Weeks 6-8**: Issue #6 (Visualization)
5. **Weeks 7-8**: Issue #7 (Monitoring)

## Contributing

When working on an issue:

1. Create a feature branch: `feature/issue-XXX-description`
2. Reference the issue in commits: `Implements part of #XXX`
3. Update issue with progress
4. Create PR when ready
5. Link PR to issue: `Closes #XXX`

## Questions?

For questions about these issues, please:
- Comment on the specific GitHub issue
- Start a discussion in GitHub Discussions
- Contact the project maintainers
