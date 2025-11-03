"""Tests for SPOF monitoring service."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, Mock

import pytest

from topdeck.analysis.risk.models import SinglePointOfFailure
from topdeck.monitoring.spof_monitor import SPOFChange, SPOFMonitor, SPOFSnapshot


@pytest.fixture
def mock_neo4j_client():
    """Create a mock Neo4j client."""
    return MagicMock()


@pytest.fixture
def mock_risk_analyzer():
    """Create a mock risk analyzer."""
    return MagicMock()


@pytest.fixture
def spof_monitor(mock_neo4j_client):
    """Create a SPOF monitor instance."""
    return SPOFMonitor(mock_neo4j_client)


@pytest.fixture
def sample_spofs():
    """Create sample SPOF data."""
    return [
        SinglePointOfFailure(
            resource_id="db-primary",
            resource_name="Primary Database",
            resource_type="database",
            dependents_count=10,
            blast_radius=15,
            risk_score=85.0,
            recommendations=[
                "Add database replica",
                "Implement automatic failover",
            ],
        ),
        SinglePointOfFailure(
            resource_id="auth-service",
            resource_name="Authentication Service",
            resource_type="web_app",
            dependents_count=5,
            blast_radius=8,
            risk_score=75.0,
            recommendations=[
                "Deploy multiple instances",
                "Add load balancing",
            ],
        ),
    ]


def test_spof_monitor_initialization(spof_monitor, mock_neo4j_client):
    """Test SPOF monitor initialization."""
    assert spof_monitor.neo4j_client == mock_neo4j_client
    assert spof_monitor.last_snapshot is None
    assert spof_monitor.changes == []


def test_spof_scan(spof_monitor, sample_spofs):
    """Test SPOF scanning."""
    # Mock the risk analyzer to return sample SPOFs
    spof_monitor.risk_analyzer.identify_single_points_of_failure = Mock(
        return_value=sample_spofs
    )

    # Perform scan
    snapshot = spof_monitor.scan()

    # Verify snapshot
    assert isinstance(snapshot, SPOFSnapshot)
    assert snapshot.total_count == 2
    assert snapshot.high_risk_count == 1  # Only db-primary has risk_score > 80
    assert snapshot.by_resource_type == {"database": 1, "web_app": 1}
    assert len(snapshot.spofs) == 2


def test_spof_scan_empty(spof_monitor):
    """Test SPOF scanning with no SPOFs."""
    # Mock the risk analyzer to return empty list
    spof_monitor.risk_analyzer.identify_single_points_of_failure = Mock(return_value=[])

    # Perform scan
    snapshot = spof_monitor.scan()

    # Verify snapshot
    assert snapshot.total_count == 0
    assert snapshot.high_risk_count == 0
    assert snapshot.by_resource_type == {}
    assert len(snapshot.spofs) == 0


def test_detect_new_spofs(spof_monitor, sample_spofs):
    """Test detection of new SPOFs."""
    # Mock the risk analyzer
    spof_monitor.risk_analyzer.identify_single_points_of_failure = Mock(
        return_value=[sample_spofs[0]]
    )

    # First scan
    spof_monitor.scan()
    assert len(spof_monitor.changes) == 0

    # Second scan with additional SPOF
    spof_monitor.risk_analyzer.identify_single_points_of_failure = Mock(
        return_value=sample_spofs
    )
    spof_monitor.scan()

    # Verify new SPOF was detected
    assert len(spof_monitor.changes) == 1
    change = spof_monitor.changes[0]
    assert change.change_type == "new"
    assert change.resource_id == "auth-service"
    assert change.resource_name == "Authentication Service"


def test_detect_resolved_spofs(spof_monitor, sample_spofs):
    """Test detection of resolved SPOFs."""
    # Mock the risk analyzer
    spof_monitor.risk_analyzer.identify_single_points_of_failure = Mock(
        return_value=sample_spofs
    )

    # First scan with both SPOFs
    spof_monitor.scan()
    assert len(spof_monitor.changes) == 0

    # Second scan with one SPOF resolved
    spof_monitor.risk_analyzer.identify_single_points_of_failure = Mock(
        return_value=[sample_spofs[0]]
    )
    spof_monitor.scan()

    # Verify SPOF resolution was detected
    assert len(spof_monitor.changes) == 1
    change = spof_monitor.changes[0]
    assert change.change_type == "resolved"
    assert change.resource_id == "auth-service"


def test_get_current_spofs(spof_monitor, sample_spofs):
    """Test retrieving current SPOFs."""
    # Mock the risk analyzer
    spof_monitor.risk_analyzer.identify_single_points_of_failure = Mock(
        return_value=sample_spofs
    )

    # Perform scan
    spof_monitor.scan()

    # Get current SPOFs
    current = spof_monitor.get_current_spofs()

    # Verify
    assert len(current) == 2
    assert current[0]["resource_id"] == "db-primary"
    assert current[0]["risk_score"] == 85.0
    assert current[1]["resource_id"] == "auth-service"


def test_get_current_spofs_before_scan(spof_monitor):
    """Test retrieving current SPOFs before any scan."""
    current = spof_monitor.get_current_spofs()
    assert current == []


def test_get_recent_changes(spof_monitor, sample_spofs):
    """Test retrieving recent changes."""
    # Mock the risk analyzer to simulate changes
    spof_monitor.risk_analyzer.identify_single_points_of_failure = Mock(
        return_value=[sample_spofs[0]]
    )
    spof_monitor.scan()

    spof_monitor.risk_analyzer.identify_single_points_of_failure = Mock(
        return_value=sample_spofs
    )
    spof_monitor.scan()

    # Get recent changes
    changes = spof_monitor.get_recent_changes(limit=10)

    # Verify
    assert len(changes) == 1
    assert changes[0]["change_type"] == "new"
    assert changes[0]["resource_id"] == "auth-service"


def test_get_recent_changes_with_limit(spof_monitor):
    """Test retrieving recent changes with limit."""
    # Create multiple changes by adding them directly
    for i in range(10):
        change = SPOFChange(
            change_type="new",
            resource_id=f"resource-{i}",
            resource_name=f"Resource {i}",
            resource_type="web_app",
            detected_at=datetime.now(UTC),
            risk_score=75.0,
            blast_radius=5,
        )
        spof_monitor.changes.append(change)

    # Get with limit
    changes = spof_monitor.get_recent_changes(limit=5)

    # Verify - should get last 5 in reverse order
    assert len(changes) == 5
    assert changes[0]["resource_id"] == "resource-9"
    assert changes[4]["resource_id"] == "resource-5"


def test_get_statistics_before_scan(spof_monitor):
    """Test getting statistics before any scan."""
    stats = spof_monitor.get_statistics()

    assert stats["status"] == "not_scanned"
    assert "message" in stats


def test_get_statistics_after_scan(spof_monitor, sample_spofs):
    """Test getting statistics after scan."""
    # Mock the risk analyzer
    spof_monitor.risk_analyzer.identify_single_points_of_failure = Mock(
        return_value=sample_spofs
    )

    # Perform scan
    spof_monitor.scan()

    # Get statistics
    stats = spof_monitor.get_statistics()

    # Verify
    assert stats["status"] == "active"
    assert "last_scan" in stats
    assert stats["total_spofs"] == 2
    assert stats["high_risk_spofs"] == 1
    assert stats["by_resource_type"] == {"database": 1, "web_app": 1}
    assert stats["total_changes"] == 0


def test_spof_snapshot_creation():
    """Test SPOFSnapshot dataclass creation."""
    spofs = [
        SinglePointOfFailure(
            resource_id="test-1",
            resource_name="Test 1",
            resource_type="database",
            dependents_count=5,
            blast_radius=10,
            risk_score=90.0,
            recommendations=["Add redundancy"],
        )
    ]

    snapshot = SPOFSnapshot(
        timestamp=datetime.now(UTC),
        spofs=spofs,
        total_count=1,
        high_risk_count=1,
        by_resource_type={"database": 1},
    )

    assert snapshot.total_count == 1
    assert snapshot.high_risk_count == 1
    assert len(snapshot.spofs) == 1


def test_spof_change_creation():
    """Test SPOFChange dataclass creation."""
    change = SPOFChange(
        change_type="new",
        resource_id="test-resource",
        resource_name="Test Resource",
        resource_type="web_app",
        detected_at=datetime.now(UTC),
        risk_score=85.0,
        blast_radius=12,
    )

    assert change.change_type == "new"
    assert change.resource_id == "test-resource"
    assert change.risk_score == 85.0
