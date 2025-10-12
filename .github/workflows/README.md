# GitHub Actions Workflows

This directory will contain CI/CD workflows for TopDeck.

## Planned Workflows

### 1. CI - Continuous Integration
**Trigger**: Pull requests and pushes to main/develop

**Jobs**:
- **Lint**: Run linters (pylint/flake8 or golint)
- **Test**: Run unit and integration tests
- **Build**: Build application
- **Security Scan**: Run CodeQL and dependency scanning

### 2. CD - Continuous Deployment
**Trigger**: Successful merge to main

**Jobs**:
- **Build Images**: Build Docker images
- **Push to Registry**: Push to container registry
- **Deploy to Dev**: Deploy to development environment
- **Integration Tests**: Run E2E tests
- **Deploy to Prod**: Deploy to production (manual approval)

### 3. Documentation
**Trigger**: Changes to /docs directory

**Jobs**:
- **Build Docs**: Build documentation site
- **Deploy Docs**: Deploy to GitHub Pages or documentation host

### 4. Scheduled Jobs
**Trigger**: Cron schedule

**Jobs**:
- **Dependency Updates**: Check for dependency updates
- **Security Scan**: Weekly security scan
- **Performance Tests**: Monthly performance benchmarks

## Example Workflow Files

Create these files when ready to implement CI/CD:

- `ci.yml` - Continuous integration
- `cd.yml` - Continuous deployment
- `security.yml` - Security scanning
- `docs.yml` - Documentation deployment
- `release.yml` - Release automation

## Secrets Required

Configure these secrets in GitHub repository settings:

### Cloud Providers
- `AZURE_CREDENTIALS` - Azure service principal credentials
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `GCP_CREDENTIALS` - GCP service account JSON

### Container Registry
- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub password
- `ACR_USERNAME` - Azure Container Registry username
- `ACR_PASSWORD` - Azure Container Registry password

### Deployment
- `KUBECONFIG` - Kubernetes configuration for deployment

## Status Badges

Add these to README.md once workflows are created:

```markdown
![CI](https://github.com/MattVerwey/TopDeck/workflows/CI/badge.svg)
![CD](https://github.com/MattVerwey/TopDeck/workflows/CD/badge.svg)
![Security](https://github.com/MattVerwey/TopDeck/workflows/Security/badge.svg)
```
