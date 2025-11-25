"""
Tests for improved change impact analysis.

This test validates that the change impact analysis now considers:
- Resource type characteristics
- Resource risk scores
- Number of dependencies
- Change type + resource type combinations
- Critical path status
"""

from unittest.mock import Mock, MagicMock
import pytest

from topdeck.change_management.models import ChangeRequest, ChangeStatus, ChangeType
from topdeck.change_management.service import ChangeManagementService
from topdeck.analysis.risk.models import RiskAssessment, RiskLevel


@pytest.fixture
def mock_neo4j_client():
    """Create a mock Neo4j client."""
    client = Mock()
    client.driver = Mock()
    client.driver.session = Mock()
    return client


@pytest.fixture
def mock_risk_analyzer():
    """Create a mock risk analyzer."""
    analyzer = Mock()
    return analyzer


@pytest.fixture
def change_service(mock_neo4j_client, mock_risk_analyzer):
    """Create a change management service with mocked dependencies."""
    service = ChangeManagementService(mock_neo4j_client)
    service.risk_analyzer = mock_risk_analyzer
    return service


def test_downtime_varies_by_resource_type(change_service):
    """Test that downtime estimation varies based on resource type."""
    # Database changes should take longer than function app changes
    # Using risk_score=0.0 to isolate resource type impact
    db_downtime = change_service._estimate_downtime_for_resource(
        ChangeType.DEPLOYMENT,
        "database",
        risk_score=0.0,
        dependent_count=0,
        is_critical=False,
    )

    func_downtime = change_service._estimate_downtime_for_resource(
        ChangeType.DEPLOYMENT,
        "function_app",
        risk_score=0.0,
        dependent_count=0,
        is_critical=False,
    )

    # Database should take longer (has 2.0x multiplier vs 0.8x for function app)
    assert db_downtime > func_downtime
    # With 0.0 risk and no dependencies, we can verify the resource type multipliers
    # Base 900 * 2.0 (database) = 1800
    assert db_downtime > 900  # Base deployment time
    # Base 900 * 0.8 (function_app) * 0.8 (complexity for DEPLOYMENT + function_app) = 576
    assert func_downtime < 900  # Less than base deployment time


def test_downtime_scales_with_risk_score(change_service):
    """Test that downtime increases with resource risk score."""
    low_risk_downtime = change_service._estimate_downtime_for_resource(
        ChangeType.DEPLOYMENT,
        "web_app",
        risk_score=20.0,
        dependent_count=0,
        is_critical=False,
    )

    high_risk_downtime = change_service._estimate_downtime_for_resource(
        ChangeType.DEPLOYMENT,
        "web_app",
        risk_score=80.0,
        dependent_count=0,
        is_critical=False,
    )

    # Higher risk should mean longer downtime
    assert high_risk_downtime > low_risk_downtime


def test_downtime_scales_with_dependencies(change_service):
    """Test that downtime increases with number of dependents."""
    few_deps_downtime = change_service._estimate_downtime_for_resource(
        ChangeType.DEPLOYMENT,
        "web_app",
        risk_score=50.0,
        dependent_count=2,
        is_critical=False,
    )

    many_deps_downtime = change_service._estimate_downtime_for_resource(
        ChangeType.DEPLOYMENT,
        "web_app",
        risk_score=50.0,
        dependent_count=20,
        is_critical=False,
    )

    # More dependencies should mean longer downtime
    assert many_deps_downtime > few_deps_downtime


def test_critical_resources_have_longer_downtime(change_service):
    """Test that critical resources have longer estimated downtime."""
    normal_downtime = change_service._estimate_downtime_for_resource(
        ChangeType.DEPLOYMENT,
        "web_app",
        risk_score=50.0,
        dependent_count=5,
        is_critical=False,
    )

    critical_downtime = change_service._estimate_downtime_for_resource(
        ChangeType.DEPLOYMENT,
        "web_app",
        risk_score=50.0,
        dependent_count=5,
        is_critical=True,
    )

    # Critical resources should have 1.5x longer downtime
    assert critical_downtime > normal_downtime
    assert critical_downtime == pytest.approx(normal_downtime * 1.5, rel=0.1)


def test_complex_change_type_resource_combinations(change_service):
    """Test that specific change type + resource type combinations have adjusted risk."""
    # Database updates are particularly complex
    db_update_downtime = change_service._estimate_downtime_for_resource(
        ChangeType.UPDATE,
        "database",
        risk_score=50.0,
        dependent_count=0,
        is_critical=False,
    )

    # Web app updates are less complex
    webapp_update_downtime = change_service._estimate_downtime_for_resource(
        ChangeType.UPDATE,
        "web_app",
        risk_score=50.0,
        dependent_count=0,
        is_critical=False,
    )

    # Database updates should take significantly longer
    assert db_update_downtime > webapp_update_downtime


def test_downtime_respects_minimum_and_maximum(change_service):
    """Test that downtime is capped at reasonable min/max values."""
    # Very low risk, simple change
    min_downtime = change_service._estimate_downtime_for_resource(
        ChangeType.RESTART,
        "function_app",
        risk_score=5.0,
        dependent_count=0,
        is_critical=False,
    )

    # Very high risk, complex change
    max_downtime = change_service._estimate_downtime_for_resource(
        ChangeType.INFRASTRUCTURE,
        "database",
        risk_score=95.0,
        dependent_count=50,
        is_critical=True,
    )

    # Should be capped
    assert min_downtime >= 30  # Min 30 seconds
    assert max_downtime <= 14400  # Max 4 hours


