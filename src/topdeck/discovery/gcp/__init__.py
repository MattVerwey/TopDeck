"""
GCP resource discovery module.

Discovers and maps GCP resources to TopDeck's normalized model.
"""

from .mapper import GCPResourceMapper
from .discoverer import GCPDiscoverer

__all__ = ["GCPResourceMapper", "GCPDiscoverer"]
