"""
Tests for enhanced impact analysis.
"""

import pytest
from unittest.mock import MagicMock, Mock

from topdeck.analysis.risk.enhanced_impact import EnhancedImpactAnalyzer
from topdeck.analysis.risk.models import (
    ImpactLevel,
    ResourceCategory,
)


@pytest.fixture
def mock_neo4j_client():
    """Create a mock Neo4j client."""
    return Mock()


@pytest.fixture
def mock_dependency_analyzer():
    """Create a mock dependency analyzer."""
    return Mock()


@pytest.fixture
def enhanced_impact_analyzer(mock_neo4j_client, mock_dependency_analyzer):
    """Create an enhanced impact analyzer."""
    return EnhancedImpactAnalyzer(mock_neo4j_client, mock_dependency_analyzer)


@pytest.fixture
def mock_neo4j_session():
    """Create a reusable mock Neo4j session with context manager support."""
    mock_session = MagicMock()
    return MagicMock(__enter__=lambda self: mock_session, __exit__=lambda self, *args: None), mock_session


def test_analyze_downstream_impact_no_dependencies(
    enhanced_impact_analyzer, mock_dependency_analyzer
):
    """Test downstream impact with no affected resources."""
    # Mock no affected resources
    mock_dependency_analyzer.get_affected_resources.return_value = ([], [])

    result = enhanced_impact_analyzer.analyze_downstream_impact("resource-1", "Test Resource")

    assert result.resource_id == "resource-1"
    assert result.resource_name == "Test Resource"
    assert result.total_affected == 0
    assert result.user_facing_impact == "No direct user-facing services affected"
    assert result.backend_impact == "No backend services affected"
    assert result.data_impact == "No data stores directly affected"


def test_analyze_downstream_impact_with_user_facing_services(
    enhanced_impact_analyzer, mock_dependency_analyzer
):
    """Test downstream impact with user-facing services."""
    # Mock affected resources
    affected = [
        {"id": "web-1", "name": "Web App", "type": "web_app", "is_critical": True},
        {"id": "api-1", "name": "API Gateway", "type": "api_gateway", "is_critical": True},
    ]
    mock_dependency_analyzer.get_affected_resources.return_value = (affected, [])

    result = enhanced_impact_analyzer.analyze_downstream_impact("resource-1", "Test Resource")

    assert result.resource_id == "resource-1"
    assert result.total_affected == 2
    assert ResourceCategory.USER_FACING in result.affected_by_category
    assert len(result.affected_by_category[ResourceCategory.USER_FACING]) == 2
    assert len(result.critical_services_affected) == 2
    assert "user-facing services affected" in result.user_facing_impact


def test_analyze_downstream_impact_with_data_stores(
    enhanced_impact_analyzer, mock_dependency_analyzer
):
    """Test downstream impact with data stores."""
    # Mock affected resources
    affected = [
        {"id": "db-1", "name": "SQL Database", "type": "database", "is_critical": True},
        {"id": "cache-1", "name": "Redis Cache", "type": "redis", "is_critical": False},
    ]
    mock_dependency_analyzer.get_affected_resources.return_value = (affected, [])

    result = enhanced_impact_analyzer.analyze_downstream_impact("resource-1", "Test Resource")

    assert result.total_affected == 2
    assert ResourceCategory.DATA_STORE in result.affected_by_category
    assert len(result.affected_by_category[ResourceCategory.DATA_STORE]) == 2
    assert "data stores affected" in result.data_impact


def test_analyze_upstream_dependencies_no_dependencies(
    enhanced_impact_analyzer, mock_neo4j_client, mock_neo4j_session
):
    """Test upstream dependencies with no dependencies."""
    # Mock empty dependencies
    mock_context, mock_session = mock_neo4j_session
    mock_result = MagicMock()
    mock_result.__iter__.return_value = iter([])
    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value = mock_context

    result = enhanced_impact_analyzer.analyze_upstream_dependencies("resource-1", "Test Resource")

    assert result.resource_id == "resource-1"
    assert result.total_dependencies == 0
    assert result.dependency_health_score == 100.0
    assert any("dependencies appear healthy" in rec.lower() for rec in result.recommendations)


def test_analyze_upstream_dependencies_with_healthy_deps(
    enhanced_impact_analyzer, mock_neo4j_client, mock_dependency_analyzer, mock_neo4j_session
):
    """Test upstream dependencies with healthy dependencies."""
    # Mock dependencies
    mock_context, mock_session = mock_neo4j_session
    mock_result = MagicMock()
    mock_result.__iter__.return_value = iter(
        [
            {
                "id": "db-1",
                "name": "Database",
                "type": "database",
                "relationship_type": "DEPENDS_ON",
                "is_critical": False,
                "risk_score": 30.0,
            },
            {
                "id": "cache-1",
                "name": "Cache",
                "type": "redis",
                "relationship_type": "USES",
                "is_critical": False,
                "risk_score": 20.0,
            },
        ]
    )
    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value = mock_context
    mock_dependency_analyzer.is_single_point_of_failure.return_value = False

    result = enhanced_impact_analyzer.analyze_upstream_dependencies("resource-1", "Test Resource")

    assert result.total_dependencies == 2
    assert result.dependency_health_score == 100.0
    assert len(result.unhealthy_dependencies) == 0
    assert len(result.single_points_of_failure) == 0


