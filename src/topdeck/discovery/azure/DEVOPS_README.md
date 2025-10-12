# Azure DevOps Integration

This module provides integration with Azure DevOps to discover repositories, pipelines, and deployments, linking them to deployed Azure resources for complete application topology mapping.

## Overview

The Azure DevOps integration enables TopDeck to:
- Discover Git repositories from Azure DevOps projects
- Track build and release pipelines
- Map deployment history to Azure resources
- Link applications to source code repositories
- Extract deployment metadata from resource tags

## Features

### ✅ Implemented (Foundation)

1. **Deployment Metadata Extraction**
   - Extract version, pipeline ID, commit SHA from resource tags
   - Support multiple tag naming conventions
   - Parse deployment timestamps
   - Track deployer information

2. **Application Inference**
   - Automatically infer applications from deployed resources
   - Support common naming patterns (e.g., `{env}-{app}-{type}`)
   - Extract application metadata from tags
   - Link applications to deployment methods (AKS, App Service, VM)

3. **Smart Tag Recognition**
   - Version tags: `deploy_version`, `version`, `app_version`, `image_tag`
   - Pipeline tags: `deploy_pipeline`, `pipeline_id`, `build_id`
   - Commit tags: `deploy_commit`, `commit_sha`, `git_commit`
   - Deployer tags: `deployed_by`, `deployer`, `owner`
   - Repository tags: `repository`, `repo_url`, `git_url`

4. **Data Models**
   - Complete Application model
   - Complete Repository model
   - Complete Deployment model
   - Neo4j conversion methods

### 🚧 Planned (API Integration)

1. **Repository Discovery**
   - List all Git repositories in project
   - Get repository details and metadata
   - Track branches and commits
   - Monitor repository activity

2. **Pipeline Discovery**
   - List build and release pipelines
   - Get pipeline configurations
   - Track pipeline runs and history
   - Extract deployment targets

3. **Deployment Tracking**
   - Get deployment history
   - Link deployments to resources
   - Track deployment status
   - Monitor deployment frequency

## Usage

### Basic Application Inference

```python
from topdeck.discovery.azure import AzureDiscoverer

# Discover Azure resources
discoverer = AzureDiscoverer(subscription_id="...")
result = await discoverer.discover_all_resources()

# Applications are automatically inferred from resources
print(f"Found {result.application_count} applications")

for app in result.applications:
    print(f"  - {app.name} ({app.environment})")
    print(f"    Deployment: {app.deployment_method}")
    print(f"    Version: {app.current_version}")
```

### Extract Deployment Metadata from Tags

```python
from topdeck.discovery.azure.devops import AzureDevOpsDiscoverer

discoverer = AzureDevOpsDiscoverer(organization="myorg", project="myproject")

# Example resource tags
tags = {
    "deploy_version": "v1.2.3",
    "deploy_pipeline": "pipeline-123",
    "commit_sha": "abc123def456",
    "deployed_by": "user@example.com",
    "repository": "https://dev.azure.com/myorg/myproject/_git/repo",
}

metadata = discoverer.extract_deployment_metadata_from_tags(tags)

# Returns:
# {
#     "version": "v1.2.3",
#     "pipeline_id": "pipeline-123",
#     "commit_sha": "abc123def456",
#     "deployed_by": "user@example.com",
#     "repository_url": "https://dev.azure.com/myorg/myproject/_git/repo"
# }
```

### Infer Application from Resource

```python
from topdeck.discovery.azure.devops import AzureDevOpsDiscoverer

discoverer = AzureDevOpsDiscoverer(organization="myorg", project="myproject")

tags = {
    "app_name": "ecommerce",
    "environment": "prod",
    "owner_team": "platform-team",
}

app = discoverer.infer_application_from_resource(
    resource_name="prod-ecommerce-aks",
    resource_type="aks",
    tags=tags,
)

# Returns Application object with:
# - name: "ecommerce"
# - environment: "prod"
# - deployment_method: "aks"
# - owner_team: "platform-team"
```

### Combined Discovery (Infrastructure + DevOps)

