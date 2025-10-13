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

3. **[Azure Resource Discovery](issue-003-azure-resource-discovery.md)**
   - Priority: High
   - Implement Azure cloud resource discovery
   - Support AKS, App Service, VMs, networking, databases

### Phase 2: Platform Integrations (Weeks 3-4)

4. **[Azure DevOps Integration](issue-004-azure-devops-integration.md)**
   - Priority: High
   - Integrate with Azure DevOps pipelines
   - Link deployments to infrastructure

10. **[GitHub Integration](issue-010-github-integration.md)**
    - Priority: High
    - Integrate with GitHub Actions and repositories
    - Track deployments and link to cloud resources

6. **[Topology Visualization Dashboard](issue-006-topology-visualization.md)**
   - Priority: High
   - Build React-based web dashboard
   - Create interactive topology visualizations

### Phase 3: Analysis & Intelligence (Weeks 5-6)

5. **[Risk Analysis Engine](issue-005-risk-analysis-engine.md)**
   - Priority: High
   - Implement risk scoring algorithms
   - Build impact assessment and blast radius calculation

7. **[Performance Monitoring Integration](issue-007-performance-monitoring-integration.md)**
   - Priority: Medium
   - Integrate with Application Insights, CloudWatch, Cloud Monitoring
   - Implement error correlation and anomaly detection

### Phase 4: Multi-Cloud Architecture (Weeks 7-10)

8. **[AWS Resource Discovery](issue-008-aws-resource-discovery.md)**
   - Priority: High
   - Implement AWS cloud resource discovery using Terraform
   - Support EKS, EC2, Lambda, RDS, networking
   - Generate and manage Terraform configurations

9. **[GCP Resource Discovery](issue-009-gcp-resource-discovery.md)**
   - Priority: High
   - Implement GCP cloud resource discovery using Terraform
   - Support GKE, Compute Engine, Cloud Run, Cloud SQL
   - Generate and manage Terraform configurations

11. **[Multi-Cloud Resource Abstraction Layer](issue-011-multi-cloud-abstraction-layer.md)**
    - Priority: High
    - Build unified abstraction layer for resources across all clouds
    - Enable consistent interface for cross-cloud operations
    - Support cloud-agnostic application logic

12. **[Infrastructure Deployment Automation](issue-012-infrastructure-deployment-automation.md)**
    - Priority: High
    - Create Terraform-based deployment automation system
    - Manage infrastructure as code across clouds
    - State management and deployment workflows

## Additional Issues to Consider

### Future Enhancements
- **AWS CodePipeline Integration**: Native AWS CI/CD integration
- **Cloud Build Integration**: GCP CI/CD integration
- **GitLab CI/CD Integration**: GitLab pipeline support

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
    │       ├─→ Issue #8 (AWS Discovery)
    │       ├─→ Issue #9 (GCP Discovery)
    │       ├─→ Issue #4 (Azure DevOps)
    │       ├─→ Issue #10 (GitHub)
    │       ├─→ Issue #5 (Risk Analysis)
    │       └─→ Issue #7 (Monitoring)
    ├─→ Issue #6 (Visualization)
    │       └─→ (depends on API from Issues #3-5, #7-10)
    └─→ Phase 4 Multi-Cloud
            ├─→ Issue #11 (Multi-Cloud Abstraction)
            │       ├─→ depends on Issues #3, #8, #9
            │       └─→ used by Issues #5, #6
            └─→ Issue #12 (Deployment Automation)
                    └─→ depends on Issue #11
```

## Development Process

1. **Weeks 1-2**: Issues #1-3 (Foundation & Azure)
2. **Weeks 3-4**: Issues #4, #10, #6 (Platform Integrations)
3. **Weeks 5-6**: Issues #5, #7 (Analysis & Intelligence)
4. **Weeks 7-10**: Issues #8, #9, #11, #12 (Multi-Cloud Architecture)

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
