"""
Dependency analysis for risk assessment.
"""

from topdeck.storage.neo4j_client import Neo4jClient


class DependencyAnalyzer:
    """
    Analyzes resource dependencies for risk assessment.
    """

    def __init__(self, neo4j_client: Neo4jClient):
        """
        Initialize dependency analyzer.

        Args:
            neo4j_client: Neo4j client for graph queries
        """
        self.neo4j_client = neo4j_client

    def get_dependency_counts(self, resource_id: str) -> tuple[int, int]:
        """
        Get count of upstream and downstream dependencies.

        Searches ALL relationship types (not just DEPENDS_ON) to find
        genuine dependencies in the infrastructure graph.

        Args:
            resource_id: Resource to analyze

        Returns:
            Tuple of (dependencies_count, dependents_count)
        """
        with self.neo4j_client.session() as session:
            # Count upstream dependencies (what this depends on)
            # Include all outgoing relationships that indicate dependency
            upstream_query = """
            MATCH (r {id: $id})-[rel]->(dep)
            WHERE dep.id IS NOT NULL
            AND type(rel) IN [
                'DEPENDS_ON', 'USES', 'CONNECTS_TO', 'ROUTES_TO',
                'ACCESSES', 'AUTHENTICATES_WITH', 'READS_FROM', 'WRITES_TO'
            ]
            WITH DISTINCT dep
            RETURN COUNT(dep) as count
            """
            upstream_result = session.run(upstream_query, id=resource_id)
            upstream_record = upstream_result.single()
            dependencies_count = upstream_record["count"] if upstream_record else 0

            # Count downstream dependents (what depends on this)
            # Include all incoming relationships that indicate dependency
            downstream_query = """
            MATCH (r {id: $id})<-[rel]-(dependent)
            WHERE dependent.id IS NOT NULL
            AND type(rel) IN [
                'DEPENDS_ON', 'USES', 'CONNECTS_TO', 'ROUTES_TO',
                'ACCESSES', 'AUTHENTICATES_WITH', 'READS_FROM', 'WRITES_TO'
            ]
            WITH DISTINCT dependent
            RETURN COUNT(dependent) as count
            """
            downstream_result = session.run(downstream_query, id=resource_id)
            downstream_record = downstream_result.single()
            dependents_count = downstream_record["count"] if downstream_record else 0

        return dependencies_count, dependents_count

    def get_all_dependency_types(self, resource_id: str) -> dict[str, list[dict]]:
        """
        Get detailed breakdown of all dependency types.

        This provides in-depth analysis of what depends on this resource
        and how (via which relationship type).

        Args:
            resource_id: Resource to analyze

        Returns:
            Dictionary mapping relationship type to list of dependencies
        """
        query = """
        MATCH (r {id: $id})<-[rel]-(dependent)
        WHERE dependent.id IS NOT NULL
        RETURN type(rel) as relationship_type,
               dependent.id as dep_id,
               dependent.name as dep_name,
               COALESCE(dependent.resource_type, labels(dependent)[0]) as dep_type
        """

        dependencies_by_type: dict[str, list[dict]] = {}

        with self.neo4j_client.session() as session:
            result = session.run(query, id=resource_id)
            for record in result:
                rel_type = record["relationship_type"]
                if rel_type not in dependencies_by_type:
                    dependencies_by_type[rel_type] = []

                dependencies_by_type[rel_type].append(
                    {
                        "id": record["dep_id"],
                        "name": record["dep_name"],
                        "type": record["dep_type"],
                    }
                )

        return dependencies_by_type

    def find_critical_path(self, resource_id: str) -> list[str]:
        """
        Find the most critical dependency path from this resource.

        The critical path is the longest dependency chain, indicating
        the deepest cascading impact.

        Args:
            resource_id: Resource to analyze

        Returns:
            List of resource IDs in the critical path
        """
        query = """
        MATCH path = (r {id: $id})<-[*1..10]-(dependent)
        WHERE dependent.id IS NOT NULL
        WITH path, length(path) as depth
        ORDER BY depth DESC
        LIMIT 1
        RETURN [node IN nodes(path) | node.id] as path_ids
        """

        with self.neo4j_client.session() as session:
            result = session.run(query, id=resource_id)
            record = result.single()
            if record:
                return record["path_ids"]

        return [resource_id]

    def get_dependency_tree(
        self, resource_id: str, direction: str = "downstream", max_depth: int = 5
    ) -> dict[str, list[dict]]:
        """
        Get full dependency tree for a resource.

        Args:
            resource_id: Resource to analyze
            direction: "upstream" or "downstream"
            max_depth: Maximum depth to traverse

        Returns:
            Dictionary mapping resource IDs to their direct dependencies
        """
        if direction == "upstream":
            query = f"""
            MATCH path = (r {{id: $id}})-[*1..{max_depth}]->(dep)
            WHERE dep.id IS NOT NULL
            WITH path, relationships(path) as rels
            UNWIND rels as rel
            WITH startNode(rel) as source, endNode(rel) as target
            WHERE source.id IS NOT NULL AND target.id IS NOT NULL
            RETURN DISTINCT
                source.id as source_id,
                source.name as source_name,
                COALESCE(source.resource_type, labels(source)[0]) as source_type,
                target.id as target_id,
                target.name as target_name,
                COALESCE(target.resource_type, labels(target)[0]) as target_type
            """
        else:  # downstream
            query = f"""
            MATCH path = (r {{id: $id}})<-[*1..{max_depth}]-(dep)
            WHERE dep.id IS NOT NULL
            WITH path, relationships(path) as rels
            UNWIND rels as rel
            WITH startNode(rel) as source, endNode(rel) as target
            WHERE source.id IS NOT NULL AND target.id IS NOT NULL
            RETURN DISTINCT
                source.id as source_id,
                source.name as source_name,
                COALESCE(source.resource_type, labels(source)[0]) as source_type,
                target.id as target_id,
                target.name as target_name,
                COALESCE(target.resource_type, labels(target)[0]) as target_type
            """

        tree: dict[str, list[dict]] = {}

        with self.neo4j_client.session() as session:
            result = session.run(query, id=resource_id)
            for record in result:
                source_id = record["source_id"]
                if source_id not in tree:
                    tree[source_id] = []

                tree[source_id].append(
                    {
                        "id": record["target_id"],
                        "name": record["target_name"],
                        "type": record["target_type"],
                    }
                )

        return tree

    def is_single_point_of_failure(self, resource_id: str) -> bool:
        """
        Check if a resource is a single point of failure.

        A resource is a SPOF if:
        1. It has dependents (other resources depend on it)
        2. It has no redundant alternatives

        Args:
            resource_id: Resource to check

        Returns:
            True if this is a SPOF
        """
        query = """
        MATCH (r {id: $id})

        // Check if it has dependents
        OPTIONAL MATCH (r)<-[:DEPENDS_ON]-(dependent)
        WHERE dependent.id IS NOT NULL
        WITH r, COUNT(dependent) as dependent_count

        // Check if it has redundant alternatives
        OPTIONAL MATCH (r)-[:REDUNDANT_WITH]->(alt)
        WHERE alt.id IS NOT NULL
        WITH r, dependent_count, COUNT(alt) as redundant_count

        RETURN dependent_count > 0 AND redundant_count = 0 as is_spof
        """

        with self.neo4j_client.session() as session:
            result = session.run(query, id=resource_id)
            record = result.single()
            if record:
                return bool(record["is_spof"])

        return False

    def get_affected_resources(
        self, resource_id: str, max_depth: int = 10
    ) -> tuple[list[dict], list[dict]]:
        """
        Get all resources that would be affected if this resource fails.

        Args:
            resource_id: Resource to analyze
            max_depth: Maximum cascade depth

        Returns:
            Tuple of (directly_affected, indirectly_affected) resource lists
        """
        # Get directly affected (immediate dependents)
        direct_query = """
        MATCH (r {id: $id})<-[:DEPENDS_ON]-(dependent)
        WHERE dependent.id IS NOT NULL
        RETURN DISTINCT
            dependent.id as id,
            dependent.name as name,
            COALESCE(dependent.resource_type, labels(dependent)[0]) as type,
            dependent.cloud_provider as cloud_provider
        """

        directly_affected = []
        with self.neo4j_client.session() as session:
            result = session.run(direct_query, id=resource_id)
            for record in result:
                directly_affected.append(
                    {
                        "id": record["id"],
                        "name": record["name"],
                        "type": record["type"],
                        "cloud_provider": record["cloud_provider"],
                    }
                )

        # Get indirectly affected (cascade effects)
        indirect_query = f"""
        MATCH path = (r {{id: $id}})<-[:DEPENDS_ON*2..{max_depth}]-(dependent)
        WHERE dependent.id IS NOT NULL
        RETURN DISTINCT
            dependent.id as id,
            dependent.name as name,
            COALESCE(dependent.resource_type, labels(dependent)[0]) as type,
            dependent.cloud_provider as cloud_provider,
            length(path) as distance
        ORDER BY distance
        """

        indirectly_affected = []
        direct_ids = {r["id"] for r in directly_affected}

        with self.neo4j_client.session() as session:
            result = session.run(indirect_query, id=resource_id)
            for record in result:
                # Don't include resources already in direct list
                if record["id"] not in direct_ids:
                    indirectly_affected.append(
                        {
                            "id": record["id"],
                            "name": record["name"],
                            "type": record["type"],
                            "cloud_provider": record["cloud_provider"],
                            "distance": record["distance"],
                        }
                    )

        return directly_affected, indirectly_affected