```python
from topdeck.discovery.azure import AzureDiscoverer

discoverer = AzureDiscoverer(subscription_id="...")

# Discover both infrastructure and DevOps artifacts
result = await discoverer.discover_with_devops(
    organization="myorg",
    project="myproject",
    personal_access_token="...",  # Optional PAT for authentication
)

print(f"Resources: {result.resource_count}")
print(f"Applications: {result.application_count}")
print(f"Repositories: {result.repository_count}")
print(f"Deployments: {result.deployment_count}")
print(f"Dependencies: {result.dependency_count}")
```

### Store in Neo4j

```python
from topdeck.storage.neo4j_client import Neo4jClient

client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
client.connect()

# Store applications
for app in result.applications:
    client.upsert_application(app.to_neo4j_properties())

# Store repositories
for repo in result.repositories:
    client.upsert_repository(repo.to_neo4j_properties())

# Store deployments
for deployment in result.deployments:
    client.upsert_deployment(deployment.to_neo4j_properties())

# Create relationships
for app in result.applications:
    if app.repository_id:
        # Link application to repository (BUILT_FROM)
        client.create_relationship(
            app.id, "Application",
            app.repository_id, "Repository",
            "BUILT_FROM",
            {"branch": "main"}
        )
```

## Tagging Conventions

To enable automatic discovery and linking, tag your Azure resources with deployment metadata:

### Recommended Tags

```yaml
# Version Information
deploy_version: "v1.2.3"          # or: version, app_version, image_tag

# Pipeline Information
deploy_pipeline: "pipeline-123"    # or: pipeline_id, build_id

# Commit Information
deploy_commit: "abc123def456"      # or: commit_sha, git_commit

# Deployment Information
deployed_by: "user@example.com"    # or: deployer, owner
deploy_date: "2024-10-12T10:30:00Z"  # ISO format

# Repository Information
repository: "https://dev.azure.com/org/project/_git/repo"  # or: repo_url

# Application Information
app_name: "ecommerce"              # or: application, service_name
environment: "prod"                 # or: env
owner_team: "platform-team"        # or: team, owner
```

### Tag Example for AKS Cluster

```terraform
resource "azurerm_kubernetes_cluster" "example" {
  name                = "prod-ecommerce-aks"
  location            = "East US"
  resource_group_name = "rg-prod"
  
  tags = {
    app_name        = "ecommerce"
    environment     = "prod"
    owner_team      = "platform-team"
    deploy_version  = "v1.2.3"
    deploy_pipeline = "pipeline-123"
    commit_sha      = "abc123def456"
    deployed_by     = "user@example.com"
    deploy_date     = "2024-10-12T10:30:00Z"
    repository      = "https://dev.azure.com/myorg/myproject/_git/ecommerce"
  }
}
```

## Resource Naming Patterns

TopDeck recognizes common resource naming patterns to infer applications:

### Pattern: `{environment}-{application}-{resource_type}`

Examples:
- `prod-ecommerce-aks` → app: "ecommerce", env: "prod"
- `staging-api-service` → app: "api", env: "staging"
- `dev-webapp-app` → app: "webapp", env: "dev"

### Pattern: `{application}-{environment}-{resource_type}`

Examples:
- `ecommerce-prod-aks` → app: "ecommerce", env: "prod"
- `api-staging-service` → app: "api", env: "staging"

### Pattern: Application from tags

If resource naming doesn't follow a pattern, use explicit tags:

```yaml
tags:
  app_name: "my-complex-application-name"
  environment: "production"
```

## Azure DevOps API Integration (Planned)

### Repository Discovery

```python
# TODO: Implement
repositories = await devops_discoverer.discover_repositories()

for repo in repositories:
    print(f"Repository: {repo.name}")
    print(f"  URL: {repo.url}")
    print(f"  Branch: {repo.default_branch}")
    print(f"  Last commit: {repo.last_commit_sha}")
```

### Pipeline Discovery

```python
# TODO: Implement
deployments = await devops_discoverer.discover_deployments(limit=100)

for deployment in deployments:
    print(f"Deployment: {deployment.version}")
    print(f"  Pipeline: {deployment.pipeline_name}")
    print(f"  Status: {deployment.status}")
    print(f"  Environment: {deployment.environment}")
    print(f"  Deployed: {deployment.deployed_at}")
```

### Application Discovery

```python
# TODO: Implement
applications = await devops_discoverer.discover_applications()

for app in applications:
    print(f"Application: {app.name}")
    print(f"  Repository: {app.repository_url}")
    print(f"  Version: {app.current_version}")
    print(f"  Health: {app.health_score}")
```

