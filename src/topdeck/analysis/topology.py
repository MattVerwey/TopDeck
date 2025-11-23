"""
Topology analysis and aggregation service.

Builds network topology graphs from discovered resources and relationships,
supporting drill-down capabilities and data flow visualization.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

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
    region: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TopologyEdge:
    """Represents an edge (relationship) in the topology graph."""

    source_id: str
    target_id: str
    relationship_type: str
    flow_type: FlowType | None = None
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class TopologyGraph:
    """Complete topology graph with nodes and edges."""

    nodes: list[TopologyNode]
    edges: list[TopologyEdge]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DataFlow:
    """Represents a data flow path through the system."""

    id: str
    name: str
    path: list[str]  # List of resource IDs in the flow
    flow_type: FlowType
    nodes: list[TopologyNode]
    edges: list[TopologyEdge]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceAttachment:
    """Detailed attachment information between two resources."""

    source_id: str
    source_name: str
    source_type: str
    target_id: str
    target_name: str
    target_type: str
    relationship_type: str
    relationship_properties: dict[str, Any] = field(default_factory=dict)
    attachment_context: dict[str, Any] = field(default_factory=dict)  # ports, protocols, etc.


@dataclass
class ResourceDependencies:
    """Dependencies for a specific resource."""

    resource_id: str
    resource_name: str
    upstream: list[TopologyNode]  # Resources this depends on
    downstream: list[TopologyNode]  # Resources that depend on this
    upstream_attachments: list[ResourceAttachment] = field(
        default_factory=list
    )  # Detailed upstream connections
    downstream_attachments: list[ResourceAttachment] = field(
        default_factory=list
    )  # Detailed downstream connections
    depth: int = 1


@dataclass
class DependencyChain:
    """Represents a complete dependency chain path."""

    chain_id: str
    resource_ids: list[str]
    resource_names: list[str]
    resource_types: list[str]
    relationships: list[str]
    chain_length: int
    total_risk_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceAttachmentAnalysis:
    """In-depth analysis of resource attachments."""

    resource_id: str
    resource_name: str
    resource_type: str
    total_attachments: int
    attachment_by_type: dict[str, int]  # Count of attachments by relationship type
    critical_attachments: list[ResourceAttachment]  # High-impact attachments
    attachment_strength: dict[str, float]  # Strength score by relationship type
    dependency_chains: list[DependencyChain]
    impact_radius: int  # Number of resources affected within N hops
    metadata: dict[str, Any] = field(default_factory=dict)


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
    def _deserialize_json_properties(properties: dict[str, Any]) -> dict[str, Any]:
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
            if key in ("tags", "properties") and isinstance(value, str):
                try:
                    deserialized = json.loads(value)
                    # If the properties field is deserialized, it may contain nested structures
                    # like topics/queues for Service Bus, so we need to ensure those are also properly handled
                    if key == "properties" and isinstance(deserialized, dict):
                        # Recursively deserialize nested properties
                        result[key] = deserialized
                    else:
                        result[key] = deserialized
                except (json.JSONDecodeError, TypeError):
                    # If it fails, keep as-is
                    result[key] = value
            # Handle other JSON string fields (lists like topics, approvers, etc.)
            elif key in (
                "topics",
                "queues",
                "identifier_uris",
                "redirect_uris",
                "target_resources",
                "approvers",
                "containers",
                "init_containers",
                "volumes",
                "conditions",
                "labels",
                "annotations",
                "app_roles",
                "oauth2_permissions",
                "required_resource_access",
            ) and isinstance(value, str):
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = value
            else:
                result[key] = value

        return result

    def get_topology(
        self,
        cloud_provider: str | None = None,
        resource_type: str | None = None,
        region: str | None = None,
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
                
                # Flatten nested properties field if it exists
                # Neo4j stores detailed properties as a JSON string in the 'properties' field
                # We want to merge those into the top level for easier access
                if "properties" in deserialized_props and isinstance(deserialized_props["properties"], dict):
                    nested_props = deserialized_props.pop("properties")
                    # Merge nested properties into parent, but don't overwrite existing keys
                    for key, value in nested_props.items():
                        if key not in deserialized_props:
                            deserialized_props[key] = value

                nodes.append(
                    TopologyNode(
                        id=record["id"],
                        resource_type=record["resource_type"],
                        name=record["name"],
                        cloud_provider=record["cloud_provider"],
                        region=record["region"],
                        properties=deserialized_props,
                    )
                )

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
                    record["relationship_type"], record["properties"] or {}
                )
                edges.append(
                    TopologyEdge(
                        source_id=record["source_id"],
                        target_id=record["target_id"],
                        relationship_type=record["relationship_type"],
                        flow_type=flow_type,
                        properties=dict(record["properties"]) if record["properties"] else {},
                    )
                )

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
                },
            },
        )

    def get_resource_dependencies(
        self, resource_id: str, depth: int = 3, direction: str = "both"
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
                "MATCH (r:Resource {id: $id}) RETURN r.name as name", id=resource_id
            )
            name_record = name_result.single()
            if name_record:
                resource_name = name_record["name"]

            # Get upstream dependencies (what this resource depends on)
            if direction in ("upstream", "both"):
                # Limit depth to 5 for performance, add result limit
                upstream_query = f"""
                MATCH path = (r:Resource {{id: $id}})-[*1..{min(depth, 5)}]->(dep:Resource)
                WITH DISTINCT dep, min(length(path)) as shortest_path
                RETURN dep.id as id,
                       dep.resource_type as resource_type,
                       dep.name as name,
                       dep.cloud_provider as cloud_provider,
                       dep.region as region,
                       dep as properties
                ORDER BY shortest_path
                LIMIT 1000
                """

                result = session.run(upstream_query, id=resource_id)
                for record in result:
                    raw_props = dict(record["properties"]) if record["properties"] else {}
                    deserialized_props = self._deserialize_json_properties(raw_props)

                    upstream.append(
                        TopologyNode(
                            id=record["id"],
                            resource_type=record["resource_type"],
                            name=record["name"],
                            cloud_provider=record["cloud_provider"],
                            region=record["region"],
                            properties=deserialized_props,
                        )
                    )

            # Get downstream dependencies (what depends on this resource)
            if direction in ("downstream", "both"):
                # Limit depth to 5 for performance, add result limit
                downstream_query = f"""
                MATCH path = (dep:Resource)-[*1..{min(depth, 5)}]->(r:Resource {{id: $id}})
                WITH DISTINCT dep, min(length(path)) as shortest_path
                RETURN dep.id as id,
                       dep.resource_type as resource_type,
                       dep.name as name,
                       dep.cloud_provider as cloud_provider,
                       dep.region as region,
                       dep as properties
                ORDER BY shortest_path
                LIMIT 1000
                """

                result = session.run(downstream_query, id=resource_id)
                for record in result:
                    raw_props = dict(record["properties"]) if record["properties"] else {}
                    deserialized_props = self._deserialize_json_properties(raw_props)

                    downstream.append(
                        TopologyNode(
                            id=record["id"],
                            resource_type=record["resource_type"],
                            name=record["name"],
                            cloud_provider=record["cloud_provider"],
                            region=record["region"],
                            properties=deserialized_props,
                        )
                    )

        # Get detailed attachment information
        upstream_attachments = []
        downstream_attachments = []

        if direction in ("upstream", "both"):
            upstream_attachments = list(
                self.get_resource_attachments(resource_id, direction="upstream")
            )

        if direction in ("downstream", "both"):
            downstream_attachments = list(
                self.get_resource_attachments(resource_id, direction="downstream")
            )

        return ResourceDependencies(
            resource_id=resource_id,
            resource_name=resource_name,
            upstream=upstream,
            downstream=downstream,
            upstream_attachments=upstream_attachments,
            downstream_attachments=downstream_attachments,
            depth=depth,
        )

    def get_data_flows(
        self,
        flow_type: FlowType | None = None,
        start_resource_type: str | None = None,
    ) -> list[DataFlow]:
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
                    f"r{i}.resource_type = '{rtype}'" for i, rtype in enumerate(pattern)
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

                    flows.append(
                        DataFlow(
                            id=f"flow_{len(flows)}",
                            name=flow_name,
                            path=record["path_ids"],
                            flow_type=inferred_flow_type,
                            nodes=flow_nodes,
                            edges=flow_edges,
                            metadata={"pattern": pattern},
                        )
                    )

        return flows

    def _infer_flow_type(
        self, relationship_type: str, properties: dict[str, Any]
    ) -> FlowType | None:
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

    def _infer_flow_type_from_pattern(self, pattern: tuple[str, ...]) -> FlowType:
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

    def get_resource_attachments(
        self, resource_id: str, direction: str = "both"
    ) -> list[ResourceAttachment]:
        """
        Get detailed attachment information for a resource.

        Shows all relationship types, properties, and connection context
        for understanding how resources are connected.

        Args:
            resource_id: Resource ID to analyze
            direction: "upstream", "downstream", or "both"

        Returns:
            List of ResourceAttachment objects with detailed connection info
        """
        attachments = []

        with self.neo4j_client.session() as session:
            # Get upstream attachments (what this resource connects to)
            if direction in ("upstream", "both"):
                upstream_query = """
                MATCH (source:Resource {id: $id})-[rel]->(target:Resource)
                RETURN source.id as source_id,
                       source.name as source_name,
                       source.resource_type as source_type,
                       target.id as target_id,
                       target.name as target_name,
                       target.resource_type as target_type,
                       type(rel) as relationship_type,
                       properties(rel) as rel_properties
                """

                result = session.run(upstream_query, id=resource_id)
                for record in result:
                    attachments.append(
                        ResourceAttachment(
                            source_id=record["source_id"],
                            source_name=record["source_name"],
                            source_type=record["source_type"],
                            target_id=record["target_id"],
                            target_name=record["target_name"],
                            target_type=record["target_type"],
                            relationship_type=record["relationship_type"],
                            relationship_properties=(
                                dict(record["rel_properties"]) if record["rel_properties"] else {}
                            ),
                            attachment_context=self._build_attachment_context(
                                record["relationship_type"],
                                dict(record["rel_properties"]) if record["rel_properties"] else {},
                            ),
                        )
                    )

            # Get downstream attachments (what connects to this resource)
            if direction in ("downstream", "both"):
                downstream_query = """
                MATCH (source:Resource)-[rel]->(target:Resource {id: $id})
                RETURN source.id as source_id,
                       source.name as source_name,
                       source.resource_type as source_type,
                       target.id as target_id,
                       target.name as target_name,
                       target.resource_type as target_type,
                       type(rel) as relationship_type,
                       properties(rel) as rel_properties
                """

                result = session.run(downstream_query, id=resource_id)
                for record in result:
                    attachments.append(
                        ResourceAttachment(
                            source_id=record["source_id"],
                            source_name=record["source_name"],
                            source_type=record["source_type"],
                            target_id=record["target_id"],
                            target_name=record["target_name"],
                            target_type=record["target_type"],
                            relationship_type=record["relationship_type"],
                            relationship_properties=(
                                dict(record["rel_properties"]) if record["rel_properties"] else {}
                            ),
                            attachment_context=self._build_attachment_context(
                                record["relationship_type"],
                                dict(record["rel_properties"]) if record["rel_properties"] else {},
                            ),
                        )
                    )

        return attachments

    def _build_attachment_context(
        self, relationship_type: str, properties: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Build contextual information about the attachment.

        Extracts meaningful connection details like ports, protocols, etc.
        """
        context = {}

        # Extract common connection properties
        if "port" in properties:
            context["port"] = properties["port"]
        if "protocol" in properties:
            context["protocol"] = properties["protocol"]
        if "connection_string" in properties:
            context["connection_string"] = properties["connection_string"]
        if "endpoint" in properties:
            context["endpoint"] = properties["endpoint"]

        # Add relationship-specific context
        context["relationship_category"] = self._categorize_relationship(relationship_type)
        context["is_critical"] = self._is_critical_attachment(relationship_type)

        return context

    def _categorize_relationship(self, relationship_type: str) -> str:
        """Categorize relationship into high-level groups."""
        rel_lower = relationship_type.lower()

        if any(x in rel_lower for x in ["depends", "uses"]):
            return "dependency"
        elif any(x in rel_lower for x in ["connects", "routes", "accesses"]):
            return "connectivity"
        elif any(x in rel_lower for x in ["deployed", "built", "contains"]):
            return "deployment"
        elif any(x in rel_lower for x in ["authenticates", "authorizes"]):
            return "security"
        else:
            return "other"

    def _is_critical_attachment(self, relationship_type: str) -> bool:
        """Determine if an attachment is critical."""
        critical_types = ["DEPENDS_ON", "AUTHENTICATES_WITH", "ROUTES_TO", "CONNECTS_TO"]
        return relationship_type.upper() in critical_types

    def get_dependency_chains(
        self, resource_id: str, max_depth: int = 5, direction: str = "downstream"
    ) -> list[DependencyChain]:
        """
        Get all dependency chains starting from a resource.

        Identifies complete paths showing how failures propagate.

        Args:
            resource_id: Resource ID to start from
            max_depth: Maximum chain length
            direction: "upstream" or "downstream"

        Returns:
            List of DependencyChain objects
        """
        chains = []

        # Build the path pattern based on direction
        if direction == "downstream":
            path_pattern = f"(r:Resource {{id: $id}})<-[*1..{max_depth}]-(dependent:Resource)"
        else:
            path_pattern = f"(r:Resource {{id: $id}})-[*1..{max_depth}]->(dependency:Resource)"

        query = f"""
        MATCH path = {path_pattern}
        WITH path, [node IN nodes(path) | node.id] as ids,
             [node IN nodes(path) | node.name] as names,
             [node IN nodes(path) | node.resource_type] as types,
             [rel IN relationships(path) | type(rel)] as rels
        WHERE size(ids) > 1
        RETURN DISTINCT ids, names, types, rels, length(path) as chain_length
        ORDER BY chain_length DESC
        LIMIT 50
        """

        with self.neo4j_client.session() as session:
            result = session.run(query, id=resource_id)
            for idx, record in enumerate(result):
                chains.append(
                    DependencyChain(
                        chain_id=f"chain_{idx}",
                        resource_ids=record["ids"],
                        resource_names=record["names"],
                        resource_types=record["types"],
                        relationships=record["rels"],
                        chain_length=record["chain_length"],
                        metadata={"direction": direction, "start_resource": resource_id},
                    )
                )

        return chains

    def get_attachment_analysis(self, resource_id: str) -> ResourceAttachmentAnalysis:
        """
        Get comprehensive in-depth analysis of resource attachments.

        Provides detailed metrics about how a resource connects to others,
        including attachment types, strength, and impact analysis.

        Args:
            resource_id: Resource ID to analyze

        Returns:
            ResourceAttachmentAnalysis with comprehensive metrics
        """
        with self.neo4j_client.session() as session:
            # Get basic resource info
            resource_query = """
            MATCH (r:Resource {id: $id})
            RETURN r.name as name, r.resource_type as type
            """
            resource_result = session.run(resource_query, id=resource_id)
            resource_record = resource_result.single()

            if not resource_record:
                raise ValueError(f"Resource {resource_id} not found")

            resource_name = resource_record["name"]
            resource_type = resource_record["type"]

            # Get all attachments
            attachments = self.get_resource_attachments(resource_id, direction="both")

            # Count attachments by type
            attachment_by_type: dict[str, int] = {}
            attachment_strength: dict[str, float] = {}
            critical_attachments = []

            for attachment in attachments:
                rel_type = attachment.relationship_type
                attachment_by_type[rel_type] = attachment_by_type.get(rel_type, 0) + 1

                # Calculate strength score (based on criticality and properties)
                strength = 0.5  # Base strength
                if attachment.attachment_context.get("is_critical", False):
                    strength += 0.3
                    critical_attachments.append(attachment)
                if attachment.relationship_properties:
                    strength += 0.2

                if rel_type not in attachment_strength:
                    attachment_strength[rel_type] = strength
                else:
                    attachment_strength[rel_type] = max(attachment_strength[rel_type], strength)

            # Get dependency chains
            downstream_chains = self.get_dependency_chains(
                resource_id, direction="downstream", max_depth=5
            )
            upstream_chains = self.get_dependency_chains(
                resource_id, direction="upstream", max_depth=5
            )
            all_chains = downstream_chains + upstream_chains

            # Calculate impact radius
            impact_radius_query = """
            MATCH (r:Resource {id: $id})-[*1..3]-(connected:Resource)
            WITH DISTINCT connected
            RETURN count(connected) as radius
            """
            radius_result = session.run(impact_radius_query, id=resource_id)
            radius_record = radius_result.single()
            impact_radius = radius_record["radius"] if radius_record else 0

        return ResourceAttachmentAnalysis(
            resource_id=resource_id,
            resource_name=resource_name,
            resource_type=resource_type,
            total_attachments=len(attachments),
            attachment_by_type=attachment_by_type,
            critical_attachments=critical_attachments,
            attachment_strength=attachment_strength,
            dependency_chains=all_chains,
            impact_radius=impact_radius,
            metadata={
                "analysis_depth": 3,
                "max_chain_length": (
                    max(chain.chain_length for chain in all_chains) if all_chains else 0
                ),
                "unique_relationship_types": len(attachment_by_type),
            },
        )
