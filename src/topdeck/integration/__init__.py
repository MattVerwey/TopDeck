"""Platform integrations for CI/CD and code repositories.

This module contains integrations with:
- Azure DevOps: Pipelines, repositories, deployments
- GitHub: Actions, repositories, deployments
- GitLab: CI/CD, repositories (future)
"""

from .github import GitHubIntegration

__all__ = ["GitHubIntegration"]
