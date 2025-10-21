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
    ResourceAttachment,
    DependencyChain,
    ResourceAttachmentAnalysis,
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


class ResourceAttachmentResponse(BaseModel):
    """Response model for resource attachment."""
    
    source_id: str
    source_name: str
    source_type: str
    target_id: str
    target_name: str
    target_type: str
    relationship_type: str
    relationship_properties: dict = Field(default_factory=dict)
    attachment_context: dict = Field(default_factory=dict)


class ResourceDependenciesResponse(BaseModel):
    """Response model for resource dependencies."""
    
    resource_id: str
    resource_name: str
    upstream: List[TopologyNodeResponse]
    downstream: List[TopologyNodeResponse]
    upstream_attachments: List[ResourceAttachmentResponse] = Field(default_factory=list)
    downstream_attachments: List[ResourceAttachmentResponse] = Field(default_factory=list)
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


class DependencyChainResponse(BaseModel):
    """Response model for dependency chain."""
    
    chain_id: str
    resource_ids: List[str]
    resource_names: List[str]
    resource_types: List[str]
    relationships: List[str]
    chain_length: int
    total_risk_score: float = 0.0
    metadata: dict = Field(default_factory=dict)


class ResourceAttachmentAnalysisResponse(BaseModel):
    """Response model for in-depth resource attachment analysis."""
    
    resource_id: str
    resource_name: str
    resource_type: str
    total_attachments: int
    attachment_by_type: dict = Field(default_factory=dict)
    critical_attachments: List[ResourceAttachmentResponse] = Field(default_factory=list)
    attachment_strength: dict = Field(default_factory=dict)
    dependency_chains: List[DependencyChainResponse] = Field(default_factory=list)
    impact_radius: int
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
            upstream_attachments=[
                ResourceAttachmentResponse(
                    source_id=att.source_id,
                    source_name=att.source_name,
                    source_type=att.source_type,
                    target_id=att.target_id,
                    target_name=att.target_name,
                    target_type=att.target_type,
                    relationship_type=att.relationship_type,
                    relationship_properties=att.relationship_properties,
                    attachment_context=att.attachment_context,
                )
                for att in dependencies.upstream_attachments
            ],
            downstream_attachments=[
                ResourceAttachmentResponse(
                    source_id=att.source_id,
                    source_name=att.source_name,
                    source_type=att.source_type,
                    target_id=att.target_id,
                    target_name=att.target_name,
                    target_type=att.target_type,
                    relationship_type=att.relationship_type,
                    relationship_properties=att.relationship_properties,
                    attachment_context=att.attachment_context,
                )
                for att in dependencies.downstream_attachments
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


@router.get("/resources/{resource_id}/attachments", response_model=List[ResourceAttachmentResponse])
async def get_resource_attachments(
    resource_id: str,
    direction: str = Query(
        "both",
        regex="^(upstream|downstream|both)$",
        description="Direction to get attachments (upstream, downstream, or both)"
    ),
) -> List[ResourceAttachmentResponse]:
    """
    Get detailed attachment information for a resource.
    
    Shows all relationship types, properties, and connection context
    to understand how resources are connected. This provides the detailed
    "which resources are attached to which" view.
    """
    try:
        service = get_topology_service()
        attachments = service.get_resource_attachments(
            resource_id=resource_id,
            direction=direction,
        )
        
        return [
            ResourceAttachmentResponse(
                source_id=att.source_id,
                source_name=att.source_name,
                source_type=att.source_type,
                target_id=att.target_id,
                target_name=att.target_name,
                target_type=att.target_type,
                relationship_type=att.relationship_type,
                relationship_properties=att.relationship_properties,
                attachment_context=att.attachment_context,
            )
            for att in attachments
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get resource attachments: {str(e)}"
        )


@router.get("/resources/{resource_id}/chains", response_model=List[DependencyChainResponse])
async def get_dependency_chains(
    resource_id: str,
    max_depth: int = Query(5, ge=1, le=10, description="Maximum chain depth"),
    direction: str = Query(
        "downstream",
        regex="^(upstream|downstream)$",
        description="Direction to trace chains (upstream or downstream)"
    ),
) -> List[DependencyChainResponse]:
    """
    Get all dependency chains starting from a resource.
    
    Identifies complete paths showing how dependencies and failures propagate
    through the system. Useful for understanding cascading impacts.
    """
    try:
        service = get_topology_service()
        chains = service.get_dependency_chains(
            resource_id=resource_id,
            max_depth=max_depth,
            direction=direction,
        )
        
        return [
            DependencyChainResponse(
                chain_id=chain.chain_id,
                resource_ids=chain.resource_ids,
                resource_names=chain.resource_names,
                resource_types=chain.resource_types,
                relationships=chain.relationships,
                chain_length=chain.chain_length,
                total_risk_score=chain.total_risk_score,
                metadata=chain.metadata,
            )
            for chain in chains
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get dependency chains: {str(e)}"
        )


@router.get("/resources/{resource_id}/analysis", response_model=ResourceAttachmentAnalysisResponse)
async def get_attachment_analysis(
    resource_id: str,
) -> ResourceAttachmentAnalysisResponse:
    """
    Get comprehensive in-depth analysis of resource attachments.
    
    Provides detailed metrics about how a resource connects to others, including:
    - Attachment types and distribution
    - Attachment strength scores
    - Critical attachments
    - Dependency chains
    - Impact radius
    
    This endpoint provides the "bigger picture" and "in-depth analysis" requested.
    """
    try:
        service = get_topology_service()
        analysis = service.get_attachment_analysis(resource_id=resource_id)
        
        return ResourceAttachmentAnalysisResponse(
            resource_id=analysis.resource_id,
            resource_name=analysis.resource_name,
            resource_type=analysis.resource_type,
            total_attachments=analysis.total_attachments,
            attachment_by_type=analysis.attachment_by_type,
            critical_attachments=[
                ResourceAttachmentResponse(
                    source_id=att.source_id,
                    source_name=att.source_name,
                    source_type=att.source_type,
                    target_id=att.target_id,
                    target_name=att.target_name,
                    target_type=att.target_type,
                    relationship_type=att.relationship_type,
                    relationship_properties=att.relationship_properties,
                    attachment_context=att.attachment_context,
                )
                for att in analysis.critical_attachments
            ],
            attachment_strength=analysis.attachment_strength,
            dependency_chains=[
                DependencyChainResponse(
                    chain_id=chain.chain_id,
                    resource_ids=chain.resource_ids,
                    resource_names=chain.resource_names,
                    resource_types=chain.resource_types,
                    relationships=chain.relationships,
                    chain_length=chain.chain_length,
                    total_risk_score=chain.total_risk_score,
                    metadata=chain.metadata,
                )
                for chain in analysis.dependency_chains
            ],
            impact_radius=analysis.impact_radius,
            metadata=analysis.metadata,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get attachment analysis: {str(e)}"
        )