def test_change_type_risk_multipliers(change_service):
    """Test that different change types have different risk multipliers."""
    emergency_risk = change_service._get_change_type_risk_multiplier(ChangeType.EMERGENCY)
    restart_risk = change_service._get_change_type_risk_multiplier(ChangeType.RESTART)
    infrastructure_risk = change_service._get_change_type_risk_multiplier(
        ChangeType.INFRASTRUCTURE
    )

    # Emergency and infrastructure should be higher risk than restart
    assert emergency_risk > 1.0
    assert infrastructure_risk > 1.0
    assert restart_risk < 1.0
    assert emergency_risk > restart_risk
    assert infrastructure_risk > restart_risk


def test_performance_impact_nonlinear(change_service):
    """Test that performance impact uses non-linear scaling."""
    low_risk_perf = change_service._estimate_performance_impact(20.0)
    medium_risk_perf = change_service._estimate_performance_impact(55.0)
    high_risk_perf = change_service._estimate_performance_impact(85.0)

    # Should increase non-linearly
    assert low_risk_perf < 5.0  # Low risk minimal impact
    assert 5.0 < medium_risk_perf < 15.0  # Medium risk moderate impact
    assert high_risk_perf > 15.0  # High risk significant impact


def test_impact_assessment_uses_resource_characteristics(
    change_service, mock_risk_analyzer, mock_neo4j_client
):
    """Test that impact assessment considers resource-specific factors."""
    # Setup mocks
    session_mock = MagicMock()
    mock_neo4j_client.driver.session.return_value.__enter__ = Mock(return_value=session_mock)
    mock_neo4j_client.driver.session.return_value.__exit__ = Mock(return_value=False)

    # Mock query result for dependents
    session_mock.run.return_value = [
        {"id": "dep-1", "name": "Dependent 1", "resource_type": "web_app"},
        {"id": "dep-2", "name": "Dependent 2", "resource_type": "api_gateway"},
    ]

    # Create a mock risk assessment for a database
    mock_risk_analyzer.analyze_resource.return_value = RiskAssessment(
        resource_id="db-1",
        resource_name="Production Database",
        resource_type="database",
        risk_score=75.0,
        risk_level=RiskLevel.HIGH,
        criticality_score=80.0,
        dependencies_count=5,
        dependents_count=10,
        blast_radius=10,
        single_point_of_failure=True,
        recommendations=["High risk resource"],
    )

    # Create a change request for database deployment
    change_request = ChangeRequest(
        id="change-1",
        title="Deploy database update",
        description="Update production database",
        change_type=ChangeType.DEPLOYMENT,
        status=ChangeStatus.DRAFT,
        affected_resources=["db-1"],
    )

    # Assess the impact
    assessment = change_service.assess_change_impact(change_request)

    # Validate that assessment reflects database characteristics
    assert assessment.overall_risk_score > 75.0  # Should be adjusted up due to deployment type
    assert assessment.critical_path_affected is True
    assert assessment.estimated_downtime_seconds > 900  # Should be > base deployment time
    assert assessment.rollback_plan_required is True  # High risk + critical
    assert assessment.approval_required is True  # High risk + critical
    assert len(assessment.directly_affected_resources) == 1
    assert len(assessment.indirectly_affected_resources) == 2


def test_different_resources_same_change_different_impact(
    change_service, mock_risk_analyzer, mock_neo4j_client
):
    """Test that the same change type on different resources yields different impacts."""
    # Setup mocks for session
    session_mock = MagicMock()
    mock_neo4j_client.driver.session.return_value.__enter__ = Mock(return_value=session_mock)
    mock_neo4j_client.driver.session.return_value.__exit__ = Mock(return_value=False)
    session_mock.run.return_value = []  # No dependents for simplicity

    # Test with database
    mock_risk_analyzer.analyze_resource.return_value = RiskAssessment(
        resource_id="db-1",
        resource_name="Database",
        resource_type="database",
        risk_score=60.0,
        risk_level=RiskLevel.MEDIUM,
        criticality_score=60.0,
        dependencies_count=3,
        dependents_count=5,
        blast_radius=5,
        single_point_of_failure=False,
        recommendations=[],
    )

    db_change = ChangeRequest(
        id="change-db",
        title="Restart database",
        description="Restart database",
        change_type=ChangeType.RESTART,
        status=ChangeStatus.DRAFT,
        affected_resources=["db-1"],
    )
    db_assessment = change_service.assess_change_impact(db_change)

    # Test with function app
    mock_risk_analyzer.analyze_resource.return_value = RiskAssessment(
        resource_id="func-1",
        resource_name="Function App",
        resource_type="function_app",
        risk_score=60.0,
        risk_level=RiskLevel.MEDIUM,
        criticality_score=60.0,
        dependencies_count=3,
        dependents_count=5,
        blast_radius=5,
        single_point_of_failure=False,
        recommendations=[],
    )

    func_change = ChangeRequest(
        id="change-func",
        title="Restart function app",
        description="Restart function app",
        change_type=ChangeType.RESTART,
        status=ChangeStatus.DRAFT,
        affected_resources=["func-1"],
    )
    func_assessment = change_service.assess_change_impact(func_change)

    # Database restart should have higher downtime estimate than function app restart
    assert db_assessment.estimated_downtime_seconds > func_assessment.estimated_downtime_seconds


def test_backward_compatibility_legacy_downtime_method(change_service):
    """Test that the legacy _estimate_downtime method still works."""
    # Legacy method should still work for backward compatibility
    deployment_time = change_service._estimate_downtime(ChangeType.DEPLOYMENT)
    restart_time = change_service._estimate_downtime(ChangeType.RESTART)

    assert deployment_time == 900  # 15 minutes
    assert restart_time == 60  # 1 minute
