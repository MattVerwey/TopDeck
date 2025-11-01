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
            max_depth: Maximum depth to traverse (clamped to 1-10)

        Returns:
            Dictionary mapping resource IDs to their direct dependencies
        """
        # Clamp max_depth to reasonable bounds
        # Note: Neo4j variable-length relationships cannot use query parameters for bounds
        clamped_depth = max(1, min(max_depth, 10))
        
        if direction == "upstream":
            # Using hardcoded maximum to avoid f-string query construction
            query = """
            MATCH path = (r {id: $id})-[*1..10]->(dep)
            WHERE dep.id IS NOT NULL
            WITH path, relationships(path) as rels, length(path) as pathLength
            WHERE pathLength <= $max_depth
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
            # Using hardcoded maximum to avoid f-string query construction
            query = """
            MATCH path = (r {id: $id})<-[*1..10]-(dep)
            WHERE dep.id IS NOT NULL
            WITH path, relationships(path) as rels, length(path) as pathLength
            WHERE pathLength <= $max_depth
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
            result = session.run(query, id=resource_id, max_depth=clamped_depth)
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
            max_depth: Maximum cascade depth (clamped to 1-20)

        Returns:
            Tuple of (directly_affected, indirectly_affected) resource lists
        """
        # Clamp max_depth to reasonable bounds
        clamped_depth = max(2, min(max_depth, 20))
        
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
        # Using hardcoded maximum to avoid f-string query construction
        indirect_query = """
        MATCH path = (r {id: $id})<-[:DEPENDS_ON*2..20]-(dependent)
        WHERE dependent.id IS NOT NULL AND length(path) <= $max_depth
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
            result = session.run(indirect_query, id=resource_id, max_depth=clamped_depth)
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

    def detect_circular_dependencies(self, resource_id: str = None) -> list[list[str]]:
        """
        Detect circular dependencies in the infrastructure graph.

        Circular dependencies can cause cascading failures and make it difficult
        to reason about system behavior. This method finds all cycles involving
        the specified resource, or all cycles in the graph if no resource is specified.

        Args:
            resource_id: Optional resource to check for circular dependencies.
                        If None, detects all circular dependencies in the graph.

        Returns:
            List of circular dependency paths, where each path is a list of resource IDs
            forming a cycle (last element connects back to first)
        """
        if resource_id:
            # Find cycles involving a specific resource
            query = """
            MATCH path = (r {id: $id})-[*1..10]->(r)
            WHERE ALL(rel in relationships(path) WHERE type(rel) IN [
                'DEPENDS_ON', 'USES', 'CONNECTS_TO', 'ROUTES_TO',
                'ACCESSES', 'AUTHENTICATES_WITH', 'READS_FROM', 'WRITES_TO'
            ])
            WITH path, [node in nodes(path) | node.id] as cycle
            WHERE size(cycle) > 2
            RETURN DISTINCT cycle
            ORDER BY size(cycle)
            """
            params = {"id": resource_id}
        else:
            # Find all cycles in the graph
            query = """
            MATCH path = (r)-[*2..10]->(r)
            WHERE r.id IS NOT NULL
            AND ALL(rel in relationships(path) WHERE type(rel) IN [
                'DEPENDS_ON', 'USES', 'CONNECTS_TO', 'ROUTES_TO',
                'ACCESSES', 'AUTHENTICATES_WITH', 'READS_FROM', 'WRITES_TO'
            ])
            WITH path, [node in nodes(path) | node.id] as cycle
            WHERE size(cycle) > 2
            WITH cycle
            ORDER BY size(cycle), cycle[0]
            RETURN DISTINCT cycle
            LIMIT 50
            """
            params = {}

        cycles = []
        with self.neo4j_client.session() as session:
            result = session.run(query, **params)
            for record in result:
                cycle = record["cycle"]
                # Normalize cycle to start with smallest ID (for deduplication)
                min_idx = min(range(len(cycle)), key=lambda i: cycle[i])
                normalized = cycle[min_idx:] + cycle[:min_idx]
                
                # Only add if not already present (avoid duplicates)
                if normalized not in cycles:
                    cycles.append(normalized)

        return cycles

    def get_dependency_health_score(self, resource_id: str) -> dict:
        """
        Calculate a health score for a resource's dependencies.

        This score considers:
        - Number of dependencies (too many = tight coupling)
        - Circular dependencies (bad)
        - Single points of failure in dependency chain
        - Depth of dependency tree (deep = complex)

        Args:
            resource_id: Resource to analyze

        Returns:
            Dictionary with health score (0-100) and contributing factors
        """
        score = 100.0
        factors = {}

        # Factor 1: Dependency count (penalize high coupling)
        dependencies_count, dependents_count = self.get_dependency_counts(resource_id)
        if dependencies_count > 10:
            dependency_penalty = min(30, (dependencies_count - 10) * 3)
            score -= dependency_penalty
            factors["high_dependency_count"] = {
                "count": dependencies_count,
                "penalty": dependency_penalty,
                "reason": f"Resource depends on {dependencies_count} other resources (high coupling)"
            }

        # Factor 2: Circular dependencies (severe penalty)
        circular_deps = self.detect_circular_dependencies(resource_id)
        if circular_deps:
            circular_penalty = min(40, len(circular_deps) * 20)
            score -= circular_penalty
            factors["circular_dependencies"] = {
                "count": len(circular_deps),
                "penalty": circular_penalty,
                "cycles": circular_deps,
                "reason": f"Found {len(circular_deps)} circular dependency path(s)"
            }

        # Factor 3: Single points of failure in dependency chain
        dependency_tree = self.get_dependency_tree(resource_id, direction="upstream", max_depth=3)
        
        # Batch check all dependencies for SPOF status in single query
        dep_ids = list(dependency_tree.keys())
        spof_in_deps = []
        
        if dep_ids:
            # Query all at once to reduce database roundtrips
            spof_query = """
            UNWIND $dep_ids as dep_id
            MATCH (r {id: dep_id})
            OPTIONAL MATCH (r)<-[:DEPENDS_ON]-(dependent)
            WHERE dependent.id IS NOT NULL
            WITH r, dep_id, COUNT(dependent) as dependent_count
            OPTIONAL MATCH (r)-[:REDUNDANT_WITH]->(alt)
            WHERE alt.id IS NOT NULL
            WITH dep_id, dependent_count, COUNT(alt) as redundant_count
            WHERE dependent_count > 0 AND redundant_count = 0
            RETURN dep_id
            """
            
            with self.neo4j_client.session() as session:
                result = session.run(spof_query, dep_ids=dep_ids)
                spof_in_deps = [record["dep_id"] for record in result]
        
        if spof_in_deps:
            spof_penalty = min(20, len(spof_in_deps) * 5)
            score -= spof_penalty
            factors["spof_in_dependencies"] = {
                "count": len(spof_in_deps),
                "penalty": spof_penalty,
                "resources": spof_in_deps,
                "reason": f"Depends on {len(spof_in_deps)} single point(s) of failure"
            }

        # Factor 4: Dependency depth (penalize deep trees)
        max_depth = self._calculate_max_dependency_depth(resource_id)
        if max_depth > 5:
            depth_penalty = min(15, (max_depth - 5) * 3)
            score -= depth_penalty
            factors["deep_dependency_tree"] = {
                "max_depth": max_depth,
                "penalty": depth_penalty,
                "reason": f"Dependency tree is {max_depth} levels deep (complex)"
            }

        # Ensure score is in valid range
        score = max(0.0, min(100.0, score))

        return {
            "resource_id": resource_id,
            "health_score": round(score, 2),
            "health_level": self._get_health_level(score),
            "factors": factors,
            "recommendations": self._generate_health_recommendations(factors)
        }

    def _calculate_max_dependency_depth(self, resource_id: str, max_depth: int = 10) -> int:
        """Calculate maximum depth of dependency tree."""
        # Note: Neo4j variable-length relationships cannot use query parameters for bounds
        # Using hardcoded maximum to avoid f-string query construction
        # The max_depth parameter is kept for API compatibility but limited to 20
        query = """
        MATCH path = (r {id: $id})-[*1..20]->(dep)
        WHERE dep.id IS NOT NULL
        AND ALL(rel in relationships(path) WHERE type(rel) IN [
            'DEPENDS_ON', 'USES', 'CONNECTS_TO', 'ROUTES_TO'
        ])
        RETURN max(length(path)) as max_depth
        """
        
        with self.neo4j_client.session() as session:
            result = session.run(query, id=resource_id)
            record = result.single()
            calculated_depth = record["max_depth"] if record and record["max_depth"] else 0
            # Respect the requested max_depth by clamping the result
            requested_max = max(1, min(max_depth, 20))
            return min(calculated_depth, requested_max) if calculated_depth else 0

    def _get_health_level(self, score: float) -> str:
        """Convert health score to categorical level."""
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "fair"
        elif score >= 20:
            return "poor"
        else:
            return "critical"

    def _generate_health_recommendations(self, factors: dict) -> list[str]:
        """Generate recommendations based on health factors."""
        recommendations = []
        
        if "high_dependency_count" in factors:
            recommendations.append(
                "⚠️ Reduce coupling by consolidating dependencies or using facade pattern"
            )
            recommendations.append(
                "Consider implementing dependency injection to manage complexity"
            )
        
        if "circular_dependencies" in factors:
            recommendations.append(
                "🔴 CRITICAL: Break circular dependencies immediately - they can cause deadlocks"
            )
            recommendations.append(
                "Refactor to use event-driven architecture or introduce a mediator"
            )
        
        if "spof_in_dependencies" in factors:
            recommendations.append(
                "Add redundancy to critical dependencies that are single points of failure"
            )
            recommendations.append(
                "Implement circuit breakers and fallbacks for SPOF dependencies"
            )
        
        if "deep_dependency_tree" in factors:
            recommendations.append(
                "Simplify dependency tree by introducing abstraction layers"
            )
            recommendations.append(
                "Consider using service mesh for better dependency management"
            )
        
        if not recommendations:
            recommendations.append("✅ Dependency health is good - maintain current practices")
        
        return recommendations
