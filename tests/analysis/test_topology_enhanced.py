"""Tests for enhanced topology analysis features."""

import pytest
from unittest.mock import Mock, MagicMock
from topdeck.analysis.topology import (
    TopologyService,
    ResourceAttachment,
    DependencyChain,
    ResourceAttachmentAnalysis,
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


def test_get_resource_attachments_upstream(topology_service, mock_neo4j_client):
    """Test getting upstream resource attachments."""
    # Mock the session and query result
    mock_session = MagicMock()
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session
    
    mock_result = Mock()
    mock_result.__iter__ = Mock(return_value=iter([
        {
            "source_id": "resource-1",
            "source_name": "app-service",
            "source_type": "app_service",
            "target_id": "resource-2",
            "target_name": "sql-db",
            "target_type": "sql_database",
            "relationship_type": "DEPENDS_ON",
            "rel_properties": {"port": 1433, "protocol": "tcp"},
        }
    ]))
    mock_session.run.return_value = mock_result
    
    attachments = topology_service.get_resource_attachments("resource-1", direction="upstream")
    
    assert len(attachments) == 1
    assert attachments[0].source_id == "resource-1"
    assert attachments[0].target_id == "resource-2"
    assert attachments[0].relationship_type == "DEPENDS_ON"
    assert "port" in attachments[0].relationship_properties


def test_get_resource_attachments_downstream(topology_service, mock_neo4j_client):
    """Test getting downstream resource attachments."""
    mock_session = MagicMock()
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session
    
    mock_result = Mock()
    mock_result.__iter__ = Mock(return_value=iter([
        {
            "source_id": "resource-3",
            "source_name": "pod",
            "source_type": "pod",
            "target_id": "resource-1",
            "target_name": "app-service",
            "target_type": "app_service",
            "relationship_type": "CONNECTS_TO",
            "rel_properties": {"endpoint": "http://app-service:80"},
        }
    ]))
    mock_session.run.return_value = mock_result
    
    attachments = topology_service.get_resource_attachments("resource-1", direction="downstream")
    
    assert len(attachments) == 1
    assert attachments[0].source_id == "resource-3"
    assert attachments[0].target_id == "resource-1"
    assert attachments[0].relationship_type == "CONNECTS_TO"


def test_get_resource_attachments_both_directions(topology_service, mock_neo4j_client):
    """Test getting attachments in both directions."""
    mock_session = MagicMock()
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session
    
    # Mock two separate query results (upstream and downstream)
    mock_upstream_result = Mock()
    mock_upstream_result.__iter__ = Mock(return_value=iter([
        {
            "source_id": "resource-1",
            "source_name": "app",
            "source_type": "app",
            "target_id": "resource-2",
            "target_name": "db",
            "target_type": "database",
            "relationship_type": "DEPENDS_ON",
            "rel_properties": {},
        }
    ]))
    
    mock_downstream_result = Mock()
    mock_downstream_result.__iter__ = Mock(return_value=iter([
        {
            "source_id": "resource-3",
            "source_name": "lb",
            "source_type": "load_balancer",
            "target_id": "resource-1",
            "target_name": "app",
            "target_type": "app",
            "relationship_type": "ROUTES_TO",
            "rel_properties": {},
        }
    ]))
    
    mock_session.run.side_effect = [mock_upstream_result, mock_downstream_result]
    
    attachments = topology_service.get_resource_attachments("resource-1", direction="both")
    
    assert len(attachments) == 2
    # Verify both upstream and downstream were called
    assert mock_session.run.call_count == 2


def test_build_attachment_context(topology_service):
    """Test building attachment context."""
    properties = {
        "port": 443,
        "protocol": "https",
        "endpoint": "https://api.example.com"
    }
    
    context = topology_service._build_attachment_context("CONNECTS_TO", properties)
    
    assert "port" in context
    assert context["port"] == 443
    assert "protocol" in context
    assert context["protocol"] == "https"
    assert "endpoint" in context
    assert "relationship_category" in context
    assert "is_critical" in context


def test_categorize_relationship(topology_service):
    """Test relationship categorization."""
    assert topology_service._categorize_relationship("DEPENDS_ON") == "dependency"
    assert topology_service._categorize_relationship("USES") == "dependency"
    assert topology_service._categorize_relationship("CONNECTS_TO") == "connectivity"
    assert topology_service._categorize_relationship("ROUTES_TO") == "connectivity"
    assert topology_service._categorize_relationship("DEPLOYED_TO") == "deployment"
    assert topology_service._categorize_relationship("AUTHENTICATES_WITH") == "security"
    assert topology_service._categorize_relationship("CUSTOM_REL") == "other"


def test_is_critical_attachment(topology_service):
    """Test critical attachment detection."""
    assert topology_service._is_critical_attachment("DEPENDS_ON") is True
    assert topology_service._is_critical_attachment("AUTHENTICATES_WITH") is True
    assert topology_service._is_critical_attachment("ROUTES_TO") is True
    assert topology_service._is_critical_attachment("CONNECTS_TO") is True
    assert topology_service._is_critical_attachment("USES") is False
    assert topology_service._is_critical_attachment("CUSTOM") is False


def test_get_dependency_chains_downstream(topology_service, mock_neo4j_client):
    """Test getting downstream dependency chains."""
    mock_session = MagicMock()
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session
    
    mock_result = Mock()
    mock_result.__iter__ = Mock(return_value=iter([
        {
            "ids": ["resource-1", "resource-2", "resource-3"],
            "names": ["app", "service", "database"],
            "types": ["app", "service", "database"],
            "rels": ["DEPENDS_ON", "USES"],
            "chain_length": 2,
        }
    ]))
    mock_session.run.return_value = mock_result
    
    chains = topology_service.get_dependency_chains("resource-1", direction="downstream")
    
    assert len(chains) == 1
    assert chains[0].chain_length == 2
    assert len(chains[0].resource_ids) == 3
    assert chains[0].metadata["direction"] == "downstream"


def test_get_dependency_chains_upstream(topology_service, mock_neo4j_client):
    """Test getting upstream dependency chains."""
    mock_session = MagicMock()
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session
    
    mock_result = Mock()
    mock_result.__iter__ = Mock(return_value=iter([
        {
            "ids": ["resource-1", "resource-0"],
            "names": ["app", "config"],
            "types": ["app", "config"],
            "rels": ["READS_FROM"],
            "chain_length": 1,
        }
    ]))
    mock_session.run.return_value = mock_result
    
    chains = topology_service.get_dependency_chains("resource-1", direction="upstream")
    
    assert len(chains) == 1
    assert chains[0].metadata["direction"] == "upstream"


def test_get_attachment_analysis(topology_service, mock_neo4j_client):
    """Test comprehensive attachment analysis."""
    mock_session = MagicMock()
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session
    
    # Mock resource query
    mock_resource_result = Mock()
    mock_resource_result.single.return_value = {
        "name": "test-app",
        "type": "app_service"
    }
    
    # Mock attachments (both directions)
    mock_upstream_result = Mock()
    mock_upstream_result.__iter__ = Mock(return_value=iter([
        {
            "source_id": "resource-1",
            "source_name": "app",
            "source_type": "app",
            "target_id": "resource-2",
            "target_name": "db",
            "target_type": "database",
            "relationship_type": "DEPENDS_ON",
            "rel_properties": {},
        }
    ]))
    
    mock_downstream_result = Mock()
    mock_downstream_result.__iter__ = Mock(return_value=iter([]))
    
    # Mock chains
    mock_chains_down = Mock()
    mock_chains_down.__iter__ = Mock(return_value=iter([
        {
            "ids": ["resource-1", "resource-2"],
            "names": ["app", "db"],
            "types": ["app", "database"],
            "rels": ["DEPENDS_ON"],
            "chain_length": 1,
        }
    ]))
    
    mock_chains_up = Mock()
    mock_chains_up.__iter__ = Mock(return_value=iter([]))
    
    # Mock impact radius
    mock_radius_result = Mock()
    mock_radius_result.single.return_value = {"radius": 5}
    
    mock_session.run.side_effect = [
        mock_resource_result,
        mock_upstream_result,
        mock_downstream_result,
        mock_chains_down,
        mock_chains_up,
        mock_radius_result,
    ]
    
    analysis = topology_service.get_attachment_analysis("resource-1")
    
    assert analysis.resource_id == "resource-1"
    assert analysis.resource_name == "test-app"
    assert analysis.resource_type == "app_service"
    assert analysis.total_attachments == 1
    assert "DEPENDS_ON" in analysis.attachment_by_type
    assert analysis.impact_radius == 5
    assert len(analysis.dependency_chains) == 1


def test_get_attachment_analysis_resource_not_found(topology_service, mock_neo4j_client):
    """Test attachment analysis with non-existent resource."""
    mock_session = MagicMock()
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session
    
    mock_resource_result = Mock()
    mock_resource_result.single.return_value = None
    mock_session.run.return_value = mock_resource_result
    
    with pytest.raises(ValueError, match="Resource .* not found"):
        topology_service.get_attachment_analysis("non-existent")


def test_attachment_strength_calculation(topology_service, mock_neo4j_client):
    """Test that attachment strength is calculated correctly."""
    mock_session = MagicMock()
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session
    
    # Mock resource
    mock_resource_result = Mock()
    mock_resource_result.single.return_value = {
        "name": "test-app",
        "type": "app_service"
    }
    
    # Mock attachments with critical and non-critical
    mock_upstream_result = Mock()
    mock_upstream_result.__iter__ = Mock(return_value=iter([
        {
            "source_id": "resource-1",
            "source_name": "app",
            "source_type": "app",
            "target_id": "resource-2",
            "target_name": "db",
            "target_type": "database",
            "relationship_type": "DEPENDS_ON",  # Critical
            "rel_properties": {"connection": "string"},
        },
        {
            "source_id": "resource-1",
            "source_name": "app",
            "source_type": "app",
            "target_id": "resource-3",
            "target_name": "cache",
            "target_type": "cache",
            "relationship_type": "USES",  # Non-critical
            "rel_properties": {},
        }
    ]))
    
    mock_downstream_result = Mock()
    mock_downstream_result.__iter__ = Mock(return_value=iter([]))
    
    mock_chains_down = Mock()
    mock_chains_down.__iter__ = Mock(return_value=iter([]))
    
    mock_chains_up = Mock()
    mock_chains_up.__iter__ = Mock(return_value=iter([]))
    
    mock_radius_result = Mock()
    mock_radius_result.single.return_value = {"radius": 2}
    
    mock_session.run.side_effect = [
        mock_resource_result,
        mock_upstream_result,
        mock_downstream_result,
        mock_chains_down,
        mock_chains_up,
        mock_radius_result,
    ]
    
    analysis = topology_service.get_attachment_analysis("resource-1")
    
    # Critical attachment should have higher strength
    assert "DEPENDS_ON" in analysis.attachment_strength
    assert "USES" in analysis.attachment_strength
    assert analysis.attachment_strength["DEPENDS_ON"] > analysis.attachment_strength["USES"]
    
    # Critical attachment should be in critical list
    assert len(analysis.critical_attachments) == 1
    assert analysis.critical_attachments[0].relationship_type == "DEPENDS_ON"
