"""
Neo4j Client for TopDeck.

Handles connection and operations with Neo4j graph database.
Supports encrypted connections using bolt+s:// or neo4j+s:// schemes.
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
    """

    def __init__(self, uri: str, username: str, password: str, encrypted: bool = False):
        """
        Initialize Neo4j client.

        Args:
            uri: Neo4j connection URI (e.g., "bolt://localhost:7687" or "bolt+s://localhost:7687")
            username: Neo4j username
            password: Neo4j password
            encrypted: If True and URI doesn't specify encryption, upgrades to encrypted connection
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.encrypted = encrypted
        self.driver: Driver | None = None

        # Auto-upgrade to encrypted connection if requested and not already encrypted
        if encrypted and not ("+s://" in uri or "+ssc://" in uri):
            if uri.startswith("bolt://"):
                self.uri = "bolt+s://" + uri[len("bolt://") :]
            elif uri.startswith("neo4j://"):
                self.uri = "neo4j+s://" + uri[len("neo4j://") :]
            else:
                self.uri = uri

    def _is_encrypted_uri(self, uri: str) -> bool:
        """Check if a URI uses an encrypted protocol."""
        return "+s://" in uri or "+ssc://" in uri

    def connect(self) -> None:
        """Establish connection to Neo4j with optional TLS encryption."""
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password),
            encrypted=self.encrypted or self._is_encrypted_uri(self.uri),
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
