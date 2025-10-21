"""
Integration test for the discovery scheduler.

This test verifies that the scheduler integrates correctly with the FastAPI application.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient


@pytest.fixture
def mock_neo4j():
    """Mock Neo4j client to avoid needing a real database."""
    with patch("topdeck.common.scheduler.Neo4jClient") as mock:
        client = Mock()
        client.connect = Mock()
        client.close = Mock()
        client.upsert_resource = Mock()
        client.create_dependency = Mock()
        mock.return_value = client
        yield mock


@pytest.fixture
def mock_apscheduler():
    """Mock APScheduler to avoid background threads in tests."""
    with patch("topdeck.common.scheduler.AsyncIOScheduler") as mock_scheduler_class:
        scheduler = Mock()
        scheduler.add_job = Mock()
        scheduler.start = Mock()
        scheduler.shutdown = Mock()
        scheduler.running = False
        mock_scheduler_class.return_value = scheduler
        yield mock_scheduler_class


def test_app_starts_with_scheduler(mock_neo4j, mock_apscheduler):
    """Test that the FastAPI app starts correctly with the scheduler."""
    # Import app after mocks are in place
    from topdeck.api.main import app
    
    # Create test client (this triggers lifespan events)
    with TestClient(app) as client:
        # Verify app is accessible
        response = client.get("/")
        assert response.status_code == 200
        
        # Verify the app object exists and has routes
        assert app is not None
        assert len(app.routes) > 0


def test_discovery_endpoints_available(mock_neo4j, mock_apscheduler):
    """Test that discovery endpoints are available."""
    from topdeck.api.main import app
    
    with TestClient(app) as client:
        # Test status endpoint
        with patch("topdeck.api.routes.discovery.get_scheduler") as mock_get_scheduler:
            mock_scheduler = Mock()
            mock_scheduler.get_status = Mock(return_value={
                "scheduler_running": True,
                "discovery_in_progress": False,
                "last_discovery_time": None,
                "interval_hours": 8,
                "enabled_providers": {
                    "azure": False,
                    "aws": False,
                    "gcp": False,
                },
            })
            mock_get_scheduler.return_value = mock_scheduler
            
            response = client.get("/api/v1/discovery/status")
            assert response.status_code == 200
            data = response.json()
            assert "scheduler_running" in data
            assert "discovery_in_progress" in data
            assert "interval_hours" in data


def test_scheduler_handles_no_credentials(mock_neo4j, mock_apscheduler):
    """Test that scheduler handles missing credentials gracefully."""
    # Ensure no credentials are configured
    with patch("topdeck.common.config.settings") as mock_settings:
        mock_settings.neo4j_uri = "bolt://localhost:7687"
        mock_settings.neo4j_username = "neo4j"
        mock_settings.neo4j_password = "password"
        mock_settings.discovery_scan_interval = 28800
        mock_settings.enable_azure_discovery = False
        mock_settings.enable_aws_discovery = False
        mock_settings.enable_gcp_discovery = False
        
        from topdeck.common.scheduler import DiscoveryScheduler
        
        scheduler = DiscoveryScheduler()
        
        # Should not run discovery without credentials
        assert scheduler._should_run_discovery() is False


def test_health_check_still_works(mock_neo4j, mock_apscheduler):
    """Test that health check endpoints still work with scheduler."""
    from topdeck.api.main import app
    
    with TestClient(app) as client:
        # Basic health check
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


def test_api_info_includes_features(mock_neo4j, mock_apscheduler):
    """Test that API info endpoint returns feature flags."""
    from topdeck.api.main import app
    
    with TestClient(app) as client:
        response = client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        
        assert "features" in data
        assert "azure_discovery" in data["features"]
        assert "aws_discovery" in data["features"]
        assert "gcp_discovery" in data["features"]