## Architecture

### Data Flow

```
Azure Resources → Extract Tags → Infer Applications
       ↓                              ↓
    Neo4j                        Neo4j
       ↓                              ↓
  Resources                    Applications
       ↓                              ↓
       └──── DEPLOYED_TO ────────────┘

Azure DevOps → Discover Repos → Store in Neo4j
       ↓              ↓                 ↓
   Pipelines    Deployments       Repositories
       ↓              ↓                 ↓
       └──────────────┴─────────────────┘
                      ↓
              Link to Resources
```

### Component Diagram

```
┌─────────────────────────────────────────┐
│       AzureDiscoverer                   │
│  - discover_all_resources()             │
│  - discover_with_devops()               │
│  - _infer_applications()                │
└────────────┬────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│    AzureDevOpsDiscoverer                │
│  - extract_deployment_metadata()        │
│  - infer_application_from_resource()    │
│  - discover_repositories() [TODO]       │
│  - discover_deployments() [TODO]        │
└────────────┬────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│         Neo4jClient                     │
│  - upsert_application()                 │
│  - upsert_repository()                  │
│  - upsert_deployment()                  │
│  - create_relationship()                │
└─────────────────────────────────────────┘
```

## Future Enhancements

### Phase 1: API Integration ✅
- [x] Foundation implemented
- [ ] Azure DevOps REST API calls
- [ ] Authentication handling
- [ ] Response parsing and mapping

### Phase 2: Advanced Discovery
- [ ] Parse pipeline YAML for configurations
- [ ] Extract service connections
- [ ] Discover variable groups
- [ ] Track deployment approvals

### Phase 3: Relationship Mapping
- [ ] Link pipelines to deployed resources
- [ ] Track deployment history over time
- [ ] Map code changes to resource changes
- [ ] Correlate with incidents

### Phase 4: Multi-Repository Support
- [ ] GitHub integration
- [ ] GitLab integration
- [ ] Bitbucket integration
- [ ] Generic Git support

## Testing

```bash
# Run unit tests
pytest tests/discovery/azure/test_devops.py -v

# Run integration tests (requires Azure DevOps)
pytest tests/integration/test_devops_integration.py -v
```

## Configuration

### Environment Variables

```bash
# Azure DevOps configuration
export AZURE_DEVOPS_ORG="myorg"
export AZURE_DEVOPS_PROJECT="myproject"
export AZURE_DEVOPS_PAT="personal-access-token"

# Azure subscription
export AZURE_SUBSCRIPTION_ID="..."
```

### Configuration File

```yaml
# config.yaml
azure_devops:
  organization: myorg
  project: myproject
  pat: ${AZURE_DEVOPS_PAT}  # From environment variable
  
discovery:
  infer_applications: true
  extract_metadata: true
  tag_patterns:
    - app_name
    - application
    - service_name
```

## Troubleshooting

### Applications Not Inferred

**Problem**: Applications not appearing in discovery results.

**Solutions**:
1. Add explicit `app_name` tag to resources
2. Follow naming conventions: `{env}-{app}-{type}`
3. Check that resource is a deployable type (AKS, App Service, VM)

### Deployment Metadata Missing

**Problem**: Deployment metadata not extracted from tags.

**Solutions**:
1. Ensure tags use supported naming conventions
2. Add standard tags: `deploy_version`, `deploy_pipeline`, etc.
3. Check tag values are not empty

### Repository URL Not Linked

**Problem**: Applications don't link to repositories.

**Solutions**:
1. Add `repository` or `repo_url` tag to resources
2. Include repository URL in application tags
3. Ensure URL is valid and accessible

## References

- [Azure DevOps REST API Documentation](https://docs.microsoft.com/en-us/rest/api/azure/devops/)
- [TopDeck Data Models](../../docs/architecture/data-models.md)
- [Neo4j Schema](../../docs/architecture/neo4j-schema.cypher)
- [Issue #3: Azure Resource Discovery](../../docs/issues/issue-003-azure-resource-discovery.md)
- [Issue #4: Azure DevOps Integration](../../docs/issues/issue-004-azure-devops-integration.md)

---

**Status**: Foundation Complete ✅  
**API Integration**: Planned 🚧  
**Last Updated**: 2025-10-12
