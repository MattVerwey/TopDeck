"""
Topology analysis and aggregation service.

Builds network topology graphs from discovered resources and relationships,
supporting drill-down capabilities and data flow visualization.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from topdeck.storage.neo4j_client import Neo4jClient


class FlowType(str, Enum):
    """Types of data flows between resources."""
    
    HTTP = "http"
    HTTPS = "https"
    DATABASE = "database"
    MESSAGE_QUEUE = "message_queue"
    STORAGE = "storage"
    CACHE = "cache"
    INTERNAL = "internal"


@dataclass
class TopologyNode:
    """Represents a node in the topology graph."""
    
    id: str
    resource_type: str
    name: str
    cloud_provider: str
    region: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TopologyEdge:
    """Represents an edge (relationship) in the topology graph."""
    
    source_id: str
    target_id: str
    relationship_type: str
    flow_type: Optional[FlowType] = None
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TopologyGraph:
    """Complete topology graph with nodes and edges."""
    
    nodes: List[TopologyNode]
    edges: List[TopologyEdge]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataFlow:
    """Represents a data flow path through the system."""
    
    id: str
    name: str
    path: List[str]  # List of resource IDs in the flow
    flow_type: FlowType
    nodes: List[TopologyNode]
    edges: List[TopologyEdge]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceDependencies:
    """Dependencies for a specific resource."""
    
    resource_id: str
    resource_name: str
    upstream: List[TopologyNode]  # Resources this depends on
    downstream: List[TopologyNode]  # Resources that depend on this
    depth: int = 1


class TopologyService:
    """Service for building and analyzing network topology."""
    
    def __init__(self, neo4j_client: Neo4jClient):
        """
        Initialize topology service.
        
        Args:
            neo4j_client: Neo4j client for accessing graph data
        """
        self.neo4j_client = neo4j_client
    
    @staticmethod
    def _deserialize_json_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deserialize JSON strings in properties back to Python objects.
        
        Properties like 'tags' and 'properties' are stored as JSON strings in Neo4j
        for compatibility. This method deserializes them back to dicts/lists.
        
        Args:
            properties: Properties dict from Neo4j
            
        Returns:
            Properties dict with JSON strings deserialized
        """
        import json
        
        result = {}
        for key, value in properties.items():
            # Try to deserialize known JSON string fields
            if key in ('tags', 'properties') and isinstance(value, str):
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    # If it fails, keep as-is
                    result[key] = value
            # Handle other JSON string fields (lists like topics, approvers, etc.)
            elif key in ('topics', 'identifier_uris', 'redirect_uris', 'target_resources', 
                        'approvers', 'containers', 'init_containers', 'volumes', 
                        'conditions', 'labels', 'annotations', 'app_roles', 
                        'oauth2_permissions', 'required_resource_access') and isinstance(value, str):
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = value
            else:
                result[key] = value
        
        return result
    
    def get_topology(
        self,
        cloud_provider: Optional[str] = None,
        resource_type: Optional[str] = None,
        region: Optional[str] = None,
    ) -> TopologyGraph:
        """
        Get complete topology graph with optional filtering.
        
        Args:
            cloud_provider: Filter by cloud provider (azure, aws, gcp)
            resource_type: Filter by resource type
            region: Filter by region
            
        Returns:
            TopologyGraph with nodes and edges
        """
        # Build filter conditions
        filters = []
        params = {}
        
        if cloud_provider:
            filters.append("r.cloud_provider = $cloud_provider")
            params["cloud_provider"] = cloud_provider
        
        if resource_type:
            filters.append("r.resource_type = $resource_type")
            params["resource_type"] = resource_type
        
        if region:
            filters.append("r.region = $region")
            params["region"] = region
        
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        
        # Get all resources (nodes)
        nodes_query = f"""
        MATCH (r:Resource)
        {where_clause}
        RETURN r.id as id,
               r.resource_type as resource_type,
               r.name as name,
               r.cloud_provider as cloud_provider,
               r.region as region,
               r as properties
        """
        
        nodes = []
        with self.neo4j_client.session() as session:
            result = session.run(nodes_query, params)
            for record in result:
                # Deserialize properties (tags and properties are JSON strings)
                raw_props = dict(record["properties"]) if record["properties"] else {}
                deserialized_props = self._deserialize_json_properties(raw_props)
                
                nodes.append(TopologyNode(
                    id=record["id"],
                    resource_type=record["resource_type"],
                    name=record["name"],
                    cloud_provider=record["cloud_provider"],
                    region=record["region"],
                    properties=deserialized_props,
                ))
        
        # Get all relationships (edges)
        edges_query = f"""
        MATCH (source:Resource)-[rel]->(target:Resource)
        {where_clause.replace('r.', 'source.')}
        RETURN source.id as source_id,
               target.id as target_id,
               type(rel) as relationship_type,
               properties(rel) as properties
        """
        
        edges = []
        with self.neo4j_client.session() as session:
            result = session.run(edges_query, params)
            for record in result:
                flow_type = self._infer_flow_type(
                    record["relationship_type"],
                    record["properties"] or {}
                )
                edges.append(TopologyEdge(
                    source_id=record["source_id"],
                    target_id=record["target_id"],
                    relationship_type=record["relationship_type"],
                    flow_type=flow_type,
                    properties=dict(record["properties"]) if record["properties"] else {},
                ))
        
        return TopologyGraph(
            nodes=nodes,
            edges=edges,
            metadata={
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "filters": {
                    "cloud_provider": cloud_provider,
                    "resource_type": resource_type,
                    "region": region,
                }
            }
        )
    
    def get_resource_dependencies(
        self,
        resource_id: str,
        depth: int = 3,
        direction: str = "both"
    ) -> ResourceDependencies:
        """
        Get dependencies for a specific resource.
        
        Args:
            resource_id: Resource ID to analyze
            depth: Maximum depth to traverse (default 3)
            direction: "upstream", "downstream", or "both"
            
        Returns:
            ResourceDependencies with upstream and downstream resources
        """
        upstream = []
        downstream = []
        resource_name = ""
        
        with self.neo4j_client.session() as session:
            # Get resource name
            name_result = session.run(
                "MATCH (r:Resource {id: $id}) RETURN r.name as name",
                id=resource_id
            )
            name_record = name_result.single()
            if name_record:
                resource_name = name_record["name"]
            
            # Get upstream dependencies (what this resource depends on)
            if direction in ("upstream", "both"):
                upstream_query = f"""
                MATCH path = (r:Resource {{id: $id}})-[*1..{depth}]->(dep:Resource)
                RETURN DISTINCT dep.id as id,
                       dep.resource_type as resource_type,
                       dep.name as name,
                       dep.cloud_provider as cloud_provider,
                       dep.region as region,
                       dep as properties
                """
                
                result = session.run(upstream_query, id=resource_id)
                for record in result:
                    raw_props = dict(record["properties"]) if record["properties"] else {}
                    deserialized_props = self._deserialize_json_properties(raw_props)
                    
                    upstream.append(TopologyNode(
                        id=record["id"],
                        resource_type=record["resource_type"],
                        name=record["name"],
                        cloud_provider=record["cloud_provider"],
                        region=record["region"],
                        properties=deserialized_props,
                    ))
            
            # Get downstream dependencies (what depends on this resource)
            if direction in ("downstream", "both"):
                downstream_query = f"""
                MATCH path = (dep:Resource)-[*1..{depth}]->(r:Resource {{id: $id}})
                RETURN DISTINCT dep.id as id,
                       dep.resource_type as resource_type,
                       dep.name as name,
                       dep.cloud_provider as cloud_provider,
                       dep.region as region,
                       dep as properties
                """
                
                result = session.run(downstream_query, id=resource_id)
                for record in result:
                    raw_props = dict(record["properties"]) if record["properties"] else {}
                    deserialized_props = self._deserialize_json_properties(raw_props)
                    
                    downstream.append(TopologyNode(
                        id=record["id"],
                        resource_type=record["resource_type"],
                        name=record["name"],
                        cloud_provider=record["cloud_provider"],
                        region=record["region"],
                        properties=deserialized_props,
                    ))
        
        return ResourceDependencies(
            resource_id=resource_id,
            resource_name=resource_name,
            upstream=upstream,
            downstream=downstream,
            depth=depth,
        )
    
    def get_data_flows(
        self,
        flow_type: Optional[FlowType] = None,
        start_resource_type: Optional[str] = None,
    ) -> List[DataFlow]:
        """
        Get data flow paths through the system.
        
        Args:
            flow_type: Filter by flow type
            start_resource_type: Filter by starting resource type (e.g., "load_balancer")
            
        Returns:
            List of DataFlow objects
        """
        flows = []
        
        # Common data flow patterns to detect
        flow_patterns = [
            # Web traffic: Load Balancer -> Gateway -> Pods -> Database
            ("load_balancer", "gateway", "pod", "database"),
            # Storage flow: Pod -> Storage Account
            ("pod", "storage_account"),
            # Cache flow: Pod -> Redis/Cache
            ("pod", "cache"),
            # Message flow: Service -> Message Queue -> Service
            ("pod", "message_queue", "pod"),
        ]
        
        with self.neo4j_client.session() as session:
            for pattern in flow_patterns:
                if start_resource_type and pattern[0] != start_resource_type:
                    continue
                
                # Build path pattern
                pattern_match = "->".join([f"(r{i}:Resource)" for i in range(len(pattern))])
                
                # Build WHERE clause for resource types
                type_conditions = [
                    f"r{i}.resource_type = '{rtype}'" 
                    for i, rtype in enumerate(pattern)
                ]
                
                query = f"""
                MATCH path = {pattern_match}
                WHERE {' AND '.join(type_conditions)}
                RETURN [node in nodes(path) | node.id] as path_ids,
                       [node in nodes(path) | {{
                           id: node.id,
                           resource_type: node.resource_type,
                           name: node.name,
                           cloud_provider: node.cloud_provider,
                           region: node.region
                       }}] as nodes,
                       [rel in relationships(path) | {{
                           source: startNode(rel).id,
                           target: endNode(rel).id,
                           type: type(rel)
                       }}] as edges
                LIMIT 50
                """
                
                result = session.run(query)
                for record in result:
                    # Convert to TopologyNode objects
                    flow_nodes = [
                        TopologyNode(
                            id=n["id"],
                            resource_type=n["resource_type"],
                            name=n["name"],
                            cloud_provider=n["cloud_provider"],
                            region=n["region"],
                        )
                        for n in record["nodes"]
                    ]
                    
                    # Convert to TopologyEdge objects
                    flow_edges = [
                        TopologyEdge(
                            source_id=e["source"],
                            target_id=e["target"],
                            relationship_type=e["type"],
                            flow_type=self._infer_flow_type(e["type"], {}),
                        )
                        for e in record["edges"]
                    ]
                    
                    # Create flow name from pattern
                    flow_name = " -> ".join([n.resource_type for n in flow_nodes])
                    
                    # Infer flow type from pattern
                    inferred_flow_type = self._infer_flow_type_from_pattern(pattern)
                    
                    if flow_type and inferred_flow_type != flow_type:
                        continue
                    
                    flows.append(DataFlow(
                        id=f"flow_{len(flows)}",
                        name=flow_name,
                        path=record["path_ids"],
                        flow_type=inferred_flow_type,
                        nodes=flow_nodes,
                        edges=flow_edges,
                        metadata={"pattern": pattern}
                    ))
        
        return flows
    
    def _infer_flow_type(
        self,
        relationship_type: str,
        properties: Dict[str, Any]
    ) -> Optional[FlowType]:
        """Infer flow type from relationship type and properties."""
        rel_lower = relationship_type.lower()
        
        if "http" in rel_lower:
            return FlowType.HTTPS if "https" in rel_lower else FlowType.HTTP
        elif "database" in rel_lower or "sql" in rel_lower:
            return FlowType.DATABASE
        elif "storage" in rel_lower or "blob" in rel_lower:
            return FlowType.STORAGE
        elif "cache" in rel_lower or "redis" in rel_lower:
            return FlowType.CACHE
        elif "queue" in rel_lower or "message" in rel_lower:
            return FlowType.MESSAGE_QUEUE
        else:
            return FlowType.INTERNAL
    
    def _infer_flow_type_from_pattern(self, pattern: Tuple[str, ...]) -> FlowType:
        """Infer flow type from resource type pattern."""
        pattern_str = "->".join(pattern)
        
        if "database" in pattern_str:
            return FlowType.DATABASE
        elif "storage" in pattern_str:
            return FlowType.STORAGE
        elif "cache" in pattern_str:
            return FlowType.CACHE
        elif "message_queue" in pattern_str:
            return FlowType.MESSAGE_QUEUE
        elif any(x in pattern_str for x in ("load_balancer", "gateway", "pod")):
            return FlowType.HTTPS
        else:
            return FlowType.INTERNAL
