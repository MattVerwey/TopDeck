"""Tests for transaction flow service."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from topdeck.monitoring.transaction_flow import (
    TransactionFlowService,
    FlowNode,
    FlowEdge,
    TransactionFlowVisualization,
)


@pytest.fixture
def mock_neo4j_client():
    """Create a mock Neo4j client."""
    client = Mock()
    client.driver = Mock()
    session = Mock()
    client.driver.session.return_value.__enter__ = Mock(return_value=session)
    client.driver.session.return_value.__exit__ = Mock(return_value=False)
    return client


@pytest.fixture
def transaction_flow_service(mock_neo4j_client):
    """Create a transaction flow service instance."""
    return TransactionFlowService(
        neo4j_client=mock_neo4j_client,
        loki_url="http://loki:3100",
        prometheus_url="http://prometheus:9090",
        azure_workspace_id="test-workspace-id",
    )


def test_initialization(transaction_flow_service):
    """Test transaction flow service initialization."""
    assert transaction_flow_service.loki_url == "http://loki:3100"
    assert transaction_flow_service.prometheus_url == "http://prometheus:9090"
    assert transaction_flow_service.azure_workspace_id == "test-workspace-id"


def test_extract_resource_name(transaction_flow_service):
    """Test resource name extraction."""
    # Azure resource ID format
    resource_id = "/subscriptions/sub-id/resourceGroups/rg/providers/Microsoft.ContainerService/managedClusters/aks/pods/pod-123"
    name = transaction_flow_service._extract_resource_name(resource_id)
    assert name == "pod-123"

    # Simple name
    name = transaction_flow_service._extract_resource_name("simple-name")
    assert name == "simple-name"


def test_infer_resource_type(transaction_flow_service):
    """Test resource type inference."""
    # Pod
    resource_id = "/subscriptions/sub-id/resourceGroups/rg/providers/Microsoft.ContainerService/managedClusters/aks/pods/pod-123"
    resource_type = transaction_flow_service._infer_resource_type(resource_id)
    assert resource_type == "pod"

    # App Service
    resource_id = "/subscriptions/sub-id/resourceGroups/rg/providers/Microsoft.Web/sites/myapp"
    resource_type = transaction_flow_service._infer_resource_type(resource_id)
    assert resource_type == "app_service"

    # Load Balancer
    resource_id = "/subscriptions/sub-id/resourceGroups/rg/providers/Microsoft.Network/loadBalancers/lb-1"
    resource_type = transaction_flow_service._infer_resource_type(resource_id)
    assert resource_type == "load_balancer"

    # Database
    resource_id = "/subscriptions/sub-id/resourceGroups/rg/providers/Microsoft.Sql/servers/server1/databases/db1"
    resource_type = transaction_flow_service._infer_resource_type(resource_id)
    assert resource_type == "database"

    # Unknown
    resource_id = "/some/unknown/resource"
    resource_type = transaction_flow_service._infer_resource_type(resource_id)
    assert resource_type == "service"


def test_merge_flows_empty(transaction_flow_service):
    """Test merging empty flows."""
    result = transaction_flow_service._merge_flows([], "test-correlation-id")
    assert result is None


def test_merge_flows_single(transaction_flow_service):
    """Test merging single flow."""
    flow = TransactionFlowVisualization(
        transaction_id="test-id",
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow(),
        total_duration_ms=100.0,
        nodes=[],
        edges=[],
        status="success",
        error_count=0,
        warning_count=0,
        source="loki",
    )
    result = transaction_flow_service._merge_flows([flow], "test-id")
    assert result == flow


def test_merge_flows_multiple(transaction_flow_service):
    """Test merging multiple flows."""
    start_time1 = datetime.utcnow()
    end_time1 = start_time1 + timedelta(seconds=1)

    start_time2 = start_time1 + timedelta(seconds=0.5)
    end_time2 = start_time2 + timedelta(seconds=1)

    node1 = FlowNode(
        resource_id="resource-1",
        resource_name="Resource 1",
        resource_type="pod",
        timestamp=start_time1,
        status="success",
        log_entries=[],
    )

    node2 = FlowNode(
        resource_id="resource-2",
        resource_name="Resource 2",
        resource_type="service",
        timestamp=start_time2,
        status="success",
        log_entries=[],
    )

    edge1 = FlowEdge(source_id="resource-1", target_id="resource-2")

    flow1 = TransactionFlowVisualization(
        transaction_id="test-id",
        start_time=start_time1,
        end_time=end_time1,
        total_duration_ms=1000.0,
        nodes=[node1],
        edges=[edge1],
        status="success",
        error_count=0,
        warning_count=0,
        source="loki",
    )

    flow2 = TransactionFlowVisualization(
        transaction_id="test-id",
        start_time=start_time2,
        end_time=end_time2,
        total_duration_ms=1000.0,
        nodes=[node2],
        edges=[edge1],
        status="success",
        error_count=1,
        warning_count=0,
        source="azure_log_analytics",
    )

    result = transaction_flow_service._merge_flows([flow1, flow2], "test-id")

    assert result is not None
    assert result.transaction_id == "test-id"
    assert len(result.nodes) == 2
    assert len(result.edges) == 1  # Duplicate removed
    assert result.error_count == 1
    assert result.status == "error"
    assert result.source == "multi"


@pytest.mark.asyncio
async def test_find_correlation_ids_for_pod_empty(transaction_flow_service):
    """Test finding correlation IDs with no results."""
    with patch.object(
        transaction_flow_service, "azure_workspace_id", None
    ), patch.object(transaction_flow_service, "loki_url", None):
        result = await transaction_flow_service.find_correlation_ids_for_pod(
            "pod-123", timedelta(hours=1), 50
        )
        assert result == []


def test_flow_node_creation():
    """Test FlowNode creation."""
    node = FlowNode(
        resource_id="test-resource",
        resource_name="Test Resource",
        resource_type="pod",
        timestamp=datetime.utcnow(),
        status="success",
        log_entries=[],
    )

    assert node.resource_id == "test-resource"
    assert node.resource_name == "Test Resource"
    assert node.resource_type == "pod"
    assert node.status == "success"
    assert node.log_entries == []


def test_flow_edge_creation():
    """Test FlowEdge creation."""
    edge = FlowEdge(
        source_id="resource-1",
        target_id="resource-2",
        protocol="https",
        duration_ms=100.0,
        status_code=200,
    )

    assert edge.source_id == "resource-1"
    assert edge.target_id == "resource-2"
    assert edge.protocol == "https"
    assert edge.duration_ms == 100.0
    assert edge.status_code == 200


def test_transaction_flow_visualization_creation():
    """Test TransactionFlowVisualization creation."""
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(seconds=1)

    flow = TransactionFlowVisualization(
        transaction_id="test-id",
        start_time=start_time,
        end_time=end_time,
        total_duration_ms=1000.0,
        nodes=[],
        edges=[],
        status="success",
        error_count=0,
        warning_count=0,
        source="loki",
        metadata={"key": "value"},
    )

    assert flow.transaction_id == "test-id"
    assert flow.start_time == start_time
    assert flow.end_time == end_time
    assert flow.total_duration_ms == 1000.0
    assert flow.status == "success"
    assert flow.error_count == 0
    assert flow.warning_count == 0
    assert flow.source == "loki"
    assert flow.metadata == {"key": "value"}
