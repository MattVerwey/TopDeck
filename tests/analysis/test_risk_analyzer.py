"""Tests for main risk analyzer module."""

from unittest.mock import MagicMock, Mock

import pytest

from topdeck.analysis.risk.analyzer import RiskAnalyzer


@pytest.fixture
def mock_neo4j_client():
    """Create a mock Neo4j client."""
    client = Mock()
    client.session = MagicMock()
    return client


@pytest.fixture
def risk_analyzer(mock_neo4j_client):
    """Create a risk analyzer with mock Neo4j client."""
    return RiskAnalyzer(mock_neo4j_client)


def test_risk_analyzer_initialization(risk_analyzer, mock_neo4j_client):
    """Test risk analyzer initialization."""
    assert risk_analyzer.neo4j_client == mock_neo4j_client
    assert risk_analyzer.dependency_analyzer is not None
    assert risk_analyzer.risk_scorer is not None
    assert risk_analyzer.impact_analyzer is not None
    assert risk_analyzer.failure_simulator is not None


def test_analyze_resource_not_found(risk_analyzer, mock_neo4j_client):
    """Test analyzing a resource that doesn't exist."""
    # Mock empty result
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single.return_value = None

    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session

    with pytest.raises(ValueError, match="not found"):
        risk_analyzer.analyze_resource("nonexistent-resource")


def test_get_resource_details_success(risk_analyzer, mock_neo4j_client):
    """Test getting resource details."""
    # Mock successful query
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single.return_value = {
        "id": "resource-1",
        "name": "Test Resource",
        "resource_type": "web_app",
        "cloud_provider": "azure",
        "region": "eastus",
    }

    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session

    resource = risk_analyzer._get_resource_details("resource-1")

    assert resource is not None
    assert resource["id"] == "resource-1"
    assert resource["name"] == "Test Resource"
    assert resource["resource_type"] == "web_app"


def test_get_resource_details_not_found(risk_analyzer, mock_neo4j_client):
    """Test getting details for nonexistent resource."""
    # Mock empty result
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single.return_value = None

    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session

    resource = risk_analyzer._get_resource_details("nonexistent")

    assert resource is None


def test_check_redundancy_true(risk_analyzer, mock_neo4j_client):
    """Test checking redundancy when it exists."""
    # Mock result with redundancy
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single.return_value = {"redundant_count": 2}

    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session

    has_redundancy = risk_analyzer._check_redundancy("resource-1")

    assert has_redundancy is True


def test_check_redundancy_false(risk_analyzer, mock_neo4j_client):
    """Test checking redundancy when none exists."""
    # Mock result with no redundancy
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single.return_value = {"redundant_count": 0}

    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session

    has_redundancy = risk_analyzer._check_redundancy("resource-1")

    assert has_redundancy is False


def test_get_change_risk_score(risk_analyzer, mock_neo4j_client):
    """Test getting change risk score."""
    # Mock all required data
    mock_session = MagicMock()

    # Resource details
    mock_result_resource = MagicMock()
    mock_result_resource.single.return_value = {
        "id": "resource-1",
        "name": "Test Resource",
        "resource_type": "web_app",
        "cloud_provider": "azure",
        "region": "eastus",
    }

    # Dependencies
    mock_result_deps = MagicMock()
    mock_result_deps.single.return_value = {"count": 5}

    # SPOF check
    mock_result_spof = MagicMock()
    mock_result_spof.single.return_value = {"is_spof": False}

    # Redundancy check
    mock_result_redundancy = MagicMock()
    mock_result_redundancy.single.return_value = {"redundant_count": 1}

    # Affected resources for blast radius
    mock_result_direct = MagicMock()
    mock_result_direct.__iter__.return_value = [
        {"id": "r1", "name": "R1", "type": "api", "cloud_provider": "azure"}
    ]

    mock_result_indirect = MagicMock()
    mock_result_indirect.__iter__.return_value = []

    # Critical path
    mock_result_path = MagicMock()
    mock_result_path.single.return_value = {"path_ids": ["resource-1", "r1"]}

    # Setup session to return appropriate results for each query
    mock_session.run.side_effect = [
        mock_result_resource,  # get resource details
        mock_result_deps,  # upstream dependencies
        mock_result_deps,  # downstream dependents
        mock_result_spof,  # is SPOF check
        mock_result_direct,  # directly affected
        mock_result_indirect,  # indirectly affected
        mock_result_path,  # critical path
        mock_result_redundancy,  # redundancy check
    ]

    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session

    score = risk_analyzer.get_change_risk_score("resource-1")

    assert isinstance(score, float)
    assert 0 <= score <= 100


def test_identify_single_points_of_failure(risk_analyzer, mock_neo4j_client):
    """Test identifying SPOFs."""
    # Mock query results
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.__iter__.return_value = [
        {
            "id": "resource-1",
            "name": "Critical Database",
            "resource_type": "database",
            "dependents_count": 10,
        },
        {
            "id": "resource-2",
            "name": "API Gateway",
            "resource_type": "api_gateway",
            "dependents_count": 8,
        },
    ]

    # Mock blast radius queries for each SPOF
    mock_result_direct = MagicMock()
    mock_result_direct.__iter__.return_value = []

    mock_result_indirect = MagicMock()
    mock_result_indirect.__iter__.return_value = []

    mock_result_path = MagicMock()
    mock_result_path.single.return_value = {"path_ids": ["resource-1"]}

    mock_session.run.side_effect = [
        mock_result,  # Main SPOF query
        # First SPOF blast radius
        mock_result_direct,
        mock_result_indirect,
        mock_result_path,
        # Second SPOF blast radius
        mock_result_direct,
        mock_result_indirect,
        mock_result_path,
    ]

    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session

    spofs = risk_analyzer.identify_single_points_of_failure()

    assert len(spofs) == 2
    assert spofs[0].resource_id == "resource-1"
    assert spofs[0].dependents_count == 10
    assert spofs[1].resource_id == "resource-2"
    assert spofs[1].dependents_count == 8
    assert all(spof.risk_score >= 0 for spof in spofs)
    assert all(spof.recommendations for spof in spofs)


