"""
AWS resource discovery module.

Discovers and maps AWS resources to TopDeck's normalized model.
"""

from .discoverer import AWSDiscoverer
from .mapper import AWSResourceMapper

__all__ = ["AWSResourceMapper", "AWSDiscoverer"]
