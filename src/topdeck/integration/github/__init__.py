"""
GitHub Integration for Repository and Deployment Discovery.

Discovers repositories, GitHub Actions workflows, and deployments from GitHub.
"""

from .client import GitHubIntegration

__all__ = ["GitHubIntegration"]
