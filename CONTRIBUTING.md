# Contributing to TopDeck

Thank you for your interest in contributing to TopDeck! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors. We expect all participants to:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

1. **Development Tools**
   - Git
   - Docker and Docker Compose
   - Python 3.11+ or Go 1.21+ (depending on component)
   - Node.js 18+ (for frontend development)

2. **Cloud Accounts** (for testing)
   - Azure subscription (free tier acceptable)
   - AWS account (free tier acceptable)
   - GCP project (free tier acceptable)

3. **Required Services**
   - Neo4j (can run via Docker)
   - Redis (can run via Docker)

### Setting Up Development Environment

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR-USERNAME/TopDeck.git
cd TopDeck

# 3. Add upstream remote
git remote add upstream https://github.com/MattVerwey/TopDeck.git

# 4. Create a feature branch
git checkout -b feature/your-feature-name

# 5. Set up development environment
# (Instructions will be added as tech stack is finalized)
```

## Development Process

### Branching Strategy

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes
- `docs/*` - Documentation updates

### Workflow

1. **Create an Issue** - Before starting work, create or find an issue
2. **Branch** - Create a feature branch from `develop`
3. **Develop** - Write code following our standards
4. **Test** - Ensure all tests pass and add new tests
5. **Commit** - Make clear, atomic commits
6. **Push** - Push your branch to your fork
7. **Pull Request** - Submit a PR to `develop` branch

## Coding Standards

### General Principles

- **SOLID Principles** - Follow SOLID design principles
- **DRY** - Don't Repeat Yourself
- **KISS** - Keep It Simple, Stupid
- **YAGNI** - You Aren't Gonna Need It
- **Separation of Concerns** - Keep components focused and modular

### Python Standards (if Python is chosen)

```python
# Follow PEP 8 style guide
# Use type hints
# Document with docstrings

from typing import List, Dict

def discover_resources(cloud_provider: str) -> List[Dict[str, str]]:
    """
    Discover resources from the specified cloud provider.
    
    Args:
        cloud_provider: Name of the cloud provider (azure, aws, gcp)
        
    Returns:
        List of discovered resources as dictionaries
        
    Raises:
        ValueError: If cloud_provider is not supported
    """
    pass
```

**Tools:**
- `black` - Code formatting
- `pylint` / `flake8` - Linting
- `mypy` - Type checking
- `pytest` - Testing

### Go Standards (if Go is chosen)

```go
// Follow Go standard conventions
// Use gofmt for formatting
// Document exported functions

package discovery

// DiscoverResources discovers resources from the specified cloud provider.
// Returns a slice of resources and an error if the operation fails.
func DiscoverResources(cloudProvider string) ([]Resource, error) {
    // Implementation
}
```

**Tools:**
- `gofmt` - Code formatting
- `golint` / `staticcheck` - Linting
- `go vet` - Static analysis
- Built-in `testing` package

### JavaScript/TypeScript Standards (Frontend)

```typescript
// Use TypeScript for type safety
// Follow Airbnb style guide
// Use functional components with hooks

interface Resource {
  id: string;
  type: string;
  name: string;
}

export const ResourceList: React.FC<{ resources: Resource[] }> = ({ 
  resources 
}) => {
  return (
    <div>
      {resources.map(resource => (
        <ResourceCard key={resource.id} resource={resource} />
      ))}
    </div>
  );
};
```

**Tools:**
- `prettier` - Code formatting
- `eslint` - Linting
- `jest` - Testing
- `react-testing-library` - Component testing

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting)
- `refactor` - Code refactoring
- `test` - Adding or updating tests
- `chore` - Maintenance tasks

**Examples:**
```
feat(discovery): add Azure AKS cluster discovery

Implements discovery of AKS clusters including node pools,
networking configuration, and associated resources.

Closes #42
```

```
fix(api): correct error handling in resource endpoint

Previously, the endpoint would return 500 instead of 404
when a resource was not found.

Fixes #89
```

## Pull Request Process

### Before Submitting

1. **Update Documentation** - Update relevant docs
2. **Add Tests** - Ensure adequate test coverage
3. **Run Tests** - All tests must pass
4. **Run Linters** - Code must pass linting
5. **Update CHANGELOG** - Add entry for your changes
6. **Rebase** - Rebase on latest `develop`

### PR Description Template

```markdown
## Description
Brief description of changes

## Related Issue
Closes #<issue-number>

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added and passing
- [ ] Dependent changes merged
```

### Review Process

1. **Automated Checks** - CI/CD must pass
2. **Code Review** - At least one approval required
3. **Address Feedback** - Respond to all comments
4. **Squash Commits** - May be required before merge
5. **Merge** - Maintainer will merge when approved

## Issue Guidelines

### Creating Issues

Use appropriate issue templates:

- **Bug Report** - For reporting bugs
- **Feature Request** - For suggesting features
- **Documentation** - For doc improvements
- **Question** - For asking questions

### Issue Labels

- `bug` - Something isn't working
- `enhancement` - New feature or improvement
- `documentation` - Documentation needs
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `priority: high` - High priority
- `priority: medium` - Medium priority
- `priority: low` - Low priority
- `cloud: azure` - Azure-related
- `cloud: aws` - AWS-related
- `cloud: gcp` - GCP-related

## Testing Guidelines

### Test Coverage

- Aim for >80% code coverage
- Critical paths must have 100% coverage
- Write tests for edge cases

### Test Types

1. **Unit Tests**
   - Test individual functions/methods
   - Mock external dependencies
   - Fast execution

2. **Integration Tests**
   - Test component interactions
   - Use test databases/services
   - Verify data flow

3. **End-to-End Tests**
   - Test complete workflows
   - Simulate real user scenarios
   - Test critical paths

### Test Naming

```python
# Python
def test_discover_azure_resources_returns_list():
    pass

def test_discover_azure_resources_handles_auth_error():
    pass
```

```go
// Go
func TestDiscoverAzureResources_ReturnsList(t *testing.T) {}
func TestDiscoverAzureResources_HandlesAuthError(t *testing.T) {}
```

## Documentation

### Code Documentation

- Document all public APIs
- Explain complex algorithms
- Include examples for key functions
- Keep docs up-to-date with code

### Architecture Decisions

Use Architecture Decision Records (ADRs) for significant decisions:

```markdown
# ADR-001: Use Neo4j for Graph Database

## Status
Accepted

## Context
Need a database to store resource relationships and dependencies.

## Decision
Use Neo4j graph database for storing topology.

## Consequences
- Pros: Native graph queries, good visualization tools
- Cons: Additional service to manage
```

## Questions?

- Check existing documentation in `/docs`
- Search closed issues
- Ask in GitHub Discussions
- Contact maintainers

## Recognition

Contributors will be recognized in:
- README contributors section
- Release notes
- Project documentation

Thank you for contributing to TopDeck! 🚀
