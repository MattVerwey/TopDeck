"""Tests for SPOF monitoring API routes."""

from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from topdeck.api.main import app

client = TestClient(app)


@pytest.fixture
def mock_spof_monitor():
    """Create a mock SPOF monitor."""
    monitor = Mock()
    monitor.get_current_spofs = Mock(
        return_value=[
            {
                "resource_id": "db-primary",
                "resource_name": "Primary Database",
                "resource_type": "database",
                "dependents_count": 10,
                "blast_radius": 15,
                "risk_score": 85.0,
                "recommendations": [
                    "Add database replica",
                    "Implement automatic failover",
                ],
            }
        ]
    )
    monitor.get_recent_changes = Mock(
        return_value=[
            {
                "change_type": "new",
                "resource_id": "db-primary",
                "resource_name": "Primary Database",
                "resource_type": "database",
                "detected_at": datetime.now(UTC).isoformat(),
                "risk_score": 85.0,
                "blast_radius": 15,
            }
        ]
    )
    monitor.get_statistics = Mock(
        return_value={
            "status": "active",
            "last_scan": datetime.now(UTC).isoformat(),
            "total_spofs": 1,
            "high_risk_spofs": 1,
            "by_resource_type": {"database": 1},
            "total_changes": 1,
            "recent_changes": {"new": 1, "resolved": 0},
        }
    )
    return monitor


@pytest.fixture
def mock_scheduler(mock_spof_monitor):
    """Create a mock scheduler with SPOF monitor."""
    scheduler = Mock()
    scheduler.spof_monitor = mock_spof_monitor
    scheduler.trigger_manual_spof_scan = Mock(
        return_value={
            "status": "scheduled",
            "message": "SPOF scan has been scheduled to run",
            "last_scan": datetime.now(UTC).isoformat(),
        }
    )
    return scheduler


@patch("topdeck.api.routes.spof_monitoring.get_scheduler")
def test_get_current_spofs(mock_get_scheduler, mock_scheduler):
    """Test GET /api/v1/monitoring/spof/current endpoint."""
    mock_get_scheduler.return_value = mock_scheduler

    response = client.get("/api/v1/monitoring/spof/current")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["resource_id"] == "db-primary"
    assert data[0]["risk_score"] == 85.0


@patch("topdeck.api.routes.spof_monitoring.get_scheduler")
def test_get_current_spofs_no_monitor(mock_get_scheduler):
    """Test GET /api/v1/monitoring/spof/current when monitor not initialized."""
    scheduler = Mock()
    scheduler.spof_monitor = None
    mock_get_scheduler.return_value = scheduler

    response = client.get("/api/v1/monitoring/spof/current")

    assert response.status_code == 503
    assert "SPOF monitor not initialized" in response.json()["detail"]


@patch("topdeck.api.routes.spof_monitoring.get_scheduler")
def test_get_spof_history(mock_get_scheduler, mock_scheduler):
    """Test GET /api/v1/monitoring/spof/history endpoint."""
    mock_get_scheduler.return_value = mock_scheduler

    response = client.get("/api/v1/monitoring/spof/history")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["change_type"] == "new"
    assert data[0]["resource_id"] == "db-primary"


@patch("topdeck.api.routes.spof_monitoring.get_scheduler")
def test_get_spof_history_with_limit(mock_get_scheduler, mock_scheduler):
    """Test GET /api/v1/monitoring/spof/history with limit parameter."""
    mock_get_scheduler.return_value = mock_scheduler

    response = client.get("/api/v1/monitoring/spof/history?limit=10")

    assert response.status_code == 200
    # Verify the limit was passed to the monitor
    mock_scheduler.spof_monitor.get_recent_changes.assert_called_with(limit=10)


@patch("topdeck.api.routes.spof_monitoring.get_scheduler")
def test_get_spof_statistics(mock_get_scheduler, mock_scheduler):
    """Test GET /api/v1/monitoring/spof/statistics endpoint."""
    mock_get_scheduler.return_value = mock_scheduler

    response = client.get("/api/v1/monitoring/spof/statistics")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["total_spofs"] == 1
    assert data["high_risk_spofs"] == 1
    assert "last_scan" in data


@patch("topdeck.api.routes.spof_monitoring.get_scheduler")
def test_trigger_spof_scan(mock_get_scheduler, mock_scheduler):
    """Test POST /api/v1/monitoring/spof/scan endpoint."""
    mock_get_scheduler.return_value = mock_scheduler

    response = client.post("/api/v1/monitoring/spof/scan")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "scheduled"
    assert "message" in data


@patch("topdeck.api.routes.spof_monitoring.get_scheduler")
def test_get_spof_metrics(mock_get_scheduler, mock_scheduler):
    """Test GET /api/v1/monitoring/spof/metrics endpoint."""
    mock_get_scheduler.return_value = mock_scheduler

    response = client.get("/api/v1/monitoring/spof/metrics")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert "metrics" in data
    assert data["metrics"]["spof_total"] == 1
    assert data["metrics"]["spof_high_risk"] == 1


@patch("topdeck.api.routes.spof_monitoring.get_scheduler")
def test_get_spof_metrics_not_scanned(mock_get_scheduler):
    """Test GET /api/v1/monitoring/spof/metrics when no scan performed."""
    scheduler = Mock()
    monitor = Mock()
    monitor.get_statistics = Mock(return_value={"status": "not_scanned"})
    scheduler.spof_monitor = monitor
    mock_get_scheduler.return_value = scheduler

    response = client.get("/api/v1/monitoring/spof/metrics")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_scanned"
    assert data["metrics"] == {}
