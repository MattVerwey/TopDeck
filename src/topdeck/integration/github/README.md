# GitHub Integration

GitHub integration module for TopDeck, enabling discovery of repositories, GitHub Actions workflows, and deployments.

## Overview

This module provides comprehensive GitHub integration capabilities:

- **Repository Discovery**: List and analyze repositories from organizations or users
- **GitHub Actions Integration**: Discover workflows and track workflow runs
- **Deployment Tracking**: Monitor deployments and link them to cloud resources
- **Application Inference**: Identify applications from repository metadata

## Features

### Repository Discovery

Discovers repositories with complete metadata:
- Basic information (name, description, URL)
- Repository structure and languages
- Activity metrics (stars, forks, issues)
- Topics and tags
- Branch information

### GitHub Actions Integration

Tracks CI/CD pipelines:
- Workflow definitions (.github/workflows/*.yml)
- Workflow run history
- Deployment events
- Build and deployment status

### Deployment Tracking

Links deployments to infrastructure:
- Deployment history and status
- Environment tracking (production, staging, dev)
- Commit and version tracking
- Deployment metadata

### Application Inference

Identifies applications from repositories:
- Smart environment detection from topics/names
- Repository-to-application mapping
- Ownership and team information

## Usage

### Basic Setup

```python
from topdeck.integration.github import GitHubIntegration

# Initialize with token and organization
github = GitHubIntegration(
    token="ghp_your_personal_access_token",
    organization="your-org"
)

# Or for a specific user
github = GitHubIntegration(
    token="ghp_your_personal_access_token",
    user="your-username"
)
```

### Discover Repositories

```python
# Discover all repositories
repositories = await github.discover_repositories()

for repo in repositories:
    print(f"Repository: {repo.name}")
    print(f"  URL: {repo.url}")
    print(f"  Language: {repo.language}")
    print(f"  Stars: {repo.stars}")
    print(f"  Topics: {', '.join(repo.topics)}")
```

### Discover GitHub Actions Workflows

```python
# Discover workflows in a repository
workflows = await github.discover_workflows("your-org/your-repo")

for workflow in workflows:
    print(f"Workflow: {workflow['name']}")
    print(f"  Path: {workflow['path']}")
    print(f"  State: {workflow['state']}")
```

### Discover Workflow Runs

```python
# Get recent workflow runs
runs = await github.discover_workflow_runs(
    repo_full_name="your-org/your-repo",
    limit=50
)

for run in runs:
    print(f"Run #{run['id']}: {run['name']}")
    print(f"  Status: {run['status']}")
    print(f"  Conclusion: {run['conclusion']}")
```

### Discover Deployments

```python
# Discover deployments for a repository
deployments = await github.discover_deployments("your-org/your-repo")

for deployment in deployments:
    print(f"Deployment: {deployment.id}")
    print(f"  Environment: {deployment.environment}")
    print(f"  Version: {deployment.version}")
    print(f"  Status: {deployment.status}")
    print(f"  Deployed by: {deployment.deployed_by}")
```

### Discover Applications

```python
# Infer applications from repositories
applications = await github.discover_applications()

for app in applications:
    print(f"Application: {app.name}")
    print(f"  Repository: {app.repository_url}")
    print(f"  Environment: {app.environment}")
    print(f"  Owner: {app.owner_team}")
```

### Complete Discovery Example

```python
import asyncio
from topdeck.integration.github import GitHubIntegration

async def main():
    # Initialize GitHub integration
    github = GitHubIntegration(
        token="ghp_your_token",
        organization="your-org"
    )
    
    try:
        # Discover repositories
        print("Discovering repositories...")
        repositories = await github.discover_repositories()
        print(f"Found {len(repositories)} repositories")
        
        # For each repository, discover workflows and deployments
        for repo in repositories[:5]:  # Limit to first 5 for demo
            print(f"\nRepository: {repo.full_name}")
            
            # Discover workflows
            workflows = await github.discover_workflows(repo.full_name)
            print(f"  Workflows: {len(workflows)}")
            
            # Discover deployments
            deployments = await github.discover_deployments(repo.full_name)
            print(f"  Deployments: {len(deployments)}")
        
        # Infer applications
        print("\nDiscovering applications...")
        applications = await github.discover_applications()
        print(f"Found {len(applications)} applications")
        
    finally:
        # Always close the client
        await github.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Authentication

### Personal Access Token (PAT)

The recommended authentication method for testing and development:

1. Generate a PAT in GitHub Settings → Developer settings → Personal access tokens
2. Required scopes:
   - `repo` - Access to repositories
   - `workflow` - Access to GitHub Actions
   - `read:org` - Read organization data (if using organizations)

3. Store token securely:
   ```bash
   export GITHUB_TOKEN="ghp_your_token_here"
   ```

4. Use in code:
   ```python
   import os
   
   github = GitHubIntegration(
       token=os.getenv("GITHUB_TOKEN"),
       organization="your-org"
   )
   ```

### GitHub App (Future)

GitHub App authentication provides better security and higher rate limits. This will be supported in a future release.

## Rate Limiting

GitHub API has rate limits:
- **Authenticated**: 5,000 requests per hour
- **Unauthenticated**: 60 requests per hour

The integration automatically:
- Limits requests to ~80 per minute (safe margin)
- Monitors rate limit headers
- Warns when rate limit is low
- Implements retry logic with exponential backoff

## Error Handling

The integration includes comprehensive error handling:

### Automatic Retry

Failed requests are automatically retried with exponential backoff:
- Max 3 attempts
- Initial delay: 1 second
- Max delay: 30 seconds

### Error Tracking

Batch operations track errors:
```python
from topdeck.common.resilience import ErrorTracker

tracker = ErrorTracker()
# Errors are tracked automatically during discovery
```

### Graceful Degradation

The integration continues processing even if some operations fail:
- 404 errors are logged but don't stop discovery
- Individual repository failures don't affect others
- Partial results are returned

## Configuration

### Environment Variables

```bash
# GitHub authentication
export GITHUB_TOKEN="ghp_your_token"

# Optional: Default organization
export GITHUB_ORG="your-org"

# Optional: Rate limit (requests per minute)
export GITHUB_RATE_LIMIT=80
```

### Programmatic Configuration

```python
from topdeck.integration.github import GitHubIntegration
from topdeck.common.resilience import RateLimiter, RetryConfig

# Custom rate limiting
github = GitHubIntegration(token="ghp_token", organization="org")
github._rate_limiter = RateLimiter(max_calls=100, time_window=60.0)

# Custom retry configuration
github._retry_config = RetryConfig(
    max_attempts=5,
    initial_delay=2.0,
    max_delay=60.0,
)
```

## Integration with Neo4j

Store discovered data in Neo4j:

```python
from topdeck.storage.neo4j_client import Neo4jClient

# Initialize clients
github = GitHubIntegration(token="ghp_token", organization="org")
neo4j = Neo4jClient("bolt://localhost:7687", "neo4j", "password")

# Discover and store
repositories = await github.discover_repositories()
for repo in repositories:
    await neo4j.create_repository(repo)

applications = await github.discover_applications()
for app in applications:
    await neo4j.create_application(app)

# Create relationships
for app in applications:
    if app.repository_id:
        await neo4j.create_relationship(
            from_id=app.id,
            to_id=app.repository_id,
            relationship_type="BUILT_FROM"
        )
```

## Best Practices

### 1. Always Close Clients

```python
async def discover():
    github = GitHubIntegration(token="ghp_token", organization="org")
    try:
        repositories = await github.discover_repositories()
        return repositories
    finally:
        await github.close()
```

### 2. Use Context Managers (Future)

```python
# Future feature
async with GitHubIntegration(token="ghp_token", organization="org") as github:
    repositories = await github.discover_repositories()
```

### 3. Handle Rate Limits

```python
import asyncio

async def discover_with_backoff():
    github = GitHubIntegration(token="ghp_token", organization="org")
    
    try:
        repositories = await github.discover_repositories()
        
        # Wait between operations to avoid rate limits
        await asyncio.sleep(1)
        
        for repo in repositories:
            workflows = await github.discover_workflows(repo.full_name)
            await asyncio.sleep(0.5)  # Small delay between repos
    
    finally:
        await github.close()
```

### 4. Filter Repositories

```python
# Discover only active repositories
repositories = await github.discover_repositories()
active_repos = [r for r in repositories if not r.is_archived]

# Filter by language
python_repos = [r for r in repositories if r.language == "Python"]

# Filter by topics
prod_repos = [r for r in repositories if "production" in r.topics]
```

## Troubleshooting

### Authentication Errors

**Error**: `401 Unauthorized`
**Solution**: Check token validity and required scopes

```python
# Verify token has required scopes
# Required: repo, workflow, read:org (for organizations)
```

### Rate Limit Errors

**Error**: `403 Forbidden` with rate limit message
**Solution**: Wait for rate limit reset or reduce request frequency

```python
# Check rate limit status
headers = github._headers
# Add delay between requests
await asyncio.sleep(1)
```

### 404 Errors

**Error**: `404 Not Found`
**Solutions**:
- Verify organization/user name is correct
- Ensure token has access to the repository
- Check repository exists and is not deleted

### Empty Results

**Issue**: No repositories found
**Solutions**:
- Verify organization/user has repositories
- Check token has access to repositories
- Ensure repositories are not all archived (filtered out)

## Testing

Run the test suite:

```bash
# Run all GitHub integration tests
pytest tests/integration/github/

# Run specific test
pytest tests/integration/github/test_client.py::TestGitHubIntegration::test_parse_repository

# Run with coverage
pytest tests/integration/github/ --cov=src/topdeck/integration/github
```

## Performance Considerations

### Parallel Discovery

For large organizations, consider parallel repository processing:

```python
import asyncio

async def discover_repository_details(github, repo):
    workflows = await github.discover_workflows(repo.full_name)
    deployments = await github.discover_deployments(repo.full_name)
    return repo, workflows, deployments

async def parallel_discovery():
    github = GitHubIntegration(token="ghp_token", organization="org")
    
    try:
        # Discover repositories first
        repositories = await github.discover_repositories()
        
        # Process repositories in parallel (batches of 5)
        batch_size = 5
        for i in range(0, len(repositories), batch_size):
            batch = repositories[i:i+batch_size]
            tasks = [
                discover_repository_details(github, repo)
                for repo in batch
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    print(f"Error: {result}")
                else:
                    repo, workflows, deployments = result
                    print(f"Processed {repo.name}: {len(workflows)} workflows, {len(deployments)} deployments")
    
    finally:
        await github.close()
```

### Caching

For frequently accessed data, consider caching:

```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedGitHubIntegration(GitHubIntegration):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache = {}
        self._cache_ttl = timedelta(minutes=5)
    
    async def discover_repositories_cached(self):
        cache_key = "repositories"
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if datetime.utcnow() - timestamp < self._cache_ttl:
                return data
        
        repositories = await self.discover_repositories()
        self._cache[cache_key] = (repositories, datetime.utcnow())
        return repositories
```

## Future Enhancements

- [ ] GitHub App authentication support
- [ ] Webhook integration for real-time updates
- [ ] Advanced workflow parsing (extract deployment targets)
- [ ] Branch protection rule discovery
- [ ] Pull request integration
- [ ] GitHub Packages integration
- [ ] Repository dependency graph analysis
- [ ] Security alert integration
- [ ] Code scanning results
- [ ] Deployment environment tracking

## Related Documentation

- [Azure DevOps Integration](../../discovery/azure/devops.py)
- [Data Models](../../discovery/models.py)
- [Resilience Patterns](../../common/resilience.py)
- [Neo4j Client](../../storage/neo4j_client.py)
- [Issue #10: GitHub Integration](../../../docs/issues/issue-010-github-integration.md)

## Contributing

When adding new features:

1. Follow the existing code structure and patterns
2. Add comprehensive tests
3. Update this documentation
4. Ensure rate limiting is properly implemented
5. Add error handling and logging
6. Test with various repository types and sizes

## License

MIT License - See LICENSE file for details
