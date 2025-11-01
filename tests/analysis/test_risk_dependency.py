"""Tests for dependency analyzer module."""

from unittest.mock import MagicMock, Mock

import pytest

from topdeck.analysis.risk.dependency import DependencyAnalyzer


@pytest.fixture
def mock_neo4j_client():
    """Create a mock Neo4j client."""
    client = Mock()
    client.session = MagicMock()
    return client


@pytest.fixture
def dependency_analyzer(mock_neo4j_client):
    """Create a dependency analyzer with mock client."""
    return DependencyAnalyzer(mock_neo4j_client)


def test_dependency_analyzer_initialization(dependency_analyzer, mock_neo4j_client):
    """Test dependency analyzer initialization."""
    assert dependency_analyzer.neo4j_client == mock_neo4j_client


def test_get_dependency_counts(dependency_analyzer, mock_neo4j_client):
    """Test getting dependency counts."""
    # Mock session and query results
    mock_session = MagicMock()
    mock_result_upstream = MagicMock()
    mock_result_upstream.single.return_value = {"count": 3}
    mock_result_downstream = MagicMock()
    mock_result_downstream.single.return_value = {"count": 5}

    mock_session.run.side_effect = [mock_result_upstream, mock_result_downstream]
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session

    dependencies, dependents = dependency_analyzer.get_dependency_counts("resource-1")

    assert dependencies == 3
    assert dependents == 5
    assert mock_session.run.call_count == 2


def test_get_dependency_counts_no_dependencies(dependency_analyzer, mock_neo4j_client):
    """Test getting dependency counts when none exist."""
    # Mock empty results
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single.return_value = {"count": 0}

    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session

    dependencies, dependents = dependency_analyzer.get_dependency_counts("resource-1")

    assert dependencies == 0
    assert dependents == 0


def test_find_critical_path(dependency_analyzer, mock_neo4j_client):
    """Test finding critical dependency path."""
    # Mock query result with path
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single.return_value = {
        "path_ids": ["resource-1", "resource-2", "resource-3", "resource-4"]
    }

    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session

    path = dependency_analyzer.find_critical_path("resource-1")

    assert len(path) == 4
    assert path == ["resource-1", "resource-2", "resource-3", "resource-4"]


def test_find_critical_path_no_dependents(dependency_analyzer, mock_neo4j_client):
    """Test critical path when no dependents exist."""
    # Mock empty result
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single.return_value = None

    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session

    path = dependency_analyzer.find_critical_path("resource-1")

    assert path == ["resource-1"]


def test_get_dependency_tree_downstream(dependency_analyzer, mock_neo4j_client):
    """Test getting downstream dependency tree."""
    # Mock query results
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.__iter__.return_value = [
        {
            "source_id": "resource-1",
            "source_name": "Resource 1",
            "source_type": "web_app",
            "target_id": "resource-2",
            "target_name": "Resource 2",
            "target_type": "database",
        },
        {
            "source_id": "resource-2",
            "source_name": "Resource 2",
            "source_type": "database",
            "target_id": "resource-3",
            "target_name": "Resource 3",
            "target_type": "storage",
        },
    ]

    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session

    tree = dependency_analyzer.get_dependency_tree("resource-1", direction="downstream")

    assert "resource-1" in tree
    assert len(tree["resource-1"]) == 1
    assert tree["resource-1"][0]["id"] == "resource-2"
    assert "resource-2" in tree
    assert len(tree["resource-2"]) == 1


def test_get_dependency_tree_upstream(dependency_analyzer, mock_neo4j_client):
    """Test getting upstream dependency tree."""
    # Mock query results
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.__iter__.return_value = [
        {
            "source_id": "resource-1",
            "source_name": "Resource 1",
            "source_type": "web_app",
            "target_id": "resource-2",
            "target_name": "Resource 2",
            "target_type": "database",
        },
    ]

    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session

    tree = dependency_analyzer.get_dependency_tree("resource-1", direction="upstream")

    assert "resource-1" in tree


def test_is_single_point_of_failure_true(dependency_analyzer, mock_neo4j_client):
    """Test SPOF detection when resource is a SPOF."""
    # Mock result: has dependents, no redundancy
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single.return_value = {"is_spof": True}

    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session

    is_spof = dependency_analyzer.is_single_point_of_failure("resource-1")

    assert is_spof is True


def test_is_single_point_of_failure_false_no_dependents(dependency_analyzer, mock_neo4j_client):
    """Test SPOF detection when resource has no dependents."""
    # Mock result: no dependents
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single.return_value = {"is_spof": False}

    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session

    is_spof = dependency_analyzer.is_single_point_of_failure("resource-1")

    assert is_spof is False


def test_is_single_point_of_failure_false_has_redundancy(dependency_analyzer, mock_neo4j_client):
    """Test SPOF detection when resource has redundancy."""
    # Mock result: has dependents but also has redundancy
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single.return_value = {"is_spof": False}

    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session

    is_spof = dependency_analyzer.is_single_point_of_failure("resource-1")

    assert is_spof is False


