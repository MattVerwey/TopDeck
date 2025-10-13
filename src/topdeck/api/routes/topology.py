"""
Topology API endpoints.

Provides API endpoints for retrieving topology data, resource dependencies,
and data flows for network visualization and drill-down.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from topdeck.analysis.topology import (
    TopologyService,
    TopologyGraph,
    TopologyNode,
    TopologyEdge,
    ResourceDependencies,
    DataFlow,
    FlowType,
)
from topdeck.storage.neo4j_client import Neo4jClient
from topdeck.common.config import settings


# Pydantic models for API responses
class TopologyNodeResponse(BaseModel):
    """Response model for topology node."""
    
    id: str
    resource_type: str
    name: str
    cloud_provider: str
    region: Optional[str] = None
    properties: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class TopologyEdgeResponse(BaseModel):
    """Response model for topology edge."""
    
    source_id: str
    target_id: str
    relationship_type: str
    flow_type: Optional[str] = None
    properties: dict = Field(default_factory=dict)


class TopologyGraphResponse(BaseModel):
    """Response model for topology graph."""
    
    nodes: List[TopologyNodeResponse]
    edges: List[TopologyEdgeResponse]
    metadata: dict = Field(default_factory=dict)


class ResourceDependenciesResponse(BaseModel):
    """Response model for resource dependencies."""
    
    resource_id: str
    resource_name: str
    upstream: List[TopologyNodeResponse]
    downstream: List[TopologyNodeResponse]
    depth: int


class DataFlowResponse(BaseModel):
    """Response model for data flow."""
    
    id: str
    name: str
    path: List[str]
    flow_type: str
    nodes: List[TopologyNodeResponse]
    edges: List[TopologyEdgeResponse]
    metadata: dict = Field(default_factory=dict)


# Create router
router = APIRouter(prefix="/api/v1/topology", tags=["topology"])


def get_topology_service() -> TopologyService:
    """Get topology service instance."""
    neo4j_client = Neo4jClient(
        uri=settings.neo4j_uri,
        username=settings.neo4j_username,
        password=settings.neo4j_password,
    )
    neo4j_client.connect()
    return TopologyService(neo4j_client)


@router.get("", response_model=TopologyGraphResponse)
async def get_topology(
    cloud_provider: Optional[str] = Query(
        None,
        description="Filter by cloud provider (azure, aws, gcp)"
    ),
    resource_type: Optional[str] = Query(
        None,
        description="Filter by resource type"
    ),
    region: Optional[str] = Query(
        None,
        description="Filter by region"
    ),
) -> TopologyGraphResponse:
    """
    Get complete topology graph with optional filtering.
    
    Returns nodes (resources) and edges (relationships) that form the
    network topology. Supports filtering by cloud provider, resource type,
    and region.
    """
    try:
        service = get_topology_service()
        topology = service.get_topology(
            cloud_provider=cloud_provider,
            resource_type=resource_type,
            region=region,
        )
        
        return TopologyGraphResponse(
            nodes=[
                TopologyNodeResponse(
                    id=node.id,
                    resource_type=node.resource_type,
                    name=node.name,
                    cloud_provider=node.cloud_provider,
                    region=node.region,
                    properties=node.properties,
                    metadata=node.metadata,
                )
                for node in topology.nodes
            ],
            edges=[
                TopologyEdgeResponse(
                    source_id=edge.source_id,
                    target_id=edge.target_id,
                    relationship_type=edge.relationship_type,
                    flow_type=edge.flow_type.value if edge.flow_type else None,
                    properties=edge.properties,
                )
                for edge in topology.edges
            ],
            metadata=topology.metadata,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get topology: {str(e)}")


@router.get("/resources/{resource_id}/dependencies", response_model=ResourceDependenciesResponse)
async def get_resource_dependencies(
    resource_id: str,
    depth: int = Query(3, ge=1, le=10, description="Maximum depth to traverse"),
    direction: str = Query(
        "both",
        regex="^(upstream|downstream|both)$",
        description="Direction to traverse (upstream, downstream, or both)"
    ),
) -> ResourceDependenciesResponse:
    """
    Get dependencies for a specific resource.
    
    Returns upstream dependencies (what this resource depends on) and
    downstream dependencies (what depends on this resource).
    """
    try:
        service = get_topology_service()
        dependencies = service.get_resource_dependencies(
            resource_id=resource_id,
            depth=depth,
            direction=direction,
        )
        
        return ResourceDependenciesResponse(
            resource_id=dependencies.resource_id,
            resource_name=dependencies.resource_name,
            upstream=[
                TopologyNodeResponse(
                    id=node.id,
                    resource_type=node.resource_type,
                    name=node.name,
                    cloud_provider=node.cloud_provider,
                    region=node.region,
                    properties=node.properties,
                    metadata=node.metadata,
                )
                for node in dependencies.upstream
            ],
            downstream=[
                TopologyNodeResponse(
                    id=node.id,
                    resource_type=node.resource_type,
                    name=node.name,
                    cloud_provider=node.cloud_provider,
                    region=node.region,
                    properties=node.properties,
                    metadata=node.metadata,
                )
                for node in dependencies.downstream
            ],
            depth=dependencies.depth,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get dependencies: {str(e)}"
        )


@router.get("/flows", response_model=List[DataFlowResponse])
async def get_data_flows(
    flow_type: Optional[str] = Query(
        None,
        description="Filter by flow type (http, https, database, storage, cache, etc.)"
    ),
    start_resource_type: Optional[str] = Query(
        None,
        description="Filter by starting resource type (e.g., load_balancer, pod)"
    ),
) -> List[DataFlowResponse]:
    """
    Get data flow paths through the system.
    
    Returns detected data flows showing how data moves through resources.
    Useful for visualizing request paths, database connections, and
    service dependencies.
    """
    try:
        service = get_topology_service()
        
        # Convert flow_type string to FlowType enum if provided
        flow_type_enum = None
        if flow_type:
            try:
                flow_type_enum = FlowType(flow_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid flow_type: {flow_type}"
                )
        
        flows = service.get_data_flows(
            flow_type=flow_type_enum,
            start_resource_type=start_resource_type,
        )
        
        return [
            DataFlowResponse(
                id=flow.id,
                name=flow.name,
                path=flow.path,
                flow_type=flow.flow_type.value,
                nodes=[
                    TopologyNodeResponse(
                        id=node.id,
                        resource_type=node.resource_type,
                        name=node.name,
                        cloud_provider=node.cloud_provider,
                        region=node.region,
                        properties=node.properties,
                        metadata=node.metadata,
                    )
                    for node in flow.nodes
                ],
                edges=[
                    TopologyEdgeResponse(
                        source_id=edge.source_id,
                        target_id=edge.target_id,
                        relationship_type=edge.relationship_type,
                        flow_type=edge.flow_type.value if edge.flow_type else None,
                        properties=edge.properties,
                    )
                    for edge in flow.edges
                ],
                metadata=flow.metadata,
            )
            for flow in flows
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get data flows: {str(e)}"
        )
