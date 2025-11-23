"""
Neo4j Client for TopDeck.

Handles connection and operations with Neo4j graph database.
Supports encrypted connections using bolt+s:// or neo4j+s:// schemes.
Implements connection pooling for improved performance.
"""

from contextlib import contextmanager
from typing import Any

from neo4j import Driver, GraphDatabase, Session


class Neo4jClient:
    """
    Client for interacting with Neo4j database.

    Supports both encrypted and unencrypted connections:
    - bolt://     - Unencrypted (development only)
    - bolt+s://   - Encrypted with TLS
    - neo4j://    - Unencrypted routing
    - neo4j+s://  - Encrypted routing with TLS
    
    Uses connection pooling for improved performance.
    """

    def __init__(
        self,
        uri: str,
        username: str,
        password: str,
        encrypted: bool = False,
        max_connection_pool_size: int = 50,
        connection_acquisition_timeout: float = 60.0,
        enable_query_cache: bool = True,
    ):
        """
        Initialize Neo4j client.

        Args:
            uri: Neo4j connection URI (e.g., "bolt://localhost:7687" or "bolt+s://localhost:7687")
            username: Neo4j username
            password: Neo4j password
            encrypted: If True and URI doesn't specify encryption, upgrades to encrypted connection
            max_connection_pool_size: Maximum number of connections in the pool (default: 50)
            connection_acquisition_timeout: Timeout in seconds for acquiring a connection (default: 60.0)
            enable_query_cache: Whether to enable query result caching (default: True)
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.encrypted = encrypted
        self.max_connection_pool_size = max_connection_pool_size
        self.connection_acquisition_timeout = connection_acquisition_timeout
        self.enable_query_cache = enable_query_cache
        self.driver: Driver | None = None
        self._query_cache = None

        # Auto-upgrade to encrypted connection if requested and not already encrypted
        if encrypted and not ("+s://" in uri or "+ssc://" in uri):
            if uri.startswith("bolt://"):
                self.uri = "bolt+s://" + uri[len("bolt://") :]
            elif uri.startswith("neo4j://"):
                self.uri = "neo4j+s://" + uri[len("neo4j://") :]
            else:
                self.uri = uri

        # Initialize query cache if enabled
        if enable_query_cache:
            from topdeck.storage.query_cache import get_query_cache
            self._query_cache = get_query_cache()

    def _is_encrypted_uri(self, uri: str) -> bool:
        """Check if a URI uses an encrypted protocol."""
        return "+s://" in uri or "+ssc://" in uri

    def connect(self) -> None:
        """Establish connection to Neo4j with optional TLS encryption and connection pooling."""
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password),
            encrypted=self.encrypted or self._is_encrypted_uri(self.uri),
            max_connection_pool_size=self.max_connection_pool_size,
            connection_acquisition_timeout=self.connection_acquisition_timeout,
        )

    def close(self) -> None:
        """Close connection to Neo4j"""
        if self.driver:
            self.driver.close()
            self.driver = None

    @contextmanager
    def session(self) -> Session:
        """
        Context manager for Neo4j sessions.

        Usage:
            with client.session() as session:
                session.run("MATCH (n) RETURN n")
        """
        if not self.driver:
            self.connect()

        session = self.driver.session()
        try:
            yield session
        finally:
            session.close()

    def create_resource(self, properties: dict[str, Any]) -> str:
        """
        Create a resource node in Neo4j.

        Args:
            properties: Resource properties

        Returns:
            Node element ID
        """
        with self.session() as session:
            result = session.run(
                """
                CREATE (r:Resource)
                SET r = $properties
                RETURN elementId(r) as node_id
            """,
                properties=properties,
            )

            record = result.single()
            return record["node_id"] if record else None

    def create_dependency(
        self,
        source_id: str,
        target_id: str,
        properties: dict[str, Any],
    ) -> bool:
        """
        Create a DEPENDS_ON relationship between resources.

        Args:
            source_id: Source resource ID
            target_id: Target resource ID
            properties: Relationship properties

        Returns:
            True if successful, False otherwise
        """
        with self.session() as session:
            result = session.run(
                """
                MATCH (source:Resource {id: $source_id})
                MATCH (target:Resource {id: $target_id})
                CREATE (source)-[r:DEPENDS_ON]->(target)
                SET r = $properties
                RETURN r
            """,
                source_id=source_id,
                target_id=target_id,
                properties=properties,
            )

            return result.single() is not None

    def upsert_resource(self, properties: dict[str, Any]) -> str:
        """
        Create or update a resource node.

        Args:
            properties: Resource properties (must include 'id')

        Returns:
            Node element ID
        """
        if "id" not in properties:
            raise ValueError("Resource properties must include 'id'")

        with self.session() as session:
            result = session.run(
                """
                MERGE (r:Resource {id: $id})
                SET r += $properties
                RETURN elementId(r) as node_id
            """,
                id=properties["id"],
                properties=properties,
            )

            record = result.single()
            return record["node_id"] if record else None

    def get_resource_by_id(self, resource_id: str) -> dict[str, Any] | None:
        """
        Get a resource by ID.

        Args:
            resource_id: Resource ID

        Returns:
            Resource properties or None if not found
        """
        with self.session() as session:
            result = session.run(
                """
                MATCH (r:Resource {id: $id})
                RETURN r
            """,
                id=resource_id,
            )

            record = result.single()
            if record:
                return dict(record["r"])
            return None

    def get_resources_by_type(
        self,
        resource_type: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get resources by type.

        Args:
            resource_type: Resource type
            limit: Maximum number of results

        Returns:
            List of resource properties
        """
        with self.session() as session:
            result = session.run(
                """
                MATCH (r:Resource {resource_type: $resource_type})
                RETURN r
                LIMIT $limit
            """,
                resource_type=resource_type,
                limit=limit,
            )

            return [dict(record["r"]) for record in result]

    def get_dependencies(self, resource_id: str) -> list[dict[str, Any]]:
        """
        Get all dependencies for a resource.

        Args:
            resource_id: Resource ID

        Returns:
            List of dependency relationships with target resources
        """
        with self.session() as session:
            result = session.run(
                """
                MATCH (source:Resource {id: $id})-[dep:DEPENDS_ON]->(target:Resource)
                RETURN target, dep
            """,
                id=resource_id,
            )

            return [
                {
                    "target": dict(record["target"]),
                    "relationship": dict(record["dep"]),
                }
                for record in result
            ]

    def create_application(self, properties: dict[str, Any]) -> str:
        """
        Create an application node in Neo4j.

        Args:
            properties: Application properties

        Returns:
            Node element ID
        """
        with self.session() as session:
            result = session.run(
                """
                CREATE (a:Application)
                SET a = $properties
                RETURN elementId(a) as node_id
            """,
                properties=properties,
            )

            record = result.single()
            return record["node_id"] if record else None

    def upsert_application(self, properties: dict[str, Any]) -> str:
        """
        Create or update an application node.

        Args:
            properties: Application properties (must include 'id')

        Returns:
            Node element ID
        """
        if "id" not in properties:
            raise ValueError("Application properties must include 'id'")

        with self.session() as session:
            result = session.run(
                """
                MERGE (a:Application {id: $id})
                SET a += $properties
                RETURN elementId(a) as node_id
            """,
                id=properties["id"],
                properties=properties,
            )

            record = result.single()
            return record["node_id"] if record else None

    def create_repository(self, properties: dict[str, Any]) -> str:
        """
        Create a repository node in Neo4j.

        Args:
            properties: Repository properties

        Returns:
            Node element ID
        """
        with self.session() as session:
            result = session.run(
                """
                CREATE (r:Repository)
                SET r = $properties
                RETURN elementId(r) as node_id
            """,
                properties=properties,
            )

            record = result.single()
            return record["node_id"] if record else None

    def upsert_repository(self, properties: dict[str, Any]) -> str:
        """
        Create or update a repository node.

        Args:
            properties: Repository properties (must include 'id')

        Returns:
            Node element ID
        """
        if "id" not in properties:
            raise ValueError("Repository properties must include 'id'")

        with self.session() as session:
            result = session.run(
                """
                MERGE (r:Repository {id: $id})
                SET r += $properties
                RETURN elementId(r) as node_id
            """,
                id=properties["id"],
                properties=properties,
            )

            record = result.single()
            return record["node_id"] if record else None

    def create_deployment(self, properties: dict[str, Any]) -> str:
        """
        Create a deployment node in Neo4j.

        Args:
            properties: Deployment properties

        Returns:
            Node element ID
        """
        with self.session() as session:
            result = session.run(
                """
                CREATE (d:Deployment)
                SET d = $properties
                RETURN elementId(d) as node_id
            """,
                properties=properties,
            )

            record = result.single()
            return record["node_id"] if record else None

    def upsert_deployment(self, properties: dict[str, Any]) -> str:
        """
        Create or update a deployment node.

        Args:
            properties: Deployment properties (must include 'id')

        Returns:
            Node element ID
        """
        if "id" not in properties:
            raise ValueError("Deployment properties must include 'id'")

        with self.session() as session:
            result = session.run(
                """
                MERGE (d:Deployment {id: $id})
                SET d += $properties
                RETURN elementId(d) as node_id
            """,
                id=properties["id"],
                properties=properties,
            )

            record = result.single()
            return record["node_id"] if record else None

    def create_relationship(
        self,
        source_id: str,
        source_label: str,
        target_id: str,
        target_label: str,
        relationship_type: str,
        properties: dict[str, Any],
    ) -> bool:
        """
        Create a relationship between any two nodes.

        Args:
            source_id: Source node ID
            source_label: Source node label (e.g., "Application", "Resource")
            target_id: Target node ID
            target_label: Target node label
            relationship_type: Type of relationship (e.g., "BUILT_FROM", "DEPLOYED_TO")
            properties: Relationship properties

        Returns:
            True if successful, False otherwise
        """
        with self.session() as session:
            # Build dynamic query with labels
            query = f"""
                MATCH (source:{source_label} {{id: $source_id}})
                MATCH (target:{target_label} {{id: $target_id}})
                CREATE (source)-[r:{relationship_type}]->(target)
                SET r = $properties
                RETURN r
            """
            result = session.run(
                query, source_id=source_id, target_id=target_id, properties=properties
            )

            return result.single() is not None

    def create_namespace(self, properties: dict[str, Any]) -> str:
        """
        Create a Kubernetes namespace node in Neo4j.

        Args:
            properties: Namespace properties

        Returns:
            Node element ID
        """
        with self.session() as session:
            result = session.run(
                """
                CREATE (n:Namespace)
                SET n = $properties
                RETURN elementId(n) as node_id
            """,
                properties=properties,
            )

            record = result.single()
            return record["node_id"] if record else None

    def upsert_namespace(self, properties: dict[str, Any]) -> str:
        """
        Create or update a namespace node.

        Args:
            properties: Namespace properties (must include 'id')

        Returns:
            Node element ID
        """
        with self.session() as session:
            result = session.run(
                """
                MERGE (n:Namespace {id: $id})
                SET n = $properties
                RETURN elementId(n) as node_id
            """,
                id=properties["id"],
                properties=properties,
            )

            record = result.single()
            return record["node_id"] if record else None

    def create_pod(self, properties: dict[str, Any]) -> str:
        """
        Create a Kubernetes pod node in Neo4j.

        Args:
            properties: Pod properties

        Returns:
            Node element ID
        """
        with self.session() as session:
            result = session.run(
                """
                CREATE (p:Pod)
                SET p = $properties
                RETURN elementId(p) as node_id
            """,
                properties=properties,
            )

            record = result.single()
            return record["node_id"] if record else None

    def upsert_pod(self, properties: dict[str, Any]) -> str:
        """
        Create or update a pod node.

        Args:
            properties: Pod properties (must include 'id')

        Returns:
            Node element ID
        """
        with self.session() as session:
            result = session.run(
                """
                MERGE (p:Pod {id: $id})
                SET p = $properties
                RETURN elementId(p) as node_id
            """,
                id=properties["id"],
                properties=properties,
            )

            record = result.single()
            return record["node_id"] if record else None

    def create_managed_identity(self, properties: dict[str, Any]) -> str:
        """
        Create a managed identity node in Neo4j.

        Args:
            properties: ManagedIdentity properties

        Returns:
            Node element ID
        """
        with self.session() as session:
            result = session.run(
                """
                CREATE (mi:ManagedIdentity)
                SET mi = $properties
                RETURN elementId(mi) as node_id
            """,
                properties=properties,
            )

            record = result.single()
            return record["node_id"] if record else None

    def upsert_managed_identity(self, properties: dict[str, Any]) -> str:
        """
        Create or update a managed identity node.

        Args:
            properties: ManagedIdentity properties (must include 'id')

        Returns:
            Node element ID
        """
        with self.session() as session:
            result = session.run(
                """
                MERGE (mi:ManagedIdentity {id: $id})
                SET mi = $properties
                RETURN elementId(mi) as node_id
            """,
                id=properties["id"],
                properties=properties,
            )

            record = result.single()
            return record["node_id"] if record else None

    def create_service_principal(self, properties: dict[str, Any]) -> str:
        """
        Create a service principal node in Neo4j.

        Args:
            properties: ServicePrincipal properties

        Returns:
            Node element ID
        """
        with self.session() as session:
            result = session.run(
                """
                CREATE (sp:ServicePrincipal)
                SET sp = $properties
                RETURN elementId(sp) as node_id
            """,
                properties=properties,
            )

            record = result.single()
            return record["node_id"] if record else None

    def upsert_service_principal(self, properties: dict[str, Any]) -> str:
        """
        Create or update a service principal node.

        Args:
            properties: ServicePrincipal properties (must include 'id')

        Returns:
            Node element ID
        """
        with self.session() as session:
            result = session.run(
                """
                MERGE (sp:ServicePrincipal {id: $id})
                SET sp = $properties
                RETURN elementId(sp) as node_id
            """,
                id=properties["id"],
                properties=properties,
            )

            record = result.single()
            return record["node_id"] if record else None

    def create_app_registration(self, properties: dict[str, Any]) -> str:
        """
        Create an app registration node in Neo4j.

        Args:
            properties: AppRegistration properties

        Returns:
            Node element ID
        """
        with self.session() as session:
            result = session.run(
                """
                CREATE (ar:AppRegistration)
                SET ar = $properties
                RETURN elementId(ar) as node_id
            """,
                properties=properties,
            )

            record = result.single()
            return record["node_id"] if record else None

    def upsert_app_registration(self, properties: dict[str, Any]) -> str:
        """
        Create or update an app registration node.

        Args:
            properties: AppRegistration properties (must include 'id')

        Returns:
            Node element ID
        """
        with self.session() as session:
            result = session.run(
                """
                MERGE (ar:AppRegistration {id: $id})
                SET ar = $properties
                RETURN elementId(ar) as node_id
            """,
                id=properties["id"],
                properties=properties,
            )

            record = result.single()
            return record["node_id"] if record else None

    def clear_all(self) -> int:
        """
        Delete all nodes and relationships (use with caution!).

        Returns:
            Number of nodes deleted
        """
        with self.session() as session:
            result = session.run(
                """
                MATCH (n)
                DETACH DELETE n
                RETURN count(n) as count
            """
            )

            record = result.single()
            return record["count"] if record else 0

    def batch_create_resources(self, resources: list[dict[str, Any]]) -> int:
        """
        Create multiple resource nodes in a single transaction using UNWIND.
        
        This is much more efficient than creating resources one at a time.
        
        Note: This method uses CREATE (not MERGE) and requires pre-defined IDs.
        It will fail if resources with these IDs already exist. Use this when you
        know the resources are new. For updates or when existence is uncertain,
        use batch_upsert_resources() instead.

        Args:
            resources: List of resource property dictionaries (each must include 'id')

        Returns:
            Number of resources created
        """
        if not resources:
            return 0

        # Validate all resources have an ID
        for idx, resource in enumerate(resources):
            if "id" not in resource:
                raise ValueError(f"Resource at index {idx} is missing required 'id' field")

        with self.session() as session:
            result = session.run(
                """
                UNWIND $resources as resource
                CREATE (r:Resource)
                SET r = resource
                RETURN count(r) as count
                """,
                resources=resources,
            )

            record = result.single()
            return record["count"] if record else 0

    def batch_upsert_resources(self, resources: list[dict[str, Any]]) -> int:
        """
        Create or update multiple resource nodes in a single transaction using UNWIND.
        
        This is much more efficient than upserting resources one at a time.

        Args:
            resources: List of resource property dictionaries (each must include 'id')

        Returns:
            Number of resources upserted
        """
        if not resources:
            return 0

        # Validate all resources have an ID
        for idx, resource in enumerate(resources):
            if "id" not in resource:
                raise ValueError(f"Resource at index {idx} is missing required 'id' field")

        with self.session() as session:
            result = session.run(
                """
                UNWIND $resources as resource
                MERGE (r:Resource {id: resource.id})
                SET r += resource
                RETURN count(r) as count
                """,
                resources=resources,
            )

            record = result.single()
            return record["count"] if record else 0

    def batch_create_dependencies(
        self, dependencies: list[dict[str, Any]]
    ) -> int:
        """
        Create multiple DEPENDS_ON relationships in a single transaction using UNWIND.
        
        This is much more efficient than creating dependencies one at a time.
        
        Note: Uses MERGE to ensure both source and target resources exist. If either
        resource doesn't exist, it will be created with just the ID property.

        Args:
            dependencies: List of dependency dictionaries, each with:
                - source_id: Source resource ID
                - target_id: Target resource ID
                - properties: Relationship properties (optional)

        Returns:
            Number of dependencies created
        """
        if not dependencies:
            return 0

        # Validate all dependencies have required fields
        for idx, dep in enumerate(dependencies):
            if "source_id" not in dep or "target_id" not in dep:
                missing = []
                if "source_id" not in dep:
                    missing.append("source_id")
                if "target_id" not in dep:
                    missing.append("target_id")
                raise ValueError(
                    f"Dependency at index {idx} is missing required fields: {', '.join(missing)}"
                )

        with self.session() as session:
            result = session.run(
                """
                UNWIND $dependencies as dep
                MERGE (source:Resource {id: dep.source_id})
                MERGE (target:Resource {id: dep.target_id})
                CREATE (source)-[r:DEPENDS_ON]->(target)
                SET r = COALESCE(dep.properties, {})
                RETURN count(r) as count
                """,
                dependencies=dependencies,
            )

            record = result.single()
            return record["count"] if record else 0

    def initialize_schema(self) -> dict[str, Any]:
        """
        Initialize database schema by creating indexes and constraints.
        
        This should be called on application startup to ensure optimal query performance.
        Uses IF NOT EXISTS to avoid errors on subsequent calls.

        Returns:
            Dictionary with counts of constraints and indexes created
        """
        constraints_created = 0
        indexes_created = 0
        errors = []

        with self.session() as session:
            # Create uniqueness constraints
            constraint_queries = [
                "CREATE CONSTRAINT resource_id_unique IF NOT EXISTS FOR (r:Resource) REQUIRE r.id IS UNIQUE",
                "CREATE CONSTRAINT application_id_unique IF NOT EXISTS FOR (a:Application) REQUIRE a.id IS UNIQUE",
                "CREATE CONSTRAINT repository_id_unique IF NOT EXISTS FOR (r:Repository) REQUIRE r.id IS UNIQUE",
                "CREATE CONSTRAINT deployment_id_unique IF NOT EXISTS FOR (d:Deployment) REQUIRE d.id IS UNIQUE",
                "CREATE CONSTRAINT namespace_id_unique IF NOT EXISTS FOR (n:Namespace) REQUIRE n.id IS UNIQUE",
                "CREATE CONSTRAINT pod_id_unique IF NOT EXISTS FOR (p:Pod) REQUIRE p.id IS UNIQUE",
                "CREATE CONSTRAINT managed_identity_id_unique IF NOT EXISTS FOR (mi:ManagedIdentity) REQUIRE mi.id IS UNIQUE",
                "CREATE CONSTRAINT service_principal_id_unique IF NOT EXISTS FOR (sp:ServicePrincipal) REQUIRE sp.id IS UNIQUE",
                "CREATE CONSTRAINT app_registration_id_unique IF NOT EXISTS FOR (ar:AppRegistration) REQUIRE ar.id IS UNIQUE",
            ]

            for query in constraint_queries:
                try:
                    session.run(query)
                    constraints_created += 1
                except Exception as e:
                    # Constraint might already exist or be an enterprise feature
                    if "already exists" not in str(e).lower():
                        errors.append(f"Constraint error: {str(e)}")

            # Create indexes for common query patterns
            index_queries = [
                # Resource indexes
                "CREATE INDEX resource_id IF NOT EXISTS FOR (r:Resource) ON (r.id)",
                "CREATE INDEX resource_type IF NOT EXISTS FOR (r:Resource) ON (r.resource_type)",
                "CREATE INDEX resource_cloud_provider IF NOT EXISTS FOR (r:Resource) ON (r.cloud_provider)",
                "CREATE INDEX resource_name IF NOT EXISTS FOR (r:Resource) ON (r.name)",
                "CREATE INDEX resource_region IF NOT EXISTS FOR (r:Resource) ON (r.region)",
                "CREATE INDEX resource_status IF NOT EXISTS FOR (r:Resource) ON (r.status)",
                "CREATE INDEX resource_environment IF NOT EXISTS FOR (r:Resource) ON (r.environment)",
                # Composite indexes for common query patterns
                "CREATE INDEX resource_type_provider IF NOT EXISTS FOR (r:Resource) ON (r.resource_type, r.cloud_provider)",
                "CREATE INDEX resource_region_type IF NOT EXISTS FOR (r:Resource) ON (r.region, r.resource_type)",
                # Application indexes
                "CREATE INDEX application_id IF NOT EXISTS FOR (a:Application) ON (a.id)",
                "CREATE INDEX application_name IF NOT EXISTS FOR (a:Application) ON (a.name)",
                # Deployment indexes
                "CREATE INDEX deployment_id IF NOT EXISTS FOR (d:Deployment) ON (d.id)",
                "CREATE INDEX deployment_status IF NOT EXISTS FOR (d:Deployment) ON (d.status)",
                # Namespace indexes
                "CREATE INDEX namespace_id IF NOT EXISTS FOR (n:Namespace) ON (n.id)",
                "CREATE INDEX namespace_name IF NOT EXISTS FOR (n:Namespace) ON (n.name)",
                # Pod indexes
                "CREATE INDEX pod_id IF NOT EXISTS FOR (p:Pod) ON (p.id)",
                "CREATE INDEX pod_name IF NOT EXISTS FOR (p:Pod) ON (p.name)",
            ]

            for query in index_queries:
                try:
                    session.run(query)
                    indexes_created += 1
                except Exception as e:
                    # Index might already exist
                    if "already exists" not in str(e).lower():
                        errors.append(f"Index error: {str(e)}")

        return {
            "constraints_created": constraints_created,
            "indexes_created": indexes_created,
            "errors": errors,
        }

    def run_cached_query(
        self, query: str, params: dict[str, Any] | None = None, ttl: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Run a query with caching enabled.
        
        Results are cached based on query + parameters. Use for read-only queries
        that are frequently executed with the same parameters.
        
        WARNING: Do not use for queries that modify data (CREATE, MERGE, DELETE, SET).

        Args:
            query: Cypher query string
            params: Query parameters
            ttl: Cache TTL in seconds (uses cache default if None)

        Returns:
            List of result records as dictionaries
        """
        if not self.enable_query_cache or self._query_cache is None:
            # Cache disabled, execute directly
            with self.session() as session:
                result = session.run(query, params or {})
                return [dict(record) for record in result]

        # Check cache first
        cached_result = self._query_cache.get(query, params)
        if cached_result is not None:
            return cached_result

        # Execute query and cache result
        with self.session() as session:
            result = session.run(query, params or {})
            result_list = [dict(record) for record in result]
            self._query_cache.set(query, result_list, params, ttl)
            return result_list

    def invalidate_cache(self, query: str | None = None, params: dict[str, Any] | None = None) -> None:
        """
        Invalidate cached query results.

        Args:
            query: Specific query to invalidate (None = clear all)
            params: Query parameters (only used if query is specified)
        """
        if self._query_cache is None:
            return

        if query is None:
            self._query_cache.clear()
        else:
            self._query_cache.invalidate(query, params)

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get query cache statistics.

        Returns:
            Dictionary with cache stats or empty dict if caching disabled
        """
        if self._query_cache is None:
            return {
                "enabled": False,
                "message": "Query caching is disabled"
            }

        stats = self._query_cache.get_stats()
        stats["enabled"] = True
        return stats
