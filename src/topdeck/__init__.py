"""
TopDeck - Multi-Cloud Integration & Risk Analysis Platform

A platform for discovering, mapping, and analyzing cloud infrastructure
and application dependencies across Azure, AWS, and GCP.
"""

__version__ = "0.1.0"
__author__ = "TopDeck Team"
__license__ = "MIT"

# Don't import Settings by default to avoid pydantic dependency
# Users can: from topdeck.common.config import Settings

__all__ = ["__version__"]
