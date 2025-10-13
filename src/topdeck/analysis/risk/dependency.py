"""
Dependency analysis for risk assessment.
"""

from typing import Dict, List, Optional, Set, Tuple

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
    
    def get_dependency_counts(self, resource_id: str) -> Tuple[int, int]:
        """
        Get count of upstream and downstream dependencies.
        
        Args:
            resource_id: Resource to analyze
            
        Returns:
            Tuple of (dependencies_count, dependents_count)
        """
        with self.neo4j_client.session() as session:
            # Count upstream dependencies (what this depends on)
            upstream_query = """
            MATCH (r:Resource {id: $id})-[*1..5]->(dep:Resource)
            RETURN COUNT(DISTINCT dep) as count
            """
            upstream_result = session.run(upstream_query, id=resource_id)
            dependencies_count = upstream_result.single()["count"] if upstream_result.single() else 0
            
            # Count downstream dependents (what depends on this)
            downstream_query = """
            MATCH (r:Resource {id: $id})<-[*1..5]-(dependent:Resource)
            RETURN COUNT(DISTINCT dependent) as count
            """
            downstream_result = session.run(downstream_query, id=resource_id)
            dependents_count = downstream_result.single()["count"] if downstream_result.single() else 0
        
        return dependencies_count, dependents_count
    
    def find_critical_path(self, resource_id: str) -> List[str]:
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
        MATCH path = (r:Resource {id: $id})<-[*1..10]-(dependent:Resource)
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
        self,
        resource_id: str,
        direction: str = "downstream",
        max_depth: int = 5
    ) -> Dict[str, List[Dict]]:
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
            MATCH path = (r:Resource {{id: $id}})-[*1..{max_depth}]->(dep:Resource)
            WITH path, relationships(path) as rels
            UNWIND rels as rel
            WITH startNode(rel) as source, endNode(rel) as target
            RETURN DISTINCT 
                source.id as source_id,
                source.name as source_name,
                source.resource_type as source_type,
                target.id as target_id,
                target.name as target_name,
                target.resource_type as target_type
            """
        else:  # downstream
            query = f"""
            MATCH path = (r:Resource {{id: $id}})<-[*1..{max_depth}]-(dep:Resource)
            WITH path, relationships(path) as rels
            UNWIND rels as rel
            WITH startNode(rel) as source, endNode(rel) as target
            RETURN DISTINCT 
                source.id as source_id,
                source.name as source_name,
                source.resource_type as source_type,
                target.id as target_id,
                target.name as target_name,
                target.resource_type as target_type
            """
        
        tree: Dict[str, List[Dict]] = {}
        
        with self.neo4j_client.session() as session:
            result = session.run(query, id=resource_id)
            for record in result:
                source_id = record["source_id"]
                if source_id not in tree:
                    tree[source_id] = []
                
                tree[source_id].append({
                    "id": record["target_id"],
                    "name": record["target_name"],
                    "type": record["target_type"],
                })
        
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
        MATCH (r:Resource {id: $id})
        
        // Check if it has dependents
        OPTIONAL MATCH (r)<-[:DEPENDS_ON]-(dependent:Resource)
        WITH r, COUNT(dependent) as dependent_count
        
        // Check if it has redundant alternatives
        OPTIONAL MATCH (r)-[:REDUNDANT_WITH]->(alt:Resource)
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
        self,
        resource_id: str,
        max_depth: int = 10
    ) -> Tuple[List[Dict], List[Dict]]:
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
        MATCH (r:Resource {id: $id})<-[:DEPENDS_ON]-(dependent:Resource)
        RETURN DISTINCT
            dependent.id as id,
            dependent.name as name,
            dependent.resource_type as type,
            dependent.cloud_provider as cloud_provider
        """
        
        directly_affected = []
        with self.neo4j_client.session() as session:
            result = session.run(direct_query, id=resource_id)
            for record in result:
                directly_affected.append({
                    "id": record["id"],
                    "name": record["name"],
                    "type": record["type"],
                    "cloud_provider": record["cloud_provider"],
                })
        
        # Get indirectly affected (cascade effects)
        indirect_query = f"""
        MATCH path = (r:Resource {{id: $id}})<-[:DEPENDS_ON*2..{max_depth}]-(dependent:Resource)
        RETURN DISTINCT
            dependent.id as id,
            dependent.name as name,
            dependent.resource_type as type,
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
                    indirectly_affected.append({
                        "id": record["id"],
                        "name": record["name"],
                        "type": record["type"],
                        "cloud_provider": record["cloud_provider"],
                        "distance": record["distance"],
                    })
        
        return directly_affected, indirectly_affected