def test_analyze_upstream_dependencies_with_spof(
    enhanced_impact_analyzer, mock_neo4j_client, mock_dependency_analyzer, mock_neo4j_session
):
    """Test upstream dependencies with SPOF."""
    # Mock dependencies
    mock_context, mock_session = mock_neo4j_session
    mock_result = MagicMock()
    mock_result.__iter__.return_value = iter(
        [
            {
                "id": "db-1",
                "name": "Database",
                "type": "database",
                "relationship_type": "DEPENDS_ON",
                "is_critical": True,
                "risk_score": 30.0,
            },
        ]
    )
    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value = mock_context
    mock_dependency_analyzer.is_single_point_of_failure.return_value = True

    result = enhanced_impact_analyzer.analyze_upstream_dependencies("resource-1", "Test Resource")

    assert result.total_dependencies == 1
    assert len(result.single_points_of_failure) == 1
    assert result.dependency_health_score < 100.0
    assert any("single point" in rec.lower() for rec in result.recommendations)


def test_categorize_resource_web_app(enhanced_impact_analyzer):
    """Test resource categorization for web app."""
    resource = {"id": "web-1", "name": "Web App", "type": "web_app", "risk_score": 50}

    categorized = enhanced_impact_analyzer._categorize_resource(resource)

    assert categorized.category == ResourceCategory.USER_FACING
    assert categorized.impact_severity == ImpactLevel.HIGH
    assert categorized.is_critical is True


def test_categorize_resource_database(enhanced_impact_analyzer):
    """Test resource categorization for database."""
    resource = {"id": "db-1", "name": "Database", "type": "database", "risk_score": 40}

    categorized = enhanced_impact_analyzer._categorize_resource(resource)

    assert categorized.category == ResourceCategory.DATA_STORE
    assert categorized.impact_severity == ImpactLevel.HIGH
    assert categorized.is_critical is True


def test_categorize_resource_backend_service(enhanced_impact_analyzer):
    """Test resource categorization for backend service."""
    resource = {
        "id": "svc-1",
        "name": "Backend Service",
        "type": "service",
        "risk_score": 30,
    }

    categorized = enhanced_impact_analyzer._categorize_resource(resource)

    assert categorized.category == ResourceCategory.BACKEND_SERVICE
    assert categorized.impact_severity == ImpactLevel.MEDIUM


def test_analyze_what_if_scenario_failure(
    enhanced_impact_analyzer, mock_dependency_analyzer, mock_neo4j_client, mock_neo4j_session
):
    """Test what-if analysis for failure scenario."""
    # Mock affected resources (downstream)
    mock_dependency_analyzer.get_affected_resources.return_value = (
        [{"id": "web-1", "name": "Web App", "type": "web_app", "is_critical": True}],
        [],
    )

    # Mock dependencies (upstream)
    mock_context, mock_session = mock_neo4j_session
    mock_result = MagicMock()
    mock_result.__iter__.return_value = iter([])
    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value = mock_context

    result = enhanced_impact_analyzer.analyze_what_if_scenario(
        "resource-1", "Test Resource", "failure"
    )

    assert result.resource_id == "resource-1"
    assert result.scenario_type == "failure"
    assert result.timeline_minutes == 0  # Immediate for failure
    assert result.downstream_impact.total_affected == 1
    assert result.rollback_possible is False  # Can't rollback a failure


def test_analyze_what_if_scenario_update(
    enhanced_impact_analyzer, mock_dependency_analyzer, mock_neo4j_client, mock_neo4j_session
):
    """Test what-if analysis for update scenario."""
    # Mock affected resources (downstream)
    mock_dependency_analyzer.get_affected_resources.return_value = ([], [])

    # Mock dependencies (upstream)
    mock_context, mock_session = mock_neo4j_session
    mock_result = MagicMock()
    mock_result.__iter__.return_value = iter([])
    mock_session.run.return_value = mock_result
    mock_neo4j_client.session.return_value = mock_context

    result = enhanced_impact_analyzer.analyze_what_if_scenario(
        "resource-1", "Test Resource", "update"
    )

    assert result.scenario_type == "update"
    assert result.timeline_minutes == 30  # Gradual for update
    assert result.rollback_possible is True  # Can rollback updates


def test_calculate_dependency_health_score_perfect(enhanced_impact_analyzer):
    """Test health score calculation with no issues."""
    score = enhanced_impact_analyzer._calculate_dependency_health_score(5, [], [], [])
    assert score == 100.0


def test_calculate_dependency_health_score_with_issues(enhanced_impact_analyzer):
    """Test health score calculation with issues."""
    # Mock some issues
    unhealthy = [MagicMock()]  # 1 unhealthy out of 5
    spofs = [MagicMock()]  # 1 SPOF out of 5
    high_risk = [MagicMock()]  # 1 high risk out of 5

    score = enhanced_impact_analyzer._calculate_dependency_health_score(
        5, unhealthy, spofs, high_risk
    )

    # Should deduct: (1/5)*30 + (1/5)*40 + (1/5)*20 = 6 + 8 + 4 = 18
    assert score == pytest.approx(82.0, abs=0.1)


def test_estimate_users_affected(enhanced_impact_analyzer):
    """Test user estimation based on affected services."""
    from topdeck.analysis.risk.models import CategorizedResource

    affected = {
        ResourceCategory.USER_FACING: [
            CategorizedResource(
                "web-1",
                "Web",
                "web_app",
                ResourceCategory.USER_FACING,
                impact_severity=ImpactLevel.HIGH,
            ),
            CategorizedResource(
                "api-1",
                "API",
                "api_gateway",
                ResourceCategory.USER_FACING,
                impact_severity=ImpactLevel.HIGH,
            ),
        ],
        ResourceCategory.CLIENT_APP: [
            CategorizedResource(
                "client-1",
                "Client",
                "client_app",
                ResourceCategory.CLIENT_APP,
                impact_severity=ImpactLevel.MEDIUM,
            )
        ],
    }

    users = enhanced_impact_analyzer._estimate_users_affected(affected)

    # 2 user-facing * 1000 + 1 client * 500 = 2500
    assert users == 2500
