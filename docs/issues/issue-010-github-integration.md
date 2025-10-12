# Issue #10: Implement GitHub Integration

**Labels**: `enhancement`, `integration`, `priority: high`, `phase-3`

## Description

Implement the GitHub integration module that discovers repositories, analyzes GitHub Actions workflows, tracks deployments, and links code to deployed cloud resources. This complements the Azure DevOps integration and provides visibility into GitHub-based CI/CD pipelines.

## Scope

### Integration Features

**Repository Discovery**:
- List all repositories in an organization or user account
- Extract repository metadata (name, description, topics, languages)
- Track repository structure and key files
- Identify deployment-related files (Dockerfiles, k8s manifests, Terraform configs)

**GitHub Actions Integration**:
- Discover workflow files (.github/workflows/*.yml)
- Parse workflow definitions
- Track workflow runs and deployment history
- Extract deployment targets and environments
- Identify secrets and variables used

**Deployment Tracking**:
- Monitor GitHub Actions deployment events
- Link deployments to cloud resources
- Track deployment status and outcomes
- Correlate commits to deployed versions

**Code Analysis**:
- Parse application configuration files
- Extract connection strings and service dependencies
- Identify infrastructure-as-code (Terraform, CloudFormation, etc.)
- Map code repositories to deployed services

## Requirements

### Authentication
- Support Personal Access Token (PAT)
- Support GitHub App authentication
- Support OAuth 2.0 for user access
- Securely store credentials

### Linking Logic
- Match GitHub Actions deployments to discovered cloud resources
- Extract deployment targets from workflow YAML
- Parse deployment environments (production, staging, etc.)
- Link source code repositories to deployed services
- Track which commit/tag is currently deployed

### Data Extraction
- Repository metadata and activity
- Workflow definitions and runs
- Deployment history
- Environment configurations
- Secrets and variables (names only, not values)
- Branch protection rules
- Pull request integrations with deployments

## Technical Design

### Module Structure
```
src/integration/github/
├── __init__.py
├── client.py           # GitHub API client
├── authenticator.py    # Authentication logic
├── repositories.py     # Repository discovery
├── workflows.py        # GitHub Actions workflow discovery
├── deployments.py      # Deployment tracking
├── parser.py           # YAML workflow parser
├── linker.py           # Link deployments to resources
└── config.py           # Configuration
```

### Key Classes

```python
class GitHubIntegration:
    def __init__(self, token: str, organization: str = None):
        """Initialize GitHub integration"""
        
    def discover_repositories(self) -> List[Repository]:
        """Discover all accessible repositories"""
        
    def discover_workflows(self, repo: str) -> List[Workflow]:
        """Discover workflows in a repository"""
        
    def get_workflow_runs(self, repo: str, workflow_id: str, limit: int = 50) -> List[WorkflowRun]:
        """Get recent workflow runs"""
        
    def get_deployments(self, repo: str) -> List[Deployment]:
        """Get deployment history for a repository"""
        
    def link_deployment_to_resources(self, deployment: Deployment) -> List[ResourceLink]:
        """Link a deployment to cloud resources"""
```

### Configuration

```yaml
# config/github.yaml
github:
  authentication:
    method: pat  # or github_app, oauth
    token: ${GITHUB_TOKEN}
    app_id: ${GITHUB_APP_ID}
    private_key: ${GITHUB_APP_PRIVATE_KEY}
  
  discovery:
    organizations:
      - my-org
    users:
      - my-user
    
    repositories:
      include:
        - "my-org/*"
      exclude:
        - "*/archive-*"
        - "*/test-*"
    
    scan_interval: 1800  # seconds
    workflow_run_limit: 100
    
  linking:
    deployment_patterns:
      # Patterns to identify cloud resources in workflow files
      azure:
        - resource_group: "\\$\\{\\{ secrets\\.AZURE_RG \\}\\}"
        - app_name: "\\$\\{\\{ secrets\\.AZURE_APP_NAME \\}\\}"
      aws:
        - cluster: "\\$\\{\\{ secrets\\.EKS_CLUSTER \\}\\}"
        - function: "\\$\\{\\{ secrets\\.LAMBDA_FUNCTION \\}\\}"
      gcp:
        - project: "\\$\\{\\{ secrets\\.GCP_PROJECT \\}\\}"
        - cluster: "\\$\\{\\{ secrets\\.GKE_CLUSTER \\}\\}"
```

## Tasks

- [ ] Set up GitHub REST API and GraphQL API client
- [ ] Implement authentication module (PAT, GitHub App, OAuth)
- [ ] Implement repository discovery
- [ ] Implement GitHub Actions workflow discovery
- [ ] Implement workflow run tracking
- [ ] Create YAML parser for workflow definitions
- [ ] Implement deployment event tracking
- [ ] Implement deployment-to-resource linking logic
- [ ] Extract and parse infrastructure-as-code files
- [ ] Parse application configuration for dependencies
- [ ] Store data in graph database
- [ ] Create webhook handler for real-time updates
- [ ] Add error handling and retry logic
- [ ] Implement rate limiting for GitHub API
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Create documentation

## Linking Examples

### Example 1: GitHub Actions to AKS

**Workflow File** (.github/workflows/deploy.yml):
```yaml
name: Deploy to AKS
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: azure/k8s-set-context@v1
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG }}
      - name: Deploy to AKS
        run: |
          kubectl apply -f k8s/deployment.yaml
          kubectl set image deployment/myapp myapp=${{ secrets.ACR_REGISTRY }}/myapp:${{ github.sha }}
