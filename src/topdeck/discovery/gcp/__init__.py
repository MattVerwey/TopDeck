"""
GCP resource discovery module.

Discovers and maps GCP resources to TopDeck's normalized model.
"""

from .discoverer import GCPDiscoverer
from .mapper import GCPResourceMapper

__all__ = ["GCPResourceMapper", "GCPDiscoverer"]
