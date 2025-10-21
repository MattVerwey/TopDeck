"""
Azure Resource Discovery Module.

This module provides functionality to discover and catalog Azure resources
including compute, networking, data services, and configuration resources.
"""

from .devops import AzureDevOpsDiscoverer
from .discoverer import AzureDiscoverer
from .mapper import AzureResourceMapper

__all__ = ["AzureDiscoverer", "AzureResourceMapper", "AzureDevOpsDiscoverer"]
