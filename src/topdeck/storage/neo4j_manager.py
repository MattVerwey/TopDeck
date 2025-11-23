"""
Neo4j Connection Manager with Singleton Pattern.

Provides a single shared Neo4j driver instance across the application
for optimal connection pooling and resource management.
"""

from typing import Any

from topdeck.storage.neo4j_client import Neo4jClient


class Neo4jManager:
    """
    Singleton manager for Neo4j connections.
    
    Ensures a single shared driver instance is used across the application
    for optimal connection pooling.
    """

    _instance: "Neo4jManager | None" = None
    _client: Neo4jClient | None = None

    def __new__(cls) -> "Neo4jManager":
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(
        self,
        uri: str,
        username: str,
        password: str,
        encrypted: bool = False,
        max_connection_pool_size: int = 50,
        connection_acquisition_timeout: float = 60.0,
        auto_create_schema: bool = True,
    ) -> None:
        """
        Initialize the Neo4j client with connection pooling.

        Args:
            uri: Neo4j connection URI
            username: Neo4j username
            password: Neo4j password
            encrypted: Whether to use encrypted connection
            max_connection_pool_size: Maximum connections in pool
            connection_acquisition_timeout: Timeout for acquiring connection
            auto_create_schema: Whether to automatically create schema on initialization
        """
        if self._client is None:
            self._client = Neo4jClient(
                uri=uri,
                username=username,
                password=password,
                encrypted=encrypted,
                max_connection_pool_size=max_connection_pool_size,
                connection_acquisition_timeout=connection_acquisition_timeout,
            )
            self._client.connect()

            # Automatically create schema if requested
            if auto_create_schema:
                schema_result = self._client.initialize_schema()
                print(
                    f"Neo4j schema initialized: "
                    f"{schema_result['constraints_created']} constraints, "
                    f"{schema_result['indexes_created']} indexes"
                )
                if schema_result["errors"]:
                    print(f"Schema initialization warnings: {schema_result['errors']}")

    def get_client(self) -> Neo4jClient:
        """
        Get the shared Neo4j client instance.

        Returns:
            Shared Neo4jClient instance

        Raises:
            RuntimeError: If client hasn't been initialized
        """
        if self._client is None:
            raise RuntimeError(
                "Neo4jManager not initialized. Call initialize() first."
            )
        return self._client

    def close(self) -> None:
        """Close the Neo4j connection."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def is_initialized(self) -> bool:
        """Check if the manager has been initialized."""
        return self._client is not None


# Global instance
_neo4j_manager = Neo4jManager()


def get_neo4j_client() -> Neo4jClient:
    """
    Get the shared Neo4j client instance.
    
    This is the recommended way to get a Neo4j client in the application.
    
    Returns:
        Shared Neo4jClient instance
        
    Raises:
        RuntimeError: If manager hasn't been initialized
    """
    return _neo4j_manager.get_client()


def initialize_neo4j(
    uri: str,
    username: str,
    password: str,
    encrypted: bool = False,
    max_connection_pool_size: int = 50,
    connection_acquisition_timeout: float = 60.0,
    auto_create_schema: bool = True,
) -> None:
    """
    Initialize the global Neo4j connection manager.
    
    Should be called once at application startup.

    Args:
        uri: Neo4j connection URI
        username: Neo4j username
        password: Neo4j password
        encrypted: Whether to use encrypted connection
        max_connection_pool_size: Maximum connections in pool
        connection_acquisition_timeout: Timeout for acquiring connection
        auto_create_schema: Whether to automatically create schema
    """
    _neo4j_manager.initialize(
        uri=uri,
        username=username,
        password=password,
        encrypted=encrypted,
        max_connection_pool_size=max_connection_pool_size,
        connection_acquisition_timeout=connection_acquisition_timeout,
        auto_create_schema=auto_create_schema,
    )


def close_neo4j() -> None:
    """Close the global Neo4j connection."""
    _neo4j_manager.close()


def is_neo4j_initialized() -> bool:
    """Check if Neo4j has been initialized."""
    return _neo4j_manager.is_initialized()
