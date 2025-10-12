# Issue #4: Implement Azure DevOps Integration

**Labels**: `enhancement`, `integration`, `priority: high`, `phase-2`

## Description

Implement integration with Azure DevOps to discover CI/CD pipelines, link deployments to infrastructure, and understand how applications are built and deployed.

## Scope

### Data to Discover

**Repositories**:
- Repository details (name, URL, default branch)
- Recent commits and changes
- Branch policies and protection rules

**Pipelines**:
- Build pipelines
- Release pipelines
- Pipeline definitions (YAML)
- Pipeline runs and history
- Deployment stages and environments

**Deployments**:
- Deployment history
- Deployment targets (AKS, App Service, VM, etc.)
- Success/failure rates
- Deployment artifacts

**Configuration**:
- Variable groups
- Service connections (to Azure, AWS, GCP)
- Secure files

## Requirements

### Authentication
- Support Personal Access Token (PAT)
- Support OAuth 2.0
- Support Managed Identity (when running in Azure)
- Securely store credentials

### Linking Logic
- Match pipeline deployments to discovered cloud resources
- Extract deployment targets from pipeline YAML
- Parse connection strings and configuration
- Link source code to deployed services

### Data Extraction

From pipeline YAML:
```yaml
# Example: Extract AKS deployment target
stages:
- stage: Deploy
  jobs:
  - deployment: DeployToAKS
    environment: production
    strategy:
      runOnce:
        deploy:
          steps:
          - task: Kubernetes@1
            inputs:
              connectionType: 'Azure Resource Manager'
              azureSubscriptionEndpoint: 'my-subscription'
              azureResourceGroup: 'my-rg'
              kubernetesCluster: 'my-aks-cluster'  # <- Link to discovered AKS
```

Extract:
- Target subscription
- Resource group
- Cluster name
- Deployment environment
- Connection endpoints

## Technical Design

### Module Structure
```
src/integration/azure-devops/
├── __init__.py
├── client.py           # Azure DevOps API client
├── authenticator.py    # Authentication logic
├── repositories.py     # Repository discovery
├── pipelines.py        # Pipeline discovery
├── deployments.py      # Deployment tracking
├── parser.py           # YAML pipeline parser
├── linker.py           # Link deployments to resources
└── config.py           # Configuration
```

### Key Classes

```python
class AzureDevOpsIntegration:
    def __init__(self, organization: str, project: str, credentials):
        """Initialize Azure DevOps integration"""
        
    def discover_repositories(self) -> List[Repository]:
        """Discover all repositories in project"""
        
    def discover_pipelines(self) -> List[Pipeline]:
        """Discover all pipelines"""
        
    def get_deployment_history(self, pipeline_id: str) -> List[Deployment]:
        """Get deployment history for a pipeline"""
        
    def link_deployments_to_resources(self) -> List[DeploymentLink]:
        """Link pipeline deployments to discovered cloud resources"""
```

### Configuration

```yaml
# config/azure-devops.yaml
azure_devops:
  authentication:
    method: pat  # or oauth, managed_identity
    pat_token: ${AZURE_DEVOPS_PAT}
    
  organizations:
    - name: my-org
      projects:
        - project-1
        - project-2
      
  discovery:
    repositories:
      enabled: true
      branches:
        - main
        - master
        - develop
    
    pipelines:
      enabled: true
      types:
        - build
        - release
      
    scan_interval: 1800  # seconds
```

## Tasks

- [ ] Set up Azure DevOps SDK/API client
- [ ] Implement authentication module
- [ ] Implement repository discovery
- [ ] Implement pipeline discovery
- [ ] Implement deployment history tracking
- [ ] Create YAML parser for pipeline definitions
- [ ] Implement deployment-to-resource linking logic
- [ ] Extract connection strings and secrets (masked)
- [ ] Store data in graph database
- [ ] Add error handling and retry logic
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Create documentation

## Linking Examples

### Example 1: AKS Deployment
```
(Pipeline: "Deploy to Production")
    -[DEPLOYS_TO]-> (AKS Cluster: "prod-aks-cluster")
    
(Repository: "backend-api")
    -[USES_PIPELINE]-> (Pipeline: "Deploy to Production")
```

### Example 2: App Service Deployment
```
(Pipeline: "Web App CI/CD")
    -[DEPLOYS_TO]-> (App Service: "webapp-prod")
    
(Deployment Run: "Run #142")
    -[DEPLOYED_BY]-> (Pipeline: "Web App CI/CD")
    -[DEPLOYED_TO]-> (App Service: "webapp-prod")
    -[DEPLOYED_AT]-> timestamp
```

## Success Criteria

- [ ] Can authenticate with Azure DevOps
- [ ] Discovers repositories, pipelines, and deployments
- [ ] Correctly parses YAML pipeline definitions
- [ ] Links deployments to cloud resources
- [ ] Stores relationships in graph database
- [ ] Handles API rate limits gracefully
- [ ] Tests pass with >80% coverage
- [ ] Documentation complete

## Security Considerations

- Never log PATs or credentials
- Mask sensitive values in logs
- Store credentials securely (Key Vault)
- Implement proper access controls
- Audit access to deployment information

## Dependencies

- Issue #1: Technology Stack Decision
- Issue #2: Core Data Models
- Issue #3: Azure Resource Discovery (for linking)
- Azure DevOps organization for testing

## Timeline

Weeks 3-4

## Related Issues

- Issue #5: GitHub Integration (similar pattern)
- Issue #6: GitLab Integration