def test_identify_single_points_of_failure_none_found(risk_analyzer, mock_neo4j_client):
    """Test identifying SPOFs when none exist."""
    # Mock empty result
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.__iter__.return_value = []

    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session

    spofs = risk_analyzer.identify_single_points_of_failure()

    assert len(spofs) == 0


def test_compare_risk_scores_multiple_resources(risk_analyzer, mock_neo4j_client):
    """Test comparing risk scores across multiple resources."""
    mock_session = MagicMock()

    # Mock resource details for 3 resources
    resource_details = [
        {
            "id": "res-1",
            "name": "Database A",
            "resource_type": "database",
            "cloud_provider": "azure",
            "region": "eastus",
        },
        {
            "id": "res-2",
            "name": "Database B",
            "resource_type": "database",
            "cloud_provider": "azure",
            "region": "westus",
        },
        {
            "id": "res-3",
            "name": "Web App",
            "resource_type": "web_app",
            "cloud_provider": "azure",
            "region": "eastus",
        },
    ]

    # Mock dependency counts
    dependency_counts = [(3, 5), (2, 3), (5, 1)]

    # Mock SPOF checks
    spof_results = [True, False, False]

    # Mock redundancy checks
    redundancy_results = [{"redundant_count": 0}, {"redundant_count": 1}, {"redundant_count": 0}]

    call_index = [0]

    def mock_run_side_effect(*args, **kwargs):
        idx = call_index[0]
        call_index[0] += 1

        # Resource details queries (3x)
        if idx < 3:
            mock_result = MagicMock()
            mock_result.single.return_value = resource_details[idx]
            return mock_result

        # Dependency counts (6 queries, 2 per resource)
        elif idx < 9:
            dep_idx = (idx - 3) // 2
            count_type = (idx - 3) % 2
            mock_result = MagicMock()
            mock_result.single.return_value = {"count": dependency_counts[dep_idx][count_type]}
            return mock_result

        # SPOF checks (3x)
        elif idx < 12:
            spof_idx = idx - 9
            mock_result = MagicMock()
            mock_result.single.return_value = {"is_spof": spof_results[spof_idx]}
            return mock_result

        # Redundancy checks (3x)
        elif idx < 15:
            red_idx = idx - 12
            mock_result = MagicMock()
            mock_result.single.return_value = redundancy_results[red_idx]
            return mock_result

        # Blast radius queries (3x, minimal mocking)
        else:
            mock_result = MagicMock()
            mock_result.__iter__.return_value = []
            return mock_result

    mock_session.run.side_effect = mock_run_side_effect
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session

    comparison = risk_analyzer.compare_risk_scores(["res-1", "res-2", "res-3"])

    assert comparison["resources_compared"] == 3
    assert "average_risk_score" in comparison
    assert "highest_risk" in comparison
    assert "lowest_risk" in comparison
    assert "risk_distribution" in comparison
    assert comparison["highest_risk"]["resource_id"] in ["res-1", "res-2", "res-3"]


def test_compare_risk_scores_empty_list(risk_analyzer, mock_neo4j_client):
    """Test comparing risk scores with empty resource list."""
    comparison = risk_analyzer.compare_risk_scores([])

    assert comparison["resources_compared"] == 0
    assert "error" in comparison


def test_calculate_cascading_failure_probability(risk_analyzer, mock_neo4j_client):
    """Test cascading failure probability calculation."""
    mock_session = MagicMock()

    # Mock dependency tree
    # Resource 1 -> Resource 2, Resource 3
    # Resource 2 -> Resource 4
    mock_tree_result = MagicMock()
    mock_tree_result.__iter__.return_value = [
        {
            "source_id": "res-1",
            "source_name": "App",
            "source_type": "web_app",
            "target_id": "res-2",
            "target_name": "Database",
            "target_type": "database",
        },
        {
            "source_id": "res-1",
            "source_name": "App",
            "source_type": "web_app",
            "target_id": "res-3",
            "target_name": "Cache",
            "target_type": "cache",
        },
        {
            "source_id": "res-2",
            "source_name": "Database",
            "source_type": "database",
            "target_id": "res-4",
            "target_name": "Storage",
            "target_type": "storage",
        },
    ]

    mock_session.run.return_value = mock_tree_result
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session

    analysis = risk_analyzer.calculate_cascading_failure_probability("res-1", 1.0)

    assert "initial_resource" in analysis
    assert analysis["initial_resource"] == "res-1"
    assert analysis["initial_failure_probability"] == 1.0
    assert "levels" in analysis
    assert len(analysis["levels"]) > 0
    assert "summary" in analysis
    assert "max_cascade_depth" in analysis["summary"]
    assert "total_resources_at_risk" in analysis["summary"]
    assert "recommendations" in analysis["summary"]


def test_calculate_cascading_failure_probability_no_dependencies(risk_analyzer, mock_neo4j_client):
    """Test cascading failure when resource has no dependencies."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.__iter__.return_value = []

    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value.__enter__.return_value = mock_session

    analysis = risk_analyzer.calculate_cascading_failure_probability("res-1", 1.0)

    assert analysis["initial_resource"] == "res-1"
    assert len(analysis["levels"]) == 0
    assert analysis["summary"]["total_resources_at_risk"] == 0
