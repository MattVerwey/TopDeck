"""Tests for impact analyzer module."""

from unittest.mock import Mock

import pytest

from topdeck.analysis.risk.dependency import DependencyAnalyzer
from topdeck.analysis.risk.impact import ImpactAnalyzer
from topdeck.analysis.risk.models import ImpactLevel


@pytest.fixture
def mock_dependency_analyzer():
    """Create a mock dependency analyzer."""
    analyzer = Mock(spec=DependencyAnalyzer)
    return analyzer


@pytest.fixture
def impact_analyzer(mock_dependency_analyzer):
    """Create an impact analyzer with mock dependency analyzer."""
    return ImpactAnalyzer(mock_dependency_analyzer)


def test_impact_analyzer_initialization(impact_analyzer, mock_dependency_analyzer):
    """Test impact analyzer initialization."""
    assert impact_analyzer.dependency_analyzer == mock_dependency_analyzer


def test_calculate_blast_radius_no_impact(impact_analyzer, mock_dependency_analyzer):
    """Test blast radius calculation with no impact."""
    # Mock no affected resources
    mock_dependency_analyzer.get_affected_resources.return_value = ([], [])
    mock_dependency_analyzer.find_critical_path.return_value = ["resource-1"]

    blast_radius = impact_analyzer.calculate_blast_radius("resource-1", "Resource 1")

    assert blast_radius.resource_id == "resource-1"
    assert blast_radius.resource_name == "Resource 1"
    assert blast_radius.total_affected == 0
    assert blast_radius.user_impact == ImpactLevel.MINIMAL
    assert blast_radius.estimated_downtime_seconds > 0


def test_calculate_blast_radius_low_impact(impact_analyzer, mock_dependency_analyzer):
    """Test blast radius calculation with low impact."""
    # Mock minimal affected resources
    directly_affected = [{"id": "r1", "name": "R1", "type": "storage", "cloud_provider": "azure"}]
    mock_dependency_analyzer.get_affected_resources.return_value = (directly_affected, [])
    mock_dependency_analyzer.find_critical_path.return_value = ["resource-1", "r1"]

    blast_radius = impact_analyzer.calculate_blast_radius("resource-1", "Resource 1")

    assert blast_radius.total_affected == 1
    assert blast_radius.user_impact == ImpactLevel.LOW
    assert len(blast_radius.directly_affected) == 1
    assert len(blast_radius.indirectly_affected) == 0


def test_calculate_blast_radius_high_impact(impact_analyzer, mock_dependency_analyzer):
    """Test blast radius calculation with high impact."""
    # Mock many affected resources including user-facing
    directly_affected = [
        {"id": "r1", "name": "R1", "type": "web_app", "cloud_provider": "azure"},
        {"id": "r2", "name": "R2", "type": "api_gateway", "cloud_provider": "azure"},
    ]
    indirectly_affected = [
        {
            "id": "r3",
            "name": "R3",
            "type": "function_app",
            "cloud_provider": "azure",
            "distance": 2,
        },
        {"id": "r4", "name": "R4", "type": "storage", "cloud_provider": "azure", "distance": 2},
    ]
    mock_dependency_analyzer.get_affected_resources.return_value = (
        directly_affected,
        indirectly_affected,
    )
    mock_dependency_analyzer.find_critical_path.return_value = ["resource-1", "r1", "r3"]

    blast_radius = impact_analyzer.calculate_blast_radius("resource-1", "Resource 1")

    assert blast_radius.total_affected == 4
    assert blast_radius.user_impact in [ImpactLevel.MEDIUM, ImpactLevel.HIGH]
    assert len(blast_radius.directly_affected) == 2
    assert len(blast_radius.indirectly_affected) == 2


def test_calculate_blast_radius_severe_impact(impact_analyzer, mock_dependency_analyzer):
    """Test blast radius calculation with severe impact."""
    # Mock many affected resources
    directly_affected = [
        {"id": f"r{i}", "name": f"R{i}", "type": "web_app", "cloud_provider": "azure"}
        for i in range(10)
    ]
    indirectly_affected = [
        {"id": f"r{i}", "name": f"R{i}", "type": "pod", "cloud_provider": "azure", "distance": 2}
        for i in range(10, 25)
    ]
    mock_dependency_analyzer.get_affected_resources.return_value = (
        directly_affected,
        indirectly_affected,
    )
    mock_dependency_analyzer.find_critical_path.return_value = ["resource-1", "r1"]

    blast_radius = impact_analyzer.calculate_blast_radius("resource-1", "Resource 1")

    assert blast_radius.total_affected == 25
    assert blast_radius.user_impact == ImpactLevel.SEVERE