```

**TopDeck Links**:
- Repository → AKS Cluster (extracted from kubeconfig)
- Workflow → Deployment object in AKS
- Commit SHA → Running container version
- ACR Registry → Container image source

### Example 2: GitHub Actions to AWS Lambda

**Workflow File**:
```yaml
name: Deploy Lambda
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Lambda
        uses: aws-actions/lambda-deploy@v1
        with:
          function-name: my-function
          zip-file: function.zip
```

**TopDeck Links**:
- Repository → Lambda Function
- Workflow → Lambda deployment
- Commit → Lambda version

## Success Criteria

- [ ] Successfully discovers repositories and workflows
- [ ] Accurately parses GitHub Actions workflow files
- [ ] Tracks deployment history with >95% accuracy
- [ ] Successfully links deployments to cloud resources
- [ ] Identifies resource dependencies from code
- [ ] Stores all data in Neo4j with proper relationships
- [ ] Handles GitHub API rate limits gracefully
- [ ] Supports webhook-based real-time updates
- [ ] Has >80% test coverage
- [ ] Documentation is complete with examples

## Security Considerations

- Use read-only tokens where possible
- Never log or expose tokens, secrets, or credentials
- Support GitHub App for better security over PATs
- Securely store credentials using secrets management
- Mask sensitive data in logs and UI
- Follow principle of least privilege
- Validate webhook signatures

## Dependencies

- Issue #1: Technology Stack Decision
- Issue #2: Core Data Models
- Issue #4: Azure DevOps Integration (reference implementation)
- GitHub REST API
- GitHub GraphQL API
- PyGithub or similar library

## Timeline

**Estimated Duration**: 2-3 weeks

**Phase 3 Priority**: High

## Related Issues

- Issue #4: Azure DevOps Integration
- Issue #3: Azure Resource Discovery
- Issue #8: AWS Resource Discovery
- Issue #9: GCP Resource Discovery

## Notes

- GitHub Actions is the primary CI/CD platform for GitHub
- Many organizations use both GitHub and Azure DevOps - support both
- GitHub Deployments API provides structured deployment tracking
- Consider supporting GitHub Packages for container registry linking
- GitHub Environments provide deployment protection rules
- Workflow reuse (reusable workflows and composite actions) should be handled
- Self-hosted runners may have different deployment patterns
