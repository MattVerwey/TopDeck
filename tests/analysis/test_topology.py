"""Tests for topology service."""

from unittest.mock import MagicMock, Mock

import pytest

from topdeck.analysis.topology import (
    FlowType,
    TopologyEdge,
    TopologyNode,
    TopologyService,
)


@pytest.fixture
def mock_neo4j_client():
    """Create a mock Neo4j client."""
    client = Mock()
    client.session = MagicMock()
    return client


@pytest.fixture
def topology_service(mock_neo4j_client):
    """Create a topology service with mock Neo4j client."""
    return TopologyService(mock_neo4j_client)


def test_topology_service_initialization(topology_service, mock_neo4j_client):
    """Test topology service initialization."""
    assert topology_service.neo4j_client == mock_neo4j_client


def test_infer_flow_type_http(topology_service):
    """Test flow type inference for HTTP."""
    flow_type = topology_service._infer_flow_type("HTTP_CONNECTION", {})
    assert flow_type == FlowType.HTTP


def test_infer_flow_type_https(topology_service):
    """Test flow type inference for HTTPS."""
    flow_type = topology_service._infer_flow_type("HTTPS_CONNECTION", {})
    assert flow_type == FlowType.HTTPS


def test_infer_flow_type_database(topology_service):
    """Test flow type inference for database."""
    flow_type = topology_service._infer_flow_type("DATABASE_CONNECTION", {})
    assert flow_type == FlowType.DATABASE


def test_infer_flow_type_storage(topology_service):
    """Test flow type inference for storage."""
    flow_type = topology_service._infer_flow_type("STORAGE_CONNECTION", {})
    assert flow_type == FlowType.STORAGE


def test_infer_flow_type_cache(topology_service):
    """Test flow type inference for cache."""
    flow_type = topology_service._infer_flow_type("CACHE_CONNECTION", {})
    assert flow_type == FlowType.CACHE


def test_infer_flow_type_internal(topology_service):
    """Test flow type inference for internal."""
    flow_type = topology_service._infer_flow_type("DEPENDS_ON", {})
    assert flow_type == FlowType.INTERNAL


def test_infer_flow_type_from_pattern_database(topology_service):
    """Test flow type inference from pattern with database."""
    pattern = ("pod", "database")
    flow_type = topology_service._infer_flow_type_from_pattern(pattern)
    assert flow_type == FlowType.DATABASE


def test_infer_flow_type_from_pattern_storage(topology_service):
    """Test flow type inference from pattern with storage."""
    pattern = ("pod", "storage_account")
    flow_type = topology_service._infer_flow_type_from_pattern(pattern)
    assert flow_type == FlowType.STORAGE


def test_infer_flow_type_from_pattern_https(topology_service):
    """Test flow type inference from pattern with load balancer."""
    pattern = ("load_balancer", "gateway", "pod")
    flow_type = topology_service._infer_flow_type_from_pattern(pattern)
    assert flow_type == FlowType.HTTPS


def test_topology_node_creation():
    """Test topology node creation."""
    node = TopologyNode(
        id="test-resource-1",
        resource_type="pod",
        name="test-pod",
        cloud_provider="azure",
        region="eastus",
    )

    assert node.id == "test-resource-1"
    assert node.resource_type == "pod"
    assert node.name == "test-pod"
    assert node.cloud_provider == "azure"
    assert node.region == "eastus"


def test_topology_edge_creation():
    """Test topology edge creation."""
    edge = TopologyEdge(
        source_id="resource-1",
        target_id="resource-2",
        relationship_type="DEPENDS_ON",
        flow_type=FlowType.HTTP,
    )

    assert edge.source_id == "resource-1"
    assert edge.target_id == "resource-2"
    assert edge.relationship_type == "DEPENDS_ON"
    assert edge.flow_type == FlowType.HTTP
