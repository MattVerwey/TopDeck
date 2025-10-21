"""
Tests for the discovery API routes.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from topdeck.api.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_scheduler():
    """Create a mock scheduler."""
    scheduler = Mock()
    scheduler.get_status = Mock(
        return_value={
            "scheduler_running": True,
            "discovery_in_progress": False,
            "last_discovery_time": "2025-10-21T12:00:00",
            "interval_hours": 8,
            "enabled_providers": {
                "azure": True,
                "aws": False,
                "gcp": False,
            },
        }
    )
    scheduler.trigger_manual_discovery = AsyncMock(
        return_value={
            "status": "scheduled",
            "message": "Discovery has been scheduled to run",
            "last_run": "2025-10-21T12:00:00",
        }
    )
    return scheduler


@patch("topdeck.api.routes.discovery.get_scheduler")
def test_get_discovery_status(mock_get_scheduler, client, mock_scheduler):
    """Test GET /api/v1/discovery/status endpoint."""
    mock_get_scheduler.return_value = mock_scheduler

    response = client.get("/api/v1/discovery/status")

    assert response.status_code == 200
    data = response.json()

    assert data["scheduler_running"] is True
    assert data["discovery_in_progress"] is False
    assert data["last_discovery_time"] == "2025-10-21T12:00:00"
    assert data["interval_hours"] == 8
    assert data["enabled_providers"]["azure"] is True
    assert data["enabled_providers"]["aws"] is False
    assert data["enabled_providers"]["gcp"] is False


@patch("topdeck.api.routes.discovery.get_scheduler")
def test_get_discovery_status_error(mock_get_scheduler, client):
    """Test GET /api/v1/discovery/status with error."""
    mock_get_scheduler.side_effect = Exception("Test error")

    response = client.get("/api/v1/discovery/status")

    assert response.status_code == 500
    assert "Failed to get discovery status" in response.json()["detail"]


@patch("topdeck.api.routes.discovery.get_scheduler")
@pytest.mark.asyncio
async def test_trigger_discovery(mock_get_scheduler, client, mock_scheduler):
    """Test POST /api/v1/discovery/trigger endpoint."""
    mock_get_scheduler.return_value = mock_scheduler

    response = client.post("/api/v1/discovery/trigger")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "scheduled"
    assert "scheduled to run" in data["message"]
    assert data["last_run"] == "2025-10-21T12:00:00"


@patch("topdeck.api.routes.discovery.get_scheduler")
@pytest.mark.asyncio
async def test_trigger_discovery_already_running(mock_get_scheduler, client):
    """Test POST /api/v1/discovery/trigger when already running."""
    mock_scheduler = Mock()
    mock_scheduler.trigger_manual_discovery = AsyncMock(
        return_value={
            "status": "already_running",
            "message": "Discovery is already in progress",
        }
    )
    mock_get_scheduler.return_value = mock_scheduler

    response = client.post("/api/v1/discovery/trigger")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "already_running"
    assert "already in progress" in data["message"]


@patch("topdeck.api.routes.discovery.get_scheduler")
@pytest.mark.asyncio
async def test_trigger_discovery_error(mock_get_scheduler, client):
    """Test POST /api/v1/discovery/trigger with error."""
    mock_scheduler = Mock()
    mock_scheduler.trigger_manual_discovery = AsyncMock(side_effect=Exception("Test error"))
    mock_get_scheduler.return_value = mock_scheduler

    response = client.post("/api/v1/discovery/trigger")

    assert response.status_code == 500
    assert "Failed to trigger discovery" in response.json()["detail"]