def test_estimate_user_impact_minimal(impact_analyzer):
    """Test user impact estimation for minimal impact."""
    impact = impact_analyzer._estimate_user_impact("resource-1", [], [])
    assert impact == ImpactLevel.MINIMAL


def test_estimate_user_impact_low(impact_analyzer):
    """Test user impact estimation for low impact."""
    directly_affected = [{"id": "r1", "name": "R1", "type": "storage", "cloud_provider": "azure"}]
    impact = impact_analyzer._estimate_user_impact("resource-1", directly_affected, [])
    assert impact == ImpactLevel.LOW


def test_estimate_user_impact_with_user_facing(impact_analyzer):
    """Test user impact increases with user-facing services."""
    directly_affected = [{"id": "r1", "name": "R1", "type": "web_app", "cloud_provider": "azure"}]
    impact = impact_analyzer._estimate_user_impact("resource-1", directly_affected, [])
    # Should be at least MEDIUM due to user-facing service
    assert impact in [ImpactLevel.MEDIUM, ImpactLevel.HIGH]


def test_estimate_downtime_minimal(impact_analyzer):
    """Test downtime estimation for minimal impact."""
    downtime = impact_analyzer._estimate_downtime(0, ImpactLevel.MINIMAL)
    assert downtime > 0
    assert downtime < 1000  # Less than reasonable time


def test_estimate_downtime_severe(impact_analyzer):
    """Test downtime estimation for severe impact."""
    downtime = impact_analyzer._estimate_downtime(25, ImpactLevel.SEVERE)
    assert downtime > 1000  # Should be substantial
    assert downtime <= 86400  # But capped at 24 hours


def test_estimate_downtime_scales_with_affected(impact_analyzer):
    """Test that downtime scales with number of affected resources."""
    downtime_few = impact_analyzer._estimate_downtime(2, ImpactLevel.MEDIUM)
    downtime_many = impact_analyzer._estimate_downtime(20, ImpactLevel.MEDIUM)
    assert downtime_many > downtime_few


def test_count_by_service_type(impact_analyzer):
    """Test counting resources by service type."""
    resources = [
        {"type": "web_app"},
        {"type": "web_app"},
        {"type": "database"},
        {"type": "web_app"},
        {"type": "storage"},
        {"type": "database"},
    ]

    counts = impact_analyzer._count_by_service_type(resources)

    assert counts["web_app"] == 3
    assert counts["database"] == 2
    assert counts["storage"] == 1


def test_count_by_service_type_empty(impact_analyzer):
    """Test counting with empty resource list."""
    counts = impact_analyzer._count_by_service_type([])
    assert len(counts) == 0


def test_count_by_service_type_unknown(impact_analyzer):
    """Test counting with unknown service types."""
    resources = [
        {"type": "unknown_type"},
        {},  # Missing type
    ]

    counts = impact_analyzer._count_by_service_type(resources)

    assert "unknown_type" in counts
    assert "unknown" in counts


def test_blast_radius_includes_critical_path(impact_analyzer, mock_dependency_analyzer):
    """Test that blast radius includes critical path."""
    directly_affected = [{"id": "r1", "name": "R1", "type": "web_app", "cloud_provider": "azure"}]
    mock_dependency_analyzer.get_affected_resources.return_value = (directly_affected, [])
    mock_dependency_analyzer.find_critical_path.return_value = ["resource-1", "r1", "r2"]

    blast_radius = impact_analyzer.calculate_blast_radius("resource-1", "Resource 1")

    assert len(blast_radius.critical_path) == 3
    assert blast_radius.critical_path[0] == "resource-1"


def test_blast_radius_includes_affected_services(impact_analyzer, mock_dependency_analyzer):
    """Test that blast radius includes service breakdown."""
    directly_affected = [
        {"id": "r1", "name": "R1", "type": "web_app", "cloud_provider": "azure"},
        {"id": "r2", "name": "R2", "type": "web_app", "cloud_provider": "azure"},
    ]
    indirectly_affected = [
        {"id": "r3", "name": "R3", "type": "database", "cloud_provider": "azure", "distance": 2},
    ]
    mock_dependency_analyzer.get_affected_resources.return_value = (
        directly_affected,
        indirectly_affected,
    )
    mock_dependency_analyzer.find_critical_path.return_value = ["resource-1"]

    blast_radius = impact_analyzer.calculate_blast_radius("resource-1", "Resource 1")

    assert "web_app" in blast_radius.affected_services
    assert "database" in blast_radius.affected_services
    assert blast_radius.affected_services["web_app"] == 2
    assert blast_radius.affected_services["database"] == 1
