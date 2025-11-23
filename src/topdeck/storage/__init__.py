"""Data persistence layers.

This module contains:
- Graph: Neo4j graph database interface
- Cache: Redis caching layer
"""

from topdeck.storage.neo4j_client import Neo4jClient
from topdeck.storage.neo4j_manager import (
    Neo4jManager,
    close_neo4j,
    get_neo4j_client,
    initialize_neo4j,
    is_neo4j_initialized,
)

__all__ = [
    "Neo4jClient",
    "Neo4jManager",
    "get_neo4j_client",
    "initialize_neo4j",
    "close_neo4j",
    "is_neo4j_initialized",
]