def test_get_affected_resources(dependency_analyzer, mock_neo4j_client):
    """Test getting affected resources."""
    # Mock session with two queries
    mock_session = MagicMock()

    # Direct dependents
    mock_result_direct = MagicMock()
    mock_result_direct.__iter__.return_value = [
        {
            "id": "resource-2",
            "name": "Resource 2",
            "type": "web_app",
            "cloud_provider": "azure",
        },
        {
            "id": "resource-3",
            "name": "Resource 3",
            "type": "api",
            "cloud_provider": "azure",
        },
    ]

    # Indirect dependents
    mock_result_indirect = MagicMock()
    mock_result_indirect.__iter__.return_value = [
        {
            "id": "resource-4",
            "name": "Resource 4",
            "type": "function",
            "cloud_provider": "azure",
            "distance": 2,
        },
    ]

    mock_session.run.side_effect = [mock_result_direct, mock_result_indirect]
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session

    directly_affected, indirectly_affected = dependency_analyzer.get_affected_resources(
        "resource-1"
    )

    assert len(directly_affected) == 2
    assert len(indirectly_affected) == 1
    assert directly_affected[0]["id"] == "resource-2"
    assert indirectly_affected[0]["id"] == "resource-4"
    assert "distance" in indirectly_affected[0]


def test_get_affected_resources_none(dependency_analyzer, mock_neo4j_client):
    """Test getting affected resources when none exist."""
    # Mock empty results
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.__iter__.return_value = []

    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session

    directly_affected, indirectly_affected = dependency_analyzer.get_affected_resources(
        "resource-1"
    )

    assert len(directly_affected) == 0
    assert len(indirectly_affected) == 0


def test_detect_circular_dependencies_for_resource(dependency_analyzer, mock_neo4j_client):
    """Test detecting circular dependencies for a specific resource."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    
    # Mock a circular dependency: A -> B -> C -> A
    mock_result.__iter__.return_value = [
        {"cycle": ["resource-a", "resource-b", "resource-c", "resource-a"]},
        {"cycle": ["resource-a", "resource-d", "resource-a"]},
    ]
    
    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session
    
    cycles = dependency_analyzer.detect_circular_dependencies("resource-a")
    
    assert len(cycles) == 2
    assert mock_session.run.call_count == 1


def test_detect_circular_dependencies_all(dependency_analyzer, mock_neo4j_client):
    """Test detecting all circular dependencies in graph."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    
    # Mock multiple cycles
    mock_result.__iter__.return_value = [
        {"cycle": ["res-1", "res-2", "res-3", "res-1"]},
        {"cycle": ["res-4", "res-5", "res-4"]},
    ]
    
    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session
    
    cycles = dependency_analyzer.detect_circular_dependencies()
    
    assert len(cycles) == 2
    assert mock_session.run.call_count == 1


def test_detect_circular_dependencies_none_found(dependency_analyzer, mock_neo4j_client):
    """Test detecting circular dependencies when none exist."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.__iter__.return_value = []
    
    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session
    
    cycles = dependency_analyzer.detect_circular_dependencies("resource-1")
    
    assert len(cycles) == 0


def test_get_dependency_health_score_healthy(dependency_analyzer, mock_neo4j_client):
    """Test dependency health score for healthy resource."""
    # Mock minimal dependencies, no circular deps, no SPOFs
    mock_session = MagicMock()
    
    # Mock get_dependency_counts
    mock_count_result_upstream = MagicMock()
    mock_count_result_upstream.single.return_value = {"count": 3}
    mock_count_result_downstream = MagicMock()
    mock_count_result_downstream.single.return_value = {"count": 2}
    
    # Mock detect_circular_dependencies (no cycles)
    mock_circular_result = MagicMock()
    mock_circular_result.__iter__.return_value = []
    
    # Mock get_dependency_tree
    mock_tree_result = MagicMock()
    mock_tree_result.__iter__.return_value = []
    
    # Mock max depth query
    mock_depth_result = MagicMock()
    mock_depth_result.single.return_value = {"max_depth": 2}
    
    mock_session.run.side_effect = [
        mock_count_result_upstream,
        mock_count_result_downstream,
        mock_circular_result,
        mock_tree_result,
        mock_depth_result,
    ]
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session
    
    health = dependency_analyzer.get_dependency_health_score("resource-1")
    
    assert health["health_score"] == 100.0
    assert health["health_level"] == "excellent"
    assert len(health["factors"]) == 0
    assert "✅" in health["recommendations"][0]


def test_get_dependency_health_score_with_issues(dependency_analyzer, mock_neo4j_client):
    """Test dependency health score with various issues."""
    mock_session = MagicMock()
    
    # Mock high dependency count
    mock_count_result_upstream = MagicMock()
    mock_count_result_upstream.single.return_value = {"count": 15}
    mock_count_result_downstream = MagicMock()
    mock_count_result_downstream.single.return_value = {"count": 2}
    
    # Mock circular dependency
    mock_circular_result = MagicMock()
    mock_circular_result.__iter__.return_value = [
        {"cycle": ["res-1", "res-2", "res-1"]},
    ]
    
    # Mock dependency tree
    mock_tree_result = MagicMock()
    mock_tree_result.__iter__.return_value = []
    
    # Mock depth
    mock_depth_result = MagicMock()
    mock_depth_result.single.return_value = {"max_depth": 7}
    
    mock_session.run.side_effect = [
        mock_count_result_upstream,
        mock_count_result_downstream,
        mock_circular_result,
        mock_tree_result,
        mock_depth_result,
    ]
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session
    
    health = dependency_analyzer.get_dependency_health_score("resource-1")
    
    assert health["health_score"] < 100.0
    assert "high_dependency_count" in health["factors"]
    assert "circular_dependencies" in health["factors"]
    assert "deep_dependency_tree" in health["factors"]
    assert any("circular" in rec.lower() for rec in health["recommendations"])
