"""
AWS resource discovery module.

Discovers and maps AWS resources to TopDeck's normalized model.
"""

from .mapper import AWSResourceMapper
from .discoverer import AWSDiscoverer

__all__ = ["AWSResourceMapper", "AWSDiscoverer"]
